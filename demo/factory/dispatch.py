"""S2+S3 dispatch: freeze, build, validate, check, review and record a bound receipt.

Builders may use live inference or a labeled fixture. A fake forge is the default and a local
live completion is not evidence of a GitHub operation or an integrated feature. The gate
never trusts the candidate's own claims: it re-checks the frozen identity and the actual
diff, then asks the publisher policy before recording anything.
"""
import json
import hashlib
import re
import shutil
import subprocess
import tempfile
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import boundary as stop
from .artifact import scoped_texts, validate_artifact
from .connectivity import NETWORK_STOPS, same_model_resume, resume_trigger
from .budget import BudgetError
from .checks import DEFAULT_CHECKS, ProtectedChecks, target_check
from .freeze import FreezeError, freeze_build
from .gateway import SessionError
from .github import GitHubForge
from .keys import assert_worker_isolated
from .models import Router, Telemetry
from .routing import OutcomeTelemetry, cohort_for
from .agent_files import BuilderError
from .publish import FakeForge, Publisher
from .review import SECRET_PATTERNS, content_digest, review
from .review_circuit import two_vote_review, baseline_diff, CircuitError, MAX_SUBSTITUTIONS
from .store import (FAILED, HELD, LIVE_COMPLETE, MAX_ATTEMPTS, MAX_CORRECTION_ROUNDS, QUEUED,
                    SIMULATED_COMPLETE, StoreError, continuation_step)
from .target import TargetError
from .preparation import PreparationError

DEFAULT_REQUIRED_CHECKS = ["scope", "spec_unchanged"]
# Author stops that say nothing against the candidate or the boundary: the next attempt, on
# another model, continues from the validated candidate. Everything else (scope or secret
# refusals, revocation, a lost sandbox, unknown cost or context accounting, missing funds or
# keys) stops the chain for the owner: unknown means no.
RETRYABLE_AUTHOR_STOPS = frozenset({
    'CLI_FAILED', 'CLI_STARTUP_FAILED', 'CLI_PROTOCOL_ERROR', 'HARNESS_COMPACTION',
    'PROVIDER_ERROR', 'PROVIDER_UNAVAILABLE', 'PROVIDER_RATE_LIMITED', 'PROVIDER_TIMEOUT',
    'PROVIDER_REJECTED', 'MODEL_DISABLED', 'TRANSPORT_ERROR', 'BUDGET_STOP', 'STEP_LIMIT',
    'OUTPUT_LIMIT', 'AGENT_TIMEOUT', 'AGENT_DEADLINE', 'HANDOVER_NOT_READY', 'NO_PATCH',
    'agent_deadline', 'handover_limit', 'no_eligible_model', 'model_ineligible', 'repeated_check_failure', 'RELAY_FAULT'})
TOKEN = re.compile(r'[A-Za-z][A-Za-z0-9_]{1,63}')


def next_step(attempt, number, crash=False):
    """The (attempt, round) after a refused or crashed one, or None when the owner decides.

    A refusal is corrected by the same model while rounds remain, then a new attempt starts on
    another model; a crash always starts the next attempt.
    """
    if crash:
        if type(attempt) is int and 1 <= attempt < MAX_ATTEMPTS:
            return attempt + 1, 0
        return None
    return continuation_step(attempt, number)


def _token(value):
    return value if isinstance(value, str) and TOKEN.fullmatch(value) else None


def replace_own_directory(work_root, build_id, name):
    if (name not in ('prepared', 'repo') or not isinstance(build_id, str)
            or not re.fullmatch(r'[a-f0-9]{32}', build_id)):
        raise ValueError('workspace_refused')
    root = Path(work_root).resolve()
    build_root = root / build_id
    if build_root.is_symlink():
        raise ValueError('workspace_refused')
    directory = build_root / name
    if directory.is_symlink() or (directory.exists() and directory.resolve().parent != build_root.resolve()):
        raise ValueError('workspace_refused')
    if directory.exists():
        shutil.rmtree(directory)


def review_retry_eligible(receipt):
    if not isinstance(receipt, dict):
        return False
    circuit = receipt.get('circuit') if isinstance(receipt.get('circuit'), dict) else {}
    context = receipt.get('review_context') if isinstance(receipt.get('review_context'), dict) else {}
    gate = receipt.get('gate') if isinstance(receipt.get('gate'), dict) else {}
    return (circuit.get('reason') == 'reviewer_failed'
            and circuit.get('review_input_version') == 2
            and context.get('retry_failed_review') is not True
            and gate.get('status') == 'passed')


DEFAULT_TARGET_REPO = "agora/forum"
HOLD_REASON_MAP = {
    "owner_review_required": "owner_review_required",
    "stale_base": "reconciliation_needed",
    "stale_head": "reconciliation_needed",
}


# Fixed repair notes for required checks this factory knows. They are our text, never a CI log.
CI_REPAIRS = {
    "Knowledge, links and repository health":
        "Repair this check only: a changed code file needs its owning knowledge document updated "
        "in the same change (rule L3), or a Docs-Checked note when no fact changed. "
        "Do not redesign the feature.",
    "Product artifacts":
        "Repair this check only: fix the failing product build or test. Do not change ports, "
        "routes, or defaults the brief does not name.",
    "Graphify and Archify":
        "Repair this check only: fix the repository structure check. Do not redesign the feature.",
    "secret-scan":
        "Repair this check only: remove credential-shaped text from the change. Do not copy that text.",
    "dependency-scan":
        "Repair this check only: fix the dependency finding. Do not add a package the brief does not name.",
    "sast-scan":
        "Repair this check only: fix the static-analysis finding in the changed code.",
}


def _named_checks(failed_checks):
    """A short list of real check names, or None when the list is not safe to store."""
    name_ok = re.compile(r'[A-Za-z0-9_ .,/:+-]{1,80}')
    conclusions = {'failure', 'cancelled', 'timed_out', 'action_required', 'skipped',
                   'neutral', 'stale', 'startup_failure', 'failed'}
    if not isinstance(failed_checks, list) or not 0 < len(failed_checks) <= 8:
        return None
    clean = []
    for item in failed_checks:
        if not isinstance(item, dict):
            return None
        name, conclusion = item.get('name'), item.get('conclusion')
        if (not isinstance(name, str) or not name_ok.fullmatch(name) or name == 'check'
                or conclusion not in conclusions):
            return None
        clean.append({'name': name, 'conclusion': conclusion})
    return clean


def repair_blind_ci(store, build_id, failed_checks):
    """Name a placeholder CI failure and queue that same unchanged correction once."""
    clean = _named_checks(failed_checks)
    if clean is None:
        return {'status': 'unchanged'}
    with store._lock:
        conn = store._connect()
        try:
            with conn:
                conn.execute('BEGIN IMMEDIATE')
                row = store._row(conn, build_id)
                if row is None or row['status'] != HELD or row['hold_reason'] != 'owner_review_required':
                    return {'status': 'unchanged'}
                receipt = store._receipt_dict(row)
                if receipt.get('reason') != 'correction_unchanged' or receipt.get('ci_repair_retried') is True:
                    return {'status': 'unchanged'}
                link = store._correction_link(conn, build_id)
                if link is None:
                    return {'status': 'unchanged'}
                previous = store._row(conn, link['previous_build_id'])
                if previous is None or previous['status'] != FAILED:
                    return {'status': 'unchanged'}
                prior = store._receipt_dict(previous)
                publisher = prior.get('publisher') if isinstance(prior.get('publisher'), dict) else {}
                stored = publisher.get('failed_checks') if isinstance(publisher.get('failed_checks'), list) else []
                if (publisher.get('reason') != 'ci_failed' or not stored
                        or any(not isinstance(item, dict) or item.get('name') != 'check' for item in stored)):
                    return {'status': 'unchanged'}
                prior['publisher'] = {**publisher, 'failed_checks': clean}
                receipt['ci_repair_retried'] = True
                now = store._now()
                conn.execute('UPDATE builds SET receipt=?,updated_ns=? WHERE build_id=?',
                             (json.dumps(prior), now, previous['build_id']))
                conn.execute(
                    'UPDATE builds SET status=?,hold_reason=NULL,receipt=?,lease_until_ns=NULL,updated_ns=? '
                    'WHERE build_id=?',
                    (QUEUED, json.dumps(receipt), now, build_id))
                store._event(conn, build_id, now, 'supervisor', QUEUED,
                             json.dumps({'reason': 'ci_repair_retried'}), row['cancellation_generation'])
                return {'status': 'queued', 'build_id': build_id}
        finally:
            conn.close()


def _plain(value, limit):
    """One bounded line of untrusted text: printable characters only, secret-like text removed."""
    if not isinstance(value, str):
        return ''
    text = re.sub(r'[^\x20-\x7e\u00a0-\u024f\u2010-\u2027\u2190-\u21ff]+', ' ', value)[:limit].strip()
    return '[redacted]' if any(pattern.search(text) for pattern in SECRET_PATTERNS) else text


def correction_feedback(receipt):
    """What stopped a failed attempt, as data lines for the next author.

    Reviewer reasons and agent notes are model output. Check names come from the gate or from
    the required CI result (name and conclusion only, never a log). A known check also adds one
    fixed supervisor repair sentence. Agent text is not an instruction.
    """
    lines = []
    publisher = receipt.get('publisher') if isinstance(receipt.get('publisher'), dict) else {}
    if publisher.get('reason') == 'ci_failed':
        checks = []
        for item in (publisher.get('failed_checks') or [])[:8]:
            if not isinstance(item, dict) or item.get('conclusion') == 'success':
                continue
            name = _plain(item.get('name'), 80)
            conclusion = item.get('conclusion') if isinstance(item.get('conclusion'), str) else 'failed'
            conclusion = _plain(conclusion, 32) or 'failed'
            if name:
                checks.append(name + ' (' + conclusion + ')')
                repair = CI_REPAIRS.get(name)
                if repair and repair not in lines:
                    lines.append('Supervisor: ' + repair)
        lines.insert(0, 'Required CI failed' + (': ' + '; '.join(checks) if checks else '')
                     + '. The pull request was not merged.')
    for vote in ((receipt.get('circuit') or {}).get('votes') or [])[:4]:
        if isinstance(vote, dict) and vote.get('verdict') in ('approve', 'reject'):
            reason = _plain(vote.get('reason'), 120)
            if reason:
                lines.append(('A reviewer rejected it: ' if vote['verdict'] == 'reject'
                              else 'A reviewer approved it, noting: ') + reason)
    gate = receipt.get('gate') or {}
    if gate.get('status') == 'failed':
        for name, result in sorted((gate.get('results') or {}).items()):
            if not isinstance(result, dict) or result.get('status') != 'failed':
                continue
            detail = result.get('detail') if isinstance(result.get('detail'), dict) else {}
            lines.append('Protected check ' + _plain(name, 40) + ' failed: '
                         + (_plain(detail.get('reason'), 96) or 'check_failed'))
            tests = [_plain(t, 160) for t in (detail.get('failed_tests') or [])[:8]]
            if any(tests):
                lines.append('Failing tests: ' + '; '.join(t for t in tests if t))
    elif (receipt.get('gate') or {}).get('status') != 'passed' and isinstance((receipt.get('execution') or {}).get('check'), dict) and (receipt.get('execution') or {}).get('check', {}).get('status') == 'failed':
        check = receipt['execution']['check']
        named = '; '.join(t for t in (_plain(x, 160) for x in (check.get('failed_tests') or [])[:8]) if t)
        if _plain(check.get('reason'), 96) or named:
            lines.append('Protected check failed: ' + (_plain(check.get('reason'), 96) or 'check_failed') + (('; ' + named) if named else ''))
    feedback = receipt.get('feedback') if isinstance(receipt.get('feedback'), dict) else {}
    author = _plain(feedback.get('author'), 200)
    if author:
        lines.append('Untrusted author note: ' + author)
    for note in (feedback.get('reviewers') or [])[:3]:
        if not isinstance(note, dict):
            continue
        text = _plain(note.get('text'), 200)
        who = _plain(note.get('model'), 40) or 'reviewer'
        if text:
            lines.append('Untrusted note from ' + who + ': ' + text)
    return lines[:12]


def _isolation_unqualified(result):
    """A lost check boundary is a hold, never a failed build: the candidate never ran.

    ``ProtectedChecks`` nests whatever a check returned under ``detail``; older receipts
    carried the reason at the top level, so both shapes are read.
    """
    detail = result.get("detail")
    return ((isinstance(detail, dict) and detail.get("reason") == "isolation_unqualified")
            or result.get("reason") == "isolation_unqualified")


class DispatchWorker:
    def __init__(self, store, catalog, spec_dir, work_root, config=None,
                 checks=None, required_checks=None, forge=None, target_repo=None,
                 trusted_issuer="gate", review_complete=None, author_model="deepseek-4.1-flash",
                 require_circuit=None, defer_to=None, gateway=None, agent_id=None,
                 target=None, builder=None, telemetry=None, budget=None,
                 budget_scope="aeion-autonomous-forum", allow_unbudgeted=False,
                 startup_hold=None, check_sandbox=None, targets=None, preparer=None):
        self.store = store
        self.catalog = catalog
        self.spec_dir = Path(spec_dir)
        self.work_root = Path(work_root)
        self.config = config or {}
        self.target = target
        self.targets = dict(targets) if targets is not None else None
        self.correction = None
        self.review_feedback = []
        self.check_sandbox = check_sandbox
        self.explicit_checks = checks is not None
        self.explicit_required_checks = required_checks is not None
        self.builder = builder
        self.telemetry = telemetry
        self.budget = budget
        self.budget_scope = budget_scope
        self.allow_unbudgeted = bool(allow_unbudgeted)
        self.startup_hold = startup_hold
        self.admission_check = None
        self.connectivity = None
        self._network_checked = False
        self._network_ok = None
        self.paid = bool(getattr(builder, "paid", False))
        self.last_usage = None
        if checks is not None:
            self.checks = checks
        else:
            registered = dict(DEFAULT_CHECKS)
            if target is not None:
                registered[target.protected_check.id] = target_check(
                    target, work_root=self.work_root, sandbox=check_sandbox)
            self.checks = ProtectedChecks(registered)
        if required_checks is not None:
            self.required_checks = list(required_checks)
        else:
            self.required_checks = list(DEFAULT_REQUIRED_CHECKS)
            if target is not None and target.protected_check.id not in self.required_checks:
                self.required_checks.append(target.protected_check.id)
        self.forge = forge if forge is not None else FakeForge()
        self.target_repo = target_repo or (target.target_repo if target is not None
                                           else DEFAULT_TARGET_REPO)
        self.trusted_issuer = trusted_issuer
        self.review_complete = review_complete
        self.author_model = author_model
        self.router = Router(Telemetry())
        self.progress = None
        self.publication = None
        self.preparer = preparer
        self.preparation_evidence = None
        self.author_routing = None
        self.author_ms = None
        self.started_build_ns = None
        self.review_context = None
        self.reused_execution = None
        # A real forge is only reachable once two independent models have approved the diff.
        self.defer_to = defer_to
        # No agent holds a GitHub key: when a gateway is configured, every attempt gets its own
        # short-lived session, recorded in the receipt and revoked when the attempt ends.
        self.gateway = gateway
        self.agent_id = agent_id
        self.require_circuit = (self.paid or bool(defer_to) or isinstance(self.forge, GitHubForge)
                                if require_circuit is None else bool(require_circuit))

    def _make_repo(self, build_id):
        repo = self.work_root / build_id / "repo"
        (repo / "demo/forum/product").mkdir(parents=True, exist_ok=True)
        (repo / "demo/forum/product/.keep").write_text("")
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "builder@fake.local"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "fake-builder"], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "base"], check=True)
        base_sha = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        return repo, base_sha

    def _write_simulated_impl(self, repo, frozen, feature):
        """Write the fake builder's output inside its first declared write scope."""
        scope = frozen.write_scopes[0]
        if scope.endswith("/"):
            target = repo / scope / f"{feature['id']}-impl.md"
        else:
            target = repo / scope
        target.parent.mkdir(parents=True, exist_ok=True)
        # A heading that names the feature: the product contract checks it again, independently.
        target.write_text(
            f"# Feature {feature['id']} — {feature['title']}\n\n"
            f"Simulated implementation for the S3 gate; not product code.\n"
        )

    @staticmethod
    def _content_bound(files, verdict):
        """The bytes about to be reviewed and published must be the bytes the gate hashed."""
        return isinstance(files, dict) and content_digest(files) == verdict.get("digest")

    def _feedback(self, build, preparation_execution):
        """Owner-facing agent notes. A later correction may copy a short redacted excerpt as data."""
        author = getattr(self.builder, 'last_feedback', None)
        execution = getattr(self.builder, 'last_execution', None)
        preparer = getattr(getattr(self.preparer, 'role', None), 'last_feedback', None)
        notes = {'author': _plain(author, 800) if isinstance(execution, dict)
                 and execution.get('build_id') == build['build_id'] else None,
                 'preparer': _plain(preparer, 800) if preparation_execution else None,
                 'reviewers': list(getattr(self, 'review_feedback', []))}
        return {key: value for key, value in notes.items() if value} or None

    def _identity(self, build, feature, frozen, base_sha, verdict):
        """The four ids every receipt carries, so a board row reaches its trace and artifact."""
        execution = self.reused_execution or getattr(self.builder, 'last_execution', None)
        if not isinstance(execution, dict) or execution.get('build_id') != build['build_id']:
            execution = None
        preparation_execution = getattr(getattr(self.preparer,'role',None),'last_execution',None)
        if not isinstance(preparation_execution,dict) or preparation_execution.get('build_id') != build['build_id']:
            preparation_execution = None
        return {
            "simulated": not self.paid,
            "author_model": self.author_model if self.paid else None,
            "build_id": build["build_id"],
            "feature_id": feature["id"],
            "attempt_id": build["attempt_id"],
            "frozen_digest": frozen.digest(),
            "contract_digest": frozen.contract_digest,
            "spec_digest": frozen.spec_digest,
            "acceptance_digest": frozen.acceptance_digest,
            "dependency_changes": frozen.dependency_changes,
            "preparation": self.preparation_evidence,
            "preparation_execution": preparation_execution,
            "feedback": self._feedback(build, preparation_execution),
            "base_sha": base_sha,
            "artifact_digest": verdict.get("digest"),
            "routing": self.author_routing,
            "execution": execution,
            **({'review_context':self.review_context} if self.review_context else {}),
        }

    def _progress(self, build, phase, detail=None):
        if self.store.record_progress(build['attempt_id'], build['attempt_generation'], phase, detail or {}):
            if self.progress:
                self.progress(build['build_id'], phase)

    def _attempt_authorized(self, build):
        if self.admission_check is not None:
            try:
                if self.admission_check() is not True:return False
            except Exception:return False
        return self.catalog.matches_contract(build) and self.store.attempt_authorized(
            build['attempt_id'],build['attempt_generation'])

    def _record_author(self, build):
        """Quality here means the bound artifact checks/reviews, not deployment success."""
        if not self.paid or getattr(self.builder, 'engine', None) != 'flue-pi':
            return
        execution = getattr(self.builder, 'last_execution', None)
        if (not isinstance(execution, dict) or execution.get('build_id') != build['build_id']
                or not execution.get('forwarded_count')):
            return  # A local preflight/budget error is not an observed model outcome.
        row = self.store.by_attempt(build['attempt_id'])
        receipt = json.loads(row['receipt']) if row and row.get('receipt') else {}
        if ((receipt.get('gate') or {}).get('status') == 'passed'
                and (receipt.get('review') or {}).get('status') == 'approved'
                and (receipt.get('circuit') or {}).get('status') == 'approved'):
            outcome = 'passed'
        elif (row and row['status'] == FAILED) or (receipt.get('circuit') or {}).get('reason') == 'reviewer_rejected':
            outcome = 'failed'
        else:
            outcome = 'unknown'
        measurement = self.last_usage or {}
        cost = measurement.get('cost_usd') if measurement.get('complete') is True else None
        self.router.telemetry.record(self.author_model, 'author', outcome,
                                     latency_ms=self.author_ms, cost_usd=cost)

    def _telemetry_evidence(self, build, feature, frozen, base_sha, verdict, gate, decision):
        """Best-effort trace evidence; a telemetry failure never rewrites a build outcome."""
        if self.telemetry is None:
            return {"status": "disabled"}
        try:
            execution=self.reused_execution or getattr(self.builder,'last_execution',None) or {}
            if execution.get('build_id')!=build['build_id']:execution={}
            diagnostic={**execution,'failure_code':execution.get('failure'),
                'execution_trace_id':execution.get('trace_id'),'phase':'building' if (gate or {}).get('status')=='builder_error' else 'checking'}
            for result in ((gate or {}).get('results') or {}).values():
                if isinstance(result,dict) and isinstance(result.get('detail'),dict):
                    diagnostic['check']={'status':result.get('status'),'reason':result['detail'].get('reason')}
                    if result.get('status')=='failed':break
            if execution.get('failure')=='CLI_STARTUP_FAILED':diagnostic['phase']='startup'
            evidence = self.telemetry.emit(
                build_id=build["build_id"], feature_id=feature["id"],
                attempt_id=build["attempt_id"], artifact_digest=verdict.get("digest"),
                base_sha=base_sha, gate_status=(gate or {}).get("status"),
                publisher_decision=(decision or {}).get("decision"), synthetic=not self.paid,
                duration_ms=max(0,(time.time_ns()-self.started_build_ns)//1000000) if self.started_build_ns else None,
                diagnostics=diagnostic,
            )
        except Exception as exc:  # noqa: BLE001 - observability is not a gate
            return {"status": "unavailable", "reason": type(exc).__name__}
        if not isinstance(evidence, dict):
            return {"status": "unavailable", "reason": "invalid_evidence"}
        return evidence

    def _budget_estimate(self):
        """The most this attempt may spend, from the frozen run config; invalid means no."""
        raw = self.config.get("cost_reservation_usd", "0.00")
        try:
            estimate = Decimal(str(raw))
        except (InvalidOperation, ValueError):
            raise BudgetError("invalid_estimate") from None
        if not estimate.is_finite() or estimate < 0:
            raise BudgetError("invalid_estimate")
        return estimate

    def _reserve(self, build):
        """Journal the attempt's spending cap before any model or tool can spend."""
        if self.budget is None:
            if self.allow_unbudgeted:
                return None
            # No purse means no paid work; a fake-only caller must opt in explicitly.
            raise BudgetError("budget_unavailable")
        return self.budget.admit(
            self.budget_scope, self._budget_estimate(),
            note=f"{build['build_id']}:{build['feature_id']}",
        )

    def _settle(self, reservation, build=None):
        if reservation is None or self.budget is None:
            return
        usage = self.last_usage
        if isinstance(usage, dict) and usage.get("complete") is True and usage.get("cost_usd") is not None:
            try:
                self.budget.settle(reservation, Decimal(str(usage["cost_usd"])))
            except (BudgetError, InvalidOperation, ValueError):
                return
            return
        if build is not None and self._author_never_forwarded(build):
            try:
                self.budget.settle(reservation, Decimal("0"))
            except (BudgetError, InvalidOperation, ValueError):
                return

    def _author_never_forwarded(self, build):
        execution = getattr(self.builder, "last_execution", None) if self.builder is not None else None
        if getattr(self, "_author_started", False):
            if not isinstance(execution, dict) or execution.get("build_id") != build.get("build_id"):
                return False
            count = execution.get("forwarded_count")
            return not (type(count) is int and count > 0)
        if isinstance(execution, dict) and execution.get("build_id") == build.get("build_id"):
            count = execution.get("forwarded_count")
            return not (type(count) is int and count > 0)
        return True

    def _review_never_forwarded(self):
        reviewer = self.review_complete
        if reviewer is None or not hasattr(reviewer, "last_execution"):
            return False
        execution = reviewer.last_execution
        if not isinstance(execution, dict):
            return True
        count = execution.get("forwarded_count")
        return not (type(count) is int and count > 0)

    def run_once(self):
        """Claim one build, give its agent a session, run it, and end the session whatever happens."""
        assert_worker_isolated()
        # A required CI failure is already durable. Continue it before polling the forge again,
        # including a hold recorded by an older controller that only knew how to stop.
        continued = self._continue_held_ci()
        if continued is not None:
            return continued
        retried = self._continue_held_review()
        if retried is not None:
            return retried
        if self.publication is not None:
            publication = self.publication.run_once()
            if publication is not None:
                return publication
        self.last_usage = None
        self._author_started = False
        self.review_context = self.reused_execution = None
        self._network_checked = False
        self._network_ok = None
        if self.paid and self.connectivity is not None and self._provider_needed():
            self._network_ok = self._probe_provider()
            self._network_checked = True
            if self._network_ok:
                self._release_network_holds()
            elif self._held_for_network():
                # Already explaining the outage. Do not claim another author.
                return None
        if self.paid and getattr(self, 'security_fresh', None) is not None:
            if not any(row.get('status') == 'dispatched' for row in self.store.board()):
                try:
                    proof_fresh = self.security_fresh() is True
                except Exception:  # noqa: BLE001 - an unreadable proof is not a sandbox open
                    proof_fresh = False
                if proof_fresh:
                    self._release_security_holds()
                elif self._held_for_security():
                    # Already explaining the stale proof. Do not claim another author.
                    return None
        # Cover the longest admitted check, one author call, two votes and teardown.
        # Expiry is recovery from an interrupted process, not an ordinary slow check.
        targets = list((self.targets or {}).values()) or ([self.target] if self.target else [])
        check_seconds = max((t.protected_check.timeout_seconds for t in targets), default=0)
        # Live Flue roles declare their own transport window; fixtures have no remote wait.
        author_seconds = getattr(self.builder, 'timeout_seconds', 0)
        review_seconds = getattr(self.review_complete, 'timeout_seconds', 0)
        preparation_seconds = getattr(self.preparer,'timeout_seconds',0)
        if self.preparer is not None:check_seconds=max(check_seconds,900)
        # Two votes plus the bounded substitute for a busy reviewer (review_circuit.MAX_SUBSTITUTIONS).
        lease_ns = (preparation_seconds + check_seconds + author_seconds
                    + (2 + MAX_SUBSTITUTIONS) * review_seconds + 60) * 1_000_000_000
        build = self.store.claim_next(self.catalog, lease_ns=lease_ns)
        if build is None:
            return None
        self.started_build_ns = time.time_ns()
        self.review_feedback = []
        self.author_routing, self.author_ms = None, None
        self.preparation_evidence = None
        self.correction = None
        for role in (self.builder, self.review_complete):
            if role is not None and hasattr(role, 'authorization_check'):
                role.authorization_check = lambda: self._attempt_authorized(build)
        feature = self.catalog.by_id[build['feature_id']]
        selected_target = (self.targets or {}).get(feature['id']) or self.target
        cohort = cohort_for(feature, selected_target.protected_check.id if selected_target else
                            'prepared_product' if getattr(self.preparer,'product',False) else
                            'prepared_gradle' if self.preparer is not None else 'fixture',
            execution_bounds={key:value for key,value in {
                'step_cap':self.config.get('step_cap'),'deadline_ns':self.config.get('deadline_ns'),
                'context_limit':self.config.get('context_limit'),
                'author_output_tokens':getattr(self.builder,'max_output_tokens',None),
                'author_seconds':author_seconds,'review_seconds':review_seconds,
                'preparation_seconds':preparation_seconds}.items() if type(value) is int or value is None}
                | {'cost_reservation_usd':str(self.config.get('cost_reservation_usd','unknown'))})
        self.router = Router(OutcomeTelemetry(self.store, cohort, build['attempt_id'],
            synthetic=not (self.paid and getattr(self.builder, 'engine', None) == 'flue-pi')))
        if self.startup_hold:
            # The configured execution is unavailable (or unknown): hold before any spend.
            self.store.hold_dispatched(build["build_id"], self.startup_hold)
            return {"build_id": build["build_id"],
                    "result": {"status": "held", "reason": self.startup_hold}}
        if self.targets is not None and build['feature_id'] not in self.targets and self.preparer is None:
            self.store.hold_dispatched(build['build_id'], 'target_unavailable')
            return {'build_id': build['build_id'],
                    'result': {'status': 'held', 'reason': 'target_unavailable'}}
        if not self._security_ready(build):
            return {'build_id': build['build_id'],
                    'result': {'status': 'held', 'reason': 'sandbox_qualification_stale'}}
        if self.paid and self._network_checked and not self._network_ok:
            self.store.hold_dispatched(build['build_id'], 'network_unavailable')
            return {'build_id': build['build_id'],
                    'result': {'status': 'held', 'reason': 'network_unavailable'}}
        prepared_target = None
        if self.preparer is not None:
            self._progress(build,'preparing')
            self.preparer.role.progress = lambda phase, detail=None: self._progress(build,phase,detail)
            started=time.monotonic()
            try:
                loaded = None
                if self._keeps_resume_clone(build):
                    try:
                        loaded = self.preparer.resume_prepared(self.work_root / build['build_id'] / 'prepared')
                    except PreparationError:
                        loaded = None
                if loaded is None:
                    try:
                        replace_own_directory(self.work_root, build['build_id'], 'prepared')
                    except (ValueError, OSError):
                        raise PreparationError('preparation_workspace_refused') from None
                    loaded = self.preparer.prepare(
                        build=build,catalog=self.catalog,spec_dir=self.spec_dir,
                        destination=self.work_root / build['build_id'] / 'prepared',budget=self.budget,
                        router=self.router,authorized=lambda:self._attempt_authorized(build))
                prepared_target,self.preparation_evidence=loaded
                if not self.store.record_preparation(build['attempt_id'],build['attempt_generation'],self.preparation_evidence):
                    return {'build_id':build['build_id'],'result':{'status':'stale_attempt'}}
            except (PreparationError,TargetError,BudgetError) as error:
                self.store.hold_dispatched(build['build_id'],'preparation_unavailable',receipt={
                    'build_id':build['build_id'],'attempt_id':build['attempt_id'],
                    'reason':str(error) if isinstance(error,PreparationError) else 'preparation_infrastructure_unavailable',
                    'preparation_execution':getattr(self.preparer.role,'last_execution',None)})
                return {'build_id':build['build_id'],'result':{'status':'held','reason':'preparation_unavailable'}}
            except Exception as error:
                self.store.hold_dispatched(build['build_id'],'preparation_unavailable',receipt={
                    'build_id':build['build_id'],'attempt_id':build['attempt_id'],
                    'reason':'preparation_failed','error_type':type(error).__name__,
                    'preparation_execution':getattr(self.preparer.role,'last_execution',None)})
                return {'build_id':build['build_id'],'result':{'status':'held','reason':'preparation_unavailable'}}
            finally:
                role=self.preparer.role
                execution=getattr(role,'last_execution',None) or {}
                if getattr(role,'paid',False) and execution.get('forwarded_count') and self.preparer.last_model:
                    measured=getattr(role,'last_usage',None) or {}
                    self.router.telemetry.record(self.preparer.last_model,'prepare',
                        'passed' if self.preparation_evidence is not None else
                        'error' if measured.get('complete') is True else 'unknown',
                        latency_ms=int((time.monotonic()-started)*1000),
                        cost_usd=measured.get('cost_usd') if measured.get('complete') is True else None)
            if hasattr(self.builder,'preparer_model'):
                self.builder.preparer_model=self.preparation_evidence['preparer_model']
        try:
            reservation = self._reserve(build)
        except BudgetError:
            self.store.hold_dispatched(build["build_id"], "budget_unavailable")
            return {"build_id": build["build_id"],
                    "result": {"status": "held", "reason": "budget_unavailable"}}
        try:
            try:
                session = self._open_session(build)
            except SessionError as error:
                return {"build_id": build["build_id"],
                        "result": {"status": "held", "reason": "credential_unavailable",
                                   "detail": str(error)}}
            try:
                return self._run(build, session, target_override=prepared_target)
            except Exception as error:
                # Persist an observable hold; never retry a possibly paid call blindly.
                self.store.hold_dispatched(build['build_id'], 'worker_error')
                return {'build_id': build['build_id'], 'result': {
                    'status': 'held', 'reason': 'worker_error', 'error_type': type(error).__name__}}
            finally:
                self._close_session(session)
        finally:
            try:
                self._record_author(build)
            finally:
                self._settle(reservation, build)

    def _open_session(self, build):
        """Mint the session this attempt may use; without a gateway there is nothing to mint."""
        if self.gateway is None:
            return None
        agent = self.agent_id or ("builder-" + build["attempt_id"][:8])
        try:
            return self.gateway.issue(agent_id=agent, build_id=build["build_id"],
                                      feature_id=build["feature_id"])
        except SessionError:
            self.store.hold_dispatched(build["build_id"], "credential_unavailable")
            raise

    def _close_session(self, session):
        """Revoke on the way out: a finished build keeps no usable credential."""
        if session is None or self.gateway is None:
            return
        try:
            self.gateway.revoke(session["token"], reason="build_finished")
        except SessionError:
            pass

    @staticmethod
    def session_evidence(session):
        """What a receipt may say about a session: its id, its window, its scope. Never the token."""
        if not session:
            return None
        return {"session": session["session"], "expires_ns": session["expires_ns"],
                "capabilities": list(session["capabilities"]), "repo": session["repo"]}

    def _take_builder_state(self):
        """Copy the paid builder's measured usage and model identity before any receipt.

        The author is refreshed even when the call failed, so an error receipt never
        attributes the attempt to the worker's default model.
        """
        if self.builder is None:
            return
        self.author_model = getattr(self.builder, "model", self.author_model)
        self.author_routing = getattr(self.builder, 'last_routing', None)
        if self.paid:
            self.last_usage = getattr(self.builder, "last_usage", None)

    def _review_vote(self, model, prompt):
        """Reserve before one review vote, then settle only that call's measured usage.

        Each vote is a separate paid action: reserving once per build would let two votes
        spend without a journal entry, and a failed vote must leave its own reservation open.
        """
        reservation = None
        if hasattr(self.review_complete, 'last_usage'):
            self.review_complete.last_usage = None
        if hasattr(self.review_complete, 'last_execution'):
            self.review_complete.last_execution = None
        if self.budget is not None:
            reservation = self.budget.admit(
                self.budget_scope, getattr(self.review_complete,'cost_limit','0.05'), note=f"review:{model}")
        # The wrapper owns this read: clear any earlier vote's usage before the call, so a
        # failure cannot settle the new reservation with stale cost.
        try:
            if hasattr(self.review_complete, 'last_feedback'):
                self.review_complete.last_feedback = None
            answer=self.review_complete(model, prompt)
            note = getattr(self.review_complete, 'last_feedback', None)
            if isinstance(note, str) and note:
                self.review_feedback = [*getattr(self, 'review_feedback', [])[:3],
                                        {'model': str(model)[:64], 'text': _plain(note, 800)}]
            if getattr(self.review_complete,'paid',False) or hasattr(self.review_complete,'last_usage'):
                measured=getattr(self.review_complete,'last_usage',None)
                try:
                    cost=Decimal(str(measured.get('cost_usd'))) if isinstance(measured,dict) else Decimal('NaN')
                    if (not isinstance(measured,dict) or measured.get('complete') is not True
                            or not cost.is_finite() or cost<0):
                        raise ValueError('USAGE_UNKNOWN')
                except (InvalidOperation,TypeError):raise ValueError('USAGE_UNKNOWN') from None
            return answer
        finally:
            usage = getattr(self.review_complete, "last_usage", None)
            if reservation is not None and isinstance(usage, dict) and usage.get("complete") is True and usage.get("cost_usd") is not None:
                try:
                    self.budget.settle(reservation, Decimal(str(usage["cost_usd"])))
                except (BudgetError, InvalidOperation, ValueError):
                    # Unknown or unreadable cost keeps the reservation counted.
                    pass
            elif reservation is not None and self._review_never_forwarded():
                try:
                    self.budget.settle(reservation, Decimal("0"))
                except (BudgetError, InvalidOperation, ValueError):
                    pass

    def _zero_transport_proven(self):
        """Only a build with no paid builder and no model review can prove zero spend."""
        return not self.paid and self.review_complete is None

    def reassess_review_context(self,build_id,retry_failed_review=False):
        """Explicit operator repair for the old full-files-only review envelope.

        No author is rerun or charged twice. A stale base, changed artifact/contract, unknown
        usage, prior publication or second request refuses the repair. Genuine v2 rejections
        require a worker correction, not repeated votes on the same proposal.
        """
        from dataclasses import replace
        from .preparation import freeze_task, _read
        from .product_checks import prepared_target
        from .target import _git
        assert_worker_isolated()
        if (not self.paid or self.preparer is None or not self.preparer.product
                or self.review_complete is None or self.admission_check is None
                or self.admission_check() is not True):
            raise CircuitError('review_context_execution_unavailable')
        row=next((r for r in self.store.board() if r['build_id']==build_id),None)
        if row is None or not row.get('receipt'):
            raise CircuitError('review_context_receipt_missing')
        prior=json.loads(row['receipt']);preparation=prior.get('preparation') or {}
        if preparation.get('synthetic') is not False or not self.catalog.matches_contract(row):
            raise CircuitError('review_context_contract_changed')
        base=self.preparer.synchronize() if self.preparer.synchronize else None
        if base!=prior.get('base_sha'):
            raise CircuitError('review_context_base_changed')
        task=freeze_task(self.catalog,row['feature_id'],self.spec_dir,
            self.preparer.root/'demo/forum/ARCHITECTURE.md',base,product=True)
        task=replace(task,catalog_digest=row['catalog_digest'])
        if task.digest()!=preparation.get('task_digest'):
            raise CircuitError('review_context_task_changed')
        repo=self.work_root/build_id/'repo'
        head=_git(['-C',str(repo),'rev-parse','HEAD'])
        if head.returncode or head.stdout.strip()!=base:
            raise CircuitError('review_context_checkout_changed')
        acceptance=_read(repo.parent/'prepared/acceptance.mjs',48000)
        folder=Path(tempfile.mkdtemp(prefix='review-context-',dir=repo.parent))
        target=prepared_target(self.preparer.root,self.preparer.source,task,folder,acceptance)
        frozen=freeze_build(row,self.catalog,self.spec_dir,base,
            {**self.config,**({'dependency_changes':dict(target.dependency_changes)} if target.dependency_changes else {})},
            write_scopes=target.write_paths,spec_path=target.brief,acceptance_path=target.protected_check.contract_test)
        artifact=validate_artifact(repo,frozen.write_scopes)
        if (frozen.digest()!=prior.get('frozen_digest') or not artifact['accepted']
                or artifact.get('digest')!=prior.get('artifact_digest')
                or hashlib.sha256(acceptance.encode()).hexdigest()!=preparation.get('acceptance_digest')
                or _read(repo.parent/'BRIEF.md',12000)!=task.specification):
            raise CircuitError('review_context_artifact_changed')
        previous_votes=(prior.get('circuit') or {}).get('votes') or []
        rejecting=next((v.get('model') for v in previous_votes
            if v.get('verdict')==('error' if retry_failed_review else 'reject')),None)
        if rejecting is None:raise CircuitError('review_context_not_eligible')
        lease_ns=(target.protected_check.timeout_seconds
            +(2+MAX_SUBSTITUTIONS)*getattr(self.review_complete,'timeout_seconds',900)+60)*10**9
        build=self.store.claim_review_context(build_id,self.catalog,
            hashlib.sha256(row['receipt'].encode()).hexdigest(),lease_ns,retry_failed_review=retry_failed_review)
        if build is None:raise CircuitError('review_context_not_eligible')
        self.review_context=json.loads(build['receipt'])['review_context']
        self.correction=None
        self.reused_execution=prior['execution']
        self.author_model=prior['author_model'];self.author_routing=prior.get('routing')
        self.preparation_evidence=preparation;self.last_usage=None
        self.started_build_ns=time.time_ns()
        self.review_feedback=[]
        self.router=Router(OutcomeTelemetry(self.store,cohort_for(self.catalog.by_id[build['feature_id']],
            target.protected_check.id),build['attempt_id'],synthetic=False,generation=build['attempt_generation']))
        self.review_complete.authorization_check=lambda:self._attempt_authorized(build)
        registered=dict(DEFAULT_CHECKS)
        registered[target.protected_check.id]=target_check(target,work_root=self.work_root,sandbox=self.check_sandbox)
        try:
            return self._judge_and_publish(build,None,repo,frozen,self.catalog.by_id[build['feature_id']],
                target,base,ProtectedChecks(registered),[*DEFAULT_REQUIRED_CHECKS,target.protected_check.id],
                first_reviewer=rejecting)
        except Exception as error:
            self.store.hold_dispatched(build_id,'worker_error')
            return {'build_id':build_id,'result':{'status':'held','reason':'worker_error','error_type':type(error).__name__}}

    def _provider_needed(self):
        for build in self.store.board():
            if build.get('status') == 'queued':
                return True
            if build.get('status') == 'held' and build.get('hold_reason') == 'network_unavailable':
                return True
        return False

    def _held_for_network(self):
        return any(build.get('status') == 'held' and build.get('hold_reason') == 'network_unavailable'
                   for build in self.store.board())

    def _probe_provider(self):
        try:
            return self.connectivity.reachable() is True
        except Exception:  # noqa: BLE001 - an unreadable probe is a down provider, never a model call
            return False

    def _release_network_holds(self):
        for build in self.store.board():
            if build.get('status') == 'held' and build.get('hold_reason') == 'network_unavailable':
                self.store.release_network_hold(build['build_id'])

    def _held_for_security(self):
        return any(build.get('status') == 'held' and build.get('hold_reason') == 'sandbox_qualification_stale'
                   for build in self.store.board())

    def _release_security_holds(self):
        for build in self.store.board():
            if build.get('status') == 'held' and build.get('hold_reason') == 'sandbox_qualification_stale':
                self.store.release_qualification_hold(build['build_id'])

    def _security_ready(self, build):
        """A paid controller refreshes the OpenShell proof before preparation spends."""
        check = getattr(self, 'security_fresh', None)
        if not self.paid or check is None:
            return True
        try:
            fresh = check() is True
        except Exception:  # noqa: BLE001 - a probe that raises is a stale proof, never an author
            fresh = False
        if fresh:
            return True
        self.store.hold_dispatched(build['build_id'], 'sandbox_qualification_stale')
        return False

    def _network_ready(self, build):
        """A paid controller with a probe must reach the provider twice before any model call."""
        if not self.paid or self.connectivity is None:
            return True
        if not self._network_checked:
            self._network_ok = self._probe_provider()
            self._network_checked = True
        if self._network_ok:
            return True
        self.store.hold_dispatched(build['build_id'], 'network_unavailable')
        return False

    def _reap_ghosts(self):
        if self.connectivity is None:
            return
        try:
            self.connectivity.reap(self.store.path)
        except Exception:  # noqa: BLE001 - a reap failure must not lose the queued resume
            return

    def _run(self, build, session, target_override=None):
        feature = self.catalog.by_id[build["feature_id"]]
        if not self._network_ready(build):
            return {'build_id': build['build_id'],
                    'result': {'status': 'held', 'reason': 'network_unavailable'}}
        progress = lambda phase, detail=None: self._progress(build, phase, detail)
        target = target_override or (self.targets.get(feature["id"]) if self.targets is not None else self.target)
        target_repo = target.target_repo if target is not None else self.target_repo
        checks, required_checks = self.checks, self.required_checks
        if (self.targets is not None or target_override is not None) and target is not None:
            if not self.explicit_checks:
                registered = dict(DEFAULT_CHECKS)
                registered[target.protected_check.id] = target_check(
                    target, work_root=self.work_root, sandbox=self.check_sandbox)
                checks = ProtectedChecks(registered)
            if not self.explicit_required_checks:
                required_checks = [*DEFAULT_REQUIRED_CHECKS, target.protected_check.id]
        if target is not None and feature["id"] != target.feature_id:
            # A pinned profile belongs to one feature; it must never freeze another one.
            self.store.hold_dispatched(build["build_id"], "target_feature_mismatch")
            return {"build_id": build["build_id"],
                    "result": {"status": "held", "reason": "target_feature_mismatch"}}
        try:
            if target is None:
                repo, base_sha = self._make_repo(build["build_id"])
            else:
                repo = self.work_root / build["build_id"] / "repo"
                if self._keeps_resume_clone(build):
                    base_sha = target.base_sha
                else:
                    try:
                        replace_own_directory(self.work_root, build['build_id'], 'repo')
                    except (ValueError, OSError) as exc:
                        raise TargetError('workspace_refused') from exc
                    base_sha = target.materialize(repo)
            frozen = freeze_build(
                build, self.catalog, self.spec_dir, base_sha,
                {**self.config, **({'dependency_changes':dict(target.dependency_changes)}
                    if target is not None and target.dependency_changes else {})},
                write_scopes=target.write_paths if target is not None else None,
                spec_path=target.brief if target is not None else None,
                acceptance_path=target.protected_check.contract_test if target is not None else None,
            )
        except TargetError as exc:
            self.store.hold_dispatched(build["build_id"], "base_unavailable")
            return {"build_id": build["build_id"],
                    "result": {"status": "held", "reason": "base_unavailable",
                               "detail": str(exc)}}
        except FreezeError as exc:
            self.store.hold_dispatched(build["build_id"], "qualification_missing")
            return {"build_id": build["build_id"], "result": {"status": "held", "reason": str(exc)}}

        # The build brief lives outside the clone: the agent reads where it stops, the artifact
        # validator never sees it, and the branch it names is the one the publisher will push.
        branch = f"aeion/build-{build['attempt_id'][:24]}"
        brief = stop.build_brief(feature["id"], feature["title"], branch)
        spec_source = target.brief if target is not None else self.spec_dir / feature['file']
        (repo.parent / 'BRIEF.md').write_bytes(spec_source.read_bytes())
        if target is not None:
            (repo.parent / "CONTEXT.md").write_text(target.source_context(), encoding='utf-8')
            brief += ("\nSpecification: BRIEF.md, outside the repository and read-only.\n"
                      "Write scopes: " + ", ".join(target.write_paths) + ".\n")
        (repo.parent / "TASK.md").write_text(brief + "\n")
        # A configured review circuit may make paid calls even when the builder is fake. Only
        # a path with neither a paid builder nor any model review can prove zero transport.
        self.last_usage = ({"cost_usd": "0", "complete": True, "basis": "no_paid_transport"}
                           if self._zero_transport_proven() else None)
        started_author = time.monotonic()
        try:
            progress('building')
            if self.builder is None:
                self._write_simulated_impl(repo, frozen, feature)
            else:
                self._author_started = True
                if hasattr(self.builder, 'run_build'):
                    self.correction = (self._resume_correction(build, frozen, repo)
                                       or self._correction_input(build, frozen))
                    previous = (None if self.correction is not None
                                else self.store.previous_check_failure(feature['id'], frozen.spec_digest))
                    self.builder.run_build(repo=repo, frozen=frozen, feature=feature,
                        brief=repo.parent / 'BRIEF.md', target=target, build=build,
                        progress=progress, router=self.router, previous_failure=previous,
                        **({'correction': self.correction} if self.correction is not None else {}))
                else:
                    self.builder(repo=repo, frozen=frozen, feature=feature,
                                 brief=repo.parent / "BRIEF.md")
                self._take_builder_state()
        except Exception as exc:  # noqa: BLE001 - a failed builder never publishes
            self._take_builder_state()
            execution = getattr(self.builder, 'last_execution', None) or {}
            stop_code = _token(str(exc)) or type(exc).__name__
            receipt = {**self._identity(build,feature,frozen,base_sha,{}),
                 "reason": "builder_error", "detail": type(exc).__name__,
                 "error": execution.get('failure')
                    or (str(exc) if isinstance(exc, BuilderError) else type(exc).__name__),
                 "execution": execution if isinstance(execution, dict) else {},
                 "telemetry": self._telemetry_evidence(
                     build, feature, frozen, base_sha, {}, {"status": "builder_error"}, None)}
            if hasattr(self.builder, 'run_build') and stop_code in RETRYABLE_AUTHOR_STOPS:
                execution = execution if isinstance(execution, dict) else {}
                if same_model_resume(stop_code, execution, self.store.work_event_count(build['build_id'])):
                    resumed = self._resume_same_model(build, stop_code, execution)
                    if resumed is not None:
                        return resumed
                return self._fail_or_correct(build, feature, receipt, self._crash_candidate(repo, frozen),
                    'crash', crash={'failure': stop_code, 'error_class': _token(execution.get('error_class'))})
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"], receipt, terminal=FAILED)
            return {"build_id": build["build_id"], "result": result}
        finally:
            self.author_ms = int((time.monotonic() - started_author) * 1000)
        return self._judge_and_publish(build,session,repo,frozen,feature,target,base_sha,checks,required_checks)

    def _continue_held_ci(self):
        """Queue the next correction for one held build whose required CI failed, or None."""
        for build in self.store.board():
            if build.get('status') != HELD or build.get('hold_reason') != 'publication_blocked':
                continue
            receipt = self._receipt(build)
            marker = receipt.get('correction') if isinstance(receipt.get('correction'), dict) else {}
            publisher = receipt.get('publisher') if isinstance(receipt.get('publisher'), dict) else {}
            if publisher.get('reason') != 'ci_failed' or marker.get('trigger') == 'ci_failed':
                continue
            try:
                result = self.store.continue_after_ci_failure(
                    build['build_id'], self.catalog, self._reviewed_candidate(build, receipt))
            except StoreError:
                return {'build_id': build['build_id'], 'result': {'status': 'held', 'reason': 'ci_failed'}}
            if result.get('status') == 'unchanged':
                continue
            return {'build_id': build['build_id'], 'result': result}
        return None

    def _keeps_resume_clone(self, build):
        continued = self._receipt(build).get('continued')
        repo = self.work_root / build['build_id'] / 'repo'
        return (isinstance(continued, dict) and repo.is_dir() and not repo.is_symlink()
                and (repo / '.git').is_dir())

    def _continue_held_review(self):
        refused = getattr(self, '_review_retry_refused', None)
        if refused is None:
            refused = self._review_retry_refused = set()
        for build in self.store.board():
            if build.get('status') != HELD or build.get('hold_reason') != 'owner_review_required':
                continue
            build_id = build.get('build_id')
            if not isinstance(build_id, str) or build_id in refused:
                continue
            if not review_retry_eligible(self._receipt(build)):
                continue
            try:
                return self.reassess_review_context(build_id, retry_failed_review=True)
            except CircuitError:
                refused.add(build_id)
                return None
        return None

    def _reviewed_candidate(self, build, receipt):
        """The published bytes, restored into the candidate clone when the digest matches.

        The publication request is the reviewed artifact. The next round reads those same paths
        from this build's workspace, so a missing clone is rewritten with those bytes only.
        """
        request = self.store.publication_request(build.get('attempt_id')) or {}
        files = request.get('files')
        if not isinstance(files, dict) or not files:
            return {}
        try:
            if content_digest(files) != receipt.get('artifact_digest'):
                return {}
        except (TypeError, UnicodeEncodeError):
            return {}
        root = (self.work_root / build['build_id'] / 'repo').resolve()
        try:
            root.mkdir(parents=True, exist_ok=True)
            for name, text in files.items():
                if not isinstance(name, str) or not isinstance(text, str) or name.startswith('/') or '..' in name.split('/'):
                    return {}
                path = (root / name).resolve()
                if not path.is_relative_to(root) or path.is_symlink():
                    return {}
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding='utf-8')
        except OSError:
            return {}
        return files

    @staticmethod
    def _receipt(row):
        try:
            receipt = json.loads(row['receipt']) if row and row.get('receipt') else {}
        except ValueError:
            receipt = {}
        return receipt if isinstance(receipt, dict) else {}

    def _chain_models(self, build_id):
        """Author models of every earlier build in this owner launch, nearest first (bounded walk)."""
        models, current = [], build_id
        for _ in range(MAX_ATTEMPTS * (MAX_CORRECTION_ROUNDS + 1)):
            link = self.store.correction_of(current)
            previous = self.store.build(link['previous_build_id']) if link else None
            if previous is None:
                break
            model = self._receipt(previous).get('author_model')
            if isinstance(model, str) and model not in models:
                models.append(model)
            current = previous['build_id']
        return models

    def _resume_same_model(self, build, stop_code, execution):
        """Queue this same build again. None means the caller should use the crash path."""
        continued = {
            'failure': stop_code,
            'trigger': resume_trigger(stop_code),
            'error_class': _token(execution.get('error_class')),
            'cli_steps': execution.get('cli_steps') if type(execution.get('cli_steps')) is int else None,
            'model': self.author_model if isinstance(self.author_model, str) else None,
        }
        result = self.store.resume_interrupted(build['attempt_id'], build['attempt_generation'], continued)
        if result.get('status') == 'queued':
            self._reap_ghosts()
            return {'build_id': build['build_id'], 'result': result}
        if result.get('status') == 'remote':
            # Publication was already in flight. Do not start another model over an open effect.
            self.store.hold_dispatched(build['build_id'], 'reconciliation_needed')
            return {'build_id': build['build_id'],
                    'result': {'status': 'held', 'reason': 'reconciliation_needed'}}
        return None

    def _resume_correction(self, build, frozen, repo):
        """The prompt for a same-model resume: where it stopped, and the files already on disk."""
        continued = self._receipt(build).get('continued')
        if not isinstance(continued, dict):
            return None
        link = self.store.correction_of(build['build_id'])
        attempt, number = (link['attempt'], link['round']) if link else (1, 0)
        try:
            files = scoped_texts(repo, frozen.write_scopes)
        except Exception:  # noqa: BLE001 - an unreadable clone carries the note without bytes
            files = {}
        interruption = {'failure': _token(continued.get('failure')) or 'CLI_FAILED'}
        error_class = _token(continued.get('error_class'))
        if error_class:
            interruption['error_class'] = error_class
        if type(continued.get('cli_steps')) is int:
            interruption['cli_steps'] = continued['cli_steps']
        trigger = continued.get('trigger')
        model = continued.get('model') if isinstance(continued.get('model'), str) else None
        return {
            'resume': True,
            'attempt': attempt,
            'round': number,
            'trigger': trigger if trigger in ('cli_interrupted', 'network', 'lease_expired') else 'cli_interrupted',
            'feedback': correction_feedback(self._receipt(self.store.build(link['previous_build_id']))) if link else [],
            'files': files or None,
            'model': model or (self.author_model if isinstance(self.author_model, str) else None),
            'exclude_models': [],
            'interruption': interruption,
        }

    def _crash_candidate(self, repo, frozen):
        """The validated scoped files a crashed author left in the host clone, or {}."""
        try:
            verdict = validate_artifact(repo, frozen.write_scopes)
        except Exception:  # noqa: BLE001 - an unreadable clone carries nothing
            return {}
        files = verdict.pop('files', {})
        if not verdict.get('accepted') or not self._content_bound(files, verdict):
            return {}
        return files

    def _correction_input(self, build, frozen):
        """Feedback, model choice and the exact previous candidate for a continuation, or None.

        A correction round keeps the previous model; a new attempt excludes every model of this
        launch. The candidate is reused only when its bytes still match the digest its failed
        receipt recorded and the base is unchanged; otherwise the build starts from the base with
        the feedback alone. The candidate is untrusted either way: it is checked and reviewed again.
        """
        link = self.store.correction_of(build['build_id'])
        if link is None:
            return None
        previous = self.store.build(link['previous_build_id'])
        receipt = self._receipt(previous)
        marker = receipt.get('correction') if isinstance(receipt.get('correction'), dict) else {}
        marker_attempt = marker.get('attempt', 1)
        follows = (marker_attempt == link['attempt'] and marker.get('round') == link['round'] - 1
                   if link['round'] > 0 else marker_attempt == link['attempt'] - 1
                   and type(marker.get('round')) is int)
        crash = (marker.get('crash') if follows and marker.get('trigger') == 'crash'
                 and isinstance(marker.get('crash'), dict) else None)
        empty = {'attempt': link['attempt'], 'round': link['round'], 'feedback': [], 'files': None,
                 'candidate_digest': None, 'trigger': marker.get('trigger') if follows else None,
                 'crash': ({'failure': _token(crash.get('failure')), 'error_class': _token(crash.get('error_class'))}
                           if crash else None),
                 'model': (receipt.get('author_model') if link['round'] > 0
                           and isinstance(receipt.get('author_model'), str) else None),
                 'exclude_models': self._chain_models(build['build_id']) if link['round'] == 0 else []}
        if (previous is None or previous['status'] != FAILED or previous['feature_id'] != build['feature_id']
                or receipt.get('spec_digest') != frozen.spec_digest or not follows):
            return empty
        names, files = marker.get('candidate_files'), None
        if (receipt.get('base_sha') == frozen.base_sha and isinstance(names, list) and 0 < len(names) <= 200
                and all(isinstance(name, str) and '..' not in name.split('/') and not name.startswith('/')
                        and any(name.startswith(scope) for scope in frozen.write_scopes) for name in names)):
            source = self.work_root / previous['build_id'] / 'repo'
            try:
                loaded = {name: (source / name).read_text(encoding='utf-8') for name in names
                          if (source / name).is_file() and not (source / name).is_symlink()}
            except (OSError, UnicodeDecodeError):
                loaded = {}
            if len(loaded) == len(names) and content_digest(loaded) == marker.get('candidate_digest'):
                files = loaded
        return {**empty, 'feedback': correction_feedback(receipt), 'files': files,
                'candidate_digest': marker.get('candidate_digest') if files is not None else None}

    def _fail_or_correct(self, build, feature, receipt, files, trigger, crash=None):
        """Close a refused or crashed build as failed and queue its continuation while one remains.

        The receipt marker names this build's attempt and round, why it stopped and the exact
        candidate bytes, so the next build can only reuse what this receipt bound.
        """
        link = self.store.correction_of(build['build_id'])
        attempt, current = (link['attempt'], link['round']) if link else (1, 0)
        if link is not None and 'publisher' not in receipt:
            inherited = self._receipt(self.store.build(link['previous_build_id'])).get('publisher')
            if isinstance(inherited, dict) and inherited.get('reason') == 'ci_failed':
                receipt = {**receipt, 'publisher': {'status': inherited.get('status'), 'reason': 'ci_failed',
                                                    'failed_checks': inherited.get('failed_checks')}}
        step = next_step(attempt, current, crash=trigger == 'crash')
        receipt = {**receipt, 'correction': {'attempt': attempt, 'round': current, 'trigger': trigger,
                   'candidate_files': sorted(files), 'candidate_digest': content_digest(files) if files else None,
                   **({'crash': crash} if crash else {}), **({'exhausted': True} if step is None else {})}}
        result = self.store.complete_attempt(build['attempt_id'], build['attempt_generation'],
                                             receipt, terminal=FAILED)
        if result.get('status') != 'completed' or step is None:
            return {'build_id': build['build_id'], 'result': result}
        try:
            admitted = self.store.admit([feature['id']], 'factory-correction:' + build['build_id'],
                self.catalog, actor='supervisor',
                correction={'previous_build_id': build['build_id'], 'attempt': step[0], 'round': step[1]})
        except StoreError as error:
            admitted = {'status': 'refused', 'reason': str(error)}
        return {'build_id': build['build_id'], 'result': {**result, 'correction': {
            'attempt': step[0], 'round': step[1], **admitted}}}

    def _judge_and_publish(self,build,session,repo,frozen,feature,target,base_sha,checks,required_checks,
                           first_reviewer=None):
        """One shared gate/review/publication path for fresh work and the bounded context repair."""
        progress=lambda phase,detail=None:self._progress(build,phase,detail)
        target_repo=target.target_repo if target is not None else self.target_repo
        verdict = validate_artifact(repo, frozen.write_scopes)
        files = verdict.pop("files", {})
        if verdict["accepted"] and not self._content_bound(files, verdict):
            verdict = {**verdict, "accepted": False,
                       "rejected": [{"path": "*", "reason": "content_digest_mismatch"}]}
        if not verdict["accepted"]:
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"],
                {"simulated": not self.paid, "author_model": self.author_model if self.paid else None,
                 "build_id": build["build_id"], "feature_id": feature["id"],
                 "attempt_id": build["attempt_id"], "verdict": verdict}, terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}

        if (self.correction is not None and self.correction.get('candidate_digest')
                and self.correction.get('trigger') != 'crash'
                and content_digest(files) == self.correction['candidate_digest']):
            # No progress: the correction returned the refused candidate unchanged. Asking the
            # same checks and reviewers again would only spend; the owner decides.
            self.store.hold_dispatched(build['build_id'], 'owner_review_required', receipt={
                **self._identity(build, feature, frozen, base_sha, verdict), 'reason': 'correction_unchanged'})
            return {'build_id': build['build_id'], 'result': {'status': 'held', 'reason': 'correction_unchanged'}}

        # The builder faithfully reports the spec it read; the gate re-checks this
        # claim against the frozen spec digest (spec_unchanged).
        verdict["spec_digest"] = frozen.spec_digest
        # The protected check needs the tree, never the candidate's claim; it is not
        # persisted in the receipt and is dropped as soon as the gate has judged.
        verdict["repo"] = str(repo)

        # S3 gate: protected checks judged outside the candidate's control.
        progress('checking')
        gate = checks.verdict(required_checks, frozen, verdict)
        verdict.pop("repo", None)
        if any(_isolation_unqualified(result)
               for result in gate["results"].values()):
            self.store.hold_dispatched(build["build_id"], "sandbox_unqualified")
            return {"build_id": build["build_id"], "result": {
                "status": "held", "reason": "sandbox_unqualified", "gate": gate}}
        if gate["status"] == "qualification_missing":
            self.store.hold_dispatched(build["build_id"], "qualification_missing")
            return {"build_id": build["build_id"], "result": {"status": "held",
                    "reason": "qualification_missing", "gate": gate}}
        if gate["status"] == "failed":
            evidence = self._telemetry_evidence(
                build, feature, frozen, base_sha, verdict, gate, None)
            return self._fail_or_correct(build, feature,
                {**self._identity(build, feature, frozen, base_sha, verdict),
                 "gate": gate, "telemetry": evidence}, files, 'gate_failed')

        # Independent deterministic review: the publisher never sees an unreviewed diff.
        review_verdict = review(frozen, verdict, files)
        if review_verdict["status"] == "refused":
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"],
                {"simulated": not self.paid, "author_model": self.author_model if self.paid else None,
                 "build_id": build["build_id"], "feature_id": feature["id"],
                 "attempt_id": build["attempt_id"], "gate": gate,
                 "review": review_verdict}, terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}
        if review_verdict["status"] == "held":
            self.store.hold_dispatched(build["build_id"], "owner_review_required", receipt={
                **self._identity(build, feature, frozen, base_sha, verdict),
                'gate': gate, 'review': review_verdict})
            return {"build_id": build["build_id"], "result": {"status": "held",
                    "reason": "owner_review_required", "review": review_verdict}}

        # Two independent model votes from different families, never the author's.
        circuit = None
        if self.require_circuit:
            progress('reviewing')
            if hasattr(self.review_complete, 'build_id'):
                self.review_complete.build_id = build['build_id']
                self.review_complete.progress = progress
            if self.review_complete is None:
                self.store.hold_dispatched(build["build_id"], "owner_review_required")
                return {"build_id": build["build_id"], "result": {
                    "status": "held", "reason": "review_circuit_unconfigured"}}
            try:
                diff=baseline_diff(repo,frozen.base_sha,files)
            except CircuitError as error:
                self.store.hold_dispatched(build['build_id'],'owner_review_required',receipt={
                    **self._identity(build,feature,frozen,base_sha,verdict),'gate':gate,'review':review_verdict,
                    'reason':str(error),'circuit':{'status':'held','reason':str(error),'votes':[],
                        'review_input_version':2}})
                return {'build_id':build['build_id'],'result':{'status':'held','reason':str(error)}}
            circuit = two_vote_review(self.author_model, feature["id"], files,
                                      self.router, self._review_vote,
                                      usage_for_vote=lambda: getattr(self.review_complete, 'last_usage', None),
                                      execution_for_vote=lambda: getattr(self.review_complete,'last_execution',None),
                                      observed_for_vote=lambda: not getattr(self.review_complete, 'paid', False)
                                        or bool((getattr(self.review_complete, 'last_execution', None) or {}).get('forwarded_count')),
                                      specification=(repo.parent / 'BRIEF.md').read_bytes().decode('utf-8'),
                                      preparer_model=(self.preparation_evidence or {}).get('preparer_model'),
                                      acceptance=target.protected_check.contract_test.read_bytes().decode('utf-8') if target else '',
                                      baseline=diff,base_sha=frozen.base_sha,first_reviewer=first_reviewer)
            if circuit["status"] != "approved":
                held = {**self._identity(build, feature, frozen, base_sha, verdict),
                    "gate": gate, "review": review_verdict, "circuit": circuit,
                    "reason": circuit.get("reason", "review_circuit_held"),
                    "telemetry": self._telemetry_evidence(
                        build, feature, frozen, base_sha, verdict, gate, None)}
                link = self.store.correction_of(build['build_id'])
                attempt, current = (link['attempt'], link['round']) if link else (1, 0)
                if (circuit.get('reason') == 'reviewer_rejected' and first_reviewer is None
                        and next_step(attempt, current) is not None):
                    # A substantive rejection becomes the next author's input, not an owner chore.
                    return self._fail_or_correct(build, feature, held, files, 'reviewer_rejected')
                self.store.hold_dispatched(build["build_id"], "owner_review_required", receipt={
                    **held, **({'correction': {'attempt': attempt, 'round': current, 'exhausted': True}}
                               if link else {})})
                return {"build_id": build["build_id"], "result": {
                    "status": "held", "reason": circuit.get("reason", "review_circuit_held"),
                    "circuit": circuit}}

        request = {
            "attempt_id": build["attempt_id"],
            "build_id": build["build_id"],
            "attempt_generation": build['attempt_generation'],
            "frozen_digest": frozen.digest(),
            "contract_digest": frozen.contract_digest,
            "spec_digest": frozen.spec_digest,
            "acceptance_digest": frozen.acceptance_digest,
            "preparation_digest": (self.preparation_evidence or {}).get('task_digest'),
            "feature_id": feature["id"],
            "title": f"{feature['id']} {feature['title']}",
            "issuer": self.trusted_issuer,
            "target_repo": target_repo,
            "base": frozen.base_sha,
            "head": base_sha,
            "artifact_digest": verdict["digest"],
            "reviewed_diff": verdict["allowed"],
            "files": files,
            "review_status": review_verdict["status"],
            "circuit_status": (circuit or {}).get("status"),
            "review_digest": review_verdict["digest"],
            "review_content_digest": review_verdict["content_digest"],
            "write_scopes": frozen.write_scopes,
            "cancelled": False,
        }
        if self.publication is not None:
            receipt = {**self._identity(build,feature,frozen,base_sha,verdict),
                'allowed':verdict['allowed'],'gate':gate,'review':review_verdict,'circuit':circuit,
                'telemetry':self._telemetry_evidence(build,feature,frozen,base_sha,verdict,gate,None)}
            staged=self.publication.stage(build,request,receipt)
            return {'build_id':build['build_id'],'result':{'status':'publication_queued' if staged else 'stale_attempt'}}
        if self.paid:
            self.store.hold_dispatched(build['build_id'], 'publication_blocked', receipt={
                **self._identity(build,feature,frozen,base_sha,verdict),
                'allowed':verdict['allowed'],'gate':gate,'review':review_verdict,'circuit':circuit,
                'publisher':{'status':'held','reason':'publication_unavailable'}})
            return {'build_id':build['build_id'],'result':{'status':'held','reason':'publication_unavailable'}}
        if self.defer_to:
            # The worker holds no publish credential: it hands the reviewed request to the
            # publisher process, which decides and publishes on its own.
            from .queue import enqueue
            enqueue(self.defer_to, request)
            decision = {"decision": "deferred", "queue": "publish-queue"}
            receipt = {
                **self._identity(build, feature, frozen, base_sha, verdict),
                "pr_shaped": True, "allowed": verdict["allowed"],
                "simulated": not self.paid,
                "gate": gate, "review": review_verdict, "circuit": circuit,
                "publisher": decision,
                "telemetry": self._telemetry_evidence(
                    build, feature, frozen, base_sha, verdict, gate, decision),
                "agent_session": self.session_evidence(session),
            }
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"], receipt,
                terminal=LIVE_COMPLETE if self.paid else SIMULATED_COMPLETE)
            return {"build_id": build["build_id"], "result": result}

        # S3 publisher policy on a fake forge: refused, held or simulated-published.
        publisher = Publisher(
            target_repo, self.forge, trusted_issuer=self.trusted_issuer,
            expected_base=frozen.base_sha, expected_artifact_digest=verdict["digest"],
        )
        decision = publisher.decide(request)
        if decision["decision"] == "refused":
            evidence = self._telemetry_evidence(
                build, feature, frozen, base_sha, verdict, gate, decision)
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"],
                {**self._identity(build, feature, frozen, base_sha, verdict),
                 "gate": gate, "publisher": decision, "telemetry": evidence}, terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}
        if decision["decision"] == "hold":
            reason = HOLD_REASON_MAP.get(decision["reason"], "reconciliation_needed")
            self.store.hold_dispatched(build["build_id"], reason)
            return {"build_id": build["build_id"], "result": {"status": "held",
                    "reason": reason, "publisher": decision}}

        receipt = {
            **self._identity(build, feature, frozen, base_sha, verdict),
            "pr_shaped": True,
            "allowed": verdict["allowed"],
            "simulated": not self.paid,
            "gate": gate,
            "review": review_verdict,
            "circuit": circuit,
            "publisher": decision,
            "telemetry": self._telemetry_evidence(
                build, feature, frozen, base_sha, verdict, gate, decision),
            "agent_session": self.session_evidence(session),
        }
        result = self.store.complete_attempt(
            build["attempt_id"], build["attempt_generation"], receipt,
            terminal=LIVE_COMPLETE if self.paid else SIMULATED_COMPLETE)
        return {"build_id": build["build_id"], "result": result}
