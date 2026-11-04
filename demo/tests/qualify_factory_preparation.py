"""Real automatic Java preparation and Flue/OpenShell execution, scripted inference only.

Uses a historical Java/SQLite source and a disposable one-feature MD. This does not qualify
the PostgreSQL/React adapters, real provider efficacy, GitHub writes or main integration.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'demo/tests'), str(ROOT / 'demo'), str(ROOT / 'demo/app')]
import qualify_factory_flue as fixture
from factory.api import FactoryApp
from factory.budget import DailyBudget
from factory.isolation import DockerCheckRunner
from factory.preparation import TaskPreparer, FluePreparation
from factory.target import load_target
from relay import ContextRelay
import runner


class FixturePreparation(FluePreparation):
    paid = False


def main():
    target = load_target(ROOT / 'demo/forum/targets/forum-app-013.json', ROOT)
    fixture.preparation_contract = target.protected_check.contract_test.read_text().replace(
        'SecurityHeadersContractTest', 'FactoryAcceptance013Test')
    server = ThreadingHTTPServer(('127.0.0.1', 0), fixture.Inference)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    folder = Path(tempfile.mkdtemp(prefix='aeion-real-preparation-', dir='/private/tmp'))
    print(json.dumps({'state': str(folder), 'real_models': False, 'architecture_qualified': False}), flush=True)
    spec = '# 013 Security headers\n\n## Acceptance checks\n- [ ] Enforce CSP, nosniff and no-referrer on health and refusals.\n'
    (folder / '013.md').write_text(spec)
    architecture = (ROOT / 'demo/forum/ARCHITECTURE.md').read_bytes()
    (folder / 'MANIFEST.json').write_text(json.dumps({'schema_version':2,'count':1,'features':[{
        'id':'013','title':'Security headers','area':'foundation','size':'S','phase':'P0','tier':3,
        'parallel':False,'depends_on':[],'write_paths':['demo/forum-app/'],'file':'013.md',
        'architecture_digest':hashlib.sha256(architecture).hexdigest()}]}))
    checker = DockerCheckRunner(ROOT)
    role = FixturePreparation()
    preparer = TaskPreparer(ROOT, target.base_source, role=role, checker=checker, base_ref=target.base_sha)
    builder, review = fixture.FixtureBuilder(ROOT, {}), fixture.FixtureReview()
    class Counter:
        revision = 'synthetic-admission-bound'
        def count(self, _payload):
            return 245000 if fixture.calls['author'] == 3 else 4000
    def local_relay(model, key, limit, checkpoint, event, **kwargs):
        route = '/v1/messages' if kwargs.get('api') == 'anthropic-messages' else '/v1/chat/completions'
        return ContextRelay(model, key, limit, checkpoint, event, **kwargs,
            upstream=f'http://127.0.0.1:{server.server_port}' + route, counter=Counter())
    try:
        with patch.dict(os.environ, {'OPENCODE_API_KEY':'synthetic'}), patch.object(runner,'ContextRelay',side_effect=local_relay):
            app = FactoryApp(folder / 'MANIFEST.json', folder / 'state', bootstrap_token='synthetic-only',
                budget=DailyBudget(folder / 'ledger.jsonl'), execution={'mode':'live','preparer':preparer,
                    'builder':builder,'review_complete':review,'check_sandbox':checker,'cost_reservation_usd':'0.50'})
            app.worker.require_circuit = True
            session = app.auth.login('synthetic-only')
            app.queue('127.0.0.1:8088','http://127.0.0.1:8088',session,session['csrf'],
                      {'ids':['013'],'idempotency_key':'automatic-java-preparation-fixture'})
            result=app.tick()
            row=app.store.board()[0]
            receipt=json.loads(row['receipt'])
            print(json.dumps({'status':row['status'],'worker':result,'preparation':receipt.get('preparation'),
                'preparation_execution':role.last_execution,'builder':builder.last_execution,
                'gate':receipt.get('gate'),'circuit':receipt.get('circuit'),'calls':fixture.calls}),flush=True)
            assert row['status']=='simulated_complete'
            assert receipt['preparation']['negative_control']=='failed_contract_assertion'
            assert receipt['preparation']['synthetic'] is True
            assert receipt['circuit']['status']=='approved'
            for execution in (role.last_execution,builder.last_execution,
                              *(vote['execution'] for vote in receipt['circuit']['votes'])):
                assert execution['memory']['claude_mem']['status']=='confirmed'
                assert execution['memory']['hindsight']['status']=='confirmed'
            models={builder.model,receipt['preparation']['preparer_model'],
                    *(vote['model'] for vote in receipt['circuit']['votes'])}
            assert len(models)==4
            assert builder.last_execution['sessions']==2
            assert fixture.checks==['failed-feedback','passed-feedback']
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
