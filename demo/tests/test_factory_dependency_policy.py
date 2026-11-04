"""Dependency exceptions are exact supervisor data, scope-bound and frozen into receipts."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.freeze import FreezeError,freeze_build


class DependencyPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'002.md').write_text('# Migration fixture\n')
        self.catalog=SimpleNamespace(digest='f'*64,by_id={'002':{'file':'002.md','tier':3,
            'parallel':False,'depends_on':[],'write_paths':['demo/forum-app/']}})
        self.build={'build_id':'a'*32,'feature_id':'002'}
        self.config={'profile':'synthetic-fixture','mode':'fake','deadline_ns':60_000_000_000,
            'step_cap':12,'context_limit':250000,'cost_reservation_usd':'1.00'}

    def freeze(self,config=None,scopes=None):
        return freeze_build(self.build,self.catalog,self.root,'b'*40,config or self.config,write_scopes=scopes)

    def test_existing_receipt_identity_is_preserved_without_an_exception(self):
        frozen=self.freeze();legacy=asdict(frozen);legacy.pop('dependency_changes')
        expected=hashlib.sha256(json.dumps(legacy,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.assertEqual(frozen.digest(),expected)

    def test_exact_hashes_are_copied_and_participate_in_the_frozen_identity(self):
        policy={'demo/forum-app/build.gradle':'c'*64}
        config={**self.config,'dependency_changes':policy}
        frozen=self.freeze(config);original=frozen.digest()
        policy['demo/forum-app/build.gradle']='d'*64
        self.assertEqual(frozen.dependency_changes['demo/forum-app/build.gradle'],'c'*64)
        self.assertEqual(frozen.digest(),original)
        self.assertNotEqual(self.freeze(config).digest(),original)

    def test_only_known_manifest_paths_and_valid_hashes_within_the_scope_are_admitted(self):
        for policy in ({},{'demo/forum-app/.env':'c'*64},{'.github/workflows/ci.yml':'c'*64},
                       {'demo/forum-app/build.gradle':'not-a-hash'},['untrusted'],
                       {'demo/forum-web/package.json':None}):
            with self.subTest(policy=policy),self.assertRaisesRegex(FreezeError,'invalid_dependency_policy'):
                self.freeze({**self.config,'dependency_changes':policy})
        with self.assertRaisesRegex(FreezeError,'dependency_policy_out_of_scope'):
            self.freeze({**self.config,'dependency_changes':{'demo/forum-app/build.gradle':'c'*64}},
                        scopes=['demo/forum-app/src/main/java/'])


if __name__=='__main__':unittest.main()
