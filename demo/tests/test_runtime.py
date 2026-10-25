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
    AVAILABLE = (Path(__file__).resolve().parents[1] / "tokenizers/glm/tokenizer.json").exists()
except ModuleNotFoundError:
    AVAILABLE = False


@unittest.skipUnless(AVAILABLE, "Docker runtime/tokenizers required")
class RuntimeTests(unittest.TestCase):
    def test_exact_300k_reservation_boundary(self):
        self.assertTrue(admit(275904, 4096))
        self.assertFalse(admit(275905, 4096))
        with self.assertRaises(ValueError):
            admit(100, 4097)

    def test_both_official_templates_count_tool_roundtrip(self):
        body = {"messages": [{"role": "user", "content": "Implement a pricing function."},
                {"role": "assistant", "content": "", "tool_calls": [{"id": "x", "type": "function", "function": {"name": "read", "arguments": '{"filePath":"src/pricing.js"}'}}]},
                {"role": "tool", "tool_call_id": "x", "content": "export function totalCents() {}"}],
                "tools": [{"type": "function", "function": {"name": "read", "parameters": {"type": "object"}}}]}
        for model in ("glm-5.3-flash", "deepseek-v4.1-flash"):
            with self.subTest(model=model):
                counter = TokenBudget(model)
                count = counter.count(body)
                self.assertGreater(count, 10)
                self.assertEqual(count, counter.count(body))
                with self.assertRaises(ValueError):
                    counter.count({"messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "private"}}]}]})

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
                             upstream="http://127.0.0.1:1/never", counter=Counter())
        relay.start()
        payload = json.dumps({"model": "mock", "messages": [{"role": "user", "content": "small"}], "stream": True, "max_tokens": 4096}).encode()
        statuses = []
        def send(token):
            try:
                req = urllib.request.Request(relay.url + "/chat/completions", data=payload,
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


if __name__ == "__main__":
    unittest.main()
