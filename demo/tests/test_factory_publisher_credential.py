"""The publisher's real credential loader must run, not raise NameError before any read."""
import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory import publisher
from factory.keys import CredentialError


class CredentialLoaderTests(unittest.TestCase):
    def test_loader_reads_the_publish_role(self):
        with mock.patch.dict(os.environ, {"GH_API_KEY": "publish-token"}, clear=True), \
                mock.patch("factory.gh_probe.load_secret", return_value=None):
            self.assertEqual(publisher.load_publish_credential(), "publish-token")

    def test_loader_fails_closed_without_a_publish_key(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch("factory.gh_probe.load_secret", return_value=None):
            with self.assertRaisesRegex(CredentialError, "credential_missing:publish"):
                publisher.load_publish_credential()

    def test_cli_reports_a_missing_credential_without_a_traceback(self):
        output = io.StringIO()
        with mock.patch.object(publisher, "present", return_value={"inference": [], "release": []}), \
                mock.patch.object(publisher, "load_publish_credential",
                                  side_effect=CredentialError("credential_missing:publish")), \
                contextlib.redirect_stdout(output):
            self.assertEqual(publisher.main(["--dry-run"]), 2)
        self.assertIn("credential_missing:publish", output.getvalue())


if __name__ == "__main__":
    unittest.main()
