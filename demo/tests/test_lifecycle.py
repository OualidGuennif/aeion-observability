"""Campaign totals follow the executed plan; a restart never leaves the cockpit busy."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from lifecycle import plan, recover
from profiles import PROFILES
from scenarios import SCENARIOS


class PlanTests(unittest.TestCase):
    def test_every_task_and_profile_twice_in_rotated_order(self):
        with patch("lifecycle.available", return_value=True):
            steps = plan()
        self.assertEqual(len(steps), len(SCENARIOS) * len(PROFILES) * 2)
        self.assertEqual({(task, profile) for _, task, profile in steps},
                         {(task, profile) for task in SCENARIOS for profile in PROFILES})
        first, second = list(SCENARIOS)[:2]
        self.assertEqual(steps[0], (0, first, list(PROFILES)[0]))
        self.assertEqual(steps[len(PROFILES)], (0, second, list(PROFILES)[1]))

    def test_expired_profile_is_neither_planned_nor_counted(self):
        with patch("lifecycle.available", side_effect=lambda key: key != "deepseek"):
            steps = plan()
        self.assertEqual(len(steps), len(SCENARIOS) * (len(PROFILES) - 1) * 2)
        self.assertNotIn("deepseek", {profile for _, _, profile in steps})


class RecoveryTests(unittest.TestCase):
    def test_stopped_postprocessing_is_closed_once(self):
        report = {"status": "passed", "postprocessing": True, "memory": {"status": "pending"}}
        self.assertTrue(recover(report))
        self.assertEqual(report, {"status": "passed", "postprocessing": False, "memory": {"status": "interrupted"}})
        self.assertFalse(recover(report))

    def test_running_records_are_interrupted_and_finished_ones_untouched(self):
        running = {"status": "running", "postprocessing": True}
        self.assertTrue(recover(running))
        self.assertEqual(running["status"], "interrupted")
        finished = {"status": "passed", "postprocessing": False, "memory": {"status": "retained"}}
        self.assertFalse(recover(dict(finished)))
        campaign = {"status": "running", "run_ids": []}
        self.assertTrue(recover(campaign))
        self.assertEqual(campaign["status"], "interrupted")


if __name__ == "__main__":
    unittest.main()
