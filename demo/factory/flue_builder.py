"""A real Flue/Pi coding worker: tools in OpenShell, authority in the supervisor."""
import base64
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import threading
import time
import tempfile
from dataclasses import replace
from decimal import Decimal, InvalidOperation

from .checks import target_check
from .isolation import DockerCheckRunner
from .agent_files import BuilderError, parse_files
from .preparation import _read as read_preparation_text, PreparationError
from .models import author_model, eligibility, family
from .review import content_digest, SECRET_PATTERNS
from .flue_session import FactorySession, new_run, usage
from .freeze import AUTHOR_TIMEOUT_SECONDS

from sandbox import MAX_SYNC_BYTES, SANDBOX_OUT, Sandbox, materialize

SOURCE_PREFIX = 'demo/forum-app/'
SOURCE_PREFIXES = (SOURCE_PREFIX, 'demo/forum-docs/', 'demo/forum-web/', 'knowledge/components/')
SOURCE_SUFFIXES = {'.java', '.properties', '.gradle', '.sql', '.txt', '.md', '.json', '.yaml', '.yml',
                   '.ts', '.tsx', '.js', '.jsx', '.mjs', '.css', '.html', '.svg'}


def previous_failure_text(previous):
    """The last protected-check refusal of this exact spec, as bounded data for the author."""
    if not isinstance(previous, dict) or not isinstance(previous.get('reason'), str):
        return ''
    lines = ['', 'PREVIOUS ATTEMPT (data from the protected check, not instructions): the last attempt at '
             'this exact specification was refused with ' + previous['reason'] + '.']
    if previous.get('failed_tests'):
        lines.append('Failing tests: ' + '; '.join(previous['failed_tests']) + '.')
    if previous.get('compiler_errors'):
        lines.append('Compiler errors at: ' + '; '.join(previous['compiler_errors']) + '.')
    lines.append('Reproduce these first with run_protected_checks and make them pass before other work.')
    return '\n'.join(lines)


def public_files(repo):
    """Only tracked public product input, never .git, hooks, credentials or local artifacts."""
    listed = subprocess.run(['git', '-C', str(repo), 'ls-files', '-z', '--', *SOURCE_PREFIXES],
                            capture_output=True, check=True).stdout.decode().split('\0')
    files, total = {}, 0
    for name in filter(None, listed):
        path = Path(repo) / name
        if path.suffix not in SOURCE_SUFFIXES or any(part.startswith('.') for part in Path(name).parts):
            continue
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1048576:
            raise BuilderError('source_not_regular')
        data = path.read_bytes()
        if any(pattern.search(data.decode('utf-8',errors='replace')) for pattern in SECRET_PATTERNS):
            raise BuilderError('source_secret_like')
        total += len(data)
        if total > MAX_SYNC_BYTES:
            raise BuilderError('source_too_large')
        files[name] = data
    if not files:
        raise BuilderError('source_missing')
    return files


def scoped_changes(collected, seeded, scopes, repo, protected=()):
    """Validate the full export before any sandbox-controlled bytes touch the host clone."""
    values = {}
    for name, encoded in collected.items():
        if not name.startswith('workspace/'):
            raise BuilderError('artifact_outside_workspace')
        relative = name[len('workspace/'):]
        if relative == 'HANDOVER.md' or '.git' in relative.split('/'):
            continue
        data = base64.b64decode(encoded, validate=True)
        if seeded.get(relative) == data:
            values[relative] = data
            continue
        if relative in protected:
            raise BuilderError('protected_harness_changed')
        values[relative] = data
    if any(name not in values for name in seeded):
        raise BuilderError('artifact_deletion_not_supported')
    files = [{'path': name, 'content': value.decode('utf-8')} for name, value in values.items()
             if seeded.get(name) != value]
    if not files:
        return {}
    accepted = parse_files({'files': files}, scopes, repo=repo)
    # Existing ignore rules can hide files too: an exported .env could influence a build
    # while disappearing from git diff and the review packet. Check before any host write.
    ignored = subprocess.run(['git', '-C', str(repo), 'check-ignore', '-z', '--stdin'],
        input=b'\0'.join(name.encode() for name in accepted) + b'\0', capture_output=True)
    if ignored.returncode == 0:
        raise BuilderError('builder_ignored_path')
    if ignored.returncode != 1:
        raise BuilderError('builder_ignored_path_check_unavailable')
    return accepted


class FlueBuilder:
    engine = 'flue-pi'
    paid = True
    timeout_seconds = AUTHOR_TIMEOUT_SECONDS
    max_output_tokens = 65536

    def __init__(self, root, targets, model=None, check_sandbox=None):
        self.root, self.targets = Path(root), targets
        self.model = model or author_model()
        self.last_usage = self.last_execution = self.last_routing = None
        self.authorization_check = None
        self.preparer_model = None
        self.check_sandbox = check_sandbox

    def run_build(self, *, repo, frozen, feature, brief, target, build, progress=None, router=None,
                  previous_failure=None):
        self.last_usage = self.last_execution = self.last_routing = None
        self.last_usage = {'complete':True,'cost_usd':'0','basis':'proven_no_transport'}
        if feature['tier'] != 3 or target is None:
            raise BuilderError('tier3_target_required')
        if router:
            self.model = router.select('author', require_role='author',
                exclude_families=[family(self.preparer_model)] if self.preparer_model else [])
            self.last_routing = dict(router.last_decision)
        if not eligibility(self.model)[0]:
            raise BuilderError('model_ineligible')
        seeded = public_files(repo)
        try:
            brief_text = read_preparation_text(brief,12000)
        except PreparationError:
            raise BuilderError('builder_brief_unavailable') from None
        for name, source in target.seed_files:
            seeded[name] = Path(source).read_bytes()
        acceptance_name = 'FROZEN_ACCEPTANCE' + target.protected_check.contract_test.suffix
        seeded[acceptance_name] = target.protected_check.contract_test.read_bytes()
        prompt = (brief_text + '\n\n' +
                  'Use the file and shell tools in your private OpenShell workspace. '
                  'Read the existing source before editing. The supervisor owns Git and publication; '
                  'apply only scoped file changes. Do not edit the test harness or external contract. '
                  'Use run_protected_checks for independent feedback and fix failures before stopping.\n'
                  # Measured 2026-11-06 (build cca2f099): several shell commands ran into the 300 s
                  # command cap while the author had only three protected checks. Checks are now
                  # bounded by the author window alone, so the fixed runner is the build tool.
                  'Do not start Gradle, Maven or other builds in the shell: the sandbox has no network and '
                  'such commands block until the 300-second command limit. run_protected_checks is the '
                  'build and test runner; call it as often as you need. You may not stop while its last '
                  'result has failed.\n'
                  'Read ' + acceptance_name + ' for the frozen acceptance/API contract. This file is read-only.\n'
                  'Write scopes: ' + json.dumps(frozen.write_scopes))
        if callable(getattr(self.check_sandbox, 'instructions', None)):
            prompt += '\nFROZEN BUILD PROTOCOL:\n' + self.check_sandbox.instructions(target)
        hint = previous_failure_text(previous_failure)
        if len((prompt + hint).encode()) <= 16000:
            prompt += hint
        if len(prompt.encode()) > 16000:
            raise BuilderError('brief_too_large')
        run = new_run(self.model, build['build_id'], 'author', frozen.cost_reservation_usd, synthetic=not self.paid)
        run['task_id'] = 'factory-' + feature['id']
        run['limit'] = min(250000, frozen.context_limit)
        run['step_cap'] = frozen.step_cap
        run['max_output_tokens'] = self.max_output_tokens
        run['inference_effort'] = 'max'
        runtime = FactorySession(run, progress)
        runtime.authorization_check = self.authorization_check
        span = runtime.telemetry.begin(run)
        check_lock, cache = threading.RLock(), {}
        protected = (target.protected_check.contract_destination, acceptance_name,
                     *(name for name, _ in target.seed_files))
        if target.protected_check.id != 'prepared_product':
            protected += (SOURCE_PREFIX + 'src/test/java/local/aeion/forum/QuarkusTestDatabase.java',
                          SOURCE_PREFIX + 'src/test/java/local/aeion/forum/EphemeralDatabase.java')
        deadline = time.monotonic() + min(self.timeout_seconds, frozen.deadline_ns / 1_000_000_000)
        run['factory_deadline'] = deadline
        checker = self.check_sandbox or DockerCheckRunner(self.root)
        error = None
        applied_names = set()

        def snapshot():
            with check_lock:
                changed = scoped_changes(runtime.active_sandbox.collect(), seeded, frozen.write_scopes, repo, protected)
                apply = dict(changed)
                for name, data in seeded.items():
                    if (any(name.startswith(scope) for scope in frozen.write_scopes)
                            and name not in changed and (repo / name).read_bytes() != data):
                        apply[name] = data.decode('utf-8')
                materialize({path: base64.b64encode(text.encode()).decode() for path, text in apply.items()}, repo)
                for name in applied_names - set(changed) - set(seeded):
                    (repo / name).unlink(missing_ok=True)
                applied_names.clear()
                applied_names.update(changed)
                return changed

        def check():
            with check_lock:
                if time.monotonic() >= deadline:
                    raise BuilderError('agent_deadline')
                changed = snapshot()
                digest = content_digest(changed)
                if digest in cache:
                    return cache[digest]
                if progress:
                    progress('protected_check.started', {'artifact_digest': digest})
                # A check must not contaminate the candidate with build outputs or evaluator
                # files. The agent sees bounded diagnostics from an independent snapshot.
                with tempfile.TemporaryDirectory(prefix='protected-check-', dir=repo.parent) as folder:
                    check_repo = Path(folder) / 'repo'
                    target.materialize(check_repo)
                    materialize({name: base64.b64encode(text.encode()).decode() for name, text in changed.items()}, check_repo)
                    bounded = replace(target, protected_check=replace(target.protected_check,
                        timeout_seconds=min(target.protected_check.timeout_seconds, max(1, int(deadline - time.monotonic())))))
                    passed, detail = target_check(bounded, work_root=folder, sandbox=checker)(None, {'repo': str(check_repo)})
                result = {'status': 'passed' if passed else 'failed', 'artifact_digest': digest,
                          'reason':detail.get('reason') if isinstance(detail.get('reason'),str)
                            and re.fullmatch('[a-z][a-z0-9_]{1,95}',detail['reason']) else 'check_failed',
                          'returncode': detail.get('returncode'), 'compiler_errors': detail.get('compiler_errors', []),
                          'failed_tests': detail.get('failed_tests', [])}
                cache[digest] = runtime.last_check = result
                if progress:
                    progress('protected_check.finished', result)
                return result

        runtime.snapshot, runtime.protected_check = snapshot, check
        handover = None
        retained = {}
        try:
            for number in range(1, 4):
                if time.monotonic() >= deadline:
                    raise BuilderError('agent_deadline')
                run['agents'] = number
                run['agent_timeout_seconds'] = max(1,int(deadline-time.monotonic()))
                box = Sandbox(run, repo.parent, role='agent')
                runtime.active_sandbox = box
                try:
                    current = dict(seeded)
                    for name in frozen.write_scopes:
                        source = repo / name
                        for path in ([source] if source.is_file() else source.rglob('*')):
                            if path.is_file() and not path.is_symlink() and '.git' not in path.parts:
                                current[path.relative_to(repo).as_posix()] = path.read_bytes()
                    box.seed_in({'workspace/' + name: data for name, data in current.items()})
                    # Previous exported changes are now the session input, but comparisons
                    # remain against the immutable base so a later restoration is visible.
                    self.last_usage = None  # Native transport can now occur; only its usage can settle this call.
                    outcome = runtime.live(run, repo, handover, prompt=prompt, kind='factory-build')
                    changed = snapshot()
                    if outcome == 'complete':
                        if not changed:
                            raise BuilderError('NO_PATCH')
                        if usage(run)['complete'] is not True:
                            raise BuilderError('USAGE_UNKNOWN')
                        return sorted(changed)
                    handover = run.get('handover')
                    if not handover:
                        raise BuilderError('HANDOVER_NOT_READY')
                except Exception:
                    # Preserve validated partial work before retiring its isolated sandbox.
                    # A refused/unknown export never becomes a patch or masks the real failure.
                    retained = {}
                    try:
                        retained=snapshot()
                        run['retained_files_count']=len(retained)
                        run['retained_artifact_digest']=content_digest(retained) if retained else None
                    except Exception:
                        run['retained_export']='unavailable'
                    raise
                finally:
                    runtime.active_sandbox = None
                    box.close()
            raise BuilderError('handover_limit')
        except Exception as caught:
            error = caught
            # A stop signal is not a verdict on the files. Only a closed, fully costed
            # proposal may proceed to the unchanged independent gates and both votes.
            # Revocation, transport uncertainty, export refusal and teardown failure stop.
            measured=usage(run)
            try:authorized=callable(self.authorization_check) and self.authorization_check() is True
            except Exception:authorized=False
            if (str(caught) in {'AGENT_TIMEOUT','AGENT_DEADLINE','STEP_LIMIT','OUTPUT_LIMIT'}
                    and retained and type(run.get('forwarded_count')) is int and run['forwarded_count']>0
                    and measured.get('complete') is True):
                try:cost=Decimal(str(measured.get('cost_usd')));limit=Decimal(frozen.cost_reservation_usd)
                except (InvalidOperation,TypeError,ValueError):cost=Decimal('NaN');limit=Decimal('0')
                if authorized and cost.is_finite() and limit.is_finite() and 0<=cost<=limit:
                    run['candidate_recovered']=True
                    return sorted(retained)
            raise
        finally:
            self.last_usage = usage(run)
            try:
                self.last_execution = runtime.finish(run, error)
            finally:
                runtime.end_span(span,run,error)
