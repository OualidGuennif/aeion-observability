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
                gate_status="passed", publisher_decision="published",
            )
        self.assertEqual(evidence["status"], "emitted")
        self.assertEqual(len(evidence["trace_id"]), 32)
        self.assertEqual(len(captured), 1)
        span = captured[0]
        self.assertEqual(span.name, "factory.build")
        self.assertEqual(span.attributes["aeion.build.id"], "b" * 32)
        self.assertEqual(span.attributes["aeion.feature.id"], "013")
        self.assertEqual(span.attributes["aeion.artifact.digest"], "d" * 64)
        self.assertEqual(format(span.context.trace_id, "032x"), evidence["trace_id"])


if __name__ == "__main__":
    unittest.main()
