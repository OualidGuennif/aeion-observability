"""Measured routing survives restart without learning from fixtures or another task cohort."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.store import Store
from factory.routing import OutcomeTelemetry, cohort_for
from factory.models import Router


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'factory.db'
        self.store = Store(self.path)
        self.cohort = cohort_for({'area': 'foundation', 'size': 'S', 'architecture_digest': 'a' * 64}, 'gradle_test')

    def telemetry(self, attempt='attempt-1', synthetic=False, cohort=None):
        return OutcomeTelemetry(self.store, cohort or self.cohort, attempt, synthetic=synthetic)

    def test_real_outcomes_survive_a_new_store_and_router(self):
        self.telemetry().record('glm-5.3-flash', 'author', 'passed', 1000, '0.02')
        rows = OutcomeTelemetry(Store(self.path), self.cohort, 'attempt-2').records
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['cost_usd'], '0.02')

    def test_same_attempt_role_model_is_idempotent_but_conflicting_evidence_refuses(self):
        item = self.telemetry()
        item.record('glm-5.3-flash', 'author', 'failed', 1000, None)
        item.record('glm-5.3-flash', 'author', 'failed', 1000, None)
        self.assertEqual(len(self.telemetry('other').records), 1)
        with self.assertRaisesRegex(ValueError, 'outcome_conflict'):
            item.record('glm-5.3-flash', 'author', 'passed', 1000, '0')

    def test_synthetic_outcomes_never_enter_live_evidence(self):
        self.telemetry(synthetic=True).record('glm-5.3-flash', 'author', 'passed', 1000, '0')
        self.assertEqual(self.telemetry('other').records, [])

    def test_cold_start_does_not_invent_model_quality_or_measured_prices(self):
        from factory.models import MODELS
        self.assertTrue(all('quality' not in spec and 'cost' not in spec for spec in MODELS.values()))
        router=Router(self.telemetry('new'))
        self.assertEqual(router.select('author'),'glm-5.3-flash')
        self.assertEqual(router.last_decision['basis'],'cold_start_prior')

    def test_role_and_cohort_do_not_mix(self):
        self.telemetry().record('glm-5.3-flash', 'review', 'approved', 1000, '0.01')
        other = cohort_for({'area': 'corpus', 'size': 'M', 'architecture_digest': 'a' * 64}, 'gradle_test')
        self.assertEqual(self.telemetry(cohort=other).records, [])
        self.assertEqual(self.telemetry().stats('glm-5.3-flash', 'author')['n'], 0)

    def test_different_enforced_execution_bounds_never_share_model_measurements(self):
        feature={'area':'foundation','size':'S','architecture_digest':'a'*64}
        before=cohort_for(feature,'prepared_product',execution_bounds={'step_cap':12,'deadline_ns':900000000000})
        after=cohort_for(feature,'prepared_product',execution_bounds={'step_cap':200,'deadline_ns':900000000000})
        self.assertNotEqual(before,after)
        self.telemetry(cohort=before).record('glm-5.3-flash','author','failed',1000,'0.03')
        self.assertEqual(self.telemetry(cohort=after).records,[])
        prior_treatment=cohort_for(feature,'prepared_product',treatment='relay-v1')
        next_treatment=cohort_for(feature,'prepared_product',treatment='relay-v2')
        self.assertNotEqual(prior_treatment,next_treatment)
        self.telemetry(cohort=prior_treatment).record('glm-5.3-flash','author','passed',1000,'0.02')
        self.assertEqual(self.telemetry(cohort=next_treatment).records,[])

    def test_unknown_cost_is_not_free_or_an_eligible_cost_measurement(self):
        self.telemetry().record('glm-5.3-flash', 'author', 'failed', 1000, None)
        stats = self.telemetry().stats('glm-5.3-flash', 'author')
        self.assertEqual(stats['n'], 1)
        self.assertIsNone(stats['avg_cost_usd'])
        self.assertFalse(stats['usage_complete'])

    def test_unknown_outcome_is_not_a_measured_model_failure(self):
        self.telemetry().record('glm-5.3-flash','author','unknown',1000,None)
        stats=self.telemetry().stats('glm-5.3-flash','author')
        self.assertEqual(stats['n'],1)
        self.assertIsNone(stats['success_rate'])
        self.assertEqual(Router(self.telemetry('next')).select('author'),'glm-5.3-flash')

    def test_observed_cost_and_latency_change_choice_only_with_comparable_evidence(self):
        for number in range(3):
            self.telemetry('glm-' + str(number)).record('glm-5.3-flash', 'author', 'passed', 20000, '0.10')
            self.telemetry('qwen-' + str(number)).record('qwen-3.8-flash', 'author', 'passed', 1000, '0.01')
        router = Router(self.telemetry('new'))
        self.assertEqual(router.select('author', require_role='author'), 'qwen-3.8-flash')
        self.assertEqual(router.last_decision['basis'], 'measured_cost_latency')
        self.assertEqual(router.last_decision['cohort'], self.cohort)

    def test_rejection_is_valid_protocol_response_not_evidence_of_correctness(self):
        self.telemetry().record('glm-5.3-flash', 'review', 'rejected', 1000, '0.01')
        row = self.telemetry().records[0]
        self.assertNotIn('quality', row)
        self.assertEqual(row['outcome'], 'rejected')

    def test_invalid_money_and_untrusted_outcomes_are_refused(self):
        for value in ('NaN', '-1', 'Infinity'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.telemetry().record('glm-5.3-flash', 'author', 'passed', 1000, value)
        with self.assertRaises(ValueError):
            self.telemetry().record('arbitrary-model', 'author', 'passed', 1000, '0.01')


if __name__ == '__main__': unittest.main()
