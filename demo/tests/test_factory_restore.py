import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.manifest import Catalog
from factory.restore import RestoreError, backup_db, drill, verify_db
from factory.store import SIMULATED_COMPLETE, Store


def feat(fid):
    return {
        "id": fid, "title": f"Feature {fid}", "area": "foundation", "size": "S",
        "parallel": False, "phase": "P0", "tier": 3,
        "write_paths": ["demo/forum/product/"], "depends_on": [], "file": f"{fid}.md",
    }


class RestoreDrillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cat = Catalog({"schema_version": 2, "count": 1, "features": [feat("001")]})
        self.db = self.root / "live" / "factory.db"
        self.store = Store(self.db)
        self.store.admit(["001"], "k1", self.cat)
        build = self.store.board()[0]
        self.store.claim_next(self.cat)
        self.store.complete_attempt(
            self.store.board()[0]["attempt_id"], build["cancellation_generation"],
            {"simulated": True, "artifact_digest": "dig"}, terminal=SIMULATED_COMPLETE,
        )

    def test_drill_restores_an_intact_copy(self):
        dest = self.root / "backup" / "factory.db"
        receipt = drill(self.db, dest)
        self.assertEqual(receipt["integrity"], "ok")
        self.assertEqual(receipt["builds"], 1)
        self.assertGreaterEqual(receipt["events"], 3)
        restored = Store(dest)
        self.assertEqual(restored.board()[0]["status"], SIMULATED_COMPLETE)
        self.assertEqual(restored.board()[0]["feature_id"], "001")

    def test_missing_source_is_refused(self):
        with self.assertRaisesRegex(RestoreError, "source_missing"):
            backup_db(self.root / "nope.db", self.root / "out.db")

    def test_corrupt_backup_is_refused(self):
        bad = self.root / "bad.db"
        bad.write_bytes(b"not a sqlite database at all")
        with self.assertRaises(RestoreError):
            verify_db(bad)

    def test_backup_without_factory_schema_is_refused(self):
        empty = self.root / "empty.db"
        conn = sqlite3.connect(empty)
        try:
            conn.execute("CREATE TABLE unrelated (x INTEGER)")
            conn.commit()
        finally:
            conn.close()
        with self.assertRaisesRegex(RestoreError, "missing_tables"):
            verify_db(empty)

    def test_backup_overwrites_a_stale_destination(self):
        dest = self.root / "backup" / "factory.db"
        dest.parent.mkdir(parents=True)
        dest.write_bytes(b"stale")
        receipt = drill(self.db, dest)
        self.assertEqual(receipt["builds"], 1)


if __name__ == "__main__":
    unittest.main()
