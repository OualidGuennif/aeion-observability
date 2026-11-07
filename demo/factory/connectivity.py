"""Decide whether a stopped author was still working, and check the provider before spending.

Spec: knowledge/components/factory-flue.md

A product exception or a CLI stop after the agent has already been using tools is an
interruption: the same model continues in the same workspace. A stop before that work
exists is a crash and starts another model. A network stop resumes the same model even
when little work was saved. Nothing here calls a model or reads a secret.
"""
import importlib.util
import re
import socket
import time
from pathlib import Path

# Three tool steps, forwarded requests, or tool/model progress events is "still working".
# One or two steps is a startup death and stays on the crash path.
WORKING_FLOOR = 3
MAX_SAME_MODEL_RESUMES = 3
PROBE_HOST = 'opencode.ai'
PROBE_PORT = 443
PROBE_GAP_SECONDS = 1
PROBE_TIMEOUT_SECONDS = 3

# The provider could not be reached. Resume the same role; do not treat it as a bad model.
NETWORK_STOPS = frozenset({
    'TRANSPORT_ERROR', 'PROVIDER_UNAVAILABLE', 'PROVIDER_TIMEOUT', 'PROVIDER_RATE_LIMITED',
})
# A harness stop that is a crash only when the session never got going.
INTERRUPTIBLE_STOPS = frozenset({'CLI_FAILED', 'CLI_PROTOCOL_ERROR', 'HARNESS_COMPACTION'})
REMOTE_PHASES = frozenset({'publishing', 'waiting_ci', 'merging'})
TOOL_PHASES = frozenset({'tool.finished', 'gen_ai.request', 'model.step.started'})
RESUME_TRIGGERS = frozenset({'cli_interrupted', 'network', 'lease_expired'})
CHECK_NAME = re.compile(r'^aeion-check-[0-9a-f]{12}$')
PG_NAME = re.compile(r'^aeion-check-pg-[0-9a-f]{16}$')
MODEL_NAME = re.compile(r'^[A-Za-z0-9_./-]{1,80}$')
# A qualification sandbox has no factory lease. Removing every idle pair at once deletes
# that sandbox while its owner is still stopping it. Thirty minutes outlives one admission
# command and still clears a pair left behind by a cancel.
ORPHAN_MIN_AGE = 1800


def _count(value):
    return value if type(value) is int and value >= 0 else 0


def session_was_working(execution, tool_events=0):
    """True when the agent had already been working, not merely that a process existed.

    ``execution`` is the builder's bounded result (step and forward counts). ``tool_events``
    is how many tool or model progress events the supervisor already stored. A finish reason
    alone is not enough: one step that ends on toolUse is not a calm working session.
    """
    execution = execution if isinstance(execution, dict) else {}
    return (_count(execution.get('cli_steps')) >= WORKING_FLOOR
            or _count(execution.get('forwarded_count')) >= WORKING_FLOOR
            or _count(tool_events) >= WORKING_FLOOR)


def same_model_resume(stop_code, execution, tool_events=0):
    """True when this stop should continue the same model instead of burning an attempt.

    A network cut resumes even with no saved steps. A CLI stop resumes only when the
    session was already working. A startup failure and a real provider error do not.
    """
    if stop_code in NETWORK_STOPS:
        return True
    return stop_code in INTERRUPTIBLE_STOPS and session_was_working(execution, tool_events)


def resume_trigger(stop_code):
    return 'network' if stop_code in NETWORK_STOPS else 'cli_interrupted'


def probe_twice(connect, sleep=None, gap=PROBE_GAP_SECONDS):
    """Both connects must succeed. One failure or an exception means the provider is down."""
    pause = sleep if sleep is not None else time.sleep
    for attempt in range(2):
        try:
            if connect() is not True:
                return False
        except OSError:
            return False
        if attempt == 0:
            pause(gap)
    return True


def connect_host(host=PROBE_HOST, port=PROBE_PORT, timeout=PROBE_TIMEOUT_SECONDS):
    """Open a TCP connection and close it. Raises OSError when the host is unreachable."""
    with socket.create_connection((host, port), timeout=timeout):
        return True


class Connectivity:
    """The live controller's provider probe and orphan-container reap. Tests inject both."""

    def __init__(self, connect=None, docker=None, sleep=None):
        self._connect = connect or connect_host
        self._docker = docker
        self._sleep = sleep

    def reachable(self):
        return probe_twice(self._connect, sleep=self._sleep)

    def reap(self, store_path):
        """Remove exited check containers, then aged OpenShell orphans when no lease is active."""
        docker = self._docker or load_reaper()._docker
        removed = reap_exited_checks(docker)
        try:
            reaper = load_reaper()
            if reaper.lease_state(store=store_path).get('state') == 'idle':
                report = reaper.sweep(older_than=ORPHAN_MIN_AGE, execute=True, docker=docker, store=store_path)
                removed.extend(report.get('removed') or [])
        except (OSError, RuntimeError, TypeError, ValueError):
            pass
        return removed


def load_reaper():
    """Load the host reaper by file path.

    The installed OpenShell package owns the name ``openshell``. This repository's
    reaper is a script beside it, not that package, so a normal import cannot see it.
    """
    path = Path(__file__).resolve().parents[1] / "openshell" / "reap.py"
    spec = importlib.util.spec_from_file_location("aeion_openshell_reap", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reap_idle(store_path, docker=None):
    """Remove leftover OpenShell pairs when no build lease is active.

    A pair younger than ``ORPHAN_MIN_AGE`` stays. Qualification runs outside the factory
    lease, and deleting its sandbox makes the sandbox stop look like a failure.
    """
    return load_reaper().sweep(
        older_than=ORPHAN_MIN_AGE, execute=True, docker=docker, store=store_path)


def reap_exited_checks(docker):
    """Remove finished protected-check containers by their exact names. Leave everything else."""
    try:
        listed = docker('ps', '-a', '--filter', 'status=exited', '--format', '{{.Names}}', check=False)
    except (OSError, RuntimeError, TypeError, ValueError):
        return []
    removed = []
    for name in (getattr(listed, 'stdout', '') or '').splitlines():
        name = name.strip()
        if not (CHECK_NAME.fullmatch(name) or PG_NAME.fullmatch(name)):
            continue
        try:
            docker('rm', '-f', name, check=False)
        except (OSError, RuntimeError, TypeError, ValueError):
            continue
        removed.append(name)
    return removed
