"""Explicit, one-time repair of a held legacy review envelope; no HTTP/worker authority.

From the repository: PYTHONPATH=demo demo/.local/venv/bin/python -m factory.review_context BUILD_ID
Spec: knowledge/components/factory-flue.md. Existing daily budget and live admission still apply.
"""
import argparse
import json
from pathlib import Path
import re
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_id')
    parser.add_argument('--retry-failed-review',action='store_true',
        help='Once only after a failed v2 review, never after a v2 code rejection. All votes are rerun.')
    args=parser.parse_args()
    if not re.fullmatch('[0-9a-f]{32}',args.build_id):parser.error('Invalid build identity')
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/'demo/app'))
    from .api import FactoryApp
    from .budget import DailyBudget
    from .execution import resolve
    from .review_circuit import CircuitError
    app=FactoryApp(root/'demo/forum/features/MANIFEST.json',root/'demo/.local/factory',
        spec_dir=root/'demo/forum/features',bootstrap_token='unused-local-cli-no-server',
        budget=DailyBudget(root/'demo/.local/budget/ledger.jsonl'),execution=resolve(root,'live'))
    try:
        result=app.worker.reassess_review_context(args.build_id,retry_failed_review=args.retry_failed_review)['result']
    except CircuitError as error:
        print(json.dumps({'build_id':args.build_id,'status':'held','reason':str(error)}))
        return 1
    print(json.dumps({'build_id':args.build_id,'status':result.get('status'),'reason':result.get('reason')}))
    return 0 if result.get('status')=='publication_queued' else 1


if __name__=='__main__':raise SystemExit(main())
