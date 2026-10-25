"""Loopback-published demo UI; fixed task only, one active run, no shell endpoint."""
import json
import os
from pathlib import Path
import re
import threading
import time
import uuid
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from runner import Runner
from telemetry import Telemetry
from memory import Memory
from kpis import summarize
from audit import Audit
from scores import publish

DATA = Path("/data")
DATA.mkdir(mode=0o700, exist_ok=True)
LOCK = threading.Lock()
SAVE_LOCK = threading.Lock()
PROFILES = {"glm": "opencode-go/glm-5.3-flash", "deepseek": "opencode-go/deepseek-v4.1-flash"}


def save(run):
    with SAVE_LOCK:
        path = DATA / (run["id"] + ".json")
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(run))
        temporary.chmod(0o600)
        temporary.replace(path)


for path in DATA.glob("*.json"):
    previous = json.loads(path.read_text())
    if previous["status"] == "running":
        previous["status"] = "interrupted"
        save(previous)
    if previous.get("postprocessing"):
        previous["postprocessing"] = False
        save(previous)

memory = Memory()
runner = Runner(Telemetry(), save, memory=memory, audit=Audit(DATA))


def live_ready():
    model = os.environ.get("DEMO_MODEL", "")
    # Freeze the qualified Go tuple. Never silently fall back to Zen or a free model.
    return bool(os.environ.get("OPENCODE_API_KEY") and model == "opencode-go/glm-5.3-flash" and not (DATA / "context.blocked").exists())


def execute(run):
    try:
        runner.run(run)
        if run.get("failure") in {"PROVIDER_CONTEXT_VIOLATION", "CONTEXT_ACCOUNTING_MISMATCH"}:
            (DATA / "context.blocked").write_text("Profile requires context-accounting requalification.\n")
        try:
            run["langfuse_scores"] = publish(run)
            runner.event(run, "quality.scored", **{"aeion.check.passed": run.get("check", {}).get("passed", 0)})
        except Exception:
            run["langfuse_scores"] = {"status": "unavailable"}
        run["memory"] = {"status": "pending"}
        save(run)
        try:
            run["memory"] = memory.retain(run)
            runner.event(run, "memory.retained", **{"aeion.memory.backend": "hindsight"})
        except Exception:
            run["memory"] = {"status": "unavailable"}
        save(run)
    finally:
        run["postprocessing"] = False
        save(run)
        LOCK.release()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def respond(self, code, body, content_type="application/json"):
        payload = body if isinstance(body, bytes) else body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        artifact = re.fullmatch(r"/api/runs/([a-f0-9]{32})/(logs|handover)", self.path)
        if artifact:
            run_id, kind = artifact.groups()
            path = DATA / (run_id + ".events.jsonl") if kind == "logs" else Path("/work") / run_id / "workspace/HANDOVER.md"
            if path.is_file() and not path.is_symlink() and path.stat().st_size <= 1100000:
                self.respond(200, path.read_bytes(), "application/x-ndjson" if kind == "logs" else "text/markdown; charset=utf-8")
            else:
                self.respond(404, {"error": "not_available"})
        elif self.path in {"/assets/agent-atelier.png", "/fonts/Manrope.woff2", "/fonts/CormorantGaramond.woff2"}:
            content_type = "image/png" if self.path.endswith(".png") else "font/woff2"
            self.respond(200, (Path(__file__).parent / self.path[1:]).read_bytes(), content_type)
        elif self.path in {"/", "/app.js", "/style.css"}:
            name = "index.html" if self.path == "/" else self.path[1:]
            content_type = {"index.html": "text/html; charset=utf-8", "app.js": "text/javascript", "style.css": "text/css"}[name]
            self.respond(200, (Path(__file__).parent / name).read_text(), content_type)
        elif self.path == "/api/health":
            self.respond(200, {"status": "ok", "live_ready": live_ready(), "model": os.environ.get("DEMO_MODEL", ""),
                               "limit": int(os.environ.get("DEMO_CONTEXT_LIMIT", "250000")),
                               "metric": os.environ.get("DEMO_CONTEXT_METRIC", "active_context")})
        elif self.path == "/api/integrations":
            from memory import request
            targets = {"otel": ("http://otel-collector:13133", "/"),
                       "langfuse": ("http://langfuse-web:3000", "/api/public/health"),
                       "hindsight": ("http://hindsight:8888", "/health"),
                       "claude_mem": ("http://claude-mem:37777", "/health"),
                       "playground": ("http://playground:8000", "/health")}
            statuses = {}
            for name, (base, path) in targets.items():
                try:
                    request(base, path, timeout=2)
                    statuses[name] = "connected"
                except Exception:
                    statuses[name] = "unavailable"
            self.respond(200, statuses)
        elif self.path == "/api/runs":
            self.respond(200, sorted([json.loads(p.read_text()) for p in DATA.glob("*.json")],
                                     key=lambda r: r["started_ns"], reverse=True))
        elif self.path == "/api/kpis":
            self.respond(200, summarize([json.loads(p.read_text()) for p in DATA.glob("*.json")]))
        elif self.path in {"/api/memory", "/api/memory?synthetic=true"}:
            try:
                self.respond(200, memory.recall(synthetic="synthetic=true" in self.path))
            except Exception:
                self.respond(503, {"status": "unavailable", "results": []})
        else:
            self.respond(404, {"error": "not_found"})

    def do_POST(self):
        # Block browser cross-origin submissions/DNS rebinding; no CORS or form requests.
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        if not re.fullmatch(r"(?:127\.0\.0\.1|localhost)(?::\d+)?", host) or (origin and origin != "http://" + host):
            self.respond(403, {"error": "origin_denied"})
            return
        if self.path != "/api/runs" or self.headers.get("Content-Type") != "application/json":
            self.respond(400, {"error": "invalid_request"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1024:
                raise ValueError
            request = json.loads(self.rfile.read(length))
            if (not isinstance(request, dict) or set(request) - {"mode", "profile", "run_id"}
                    or request.get("mode") not in {"simulation", "live", "intervention"}
                    or request.get("profile", "glm") not in PROFILES):
                raise ValueError
        except (ValueError, TypeError):
            self.respond(400, {"error": "invalid_request"})
            return
        if request["mode"] == "live" and not live_ready():
            self.respond(409, {"error": "live_not_configured"})
            return
        if request["mode"] == "live" and request.get("profile") == "deepseek" and datetime.date.today() > datetime.date(2026, 10, 31):
            self.respond(409, {"error": "deepseek_privacy_requalification_required"})
            return
        if request["mode"] == "intervention":
            run_id = request.get("run_id", "")
            if not isinstance(run_id, str) or not re.fullmatch(r"[a-f0-9]{32}", run_id) or not (DATA / (run_id + ".json")).is_file():
                self.respond(404, {"error": "not_found"})
                return
            if not LOCK.acquire(blocking=False):
                self.respond(409, {"error": "run_active"})
                return
            try:
                run = json.loads((DATA / (run_id + ".json")).read_text())
                if not run.get("human_interventions"):
                    run["human_interventions"] = 1  # Explicit attestation, idempotent.
                    runner.event(run, "human.intervention.recorded", **{"aeion.human.interventions": 1})
                save(run)
                try:
                    run["langfuse_scores"] = publish(run)
                except Exception:
                    run["langfuse_scores"] = {"status": "unavailable"}
                try:
                    run["memory"] = memory.retain(run)
                except Exception:
                    run["memory"] = {"status": "unavailable"}
                save(run)
                self.respond(200, {"status": "marked_assisted"})
            finally:
                LOCK.release()
            return
        if len(list(DATA.glob("*.json"))) >= 20:
            self.respond(409, {"error": "demo_run_limit_20"})
            return
        if not LOCK.acquire(blocking=False):
            self.respond(409, {"error": "run_active"})
            return
        run = {"id": uuid.uuid4().hex, "status": "running", "synthetic": request["mode"] == "simulation",
               "started_ns": time.time_ns(), "events": [], "sessions": [], "agents": 0,
               "human_interventions": 0,
               "postprocessing": True,
               "usage_complete": True,
               "task_id": "pricing-js-v1", "profile_version": "go-build-v2-counted", "native_cost_usd": "0", "model": PROFILES[request.get("profile", "glm")],
               "limit": int(os.environ.get("DEMO_CONTEXT_LIMIT", "250000")),
               "metric": os.environ.get("DEMO_CONTEXT_METRIC", "active_context")}
        if run["metric"] not in {"active_context", "cumulative_input"} or not 1 <= run["limit"] <= 250000:
            LOCK.release()
            self.respond(409, {"error": "invalid_gate_configuration"})
            return
        save(run)
        threading.Thread(target=execute, args=(run,), daemon=True).start()
        self.respond(202, {"id": run["id"]})


ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
