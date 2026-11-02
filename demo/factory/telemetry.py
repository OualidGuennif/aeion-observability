"""Bounded OTLP evidence for one factory build.

Only identity and outcome leave the process: build, feature and attempt ids, the
artifact digest, the pinned base, the gate and publisher outcomes. No source, prompt,
diff or receipt body is exported. A failure to export never rewrites the build result;
the receipt records the attempt, and the Langfuse read-back proves delivery.
"""
import os
import time

DEFAULT_ENDPOINT = "http://127.0.0.1:4318/v1/traces"
SERVICE_NAME = "aeion-factory"
SPAN_NAME = "factory.build"
SESSION_PREFIX = "factory:"


def _load_otel():
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    return trace, TracerProvider, Resource, SimpleSpanProcessor, OTLPSpanExporter


def build_attributes(build_id, feature_id, attempt_id, artifact_digest=None, base_sha=None,
                     gate_status=None, publisher_decision=None, synthetic=True,
                     duration_ms=None):
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
        attributes["aeion.build.duration_ms"] = int(duration_ms)
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
    def __init__(self, endpoint=None, service_name=SERVICE_NAME, enabled=True):
        self.endpoint = endpoint or os.environ.get("AEION_FACTORY_OTLP_TRACES", DEFAULT_ENDPOINT)
        self.service_name = service_name
        self.enabled = bool(enabled)

    def emit(self, *, build_id, feature_id, attempt_id, artifact_digest=None, base_sha=None,
             gate_status=None, publisher_decision=None, synthetic=True, duration_ms=None):
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
            duration_ms=duration_ms,
        )
        provider = TracerProvider(
            resource=Resource.create({"service.name": self.service_name}))
        recorder = _RecordingExporter(
            OTLPSpanExporter(endpoint=self.endpoint, timeout=5))
        provider.add_span_processor(SimpleSpanProcessor(recorder))
        tracer = provider.get_tracer("aeion.factory", "1")
        started = time.time_ns()
        span = tracer.start_span(SPAN_NAME, attributes=attributes, start_time=started)
        span.end(end_time=time.time_ns())
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
