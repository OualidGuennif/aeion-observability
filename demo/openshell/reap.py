"""Reap orphaned OpenShell Docker containers left behind by an interrupted run.

The gateway normally deletes both containers of a sandbox. A killed qualification or a gateway
restart can leave the supervisor/sandbox pair running with nothing tracking them, which burns CPU
forever. This host-side tool removes only containers carrying OpenShell's own managed-by label
and only when they are older than the safety window; it never touches the Langfuse, cockpit or
forum containers.

Dry run by default:

    python3 demo/openshell/reap.py --older-than 3600
    python3 demo/openshell/reap.py --older-than 3600 --execute
"""
import argparse
from datetime import datetime
import json
import subprocess
import sys
import time

LABEL = "openshell.ai/managed-by=openshell"
NAMESPACE = "aeion-observability"
DEFAULT_OLDER_THAN = 3600


def _docker(*args, check=True):
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=check)


def created_timestamp(value):
    """Docker's RFC3339Nano timestamp to epoch seconds; malformed evidence is skipped."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


def container_ages(ids, now=None, docker=None):
    """Return [(id, name, age_seconds)] for containers whose creation time is readable."""
    now = time.time() if now is None else now
    docker = docker or _docker
    result = []
    for container_id in ids:
        try:
            payload = json.loads(docker("inspect", container_id).stdout)[0]
        except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError, TypeError):
            continue
        created = created_timestamp(payload.get("Created"))
        if created is None:
            continue
        name = str(payload.get("Name") or container_id).lstrip("/")
        result.append((container_id, name, max(0.0, now - created)))
    return result


def stale_ids(ids, older_than=DEFAULT_OLDER_THAN, now=None, docker=None):
    return [container_id for container_id, _, age in container_ages(ids, now=now, docker=docker)
            if age >= older_than]


def managed_ids(docker=None):
    docker = docker or _docker
    result = docker("ps", "-q", "--filter", f"label={LABEL}",
                    "--filter", f"label=openshell.ai/sandbox-namespace={NAMESPACE}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def reap(older_than=DEFAULT_OLDER_THAN, execute=False, now=None, docker=None):
    """Return the container names selected; remove them only when execute is true."""
    docker = docker or _docker
    candidates = stale_ids(managed_ids(docker), older_than=older_than, now=now, docker=docker)
    names = [name for _, name, _ in container_ages(candidates, now=now, docker=docker)]
    if execute:
        for container_id in candidates:
            docker("rm", "-f", container_id)
    return names


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--older-than", type=int, default=DEFAULT_OLDER_THAN,
                        help="seconds a container must have existed before it is stale")
    parser.add_argument("--execute", action="store_true", help="actually remove; default is a dry run")
    args = parser.parse_args(argv)
    if args.older_than < 600:
        parser.error("--older-than must be at least 600 seconds")
    names = reap(older_than=args.older_than, execute=args.execute)
    print(json.dumps({"execute": args.execute, "count": len(names), "containers": names}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
