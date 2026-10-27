"""Routing uses comparable measured evidence, never a model-name preference."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from profiles import PROFILE_VERSION, PROFILES
from selection import recommend


def cohort(profile, cost='0.01', seconds=2, task='pricing-js-v1'):
    return [dict(id=f'{profile}-{i}', model=PROFILES[profile]['model'], task_id=task,
                 synthetic=False, profile_version=PROFILE_VERSION, runtime='openshell',
                 metric='active_context', limit=250000, status='passed',
                 started_ns=1, ended_ns=1+int(seconds*1e9), agents=1,
                 human_interventions=0, native_cost_usd=cost, usage_complete=True, events=[])
            for i in range(2)]


class SelectionTests(unittest.TestCase):
    def test_objectives_choose_from_the_same_task(self):
        runs=cohort('glm',cost='0.01',seconds=4)+cohort('glm-full',cost='0.03',seconds=1)
        self.assertEqual(recommend(runs,'pricing-js-v1','cost')['profile'],'glm')
        self.assertEqual(recommend(runs,'pricing-js-v1','speed')['profile'],'glm-full')
        self.assertEqual(recommend(runs,'cart-js-v1')['basis'],'provisional_default')
        self.assertEqual(len(recommend(runs,'pricing-js-v1')['candidates']),2)

    def test_unknown_usage_failures_and_assistance_are_not_winners(self):
        for field,value in [('usage_complete',False),('status','failed'),('human_interventions',1)]:
            with self.subTest(field=field):
                runs=cohort('glm');runs[0][field]=value
                self.assertEqual(recommend(runs,'pricing-js-v1')['basis'],'provisional_default')
        self.assertEqual(recommend(cohort('glm',cost='0'),'pricing-js-v1')['basis'],'provisional_default')
        self.assertEqual(recommend(cohort('glm')[:1],'pricing-js-v1')['basis'],'provisional_default')

    def test_synthetic_legacy_and_other_runtime_cannot_influence_routing(self):
        for field,value in [('synthetic',True),('profile_version','old'),('runtime','docker')]:
            with self.subTest(field=field):
                runs=cohort('glm')
                for run in runs:run[field]=value
                self.assertEqual(recommend(runs,'pricing-js-v1')['basis'],'provisional_default')

    def test_run_ids_are_limited_to_the_selected_gate_cohort(self):
        runs=cohort('glm')+cohort('glm',task='cart-js-v1')
        other=copy.deepcopy(cohort('glm'))
        for run in other:run.update(id='other-'+run['id'],limit=12000)
        result=recommend(runs+other,'pricing-js-v1')
        self.assertEqual(result['candidates'][0]['evidence_run_ids'],['glm-0','glm-1'])


if __name__=='__main__':unittest.main()
