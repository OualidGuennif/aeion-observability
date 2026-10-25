"""Credential-owning local inference boundary. The agent never receives the Go key."""
import hmac
import json
import secrets
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from token_budget import TokenBudget, admit, PROVIDER_RESERVE
from json_input import loads


class ContextRelay:
    def __init__(self, model, api_key, limit, checkpoint, event, *, upstream=None, counter=None):
        self.model = model.split("/", 1)[1]
        self.key, self.limit, self.checkpoint, self.event = api_key, limit, checkpoint, event
        self.counter = counter or TokenBudget(self.model)
        self.upstream = upstream or "https://opencode.ai/inference/go/openai/v1/chat/completions"
        self.token = secrets.token_urlsafe(32)
        self.closed = False
        self.active = threading.Lock()
        self.responses = []
        self.last_count = None
        self.forwarded_count = 0
        self.last_error_code = None
        relay = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def deny(self, status, code):
                data = json.dumps({"error": {"message": code, "code": code}}).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_POST(self):
                authorization = self.headers.get("Authorization", "")
                if relay.closed or not hmac.compare_digest(authorization, "Bearer " + relay.token):
                    return self.deny(403, "GATE_CLOSED")
                if self.path != "/v1/chat/completions" or not relay.active.acquire(blocking=False):
                    return self.deny(409, "GATE_CLOSED")
                try:
                    if relay.closed:
                        return self.deny(403, "GATE_CLOSED")
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 2000000:
                        raise ValueError("CONTEXT_UNKNOWN")
                    body = self.rfile.read(length)
                    payload = loads(body)
                    if payload.get("model") != relay.model or payload.get("stream") is not True:
                        raise ValueError("CONTEXT_UNKNOWN")
                    if payload.get("n", 1) != 1 or any(k in payload for k in ("previous_response_id", "conversation", "session_id")):
                        raise ValueError("CONTEXT_UNKNOWN")
                    maximum = payload.get("max_tokens", payload.get("max_completion_tokens"))
                    for key in ("max_tokens", "max_completion_tokens"):
                        if key in payload and (type(payload[key]) is not int or not 1 <= payload[key] <= 4096):
                            raise ValueError("CONTEXT_UNKNOWN")
                    counted = relay.counter.count(payload)
                    relay.last_count = counted
                    relay.event("context.preflight", **{"aeion.context.counted": counted,
                                                       "aeion.context.hard_limit": 300000,
                                                       "aeion.context.reserve": PROVIDER_RESERVE,
                                                       "aeion.context.max_output": maximum,
                                                       "aeion.context.tokenizer_revision": getattr(relay.counter, "revision", "fixture")})
                    if relay.forwarded_count >= 12:
                        relay.closed = True
                        relay.last_error_code = "STEP_LIMIT"
                        relay.event("context.refused", **{"aeion.failure.code": "STEP_LIMIT"})
                        return self.deny(409, "STEP_LIMIT")
                    if not admit(counted, maximum) or counted >= min(relay.limit, 250000):
                        relay.closed = True
                        relay.checkpoint(counted, True)
                        return self.deny(409, "AEION_HANDOVER")
                    if counted >= max(1, relay.limit - 20000):
                        relay.checkpoint(counted, False)
                    headers = {name: value for name, value in self.headers.items()
                               if name.lower() == "user-agent" or name.lower().startswith("x-opencode-")}
                    request = urllib.request.Request(relay.upstream, data=body, headers={**headers,
                        "Authorization": "Bearer " + relay.key, "Content-Type": "application/json",
                        "Accept-Encoding": "identity",
                    })
                    # No retries, redirects, environment proxy or raw request/response logging.
                    class NoRedirect(urllib.request.HTTPRedirectHandler):
                        def redirect_request(self, *_args, **_kwargs):
                            return None
                    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
                    relay.forwarded_count += 1
                    with opener.open(request, timeout=45) as response:
                        relay.responses.append(response)
                        self.send_response(response.status)
                        self.send_header("Content-Type", "text/event-stream")
                        self.send_header("Connection", "close")
                        self.end_headers()
                        self.close_connection = True
                        while not relay.closed:
                            block = response.read1(65536)
                            if not block:
                                break
                            self.wfile.write(block)
                            self.wfile.flush()
                        relay.responses.remove(response)
                except urllib.error.HTTPError as error:
                    relay.closed = True
                    relay.event("provider.rejected", **{"aeion.http.status": error.code})
                    # Classify only fixed operational errors; never copy a provider body into logs.
                    detail = error.read(4096).decode("utf-8", errors="replace").lower()
                    code = "GO_REGION_REQUIRED" if "global" in detail and "region" in detail else "PROVIDER_REJECTED"
                    if "opencode" in detail and ("client" in detail or "within" in detail):
                        code = "CLI_CLIENT_REQUIRED"
                    if "subscription" in detail:
                        code = "GO_SUBSCRIPTION_REQUIRED"
                    if "disabled" in detail:
                        code = "MODEL_DISABLED"
                    if error.code == 402:
                        code = "INSUFFICIENT_FUNDS"
                    relay.last_error_code = code
                    relay.event("provider.reason", **{"aeion.failure.code": code})
                    self.deny(error.code, code)
                except (ValueError, TypeError, KeyError):
                    relay.closed = True
                    relay.event("context.refused", **{"aeion.failure.code": "CONTEXT_UNKNOWN"})
                    self.deny(409, "CONTEXT_UNKNOWN")
                except (OSError, TimeoutError):
                    relay.closed = True
                    relay.event("provider.failed", **{"aeion.failure.code": "TRANSPORT_ERROR"})
                except Exception:
                    relay.closed = True
                    relay.event("context.refused", **{"aeion.failure.code": "CONTEXT_UNKNOWN"})
                    self.deny(409, "CONTEXT_UNKNOWN")
                finally:
                    relay.active.release()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()

    def close(self):
        self.closed = True
        for response in self.responses[:]:
            response.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
