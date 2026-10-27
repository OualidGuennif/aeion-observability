"""Run in the demo Docker image; host-only checks explicitly skip these dependencies."""
import json
from pathlib import Path
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
try:
    from token_budget import TokenBudget, admit
    from relay import ContextRelay
    IMPORTABLE = True
    AVAILABLE = (Path(__file__).resolve().parents[1] / "tokenizers/glm/tokenizer.json").exists()
except ModuleNotFoundError:
    IMPORTABLE = AVAILABLE = False


@unittest.skipUnless(AVAILABLE, "pinned tokenizers required (python3 demo/install.py)")
class RuntimeTests(unittest.TestCase):
    def test_exact_300k_reservation_boundary(self):
        self.assertTrue(admit(275904, 4096))
        self.assertFalse(admit(275905, 4096))
        with self.assertRaises(ValueError):
            admit(100, 4097)

    def test_all_official_templates_count_tool_roundtrip(self):
        body = {"messages": [{"role": "user", "content": "Implement a pricing function."},
                {"role": "assistant", "content": "", "tool_calls": [{"id": "x", "type": "function", "function": {"name": "read", "arguments": '{"filePath":"src/pricing.js"}'}}]},
                {"role": "tool", "tool_call_id": "x", "content": "export function totalCents() {}"}],
                "tools": [{"type": "function", "function": {"name": "read", "parameters": {"type": "object"}}}]}
        from token_budget import MODELS
        for model in MODELS:
            with self.subTest(model=model):
                counter = TokenBudget(model)
                count = counter.count(body)
                self.assertGreater(count, 10)
                self.assertEqual(count, counter.count(body))
                with self.assertRaises(ValueError):
                    counter.count({"messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "private"}}]}]})

    def test_all_official_templates_count_the_pi_request_shape(self):
        # Shape captured from Flue 2.3.0 / Pi 1.4.0: text parts, null assistant content with tool
        # calls, replayed reasoning_content, and OpenAI-style tool declarations.
        body = {"messages": [{"role": "system", "content": "You are a coding agent."},
                {"role": "user", "content": [{"type": "text", "text": "Implement a pricing function."}]},
                {"role": "assistant", "content": None, "reasoning_content": "Read the file first.",
                 "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "read", "arguments": '{"path":"src/pricing.js"}'}}]},
                {"role": "tool", "tool_call_id": "c1", "content": "export function totalCents() {}"}],
                "tools": [{"type": "function", "function": {"name": "read", "description": "Read a file.",
                                                            "parameters": {"type": "object"}}}]}
        from token_budget import MODELS
        for model in MODELS:
            with self.subTest(model=model):
                self.assertGreater(TokenBudget(model).count(body), 10)

    def test_relay_refuses_before_any_upstream_request_and_wait_does_not_admit_more(self):
        class Counter:
            def count(self, _payload):
                return 300001
        called, ready, release = [], threading.Event(), threading.Event()
        def checkpoint(value, closed):
            called.append((value, closed))
            ready.set()
            release.wait(timeout=3)
        relay = ContextRelay("fixture/mock", "not-sent", 250000, checkpoint, lambda *_a, **_k: None,
                             upstream="http://127.0.0.1:1/never", counter=Counter(), bind=("127.0.0.1",0))
        relay.start()
        payload = json.dumps({"model": "mock", "messages": [{"role": "user", "content": "small"}], "stream": True, "max_tokens": 4096}).encode()
        statuses = []
        def send(token):
            try:
                req = urllib.request.Request(f"http://127.0.0.1:{relay.server.server_port}/v1/chat/completions", data=payload,
                    headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=4)
            except urllib.error.HTTPError as error:
                statuses.append(error.code)
        try:
            send("invalid")
            self.assertEqual(statuses, [403])
            first = threading.Thread(target=send, args=(relay.token,))
            first.start()
            self.assertTrue(ready.wait(timeout=2))
            send(relay.token)
            self.assertEqual(statuses[-1], 403)
            self.assertEqual(called, [(300001, True)])
            release.set()
            first.join(timeout=3)
            self.assertEqual(statuses[-1], 409)
        finally:
            release.set()
            relay.close()


@unittest.skipUnless(IMPORTABLE, "controller requirements required")
class AdmissionTests(unittest.TestCase):
    def test_admission_stop_refuses_before_forwarding_and_closes_the_relay(self):
        class Counter:
            def count(self, _payload):
                return 4000
        forwarded, decisions = [], ["BUDGET_STOP"]

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                forwarded.append(self.path)
                self.send_response(500)
                self.end_headers()
        upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        threading.Thread(target=upstream.serve_forever, daemon=True).start()
        events = []
        relay = ContextRelay("fixture/mock", "not-sent", 250000, lambda *_a: None, lambda name, **attrs: events.append((name, attrs)),
                             upstream=f"http://127.0.0.1:{upstream.server_port}/v1/chat/completions", counter=Counter(),
                             admission=lambda: decisions.pop(0) if decisions else None)
        relay.start()
        payload = json.dumps({"model": "mock", "messages": [{"role": "user", "content": "small"}], "stream": True, "max_tokens": 4096}).encode()
        try:
            request = urllib.request.Request(relay.url + "/chat/completions", data=payload,
                                             headers={"Authorization": "Bearer " + relay.token, "Content-Type": "application/json"})
            with self.assertRaises(urllib.error.HTTPError) as refused:
                urllib.request.urlopen(request, timeout=5)
            self.assertEqual(refused.exception.code, 409)
            self.assertIn(b"BUDGET_STOP", refused.exception.read())
            self.assertEqual(forwarded, [])
            self.assertTrue(relay.closed)
            self.assertIn(("context.refused", {"aeion.failure.code": "BUDGET_STOP"}), events)
            self.assertEqual(relay.forwarded_count, 0)
        finally:
            relay.close()
            upstream.shutdown()


if __name__ == "__main__":
    unittest.main()
