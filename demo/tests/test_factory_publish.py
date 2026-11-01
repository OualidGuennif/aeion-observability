import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.publish import FakeForge, Publisher, is_sensitive_path


def request(**overrides):
    base = {
        "attempt_id": "a1", "issuer": "gate", "target_repo": "agora/forum",
        "base": "base1", "head": "head1", "artifact_digest": "dig1",
        "reviewed_diff": ["demo/forum/product/x.md"],
        "write_scopes": ["demo/forum/product/"], "cancelled": False,
    }
    base.update(overrides)
    return base


class SensitivePathTests(unittest.TestCase):
    def test_markers(self):
        self.assertTrue(is_sensitive_path("demo/forum/product/auth/x.py"))
        self.assertTrue(is_sensitive_path("demo/forum/product/migrations/001.sql"))
        self.assertTrue(is_sensitive_path("demo/forum/product/deploy/x.yml"))
        self.assertTrue(is_sensitive_path("package.json"))
        self.assertTrue(is_sensitive_path("demo/forum/product/poetry.lock"))
        self.assertFalse(is_sensitive_path("demo/forum/product/app/views.py"))


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.forge = FakeForge()
        self.publisher = Publisher("agora/forum", self.forge, expected_base="base1",
                                   expected_artifact_digest="dig1")

    def test_publishes_permitted_request(self):
        result = self.publisher.decide(request())
        self.assertEqual(result["decision"], "published")
        self.assertTrue(result["forge"]["pr"]["merged"])
        self.assertIn("a1", self.forge.published)

    def test_refuses_forged_issuer(self):
        result = self.publisher.decide(request(issuer="builder"))
        self.assertEqual(result["decision"], "refused")
        self.assertEqual(result["reason"], "forged_issuer")

    def test_refuses_forbidden_target(self):
        result = self.publisher.decide(request(target_repo="other/repo"))
        self.assertEqual(result["reason"], "forbidden_target")

    def test_refuses_cancelled(self):
        result = self.publisher.decide(request(cancelled=True))
        self.assertEqual(result["reason"], "cancelled")

    def test_refuses_forged_receipt(self):
        result = self.publisher.decide(request(artifact_digest="other"))
        self.assertEqual(result["reason"], "forged_receipt")

    def test_refuses_out_of_scope_path(self):
        result = self.publisher.decide(request(reviewed_diff=["demo/factory/x.py"]))
        self.assertEqual(result["reason"], "forbidden_path")

    def test_holds_stale_base(self):
        result = self.publisher.decide(request(base="stale"))
        self.assertEqual(result["decision"], "hold")
        self.assertEqual(result["reason"], "stale_base")

    def test_holds_sensitive_path_for_owner_review(self):
        result = self.publisher.decide(request(reviewed_diff=["demo/forum/product/auth/x.py"]))
        self.assertEqual(result["decision"], "hold")
        self.assertEqual(result["reason"], "owner_review_required")

    def test_uncertain_result_is_reconciled_not_redone(self):
        forge = FakeForge(crash_on={"a1"})
        publisher = Publisher("agora/forum", forge, expected_base="base1",
                              expected_artifact_digest="dig1")
        result = publisher.decide(request())
        self.assertEqual(result["decision"], "reconciled")
        self.assertEqual(result["forge"]["status"], "published")
        self.assertEqual(len(forge.published), 1)

    def test_reconcile_absent(self):
        self.assertEqual(self.forge.reconcile("nope")["status"], "absent")


if __name__ == "__main__":
    unittest.main()
