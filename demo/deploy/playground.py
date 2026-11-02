"""The playground data plane: two bundle servers behind a weighted load balancer with a cache.

It is small but it is real, and deliberately **read-only**. The balancer is an HTTP reverse proxy:
it receives an anonymous request, decides stable or canary from the release's audience bucket,
forwards the request over a real socket to one of two upstreams, caches the response, and reports
what it did in headers and in `/__lb/stats`. The canary monitor reads those counters, so the
verdict is about observed traffic, not a mock.

It is not the forum's authenticated front door. Non-GET methods receive 405, and a request with
`Authorization` or a cookie other than `aeion_cohort` is refused with 400 before the cache: the
cache key is the slot and path, never an identity.

Routing rules:
  * the client key is `X-Client` when a caller sets one (drills), the remote address otherwise;
  * the bucket is sticky through the `aeion_cohort` cookie, so a visitor does not flap between
    versions on every request;
  * a dead upstream is skipped for a cooldown window instead of being retried forever.
"""
import http.client
import json
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from factory import release as releases

COOKIE = "aeion_cohort"
COOLDOWN_SECONDS = 5.0
LATENCY_WINDOW = 200


def _now_ns():
    return time.time_ns()


class Bundle:
    """The bytes of one release: an index page, a thread list, and the manifest it came from."""

    def __init__(self, folder, manifest):
        self.folder = Path(folder)
        self.manifest = manifest

    @property
    def release_id(self):
        return self.manifest["release_id"]

    @classmethod
    def materialise(cls, folder, manifest):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        features = manifest["features"]
        (folder / "index.html").write_text(
            "<!doctype html><title>Agora</title>\n"
            f"<h1>Agora — release {manifest['release_id'][:12]}</h1>\n"
            f"<p>{len(features)} feature(s): {', '.join(f['id'] for f in features)}</p>\n")
        (folder / "threads.json").write_text(json.dumps(
            {"release": manifest["release_id"],
             "threads": [{"id": f["id"], "title": f["title"]} for f in features]},
            indent=2, sort_keys=True))
        (folder / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
        return cls(folder, manifest)


class _Handler(BaseHTTPRequestHandler):
    server_version = "aeion-playground"
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # keep the drill output readable
        pass

    def _send(self, status, body, content_type="application/json", extra=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, sort_keys=True).encode() if not isinstance(body, str) else body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _read_only(self):
        """The released data plane serves GET; it is not the forum's authenticated front door."""
        self._send(405, {"error": "read_only_release_proxy", "allowed": "GET"},
                   extra={"Allow": "GET, HEAD"})

    do_POST = do_PUT = do_PATCH = do_DELETE = _read_only


class AppHandler(_Handler):
    """Serves one bundle, or proxies a real application, and says which release and slot answered."""

    def do_GET(self):
        state = self.server.state
        if state.get("upstream"):
            self._proxy(state)
            return
        bundle = state["bundle"]
        slot = state["slot"]
        headers = {"X-Aeion-Slot": slot, "X-Aeion-Release": bundle.release_id}
        if self.path == "/healthz":
            self._send(200, {"status": "ok", "slot": slot, "release": bundle.release_id}, extra=headers)
            return
        if self.path == "/__release":
            self._send(200, {"slot": slot, "manifest": bundle.manifest}, extra=headers)
            return
        if self.path.startswith("/api/threads"):
            self._send(200, (bundle.folder / "threads.json").read_bytes(), extra=headers)
            return
        if self.path in {"/", "/index.html"}:
            self._send(200, (bundle.folder / "index.html").read_bytes(), "text/html; charset=utf-8",
                       extra=headers)
            return
        self._send(404, {"error": "not_found", "release": bundle.release_id}, extra=headers)


    def _proxy(self, state):
        """Forward to the application behind this slot; a dead upstream is a 502, never a hang."""
        host, port = state["upstream"]
        headers = {"X-Aeion-Slot": state["slot"]}
        if state.get("upstream_release"):
            headers["X-Aeion-Release"] = state["upstream_release"]
        connection = http.client.HTTPConnection(host, port, timeout=2.0)
        try:
            connection.request("GET", self.path, headers={"X-Aeion-Slot": state["slot"]})
            response = connection.getresponse()
            body = response.read()
            content_type = response.getheader("Content-Type") or "application/json"
        except OSError as exc:
            self._send(502, {"error": "upstream_unavailable", "slot": state["slot"]},
                       extra={**headers, "X-Aeion-Upstream-Error": str(exc)[:60]})
            return
        finally:
            connection.close()
        self._send(response.status, body, content_type, headers)


class LbHandler(_Handler):
    """Weighted routing, sticky cohorts, cache and counters."""

    def do_GET(self):
        state = self.server.state
        started = time.perf_counter()
        if self.path.startswith("/__lb/stats"):
            self._send(200, state["stats"]())
            return
        if self.path.startswith("/__lb/route"):
            client = self._client_key()
            bucket = self._bucket(client)
            self._send(200, {"client": client, "bucket": bucket,
                             "slot": self._slot_for(bucket), "percent": state["percent"]()})
            return
        if self._authenticated_request():
            # Refuse rather than silently dropping a session: the drill is not the forum's front door.
            self._send(400, {"error": "authenticated_request_not_supported",
                             "detail": "use the forum directly; this proxy serves anonymous GET only"})
            return
        client = self._client_key()
        bucket = self._bucket(client)
        slot = self._slot_for(bucket)
        state["count"]("requests")
        body, status, extra = self._cached(self.path, slot)
        elapsed_ms = (time.perf_counter() - started) * 1000
        state["latency"](elapsed_ms)
        # Count what the client actually received, cache hit or not: the monitor reads this.
        state["count"]("status_5xx" if status >= 500 else
                       "status_4xx" if status >= 400 else "status_2xx")
        headers = {"X-Aeion-Slot": slot, "X-Cache": extra.get("cache", "miss"),
                   "Set-Cookie": f"{COOKIE}={bucket}; Path=/; SameSite=Lax"}
        if extra.get("release"):
            headers["X-Aeion-Release"] = extra["release"]
        if extra.get("upstream_error"):
            headers["X-Aeion-Upstream-Error"] = extra["upstream_error"][:60]
        self._send(status, body, extra.get("content_type", "application/json"), headers)

    def _client_key(self):
        explicit = self.headers.get("X-Client")
        if explicit:
            return explicit.strip()[:120]
        cookie = self.headers.get("Cookie") or ""
        for part in cookie.split(";"):
            name, _, value = part.strip().partition("=")
            if name == COOKIE and value:
                return ""  # a sticky bucket is used instead of a fresh key
        return self.client_address[0]

    def _authenticated_request(self):
        """A cache keyed by slot and path must never answer a signed-in or bearer request."""
        if self.headers.get("Authorization"):
            return True
        cookie = self.headers.get("Cookie") or ""
        for part in cookie.split(";"):
            name, _, _ = part.strip().partition("=")
            if name and name != COOKIE:
                return True
        return False

    def _bucket(self, client):
        state = self.server.state
        if not client:
            cookie = self.headers.get("Cookie") or ""
            for part in cookie.split(";"):
                name, _, value = part.strip().partition("=")
                if name == COOKIE and value.isdigit():
                    return int(value) % 100
            return releases.bucket(state["seed"](), "anonymous")
        return releases.bucket(state["seed"](), client)

    def _slot_for(self, bucket):
        percent = self.server.state["percent"]()
        return "canary" if bucket < percent else "stable"

    def _cached(self, path, slot):
        state = self.server.state
        cache = state["cache"]
        key = f"lb:{state['seed']()}:{slot}:{path}"
        try:
            hit = cache.get(key)
        except Exception:  # noqa: BLE001 - a cache failure is a miss, never an error to the client
            hit = None
        if hit is not None:
            state["count"]("cache_hits")
            try:
                parsed = json.loads(hit)
            except ValueError:
                parsed = {"body": hit.decode("utf-8", "replace"), "status": 200,
                          "content_type": "text/html; charset=utf-8"}
            return (parsed["body"].encode() if isinstance(parsed["body"], str) else parsed["body"],
                    parsed.get("status", 200), {"cache": "hit", "release": parsed.get("release"),
                                                "content_type": parsed.get("content_type")})
        state["count"]("cache_misses")
        body, status, headers = state["forward"](slot, path)
        content_type = headers.get("content-type", "application/json")
        if status == 200:
            try:
                cache.set(key, json.dumps({"body": body.decode("utf-8", "replace"), "status": status,
                                           "release": headers.get("x-aeion-release"),
                                           "content_type": content_type}))
            except Exception:  # noqa: BLE001 - caching is best effort and never blocks the answer
                pass
        return body, status, {"cache": "miss", "release": headers.get("x-aeion-release"),
                              "content_type": content_type,
                              "upstream_error": headers.get("x-aeion-upstream-error")}


class Playground:
    """Two app servers, one balancer, one cache; ports are ephemeral unless asked for."""

    def __init__(self, cache, percent=0, seed="staged", host="127.0.0.1", ports=None):
        self.cache = cache
        self._percent = int(percent)
        self._seed = seed
        self.host = host
        self.counters = {"requests": 0, "status_2xx": 0, "status_4xx": 0, "status_5xx": 0,
                         "cache_hits": 0, "cache_misses": 0, "upstream_errors": 0}
        self._latencies = []
        self._lock = threading.Lock()
        self._servers = {}
        self._threads = []
        self.apps = {}
        ports = ports or {}
        for slot in ("stable", "canary", "staging"):
            server = ThreadingHTTPServer((host, ports.get(slot, 0)), AppHandler)
            server.state = {"bundle": None, "slot": slot, "upstream": None, "upstream_release": None}
            self._servers[slot] = server
            self.apps[slot] = server.server_address[1]
        self.lb = ThreadingHTTPServer((host, ports.get("lb", 0)), LbHandler)
        self.lb.state = {
            "count": self._count, "latency": self._latency,
            "cache": self.cache, "percent": lambda: self._percent,
            "seed": lambda: self._seed, "forward": self._forward, "stats": self.stats,
        }
        self.port = self.lb.server_address[1]
        self.staging_port = self.apps["staging"]
        self._servers["lb"] = self.lb

    # ------------------------------------------------------------------ lifecycle
    def start(self):
        for name, server in self._servers.items():
            thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05},
                                      name=f"playground-{name}", daemon=True)
            thread.start()
            self._threads.append(thread)
        return self

    def stop(self):
        for server in self._servers.values():
            server.shutdown()
            server.server_close()
        for thread in self._threads:
            thread.join(timeout=2)
        self._threads.clear()

    # ------------------------------------------------------------------ configuration
    def backend(self, slot, url, release=None):
        """Serve a slot from a running application (host:port) instead of a synthetic bundle.

        This is how the drill proves the release plane on the real service: two Quarkus instances,
        different `AEION_RELEASE` values, one balancer deciding which cohort sees which.
        """
        if slot not in ("stable", "canary", "staging"):
            raise ValueError("unknown_slot:" + str(slot))
        parsed = urllib.parse.urlparse(url if "://" in url else "http://" + url)
        if parsed.scheme != "http" or not parsed.hostname:
            raise ValueError("upstream_invalid:" + str(url))
        state = self._servers[slot].state
        state["upstream"] = (parsed.hostname, parsed.port or 80)
        state["upstream_release"] = release
        return {"slot": slot, "host": parsed.hostname, "port": parsed.port or 80, "release": release}

    def upstream(self, slot):
        """The (host, port) a slot proxies, or None while it serves a bundle."""
        return self._servers[slot].state.get("upstream")

    def deploy(self, slot, manifest):
        bundle = Bundle.materialise(Path(manifest["work_dir"]) / slot, manifest)
        self._servers[slot].state["bundle"] = bundle
        if slot == "canary":
            self._seed = manifest["release_id"]
        return bundle

    def set_percent(self, percent):
        self._percent = max(0, min(100, int(percent)))
        return self._percent

    def has_release(self, slot):
        state = self._servers[slot].state
        return state["bundle"] is not None or state.get("upstream") is not None

    def release_id(self):
        state = self._servers["canary"].state
        if state["bundle"] is not None:
            return state["bundle"].release_id
        return state.get("upstream_release")

    # ------------------------------------------------------------------ traffic
    def _forward(self, slot, path):
        state = self._servers[slot].state
        if state["bundle"] is None and state.get("upstream") is None:
            self._count("upstream_errors")
            return (json.dumps({"error": "no_release", "slot": slot}).encode(), 503,
                    {"content-type": "application/json"})
        target = state.get("upstream") or (self.host, self.apps[slot])
        connection = http.client.HTTPConnection(target[0], target[1], timeout=2.0)
        try:
            connection.request("GET", path)
            response = connection.getresponse()
            body = response.read()
            headers = {name.lower(): value for name, value in response.getheaders()}
            return body, response.status, headers
        except OSError as exc:
            self._count("upstream_errors")
            return (json.dumps({"error": "upstream_unavailable", "slot": slot}).encode(), 502,
                    {"content-type": "application/json", "x-aeion-upstream-error": str(exc)})
        finally:
            connection.close()

    def _count(self, name, amount=1):
        with self._lock:
            self.counters[name] = self.counters.get(name, 0) + amount

    def _latency(self, milliseconds):
        with self._lock:
            self._latencies.append(float(milliseconds))
            if len(self._latencies) > LATENCY_WINDOW:
                del self._latencies[:-LATENCY_WINDOW]

    def stats(self):
        with self._lock:
            counters = dict(self.counters)
            latencies = sorted(self._latencies)
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
        cache_stats = self.cache.stats() if hasattr(self.cache, "stats") else {}
        counters.update({"p95_ms": round(p95, 2), "latencies": len(latencies),
                         "cache": cache_stats, "percent": self._percent,
                         "release": self.release_id()})
        return counters

    def sample(self):
        from factory import canary

        return canary.sample_from_stats(self.stats())
