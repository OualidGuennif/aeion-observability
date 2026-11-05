"""Credential-owning local inference boundary. The agent never receives the Go key."""
import hashlib
import hmac
import json
import secrets
import ssl
import threading
from decimal import Decimal
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from token_budget import TokenBudget, admit, PROVIDER_RESERVE
from provider_usage import ReportedUsage


def _tls_context():
    # This interpreter ships no OS trust store; prefer certifi when it is installed.
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, OSError):
        return ssl.create_default_context()
from json_input import loads

# Longest silence tolerated on the upstream socket (connect or between bytes). A reasoning model
# can think for minutes over a large review packet before its first byte; role deadlines still
# bound the whole session. Measured: a 45s bound cut a DeepSeek review at 45.4s with zero tokens.
UPSTREAM_IDLE_SECONDS = 300

# A provider that answers "busy" (rate limit, overload, gateway error) has refused the request
# before producing any token, so the same request may be sent again a bounded number of times.
# Measured 2026-11-05: one DeepSeek review vote failed on a provider HTTP error with zero tokens
# and held a build whose gate had passed. Any other status, a timeout or a transport error is
# not retried: those may have consumed provider work or point at a lasting cause.
RETRYABLE_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504, 529})
PROVIDER_RETRY_DELAYS = (5, 20)
RETRY_AFTER_CEILING_SECONDS = 30


def retry_delay(error, fallback):
    """Seconds before the next attempt: an integer Retry-After within the ceiling, else fallback."""
    raw = str((error.headers.get('Retry-After') if error.headers is not None else None) or '').strip()
    if raw.isascii() and raw.isdigit() and len(raw) <= 4:
        return min(int(raw), RETRY_AFTER_CEILING_SECONDS)
    return fallback


class ContextRelay:
    def __init__(self, model, api_key, limit, checkpoint, event, *, upstream=None, counter=None, bind=None, admission=None,
                 api='openai-completions', prices=None, cost_limit=None, required_effort=None,max_output_tokens=4096,
                 required_reasoning_effort=None, max_requests=12):
        if type(max_requests) is not int or not 1<=max_requests<=200:
            raise ValueError('STEP_LIMIT_INVALID')
        self.max_requests=max_requests
        if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 65536:
            raise ValueError('OUTPUT_LIMIT_INVALID')
        self.max_output_tokens=max_output_tokens
        if required_reasoning_effort not in (None,'low','high','max'):
            raise ValueError('REASONING_EFFORT_INVALID')
        self.required_reasoning_effort=required_reasoning_effort
        self.model = model.split("/", 1)[1]
        self.key, self.limit, self.checkpoint, self.event = api_key, limit, checkpoint, event
        self.counter = counter or TokenBudget(self.model)
        self.context_basis = getattr(self.counter, 'context_basis', 'local_tokenizer')
        if api not in ('openai-completions', 'anthropic-messages'):
            raise ValueError('PROTOCOL_UNKNOWN')
        self.api = api
        self.route = '/v1/messages' if api == 'anthropic-messages' else '/v1/chat/completions'
        self.upstream = upstream or ('https://opencode.ai/inference/go/anthropic/v1/messages'
            if api == 'anthropic-messages' else 'https://opencode.ai/inference/go/openai/v1/chat/completions')
        self.prices, self.cost_limit = prices, None if cost_limit is None else Decimal(str(cost_limit))
        self.required_effort = required_effort
        self.projected_cost = Decimal('0')
        self.reported_usage = []
        self.accounting_complete = True
        self.token = secrets.token_urlsafe(32)
        self.closed = False
        self.active = threading.Lock()
        self.dispatch_lock = threading.Lock()
        self.responses = []
        self.last_count = None
        self.forwarded_count = 0
        self.forwarded_counts = []
        self.last_error_code = None
        # The last provider HTTP status that refused a request, kept as local metadata so a
        # failed vote says why without opening the trace backend; retries are counted too.
        self.last_http_status = None
        self.provider_retries = 0
        self.stopping = threading.Event()
        # Harnesses sometimes submit the same turn twice — once as a prompt and once as a
        # JSON payload. An identical body with no new conversation state is a duplicate and
        # would be paid twice, so it is refused instead of forwarded.
        self.last_body_sha256 = None
        # Called before every forward; returns a stop code once the supervisor has accounted
        # the previous response and found the budget or native context gate reached.
        self.admission = admission
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
                api_key = self.headers.get('x-api-key', '')
                authenticated = hmac.compare_digest(authorization, "Bearer " + relay.token) or hmac.compare_digest(api_key, relay.token)
                if relay.closed or not authenticated:
                    return self.deny(403, "GATE_CLOSED")
                routes = {relay.route}
                if relay.api == 'anthropic-messages':
                    # Pi uses the pinned Anthropic SDK beta.messages path. No arbitrary query.
                    routes.add(relay.route + '?beta=true')
                if self.path not in routes or not relay.active.acquire(blocking=False):
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
                    digest = hashlib.sha256(body).hexdigest()
                    if digest == relay.last_body_sha256:
                        # Same bytes, no new state: a duplicate submission, never a new turn.
                        relay.event("context.duplicate_refused",
                                    **{"aeion.failure.code": "DUPLICATE_REQUEST"})
                        return self.deny(409, "DUPLICATE_REQUEST")
                    relay.last_body_sha256 = digest
                    maximum = payload.get("max_tokens", payload.get("max_completion_tokens"))
                    if type(maximum) is not int or not 1 <= maximum <= relay.max_output_tokens:
                        raise ValueError('CONTEXT_UNKNOWN')
                    for key in ("max_tokens", "max_completion_tokens"):
                        if key in payload and (type(payload[key]) is not int or not 1 <= payload[key] <= relay.max_output_tokens):
                            raise ValueError("CONTEXT_UNKNOWN")
                    if relay.required_effort and (payload.get('thinking', {}).get('type') != 'adaptive'
                            or payload.get('output_config', {}).get('effort') != relay.required_effort):
                        raise ValueError('CONTEXT_UNKNOWN')
                    if relay.required_reasoning_effort and (payload.get('thinking',{}).get('type')!='enabled'
                            or payload.get('reasoning_effort')!=relay.required_reasoning_effort):
                        raise ValueError('CONTEXT_UNKNOWN')
                    counted = relay.counter.count(payload)
                    relay.last_count = counted
                    relay.event("context.preflight", **{
                                                       ('aeion.cost.input_token_bound' if relay.context_basis == 'provider_usage'
                                                        else 'aeion.context.counted'): counted,
                                                       'aeion.context.measurement_basis': relay.context_basis,
                                                       "aeion.context.reserve": PROVIDER_RESERVE,
                                                       "aeion.context.max_output": maximum,
                                                       "aeion.context.tokenizer_revision": getattr(relay.counter, "revision", "fixture")})
                    if relay.forwarded_count >= relay.max_requests:
                        relay.closed = True
                        relay.last_error_code = "STEP_LIMIT"
                        relay.event("context.refused", **{"aeion.failure.code": "STEP_LIMIT"})
                        return self.deny(409, "STEP_LIMIT")
                    stop = relay.admission() if relay.admission else None
                    if stop:
                        relay.closed = True
                        relay.last_error_code = stop
                        relay.event("context.refused", **{"aeion.failure.code": stop})
                        return self.deny(409, stop)
                    context_count = counted
                    if relay.context_basis == 'provider_usage':
                        context_count = None
                        if relay.forwarded_count:
                            previous = relay.reported_usage[-1] if len(relay.reported_usage) == relay.forwarded_count else {}
                            if (previous.get('complete') is not True
                                    or any(type(previous.get(k)) is not int or previous[k] < 0
                                           for k in ('input_tokens','output_tokens'))):
                                relay.closed = True
                                relay.last_error_code = 'USAGE_UNKNOWN'
                                return self.deny(409, 'USAGE_UNKNOWN')
                            context_count = previous['input_tokens']
                            if context_count + previous['output_tokens'] > 300000:
                                relay.closed = True
                                relay.last_error_code = 'PROVIDER_CONTEXT_VIOLATION'
                                return self.deny(409, relay.last_error_code)
                    if context_count is not None and (not admit(context_count, maximum)
                            or context_count >= min(relay.limit, 250000)):
                        relay.closed = True
                        relay.last_error_code = 'AEION_HANDOVER'
                        relay.checkpoint(context_count, True)
                        return self.deny(409, "AEION_HANDOVER")
                    if context_count is not None and context_count >= max(1, relay.limit - 20000):
                        relay.checkpoint(context_count, False)
                    if relay.prices is not None and relay.cost_limit is not None:
                        input_rate = max(Decimal(str(relay.prices['input'])), Decimal(str(relay.prices.get('cacheWrite', 0))))
                        projected = (Decimal(counted) * input_rate + Decimal(maximum) * Decimal(str(relay.prices['output']))) / 1000000
                        if relay.projected_cost + projected > relay.cost_limit:
                            relay.closed = True
                            relay.last_error_code = 'BUDGET_STOP'
                            return self.deny(409, 'BUDGET_STOP')
                        relay.projected_cost += projected
                    headers = {name: value for name, value in self.headers.items()
                               if name.lower() in {'user-agent', 'anthropic-version', 'anthropic-beta'} or name.lower().startswith("x-opencode-")}
                    request = urllib.request.Request(relay.upstream, data=body, headers={**headers,
                        "Authorization": "Bearer " + relay.key, "Content-Type": "application/json",
                        "Accept-Encoding": "identity",
                    })
                    # No retries, redirects, environment proxy or raw request/response logging.
                    class NoRedirect(urllib.request.HTTPRedirectHandler):
                        def redirect_request(self, *_args, **_kwargs):
                            return None
                    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
                                                         urllib.request.HTTPSHandler(context=_tls_context()))
                    if not relay.claim_forward(counted):
                        self.deny(409,'RELAY_CLOSED')
                        return
                    usage = ReportedUsage()
                    attempt = 0
                    while True:
                        try:
                            opened = opener.open(request, timeout=UPSTREAM_IDLE_SECONDS)
                            break
                        except urllib.error.HTTPError as busy:
                            relay.last_http_status = busy.code
                            if (busy.code not in RETRYABLE_STATUSES or attempt >= len(PROVIDER_RETRY_DELAYS)
                                    or relay.closed):
                                raise
                            delay = retry_delay(busy, PROVIDER_RETRY_DELAYS[attempt])
                            busy.close()
                            attempt += 1
                            relay.provider_retries += 1
                            relay.event("provider.retry", **{"aeion.http.status": busy.code})
                            if relay.stopping.wait(delay) or relay.closed:
                                relay.last_error_code = relay.last_error_code or 'RELAY_CLOSED'
                                return self.deny(409, 'RELAY_CLOSED')
                    with opened as response:
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
                            usage.feed(block)
                            self.wfile.write(block)
                            self.wfile.flush()
                        relay.responses.remove(response)
                        summary=usage.summary()
                        relay.reported_usage.append(summary)
                        if (relay.prices is not None and relay.cost_limit is not None
                                and summary.get('complete') is True):
                            # The active lock serializes settlement with the next admission.
                            # Keep the counted full-input price and the larger provider cost;
                            # only finalized, unused output liability becomes available again.
                            resource_cost=Decimal(str(summary['cost_usd']))
                            spent_bound=max(resource_cost,projected)
                            if type(summary.get('output_tokens')) is int and 0<=summary['output_tokens']<=maximum:
                                spent_bound=max(resource_cost,
                                    (Decimal(counted)*input_rate+Decimal(summary['output_tokens'])*
                                     Decimal(str(relay.prices['output'])))/1000000)
                            relay.projected_cost+=spent_bound-projected
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
                    # A busy provider is named apart from a refusal: it produced nothing, and a
                    # review circuit may give its vote to another eligible reviewer.
                    if code == "PROVIDER_REJECTED" and error.code == 429:
                        code = "PROVIDER_RATE_LIMITED"
                    elif code == "PROVIDER_REJECTED" and error.code in RETRYABLE_STATUSES:
                        code = "PROVIDER_UNAVAILABLE"
                    relay.last_error_code = code
                    relay.event("provider.reason", **{"aeion.failure.code": code})
                    self.deny(error.code, code)
                except (ValueError, TypeError, KeyError):
                    relay.closed = True
                    relay.last_error_code = 'CONTEXT_UNKNOWN'
                    relay.event("context.refused", **{"aeion.failure.code": "CONTEXT_UNKNOWN"})
                    self.deny(409, "CONTEXT_UNKNOWN")
                except OSError as error:
                    relay.closed = True
                    # urllib wraps a connect timeout in URLError; a header/body read timeout is raw.
                    timed_out = isinstance(error, TimeoutError) or isinstance(getattr(error, 'reason', None), TimeoutError)
                    relay.last_error_code = 'PROVIDER_TIMEOUT' if timed_out else 'TRANSPORT_ERROR'
                    relay.event("provider.failed", **{"aeion.failure.code": relay.last_error_code})
                except Exception:
                    relay.closed = True
                    relay.last_error_code = 'CONTEXT_UNKNOWN'
                    relay.event("context.refused", **{"aeion.failure.code": "CONTEXT_UNKNOWN"})
                    self.deny(409, "CONTEXT_UNKNOWN")
                finally:
                    relay.active.release()

        # The harness runs on this host; the relay is never reachable from sandboxes or the LAN.
        self.server = ThreadingHTTPServer(bind or ("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()

    def claim_forward(self, counted):
        # Shutdown and the liability counter share one ordering point. Once closed, local
        # preflight cannot later start an uncounted provider request after a zero settlement.
        with self.dispatch_lock:
            if self.closed:
                return False
            self.forwarded_count += 1
            self.forwarded_counts.append(counted)
            return True

    def close(self):
        with self.dispatch_lock:
            self.closed = True
        self.stopping.set()
        for response in self.responses[:]:
            response.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        # The daemon HTTP handler may still be appending the final usage after the SDK has
        # read its stop event. Join that accounting boundary before the supervisor snapshots it.
        if self.active.acquire(timeout=5):
            self.active.release()
        else:
            self.accounting_complete = False
            self.last_error_code = self.last_error_code or 'RELAY_ACCOUNTING_INCOMPLETE'
