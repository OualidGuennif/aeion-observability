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
        self.mode='complete';owner=self;self.busy=[];self.posts=0
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                owner.posts+=1
                if owner.busy:
                    status,retry_after=owner.busy.pop(0);raw=b'{"error":"busy"}'
                    self.send_response(status)
                    if retry_after is not None:self.send_header('Retry-After',retry_after)
                    self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
                if owner.mode=='silent':time.sleep(1)
                usage={'prompt_tokens':2000,'completion_tokens':10}
                if owner.mode!='unknown_cost':usage['cost']=0.000001
                if owner.mode=='missing_output':del usage['completion_tokens']
                if owner.mode=='expensive':usage['cost']=0.1
                if owner.mode=='cached':usage['prompt_tokens_details']={'cached_tokens':1500}
                if owner.mode=='overcached':usage['prompt_tokens_details']={'cached_tokens':2001}
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

    def test_a_closed_profile_settles_on_the_reported_input_not_its_byte_bound(self):
        # Build ea3fe718 (2026-11-06): a byte bound eight times the real input stopped the author
        # with BUDGET_STOP after 20 requests and 0.155 USD of 2 USD.
        class ByteBound:
            context_basis='provider_usage'
            def count(self,_):return 16000
        relay=ContextRelay('fixture/model','synthetic',250000,lambda *_:None,lambda *_a,**_k:None,
            counter=ByteBound(),upstream=f'http://127.0.0.1:{self.server.server_port}',
            max_output_tokens=32768,prices={'input':0.15,'output':1.2},cost_limit='0.08')
        relay.start();self.addCleanup(relay.close)
        self.assertEqual([self.send(relay,i) for i in range(3)],[200,200,200])
        with relay.active:
            # 3 x (2000 reported input x 0.15 + 10 output x 1.2) / 1e6, not 16000 x 0.15 each.
            self.assertEqual(relay.projected_cost,Decimal('0.000936'))
        self.mode='missing_output';relay=self.relay()
        self.assertEqual([self.send(relay,i) for i in range(3)],[200,200,409])

    def test_reported_cache_reads_settle_at_the_cache_read_rate_and_bad_counts_at_full_rate(self):
        for mode,expected in (('cached','0.000306'),('overcached','0.000936')):
            with self.subTest(mode=mode):
                self.mode=mode
                relay=ContextRelay('fixture/model','synthetic',250000,lambda *_:None,lambda *_a,**_k:None,
                    counter=type('C',(),{'count':lambda self,_:2000})(),
                    upstream=f'http://127.0.0.1:{self.server.server_port}',max_output_tokens=32768,
                    prices={'input':0.15,'cacheRead':0.01,'output':1.2},cost_limit='0.08')
                relay.start();self.addCleanup(relay.close)
                self.assertEqual([self.send(relay,i) for i in range(3)],[200,200,200])
                with relay.active:
                    # 3 x (500 x 0.15 + 1500 x 0.01 + 10 x 1.2) / 1e6; a count above the input is ignored.
                    self.assertEqual(relay.projected_cost,Decimal(expected))

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

    def test_a_busy_provider_is_retried_a_bounded_number_of_times_with_one_forward(self):
        waits=[]
        with patch.object(relay_module,'PROVIDER_RETRY_DELAYS',(0.01,0.02)):
            relay=self.relay()
            relay.stopping.wait=lambda delay:waits.append(delay) or False
            self.busy=[(503,None),(429,'0')]
            self.assertEqual(self.send(relay,0),200)
        self.assertEqual((self.posts,waits,relay.provider_retries),(3,[0.01,0],2))
        self.assertEqual((relay.forwarded_count,relay.last_http_status),(1,429))
        self.assertIsNone(relay.last_error_code)

    def test_retries_stop_at_the_bound_and_never_cover_a_lasting_refusal(self):
        with patch.object(relay_module,'PROVIDER_RETRY_DELAYS',(0,0)):
            relay=self.relay();relay.stopping.wait=lambda _delay:False
            self.busy=[(503,None)]*3
            self.assertEqual(self.send(relay,0),503)
            self.assertEqual((self.posts,relay.provider_retries),(3,2))
            self.assertEqual((relay.last_error_code,relay.last_http_status),('PROVIDER_UNAVAILABLE',503))
            self.posts=0;relay=self.relay();relay.stopping.wait=lambda _delay:False
            self.busy=[(429,None)]*3
            self.assertEqual(self.send(relay,0),429)
            self.assertEqual((self.posts,relay.last_error_code),(3,'PROVIDER_RATE_LIMITED'))
            for status in (400,401,403,404,402):
                with self.subTest(status=status):
                    self.posts=0;relay=self.relay();relay.stopping.wait=lambda _delay:False
                    self.busy=[(status,None),(503,None)]
                    self.assertEqual(self.send(relay,0),status)
                    self.assertEqual((self.posts,relay.provider_retries,relay.last_http_status),(1,0,status))
                    self.busy=[]

    def test_a_retry_wait_is_capped_and_ends_when_the_relay_closes(self):
        class Busy:
            def __init__(self,value):self.headers={'Retry-After':value}
        self.assertEqual(relay_module.retry_delay(Busy('9999'),5),relay_module.RETRY_AFTER_CEILING_SECONDS)
        for value in ('-1','1.5','soon','\u0663',''):
            self.assertEqual(relay_module.retry_delay(Busy(value),5),5)
        relay=self.relay();relay.stopping.wait=lambda _delay:relay.stopping.set() or True
        self.busy=[(503,None),(503,None)]
        self.assertEqual(self.send(relay,0),409)
        self.assertEqual((self.posts,relay.last_error_code),(1,'RELAY_CLOSED'))

    def test_lab_default_and_invalid_factory_step_bounds_remain_closed(self):
        relay=self.relay()
        self.assertEqual([self.send(relay,i) for i in range(13)],[200]*12+[409])
        for cap in (0,True,201):
            with self.subTest(cap=cap),self.assertRaisesRegex(ValueError,'STEP_LIMIT_INVALID'):
                self.relay(max_requests=cap)


if __name__=='__main__':unittest.main()
