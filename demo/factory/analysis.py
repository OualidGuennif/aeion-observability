"""Activate the template's architecture integrations (Graphify + Archify) in a target clone.

The factory clones a product repository into an agent workspace; before any agent touches
it, the pinned analysis integrations must be installed and proven reachable. Installation
happens in the ignored ``.aeion/integrations`` directory and never modifies tracked files.
A missing integration definition is reported, never invented.
"""
import json
import shutil
import subprocess
from pathlib import Path

SETUP = Path("tools/architecture/setup")
INTEGRATIONS = Path("tools/architecture/integrations.json")
GRAPHIFY_PYTHON = Path(".aeion/integrations/graphify-venv/bin/python")
ARCHIFY_CLI = Path(".aeion/integrations/archify/archify/bin/archify.mjs")
# Pi loads the factory skills and hooks only through this extension; Flue does not add it.
PI_EXTENSION = Path(".pi/extensions/factory/index.js")


class AnalysisError(ValueError):
    """An analysis integration that cannot be activated."""


def definition(repo):
    """Return the pinned integration revisions, or raise when the template is absent."""
    repo = Path(repo)
    manifest = repo / INTEGRATIONS
    if not manifest.is_file():
        raise AnalysisError("integration_missing:integrations.json")
    if not (repo / SETUP).is_file():
        raise AnalysisError("integration_missing:setup")
    try:
        data = json.loads(manifest.read_text())
    except ValueError as exc:
        raise AnalysisError("integration_unreadable") from exc
    graphify = data.get("graphify") or {}
    archify = data.get("archify") or {}
    return {
        "graphify_revision": graphify.get("revision"),
        "graphify_version": graphify.get("version"),
        "archify_revision": archify.get("revision"),
    }


def state(repo):
    """Report what is actually installed, without touching the network."""
    repo = Path(repo)
    return {
        "graphify": (repo / GRAPHIFY_PYTHON).is_file(),
        "archify": (repo / ARCHIFY_CLI).is_file(),
    }


def pi_extension(repo):
    """Pi must be started with this extension or the factory skills and hooks never load."""
    repo = Path(repo)
    return {
        "path": str(PI_EXTENSION),
        "present": (repo / PI_EXTENSION).is_file(),
        "required_flag": f"pi -e {PI_EXTENSION}",
    }


def activate(repo, timeout=900, run=subprocess.run):
    """Install the pinned integrations in the clone and prove they are reachable."""
    repo = Path(repo).resolve()
    pinned = definition(repo)
    if state(repo) == {"graphify": True, "archify": True}:
        return {"status": "already_active", **pinned}
    setup = repo / SETUP
    completed = run(["python3", str(setup)], cwd=str(repo), timeout=timeout,
                    capture_output=True, text=True)
    if completed.returncode != 0:
        raise AnalysisError(f"setup_failed:{completed.returncode}")
    installed = state(repo)
    if not all(installed.values()):
        raise AnalysisError("integration_incomplete:" + ",".join(k for k, v in installed.items() if not v))
    return {"status": "activated", **pinned, "graphify": True, "archify": True}


def clone(repo_url, destination, branch=None, timeout=300, run=subprocess.run):
    """Shallow-clone a product repository into the agent workspace root."""
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise AnalysisError("clone_destination_not_empty")
    destination.parent.mkdir(parents=True, exist_ok=True)
    argv = ["git", "clone", "--depth", "1"]
    if branch:
        argv += ["--branch", branch]
    argv += [repo_url, str(destination)]
    completed = run(argv, timeout=timeout, capture_output=True, text=True)
    if completed.returncode != 0:
        raise AnalysisError(f"clone_failed:{completed.returncode}")
    return destination


def prepare(repo_url, destination, branch=None, timeout=900, run=subprocess.run):
    """Clone, then activate: the single entry point the factory uses before an agent runs."""
    path = clone(repo_url, destination, branch=branch, run=run)
    receipt = activate(path, run=run)
    receipt["clone"] = str(path)
    receipt["branch"] = branch
    receipt["pi_extension"] = pi_extension(path)
    return receipt


def tools_available():
    """Report the host tools the activation needs, so a missing one fails early and clearly."""
    return {"git": shutil.which("git") is not None,
            "node": shutil.which("node") is not None,
            "python3": shutil.which("python3") is not None}


def main(argv=None):
    """Clone a product repository into an agent workspace and activate its analysis tools."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--dest", required=True)
    parser.add_argument("--branch")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)
    missing = [name for name, present in tools_available().items() if not present]
    if missing:
        print(json.dumps({"ok": False, "reason": "missing_host_tools", "tools": missing}))
        return 2
    try:
        receipt = prepare(args.repo_url, args.dest, branch=args.branch, timeout=args.timeout)
    except AnalysisError as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}))
        return 1
    print(json.dumps({"ok": True, **receipt}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
