"""A slow trace backend must not block native usage-accounting events."""
import sys
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from telemetry import Telemetry
from opentelemetry.sdk.trace.export import SpanExportResult


class RuntimeTelemetryTests(unittest.TestCase):
    def test_slow_trace_export_does_not_block_the_accounting_thread(self):
        release,finished=threading.Event(),threading.Event()
        captured=[]
        class Exporter:
            def __init__(self,**_kwargs):pass
            def export(self,spans):
                release.wait(3);captured.extend(spans)
                return SpanExportResult.SUCCESS
            def shutdown(self):pass
        with patch('telemetry.OTLPSpanExporter',Exporter),patch('telemetry.urllib.request.urlopen',side_effect=OSError):
            telemetry=Telemetry()
            run={'trace_id':'1'*32,'root_span_id':'2'*16,'id':'public-fixture','synthetic':True,
                'limit':250000,'metric':'active_context'}
            def emit():
                telemetry.emit(run,'model.step.started');finished.set()
            worker=threading.Thread(target=emit);worker.start()
            try:self.assertTrue(finished.wait(.5),'Trace exporter blocked native accounting')
            finally:
                release.set();worker.join(5);telemetry.provider.shutdown()
            self.assertEqual(len(captured),1)


if __name__=='__main__':unittest.main()
