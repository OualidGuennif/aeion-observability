import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory import keys, queue
from factory.model_client import ModelClientError, complete


class CredentialSeparationTests(unittest.TestCase):
    def test_publish_credential_is_scrubbed_from_a_worker_environment(self):
        environ = {"GH_API_KEY": "x", "OPENCODE_API_KEY": "y"}
        removed = keys.scrub_publish_credentials(environ)
        self.assertEqual(removed, ["GH_API_KEY"])
        self.assertNotIn("GH_API_KEY", environ)
        self.assertEqual(environ, {"OPENCODE_API_KEY": "y"})

    def test_worker_with_a_publish_credential_fails_closed(self):
        with self.assertRaisesRegex(keys.CredentialError, "worker_holds_publish_credential"):
            keys.assert_worker_isolated({"GH_API_KEY": "x"})
        self.assertTrue(keys.assert_worker_isolated({"OPENCODE_API_KEY": "y"}))

    def test_capabilities_are_disjoint(self):
        self.assertEqual(keys.capabilities("GH_API_KEY"), {"publish"})
        self.assertEqual(keys.capabilities("OPENCODE_API_KEY"), {"inference"})
        self.assertEqual(keys.capabilities("unknown"), set())

    def test_app_settings_scrub_the_publish_credential(self):
        script = (
            "import sys; sys.path.insert(0, 'app'); import settings; "
            "import os; print('GH_API_KEY' in os.environ, settings.SCRUBBED_CREDENTIALS)"
        )
        env = dict(os.environ, GH_API_KEY="must-not-survive", AEION_LOCAL_DIR=tempfile.mkdtemp())
        out = subprocess.run([sys.executable, "-c", script], cwd=str(Path(__file__).resolve().parents[1]),
                             env=env, capture_output=True, text=True)
        self.assertIn("False", out.stdout)
        self.assertIn("GH_API_KEY", out.stdout)


class RoleTests(unittest.TestCase):
    """One GitHub key per capability: a role never borrows another role's key."""

    def test_each_credential_belongs_to_exactly_one_role(self):
        self.assertEqual(keys.role_of("GH_BUILD_KEY"), "build")
        self.assertEqual(keys.role_of("GH_API_KEY"), "publish")
        self.assertEqual(keys.role_of("GH_RELEASE_KEY"), "release")
        self.assertEqual(keys.role_of("OPENCODE_API_KEY"), "inference")
        self.assertEqual(keys.role_of("GH_TOKEN"), "publish")
        self.assertIsNone(keys.role_of("AWS_SECRET_ACCESS_KEY"))

    def test_a_role_reads_only_its_own_key(self):
        environ = {"GH_API_KEY": "publish-value", "GH_RELEASE_KEY": "release-value"}
        self.assertEqual(keys.for_role("publish", environ), ("GH_API_KEY", "publish-value"))
        self.assertEqual(keys.for_role("release", environ), ("GH_RELEASE_KEY", "release-value"))
        with self.assertRaisesRegex(keys.CredentialError, "credential_missing:build"):
            keys.for_role("build", environ)

    def test_a_process_refuses_a_role_it_does_not_need(self):
        with self.assertRaisesRegex(keys.CredentialError, "credential_role_conflict:release"):
            keys.assert_only("publish", {"GH_API_KEY": "a", "GH_RELEASE_KEY": "b"})
        self.assertTrue(keys.assert_only("publish", {"GH_API_KEY": "a"}))
        self.assertTrue(keys.assert_only({"build", "inference"},
                                         {"GH_BUILD_KEY": "a", "OPENCODE_API_KEY": "b"}))

    def test_a_worker_may_hold_the_build_key_but_never_the_release_key(self):
        self.assertTrue(keys.assert_worker_isolated({"GH_BUILD_KEY": "read-only"}))
        with self.assertRaisesRegex(keys.CredentialError, "worker_holds_publish_credential"):
            keys.assert_worker_isolated({"GH_RELEASE_KEY": "merge"})

    def test_publishing_scrubs_the_release_key_too(self):
        environ = {"GH_RELEASE_KEY": "r", "GH_API_KEY": "p", "OPENCODE_API_KEY": "i"}
        self.assertEqual(keys.scrub_publish_credentials(environ), ["GH_API_KEY", "GH_RELEASE_KEY"])
        self.assertEqual(environ, {"OPENCODE_API_KEY": "i"})

    def test_present_reports_roles_without_values(self):
        found = keys.present({"GH_BUILD_KEY": "build-secret-value",
                              "OPENCODE_API_KEY": "inference-secret-value"})
        self.assertEqual(found["build"], ["GH_BUILD_KEY"])
        self.assertEqual(found["inference"], ["OPENCODE_API_KEY"])
        self.assertEqual(found["publish"], [])
        self.assertEqual(keys.held_roles({"GH_RELEASE_KEY": "release-secret-value"}), ["release"])
        self.assertNotIn("secret-value", json.dumps(found))

    def test_the_env_example_names_every_credential_and_its_permissions(self):
        """The template is the owner's contract: it drifts only when this test lets it."""
        example = (Path(__file__).resolve().parents[2] / ".env.example").read_text()
        for row in keys.describe():
            self.assertIn(row["name"] + "=", example, row["name"])
            for permission in row["permissions"]:
                self.assertIn(permission, example, f"{row['name']} missing {permission}")
        # A template that carries a value would leak the placeholder into a real `.env`.
        for line in example.splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                self.assertEqual(line.split("=", 1)[1].strip(), "", line)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)

    def test_enqueue_then_drain(self):
        path = queue.enqueue(self.state, {"attempt_id": "a" * 32, "base": "x"})
        self.assertTrue(Path(path).is_file())
        self.assertEqual(len(queue.pending(self.state)), 1)
        request = queue.read(path)
        self.assertEqual(request["attempt_id"], "a" * 32)
        queue.done(self.state, path, {"decision": "published"})
        self.assertEqual(queue.pending(self.state), [])
        self.assertTrue((self.state / "publish-queue/done" / Path(path).name).is_file())

    def test_request_without_attempt_is_refused(self):
        with self.assertRaisesRegex(queue.QueueError, "missing_attempt_id"):
            queue.enqueue(self.state, {"base": "x"})

    def test_oversized_request_is_refused(self):
        with self.assertRaisesRegex(queue.QueueError, "request_too_large"):
            queue.enqueue(self.state, {"attempt_id": "b" * 32, "blob": "x" * (1024 * 1024 + 10)})


class ModelClientTests(unittest.TestCase):
    def test_unconfigured_endpoint_raises_instead_of_guessing(self):
        with patch.dict(os.environ, {"OPENCODE_API_KEY": ""}, clear=False):
            with self.assertRaisesRegex(ModelClientError, "review_endpoint_unconfigured"):
                complete("glm-5.3-flash", "prompt")

    def test_answer_is_parsed_from_a_fenced_block(self):
        def transport(url, payload, headers, timeout=60):
            return 200, {"choices": [{"message": {"content": '```json\n{"verdict":"approve","reason":"ok"}\n```'}}]}

        with patch.dict(os.environ, {"OPENCODE_API_KEY": "x"}):
            answer = complete("glm-5.3-flash", "prompt", transport=transport)
        self.assertEqual(answer["verdict"], "approve")

    def test_a_failed_call_raises(self):
        with patch.dict(os.environ, {"OPENCODE_API_KEY": "x"}):
            with self.assertRaisesRegex(ModelClientError, "review_call_failed"):
                complete("qwen-3.8-flash", "p", transport=lambda *a, **k: (500, {}))

    def test_malformed_answer_raises(self):
        def transport(url, payload, headers, timeout=60):
            return 200, {"choices": [{"message": {"content": "looks good to me"}}]}

        with patch.dict(os.environ, {"OPENCODE_API_KEY": "x"}):
            with self.assertRaisesRegex(ModelClientError, "no_json_answer"):
                complete("qwen-3.8-flash", "p", transport=transport)


if __name__ == "__main__":
    unittest.main()
