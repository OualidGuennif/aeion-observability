"""Publisher policy and a fake forge: deterministic permitted effects, refused or held otherwise.

Builders and observers have no forge token. The publisher accepts only the pinned target,
a reviewed diff inside declared product scopes, and rejects sensitive, mixed, forged or
cancelled effects. Fake forge responses are labelled; an uncertain result is reconciled
against the forge before any retry, never blindly redone.
"""
from .review import content_digest

SENSITIVE_MARKERS = ("migrations", "auth", "security", "moderation", "rules", "runtime", "deploy", "permission")
DEPENDENCY_MANIFESTS = (
    "package.json", "package-lock.json", "requirements.txt", "pyproject.toml", "poetry.lock",
    "dockerfile", "yarn.lock", "pnpm-lock.yaml", "go.mod", "go.sum", "cargo.lock",
)


def is_sensitive_path(path):
    p = path.lower().replace("\\", "/")
    parts = p.split("/")
    if any(m in parts for m in SENSITIVE_MARKERS):
        return True
    if p.endswith(".lock") or any(p.endswith(m) for m in DEPENDENCY_MANIFESTS):
        return True
    return False


def _in_scope(path, write_scopes):
    return any(path == s or (s.endswith("/") and path.startswith(s)) for s in write_scopes)


def _content_digest(files):
    """Digest of the submitted bytes, or None when they are missing or not text."""
    if not isinstance(files, dict) or not files:
        return None
    if any(not isinstance(path, str) or not isinstance(text, str) for path, text in files.items()):
        return None
    try:
        return content_digest(files)
    except (TypeError, AttributeError):
        return None


class FakeForge:
    """In-memory forge whose responses are explicitly simulated, not a GitHub operation."""

    def __init__(self, crash_on=None):
        self.published = {}
        self._seq = 0
        self.crash_on = set(crash_on or [])

    def publish(self, request):
        attempt_id = request["attempt_id"]
        self._seq += 1
        pr = {"attempt_id": attempt_id, "head": request.get("head"), "pr_number": self._seq, "merged": True}
        self.published[attempt_id] = pr
        if attempt_id in self.crash_on:
            # The external effect happened, but the caller "crashed" before recording it.
            return {"status": "uncertain", "attempt_id": attempt_id}
        return {"status": "published", "pr": pr}

    def reconcile(self, attempt_id):
        pr = self.published.get(attempt_id)
        if pr is None:
            return {"status": "absent"}
        return {"status": "published", "pr": pr}


class Publisher:
    def __init__(self, target_repo, forge, trusted_issuer="gate", expected_base=None,
                 expected_head=None, expected_artifact_digest=None):
        self.target_repo = target_repo
        self.forge = forge
        self.trusted_issuer = trusted_issuer
        self.expected_base = expected_base
        self.expected_head = expected_head
        self.expected_artifact_digest = expected_artifact_digest

    def decide(self, request):
        if request.get("issuer") != self.trusted_issuer:
            return {"decision": "refused", "reason": "forged_issuer"}
        if request.get("target_repo") != self.target_repo:
            return {"decision": "refused", "reason": "forbidden_target"}
        if request.get("cancelled"):
            return {"decision": "refused", "reason": "cancelled"}
        if self.expected_base is not None and request.get("base") != self.expected_base:
            return {"decision": "hold", "reason": "stale_base"}
        if self.expected_head is not None and request.get("head") != self.expected_head:
            return {"decision": "hold", "reason": "stale_head"}
        files = request.get("files")
        digest = _content_digest(files)
        if digest is None:
            return {"decision": "refused", "reason": "missing_content"}
        paths = request.get("reviewed_diff", [])
        if sorted(files) != sorted(paths):
            return {"decision": "refused", "reason": "path_set_mismatch"}
        if self.expected_artifact_digest is not None and digest != self.expected_artifact_digest:
            return {"decision": "refused", "reason": "forged_content"}
        if request.get("artifact_digest") not in (None, digest):
            return {"decision": "refused", "reason": "forged_receipt"}
        if request.get("review_content_digest") not in (None, digest):
            return {"decision": "refused", "reason": "forged_review"}
        scopes = request.get("write_scopes", [])
        if not all(_in_scope(p, scopes) for p in paths):
            return {"decision": "refused", "reason": "forbidden_path"}
        if request.get("review_status", "approved") != "approved":
            return {"decision": "hold", "reason": "owner_review_required"}
        if request.get("review_sensitive") or any(is_sensitive_path(p) for p in paths):
            return {"decision": "hold", "reason": "owner_review_required"}
        result = self.forge.publish(request)
        if result.get("status") == "uncertain":
            reconciled = self.forge.reconcile(request["attempt_id"])
            return {"decision": "reconciled", "forge": reconciled}
        return {"decision": "published", "forge": result}
