"""Real spec-bound static MD preparation and durable binding; no model or product delivery."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'demo'),str(ROOT/'demo/app')]
from factory.manifest import load_manifest
from factory.models import Router
from factory.preparation import TaskPreparer
from factory.product_checks import ProductCheckRunner
from factory.store import Store

BASE='63bdece8056136209e0e3d2e68dbf0879005fec9'

def main():
    source=ROOT/'demo/.local/factory/agents/aeion-autonomous-forum'
    before={key:subprocess.run(['git','-C',str(source),*args],capture_output=True,text=True,check=True).stdout
        for key,args in {'head':['rev-parse','HEAD'],'status':['status','--porcelain']}.items()}
    folder=Path(tempfile.mkdtemp(prefix='aeion-registered-foundation-',dir='/private/tmp'))
    catalog=load_manifest(ROOT/'demo/forum/features/MANIFEST.json',spec_dir=ROOT/'demo/forum/features')
    store=Store(folder/'state.db');store.admit(['001'],'native-registered-foundation',catalog)
    build=store.claim_next(catalog,lease_ns=1800*1_000_000_000)
    preparer=TaskPreparer(ROOT,source,checker=ProductCheckRunner(ROOT),base_ref=BASE,product=True)
    target,evidence=preparer.prepare(build=build,catalog=catalog,spec_dir=ROOT/'demo/forum/features',
        destination=folder/'prepared',budget=None,router=Router(),authorized=lambda:True)
    assert evidence['preparer_model'] is None and evidence['preparation_kind']=='registered_static_acceptance'
    assert preparer.role.last_usage=={'complete':True,'cost_usd':'0','basis':'proven_no_transport'}
    assert store.record_preparation(build['attempt_id'],build['attempt_generation'],evidence)
    saved=json.loads(store.by_attempt(build['attempt_id'])['receipt'])['preparation']
    assert saved==evidence
    after={key:subprocess.run(['git','-C',str(source),*args],capture_output=True,text=True,check=True).stdout
        for key,args in {'head':['rev-parse','HEAD'],'status':['status','--porcelain']}.items()}
    assert before==after
    proof={'status':'passed','kind':'native_registered_foundation_preparation','model_requests':0,
        'cost_usd':'0','product_delivery_claimed':False,'base_sha':target.base_sha,
        'task_digest':evidence['task_digest'],'acceptance_digest':evidence['acceptance_digest'],
        'negative_control':evidence['negative_control'],'durable_binding':'passed','source_unchanged':True}
    proof['transitions']={}
    for feature in ('002','014'):
        store=Store(folder/('state-'+feature+'.db'));store.seed_merged('001',catalog)
        store.admit([feature],'native-registered-'+feature,catalog)
        build=store.claim_next(catalog,lease_ns=1800*1_000_000_000)
        target,evidence=preparer.prepare(build=build,catalog=catalog,spec_dir=ROOT/'demo/forum/features',
            destination=folder/('prepared-'+feature),budget=None,router=Router(),authorized=lambda:True)
        assert evidence['preparer_model'] is None
        assert evidence['negative_control']=='registered_transition_source_missing'
        assert store.record_preparation(build['attempt_id'],build['attempt_generation'],evidence)
        proof['transitions'][feature]={'negative_control':evidence['negative_control'],
            'acceptance_digest':evidence['acceptance_digest'],'frozen_dependency_count':len(target.dependency_changes)}
    (folder/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'evidence':str(folder/'proof.json'),**proof}))

if __name__=='__main__':main()
