"""Durable bounded metadata audit; no CLI text, request bodies or secrets."""
import json
import os
from pathlib import Path
import threading


class Audit:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.lock = threading.Lock()

    def record(self, run, event):
        allowed = {"name", "id", "sequence", "time_unix_ns", "severity", "aeion.agent.number",
                   "aeion.context.observed", "aeion.context.counted", "aeion.context.hard_limit",
                   "gen_ai.usage.input_tokens", "gen_ai.usage.output_tokens", "gen_ai.request.model",
                   "aeion.check.passed", "aeion.artifact.changed", "aeion.memory.backend",
                   "aeion.app.probe_ms", "aeion.failure.code", "aeion.process.pid", "aeion.http.status"}
        allowed.update({"aeion.tool.name", "aeion.tool.status", "aeion.step.elapsed_ms", "trace_id", "span_id", "aeion.cost.estimated_usd", "aeion.human.interventions"})
        allowed.update({"aeion.context.reserve", "aeion.context.max_output", "aeion.context.tokenizer_revision"})
        allowed.update({"aeion.context.basis", "aeion.handover.sha256"})
        if set(event) - allowed or any(not isinstance(v, (str, int, float, bool)) or isinstance(v, str) and len(v) > 256 for v in event.values()):
            raise ValueError("INVALID_AUDIT_EVENT")
        path = self.folder / (run["id"] + ".events.jsonl")
        encoded = json.dumps(event, sort_keys=True)
        if len(encoded) > 4096:
            raise ValueError("AUDIT_EVENT_TOO_LARGE")
        with self.lock:
            if path.exists() and path.stat().st_size > 1048576:
                raise ValueError("AUDIT_FULL")
            with path.open("a") as output:
                path.chmod(0o600)
                output.write(encoded + "\n")
                output.flush()
                os.fsync(output.fileno())
            print(encoded, flush=True)
