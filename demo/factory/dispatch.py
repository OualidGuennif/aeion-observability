"""S2+S3 dispatch: freeze, build, validate the artifact, gate with protected checks and
a publisher policy, then record an honest simulated receipt.

Everything here is fake inference and a fake forge. The receipt is explicitly PR-shaped
and labelled ``simulated``; it is never evidence of a real GitHub operation. The gate
never trusts the candidate's own claims: it re-checks the frozen identity and the actual
diff, then asks the publisher policy before recording anything.
"""
import subprocess
from pathlib import Path

from . import boundary as stop
from .artifact import validate_artifact
from .checks import DEFAULT_CHECKS, ProtectedChecks
from .freeze import FreezeError, freeze_build
from .gateway import SessionError
from .github import GitHubForge
from .keys import assert_worker_isolated
from .models import Router, Telemetry
from .publish import FakeForge, Publisher
from .review import review
from .review_circuit import two_vote_review
from .store import FAILED

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
                 require_circuit=None, defer_to=None, gateway=None, agent_id=None):
        self.store = store
        self.catalog = catalog
        self.spec_dir = Path(spec_dir)
        self.work_root = Path(work_root)
        self.config = config or {}
        self.checks = checks if checks is not None else ProtectedChecks(DEFAULT_CHECKS)
        self.required_checks = list(required_checks if required_checks is not None else DEFAULT_REQUIRED_CHECKS)
        self.forge = forge if forge is not None else FakeForge()
        self.target_repo = target_repo or DEFAULT_TARGET_REPO
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
    def _collect_files(repo, allowed, limit=512 * 1024):
        """Read the reviewed text files so a real forge can commit exactly what was approved."""
        files = {}
        for relative in allowed:
            path = Path(repo) / relative
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if len(data) > limit or b"\x00" in data:
                continue
            try:
                files[relative] = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
        return files

    def run_once(self):
        """Claim one build, give its agent a session, run it, and end the session whatever happens."""
        assert_worker_isolated()
        build = self.store.claim_next(self.catalog)
        if build is None:
            return None
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
        try:
            repo, base_sha = self._make_repo(build["build_id"])
            frozen = freeze_build(build, self.catalog, self.spec_dir, base_sha, self.config)
        except FreezeError as exc:
            self.store.hold_dispatched(build["build_id"], "qualification_missing")
            return {"build_id": build["build_id"], "result": {"status": "held", "reason": str(exc)}}

        feature = self.catalog.by_id[build["feature_id"]]
        # The build brief lives outside the clone: the agent reads where it stops, the artifact
        # validator never sees it, and the branch it names is the one the publisher will push.
        branch = f"aeion/build-{build['attempt_id'][:24]}"
        (repo.parent / "TASK.md").write_text(
            stop.build_brief(feature["id"], feature["title"], branch) + "\n")
        self._write_simulated_impl(repo, frozen, feature)
        verdict = validate_artifact(repo, frozen.write_scopes)
        if not verdict["accepted"]:
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"],
                {"simulated": True, "verdict": verdict}, terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}

        # The fake builder faithfully reports the spec it read; the gate re-checks this
        # claim against the frozen spec digest (spec_unchanged).
        verdict["spec_digest"] = frozen.spec_digest

        # S3 gate: protected checks judged outside the candidate's control.
        gate = self.checks.verdict(self.required_checks, frozen, verdict)
        if gate["status"] == "qualification_missing":
            self.store.hold_dispatched(build["build_id"], "qualification_missing")
            return {"build_id": build["build_id"], "result": {"status": "held",
                    "reason": "qualification_missing", "gate": gate}}
        if gate["status"] == "failed":
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"],
                {"simulated": True, "gate": gate}, terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}

        # Independent deterministic review: the publisher never sees an unreviewed diff.
        files = self._collect_files(repo, verdict["allowed"])
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
            "write_scopes": frozen.write_scopes,
            "cancelled": False,
        }
        if self.defer_to:
            # The worker holds no publish credential: it hands the reviewed request to the
            # publisher process, which decides and publishes on its own.
            from .queue import enqueue
            enqueue(self.defer_to, request)
            receipt = {
                "simulated": True, "pr_shaped": True, "feature_id": feature["id"],
                "frozen_digest": frozen.digest(), "base_sha": base_sha,
                "artifact_digest": verdict["digest"], "allowed": verdict["allowed"],
                "gate": gate, "review": review_verdict, "circuit": circuit,
                "publisher": {"decision": "deferred", "queue": "publish-queue"},
                "agent_session": self.session_evidence(session),
            }
            result = self.store.complete_attempt(build["attempt_id"], build["attempt_generation"], receipt)
            return {"build_id": build["build_id"], "result": result}

        # S3 publisher policy on a fake forge: refused, held or simulated-published.
        publisher = Publisher(
            self.target_repo, self.forge, trusted_issuer=self.trusted_issuer,
            expected_base=frozen.base_sha, expected_artifact_digest=verdict["digest"],
        )
        decision = publisher.decide(request)
        if decision["decision"] == "refused":
            result = self.store.complete_attempt(
                build["attempt_id"], build["attempt_generation"],
                {"simulated": True, "gate": gate, "publisher": decision}, terminal=FAILED,
            )
            return {"build_id": build["build_id"], "result": result}
        if decision["decision"] == "hold":
            reason = HOLD_REASON_MAP.get(decision["reason"], "reconciliation_needed")
            self.store.hold_dispatched(build["build_id"], reason)
            return {"build_id": build["build_id"], "result": {"status": "held",
                    "reason": reason, "publisher": decision}}

        receipt = {
            "simulated": True,
            "pr_shaped": True,
            "feature_id": feature["id"],
            "frozen_digest": frozen.digest(),
            "base_sha": base_sha,
            "artifact_digest": verdict["digest"],
            "allowed": verdict["allowed"],
            "gate": gate,
            "review": review_verdict,
            "circuit": circuit,
            "publisher": decision,
            "agent_session": self.session_evidence(session),
        }
        result = self.store.complete_attempt(build["attempt_id"], build["attempt_generation"], receipt)
        return {"build_id": build["build_id"], "result": result}
