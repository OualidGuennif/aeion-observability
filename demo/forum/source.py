"""Keep the demo's product snapshot owned by the product repository.

The factory builds the forum from `demo/forum-app`, hashes its baseline and packages it for
Compose, but the canonical source lives in `aeion-autonomous-forum`. Those three directories are
therefore a read-only snapshot: `demo/forum/source.json` pins the product commit and
`demo/forum/source.lock.json` records every file digest. Hand edits here are drift, not work.

    python3 demo/forum/source.py --check
    python3 demo/forum/source.py --refresh --product demo/.local/factory/agents/aeion-autonomous-forum

`--check` is the default and needs only this checkout. `--refresh` re-copies the pinned commit
from a product checkout that contains it (read from the object store, so the checkout may be
ahead), refuses a dirty snapshot, and rewrites the lock. It never pushes or checks out the
product.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "demo/forum/source.json"
LOCK = "demo/forum/source.lock.json"
DEFAULT_PRODUCT = ROOT / "demo/.local/factory/agents/aeion-autonomous-forum"


class SourceError(ValueError):
    """A snapshot that cannot be trusted."""


def _load(root, relative):
    try:
        return json.loads((Path(root) / relative).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SourceError(f"unreadable:{relative}") from exc


def _valid_paths(paths):
    """Snapshot roots must be relative repository paths, never escapes."""
    if not paths:
        raise SourceError("snapshot_paths_missing")
    for path in paths:
        parts = PurePosixPath(path).parts
        if not parts or ".." in parts or PurePosixPath(path).is_absolute():
            raise SourceError("snapshot_path_invalid")
    return paths


def tracked(root, paths):
    """Every tracked path under the snapshot roots, relative to the repository."""
    completed = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", *paths],
                               capture_output=True, check=False)
    if completed.returncode != 0:
        raise SourceError("not_a_git_checkout")
    return sorted(part for part in completed.stdout.decode("utf-8", "replace").split("\0") if part)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compare(root, expected, paths):
    """The three drift lists a lock can produce: missing, changed and unexpected files."""
    root = Path(root)
    present = {path for path in tracked(root, paths) if (root / path).is_file()}
    changed = [path for path in sorted(present & set(expected))
               if digest((root / path).read_bytes()) != expected[path]]
    return {
        "missing": sorted(set(expected) - present),
        "changed": changed,
        "unexpected": sorted(present - set(expected)),
    }


def check(root=ROOT):
    """Verify the snapshot against its lock and its pinned commit."""
    source, lock = _load(root, SOURCE), _load(root, LOCK)
    drift = compare(root, lock.get("files") or {}, _valid_paths(source.get("paths") or []))
    ok = not any(drift.values()) and source.get("commit") == lock.get("commit")
    return {"ok": ok, "commit": lock.get("commit"), "files": len(lock.get("files") or {}),
            "drift": drift}


def _snapshot(product, commit, paths):
    """The pinned files as bytes, read from the product's object store.

    `git archive` cannot be used: the product repository marks `/demo` export-ignore, so the
    archives it produces deliberately omit the snapshot paths.
    """
    listing = subprocess.run(["git", "-C", str(product), "ls-tree", "-r", "-z", commit, "--", *paths],
                             capture_output=True, check=False)
    if listing.returncode != 0:
        raise SourceError("product_commit_missing")
    blobs = {}
    for record in listing.stdout.split(b"\0"):
        if not record:
            continue
        meta, _, name = record.partition(b"\t")
        fields = meta.split()
        if len(fields) != 3 or fields[1] != b"blob":
            continue
        mode = fields[0].decode("ascii", "replace")
        if mode not in {"100644", "100755"}:
            # A symlink or submodule would change shape if copied as a regular file.
            raise SourceError("product_entry_not_a_file")
        parts = PurePosixPath(name.decode("utf-8", "replace")).parts
        if not parts or parts[0] == "..":
            continue
        blob = subprocess.run(["git", "-C", str(product), "cat-file", "blob", fields[2].decode()],
                              capture_output=True, check=False)
        if blob.returncode != 0:
            raise SourceError("product_blob_missing")
        blobs[name.decode("utf-8")] = (blob.stdout, mode == "100755")
    if not blobs:
        raise SourceError("product_snapshot_empty")
    return blobs


def refresh(root=ROOT, product=DEFAULT_PRODUCT):
    """Re-copy the pinned commit into the snapshot and rewrite the lock."""
    root, product = Path(root), Path(product)
    source = _load(root, SOURCE)
    paths, commit = _valid_paths(source["paths"]), source["commit"]
    status = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", *paths],
                            capture_output=True, text=True, check=False)
    if status.returncode != 0:
        raise SourceError("not_a_git_checkout")
    if status.stdout.strip():
        raise SourceError("mirror_dirty")
    blobs = _snapshot(product, commit, paths)
    previous = set(tracked(root, paths))
    removed = sorted(previous - set(blobs))
    for path in removed:
        (root / path).unlink()
    for name, (data, executable) in blobs.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if executable:
            target.chmod(0o755)
    lock = {"commit": commit,
            "files": {name: digest(data) for name, (data, _) in sorted(blobs.items())}}
    (root / LOCK).write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    return {"commit": commit, "files": len(blobs), "removed": len(removed)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the snapshot (default)")
    parser.add_argument("--refresh", action="store_true", help="re-copy the pinned commit and rewrite the lock")
    parser.add_argument("--product", default=str(DEFAULT_PRODUCT),
                        help="product checkout that contains the pinned commit")
    parser.add_argument("--root", default=str(ROOT), help="repository to verify or update")
    args = parser.parse_args(argv)
    if args.refresh and args.check:
        parser.error("choose --check or --refresh")
    try:
        report = refresh(root=args.root, product=args.product) if args.refresh else check(args.root)
    except SourceError as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0 if (args.refresh or report["ok"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
