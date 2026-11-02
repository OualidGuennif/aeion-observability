"""S2+S3 dispatch: freeze, build, validate the artifact, gate with protected checks and
a publisher policy, then record an honest simulated receipt.

Everything here is fake inference and a fake forge. The receipt is explicitly PR-shaped
and labelled ``simulated``; it is never evidence of a real GitHub operation. The gate
never trusts the candidate's own claims: it re-checks the frozen identity and the actual
diff, then asks the publisher policy before recording anything.
"""
import subprocess
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
from .publish import FakeForge, Publisher
from .review import content_digest, review
from .review_circuit import two_vote_review
from .store import FAILED, LIVE_COMPLETE, SIMULATED_COMPLETE
from .target import TargetError

DEFAULT_REQUIRED_CHECKS = ["scope", "spec_unchanged"]
DEFAULT_TARGET_REPO = "agora/forum"
HOLD_REASON_MAP = {
    "owner_review_required": "owner_review_required",
    "stale_base": "reconciliation_needed",
    "stale_head": "reconciliation_needed",
}


class DispatchWorker:
    def __init__(self, store, catalog, spec_dir, work_root, config=None,
                 checks=None, required_checks=None, forge=None, target_repo=None,
                 trusted_issuer="gate", review_complete=None, author_model="deepseek-4.1-flash",
                 require_circuit=None, defer_to=None, gateway=None, agent_id=None,
                 target=None, builder=None, telemetry=None, budget=None,
                 budget_scope="aeion-autonomous-forum", allow_unbudgeted=False,
                 startup_hold=None, check_sandbox=None):
        self.store = store
        self.catalog = catalog
        self.spec_dir = Path(spec_dir)
        self.work_root = Path(work_root)
        self.config = config or {}
        self.target = target
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
        # A real forge is only reachable once two independent models have approved the diff.
        self.defer_to = defer_to
        # No agent holds a GitHub key: when a gateway is configured, every attempt gets its own
        # short-lived session, recorded in the receipt and revoked when the attempt ends.
        self.gateway = gateway
        self.agent_id = agent_id
        self.require_circuit = (bool(defer_to) or isinstance(self.forge, GitHubForge)
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
        return {
            "simulated": not self.paid,
            "author_model": self.author_model if self.paid else None,
            "build_id": build["build_id"],
            "feature_id": feature["id"],
            "attempt_id": build["attempt_id"],
            "frozen_digest": frozen.digest(),
            "base_sha": base_sha,
            "artifact_digest": verdict.get("digest"),
        }

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
        self.last_usage = None
        build = self.store.claim_next(self.catalog)
        if build is None:
            return None
        if self.startup_hold:
            # The configured execution is unavailable (or unknown): hold before any spend.
            self.store.hold_dispatched(build["build_id"], self.startup_hold)
            return {"build_id": build["build_id"],
                    "result": {"status": "held", "reason": self.startup_hold}}
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
                return self._run(build, session)
            finally:
                self._close_session(session)
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

    def _run(self, build, session):
        feature = self.catalog.by_id[build["feature_id"]]
        if self.target is not None and feature["id"] != self.target.feature_id:
            # A pinned profile belongs to one feature; it must never freeze another one.
            self.store.hold_dispatched(build["build_id"], "target_feature_mismatch")
            return {"build_id": build["build_id"],
                    "result": {"status": "held", "reason": "target_feature_mismatch"}}
        try:
            if self.target is None:
                repo, base_sha = self._make_repo(build["build_id"])
            else:
                repo = self.work_root / build["build_id"] / "repo"
                base_sha = self.target.materialize(repo)
            frozen = freeze_build(
                build, self.catalog, self.spec_dir, base_sha, self.config,
                write_scopes=self.target.write_paths if self.target is not None else None,
                spec_path=self.target.brief if self.target is not None else None,
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
        if self.target is not None:
            (repo.parent / "BRIEF.md").write_text(self.target.brief.read_text())
            brief += ("\nSpecification: BRIEF.md, outside the repository and read-only.\n"
                      "Write scopes: " + ", ".join(self.target.write_paths) + ".\n")
        (repo.parent / "TASK.md").write_text(brief + "\n")
        self.last_usage = (None if self.paid else
                           {"cost_usd": "0", "complete": True, "basis": "no_paid_transport"})
        try:
            if self.builder is None:
                self._write_simulated_impl(repo, frozen, feature)
            else:
                self.builder(repo=repo, frozen=frozen, feature=feature,
                             brief=repo.parent / "BRIEF.md")
                if self.paid:
                    self.last_usage = getattr(self.builder, "last_usage", None)
                    self.author_model = getattr(self.builder, "model", self.author_model)
        except Exception as exc:  # noqa: BLE001 - a failed builder never publishes
            if self.paid:
                self.last_usage = getattr(self.builder, "last_usage", None)
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"],
                {"simulated": not self.paid, "build_id": build["build_id"],
                 "feature_id": feature["id"], "attempt_id": build["attempt_id"],
                 "reason": "builder_error", "detail": type(exc).__name__},
                terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}
        verdict = validate_artifact(repo, frozen.write_scopes)
        files = verdict.pop("files", {})
        if verdict["accepted"] and not self._content_bound(files, verdict):
            verdict = {**verdict, "accepted": False,
                       "rejected": [{"path": "*", "reason": "content_digest_mismatch"}]}
        if not verdict["accepted"]:
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"],
                {"simulated": True, "verdict": verdict}, terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}

        # The builder faithfully reports the spec it read; the gate re-checks this
        # claim against the frozen spec digest (spec_unchanged).
        verdict["spec_digest"] = frozen.spec_digest
        # The protected check needs the tree, never the candidate's claim; it is not
        # persisted in the receipt and is dropped as soon as the gate has judged.
        verdict["repo"] = str(repo)

        # S3 gate: protected checks judged outside the candidate's control.
        gate = self.checks.verdict(self.required_checks, frozen, verdict)
        verdict.pop("repo", None)
        if any(result.get("reason") == "isolation_unqualified"
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
                {"simulated": True, "gate": gate, "review": review_verdict}, terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}
        if review_verdict["status"] == "held":
            self.store.hold_dispatched(build["build_id"], "owner_review_required")
            return {"build_id": build["build_id"], "result": {"status": "held",
                    "reason": "owner_review_required", "review": review_verdict}}

        # Two independent model votes from different families, never the author's.
        circuit = None
        if self.require_circuit:
            if self.review_complete is None:
                self.store.hold_dispatched(build["build_id"], "owner_review_required")
                return {"build_id": build["build_id"], "result": {
                    "status": "held", "reason": "review_circuit_unconfigured"}}
            circuit = two_vote_review(self.author_model, feature["id"], files,
                                      self.router, self.review_complete)
            if circuit["status"] != "approved":
                self.store.hold_dispatched(build["build_id"], "owner_review_required")
                return {"build_id": build["build_id"], "result": {
                    "status": "held", "reason": circuit.get("reason", "review_circuit_held"),
                    "circuit": circuit}}

        request = {
            "attempt_id": build["attempt_id"],
            "build_id": build["build_id"],
            "feature_id": feature["id"],
            "title": f"{feature['id']} {feature['title']}",
            "issuer": self.trusted_issuer,
            "target_repo": self.target_repo,
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
            self.target_repo, self.forge, trusted_issuer=self.trusted_issuer,
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
