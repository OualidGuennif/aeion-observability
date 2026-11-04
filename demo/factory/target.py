"""Pinned product target: one feature, one commit, one protected check.

The catalog describes the planned product and stays unchanged. A target profile binds
one catalog feature to a real tree: an exact base commit, an adapted brief, literal
write scopes and a check that runs outside the candidate's control. A profile is
validated before a worker clones anything; a missing or drifting target holds the
build instead of letting it invent a base.
"""
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_CONTEXT_BYTES = 48000
MAX_BRIEF_BYTES = 12000
PUBLIC_JAVA = re.compile(r"demo/forum-app/src/main/java/(?:[A-Za-z_$][A-Za-z0-9_$]*/)+[A-Za-z_$][A-Za-z0-9_$]*\.java")


class TargetError(ValueError):
    """A target that cannot be trusted or materialised."""


@dataclass(frozen=True)
class ProtectedCheck:
    id: str
    command: list
    env: dict
    contract_test: Path
    contract_destination: str
    timeout_seconds: int

    def command_for(self, repo, controller):
        return [part.replace("{repo}", str(repo)).replace("{controller}", str(controller))
                for part in self.command]

    def env_for(self, repo, controller):
        return {key: value.replace("{repo}", str(repo)).replace("{controller}", str(controller))
                for key, value in self.env.items()}


@dataclass(frozen=True)
class Target:
    id: str
    feature_id: str
    target_repo: str
    controller: Path
    base_source: Path
    base_sha: str
    write_paths: list
    brief: Path
    protected_check: ProtectedCheck
    context_files: tuple = ()

    def source_context(self):
        """Read only bounded regular public blobs from the pinned Git tree."""
        parts = []
        for path in self.context_files:
            ref = f"{self.base_sha}:{path}"
            entry = _git(['-C', str(self.base_source), 'ls-tree', self.base_sha, '--', path])
            if entry.returncode or not entry.stdout.startswith(('100644 blob ', '100755 blob ')):
                raise TargetError('context_not_regular_blob')
            size = _git(['-C', str(self.base_source), 'cat-file', '-s', ref])
            if size.returncode or not size.stdout.strip().isdigit() or int(size.stdout) > 24000:
                raise TargetError('context_file_size')
            blob = _git(['-C', str(self.base_source), 'show', ref])
            if blob.returncode:
                raise TargetError('context_blob_unavailable')
            parts.append(f'FILE: {path}\n{blob.stdout}\nEND FILE\n')
        context = '\n'.join(parts)
        if len(context.encode('utf-8')) > MAX_CONTEXT_BYTES:
            raise TargetError('context_too_large')
        return context

    def materialize(self, destination):
        """Clone the pinned base into an isolated worktree and prove its identity."""
        destination = Path(destination)
        if destination.exists():
            raise TargetError("destination_exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        cloned = _git(["clone", "--quiet", "--no-hardlinks", "--no-checkout",
                       str(self.base_source), str(destination)])
        if cloned.returncode != 0:
            shutil.rmtree(destination, ignore_errors=True)
            raise TargetError("base_clone_failed")
        # A shallow source can keep the frozen main only in a remote-tracking ref,
        # which clone does not copy. Fetch that exact commit locally if necessary.
        present = _git(["-C", str(destination), "cat-file", "-e", f"{self.base_sha}^{{commit}}"])
        if present.returncode != 0:
            fetched = _git(["-C", str(destination), "fetch", "--quiet", "--no-tags",
                            "--no-write-fetch-head", str(self.base_source), self.base_sha])
            if fetched.returncode != 0:
                shutil.rmtree(destination, ignore_errors=True)
                raise TargetError("base_fetch_failed")
        checked_out = _git(["-C", str(destination), "checkout", "--quiet", "--detach", self.base_sha])
        if checked_out.returncode != 0:
            shutil.rmtree(destination, ignore_errors=True)
            raise TargetError("base_checkout_failed")
        head = _git(["-C", str(destination), "rev-parse", "HEAD"]).stdout.strip()
        if head != self.base_sha:
            shutil.rmtree(destination, ignore_errors=True)
            raise TargetError("base_drift")
        status = _git(["-C", str(destination), "status", "--porcelain"])
        if status.returncode != 0 or status.stdout.strip():
            shutil.rmtree(destination, ignore_errors=True)
            raise TargetError("base_not_clean")
        return head


def _git(args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def _relative(value, label):
    if not isinstance(value, str) or not value:
        raise TargetError(f"missing_{label}")
    if value.startswith("/") or "\\" in value or value.startswith("..") or "/../" in value:
        raise TargetError(f"invalid_{label}")
    return value


def _inside(root, path, label):
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
    except ValueError:
        raise TargetError(f"{label}_outside_repository") from None


def load_target(path, repo_root):
    """Load and validate a target profile; every field is checked before any effect."""
    repo_root = Path(repo_root).resolve()
    data = json.loads(Path(path).read_text())
    if data.get("schema_version") != 1:
        raise TargetError("unsupported_schema_version")
    feature_id = data.get("feature_id")
    if not isinstance(data.get("id"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", data["id"]):
        raise TargetError("invalid_target_id")
    if not isinstance(feature_id, str) or not re.fullmatch(r"\d{3}", feature_id):
        raise TargetError("invalid_feature_id")
    target_repo = data.get("target_repo")
    if not isinstance(target_repo, str) or target_repo.count("/") != 1:
        raise TargetError("invalid_target_repo")

    base = data.get("base") if isinstance(data.get("base"), dict) else {}
    source = _relative(base.get("source"), "base_source")
    base_source = (repo_root / source).resolve()
    if not base_source.is_dir():
        raise TargetError("base_source_missing")
    sha = base.get("sha")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise TargetError("invalid_base_sha")
    commit = _git(["-C", str(base_source), "rev-parse", "--verify", f"{sha}^{{commit}}"])
    if commit.returncode != 0:
        raise TargetError("base_commit_missing")

    prefix = _relative(data.get("allowed_scope_prefix"), "allowed_scope_prefix")
    scopes = data.get("write_paths")
    if not isinstance(scopes, list) or not scopes:
        raise TargetError("missing_write_paths")
    normalized = []
    for scope in scopes:
        scope = _relative(scope, "write_path")
        if not scope.endswith("/") or not scope.startswith(prefix) or scope == prefix:
            raise TargetError(f"scope_outside_target:{scope}")
        normalized.append(scope)

    brief_rel = _relative(data.get("brief"), "brief")
    brief = (repo_root / brief_rel).resolve()
    _inside(repo_root, brief, "brief")
    if not brief.is_file():
        raise TargetError("brief_missing")
    if brief.stat().st_size > MAX_BRIEF_BYTES:
        raise TargetError("brief_too_large")

    context_files = data.get('context_files', [])
    if (not isinstance(context_files, list) or len(context_files) > 8
            or any(not isinstance(item, str) or not PUBLIC_JAVA.fullmatch(item)
                   for item in context_files) or len(set(context_files)) != len(context_files)):
        raise TargetError('invalid_context_files')

    check = data.get("protected_check") if isinstance(data.get("protected_check"), dict) else {}
    check_id = check.get("id")
    if not isinstance(check_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]{2,40}", check_id):
        raise TargetError("invalid_check_id")
    command = check.get("command")
    if (not isinstance(command, list) or not command
            or not all(isinstance(part, str) and part for part in command)
            or not any("{repo}" in part for part in command)):
        raise TargetError("invalid_check_command")
    env = check.get("env", {})
    if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str)
                                            for k, v in env.items()):
        raise TargetError("invalid_check_env")
    contract_rel = _relative(check.get("contract_test"), "contract_test")
    contract = (repo_root / contract_rel).resolve()
    _inside(repo_root, contract, "contract_test")
    if not contract.is_file():
        raise TargetError("contract_test_missing")
    if contract.stat().st_size > 65536:
        raise TargetError("contract_test_too_large")
    for root in (repo_root, base_source):
        try:
            relative = contract.relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        if any(relative == scope.rstrip("/") or relative.startswith(scope) for scope in normalized):
            raise TargetError("contract_test_in_candidate_scope")
    destination = _relative(check.get("contract_destination"), "contract_destination")
    if not any(destination.startswith(scope) for scope in normalized):
        raise TargetError("contract_destination_outside_scope")
    if _git(["-C", str(base_source), "cat-file", "-e", f"{sha}:{destination}"]).returncode == 0:
        raise TargetError("contract_destination_tracked")
    timeout = check.get("timeout_seconds")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 3600:
        raise TargetError("invalid_check_timeout")

    target = Target(
        id=str(data.get("id") or ""), feature_id=feature_id, target_repo=target_repo,
        controller=repo_root, base_source=base_source, base_sha=sha,
        write_paths=normalized, brief=brief,
        protected_check=ProtectedCheck(
            id=check_id, command=list(command), env=dict(env), contract_test=contract,
            contract_destination=destination, timeout_seconds=timeout,
        ),
        context_files=tuple(context_files),
    )
    target.source_context()
    return target
