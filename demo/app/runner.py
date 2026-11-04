"""Single-task demo supervisor. Agent history and harness output are disposable."""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from decimal import Decimal, InvalidOperation

from bridge import SandboxBridge
from json_input import loads
from policy import gate_value, native_usage
from profiles import PROFILES, model_metadata
from relay import ContextRelay
from sandbox import SANDBOX_OUT, Sandbox
from scenarios import SCENARIOS, SOLUTIONS, contract
from settings import AGENT_UID, FLUE, HARNESS, WORK
from factory.budget import BudgetError
import triage

CHECKER = "/opt/demo/fixtures/check-scenario.js"
AGENT_TIMEOUT_SECONDS = 360
# On Docker Desktop the host-backed work volume accepts a write but returns EACCES, so agent
# writes happen in a sandbox-owned directory and are collected out over the exec channel.
SANDBOX_WORKSPACE = SANDBOX_OUT + "/workspace"
COPYOUT = os.environ.get("AEION_SANDBOX_COPYOUT", "auto") != "0"
# Execution tier per run runtime. Relay gates, handover, checks, telemetry and memory are shared.
AGENTS = {"flue-openshell": "src/agents/coder.ts", "flue-local": "src/agents/local-assistant.ts",
          "flue-just-bash": "src/agents/triage.ts"}
TRIAGE = "flue-just-bash"
FAILURES = {"USAGE_UNKNOWN", "COST_UNKNOWN", "INVALID_ARTIFACT", "INVALID_CHECK_OUTPUT", "PROVIDER_CONTEXT_VIOLATION",
            "CONTEXT_ACCOUNTING_MISMATCH", "CONTEXT_UNKNOWN", "PROVIDER_REJECTED", "CLI_CLIENT_REQUIRED",
            "GO_SUBSCRIPTION_REQUIRED", "MODEL_DISABLED", "PROVIDER_ERROR", "CLI_FAILED", "CLI_PROTOCOL_ERROR",
            "HARNESS_COMPACTION", "AGENT_TIMEOUT", "BUDGET_STOP", "STEP_LIMIT", "HANDOVER_NOT_READY",
            "OUTPUT_LIMIT", "AEION_HANDOVER",
            "INSUFFICIENT_FUNDS", "GO_REGION_REQUIRED", "QUOTA_STOP", "AUTH_ERROR", "SANDBOX_NOT_QUALIFIED",
            "SANDBOX_UNAVAILABLE", "SANDBOX_VERSION_MISMATCH", "SANDBOX_EXEC_FAILED", "SANDBOX_STOP_FAILED"}


def max_cost():
    # One default for the pre-dispatch budget and the after-response monitor; the documented $0.10.
    return Decimal(os.environ.get("DEMO_MAX_COST_USD", "0.10"))


def digest(path):
    # Never follow an agent-created symlink, read a device or accept a giant artifact.
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32768:
        raise ValueError("INVALID_ARTIFACT")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def acceptance(workspace, sandbox, task_id="pricing-js-v1", artifact=None):
    path = workspace / "src/pricing.js"
    digest(path)
    # The artifact the checker reads is the one seeded into the sandbox, not the host mount:
    # on Docker Desktop the mount reports writes it did not make visible and refuses listings.
    if artifact is None and hasattr(sandbox, "seed_in"):
        sandbox.seed_in({"src/pricing.js": path.read_bytes()}, SANDBOX_WORKSPACE)
        target = SANDBOX_WORKSPACE + "/src/pricing.js"
    else:
        target = artifact or str(path)
    task = SCENARIOS[task_id]
    # Agent code runs as the sandbox user with read access to the artifact only. Expected
    # results travel on stdin and never exist in the agent's image or workspace.
    result = sandbox.exec(
        ["deno", "run", "--no-config", "--no-npm", "--no-remote", "--no-prompt", "--allow-read=" + target, CHECKER, target],
        timeout=10, env={"DENO_DIR": "/tmp/deno-checks"},
        stdin=json.dumps({"export": task["export"], "cases": task["cases"]}).encode(),
    )
    if len(result.stdout) > 4096:
        raise ValueError("INVALID_CHECK_OUTPUT")
    try:
        check = json.loads(result.stdout)
        if set(check) != {"passed", "failed", "total"} or type(check["passed"]) is not int:
            raise ValueError
        if not isinstance(check["failed"], list) or any(not isinstance(v, str) or len(v) > 40 for v in check["failed"]):
            raise ValueError
        if (result.exit_code == 0) != (check == {"passed": len(task["cases"]), "failed": [], "total": len(task["cases"])}):
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("INVALID_CHECK_OUTPUT") from None
    return check


def usage_is_complete(steps, forwarded_count, error=None):
    """Complete accounting needs at least one request and one accounted response per relay."""
    return bool(steps) and steps == forwarded_count and error is None


def factory_work_limit(run, current_forwards, now=None):
    """The author deadline and model-step cap survive fresh harness sessions."""
    cap = run.get('step_cap',12)
    previous = run.get('forwarded_count',0)
    deadline = run.get('factory_deadline')
    if (type(cap) is not int or cap < 1 or type(previous) is not int or previous < 0
            or type(current_forwards) is not int or current_forwards < 0):
        return 'WORK_LIMIT_INVALID'
    if deadline is not None:
        if type(deadline) not in (int,float) or not math.isfinite(deadline):
            return 'WORK_LIMIT_INVALID'
        if (time.monotonic() if now is None else now) >= deadline:
            return 'AGENT_DEADLINE'
    if previous + current_forwards >= cap:
        return 'STEP_LIMIT'
    return None


def artifact_name(run):
    return triage.ARTIFACT if run.get("runtime") == TRIAGE else "src/pricing.js"


def tasks(runtime):
    # Tier 1 has its own frozen triage contract; tiers 2 and 3 share the four coding contracts.
    return triage.TRIAGE if runtime == TRIAGE else SCENARIOS


def task_contract(run):
    task_id = run.get("task_id", "pricing-js-v1")
    return triage.contract(task_id) if run.get("runtime") == TRIAGE else contract(task_id)


class Runner:
    def __init__(self, telemetry, save, work_root=WORK, memory=None, audit=None,
                 budget=None, budget_scope="aeion-observability"):
        self.telemetry, self.save, self.work_root = telemetry, save, work_root
        self.memory = memory
        self.audit = audit
        self.budget = budget
        self.budget_scope = budget_scope
        self.active_sandbox = None
        self.event_lock = threading.RLock()

    def _reserve(self, run):
        """Journal this live run's spending cap; no purse or no room means no run."""
        if self.budget is None:
            raise ValueError("BUDGET_STOP")
        try:
            reservation = self.budget.admit(
                self.budget_scope, max_cost(), note=run["id"])
        except (BudgetError, InvalidOperation):
            raise ValueError("BUDGET_STOP") from None
        run["budget"] = {"scope": self.budget_scope, "reservation": reservation.id,
                         "estimated_usd": format(reservation.estimate_usd, "f")}
        return reservation

    def _settle(self, run, reservation):
        if reservation is None:
            return
        # A zero default is not evidence of a free run. Only complete, trusted usage (or an
        # explicitly proven no-transport outcome) may close the reservation; otherwise it stays
        # open and keeps its estimate counted against the purse.
        if run.get("usage_complete") is not True and run.get("budget_release") != "proven_no_transport":
            run["budget"]["settled_usd"] = "unsettled"
            return
        try:
            actual = Decimal(str(run.get("native_cost_usd", "0")))
            self.budget.settle(reservation, actual)
            run["budget"]["settled_usd"] = format(actual, "f")
        except (BudgetError, InvalidOperation, ValueError):
            # The reservation stays open and keeps counting: fail closed, never free the money.
            run["budget"]["settled_usd"] = "unsettled"

    def event(self, run, name, **attrs):
        # The allowlist is mirrored by the Collector, never copy a harness event into telemetry.
        with self.event_lock:
            sequence = len(run["events"]) + 1
            event = {"name": name, "id": f"{run['id']}:{sequence}", "sequence": sequence,
                     "time_unix_ns": time.time_ns(), "trace_id": run["trace_id"], "span_id": run["root_span_id"],
                     "aeion.task.id": run.get("task_id", "pricing-js-v1"), "aeion.runtime": run.get("runtime", "legacy"),
                     "severity": "WARN" if name in {"gate.closed", "task.failed", "context.refused"} else "INFO", **attrs}
            if self.audit:
                self.audit.record(run, event)
            run["events"].append(event)
            self.telemetry.emit(run, name, **attrs, **{"aeion.event.id": event["id"], "aeion.event.sequence": sequence})
            self.save(run)

    def check(self, run, workspace, sandbox):
        if run.get("runtime") == TRIAGE:
            return triage.check(workspace / triage.ARTIFACT, run.get("task_id"))
        return acceptance(workspace, sandbox, run.get("task_id", "pricing-js-v1"))

    def prepare_handover(self, run, workspace, observed, basis="native_report"):
        # Informational check in the live sandbox; the authoritative verdict uses a fresh one.
        check = self.check(run, workspace, self.active_sandbox)
        artifact = artifact_name(run)
        source_hash = digest(workspace / artifact)
        if run.get("runtime") == TRIAGE:
            basis_note = "interim check by the supervisor's deterministic validator."
            next_action = ("Re-read /data/events.json, complete the triage and submit the full result again with "
                           "submit_triage; the supervisor checks the submitted result.")
        else:
            basis_note = "interim protected check in the live sandbox; the final verdict uses a fresh sandbox."
            next_action = ("Read this document and the preserved source. Complete or verify the implementation; "
                           "the supervisor runs immutable Deno checks. Edit only src/pricing.js.")
        markdown = (
            "# AEion agent handover\n\n"
            f"Task: {run.get('task_id', 'pricing-js-v1')}\nAgent: {run['agents']}\n"
            f"Context ({basis}, {run['metric']}): {observed}\nGate: {run['limit']} tokens\nHard admission budget: 300000 tokens\n\n"
            "## Objective\n\n" + task_contract(run) + "\n\n"
            f"## Preserved artifact\n\n- File: `{artifact}`\n- SHA-256: `{source_hash}`\n\n"
            f"## Independent verification\n\n- Passed: {check['passed']}/{check['total']}\n"
            "- Remaining checks: " + (", ".join(check["failed"]) or "none") + "\n"
            "- Basis: " + basis_note + "\n\n"
            "## Next action\n\n" + next_action + " "
            "This is a new session: no prior transcript, resumed session, compaction summary or tool state is required.\n"
        )
        path = workspace / "HANDOVER.md"
        temporary = workspace / ".HANDOVER.tmp"
        with temporary.open("w") as output:
            output.write(markdown)
            output.flush()
            os.fsync(output.fileno())
        temporary.chmod(0o444)
        temporary.replace(path)
        # Fsync the directory entry before acknowledging the durable checkpoint.
        directory = os.open(workspace, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        run["handover_md_sha256"] = digest(path)
        field = "aeion.context.observed" if basis == "native_report" else "aeion.context.counted"
        self.event(run, "handover.prepared", **{field: observed, "aeion.context.basis": basis,
                                               "aeion.handover.sha256": run["handover_md_sha256"]})
        return run["handover_md_sha256"]

    @staticmethod
    def copies_out(run):
        """Only tier 3 writes inside the sandbox; tier 2 tools act on the host workspace."""
        return COPYOUT and run.get("runtime") == "flue-openshell"

    def seed_workspace(self, sandbox, workspace):
        """Send the supervisor's starting files into the sandbox before the agent runs."""
        files = {}
        for path in sorted(workspace.rglob("*")):
            if path.is_file() and not path.is_symlink() and ".git" not in path.parts:
                files[str(path.relative_to(workspace))] = path.read_bytes()
        return sandbox.seed_in(files, SANDBOX_WORKSPACE)

    def collect_workspace(self, sandbox, workspace):
        """Bring the agent's writes back to the host over the exec channel."""
        copied = sandbox.sync_out(workspace, SANDBOX_WORKSPACE)
        return copied

    def verify(self, run, root, workspace):
        if run.get("runtime") == TRIAGE:
            return self.check(run, workspace, None)  # Data comparison only; no generated code runs.
        # Authoritative verdict in a fresh sandbox where no agent process has ever run.
        sandbox = Sandbox(run, root, role="check")
        try:
            # The checker reads the artifact from inside the sandbox, never from the mount:
            # a host-written file is unreadable to the sandbox UID on Docker Desktop.
            self.seed_workspace(sandbox, workspace)
            return acceptance(workspace, sandbox, run.get("task_id", "pricing-js-v1"),
                              artifact=SANDBOX_WORKSPACE + "/src/pricing.js")
        finally:
            sandbox.close()

    def run(self, run):
        root_span = self.telemetry.begin(run)
        root = self.work_root / run["id"]
        workspace = root / "workspace"
        source = workspace / artifact_name(run)
        isolated = run.get("runtime") != TRIAGE
        if run.get("synthetic"):
            # The simulator makes no provider call: zero usage is measured, not a default.
            run["usage_complete"] = True
        # On Linux the sandbox runs as this user; Docker Desktop maps a foreign UID instead.
        reservation = None
        try:
            # No live run starts without a journaled, bounded claim on the daily purse.
            if not run.get("synthetic"):
                reservation = self._reserve(run)
            root.mkdir(mode=0o700, parents=False)
            workspace.mkdir(mode=0o755)
            if isolated:
                source.parent.mkdir(mode=0o755)
                source.write_text("export function " + SCENARIOS[run.get("task_id", "pricing-js-v1")]["export"] + "() { throw new Error(\"not implemented\"); }\n")
            else:
                source.write_text(triage.EMPTY)  # Tier 1 has no OpenShell sandbox; its harness writes as this user.
            subprocess.run(["git", "init", "-q", str(workspace)], check=True, capture_output=True)
            original = digest(source)
            handover = None
            for agent in range(1, 4):
                run["agents"] = agent
                self.event(run, "agent.started", **{"aeion.agent.number": agent})
                # Tier 2 tools never reach this sandbox; it serves the supervisor's interim checks.
                self.active_sandbox = Sandbox(run, root) if isolated else None
                sandbox = self.active_sandbox
                entered = False
                try:
                    if sandbox:
                        self.event(run, "sandbox.ready", **{"aeion.sandbox.id": sandbox.ref.id})
                        if self.copies_out(run):
                            try:
                                seeded = self.seed_workspace(sandbox, workspace)
                            except Exception as error:  # noqa: BLE001 - record the type, fail closed
                                self.event(run, "sandbox.seed_failed",
                                           **{"aeion.failure.code": "SANDBOX_SEED_FAILED",
                                              "aeion.failure.type": type(error).__name__})
                                raise
                            self.event(run, "sandbox.seeded", **{"aeion.sandbox.files": seeded})
                    entered = True
                    outcome = self.simulate(run, workspace, agent) if run["synthetic"] else self.live(run, workspace, handover)
                finally:
                    if sandbox:
                        try:
                            if entered and self.copies_out(run):
                                try:
                                    copied = self.collect_workspace(sandbox, workspace)
                                    self.event(run, "sandbox.collected", **{"aeion.sandbox.files": len(copied)})
                                except ValueError as error:
                                    self.event(run, "sandbox.collect_failed", **{"aeion.failure.code": str(error)})
                                    raise
                        finally:
                            # Close runs even when seeding, collection or the agent raised.
                            try:
                                sandbox.close()  # OpenShell deletes the workload and reaps every process in it.
                            finally:
                                self.active_sandbox = None
                                self.event(run, "sandbox.retired", **{"aeion.sandbox.id": sandbox.ref.id})
                    self.event(run, "session.wiped", **{"aeion.agent.number": agent})
                check = self.verify(run, root, workspace)
                changed = digest(source) != original
                run.update(check=check, artifact_sha256=digest(source), changed=changed)
                self.event(run, "artifact.checked", **{"aeion.check.passed": check["passed"], "aeion.artifact.changed": changed})
                state = {"task": run.get("task_id", "pricing-js-v1"), "previous_agent": agent,
                         "artifact": artifact_name(run), "sha256": digest(source), "check": check}
                if self.memory:
                    try:
                        state = self.memory.checkpoint(run, state)
                        self.event(run, "memory.checkpoint", **{"aeion.memory.backend": "claude-mem"})
                    except Exception:
                        # Storage is advisory; artifact/check state remains locally authoritative.
                        run["checkpoint_status"] = "unavailable"
                if outcome == "handover":
                    if not run.get("handover_md_sha256") or digest(workspace / "HANDOVER.md") != run["handover_md_sha256"]:
                        raise ValueError("HANDOVER_NOT_READY")
                    handover = {**state, "handover_document": "HANDOVER.md", "handover_sha256": run.get("handover_md_sha256")}
                    # Deterministic, bounded state, with no old conversation or generated summary.
                    self.event(run, "agent.handover", **{"aeion.agent.number": agent})
                    continue
                run["status"] = "passed" if changed and check["failed"] == [] else "failed_acceptance"
                if run["status"] == "passed" and isolated:
                    published = self.work_root / "published"
                    published.mkdir(exist_ok=True, mode=0o755)
                    target = published / (run.get("task_id", "pricing-js-v1") + ".js")
                    temporary = target.with_suffix(".tmp")
                    temporary.write_bytes(source.read_bytes())
                    temporary.chmod(0o644)
                    temporary.replace(target)
                break
            else:
                run["status"] = "handover_limit"
        except Exception as error:
            # Never export arbitrary error strings, provider responses or stderr.
            reason = str(error) if str(error) in FAILURES else "RUN_FAILED"
            run.update(status="failed", failure=reason)
            # Only the exception type and a bounded message: never provider text or a traceback.
            self.event(run, "task.failed", **{"aeion.failure.code": reason,
                                              "aeion.failure.type": type(error).__name__})
        finally:
            root_span.set_attribute("aeion.status", run["status"])
            if run["status"] != "passed" and hasattr(root_span, "set_status"):
                try:
                    from opentelemetry.trace import Status, StatusCode
                except ImportError:
                    # Telemetry is optional: a host without the SDK still records the run.
                    pass
                else:
                    root_span.set_status(
                        Status(StatusCode.ERROR, run.get("failure", run["status"])))
            root_span.end()
            run["ended_ns"] = time.time_ns()
            self._settle(run, reservation)
            self.save(run)

    def simulate(self, run, workspace, agent):
        # Explicit synthetic replay; does not masquerade as a harness/provider run.
        contexts = [120000, 230000, 249999, 250000] if agent == 1 else [6000]
        cumulative = 0
        for value in contexts:
            time.sleep(0.8)
            cumulative += value
            observed = value if run["metric"] == "active_context" else cumulative
            self.event(run, "gen_ai.request", **{"aeion.agent.number": agent,
                       "gen_ai.usage.input_tokens": value, "gen_ai.usage.output_tokens": 100,
                       "aeion.context.observed": observed, "gen_ai.request.model": "synthetic-replay"})
            if observed >= run["limit"]:
                self.prepare_handover(run, workspace, observed)
                self.event(run, "gate.closed", **{"aeion.context.observed": observed})
                return "handover"
            if observed >= max(1, run["limit"] - 20000):
                self.prepare_handover(run, workspace, observed)
        task_id = run.get("task_id", "pricing-js-v1")
        solution = triage.solution(task_id) if run.get("runtime") == TRIAGE else SOLUTIONS[task_id]
        (workspace / artifact_name(run)).write_text(solution)
        return "complete"

    def live(self, run, workspace, handover, *, prompt=None, kind='lab', review_result=None, preparation_result=None):
        prompt = task_contract(run) if prompt is None else prompt
        cost_limit = Decimal(str(run.get('session_cost_limit', max_cost())))
        handover_path = workspace / 'HANDOVER.md' if kind == 'lab' else workspace.parent / 'HANDOVER.md'
        if handover:
            if digest(handover_path) != handover["handover_sha256"]:
                raise ValueError("HANDOVER_NOT_READY")
            prompt += ("\nFresh session. Supervisor-loaded HANDOVER.md:\n" + handover_path.read_text()
                       + "\nPreserved artifact/check state: " + json.dumps(handover))
        instance = f"{run['id']}-{run['agents']}"
        state = {"steps": 0, "done": False, "threshold": False, "peak": 0, "last": 0,
                 "counted_handover": None, "native_md": None, "stop": None}
        accounted = threading.Condition()

        def admission():
            # Runs in the relay before each forward, so the native gate and budget act pre-dispatch.
            if kind != 'lab':
                authorize = getattr(self, 'authorization_check', None)
                try:
                    if not callable(authorize) or not authorize():
                        return 'ATTEMPT_REVOKED'
                except Exception:
                    return 'ATTEMPT_AUTHORITY_UNAVAILABLE'
                limit = factory_work_limit(run, relay.forwarded_count)
                if limit:
                    return limit
            with accounted:
                if not accounted.wait_for(lambda: state["steps"] >= relay.forwarded_count or state["done"], timeout=10):
                    state["stop"] = "USAGE_UNKNOWN"
                    return "USAGE_UNKNOWN"
                if state['stop']:
                    return state['stop']
                last, threshold = state["last"], state["threshold"]
                over_budget = Decimal(run["native_cost_usd"]) > cost_limit
            if last >= max(1, run["limit"] - 20000) and state["native_md"] != last:
                self.prepare_handover(run, workspace, last)
                state["native_md"] = last
            if threshold:
                return "AEION_HANDOVER"
            if over_budget:
                state["stop"] = "BUDGET_STOP"
                return "BUDGET_STOP"
            return None

        def relay_checkpoint(counted, close):
            if kind in {'factory-review', 'factory-prepare'}:
                # These roles have an immutable input and no author snapshot to checkpoint.
                # Keep the relay's context refusal instead of masking it as an unknown error.
                return
            self.prepare_handover(run, workspace, counted, basis="local_tokenizer")
            if close:
                state["counted_handover"] = counted

        key = next(k for k, p in PROFILES.items() if p['model'] == run['model'])
        metadata = model_metadata(key)
        output_limit=run.get('max_output_tokens',4096)
        relay_options = {'api': metadata['api'], 'required_effort': metadata.get('thinking'),
                         'max_output_tokens':output_limit}
        review_effort=run.get('review_thinking_level','medium') if kind=='factory-review' else 'medium'
        if review_effort not in ('low','medium'):
            raise ValueError('REASONING_EFFORT_INVALID')
        if key=='deepseek':
            relay_options['required_reasoning_effort']='low' if review_effort=='low' else 'high'
        if kind != 'lab':
            relay_options.update(prices=metadata, cost_limit=cost_limit - Decimal(run.get('projected_cost_usd', '0')))
        relay = ContextRelay(run["model"], os.environ["OPENCODE_API_KEY"], run["limit"], relay_checkpoint,
                             lambda name, **attrs: self.event(run, name, **attrs), admission=admission, **relay_options)
        runtime = run.get("runtime", "flue-openshell")
        # Only tier 3 tools reach OpenShell; tier 2 tools act on the workspace folder directly.
        bridge = SandboxBridge(self.active_sandbox, check=getattr(self, 'protected_check', None)) if runtime == "flue-openshell" else None
        HARNESS.mkdir(mode=0o700, parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(dir=HARNESS))
        events, empty_env = scratch / "events.ndjson", scratch / "empty.env"
        events.touch(mode=0o600)
        empty_env.touch(mode=0o600)
        # Only loopback credentials scoped to this session; never the Go key or host secrets.
        env = {"PATH": os.environ["PATH"], "HOME": str(scratch), "LANG": "C.UTF-8", "NODE_NO_WARNINGS": "1",
               "AEION_RELAY_URL": relay.url, "AEION_RELAY_TOKEN": relay.token,
               "AEION_MODEL_JSON": json.dumps({**model_metadata(key),'maxOutputTokens':output_limit}), "AEION_EVENTS_FILE": str(events),
               "AEION_CONVERSATION_ID": instance}
        if kind == 'factory-review':
            (scratch / 'review.txt').write_text(prompt)
            env.update(AEION_REVIEW_INPUT=str(scratch / 'review.txt'), AEION_REVIEW_RESULT=str(review_result),
                       AEION_REVIEW_EFFORT=review_effort)
        elif kind == 'factory-prepare':
            (scratch / 'preparation.txt').write_text(prompt)
            env.update(AEION_PREPARATION_INPUT=str(scratch / 'preparation.txt'),
                       AEION_PREPARATION_RESULT=str(preparation_result))
        elif runtime == TRIAGE:
            # Events and labels only; expected answers never leave the supervisor.
            (scratch / "input.json").write_text(triage.agent_input(run["task_id"]))
            env.update(AEION_TRIAGE_INPUT=str(scratch / "input.json"), AEION_RESULT_FILE=str(workspace / triage.ARTIFACT))
        else:
            env["AEION_WORKSPACE"] = SANDBOX_WORKSPACE if self.copies_out(run) else str(workspace)
        if bridge:
            env.update(AEION_BRIDGE_URL=bridge.url, AEION_BRIDGE_TOKEN=bridge.token)
        if kind == 'factory-build':
            env['AEION_FACTORY_BUILD'] = '1'
        entry = ({'factory-review':'src/agents/reviewer.ts', 'factory-prepare':'src/agents/preparer.ts'}
                 .get(kind, AGENTS[runtime]))
        message = ('Review the complete attached frozen_review_packet and submit one verdict.'
                   if kind == 'factory-review' else prompt)
        argv = [str(FLUE / "node_modules/.bin/flue"), "run", entry, "--message", message,
                "--id", instance, "--new", "--json", "--env", str(empty_env)]
        process = None
        try:
            relay.start()
            if bridge:
                bridge.start()
            # stdout carries the model reply and stderr streams conversation text: discard both.
            process = subprocess.Popen(argv, cwd=FLUE, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, start_new_session=True)
            self.event(run, "process.started", **{"aeion.process.pid": process.pid, "aeion.agent.number": run["agents"]})
            deadline = time.monotonic() + min(900, int(run.get('agent_timeout_seconds', AGENT_TIMEOUT_SECONDS)))
            buffer, cumulative, conversation, final, outcome = b"", 0, None, False, None
            request_started_ns = time.time_ns()
            with events.open("rb") as stream:
                while True:
                    block = stream.read(65536)
                    if not block:
                        if process.poll() is not None:
                            block = stream.read(65536)  # Final drain: every write precedes process exit.
                            if not block:
                                break
                        elif time.monotonic() >= deadline:
                            break
                        else:
                            time.sleep(0.05)
                            continue
                    buffer += block
                    if len(buffer) > 1048576:
                        raise ValueError("CLI_PROTOCOL_ERROR")
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        try:
                            record = loads(line)
                        except (ValueError, UnicodeError):
                            raise ValueError("CLI_PROTOCOL_ERROR") from None
                        event_kind = record.get("type") if isinstance(record, dict) else None
                        if event_kind == "step_start":
                            request_started_ns = time.time_ns()
                            self.event(run, "model.step.started", **{"aeion.agent.number": run["agents"]})
                        elif event_kind == "tool":
                            if record.get("name") != "other" and record.get("status") in {"completed", "error"}:
                                self.event(run, "tool.finished", **{"aeion.tool.name": record["name"], "aeion.tool.status": record["status"]})
                        elif event_kind == "compaction":
                            raise ValueError("HARNESS_COMPACTION")
                        elif event_kind == "settled":
                            outcome = record.get("outcome")
                        elif event_kind == "step_finish":
                            if record.get("instance") != instance:
                                raise ValueError("CLI_PROTOCOL_ERROR")
                            if conversation is None:
                                conversation = record.get("conversation")
                                if not isinstance(conversation, str) or conversation in run["sessions"]:
                                    raise ValueError("CLI_PROTOCOL_ERROR")
                                run["sessions"].append(conversation)
                            elif record.get("conversation") != conversation:
                                raise ValueError("CLI_PROTOCOL_ERROR")
                            if record.get("error") is True:
                                continue  # A refused or failed request has no billable response to account.
                            run['last_finish_reason']=record.get('finish') if record.get('finish') in {'stop','toolUse','length','error','aborted'} else 'other'
                            usage = native_usage(record.get("usage"))
                            cumulative += usage["input"]
                            observed = gate_value(usage, cumulative, run["metric"])
                            request_index = state['steps']
                            request_bound = relay.forwarded_counts[request_index] if request_index < len(relay.forwarded_counts) else None
                            if usage['input'] + usage['output'] > 300000:
                                raise ValueError('PROVIDER_CONTEXT_VIOLATION')
                            if (relay.context_basis == 'local_tokenizer' and not run['model'].startswith('fixture/')
                                    and (request_bound is None or usage['input'] > request_bound + 20000)):
                                raise ValueError('CONTEXT_ACCOUNTING_MISMATCH')
                            with accounted:
                                run["native_cost_usd"] = str(Decimal(run["native_cost_usd"]) + usage["cost"])
                                state["last"], state["peak"] = observed, max(state["peak"], observed)
                                if observed >= run["limit"]:
                                    state["threshold"] = True
                                state["steps"] += 1
                                accounted.notify_all()
                            self.event(run, "gen_ai.request", **{"aeion.agent.number": run["agents"],
                                       "gen_ai.request.model": run["model"], "gen_ai.usage.input_tokens": usage["input"],
                                       "gen_ai.usage.output_tokens": usage["output"], "aeion.context.observed": observed,
                                       "aeion.cost.estimated_usd": float(usage["cost"]),
                                       "aeion.step.elapsed_ms": round((time.time_ns() - request_started_ns) / 1000000, 2)})
                            final = record.get("finish") == "stop"
            with accounted:
                state["done"] = True
                accounted.notify_all()
            if state["counted_handover"] is not None:
                self.event(run, "gate.closed", **{"aeion.context.counted": state["counted_handover"]})
                return "handover"
            if state["threshold"]:
                if state["native_md"] != state["peak"]:
                    self.prepare_handover(run, workspace, state["peak"])
                self.event(run, "gate.closed", **{"aeion.context.observed": state["peak"]})
                return "handover"
            if process.poll() is None:
                raise ValueError("AGENT_TIMEOUT")
            if state["stop"] or Decimal(run["native_cost_usd"]) > cost_limit:
                raise ValueError(state["stop"] or "BUDGET_STOP")
            if relay.last_error_code:
                raise ValueError(relay.last_error_code)
            if run.get('last_finish_reason')=='length':
                raise ValueError('OUTPUT_LIMIT')
            if process.returncode != 0 or outcome != "completed" or not state["steps"] or not final:
                raise ValueError("CLI_FAILED")
            return "complete"
        finally:
            relay.closed = True
            with accounted:
                state["done"] = True
                accounted.notify_all()
            if process is not None:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
                self.event(run, "process.retired", **{"aeion.process.pid": process.pid})
            relay.close()
            if bridge:
                bridge.close()
            shutil.rmtree(scratch, ignore_errors=True)
            run["usage_complete"] = usage_is_complete(
                state["steps"], relay.forwarded_count, relay.last_error_code)
            run.setdefault('provider_usages', []).extend(relay.reported_usage)
            run['provider_accounting_complete'] = relay.accounting_complete
            run['forwarded_count'] = run.get('forwarded_count', 0) + relay.forwarded_count
            run['projected_cost_usd'] = str(Decimal(run.get('projected_cost_usd', '0')) + relay.projected_cost)
