"""The cockpit receipt must expose the build identity and its Langfuse trace."""
import sys
import unittest
from pathlib import Path

JS = (Path(__file__).resolve().parents[1] / "app/factory.js").read_text()


class BoardLinkTests(unittest.TestCase):
    def test_receipt_summary_shows_build_attempt_and_trace(self):
        self.assertIn("r.build_id", JS)
        self.assertIn("r.attempt_id", JS)
        self.assertIn("r.telemetry.trace_id", JS)
        self.assertIn("LANGFUSE_UI", JS)
        self.assertIn("/trace/", JS)
        self.assertIn("encodeURIComponent(trace)", JS)

    def test_the_trace_link_opens_away_from_the_cockpit(self):
        self.assertIn('target="_blank"', JS)
        self.assertIn('rel="noreferrer"', JS)

    def test_build_identifiers_are_escaped(self):
        self.assertIn("esc(String(r.build_id)", JS)
        self.assertIn("esc(String(r.attempt_id)", JS)


if __name__ == "__main__":
    unittest.main()
