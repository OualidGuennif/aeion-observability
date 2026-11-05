"""Bounded, immutable real outcome evidence in the existing supervisor database.

Spec: knowledge/components/factory-flue.md
"""
from decimal import Decimal, InvalidOperation
import hashlib
import json

from .models import Telemetry, known
from app.profiles import PROFILE_VERSION

METHOD = 'flue-factory-routing-v3'


def cohort_for(feature, check_profile, runtime='flue-openshell', execution_bounds=None):
    """Only maintainer-controlled task metadata defines a comparable cohort."""
    fields = {'method': METHOD, 'area': feature['area'], 'size': feature['size'],
              'architecture': feature.get('architecture_digest', 'legacy'),
              'check': check_profile, 'runtime': runtime, 'profile_version':PROFILE_VERSION}
    if execution_bounds is not None:fields['execution_bounds']=execution_bounds
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()


class OutcomeTelemetry(Telemetry):
    def __init__(self, store, cohort, attempt_id, synthetic=False):
        super().__init__()
        self.store, self.cohort, self.attempt_id = store, cohort, attempt_id
        self.synthetic = bool(synthetic)
        self.records = [] if self.synthetic else store.routing_read(cohort)

    def record(self, model, purpose, outcome, latency_ms=None, cost_usd=None):
        if (not known(model) or purpose not in {'author', 'review', 'prepare'}
                or outcome not in {'passed', 'failed', 'approved', 'rejected', 'error', 'unknown'}
                or (latency_ms is not None and (type(latency_ms) is not int or latency_ms < 0))):
            raise ValueError('invalid_routing_outcome')
        if ((purpose == 'review' and outcome not in {'approved', 'rejected', 'error', 'unknown'})
                or (purpose != 'review' and outcome not in {'passed', 'failed', 'error', 'unknown'})):
            raise ValueError('invalid_routing_outcome')
        cost = None
        if cost_usd is not None:
            try:
                amount = Decimal(str(cost_usd))
                if not amount.is_finite() or amount < 0 or amount > 1000:
                    raise ValueError('invalid_routing_cost')
                cost = format(amount.normalize(), 'f')
            except (InvalidOperation, TypeError):
                raise ValueError('invalid_routing_cost') from None
        row = {'model': model, 'purpose': purpose, 'outcome': outcome,
               'latency_ms': latency_ms, 'cost_usd': cost}
        if self.synthetic:
            super().record(model, purpose, outcome, latency_ms, cost)
            return
        identity = hashlib.sha256(json.dumps([self.cohort, self.attempt_id, purpose, model]).encode()).hexdigest()
        self.store.routing_record(identity, self.cohort, row)
        self.records = self.store.routing_read(self.cohort)

    def stats(self, model, purpose=None):
        rows = [r for r in self.records if r['model'] == model
                and (purpose is None or r['purpose'] == purpose)]
        valid = {'passed', 'approved', 'rejected'}
        known_outcomes = [r for r in rows if r['outcome'] != 'unknown']
        costs = [Decimal(r['cost_usd']) for r in rows if r['cost_usd'] is not None]
        durations = [r['latency_ms'] for r in rows if r['latency_ms'] is not None]
        return {'n': len(rows),
                'success_rate': (sum(r['outcome'] in valid for r in known_outcomes) / len(known_outcomes)
                                 if known_outcomes else None),
                'avg_cost_usd': float(sum(costs) / len(costs)) if costs else None,
                'avg_latency_ms': sum(durations) / len(durations) if durations else None,
                'usage_complete': bool(rows) and len(costs) == len(rows),
                'latency_complete': bool(rows) and len(durations) == len(rows),
                'outcomes_complete': bool(rows) and all(r['outcome'] != 'unknown' for r in rows)}
