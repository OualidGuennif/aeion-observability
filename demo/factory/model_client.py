"""Real model calls for the review circuit, behind one bounded interface.

Each voter is one chat completion with a short prompt and a JSON answer. The client is
transport-injectable so the circuit can be tested without a network, and unconfigured means
"no call": the circuit then holds for a human instead of inventing a vote.
"""
import json
import os
import ssl
import urllib.error
import urllib.request

DEFAULT_ENDPOINT = "https://opencode.ai/inference/go/openai/v1/chat/completions"
MAX_OUTPUT_TOKENS = 120
TIMEOUT_SECONDS = 60


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
    return bool(os.environ.get("OPENCODE_API_KEY"))


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


def complete(model, prompt, transport=None):
    """Ask one model for one review vote; raises rather than guessing."""
    token = os.environ.get("OPENCODE_API_KEY")
    if not token:
        raise ModelClientError("review_endpoint_unconfigured")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0,
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json",
               "Accept": "application/json"}
    transport = transport or _urllib_transport
    status, body = transport(_endpoint(), payload, headers)
    if status != 200 or not isinstance(body, dict):
        raise ModelClientError(f"review_call_failed:{status}")
    try:
        text = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelClientError("review_answer_shape") from exc
    return _parse(text)


def open_code_complete(model, prompt):
    return complete(model, prompt)
