"""The build agent stops on its branch: the boundary is written once and copied on purpose."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory import boundary

DEMO = Path(__file__).resolve().parents[1]


class BoundaryTests(unittest.TestCase):
    def test_the_coder_agent_carries_every_rule_verbatim(self):
        coder = (DEMO / "flue/src/agents/coder.ts").read_text()
        for rule in boundary.RULES:
            self.assertIn(rule, coder)
        self.assertIn(boundary.STOP, coder)

    def test_the_brief_names_the_branch_and_ends_with_a_stop(self):
        brief = boundary.build_brief("001", "App skeleton", "aeion/build-1234")
        self.assertIn("Feature 001: App skeleton", brief)
        self.assertIn("aeion/build-1234", brief)
        self.assertIn(boundary.STOP, brief)
        self.assertTrue(brief.rstrip().endswith(boundary.STOP))

    def test_the_contract_forbids_the_three_actions_that_would_break_the_circuit(self):
        text = boundary.contract().lower()
        for verb in ("push nothing", "open no pull request", "never review your own work"):
            self.assertIn(verb, text)

    def test_rules_are_numbered_and_imperative(self):
        lines = boundary.contract().splitlines()
        self.assertEqual(len(lines), len(boundary.RULES))
        for number, line in enumerate(lines, start=1):
            self.assertTrue(line.startswith(f"{number}. "), line)
            self.assertTrue(line.endswith("."), line)


if __name__ == "__main__":
    unittest.main()
