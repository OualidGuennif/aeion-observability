"""Publish deterministic fixture outcomes as native Langfuse boolean scores."""
import json
import os
import urllib.request
import uuid

from settings import LANGFUSE_URL


def publish(run):
    auth = os.environ.get("LANGFUSE_AUTH")
    if not auth:
        return {"status": "disabled"}
    correct = run["status"] == "passed"
    values = {"demo_verified_checks": correct,
              "demo_autonomous_success": correct and run.get("human_interventions", 0) == 0}
    ids = []
    for name, value in values.items():
        # Langfuse preserves the initial score environment on ID upsert.
        score_id = uuid.uuid5(uuid.NAMESPACE_URL, "aeion-demo/default/" + run["id"] + "/" + name).hex
        payload = {"id": score_id, "traceId": run["trace_id"], "name": name, "value": int(value),
                   "dataType": "BOOLEAN", "environment": "default",
                   "comment": "Protected synthetic-task checks; descriptive pilot evidence only.",
                   "metadata": {"run_id": run["id"], "synthetic": run["synthetic"], "task": run.get("task_id", "pricing-js-v1")}}
        request = urllib.request.Request(LANGFUSE_URL + "/api/public/scores", data=json.dumps(payload).encode(),
                                         headers={"Authorization": "Basic " + auth, "Content-Type": "application/json"})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=5) as response:
            result = json.loads(response.read(4096))
        if result.get("id") != score_id:
            raise ValueError("SCORE_NOT_ACKNOWLEDGED")
        ids.append(score_id)
    return {"status": "accepted", "ids": ids}
