"""One trusted publication operation with exactly one GitHub credential role."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'demo'))
from factory.github import GitHubError,GitHubForge
from factory.keys import assert_only,for_role,names_for,CredentialError
from factory.gh_probe import load_secret
from factory.publication import REPOSITORY
from factory.publisher import verified_receipt
from factory.publish import Publisher
from factory.store import CANCELLED, FAILED, Store


def operate(args):
    if args.repo!=REPOSITORY:
        return {'status':'held','reason':'forbidden_repository'}
    state=Path(args.state).resolve()
    try:state.relative_to((ROOT/'demo/.local/factory').resolve())
    except ValueError:return {'status':'held','reason':'forbidden_publication_state'}
    if args.action=='prune' and args.role!='publish':
        return {'status':'held','reason':'wrong_publication_role'}
    # Check role conflicts both before and after the named loader; no unrelated key is loaded.
    assert_only(args.role)
    load_secret(names_for(args.role)[0]);assert_only(args.role)
    _,token=for_role(args.role)
    store=Store(state/'factory.db')
    if args.action=='prune':
        # The publish role removes only its own branch of a failed or cancelled build.
        row=store.by_attempt(args.attempt)
        if row is None or row['status'] not in (FAILED,CANCELLED):
            return {'status':'held','reason':'prune_not_eligible'}
        return GitHubForge(args.repo,token=token,dry_run=False).prune_branch(args.attempt)
    request=store.publication_request(args.attempt)
    if not request:return {'status':'held','reason':'publication_request_missing'}
    receipt=verified_receipt(store,request)
    generation=request['attempt_generation']
    authorized=lambda:store.publication_authorized(args.attempt,generation,args.lease)
    if receipt is None or not authorized():
        return {'status':'held','reason':'publication_revoked'}
    forge=GitHubForge(args.repo,token=token,dry_run=False,allow_merge=args.role=='release',before_write=authorized)
    if args.role=='publish':
        decision=Publisher(args.repo,forge,expected_base=receipt['base_sha'],
            expected_artifact_digest=receipt['artifact_digest'],
            approved_dependencies=receipt.get('dependency_changes')).decide(request)
        if decision.get('decision')=='hold':return {'status':'held','reason':decision['reason']}
        if decision.get('decision') not in {'published','reconciled'}:
            return {'status':'held','reason':decision.get('reason','publication_refused')}
        return decision['forge']
    row=store.by_attempt(args.attempt)
    prior=(json.loads(row['receipt']).get('publisher') or {}).get('pr')
    # CI polling receipts retain this same PR; never choose a number from model output.
    if not prior:
        found=forge.reconcile(args.attempt)
        prior=found.get('pr')
    if not prior or not prior.get('head_sha'):
        return {'status':'pending','reason':'publication_reconciliation_required'}
    return forge.merge(prior['pr_number'],expected_head=prior['head_sha'],expected_base=request['base'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',required=True);parser.add_argument('--repo',required=True)
    parser.add_argument('--role',choices=['publish','release'],required=True)
    parser.add_argument('--attempt',required=True);parser.add_argument('--lease',default='')
    parser.add_argument('--action',choices=['operate','prune'],default='operate')
    args=parser.parse_args()
    if args.action=='operate' and not args.lease:
        parser.error('--lease is required')
    try:result=operate(args)
    except CredentialError:result={'status':'held','reason':'publication_credential_unavailable'}
    except GitHubError as error:result={'status':'held','reason':str(error)}
    except (OSError,TimeoutError,ValueError,KeyError):
        result={'status':'pending','reason':'forge_reconciliation_required'}
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=='__main__':raise SystemExit(main())
