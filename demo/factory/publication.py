"""Durable PR/CI/main continuation using isolated short-lived credential roles.

Spec: knowledge/components/factory-flue.md
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from .publisher import independent_circuit

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = 'OualidGuennif/aeion-autonomous-forum'


class RoleExecutor:
    real = True

    def __init__(self, state_dir, repo=REPOSITORY):
        self.state_dir, self.repo = Path(state_dir).resolve(), repo

    def __call__(self, job):
        role = 'publish' if job['phase'] == 'publish' else 'release'
        argv = [sys.executable, str(ROOT / 'demo/factory/publication_role.py'),
                '--state', str(self.state_dir), '--repo', self.repo, '--role', role,
                '--attempt', job['attempt_id'], '--lease', job['lease_owner']]
        # The role reloads one credential internally; no parent credential is inherited.
        env = {'PATH':os.environ.get('PATH','/usr/bin:/bin'),'LANG':'C.UTF-8',
               'HOME':'/nonexistent','PYTHONDONTWRITEBYTECODE':'1'}
        try:
            result = subprocess.run(argv,env=env,capture_output=True,text=True,timeout=180)
        except (OSError,subprocess.TimeoutExpired):
            return {'status':'pending','reason':'forge_reconciliation_required'}
        # Stdout is a bounded typed protocol; stderr is never copied to receipts or UI.
        if result.returncode or len(result.stdout.encode()) > 16384:
            return {'status':'pending','reason':'publisher_unavailable'}
        try:
            body=json.loads(result.stdout)
        except ValueError:
            return {'status':'pending','reason':'publisher_response_invalid'}
        if not isinstance(body,dict) or body.get('status') not in {'published','pending','held','merged'}:
            return {'status':'pending','reason':'publisher_response_invalid'}
        if body['status']=='merged' and any(not isinstance(body.get(k),str)
                or not re.fullmatch('[a-f0-9]{40}',body[k]) for k in ('merge_sha','main_sha')):
            return {'status':'held','reason':'merge_not_confirmed'}
        return body


class PublicationCoordinator:
    def __init__(self, store, executor=None, repo=REPOSITORY):
        self.store,self.repo=store,repo
        self.executor=executor or RoleExecutor(Path(store.path).parent,repo)

    def stage(self, build, request, receipt):
        if (request.get('target_repo') != self.repo or not independent_circuit(receipt.get('circuit'))
                or (receipt.get('gate') or {}).get('status')!='passed'
                or (receipt.get('review') or {}).get('status')!='approved'):
            raise ValueError('publication_evidence_invalid')
        receipt={**receipt,'publisher':{'status':'pending','reason':'publication_queued'}}
        return self.store.stage_publication(build,request,receipt)

    def run_once(self):
        job=self.store.claim_publication()
        if job is None:return None
        result=self.executor(job)
        if not isinstance(result,dict):result={'status':'pending','reason':'publisher_response_invalid'}
        # Every CI polling result keeps the known PR identity visible on the board.
        if job['remote'] and not result.get('pr'):result={**result,'pr':job['remote']}
        transition=self.store.finish_publication(job,result,simulated=not self.executor.real)
        return {'build_id':job['build_id'],'result':transition}
