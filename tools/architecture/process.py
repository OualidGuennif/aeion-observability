# Spec: knowledge/operations/architecture-maintenance.md
"""Bound integration commands and terminate their ordinary descendant processes on timeout."""
import os
import signal
import subprocess


def run(command, *, cwd=None, timeout=180, **options):
    process = subprocess.Popen(command, cwd=cwd, start_new_session=True, **options)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command, stdout, stderr)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
