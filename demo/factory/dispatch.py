"""S2+S3 dispatch: freeze, build, validate, check, review and record a bound receipt.

Builders may use live inference or a labeled fixture. A fake forge is the default and a local
live completion is not evidence of a GitHub operation or an integrated feature. The gate
never trusts the candidate's own claims: it re-checks the frozen identity and the actual
diff, then asks the publisher policy before recording anything.
"""
import json
import subprocess
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from . import boundary as stop
from .artifact import validate_artifact
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
from .review import content_digest, review
from .review_circuit import two_vote_review
from .store import FAILED, LIVE_COMPLETE, SIMULATED_COMPLETE
from .target import TargetError
from .preparation import PreparationError

DEFAULT_REQUIRED_CHECKS = ["scope", "spec_unchanged"]
DEFAULT_TARGET_REPO = "agora/forum"
HOLD_REASON_MAP = {
    "owner_review_required": "owner_review_required",
    "stale_base": "reconciliation_needed",
    "stale_head": "reconciliation_needed",
}


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
        self.check_sandbox = check_sandbox
        self.explicit_checks = checks is not None
        self.explicit_required_checks = required_checks is not None
        self.builder = builder
        self.telemetry = telemetry
        self.budget = budget
        self.budget_scope = budget_scope
        self.allow_unbudgeted = bool(allow_unbudgeted)
        self.startup_hold = startup_hold
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

    def _identity(self, build, feature, frozen, base_sha, verdict):
        """The four ids every receipt carries, so a board row reaches its trace and artifact."""
        execution = getattr(self.builder, 'last_execution', None)
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
            "preparation": self.preparation_evidence,
            "preparation_execution": preparation_execution,
            "base_sha": base_sha,
            "artifact_digest": verdict.get("digest"),
            "routing": self.author_routing,
            "execution": execution,
        }

    def _progress(self, build, phase, detail=None):
        if self.store.record_progress(build['attempt_id'], build['attempt_generation'], phase, detail or {}):
            if self.progress:
                self.progress(build['build_id'], phase)

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
            evidence = self.telemetry.emit(
                build_id=build["build_id"], feature_id=feature["id"],
                attempt_id=build["attempt_id"], artifact_digest=verdict.get("digest"),
                base_sha=base_sha, gate_status=(gate or {}).get("status"),
                publisher_decision=(decision or {}).get("decision"), synthetic=not self.paid,
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

    def _settle(self, reservation):
        """Close the reservation only with measured, complete usage; unknown stays open."""
        if reservation is None:
            return
        usage = self.last_usage
        if not isinstance(usage, dict) or usage.get("complete") is not True:
            return
        raw = usage.get("cost_usd")
        if raw is None:
            return
        try:
            self.budget.settle(reservation, Decimal(str(raw)))
        except (BudgetError, InvalidOperation, ValueError):
            # The reservation stays open and keeps counting: fail closed, never free the money.
            return

    def run_once(self):
        """Claim one build, give its agent a session, run it, and end the session whatever happens."""
        assert_worker_isolated()
        if self.publication is not None:
            publication = self.publication.run_once()
            if publication is not None:
                return publication
        self.last_usage = None
        # Cover the longest admitted check, one author call, two votes and teardown.
        # Expiry is recovery from an interrupted process, not an ordinary slow check.
        targets = list((self.targets or {}).values()) or ([self.target] if self.target else [])
        check_seconds = max((t.protected_check.timeout_seconds for t in targets), default=0)
        # Live Flue roles declare their own transport window; fixtures have no remote wait.
        author_seconds = getattr(self.builder, 'timeout_seconds', 0)
        review_seconds = getattr(self.review_complete, 'timeout_seconds', 0)
        preparation_seconds = getattr(self.preparer,'timeout_seconds',0)
        if self.preparer is not None:check_seconds=max(check_seconds,900)
        lease_ns = (preparation_seconds + check_seconds + author_seconds + 2 * review_seconds + 60) * 1_000_000_000
        build = self.store.claim_next(self.catalog, lease_ns=lease_ns)
        if build is None:
            return None
        self.author_routing, self.author_ms = None, None
        self.preparation_evidence = None
        for role in (self.builder, self.review_complete):
            if role is not None and hasattr(role, 'authorization_check'):
                role.authorization_check = lambda: self.catalog.matches_contract(build) and self.store.attempt_authorized(
                    build['attempt_id'], build['attempt_generation'])
        feature = self.catalog.by_id[build['feature_id']]
        selected_target = (self.targets or {}).get(feature['id']) or self.target
        cohort = cohort_for(feature, selected_target.protected_check.id if selected_target else
                            'prepared_gradle' if self.preparer is not None else 'fixture')
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
        prepared_target = None
        if self.preparer is not None:
            self._progress(build,'preparing')
            started=time.monotonic()
            try:
                prepared_target,self.preparation_evidence=self.preparer.prepare(
                    build=build,catalog=self.catalog,spec_dir=self.spec_dir,
                    destination=self.work_root / build['build_id'] / 'prepared',budget=self.budget,
                    router=self.router,authorized=lambda:self.catalog.matches_contract(build) and self.store.attempt_authorized(
                        build['attempt_id'],build['attempt_generation']))
                if not self.store.record_preparation(build['attempt_id'],build['attempt_generation'],self.preparation_evidence):
                    return {'build_id':build['build_id'],'result':{'status':'stale_attempt'}}
            except (PreparationError,TargetError,BudgetError) as error:
                self.store.hold_dispatched(build['build_id'],'preparation_unavailable',receipt={
                    'build_id':build['build_id'],'attempt_id':build['attempt_id'],
                    'reason':str(error) if isinstance(error,PreparationError) else 'preparation_infrastructure_unavailable'})
                return {'build_id':build['build_id'],'result':{'status':'held','reason':'preparation_unavailable'}}
            except Exception as error:
                self.store.hold_dispatched(build['build_id'],'preparation_unavailable',receipt={
                    'build_id':build['build_id'],'attempt_id':build['attempt_id'],
                    'reason':'preparation_failed','error_type':type(error).__name__})
                return {'build_id':build['build_id'],'result':{'status':'held','reason':'preparation_unavailable'}}
            finally:
                role=self.preparer.role
                execution=getattr(role,'last_execution',None) or {}
                if getattr(role,'paid',False) and execution.get('forwarded_count') and self.preparer.last_model:
                    measured=getattr(role,'last_usage',None) or {}
                    self.router.telemetry.record(self.preparer.last_model,'prepare',
                        'passed' if self.preparation_evidence is not None else 'unknown',
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
                self._settle(reservation)

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
            answer=self.review_complete(model, prompt)
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
            if reservation is not None and isinstance(usage, dict):
                raw = usage.get("cost_usd")
                if usage.get("complete") is True and raw is not None:
                    try:
                        self.budget.settle(reservation, Decimal(str(raw)))
                    except (BudgetError, InvalidOperation, ValueError):
                        # Unknown or unreadable cost keeps the reservation counted.
                        pass

    def _zero_transport_proven(self):
        """Only a build with no paid builder and no model review can prove zero spend."""
        return not self.paid and self.review_complete is None

    def _run(self, build, session, target_override=None):
        feature = self.catalog.by_id[build["feature_id"]]
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
                base_sha = target.materialize(repo)
            frozen = freeze_build(
                build, self.catalog, self.spec_dir, base_sha, self.config,
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
                if hasattr(self.builder, 'run_build'):
                    self.builder.run_build(repo=repo, frozen=frozen, feature=feature,
                        brief=repo.parent / 'BRIEF.md', target=target, build=build,
                        progress=progress, router=self.router)
                else:
                    self.builder(repo=repo, frozen=frozen, feature=feature,
                                 brief=repo.parent / "BRIEF.md")
                self._take_builder_state()
        except Exception as exc:  # noqa: BLE001 - a failed builder never publishes
            self._take_builder_state()
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"],
                {"simulated": not self.paid, "author_model": self.author_model if self.paid else None,
                 "build_id": build["build_id"], "feature_id": feature["id"],
                 "attempt_id": build["attempt_id"],
                 "reason": "builder_error", "detail": type(exc).__name__,
                 "error": str(exc) if isinstance(exc, BuilderError) else None,
                 "telemetry": self._telemetry_evidence(
                     build, feature, frozen, base_sha, {}, {"status": "builder_error"}, None)},
                terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}
        finally:
            self.author_ms = int((time.monotonic() - started_author) * 1000)
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
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"],
                {**self._identity(build, feature, frozen, base_sha, verdict),
                 "gate": gate, "telemetry": evidence}, terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}

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
            circuit = two_vote_review(self.author_model, feature["id"], files,
                                      self.router, self._review_vote,
                                      usage_for_vote=lambda: getattr(self.review_complete, 'last_usage', None),
                                      execution_for_vote=lambda: getattr(self.review_complete,'last_execution',None),
                                      observed_for_vote=lambda: not getattr(self.review_complete, 'paid', False)
                                        or bool((getattr(self.review_complete, 'last_execution', None) or {}).get('forwarded_count')),
                                      specification=(repo.parent / 'BRIEF.md').read_bytes().decode('utf-8'),
                                      preparer_model=(self.preparation_evidence or {}).get('preparer_model'),
                                      acceptance=target.protected_check.contract_test.read_bytes().decode('utf-8') if target else '')
            if circuit["status"] != "approved":
                self.store.hold_dispatched(build["build_id"], "owner_review_required", receipt={
                    **self._identity(build, feature, frozen, base_sha, verdict),
                    "gate": gate, "review": review_verdict, "circuit": circuit,
                    "reason": circuit.get("reason", "review_circuit_held"),
                    "telemetry": self._telemetry_evidence(
                        build, feature, frozen, base_sha, verdict, gate, None)})
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
