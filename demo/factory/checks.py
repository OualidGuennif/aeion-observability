"""Protected check registry and evaluator, held outside any candidate's control.

Acceptance cases are built from the frozen spec. A missing required check yields
``qualification_missing``, never a green result; a candidate can supply code, not the
evaluator that judges it.
"""
import hashlib
import os
import shutil
import subprocess
import time
from pathlib import Path


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


def target_check(target, runner=None, work_root=None):
    """Run the profile's protected check against the materialised candidate tree.

    The contract test is copied in from outside the candidate's write scopes, runs with
    the host toolchain, and is restored afterwards. Only a bounded failure summary is
    recorded: no raw output, no candidate-controlled evaluator.
    """
    runner = runner or subprocess.run
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
        destination = repo / spec.contract_destination
        original = destination.read_bytes() if destination.is_file() else None
        started = time.monotonic()
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(spec.contract_test, destination)
            command = spec.command_for(repo, target.controller)
            env = {**os.environ, **spec.env_for(repo, target.controller)}
            completed = runner(command, cwd=str(repo), env=env, capture_output=True,
                               text=True, timeout=spec.timeout_seconds)
        except subprocess.TimeoutExpired:
            return False, {"check": spec.id, "reason": "timeout",
                           "timeout_seconds": spec.timeout_seconds}
        except FileNotFoundError:
            return False, {"check": spec.id, "reason": "toolchain_missing"}
        except OSError:
            return False, {"check": spec.id, "reason": "check_start_failed"}
        finally:
            try:
                if original is None:
                    destination.unlink(missing_ok=True)
                else:
                    destination.write_bytes(original)
            except OSError:
                pass
        output = (completed.stdout or "") + "\n" + (completed.stderr or "")
        detail = {
            "check": spec.id,
            "returncode": completed.returncode,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "contract_sha256": hashlib.sha256(spec.contract_test.read_bytes()).hexdigest(),
            "failed_tests": _failed_tests(output) if completed.returncode != 0 else [],
        }
        return completed.returncode == 0, detail
    return check
