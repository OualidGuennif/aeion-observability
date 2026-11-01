"""Drill: two real Quarkus instances behind the release plane's balancer and cache.

What this proves, and what it does not, stated up front:

* it **starts two real forum instances** (the built jar, two SQLite files, two releases), registers
  them as the `stable` and `canary` backends of `deploy.playground`, and sends traffic through the
  load balancer, so the split is decided by a running process, not by a fixture;
* it **does not** replace the release service: promotion, the canary verdicts and the dwells stay
  where they are (`factory/releases.py`, `factory/canary.py`). This is the data plane against the
  real application, which was the missing piece.

Run:
  PYTHONPATH=demo demo/.local/venv/bin/python demo/deploy/drill_real_slots.py --requests 400
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from deploy.cache import FileCache, RedisCache, parse_url  # noqa: E402
from deploy.playground import Playground  # noqa: E402
from factory import release as releases  # noqa: E402

JAR = ROOT / "forum-app/build/quarkus-app/quarkus-run.jar"
SECRET = "drill-real-slots-secret-0123456789abcdef"


def free_port():
    import socket
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_instance(release, database, port):
    """Start the built jar on its own port and database; wait until it answers /healthz."""
    environment = dict(os.environ)
    environment.update({
        "AEION_SQLITE_PATH": str(database),
        "AEION_RELEASE": release,
        "AEION_FORUM_PORT": str(port),
        "AGORA_SESSION_SECRET": SECRET,
    })
    process = subprocess.Popen(["java", "-jar", str(JAR)], env=environment,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 60
    while time.time() < deadline:
        if process.poll() is not None:
            raise SystemExit(f"instance {release} exited with {process.returncode}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1) as response:
                if response.status == 200:
                    return process
        except OSError:
            time.sleep(0.25)
    process.kill()
    raise SystemExit(f"instance {release} never answered on {port}")


def stop(process):
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def fetch(url, client):
    request = urllib.request.Request(url, headers={"X-Client": client})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as failure:
        body = failure.read()
        failure.close()
        return failure.code, dict(failure.headers), body


def main(argv=None):
    parser = argparse.ArgumentParser(description="Two real instances behind the release plane")
    parser.add_argument("--requests", type=int, default=400)
    parser.add_argument("--percent", type=int, default=25)
    parser.add_argument("--redis", default=os.environ.get("AEION_REDIS_URL", ""))
    arguments = parser.parse_args(argv)
    if not JAR.exists():
        raise SystemExit(f"build the application first: {JAR} is missing")

    work = Path(tempfile.mkdtemp(prefix="real-slots-"))
    report = {"work": str(work), "steps": []}
    stable_port, canary_port = free_port(), free_port()
    stable = canary = None
    cache_kind = "file"
    if arguments.redis:
        try:
            cache = RedisCache(arguments.redis, ttl=30)
            cache.get("drill:probe")  # fail here, not mid-traffic, if the daemon is unreachable
            cache_kind = "redis"
        except Exception as error:  # noqa: BLE001 - the drill falls back, and says so
            report["redis_error"] = f"{type(error).__name__}: {error}"
            cache = FileCache(work / "cache", ttl=30)
    else:
        cache = FileCache(work / "cache", ttl=30)

    try:
        stable = start_instance("stable-real", work / "stable.db", stable_port)
        canary = start_instance("canary-real", work / "canary.db", canary_port)
        report["steps"].append({"step": "instances", "stable_port": stable_port,
                                "canary_port": canary_port})

        playground = Playground(cache, percent=arguments.percent, seed="drill-real",
                                ports={"lb": 0}).start()
        try:
            playground.backend("stable", f"127.0.0.1:{stable_port}", release="stable-real")
            playground.backend("canary", f"127.0.0.1:{canary_port}", release="canary-real")
            playground.set_percent(arguments.percent)
            base = f"http://127.0.0.1:{playground.port}"
            clients = [f"10.{index // 200}.{index % 200}.{index % 251}" for index in range(arguments.requests)]
            served = {"stable": 0, "canary": 0}
            statuses = {}
            for index, client in enumerate(clients):
                status, headers, body = fetch(base + "/healthz", client)
                slot = headers.get("X-Aeion-Slot", "?")
                served[slot] = served.get(slot, 0) + 1
                statuses[status] = statuses.get(status, 0) + 1
            expected_canary = sum(1 for client in clients if releases.bucket("drill-real", client)
                                  < arguments.percent)
            report["steps"].append({
                "step": "traffic", "requests": arguments.requests, "percent": arguments.percent,
                "served": served, "statuses": statuses,
                "expected_canary": expected_canary,
                "canary_matches_routing": served.get("canary", 0) == expected_canary,
            })
            # The cache answers the second identical request from the same slot.
            first = fetch(base + "/api/threads", "10.0.0.1")
            second = fetch(base + "/api/threads", "10.0.0.1")
            report["steps"].append({
                "step": "cache", "backend": cache_kind,
                "first": first[1].get("X-Cache"), "second": second[1].get("X-Cache"),
                "same_body": first[2] == second[2],
            })
            stats = playground.stats()
            report["steps"].append({"step": "stats", "requests": stats["requests"],
                                    "status_2xx": stats["status_2xx"], "status_5xx": stats["status_5xx"],
                                    "cache_hits": stats["cache_hits"],
                                    "cache_misses": stats["cache_misses"],
                                    "p95_ms": stats["p95_ms"]})
        finally:
            playground.stop()
    finally:
        stop(stable)
        stop(canary)

    traffic = report["steps"][1]
    cache_step = report["steps"][2]
    report["ok"] = bool(
        traffic["statuses"].get(200, 0) == arguments.requests
        and not traffic["statuses"].get(500)
        and traffic["canary_matches_routing"]
        and traffic["served"].get("stable", 0) > 0
        and cache_step["second"] == "hit"
        and cache_step["same_body"]
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
