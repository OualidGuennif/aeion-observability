import importlib.util
from pathlib import Path
import unittest
import sys

spec = importlib.util.spec_from_file_location("policy", Path(__file__).resolve().parents[1] / "app/policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from json_input import loads


class NativeUsageTests(unittest.TestCase):
    def test_ambiguous_json_is_refused(self):
        for raw in ('{"max_tokens":1,"max_tokens":500000}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                loads(raw)
    def part(self):
        return {"input": 1000, "cacheRead": 249000, "cacheWrite": 0, "output": 120, "cost": 0.001}

    def test_disjoint_cache_and_output(self):
        usage = policy.native_usage(self.part())
        self.assertEqual(usage["input"], 250000)
        self.assertEqual(usage["output"], 120)
        self.assertEqual(policy.gate_value(usage, 400000, "active_context"), 250000)

    def test_unknown_is_not_zero(self):
        for invalid in (None, True, -1, 1.2):
            part = self.part()
            part["input"] = invalid
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "USAGE_UNKNOWN"):
                policy.native_usage(part)
        with self.assertRaisesRegex(ValueError, "USAGE_UNKNOWN"):
            policy.native_usage(None)

    def test_invalid_cost_stops(self):
        for invalid in ("0.001", float("nan"), float("inf"), -1, None, True):
            part = self.part()
            part["cost"] = invalid
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "COST_UNKNOWN"):
                policy.native_usage(part)

    def test_missing_cache_is_unknown(self):
        part = self.part()
        del part["cacheRead"]
        with self.assertRaisesRegex(ValueError, "USAGE_UNKNOWN"):
            policy.native_usage(part)


if __name__ == "__main__":
    unittest.main()
