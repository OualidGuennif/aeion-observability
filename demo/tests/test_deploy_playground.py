"""The playground is a data plane: real proxy hops, sticky cohorts, a cache and counters."""
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deploy.cache import FileCache
from deploy.playground import Playground
from factory import release as releases

FEATURES = [{"id": "001", "title": "App skeleton", "digest": "a" * 64},
            {"id": "002", "title": "Settings", "digest": "b" * 64}]


def manifest(rid, root):
    return {"release_id": rid, "features": FEATURES, "work_dir": str(root)}


class PlaygroundTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rid = releases.release_id(FEATURES)
        self.cache = FileCache(self.root / "cache", ttl=30)
        self.playground = Playground(self.cache, seed=self.rid, percent=25).start()
        self.addCleanup(self.playground.stop)
        self.playground.deploy("stable", manifest("stable-0000", self.root))
        self.playground.deploy("canary", manifest(self.rid, self.root))

    def get(self, path, client=None, cookie=None, headers_only=False):
        request = urllib.request.Request(f"http://127.0.0.1:{self.playground.port}{path}")
        if client:
            request.add_header("X-Client", client)
        if cookie:
            request.add_header("Cookie", cookie)
        with urllib.request.urlopen(request) as response:
            body = response.read()
            return (response.status, dict(response.headers), body) if not headers_only else response.headers

    def clients(self, count, predicate):
        found = [f"agent-{index}" for index in range(count)]
        return [client for client in found if predicate(releases.bucket(self.rid, client))]

    def test_routing_splits_the_population_at_the_release_percent(self):
        canary = self.clients(400, lambda bucket: bucket < 25)[0]
        stable = self.clients(400, lambda bucket: bucket >= 25)[0]
        self.assertEqual(self.get("/api/threads", client=canary)[1]["X-Aeion-Slot"], "canary")
        self.assertEqual(self.get("/api/threads", client=stable)[1]["X-Aeion-Slot"], "stable")

    def test_the_cohort_is_sticky_through_the_cookie(self):
        client = self.clients(400, lambda bucket: bucket < 25)[0]
        status, headers, _ = self.get("/api/threads", client=client)
        cookie = headers["Set-Cookie"].split(";")[0]
        again = self.get("/api/threads", cookie=cookie)[1]
        self.assertEqual(again["X-Aeion-Slot"], "canary")
        self.assertEqual(cookie, f"aeion_cohort={releases.bucket(self.rid, client)}")

    def test_percent_zero_and_hundred_are_absolute(self):
        client = self.clients(400, lambda bucket: bucket < 25)[0]
        self.playground.set_percent(0)
        self.assertEqual(self.get("/api/threads", client=client)[1]["X-Aeion-Slot"], "stable")
        self.playground.set_percent(100)
        self.assertEqual(self.get("/api/threads", client=client)[1]["X-Aeion-Slot"], "canary")

    def test_the_cache_answers_the_second_request(self):
        client = self.clients(400, lambda bucket: bucket < 25)[0]
        first = self.get("/api/threads", client=client)[1]
        second = self.get("/api/threads", client=client)[1]
        self.assertEqual(first["X-Cache"], "miss")
        self.assertEqual(second["X-Cache"], "hit")
        stats = self.playground.stats()
        self.assertGreaterEqual(stats["cache_hits"], 1)

    def test_the_answer_names_the_release_that_served_it(self):
        client = self.clients(400, lambda bucket: bucket < 25)[0]
        headers = self.get("/api/threads", client=client)[1]
        self.assertEqual(headers["X-Aeion-Release"], self.rid)

    def test_stats_are_a_json_snapshot_the_monitor_can_read(self):
        client = self.clients(400, lambda bucket: bucket < 25)[0]
        self.get("/api/threads", client=client)
        status, _, body = self.get("/__lb/stats")
        self.assertEqual(status, 200)
        self.assertIn(b"requests", body)
        stats = self.playground.stats()
        self.assertGreaterEqual(stats["requests"], 1)
        self.assertGreaterEqual(stats["status_2xx"], 1)
        self.assertEqual(stats["percent"], 25)
        self.assertEqual(stats["release"], self.rid)

    def test_a_sample_is_what_the_monitor_expects(self):
        sample = self.playground.sample()
        self.assertIn("error_rate", sample)
        self.assertIn("cache_hit_rate", sample)

    def test_a_slot_without_a_release_fails_closed(self):
        """No bundle deployed means no traffic: 503, never an empty page that looks healthy."""
        empty = Playground(FileCache(self.root / "cache2"), seed=self.rid, percent=100).start()
        self.addCleanup(empty.stop)
        request = urllib.request.Request(
            f"http://127.0.0.1:{empty.port}/api/threads", headers={"X-Client": "agent-1"})
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(caught.exception.code, 503)
        caught.exception.close()

    def test_route_inspection_matches_the_routing(self):
        client = self.clients(400, lambda bucket: bucket < 25)[0]
        status, _, body = self.get("/__lb/route", client=client)
        self.assertEqual(status, 200)
        self.assertIn(b'"slot": "canary"', body)

    def expect_error(self, request):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        failure = caught.exception
        body = failure.read()
        failure.close()
        return failure.code, dict(failure.headers), body

    def test_mutations_are_refused_with_a_clear_method(self):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.playground.port}/api/threads", data=b"{}",
            headers={"Content-Type": "application/json"}, method="POST")
        code, headers, body = self.expect_error(request)
        self.assertEqual(code, 405)
        self.assertEqual(headers["Allow"], "GET, HEAD")
        self.assertIn("read_only_release_proxy", body.decode())

    def test_a_session_cookie_is_refused_before_the_cache(self):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.playground.port}/api/threads",
            headers={"Cookie": "aeion_session=abc"})
        code, _, body = self.expect_error(request)
        self.assertEqual(code, 400)
        self.assertIn("authenticated_request_not_supported", body.decode())

    def test_an_authorization_header_is_refused_before_the_cache(self):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.playground.port}/api/threads",
            headers={"Authorization": "Bearer token"})
        code, _, body = self.expect_error(request)
        self.assertEqual(code, 400)
        self.assertIn("authenticated_request_not_supported", body.decode())


class UpstreamSlotTests(unittest.TestCase):
    """A slot can serve a real application instead of a synthetic bundle: two instances, one LB."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.instances = {}

        def instance(release):
            handler = self.make_handler(release)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            return server.server_address[1]

        self.stable_port = instance("stable-real")
        self.canary_port = instance("canary-real")
        self.playground = Playground(FileCache(self.root / "cache", ttl=30), percent=0,
                                     seed="upstream-seed").start()
        self.addCleanup(self.playground.stop)
        self.playground.backend("stable", f"127.0.0.1:{self.stable_port}", release="stable-real")
        self.playground.backend("canary", f"127.0.0.1:{self.canary_port}", release="canary-real")

    @staticmethod
    def make_handler(release):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                body = json.dumps({"release": release, "path": self.path}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return Handler

    def get(self, path, client="10.0.0.1"):
        request = urllib.request.Request(self.url(path), headers={"X-Client": client})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as failure:
            body = failure.read()
            failure.close()
            return failure.code, dict(failure.headers), body

    def url(self, path):
        return f"http://127.0.0.1:{self.playground.port}{path}"

    def test_a_slot_serves_the_real_application_and_names_its_release(self):
        self.assertTrue(self.playground.has_release("stable"))
        status, headers, body = self.get("/healthz")
        self.assertEqual(200, status)
        self.assertEqual("stable", headers["X-Aeion-Slot"])
        self.assertIn(b"stable-real", body)

    def test_the_percentage_decides_which_instance_answers(self):
        self.playground.set_percent(25)
        canary = [client for client in (f"10.1.0.{index}" for index in range(1, 400))
                  if releases.bucket("upstream-seed", client) < 25]
        self.assertTrue(canary, "the seed must produce a canary cohort")
        for client in canary[:5]:
            status, headers, body = self.get("/api/threads", client=client)
            self.assertEqual(200, status)
            self.assertEqual("canary", headers["X-Aeion-Slot"])
            self.assertIn(b"canary-real", body)
        status, headers, _ = self.get("/api/threads", client="not-in-the-cohort")
        self.assertEqual("stable", headers["X-Aeion-Slot"])

    def test_a_dead_upstream_is_a_502_not_a_hang(self):
        self.playground.backend("stable", "127.0.0.1:1", release="gone")
        status, headers, body = self.get("/healthz")
        self.assertEqual(502, status)
        self.assertIn("upstream_unavailable", body.decode())

    def test_an_invalid_upstream_is_refused(self):
        with self.assertRaises(ValueError):
            self.playground.backend("stable", "https://example.test:443")
        with self.assertRaises(ValueError):
            self.playground.backend("nope", "127.0.0.1:9")


if __name__ == "__main__":
    unittest.main()
