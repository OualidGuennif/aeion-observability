"""Protected scenario contracts checked inside OpenShell, without provider calls."""
import json
from pathlib import Path
import tempfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from sandbox import Sandbox
from scenarios import SCENARIOS,SOLUTIONS
from runner import acceptance

with tempfile.TemporaryDirectory(prefix='aeion-contracts-',dir='/work') as directory:
    root=Path(directory);root.chmod(0o711)
    workspace=root/'workspace';workspace.mkdir(mode=0o755)
    (workspace/'src').mkdir(mode=0o755)
    run={'id':'contract-qualification','agents':1}
    sandbox=Sandbox(run,root)
    try:
        result={}
        for task_id in SCENARIOS:
            (workspace/'src/pricing.js').write_text(SOLUTIONS[task_id])
            check=acceptance(workspace,sandbox,task_id)
            assert check['failed']==[],task_id
            result[task_id]=check['passed']
            (workspace/'src/pricing.js').write_text('export function '+SCENARIOS[task_id]['export']+'(){return null;}')
            assert acceptance(workspace,sandbox,task_id)['failed'],task_id
            # An unloadable module must not pass the cases that expect a TypeError.
            (workspace/'src/pricing.js').write_text('export function '+SCENARIOS[task_id]['export']+'( {')
            unloadable=acceptance(workspace,sandbox,task_id)
            assert unloadable['passed']==0 and len(unloadable['failed'])==unloadable['total'],task_id
        print(json.dumps({'runtime':'openshell','passed_cases':result,'broken_artifacts_rejected':True,'unloadable_artifacts_pass_zero':True}))
    finally:sandbox.close()
