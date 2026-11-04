"""Factory memory export stays metadata-only and never grants execution authority."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.flue_session import FactorySession, new_run
from app.memory import analysis


class Telemetry:
    def emit(self,*_args,**_kwargs):pass


class Memory:
    def __init__(self,unavailable=False):
        self.unavailable=unavailable
        self.saved=[]
    def checkpoint(self,run,state):
        if self.unavailable:raise OSError('synthetic backend outage')
        self.saved.append(state)
        run['claude_mem_id']=123
    def retain_factory(self,run):
        if self.unavailable:raise OSError('synthetic backend outage')
        self.saved.append(analysis(run))
        return {'status':'confirmed','bank':'synthetic-fixture','document_id':'fixture'}


class MemoryTests(unittest.TestCase):
    def finish(self,unavailable=False):
        run=new_run('glm-5.3-flash','a'*32,'author','0.50',synthetic=True)
        run.update(trace_id='b'*32,root_span_id='c'*16,prompt='PRIVATE_CANARY',source='PRIVATE_CANARY')
        runtime=FactorySession(run,telemetry=Telemetry())
        runtime.memory=Memory(unavailable)
        runtime.last_check={'status':'passed','artifact_digest':'d'*64,'compiler_errors':'PRIVATE_CANARY'}
        return run,runtime,runtime.finish(run)

    def test_both_memories_receive_only_bound_outcome_metadata(self):
        run,runtime,result=self.finish()
        self.assertNotIn('PRIVATE_CANARY',str(runtime.memory.saved))
        self.assertEqual(result['memory']['claude_mem']['status'],'confirmed')
        self.assertEqual(result['memory']['hindsight']['status'],'confirmed')
        self.assertEqual(runtime.memory.saved[1]['build_id'],'a'*32)
        self.assertEqual(runtime.memory.saved[1]['factory_role'],'author')

    def test_backend_outage_is_visible_without_rewriting_the_role_result(self):
        run,runtime,result=self.finish(unavailable=True)
        self.assertEqual(run['status'],'passed')
        self.assertEqual(result['memory'],{'claude_mem':{'status':'unavailable'},'hindsight':{'status':'unavailable'}})


if __name__=='__main__':unittest.main()
