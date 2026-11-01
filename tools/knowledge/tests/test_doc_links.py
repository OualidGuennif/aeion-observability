#!/usr/bin/env python3
"""Fixture tests for tools/knowledge/doc-links: throwaway git repos, the real tool run with --root.

Run with: python3 tools/knowledge/tests/test_doc_links.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "doc-links"
# Built in two parts so this file holds no pointer the real check would follow.
TAG = "Sp" + "ec:"
DOC = """---
type: Component
title: Example
sources:
  - id: code
    resource: ../../src/app.ts
    title: The code
  - id: folder
    resource: ../../src
    title: The whole folder
  - id: owner
    resource: owner request in chat, 2026-10-20
    title: Free text, not a path
---

Body.
"""
failures, passes = [], 0


def sh(repo, *args):
    return subprocess.run(args, cwd=repo, capture_output=True, text=True, check=False)


def repo():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "knowledge/components").mkdir(parents=True)
    (tmp / "src").mkdir()
    (tmp / "knowledge/components/example.md").write_text(DOC)
    (tmp / "src/app.ts").write_text(f"// {TAG} knowledge/components/example.md\nexport const a = 1;\n")
    (tmp / "src/other.ts").write_text("export const b = 2;\n")
    sh(tmp, "git", "init", "-q", "-b", "main")
    sh(tmp, "git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "add", ".")
    sh(tmp, "git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "base")
    return tmp


def commit(tmp, message):
    sh(tmp, "git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qam", message)


def check(name, tmp, args, want_code, want_text=""):
    global passes
    r = subprocess.run([sys.executable, str(TOOL), "--root", str(tmp), *args], capture_output=True, text=True)
    if r.returncode == want_code and want_text in r.stdout:
        passes += 1
    else:
        failures.append(f"{name}: exit {r.returncode}, want {want_code} with '{want_text}'\n{r.stdout}{r.stderr}")


t = repo()
check("links resolve, free text ignored", t, [], 0, "PASS")
check("the docs covering a file", t, ["--for", "src/app.ts"], 0, "knowledge/components/example.md")
check("a directory source covers no single file", t, ["--for", "src/other.ts"], 0, "")

(t / "src/app.ts").write_text(f"// {TAG} knowledge/components/example.md\nexport const a = 2;\n")
commit(t, "change app")
check("code changed, its doc did not", t, ["--diff", "HEAD~1"], 1, "RULE L3 src/app.ts")

t = repo()
(t / "src/other.ts").write_text("export const b = 3;\n")
commit(t, "change other")
check("a file only under a directory source asks for nothing", t, ["--diff", "HEAD~1"], 0, "PASS")

t = repo()
(t / "src/app.ts").write_text(f"// {TAG} knowledge/components/example.md\nexport const a = 2;\n")
commit(t, "change app\n\nDocs-Checked: knowledge/components/example.md -- no documented fact changed")
check("a declared check passes", t, ["--diff", "HEAD~1"], 0, "PASS")

t = repo()
(t / "src/app.ts").write_text(f"// {TAG} knowledge/components/example.md\nexport const a = 2;\n")
commit(t, "change app\n\nDocs-Checked: knowledge/components/example.md")
check("an exemption requires its explanation", t, ["--diff", "HEAD~1"], 1, "RULE L3")

t = repo()
(t / "knowledge/components/example.md").write_text("---\ntype: Reference\n---\nApp still exists.\n")
commit(t, "header-only coverage")
(t / "src/app.ts").unlink()
commit(t, "remove application")
check("deleted header-linked source retains base coverage", t, ["--diff", "HEAD~1"], 1, "RULE L3 src/app.ts")

t = repo()
(t / "knowledge/components/example.md").write_text("---\ntype: Reference\n---\nApplication behavior.\n")
commit(t, "header-only coverage")
(t / "src/app.ts").write_text("export const a = 3;\n")
commit(t, "remove header and change behavior")
check("removing a pointer does not erase changed-source coverage", t, ["--diff", "HEAD~1"], 1, "RULE L3 src/app.ts")

t = repo()
(t / "src/app.ts").write_text(f"// {TAG} knowledge/components/example.md\nexport const a = 2;\n")
(t / "knowledge/components/example.md").write_text(DOC + "\nUpdated.\n")
check("the doc changed with the code (uncommitted)", t, ["--diff", "HEAD", "--worktree"], 0, "PASS")

t = repo()
(t / "src/other.ts").write_text(f"// {TAG} knowledge/components/example.md\n\nexport const b = 2;\n")
commit(t, "link other")
check("adding a Spec: line alone moves no fact", t, ["--diff", "HEAD~1"], 0, "PASS")

t = repo()
(t / "src/app.ts").write_text(f"// {TAG} knowledge/components/missing.md\n")
check("a Spec pointer to a missing doc", t, [], 1, "RULE L1 src/app.ts:1")
(t / "src/app.ts").unlink()
check("a source that disappeared", t, [], 1, "RULE L2 knowledge/components/example.md")

t = repo()
check("a valid empty diff passes", t, ["--diff", "HEAD"], 0, "PASS")
check("a missing diff base fails", t, ["--diff", "missing-test-ref"], 1)
outside = Path(tempfile.mkdtemp())
check("an invalid repository fails", outside, ["--diff", "HEAD"], 1)
check("a plain folder without git passes", outside, [], 0, "PASS")
(outside / "knowledge/components").mkdir(parents=True)
(outside / "knowledge/components/example.md").write_text(DOC)
(outside / "src").mkdir()
(outside / "src/app.ts").write_text(f"// {TAG} knowledge/components/missing.md\n")
check("a plain folder still gets L1", outside, [], 1, "RULE L1 src/app.ts:1")

# A project nested in this one (its own AGENTS.md and knowledge/) points at its own knowledge/, not ours.
t = repo()
(t / "demo/copy/knowledge/components").mkdir(parents=True)
(t / "demo/copy/AGENTS.md").write_text("# Nested\n")
(t / "demo/copy/knowledge/index.md").write_text("# Index\n")
(t / "demo/copy/knowledge/components/nested.md").write_text(DOC.replace("../../src/app.ts", "../../app.ts"))
(t / "demo/copy/app.ts").write_text(f"// {TAG} knowledge/components/nested.md\nexport const n = 1;\n")
(t / "demo/lone").mkdir()
(t / "demo/lone/knowledge").mkdir()
(t / "demo/lone/knowledge/index.md").write_text("# Not a project: no AGENTS.md\n")
(t / "demo/lone/app.ts").write_text(f"// {TAG} knowledge/components/nested.md\n")
sh(t, "git", "add", ".")
check("a folder without AGENTS.md is not a nested project", t, [], 1, "RULE L1 demo/lone/app.ts:1")
(t / "demo/lone/app.ts").unlink()
sh(t, "git", "add", "-A")
check("a nested project's pointers are its own", t, [], 0, "PASS")
commit(t, "nested project")
(t / "demo/copy/app.ts").write_text(f"// {TAG} knowledge/components/nested.md\nexport const n = 2;\n")
commit(t, "nested change")
check("a nested project's change asks nothing of this root", t, ["--diff", "HEAD~1"], 0, "PASS")

# Metadata discovery is independent of source language and Git's human-readable path quoting.
t = repo()
paths = ["src/header" + suffix for suffix in (".py", ".ts", ".tsx", ".jsx", ".mts", ".go", ".rs", ".vue", ".svelte")]
paths += ["tools/check", "Dockerfile", "src/café.py", "src/a file.py"]
for name in paths:
    path = t / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {TAG} knowledge/components/example.md\nvalue = 1\n")
sh(t, "git", "add", ".")
commit(t, "header fixtures")
for name in paths:
    check(f"header covers {name}", t, ["--for", name], 0, "knowledge/components/example.md")
(t / "src/café.py").write_text(f"# {TAG} knowledge/components/example.md\nvalue = 2\n")
check("an accented changed path requires its doc", t, ["--diff", "HEAD", "--worktree"], 1, "RULE L3 src/café.py")

t = repo()
for name, header in [("src/block.cpp", f"/* {TAG} knowledge/components/example.md */"),
                     ("src/page.html", f"<!-- {TAG} knowledge/components/example.md -->"),
                     ("src/module.py", f'"""Module.\n{TAG} knowledge/components/example.md\n"""'),
                     ("src/bom.rs", f"\ufeff// {TAG} knowledge/components/example.md")]:
    (t / name).write_text(header + "\n")
sh(t, "git", "add", ".")
commit(t, "leading comment forms")
for name in ("src/block.cpp", "src/page.html", "src/module.py", "src/bom.rs"):
    check(f"leading metadata covers {name}", t, ["--for", name], 0, "knowledge/components/example.md")

t = repo()
(t / "src/a file.json").write_text("{}\n")
(t / "knowledge/components/example.md").write_text(DOC.replace("../../src/app.ts", "../../src/a file.json"))
sh(t, "git", "add", ".")
commit(t, "explicit source with spaces")
check("a spaced explicit source needs no header", t, ["--for", "src/a file.json"], 0, "knowledge/components/example.md")
(t / "src/a file.json").write_text('{"changed":true}\n')
check("a spaced declared file requires its doc", t, ["--diff", "HEAD", "--worktree"], 1, "RULE L3 src/a file.json")

t = repo()
for name, content in [
    ("docs/example.md", f"# {TAG} knowledge/missing.md\n"),
    ("vendor/example.py", f"# {TAG} knowledge/missing.md\n"),
    ("node_modules/example.js", f"// {TAG} knowledge/missing.md\n"),
    (".aeion/generated.py", f"# {TAG} knowledge/missing.md\n"),
    ("auth.json", f"# {TAG} knowledge/missing.md\n"),
    ("src/string.py", f'VALUE = "{TAG} knowledge/missing.md"\n'),
]:
    path = t / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
(t / "src/binary.bin").write_bytes(f"# {TAG} knowledge/missing.md\n".encode() + b"\0")
(t / "src/late.py").write_text("# header\n" * 1200 + f"# {TAG} knowledge/missing.md\n")
(t / "src/alias.py").symlink_to(t / "auth.json")
sh(t, "git", "add", ".")
commit(t, "excluded metadata fixtures")
check("examples, dependencies, secrets, binary data and symlinks are not headers", t, [], 0, "PASS")

t = repo()
(t / "src/app.ts").write_text(f'export const a = 1; // {TAG} knowledge/components/example.md\n')
commit(t, "inline pointer baseline")
(t / "src/app.ts").write_text(f'export const a = 2; // {TAG} knowledge/components/example.md\n')
commit(t, "behavior change with an inline pointer")
check("an inline pointer cannot exempt executable changes", t, ["--diff", "HEAD~1"], 1, "RULE L3 src/app.ts")

# A file that names its spec must be one of the spec's sources (Pi FB-004): the contract runs both ways.
t = Path(tempfile.mkdtemp())
(t / "knowledge/components").mkdir(parents=True)
(t / "tools").mkdir()
(t / "knowledge/components/tool.md").write_text("---\ntype: Component\ntitle: Tool\nsources:\n"
                                                 "  - resource: ../../tools/listed.py\n    title: Listed first\n---\n\nBody.\n")
(t / "tools/listed.py").write_text(f"# {TAG} knowledge/components/tool.md\n")
check("a list-first resource is a source", t, [], 0, "PASS")
(t / "tools/unlisted.py").write_text(f"# {TAG} knowledge/components/tool.md\n")
check("a Spec line whose doc omits the file", t, [], 1, "RULE L4 tools/unlisted.py:1")

for f in failures:
    print("FAIL:", f)
print(f"{passes} passed, {len(failures)} failed")
sys.exit(1 if failures else 0)
