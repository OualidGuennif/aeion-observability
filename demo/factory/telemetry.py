"""Bounded OTLP evidence for one factory build.

Only identity and outcome leave the process: build, feature and attempt ids, the
artifact digest, the pinned base, the gate and publisher outcomes. No source, prompt,
diff or receipt body is exported. A failure to export never rewrites the build result;
the receipt records the attempt, and the Langfuse read-back proves delivery.
"""
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_ENDPOINT = "http://127.0.0.1:4318/v1/traces"
DEFAULT_LANGFUSE = "http://127.0.0.1:3300"
SERVICE_NAME = "aeion-factory"
SPAN_NAME = "factory.build"
SESSION_PREFIX = "factory:"


def _langfuse_auth():
    auth = os.environ.get("LANGFUSE_AUTH")
    if auth:
        return auth
    path = Path(__file__).resolve().parents[2] / "demo/.local/stack.env"
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("LANGFUSE_AUTH="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except (OSError, UnicodeError):
        return None
    return None


def confirm_trace(trace_id, timeout=8):
    """Ask the deployed Langfuse whether it stored this build's span, with bounded retries."""
    auth = _langfuse_auth()
    if not auth:
        return {"confirmed": False, "reason": "langfuse_auth_unavailable"}
    base = os.environ.get("LANGFUSE_URL", DEFAULT_LANGFUSE).rstrip("/")
    if not isinstance(trace_id,str) or not re.fullmatch('[a-f0-9]{32}',trace_id):
        return {"confirmed":False,"reason":"trace_identity_invalid"}
    now=datetime.now(timezone.utc)
    filters=[{'type':'string','column':'traceId','operator':'=','value':trace_id}]
    query = urllib.parse.urlencode({"filter":json.dumps(filters),
        "fromStartTime":(now-timedelta(days=1)).isoformat(),"toStartTime":(now+timedelta(minutes=1)).isoformat(),
        "fields": "basic,metadata", "limit": 50})
    request = urllib.request.Request(base + "/api/public/v2/observations?" + query,
                                     headers={"Authorization": "Basic " + auth})
    deadline = time.monotonic() + timeout
    reason = "trace_not_found"
    while True:
        try:
            with urllib.request.urlopen(request, timeout=max(.1,deadline-time.monotonic())) as response:
                raw=response.read(1048577)
                if len(raw)>1048576:raise ValueError('readback_too_large')
                data = json.loads(raw).get("data")
        except Exception as exc:  # noqa: BLE001 - readback failure is evidence, not a crash
            data, reason = None, type(exc).__name__
        rows = data if isinstance(data, list) else []
        for row in rows:
            if isinstance(row, dict) and row.get("traceId") == trace_id and row.get("name") == SPAN_NAME:
                return {"confirmed": True, "observation": row.get("id")}
        if time.monotonic() >= deadline:
            return {"confirmed": False, "reason": reason}
        time.sleep(1)


def _load_otel():
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    return trace, TracerProvider, Resource, SimpleSpanProcessor, OTLPSpanExporter


def build_attributes(build_id, feature_id, attempt_id, artifact_digest=None, base_sha=None,
                     gate_status=None, publisher_decision=None, synthetic=True,
                     duration_ms=None, diagnostics=None):
    """The complete, allowlisted attribute set for one build span."""
    attributes = {
        "aeion.build.id": build_id,
        "aeion.feature.id": feature_id,
        "aeion.attempt.id": attempt_id,
        "aeion.synthetic": bool(synthetic),
        "langfuse.session.id": SESSION_PREFIX + build_id,
        "langfuse.observation.type": "span",
        "langfuse.observation.metadata.build_id": build_id,
        "langfuse.observation.metadata.feature_id": feature_id,
        "langfuse.observation.metadata.attempt_id": attempt_id,
    }
    if artifact_digest:
        attributes["aeion.artifact.digest"] = artifact_digest
        attributes["langfuse.observation.metadata.artifact_digest"] = artifact_digest
    if base_sha:
        attributes["aeion.build.base_sha"] = base_sha
    if gate_status:
        attributes["aeion.build.gate"] = gate_status
    if publisher_decision:
        attributes["aeion.build.publisher"] = publisher_decision
    if duration_ms is not None:
        attributes["aeion.build.duration_ms"] = max(0,min(86400000,int(duration_ms)))
    diagnostic=diagnostics if isinstance(diagnostics,dict) else {}
    for key,pattern in {'failure_code':r'[A-Z][A-Z0-9_]{1,63}',
            'error_type':r'[A-Za-z][A-Za-z0-9]{1,63}',
            'run_id':r'[a-f0-9]{32}','execution_trace_id':r'[a-f0-9]{32}'}.items():
        value=diagnostic.get(key)
        if isinstance(value,str) and re.fullmatch(pattern,value):
            attributes['langfuse.observation.metadata.'+key]=value
    for key,options in {'phase':{'preparing','building','checking','reviewing','publishing','startup'},
            'role':{'prepare','author','review'},'runtime':{'flue-openshell','flue-local','flue-just-bash'}}.items():
        if isinstance(diagnostic.get(key),str) and diagnostic[key] in options:
            attributes['langfuse.observation.metadata.'+key]=diagnostic[key]
    for key,low,high in (('process_exit_code',-255,255),('cli_steps',0,10000),('forwarded_count',0,10000)):
        value=diagnostic.get(key)
        if type(value) is int and low<=value<=high:attributes['langfuse.observation.metadata.'+key]=value
    check=diagnostic.get('check')
    if isinstance(check,dict):
        if isinstance(check.get('status'),str) and check['status'] in {'passed','failed','held','not_run'}:
            attributes['langfuse.observation.metadata.check_status']=check['status']
        if isinstance(check.get('reason'),str) and re.fullmatch('[a-z][a-z0-9_]{1,95}',check['reason']):
            attributes['langfuse.observation.metadata.check_reason']=check['reason']
    retained=diagnostic.get('retained_files_count')
    if type(retained) is int and 0<=retained<=32:
        attributes['langfuse.observation.metadata.retained_files_count']=retained
    measured=diagnostic.get('usage')
    if isinstance(measured,dict) and type(measured.get('complete')) is bool:
        attributes['langfuse.observation.metadata.usage_complete']=measured['complete']
        try:cost=Decimal(str(measured.get('cost_usd')))
        except InvalidOperation:cost=Decimal('NaN')
        if measured['complete'] and cost.is_finite() and 0<=cost<=1000:
            attributes['langfuse.observation.metadata.measured_cost_usd']=str(cost)
    code=attributes.get('langfuse.observation.metadata.failure_code')
    failed=bool(code) or gate_status in ('failed','builder_error','rejected')
    attributes['langfuse.observation.level']='ERROR' if failed else 'DEFAULT' if gate_status=='passed' else 'WARNING'
    if failed:
        attributes['langfuse.observation.status_message']=code or 'PROTECTED_CHECK_FAILED'
    return attributes


class _RecordingExporter:
    """Remember what the transport actually answered; a created span is not a delivery.

    ``SimpleSpanProcessor`` discards the exporter's return value, so the wrapper keeps it. A
    successful export still proves only that the local exporter accepted the span: the backend
    receipt is a separate readback and is never claimed here.
    """

    def __init__(self, exporter):
        self.exporter = exporter
        self.result = None
        self.error = None

    def export(self, spans):
        try:
            self.result = self.exporter.export(spans)
            return self.result
        except Exception as exc:  # noqa: BLE001 - the failure becomes evidence, not a crash
            from opentelemetry.sdk.trace.export import SpanExportResult
            self.error = type(exc).__name__
            return SpanExportResult.FAILURE

    def force_flush(self, timeout_millis=None):
        return self.exporter.force_flush(timeout_millis)

    def shutdown(self):
        return self.exporter.shutdown()


class FactoryTelemetry:
    def __init__(self, endpoint=None, service_name=SERVICE_NAME, enabled=True, readback=False):
        self.endpoint = endpoint or os.environ.get("AEION_FACTORY_OTLP_TRACES", DEFAULT_ENDPOINT)
        self.service_name = service_name
        self.enabled = bool(enabled)
        self.readback = bool(readback)

    def emit(self, *, build_id, feature_id, attempt_id, artifact_digest=None, base_sha=None,
             gate_status=None, publisher_decision=None, synthetic=True, duration_ms=None, diagnostics=None):
        if not self.enabled:
            return {"status": "disabled"}
        try:
            trace, TracerProvider, Resource, SimpleSpanProcessor, OTLPSpanExporter = _load_otel()
        except ImportError:
            return {"status": "unavailable", "reason": "opentelemetry_unavailable"}
        attributes = build_attributes(
            build_id, feature_id, attempt_id, artifact_digest=artifact_digest,
            base_sha=base_sha, gate_status=gate_status,
            publisher_decision=publisher_decision, synthetic=synthetic,
            duration_ms=duration_ms, diagnostics=diagnostics,
        )
        provider = TracerProvider(
            resource=Resource.create({"service.name": self.service_name}))
        recorder = _RecordingExporter(
            OTLPSpanExporter(endpoint=self.endpoint, timeout=5))
        provider.add_span_processor(SimpleSpanProcessor(recorder))
        tracer = provider.get_tracer("aeion.factory", "1")
        ended = time.time_ns()
        started = ended - attributes.get('aeion.build.duration_ms',0)*1000000
        span = tracer.start_span(SPAN_NAME, attributes=attributes, start_time=started)
        if attributes.get('langfuse.observation.level')=='ERROR':
            span.set_status(trace.Status(trace.StatusCode.ERROR,attributes['langfuse.observation.status_message']))
        span.end(end_time=ended)
        try:
            provider.force_flush()
        finally:
            provider.shutdown()
        context = span.get_span_context()
        evidence = {
            "trace_id": format(context.trace_id, "032x"),
            "span_id": format(context.span_id, "016x"),
            "session_id": SESSION_PREFIX + build_id,
            "endpoint": self.endpoint,
        }
        if getattr(recorder.result, "name", None) == "SUCCESS":
            if self.readback:
                receipt = confirm_trace(evidence["trace_id"])
                if receipt.get("confirmed"):
                    evidence.update(status="confirmed", confirmation="backend_readback",
                                    observation=receipt.get("observation"))
                else:
                    evidence.update(status="exported_unconfirmed",
                                    confirmation="not_confirmed",
                                    readback_reason=receipt.get("reason"))
            else:
                # Local export only; the Langfuse readback is what confirms storage.
                evidence.update(status="exported_unconfirmed", confirmation="not_read_back")
        else:
            evidence.update(
                status="export_failed",
                reason=recorder.error or (
                    "exporter_returned_failure" if recorder.result is not None
                    else "exporter_not_called"),
            )
        return evidence
