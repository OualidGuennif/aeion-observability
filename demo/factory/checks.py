"""Protected check registry and evaluator, held outside any candidate's control.

Acceptance cases are built from the frozen spec. A missing required check yields
``qualification_missing``, never a green result; a candidate can supply code, not the
evaluator that judges it.
"""
import hashlib
import os
import re
import stat
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from .agent_files import MAX_FILE_BYTES, grader_tampered
from .isolation import IsolationError


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

# The check runner is handed a toolchain environment, not the controller's environment:
# provider keys, gateway credentials and harness settings must never reach candidate code.
CHECK_ENV_ALLOWLIST = (
    "PATH", "HOME", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL", "LANGUAGE",
    "JAVA_HOME", "GRADLE_USER_HOME", "GRADLE_OPTS", "JAVA_TOOL_OPTIONS",
    "SYSTEMROOT", "USERPROFILE",
)


def check_environment(spec, repo, target):
    env = {name: os.environ[name] for name in CHECK_ENV_ALLOWLIST if name in os.environ}
    env.update(spec.env_for(repo, target.controller))
    return env


def _failed_tests(output, limit=20):
    """Extract bounded test identifiers, never the raw build output."""
    found = []
    for line in (output or "").splitlines():
        line = line.strip()
        if " FAILED" not in line and not line.endswith("FAILED"):
            continue
        if " > " not in line and not line.startswith("Execution failed"):
            continue
        if line not in found:
            found.append(line[:240])
        if len(found) >= limit:
            break
    return found


def _compiler_errors(output, limit=20):
    """Keep Java file/line/identifier only; source lines and diagnostic prose stay private."""
    errors, current = [], None
    for line in (output or '').splitlines():
        location = re.search(r'([A-Za-z_$][A-Za-z0-9_.$]{0,79}\.java):([0-9]{1,6}): error:', line)
        if location:
            current = {'file': location[1], 'line': int(location[2])}
            if current in errors:
                current = None
            elif len(errors) < limit:
                errors.append(current)
            else:
                break
        elif current is not None:
            symbol = re.fullmatch(r'\s*symbol:\s+(?:variable|class|method)\s+'
                                  r'([A-Za-z_$][A-Za-z0-9_.$]{0,79})(?:\([^\r\n]*\))?\s*', line)
            if symbol:
                current['symbol'] = symbol[1]
    return errors


def _confined_contract_parent(repo, destination):
    """A candidate may replace a parent directory with a host-directed symlink during a check."""
    try:
        relative = destination.relative_to(repo)
        if any(part in ('.', '..') for part in relative.parts):
            return False
        destination.parent.resolve().relative_to(repo.resolve())
        return not any(parent.is_symlink() for parent in destination.parents if parent != repo
                       and repo in parent.parents)
    except ValueError:
        return False


def _contract_bytes(path, limit=65536):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise OSError('contract_not_regular')
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise OSError('contract_too_large')
    return data


def _grader_tampered(repo, destination):
    src = repo / 'demo/forum-app/src'
    if not src.exists():
        return False
    if src.is_symlink() or not _confined_contract_parent(repo, src / 'probe'):
        return True
    for root_dir, dirs, files in os.walk(src, followlinks=False):
        current = Path(root_dir)
        if any((current / d).is_symlink() for d in dirs):
            return True
        for name in files:
            item = current / name
            if item == destination:
                continue
            if item.is_symlink() or not _confined_contract_parent(repo, item):
                return True
            try:
                raw = _contract_bytes(item, limit=MAX_FILE_BYTES)
                text = raw.decode('utf-8')
            except (OSError, UnicodeDecodeError):
                return True
            if grader_tampered(item.relative_to(repo).as_posix(), text):
                return True
    return False


def _contract_report(repo, spec):
    classname = Path(spec.contract_destination).stem
    if not re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*', classname):
        return None, None
    report = repo / 'demo/forum-app/build/test-results/test' / ('TEST-local.aeion.forum.' + classname + '.xml')
    return classname, report


def _contract_assertions(repo, spec):
    classname, report = _contract_report(repo, spec)
    if report is None or not _confined_contract_parent(repo, report):
        return 0
    try:
        data = _contract_bytes(report)
        if b'\0' in data or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
            return 0
        root = ET.fromstring(data)
    except (OSError,ET.ParseError):
        return 0
    return min(1000,sum(1 for case in root.iter('testcase')
        if case.get('classname') == 'local.aeion.forum.' + classname
        for failure in case.findall('failure')
        if failure.get('type') in {'org.opentest4j.AssertionFailedError','java.lang.AssertionError'}))


def _contract_executed(repo, spec):
    results_dir = repo / 'demo/forum-app/build/test-results/test'
    if not results_dir.exists():
        return True
    classname, report = _contract_report(repo, spec)
    if report is None or not _confined_contract_parent(repo, report):
        return False
    try:
        data = _contract_bytes(report)
        if b'\0' in data or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
            return False
        root = ET.fromstring(data)
        if (int(root.get('tests', '0')) < 1 or int(root.get('skipped', '0')) != 0
                or int(root.get('failures', '0')) != 0 or int(root.get('errors', '0')) != 0):
            return False
    except (OSError, ET.ParseError, ValueError):
        return False
    cases = [case for case in root.iter('testcase')
             if case.get('classname') == 'local.aeion.forum.' + classname]
    return bool(cases) and all(
        not case.findall('skipped') and not case.findall('failure') and not case.findall('error')
        for case in cases)


def target_check(target, runner=None, work_root=None, sandbox=None):
    """Run the profile's protected check against the materialised candidate tree.

    The contract test is copied in from outside the candidate's write scopes, runs with a
    toolchain-only environment (never the controller's), and is restored afterwards. When a
    DockerCheckRunner is supplied it also enforces the isolated runtime; without one this is
    path and environment confinement only, so untrusted candidate code stays held. Only a
    bounded failure summary is recorded: no raw output, no candidate-controlled evaluator.
    """
    runner = sandbox or runner or subprocess.run
    allowed_root = Path(work_root).resolve() if work_root is not None else None

    def check(frozen, artifact_verdict):
        # An absent or relative path must never resolve to the controller's own directory.
        raw_repo = artifact_verdict.get("repo")
        if not isinstance(raw_repo, str) or not raw_repo:
            return False, {"reason": "repository_missing"}
        repo = Path(raw_repo)
        if not repo.is_absolute() or not repo.is_dir():
            return False, {"reason": "repository_missing"}
        if allowed_root is not None:
            try:
                repo.resolve().relative_to(allowed_root)
            except ValueError:
                return False, {"reason": "repository_outside_workspace"}
        spec = target.protected_check
        if spec.id == 'prepared_product':
            if sandbox is None or not callable(getattr(sandbox, 'check_target', None)):
                return False, {'reason':'isolation_unqualified'}
            return sandbox.check_target(target, repo, frozen)
        destination = repo / spec.contract_destination
        if not _confined_contract_parent(repo, destination) or destination.is_symlink():
            return False, {'check':spec.id, 'reason':'contract_path_unsafe'}
        if _grader_tampered(repo, destination):
            return False, {'check': spec.id, 'reason': 'grader_tampered'}
        _, report = _contract_report(repo, spec)
        if report is not None and _confined_contract_parent(repo, report) and not report.is_symlink():
            report.unlink(missing_ok=True)
        original = None
        started = time.monotonic()
        try:
            original = _contract_bytes(destination) if destination.exists() else None
            contract = _contract_bytes(spec.contract_test)
            contract_sha256 = hashlib.sha256(contract).hexdigest()
            expected = getattr(frozen, 'acceptance_digest', '')
            if expected and expected != contract_sha256:
                return False, {'check': spec.id, 'reason': 'acceptance_changed'}
            destination.parent.mkdir(parents=True, exist_ok=True)
            with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600), 'wb') as handle:
                handle.write(contract)
            command = spec.command_for(repo, target.controller)
            env = check_environment(spec, repo, target)
            try:
                completed = runner(command, cwd=str(repo), env=env, capture_output=True,
                                   text=True, timeout=spec.timeout_seconds)
            except IsolationError as exc:
                return False, {"check": spec.id, "reason": "isolation_unqualified",
                               "detail": str(exc)[:120]}
            # Deletion is tampering too; without this guard the read raises and the check is
            # misreported as a missing toolchain instead of a modified contract.
            if not _confined_contract_parent(repo, destination):
                return False, {"check": spec.id, "reason": "contract_modified"}
            try:
                intact = _contract_bytes(destination) == contract
            except OSError:
                intact = False
            if not intact:
                return False, {"check": spec.id, "reason": "contract_modified"}
            if _grader_tampered(repo, destination):
                return False, {"check": spec.id, "reason": "grader_tampered"}
        except subprocess.TimeoutExpired:
            return False, {"check": spec.id, "reason": "timeout",
                           "timeout_seconds": spec.timeout_seconds}
        except FileNotFoundError:
            return False, {"check": spec.id, "reason": "toolchain_missing"}
        except OSError:
            return False, {"check": spec.id, "reason": "check_start_failed"}
        finally:
            try:
                if _confined_contract_parent(repo, destination):
                    destination.unlink(missing_ok=True)
                    if original is not None:
                        with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'wb') as handle:
                            handle.write(original)
            except OSError:
                pass
        output = (completed.stdout or "") + "\n" + (completed.stderr or "")
        detail = {
            "check": spec.id,
            "returncode": completed.returncode,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "contract_sha256": contract_sha256,
            "failed_tests": _failed_tests(output) if completed.returncode != 0 else [],
            "contract_assertion_failures": _contract_assertions(repo,spec) if completed.returncode != 0 else 0,
        }
        if completed.returncode != 0:
            errors = _compiler_errors(output)
            detail['failure_kind'] = ('java_compilation_failed' if errors else
                                      'tests_failed' if detail['failed_tests'] else 'check_failed')
            detail['compiler_errors'] = errors
        elif not _contract_executed(repo, spec):
            detail['reason'] = 'contract_not_executed'
            detail['failure_kind'] = 'contract_not_executed'
            return False, detail
        isolation = getattr(completed, "qualification", None)
        if isolation is not None:
            detail["isolation"] = isolation
        return completed.returncode == 0, detail
    return check
