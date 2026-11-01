#!/usr/bin/env python3
# Spec: knowledge/operations/architecture-maintenance.md
"""Regression tests for the single-file diagram gallery: inlining, order, escaping and refusals."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "gallery"


class GalleryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.render = Path(self.tmp.name)
        (self.render / "diagrams").mkdir()

    def diagram(self, name, kind, title, body="<svg></svg>", rendered=True):
        spec = {"diagram_type": kind, "meta": {"title": title, "subtitle": f"Why {name}?"}}
        (self.render / "diagrams" / f"{name}.json").write_text(json.dumps(spec))
        if rendered:
            (self.render / "diagrams" / f"{name}.html").write_text(f"<html><body>{body}</body></html>")

    def build(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.render), *args],
                              capture_output=True, text=True)

    def test_inlines_every_diagram_in_one_page(self):
        self.diagram("vote", "sequence", "A vote")
        self.diagram("system", "architecture", "One board")
        result = self.build("--title", "Idea Board")
        self.assertEqual(result.returncode, 0, result.stderr)
        page = (self.render / "index.html").read_text()
        self.assertEqual(page.count('type="application/json" data-diagram='), 2)
        self.assertIn("<h2>System</h2>", page)
        self.assertIn("<h2>Sequences</h2>", page)
        self.assertIn("Why vote?", page)
        self.assertLess(page.index("<h2>Sequences</h2>"), page.index('data-diagram="vote"'))

    def test_inlined_markup_cannot_close_its_script(self):
        self.diagram("evil", "tree", "<b>x</b>", body="<script>alert(1)</script>")
        self.assertEqual(self.build().returncode, 0)
        page = (self.render / "index.html").read_text()
        payload = page.split('<script type="application/json" data-diagram="evil">', 1)[1].split("</script>", 1)[0]
        self.assertIn("<\\/script>", payload)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", page)
        self.assertIn("<h2>Models and delivery</h2>", page)

    def test_catalog_sets_order_question_and_group(self):
        self.diagram("a", "architecture", "A")
        self.diagram("b", "architecture", "B")
        catalog = [{"name": "b", "question": "Asked by the catalog?", "group": "First"}]
        (self.render / "catalog.json").write_text(json.dumps(catalog))
        self.assertEqual(self.build().returncode, 0)
        page = (self.render / "index.html").read_text()
        self.assertLess(page.index('data-open="b"'), page.index('data-open="a"'))
        self.assertIn("Asked by the catalog?", page)
        self.assertIn("<h2>First</h2>", page)

    def test_skips_archify_receipts_beside_the_inputs(self):
        self.diagram("vote", "sequence", "A vote")
        (self.render / "diagrams" / "vote.browser-check.json").write_text(json.dumps({"ok": True}))
        self.assertEqual(self.build().returncode, 0)
        page = (self.render / "index.html").read_text()
        self.assertEqual(page.count('type="application/json" data-diagram='), 1)

    def test_refuses_a_diagram_without_its_render(self):
        self.diagram("done", "sequence", "Done")
        self.diagram("pending", "sequence", "Pending", rendered=False)
        result = self.build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("pending.html", result.stderr)
        self.assertFalse((self.render / "index.html").exists())

    def test_refuses_an_empty_folder(self):
        result = self.build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("no diagrams", result.stderr)


if __name__ == "__main__":
    unittest.main()
