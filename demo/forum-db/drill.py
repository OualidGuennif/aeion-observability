"""Drill: the SQLite service guards the live forum database while the forum keeps writing.

What is proven, in order, against a real file written by the running Quarkus service:

  1. the database is in WAL, `quick_check` passes, and every table is present;
  2. snapshots taken **while the application writes** are consistent copies (integrity ok, readable);
  3. retention keeps the newest and reports what it deleted;
  4. the restore drill proves a snapshot is usable and says how far behind live it is;
  5. the lease refuses a second writer that owns the same file.

Run: `PYTHONPATH=demo demo/.local/venv/bin/python demo/forum-db/drill.py --database /tmp/agora.db`
"""
import argparse
import json
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from service import ServiceError, SqliteService  # noqa: E402

FORUM = "http://127.0.0.1:8081"


def write_settings(names, stop, written):
    """Keep writing through the forum's own API, so the writer is the real application."""
    index = 0
    while not stop.is_set() and index < names:
        body = json.dumps({"value": "drill-%d" % index}).encode()
        request = urllib.request.Request(FORUM + "/api/settings/drill.%d" % index, data=body,
                                        method="PUT", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status == 200:
                    written.append(index)
        except Exception as error:  # a failed write must not silently pass as a sample
            written.append(("error", type(error).__name__))
        index += 1


def main(argv=None):
    parser = argparse.ArgumentParser(description="Guardian drill on the live forum database")
    parser.add_argument("--database", default="/tmp/agora.db")
    parser.add_argument("--snapshots", default="/tmp/agora-snapshots")
    parser.add_argument("--keep", type=int, default=3)
    parser.add_argument("--writes", type=int, default=200)
    arguments = parser.parse_args(argv)

    service = SqliteService(arguments.database, arguments.snapshots, keep=arguments.keep)
    report = {"database": str(service.database), "steps": []}

    integrity = service.integrity()
    report["steps"].append({"step": "integrity", **integrity})
    if not integrity["ok"]:
        print(json.dumps(report, indent=2))
        return 2

    stop = threading.Event()
    written = []
    producer = threading.Thread(target=write_settings, args=(arguments.writes, stop, written), daemon=True)
    producer.start()
    records = []
    try:
        for attempt in range(5):
            records.append(service.snapshot(label="live"))
            time.sleep(0.15)
    finally:
        stop.set()
        producer.join(timeout=15)

    failures = [item for item in written if isinstance(item, tuple)]
    report["steps"].append({
        "step": "snapshots_during_writes",
        "written": len(written) - len(failures),
        "write_errors": failures,
        "snapshots": [{"name": record["name"], "bytes": record["bytes"],
                       "integrity": record["integrity"],
                       "settings": record["tables"].get("settings")} for record in records],
    })
    pruned = service.prune()
    retained = service.snapshots()
    report["steps"].append({"step": "retention", "keep": service.keep, "pruned": pruned,
                            "retained": [item["name"] for item in retained]})

    drill = service.restore_drill()
    report["steps"].append({"step": "restore_drill", **drill})

    contender = SqliteService(arguments.database, arguments.snapshots, clock=time.time)
    service.take_writer_lease()
    refusal = ""
    try:
        contender.take_writer_lease()
    except ServiceError as error:
        refusal = str(error)
    finally:
        service.release_writer_lease()
    report["steps"].append({"step": "writer_lease", "second_writer_refused": bool(refusal),
                            "reason": refusal.split(":", 1)[0] if refusal else ""})

    ok = (integrity["ok"] and not failures and drill["ok"] and refusal
          and all(record["integrity"] == "ok" for record in records))
    report["ok"] = bool(ok)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
