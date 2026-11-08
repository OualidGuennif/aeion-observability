"""Closed-tokenizer profiles launch on bounded inputs and gate on measured API usage."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from provider_usage import ReportedUsage
from relay import ContextRelay


class ContextAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.usage={'input_tokens':4000,'output_tokens':10,'cost':0.001}
        owner=self
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_POST(self):
                owner.calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                events=[{'type':'message_start','message':{'usage':owner.usage}},
                        {'type':'message_stop'}]
                raw=''.join('data: '+json.dumps(event)+'\n\n' for event in events).encode()
                self.send_response(200);self.send_header('Content-Length',str(len(raw)))
                self.end_headers();self.wfile.write(raw)
        self.upstream=ThreadingHTTPServer(('127.0.0.1',0),Upstream)
        threading.Thread(target=self.upstream.serve_forever,daemon=True).start()
        self.addCleanup(self.upstream.server_close);self.addCleanup(self.upstream.shutdown)

    def relay(self,**options):
        self.checkpoints=[]
        box=ContextRelay('opencode-go/qwen3.8-flash','synthetic',250000,
            lambda *args:self.checkpoints.append(args),lambda *_a,**_k:None,
            api='anthropic-messages',upstream=f'http://127.0.0.1:{self.upstream.server_port}/v1/messages',
            prices={'input':0.15,'output':0.47},cost_limit='1.00',**options)
        box.start();self.addCleanup(box.close);return box

    def send(self,box,index=0):
        payload={'model':'qwen3.8-flash','stream':True,'max_tokens':4096,
                 'messages':[{'role':'user','content':'x'*170000+str(index)}]}
        request=urllib.request.Request(box.url+'/messages',data=json.dumps(payload).encode(),
            headers={'x-api-key':box.token,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=4) as response:
                response.read();status=response.status
        except urllib.error.HTTPError as error:
            with error:error.read();status=error.code
        # Inspect completed accounting, not the stop-event/HTTP-handler timing race.
        with box.active:pass
        return status

    def test_complete_170kb_packet_launches_without_treating_cost_bound_as_context(self):
        box=self.relay()
        self.assertEqual([self.send(box,i) for i in range(2)],[200,200])
        self.assertEqual(len(self.calls),2)
        self.assertGreater(box.forwarded_counts[0],300000)
        self.assertGreater(box.projected_cost,0)
        self.assertEqual(self.checkpoints,[])

    def test_exact_local_count_still_refuses_an_oversized_request_before_transport(self):
        class Counter:
            def count(self,_):return 300001
        box=self.relay(counter=Counter())
        self.assertEqual(self.send(box),409)
        self.assertEqual(self.calls,[])
        self.assertEqual(self.checkpoints,[(300001,True)])

    def test_native_context_including_cache_closes_before_the_next_request(self):
        self.usage.update(input_tokens=1000,cache_read_input_tokens=250000)
        box=self.relay()
        self.assertEqual(self.send(box),200)
        self.assertEqual(self.send(box,1),409)
        self.assertEqual(len(self.calls),1)
        self.assertEqual(box.last_error_code,'AEION_HANDOVER')
        self.assertEqual(self.checkpoints,[(251000,True)])

    def test_unknown_usage_never_admits_another_paid_request(self):
        for missing in ('input_tokens','output_tokens','cost'):
            with self.subTest(missing=missing):
                self.usage={'input_tokens':4000,'output_tokens':10,'cost':0.001}
                del self.usage[missing]
                box=self.relay();before=len(self.calls)
                self.assertEqual(self.send(box),200)
                self.assertEqual(self.send(box,1),409)
                self.assertEqual(len(self.calls),before+1)
                self.assertEqual(box.last_error_code,'USAGE_UNKNOWN')

    def test_supervisor_stop_reason_survives_the_refused_request(self):
        box=self.relay(admission=lambda:'STEP_LIMIT')
        self.assertEqual(self.send(box),409)
        self.assertEqual(self.calls,[])
        self.assertEqual(box.last_error_code,'STEP_LIMIT')

    def test_actual_300k_violation_is_distinct_from_a_handover(self):
        self.usage.update(input_tokens=299999,output_tokens=10)
        box=self.relay()
        self.assertEqual(self.send(box),200)
        self.assertEqual(self.send(box,1),409)
        self.assertEqual(box.last_error_code,'PROVIDER_CONTEXT_VIOLATION')
        self.assertEqual(len(self.calls),1)

    def post_messages(self, box, count):
        payload={'model':'qwen3.8-flash','stream':True,'max_tokens':16,
                 'messages':[{'role':'user','content':'x'} for _ in range(count)]}
        request=urllib.request.Request(box.url+'/messages',data=json.dumps(payload).encode(),
            headers={'x-api-key':box.token,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=4) as response:
                response.read();status=response.status
        except urllib.error.HTTPError as error:
            with error:error.read();status=error.code
        with box.active:pass
        return status

    def test_a_follow_up_past_the_message_cap_hands_over(self):
        box=self.relay()
        self.assertEqual(self.send(box),200)
        self.assertEqual(self.post_messages(box,257),409)
        self.assertEqual(box.last_error_code,'AEION_HANDOVER')
        self.assertEqual(len(self.calls),1)
        self.assertEqual(self.checkpoints,[(4000,True)])

    def test_the_first_request_past_the_message_cap_stays_unknown(self):
        box=self.relay()
        self.assertEqual(self.post_messages(box,257),409)
        self.assertEqual(box.last_error_code,'CONTEXT_UNKNOWN')
        self.assertEqual(self.calls,[])
        self.assertEqual(self.checkpoints,[])

    def test_an_unexpected_follow_up_exception_is_relay_fault(self):
        box=self.relay()
        self.assertEqual(self.send(box),200)
        class Boom:
            def count(self, _payload):
                raise RuntimeError('synthetic')
        box.counter=Boom()
        status=self.send(box,1)
        self.assertEqual(status,409)
        self.assertEqual(box.last_error_code,'RELAY_FAULT')
        self.assertEqual(len(self.calls),1)
        self.assertTrue(self.checkpoints)

    def test_a_first_request_unexpected_exception_stays_unknown(self):
        box=self.relay()
        class Boom:
            def count(self, _payload):
                raise RuntimeError('synthetic')
        box.counter=Boom()
        status=self.send(box)
        self.assertEqual(status,409)
        self.assertEqual(box.last_error_code,'CONTEXT_UNKNOWN')
        self.assertEqual(self.calls,[])
        self.assertEqual(self.checkpoints,[])


class ProviderContextTests(unittest.TestCase):
    def test_anthropic_input_includes_cache_and_output_updates_preserve_it(self):
        usage=ReportedUsage()
        for item in ({'input_tokens':100,'cache_read_input_tokens':200,'cache_creation_input_tokens':300},
                     {'output_tokens':10,'cost':0.01}):
            usage.feed(('data: '+json.dumps({'usage':item})+'\n\n').encode())
        usage.feed(b'data: {"type":"message_stop"}\n\n')
        self.assertEqual(usage.summary()['input_tokens'],600)
        self.assertEqual(usage.summary()['output_tokens'],10)
        self.assertEqual(usage.summary()['cache_read_tokens'],200)

    def test_openai_prompt_total_does_not_add_cached_tokens_twice(self):
        usage=ReportedUsage()
        usage.feed(b'data: {"usage":{"prompt_tokens":600,"prompt_tokens_details":{"cached_tokens":200},"completion_tokens":10,"cost":0.01}}\n\ndata: [DONE]\n\n')
        self.assertEqual(usage.summary()['input_tokens'],600)
        self.assertEqual(usage.summary()['cache_read_tokens'],200)
        usage=ReportedUsage()
        usage.feed(b'data: {"usage":{"prompt_tokens":600,"cache_read_input_tokens":-1,"completion_tokens":10,"cost":0.01}}\n\n')
        self.assertIsNone(usage.summary()['cache_read_tokens'])


if __name__=='__main__':unittest.main()
