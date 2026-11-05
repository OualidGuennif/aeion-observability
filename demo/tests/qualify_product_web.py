"""Native frozen web-tool proof using a tiny synthetic React fixture, never product source."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'demo'),str(ROOT/'demo/app')]
from factory.product_checks import ProductCheckRunner


def main():
    runner=ProductCheckRunner(ROOT)
    checker=ROOT/'demo/factory/checker-tools'
    with tempfile.TemporaryDirectory(prefix='aeion-synthetic-web-tool-') as directory:
        workspace=Path(directory);web=workspace/'demo/forum-web';(web/'src').mkdir(parents=True)
        (web/'package.json').write_text('{"type":"module","scripts":{"build":"exit 99"}}\n')
        (web/'index.html').write_text('<div id="root"></div><script type="module" src="/src/main.tsx"></script>')
        (web/'src/main.tsx').write_text("import React from 'react'; import {createRoot} from 'react-dom/client';\n"
            "import './style.css';createRoot(document.getElementById('root')!).render(<h1>Synthetic tool fixture</h1>);\n")
        (web/'src/style.css').write_text('h1 { color: #164c38; }\n')
        (web/'src/types.d.ts').write_text("declare module '*.css';\n")
        trap="require('node:fs').writeFileSync('/workspace/untrusted-config-ran','forbidden');throw Error('UNTRUSTED_CONFIG');"
        for name in ('vite.config.cjs','postcss.config.cjs'):(web/name).write_text(trap)
        (web/'tsconfig.json').write_text('deliberately invalid candidate configuration')
        (web/'node_modules').symlink_to('/opt/aeion-checker/node_modules')
        args=['run','--rm','--network','none','--read-only','--user','1000:1000','-e','HOME=/tmp',
            '--cap-drop','ALL','--security-opt','no-new-privileges','--memory','1g','--cpus','2',
            '--pids-limit','128','--tmpfs','/tmp:rw,exec,size=512m',
            '-v',str(workspace)+':/workspace','-v',str(checker/'build-web.mjs')+':/opt/aeion-checker/build-web.mjs:ro']
        config=checker/'tsconfig.web.json'
        if config.is_file():args+=['-v',str(config)+':/opt/aeion-checker/tsconfig.web.json:ro']
        args+=['-v',str(checker/'vitest.config.mjs')+':/opt/aeion-checker/vitest.config.mjs:ro']
        def execute(command,**kwargs):
            name='aeion-web-proof-'+uuid.uuid4().hex[:12]
            try:return runner._call(args[:1]+['--name',name]+args[1:]+command,**kwargs)
            finally:runner._kill(name)
        result=execute(['-w','/opt/aeion-checker',runner.verifier_image,'node','build-web.mjs'],timeout=120)
        assert result.returncode==0,'Trusted web compilation failed with poisoned candidate configs'
        assert not (workspace/'untrusted-config-ran').exists(),'Untrusted configuration executed'
        assert (web/'dist/index.html').is_file()
        assert list((web/'dist/assets').glob('*.js')) and list((web/'dist/assets').glob('*.css'))
        for expected in (True,False):
            (web/'src/fixture.test.ts').write_text("import {test,expect} from 'vitest';\n"
                "test('public fixture',()=>expect(1).toBe("+('1' if expected else '2')+"));\n")
            result=execute(['-w','/workspace/demo/forum-web',runner.verifier_image,'node',
                '/opt/aeion-checker/node_modules/vitest/vitest.mjs','run',
                '--config','/opt/aeion-checker/vitest.config.mjs','--configLoader','native'],timeout=60)
            assert (result.returncode==0) is expected, ('Fixed Vitest outcome did not match the assertion: '
                + (result.stdout+result.stderr)[-5000:])  # Public synthetic fixture only.
    proof={'status':'passed','kind':'frozen_web_build_tools','synthetic':True,'real_model_requests':0,
        'product_delivery_claimed':False,'react_typescript_production_build':True,
        'candidate_vite_postcss_and_typescript_configs_ignored':True,'candidate_npm_script_ignored':True,
        'vitest_positive_and_deliberate_failure':True,
        'network':'none'}
    folder=Path(tempfile.mkdtemp(prefix='aeion-frozen-web-proof-',dir='/private/tmp'))
    (folder/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'evidence':str(folder/'proof.json'),**proof}))


if __name__=='__main__':main()
