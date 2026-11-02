"""Validate a returned artifact against the actual Git diff and bind it to its bytes.

The host enumerates changed paths from the worktree, checks each against the frozen
literal write scopes and rejects traversal, absolute paths, symlinks, Git metadata and
out-of-scope entries. The digest covers each path *and* its content, so a receipt can
only ever describe the exact bytes a reviewer saw.

Only ordinary added or modified regular UTF-8 files are supported. A rename, deletion,
type change, binary blob or unreadable file is held as an unsupported effect instead of
being silently left out of the published payload. Product code never runs here.
"""
import os
import subprocess
from pathlib import Path

from .review import content_digest

MAX_CONTENT_BYTES = 512 * 1024
SUPPORTED_STATUSES = {"A", "M", "??"}


class ArtifactError(ValueError):
    """A diff that cannot be safely committed."""


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def changed_entries(repo):
    """Return (status, path) tuples, with renames as (old, new) under status 'R'."""
    tracked = _git(repo, "diff", "--name-status", "HEAD")
    if tracked.returncode != 0:
        raise ArtifactError("git_unavailable")
    entries = []
    for line in tracked.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R"):
            if len(parts) < 3:
                raise ArtifactError("malformed_rename")
            entries.append(("R", parts[1], parts[2]))
        elif len(parts) >= 2:
            entries.append((status, parts[1]))
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard")
    if untracked.returncode != 0:
        raise ArtifactError("git_unavailable")
    for path in untracked.stdout.splitlines():
        if path.strip():
            entries.append(("??", path))
    return entries


def _in_scope(path, write_scopes):
    return any(path == s or (s.endswith("/") and path.startswith(s)) for s in write_scopes)


def _path_problem(path, repo, write_scopes):
    if not path or path.startswith("/") or "\\" in path or path.startswith("..") or "/../" in path or path == "..":
        return "traversal_or_absolute"
    parts = Path(path).parts
    if ".git" in parts or path.startswith(".git"):
        return "git_metadata"
    if not _in_scope(path, write_scopes):
        return "out_of_scope"
    full = Path(repo) / path
    if os.path.islink(full):
        return "symlink"
    if full.exists() and not full.is_file():
        return "non_regular"
    return None


def _read_text(full, limit=MAX_CONTENT_BYTES):
    """Read one supported file; return (text, problem), never guessing at binary bytes."""
    try:
        data = Path(full).read_bytes()
    except OSError:
        return None, "unreadable_content"
    if len(data) > limit:
        return None, "file_too_large"
    if b"\x00" in data:
        return None, "binary_content"
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, "non_utf8_content"


def validate_artifact(repo, write_scopes):
    """Validate the whole diff. Returns a verdict with content-bound allowed/rejected paths."""
    repo = Path(repo)
    entries = changed_entries(repo)
    allowed = []
    rejected = []
    files = {}
    for entry in entries:
        status = entry[0]
        if status == "R":
            _, old, new = entry
            rejected.append({"path": f"{old} -> {new}", "reason": "unsupported_effect:rename"})
            continue
        if status not in SUPPORTED_STATUSES:
            rejected.append({"path": entry[1], "reason": f"unsupported_effect:{status}"})
            continue
        path = entry[1]
        problem = _path_problem(path, repo, write_scopes)
        if problem:
            rejected.append({"path": path, "reason": problem})
            continue
        text, problem = _read_text(repo / path)
        if problem:
            rejected.append({"path": path, "reason": problem})
            continue
        files[path] = text
        allowed.append(path)
    if rejected:
        return {"accepted": False, "allowed": sorted(allowed), "rejected": rejected, "digest": None}
    return {"accepted": True, "allowed": sorted(allowed), "rejected": [],
            "digest": content_digest(files), "files": files}
