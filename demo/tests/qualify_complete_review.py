"""Real Flue intake of a complete large artifact once; local scripted inference only."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import argparse
import json
import os
from pathlib import Path
import sys
import threading
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'demo'),str(ROOT/'demo/app')]
from factory.flue_review import FlueReview
from app.relay import ContextRelay
from token_budget import TokenBudget
import runner

MARKER='COMPLETE_ARTIFACT_END_QUALIFICATION'
calls=[]
packet='# Complete source fixture\n'+'x'*170000+'\n'+MARKER


class Inference(BaseHTTPRequestHandler):
    output_window=16384
    effort='low'
    omit_final_cost=False
    def log_message(self,*_):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        assert body['max_tokens']==self.output_window,'Only the frozen supervisor output bound may reach the provider'
        if body['model']=='deepseek-v4.1-flash':
            assert body['thinking']=={'type':'enabled'} and body['reasoning_effort']==self.effort
        anthropic=body['model']=='qwen3.8-flash'
        names={tool['name'] if anthropic else tool['function']['name'] for tool in body.get('tools',[])}
        assert not names.intersection({'bash','read','write','edit'}),'The frozen review needs no filesystem capability'
        assert json.dumps(body['messages']).count(MARKER)==1,'Complete packet must appear exactly once'
        assert 'x'*170000 in json.dumps(body['messages']),'No excerpt may reach the provider'
        calls.append(len(json.dumps(body).encode()))
        if anthropic:
            events=[{'type':'message_start','message':{'id':'fixture','type':'message','role':'assistant',
                'content':[],'model':body['model'],'usage':{'input_tokens':40000,'output_tokens':0,
                'cache_read_input_tokens':0,'cache_creation_input_tokens':0}}}]
            if len(calls)==1:
                events.extend([{'type':'content_block_start','index':0,'content_block':{
                    'type':'tool_use','id':'fixture-review','name':'submit_review','input':{}}},
                    {'type':'content_block_delta','index':0,'delta':{'type':'input_json_delta',
                    'partial_json':json.dumps({'verdict':'approve','reason':'Synthetic full coverage'})}}])
            else:
                events.extend([{'type':'content_block_start','index':0,'content_block':{'type':'text','text':''}},
                    {'type':'content_block_delta','index':0,'delta':{'type':'text_delta','text':'Done.'}}])
            final_usage={'output_tokens':100,'cost':0}
            if self.omit_final_cost and len(calls)==2:final_usage.pop('cost')
            events.extend([{'type':'content_block_stop','index':0},
                {'type':'message_delta','delta':{'stop_reason':'tool_use' if len(calls)==1 else 'end_turn',
                 'stop_sequence':None},'usage':final_usage}, {'type':'message_stop'}])
            data=''.join('event: '+event['type']+'\ndata: '+json.dumps(event)+'\n\n' for event in events)
            self.send_response(200);self.send_header('Content-Type','text/event-stream')
            self.send_header('Content-Length',str(len(data.encode())))
            self.end_headers();self.wfile.write(data.encode());return
        delta={'role':'assistant','content':'Done.'}
        if len(calls)==1:
            delta={'role':'assistant','tool_calls':[{'index':0,'id':'fixture-review','type':'function',
                'function':{'name':'submit_review','arguments':json.dumps({'verdict':'approve','reason':'Synthetic full coverage'})}}]}
        pieces=[{'choices':[{'index':0,'delta':delta,'finish_reason':None}]},
            {'choices':[{'index':0,'delta':{},'finish_reason':'tool_calls' if len(calls)==1 else 'stop'}]},
            {'choices':[],'usage':{'prompt_tokens':TokenBudget(body['model']).count(body),'completion_tokens':100,'cost':0}}]
        if self.omit_final_cost and len(calls)==2:pieces[-1]['usage'].pop('cost')
        data=''.join('data: '+json.dumps({'id':'fixture','object':'chat.completion.chunk','model':body['model'],**p})+'\n\n' for p in pieces)+'data: [DONE]\n\n'
        self.send_response(200);self.send_header('Content-Type','text/event-stream')
        self.send_header('Content-Length',str(len(data.encode())));self.end_headers();self.wfile.write(data.encode())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',choices=('glm-5.3-flash','deepseek-4.1-flash','qwen-3.8-flash'),default='glm-5.3-flash')
    parser.add_argument('--max-output-tokens',type=int,choices=(16384,32768,65536),default=16384)
    parser.add_argument('--deepseek-effort',choices=('low','medium'),default='low')
    parser.add_argument('--omit-final-cost',action='store_true')
    args=parser.parse_args()
    Inference.output_window=args.max_output_tokens
    Inference.effort='high' if args.deepseek_effort=='medium' else 'low'
    Inference.omit_final_cost=args.omit_final_cost
    server=ThreadingHTTPServer(('127.0.0.1',0),Inference)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    def relay(*args,**kwargs):
        return ContextRelay(*args,**kwargs,upstream=f'http://127.0.0.1:{server.server_port}/v1/chat/completions')
    class FixtureReview(FlueReview):paid=False
    role=FixtureReview(max_prompt_bytes=200000,cost_limit='0.25',max_output_tokens=args.max_output_tokens,deepseek_effort=args.deepseek_effort)
    role.build_id='a'*32;role.authorization_check=lambda:True
    try:
        with patch.dict(os.environ,{'OPENCODE_API_KEY':'synthetic'}),patch.object(runner,'ContextRelay',side_effect=relay):
            if args.omit_final_cost:
                try:role(args.model,packet)
                except ValueError as error:assert str(error)=='USAGE_UNKNOWN'
                else:raise AssertionError('A typed approval with unknown final cost must not be accepted')
                assert len(calls)==2 and role.last_usage['complete'] is False
                assert role.last_execution['failure']=='USAGE_UNKNOWN'
                print(json.dumps({'status':'passed','case':'unknown_final_cost_refused','requests':2,
                    'model':args.model,'real_provider_requests':0,'synthetic':True}))
                return
            result=role(args.model,packet)
        assert result['verdict']=='approve' and len(calls)==2
        assert role.last_execution['forwarded_count']==2
        print(json.dumps({'status':'passed','packet_bytes':len(packet.encode()),'requests':len(calls),
            'complete_packet_copies_per_request':1,'max_output_tokens':args.max_output_tokens,'model':args.model,
            'real_provider_requests':0,'synthetic':True}))
    finally:server.shutdown();server.server_close()


if __name__=='__main__':main()
