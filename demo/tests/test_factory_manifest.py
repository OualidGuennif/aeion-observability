import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog, ManifestError, load_manifest

MANIFEST = Path(__file__).resolve().parents[1] / "forum/features/MANIFEST.json"


def feature(fid, depends_on=(), phase="P0", **overrides):
    base = {
        "id": fid,
        "title": f"Feature {fid}",
        "area": "foundation",
        "size": "S",
        "parallel": False,
        "phase": phase,
        "tier": 3,
        "write_paths": ["demo/forum/product/"],
        "depends_on": list(depends_on),
        "file": f"{fid}-feature.md",
    }
    base.update(overrides)
    return base


def catalog(features):
    return {"schema_version": 2, "count": len(features), "features": features}


class ManifestTests(unittest.TestCase):
    def test_real_manifest_loads_with_100_features(self):
        cat = load_manifest(MANIFEST)
        self.assertEqual(cat.schema_version, 2)
        self.assertEqual(len(cat.features), 100)
        self.assertEqual(len(cat.by_id), 100)
        self.assertEqual(cat.by_id["001"]["tier"], 3)

    def test_digest_is_stable_across_key_order(self):
        a = Catalog(catalog([feature("001"), feature("002", depends_on=["001"])]))
        reordered = catalog([
            {"file": "002-feature.md", "depends_on": ["001"], "write_paths": ["demo/forum/product/"],
             "tier": 3, "phase": "P0", "parallel": False, "size": "S", "area": "foundation",
             "title": "Feature 002", "id": "002"},
            {"file": "001-feature.md", "depends_on": [], "write_paths": ["demo/forum/product/"],
             "tier": 3, "phase": "P0", "parallel": False, "size": "S", "area": "foundation",
             "title": "Feature 001", "id": "001"},
        ])
        self.assertEqual(a.digest, Catalog(reordered).digest)

    def test_unsupported_schema_rejected(self):
        bad = catalog([feature("001")])
        bad["schema_version"] = 99
        with self.assertRaisesRegex(ManifestError, "unsupported_schema_version"):
            Catalog(bad)

    def test_count_mismatch_rejected(self):
        bad = catalog([feature("001")])
        bad["count"] = 5
        with self.assertRaisesRegex(ManifestError, "feature_count_mismatch"):
            Catalog(bad)

    def test_missing_fields_rejected(self):
        bad = catalog([{"id": "001"}])
        with self.assertRaisesRegex(ManifestError, "feature_missing_fields"):
            Catalog(bad)

    def test_unknown_dependency_rejected(self):
        bad = catalog([feature("001", depends_on=["999"])])
        with self.assertRaisesRegex(ManifestError, "unknown_dependency"):
            Catalog(bad)

    def test_real_cycle_rejected(self):
        bad = catalog([feature("001", depends_on=["002"]), feature("002", depends_on=["001"])])
        with self.assertRaisesRegex(ManifestError, "cycle"):
            Catalog(bad)

    def test_later_phase_dependency_rejected(self):
        bad = catalog([feature("001", phase="P2"), feature("002", phase="P1", depends_on=["001"])])
        with self.assertRaisesRegex(ManifestError, "later_phase_dependency"):
            Catalog(bad)

    def test_invalid_tier_rejected(self):
        bad = catalog([feature("001", tier=2)])
        with self.assertRaisesRegex(ManifestError, "invalid_tier"):
            Catalog(bad)

    def test_write_path_traversal_rejected(self):
        for path in ("/etc/passwd", "../sibling", "a/../../b", "demo\\forum"):
            bad = catalog([feature("001", write_paths=["demo/forum/product/", path])])
            with self.subTest(path=path), self.assertRaisesRegex(ManifestError, "invalid_write_paths"):
                Catalog(bad)

    def test_missing_dependencies_computed_against_merged(self):
        cat = Catalog(catalog([feature("001"), feature("002", depends_on=["001"])]))
        self.assertEqual(cat.missing_dependencies("002", set()), ["001"])
        self.assertEqual(cat.missing_dependencies("002", {"001"}), [])


if __name__ == "__main__":
    unittest.main()
