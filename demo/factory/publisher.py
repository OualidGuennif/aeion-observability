"""The only process allowed to hold the publish credential.

It drains the worker's bounded publish queue, applies the publisher policy (which refuses
anything without an approved review, a pinned target and matching digests), and records the
outcome. It never writes code, never calls a model, and never merges unless the operator
explicitly enabled merging.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from factory import queue
from factory.github import GitHubForge, GitHubError
from factory.keys import CredentialError, for_role, present
from factory.publish import Publisher
from factory.review import content_digest
from factory.store import Store

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
    """A circuit is approved only by at least two votes from distinct model families."""
    if not isinstance(circuit, dict):
        return False
    votes = circuit.get("votes")
    if not isinstance(votes, list) or len(votes) < 2:
        return False
    families = []
    for vote in votes:
        if not isinstance(vote, dict) or not isinstance(vote.get("family"), str) or not vote["family"]:
            return False
        families.append(vote["family"])
    return len(set(families)) == len(families)


def verified_receipt(store, request):
    """Cross-check the queued request, including its bytes, against the worker's stored receipt."""
    row = store.by_attempt(request.get("attempt_id"))
    if not row or not row.get("receipt"):
        return None
    import json as _json

    receipt = _json.loads(row["receipt"])
    if (receipt.get("gate") or {}).get("status") != "passed":
        return None
    if (receipt.get("review") or {}).get("status") != "approved":
        return None
    # The circuit is mandatory: a receipt without two distinct approving families is not publishable.
    circuit = receipt.get("circuit") or {}
    if circuit.get("status") != "approved" or not independent_circuit(circuit):
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
