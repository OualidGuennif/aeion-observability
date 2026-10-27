"""Real pinned Flue/Pi harness, local fake inference only: one scripted run per execution tier.

Tier 3 proves the pre-dispatch barrier and handover in the sandbox, tier 2 the strict skill and
src/-only file tools, tier 1 the in-memory shell and validated submission. Default: tier 2 and 3
checks run in a real OpenShell sandbox and success of all three writes the qualification marker
bound to the protocol hash. `--local-sandbox` exercises the same chain with a host stand-in for
development; it never writes the marker.
"""
import argparse
from contextlib import nullcontext
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS.parent / "app"))
sys.path.insert(0, str(TESTS))
from local_sandbox import LocalSandbox
import runner
from relay import ContextRelay
from scenarios import SCENARIOS, SOLUTIONS
from settings import DATA, FLUE, HARNESS, WORK
import triage

requests = []
workspace = None
script = None
PARTIAL = 'export function totalCents(items, shippingCents = 0) { return shippingCents; }\n'
TRIAGE_TASK = "webhook-triage-v1"


def tool_text(body):
    content = next(m for m in reversed(body["messages"]) if m["role"] == "tool")["content"]
    return content if isinstance(content, str) else "".join(part.get("text", "") for part in content)


def tool_names(body):
    return {tool["function"]["name"] for tool in body.get("tools", [])}


def coding(number, body):
    # Tier 3: real tools in the sandbox, MD before the counted close at 250k, then a fresh session.
    if number == 1:
        return ("glob", {"pattern": "*.js", "path": "src"})
    if number == 2:
        assert "pricing.js" in tool_text(body), "Glob must run inside the sandbox workspace"
        return ("grep", {"pattern": "export function", "path": "src"})
    if number == 3:
        assert "export function totalCents" in tool_text(body), "Grep must run inside the sandbox workspace"
        return ("read", {"path": "src/pricing.js"})
    if number == 4:
        return ("write", {"path": "src/pricing.js", "content": PARTIAL})
    if number == 5:
        assert (workspace / "src/pricing.js").read_text() == PARTIAL, "Partial work must survive the handover"
        text = (workspace / "HANDOVER.md").read_text()
        assert "## Independent verification" in text, "MD must precede the fresh session"
        dumped = json.dumps(body["messages"])
        assert "Supervisor-loaded HANDOVER.md" in dumped and "previous_agent" in dumped
        assert sum(m["role"] == "assistant" for m in body["messages"]) == 0, "The successor starts with no transcript"
        return ("write", {"path": "src/pricing.js", "content": SOLUTIONS["pricing-js-v1"]})
    return None


def local(number, body):
    # Tier 2: the strict skill loads, file tools only, and writes outside src/ are refused.
    if number == 1:
        names = tool_names(body)
        assert {"read", "write", "edit", "activate_skill"} <= names, names
        assert not names & {"bash", "grep", "glob"}, "Tier 2 offers no shell or exec-backed tools"
        return ("activate_skill", {"name": "local-change"})
    if number == 2:
        assert "Follow these steps in order" in tool_text(body), "The strict skill must load"
        return ("read", {"path": "src/pricing.js"})
    if number == 3:
        assert "not implemented" in tool_text(body), "Read must see the run workspace"
        return ("write", {"path": "package.json", "content": "{}\n"})
    if number == 4:
        assert "Only src/ is writable" in tool_text(body), "The refusal must reach the model"
        assert not (workspace / "package.json").exists(), "Refused writes leave no file"
        return ("write", {"path": "src/pricing.js", "content": SOLUTIONS["pricing-js-v1"]})
    return None


def triage_run(number, body):
    # Tier 1: an emulated shell over memory with no host files; only submit_triage leaves it.
    results = json.loads(triage.solution(TRIAGE_TASK))["results"]
    if number == 1:
        assert {"bash", "submit_triage"} <= tool_names(body), tool_names(body)
        return ("bash", {"command": "jq length /data/events.json"})
    if number == 2:
        assert tool_text(body).strip() == "8", "The shell must see the supplied events"
        return ("bash", {"command": "cat /etc/passwd"})
    if number == 3:
        text = tool_text(body)
        assert "No such file" in text and "root:" not in text, "Host files must stay invisible"
        return ("submit_triage", {"results": results[:-1]})
    if number == 4:
        assert "Missing results for: evt-008" in tool_text(body), "Incomplete submissions must be refused"
        assert json.loads((workspace / triage.ARTIFACT).read_text()) == json.loads(triage.EMPTY), \
            "A refused submission writes nothing"
        return ("submit_triage", {"results": results})
    if number == 5:
        assert "Recorded 8 results." in tool_text(body)
    return None


# runtime: (task, script, requests, agents, check total)
RUNS = {"flue-openshell": ("pricing-js-v1", coding, 6, 2, 12), "flue-local": ("pricing-js-v1", local, 5, 1, 12),
        "flue-just-bash": (TRIAGE_TASK, triage_run, 5, 1, 8)}


class Inference(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_POST(self):
        assert self.headers.get("Authorization") == "Bearer synthetic", "Relay must replace the harness token"
        assert self.headers.get("User-Agent", "").startswith("pi/") and self.headers.get("x-opencode-session"), \
            "Validated Go client identity must survive the relay"
        assert not any(h.lower().startswith("x-stainless") for h in self.headers), "Only identity headers are forwarded"
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert {m["role"] for m in body["messages"]} <= {"system", "user", "assistant", "tool"}, "No developer role"
        requests.append(time.monotonic())
        number = len(requests)
        if number > RUNS[script][2]:
            self.send_error(500)
            return
        call = RUNS[script][1](number, body)
        if call:
            delta = {"role": "assistant", "tool_calls": [{"index": 0, "id": f"call_{number}", "type": "function",
                     "function": {"name": call[0], "arguments": json.dumps(call[1])}}]}
        else:
            delta = {"role": "assistant", "content": "Done."}
        count = 250000 if script == "flue-openshell" and number == 4 else 4000
        chunks = [
            {"choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
            {"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls" if call else "stop"}]},
            {"choices": [], "usage": {"prompt_tokens": count, "completion_tokens": 100, "total_tokens": count + 100}},
        ]
        out = "".join("data: " + json.dumps({"id": "fixture", "model": "mock", "object": "chat.completion.chunk", **c}) + "\n\n"
                      for c in chunks) + "data: [DONE]\n\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(out.encode())))
        self.end_headers()
        self.wfile.write(out.encode())


class NoExport:
    def begin(self, run):
        run.update(trace_id="1" * 32, root_span_id="1" * 16)
        return self

    def emit(self, *_args, **_kwargs):
        pass

    def set_attribute(self, *_args):
        pass

    def end(self):
        pass


def qualify(runtime, root, local_sandbox):
    global script, workspace
    task_id, _, request_count, agents, total = RUNS[runtime]
    script, workspace = runtime, root / runtime / "workspace"
    requests.clear()
    run = {"id": runtime, "synthetic": False, "status": "running", "started_ns": time.time_ns(), "runtime": runtime,
           "task_id": task_id, "model": "fixture/mock", "limit": 250000, "metric": "active_context",
           "native_cost_usd": "0", "events": [], "sessions": [], "agents": 0}
    with patch("runner.Sandbox", LocalSandbox) if local_sandbox else nullcontext():
        runner.Runner(NoExport(), lambda _run: None, root).run(run)
    names = [e["name"] for e in run["events"]]
    summary = {key: run.get(key) for key in ("runtime", "status", "failure", "agents", "check", "changed", "usage_complete")}
    summary.update(request_count=len(requests), fresh_sessions=len(set(run["sessions"])),
                   sandbox_mode="local-stand-in" if local_sandbox else "openshell")
    print(json.dumps(summary))
    assert run["status"] == "passed" and run["check"] == {"passed": total, "failed": [], "total": total}, summary
    assert len(requests) == request_count and run["agents"] == agents == len(set(run["sessions"])), summary
    assert run["usage_complete"] is True, summary
    assert "HARNESS_COMPACTION" not in json.dumps(run["events"])
    contract = runner.task_contract(run)
    assert contract[:60] not in json.dumps(run["events"]) and "Supervisor-loaded" not in json.dumps(run["events"]), \
        "Prompt text must never enter events"
    if runtime == "flue-openshell":
        assert any(e["name"] == "gate.closed" and e.get("aeion.context.observed") == 250000 for e in run["events"])
        assert names.index("handover.prepared") < names.index("context.refused") < names.index("gate.closed") \
            < names.index("agent.handover")
    if runtime == "flue-just-bash":
        assert not any(name.startswith("sandbox.") for name in names), "Tier 1 never creates an OpenShell sandbox"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-sandbox", action="store_true", help="Development only: no isolation, no marker")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Inference)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    run_db = FLUE / "node_modules/.cache/flue/run.db"
    WORK.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Under WORK: sandboxes can only mount subpaths of the labeled work volume.
    with tempfile.TemporaryDirectory(prefix=".qualify-flue-", dir=WORK) as folder:
        root = Path(folder)

        class FixtureCounter:
            def count(self, _payload):
                return 4000

        def local_relay(model, key, limit, checkpoint, event, admission=None):
            return ContextRelay(model, key, limit, checkpoint, event, admission=admission,
                                upstream=f"http://127.0.0.1:{server.server_port}/v1/chat/completions", counter=FixtureCounter())

        profile = {"model": "fixture/mock", "name": "Fixture", "context": 1000000, "input": 0, "output": 0, "cache_read": 0}
        with patch.dict(os.environ, {"OPENCODE_API_KEY": "synthetic", "DEMO_MAX_COST_USD": "0", "PLAYGROUND_URL": ""}), \
                patch.dict(runner.PROFILES, {"fixture": profile}), patch("runner.ContextRelay", side_effect=local_relay):
            for runtime in RUNS:
                qualify(runtime, root, args.local_sandbox)
        assert not run_db.exists(), "Conversations must stay in memory"
        assert not HARNESS.exists() or not any(HARNESS.iterdir()), "Harness scratch must be removed"
    server.shutdown()
    if not args.local_sandbox:
        from sandbox import protocol_hash
        DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
        marker = DATA / "cli-qualification.json"
        temporary = marker.with_suffix(".tmp")
        temporary.write_text(json.dumps({"protocol_sha256": protocol_hash(), "expires_ns": time.time_ns() + 86400000000000}))
        temporary.chmod(0o600)
        temporary.replace(marker)


if __name__ == "__main__":
    main()
