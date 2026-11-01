"""The authentication gateway: agents never hold a GitHub key, only a short-lived session.

Every agent is created with an identity and a session token minted at that moment. The token is
bound to the project, to the agent and to the build; it expires in minutes; it is stored hashed; and
it only unlocks the two or three read calls that identity is allowed to make. When the agent wants
GitHub it calls the gateway, and the gateway performs the request with the real key, which never
enters the agent's process, its workspace or its prompt.

Properties, each with the code that enforces it:

* **no shared key** — `issue()` returns a token; the key stays in the gateway process
  (`call()` uses the transport it was constructed with);
* **temporary** — `expires_ns` is set at issue time and `verify()` refuses an expired session;
* **identifiable** — every call appends `{agent_id, session, method, path, status}` to the audit
  log, so "which agent asked for what" is answerable after the fact;
* **not usable outside the project** — the path must start with `/repos/<pinned repo>/`, so a token
  cannot reach another repository even if it leaks;
* **least privilege** — a capability is a set of HTTP methods, and an agent's default session is
  `github:read` only, so it cannot push, open a pull request or merge;
* **revocable** — `revoke()` ends a session immediately, before its expiry.
"""
import hashlib
import json
import secrets
import time
from pathlib import Path

TTL_SECONDS = 900
MAX_TTL_SECONDS = 3600
# A 15-minute token breaks a 20-minute build, so a session may renew — but only three times, and
# never past an absolute deadline. Sixteen minutes of grace let a renew land after a late expiry.
MAX_RENEWALS = 3
GRACE_SECONDS = 120
MIN_RENEW_FRACTION = 0.5   # renewing with more than half the TTL left burns budget for nothing
IDLE_SECONDS = 900         # a session nobody used for 15 min is not kept alive
MAX_SESSIONS = 500
CAPABILITIES = {
    "github:read": frozenset({"GET"}),
    "github:write": frozenset({"GET", "POST", "PATCH", "PUT", "DELETE"}),
}
AGENT_CAPABILITIES = ("github:read",)


class SessionError(ValueError):
    """A session that cannot be used: missing, expired, revoked, or out of its scope."""


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


class Gateway:
    def __init__(self, store, transport, repo, ttl_seconds=TTL_SECONDS, clock=None, audit_path=None):
        self.store = store
        self.transport = transport
        self.repo = repo
        self.ttl_seconds = min(int(ttl_seconds), MAX_TTL_SECONDS)
        self.clock = clock or time.time_ns
        self.audit_path = Path(audit_path) if audit_path else None

    # ------------------------------------------------------------------ sessions
    def _index(self):
        try:
            return json.loads(self.store.meta_get("session:index") or "[]")
        except ValueError:
            return []

    def issue(self, agent_id, build_id, feature_id=None, capabilities=AGENT_CAPABILITIES,
              ttl_seconds=None, max_renewals=MAX_RENEWALS):
        """Mint a session for one agent; the token is returned once and stored only as a digest."""
        if not agent_id or not build_id:
            raise SessionError("agent_and_build_required")
        capabilities = tuple(capabilities)
        unknown = [capability for capability in capabilities if capability not in CAPABILITIES]
        if unknown:
            raise SessionError("unknown_capability:" + ",".join(unknown))
        now = self.clock()
        ttl = min(int(ttl_seconds or self.ttl_seconds), MAX_TTL_SECONDS)
        token = "aeion_" + secrets.token_urlsafe(32)
        max_renewals = max(0, min(int(max_renewals), MAX_RENEWALS))
        record = {
            "session": _hash(token)[:32],
            "agent_id": str(agent_id)[:120],
            "build_id": str(build_id)[:120],
            "feature_id": str(feature_id)[:40] if feature_id else None,
            "capabilities": list(capabilities),
            "repo": self.repo,
            "issued_ns": now,
            "expires_ns": now + ttl * 1_000_000_000,
            # The hard ceiling: renewals buy time inside it, they never move it.
            "absolute_expires_ns": now + ttl * (1 + max_renewals) * 1_000_000_000,
            "renewals": 0,
            "max_renewals": max_renewals,
            "parent": None,
            "last_used_ns": None,
            "uses": 0,
            "revoked_ns": None,
            "revoked_reason": None,
        }
        self.store.meta_set(f"session:{record['session']}", json.dumps(record, sort_keys=True))
        index = self._index() + [record["session"]]
        self.store.meta_set("session:index", json.dumps(index[-MAX_SESSIONS:]))
        self._audit({"event": "issued", "at_ns": now, "session": record["session"],
                     "agent_id": record["agent_id"], "build_id": record["build_id"],
                     "capabilities": record["capabilities"], "expires_ns": record["expires_ns"]})
        return {"session": record["session"], "token": token, "expires_ns": record["expires_ns"],
                "capabilities": record["capabilities"], "repo": self.repo}

    def _load(self, token):
        if not isinstance(token, str) or not token.startswith("aeion_"):
            raise SessionError("malformed_session")
        raw = self.store.meta_get(f"session:{_hash(token)[:32]}")
        if not raw:
            raise SessionError("unknown_session")
        try:
            return json.loads(raw)
        except ValueError as exc:
            raise SessionError("session_corrupt") from exc

    def verify(self, token):
        """A usable session, or a refusal that names why — never a default allow."""
        record = self._load(token)
        now = self.clock()
        if record.get("revoked_ns"):
            raise SessionError("session_revoked")
        if now >= int(record["expires_ns"]):
            raise SessionError("session_expired")
        return record

    def renew(self, token, ttl_seconds=None):
        """Rotate a live session forward, inside a bounded budget and an absolute deadline.

        Four guards, each with a reason a caller can act on:
          * a revoked session never renews;
          * an expired session may renew only inside the grace window (a build that ran 40 s late);
          * a session that burned its three renewals stops, whatever its deadline;
          * renewing with more than half the TTL left is refused, because it buys nothing and
            spends budget a long build may need later.
        The token rotates: the old value stops working the moment the new one exists.
        """
        record = self._load(token)
        now = self.clock()
        if record.get("revoked_ns"):
            raise SessionError("session_revoked")
        expired_at = int(record["expires_ns"])
        if now >= expired_at + GRACE_SECONDS * 1_000_000_000:
            raise SessionError("session_expired")
        renewals = int(record.get("renewals", 0))
        if renewals >= int(record.get("max_renewals", MAX_RENEWALS)):
            raise SessionError("renewal_budget_exhausted")
        if now < expired_at:
            remaining = (expired_at - now) / 1_000_000_000
            lifetime = max(1.0, (expired_at - int(record["issued_ns"])) / 1_000_000_000)
            if remaining > lifetime * MIN_RENEW_FRACTION:
                raise SessionError("renewal_too_early")
        last_used = record.get("last_used_ns")
        if last_used and now - int(last_used) > IDLE_SECONDS * 1_000_000_000:
            raise SessionError("session_idle")

        ttl = min(int(ttl_seconds or self.ttl_seconds), MAX_TTL_SECONDS)
        candidate = now + ttl * 1_000_000_000
        deadline = int(record.get("absolute_expires_ns", expired_at))
        rotated = "aeion_" + secrets.token_urlsafe(32)
        successor = dict(record)
        successor.update({
            "session": _hash(rotated)[:32],
            "issued_ns": now,
            "expires_ns": min(candidate, deadline),
            "renewals": renewals + 1,
            "parent": record["session"],
            "last_used_ns": None,
            "uses": 0,
        })
        record["revoked_ns"] = now
        record["revoked_reason"] = "rotated"
        self.store.meta_set(f"session:{record['session']}", json.dumps(record, sort_keys=True))
        self.store.meta_set(f"session:{successor['session']}", json.dumps(successor, sort_keys=True))
        index = self._index() + [successor["session"]]
        self.store.meta_set("session:index", json.dumps(index[-MAX_SESSIONS:]))
        self._audit({"event": "renewed", "at_ns": now, "session": successor["session"],
                     "parent": record["session"], "agent_id": record["agent_id"],
                     "build_id": record.get("build_id"), "renewals": successor["renewals"],
                     "expires_ns": successor["expires_ns"],
                     "deadline_ns": deadline})
        return {"session": successor["session"], "token": rotated,
                "expires_ns": successor["expires_ns"], "deadline_ns": deadline,
                "renewals": successor["renewals"],
                "renewals_left": max(0, int(successor["max_renewals"]) - successor["renewals"])}

    def revoke(self, token, reason="agent_finished"):
        record = self._load(token)
        now = self.clock()
        record["revoked_ns"] = now
        record["revoked_reason"] = str(reason)[:120]
        self.store.meta_set(f"session:{record['session']}", json.dumps(record, sort_keys=True))
        self._audit({"event": "revoked", "at_ns": now, "session": record["session"],
                     "agent_id": record["agent_id"], "reason": record["revoked_reason"]})
        return record

    # ------------------------------------------------------------------ proxy
    def call(self, token, method, path, body=None):
        """Perform one GitHub call on behalf of an agent, after checking identity and scope."""
        record = self.verify(token)
        method = str(method).upper()
        if method not in self._allowed(record):
            raise SessionError(f"method_not_allowed:{method}")
        if not isinstance(path, str) or not path.startswith(f"/repos/{self.repo}/"):
            raise SessionError("repo_not_pinned")
        status, payload = self.transport(method, path, body)
        now = self.clock()
        record["last_used_ns"] = now
        record["uses"] = int(record.get("uses", 0)) + 1
        self.store.meta_set(f"session:{record['session']}", json.dumps(record, sort_keys=True))
        self._audit({"event": "call", "at_ns": now, "session": record["session"],
                     "agent_id": record["agent_id"], "build_id": record["build_id"],
                     "method": method, "path": path[:200], "status": status})
        return status, payload

    @staticmethod
    def _allowed(record):
        allowed = set()
        for capability in record.get("capabilities", []):
            allowed |= set(CAPABILITIES.get(capability, frozenset()))
        return allowed

    # ------------------------------------------------------------------ audit
    def _audit(self, entry):
        if self.audit_path is None:
            return
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, sort_keys=True) + "\n")

    def audit(self, limit=200):
        if self.audit_path is None or not self.audit_path.is_file():
            return []
        lines = self.audit_path.read_text(encoding="utf-8").splitlines()[-limit:]
        entries = []
        for line in lines:
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue
        return entries

    def sessions(self):
        """Metadata only: the digest prefix identifies a session, the token is never returned."""
        found = []
        for session in self._index():
            raw = self.store.meta_get(f"session:{session}")
            if not raw:
                continue
            record = json.loads(raw)
            found.append({key: record.get(key) for key in
                          ("session", "agent_id", "build_id", "feature_id", "capabilities",
                           "issued_ns", "expires_ns", "absolute_expires_ns", "renewals",
                           "max_renewals", "last_used_ns", "uses", "revoked_ns")})
        return found
