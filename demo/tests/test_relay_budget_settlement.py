"""Only finalized measured usage releases a request's unused output reservation."""
from decimal import Decimal
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from relay import ContextRelay


class SettlementTests(unittest.TestCase):
    def setUp(self):
        self.mode='complete';owner=self
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
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

    def relay(self):
        class Counter:
            def count(self,_):return 2000
        relay=ContextRelay('fixture/model','synthetic',250000,lambda *_:None,lambda *_a,**_k:None,
            counter=Counter(),upstream=f'http://127.0.0.1:{self.server.server_port}',
            max_output_tokens=32768,prices={'input':0.15,'output':1.2},cost_limit='0.08')
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


if __name__=='__main__':unittest.main()
