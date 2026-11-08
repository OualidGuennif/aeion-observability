"""Native Pi protocol compatibility at the authenticated relay; no external inference."""
import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
import sys
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from relay import ContextRelay


class ProtocolTests(unittest.TestCase):
    def test_shutdown_cannot_race_a_local_preflight_into_an_uncounted_late_forward(self):
        box=self.relay()
        entered,release,closing=threading.Event(),threading.Event(),threading.Event()
        count=box.counter.count
        shutdown=box.server.shutdown
        def paused_count(payload):
            entered.set()
            if not release.wait(3):raise AssertionError('preflight was not released')
            return count(payload)
        def announced_shutdown():
            closing.set()
            return shutdown()
        with patch.object(box.counter,'count',side_effect=paused_count), \
                patch.object(box.server,'shutdown',side_effect=announced_shutdown), \
                ThreadPoolExecutor(max_workers=2) as pool:
            client=pool.submit(self.send,box,'/messages')
            try:
                self.assertTrue(entered.wait(2))
                stopping=pool.submit(box.close)
                self.assertTrue(closing.wait(2))
            finally:
                release.set()
            self.assertEqual(client.result(timeout=3)[0],409)
            stopping.result(timeout=3)
        self.assertEqual(box.forwarded_count,0)
        self.assertEqual(self.forwarded,[])

    def test_close_waits_for_handler_usage_accounting_before_returning(self):
        box=self.relay()
        # The active lock spans forwarding and its final usage append, not just socket I/O.
        box.active.acquire()
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending=pool.submit(box.close)
            try:
                with self.assertRaises(TimeoutError):pending.result(timeout=1)
            finally:
                box.active.release()
            pending.result(timeout=3)

    def setUp(self):
        self.forwarded = []
        calls = self.forwarded

        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *_args): pass

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                calls.append({'path': self.path, 'model': payload['model'],
                              'session': self.headers.get('x-opencode-session')})
                body = b'data: {"type":"message_stop"}\n\n'
                self.send_response(200)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.upstream = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        threading.Thread(target=self.upstream.serve_forever, daemon=True).start()
        self.addCleanup(self.upstream.server_close)
        self.addCleanup(self.upstream.shutdown)

    def relay(self, required_effort=None, **options):
        class Counter:
            def count(self, _payload): return 4000
        box = ContextRelay('opencode-go/fixture', 'synthetic-upstream-only', 250000,
            lambda *_args: None, lambda *_args, **_kwargs: None, counter=Counter(),
            api='anthropic-messages', required_effort=required_effort,
            upstream=f'http://127.0.0.1:{self.upstream.server_port}/v1/messages',**options)
        box.start()
        self.addCleanup(box.close)
        return box

    def send(self, box, suffix, extra=None):
        payload = {'model': 'fixture', 'stream': True, 'max_tokens': 4096,
                   'messages': [{'role': 'user', 'content': 'Synthetic fixture'}], **(extra or {})}
        request = urllib.request.Request(box.url + suffix, data=json.dumps(payload).encode(),
            headers={'x-api-key': box.token, 'Content-Type': 'application/json',
                     'x-opencode-session': 'fixture-session'})
        try:
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            with error:
                return error.code, error.read()

    def test_pinned_anthropic_beta_path_forwards_to_only_the_fixed_upstream(self):
        box = self.relay()
        self.assertEqual(self.send(box, '/messages?beta=true')[0], 200)
        self.assertEqual(self.forwarded, [{'path': '/v1/messages', 'model': 'fixture',
                                          'session': 'fixture-session'}])

    def test_unknown_query_cannot_select_a_protocol_or_upstream(self):
        box = self.relay()
        self.assertEqual(self.send(box, '/messages?beta=false')[0], 409)
        self.assertEqual(self.forwarded, [])
        self.assertEqual(box.forwarded_count, 0)

    def test_max_effort_is_required_before_any_haiku_forward(self):
        box = self.relay(required_effort='max')
        self.assertEqual(self.send(box, '/messages')[0], 409)
        self.assertEqual(box.last_error_code, 'CONTEXT_UNKNOWN')
        self.assertEqual(self.forwarded, [])

    def test_explicit_adaptive_max_is_admitted(self):
        box = self.relay(required_effort='max')
        self.assertEqual(self.send(box, '/messages?beta=true', {
            'thinking': {'type': 'adaptive'}, 'output_config': {'effort': 'max'}})[0], 200)
        self.assertEqual(len(self.forwarded), 1)

    def test_larger_output_requires_the_supervisor_bound_and_keeps_default_strict(self):
        default=self.relay()
        self.assertEqual(self.send(default,'/messages',{'max_tokens':8192})[0],409)
        self.assertEqual(self.forwarded,[])
        extended=self.relay(max_output_tokens=16384)
        self.assertEqual(self.send(extended,'/messages',{'max_tokens':8192})[0],200)
        self.assertEqual(len(self.forwarded),1)
        with self.assertRaisesRegex(ValueError,'OUTPUT_LIMIT_INVALID'):
            self.relay(max_output_tokens=65537)
        largest=self.relay(max_output_tokens=32768)
        self.assertEqual(self.send(largest,'/messages',{'max_tokens':32768})[0],200)
        self.assertEqual(self.send(largest,'/messages',{'max_tokens':32769})[0],409)
        bulk=self.relay(max_output_tokens=65536)
        self.assertEqual(self.send(bulk,'/messages',{'max_tokens':65536})[0],200)
        self.assertEqual(self.send(bulk,'/messages',{'max_tokens':65537})[0],409)

    def test_explicit_deepseek_effort_cannot_be_omitted_disabled_or_raised_by_the_worker(self):
        for wrong in ({},{'thinking':{'type':'disabled'},'reasoning_effort':'low'},
                      {'thinking':{'type':'enabled'},'reasoning_effort':'high'}):
            box=self.relay(required_reasoning_effort='low')
            with self.subTest(payload=wrong):self.assertEqual(self.send(box,'/messages',wrong)[0],409)
            self.assertEqual(box.forwarded_count,0)
        admitted=self.relay(required_reasoning_effort='low')
        self.assertEqual(self.send(admitted,'/messages',{
            'thinking':{'type':'enabled'},'reasoning_effort':'low'})[0],200)
        self.assertEqual(len(self.forwarded),1)

    def test_openai_style_effort_is_exact_and_carries_no_thinking_object(self):
        # GPT-6 Luna and Mistral Large 4 (measured 2026-11-06) send reasoning_effort alone.
        for required,wrong in (('max',{}),('max',{'reasoning_effort':'high'}),
                               ('max',{'reasoning_effort':'max','thinking':{'type':'enabled'}}),
                               ('high',{'reasoning_effort':'max'})):
            box=self.relay(required_reasoning_effort=required,reasoning_thinking_object=False)
            with self.subTest(required=required,payload=wrong):
                self.assertEqual(self.send(box,'/messages',wrong)[0],409)
            self.assertEqual(box.forwarded_count,0)
        for required in ('max','high'):
            admitted=self.relay(required_reasoning_effort=required,reasoning_thinking_object=False)
            self.assertEqual(self.send(admitted,'/messages',{'reasoning_effort':required})[0],200)
        self.assertEqual(len(self.forwarded),2)

    def test_minimax_reserves_the_highest_measured_go_multiple_and_sends_no_effort(self):
        from profiles import PROFILES, available, model_metadata
        self.assertEqual(PROFILES['luna']['efforts']['max'],'max')
        self.assertEqual(PROFILES['minimax']['model'],'opencode-go/minimax-m3.1-flash')
        self.assertEqual(PROFILES['minimax']['budget_multiplier'],'4')
        self.assertNotIn('efforts',PROFILES['minimax'])
        self.assertNotIn('upstream',PROFILES['minimax'])
        self.assertEqual(model_metadata('minimax')['api'],'openai-completions')
        self.assertTrue(available('luna') and available('minimax'))
        self.assertNotIn('mistral',PROFILES)


if __name__ == '__main__':
    unittest.main()
