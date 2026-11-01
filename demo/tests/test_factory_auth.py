from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.auth import AdminSessions, host_origin_ok


class HostOriginTests(unittest.TestCase):
    def test_loopback_host_with_matching_origin(self):
        self.assertTrue(host_origin_ok("127.0.0.1:8088", "http://127.0.0.1:8088"))
        self.assertTrue(host_origin_ok("localhost", "http://localhost"))

    def test_loopback_host_without_origin_is_allowed(self):
        self.assertTrue(host_origin_ok("127.0.0.1"))

    def test_foreign_host_is_refused(self):
        self.assertFalse(host_origin_ok("evil.example.com", "http://evil.example.com"))

    def test_mismatched_origin_is_refused(self):
        self.assertFalse(host_origin_ok("127.0.0.1:8088", "http://evil.example.com"))
        self.assertFalse(host_origin_ok("127.0.0.1:8088", "http://127.0.0.1:9999"))


class AdminSessionTests(unittest.TestCase):
    def setUp(self):
        self.auth = AdminSessions(bootstrap_token="bootstrap-secret")

    def test_wrong_token_is_refused(self):
        self.assertIsNone(self.auth.login("wrong"))

    def test_correct_token_mints_session_and_rotates(self):
        first = self.auth.login("bootstrap-secret")
        self.assertIn("session_id", first)
        self.assertIn("csrf", first)
        # The old bootstrap token is now single-use.
        self.assertIsNone(self.auth.login("bootstrap-secret"))

    def test_authenticate_valid_session(self):
        first = self.auth.login("bootstrap-secret")
        self.assertEqual(self.auth.authenticate(first["session_id"], now_ns=0)["csrf"], first["csrf"])

    def test_authenticate_missing_or_wrong_session(self):
        self.auth.login("bootstrap-secret")
        self.assertIsNone(self.auth.authenticate("nope", now_ns=0))
        self.assertIsNone(self.auth.authenticate(None, now_ns=0))

    def test_idle_expiry(self):
        first = self.auth.login("bootstrap-secret")
        self.assertIsNotNone(self.auth.authenticate(first["session_id"], now_ns=0))
        # Jump past the idle window.
        self.assertIsNone(self.auth.authenticate(first["session_id"], now_ns=self.auth.idle_ns + 1))

    def test_absolute_expiry(self):
        first = self.auth.login("bootstrap-secret", now_ns=0)
        self.assertIsNone(self.auth.authenticate(first["session_id"], now_ns=self.auth.absolute_ns + 1))

    def test_csrf_must_match(self):
        first = self.auth.login("bootstrap-secret")
        session = self.auth.authenticate(first["session_id"], now_ns=0)
        self.assertTrue(self.auth.check_csrf(session, first["csrf"]))
        self.assertFalse(self.auth.check_csrf(session, "wrong"))
        self.assertFalse(self.auth.check_csrf(session, None))

    def test_logout_invalidates(self):
        first = self.auth.login("bootstrap-secret")
        self.auth.logout(first["session_id"])
        self.assertIsNone(self.auth.authenticate(first["session_id"], now_ns=0))


if __name__ == "__main__":
    unittest.main()
