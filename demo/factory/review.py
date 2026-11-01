"""Independent, deterministic review gate placed between the checks and the publisher.

The reviewer never executes the candidate's code and never trusts what the builder says about
it. It reads only the bounded set of changed files the artifact validator already accepted and
applies fixed rules, so the same input always yields the same verdict.

A second language model is deliberately **not** the reviewer: a model is untrusted input too,
and a rogue one would approve a rogue diff. Anything doubtful is held for a human owner instead
of being auto-approved. The reviewer can only approve, refuse or hold; it can never publish.
"""
import hashlib
import json
import re

MAX_FILES = 50
MAX_TOTAL_BYTES = 512 * 1024
MAX_FILE_BYTES = 256 * 1024

# Credential-shaped strings that must never be committed by the factory.
SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{12,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
)
# Destructive or remote-execution shapes that a reviewed diff should never carry silently.
DANGEROUS_PATTERNS = (
    (re.compile(r"\brm\s+-rf\s+/(?:\s|$|\*)"), "destructive_command"),
    (re.compile(r"\bcurl\b[^\n|]{0,200}\|\s*(?:ba|z|d)?sh\b"), "remote_shell"),
    (re.compile(r"\bwget\b[^\n|]{0,200}\|\s*(?:ba|z|d)?sh\b"), "remote_shell"),
    (re.compile(r"\bchmod\s+(?:-R\s+)?777\b"), "world_writable"),
    (re.compile(r"\bsudo\b"), "privilege_escalation"),
    (re.compile(r"\bgit\s+push\s+.*--force\b"), "force_push"),
    (re.compile(r"\bnpm\s+publish\b|\bpip\s+install\s+--user\b"), "package_publish"),
)
DEPENDENCY_FILES = (
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "requirements.txt", "pyproject.toml", "poetry.lock", "go.mod", "go.sum", "cargo.lock",
)


class ReviewError(ValueError):
    """A review that cannot be produced from the given input."""


def _finding(code, detail, decision="held"):
    return {"code": code, "detail": detail, "decision": decision}


def review(frozen, artifact_verdict, files, max_files=MAX_FILES, max_total_bytes=MAX_TOTAL_BYTES):
    """Return a deterministic verdict for the bounded diff the gate already accepted."""
    if artifact_verdict.get("accepted") is not True:
        return _verdict([_finding("artifact_rejected", "artifact_not_accepted", "refused")], files)
    accepted = set(artifact_verdict.get("allowed") or [])
    findings = []
    if not files:
        return _verdict([_finding("empty_diff", "no_reviewable_content", "refused")], files)
    if len(files) > max_files:
        findings.append(_finding("too_many_files", f"{len(files)}>{max_files}"))
    total = 0
    for path in sorted(files):
        if path not in accepted:
            findings.append(_finding("unexpected_path", path, "refused"))
            continue
        text = files[path]
        size = len(text.encode("utf-8"))
        total += size
        if size > MAX_FILE_BYTES:
            findings.append(_finding("file_too_large", path))
            continue
        if "\x00" in text:
            findings.append(_finding("binary_content", path))
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(_finding("secret_like", path))
                break
        for pattern, code in DANGEROUS_PATTERNS:
            if pattern.search(text):
                findings.append(_finding(code, path))
        name = path.rsplit("/", 1)[-1].lower()
        if name in DEPENDENCY_FILES:
            findings.append(_finding("dependency_manifest", path))
    if total > max_total_bytes:
        findings.append(_finding("diff_too_large", f"{total}>{max_total_bytes}"))
    return _verdict(findings, files)


def content_digest(files):
    """Identity of the reviewed bytes, not just of the path list."""
    body = json.dumps({path: hashlib.sha256(files[path].encode("utf-8")).hexdigest()
                       for path in sorted(files)}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _verdict(findings, files):
    if any(f["decision"] == "refused" for f in findings):
        status = "refused"
    elif findings:
        status = "held"
    else:
        status = "approved"
    body = {"status": status, "findings": findings, "files": sorted(files),
            "content_digest": content_digest(files), "reviewer": "deterministic-rules-v1"}
    body["digest"] = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return body


def hold_reason(verdict):
    """Map a review verdict to a factory hold reason; approved never maps to one."""
    if verdict["status"] == "approved":
        return None
    return "owner_review_required"
