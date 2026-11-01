"""Catalog regression checks. Spec: demo/forum/PLAN.md"""
import copy
import re
import unittest
from unittest.mock import patch

import generate_features as catalog


class CatalogTests(unittest.TestCase):
    def validate(self, mutate):
        specs = copy.deepcopy(catalog.SPECS)
        mutate({s["id"]: s for s in specs})
        with patch.object(catalog, "SPECS", specs):
            return catalog.validate()

    def test_current_catalog_is_valid(self):
        self.assertEqual(catalog.validate(), [])

    def test_forward_dependency_is_not_a_cycle(self):
        errors = self.validate(lambda s: s[16]["deps"].append(18))
        self.assertEqual(errors, [])

    def test_real_cycle_is_rejected(self):
        def mutate(s):
            s[16]["deps"].append(18)
            s[18]["deps"].append(16)
        self.assertTrue(any("cycle" in e for e in self.validate(mutate)))

    def test_unknown_dependency_is_rejected(self):
        errors = self.validate(lambda s: s[16]["deps"].append(101))
        self.assertTrue(any("unknown feature" in e for e in errors))

    def test_later_phase_dependency_is_rejected(self):
        errors = self.validate(lambda s: s[16]["deps"].append(77))
        self.assertTrue(any("later phase" in e for e in errors))

    def test_duplicate_identity_is_rejected(self):
        errors = self.validate(lambda s: s[100].update(id=99))
        self.assertTrue(any("exactly 001..100" in e for e in errors))

    def test_missing_tier_and_host_tier_are_rejected(self):
        for value in (None, 2):
            with self.subTest(tier=value):
                errors = self.validate(lambda s: s[16].update(tier=value))
                self.assertTrue(any("tier 3" in e for e in errors))

    def test_write_scopes_cannot_reach_factory_or_escape(self):
        paths = ["demo/app/runner.py", "demo/forum/product/../PLAN.md",
                 "demo/forum/product/.git/config", "demo/forum/product/**",
                 "/demo/forum/product/app.py", "demo/forum/product/app\\escape.py"]
        for path in paths:
            with self.subTest(path=path):
                errors = self.validate(lambda s: s[77].update(write_paths=[path]))
                self.assertTrue(any("write scopes" in e for e in errors))

    def test_parallel_feature_cannot_reserve_everything(self):
        errors = self.validate(lambda s: s[77].update(write_paths=[catalog.PRODUCT]))
        self.assertTrue(any("whole product" in e for e in errors))

    def test_four_categories_cannot_be_required_by_three_category_schema(self):
        errors = self.validate(lambda s: s[83]["required_categories"].append("fourth"))
        self.assertTrue(any("three schema categories" in e for e in errors))

    def test_parallel_features_have_disjoint_output_scopes(self):
        parallel = [s for s in catalog.SPECS if s["parallel"]]
        self.assertGreaterEqual(len(parallel), 2)
        for i, left in enumerate(parallel):
            for right in parallel[i + 1:]:
                for a in left["write_paths"]:
                    for b in right["write_paths"]:
                        overlap = a == b or (a.endswith("/") and b.startswith(a))
                        overlap |= b.endswith("/") and a.startswith(b)
                        self.assertFalse(overlap, (left["id"], right["id"], a, b))

    def test_submission_waits_for_mandatory_safety_controls(self):
        specs = {s["id"]: s for s in catalog.SPECS}
        def prerequisites(sid):
            result = set()
            for dep in specs[sid]["deps"]:
                result.add(dep)
                result.update(prerequisites(dep))
            return result
        self.assertTrue({7, 20, 42, 43, 48, 52, 56, 61, 66, 72, 96}
                        <= prerequisites(63))
        self.assertNotIn(63, prerequisites(21))

    def test_generated_contract_has_eight_spec_sections(self):
        expected = ["Intent", "Data sources", "Inputs", "Outputs", "Invariants",
                    "Determinism", "Acceptance checks", "Out of scope"]
        for spec in catalog.SPECS:
            sections = [line[3:] for line in catalog.render(spec).splitlines()
                        if line.startswith("## ")]
            self.assertEqual(sections, expected, spec["id"])

    def test_manifest_carries_dispatch_metadata(self):
        manifest = catalog.manifest()
        self.assertEqual(manifest["schema_version"], 2)
        self.assertEqual(len(manifest["features"]), 100)
        for feature in manifest["features"]:
            self.assertEqual(feature["tier"], 3)
            self.assertIn(feature["phase"], catalog.PHASES)
            self.assertTrue(feature["write_paths"])

    def test_review_snapshot_rebases_local_links(self):
        for name in ("PLAN.md", "ECOSYSTEM.md"):
            text = catalog.review_snapshot(name)
            for target in re.findall(r"\]\(([^\s)]+)\)", text):
                if re.match(r"(?:[a-z]+:|#|/)", target):
                    continue
                self.assertTrue((catalog.ROOT / "openAI" / target).exists(), (name, target))


if __name__ == "__main__":
    unittest.main()
