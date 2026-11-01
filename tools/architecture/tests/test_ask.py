#!/usr/bin/env python3
"""tools/architecture/ask on fixture graphs: exact names, rebuilds, paths, tests, specs and hubs; callers
through the project's language server (skipped without deno).

Query tests write graph.json by hand, so they need no venv; the extraction test builds a real graph
with the pinned Graphify and is skipped when its venv is missing."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / "ask"
loader = importlib.machinery.SourceFileLoader("ask", str(TOOL))
spec = importlib.util.spec_from_loader("ask", loader)
ask = importlib.util.module_from_spec(spec)
loader.exec_module(ask)


def node(node_id, label, source, line, kind="code"):
    return {"id": node_id, "label": label, "source_file": source, "source_location": f"L{line}", "file_type": kind}


def link(source, target, relation, where, line, confidence="EXTRACTED"):
    return {"source": source, "target": target, "relation": relation, "source_file": where,
            "source_location": f"L{line}", "confidence": confidence}


NODES = [
    node("app", "app.py", "pkg/app.py", 1), node("app_run", "run()", "pkg/app.py", 4),
    node("app_main", "main()", "pkg/app.py", 9),
    node("util", "util.py", "pkg/util.py", 1), node("util_helper", "helper()", "pkg/util.py", 2),
    node("util_main", "main()", "pkg/util.py", 6),
    node("store", "store.py", "pkg/store.py", 1), node("store_save", "save()", "pkg/store.py", 3),
    node("tool", "tool.py", "pkg/tool.py", 1), node("tool_go", "go()", "pkg/tool.py", 2),
    node("orphan", "orphan.py", "pkg/orphan.py", 1), node("orphan_lonely", "lonely()", "pkg/orphan.py", 1),
    node("conf", "settings.json", "settings.json", 1), node("conf_key", "debug", "settings.json", 2),
    node("t_app", "test_app.py", "tests/test_app.py", 1), node("t_app_case", "AppTests", "tests/test_app.py", 5),
    node("t_tool", "test_tool.py", "tests/test_tool.py", 1), node("t_tool_case", "ToolTests", "tests/test_tool.py", 4),
    node("doc", "app.md", "knowledge/app.md", 1, "document"),
    {"id": "json", "label": "json", "source_file": "", "file_type": "concept"},
]
LINKS = [
    link("app", "util_helper", "imports", "pkg/app.py", 2), link("app_run", "util_helper", "calls", "pkg/app.py", 5),
    link("util", "store", "imports_from", "pkg/util.py", 1), link("util_helper", "store_save", "calls", "pkg/util.py", 3),
    link("app", "json", "imports", "pkg/app.py", 1),
    # A call Graphify inferred by name alone, with no import between the files: not a dependency.
    link("orphan_lonely", "app_main", "calls", "pkg/orphan.py", 2, "INFERRED"),
    link("t_app", "app", "imports_from", "tests/test_app.py", 1),
    link("t_tool", "tool", "names_file", "tests/test_tool.py", 7),
    link("doc", "app", "specifies", "knowledge/app.md", 1), link("app", "doc", "specified_by", "pkg/app.py", 1),
    link("doc", "util", "specifies", "knowledge/app.md", 1),
]
FILES = ["pkg/app.py", "pkg/util.py", "pkg/store.py", "pkg/tool.py", "pkg/orphan.py", "settings.json",
         "tests/test_app.py", "tests/test_tool.py", "knowledge/app.md"]


class AskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel in FILES:
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text(f"# {rel}\n")
        self.builds = self.root.parent / f"{self.root.name}-builds"
        self.addCleanup(lambda: self.builds.unlink(missing_ok=True))
        self.fake_venv()

    def fake_venv(self):
        """A stand-in for the venv python: it writes the fixture graph and counts its builds."""
        fake = self.root.parent / f"{self.root.name}-python"
        self.addCleanup(lambda: fake.unlink(missing_ok=True))
        graph = json.dumps({"nodes": NODES, "links": LINKS})
        fake.write_text(f"""#!{sys.executable}
import sys, pathlib
out = pathlib.Path(sys.argv[3])
(out / "graph.json").write_text({graph!r})
(out / "coverage.json").write_text('{{"inventory_only": [], "toolchain_imports": "no Deno project"}}')
with open({str(self.builds)!r}, "a") as count:
    count.write("build\\n")
""")
        fake.chmod(0o755)
        self.original = ask.VENV_PYTHON
        ask.VENV_PYTHON = fake
        self.addCleanup(setattr, ask, "VENV_PYTHON", self.original)

    def run_ask(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ask.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def build_count(self):
        return len(self.builds.read_text().splitlines()) if self.builds.exists() else 0

    def test_names_match_exactly(self):
        code, out, _ = self.run_ask("find", "pkg/app.py")
        self.assertEqual((code, out.split()[0]), (0, "pkg/app.py:1"))
        self.assertEqual(self.run_ask("find", "helper")[0], 0)
        code, _, err = self.run_ask("deps", "main")
        self.assertEqual(code, 3)
        self.assertIn("app_main", err)
        self.assertIn("util_main", err)
        self.assertEqual(self.run_ask("deps", "util_main")[0], 0)
        self.assertEqual(self.run_ask("deps", "help")[0], 4, "a prefix is not a match")
        self.assertEqual(self.run_ask("find", "app")[0], 0, "an id matches")
        self.assertEqual(self.run_ask("find", "pkg/ap")[0], 4)

    def test_rebuild_only_on_change(self):
        self.run_ask("status")
        self.run_ask("status")
        self.assertEqual(self.build_count(), 1)
        target = self.root / "pkg/util.py"
        target.write_text("# changed, longer\n")
        self.run_ask("status")
        self.assertEqual(self.build_count(), 2)
        (self.root / "pkg/new.py").write_text("x = 1\n")
        _, out, _ = self.run_ask("--json", "status")
        self.assertEqual(self.build_count(), 3)
        self.assertFalse(json.loads(self.run_ask("--json", "status")[1])["graph"]["rebuilt"])
        self.assertTrue(json.loads(out)["graph"]["rebuilt"])

    def test_refuses_without_venv(self):
        ask.VENV_PYTHON = self.root / "missing/python"
        code, _, err = self.run_ask("status")
        self.assertEqual(code, 1)
        self.assertIn("tools/architecture/setup", err)

    def test_path_names_each_hop(self):
        code, out, _ = self.run_ask("path", "pkg/app.py", "pkg/store.py")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), ["pkg/app.py -> pkg/util.py  [imports at pkg/app.py:2]",
                                            "pkg/util.py -> pkg/store.py  [imports_from at pkg/util.py:1]"])
        code, out, _ = self.run_ask("path", "pkg/store.py", "pkg/app.py")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("no edge path: pkg/store.py reaches 0 files"))
        self.assertIn("ask callers <file>:<method>", out)

    def test_inferred_call_without_import_is_dropped(self):
        _, out, _ = self.run_ask("rdeps", "pkg/app.py")
        self.assertNotIn("pkg/orphan.py", out)
        self.assertIn("tests/test_app.py", out)

    def test_rdeps_depth(self):
        _, out, _ = self.run_ask("rdeps", "pkg/store.py", "--depth", "3")
        self.assertEqual([line.split()[0] for line in out.splitlines()],
                         ["pkg/util.py", "pkg/app.py", "tests/test_app.py"])
        self.assertIn("depth 3", out.splitlines()[-1])

    def test_tests_and_untested(self):
        _, out, _ = self.run_ask("tests", "pkg/store.py")
        self.assertEqual(out.splitlines(), ["tests/test_app.py  transitive via pkg/app.py -> pkg/util.py"])
        _, out, _ = self.run_ask("tests", "pkg/app.py")
        self.assertEqual(out.splitlines(), ["tests/test_app.py  direct"])
        _, out, _ = self.run_ask("tests", "pkg/tool.py")
        self.assertEqual(out.splitlines(), ["tests/test_tool.py  named"])
        _, out, _ = self.run_ask("untested")
        lines = out.splitlines()
        self.assertEqual(lines[0], "5 source files: 1 imported by a test, 1 named by a test, "
                                   "2 reached through others, 1 reached by none")
        self.assertEqual(lines[1:], ["untested: pkg/orphan.py"], "settings.json is configuration, not source")

    def test_spec_both_directions(self):
        _, out, _ = self.run_ask("spec", "pkg/app.py")
        self.assertEqual(out.splitlines(), ["knowledge/app.md  [both]"])
        _, out, _ = self.run_ask("spec", "pkg/util.py")
        self.assertEqual(out.splitlines(), ["knowledge/app.md  [in the spec's sources; no Spec: line (gap)]"])
        _, out, _ = self.run_ask("files", "knowledge/app.md")
        self.assertEqual(out.splitlines(), ["pkg/app.py  [both]",
                                            "pkg/util.py  [in the spec's sources; no Spec: line (gap)]"])
        _, out, _ = self.run_ask("spec", "pkg/store.py")
        self.assertEqual(out.splitlines(), ["no spec names pkg/store.py, and it names none"])

    def test_hubs_exclude_noise(self):
        _, out, _ = self.run_ask("hubs")
        files = [line.split()[0] for line in out.splitlines()]
        # Fan-in ties break on fan-out, then on path.
        self.assertEqual(files[:3], ["pkg/app.py", "pkg/util.py", "pkg/store.py"])
        for noise in ("tests/test_app.py", "knowledge/app.md", "json", "settings.json"):
            self.assertNotIn(noise, files)

    def test_output_is_stable(self):
        first = [self.run_ask(*args)[1] for args in (("untested",), ("hubs",), ("find", "main"))]
        os.utime(self.root / "pkg/app.py", ns=(1, 1))
        second = [self.run_ask(*args)[1] for args in (("untested",), ("hubs",), ("find", "main"))]
        self.assertEqual(first, second)
        self.assertEqual([line.split()[0] for line in second[2].splitlines()], ["pkg/app.py:9", "pkg/util.py:6"])
        # Evidence sorts by line number, not as text: line 9 comes before line 10.
        self.assertEqual(ask.place("a.py:9") < ask.place("a.py:10"), True)

    def test_cap_and_json(self):
        code, out, _ = self.run_ask("--json", "deps", "pkg/app.py")
        data = json.loads(out)
        self.assertEqual((code, data["command"]), (0, "deps"))
        self.assertEqual(data["results"][0]["file"], "pkg/util.py")
        self.assertEqual(data["results"][-1], {"external": ["json"]})


class CallersTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def run_ask(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ask.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    @unittest.skipUnless(shutil.which("deno") or (Path.home() / ".deno/bin/deno").is_file(), "needs deno (deno lsp)")
    def test_callers_resolve_by_type(self):
        # api.ts calls add() on a parameter: no import edge reaches the method, the server does.
        (self.root / "app").mkdir()
        (self.root / "app/deno.json").write_text("{}\n")
        (self.root / "app/store.ts").write_text(
            "export function createStore() {\n  return {\n    add(x: number): number {\n      return x + 1;\n    },\n"
            "    size(): number {\n      return 0;\n    },\n  };\n}\nexport type Store = ReturnType<typeof createStore>;\n")
        (self.root / "app/api.ts").write_text(
            'import type { Store } from "./store.ts";\n\nexport function handle(store: Store) {\n  return store.add(1);\n}\n')
        code, out, err = self.run_ask("callers", "app/store.ts:add")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out.splitlines(), ["app/api.ts:4  handle  [lsp call]"])
        self.assertEqual(self.run_ask("callers", "app/store.ts:3")[1], out, "a line names the same symbol")
        self.assertEqual(self.run_ask("callers", "app/store.ts:size")[1].strip(), "no caller of size at app/store.ts:6")
        self.assertEqual(self.run_ask("callers", "app/store.ts:ad")[0], 4, "a prefix is not a match")

    def test_callers_refuse_without_server(self):
        (self.root / "pkg").mkdir()
        (self.root / "pkg/app.py").write_text("def main():\n    return 1\n")
        code, out, err = self.run_ask("callers", "pkg/app.py:main")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("no language server for pkg/app.py", err)
        self.assertIn("installs nothing", err)
        self.assertEqual(self.run_ask("callers", "pkg/missing.py:main")[0], 2)
        self.assertEqual(self.run_ask("callers", "pkg/app.py")[0], 2, "the symbol is required")


@unittest.skipUnless(ask.VENV_PYTHON.is_file(), "needs the Graphify venv (tools/architecture/setup)")
class ExtractionTests(unittest.TestCase):
    def test_real_build_adds_spec_line_and_test_name_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "tools/tests").mkdir(parents=True)
            (root / "knowledge/tool.md").write_text("---\ntitle: Tool\nsources:\n  - id: image\n"
                                                    "    resource: ../tools/Dockerfile\n  - id: owner\n"
                                                    "    resource: owner-message:2026-10-28\n---\n\n# Tool\n")
            (root / "knowledge/notes.md").write_text("# Notes\n\nA file says `Spec: knowledge/missing.md` here.\n")
            (root / "tools/tool.py").write_text("# Spec: knowledge/tool.md\ndef go():\n    return 1\n")
            # No extractor reads a Dockerfile: it still gets a node, so the spec that lists it resolves.
            (root / "tools/Dockerfile").write_text("# Spec: knowledge/tool.md\nFROM scratch\n")
            (root / "tools/tests/test_tool.py").write_text(
                "import subprocess\n\n\ndef test_go():\n    subprocess.run(['python3', 'tools/tool.py'])\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ask.main(["--root", str(root), "tests", "tools/tool.py"]), 0)
                self.assertEqual(ask.main(["--root", str(root), "spec", "tools/tool.py"]), 0)
                self.assertEqual(ask.main(["--root", str(root), "spec", "tools/Dockerfile"]), 0)
            self.assertEqual(out.getvalue().splitlines(), [
                "tools/tests/test_tool.py  named",
                "knowledge/tool.md  [Spec: line; missing from the spec's sources (gap)]",
                "knowledge/tool.md  [both]"])
            coverage = json.loads((root / ".aeion/graph/coverage.json").read_text())
            # Prose that quotes "Spec:" and a non-path resource are not unresolved pointers.
            self.assertEqual((coverage["unresolved_spec_lines"], coverage["unresolved_spec_sources"]), ([], []))
            shutil.rmtree(root / ".aeion")

    def test_frontmatter_only_edit_updates_spec_sources(self):
        # Graphify caches a page by its body, so the sources must come from the file on disk (OpenCode FB-001).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "knowledge").mkdir()
            (root / "tools").mkdir()
            spec = "---\ntitle: Tool\nsources:\n  - id: code\n    resource: ../tools/{}\n---\n\n# Tool\n"
            (root / "knowledge/tool.md").write_text(spec.format("old.py"))
            (root / "tools/old.py").write_text("def old():\n    return 1\n")
            (root / "tools/new.py").write_text("def new():\n    return 2\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ask.main(["--root", str(root), "spec", "tools/old.py"]), 0)
                (root / "knowledge/tool.md").write_text(spec.format("new.py"))
                self.assertEqual(ask.main(["--root", str(root), "spec", "tools/new.py"]), 0)
                self.assertEqual(ask.main(["--root", str(root), "spec", "tools/old.py"]), 0)
            gap = "knowledge/tool.md  [in the spec's sources; no Spec: line (gap)]"
            self.assertEqual(out.getvalue().splitlines(), [gap, gap, "no spec names tools/old.py, and it names none"])
            shutil.rmtree(root / ".aeion")


if __name__ == "__main__":
    unittest.main()
