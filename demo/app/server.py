"""Loopback-published demo UI; fixed task only, one active run, no shell endpoint."""
import json
import os
from pathlib import Path
import re
import threading
import time
import uuid
import datetime
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from runner import AGENTS, TRIAGE, Runner, tasks
from telemetry import Telemetry
from memory import Memory
from kpis import summarize
from audit import Audit
from scores import publish
from profiles import PROFILES, PROFILE_VERSION, available
from scenarios import SCENARIOS
from selection import recommend
from lifecycle import plan, recover
from settings import DATA, SERVICES, WORK

DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
WORK.mkdir(mode=0o700, parents=True, exist_ok=True)
RUNTIMES = {"flue-just-bash": "Triage · just-bash", "flue-local": "Local assistant · restricted folder",
            "flue-openshell": "Autonomous coding · OpenShell"}
LOCK = threading.Lock()
SAVE_LOCK = threading.Lock()
CAMPAIGNS = DATA / "campaigns"
CAMPAIGNS.mkdir(mode=0o700,exist_ok=True)


def report_paths():
    # Qualification metadata shares /data; only canonical run IDs are reports.
    return [p for p in DATA.glob('*.json') if re.fullmatch(r'[a-f0-9]{32}\.json',p.name)]


def runs():
    return sorted([json.loads(p.read_text()) for p in report_paths()],key=lambda r:r["started_ns"],reverse=True)


def new_run(mode,profile,task_id,objective="balanced",campaign_id=None,runtime="flue-openshell"):
    decision = recommend(runs(),task_id,objective,runtime) if profile=="auto" else {"profile":profile,"basis":"explicit_profile","task_id":task_id,"objective":objective}
    key=decision["profile"]
    if not available(key): raise ValueError("profile_requires_requalification")
    return {"id":uuid.uuid4().hex,"status":"running","synthetic":mode=="simulation","started_ns":time.time_ns(),
        "events":[],"sessions":[],"agents":0,"human_interventions":0,"postprocessing":True,"usage_complete":True,
        "task_id":task_id,"profile_version":PROFILE_VERSION,"native_cost_usd":"0","model":PROFILES[key]["model"],
        "limit":int(os.environ.get("DEMO_CONTEXT_LIMIT","250000")),"metric":os.environ.get("DEMO_CONTEXT_METRIC","active_context"),
        "runtime":runtime,"selection":decision,"campaign_id":campaign_id}


def save_campaign(value):
    path=CAMPAIGNS/(value["id"]+".json");temporary=path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value));temporary.chmod(0o600);temporary.replace(path)


def campaign(value):
    from decimal import Decimal
    total=Decimal(0)
    disabled=set()
    try:
        for repeat,task_id,profile in plan():
            if profile in disabled or not available(profile): continue
            if total>=Decimal(value["budget_estimate_usd"]):
                value["status"]="budget_stopped";return
            if not live_ready() or len(runs())>=100:
                value["status"]="guard_stopped";return
            run=new_run("live",profile,task_id,campaign_id=value["id"])
            value.update(current_task=task_id,current_profile=profile,repeat=repeat+1)
            save(run);save_campaign(value);execute(run,release=False)
            value["run_ids"].append(run["id"])
            total+=Decimal(run["native_cost_usd"]);value["native_cost_estimate_usd"]=str(total);save_campaign(value)
            if run.get("failure", "").startswith("SANDBOX") or not run.get("usage_complete") or run.get("failure") in {"INSUFFICIENT_FUNDS","PROVIDER_CONTEXT_VIOLATION","CONTEXT_ACCOUNTING_MISMATCH","SANDBOX_STOP_FAILED"}:
                value["status"]="guard_stopped";return
            if run.get("failure") in {"MODEL_DISABLED","QUOTA_STOP","GO_REGION_REQUIRED","GO_SUBSCRIPTION_REQUIRED"}: disabled.add(profile)
        value["status"]="completed"
    except Exception:
        value["status"]="failed"
    finally:
        value.update(ended_ns=time.time_ns(),recommendations={task:recommend(runs(),task) for task in SCENARIOS})
        try: value["memory"]=memory.retain_decisions(value)
        except Exception: value["memory"]={"status":"unavailable"}
        save_campaign(value);LOCK.release()



def save(run):
    with SAVE_LOCK:
        path = DATA / (run["id"] + ".json")
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(run))
        temporary.chmod(0o600)
        temporary.replace(path)


for path in report_paths():
    previous = json.loads(path.read_text())
    if recover(previous):
        save(previous)

for path in CAMPAIGNS.glob("*.json"):
    previous=json.loads(path.read_text())
    if recover(previous):
        save_campaign(previous)

memory = Memory()
runner = Runner(Telemetry(), save, memory=memory, audit=Audit(DATA))


def sandbox_ready():
    from sandbox import connection
    try:
        client=connection(timeout=2);client.close();return True
    except Exception:
        return False


def live_ready(runtime="flue-openshell"):
    from sandbox import cli_qualified
    # Tier 1 never touches OpenShell; tiers 2 and 3 verify generated code there.
    return bool(os.environ.get("OPENCODE_API_KEY") and cli_qualified() and (runtime == TRIAGE or sandbox_ready())
                and not (DATA/"context.blocked").exists())


def ready(runtime, mode):
    if mode in {"live", "benchmark"}:
        return live_ready(runtime)
    return mode != "simulation" or runtime == TRIAGE or sandbox_ready()


def execute(run, release=True):
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
        if release: LOCK.release()


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
            path = DATA / (run_id + ".events.jsonl") if kind == "logs" else WORK / run_id / "workspace/HANDOVER.md"
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
        elif self.path == "/api/catalog":
            self.respond(200,{"profiles":{k:{**p,"available":available(k)} for k,p in PROFILES.items()},
                "scenarios":{k:{"name":v["name"],"checks":len(v["cases"])} for k,v in SCENARIOS.items()},
                "runtimes":{r:{"name":RUNTIMES[r],"tasks":list(tasks(r))} for r in AGENTS},
                "triage":{k:{"name":v["name"],"checks":len(v["expected"])} for k,v in tasks(TRIAGE).items()},
                "nvidia_telemetry":False,"profile_version":PROFILE_VERSION})
        elif urlparse(self.path).path == "/api/recommendations":
            query=parse_qs(urlparse(self.path).query)
            objective=query.get("objective",["balanced"])[0]
            runtime=query.get("runtime",["flue-openshell"])[0]
            if objective not in {"balanced","cost","speed"} or runtime not in AGENTS: self.respond(400,{"error":"invalid_selection"});return
            self.respond(200,{task:recommend(runs(),task,objective,runtime) for task in tasks(runtime)})
        elif self.path == "/api/campaigns":
            self.respond(200,sorted([json.loads(p.read_text()) for p in CAMPAIGNS.glob("*.json")],key=lambda v:v["started_ns"],reverse=True))
        elif self.path == "/api/health":
            self.respond(200, {"status": "ok", "live_ready": live_ready(), "sandbox_ready": sandbox_ready(),
                               "ready": {r: {"live": live_ready(r), "simulation": ready(r, "simulation")} for r in AGENTS},
                               "nvidia_telemetry": False, "model": os.environ.get("DEMO_MODEL", ""),
                               "limit": int(os.environ.get("DEMO_CONTEXT_LIMIT", "250000")),
                               "metric": os.environ.get("DEMO_CONTEXT_METRIC", "active_context")})
        elif self.path == "/api/integrations":
            from memory import request
            statuses = {}
            for name, (base, path) in SERVICES.items():
                try:
                    request(base, path, timeout=2)
                    statuses[name] = "connected"
                except Exception:
                    statuses[name] = "unavailable"
            self.respond(200, statuses)
        elif self.path == "/api/runs":
            self.respond(200, sorted([json.loads(p.read_text()) for p in report_paths()],
                                     key=lambda r: r["started_ns"], reverse=True))
        elif self.path == "/api/kpis":
            self.respond(200, summarize([json.loads(p.read_text()) for p in report_paths()]))
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
            if not isinstance(request, dict) or set(request) - {"mode", "profile", "run_id", "task_id", "objective", "runtime"}:
                raise ValueError
            runtime = request.get("runtime", "flue-openshell")
            # Campaigns stay on tier 3; tier 1 has its own task contract.
            if (runtime not in AGENTS or request.get("mode") not in {"simulation", "live", "intervention", "benchmark"}
                    or (request["mode"] == "benchmark" and runtime != "flue-openshell")
                    or request.get("profile", "auto") not in {*PROFILES,"auto"}
                    or request.setdefault("task_id", next(iter(tasks(runtime)))) not in tasks(runtime)
                    or request.get("objective","balanced") not in {"balanced","cost","speed"}):
                raise ValueError
        except (ValueError, TypeError):
            self.respond(400, {"error": "invalid_request"})
            return
        if not ready(runtime, request["mode"]):
            self.respond(409, {"error": "live_not_configured"})
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
        if len(list(report_paths())) >= 100:
            self.respond(409, {"error": "demo_run_limit_100"})
            return
        if not LOCK.acquire(blocking=False):
            self.respond(409, {"error": "run_active"})
            return
        if request["mode"]=="benchmark":
            value={"id":uuid.uuid4().hex,"status":"running","started_ns":time.time_ns(),"run_ids":[],
                "planned":len(plan()),"budget_estimate_usd":"2.00","native_cost_estimate_usd":"0"}
            save_campaign(value);threading.Thread(target=campaign,args=(value,),daemon=True).start()
            self.respond(202,{"campaign_id":value["id"]});return
        try:
            run=new_run(request["mode"],request.get("profile","auto"),request["task_id"],request.get("objective","balanced"),runtime=runtime)
        except ValueError:
            LOCK.release();self.respond(409,{"error":"profile_requires_requalification"});return
        if run["metric"] not in {"active_context", "cumulative_input"} or not 1 <= run["limit"] <= 250000:
            LOCK.release()
            self.respond(409, {"error": "invalid_gate_configuration"})
            return
        save(run)
        threading.Thread(target=execute, args=(run,), daemon=True).start()
        self.respond(202, {"id": run["id"]})


# Host-native cockpit: loopback only; POST also checks Host/Origin against DNS rebinding.
ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("AEION_COCKPIT_PORT", "8088"))), Handler).serve_forever()
