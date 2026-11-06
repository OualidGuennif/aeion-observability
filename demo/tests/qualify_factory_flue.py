"""Real Flue/Pi + OpenShell + protected Java checks, with local scripted inference only."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'demo'), str(ROOT / 'demo/app')]
from factory.api import FactoryApp, S2_CONFIG
from factory.budget import DailyBudget
from factory.execution import FILTER
from factory.flue_builder import FlueBuilder
from factory.flue_review import FlueReview
from factory.isolation import DockerCheckRunner
from factory.target import load_target
from relay import ContextRelay
import runner

calls = {'author': 0, 'review': 0, 'haiku': 0, 'prepare': 0}
checks = []
preparation_contract = ''
review_without_tool_first = False


def last_tool(payload):
    messages = payload.get('messages', [])
    for message in reversed(messages):
        if message.get('role') == 'tool':
            return message['content']
        if isinstance(message.get('content'), list):
            for block in message['content']:
                if block.get('type') == 'tool_result':
                    return block.get('content', '')
    return ''


class Inference(BaseHTTPRequestHandler):
    def log_message(self, *_args): pass

    def do_POST(self):
        assert self.headers.get('Authorization') == 'Bearer synthetic'
        assert self.headers.get('User-Agent', '').startswith('pi/')
        assert self.headers.get('x-opencode-session')
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        anthropic = self.path == '/v1/messages'
        tools = {t['name'] if anthropic else t['function']['name'] for t in payload.get('tools', [])}
        role = ('prepare' if 'submit_preparation' in tools else 'author' if 'run_protected_checks' in tools
                else 'haiku' if payload['model'] == 'claude-haiku-5-5' else 'review')
        calls[role] += 1
        number = calls[role]
        call = None
        if role == 'author':
            if number == 1:
                call = ('read', {'path': 'demo/forum-app/src/main/java/local/aeion/forum/ForumHealth.java'})
            elif number == 2:
                bad = FILTER.replace('headers.putSingle("X-Content-Type-Options", "nosniff");', '')
                call = ('write', {'path': 'demo/forum-app/src/main/java/local/aeion/forum/SecurityHeadersFilter.java', 'content': bad})
            elif number == 3:
                call = ('run_protected_checks', {})
            elif number == 4:
                assert 'failed' in str(last_tool(payload)), 'Independent failure must reach the agent'
                checks.append('failed-feedback')
                call = ('write', {'path': 'demo/forum-app/src/main/java/local/aeion/forum/SecurityHeadersFilter.java', 'content': FILTER})
            elif number == 5:
                call = ('run_protected_checks', {})
            elif number == 6:
                assert 'passed' in str(last_tool(payload)), 'Repaired artifact must pass the real contract'
                checks.append('passed-feedback')
                # Owner-only feedback leaves through the supervisor bridge before the author stops.
                call = ('submit_feedback', {'text': 'RAS'})
            elif number == 7:
                assert 'Feedback recorded' in str(last_tool(payload)), 'Feedback must reach the bridge'
            else:
                raise AssertionError('Unexpected author retry')
        elif role == 'prepare':
            # Flue2.3 always includes task; without declared subagents it is inert.
            assert tools == {'submit_preparation','task'}, sorted(tools)
            if number == 1:
                call = ('submit_preparation', {'status':'ready', 'contract':preparation_contract,
                                               'reason':'Synthetic harness qualification'})
        else:
            # Each independent Flue reviewer gets its own submission and then ends.
            if role == 'haiku':
                assert payload['thinking']['type'] == 'adaptive'
                assert payload['output_config']['effort'] == 'max'
            if role == 'review' and review_without_tool_first:
                if number == 2:
                    assert 'factory.review.result_required' in str(payload), 'Missing verdict must trigger the native finish seam'
                    call = ('submit_review', {'verdict':'approve','reason':'Synthetic typed-channel qualification'})
                elif number > 3:
                    raise AssertionError('Unbounded format continuation')
            elif (number % 2) == 1:
                call = ('submit_review', {'verdict': 'approve', 'reason': 'Synthetic harness qualification'})
        count = 250000 if role == 'author' and number == 4 else 4000
        if anthropic:
            events = [('message_start', {'type': 'message_start', 'message': {
                'id': 'fixture', 'type': 'message', 'role': 'assistant', 'content': [],
                'model': payload['model'], 'usage': {'input_tokens': count, 'output_tokens': 0,
                'cache_read_input_tokens': 0, 'cache_creation_input_tokens': 0}}})]
            if call:
                events += [('content_block_start', {'type': 'content_block_start', 'index': 0,
                    'content_block': {'type': 'tool_use', 'id': 'call-' + str(number), 'name': call[0], 'input': {}}}),
                    ('content_block_delta', {'type': 'content_block_delta', 'index': 0,
                     'delta': {'type': 'input_json_delta', 'partial_json': json.dumps(call[1])}})]
            else:
                events += [('content_block_start', {'type': 'content_block_start', 'index': 0,
                    'content_block': {'type': 'text', 'text': ''}}),
                    ('content_block_delta', {'type': 'content_block_delta', 'index': 0,
                     'delta': {'type': 'text_delta', 'text': 'Done.'}})]
            events += [('content_block_stop', {'type': 'content_block_stop', 'index': 0}),
                ('message_delta', {'type': 'message_delta', 'delta': {
                    'stop_reason': 'tool_use' if call else 'end_turn', 'stop_sequence': None},
                    'usage': {'output_tokens': 100, 'cost': 0}}), ('message_stop', {'type': 'message_stop'})]
            data = ''.join('event: ' + event + '\ndata: ' + json.dumps(body) + '\n\n' for event, body in events)
        else:
            delta = {'role': 'assistant', 'content': 'Done.'}
            if call:
                delta = {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'call-' + str(number),
                    'type': 'function', 'function': {'name': call[0], 'arguments': json.dumps(call[1])}}]}
            events = [{'choices': [{'index': 0, 'delta': delta, 'finish_reason': None}]},
                      {'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'tool_calls' if call else 'stop'}]},
                      {'choices': [], 'usage': {'prompt_tokens': count, 'completion_tokens': 100, 'cost': 0}}]
            data = ''.join('data: ' + json.dumps({'id': 'fixture', 'model': payload['model'],
                'object': 'chat.completion.chunk', **body}) + '\n\n' for body in events) + 'data: [DONE]\n\n'
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Content-Length', str(len(data.encode())))
        self.end_headers()
        self.wfile.write(data.encode())


class FixtureBuilder(FlueBuilder):
    paid = False
    max_output_tokens = 4096  # This fixture targets the historical250k handover threshold.
class FixtureReview(FlueReview): paid = False


def main(closed_candidate=False):
    target = load_target(ROOT / 'demo/forum/targets/forum-app-013.json', ROOT)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Inference)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    class Counter:
        revision = 'synthetic-admission-bound'
        def count(self, _payload):
            return 245000 if calls['author'] == 3 else 4000
    def local_relay(model, key, limit, checkpoint, event, **kwargs):
        route = '/v1/messages' if kwargs.get('api') == 'anthropic-messages' else '/v1/chat/completions'
        return ContextRelay(model, key, limit, checkpoint, event, **kwargs,
            upstream=f'http://127.0.0.1:{server.server_port}' + route, counter=Counter())
    folder = Path(tempfile.mkdtemp(prefix='aeion-real-flue-factory-', dir='/private/tmp'))
    print(json.dumps({'state': str(folder), 'real_models': False}), flush=True)
    builder = FixtureBuilder(ROOT, {'013': target}, model='glm-5.3-flash')
    review = FixtureReview()
    try:
        with patch.dict(os.environ, {'OPENCODE_API_KEY': 'synthetic'}), patch.object(runner, 'ContextRelay', side_effect=local_relay):
            app = FactoryApp(ROOT / 'demo/forum/features/MANIFEST.json', folder / 'state',
                bootstrap_token='synthetic-only', budget=DailyBudget(folder / 'ledger.jsonl'),
                config={**S2_CONFIG,'step_cap':5,'deadline_ns':900*1_000_000_000} if closed_candidate else None,
                execution={'mode': 'live', 'targets': {'013': target}, 'builder': builder,
                           'review_complete': review, 'check_sandbox': DockerCheckRunner(ROOT),
                           'cost_reservation_usd': '0.50'})
            app.worker.require_circuit = True
            app.store.seed_merged('001', app.catalog)
            session = app.auth.login('synthetic-only')
            app.queue('127.0.0.1:8088', 'http://127.0.0.1:8088', session, session['csrf'],
                      {'ids': ['013'], 'idempotency_key': 'real-flue-fixture'})
            result = app.tick()
            row = next(row for row in app.store.board() if row['feature_id'] == '013')
            receipt = json.loads(row['receipt'])
            print(json.dumps({'status': row['status'], 'worker': result,
                'builder': builder.last_execution, 'usage': builder.last_usage,
                'gate': receipt.get('gate'), 'circuit': receipt.get('circuit'), 'calls': calls}), flush=True)
            assert row['status'] == 'simulated_complete'
            assert builder.last_execution['sessions'] == 2
            assert builder.last_feedback == (None if closed_candidate else 'RAS')
            assert receipt.get('feedback') == (None if closed_candidate else {'author': 'RAS'})
            assert checks == (['failed-feedback'] if closed_candidate else ['failed-feedback','passed-feedback'])
            if closed_candidate:
                assert builder.last_execution['failure']=='STEP_LIMIT'
                assert builder.last_execution['candidate_recovered'] is True
                assert builder.last_usage['complete'] is True
                assert builder.last_execution['check']['status']=='passed'
                assert len(receipt['circuit']['votes'])==2
            assert receipt['circuit']['status'] == 'approved'
            # Qualify the fourth allowlisted model's native protocol and explicit max effort.
            # Haiku's 4x allowance multiple projects above the 0.05 USD fixture review bound.
            probe = FixtureReview(cost_limit='0.25')
            probe.build_id = row['build_id']
            # Standalone synthetic native-protocol probe, outside the finished build lease.
            probe.authorization_check = lambda: True
            assert probe('claude-haiku-5.5', 'Review this harmless fixture: class Example {}')['verdict'] == 'approve'
            print(json.dumps({'haiku_max': True, 'calls': calls, 'state': str(folder)}), flush=True)
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__': main()
