# Spec: knowledge/operations/build-and-test.md
"""The project's files: from git when the folder is a repository, from the file system otherwise.

Many people run Æion Factory in a plain folder, so no check may require git just to list files."""
import fnmatch
import os
import subprocess
from pathlib import Path

# Never walked without git, at any depth: version control, installed dependencies, caches and local state.
SKIPPED = {".git", ".aeion", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".tox",
           ".terraform"}
# Skipped at the project root only: build output and vendored code there, a source folder of that name deeper.
TOP_SKIPPED = {"vendor", "dist", "build", "target", "out", "coverage", "htmlcov", "env", ".next", ".cache", ".gradle"}
# Files the desktop rewrites on its own: listed, they would change the project between two reads.
SKIPPED_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def git_active(root):
    """True when the root is its own git work tree; a broken repository (a .git git cannot read) is an error.

    A plain folder nested inside another repository is not that repository: its files are not tracked there,
    so git would list none of them."""
    try:
        result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree", "--show-prefix"], cwd=root,
                                capture_output=True, text=True, check=False)
    except OSError:
        result = None
    # An empty prefix means the root is the top level; it also holds when the path's letter case differs.
    lines = result.stdout.split("\n") if result is not None and result.returncode == 0 else []
    active = len(lines) >= 2 and lines[0] == "true" and lines[1] == ""
    if not active and (Path(root) / ".git").exists():
        raise subprocess.CalledProcessError(result.returncode if result else 127, "git rev-parse")
    return active


def ignore_rules(folder):
    """The simple rules of a folder's .gitignore, as (pattern, directories only): a name or glob with
    no inner slash, optionally ending in /. Negations and anchored or nested paths are not read, so
    the files they would hide stay listed: an unknown rule fails toward checking more, not less."""
    try:
        lines = (Path(folder) / ".gitignore").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    rules = []
    for line in (raw.strip() for raw in lines):
        directory_only = line.endswith("/")
        pattern = line.rstrip("/")
        if not pattern or pattern.startswith(("#", "!")) or "/" in pattern or "\\" in pattern:
            continue
        rules.append((pattern, directory_only))
    return rules


def ignored(name, is_directory, rules):
    return any(fnmatch.fnmatchcase(name, pattern) and (is_directory or not directory_only)
               for pattern, directory_only in rules)


def git_files(root, *args):
    """Relative paths from one git ls-files call; a failure is an error, never an empty project."""
    # check=True: the hooks that catch SubprocessError already fail closed on it.
    result = subprocess.run(["git", "ls-files", "-z", *args], cwd=root, capture_output=True, check=True)
    return [os.fsdecode(raw) for raw in result.stdout.split(b"\0") if raw]


def project_files(root, untracked=False):
    """Sorted relative paths: tracked files (plus untracked, unignored ones when asked) under git, else a walk."""
    root = Path(root)
    if git_active(root):
        paths = git_files(root)
        if untracked:
            paths += git_files(root, "--others", "--exclude-standard")
        return sorted(set(paths))
    paths, rules = [], {}
    # os.walk does not follow directory symlinks, so the walk stays inside the project.
    for folder, folders, files in os.walk(root):
        top = Path(folder) == root
        # A folder's .gitignore applies to it and below, as git reads it (simple rules only).
        here = rules.get(folder, []) + ignore_rules(folder)
        folders[:] = [name for name in folders if name not in SKIPPED and not (top and name in TOP_SKIPPED)
                      and not ignored(name, True, here)]
        for name in folders:
            rules[os.path.join(folder, name)] = here
        relative = Path(folder).relative_to(root)
        paths += [(relative / name).as_posix() for name in files
                  if name not in SKIPPED_FILES and not ignored(name, False, here)]
    return sorted(paths)


def nested_projects(files):
    """Folders below the root holding a project of their own (AGENTS.md and knowledge/index.md side by side).

    Their Spec pointers name their own knowledge/ and their code is theirs: doc-links and the code graph
    leave them to the nested project's own checks."""
    listed = set(files)
    return {rel[:-len("/knowledge/index.md")] for rel in listed
            if rel.endswith("/knowledge/index.md") and rel[:-len("knowledge/index.md")] + "AGENTS.md" in listed}


def inside(rel, folders):
    return any(rel.startswith(folder + "/") for folder in folders)
