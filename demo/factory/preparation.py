"""Freeze a catalog MD and independently prepare its protected Java acceptance contract.

Spec: knowledge/components/factory-flue.md

Model output may supply test bytes, never a command, repository, scope or permission.
The Java adapter is deliberately separate from unqualified PostgreSQL/web adapters.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

from .checks import target_check
from .models import RoutingError, eligibility, family
from .review import SECRET_PATTERNS
from .target import ProtectedCheck, Target, _git, SHA_RE, PUBLIC_JAVA
from .source import SourceSyncError

REPOSITORY = 'OualidGuennif/aeion-autonomous-forum'
JAVA_MAIN = 'demo/forum-app/src/main/java/local/aeion/forum/'
JAVA_TEST = 'demo/forum-app/src/test/java/local/aeion/forum/'
JAVA_RESOURCES = 'demo/forum-app/src/main/resources/'
SCOPES = (JAVA_MAIN, JAVA_TEST, JAVA_RESOURCES, 'demo/forum-docs/')
MAX_PROMPT_BYTES = 200000
TRANSITION_FEATURES = {'001', '002', '003'}


class PreparationError(ValueError):
    """A fixed preparation refusal without private diagnostics or model text."""


def _read(path, limit):
    """Read one regular UTF-8 file without following its final symlink or blocking on a FIFO."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise PreparationError('preparation_input_unsafe')
            raw = handle.read(limit + 1)
        if len(raw) > limit or b'\0' in raw:
            raise PreparationError('preparation_input_too_large_or_binary')
        return raw.decode('utf-8')
    except (OSError, UnicodeError):
        raise PreparationError('preparation_input_unavailable') from None


def _digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _contained(scope, parent):
    return scope == parent.rstrip('/') or scope.startswith(parent)


@dataclass(frozen=True)
class Task:
    feature_id: str
    catalog_digest: str
    specification: str
    architecture: str
    base_sha: str
    write_paths: tuple

    def identity(self):
        return {'feature_id': self.feature_id, 'catalog_digest': self.catalog_digest,
                'spec_digest': _digest(self.specification), 'architecture_digest': _digest(self.architecture),
                'base_sha': self.base_sha, 'write_paths': list(self.write_paths)}

    def digest(self):
        return _digest(json.dumps(self.identity(), sort_keys=True, separators=(',', ':')))


def freeze_task(catalog, feature_id, spec_dir, architecture, base_sha, *, product=False):
    feature = catalog.by_id.get(feature_id)
    if feature is None or not re.fullmatch('[0-9]{3}', feature_id):
        raise PreparationError('preparation_feature_unknown')
    if not catalog.contract_current(feature_id):
        raise PreparationError('preparation_contract_changed')
    if not isinstance(base_sha, str) or not SHA_RE.fullmatch(base_sha):
        raise PreparationError('preparation_base_invalid')
    filename = feature.get('file')
    if (not isinstance(filename, str) or Path(filename).name != filename
            or '\\' in filename or not filename.endswith('.md')):
        raise PreparationError('preparation_spec_path_invalid')
    specification = _read(Path(spec_dir) / filename, 12000)
    architecture_text = _read(architecture, 12000)
    if not catalog.matches_inputs(feature_id, _digest(specification), _digest(architecture_text)):
        raise PreparationError('preparation_contract_changed')
    if feature.get('architecture_digest') != _digest(architecture_text):
        raise PreparationError('preparation_architecture_changed')
    if '## Acceptance checks' not in specification or '- [ ] ' not in specification:
        raise PreparationError('preparation_acceptance_missing')
    scopes = feature.get('write_paths')
    if (not isinstance(scopes, list) or not scopes
            or any(not isinstance(p, str) or (not product and not p.endswith('/')) or '\\' in p
                or any(c in ('', '.', '..') or c.startswith('.') for c in p.rstrip('/').split('/'))
                or not p.startswith(('demo/forum-app/', 'demo/forum-docs/', 'demo/forum-web/', 'knowledge/components/') if product else ('demo/forum-app/', 'demo/forum-docs/')) for p in scopes)):
        raise PreparationError('preparation_profile_unavailable')
    # Narrow ordinary Java changes. Dependency/configuration transitions need their own
    # qualified adapter; a broad app root never grants control of the Gradle evaluator.
    narrowed = tuple(sorted({allowed if _contained(allowed, declared) else declared
        for declared in scopes for allowed in (SCOPES + ('demo/forum-web/', 'demo/forum-app/src/test/resources/', 'knowledge/components/') if product else SCOPES)
        if _contained(allowed, declared) or _contained(declared, allowed)}))
    if not narrowed:
        raise PreparationError('preparation_scope_unavailable')
    if feature_id in TRANSITION_FEATURES and not product:
        raise PreparationError('preparation_transition_checker_unqualified')
    if product and feature_id == '002':
        narrowed = tuple(sorted({*narrowed, 'demo/forum-app/build.gradle'}))
    return Task(feature_id, catalog.digest, specification, architecture_text, base_sha, narrowed)


class FluePreparation:
    paid = True
    timeout_seconds = 1200

    def __init__(self):
        self.authorization_check = None
        self.progress = None
        self.last_usage = self.last_execution = self.last_feedback = None

    def __call__(self, model, prompt, build_id):
        from .flue_session import FactorySession, new_run, usage
        self.last_usage = self.last_execution = self.last_feedback = None
        if len(prompt.encode('utf-8')) > MAX_PROMPT_BYTES or not eligibility(model)[0]:
            raise PreparationError('preparation_not_admitted')
        run = new_run(model, build_id, 'prepare', '0.50', synthetic=not self.paid)
        run['agent_timeout_seconds'] = self.timeout_seconds
        run['max_output_tokens'] = 65536
        runtime = FactorySession(run, self.progress)
        runtime.authorization_check = self.authorization_check
        span, error = runtime.telemetry.begin(run), None
        try:
            with tempfile.TemporaryDirectory(prefix='aeion-prepare-') as folder:
                output = Path(folder) / 'result.json'
                outcome = runtime.live(run, Path(folder), None, prompt=prompt,
                    kind='factory-prepare', preparation_result=output)
                if outcome != 'complete':
                    raise PreparationError('preparation_incomplete')
                if usage(run)['complete'] is not True:
                    raise PreparationError('preparation_usage_unknown')
                result = json.loads(_read(output, 65536))
                if (not isinstance(result, dict) or set(result) - {'feedback'} != {'status', 'contract', 'reason'}
                        or result['status'] not in ('ready', 'blocked')
                        or not isinstance(result['contract'], str) or not isinstance(result['reason'], str)
                        or len(result['reason']) > 120
                        or not isinstance(result.get('feedback', ''), str) or len(result.get('feedback', '')) > 800):
                    raise PreparationError('preparation_response_invalid')
                # Owner-only: the frozen contract never carries the preparer's note.
                self.last_feedback = result.pop('feedback', None) or None
                return result
        except Exception as caught:
            error = caught
            if isinstance(caught, ValueError) and not isinstance(caught, PreparationError):
                code = str(caught)
                if re.fullmatch('[A-Z][A-Z0-9_]{1,63}', code):
                    raise PreparationError('preparation_' + code.lower()) from None
            raise
        finally:
            self.last_usage = usage(run)
            try:
                self.last_execution = runtime.finish(run, error)
            finally:
                runtime.end_span(span,run,error)


class TaskPreparer:
    """One shared trusted Java profile, instead of a JSON configuration for every feature."""
    timeout_seconds = 1800  # One bounded preparation session and one protected baseline check.

    def __init__(self, root, source, role=None, checker=None, base_ref='refs/remotes/origin/main',synchronize=None, product=False):
        self.root, self.source = Path(root).resolve(), Path(source).resolve()
        self.role, self.checker = role or FluePreparation(), checker
        self.base_ref = base_ref
        self.synchronize = synchronize
        self.last_model = None
        self.product = bool(product)

    def resume_prepared(self, destination):
        """Reuse this build's prepared contract. A linked or altered folder is refused."""
        folder = Path(destination)
        meta_path, brief = folder / 'task.json', folder / 'BRIEF.md'
        if (folder.is_symlink() or not folder.is_dir() or any(path.is_symlink() for path in (meta_path, brief))
                or not meta_path.is_file() or not brief.is_file()):
            raise PreparationError('preparation_workspace_refused')
        try:
            evidence = json.loads(meta_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            raise PreparationError('preparation_workspace_refused') from None
        feature, base, paths = evidence.get('feature_id'), evidence.get('base_sha'), evidence.get('write_paths')
        identity = {'feature_id': feature, 'catalog_digest': evidence.get('catalog_digest'),
                    'spec_digest': evidence.get('spec_digest'), 'architecture_digest': evidence.get('architecture_digest'),
                    'base_sha': base, 'write_paths': list(paths) if isinstance(paths, list) else paths}
        contract = folder / 'acceptance.mjs'
        if (not self.product or feature in ('002', '014') or not isinstance(feature, str)
                or not isinstance(base, str) or not SHA_RE.fullmatch(base)
                or not isinstance(paths, list) or not all(isinstance(path, str) and path for path in paths)
                or evidence.get('task_digest') != _digest(json.dumps(identity, sort_keys=True, separators=(',', ':')))
                or contract.is_symlink() or not contract.is_file()):
            raise PreparationError('preparation_workspace_refused')
        try:
            spec, text = brief.read_text(encoding='utf-8'), contract.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            raise PreparationError('preparation_workspace_refused') from None
        if evidence.get('spec_digest') != _digest(spec) or evidence.get('acceptance_digest') != _digest(text):
            raise PreparationError('preparation_workspace_refused')
        self.last_model = None
        self.role.last_execution = self.role.last_usage = None
        check = ProtectedCheck('prepared_product', [], {}, contract, 'FACTORY_EXTERNAL_ACCEPTANCE.mjs', 900)
        target = Target('prepared-' + feature, feature, REPOSITORY, self.root, self.source,
                         base, list(paths), brief, check)
        return target, evidence

    def _public_interfaces(self, base):
        listing = _git(['-C', str(self.source), 'ls-tree', '-r', base, '--', JAVA_MAIN])
        if listing.returncode:
            raise PreparationError('preparation_source_unavailable')
        parts = []
        for entry in listing.stdout.splitlines():
            metadata, path = entry.split('\t', 1)
            if not path.endswith('.java'):
                continue
            if not metadata.startswith('100644 blob ') or not PUBLIC_JAVA.fullmatch(path):
                raise PreparationError('preparation_source_unsafe_or_too_large')
            size = _git(['-C', str(self.source), 'cat-file', '-s', base + ':' + path])
            if size.returncode or not size.stdout.strip().isdigit() or int(size.stdout) > 100000:
                raise PreparationError('preparation_source_unsafe_or_too_large')
            blob = _git(['-C', str(self.source), 'show', base + ':' + path])
            if blob.returncode:
                raise PreparationError('preparation_source_unavailable')
            if not re.search(r'@(?:(?:jakarta|javax)\.ws\.rs\.)?Path\s*\(',blob.stdout):
                continue
            if (not self.product and len(parts)>=8) or len(blob.stdout.encode())>100000:
                raise PreparationError('preparation_source_unsafe_or_too_large')
            if any(pattern.search(blob.stdout) for pattern in SECRET_PATTERNS):
                raise PreparationError('preparation_source_unavailable')
            parts.append('FILE: ' + path + '\n' + blob.stdout + '\nEND FILE\n')
        context = '\n'.join(parts)
        if self.product and len(context.encode('utf-8')) > 120000:
            # Explicit declaration index, never represented as a parsed OpenAPI document.
            context = '\n'.join(line for line in context.splitlines() if re.search(
                r'^FILE:|^END FILE|@|\b(public|record|class|interface|enum)\b', line))
        if len(context.encode('utf-8')) > (160000 if self.product else 48000):
            raise PreparationError('preparation_source_unsafe_or_too_large')
        return context

    def prepare(self, *, build, catalog, spec_dir, destination, budget, router, authorized):
        self.last_model = None
        self.role.last_execution = None
        from .budget import BudgetError
        self.last_model = None
        self.role.last_usage = self.role.last_execution = None
        if not authorized():
            raise PreparationError('preparation_revoked')
        if build.get('contract_digest') is not None and not catalog.matches_contract(build):
            raise PreparationError('preparation_contract_changed')
        if self.checker is None:
            raise PreparationError('preparation_checker_unqualified')
        synchronized=None
        if self.synchronize is not None:
            try:synchronized=self.synchronize()
            except SourceSyncError as error:raise PreparationError(str(error)) from None
            if not isinstance(synchronized,str) or not SHA_RE.fullmatch(synchronized):
                raise PreparationError('source_sync_unavailable')
            if not authorized():raise PreparationError('preparation_revoked')
        base = _git(['-C', str(self.source), 'rev-parse', '--verify', self.base_ref + '^{commit}'])
        if base.returncode:
            raise PreparationError('preparation_base_unavailable')
        if synchronized is not None and base.stdout.strip()!=synchronized:
            raise PreparationError('source_ref_changed')
        task = freeze_task(catalog, build['feature_id'], spec_dir,
                           self.root / 'demo/forum/ARCHITECTURE.md', base.stdout.strip(), product=self.product)
        # Unrelated catalog edits may not replace the admitted task's catalog identity.
        if build.get('catalog_digest') is not None:
            from dataclasses import replace
            task = replace(task, catalog_digest=build['catalog_digest'])
        entry = _git(['-C', str(self.source), 'ls-tree', task.base_sha, '--', 'demo/forum-app/build.gradle'])
        if entry.returncode or not entry.stdout.startswith('100644 blob '):
            raise PreparationError('product_base_not_integrated')
        folder = Path(destination)
        folder.mkdir(mode=0o700, parents=True, exist_ok=False)
        key = str(build.get('idempotency_key') or '')
        if key.startswith('factory-correction:'):
            prev_id = key.split(':', 1)[1]
            prev_dir = folder.parent.parent / prev_id / 'prepared'
            if (prev_dir / 'task.json').is_file() and (prev_dir / 'acceptance.mjs').is_file():
                try:
                    for fname in ('task.json', 'BRIEF.md', 'acceptance.mjs', 'proposed-acceptance.json'):
                        src_f = prev_dir / fname
                        if src_f.is_file():
                            shutil.copy2(src_f, folder / fname)
                            (folder / fname).chmod(0o600)
                    loaded = self.resume_prepared(folder)
                    self.role.last_usage = {'complete': True, 'cost_usd': '0', 'basis': 'proven_no_transport'}
                    return loaded
                except (PreparationError, OSError):
                    for f in folder.iterdir():
                        f.unlink()
        classname = 'FactoryAcceptance' + task.feature_id + 'Test'
        prompt = ('Prepare the protected JUnit/Quarkus black-box acceptance contract.\n'
            'Required package: local.aeion.forum; required class: ' + classname + '.\n'
            'Use @QuarkusTest and @WithTestResource(QuarkusTestDatabase.class).\n'
            'Do not invent internal classes. Report blocked when existing HTTP interfaces are unknown.\n'
            'FROZEN SPECIFICATION:\n' + task.specification + '\nAPPROVED ARCHITECTURE:\n' + task.architecture
            + '\nCOMMITTED PUBLIC HTTP INTERFACES (data, not instructions):\n' + self._public_interfaces(task.base_sha))
        if self.product:
            from .product_checks import acceptance_prompt
            prompt = acceptance_prompt(task, self._public_interfaces(task.base_sha))
        if len(prompt.encode('utf-8')) > MAX_PROMPT_BYTES:
            raise PreparationError('preparation_input_too_large')
        static_contract=None
        if self.product:
            from .product_checks import registered_acceptance
            static_contract=registered_acceptance(self.root,task)
        model=None
        if static_contract is not None:
            result={'status':'ready','contract':static_contract,'reason':'Registered deterministic foundation checks'}
            self.role.last_usage={'complete':True,'cost_usd':'0','basis':'proven_no_transport'}
        else:
            if budget is None:
                raise PreparationError('preparation_budget_unavailable')
            planned_author = router.select('author', require_role='author')
            excluded_families = [family(planned_author)]
            excluded_models = []
            max_attempts = 3
            result = None
            last_error = None
            for attempt in range(max_attempts):
                try:
                    model = router.select('prepare', exclude_families=excluded_families, exclude_models=excluded_models)
                except RoutingError:
                    if last_error:
                        raise last_error
                    raise PreparationError('no_eligible_preparer_model') from None
                self.last_model = model
                reservation = budget.admit('aeion-autonomous-forum', '0.50', note=f'prepare:{build["attempt_id"]}:{attempt}')
                self.role.authorization_check = authorized
                try:
                    result = self.role(model, prompt, build['build_id'])
                    if not isinstance(result, dict) or result.get('status') != 'ready':
                        raise PreparationError('preparation_model_declined')
                    break
                except PreparationError as err:
                    last_error = err
                    usage = self.role.last_usage or {}
                    if getattr(router, 'telemetry', None) is not None and usage.get('complete') is True:
                        try:
                            router.telemetry.record(model, 'prepare', 'error', cost_usd=usage.get('cost_usd'))
                        except Exception:
                            pass
                    RETRYABLE = ('preparation_output_limit', 'preparation_cli_failed',
                                 'preparation_incomplete', 'preparation_agent_timeout',
                                 'preparation_provider_rate_limited', 'preparation_provider_unavailable',
                                 'preparation_usage_unknown', 'preparation_model_declined')
                    if any(code in str(err) for code in RETRYABLE) and attempt + 1 < max_attempts:
                        excluded_models.append(model)
                        excluded_families.append(family(model))
                        continue
                    raise
                finally:
                    usage = self.role.last_usage or {}
                    if usage.get('complete') is True and usage.get('cost_usd') is not None:
                        try:
                            budget.settle(reservation, Decimal(str(usage['cost_usd'])))
                        except (BudgetError, InvalidOperation, ValueError):
                            pass  # Unknown cost retains its reservation and never becomes free.
            if result is None:
                if last_error:
                    raise last_error
                raise PreparationError('preparation_failed')
        if (not isinstance(self.role.last_usage,dict) or self.role.last_usage.get('complete') is not True
                or self.role.last_usage.get('cost_usd') is None):
            raise PreparationError('preparation_usage_unknown')
        with (folder/'proposed-acceptance.json').open('x',encoding='utf-8') as handle:
            json.dump(result,handle,sort_keys=True);handle.flush();os.fsync(handle.fileno())
        (folder/'proposed-acceptance.json').chmod(0o600)
        text = result.get('contract')
        if self.product:
            from .product_checks import prepared_target, validate_acceptance
            if result.get('status') != 'ready':
                raise PreparationError('preparation_model_declined')
            validate_acceptance(text)
            target = prepared_target(self.root, self.source, task, folder, text)
        else:
            if (result.get('status') != 'ready' or not isinstance(text, str) or not text
                    or len(text.encode('utf-8')) > 48000 or '\0' in text
                    or not re.search(r'\bclass\s+' + classname + r'\b', text)
                    or not re.search(r'\bpackage\s+local\.aeion\.forum\s*;', text)
                    or '@Test' not in text or '@Disabled' in text):
                raise PreparationError('preparation_contract_unavailable')
            brief, contract = folder / 'BRIEF.md', folder / (classname + '.java')
            for path, content in ((brief, task.specification), (contract, text)):
                with path.open('x', encoding='utf-8', newline='') as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                path.chmod(0o600)
            destination_path = JAVA_TEST + classname + '.java'
            if _git(['-C', str(self.source), 'cat-file', '-e', task.base_sha + ':' + destination_path]).returncode == 0:
                raise PreparationError('preparation_contract_collision')
            target = Target('prepared-' + task.feature_id, task.feature_id, REPOSITORY, self.root, self.source,
                task.base_sha, list(task.write_paths), brief, ProtectedCheck('prepared_gradle',
                    ['{controller}/demo/.local/tools/gradle-9.8.2/bin/gradle', '-p', '{repo}/demo/forum-app',
                     'test', '--offline', '--console=plain', '--no-daemon'], {}, contract, destination_path, 900))
        with tempfile.TemporaryDirectory(prefix='baseline-', dir=folder) as temporary:
            repo = Path(temporary) / 'repo'
            target.materialize(repo)
            passed, detail = target_check(target, work_root=temporary, sandbox=self.checker)(None, {'repo':str(repo)})
        if detail.get('reason')=='isolation_unqualified':
            raise PreparationError('preparation_checker_unqualified')
        if self.product:
            effective = detail.get('contract_assertion_failures', 0) > 0
            # A registered foundation transition also checks startup against deliberately
            # unavailable storage. Startup rejection is an explicit baseline, not compiler failure.
            registered_startup_rejection = (static_contract is not None and task.feature_id == '001'
                and detail.get('reason') in {'application_start_failed',
                    'explicit_database_less_startup_rejected','default_database_less_startup_rejected'})
            registered_transition_absence=(static_contract is not None and task.feature_id in ('002','014') and detail.get('reason')==
                {'002':'registered_postgres_operator_missing','014':'registered_web_source_missing'}.get(task.feature_id))
            effective |= registered_startup_rejection or registered_transition_absence
            if passed or not effective:
                raise PreparationError('preparation_negative_control_missing')
        elif (passed or detail.get('failure_kind') != 'tests_failed'
                or detail.get('contract_assertion_failures',0) < 1
                or not any(classname + ' > ' in item for item in detail.get('failed_tests', []))):
            raise PreparationError('preparation_negative_control_missing')
        if not authorized():
            raise PreparationError('preparation_revoked')
        evidence = {**task.identity(), 'task_digest':task.digest(), 'acceptance_digest':_digest(text),
                    'preparer_model':model, 'negative_control':('registered_foundation_startup_rejection' if self.product and
                        registered_startup_rejection else 'registered_transition_source_missing' if self.product and
                        registered_transition_absence else 'failed_contract_assertion'),
                    'synthetic':not self.role.paid}
        if self.product:
            evidence.update(schema_version=2, preparation_kind=('registered_static_acceptance'
                if static_contract is not None else 'flue_prepared'))
        # Private task artifacts contain code; receipts and default telemetry carry hashes only.
        with (folder / 'task.json').open('x', encoding='utf-8') as handle:
            json.dump(evidence, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        return target, evidence
