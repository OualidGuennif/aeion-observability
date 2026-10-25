"""Single-task demo supervisor. Agent history and raw CLI output are disposable."""
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import tempfile
import time
import urllib.request
import threading
from decimal import Decimal

from policy import gate_value, native_usage
from relay import ContextRelay

BASE = Path(__file__).resolve().parent.parent
AGENT_UID = 10001
TASK = (
    "Implement JavaScript export function totalCents(items, shippingCents=0) in src/pricing.js. "
    "items is an array of [priceCents, quantity] pairs. Sum price*quantity plus shipping. "
    "All numbers and the result must be nonnegative safe integers; reject invalid values, "
    "malformed pairs and overflow with TypeError. Keep the interface. Edit only src/pricing.js. "
    "Do not add imports, files or tests. The supervisor runs immutable Deno checks after you stop."
)
SOLUTION = '''export function totalCents(items, shippingCents = 0) {
  const valid = (n) => Number.isSafeInteger(n) && n >= 0;
  if (!Array.isArray(items) || !valid(shippingCents)) throw new TypeError("invalid input");
  let total = shippingCents;
  for (const pair of items) {
    if (!Array.isArray(pair) || pair.length !== 2 || !pair.every(valid)) throw new TypeError("invalid item");
    total += pair[0] * pair[1];
    if (!valid(total)) throw new TypeError("overflow");
  }
  return total;
}
'''



def digest(path):
    # Never follow an agent-created symlink, read a device or accept a giant artifact.
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32768:
        raise ValueError("INVALID_ARTIFACT")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def acceptance(workspace):
    path = workspace / "src/pricing.js"
    digest(path)
    # Agent code runs as an unprivileged user with a minimal environment; not as the supervisor.
    result = subprocess.run(
        ["deno", "run", "--no-config", "--no-npm", "--no-remote", "--no-prompt",
         "--allow-read=" + str(path), str(BASE / "fixtures/verify.js"), str(path)],
        capture_output=True, timeout=10, env={"PATH": "/usr/local/bin:/usr/bin:/bin", "DENO_DIR": "/tmp/deno-checks"},
        user=AGENT_UID, group=AGENT_UID, extra_groups=[],
    )
    if len(result.stdout) > 4096:
        raise ValueError("INVALID_CHECK_OUTPUT")
    try:
        check = json.loads(result.stdout)
        if set(check) != {"passed", "failed", "total"} or type(check["passed"]) is not int:
            raise ValueError
        if not isinstance(check["failed"], list) or any(not isinstance(v, str) or len(v) > 40 for v in check["failed"]):
            raise ValueError
        if (result.returncode == 0) != (check == {"passed": 12, "failed": [], "total": 12}):
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("INVALID_CHECK_OUTPUT") from None
    return check


def config(model):
    # No auto compaction, hidden model calls, subagents, shell or outside-workspace access.
    return {
        "$schema": "https://opencode.ai/config.json", "model": model, "small_model": model,
        "autoupdate": False, "share": "disabled", "enabled_providers": ["opencode-go"],
        "plugin": ["file:///opt/demo/context-gate.mjs"],
        "compaction": {"auto": False, "prune": False},
        "permission": {
            "*": "deny", "read": {"*": "deny", "src/*": "allow", "src/**": "allow", "HANDOVER.md": "allow"},
            "edit": {"*": "deny", "src/pricing.js": "allow"},
            "glob": "allow", "grep": "allow", "list": "allow", "todowrite": "allow",
        },
        "agent": {
            "build": {"steps": 12}, "title": {"disable": True},
            "summary": {"disable": True}, "compaction": {"disable": True},
        },
    }


def terminate(process):
    # Kill the entire process group, then reap it before any successor is admitted.
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=3)
    except ProcessLookupError:
        process.wait(timeout=3)
    finally:
        # npm's launcher can exit before its CLI child; always close the residual group.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


class Runner:
    def __init__(self, telemetry, save, work_root=Path("/work"), memory=None, audit=None):
        self.telemetry, self.save, self.work_root = telemetry, save, work_root
        self.memory = memory
        self.audit = audit
        self.event_lock = threading.RLock()

    def event(self, run, name, **attrs):
        # The allowlist is mirrored by the Collector, never copy a CLI event into telemetry.
        with self.event_lock:
            sequence = len(run["events"]) + 1
            event = {"name": name, "id": f"{run['id']}:{sequence}", "sequence": sequence,
                     "time_unix_ns": time.time_ns(), "trace_id": run["trace_id"], "span_id": run["root_span_id"],
                     "severity": "WARN" if name in {"gate.closed", "task.failed", "context.refused"} else "INFO", **attrs}
            if self.audit:
                self.audit.record(run, event)
            run["events"].append(event)
            self.telemetry.emit(run, name, **attrs, **{"aeion.event.id": event["id"], "aeion.event.sequence": sequence})
            self.save(run)

    def prepare_handover(self, run, workspace, observed, basis="native_report"):
        check = acceptance(workspace)
        source_hash = digest(workspace / "src/pricing.js")
        markdown = (
            "# AEion agent handover\n\n"
            f"Task: pricing-js-v1\nAgent: {run['agents']}\n"
            f"Context ({basis}, {run['metric']}): {observed}\nGate: {run['limit']} tokens\nHard admission budget: 300000 tokens\n\n"
            "## Objective\n\n" + TASK + "\n\n"
            f"## Preserved artifact\n\n- File: `src/pricing.js`\n- SHA-256: `{source_hash}`\n\n"
            f"## Independent verification\n\n- Passed: {check['passed']}/{check['total']}\n"
            "- Remaining checks: " + (", ".join(check["failed"]) or "none") + "\n\n"
            "## Next action\n\nRead this document and the preserved source. Complete or verify the implementation; "
            "the supervisor runs immutable Deno checks and probes the Hono API. Edit only src/pricing.js. "
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

    def run(self, run):
        root_span = self.telemetry.begin(run)
        root = self.work_root / run["id"]
        workspace = root / "workspace"
        source = workspace / "src/pricing.js"
        try:
            root.mkdir(mode=0o711)
            workspace.mkdir(mode=0o755)
            source.parent.mkdir(mode=0o755)
            shutil.copyfile(BASE / "fixtures/pricing.js", source)
            os.chown(source.parent, AGENT_UID, AGENT_UID)
            os.chown(source, AGENT_UID, AGENT_UID)
            subprocess.run(["git", "init", "-q", str(workspace)], check=True, capture_output=True)
            original = digest(source)
            handover = None
            for agent in range(1, 4):
                run["agents"] = agent
                self.event(run, "agent.started", **{"aeion.agent.number": agent})
                outcome = self.simulate(run, workspace, agent) if run["synthetic"] else self.live(run, root, workspace, handover)
                check = acceptance(workspace)
                changed = digest(source) != original
                run.update(check=check, artifact_sha256=digest(source), changed=changed)
                self.event(run, "artifact.checked", **{"aeion.check.passed": check["passed"], "aeion.artifact.changed": changed})
                state = {"task": "pricing-js-v1", "previous_agent": agent,
                         "artifact": "src/pricing.js", "sha256": digest(source), "check": check}
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
                if run["status"] == "passed":
                    published = self.work_root / "published"
                    published.mkdir(exist_ok=True, mode=0o755)
                    target = published / "pricing.js"
                    temporary = published / "pricing.tmp"
                    temporary.write_bytes(source.read_bytes())
                    temporary.chmod(0o644)
                    temporary.replace(target)
                    self.probe(run)
                break
            else:
                run["status"] = "handover_limit"
        except Exception as error:
            # Never export arbitrary error strings, provider responses or stderr.
            allowed = {"USAGE_UNKNOWN", "COST_UNKNOWN", "INVALID_ARTIFACT", "INVALID_CHECK_OUTPUT",
                       "PROVIDER_CONTEXT_VIOLATION", "CONTEXT_ACCOUNTING_MISMATCH", "CONTEXT_UNKNOWN", "PROVIDER_REJECTED", "CLI_CLIENT_REQUIRED", "GO_SUBSCRIPTION_REQUIRED", "MODEL_DISABLED", "PROVIDER_ERROR", "CLI_FAILED", "CLI_PROTOCOL_ERROR", "AGENT_TIMEOUT", "BUDGET_STOP", "STEP_LIMIT", "APP_PROBE_FAILED", "HANDOVER_NOT_READY", "INSUFFICIENT_FUNDS", "GO_REGION_REQUIRED", "QUOTA_STOP", "AUTH_ERROR"}
            reason = str(error) if str(error) in allowed else "RUN_FAILED"
            run.update(status="failed", failure=reason)
            self.event(run, "task.failed", **{"aeion.failure.code": reason})
        finally:
            root_span.set_attribute("aeion.status", run["status"])
            if run["status"] != "passed" and hasattr(root_span, "set_status"):
                from opentelemetry.trace import Status, StatusCode
                root_span.set_status(Status(StatusCode.ERROR, run.get("failure", run["status"])))
            root_span.end()
            run["ended_ns"] = time.time_ns()
            self.save(run)

    def probe(self, run):
        endpoint = os.environ.get("PLAYGROUND_URL")
        if not endpoint:
            return  # local CLI fixture has no application service
        started = time.monotonic()
        # Propagate the task trace to Deno's native HTTP instrumentation.
        header = f"00-{run['trace_id']}-{run['root_span_id']}-01"
        request = urllib.request.Request(endpoint + "/api/quote", data=b'{"items":[[125,2]],"shippingCents":75}',
                                         headers={"Content-Type": "application/json", "traceparent": header})
        with urllib.request.urlopen(request, timeout=10) as response:
            if json.loads(response.read(4096)) != {"totalCents": 325, "currency": "EUR"}:
                raise ValueError("APP_PROBE_FAILED")
        run["app_probe_ms"] = round((time.monotonic() - started) * 1000, 2)
        self.event(run, "app.verified", **{"aeion.app.probe_ms": run["app_probe_ms"]})

    def simulate(self, run, workspace, agent):
        # Explicit synthetic replay; does not masquerade as an OpenCode/provider run.
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
        (workspace / "src/pricing.js").write_text(SOLUTION)
        return "complete"

    def live(self, run, root, workspace, handover):
        prompt = TASK
        if handover:
            if digest(workspace / "HANDOVER.md") != handover["handover_sha256"]:
                raise ValueError("HANDOVER_NOT_READY")
            prompt += ("\nFresh session. Supervisor-loaded HANDOVER.md:\n" + (workspace / "HANDOVER.md").read_text()
                       + "\nPreserved artifact/check state: " + json.dumps(handover))
        runtime = Path(tempfile.mkdtemp(prefix="runtime-", dir=root))
        runtime.chmod(0o700)
        os.chown(runtime, AGENT_UID, AGENT_UID)
        gate_file = runtime / "gate.json"
        checkpoint_request = runtime / "checkpoint-request.json"
        checkpoint_ack = runtime / "checkpoint-ack.json"
        def relay_checkpoint(counted, close):
            self.prepare_handover(run, workspace, counted, basis="local_tokenizer")
            if close:
                marker = runtime / "gate.tmp"
                marker.write_text(json.dumps({"action": "handover", "observed": counted, "metric": run["metric"],
                                               "limit": run["limit"], "basis": "local_tokenizer"}))
                marker.replace(gate_file)
        try:
            relay = ContextRelay(run["model"], os.environ["OPENCODE_API_KEY"], run["limit"], relay_checkpoint,
                                 lambda name, **attrs: self.event(run, name, **attrs))
        except Exception:
            shutil.rmtree(runtime)
            raise
        cfg = config(run["model"])
        provider = run["model"].split("/", 1)[0]
        cfg.setdefault("provider", {}).setdefault(provider, {}).setdefault("options", {})["baseURL"] = relay.url
        env = {"PATH": os.environ["PATH"], "HOME": str(runtime), "CI": "true",
               "OPENCODE_DISABLE_DEFAULT_PLUGINS": "true", "OPENCODE_DISABLE_EXTERNAL_SKILLS": "true",
               "OPENCODE_DISABLE_CLAUDE_CODE": "true", "OPENCODE_DISABLE_LSP_DOWNLOAD": "true",
               "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "safe.directory", "GIT_CONFIG_VALUE_0": str(workspace),
               "OPENCODE_API_KEY": "aeion-gate-closed",
               "AEION_OPENCODE_KEY": relay.token,
               "OPENCODE_CONFIG_CONTENT": json.dumps(cfg),
               "AEION_CONTEXT_LIMIT": str(run["limit"]), "AEION_CONTEXT_METRIC": run["metric"],
               "AEION_MAX_COST_USD": str(max(Decimal(0), Decimal(os.environ.get("DEMO_MAX_COST_USD", "0.10")) - Decimal(run["native_cost_usd"]))),
               "AEION_GATE_FILE": str(gate_file)}
        env.update(AEION_CHECKPOINT_REQUEST=str(checkpoint_request), AEION_CHECKPOINT_ACK=str(checkpoint_ack))
        for key in ("DATA", "CONFIG", "STATE", "CACHE"):
            env[f"XDG_{key}_HOME"] = str(runtime / key.lower())
        argv = ["opencode", "run", "--agent", "build", "--model", run["model"], "--format", "json",
                "--title", "aeion-demo", "--auto", "--dir", str(workspace), prompt]
        process = None
        steps = 0
        def read_gate():
            if not gate_file.exists():
                return None
            if gate_file.is_symlink() or gate_file.stat().st_size > 1024:
                raise ValueError("USAGE_UNKNOWN")
            result = json.loads(gate_file.read_text())
            if result.get("action") == "stop" and result.get("reason") in {"STEP_LIMIT", "BUDGET_STOP", "HANDOVER_NOT_READY"}:
                raise ValueError(result["reason"])
            if (result.get("action") == "handover" and result.get("metric") == run["metric"]
                    and result.get("limit") == run["limit"] and type(result.get("observed")) is int
                    and result["observed"] >= run["limit"]):
                self.event(run, "gate.closed", **{"aeion.context.observed": result["observed"]})
                return "handover"
            raise ValueError("USAGE_UNKNOWN")
        try:
            relay.start()
            process = subprocess.Popen(argv, cwd=workspace, env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                       start_new_session=True, user=AGENT_UID, group=AGENT_UID, extra_groups=[])
            self.event(run, "process.started", **{"aeion.process.pid": process.pid, "aeion.agent.number": run["agents"]})
            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)
            deadline = time.monotonic() + 180
            buffer = b""
            steps, cumulative, session, final = 0, 0, None, False
            request_started_ns = time.time_ns()
            threshold_reached = False
            observed_peak = 0
            last_checkpoint = None
            while time.monotonic() < deadline:
                if checkpoint_request.exists():
                    if checkpoint_request.is_symlink() or checkpoint_request.stat().st_size > 1024:
                        raise ValueError("HANDOVER_NOT_READY")
                    checkpoint = json.loads(checkpoint_request.read_text())
                    if (checkpoint.get("id") != last_checkpoint and checkpoint.get("metric") == run["metric"]
                            and checkpoint.get("limit") == run["limit"] and type(checkpoint.get("observed")) is int):
                        md_hash = self.prepare_handover(run, workspace, checkpoint["observed"])
                        ack = runtime / "ack.tmp"
                        ack.write_text(json.dumps({"id": checkpoint["id"], "ready": True, "sha256": md_hash}))
                        ack.chmod(0o644)
                        ack.replace(checkpoint_ack)
                        self.event(run, "handover.acknowledged", **{"aeion.context.observed": checkpoint["observed"]})
                        last_checkpoint = checkpoint["id"]
                if read_gate():
                    return "handover"
                ready = selector.select(timeout=0.1)
                if not ready:
                    if process.poll() is not None:
                        break
                    continue
                block = os.read(process.stdout.fileno(), 65536)
                if not block:
                    break
                buffer += block
                if len(buffer) > 1048576:
                    raise ValueError("CLI_PROTOCOL_ERROR")
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    try:
                        event = json.loads(line)
                    except (ValueError, UnicodeError):
                        raise ValueError("CLI_PROTOCOL_ERROR") from None
                    if event.get("type") == "error":
                        if read_gate():
                            return "handover"
                        if relay.last_error_code:
                            raise ValueError(relay.last_error_code)
                        message = json.dumps(event.get("error", {})).lower()
                        for needles, code in [(("insufficient", "funds"), "INSUFFICIENT_FUNDS"),
                                               (("global", "region"), "GO_REGION_REQUIRED"),
                                               (("quota",), "QUOTA_STOP"), (("unauthorized",), "AUTH_ERROR")]:
                            if all(needle in message for needle in needles):
                                raise ValueError(code)
                        raise ValueError("PROVIDER_ERROR")
                    if event.get("type") != "step_finish":
                        if event.get("type") == "step_start":
                            request_started_ns = time.time_ns()
                            self.event(run, "model.step.started", **{"aeion.agent.number": run["agents"]})
                        elif event.get("type") == "tool_use":
                            part = event.get("part", {})
                            tool = part.get("tool")
                            status = part.get("state", {}).get("status")
                            if tool in {"read", "write", "edit", "apply_patch", "glob", "grep", "list", "todowrite"} and status in {"completed", "error"}:
                                self.event(run, "tool.finished", **{"aeion.tool.name": tool, "aeion.tool.status": status})
                        continue
                    if not session:
                        session = event.get("sessionID")
                        if not isinstance(session, str) or session in run["sessions"]:
                            raise ValueError("CLI_PROTOCOL_ERROR")
                        run["sessions"].append(session)
                    if event.get("sessionID") != session:
                        raise ValueError("CLI_PROTOCOL_ERROR")
                    usage = native_usage(event["part"])
                    steps += 1
                    cumulative += usage["input"]
                    run["native_cost_usd"] = str(Decimal(run["native_cost_usd"]) + usage["cost"])
                    observed = gate_value(usage, cumulative, run["metric"])
                    observed_peak = max(observed_peak, observed)
                    self.event(run, "gen_ai.request", **{"aeion.agent.number": run["agents"],
                               "gen_ai.request.model": run["model"], "gen_ai.usage.input_tokens": usage["input"],
                               "gen_ai.usage.output_tokens": usage["output"], "aeion.context.observed": observed,
                               "aeion.cost.estimated_usd": float(usage["cost"]),
                               "aeion.step.elapsed_ms": round((time.time_ns() - request_started_ns) / 1000000, 2)})
                    if usage["input"] + usage["output"] > 300000:
                        self.event(run, "context.violation", **{"aeion.failure.code": "PROVIDER_CONTEXT_VIOLATION"})
                        raise ValueError("PROVIDER_CONTEXT_VIOLATION")
                    if not run["model"].startswith("fixture/") and (relay.last_count is None or usage["input"] > relay.last_count + 20000):
                        raise ValueError("CONTEXT_ACCOUNTING_MISMATCH")
                    if Decimal(run["native_cost_usd"]) > Decimal(os.environ.get("DEMO_MAX_COST_USD", "0")):
                        raise ValueError("BUDGET_STOP")
                    if observed >= run["limit"]:
                        threshold_reached = True
                        relay.closed = True
                    final = event["part"].get("reason") == "stop"
            if read_gate():
                return "handover"
            if threshold_reached:
                self.prepare_handover(run, workspace, observed_peak)
                self.event(run, "gate.closed", **{"aeion.context.observed": observed_peak})
                return "handover"
            if time.monotonic() >= deadline:
                raise ValueError("AGENT_TIMEOUT")
            if process.wait(timeout=3) != 0 or not steps or not final:
                raise ValueError("CLI_FAILED")
            return "complete"
        finally:
            if process is not None:
                terminate(process)
                process.stdout.close()
                self.event(run, "process.retired", **{"aeion.process.pid": process.pid})
            relay.close()
            run["usage_complete"] = run.get("usage_complete", True) and steps == relay.forwarded_count
            # Remove only this retired runtime after reaping; preserve task files.
            shutil.rmtree(runtime)
            self.event(run, "session.wiped", **{"aeion.agent.number": run["agents"]})
