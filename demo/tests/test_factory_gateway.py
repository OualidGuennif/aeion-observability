"""The authentication gateway: short-lived agent sessions, pinned scope, audited calls."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.gateway import Gateway, SessionError
from factory.store import Store

REPO = "OualidGuennif/aeion-autonomous-forum"


class FakeGitHub:
    def __init__(self):
        self.calls = []

    def __call__(self, method, path, body):
        self.calls.append((method, path, body))
        return 200, {"ok": True, "path": path}


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / "factory.db")
        self.github = FakeGitHub()
        self.now = 1_700_000_000_000_000_000
        self.gateway = Gateway(self.store, self.github, REPO, ttl_seconds=600,
                               clock=lambda: self.now, audit_path=self.root / "audit.jsonl")

    def session(self, **kwargs):
        return self.gateway.issue("agent-1", "build-1", feature_id="001", **kwargs)

    def test_a_session_is_issued_once_and_stored_only_as_a_digest(self):
        issued = self.session()
        self.assertTrue(issued["token"].startswith("aeion_"))
        self.assertEqual(issued["capabilities"], ["github:read"])
        self.assertEqual(len(issued["session"]), 32)
        stored = self.store.meta_get(f"session:{issued['session']}")
        self.assertIsNotNone(stored)
        self.assertNotIn(issued["token"], stored)

    def test_a_session_expires(self):
        issued = self.session(ttl_seconds=60)
        self.now += 59 * 1_000_000_000
        self.assertEqual(self.gateway.verify(issued["token"])["agent_id"], "agent-1")
        self.now += 2 * 1_000_000_000
        with self.assertRaisesRegex(SessionError, "session_expired"):
            self.gateway.verify(issued["token"])

    def test_revocation_is_immediate(self):
        issued = self.session()
        self.gateway.revoke(issued["token"], reason="build_finished")
        with self.assertRaisesRegex(SessionError, "session_revoked"):
            self.gateway.verify(issued["token"])

    def test_an_agent_may_read_but_never_write(self):
        issued = self.session()
        status, payload = self.gateway.call(issued["token"], "GET", f"/repos/{REPO}/contents/README.md")
        self.assertEqual(status, 200)
        for method in ("PUT", "POST", "PATCH", "DELETE"):
            with self.assertRaisesRegex(SessionError, "method_not_allowed"):
                self.gateway.call(issued["token"], method, f"/repos/{REPO}/contents/x")

    def test_a_token_cannot_reach_another_repository(self):
        issued = self.session()
        with self.assertRaisesRegex(SessionError, "repo_not_pinned"):
            self.gateway.call(issued["token"], "GET", "/repos/someone/else/contents/README.md")

    def test_a_malformed_or_unknown_token_is_refused(self):
        for token in ("", "ghp_secret", "aeion_not-a-real-session"):
            with self.assertRaises(SessionError):
                self.gateway.verify(token)

    def test_every_call_is_audited_with_the_agent_identity(self):
        issued = self.session()
        self.gateway.call(issued["token"], "GET", f"/repos/{REPO}/contents/README.md")
        entries = self.gateway.audit()
        self.assertEqual([entry["event"] for entry in entries], ["issued", "call"])
        self.assertEqual(entries[-1]["agent_id"], "agent-1")
        self.assertEqual(entries[-1]["status"], 200)
        self.assertNotIn(issued["token"], json.dumps(entries))

    def test_an_unknown_capability_is_refused_at_issue(self):
        with self.assertRaisesRegex(SessionError, "unknown_capability:github:god"):
            self.gateway.issue("agent-1", "build-1", capabilities=("github:god",))

    def test_a_write_capability_must_be_asked_for_explicitly(self):
        issued = self.session(capabilities=("github:read", "github:write"))
        status, _ = self.gateway.call(issued["token"], "PUT", f"/repos/{REPO}/contents/x")
        self.assertEqual(status, 200)
        default = self.session()
        with self.assertRaisesRegex(SessionError, "method_not_allowed"):
            self.gateway.call(default["token"], "PUT", f"/repos/{REPO}/contents/x")

    def test_sessions_listing_carries_no_token(self):
        self.session()
        listing = self.gateway.sessions()
        self.assertEqual(len(listing), 1)
        self.assertEqual(listing[0]["agent_id"], "agent-1")
        self.assertNotIn("token", json.dumps(listing))

    def renew_later(self, token, seconds):
        self.now += seconds * 1_000_000_000
        return self.gateway.renew(token)

    def test_a_renewal_rotates_the_token_and_kills_the_old_one(self):
        issued = self.session(ttl_seconds=900)
        renewed = self.renew_later(issued["token"], 600)
        self.assertNotEqual(renewed["token"], issued["token"])
        self.assertEqual(renewed["renewals"], 1)
        self.assertEqual(renewed["renewals_left"], 2)
        self.gateway.verify(renewed["token"])
        with self.assertRaisesRegex(SessionError, "session_revoked"):
            self.gateway.verify(issued["token"])

    def test_an_early_renewal_wastes_no_budget(self):
        issued = self.session(ttl_seconds=900)
        with self.assertRaisesRegex(SessionError, "renewal_too_early"):
            self.renew_later(issued["token"], 60)

    def test_a_late_build_may_renew_inside_the_grace_window(self):
        issued = self.session(ttl_seconds=900)
        renewed = self.renew_later(issued["token"], 900 + 60)
        self.assertEqual(renewed["renewals"], 1)

    def test_after_the_grace_window_the_session_is_gone(self):
        issued = self.session(ttl_seconds=900)
        with self.assertRaisesRegex(SessionError, "session_expired"):
            self.renew_later(issued["token"], 900 + 600)

    def test_three_renewals_then_the_budget_is_exhausted(self):
        issued = self.session(ttl_seconds=900)
        token = issued["token"]
        for expected in (1, 2, 3):
            token = self.renew_later(token, 600)["token"]
            self.assertEqual(self.gateway.verify(token)["renewals"], expected)
        with self.assertRaisesRegex(SessionError, "renewal_budget_exhausted"):
            self.renew_later(token, 600)

    def test_a_session_never_lives_past_its_absolute_deadline(self):
        issued = self.session(ttl_seconds=900)
        record = self.gateway.verify(issued["token"])
        self.assertEqual(record["absolute_expires_ns"] - record["issued_ns"], 4 * 900 * 1_000_000_000)
        token = issued["token"]
        for _ in range(3):
            token = self.renew_later(token, 600)["token"]
        self.assertLessEqual(self.gateway.verify(token)["expires_ns"],
                             record["absolute_expires_ns"])

    def test_an_idle_session_is_not_kept_alive(self):
        issued = self.session(ttl_seconds=900)
        self.gateway.call(issued["token"], "GET", f"/repos/{REPO}/contents/README.md")
        record = self.gateway.verify(issued["token"])
        self.now = int(record["last_used_ns"]) + 1200 * 1_000_000_000
        record["expires_ns"] = self.now + 600 * 1_000_000_000
        self.store.meta_set(f"session:{record['session']}", json.dumps(record, sort_keys=True))
        with self.assertRaisesRegex(SessionError, "session_idle"):
            self.gateway.renew(issued["token"])

    def test_renewals_are_audited_as_a_chain(self):
        issued = self.session(ttl_seconds=900)
        first = self.renew_later(issued["token"], 600)
        self.renew_later(first["token"], 600)
        entries = [e for e in self.gateway.audit() if e["event"] == "renewed"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["parent"], issued["session"])
        self.assertEqual(entries[1]["parent"], first["session"])
        self.assertEqual([e["renewals"] for e in entries], [1, 2])

    def test_the_ttl_is_capped(self):
        issued = self.gateway.issue("agent-1", "build-1", ttl_seconds=10 ** 6)
        self.assertLessEqual(issued["expires_ns"] - self.now, 3600 * 1_000_000_000)


if __name__ == "__main__":
    unittest.main()
