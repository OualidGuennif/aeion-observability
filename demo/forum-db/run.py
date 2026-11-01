"""The HTTP surface of the SQLite service, and its command line.

Five endpoints, all read-only except the two that operate on snapshots:

  GET  /healthz                 the file exists, opens, and passes `quick_check`
  GET  /v1/stats                size, pages, WAL size, journal mode, row counts
  GET  /v1/snapshots            published snapshots, newest first, digest recomputed now
  POST /v1/snapshot             take one, verify it, prune the old ones
  POST /v1/restore-drill        restore the newest (or a named) snapshot into scratch and prove it

The service is a guardian: it does not proxy SQL and it does not write rows. `--writer` takes an
exclusive lease so a second writer cannot start, which is the property that keeps SQLite predictable
with thousands of agents in front of it.
"""
import argparse
import json
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from service import ServiceError, SqliteService

MAX_BODY = 4096


def make_server(service, host="127.0.0.1", port=0):
    """Start the HTTP server; return (server, thread-ready callable) so a test can bind port 0."""
    handler = _handler_for(service)
    return ThreadingHTTPServer((host, port), handler)


def _handler_for(service):
    class Handler(BaseHTTPRequestHandler):
        server_version = "agora-sqlite/1.0"
        protocol_version = "HTTP/1.1"

        def do_GET(self):  # noqa: N802 - http.server names its verbs
            route = urllib.parse.urlparse(self.path).path
            if route == "/healthz":
                self._answer(*health(service))
            elif route == "/v1/stats":
                self._guarded(lambda: (200, service.stats()))
            elif route == "/v1/snapshots":
                self._guarded(lambda: (200, {"snapshots": service.snapshots(), "keep": service.keep}))
            else:
                self._answer(404, {"error": "unknown_route", "route": route})

        def do_POST(self):  # noqa: N802
            route = urllib.parse.urlparse(self.path).path
            body = self._body()
            if body is None:
                return
            if route == "/v1/snapshot":
                self._guarded(lambda: (201, service.snapshot(label=body.get("label") or "manual")))
            elif route == "/v1/restore-drill":
                self._guarded(lambda: (200, service.restore_drill(body.get("snapshot"))))
            else:
                self._answer(404, {"error": "unknown_route", "route": route})

        def _body(self):
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                self._answer(400, {"error": "content_length_invalid"})
                return None
            if length > MAX_BODY:
                self._answer(413, {"error": "body_too_large", "limit": MAX_BODY})
                return None
            raw = self.rfile.read(length) if length else b"{}"
            try:
                return json.loads(raw or b"{}")
            except json.JSONDecodeError:
                self._answer(400, {"error": "body_not_json"})
                return None

        def _guarded(self, operation):
            try:
                status, payload = operation()
            except ServiceError as refusal:
                message = str(refusal)
                code = message.split(":", 1)[0]
                status = 409 if code in {"writer_lease_held", "restore_unusable"} else 400
                self._answer(status, {"error": code, "detail": message})
            except Exception as failure:  # pragma: no cover - surfaced as a 500, never swallowed
                self._answer(500, {"error": "internal", "detail": type(failure).__name__})
            else:
                self._answer(status, payload)

        def _answer(self, status, payload):
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):  # keep the drill output readable
            return

    return Handler


def health(service):
    """Liveness that means something: the file opens and `quick_check` says ok."""
    try:
        report = service.integrity()
    except ServiceError as refusal:
        return 503, {"status": "unavailable", "error": str(refusal)}
    if not report["ok"]:
        return 503, {"status": "corrupt", "detail": report}
    return 200, {"status": "ok", "database": str(service.database), "tables": report["tables"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Guardian service for the Agora SQLite database")
    parser.add_argument("--database", required=True)
    parser.add_argument("--snapshots", default=None)
    parser.add_argument("--keep", type=int, default=None)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--writer", action="store_true",
                        help="take the exclusive writer lease; refuse if another writer holds it")
    parser.add_argument("--once", choices=["integrity", "snapshot", "stats"], default=None,
                        help="run one operation, print JSON, exit")
    parser.add_argument("--label", default="manual")
    arguments = parser.parse_args(argv)
    snapshot_dir = arguments.snapshots or str(Path(arguments.database).resolve().parent / "snapshots")
    service = SqliteService(arguments.database, snapshot_dir, keep=arguments.keep)
    try:
        if arguments.writer:
            service.take_writer_lease()
        if arguments.once == "integrity":
            print(json.dumps(service.integrity(), indent=2, sort_keys=True))
            return 0
        if arguments.once == "stats":
            print(json.dumps(service.stats(), indent=2, sort_keys=True))
            return 0
        if arguments.once == "snapshot":
            print(json.dumps(service.snapshot(label=arguments.label), indent=2, sort_keys=True))
            print(json.dumps({"pruned": service.prune()}, indent=2, sort_keys=True))
            return 0
    except ServiceError as refusal:
        print(json.dumps({"error": str(refusal)}), file=sys.stderr)
        return 2
    server = make_server(service, host=arguments.host, port=arguments.port)
    host, port = server.server_address
    print(json.dumps({"listening": "http://%s:%d" % (host, port),
                      "database": str(service.database),
                      "snapshots": str(service.snapshot_dir),
                      "writer": bool(arguments.writer)}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
        service.release_writer_lease()
    return 0


if __name__ == "__main__":
    sys.exit(main())
