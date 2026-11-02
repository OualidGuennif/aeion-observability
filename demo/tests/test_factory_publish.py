import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.publish import FakeForge, Publisher, is_sensitive_path
from factory.publisher import independent_circuit
from factory.review import content_digest

FILES = {"demo/forum/product/x.md": "reviewed bytes\n"}
DIGEST = content_digest(FILES)


def request(**overrides):
    base = {
        "attempt_id": "a1", "issuer": "gate", "target_repo": "agora/forum",
        "base": "base1", "head": "head1", "artifact_digest": DIGEST,
        "reviewed_diff": sorted(FILES), "files": dict(FILES),
        "review_content_digest": DIGEST,
        "write_scopes": ["demo/forum/product/"], "cancelled": False,
    }
    base.update(overrides)
    return base


def with_path(path, text="reviewed bytes\n"):
    return {"reviewed_diff": [path], "files": {path: text},
            "artifact_digest": content_digest({path: text}),
            "review_content_digest": content_digest({path: text})}


class SensitivePathTests(unittest.TestCase):
    def test_markers(self):
        self.assertTrue(is_sensitive_path("demo/forum/product/auth/x.py"))
        self.assertTrue(is_sensitive_path("demo/forum/product/migrations/001.sql"))
        self.assertTrue(is_sensitive_path("demo/forum/product/deploy/x.yml"))
        self.assertTrue(is_sensitive_path("package.json"))
        self.assertTrue(is_sensitive_path("demo/forum/product/poetry.lock"))
        self.assertFalse(is_sensitive_path("demo/forum/product/app/views.py"))


class CircuitIndependenceTests(unittest.TestCase):
    def test_two_votes_from_one_family_are_not_independent(self):
        circuit = {"status": "approved", "votes": [
            {"model": "a", "family": "one"}, {"model": "b", "family": "one"}]}
        self.assertFalse(independent_circuit(circuit))
        circuit["votes"][1]["family"] = "two"
        self.assertTrue(independent_circuit(circuit))

    def test_missing_family_or_two_votes_is_not_independent(self):
        self.assertFalse(independent_circuit({"status": "approved", "votes": []}))
        self.assertFalse(independent_circuit({"status": "approved", "votes": [
            {"model": "a"}, {"model": "b", "family": "two"}]}))


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.forge = FakeForge()
        self.publisher = Publisher("agora/forum", self.forge, expected_base="base1",
                                   expected_artifact_digest=DIGEST)

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

    def decide_path(self, path):
        req = request(**with_path(path))
        publisher = Publisher("agora/forum", self.forge, expected_base="base1",
                              expected_artifact_digest=req["artifact_digest"])
        return publisher.decide(req)

    def test_refuses_out_of_scope_path(self):
        result = self.decide_path("demo/factory/x.py")
        self.assertEqual(result["reason"], "forbidden_path")

    def test_holds_stale_base(self):
        result = self.publisher.decide(request(base="stale"))
        self.assertEqual(result["decision"], "hold")
        self.assertEqual(result["reason"], "stale_base")

    def test_holds_sensitive_path_for_owner_review(self):
        result = self.decide_path("demo/forum/product/auth/x.py")
        self.assertEqual(result["decision"], "hold")
        self.assertEqual(result["reason"], "owner_review_required")

    def test_uncertain_result_is_reconciled_not_redone(self):
        forge = FakeForge(crash_on={"a1"})
        publisher = Publisher("agora/forum", forge, expected_base="base1",
                              expected_artifact_digest=DIGEST)
        result = publisher.decide(request())
        self.assertEqual(result["decision"], "reconciled")
        self.assertEqual(result["forge"]["status"], "published")
        self.assertEqual(len(forge.published), 1)

    def test_reconcile_absent(self):
        self.assertEqual(self.forge.reconcile("nope")["status"], "absent")

    def test_refuses_missing_content(self):
        result = self.publisher.decide(request(files={}))
        self.assertEqual(result["decision"], "refused")
        self.assertEqual(result["reason"], "missing_content")

    def test_refuses_a_path_set_that_does_not_match_the_files(self):
        result = self.publisher.decide(request(reviewed_diff=["demo/forum/product/other.md"]))
        self.assertEqual(result["decision"], "refused")
        self.assertEqual(result["reason"], "path_set_mismatch")

    def test_refuses_bytes_that_differ_from_the_reviewed_digest(self):
        # The attack: keep every receipt field, swap the queued bytes.
        result = self.publisher.decide(request(files={**FILES, "demo/forum/product/x.md": "tampered\n"}))
        self.assertEqual(result["decision"], "refused")
        self.assertEqual(result["reason"], "forged_content")
        self.assertNotIn("a1", self.forge.published)

    def test_refuses_a_forged_review_digest(self):
        result = self.publisher.decide(request(review_content_digest="other"))
        self.assertEqual(result["decision"], "refused")
        self.assertEqual(result["reason"], "forged_review")


if __name__ == "__main__":
    unittest.main()
