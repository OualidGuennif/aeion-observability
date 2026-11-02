"""The obsolete Deno/Hono demo stays deleted; no active surface may point at it again."""
import unittest
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1]


class PlaygroundRemovedTests(unittest.TestCase):
    def test_the_old_application_directory_is_gone(self):
        self.assertFalse((DEMO / "playground").exists())

    def test_no_playground_service_is_configured(self):
        settings = (DEMO / "app" / "settings.py").read_text()
        self.assertNotIn('"playground"', settings)

    def test_compose_has_no_playground_service(self):
        compose = (DEMO / "compose.yaml").read_text()
        self.assertNotIn("\n  playground:", compose)
        self.assertNotIn("8090", compose)

    def test_the_cockpit_does_not_link_the_old_port(self):
        cockpit = (DEMO / "app" / "index.html").read_text()
        self.assertNotIn("8090", cockpit)
        self.assertIn('href="/factory"', cockpit)

    def test_the_backend_verifier_no_longer_requires_a_deno_span(self):
        verifier = (DEMO / "verify_backend.py").read_text()
        self.assertNotIn("aeion-deno-playground", verifier)
        self.assertNotIn("deno_trace_join", verifier)


if __name__ == "__main__":
    unittest.main()
