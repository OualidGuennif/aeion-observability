#!/usr/bin/env python3
"""Materialise the Agora feature contract: one Markdown spec per feature, plus a manifest.

    python3 demo/forum/tools/generate_features.py          write features/ and MANIFEST.json
    python3 demo/forum/tools/generate_features.py --check  fail if the files on disk differ

The specs_*.py definitions are canonical. Validate their graph and dispatch metadata before
rendering Markdown, the manifest and index. Forward references are legal; cycles are not.
Spec: demo/forum/PLAN.md
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "features"
sys.path.insert(0, str(HERE))

from specs_a import SPECS as A  # noqa: E402
from specs_b import SPECS as B  # noqa: E402
from specs_c import SPECS as C  # noqa: E402
from specs_d import SPECS as D  # noqa: E402
from specs_e import SPECS as E  # noqa: E402
from specs_f import SPECS as F  # noqa: E402

SPECS = A + B + C + D + E + F
SIZES = {"S", "M", "L"}
AREAS = {"foundation", "forum", "moderation", "agents", "corpus", "ops"}
PHASES = {f"P{i}": i for i in range(6)}
PRODUCT_ROOTS = ("demo/forum-app/", "demo/forum-web/", "demo/forum-docs/")
ARCHITECTURE = "quarkus-postgresql-react-web-v1"

TEMPLATE = """---
id: {id:03d}
sequence: {sequence}
title: "{title}"
area: {area}
size: {size}
parallel: {parallel}
phase: {phase}
tier: {tier}
write_paths: {write_paths}
depends_on: {deps}
owner: builder
status: proposed
architecture: {architecture}
architecture_digest: {architecture_digest}
---

# {id:03d} — {title}

## Intent

{goal}

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/{source}`.

## Inputs

**Delivery steps:**

{delivery}

**Scope:**

{scope}{constraints}

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

{security}

This invariant and the acceptance cases belong to planned protected check `agora-{id:03d}`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

{accept}

**Test scenario:** {test}

## Out of scope

{out}
"""


def slug(title):
    text = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-+", "-", text)


def bullets(items):
    return "\n".join(f"- {item}" for item in items)


def checks(items):
    return "\n".join(f"- [ ] {item}" for item in items)


def architecture_digest():
    return hashlib.sha256((ROOT / 'ARCHITECTURE.md').read_bytes()).hexdigest()


def execution_order():
    """Stable topological order: ready prerequisites first, then phase and stable ID."""
    pending = {s['id']: s for s in SPECS}
    result = []
    completed = set()
    while pending:
        ready = [s for s in pending.values() if set(s['deps']) <= completed]
        if not ready:
            raise ValueError('catalog_has_no_topological_order')
        item = min(ready, key=lambda s: (PHASES[s['phase']], s['id']))
        result.append(item)
        completed.add(item['id'])
        del pending[item['id']]
    return result


def validate():
    problems = []
    ids = [s["id"] for s in SPECS]
    if ids != list(range(1, 101)):
        problems.append(f"ids are not exactly 001..100 ({len(ids)} specs)")
        return problems
    by_id = {s["id"]: s for s in SPECS}
    for spec in SPECS:
        sid = spec["id"]
        if spec["area"] not in AREAS:
            problems.append(f"{sid:03d}: unknown area {spec['area']}")
        if spec["size"] not in SIZES:
            problems.append(f"{sid:03d}: unknown size {spec['size']}")
        if any(not spec.get(k) for k in ("accept", "scope", "goal", "security", "test", "out")):
            problems.append(f"{sid:03d}: every contract section is mandatory")
        steps = spec.get('delivery')
        if (not isinstance(steps, list) or not 2 <= len(steps) <= 4
                or any(not isinstance(x, str) or not x.strip() or len(x) > 220 for x in steps)):
            problems.append(f"{sid:03d}: two to four bounded delivery steps are mandatory")
        if spec.get("phase") not in PHASES or spec.get("tier") != 3:
            problems.append(f"{sid:03d}: phase P0..P5 and builder tier 3 are mandatory")
        if type(spec.get("parallel")) is not bool:
            problems.append(f"{sid:03d}: parallel must be a boolean")
        scopes = spec.get("write_paths", [])
        if not scopes or any(not isinstance(p, str) or not p.startswith(PRODUCT_ROOTS)
                             or not re.fullmatch(r"[A-Za-z0-9_./-]+", p)
                             or any(part in {".", "..", ".git"} for part in p.rstrip('/').split('/'))
                             or "//" in p or "/./" in p for p in scopes):
            problems.append(f"{sid:03d}: write scopes must be literal paths inside the product roots")
        if spec.get("parallel") and any(p in scopes for p in PRODUCT_ROOTS):
            problems.append(f"{sid:03d}: parallel work cannot reserve the whole product tree")
        if len(spec["deps"]) != len(set(spec["deps"])):
            problems.append(f"{sid:03d}: duplicate dependencies")
        for dep in spec["deps"]:
            if dep not in ids:
                problems.append(f"{sid:03d}: depends on unknown feature {dep:03d}")
            elif (spec.get("phase") in PHASES and by_id[dep].get("phase") in PHASES
                  and PHASES[by_id[dep]["phase"]] > PHASES[spec["phase"]]):
                problems.append(f"{sid:03d}: dependency {dep:03d} belongs to a later phase")
    active, done = [], set()

    def visit(sid):
        if sid in active:
            cycle = active[active.index(sid):] + [sid]
            problems.append("dependency cycle: " + " -> ".join(f"{n:03d}" for n in cycle))
            return
        if sid in done:
            return
        active.append(sid)
        for dep in by_id[sid]["deps"]:
            if dep in by_id:
                visit(dep)
        active.pop()
        done.add(sid)

    for sid in ids:
        visit(sid)
    categories = by_id[75].get("categories", [])
    if categories != ["tech", "state", "government"]:
        problems.append("075: corpus categories must be tech, state, government")
    required = by_id[83].get("required_categories", [])
    if required != categories:
        problems.append("083: daily coverage must match the three schema categories")
    if len({slug(s["title"]) for s in SPECS}) != len(SPECS):
        problems.append("two features share a slug, so a file name would collide")
    parallel = [s for s in SPECS if s.get('parallel')]
    for pos, left in enumerate(parallel):
        for right in parallel[pos + 1:]:
            if any(a == b or (a.endswith('/') and b.startswith(a))
                   or (b.endswith('/') and a.startswith(b))
                   for a in left.get('write_paths', []) for b in right.get('write_paths', [])):
                problems.append(f"{left['id']:03d}/{right['id']:03d}: parallel write scopes overlap")
    # Stack-specific regressions are a catalog error, not a task for the builder to resolve.
    for spec in SPECS:
        text = '\n'.join(str(spec.get(k, '')) for k in ('goal', 'scope', 'accept', 'test', 'security'))
        if re.search(r'FastAPI|pytest|extra=forbid|JavaScript.disabled|without JavaScript|no client framework', text, re.I):
            problems.append(f"{spec['id']:03d}: superseded application stack requirement")
    return problems


def render(spec):
    deps = "[" + ", ".join(f"{d:03d}" for d in spec["deps"]) + "]"
    constraints = []
    for key in ("categories", "required_categories"):
        if key in spec:
            constraints.append(f"**{key}:** " + ", ".join(spec[key]) + ".")
    return TEMPLATE.format(
        architecture=ARCHITECTURE, architecture_digest=architecture_digest(),
        sequence=next(i for i, s in enumerate(execution_order(), 1) if s['id'] == spec['id']),
        id=spec["id"],
        title=spec["title"],
        area=spec["area"],
        size=spec["size"],
        parallel="true" if spec["parallel"] else "false",
        phase=spec["phase"], tier=spec["tier"], write_paths=json.dumps(spec["write_paths"]),
        source=next(f"specs_{letter}.py" for letter, items in zip("abcdef", (A, B, C, D, E, F))
                    if any(s["id"] == spec["id"] for s in items)),
        constraints=("\n\n" + "\n".join(constraints)) if constraints else "",
        deps=deps,
        goal=spec["goal"],
        scope=bullets(spec["scope"]),
        delivery='\n'.join(f'{i}. {step}' for i, step in enumerate(spec['delivery'], 1)),
        out=bullets(spec["out"]),
        accept=checks(spec["accept"]),
        security=spec["security"],
        test=spec["test"],
    )


def manifest():
    sequence = {s['id']: i for i, s in enumerate(execution_order(), 1)}
    return {
        "schema_version": 2,
        "architecture": ARCHITECTURE,
        "architecture_digest": architecture_digest(),
        "generator": "demo/forum/tools/generate_features.py",
        "plan": "demo/forum/PLAN.md",
        "count": len(SPECS),
        "features": [
            {
                "id": f"{s['id']:03d}",
                "sequence": sequence[s['id']],
                "title": s["title"],
                "area": s["area"],
                "size": s["size"],
                "parallel": s["parallel"],
                "phase": s["phase"], "tier": s["tier"], "write_paths": s["write_paths"],
                "depends_on": [f"{d:03d}" for d in s["deps"]],
                "file": f"{s['id']:03d}-{slug(s['title'])}.md",
                "architecture": ARCHITECTURE,
                "architecture_digest": architecture_digest(),
                **{key: s[key] for key in ("categories", "required_categories") if key in s},
            }
            for s in SPECS
        ],
    }


def index():
    lines = [
        "# Feature index",
        "",
        "Generated by `tools/generate_features.py`; edit canonical `tools/specs_*.py`, then regenerate.",
        "All 100 features target [Quarkus + PostgreSQL + React web](../ARCHITECTURE.md).",
        "The contract is",
        "[PLAN.md](../PLAN.md). Build one feature, or queue several: the queue honours `depends_on`",
        "and refuses a `parallel: false` feature beside another build.",
        "",
        "All builders use tier 3. IDs are not execution order; dependencies may have higher IDs.",
        "Read this table from top to bottom: its sequence puts every prerequisite before its consumer.",
        "Each MD has three small delivery steps; scope and protected acceptance remain the completion contract.",
        "Parallel work also requires disjoint declared write scopes and separate worktrees.",
        "",
        "| Sequence | Stable ID | Feature | Area | Phase | Size | Parallel | Depends on |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for sequence, spec in enumerate(execution_order(), 1):
        deps = ", ".join(f"{d:03d}" for d in spec["deps"]) or "—"
        parallel = "yes" if spec["parallel"] else "no"
        file = f"{spec['id']:03d}-{slug(spec['title'])}.md"
        lines.append(f"| {sequence:03d} | {spec['id']:03d} | [{spec['title']}]({file}) | {spec['area']} | {spec['phase']} | {spec['size']} | {parallel} | {deps} |")
    counts = {}
    for spec in SPECS:
        counts[spec["area"]] = counts.get(spec["area"], 0) + 1
    lines += ["", "Areas: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + ".", ""]
    return "\n".join(lines)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def review_snapshot(name):
    """Keep the review copy's local links valid from its extra directory level."""
    def rebase(match):
        target = match.group(1)
        return "](" + (target if re.match(r"(?:[a-z]+:|#|/)", target) else "../" + target) + ")"
    return re.sub(r"\]\(([^\s)]+)\)", rebase, (ROOT / name).read_text(encoding="utf-8"))


def main(argv):
    problems = validate()
    if problems:
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        return 1
    files = {f"{s['id']:03d}-{slug(s['title'])}.md": render(s) for s in SPECS}
    files["README.md"] = index()
    files["MANIFEST.json"] = json.dumps(manifest(), indent=2) + "\n"
    review = {name: review_snapshot(name) for name in ("PLAN.md", "ECOSYSTEM.md")}
    if "--check" in argv:
        changed = [name for name, text in files.items()
                   if not (OUT / name).exists() or (OUT / name).read_text(encoding="utf-8") != text]
        stale = [p.name for p in OUT.glob("*.md") if p.name not in files]
        changed += ["openAI/" + name for name, text in review.items()
                    if not (ROOT / "openAI" / name).exists()
                    or (ROOT / "openAI" / name).read_text(encoding="utf-8") != text]
        if changed or stale:
            print(f"FAIL {len(changed)} stale, {len(stale)} orphan file(s): {', '.join(sorted(changed + stale))[:200]}",
                  file=sys.stderr)
            return 1
        print(f"PASS {len(files) - 2} features, manifest, index and review snapshots up to date")
        return 0
    for name, text in files.items():
        write(OUT / name, text)
    for name, text in review.items():
        write(ROOT / "openAI" / name, text)
    removed = sorted(p.name for p in OUT.glob("*.md") if p.name not in files)
    for name in removed:
        (OUT / name).unlink()
    print(f"wrote {len(files) - 2} features, README.md and MANIFEST.json to {OUT}"
          + (f"; removed {len(removed)} orphan file(s): {', '.join(removed)}" if removed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
