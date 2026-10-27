"""Flue file verbs inside OpenShell, as the agent UID under Landlock; argv in, one JSON line out."""
import base64
import json
import os
import shutil
import stat
import sys

LIMIT = 1048576


def fail(op, path, error):
    print(json.dumps({"ok": False, "error": f"{op} {path}: {error.strerror or error}"}))
    raise SystemExit(0)


def main():
    if len(sys.argv) < 3 or not sys.argv[2].startswith("/") or "\0" in sys.argv[2]:
        print(json.dumps({"ok": False, "error": "usage: fs-helper OP ABSOLUTE_PATH [--recursive] [--force]"}))
        return
    op, path, flags = sys.argv[1], sys.argv[2], set(sys.argv[3:])
    recursive, force = "--recursive" in flags, "--force" in flags
    try:
        if op == "read":
            if os.path.isdir(path):
                raise IsADirectoryError(21, "Is a directory")
            with open(path, "rb") as source:
                data = source.read(LIMIT + 1)
            if len(data) > LIMIT:
                raise OSError(27, "File larger than 1 MiB")
            result = {"data": base64.b64encode(data).decode()}
        elif op == "write":
            data = sys.stdin.buffer.read(LIMIT + 1)
            if len(data) > LIMIT:
                raise OSError(27, "Content larger than 1 MiB")
            with open(path, "wb") as target:
                target.write(data)
            result = {}
        elif op == "stat":
            link, target = os.lstat(path), os.stat(path)
            result = {"stat": {"isFile": stat.S_ISREG(target.st_mode), "isDirectory": stat.S_ISDIR(target.st_mode),
                               "isSymbolicLink": stat.S_ISLNK(link.st_mode), "size": target.st_size,
                               "mtimeMs": target.st_mtime_ns // 1000000}}
        elif op == "readdir":
            result = {"entries": sorted(os.listdir(path))}
        elif op == "exists":
            result = {"exists": os.path.exists(path)}
        elif op == "mkdir":
            if recursive:
                os.makedirs(path, exist_ok=True)
            else:
                os.mkdir(path)
            result = {}
        elif op == "rm":
            # Shell `rm` semantics: -f tolerates a missing path, -r is required for directories.
            if not os.path.lexists(path):
                if not force:
                    raise FileNotFoundError(2, "No such file or directory")
            elif os.path.isdir(path) and not os.path.islink(path):
                if not recursive:
                    raise IsADirectoryError(21, "Is a directory")
                shutil.rmtree(path)
            else:
                os.unlink(path)
            result = {}
        else:
            print(json.dumps({"ok": False, "error": f"unsupported operation {op}"}))
            return
    except OSError as error:
        fail(op, path, error)
    print(json.dumps({"ok": True, **result}))


if __name__ == "__main__":
    main()
