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

    def test_execution_order_is_complete_stable_and_respects_every_dependency(self):
        ordered = catalog.execution_order()
        self.assertEqual(len(ordered), 100)
        positions = {s['id']: i for i, s in enumerate(ordered)}
        for item in ordered:
            for dep in item['deps']:
                self.assertLess(positions[dep], positions[item['id']])
        self.assertEqual([s['id'] for s in ordered], [s['id'] for s in catalog.execution_order()])
        self.assertEqual(sorted(positions), list(range(1, 101)))

    def test_each_feature_has_a_short_delivery_recipe(self):
        for spec in catalog.SPECS:
            self.assertEqual(len(spec['delivery']), 3, spec['id'])
            rendered = catalog.render(spec)
            self.assertLessEqual(len(rendered.split()), 900, spec['id'])
            self.assertIn('**Delivery steps:**', rendered)
        errors = self.validate(lambda s: s[63].update(delivery=[]))
        self.assertTrue(any('delivery steps' in e for e in errors))

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
        paths = ["demo/app/runner.py", "demo/forum-app/../PLAN.md",
                 "demo/forum-app/.git/config", "demo/forum-app/**",
                 "/demo/forum-app/app.py", "demo/forum-app/app\\escape.py",
                 "demo/forum-app/./x.java", "demo/forum-app//x.java",
                 "demo/forum-mobile/App.tsx", "demo/forum/product/app.py"]
        for path in paths:
            with self.subTest(path=path):
                errors = self.validate(lambda s: s[77].update(write_paths=[path]))
                self.assertTrue(any("write scopes" in e for e in errors))

    def test_parallel_feature_cannot_reserve_everything(self):
        errors = self.validate(lambda s: s[77].update(parallel=True,write_paths=[catalog.PRODUCT_ROOTS[0]]))
        self.assertTrue(any("whole product" in e for e in errors))

    def test_overlapping_parallel_outputs_are_rejected_by_generator(self):
        errors = self.validate(lambda s: (s[77].update(parallel=True),s[82].update(parallel=True,write_paths=s[77]['write_paths'])))
        self.assertTrue(any('overlap' in e for e in errors))

    def test_old_framework_requirement_is_rejected(self):
        for stale in ('Create a FastAPI app', 'Use a pytest fixture', 'Use extra=forbid',
                      'Every page works without JavaScript'):
            with self.subTest(stale=stale):
                errors = self.validate(lambda s: s[14].update(goal=stale))
                self.assertTrue(any('superseded application stack' in e for e in errors))

    def test_every_contract_freezes_the_common_architecture(self):
        digest = catalog.architecture_digest()
        for spec, feature in zip(catalog.SPECS, catalog.manifest()['features']):
            text = catalog.render(spec)
            self.assertIn('architecture_digest: ' + digest, text)
            self.assertEqual(feature['architecture'], catalog.ARCHITECTURE)
            self.assertEqual(feature['architecture_digest'], digest)
            self.assertIn('Quarkus/Java + PostgreSQL', text)

    def test_database_and_browser_foundations_match_owner_decision(self):
        specs = {s['id']: s for s in catalog.SPECS}
        self.assertIn('PostgreSQL', specs[2]['title'])
        self.assertIn('SQLite', specs[2]['title'])  # explicit data migration, never silently skipped
        self.assertIn('React browser', specs[14]['title'])
        self.assertIn('JUnit', ' '.join(specs[3]['scope']))
        self.assertTrue(all(p.startswith(catalog.PRODUCT_ROOTS)
                            for s in specs.values() for p in s['write_paths']))

    def test_four_categories_cannot_be_required_by_three_category_schema(self):
        errors = self.validate(lambda s: s[83]["required_categories"].append("fourth"))
        self.assertTrue(any("three schema categories" in e for e in errors))

    def test_shared_product_documentation_requires_serial_feature_builds(self):
        for spec in catalog.SPECS:
            self.assertFalse(spec['parallel'])
            self.assertIn('knowledge/components/agora-product.md',spec['write_paths'])
            self.assertIn('knowledge/components/factory-architecture.md',spec['write_paths'])

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
