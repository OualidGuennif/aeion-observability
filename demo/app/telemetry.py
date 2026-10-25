"""Explicit metadata spans only. No automatic instrumentation or exception capture."""
import os
import json
import time
import urllib.request

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags, Status, StatusCode
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import ExportLogsServiceRequest


class Telemetry:
    def __init__(self):
        self.provider = TracerProvider(resource=Resource.create({"service.name": "aeion-demo"}))
        self.provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(
            endpoint=os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://otel-collector:4318/v1/traces"),
            timeout=5,
        )))
        self.tracer = self.provider.get_tracer("aeion.demo", "1")

    def emit(self, run, name, **attributes):
        parent = SpanContext(int(run["trace_id"], 16), int(run["root_span_id"], 16), False, TraceFlags(1))
        context = trace.set_span_in_context(NonRecordingSpan(parent))
        common = {
            "aeion.run.id": run["id"], "aeion.synthetic": run["synthetic"],
            "langfuse.session.id": run["id"], "aeion.context.limit": run["limit"],
            "aeion.context.metric": run["metric"],
        }
        if name == "gen_ai.request":
            common.update({"langfuse.observation.type": "generation", "gen_ai.operation.name": "chat",
                           "gen_ai.provider.name": "synthetic" if run["synthetic"] else "opencode-go"})
            if "aeion.cost.estimated_usd" in attributes:
                common["langfuse.observation.cost_details"] = json.dumps({"total": attributes["aeion.cost.estimated_usd"]})
        common.update({"langfuse.observation.metadata.run_id": run["id"],
                       "langfuse.observation.metadata.synthetic": str(run["synthetic"]).lower(),
                       "langfuse.observation.metadata.accounting_basis": "synthetic" if run["synthetic"] else "cli_estimate_not_invoice"})
        ended = time.time_ns()
        elapsed = attributes.get("aeion.step.elapsed_ms", 0)
        span = self.tracer.start_span(name, context=context, attributes={**common, **attributes},
                                     start_time=ended - int(elapsed * 1000000))
        if name in {"task.failed", "provider.failed", "context.violation", "context.refused"}:
            span.set_status(Status(StatusCode.ERROR, attributes.get("aeion.failure.code", "OPERATION_FAILED")))
        span.end(end_time=ended)
        request = ExportLogsServiceRequest()
        resource = request.resource_logs.add()
        resource.resource.attributes.add(key="service.name").value.string_value = "aeion-demo"
        scope = resource.scope_logs.add()
        scope.scope.name = "aeion.demo"
        record = scope.log_records.add(time_unix_nano=ended, observed_time_unix_nano=ended,
                                      severity_number=13 if name in {"gate.closed", "task.failed"} else 9,
                                      trace_id=bytes.fromhex(run["trace_id"]), span_id=bytes.fromhex(run["root_span_id"]))
        record.body.string_value = "aeion.event"
        for key, value in {**common, **attributes, "aeion.event.name": name}.items():
            field = record.attributes.add(key=key).value
            if type(value) is bool:
                field.bool_value = value
            elif type(value) is int:
                field.int_value = value
            elif type(value) is float:
                field.double_value = value
            else:
                field.string_value = str(value)
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", "http://otel-collector:4318/v1/logs")
        try:
            req = urllib.request.Request(endpoint, data=request.SerializeToString(), headers={"Content-Type": "application/x-protobuf"})
            with urllib.request.urlopen(req, timeout=1) as response:
                response.read(1024)
        except OSError:
            pass  # Durable local audit remains authoritative; export is best effort.

    def begin(self, run):
        span = self.tracer.start_span("demo.task", attributes={
            "aeion.run.id": run["id"], "aeion.synthetic": run["synthetic"],
            "langfuse.session.id": run["id"],
            "aeion.context.limit": run["limit"], "aeion.context.metric": run["metric"],
        })
        context = span.get_span_context()
        run.update(trace_id=format(context.trace_id, "032x"), root_span_id=format(context.span_id, "016x"))
        return span
