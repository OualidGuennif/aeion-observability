"""Complementary memories. Canonical reports and deterministic policy remain authoritative."""
import hashlib
import json
import os
import urllib.request

HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request(base, path, payload=None, timeout=8):
    headers = {"Content-Type": "application/json"}
    # claude-mem's local worker trusts an explicitly local Host; no admin routes are used.
    if base == os.environ.get("CLAUDE_MEM_URL"):
        headers["Host"] = "localhost:37777"
    req = urllib.request.Request(base + path, data=None if payload is None else json.dumps(payload).encode(), headers=headers)
    with HTTP.open(req, timeout=timeout) as response:
        data = response.read(131073)
        if len(data) > 131072:
            raise ValueError("MEMORY_RESPONSE_TOO_LARGE")
        return json.loads(data)


def analysis(run):
    usages = [e for e in run["events"] if e["name"] == "gen_ai.request"]
    return {
        "schema": "aeion.session-analysis.v1", "run_id": run["id"], "task": "pricing-js-v1",
        "trace_id": run.get("trace_id"), "profile_version": run.get("profile_version", "unversioned"), "usage_complete": run.get("usage_complete", False),
        "synthetic": run["synthetic"], "model": run["model"] if not run["synthetic"] else "synthetic-replay",
        "status": run["status"], "agents": run["agents"],
        "failure_code": run.get("failure"), "handover_md_sha256": run.get("handover_md_sha256"),
        "gate": {"metric": run["metric"], "limit": run["limit"]},
        "input_tokens": sum(e["gen_ai.usage.input_tokens"] for e in usages),
        "output_tokens": sum(e["gen_ai.usage.output_tokens"] for e in usages),
        "cli_cost_estimate_usd": run["native_cost_usd"], "accounting_basis": "synthetic" if run["synthetic"] else "cli_estimate_not_invoice",
        "duration_ms": round((run["ended_ns"] - run["started_ns"]) / 1000000, 2),
        "human_interventions": run.get("human_interventions", 0),
        "checks": run.get("check"), "artifact_sha256": run.get("artifact_sha256"),
        "assessment": "Verified synthetic task only; insufficient evidence for a general model ranking.",
    }


class Memory:
    def checkpoint(self, run, state):
        base = os.environ.get("CLAUDE_MEM_URL")
        if not base:
            return state
        text = json.dumps(state, sort_keys=True)
        result = request(base, "/api/memory/save", {
            "text": text, "title": "AEion handover checkpoint", "project": "aeion-working-" + run["id"],
            "metadata": {"sourceFingerprint": hashlib.sha256(text.encode()).hexdigest(), "platformSource": "opencode"},
        }, timeout=3)
        if result.get("success") is not True or type(result.get("id")) is not int:
            raise ValueError("CHECKPOINT_NOT_SAVED")
        stored = request(base, "/api/observation/" + str(result["id"]), timeout=3)
        if json.loads(stored["narrative"]) != state:
            raise ValueError("CHECKPOINT_MISMATCH")
        run["claude_mem_id"] = result["id"]
        return json.loads(stored["narrative"])

    def retain(self, run):
        base = os.environ.get("HINDSIGHT_URL")
        if not base:
            return {"status": "disabled"}
        bank = "aeion-demo-synthetic" if run["synthetic"] else "aeion-demo-real"
        content = json.dumps(analysis(run), sort_keys=True)
        result = request(base, f"/v1/default/banks/{bank}/memories", {"async": False, "items": [{
            "content": content, "document_id": "run-" + run["id"],
            "context": "Local agent efficiency analysis; descriptive evidence, no control authority.",
            "tags": ["pricing-js-v1", "synthetic" if run["synthetic"] else "real"],
        }]}, timeout=45)
        if result.get("success") is not True or result.get("items_count") != 1 or result.get("async") is not False:
            raise ValueError("MEMORY_NOT_RETAINED")
        return {"status": "retained", "bank": bank, "document_id": "run-" + run["id"],
                "llm_usage": result.get("usage")}

    def recall(self, synthetic=False):
        base = os.environ.get("HINDSIGHT_URL")
        if not base:
            return {"status": "disabled", "results": []}
        bank = "aeion-demo-synthetic" if synthetic else "aeion-demo-real"
        result = request(base, f"/v1/default/banks/{bank}/memories/recall", {
            "query": "Agent execution efficiency: cost tokens duration verified checks human interventions handover",
            "budget": "low", "max_tokens": 1200,
        }, timeout=20)
        # Recalled content is display-only advisory data; never merged into a policy/config.
        return {"status": "ok", "bank": bank, "results": [
            {"id": str(item.get("id", "")), "text": str(item.get("text", ""))[:5000]}
            for item in result.get("results", [])[:8]
        ]}
