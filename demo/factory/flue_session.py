"""Reuse the pinned three-tier harness lifecycle for supervised factory roles."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import os
import re
import sys
import time
import uuid

APP = Path(__file__).resolve().parents[1] / 'app'
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))
from runner import Runner
from memory import Memory
from profiles import PROFILES, PROFILE_VERSION

SESSION_TIMEOUT_SECONDS = 900
MODEL_PROFILE = {'glm-5.3-flash': 'glm', 'deepseek-4.1-flash': 'deepseek',
                 'qwen-3.8-flash': 'qwen', 'claude-haiku-5.5': 'haiku',
                 'gpt-6-luna': 'luna', 'mistral-large-4': 'mistral'}


def check_evidence(check):
    """Keep fixed checker status/cause across later agent events and interrupted roles."""
    result = {'status':check.get('status') if check.get('status') in {'passed','failed','held'} else 'not_run'}
    reason=check.get('reason')
    if isinstance(reason,str) and re.fullmatch('[a-z][a-z0-9_]{1,95}',reason):
        result['reason']=reason
    digest=check.get('artifact_digest')
    if isinstance(digest,str) and re.fullmatch('[a-f0-9]{64}',digest):
        result['artifact_digest']=digest
    return result


def new_run(model, build_id, role, cost_limit, synthetic=False):
    if model not in MODEL_PROFILE:
        raise ValueError('MODEL_NOT_ALLOWED')
    return {'id': uuid.uuid4().hex, 'build_id': build_id, 'task_id': 'factory-' + role,
            'factory_role': role,
            'langfuse_session_id': 'factory:' + build_id, 'synthetic': synthetic,
            'status': 'running', 'started_ns': time.time_ns(), 'ended_ns': None,
            'runtime': 'flue-openshell' if role == 'author' else 'flue-just-bash',
            'model': PROFILES[MODEL_PROFILE[model]]['model'], 'profile_version': PROFILE_VERSION,
            'inference_effort':'high' if model=='deepseek-4.1-flash' else 'medium' if model=='claude-haiku-5.5' else 'default',
            'limit': 250000, 'metric': 'active_context', 'native_cost_usd': '0',
            'session_cost_limit': str(cost_limit), 'agent_timeout_seconds': SESSION_TIMEOUT_SECONDS,
            'events': [], 'sessions': [], 'agents': 1, 'human_interventions': 0}


def usage(run):
    reports = run.get('provider_usages', [])
    forwarded = run.get('forwarded_count', 0)
    complete = (run.get('provider_accounting_complete', True) and forwarded > 0 and len(reports) == forwarded
                and all(item.get('complete') is True for item in reports))
    no_transport = forwarded == 0
    return {'complete': complete or no_transport,
            'cost_usd': (str(sum((Decimal(str(item['cost_usd'])) for item in reports), Decimal(0)))
                         if complete else '0' if no_transport else None),
            'basis': 'provider_reported_resource_cost' if complete else 'proven_no_transport' if no_transport else 'provider_cost_unreported',
            'estimated_cost_usd': run['native_cost_usd'],
            'input_tokens': sum(e.get('gen_ai.usage.input_tokens', 0) for e in run['events'] if e['name'] == 'gen_ai.request'),
            'output_tokens': sum(e.get('gen_ai.usage.output_tokens', 0) for e in run['events'] if e['name'] == 'gen_ai.request')}


class FactorySession(Runner):
    """The lab's real Flue/Pi/relay/bridge lifecycle, with factory-specific checkpoint data."""

    def __init__(self, run, progress=None, telemetry=None):
        self.current = run
        self.progress = progress or (lambda *_a, **_k: None)
        self.snapshot = None
        self.last_check = {'status': 'not_run'}
        if telemetry is None:
            from telemetry import Telemetry
            telemetry = Telemetry()
        super().__init__(telemetry, lambda _run: None, memory=Memory())

    def event(self, run, name, **attrs):
        super().event(run, name, **attrs)
        if name in {'model.step.started', 'tool.finished', 'gen_ai.request', 'gate.closed', 'process.started', 'process.retired'}:
            self.progress(name, {'model': run['model'], 'runtime': run['runtime'], **attrs})

    def prepare_handover(self, run, workspace, observed, basis='native_report'):
        if run['runtime'] != 'flue-openshell' or self.snapshot is None:
            raise ValueError('HANDOVER_NOT_READY')
        files = self.snapshot()
        state = {'schema': 'factory-handover-v1', 'build_id': run['build_id'],
                 'agent': run['agents'], 'observed': observed, 'basis': basis,
                 'files': {path: hashlib.sha256(text.encode()).hexdigest() for path, text in files.items()},
                 'check': self.last_check}
        text = '# Factory handover\n\n' + json.dumps(state, sort_keys=True, indent=2)
        target = workspace.parent / 'HANDOVER.md'
        temporary = target.with_suffix('.tmp')
        with temporary.open('w') as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError('HANDOVER_NOT_READY')
        state['handover_sha256'] = digest
        run['handover'] = state
        run['handover_md_sha256'] = digest
        try:
            self.memory.checkpoint(run, state)
        except Exception:
            run['memory_checkpoint'] = 'unavailable'
        self.event(run, 'handover.prepared', **{'aeion.context.observed': observed})

    def finish(self, run, error=None):
        run.update(ended_ns=time.time_ns(), status='failed' if error else 'passed')
        if error:
            code = str(error)
            run['failure'] = code if re.fullmatch(r'[A-Z][A-Z0-9_]{1,63}', code) else type(error).__name__
        self.event(run, 'task.failed' if error else 'task.passed',
                   **({'aeion.failure.code':run['failure']} if error else {}))
        measured = usage(run)
        run['usage_complete'] = measured['complete']
        check = self.last_check
        run['check'] = check_evidence(check)
        if isinstance(check.get('artifact_digest'),str) and re.fullmatch('[a-f0-9]{64}',check['artifact_digest']):
            run['artifact_sha256'] = check['artifact_digest']
        outcome = {'schema':'factory-outcome-v1','build_id':run['build_id'],'run_id':run['id'],
            'role':run['factory_role'],'model':run['model'],'runtime':run['runtime'],
            'synthetic':run['synthetic'],'status':run['status'],'trace_id':run.get('trace_id'),
            'reasoning_effort':run.get('inference_effort','default'),
            'usage_complete':measured['complete'],'cost_usd':measured['cost_usd'],
            'cost_basis':measured['basis'],'check':run['check'],'artifact_digest':run.get('artifact_sha256')}
        memories = {}
        try:
            self.memory.checkpoint(run,outcome)
            memories['claude_mem']={'status':'confirmed' if run.get('claude_mem_id') is not None else 'disabled'}
        except Exception:
            memories['claude_mem']={'status':'unavailable'}
        try:
            result=self.memory.retain_factory(run)
            memories['hindsight']={k:result[k] for k in ('status','bank','document_id') if k in result}
        except Exception:
            memories['hindsight']={'status':'unavailable'}
        return {'build_id': run['build_id'], 'run_id':run['id'], 'role':run['factory_role'],
                'engine': 'flue-pi', 'runtime': run['runtime'], 'model': run['model'],
                'started_ns':run['started_ns'], 'ended_ns':run['ended_ns'],
                'usage':measured, 'check':run['check'], 'artifact_digest':run.get('artifact_sha256'),
                'sessions': len(run['sessions']), 'trace_id': run.get('trace_id'),
                'session_id': run['langfuse_session_id'], 'forwarded_count': run.get('forwarded_count', 0),
                'failure': run.get('failure'), 'finish_reason':run.get('last_finish_reason'),
                'provider_http_status':run.get('provider_http_status'),
                'provider_retries':run.get('provider_retries',0),
                'process_exit_code':run.get('cli_exit_code'), 'cli_steps':run.get('cli_steps'),
                'retained_files_count':run.get('retained_files_count'),
                'retained_artifact_digest':run.get('retained_artifact_digest'),
                'candidate_recovered':run.get('candidate_recovered') is True,
                'reasoning_effort':run.get('inference_effort','default'), 'memory':memories}

    def end_span(self, span, run, error=None):
        """Close a role with its actual outcome, without automatic exception/content capture."""
        try:
            measured=usage(run)
            for key,value in {'role':run['factory_role'],'runtime':run['runtime'],'run_id':run['id'],
                    'usage_complete':measured['complete'],'forwarded_count':run.get('forwarded_count',0),
                    'process_exit_code':run.get('cli_exit_code'),'cli_steps':run.get('cli_steps'),
                    'accounting_basis':measured['basis']}.items():
                if value is not None:span.set_attribute('langfuse.observation.metadata.'+key,value)
            if measured['complete']:
                span.set_attribute('langfuse.observation.metadata.measured_cost_usd',measured['cost_usd'])
            if error:
                from opentelemetry.trace import Status, StatusCode
                code=run.get('failure','ROLE_FAILED')
                span.set_attribute('langfuse.observation.level','ERROR')
                span.set_attribute('langfuse.observation.status_message',code)
                if hasattr(span,'set_status'):span.set_status(Status(StatusCode.ERROR,code))
            span.end()
        finally:
            self.telemetry.provider.shutdown()
