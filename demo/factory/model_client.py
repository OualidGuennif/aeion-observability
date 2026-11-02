"""Real model calls through one bounded interface.

The wire identifier comes from the shared model catalog, never from the display name. The
client is transport-injectable so the circuit can be tested without a network, and an
unconfigured endpoint means "no call": callers hold rather than invent a vote. Usage is
returned with the answer; a cost is trusted only when the provider reports one.
"""
import json
import os
import secrets
import ssl
import urllib.error
import urllib.request
from pathlib import Path

from .models import wire_id

DEFAULT_ENDPOINT = "https://opencode.ai/inference/go/openai/v1/chat/completions"
MAX_OUTPUT_TOKENS = 120
TIMEOUT_SECONDS = 60
ENVIRONMENT_KEYS = ("OPENCODE_API_KEY", "AEION_REVIEW_ENDPOINT")


class ModelClientError(ValueError):
    """A reviewer call that cannot be trusted."""


def tls_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, OSError):
        return ssl.create_default_context()


def _endpoint():
    return os.environ.get("AEION_REVIEW_ENDPOINT", DEFAULT_ENDPOINT)


def available():
    load_environment()
    return bool(os.environ.get("OPENCODE_API_KEY"))


def load_environment(paths=None):
    """Load only the provider keys from the project's existing dotenv files.

    Values are never logged or returned. An already-exported variable wins, so an operator
    can override a stored file without editing it. Returns the names that were loaded.
    """
    root = Path(__file__).resolve().parents[2]
    candidates = paths or [root / "demo/.local/stack.env", root / "demo/.env", root / ".env"]
    loaded = []
    for path in candidates:
        try:
            lines = Path(path).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().removeprefix("export ").strip()
            if key not in ENVIRONMENT_KEYS or key in os.environ:
                continue
            value = value.strip().strip('"').strip("'")
            if value:
                os.environ[key] = value
                loaded.append(key)
    return loaded


def _urllib_transport(url, payload, headers, timeout=TIMEOUT_SECONDS):
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    for key, value in headers.items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=tls_context()) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read(2048).decode("utf-8", "replace")[:200]}


def _parse(text):
    """Accept a bare JSON object, or one fenced block around it."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("```")[1] if "```" in text[3:] else text.strip("`")
        text = text.removeprefix("json").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ModelClientError("no_json_answer")
    try:
        answer = json.loads(text[start:end + 1])
    except ValueError as exc:
        raise ModelClientError("unreadable_json_answer") from exc
    if not isinstance(answer, dict):
        raise ModelClientError("answer_not_object")
    return answer


def complete_with_usage(model, prompt, transport=None, max_tokens=MAX_OUTPUT_TOKENS, session=None):
    """Ask one model once; return its answer, canonical wire id and reported usage."""
    load_environment()
    token = os.environ.get("OPENCODE_API_KEY")
    if not token:
        raise ModelClientError("review_endpoint_unconfigured")
    wire = wire_id(model)
    agent_session = session or secrets.token_hex(16)
    payload = {
        "model": wire,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json",
               "Accept": "application/json", "User-Agent": "aeion-factory/1.0",
               "x-opencode-session": agent_session}
    transport = transport or _urllib_transport
    status, body = transport(_endpoint(), payload, headers)
    if status != 200 or not isinstance(body, dict):
        raise ModelClientError(f"review_call_failed:{status}")
    try:
        text = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelClientError("review_answer_shape") from exc
    reported = body.get("usage") if isinstance(body.get("usage"), dict) else {}
    input_tokens = reported.get("prompt_tokens", reported.get("input_tokens"))
    output_tokens = reported.get("completion_tokens", reported.get("output_tokens"))
    raw_cost = reported.get("cost", reported.get("cost_usd"))
    cost = None
    if isinstance(raw_cost, (int, float)) and not isinstance(raw_cost, bool) and raw_cost >= 0:
        cost = raw_cost
    return {
        "answer": _parse(text),
        "wire_model": wire,
        "session": agent_session,
        "usage": {
            "input_tokens": input_tokens if isinstance(input_tokens, int) else None,
            "output_tokens": output_tokens if isinstance(output_tokens, int) else None,
            "cost_usd": cost,
            "complete": cost is not None,
            "basis": "provider_usage" if cost is not None else "provider_cost_unreported",
        },
    }


def complete(model, prompt, transport=None):
    """Compatibility wrapper: one vote, no usage surface."""
    return complete_with_usage(model, prompt, transport=transport)["answer"]


def open_code_complete(model, prompt):
    return complete(model, prompt)
