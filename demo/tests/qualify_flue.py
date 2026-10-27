"""Real pinned Flue/Pi harness, local fake inference only: prove the pre-dispatch barrier.

Default: tools and checks run in a real OpenShell sandbox and success writes the qualification
marker bound to the protocol hash. `--local-sandbox` exercises the same chain with a host stand-in
for development; it never writes the marker.
"""
import argparse
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
import runner
from relay import ContextRelay
from scenarios import SCENARIOS, SOLUTIONS
from settings import DATA, FLUE, HARNESS, WORK

requests = []
workspace = None
PARTIAL = 'export function totalCents(items, shippingCents = 0) { return shippingCents; }\n'


def tool_text(body):
    return json.dumps(next(m for m in reversed(body["messages"]) if m["role"] == "tool")["content"])


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
        if number > 6:
            self.send_error(500)
            return
        call = None
        if number == 1:
            call = ("glob", {"pattern": "*.js", "path": "src"})
        elif number == 2:
            assert "pricing.js" in tool_text(body), "Glob must run inside the sandbox workspace"
            call = ("grep", {"pattern": "export function", "path": "src"})
        elif number == 3:
            assert "export function totalCents" in tool_text(body), "Grep must run inside the sandbox workspace"
            call = ("read", {"path": "src/pricing.js"})
        elif number == 4:
            call = ("write", {"path": "src/pricing.js", "content": PARTIAL})
        elif number == 5:
            assert (workspace / "src/pricing.js").read_text() == PARTIAL, "Partial work must survive the handover"
            text = (workspace / "HANDOVER.md").read_text()
            assert "## Independent verification" in text, "MD must precede the fresh session"
            dumped = json.dumps(body["messages"])
            assert "Supervisor-loaded HANDOVER.md" in dumped and "previous_agent" in dumped
            assert sum(m["role"] == "assistant" for m in body["messages"]) == 0, "The successor starts with no transcript"
            call = ("write", {"path": "src/pricing.js", "content": SOLUTIONS["pricing-js-v1"]})
        if call:
            delta = {"role": "assistant", "tool_calls": [{"index": 0, "id": f"call_{number}", "type": "function",
                     "function": {"name": call[0], "arguments": json.dumps(call[1])}}]}
        else:
            delta = {"role": "assistant", "content": "Done."}
        count = 250000 if number == 4 else 4000
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


def main():
    global workspace
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
        workspace = root / "fixture/workspace"

        class FixtureCounter:
            def count(self, _payload):
                return 4000

        def local_relay(model, key, limit, checkpoint, event, admission=None):
            return ContextRelay(model, key, limit, checkpoint, event, admission=admission,
                                upstream=f"http://127.0.0.1:{server.server_port}/v1/chat/completions", counter=FixtureCounter())

        run = {"id": "fixture", "synthetic": False, "status": "running", "started_ns": time.time_ns(),
               "model": "fixture/mock", "limit": 250000, "metric": "active_context", "native_cost_usd": "0",
               "events": [], "sessions": [], "agents": 0}
        profile = {"model": "fixture/mock", "name": "Fixture", "context": 1000000, "input": 0, "output": 0, "cache_read": 0}
        patches = [patch.dict(os.environ, {"OPENCODE_API_KEY": "synthetic", "DEMO_MAX_COST_USD": "0", "PLAYGROUND_URL": ""}),
                   patch.dict(runner.PROFILES, {"fixture": profile}), patch("runner.ContextRelay", side_effect=local_relay)]
        if args.local_sandbox:
            from local_sandbox import LocalSandbox
            patches.append(patch("runner.Sandbox", LocalSandbox))
        for item in patches:
            item.start()
        try:
            runner.Runner(NoExport(), lambda _run: None, root).run(run)
        finally:
            for item in reversed(patches):
                item.stop()
        names = [e["name"] for e in run["events"]]
        summary = {key: run.get(key) for key in ("status", "failure", "agents", "check", "changed", "usage_complete")}
        summary.update(request_count=len(requests), fresh_sessions=len(set(run["sessions"])),
                       sandbox_mode="local-stand-in" if args.local_sandbox else "openshell")
        print(json.dumps(summary))
        assert run["status"] == "passed", summary
        assert len(requests) == 6 and run["agents"] == 2 and len(set(run["sessions"])) == 2, summary
        assert run["usage_complete"] is True, summary
        assert any(e["name"] == "gate.closed" and e.get("aeion.context.observed") == 250000 for e in run["events"])
        assert names.index("handover.prepared") < names.index("context.refused") < names.index("gate.closed") < names.index("agent.handover")
        assert "HARNESS_COMPACTION" not in json.dumps(run["events"])
        prompt_text = SCENARIOS["pricing-js-v1"]["contract"][:60]
        assert prompt_text not in json.dumps(run["events"]) and "Supervisor-loaded" not in json.dumps(run["events"]), \
            "Prompt text must never enter events"
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
