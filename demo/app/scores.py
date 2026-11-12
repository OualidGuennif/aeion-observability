"""Publish deterministic fixture outcomes and multi-dimensional factory metrics as native Langfuse scores."""
import base64
import json
import os
import urllib.request
import uuid

from settings import LANGFUSE_URL


def get_langfuse_client():
    """Attempt to initialize the official Langfuse Python client."""
    auth = os.environ.get("LANGFUSE_AUTH")
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    if not public_key and auth:
        try:
            decoded = base64.b64decode(auth).decode()
            if ":" in decoded:
                public_key, secret_key = decoded.split(":", 1)
        except Exception:
            pass
    if public_key and secret_key:
        try:
            from langfuse import Langfuse
            return Langfuse(public_key=public_key, secret_key=secret_key, host=LANGFUSE_URL)
        except Exception:
            return None
    return None


def publish(run):
    """Publish baseline boolean scores for demo and synthetic test runs."""
    auth = os.environ.get("LANGFUSE_AUTH")
    if not auth:
        return {"status": "disabled"}
    correct = run["status"] == "passed"
    values = {"demo_verified_checks": correct,
              "demo_autonomous_success": correct and run.get("human_interventions", 0) == 0}
    ids = []
    client = get_langfuse_client()
    for name, value in values.items():
        # Langfuse preserves the initial score environment on ID upsert.
        score_id = uuid.uuid5(uuid.NAMESPACE_URL, "aeion-demo/default/" + run["id"] + "/" + name).hex
        if client:
            try:
                client.create_score(
                    name=name,
                    value=float(value),
                    trace_id=run["trace_id"],
                    score_id=score_id,
                    data_type="BOOLEAN",
                    environment="default",
                    comment="Protected synthetic-task checks; descriptive pilot evidence only.",
                    metadata={"run_id": run["id"], "synthetic": run["synthetic"], "task": run.get("task_id", "pricing-js-v1")},
                )
                ids.append(score_id)
                continue
            except Exception:
                pass
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
    if client:
        try:
            client.flush()
        except Exception:
            pass
    return {"status": "accepted", "ids": ids}


def compute_factory_scores(run):
    """Compute multi-dimensional evaluation scores for an Æion Factory build."""
    scores = {}
    
    # 1. Acceptance check outcome
    check = run.get("check") or {}
    check_status = check.get("status") if isinstance(check, dict) else run.get("status")
    scores["factory.check.acceptance"] = {
        "value": 1.0 if check_status == "passed" else 0.0,
        "data_type": "BOOLEAN",
        "comment": "Protected independent acceptance checks verdict",
    }
    
    # 2. Review circuit consensus
    circuit = run.get("circuit") or {}
    circuit_status = circuit.get("status")
    votes = circuit.get("votes") or []
    if circuit_status == "approved":
        consensus = 1.0
    elif any(v.get("verdict") == "approve" for v in votes):
        consensus = 0.5
    else:
        consensus = 0.0
    scores["factory.review.consensus"] = {
        "value": consensus,
        "data_type": "NUMERIC",
        "comment": "Two-vote independent review circuit consensus (1.0 approve, 0.5 split, 0.0 reject)",
    }
    
    # 3. Budget efficiency: headroom remaining relative to reservation
    usage = run.get("usage") or {}
    cost_str = usage.get("cost_usd") or run.get("native_cost_usd") or "0"
    limit_str = run.get("cost_reservation_usd") or "50.0"
    try:
        cost = float(cost_str)
        limit = float(limit_str)
        efficiency = round(max(0.0, min(1.0, 1.0 - (cost / limit))), 4) if limit > 0 else 0.0
    except (ValueError, TypeError, ZeroDivisionError):
        efficiency = 0.0
    scores["factory.budget.efficiency"] = {
        "value": efficiency,
        "data_type": "NUMERIC",
        "comment": "Normalized spend headroom vs reservation",
    }
    
    # 4. Cache hit ratio
    input_tokens = float(usage.get("input_tokens") or 0)
    cached_tokens = float(usage.get("cached_tokens") or 0)
    cache_ratio = round(cached_tokens / input_tokens, 4) if input_tokens > 0 else 0.0
    scores["factory.cache.hit_ratio"] = {
        "value": cache_ratio,
        "data_type": "NUMERIC",
        "comment": "Prompt token caching efficiency ratio",
    }
    
    return scores


def publish_factory_scores(run):
    """Publish comprehensive multi-dimensional scores for a Factory build."""
    auth = os.environ.get("LANGFUSE_AUTH")
    if not auth:
        return {"status": "disabled", "ids": []}
    scores_dict = compute_factory_scores(run)
    trace_id = run.get("trace_id")
    build_id = run.get("build_id") or run.get("id")
    if not trace_id or not build_id:
        return {"status": "missing_trace_or_id", "ids": []}
    client = get_langfuse_client()
    ids = []
    for name, s in scores_dict.items():
        score_id = uuid.uuid5(uuid.NAMESPACE_URL, f"aeion-factory/default/{build_id}/{name}").hex
        if client:
            try:
                client.create_score(
                    name=name,
                    value=s["value"],
                    trace_id=trace_id,
                    score_id=score_id,
                    data_type=s["data_type"],
                    environment="default",
                    comment=s["comment"],
                    metadata={"build_id": build_id, "feature_id": run.get("feature_id")},
                )
                ids.append(score_id)
                continue
            except Exception:
                pass
        payload = {
            "id": score_id, "traceId": trace_id, "name": name, "value": s["value"],
            "dataType": s["data_type"], "environment": "default", "comment": s["comment"],
            "metadata": {"build_id": build_id, "feature_id": run.get("feature_id")}
        }
        try:
            req = urllib.request.Request(LANGFUSE_URL + "/api/public/scores", data=json.dumps(payload).encode(),
                                         headers={"Authorization": "Basic " + auth, "Content-Type": "application/json"})
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(req, timeout=5) as resp:
                res = json.loads(resp.read(4096))
                if res.get("id") == score_id:
                    ids.append(score_id)
        except Exception:
            pass
    if client:
        try:
            client.flush()
        except Exception:
            pass
    return {"status": "accepted", "ids": ids}
