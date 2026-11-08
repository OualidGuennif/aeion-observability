"""Frozen author bounds stop work before another model/tool session, across handovers."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import base64
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.flue_builder import FlueBuilder, BuilderError
from app.runner import factory_work_limit
from factory.agent_files import parse_files


class WorkLimitTests(unittest.TestCase):
    def test_author_window_defaults_to_thirty_minutes_and_is_capped_at_three_hours(self):
        from factory.flue_session import SESSION_TIMEOUT_SECONDS
        from factory.freeze import AUTHOR_TIMEOUT_SECONDS, AUTHOR_TIMEOUT_CEILING_SECONDS
        self.assertEqual(AUTHOR_TIMEOUT_SECONDS,1800)
        self.assertEqual(AUTHOR_TIMEOUT_CEILING_SECONDS,10800)
        self.assertEqual(FlueBuilder.timeout_seconds,AUTHOR_TIMEOUT_SECONDS)
        self.assertEqual(SESSION_TIMEOUT_SECONDS,900)

    def test_interrupted_worker_recovers_only_a_valid_export_with_complete_accounting(self):
        name='demo/forum-app/src/main/java/local/aeion/forum/Partial.java'
        original=b'package local.aeion.forum; class Partial {}\n'
        changed=b'package local.aeion.forum; class Partial { int value=1; }\n'
        for valid,complete,forwards,code,recover in ((True,True,0,'STEP_LIMIT',False),
                (False,True,1,'STEP_LIMIT',False),(True,False,1,'STEP_LIMIT',False),
                (True,True,1,'ATTEMPT_REVOKED',False),(True,True,1,'STEP_LIMIT',True)):
            with self.subTest(valid=valid,complete=complete,forwards=forwards,code=code),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);repo=root/'repo';repo.mkdir()
                (repo/name).parent.mkdir(parents=True);(repo/name).write_bytes(original)
                brief=root/'BRIEF.md';brief.write_text('# Public fixture\n')
                contract=root/'acceptance.mjs';contract.write_text('// Frozen public fixture\n')
                target=SimpleNamespace(seed_files=(),protected_check=SimpleNamespace(id='prepared_product',
                    contract_destination='EXTERNAL.mjs',contract_test=contract))
                frozen=SimpleNamespace(write_scopes=[str(Path(name).parent)+'/'],context_limit=250000,
                    step_cap=200,deadline_ns=900000000000,cost_reservation_usd='0.50')
                runtime=Mock();runtime.live.side_effect=ValueError(code)
                box=Mock();box.collect.return_value={
                    'workspace/'+name:base64.b64encode(changed).decode(),
                    'workspace/FROZEN_ACCEPTANCE.mjs':base64.b64encode(contract.read_bytes()).decode(),
                    **({} if valid else {'workspace/'+str(Path(name).parent)+'/.gitattributes':base64.b64encode(b'forbidden').decode()})}
                seen=[]
                def session(run,*_a,**_k):
                    run['forwarded_count']=forwards;seen.append(run);return runtime
                with patch('factory.flue_builder.public_files',return_value={name:original}), \
                        patch('factory.flue_builder.FactorySession',side_effect=session), \
                        patch('factory.flue_builder.Sandbox',return_value=box), \
                        patch('factory.flue_builder.usage',return_value={'complete':complete,'cost_usd':'0' if complete else None}), \
                        patch('factory.flue_builder.subprocess.run',return_value=SimpleNamespace(returncode=1)):
                    def build():
                        builder=FlueBuilder(root,{})
                        builder.authorization_check=lambda:True
                        return builder.run_build(repo=repo,frozen=frozen,feature={'id':'001','tier':3},
                            brief=brief,target=target,build={'build_id':'a'*32})
                    if recover:self.assertEqual(build(),[name])
                    else:
                        with self.assertRaisesRegex(ValueError,code):build()
                self.assertEqual((repo/name).read_bytes(),changed if valid else original)
                self.assertEqual(seen[0].get('retained_files_count'),1 if valid else None)
                if not valid:self.assertEqual(seen[0]['retained_export'],'unavailable')
                self.assertEqual(seen[0].get('candidate_recovered',False),recover)
                box.close.assert_called_once()

    def test_previous_check_failure_reaches_the_author_as_bounded_data(self):
        from factory.flue_builder import previous_failure_text
        self.assertEqual(previous_failure_text(None),'')
        self.assertEqual(previous_failure_text({'failed_tests':['x']}),'')
        text=previous_failure_text({'reason':'product_unit_tests_failed',
            'failed_tests':['DatabaseLessBootTest > livenessAnswersWithoutADatabase() FAILED'],
            'compiler_errors':['src/main/java/App.java:12']})
        self.assertIn('not instructions',text)
        self.assertIn('product_unit_tests_failed',text)
        self.assertIn('DatabaseLessBootTest > livenessAnswersWithoutADatabase() FAILED',text)
        self.assertIn('src/main/java/App.java:12',text)
        self.assertLess(len(text.encode()),4000)

    def test_transition_file_count_is_bounded_without_changing_write_scopes(self):
        files=[{'path':f'demo/forum-app/src/main/java/Fixture{i}.java','content':'class Fixture {}\n'} for i in range(32)]
        self.assertEqual(len(parse_files({'files':files},['demo/forum-app/src/main/java/'])),32)
        files.append({'path':'demo/forum-app/src/main/java/Extra.java','content':'class Extra {}\n'})
        with self.assertRaisesRegex(BuilderError,'builder_file_count'):
            parse_files({'files':files},['demo/forum-app/src/main/java/'])
    def test_oversized_local_brief_proves_no_transport_without_leaking_a_telemetry_session(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);brief=root/'BRIEF.md';brief.write_text('x'*12001)
            builder=FlueBuilder(root,{})
            with patch('factory.flue_builder.public_files',return_value={'demo/forum-app/A.java':b'class A {}'}), \
                    patch('factory.flue_builder.FactorySession') as session:
                with self.assertRaisesRegex(BuilderError,'brief_unavailable'):
                    builder.run_build(repo=root,frozen=SimpleNamespace(),feature={'id':'007','tier':3},
                        brief=brief,target=object(),build={'build_id':'a'*32})
            session.assert_not_called()
            self.assertTrue(builder.last_usage['complete'])
            self.assertEqual(builder.last_usage['cost_usd'],'0')

    def test_forward_cap_counts_previous_sessions_and_deadline_stops_the_next_request(self):
        run={'step_cap':3,'forwarded_count':2,'factory_deadline':200}
        self.assertIsNone(factory_work_limit(run,0,now=100))
        self.assertEqual(factory_work_limit(run,1,now=100),'STEP_LIMIT')
        self.assertEqual(factory_work_limit(run,0,now=200),'AGENT_DEADLINE')

    def test_three_identical_check_failures_stop_the_next_admission(self):
        from factory.flue_builder import note_check_failure
        import inspect
        run={}
        failed={'status':'failed','reason':'product_unit_tests_failed',
                'failed_tests':['DatabaseLessBootTest > livenessAnswersWithoutADatabase() FAILED']}
        note_check_failure(run,failed)
        note_check_failure(run,failed)
        self.assertIsNone(factory_work_limit({**run,'step_cap':12,'forwarded_count':0},0,now=1))
        note_check_failure(run,failed)
        self.assertEqual(factory_work_limit({**run,'step_cap':12,'forwarded_count':0,'factory_deadline':10**9},0,now=1),
                         'repeated_check_failure')
        source = inspect.getsource(FlueBuilder.run_build)
        self.assertNotIn('as often as you need', source)
        self.assertNotIn('You may not stop', source)
        self.assertIn('three identical failures', source)

    def test_frozen_deadline_and_context_are_used_before_a_sandbox_can_start(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            brief=root/'BRIEF.md';brief.write_text('# Bounded fixture\n')
            frozen=SimpleNamespace(cost_reservation_usd='0.50',write_scopes=['demo/forum-app/src/'],
                                   deadline_ns=500_000_000,context_limit=100000,step_cap=2)
            contract=root/'contract.java';contract.write_text('class Contract {}')
            target=SimpleNamespace(seed_files=(),protected_check=SimpleNamespace(
                id='prepared_gradle',contract_destination='contract.java',contract_test=contract))
            runtime=Mock();runtime.live.side_effect=AssertionError('expired work must not start inference')
            runtime.finish.return_value={'status':'stopped'}
            seen=[]
            def session(run,*_args,**_kwargs):
                seen.append(run)
                return runtime
            with patch('factory.flue_builder.FactorySession',side_effect=session), \
                 patch('factory.flue_builder.public_files',return_value={'demo/forum-app/A.java':b'class A {}'}), \
                 patch('factory.flue_builder.Sandbox') as sandbox, \
                 patch('factory.flue_builder.time.monotonic',side_effect=[100,101]):
                with self.assertRaisesRegex(BuilderError,'agent_deadline'):
                    FlueBuilder(root,{}).run_build(repo=root,frozen=frozen,feature={'id':'007','tier':3},
                        brief=brief,target=target,build={'build_id':'a'*32})
            sandbox.assert_not_called()
            runtime.live.assert_not_called()
            self.assertEqual(seen[0]['limit'],100000)
            self.assertEqual(seen[0]['step_cap'],2)


if __name__=='__main__':unittest.main()
