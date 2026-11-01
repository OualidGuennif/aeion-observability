"""Protected check registry and evaluator, held outside any candidate's control.

Acceptance cases are built from the frozen spec. A missing required check yields
``qualification_missing``, never a green result; a candidate can supply code, not the
evaluator that judges it.
"""
import hashlib


class ProtectedChecks:
    def __init__(self, checks=None):
        self.checks = dict(checks or {})  # check_id -> callable(frozen, artifact_verdict) -> (passed, detail)

    def bundle_digest(self):
        """Identity of the approved check revision; the gate binds this into its verdict."""
        return hashlib.sha256(",".join(sorted(self.checks)).encode("utf-8")).hexdigest()

    def evaluate(self, required, frozen, artifact_verdict):
        results = {}
        for check_id in required:
            fn = self.checks.get(check_id)
            if fn is None:
                results[check_id] = {"status": "qualification_missing"}
                continue
            passed, detail = fn(frozen, artifact_verdict)
            results[check_id] = {"status": "passed" if passed else "failed", "detail": detail}
        return results

    def verdict(self, required, frozen, artifact_verdict):
        results = self.evaluate(required, frozen, artifact_verdict)
        if any(r["status"] == "qualification_missing" for r in results.values()):
            return {"status": "qualification_missing", "results": results}
        if any(r["status"] == "failed" for r in results.values()):
            return {"status": "failed", "results": results}
        return {"status": "passed", "results": results}


def scope_check(frozen, artifact_verdict):
    """The artifact diff must have been accepted against the frozen write scopes."""
    return (artifact_verdict.get("accepted") is True, "artifact_in_scope")


def spec_unchanged_check(frozen, artifact_verdict):
    """The receipt must carry the frozen spec digest, not a modified copy."""
    return (artifact_verdict.get("spec_digest") == frozen.spec_digest, "spec_digest_matches")


DEFAULT_CHECKS = {"scope": scope_check, "spec_unchanged": spec_unchanged_check}
