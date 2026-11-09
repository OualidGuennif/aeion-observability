"""A slow trace or log backend must not block native usage-accounting events."""
import importlib.util
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import patch

APP_DIR=Path(__file__).resolve().parents[1]/'app'
sys.path.insert(0,str(APP_DIR))
try:
    from telemetry import Telemetry
    from opentelemetry.sdk.trace.export import SpanExportResult
except ImportError:
    Telemetry=None  # Docker-free CI intentionally has no optional telemetry SDK.


def _load_telemetry_with_stubs():
    class _AttrList:
        def add(self,**kw):return types.SimpleNamespace(key=kw.get('key',''),value=types.SimpleNamespace(
            string_value='',bool_value=False,int_value=0,double_value=0.0))
    class _RecordList:
        def add(self,**_kw):return types.SimpleNamespace(body=types.SimpleNamespace(string_value=''),attributes=_AttrList())
    class _ScopeList:
        def add(self):return types.SimpleNamespace(scope=types.SimpleNamespace(name=''),log_records=_RecordList())
    class _ResList:
        def add(self):return types.SimpleNamespace(
            resource=types.SimpleNamespace(attributes=_AttrList()),scope_logs=_ScopeList())
    class _Req:
        def __init__(self):self.resource_logs=_ResList()
        def SerializeToString(self):return b'proto-log'
    class _Span:
        def set_status(self,*_a):pass
        def end(self,**_kw):pass
        def get_span_context(self):return types.SimpleNamespace(trace_id=1,span_id=2)
    class _Tracer:
        def start_span(self,*_a,**_kw):return _Span()
    class _Provider:
        def __init__(self,**_kw):pass
        def add_span_processor(self,*_a):pass
        def get_tracer(self,*_a):return _Tracer()
        def shutdown(self):pass
    mods={
        'opentelemetry':types.SimpleNamespace(trace=types.SimpleNamespace(set_span_in_context=lambda s:s)),
        'opentelemetry.exporter.otlp.proto.http.trace_exporter':types.SimpleNamespace(OTLPSpanExporter=lambda **_kw:None),
        'opentelemetry.sdk.resources':types.SimpleNamespace(Resource=types.SimpleNamespace(create=lambda d:d)),
        'opentelemetry.sdk.trace':types.SimpleNamespace(TracerProvider=_Provider),
        'opentelemetry.sdk.trace.export':types.SimpleNamespace(BatchSpanProcessor=lambda *_a,**_kw:None),
        'opentelemetry.trace':types.SimpleNamespace(NonRecordingSpan=lambda p:p,SpanContext=lambda *_a:None,
            TraceFlags=lambda f:f,Status=lambda *_a:None,StatusCode=types.SimpleNamespace(ERROR=2)),
        'opentelemetry.proto.collector.logs.v1.logs_service_pb2':types.SimpleNamespace(ExportLogsServiceRequest=_Req),
    }
    spec=importlib.util.spec_from_file_location('telemetry_stubbed',APP_DIR/'telemetry.py')
    mod=importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,mods):
        spec.loader.exec_module(mod)
    return mod


class LogQueueTelemetryTests(unittest.TestCase):
    def test_slow_log_export_is_queued_off_the_accounting_thread(self):
        mod=_load_telemetry_with_stubs()
        release,finished,log_entered=threading.Event(),threading.Event(),threading.Event()
        logs=[]
        class LogResponse:
            def __enter__(self):return self
            def __exit__(self,*_a):return False
            def read(self,_n=None):return b''
        def slow_log(req,timeout=None):
            log_entered.set();release.wait(3);logs.append((req.full_url,timeout))
            return LogResponse()
        with patch.object(mod.urllib.request,'urlopen',side_effect=slow_log):
            telemetry=mod.Telemetry()
            run={'trace_id':'1'*32,'root_span_id':'2'*16,'id':'public-fixture','synthetic':True,
                'limit':250000,'metric':'active_context'}
            def emit():
                telemetry.emit(run,'model.step.started');finished.set()
            worker=threading.Thread(target=emit);worker.start()
            try:
                self.assertTrue(finished.wait(.5),'Log exporter blocked native accounting')
                self.assertTrue(log_entered.wait(1),'Background log worker did not start export')
            finally:
                release.set();worker.join(5);telemetry._log_queue.put_nowait(None);telemetry._log_queue.join()
            self.assertEqual(len(logs),1)


@unittest.skipIf(Telemetry is None,'requires the controller telemetry SDK')
class RuntimeTelemetryTests(unittest.TestCase):
    def test_slow_trace_export_does_not_block_the_accounting_thread(self):
        release,finished,log_entered=threading.Event(),threading.Event(),threading.Event()
        captured,logs=[],[]
        class Exporter:
            def __init__(self,**_kwargs):pass
            def export(self,spans):
                release.wait(3);captured.extend(spans)
                return SpanExportResult.SUCCESS
            def shutdown(self):pass
        class LogResponse:
            def __enter__(self):return self
            def __exit__(self,*_a):return False
            def read(self,_n=None):return b''
        def slow_log(req,timeout=None):
            log_entered.set();release.wait(3);logs.append((req.full_url,timeout))
            return LogResponse()
        with patch('telemetry.OTLPSpanExporter',Exporter),patch('telemetry.urllib.request.urlopen',side_effect=slow_log):
            telemetry=Telemetry()
            run={'trace_id':'1'*32,'root_span_id':'2'*16,'id':'public-fixture','synthetic':True,
                'limit':250000,'metric':'active_context'}
            def emit():
                telemetry.emit(run,'model.step.started');finished.set()
            worker=threading.Thread(target=emit);worker.start()
            try:
                self.assertTrue(finished.wait(.5),'Trace or log exporter blocked native accounting')
                self.assertTrue(log_entered.wait(1),'Background log worker did not start export')
            finally:
                release.set();worker.join(5);telemetry._log_queue.join();telemetry.provider.shutdown()
            self.assertEqual(len(captured),1)
            self.assertEqual(len(logs),1)


if __name__=='__main__':unittest.main()
