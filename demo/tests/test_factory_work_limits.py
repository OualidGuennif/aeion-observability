"""Frozen author bounds stop work before another model/tool session, across handovers."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.flue_builder import FlueBuilder, BuilderError
from app.runner import factory_work_limit
from factory.agent_files import parse_files


class WorkLimitTests(unittest.TestCase):
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

    def test_frozen_deadline_and_context_are_used_before_a_sandbox_can_start(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            brief=root/'BRIEF.md';brief.write_text('# Bounded fixture\n')
            frozen=SimpleNamespace(cost_reservation_usd='0.50',write_scopes=['demo/forum-app/src/'],
                                   deadline_ns=500_000_000,context_limit=100000,step_cap=2)
            target=SimpleNamespace(protected_check=SimpleNamespace(contract_destination='contract.java'))
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
