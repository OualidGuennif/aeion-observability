"""Read real Langfuse v4 observations and Hindsight recall; never print credentials/content."""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request
from app.memory import analysis


def get(url, auth=None):
    headers = {"Authorization": "Basic " + auth} if auth else {}
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    values = dict(line.split("=", 1) for line in (Path(__file__).parent / ".local/stack.env").read_text().splitlines() if "=" in line)
    runs = get("http://127.0.0.1:8088/api/runs")
    eligible = [r for r in runs if r["id"] == args.run_id] if args.run_id else [r for r in runs if r["synthetic"] == args.synthetic and r["status"] == "passed"]
    if not eligible:
        raise SystemExit("No matching completed successful run")
    run = eligible[0]
    query = urllib.parse.urlencode({"traceId": run["trace_id"], "fields": "basic,usage,model,io,metadata", "limit": 1000})
    data = get("http://127.0.0.1:3300/api/public/v2/observations?" + query, values["LANGFUSE_AUTH"])["data"]
    names = {r.get("name") for r in data}
    required = {"demo.task"} | {e["name"] for e in run["events"] if e["name"] in {
        "gen_ai.request", "artifact.checked", "app.verified", "memory.checkpoint", "task.failed"}}
    if not required <= names:
        raise SystemExit("Langfuse ingestion incomplete: missing " + ", ".join(sorted(required - names)))
    if any(row.get("input") not in (None, "") or row.get("output") not in (None, "") for row in data):
        raise SystemExit("Unexpected content field in Langfuse")
    deno_join = any(row.get("metadata", {}).get("resourceAttributes.service.name") == "aeion-deno-playground" for row in data)
    if "app.verified" in required and not deno_join:
        raise SystemExit("Deno application span did not join the task trace")
    generations = [r for r in data if r.get("name") == "gen_ai.request"]
    native = [e for e in run["events"] if e["name"] == "gen_ai.request"]
    if len(generations) != len(native) or any(r.get("type") != "GENERATION" for r in generations):
        raise SystemExit("Langfuse generation coverage mismatch")
    if not run["synthetic"] and any("aeion.cost.estimated_usd" in e for e in native):
        if any(r.get("totalCost") is None for r in generations):
            raise SystemExit("Native cost mapping missing in Langfuse")
        if abs(sum(Decimal(str(r["totalCost"])) for r in generations) - Decimal(run["native_cost_usd"])) > Decimal("0.000000001"):
            raise SystemExit("Cost estimate mapping mismatch")
    recall = get("http://127.0.0.1:8088/api/memory" + ("?synthetic=true" if run["synthetic"] else ""))
    if recall.get("status") != "ok" or not recall.get("results"):
        raise SystemExit("Hindsight recall has no evidence")
    if ("memory.checkpoint" in required and not run.get("claude_mem_id")) or run.get("memory", {}).get("status") != "retained":
        raise SystemExit("Memory persistence not acknowledged")
    bank = "aeion-demo-synthetic" if run["synthetic"] else "aeion-demo-real"
    document = get("http://127.0.0.1:8889/v1/default/banks/" + bank + "/documents/run-" + run["id"])
    if json.loads(document.get("original_text", "null")) != analysis(run) or document.get("memory_unit_count", 0) < 1:
        raise SystemExit("Hindsight document differs from the canonical analysis")
    score_ids = run.get("langfuse_scores", {}).get("ids", [])
    if len(score_ids) != 2:
        raise SystemExit("Langfuse scores not acknowledged")
    score_query = urllib.parse.urlencode({"id": ",".join(score_ids), "fields": "subject", "limit": 10})
    scores = get("http://127.0.0.1:3300/api/public/v3/scores?" + score_query, values["LANGFUSE_AUTH"])["data"]
    expected = {"demo_verified_checks": run["status"] == "passed",
                "demo_autonomous_success": run["status"] == "passed" and run.get("human_interventions", 0) == 0}
    if (len(scores) != 2 or {row["id"] for row in scores} != set(score_ids)
            or any(row.get("dataType") != "BOOLEAN" or row.get("value") is not expected.get(row.get("name"))
                   or row.get("environment") != "default" or row.get("subject", {}).get("id") != run["trace_id"] for row in scores)):
        raise SystemExit("Langfuse score values differ from the canonical outcome")
    result = {"run_id": run["id"], "trace_id": run["trace_id"], "observations": len(data),
              "generations": len(generations), "content_fields_empty": True,
              "claude_mem_checkpoint": run.get("claude_mem_id"), "hindsight_recall_results": len(recall["results"]),
              "native_cost_estimate_usd": run["native_cost_usd"], "scores": "read_back_matching",
              "deno_trace_join": deno_join, "hindsight_document": "read_back_matching"}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
