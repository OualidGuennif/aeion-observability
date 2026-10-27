"""Test-only stand-in for an OpenShell sandbox: runs the real helper, bash and Deno on this host.

It has no isolation and never writes qualification evidence; real qualification uses OpenShell.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

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

    def close(self):
        self.closed = True
