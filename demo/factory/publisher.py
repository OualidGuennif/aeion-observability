"""The only process allowed to hold the publish credential.

It drains the worker's bounded publish queue, applies the publisher policy (which refuses
anything without an approved review, a pinned target and matching digests), and records the
outcome. It never writes code, never calls a model, and never merges unless the operator
explicitly enabled merging.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from factory import queue
from factory.github import GitHubForge, GitHubError
from factory.keys import CredentialError, for_role, present
from factory.publish import Publisher
from factory.review import content_digest
from factory.models import known, family, eligibility
from factory.store import Store, GATED, PR_OPEN, APPROVED, LIVE_COMPLETE

ROOT = Path(__file__).resolve().parents[2]


def load_publish_credential():
    """Load the publish credential for this process only, and prove no other role is present."""
    from factory.gh_probe import load_secret

    load_secret("GH_API_KEY")
    name, token = for_role("publish")
    if not token:
        raise CredentialError("publisher_credential_missing")
    return token


def _request_digest(request):
    """Content digest of the exact files this request asks the forge to commit."""
    files = request.get("files")
    if not isinstance(files, dict) or not files:
        return None
    if any(not isinstance(path, str) or not isinstance(text, str) for path, text in files.items()):
        return None
    try:
        return content_digest(files)
    except (TypeError, AttributeError):
        return None


def independent_circuit(circuit):
    """Exactly two actual eligible approvals, neither the author nor its family."""
    if not isinstance(circuit, dict) or circuit.get('status') != 'approved':
        return False
    author = circuit.get('author_model')
    if not isinstance(author, str) or not known(author):
        return False
    votes = circuit.get("votes")
    if not isinstance(votes, list) or len(votes) != 2:
        return False
    families, models = {family(author)}, {author}
    preparer = circuit.get('preparer_model')
    if preparer is not None:
        if (not isinstance(preparer, str) or not known(preparer) or family(preparer) in families
                or not eligibility(preparer)[0]):
            return False
        models.add(preparer)
        families.add(family(preparer))
    for vote in votes:
        if not isinstance(vote, dict) or vote.get('verdict') != 'approve':
            return False
        model = vote.get('model')
        if not isinstance(model, str) or not known(model) or not eligibility(model)[0]:
            return False
        actual_family = family(model)
        if model in models or actual_family in families or vote.get('family') != actual_family:
            return False
        models.add(model)
        families.add(actual_family)
    return True


def verified_receipt(store, request):
    """Cross-check the queued request, including its bytes, against the worker's stored receipt."""
    row = store.by_attempt(request.get("attempt_id"))
    if not row or not row.get("receipt"):
        return None
    import json as _json

    receipt = _json.loads(row["receipt"])
    if (row['status'] not in {GATED,PR_OPEN,APPROVED,LIVE_COMPLETE}
            or receipt.get('simulated') is not False
            or row['attempt_generation'] != row['cancellation_generation']
            or request.get('attempt_generation') != row['attempt_generation']
            or request.get('build_id') != row['build_id']
            or not re.fullmatch('[a-f0-9]{64}',row.get('contract_digest') or '')
            or receipt.get('contract_digest') != row['contract_digest']
            or request.get('contract_digest') != row['contract_digest']
            or request.get('frozen_digest') != receipt.get('frozen_digest')):
        return None
    if (receipt.get("gate") or {}).get("status") != "passed":
        return None
    if (receipt.get("review") or {}).get("status") != "approved":
        return None
    # The circuit is mandatory: a receipt without two distinct approving families is not publishable.
    circuit = receipt.get("circuit") or {}
    if circuit.get("status") != "approved" or not independent_circuit(circuit):
        return None
    preparation = receipt.get('preparation')
    if preparation is not None:
        if (not isinstance(preparation, dict) or preparation.get('synthetic') is not False
                or preparation.get('preparer_model') != circuit.get('preparer_model')
                or preparation.get('task_digest') != request.get('preparation_digest')
                or preparation.get('write_paths') != request.get('write_scopes')
                or any(preparation.get(k) != receipt.get(k)
                       for k in ('spec_digest','base_sha','acceptance_digest'))):
            return None
    elif circuit.get('preparer_model') is not None:
        return None
    digest = _request_digest(request)
    if digest is None:
        return None
    paths = sorted(request.get("reviewed_diff") or [])
    if sorted(request.get("files") or {}) != paths:
        return None
    if sorted(receipt.get("allowed") or []) != paths:
        return None
    if receipt.get("artifact_digest") != digest:
        return None
    if (circuit.get('content_digest') != digest
            or not isinstance(receipt.get('spec_digest'), str)
            or circuit.get('spec_digest') != receipt['spec_digest']
            or request.get('spec_digest') != receipt['spec_digest']
            or not isinstance(receipt.get('acceptance_digest'), str)
            or not re.fullmatch('[a-f0-9]{64}', receipt['acceptance_digest'])
            or circuit.get('acceptance_digest') != receipt['acceptance_digest']
            or request.get('acceptance_digest') != receipt['acceptance_digest']
            or (circuit.get('coverage') or {}).get('complete') is not True
            or circuit.get('author_model') != receipt.get('author_model')):
        return None
    if (receipt.get("review") or {}).get("content_digest") != digest:
        return None
    if receipt.get("artifact_digest") != request.get("artifact_digest"):
        return None
    if receipt.get("base_sha") != request.get("base"):
        return None
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", default=str(ROOT / "demo/.local/factory/publish-real"))
    parser.add_argument("--repo", default="OualidGuennif/aeion-autonomous-forum")
    parser.add_argument("--base", default="develop")
    parser.add_argument("--dry-run", action="store_true", help="Decide without creating anything remote")
    parser.add_argument("--allow-merge", action="store_true", help="Permit a merge when the request asks")
    parser.add_argument("--once", action="store_true", help="Process at most one request")
    args = parser.parse_args(argv)

    credential = present()
    if credential["inference"]:
        # The publisher must not be able to spend on inference either.
        print(json.dumps({"ok": False, "reason": "publisher_holds_inference_credential",
                          "held": credential["inference"]}), file=sys.stderr)
        return 2
    if credential["release"]:
        # Publishing an open pull request and being allowed to merge it are two different jobs.
        print(json.dumps({"ok": False, "reason": "publisher_holds_release_credential",
                          "held": credential["release"]}), file=sys.stderr)
        return 2
    try:
        token = load_publish_credential()
    except CredentialError as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}))
        return 2

    forge = GitHubForge(args.repo, token=token, base_branch=args.base,
                        dry_run=args.dry_run, allow_merge=args.allow_merge)
    store = Store(Path(args.state) / "factory.db")
    processed, results = 0, []
    for path in queue.pending(args.state):
        request = queue.read(path)
        receipt = verified_receipt(store, request)
        if receipt is None:
            decision = {"decision": "refused", "reason": "unverified_request"}
        else:
            # Expectations come from the worker's own record, never from the queue file.
            publisher = Publisher(args.repo, forge, trusted_issuer="gate",
                                  expected_base=receipt.get("base_sha"),
                                  expected_artifact_digest=receipt.get("artifact_digest"))
            try:
                decision = publisher.decide(request)
            except GitHubError as exc:
                decision = {"decision": "failed", "reason": str(exc)[:120]}
        results.append({"attempt_id": request.get("attempt_id"), "decision": decision.get("decision"),
                        "reason": decision.get("reason"),
                        "pr": (decision.get("forge") or {}).get("pr")})
        queue.done(args.state, path, decision)
        processed += 1
        if args.once:
            break
    print(json.dumps({"ok": True, "processed": processed, "results": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
