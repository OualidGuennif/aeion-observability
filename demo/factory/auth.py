"""Administrator sessions and loopback transport checks for the factory API.

Bootstrap happens outside the browser: the caller supplies (or generates once) a
bootstrap token, and each successful login rotates it, so it is single-use. Sessions
carry a server-side CSRF token and enforce idle plus absolute expiry.
"""
import re
import secrets
import threading
import time

LOOPBACK_HOST = re.compile(r"(?:127\.0\.0\.1|localhost)(?::\d+)?")

DEFAULT_IDLE_NS = 30 * 60 * 1_000_000_000      # 30 minutes
DEFAULT_ABSOLUTE_NS = 12 * 3600 * 1_000_000_000  # 12 hours


def host_origin_ok(host, origin=None):
    """Reject non-loopback Host and any Origin that does not match the Host exactly."""
    if not isinstance(host, str) or not LOOPBACK_HOST.fullmatch(host):
        return False
    if origin is not None and origin != "http://" + host:
        return False
    return True


class AdminSessions:
    def __init__(self, bootstrap_token=None, idle_ns=DEFAULT_IDLE_NS, absolute_ns=DEFAULT_ABSOLUTE_NS):
        self.bootstrap_token = bootstrap_token if bootstrap_token else secrets.token_urlsafe(32)
        self.idle_ns = idle_ns
        self.absolute_ns = absolute_ns
        self._sessions = {}
        self._lock = threading.Lock()

    def login(self, token, now_ns=None):
        """Validate the bootstrap token, rotate it and mint a session + CSRF token."""
        now = now_ns if now_ns is not None else time.time_ns()
        if not isinstance(token, str) or not secrets.compare_digest(token, self.bootstrap_token):
            return None
        self.bootstrap_token = secrets.token_urlsafe(32)
        session_id = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[session_id] = {"csrf": csrf, "created_ns": now, "last_seen_ns": now}
        return {"session_id": session_id, "csrf": csrf}

    def authenticate(self, session_id, now_ns=None):
        """Return the live session for a valid, unexpired session id, else None."""
        now = now_ns if now_ns is not None else time.time_ns()
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if now - session["last_seen_ns"] > self.idle_ns or now - session["created_ns"] > self.absolute_ns:
                del self._sessions[session_id]
                return None
            session["last_seen_ns"] = now
            return session

    def check_csrf(self, session, csrf):
        return bool(csrf) and secrets.compare_digest(csrf, session["csrf"])

    def logout(self, session_id):
        with self._lock:
            self._sessions.pop(session_id, None)
