"""Independent Flue/Pi review in tier-1 memory, with a typed one-verdict output channel."""
import json
from pathlib import Path
import tempfile

from .flue_session import FactorySession, new_run, usage
from .models import eligibility
from .review_circuit import MAX_PROMPT_CHARS

MAX_COMPLETE_REVIEW_BYTES = 240000


class FlueReview:
    paid = True
    timeout_seconds = 180

    def __init__(self, max_prompt_bytes=MAX_PROMPT_CHARS, cost_limit='0.05',max_output_tokens=4096,deepseek_effort='max'):
        from decimal import Decimal,InvalidOperation
        try:amount=Decimal(cost_limit)
        except (InvalidOperation,TypeError):raise ValueError('REVIEW_BOUNDS_INVALID') from None
        if (type(max_prompt_bytes) is not int or not 1 <= max_prompt_bytes <= MAX_COMPLETE_REVIEW_BYTES
                or not amount.is_finite() or not Decimal('0') < amount <= Decimal('1.00')
                or type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 65536
                or deepseek_effort not in ('low','max')):
            raise ValueError('REVIEW_BOUNDS_INVALID')
        self.max_prompt_bytes,self.cost_limit=max_prompt_bytes,str(cost_limit)
        self.max_output_tokens=max_output_tokens
        self.deepseek_effort=deepseek_effort
        self.last_usage = self.last_execution = None
        self.build_id = 'unbound-review'
        self.progress = None
        self.authorization_check = None

    def __call__(self, model, prompt):
        self.last_usage = self.last_execution = None
        self.last_usage = {'complete':True,'cost_usd':'0','basis':'proven_no_transport'}
        if len(prompt.encode('utf-8')) > self.max_prompt_bytes or not eligibility(model)[0]:
            raise ValueError('REVIEW_NOT_ADMITTED')
        run = new_run(model, self.build_id, 'review', self.cost_limit, synthetic=not self.paid)
        run['max_output_tokens']=self.max_output_tokens
        run['review_thinking_level']=self.deepseek_effort if model=='deepseek-4.1-flash' else 'max'
        run['inference_effort']=run['review_thinking_level']
        run['agent_timeout_seconds'] = self.timeout_seconds
        runtime = FactorySession(run, self.progress)
        runtime.authorization_check = self.authorization_check
        span = runtime.telemetry.begin(run)
        error = None
        try:
            with tempfile.TemporaryDirectory(prefix='aeion-review-') as directory:
                output = Path(directory) / 'result.json'
                self.last_usage=None
                outcome = runtime.live(run, Path(directory), None, prompt=prompt, kind='factory-review', review_result=output)
                if outcome != 'complete' or not output.is_file() or output.stat().st_size > 1024:
                    raise ValueError('REVIEW_RESULT_MISSING')
                if usage(run)['complete'] is not True:
                    raise ValueError('USAGE_UNKNOWN')
                result = json.loads(output.read_text())
                if (set(result) != {'verdict', 'reason'} or result['verdict'] not in ('approve', 'reject')
                        or not isinstance(result['reason'], str) or len(result['reason']) > 120):
                    raise ValueError('REVIEW_RESULT_INVALID')
                return result
        except Exception as caught:
            error = caught
            raise
        finally:
            self.last_usage = usage(run)
            try:
                self.last_execution = runtime.finish(run, error)
            finally:
                runtime.end_span(span,run,error)
