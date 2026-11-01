"""Release endpoints: staging, validate, advance, deploy-now, rollback, flags, sessions."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.api import ApiError, FactoryApp

HOST, ORIGIN = "127.0.0.1:8088", "http://127.0.0.1:8088"
FEATURES = [{"id": "001", "title": "App skeleton", "digest": "a" * 64},
            {"id": "002", "title": "Settings", "digest": "b" * 64}]


def write_manifest(path):
    path.write_text(json.dumps({
        "schema_version": 2, "count": 1,
        "features": [{"id": "001", "title": "App skeleton", "area": "foundation", "size": "S",
                      "parallel": False, "phase": "P0", "tier": 3,
                      "write_paths": ["demo/forum/product/"], "depends_on": [], "file": "001.md"}],
    }))


class ReleaseApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        manifest = self.root / "MANIFEST.json"
        write_manifest(manifest)
        (self.root / "001.md").write_text("# 001\n")
        self.app = FactoryApp(manifest, self.root / "state", bootstrap_token="secret")
        self.addCleanup(lambda: self.app.playground and self.app.playground.stop())
        _, body, headers = self.app.login(HOST, ORIGIN, {"token": "secret"})
        self.csrf = body["csrf"]
        self.session = self.app.authenticate(headers["Set-Cookie"].split(";")[0])

    def action(self, **body):
        return self.app.release_action(HOST, ORIGIN, self.session, self.csrf, body)

    def test_a_fresh_board_has_no_release(self):
        status, view, _ = self.app.releases_view(self.session)
        self.assertEqual(status, 200)
        self.assertIsNone(view["release"])
        self.assertIn("staging", view["endpoints"])

    def test_stage_validate_and_read_the_gate(self):
        status, view, _ = self.action(action="stage", features=FEATURES,
                                      flags={"dark_mode": {"enabled": True, "rollout": 50}})
        self.assertEqual(status, 200)
        self.assertEqual(view["release"]["state"], "staged")
        release_id = view["release"]["release_id"]
        status, view, _ = self.action(action="validate", release_id=release_id)
        self.assertEqual(view["release"]["state"], "canary")
        self.assertEqual(view["release"]["percent"], 25)
        self.assertIn(view["release"]["gate"]["verdict"], {"insufficient", "hold", "continue"})
        self.assertEqual(view["release"]["flags"]["dark_mode"]["rollout"], 50)

    def test_advance_is_refused_while_the_evidence_is_missing(self):
        """The gate is checked before the dwell: no traffic yet is not a reason to widen."""
        self.action(action="stage", features=FEATURES)
        self.action(action="validate")
        with self.assertRaises(ApiError) as caught:
            self.action(action="advance")
        self.assertEqual(caught.exception.status, 409)
        self.assertIn("gate_blocks_advance:insufficient", caught.exception.code)

    def test_immediate_full_deploy_reaches_100(self):
        self.action(action="stage", features=FEATURES)
        _, view, _ = self.action(action="deploy_now")
        self.assertEqual(view["release"]["percent"], 100)
        self.assertEqual(view["release"]["state"], "released")

    def test_rollback_and_flag_changes_are_visible(self):
        self.action(action="stage", features=FEATURES,
                    flags={"search": {"enabled": True, "rollout": 10}})
        self.action(action="validate")
        _, view, _ = self.action(action="flag", name="search", enabled=False)
        self.assertFalse(view["release"]["flags"]["search"]["enabled"])
        _, view, _ = self.action(action="rollback", reason="owner")
        self.assertEqual(view["release"]["state"], "rolled_back")
        self.assertEqual(view["release"]["percent"], 0)

    def test_an_unknown_action_is_refused(self):
        self.action(action="stage", features=FEATURES)
        with self.assertRaises(ApiError) as caught:
            self.action(action="nuke")
        self.assertEqual(caught.exception.status, 400)

    def test_a_mutation_without_csrf_is_refused(self):
        with self.assertRaises(ApiError) as caught:
            self.app.release_action(HOST, ORIGIN, self.session, "wrong", {"action": "stage",
                                                                         "features": FEATURES})
        self.assertEqual(caught.exception.status, 403)

    def test_an_agent_session_is_issued_and_listed_without_its_token(self):
        status, body, _ = self.app.sessions(HOST, ORIGIN, self.session, self.csrf,
                                            {"action": "issue", "agent_id": "agent-1",
                                             "build_id": "build-1", "feature_id": "001"})
        self.assertEqual(status, 200)
        self.assertTrue(body["issued"]["token"].startswith("aeion_"))
        self.assertEqual(body["issued"]["capabilities"], ["github:read"])
        _, view, _ = self.app.releases_view(self.session)
        self.assertEqual(view["sessions"][-1]["agent_id"], "agent-1")
        self.assertNotIn(body["issued"]["token"], json.dumps(view["sessions"]))

    def test_a_revoked_session_cannot_be_used(self):
        _, body, _ = self.app.sessions(HOST, ORIGIN, self.session, self.csrf,
                                       {"action": "issue", "agent_id": "agent-2", "build_id": "build-2"})
        token = body["issued"]["token"]
        self.app.sessions(HOST, ORIGIN, self.session, self.csrf,
                          {"action": "revoke", "token": token})
        gateway = self.app._gateway()
        from factory.gateway import SessionError

        with self.assertRaisesRegex(SessionError, "session_revoked"):
            gateway.verify(token)


if __name__ == "__main__":
    unittest.main()
