"""Qualify native execution tools before admitting work; never certify product delivery.

Run with the controller venv: python -m factory.admission --activate (from demo/).
Inference in these fixtures is local and scripted. Real builds still require external
product acceptance, two independent paid votes and protected PR/CI/main confirmation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from .flue_qualification import protocol_hash

ROOT=Path(__file__).resolve().parents[2]
COMMANDS={
    'flue_openshell':('demo/tests/qualify_flue.py',),
    'external_acceptance':('demo/tests/qualify_product_verifier.py',),
    'postgres_fixture':('demo/tests/qualify_postgres.py',),
    'chromium_sandbox':('demo/tests/qualify_chromium.py',),
    'preparation_and_publication':('demo/tests/qualify_factory_preparation.py',),
    'routing_persistence':('-m','unittest','discover','-s','demo/tests','-p','test_factory_routing.py','-v'),
}


def qualify(activate=False):
    folder=Path(tempfile.mkdtemp(prefix='admission-',dir=ROOT/'demo/.local/factory'))
    folder.chmod(0o700)
    initial=protocol_hash(ROOT)
    proof={'schema_version':2,'kind':'native_execution_capabilities','protocol_sha256':initial,
        'product_check':'prepared_product','product_delivery_claimed':False,
        'inference':'local_scripted_fixtures','capabilities':{},'started_ns':time.time_ns()}
    # Fixtures load the existing private config internally. Do not inherit publication keys.
    from .keys import PUBLISH_CREDENTIALS
    environment={k:v for k,v in os.environ.items() if k not in PUBLISH_CREDENTIALS}
    for name,arguments in COMMANDS.items():
        log=folder/(name+'.log')
        with log.open('xb') as output:
            log.chmod(0o600)
            result=subprocess.run([sys.executable,*arguments],cwd=ROOT,env=environment,
                stdout=output,stderr=subprocess.STDOUT,timeout=1200)
        if result.returncode:
            raise RuntimeError('capability_failed:'+name+':'+str(log))
        proof['capabilities'][name]={'status':'passed','evidence_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
        print(json.dumps({'capability':name,'status':'passed'}),flush=True)
    # Publication is already tested as a state machine, including exact-head checks and
    # credential-role subprocesses. Do not perform a synthetic remote merge for admission.
    log=folder/'publication_state_machine.log'
    with log.open('xb') as output:
        log.chmod(0o600)
        result=subprocess.run([sys.executable,'-m','unittest','discover','-s','demo/tests',
            '-p','test_factory_publication*.py','-v'],cwd=ROOT,env=environment,
            stdout=output,stderr=subprocess.STDOUT,timeout=180)
    if result.returncode:raise RuntimeError('publication_state_machine_failed:'+str(log))
    proof['capabilities']['preparation_and_publication']['publication_evidence_sha256']=hashlib.sha256(log.read_bytes()).hexdigest()
    log=folder/'registered_foundation.log'
    with log.open('xb') as output:
        log.chmod(0o600)
        result=subprocess.run([sys.executable,'demo/tests/qualify_registered_foundation.py'],cwd=ROOT,
            env=environment,stdout=output,stderr=subprocess.STDOUT,timeout=1200)
    if result.returncode:raise RuntimeError('registered_foundation_failed:'+str(log))
    proof['capabilities']['preparation_and_publication']['registered_evidence_sha256']=hashlib.sha256(log.read_bytes()).hexdigest()
    for name,script in (('closed_candidate','qualify_closed_candidate.py'),
            ('product_unit','qualify_product_unit.py'),('product_web','qualify_product_web.py')):
        log=folder/(name+'.log')
        with log.open('xb') as output:
            log.chmod(0o600)
            result=subprocess.run([sys.executable,'demo/tests/'+script],cwd=ROOT,env=environment,
                stdout=output,stderr=subprocess.STDOUT,timeout=1200)
        if result.returncode:raise RuntimeError(name+'_failed:'+str(log))
        proof['capabilities']['preparation_and_publication'][name+'_evidence_sha256']=hashlib.sha256(log.read_bytes()).hexdigest()
    sys.path.insert(0,str(ROOT/'demo/app'))
    from sandbox import cli_qualified,connection
    if not cli_qualified():raise RuntimeError('native_cli_not_qualified')
    client=connection(timeout=10);client.close()
    if protocol_hash(ROOT)!=initial:raise RuntimeError('protocol_changed_during_qualification')
    proof['finished_ns']=time.time_ns();proof['expires_ns']=proof['finished_ns']+86400000000000
    raw=json.dumps(proof,sort_keys=True,indent=2)+'\n'
    (folder/'proof.json').write_text(raw)
    if activate:
        marker=ROOT/'demo/.local/data/factory-flue-qualification.json'
        temporary=marker.with_suffix('.tmp')
        with temporary.open('w') as output:
            output.write(raw);output.flush();os.fsync(output.fileno())
        temporary.chmod(0o600);temporary.replace(marker)
    return {'status':'qualified','activated':activate,'evidence':str(folder/'proof.json'),
        'protocol_sha256':initial,'product_delivery_claimed':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activate',action='store_true')
    args=parser.parse_args()
    print(json.dumps(qualify(args.activate)))

if __name__=='__main__':main()
