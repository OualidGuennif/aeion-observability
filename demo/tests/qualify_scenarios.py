"""Protected scenario contracts checked inside OpenShell, without provider calls.

`--local-sandbox` runs the same checks with the host stand-in (development only).
"""
import json
import os
from pathlib import Path
import tempfile
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scenarios import SCENARIOS,SOLUTIONS
from runner import acceptance
from settings import AGENT_UID, WORK

if '--local-sandbox' in sys.argv:
    from local_sandbox import LocalSandbox as Sandbox
else:
    from sandbox import Sandbox

WORK.mkdir(mode=0o700,parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='.qualify-contracts-',dir=WORK) as directory:
    root=Path(directory)
    workspace=root/'workspace';workspace.mkdir(mode=0o755)
    (workspace/'src').mkdir(mode=0o755)
    if AGENT_UID!=os.getuid():
        root.chmod(0o711);(workspace/'src').chmod(0o777)
    run={'id':'contract-qualification','agents':1}
    sandbox=Sandbox(run,root,role='check')
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
        print(json.dumps({'runtime':'local-stand-in' if '--local-sandbox' in sys.argv else 'openshell','passed_cases':result,
                          'broken_artifacts_rejected':True,'unloadable_artifacts_pass_zero':True}))
    finally:sandbox.close()
