"""Only finalized measured usage releases a request's unused output reservation."""
from decimal import Decimal
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import relay as relay_module
from relay import ContextRelay


class SettlementTests(unittest.TestCase):
    def setUp(self):
        self.mode='complete';owner=self
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                if owner.mode=='silent':time.sleep(1)
                usage={'prompt_tokens':2000,'completion_tokens':10}
                if owner.mode!='unknown_cost':usage['cost']=0.000001
                if owner.mode=='missing_output':del usage['completion_tokens']
                if owner.mode=='expensive':usage['cost']=0.1
                content='data: '+json.dumps({'usage':usage})+'\n\n'
                if owner.mode!='unfinished':content+='data: [DONE]\n\n'
                raw=content.encode();self.send_response(200)
                self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Upstream)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)

    def relay(self,**bounds):
        class Counter:
            def count(self,_):return 2000
        relay=ContextRelay('fixture/model','synthetic',250000,lambda *_:None,lambda *_a,**_k:None,
            counter=Counter(),upstream=f'http://127.0.0.1:{self.server.server_port}',
            max_output_tokens=32768,prices={'input':0.15,'output':1.2},cost_limit='0.08',**bounds)
        relay.start();self.addCleanup(relay.close);return relay

    def send(self,relay,index):
        body=json.dumps({'model':'model','messages':[{'role':'user','content':str(index)}],
            'max_tokens':32768,'stream':True}).encode()
        request=urllib.request.Request(relay.url+'/chat/completions',data=body,
            headers={'Authorization':'Bearer '+relay.token,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=4) as response:response.read();return response.status
        except urllib.error.HTTPError as error:
            with error:error.read();return error.code

    def test_complete_usage_releases_unused_output_but_keeps_a_conservative_input_bound(self):
        relay=self.relay()
        self.assertEqual([self.send(relay,i) for i in range(3)],[200,200,200])
        with relay.active:
            self.assertEqual(relay.projected_cost,Decimal('0.000936'))
        self.assertEqual(relay.forwarded_count,3)

    def test_unknown_or_unfinished_usage_keeps_the_entire_liability(self):
        for mode in ('unknown_cost','unfinished','missing_output'):
            self.mode=mode;relay=self.relay()
            self.assertEqual([self.send(relay,i) for i in range(3)],[200,200,409])
            self.assertEqual(relay.forwarded_count,2)
            self.assertEqual(relay.projected_cost,Decimal('0.0792432'))

    def test_a_higher_reported_resource_cost_blocks_the_next_request(self):
        self.mode='expensive';relay=self.relay()
        self.assertEqual([self.send(relay,i) for i in range(2)],[200,409])
        self.assertEqual(relay.projected_cost,Decimal('0.1'))

    def test_factory_bound_can_exceed_the_lab_default_and_still_stops_exactly(self):
        relay=self.relay(max_requests=13)
        self.assertEqual([self.send(relay,i) for i in range(14)],[200]*13+[409])
        self.assertEqual(relay.forwarded_count,13)
        self.assertEqual(relay.last_error_code,'STEP_LIMIT')

    def test_a_silent_thinking_provider_is_awaited_and_a_stalled_one_is_a_timeout(self):
        self.mode='silent'
        relay=self.relay()
        self.assertEqual(self.send(relay,0),200)
        self.assertIsNone(relay.last_error_code)
        with patch.object(relay_module,'UPSTREAM_IDLE_SECONDS',0.2):
            relay=self.relay()
            try:self.send(relay,0)
            except OSError:pass  # The relay closes without an answer; the client side may see a reset.
        self.assertEqual(relay.last_error_code,'PROVIDER_TIMEOUT')
        self.assertTrue(relay.closed)

    def test_lab_default_and_invalid_factory_step_bounds_remain_closed(self):
        relay=self.relay()
        self.assertEqual([self.send(relay,i) for i in range(13)],[200]*12+[409])
        for cap in (0,True,201):
            with self.subTest(cap=cap),self.assertRaisesRegex(ValueError,'STEP_LIMIT_INVALID'):
                self.relay(max_requests=cap)


if __name__=='__main__':unittest.main()
