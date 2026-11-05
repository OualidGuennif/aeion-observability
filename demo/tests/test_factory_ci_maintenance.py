"""A rejected CI proposal may be corrected; approvals and unknown costs cannot be reused."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('ci_maintenance',ROOT/'work/product-ci-adapters-2026-11-05/maintain.py')
maintenance=importlib.util.module_from_spec(spec);spec.loader.exec_module(maintenance)


class MaintenanceTests(unittest.TestCase):
    def prepare_again(self, *, rejected=True, complete=True, remote=False):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        state=Path(temporary.name)
        old={name:'old public fixture\n' for name in maintenance.ALLOWED}
        new={**old,'.github/workflows/ci.yml':'corrected public fixture\n'}
        digest=maintenance.content_digest(old)
        (state/'request.json').write_text(json.dumps({'files':old,'artifact_digest':digest}))
        (state/'check.json').write_text(json.dumps({'status':'passed'}))
        votes=[{'model':model,'answer':{'verdict':'reject' if rejected and model.startswith('qwen') else 'approve'},
            'usage':{'complete':complete,'cost_usd':'0.01' if complete else None}}
            for model in ('glm-5.3-flash','qwen-3.8-flash')]
        (state/'reviews.json').write_text(json.dumps(votes))
        if remote:(state/'remote.json').write_text('{}')
        def run():
            with patch.object(maintenance,'STATE',state),patch.object(maintenance,'files',return_value=new), \
                    patch.object(sys,'argv',['maintain','prepare']),contextlib.redirect_stdout(io.StringIO()):
                maintenance.main()
        return state,digest,old,new,run

    def test_known_rejection_is_archived_and_the_new_proposal_has_no_inherited_votes(self):
        state,digest,old,new,run=self.prepare_again()
        run()
        self.assertEqual(json.loads((state/'previous'/digest/'request.json').read_text())['files'],old)
        self.assertEqual(len(json.loads((state/'previous'/digest/'reviews.json').read_text())),2)
        self.assertEqual(json.loads((state/'request.json').read_text())['files'],new)
        self.assertFalse((state/'reviews.json').exists())
        self.assertFalse((state/'check.json').exists())

    def test_approved_unknown_or_published_jobs_are_preserved(self):
        for options in ({'rejected':False},{'complete':False},{'remote':True}):
            with self.subTest(options=options):
                state,_,old,_,run=self.prepare_again(**options)
                with self.assertRaisesRegex(ValueError,'preserve_existing_request'):run()
                self.assertEqual(json.loads((state/'request.json').read_text())['files'],old)
                self.assertTrue((state/'reviews.json').exists())
                self.assertFalse((state/'previous').exists())


if __name__=='__main__':unittest.main()
