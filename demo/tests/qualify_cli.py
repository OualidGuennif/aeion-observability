"""Real pinned OpenCode CLI, local fake inference only: prove the dispatch barrier."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from runner import Runner, SOLUTION, config
from relay import ContextRelay

requests = []
workspace = None
PARTIAL = 'export function totalCents(items, shippingCents = 0) { return shippingCents; }\n'


class Inference(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_POST(self):
        assert self.headers.get("Authorization") == "Bearer synthetic", "Gate hook did not authorize dispatch"
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        requests.append(time.monotonic())
        number = len(requests)
        if number > 6:
            self.send_error(500)
            return
        call = None
        if number == 1:
            call = {"index": 0, "id": "call_glob", "type": "function", "function": {
                "name": "glob", "arguments": json.dumps({"pattern": "src/*.js"})}}
        elif number == 2:
            tool = next(m for m in reversed(body["messages"]) if m["role"] == "tool")
            assert "src/pricing.js" in str(tool["content"]) and "Error" not in str(tool["content"]), "Glob must work offline"
            call = {"index": 0, "id": "call_grep", "type": "function", "function": {
                "name": "grep", "arguments": json.dumps({"pattern": "export function", "path": "src", "include": "*.js"})}}
        elif number == 3:
            tool = next(m for m in reversed(body["messages"]) if m["role"] == "tool")
            assert "pricing.js" in str(tool["content"]) and "export function totalCents" in str(tool["content"]), "Grep must work offline"
            call = {"index": 0, "id": "call_read", "type": "function", "function": {
                "name": "read", "arguments": json.dumps({"filePath": str(workspace / "src/pricing.js")})}}
        elif number in (4, 5):
            if number == 5:
                assert (workspace / "src/pricing.js").read_text() == PARTIAL
                assert (workspace / "HANDOVER.md").is_file(), "MD must precede the fresh session"
                assert "## Independent verification" in (workspace / "HANDOVER.md").read_text()
                assert 'previous_agent' in json.dumps(body["messages"])
                assert 'Supervisor-loaded HANDOVER.md' in json.dumps(body["messages"])
                assert '## Independent verification' in json.dumps(body["messages"])
            call = {"index": 0, "id": "call_write", "type": "function", "function": {
                "name": "write", "arguments": json.dumps({"filePath": str(workspace / "src/pricing.js"), "content": PARTIAL if number == 4 else SOLUTION})}}
        delta = {"role": "assistant", "tool_calls": [call]} if call else {"role": "assistant", "content": "Done."}
        count = 250000 if number == 4 else 4000
        usage = {"prompt_tokens": count, "completion_tokens": 100, "total_tokens": count + 100}
        chunks = [
            {"choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
            {"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls" if call else "stop"}], "usage": usage},
        ]
        body = "".join("data: " + json.dumps({"id": "fixture", "model": "mock", "object": "chat.completion.chunk", **c}) + "\n\n" for c in chunks) + "data: [DONE]\n\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body.encode())))
        self.end_headers()
        self.wfile.write(body.encode())


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


if __name__ == "__main__":
    # Fixture-only diagnostics: no credentials, real provider or user code in this process.
    failures = []
    def record_exception(frame, event, arg):
        if event == "exception" and frame.f_code.co_filename.endswith("/app/runner.py"):
            failures.append((frame.f_code.co_name, arg[0].__name__, str(arg[1])[:160]))
        return record_exception
    sys.settrace(record_exception)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Inference)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory(prefix="aeion-cli-", dir="/work") as folder:
        root = Path(folder)
        root.chmod(0o711)
        workspace = root / "fixture/workspace"
        cfg = config("fixture/mock")
        cfg["enabled_providers"] = ["fixture"]
        cfg["provider"] = {"fixture": {"npm": "@ai-sdk/openai-compatible", "name": "Local fixture",
            "options": {"baseURL": f"http://127.0.0.1:{server.server_port}/v1", "apiKey": "gate-closed"},
            "models": {"mock": {"name": "Synthetic fixture", "limit": {"context": 1000000, "output": 4096},
                                "cost": {"input": 0, "output": 0}}}}}
        class FixtureCounter:
            def count(self, _payload):
                return 4000
        def local_relay(model, key, limit, checkpoint, event):
            return ContextRelay(model, key, limit, checkpoint, event,
                                upstream=f"http://127.0.0.1:{server.server_port}/v1/chat/completions", counter=FixtureCounter())
        run = {"id": "fixture", "synthetic": False, "status": "running", "started_ns": time.time_ns(),
               "model": "fixture/mock", "limit": 250000, "metric": "active_context", "native_cost_usd": "0",
               "events": [], "sessions": [], "agents": 0}
        # Disable the outer stdout threshold: this test must rely on the CLI pre-dispatch hook.
        with patch.dict(os.environ, {"OPENCODE_API_KEY": "synthetic", "DEMO_MAX_COST_USD": "0", "PLAYGROUND_URL": ""}), patch("runner.config", return_value=cfg), patch("runner.gate_value", return_value=0), patch("runner.ContextRelay", side_effect=local_relay):
            Runner(NoExport(), lambda _run: None, root).run(run)
        summary = {key: run.get(key) for key in ("status", "failure", "agents", "check", "changed")}
        summary.update(request_count=len(requests), fresh_sessions=len(set(run["sessions"])),
                       runtimes_removed=not (root / "fixture/runtime").exists())
        print(json.dumps(summary))
        if run["status"] != "passed":
            print("Fixture supervisor exceptions:", failures[-8:])
        assert run["status"] == "passed", summary
        assert len(requests) == 6 and run["agents"] == 2 and len(set(run["sessions"])) == 2, summary
        assert any(e["name"] == "gate.closed" and e["aeion.context.observed"] == 250000 for e in run["events"])
        names = [e["name"] for e in run["events"]]
        assert names.index("handover.prepared") < names.index("gate.closed") < names.index("agent.handover")
        assert summary["runtimes_removed"], summary
        from sandbox import protocol_hash
        marker = Path('/data/cli-qualification.json')
        temporary = marker.with_suffix('.tmp')
        temporary.write_text(json.dumps({'protocol_sha256':protocol_hash(), 'expires_ns':time.time_ns()+86400000000000}))
        temporary.chmod(0o600)
        temporary.replace(marker)
    server.shutdown()
