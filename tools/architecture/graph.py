#!/usr/bin/env python3
# Spec: knowledge/operations/architecture-maintenance.md
# Spec: knowledge/components/graph-queries.md
"""Use pinned Graphify extractors on the explicit current corpus, including Markdown."""
import hashlib
import importlib.metadata
import json
import posixpath
from pathlib import Path
import re
import shutil
import subprocess
import sys

# A comment line that holds only the pointer, as doc-links reads it; prose quoting "Spec:" is not one.
SPEC_LINE = re.compile(r"^\s*(?:#|//|/\*|\*|--|;|<!--)\s*Spec:\s*(knowledge/[\w./-]+\.md)\s*(?:\*/|-->)?\s*$")
TEST_NAME = re.compile(r"(^|/)(tests?/|test_[^/]*$|[^/]*[._]test\.[^/]+$|[^/]*\.spec\.[^/]+$)")
DENO_SOURCES = (".ts", ".tsx", ".js", ".jsx", ".mts")


def is_test(path):
    return bool(TEST_NAME.search(path))


def file_nodes(nodes):
    """{source_file: the node that stands for the whole file}."""
    files = {}
    for node_id, data in nodes:
        source = str(data.get("source_file", ""))
        label, name = str(data.get("label", "")), posixpath.basename(source)
        # Graphify labels a file by its name, or by a longer suffix when two files share it (pages/vote.ts).
        if source and (label == name or label.endswith("/" + name)):
            files.setdefault(source, node_id)
    return files


def edge(relation, origin, source_file, line):
    return {"relation": relation, "confidence": "EXTRACTED", "confidence_score": 1.0, "_origin": origin,
            "source_file": source_file, "source_location": f"L{line}", "weight": 1.0}


def disk_frontmatter(root, doc, cached):
    """The doc's frontmatter as it is on disk now, parsed as Graphify parses it. Graphify's cache keys a
    page by its body alone, so after a frontmatter-only edit the page node keeps the old `sources`; a page
    whose file is gone keeps what the node has."""
    if not (root / doc).is_file():
        return cached or {}
    from graphify.extractors.markdown import _parse_frontmatter, _split_frontmatter
    lines = (root / doc).read_text(encoding="utf-8", errors="replace").splitlines()
    return _parse_frontmatter(_split_frontmatter(lines)[0])


def spec_source_edges(nodes, root):
    """The spec -> file edges a doc's frontmatter `sources` declares, and the resources that name no
    file in the graph. Graphify keeps the frontmatter on the page node but links only the code names
    written in the body, so the factory's own spec <-> code contract would otherwise be missing."""
    files = file_nodes(nodes)
    edges, unresolved = [], []
    for node_id, data in nodes:
        page = data.get("node_kind") == "page"
        sources = disk_frontmatter(root, str(data["source_file"]), data.get("frontmatter")).get("sources") if page else None
        if not isinstance(sources, list):
            continue
        doc = str(data["source_file"])
        for item in sources:
            resource = item.get("resource") if isinstance(item, dict) else None
            # Only a relative path names a file in this corpus; a URL or another scheme (owner-message:)
            # is evidence elsewhere.
            if not isinstance(resource, str) or re.match(r"[A-Za-z][\w+.-]*:", resource) or resource.startswith("/"):
                continue
            path = posixpath.normpath(posixpath.join(posixpath.dirname(doc), resource))
            if path in files:
                edges.append((node_id, files[path], edge("specifies", "frontmatter", doc, 1)))
            else:
                unresolved.append(f"{doc}: {resource}")
    return edges, unresolved


def head(path, lines=20):
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            return [handle.readline() for _ in range(lines)]
    except OSError:
        return []


def spec_line_edges(nodes, root):
    """file -> doc `specified_by` edges from a `Spec:` comment line in a file's first 20 lines, the other half
    of the spec contract; a named doc missing from the graph is returned as unresolved."""
    files, edges, unresolved = file_nodes(nodes), [], []
    for source, node_id in sorted(files.items()):
        for number, text in enumerate(head(root / source), 1):
            for doc in SPEC_LINE.findall(text):
                if doc in files and doc != source:
                    edges.append((node_id, files[doc], edge("specified_by", "spec_line", source, number)))
                elif doc not in files:
                    unresolved.append(f"{source}:{number}: {doc}")
    return edges, unresolved


PATH_TOKEN = re.compile(r"[\w.\[\]/-]+")
QUOTED_NAME = re.compile(r"[\"']([^\"'\s/]+)[\"']")


def test_name_edges(nodes, root):
    """test -> file `names_file` edges when a test's text names a project file: tests that run a script
    as a subprocess import nothing, so without these no test would reach the scripts it covers. A full
    path counts; a bare file name counts only quoted, with a dot, and unique in the project. One pass
    over each test's text, whatever the number of files."""
    files = file_nodes(nodes)
    names = {}
    for source in files:
        names.setdefault(posixpath.basename(source), []).append(source)
    unique = {name: paths[0] for name, paths in names.items() if "." in name and len(paths) == 1}
    edges = []
    for test in sorted(source for source in files if is_test(source)):
        try:
            text = (root / test).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        first = {}
        for match in PATH_TOKEN.finditer(text):
            if match.group() in files:
                first.setdefault(match.group(), match.start())
        for match in QUOTED_NAME.finditer(text):
            if match.group(1) in unique:
                first.setdefault(unique[match.group(1)], match.start())
        for source, position in sorted(first.items()):
            if source != test and not is_test(source):
                line = text.count("\n", 0, position) + 1
                edges.append((files[test], files[source], edge("names_file", "test_text", test, line)))
    return edges


def toolchain_import_edges(nodes, root, manifest_paths):
    """Exact file -> file `imports` edges of each Deno project (a folder with deno.json), from the
    module graph `deno info` resolves; returns the edges and a status for coverage.json."""
    projects = sorted({posixpath.dirname(path) for path in manifest_paths
                       if posixpath.basename(path) in ("deno.json", "deno.jsonc")})
    if not projects:
        return [], "no Deno project"
    deno = shutil.which("deno")
    if not deno:
        return [], "unavailable: deno is not on PATH"
    files, edges, seen = file_nodes(nodes), set(), set()
    for project in projects:
        prefix = f"{project}/" if project else ""
        for path in sorted(p for p in manifest_paths if p.startswith(prefix) and p.endswith(DENO_SOURCES)):
            uri = (root / path).as_uri()
            if uri in seen:
                continue
            try:
                result = subprocess.run([deno, "info", "--json", "--no-remote", "--no-npm", str(root / path)],
                                        cwd=root / project, capture_output=True, text=True, timeout=60, check=True)
                modules = json.loads(result.stdout)["modules"]
            except (OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
                return [], f"failed on {path}: {type(error).__name__}"
            for module in modules:
                source = relative(module.get("specifier", ""), root)
                seen.add(module.get("specifier", ""))
                if source not in files:
                    continue
                for dependency in module.get("dependencies", []):
                    for kind in ("code", "type"):
                        resolved = dependency.get(kind) or {}
                        target = relative(resolved.get("specifier", ""), root)
                        if target in files and target != source:
                            line = resolved.get("span", {}).get("start", {}).get("line", 0) + 1
                            edges.add((files[source], files[target], source, line))
    return [(s, t, edge("imports", "toolchain", f, n)) for s, t, f, n in sorted(edges)], "deno info"


def relative(uri, root):
    """The project-relative path of a local file:// specifier, or "" for anything else."""
    if not uri.startswith("file://"):
        return ""
    try:
        return Path(uri.removeprefix("file://")).resolve().relative_to(root).as_posix()
    except ValueError:
        return ""


def add_edges(graph, edges):
    """Add edges that Graphify did not already draw between the same two nodes; keep its own data."""
    added = 0
    for source, target, data in edges:
        if not graph.has_edge(source, target):
            graph.add_edge(source, target, **data)
            added += 1
    return added


def main():
    from graphify.extract import extract
    from graphify.build import build
    from graphify.export import to_json

    # Graphify makes source paths relative to an absolute root only.
    root, out, manifest_file = (Path(arg).resolve() for arg in sys.argv[1:])
    manifest = json.loads(manifest_file.read_text())
    paths = [root / item["path"] for item in manifest]
    extraction = extract(paths, cache_root=out, root=root, parallel=False)
    sources = {str(node.get("source_file", "")) for node in extraction["nodes"]}
    required = [item["path"] for item in manifest if item["required"]]
    missing = sorted(set(required) - sources)
    if missing:
        raise ValueError(f"Graphify coverage missing {len(missing)} required files: {', '.join(missing[:8])}")
    graph = build([extraction], directed=True, dedup=False, root=root)
    # A file no extractor reads (a Dockerfile, a stylesheet) still gets a node, so a spec that lists it
    # or a test that names it resolves instead of being reported missing.
    present = {str(data.get("source_file", "")) for _, data in graph.nodes(data=True)}
    for rel in sorted({item["path"] for item in manifest} - present):
        graph.add_node(f"file:{rel}", label=posixpath.basename(rel), source_file=rel, source_location="L1",
                       file_type="inventory")
    nodes = list(graph.nodes(data=True))
    spec_edges, unresolved = spec_source_edges(nodes, root)
    line_edges, unresolved_lines = spec_line_edges(nodes, root)
    test_edges = test_name_edges(nodes, root)
    toolchain_edges, toolchain_status = toolchain_import_edges(nodes, root, [item["path"] for item in manifest])
    # Each count is what the source found; `<name>_new` is how many Graphify had not already drawn.
    found = {"spec_source_edges": spec_edges, "spec_line_edges": line_edges, "test_name_edges": test_edges,
             "toolchain_import_edges": toolchain_edges}
    added = {name: len(edges) for name, edges in found.items()}
    added.update({f"{name}_new": add_edges(graph, edges) for name, edges in found.items()})
    if not graph or not to_json(graph, {}, str(out / "graph.json"), force=True):
        raise ValueError("Graphify did not produce a persistent graph")
    coverage = {"mode": "native structural code, Markdown and config; no LLM inference",
                "graphify_version": importlib.metadata.version("graphifyy"),
                "required_files": len(required), "extracted_files": sorted(sources & {item["path"] for item in manifest}),
                "inventory_only": sorted({item["path"] for item in manifest} - sources),
                "nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "missing": missing,
                "spec_source_edges": added["spec_source_edges"], "unresolved_spec_sources": unresolved,
                "spec_line_edges": added["spec_line_edges"], "unresolved_spec_lines": unresolved_lines,
                "test_name_edges": added["test_name_edges"], "toolchain_imports": toolchain_status,
                "toolchain_import_edges": added["toolchain_import_edges"],
                "new_edges": {name: count for name, count in added.items() if name.endswith("_new")}}
    (out / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    (out / "GRAPH_REPORT.md").write_text("# Æion Factory Graphify structural report\n\n"
        f"{coverage['nodes']} nodes, {coverage['edges']} edges; {len(required)} required source/docs files covered.\n\n"
        "Native Markdown headings, frontmatter and links are included; each spec's frontmatter `sources` adds a\n"
        f"`specifies` edge ({added['spec_source_edges']} here, {len(unresolved)} unresolved); `Spec:` lines add\n"
        f"{added['spec_line_edges']} `specified_by`, tests naming a file {added['test_name_edges']} `names_file`, and\n"
        f"the toolchain ({toolchain_status}) {added['toolchain_import_edges']} exact `imports`. Inferred edges retain upstream confidence.\n"
        "This is a structural graph, not complete semantic understanding. See coverage.json for inventory-only paths.\n")


if __name__ == "__main__":
    main()
