"""Test-only stand-in for an OpenShell sandbox: runs the real helper, bash and Deno on this host.

It has no isolation and never writes qualification evidence; real qualification uses OpenShell.
"""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

from sandbox import COLLECT_SCRIPT, MAX_SYNC_BYTES, SANDBOX_OUT, SEED_SCRIPT, materialize

DEMO = Path(__file__).resolve().parents[1]
IMAGE_PATHS = {"/opt/demo/fs-helper.py": str(DEMO / "agent/fs-helper.py"),
               "/opt/demo/fixtures/check-scenario.js": str(DEMO / "fixtures/check-scenario.js")}


class LocalSandbox:
    def __init__(self, run=None, root=None, role="agent"):
        self.calls = []
        self.ref = SimpleNamespace(id=f"local-{role}")
        self.closed = False

    def exec(self, argv, *, stdin=None, env=None, workdir=None, timeout=15):
        if self.closed:
            raise ValueError("SANDBOX_CLOSED")
        self.calls.append(list(argv))
        deno = os.environ.get("AEION_TEST_DENO") or shutil.which("deno") or "deno"
        argv = [sys.executable if a == "python3" else deno if a == "deno" else IMAGE_PATHS.get(a, a) for a in argv]
        done = subprocess.run(argv, input=stdin, capture_output=True, cwd=workdir, timeout=timeout,
                              env={"PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/tmp"), **(env or {})})
        return SimpleNamespace(stdout=done.stdout, stderr=done.stderr, exit_code=done.returncode)

    def seed_in(self, files, destination=SANDBOX_OUT):
        encoded = {}
        total = 0
        for relative, data in files.items():
            blob = base64.b64encode(data).decode("ascii")
            total += len(blob)
            if total > MAX_SYNC_BYTES:
                raise ValueError("SANDBOX_SEED_TOO_LARGE")
            encoded[relative] = blob
        result = self.exec(["python3", "-c", SEED_SCRIPT, destination],
                           stdin=json.dumps(encoded).encode("utf-8"), timeout=60)
        if result.exit_code != 0:
            raise ValueError("SANDBOX_SEED_FAILED")
        return int(result.stdout.strip() or 0)

    def collect(self, source=SANDBOX_OUT):
        result = self.exec(["python3", "-c", COLLECT_SCRIPT, source, str(MAX_SYNC_BYTES)], timeout=60)
        if result.exit_code != 0:
            raise ValueError("SANDBOX_SYNC_FAILED")
        try:
            return json.loads(result.stdout)
        except ValueError as exc:
            raise ValueError("SANDBOX_SYNC_UNREADABLE") from exc

    def sync_out(self, destination, source=SANDBOX_OUT):
        return materialize(self.collect(source), destination)

    def close(self):
        self.closed = True
