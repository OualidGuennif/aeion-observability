#!/usr/bin/env python3
# Spec: knowledge/operations/agent-compatibility.md
"""Read one git reference's files from a repository, without a checkout.

A project verifies against a reference: a release tag when it pins one, or main/develop when
someone works from a branch. The working tree may be dirty, ahead or behind any of them, so these
helpers read the reference's own bytes rather than what someone happens to have checked out.

    from refs import Refused, ref_bytes, ref_exists, ref_files, require_repository
"""
import subprocess


class Refused(Exception):
    """A condition the caller reports to its own user, with the wording it chooses."""


def git(repo, *arguments, text=False):
    result = subprocess.run(["git", "--no-pager", *arguments], cwd=repo, capture_output=True, text=text)
    if result.returncode:
        message = (result.stderr or "").strip()
        if isinstance(message, bytes):
            message = message.decode("utf-8", "replace")
        raise Refused(message or f"git {arguments[0]} failed")
    return result.stdout


def require_repository(repo):
    if not repo.is_dir():
        raise Refused(f"no such repository: {repo}")
    if subprocess.run(["git", "--no-pager", "rev-parse", "--git-dir"], cwd=repo,
                      capture_output=True).returncode:
        raise Refused(f"not a git repository: {repo}")


def ref_exists(repo, ref):
    """Whether a branch, tag or commit id resolves; a branch or tag moves, so the caller says which."""
    return subprocess.run(["git", "--no-pager", "rev-parse", "--verify", "--quiet", ref],
                          cwd=repo, capture_output=True).returncode == 0


def tag_exists(repo, tag):
    """Whether the name is a tag rather than a branch; the desktop pin needs a tag."""
    return subprocess.run(["git", "--no-pager", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"],
                          cwd=repo, capture_output=True).returncode == 0


def ref_files(repo, ref, folder):
    """The paths under one folder at a reference, sorted, exactly as the reference names them."""
    listing = git(repo, "ls-tree", "-r", "--name-only", ref, "--", folder, text=True)
    return sorted(line for line in listing.splitlines() if line.strip())


def ref_bytes(repo, ref, relative):
    """One file's bytes at one reference; git stores them as written, with no checkout filter."""
    return git(repo, "show", f"{ref}:{relative}")


def ref_diff(repo, before, after):
    """The paths that differ between two references, each resolvable."""
    listing = git(repo, "diff", "--name-only", before, after, text=True)
    return sorted(line for line in listing.splitlines() if line.strip())
