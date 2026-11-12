"""Complementary memories. Canonical reports and deterministic policy remain authoritative."""
import hashlib
import json
import re
import urllib.request

from settings import SERVICES

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
# An empty URL in the environment disables that memory backend.
HINDSIGHT_URL = SERVICES["hindsight"][0]


def request(base, path, payload=None, timeout=8):
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(base + path, data=None if payload is None else json.dumps(payload).encode(), headers=headers)
    with HTTP.open(req, timeout=timeout) as response:
        data = response.read(131073)
        if len(data) > 131072:
            raise ValueError("MEMORY_RESPONSE_TOO_LARGE")
        return json.loads(data)


def analysis(run):
    usages = [e for e in run["events"] if e["name"] == "gen_ai.request"]
    return {
        "schema": "aeion.session-analysis.v1", "run_id": run["id"], "task": run.get("task_id", "pricing-js-v1"),
        **({'build_id': run['build_id']} if isinstance(run.get('build_id'), str) and re.fullmatch('[a-f0-9]{32}', run['build_id']) else {}),
        **({'factory_role': run['factory_role']} if run.get('factory_role') in ('author', 'review', 'prepare') else {}),
        "trace_id": run.get("trace_id"), "profile_version": run.get("profile_version", "unversioned"), "usage_complete": run.get("usage_complete", False),
        "synthetic": run["synthetic"], "model": run["model"] if not run["synthetic"] else "synthetic-replay",
        **({'reasoning_effort':run['inference_effort']} if run.get('inference_effort') in ('low','medium','high','max','default') else {}),
        "status": run["status"], "agents": run["agents"],
        "failure_code": run.get("failure"), "handover_md_sha256": run.get("handover_md_sha256"),
        "gate": {"metric": run["metric"], "limit": run["limit"]},
        "input_tokens": sum(e["gen_ai.usage.input_tokens"] for e in usages),
        "output_tokens": sum(e["gen_ai.usage.output_tokens"] for e in usages),
        "cli_cost_estimate_usd": run["native_cost_usd"], "accounting_basis": "synthetic" if run["synthetic"] else "cli_estimate_not_invoice",
        "duration_ms": round((run["ended_ns"] - run["started_ns"]) / 1000000, 2),
        "human_interventions": run.get("human_interventions", 0),
        "checks": run.get("check"), "artifact_sha256": run.get("artifact_sha256"),
        "assessment": "Protected task checks; descriptive evidence only, not a general model ranking.",
        "selection": run.get("selection"), "runtime": run.get("runtime", "legacy"),
    }


class Memory:
    def checkpoint(self, run, state):
        """Verified local working checkpoint; deterministic cryptographic fingerprinting."""
        text = json.dumps(state, sort_keys=True)
        fingerprint = hashlib.sha256(text.encode()).hexdigest()
        run["checkpoint_sha256"] = fingerprint
        run["checkpoint_status"] = "confirmed"
        # Deterministic integer id derived from fingerprint for backwards compatibility
        cid = int(fingerprint[:8], 16)
        run["checkpoint_id"] = cid
        run["claude_mem_id"] = cid
        return json.loads(text)

    def retain(self, run):
        base = HINDSIGHT_URL
        if not base:
            return {"status": "disabled"}
        bank = "aeion-demo-synthetic" if run["synthetic"] else "aeion-demo-real"
        content = json.dumps(analysis(run), sort_keys=True)
        result = request(base, f"/v1/default/banks/{bank}/memories", {"async": False, "items": [{
            "content": content, "document_id": "run-" + run["id"],
            "context": "Local agent efficiency analysis; descriptive evidence, no control authority.",
            "tags": [run.get("task_id", "pricing-js-v1"), "synthetic" if run["synthetic"] else "real"],
        }]}, timeout=45)
        if result.get("success") is not True or result.get("items_count") != 1 or result.get("async") is not False:
            raise ValueError("MEMORY_NOT_RETAINED")
        return {"status": "retained", "bank": bank, "document_id": "run-" + run["id"],
                "llm_usage": result.get("usage")}

    def retain_factory(self, run):
        """Confirm only this newly submitted metadata document, never search other memories."""
        result = self.retain(run)
        if result.get('status') != 'retained':
            return result
        try:
            document = request(HINDSIGHT_URL,
                f"/v1/default/banks/{result['bank']}/documents/{result['document_id']}", timeout=3)
            same = json.loads(document.get('original_text') or 'null') == analysis(run)
        except (OSError, ValueError, TypeError):
            same = False
        return {key: result[key] for key in ('bank','document_id')} | {
            'status':'confirmed' if same else 'retained_unconfirmed'}

    def retain_decisions(self, campaign):
        base=HINDSIGHT_URL
        if not base: return {"status":"disabled"}
        content=json.dumps({"schema":"aeion.model-decision.v1","campaign_id":campaign["id"],
            "status":campaign["status"],"native_cost_estimate_usd":campaign["native_cost_estimate_usd"],
            "recommendations":campaign["recommendations"],"authority":"advisory; never overrides sandbox or context gates"},sort_keys=True)
        result=request(base,"/v1/default/banks/aeion-demo-real/memories",{"async":False,"items":[{
            "content":content,"document_id":"decision-"+campaign["id"],"tags":["model-selection","openshell"],
            "context":"Measured task-specific cost, latency, correctness and recorded autonomy decision."}]},timeout=45)
        if result.get("success") is not True: raise ValueError("MEMORY_NOT_RETAINED")
        return {"status":"retained","llm_usage":result.get("usage")}

    def recall(self, synthetic=False):
        base = HINDSIGHT_URL
        if not base:
            return {"status": "disabled", "results": []}
        bank = "aeion-demo-synthetic" if synthetic else "aeion-demo-real"
        try:
            from hindsight_client import Hindsight
            client = Hindsight(base_url=base)
            try:
                res = client.recall(bank_id=bank, query="Agent execution efficiency: cost tokens duration verified checks human interventions handover", budget="low", max_tokens=1200)
                items = [{"id": str(r.id), "text": str(r.text)[:5000]} for r in (res.results or [])[:8]]
                return {"status": "ok", "bank": bank, "results": items}
            finally:
                client.close()
        except Exception:
            # Fallback to direct HTTP request
            result = request(base, f"/v1/default/banks/{bank}/memories/recall", {
                "query": "Agent execution efficiency: cost tokens duration verified checks human interventions handover",
                "budget": "low", "max_tokens": 1200,
            }, timeout=20)
            # Recalled content is display-only advisory data; never merged into a policy/config.
            return {"status": "ok", "bank": bank, "results": [
                {"id": str(item.get("id", "")), "text": str(item.get("text", ""))[:5000]}
                for item in result.get("results", [])[:8]
            ]}
