"""HTTP-facing factory API: administrator sessions, CSRF, board, queue, cancel, releases and SSE.

This is the trust boundary of the factory. Every read requires a valid administrator
session; every mutation additionally requires a matching CSRF token and a loopback
Host/Origin. Forum reader sessions never reach these endpoints.
"""
import json
import hashlib
import os
import stat
import secrets
import threading
import time
from pathlib import Path

from .auth import AdminSessions, host_origin_ok
from .budget import DailyBudget, BudgetError
from .manifest import load_manifest, ManifestError
from .observer import Observer
from .store import Store, StoreError
from .sse import SseHub
from .dispatch import DispatchWorker
from .freeze import AUTHOR_TIMEOUT_SECONDS
from .gateway import Gateway, SessionError
from .releases import ReleaseError, ReleaseService
from .retention import Retention
from .flue_qualification import expires_ns as admission_expires_ns

COOKIE = "aeion_factory"
MAX_BODY = 65536
LOGIN_WINDOW_NS = 60 * 1_000_000_000
LOGIN_MAX_ATTEMPTS = 10
S2_CONFIG = {
    "profile": "fake", "mode": "fake", "deadline_ns": 300 * 1_000_000_000,
    "step_cap": 200, "context_limit": 250_000, "cost_reservation_usd": "0.00",
}


class ApiError(Exception):
    def __init__(self, status, code):
        super().__init__(code)
        self.status = status
        self.code = code


class FactoryApp:
    def __init__(self, manifest_path, state_dir, spec_dir=None, bootstrap_token=None, active_concurrency=1,
                 config=None, budget=None, execution=None):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.catalog = load_manifest(manifest_path, spec_dir=spec_dir)
        self.store = Store(self.state_dir / "factory.db", active_concurrency=active_concurrency)
        self.hub = SseHub()
        spec_dir = Path(spec_dir) if spec_dir else Path(manifest_path).resolve().parent
        self.spec_dir = spec_dir
        self.execution = dict(execution) if execution else {"mode": "simulator"}
        self.execution_mode = self.execution.get("mode", "simulator")
        self.execution_hold = self.execution.get("hold_reason")
        # The worker's purse is separate from the cockpit's: autonomous-forum money never pays
        # for the observability demo, and an exhausted purse holds the build before any work.
        self.budget = budget if budget is not None else DailyBudget(
            self.state_dir / "budget" / "ledger.jsonl")
        self.worker = DispatchWorker(self.store, self.catalog, spec_dir, self.state_dir / "work",
                                     config=self._worker_config(config),
                                     budget=self.budget, budget_scope="aeion-autonomous-forum",
                                     target=self.execution.get("target"),
                                     builder=self.execution.get("builder"),
                                     telemetry=self.execution.get("telemetry"),
                                     review_complete=self.execution.get("review_complete"),
                                     check_sandbox=self.execution.get("check_sandbox"),
                                     targets=self.execution.get('targets'),
                                     preparer=self.execution.get('preparer'),
                                     startup_hold=self.execution_hold)
        self.worker.progress = lambda build_id, phase: self.hub.publish(
            'build_progress', {'build_id': build_id, 'phase': phase})
        self.worker.admission_check = lambda: self._execution_blocker() is None
        prune = None
        if self.execution.get('publication'):
            from .publication import PublicationCoordinator, prune_branch
            self.worker.publication = PublicationCoordinator(self.store)
            prune = lambda attempt_id: prune_branch(self.state_dir, attempt_id)
        self.retention = Retention(self.store, self.state_dir / "work", prune_branch=prune)
        self.observer = Observer(self.store)
        self.token_path = self.state_dir / "admin.token"
        token = bootstrap_token if bootstrap_token is not None else self._load_or_create_token()
        self.auth = AdminSessions(bootstrap_token=token)
        self._lock = threading.Lock()
        self._login_attempts = []
        # The release plane opens sockets, so it is built on first use: a board-only session
        # (and every test that only queues builds) must not pay for a load balancer.
        self.release_service = None
        self.playground = None
        self.cache_backend = None
        self.gateway = None

    # ------------------------------------------------------------- bootstrap token
    def _worker_config(self, config):
        worker_config = dict(config if config is not None else S2_CONFIG)
        if self.execution_mode == 'live' and getattr(self.execution.get('builder'),'paid',False):
            worker_config.update(mode='live',profile='flue-pi')
            if config is None:
                window = getattr(self.execution.get('builder'), 'timeout_seconds', AUTHOR_TIMEOUT_SECONDS)
                worker_config['deadline_ns'] = window * 1_000_000_000
        if self.execution.get("cost_reservation_usd") is not None:
            worker_config["cost_reservation_usd"] = self.execution["cost_reservation_usd"]
        return worker_config

    def _load_or_create_token(self):
        if self.token_path.is_file():
            existing = self.token_path.read_text().strip()
            if existing:
                return existing
        token = secrets.token_urlsafe(32)
        self.token_path.write_text(token + "\n")
        os.chmod(self.token_path, 0o600)
        return token

    def _persist_token(self):
        try:
            self.token_path.write_text(self.auth.bootstrap_token + "\n")
            os.chmod(self.token_path, 0o600)
        except OSError:
            pass

    # ------------------------------------------------------------- login rate limit
    def _login_allowed(self):
        with self._lock:
            now = time.time_ns()
            self._login_attempts = [t for t in self._login_attempts if now - t < LOGIN_WINDOW_NS]
            return len(self._login_attempts) < LOGIN_MAX_ATTEMPTS

    def _record_login_attempt(self):
        with self._lock:
            self._login_attempts.append(time.time_ns())

    # ------------------------------------------------------------- auth plumbing
    @staticmethod
    def _set_cookie(session_id):
        return f"{COOKIE}={session_id}; Path=/; HttpOnly; SameSite=Strict"

    @staticmethod
    def _cookie_value(cookie_header, name):
        if not cookie_header:
            return None
        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith(name + "="):
                return part[len(name) + 1:]
        return None

    def authenticate(self, cookie_header):
        session_id = self._cookie_value(cookie_header, COOKIE)
        if not session_id:
            return None
        return self.auth.authenticate(session_id)

    def _require_csrf(self, session, csrf_header):
        if not self.auth.check_csrf(session, csrf_header):
            raise ApiError(403, "csrf_denied")

    # ------------------------------------------------------------- endpoints
    def _execution_blocker(self):
        check=self.execution.get('admission_check')
        if check is not None:
            try:qualified=callable(check) and check() is True
            except Exception:qualified=False
            if not qualified:return 'flue_factory_unqualified'
            if self.execution_hold=='flue_factory_unqualified':return None
        return self.execution_hold

    def login(self, host, origin, body):
        if not host_origin_ok(host, origin):
            raise ApiError(403, "origin_denied")
        if not self._login_allowed():
            raise ApiError(429, "too_many_login_attempts")
        token = body.get("token") if isinstance(body, dict) else None
        session = self.auth.login(token)
        if session is None:
            self._record_login_attempt()
            raise ApiError(401, "invalid_token")
        self._persist_token()
        self.hub.publish("session_rotated", None)
        return 200, {"csrf": session["csrf"]}, {"Set-Cookie": self._set_cookie(session["session_id"])}

    def catalog_view(self, session):
        target = self.execution.get('target')
        blocker=self._execution_blocker()
        availability = self.store.feature_availability(
            self.catalog, target_feature=target.feature_id if target else None,
            execution_hold=blocker, target_required=self.execution_mode != 'simulator'
                and self.execution.get('preparer') is None,
            target_features=list(self.execution['targets']) if 'targets' in self.execution else None)
        return 200, {
            "schema_version": self.catalog.schema_version,
            "count": len(self.catalog.features),
            "features": [{**feature, 'availability': availability[feature['id']]}
                         for feature in self.catalog.features],
            "execution": {
                "mode": self.execution_mode,
                "hold_reason": blocker,
                "target_feature": (self.execution.get("target").feature_id
                                   if self.execution.get("target") is not None else None),
                "target_features": sorted(self.execution.get('targets') or {}),
                "automatic_preparation": self.execution.get('preparer') is not None,
                "author_window_seconds": (int(self.execution['builder'].timeout_seconds)
                    if isinstance(getattr(self.execution.get('builder'), 'timeout_seconds', None), int)
                    else None),
                "live_hold_reason": (
                    (None if self.execution.get("builder") is not None and not blocker
                     else (blocker or "live_builder_unqualified"))
                    if self.execution_mode == "live" else "live_builder_unqualified"),
                "admission_expires_ns": admission_expires_ns(),
            },
        }, {}

    def spec_view(self, session, feature_id):
        """Authenticated by the HTTP boundary; return text as data, never rendered HTML."""
        feature = self.catalog.by_id.get(feature_id)
        if feature is None:
            raise ApiError(404, 'feature_unknown')
        name = feature['file']
        if (not isinstance(name, str) or Path(name).name != name or '\\' in name
                or not name.endswith('.md')):
            raise ApiError(409, 'spec_unavailable')
        try:
            fd = os.open(self.spec_dir / name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd, 'rb') as source:
                if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                    raise ApiError(409, 'spec_unavailable')
                data = source.read(65537)
            if len(data) > 65536:
                raise ApiError(413, 'spec_too_large')
            text = data.decode('utf-8')
        except (OSError, UnicodeError):
            raise ApiError(409, 'spec_unavailable') from None
        return 200, {'id': feature_id, 'title': feature['title'], 'markdown': text,
                     'sha256': hashlib.sha256(data).hexdigest()}, {}

    def board(self, session):
        try:
            budget = {'status': 'available', 'scopes': self.budget.summary()}
        except (BudgetError, OSError):
            budget = {'status': 'unavailable', 'scopes': {}}
        return 200, {
            "builds": self.store.board(),
            "earliest_seq": self.hub.earliest_seq(),
            "budget": budget,
            "csrf": session.get('csrf') if session else None,
        }, {}

    def queue(self, host, origin, session, csrf, body):
        if not host_origin_ok(host, origin):
            raise ApiError(403, "origin_denied")
        self._require_csrf(session, csrf)
        blocker=self._execution_blocker()
        if blocker:
            raise ApiError(409, blocker)
        ids = body.get("ids") if isinstance(body, dict) else None
        key = body.get("idempotency_key") if isinstance(body, dict) else None
        if (not isinstance(ids, list) or any(not isinstance(fid, str) for fid in ids)
                or not isinstance(key, str) or not key):
            raise ApiError(400, "invalid_request")
        try:
            result = self.store.admit(ids, key, self.catalog, actor="owner")
        except StoreError as exc:
            code = str(exc)
            conflict = code.startswith(('catalog_changed', 'feature_already_completed:', 'feature_in_progress:',
                                        'publication_reconciliation_required:'))
            raise ApiError(409 if conflict else 400, code)
        self.hub.publish("admitted", result)
        return 200, result, {}

    def cancel(self, host, origin, session, csrf, body):
        if not host_origin_ok(host, origin):
            raise ApiError(403, "origin_denied")
        self._require_csrf(session, csrf)
        build_id = body.get("build_id") if isinstance(body, dict) else None
        if not isinstance(build_id, str):
            raise ApiError(400, "invalid_request")
        result = self.store.cancel(build_id, actor="owner")
        if result["status"] == "not_found":
            raise ApiError(404, "not_found")
        self.hub.publish("cancelled", result)
        return 200, result, {}

    def logout(self, cookie_header):
        session_id = self._cookie_value(cookie_header, COOKIE)
        if session_id:
            self.auth.logout(session_id)
        return 200, {"status": "logged_out"}, {}

    def events_since(self, since):
        return self.hub.replay(since)

    def tick(self):
        """Recheck freshness without consuming an unstarted queued attempt."""
        self.worker.startup_hold=self._execution_blocker()
        # Freshness is temporary and must preserve an unstarted queued attempt.
        # Other explicit configuration holds retain their durable held receipt.
        paused = self.worker.startup_hold == 'flue_factory_unqualified'
        result = None if paused else self.worker.run_once()
        if result is not None:
            self.hub.publish("build_updated", result)
        try:
            self.retention.tick()
        except Exception:  # noqa: BLE001 - cleanup must never break the build loop
            pass
        for proposal in self.observer.propose():
            self.hub.publish("observed", proposal)
        if self.release_service is not None:
            try:
                change = self.release_service.tick()
            except Exception:  # noqa: BLE001 - monitoring must never break the build loop
                change = None
            if change:
                self.hub.publish("release_updated", change)
        return result

    # ------------------------------------------------------------- release plane
    def _release_service(self):
        """Build the data plane once, on the first release call, and never in a board-only test."""
        if self.release_service is None:
            from deploy.cache import connect
            from deploy.playground import Playground

            cache, self.cache_backend = connect(self._env("AEION_REDIS_URL") or None,
                                                self.state_dir / "cache", ttl=60)
            self.playground = Playground(cache, percent=0, seed="staged").start()
            self.release_service = ReleaseService(
                self.store, self.playground, self.state_dir / "releases",
                scale=float(self._env("AEION_RELEASE_SCALE") or 1),
                sample_interval_seconds=float(self._env("AEION_CANARY_SAMPLE_SECONDS") or 60),
            )
        return self.release_service

    @staticmethod
    def _env(name):
        import os

        return os.environ.get(name)

    def releases_view(self, session):
        try:
            service = self._release_service()
        except OSError:
            raise ApiError(503, "release_plane_unavailable")
        view = service.view()
        view["cache"] = {"backend": self.cache_backend}
        view["sessions"] = self._gateway().sessions()[-20:]
        return 200, view, {}

    def release_action(self, host, origin, session, csrf, body):
        if not host_origin_ok(host, origin):
            raise ApiError(403, "origin_denied")
        self._require_csrf(session, csrf)
        action = body.get("action") if isinstance(body, dict) else None
        release_id = body.get("release_id") if isinstance(body, dict) else None
        service = self._release_service()
        try:
            if action == "validate":
                service.validate(release_id)
            elif action == "advance":
                service.advance(release_id)
            elif action == "deploy_now":
                service.deploy_now(release_id)
            elif action == "resume":
                service.resume(release_id)
            elif action == "rollback":
                service.rollback(release_id, reason=str(body.get("reason") or "operator")[:80])
            elif action == "flag":
                service.set_flag(str(body.get("name") or ""), enabled=body.get("enabled"),
                                 rollout=body.get("rollout"), release_id=release_id)
            elif action == "stage":
                features = body.get("features")
                if not isinstance(features, list) or not features:
                    raise ApiError(400, "invalid_request")
                service.stage(features, flags=body.get("flags"))
            else:
                raise ApiError(400, "unknown_action")
        except ReleaseError as exc:
            raise ApiError(409, str(exc)[:120])
        self.hub.publish("release_updated", {"action": action})
        return self.releases_view(session)

    # ------------------------------------------------------------- agent sessions
    def _gateway(self):
        """The gateway holds the key; agents only ever hold the token it issues."""
        if self.gateway is None:
            from .gh_probe import call, load_secret

            def transport(method, path):
                load_secret("GH_API_KEY")
                import os

                status, payload, _ = call(method, path, os.environ.get("GH_API_KEY"))
                return status, payload

            self.gateway = Gateway(self.store, transport,
                                   repo="OualidGuennif/aeion-autonomous-forum",
                                   audit_path=self.state_dir / "gateway-audit.jsonl")
        return self.gateway

    def sessions(self, host, origin, session, csrf, body):
        if not host_origin_ok(host, origin):
            raise ApiError(403, "origin_denied")
        self._require_csrf(session, csrf)
        gateway = self._gateway()
        action = body.get("action") if isinstance(body, dict) else None
        try:
            if action == "issue":
                issued = gateway.issue(str(body.get("agent_id") or ""), str(body.get("build_id") or ""),
                                       feature_id=body.get("feature_id"))
                self.hub.publish("session_issued", {"agent_id": body.get("agent_id")})
                return 200, {"issued": issued, "sessions": gateway.sessions()[-20:]}, {}
            if action == "revoke":
                gateway.revoke(str(body.get("token") or ""), reason="operator")
                return 200, {"sessions": gateway.sessions()[-20:]}, {}
        except SessionError as exc:
            raise ApiError(409, str(exc)[:120])
        raise ApiError(400, "unknown_action")
