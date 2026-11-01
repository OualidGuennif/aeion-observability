"""Validate a returned artifact against the actual Git diff, never a reported path list.

The host enumerates changed paths from the worktree, checks each against the frozen
literal write scopes and rejects traversal, absolute paths, symlinks, Git metadata and
out-of-scope entries. Renames validate both endpoints. Product code never runs here.
"""
import hashlib
import os
import subprocess
from pathlib import Path


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


def validate_artifact(repo, write_scopes):
    """Validate the whole diff. Returns a verdict dict with allowed/rejected paths and digest."""
    repo = Path(repo)
    entries = changed_entries(repo)
    allowed = []
    rejected = []
    for entry in entries:
        if entry[0] == "R":
            _, old, new = entry
            problem = _path_problem(old, repo, write_scopes) or _path_problem(new, repo, write_scopes)
            item = f"{old} -> {new}"
        else:
            _, path = entry
            problem = _path_problem(path, repo, write_scopes)
            item = path
        if problem:
            rejected.append({"path": item, "reason": problem})
        else:
            allowed.append(item)
    if rejected:
        return {"accepted": False, "allowed": sorted(allowed), "rejected": rejected, "digest": None}
    digest = hashlib.sha256("\n".join(sorted(allowed)).encode("utf-8")).hexdigest()
    return {"accepted": True, "allowed": sorted(allowed), "rejected": [], "digest": digest}
