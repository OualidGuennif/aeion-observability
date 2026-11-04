"""Late worker progress cannot revive a cancelled build or leak arbitrary tool content."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.store import Store
from factory.manifest import Catalog


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory(); self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/'state.db'
        self.store=Store(self.path)
        self.catalog=Catalog({'schema_version':2,'count':1,'features':[{
            'id':'001','title':'Fixture','area':'foundation','size':'S','parallel':False,
            'phase':'P0','tier':3,'write_paths':['demo/forum-app/'],'depends_on':[],'file':'001.md'}]})
        self.store.admit(['001'],'fixture',self.catalog)
        self.build=self.store.claim_next(self.catalog)

    def report(self, phase='checking', detail=None, generation=None):
        b=self.build
        return self.store.record_progress(b['attempt_id'],b['attempt_generation'] if generation is None else generation,
                                          phase,detail or {'status':'passed'})

    def test_progress_is_visible_after_restart_and_appears_in_event_history(self):
        self.assertTrue(self.report())
        reopened=Store(self.path)
        row=reopened.board()[0]
        self.assertEqual(json.loads(row['receipt'])['progress']['phase'],'checking')
        self.assertEqual(reopened.events(row['build_id'])[-1]['event'],'progress')

    def test_cancelled_or_stale_generation_cannot_update_progress(self):
        self.assertFalse(self.report(generation=999))
        self.store.cancel(self.build['build_id'])
        self.assertFalse(self.report())
        self.assertEqual(self.store.board()[0]['status'],'cancelled')

    def test_unknown_phase_is_refused_and_arbitrary_content_is_dropped(self):
        with self.assertRaises(ValueError): self.report('user-controlled-phase')
        self.report(detail={'status':'passed','model':'opencode-go/glm-5.3-flash',
                            'content':'SYNTHETIC_SECRET_CANARY','prompt':'SYNTHETIC_SECRET_CANARY'})
        receipt=self.store.board()[0]['receipt']
        self.assertNotIn('CANARY',receipt)
        self.assertIn('glm-5.3-flash',receipt)

    def test_identical_progress_does_not_duplicate_events(self):
        self.assertTrue(self.report())
        self.assertFalse(self.report())
        self.assertEqual(sum(e['event']=='progress' for e in self.store.events(self.build['build_id'])),1)

    def test_untyped_metadata_is_discarded_without_crashing_the_worker(self):
        self.assertTrue(self.report(detail={'model':[], 'runtime':{}, 'status':[], 'step':True}))
        self.assertEqual(json.loads(self.store.board()[0]['receipt'])['progress']['detail'],{})


if __name__=='__main__': unittest.main()
