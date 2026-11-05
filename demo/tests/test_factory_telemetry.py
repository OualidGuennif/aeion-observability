"""Factory trace evidence: identity only, best effort, and a real span when the SDK exists."""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory import telemetry


class AttributeTests(unittest.TestCase):
    def test_attributes_carry_identity_and_no_content(self):
        attributes = telemetry.build_attributes(
            "b" * 32, "013", "a" * 32, artifact_digest="d" * 64,
            base_sha="f" * 40, gate_status="passed", publisher_decision="published",
        )
        self.assertEqual(attributes["aeion.build.id"], "b" * 32)
        self.assertEqual(attributes["aeion.feature.id"], "013")
        self.assertEqual(attributes["aeion.attempt.id"], "a" * 32)
        self.assertEqual(attributes["aeion.artifact.digest"], "d" * 64)
        self.assertEqual(attributes["aeion.build.base_sha"], "f" * 40)
        self.assertEqual(attributes["aeion.build.gate"], "passed")
        self.assertEqual(attributes["aeion.build.publisher"], "published")
        self.assertEqual(attributes["langfuse.session.id"], "factory:" + "b" * 32)
        self.assertTrue(attributes["aeion.synthetic"])
        self.assertFalse(any(key in attributes for key in ("files", "diff", "prompt", "output")))

    def test_omitted_fields_are_absent_not_empty(self):
        attributes = telemetry.build_attributes("b" * 32, "013", "a" * 32)
        self.assertNotIn("aeion.artifact.digest", attributes)
        self.assertNotIn("aeion.build.gate", attributes)
        self.assertNotIn("aeion.build.publisher", attributes)

    def test_error_diagnostics_are_useful_bounded_and_content_free(self):
        attributes=telemetry.build_attributes('b'*32,'001','a'*32,gate_status='builder_error',duration_ms=65432,
            diagnostics={'failure_code':'CLI_STARTUP_FAILED','phase':'startup','process_exit_code':1,
                'cli_steps':0,'forwarded_count':0,'role':'author','execution_trace_id':'c'*32,
                'usage':{'complete':True,'cost_usd':'0'},'prompt':'private-canary','stderr':'private-canary'})
        self.assertEqual(attributes['langfuse.observation.level'],'ERROR')
        self.assertEqual(attributes['langfuse.observation.status_message'],'CLI_STARTUP_FAILED')
        self.assertEqual(attributes['langfuse.observation.metadata.process_exit_code'],1)
        self.assertEqual(attributes['langfuse.observation.metadata.forwarded_count'],0)
        self.assertEqual(attributes['aeion.build.duration_ms'],65432)
        self.assertNotIn('private-canary',str(attributes))
        rejected=telemetry.build_attributes('b'*32,'001','a'*32,diagnostics={'failure_code':'secret value',
            'phase':{},'process_exit_code':'private-canary','usage':{'complete':False,'cost_usd':'0'}})
        self.assertNotIn('langfuse.observation.metadata.failure_code',rejected)
        self.assertNotIn('langfuse.observation.metadata.measured_cost_usd',rejected)

    def test_interrupted_build_keeps_the_last_protected_cause_and_retained_count(self):
        attrs=telemetry.build_attributes('b'*32,'001','a'*32,gate_status='builder_error',diagnostics={
            'failure_code':'AGENT_TIMEOUT','check':{'status':'failed','reason':'missing_secret_accepted'},
            'retained_files_count':11,'stderr':'private-canary'})
        self.assertEqual(attrs['langfuse.observation.metadata.check_status'],'failed')
        self.assertEqual(attrs['langfuse.observation.metadata.check_reason'],'missing_secret_accepted')
        self.assertEqual(attrs['langfuse.observation.metadata.retained_files_count'],11)
        self.assertNotIn('private-canary',str(attrs))

    def test_known_candidate_recovery_is_a_warning_and_never_masks_a_failed_gate(self):
        diagnostic={'failure_code':'AGENT_TIMEOUT','candidate_recovered':True}
        attrs=telemetry.build_attributes('b'*32,'001','a'*32,gate_status='passed',diagnostics=diagnostic)
        self.assertEqual(attrs['langfuse.observation.level'],'WARNING')
        self.assertEqual(attrs['langfuse.observation.status_message'],'AUTHOR_LIMIT_CANDIDATE')
        failed=telemetry.build_attributes('b'*32,'001','a'*32,gate_status='failed',diagnostics=diagnostic)
        self.assertEqual(failed['langfuse.observation.level'],'ERROR')


class EmitTests(unittest.TestCase):
    def test_disabled_emitter_does_not_load_the_sdk(self):
        evidence = telemetry.FactoryTelemetry(enabled=False).emit(
            build_id="b" * 32, feature_id="013", attempt_id="a" * 32)
        self.assertEqual(evidence, {"status": "disabled"})

    def test_missing_sdk_is_reported_not_raised(self):
        with mock.patch.object(telemetry, "_load_otel", side_effect=ImportError):
            evidence = telemetry.FactoryTelemetry().emit(
                build_id="b" * 32, feature_id="013", attempt_id="a" * 32)
        self.assertEqual(evidence["status"], "unavailable")
        self.assertEqual(evidence["reason"], "opentelemetry_unavailable")

    def test_a_span_is_created_with_the_expected_attributes(self):
        try:
            from opentelemetry.sdk.trace.export import SpanExportResult
        except ImportError:
            self.skipTest("opentelemetry sdk not installed")
        captured = []

        class FakeExporter:
            def __init__(self, endpoint=None, timeout=None):
                self.endpoint = endpoint

            def export(self, spans):
                captured.extend(spans)
                return SpanExportResult.SUCCESS

            def shutdown(self):
                return None

            def force_flush(self, timeout_millis=None):
                return True

        real = telemetry._load_otel()
        fake_loader = lambda: (real[0], real[1], real[2], real[3], FakeExporter)
        with mock.patch.object(telemetry, "_load_otel", side_effect=fake_loader):
            evidence = telemetry.FactoryTelemetry(endpoint="http://collector.invalid/v1/traces").emit(
                build_id="b" * 32, feature_id="013", attempt_id="a" * 32,
                artifact_digest="d" * 64, base_sha="f" * 40,
                gate_status="builder_error", duration_ms=1234, diagnostics={'failure_code':'CLI_STARTUP_FAILED'},
            )
        self.assertEqual(evidence["status"], "exported_unconfirmed")
        self.assertEqual(evidence["confirmation"], "not_read_back")
        self.assertEqual(len(evidence["trace_id"]), 32)
        self.assertEqual(len(captured), 1)
        span = captured[0]
        self.assertEqual(span.name, "factory.build")
        self.assertEqual(span.attributes["aeion.build.id"], "b" * 32)
        self.assertEqual(span.attributes["aeion.feature.id"], "013")
        self.assertEqual(span.attributes["aeion.artifact.digest"], "d" * 64)
        self.assertEqual(format(span.context.trace_id, "032x"), evidence["trace_id"])
        self.assertEqual(span.end_time-span.start_time,1234*1000000)
        self.assertEqual(span.status.status_code.name,'ERROR')
        self.assertEqual(span.status.description,'CLI_STARTUP_FAILED')

    def _emit_with(self, exporter_class):
        try:
            from opentelemetry.sdk.trace.export import SpanExportResult  # noqa: F401
        except ImportError:
            self.skipTest("opentelemetry sdk not installed")
        real = telemetry._load_otel()
        fake_loader = lambda: (real[0], real[1], real[2], real[3], exporter_class)
        with mock.patch.object(telemetry, "_load_otel", side_effect=fake_loader):
            return telemetry.FactoryTelemetry(endpoint="http://collector.invalid/v1/traces").emit(
                build_id="b" * 32, feature_id="013", attempt_id="a" * 32)

    def test_an_exporter_failure_is_not_reported_as_emitted(self):
        try:
            from opentelemetry.sdk.trace.export import SpanExportResult
        except ImportError:
            self.skipTest("opentelemetry sdk not installed")

        class FailingExporter:
            def __init__(self, endpoint=None, timeout=None):
                pass

            def export(self, spans):
                return SpanExportResult.FAILURE

            def shutdown(self):
                return None

            def force_flush(self, timeout_millis=None):
                return True

        evidence = self._emit_with(FailingExporter)
        self.assertEqual(evidence["status"], "export_failed")
        self.assertEqual(evidence["reason"], "exporter_returned_failure")
        self.assertEqual(len(evidence["trace_id"]), 32)
        self.assertNotIn("confirmation", evidence)

    def test_an_exporter_exception_is_recorded_as_a_failure(self):
        class RaisingExporter:
            def __init__(self, endpoint=None, timeout=None):
                pass

            def export(self, spans):
                raise ConnectionError("collector down")

            def shutdown(self):
                return None

            def force_flush(self, timeout_millis=None):
                return True

        evidence = self._emit_with(RaisingExporter)
        self.assertEqual(evidence["status"], "export_failed")
        self.assertEqual(evidence["reason"], "ConnectionError")

    def test_a_backend_readback_is_what_confirms_storage(self):
        try:
            from opentelemetry.sdk.trace.export import SpanExportResult
        except ImportError:
            self.skipTest("opentelemetry sdk not installed")

        class FakeExporter:
            def __init__(self, endpoint=None, timeout=None):
                pass

            def export(self, spans):
                return SpanExportResult.SUCCESS

            def shutdown(self):
                return None

            def force_flush(self, timeout_millis=None):
                return True

        real = telemetry._load_otel()
        fake_loader = lambda: (real[0], real[1], real[2], real[3], FakeExporter)
        with mock.patch.object(telemetry, "_load_otel", side_effect=fake_loader), \
                mock.patch.object(telemetry, "confirm_trace",
                                  return_value={"confirmed": True, "observation": "obs-1"}):
            evidence = telemetry.FactoryTelemetry(
                endpoint="http://collector.invalid/v1/traces", readback=True).emit(
                    build_id="b" * 32, feature_id="013", attempt_id="a" * 32)
        self.assertEqual(evidence["status"], "confirmed")
        self.assertEqual(evidence["observation"], "obs-1")
        self.assertEqual(evidence["confirmation"], "backend_readback")

    def test_an_unconfirmed_readback_stays_unconfirmed(self):
        try:
            from opentelemetry.sdk.trace.export import SpanExportResult
        except ImportError:
            self.skipTest("opentelemetry sdk not installed")

        class FakeExporter:
            def __init__(self, endpoint=None, timeout=None):
                pass

            def export(self, spans):
                return SpanExportResult.SUCCESS

            def shutdown(self):
                return None

            def force_flush(self, timeout_millis=None):
                return True

        real = telemetry._load_otel()
        fake_loader = lambda: (real[0], real[1], real[2], real[3], FakeExporter)
        with mock.patch.object(telemetry, "_load_otel", side_effect=fake_loader), \
                mock.patch.object(telemetry, "confirm_trace",
                                  return_value={"confirmed": False, "reason": "trace_not_found"}):
            evidence = telemetry.FactoryTelemetry(
                endpoint="http://collector.invalid/v1/traces", readback=True).emit(
                    build_id="b" * 32, feature_id="013", attempt_id="a" * 32)
        self.assertEqual(evidence["status"], "exported_unconfirmed")
        self.assertEqual(evidence["readback_reason"], "trace_not_found")


if __name__ == "__main__":
    unittest.main()
