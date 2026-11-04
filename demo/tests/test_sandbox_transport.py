"""Copy-out transport: sandbox writes stay inside the sandbox, results leave over exec."""
import base64
import json
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import sandbox as boundary


class MaterializeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def payload(self, text):
        return base64.b64encode(text.encode()).decode("ascii")

    def test_round_trips_files_into_the_destination(self):
        written = boundary.materialize(
            {"workspace/src/agent.js": self.payload("export function f() {}\n")}, self.root / "out")
        self.assertEqual(written, ["workspace/src/agent.js"])
        self.assertEqual((self.root / "out/workspace/src/agent.js").read_text(), "export function f() {}\n")

    def test_refuses_traversal(self):
        for bad in ("../escape.txt", "/etc/passwd", "a/../../b.txt", "a\\b.txt"):
            with self.subTest(path=bad), self.assertRaisesRegex(ValueError, "SANDBOX_SYNC_PATH"):
                boundary.materialize({bad: self.payload("x")}, self.root)

    def test_refuses_empty_relative_path(self):
        with self.assertRaisesRegex(ValueError, "SANDBOX_SYNC_PATH"):
            boundary.materialize({"": self.payload("x")}, self.root)

    def test_refuses_a_symlink_parent_in_the_destination(self):
        outside = self.root / 'outside'
        outside.mkdir()
        destination = self.root / 'destination'
        destination.mkdir()
        (destination / 'linked').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'SANDBOX_SYNC_PATH'):
            boundary.materialize({'linked/escape.txt': self.payload('no')}, destination)
        self.assertFalse((outside / 'escape.txt').exists())

    def test_collection_never_follows_a_sandbox_symlink(self):
        source = self.root / 'source'
        source.mkdir()
        (self.root / 'outside.txt').write_text('not an artifact')
        (source / 'link.txt').symlink_to(self.root / 'outside.txt')
        result = subprocess.run([sys.executable, '-c', boundary.COLLECT_SCRIPT,
                                 str(source), '1000'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('not an artifact', result.stdout)


class SyncOutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def sandbox_with(self, stdout, exit_code=0):
        class Fake(boundary.Sandbox):
            def __init__(self):
                self.closed = False

            def exec(self, command, **kwargs):
                self.command = command
                return SimpleNamespace(stdout=stdout, stderr="", exit_code=exit_code)
        return Fake()

    def test_sync_out_materializes_collected_files(self):
        payload = json.dumps({"workspace/src/agent.txt": base64.b64encode(b"from-sandbox").decode()})
        box = self.sandbox_with(payload)
        box.sync_out(self.root)
        self.assertEqual((self.root / "workspace/src/agent.txt").read_text(), "from-sandbox")
        self.assertEqual(box.command[0], "python3")

    def test_failed_collection_is_refused(self):
        box = self.sandbox_with("", exit_code=1)
        with self.assertRaisesRegex(ValueError, "SANDBOX_SYNC_FAILED"):
            box.sync_out(self.root)

    def test_unreadable_collection_is_refused(self):
        box = self.sandbox_with("not json")
        with self.assertRaisesRegex(ValueError, "SANDBOX_SYNC_UNREADABLE"):
            box.sync_out(self.root)

    def test_collect_script_is_bounded(self):
        self.assertIn("sync_too_large", boundary.COLLECT_SCRIPT)
        self.assertLessEqual(boundary.MAX_SYNC_BYTES, 64 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
