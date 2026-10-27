"""Runs only inside OpenShell. Own/reap the CLI process group, without a shell."""
import json
import os
import subprocess
import sys

if sys.argv[1] != 'run' or os.getuid() != 10001:
    raise SystemExit(77)
process = subprocess.Popen(sys.argv[2:], start_new_session=True, stderr=None if os.environ.get("AEION_FIXTURE_DEBUG")=="true" else subprocess.DEVNULL)
print(json.dumps({'aeion_process_pid': process.pid}), flush=True)
raise SystemExit(process.wait())
