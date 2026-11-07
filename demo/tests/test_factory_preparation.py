"""Automatic MD preparation freezes real Git bytes and refuses ineffective acceptance.

Inference and the compiler/check process are synthetic unit-test boundaries here.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.budget import DailyBudget
from factory.manifest import Catalog
from factory.models import Router
from factory.preparation import TaskPreparer, PreparationError, freeze_task

CONTRACT = '''package local.aeion.forum;
class FactoryAcceptance007Test {
    @Test void rejectsUntrustedHtml() { assertEquals("safe", "unsafe"); }
}
'''


class ScriptedRole:
    paid = False
    last_execution = None

    def __init__(self, cost='0', complete=True):
        self.calls = []
        self.cost,self.complete=cost,complete
        self.last_usage = None

    def __call__(self, model, prompt, build_id):
        self.last_usage = {'complete': self.complete, 'cost_usd': self.cost}
        self.calls.append((model, prompt, build_id))
        return {'status': 'ready', 'contract': CONTRACT, 'reason': 'Synthetic fixture'}


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        architecture = self.root / 'demo/forum/ARCHITECTURE.md'
        architecture.parent.mkdir(parents=True)
        architecture.write_text('Approved Java/PostgreSQL/React product architecture.\n')
        self.architecture = architecture
        self.specs = self.root / 'specs'
        self.specs.mkdir()
        self.spec = self.specs / '007.md'
        self.spec.write_text('# 007\n## Acceptance checks\n- [ ] Unsafe HTML is removed.\n')
        self.catalog = Catalog({'schema_version': 2, 'count': 1, 'features': [{
            'id': '007', 'title': 'Sanitize HTML', 'area': 'foundation', 'size': 'S',
            'phase': 'P0', 'parallel': False, 'tier': 3, 'file': '007.md',
            'write_paths': ['demo/forum-app/'], 'depends_on': [],
            'architecture_digest': hashlib.sha256(architecture.read_bytes()).hexdigest()}]})
        self.source = self.root / 'product'
        (self.source / 'demo/forum-app').mkdir(parents=True)
        (self.source / 'demo/forum-app/build.gradle').write_text('// Trusted baseline fixture\n')
        for command in (['init', '-q'], ['config', 'user.name', 'Fixture'],
                        ['config', 'user.email', 'fixture@example.invalid'], ['add', '.'],
                        ['commit', '-qm', 'baseline']):
            self.git(*command)
        self.base = self.git('rev-parse', 'HEAD').stdout.strip()
        self.role = ScriptedRole()
        self.budget = DailyBudget(self.root / 'ledger.jsonl')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.source), *args],
                              capture_output=True, text=True, check=True)

    def checker(self, command, **kwargs):
        self.assertIn('--offline', command)
        self.assertNotIn('GH_API_KEY', kwargs['env'])
        report=Path(kwargs['cwd']) / 'demo/forum-app/build/test-results/test/TEST-local.aeion.forum.FactoryAcceptance007Test.xml'
        report.parent.mkdir(parents=True)
        report.write_text('<testsuite><testcase classname="local.aeion.forum.FactoryAcceptance007Test">'
                          '<failure type="java.lang.AssertionError" /></testcase></testsuite>')
        return subprocess.CompletedProcess(command, 1,
            stdout='FactoryAcceptance007Test > rejectsUntrustedHtml FAILED\n', stderr='')

    def prepare(self, checker=None, authorized=lambda: True, synchronize=None, base_ref='HEAD'):
        return TaskPreparer(self.root, self.source, role=self.role,
            checker=checker or self.checker, base_ref=base_ref,synchronize=synchronize).prepare(
                build={'feature_id':'007', 'build_id':'a'*32, 'attempt_id':'b'*32},
                catalog=self.catalog, spec_dir=self.specs, destination=self.root / 'prepared',
                budget=self.budget, router=Router(), authorized=authorized)

    def test_synchronized_main_is_frozen_and_a_sync_failure_never_spends_model_budget(self):
        self.git('update-ref','refs/remotes/origin/main',self.base)
        path=self.source/'demo/forum-app/new-baseline.txt';path.write_text('new remote commit\n')
        self.git('add','.');self.git('commit','-qm','new main')
        latest=self.git('rev-parse','HEAD').stdout.strip()
        def sync():
            self.git('update-ref','refs/remotes/origin/main',latest,self.base)
            return latest
        target,_=self.prepare(synchronize=sync,base_ref='refs/remotes/origin/main')
        self.assertEqual(target.base_sha,latest)
        from factory.source import SourceSyncError
        def unavailable():raise SourceSyncError('source_fetch_failed')
        before=len(self.role.calls)
        with self.assertRaisesRegex(PreparationError,'source_fetch_failed'):
            self.prepare(synchronize=unavailable,base_ref='refs/remotes/origin/main')
        self.assertEqual(len(self.role.calls),before)
        self.assertEqual(self.budget.summary()['aeion-autonomous-forum']['spent_usd'],'0.00')

    def test_complete_md_architecture_base_scopes_and_contract_are_bound_without_manual_target_json(self):
        target, evidence = self.prepare()
        self.assertEqual(target.base_sha, self.base)
        self.assertEqual(target.brief.read_bytes(), self.spec.read_bytes())
        self.assertEqual(evidence['spec_digest'], hashlib.sha256(self.spec.read_bytes()).hexdigest())
        self.assertEqual(evidence['acceptance_digest'], hashlib.sha256(CONTRACT.encode()).hexdigest())
        self.assertEqual(evidence['negative_control'], 'failed_contract_assertion')
        self.assertTrue(all('/src/' in scope for scope in target.write_paths))
        self.assertNotIn('build.gradle', ' '.join(target.write_paths))
        self.assertNotEqual(target.protected_check.contract_test.parent, self.source)
        self.assertEqual(json.loads((self.root / 'prepared/task.json').read_text()), evidence)
        self.assertEqual(self.git('status', '--porcelain').stdout, '')
        self.assertEqual(len(self.role.calls), 1)

    def test_already_passing_baseline_is_not_evidence_of_a_new_feature(self):
        def already_passes(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, stdout='', stderr='')
        with self.assertRaisesRegex(PreparationError, 'negative_control_missing'):
            self.prepare(checker=already_passes)

    def test_preparer_sees_complete_public_interfaces_from_the_pinned_commit_only(self):
        path=self.source / 'demo/forum-app/src/main/java/local/aeion/forum/ApiResource.java'
        path.parent.mkdir(parents=True)
        path.write_text('@Path("/api/fixture") class ApiResource { /* COMMITTED_PUBLIC_INTERFACE */ }\n')
        self.git('add','.');self.git('commit','-qm','public interface')
        path.write_text('@Path("/api/fixture") class ApiResource { /* UNCOMMITTED_CANARY */ }\n')
        self.prepare()
        prompt=self.role.calls[0][1]
        self.assertIn('COMMITTED_PUBLIC_INTERFACE',prompt)
        self.assertNotIn('UNCOMMITTED_CANARY',prompt)

    def test_public_http_routes_are_selected_by_annotation_instead_of_filename_suffix(self):
        folder=self.source/'demo/forum-app/src/main/java/local/aeion/forum'
        folder.mkdir(parents=True)
        (folder/'SchemaEndpoint.java').write_text('@Path("/api/schema") class SchemaEndpoint { /* SCHEMA_HTTP_CONTRACT */ }\n')
        (folder/'InternalResource.java').write_text('class InternalResource { /* NOT_AN_HTTP_INTERFACE */ }\n')
        self.git('add','.');self.git('commit','-qm','HTTP interface naming fixture')
        self.prepare()
        prompt=self.role.calls[0][1]
        self.assertIn('SCHEMA_HTTP_CONTRACT',prompt)
        self.assertNotIn('NOT_AN_HTTP_INTERFACE',prompt)

    def test_compiler_or_unrelated_test_failure_does_not_qualify_acceptance(self):
        def broken(command, **kwargs):
            return subprocess.CompletedProcess(command, 1,
                stdout='OtherTest > unrelated FAILED\nBroken.java:3: error: missing type\n', stderr='')
        with self.assertRaisesRegex(PreparationError, 'negative_control_missing'):
            self.prepare(checker=broken)

    def test_initialization_failure_is_not_a_load_bearing_acceptance_assertion(self):
        def failed_startup(command,**kwargs):
            result=self.checker(command,**kwargs)
            report=Path(kwargs['cwd']) / 'demo/forum-app/build/test-results/test/TEST-local.aeion.forum.FactoryAcceptance007Test.xml'
            report.write_text('<testsuite><testcase classname="local.aeion.forum.FactoryAcceptance007Test">'
                              '<failure type="java.lang.RuntimeException" /></testcase></testsuite>')
            return result
        with self.assertRaisesRegex(PreparationError,'negative_control_missing'):
            self.prepare(checker=failed_startup)

    def test_architecture_drift_and_symlinked_md_are_refused_before_inference_or_spend(self):
        self.architecture.write_text('Changed architecture')
        with self.assertRaisesRegex(PreparationError, 'architecture_changed'):
            self.prepare()
        self.assertEqual(self.role.calls, [])
        self.spec.unlink()
        self.spec.symlink_to(self.architecture)
        with self.assertRaises(PreparationError):
            freeze_task(self.catalog, '007', self.specs, self.architecture, self.base)

    def test_web_scope_is_not_silently_certified_by_a_java_check(self):
        self.catalog.by_id['007']['write_paths'] = ['demo/forum-web/']
        self.catalog = Catalog(self.catalog.raw)  # This scope was declared before admission.
        with self.assertRaisesRegex(PreparationError, 'profile_unavailable'):
            self.prepare()
        self.assertEqual(self.role.calls, [])

    def test_revocation_stops_preparation_before_any_model_call(self):
        with self.assertRaisesRegex(PreparationError, 'revoked'):
            self.prepare(authorized=lambda: False)
        self.assertEqual(self.role.calls, [])

    def test_unknown_preparer_usage_keeps_its_own_reservation_open(self):
        self.role = ScriptedRole(cost=None, complete=False)
        with self.assertRaisesRegex(PreparationError,'preparation_usage_unknown'):
            self.prepare()
        self.assertEqual(str(self.budget.spent('aeion-autonomous-forum')), '0.50')

    def _contract(self, feature='007', spec='# 007\n', acceptance='export function ready() {}\n',
                  paths=None):
        folder = self.root / 'prepared' / feature
        if folder.exists():
            raise AssertionError('fixture folder already exists')
        folder.mkdir(parents=True)
        paths = paths or ['demo/forum-app/src/main/java/local/aeion/forum/']
        identity = {'feature_id': feature, 'catalog_digest': 'a' * 64, 'spec_digest': _sha(spec),
                    'architecture_digest': 'b' * 64, 'base_sha': self.base, 'write_paths': list(paths)}
        evidence = {**identity, 'task_digest': _sha(json.dumps(identity, sort_keys=True, separators=(',', ':'))),
                    'acceptance_digest': _sha(acceptance), 'preparer_model': 'glm-5.3-flash',
                    'negative_control': 'failed_contract_assertion', 'synthetic': True}
        (folder / 'task.json').write_text(json.dumps(evidence), encoding='utf-8')
        (folder / 'BRIEF.md').write_text(spec, encoding='utf-8')
        (folder / 'acceptance.mjs').write_text(acceptance, encoding='utf-8')
        return folder

    def _preparer(self):
        preparer = TaskPreparer(self.root, self.source, role=self.role, product=True)
        preparer.last_model = 'glm-5.3-flash'
        self.role.last_execution = {'forwarded_count': 4}
        self.role.last_usage = {'complete': True, 'cost_usd': '0.50'}
        return preparer

    def test_a_product_resume_reuses_the_prepared_contract_without_a_model(self):
        folder = self._contract()
        preparer = self._preparer()
        target, evidence = preparer.resume_prepared(folder)
        self.assertEqual(target.feature_id, '007')
        self.assertEqual(target.brief, folder / 'BRIEF.md')
        self.assertEqual(target.protected_check.contract_test, folder / 'acceptance.mjs')
        self.assertEqual(evidence['feature_id'], '007')
        self.assertIsNone(preparer.last_model)
        self.assertIsNone(self.role.last_execution)
        self.assertIsNone(self.role.last_usage)

    def test_a_linked_or_altered_prepared_contract_is_refused(self):
        folder = self._contract()
        preparer = self._preparer()
        linked = self.root / 'linked-prepared'
        linked.symlink_to(folder, target_is_directory=True)
        with self.assertRaisesRegex(PreparationError, 'preparation_workspace_refused'):
            preparer.resume_prepared(linked)
        brief = folder / 'BRIEF.md'
        brief.write_text(brief.read_text() + '\n', encoding='utf-8')
        with self.assertRaisesRegex(PreparationError, 'preparation_workspace_refused'):
            preparer.resume_prepared(folder)
        for feature in ('002', '014'):
            with self.assertRaisesRegex(PreparationError, 'preparation_workspace_refused'):
                preparer.resume_prepared(self._contract(feature=feature))
        plain = TaskPreparer(self.root, self.source, role=self.role, product=False)
        with self.assertRaisesRegex(PreparationError, 'preparation_workspace_refused'):
            plain.resume_prepared(self._contract(feature='008'))


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


if __name__ == '__main__':
    unittest.main()
