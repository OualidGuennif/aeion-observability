"""Native external-verifier capability proof, not a product feature or model evaluation."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'demo'),str(ROOT/'demo/app')]
from factory.product_checks import ProductCheckRunner
from factory.postgres import DisposablePostgres

POSITIVE='''import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
test('external boundary',async()=>{
 assert.notEqual(process.getuid(),0);
 assert.equal(fs.existsSync('/var/run/docker.sock'),false);
 assert.equal(fs.existsSync('/product'),false);
 assert.equal(fs.existsSync('/workspace/demo/forum-app'),false);
 assert.match(fs.readFileSync('/proc/self/status','utf8'),/^CapEff:\\s+0+$/m);
 assert.match(fs.readFileSync('/proc/self/status','utf8'),/^NoNewPrivs:\\s+1$/m);
 assert.throws(()=>fs.writeFileSync('/opt/aeion-checker/run-acceptance.mjs','forged'));
 assert.equal((await fetch('http://127.0.0.1:8080/healthz',{signal:AbortSignal.timeout(2000)})).status,200);
 await assert.rejects(fetch('http://1.1.1.1',{signal:AbortSignal.timeout(1000)}));
});
'''
NEGATIVE="""import test from 'node:test';
import assert from 'node:assert/strict';
console.log(JSON.stringify({passed:true,tests:99,assertions:0}));
test('negative',()=>assert.equal(1,2));
"""
SKIPPED="import test from 'node:test'; test.skip('skipped',()=>{});\n"

def main():
    root=Path(tempfile.mkdtemp(prefix='aeion-external-verifier-',dir='/private/tmp'))
    runner=ProductCheckRunner(ROOT)
    name='aeion-public-http-'+uuid.uuid4().hex[:12]
    proof={'kind':'native_external_acceptance_boundary','product_delivery_claimed':False,
        'real_model_requests':0,'image_id':runner.verifier_image,'cases':{}}
    with DisposablePostgres() as db:
        try:
            args=runner._runtime_flags(name,db);args.insert(1,'-d')
            launched=runner._call(args+[runner.verifier_image,'node','-e',
                "require('http').createServer((q,s)=>s.end('public-fixture')).listen(8080,'127.0.0.1')"])
            if launched.returncode:raise RuntimeError('public_http_fixture_start_failed')
            for case,content,expected in [('positive',POSITIVE,True),('assertion_failure',NEGATIVE,False),('skipped',SKIPPED,False)]:
                path=root/(case+'.mjs');path.write_text(content)
                target=SimpleNamespace(protected_check=SimpleNamespace(contract_test=path))
                passed,detail=runner._verify(target,db)
                if passed is not expected:raise RuntimeError('external_verifier_case_failed:'+case)
                if case=='assertion_failure' and detail.get('contract_assertion_failures',0)<1:
                    raise RuntimeError('negative_assertion_not_observed')
                proof['cases'][case]=detail
        finally:runner._kill(name)
    proof['owned_teardown_confirmed']=True
    proof['status']='passed'
    proof['runner_sha256']=hashlib.sha256((ROOT/'demo/factory/product_checks.py').read_bytes()).hexdigest()
    (root/'proof.json').write_text(json.dumps(proof,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'evidence':str(root/'proof.json'),**proof}))

if __name__=='__main__':main()
