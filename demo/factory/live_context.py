"""Live Context Provider via Hindsight Memory.

Retrieves historical failure evaluations, post-mortems, and reviewer feedback to inject
sanitized, bounded advisory guidance into agent prompts.
Maintains strict prompt-injection and secret scrubbing defenses.
Advisory only: never grants authority or overrides review gates or OPS permissions.
"""
import json
import re
import urllib.request

HINDSIGHT_URL = "http://127.0.0.1:8889"
MAX_ADVISORY_CHARS = 800

# Prompt injection patterns to detect and neutralize
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(an|a|in)\b", re.IGNORECASE),
    re.compile(r"switch\s+to\s+developer\s+mode", re.IGNORECASE),
    re.compile(r"new\s+system\s+instruction", re.IGNORECASE),
]

# Sensitive token / credential patterns to scrub
SECRET_PATTERNS = [
    re.compile(r"ghp_[a-zA-Z0-9]{36,40}"),
    re.compile(r"github_pat_[a-zA-Z0-9_]{40,100}"),
    re.compile(r"sk-[a-zA-Z0-9]{32,64}"),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
    re.compile(r"(password|secret|key)\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),
]


def sanitize_text(text):
    """Scrub prompt injection attempts, control characters, and secret credentials."""
    if not isinstance(text, str):
        return ""
    # Strip dangerous injection phrases
    for pattern in INJECTION_PATTERNS:
        text = pattern.sub("[REDACTED_INJECTION_ATTEMPT]", text)
    # Strip potential credentials or tokens
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED_CREDENTIAL]", text)
    # Remove control characters except newline and tab
    text = "".join(ch for ch in text if ch in "\n\t" or (len(ch.encode()) == 1 and ord(ch) >= 32))
    return text.strip()


def query_hindsight(bank="aeion-demo-real", query_str="failure postmortem repo-health architecture", budget="low", max_tokens=300):
    """Query Hindsight recall endpoint with fast, zero-event-loop HTTP client."""
    try:
        payload = {
            "query": query_str,
            "budget": budget,
            "max_tokens": max_tokens,
        }
        req = urllib.request.Request(
            f"{HINDSIGHT_URL}/v1/default/banks/{bank}/memories/recall",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return {"results": []}


def reflect_cognitive_synthesis(bank="aeion-demo-real", query_str=""):
    """Attempt cognitive synthesis via Hindsight reflect endpoint, failing closed on provider=none or error."""
    try:
        payload = {
            "query": query_str,
            "budget": "low",
        }
        req = urllib.request.Request(
            f"{HINDSIGHT_URL}/v1/default/banks/{bank}/reflect",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            text = data.get("text") or data.get("response") or ""
            return sanitize_text(text)
    except Exception:
        return ""


def query_hindsight_documents(bank="aeion-demo-real", tag="postmortem", limit=3):
    """Query Hindsight documents endpoint by tag."""
    req = urllib.request.Request(
        f"{HINDSIGHT_URL}/v1/default/banks/{bank}/documents?tag={tag}&limit={limit}",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=3) as resp:
        data = json.loads(resp.read().decode())
        items = data.get("items", [])
        docs = []
        for it in items:
            doc_id = it.get("id")
            if not doc_id:
                continue
            doc_req = urllib.request.Request(
                f"{HINDSIGHT_URL}/v1/default/banks/{bank}/documents/{doc_id}",
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(doc_req, timeout=3) as dresp:
                doc_data = json.loads(dresp.read().decode())
                if doc_data.get("original_text"):
                    docs.append(doc_data["original_text"])
        return docs


def get_live_context(feature_id=None, task_title="", write_scopes=None, bank="aeion-demo-real"):
    """Fetch relevant post-mortems and distill actionable historical hints for the builder prompt.
    
    Returns a formatted string or empty string on failure/no relevant memory.
    """
    try:
        # 1. Fetch relevant failure post-mortem documents
        docs = []
        try:
            reflection = reflect_cognitive_synthesis(bank=bank, query_str=f"Feature {feature_id or ''} failures architecture constraints")
            if reflection:
                docs.append(reflection)
        except Exception:
            pass
        try:
            docs.extend(query_hindsight_documents(bank=bank, tag="postmortem", limit=2))
        except Exception:
            pass
            
        if feature_id:
            try:
                docs.extend(query_hindsight_documents(bank=bank, tag=f"feature-{feature_id}", limit=1))
            except Exception:
                pass

        if not docs:
            # Fallback to recall endpoint
            try:
                recall = query_hindsight(bank=bank, query_str="failure postmortem repo-health comments", budget="low")
                docs.extend([r.get("text", "") for r in recall.get("results", [])])
            except Exception:
                pass
                
        if not docs:
            return ""
            
        hints = []
        seen = set()
        for raw in docs:
            clean = sanitize_text(raw)
            if not clean:
                continue
                
            # Extract high-value rules
            if "comment blocks" in clean.lower() or "20 lines" in clean.lower() or "repo-health" in clean.lower():
                rule = "Keep comment blocks under 20 lines in all source files (repo-health requirement)."
                if rule not in seen:
                    hints.append(rule)
                    seen.add(rule)
            if "docs-checked" in clean.lower() or "architecture refresh" in clean.lower():
                rule = "Ensure configuration changes are accompanied by architecture spec updates."
                if rule not in seen:
                    hints.append(rule)
                    seen.add(rule)
            if "databasefeaturefilter" in clean.lower():
                rule = "Feature 001: Keep DatabaseFeatureFilter clean and concise without verbose comments."
                if rule not in seen:
                    hints.append(rule)
                    seen.add(rule)
                    
        if not hints:
            return ""
            
        body = "\n".join(f"- {h}" for h in hints)
        advisory_block = (
            "\n\n--- BEGIN ADVISORY GUIDANCE (HISTORICAL POST-MORTEM DATA ONLY) ---\n"
            "Past builds on this repository noted the following rules:\n"
            f"{body}\n"
            "--- END ADVISORY GUIDANCE ---\n"
        )
        return advisory_block[:MAX_ADVISORY_CHARS]
    except Exception:
        # Strict fail-closed: return empty string on network or server error
        return ""
