#!/usr/bin/env python3
# Spec: knowledge/operations/agent-compatibility.md
"""Exercise the Pi RPC runner against a fake protocol server (no model calls)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / 'tools/agents/pi-rpc'

FAKE = '''#!/usr/bin/env python3
import json, os, sys, time

def emit(record):
    sys.stdout.write(json.dumps(record) + '\\n')
    sys.stdout.flush()

mode = os.environ.get('FAKE_MODE', 'normal')
delay = float(os.environ.get('FAKE_COMPACTION_DELAY', '0'))
if mode == 'exit':
    sys.exit(3)
for line in sys.stdin:
    try:
        command = json.loads(line)
    except ValueError:
        continue
    if command.get('type') != 'prompt':
        emit({'id': command.get('id'), 'type': 'response', 'command': command.get('type'), 'success': True, 'data': {}})
        continue
    if mode == 'error':
        emit({'id': command.get('id'), 'type': 'response', 'command': 'prompt', 'success': False, 'error': 'refused by fake'})
        continue
    emit({'id': command.get('id'), 'type': 'response', 'command': 'prompt', 'success': True, 'data': {'disposition': 'started'}})
    if mode == 'stream':
        while True:
            emit({'type': 'message_update', 'assistantMessageEvent': {'type': 'text_delta', 'delta': '.'}})
            time.sleep(0.05)
    text = command.get('message', '') if mode == 'echo' else 'HELLO'
    emit({'type': 'message_update', 'assistantMessageEvent': {'type': 'text_delta', 'delta': text}})
    # Pi starts a settlement compaction only after the aborted settlement, so aborted is the marker.
    emit({'type': 'agent_settled', 'aborted': mode in {'compact', 'compactfail'}})
    if mode == 'compact':
        time.sleep(delay)
        emit({'type': 'compaction_start', 'reason': 'manual'})
        emit({'type': 'compaction_end', 'reason': 'manual', 'aborted': False,
              'result': {'summary': 'summary', 'firstKeptEntryId': 'entry', 'tokensBefore': 288668,
                         'estimatedTokensAfter': 32000, 'usage': {}}})
        emit({'type': 'agent_start'})
        emit({'type': 'message_update', 'assistantMessageEvent': {'type': 'text_delta', 'delta': ' RESUMED'}})
        emit({'type': 'agent_settled', 'aborted': False})
    if mode == 'compactfail':
        time.sleep(delay)
        emit({'type': 'compaction_start', 'reason': 'manual'})
        emit({'type': 'compaction_end', 'reason': 'manual', 'aborted': False, 'errorMessage': 'summary failed'})
'''


class PiRpcTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.fake = self.dir / 'fake-pi'
        self.fake.write_text(FAKE)
        self.fake.chmod(0o755)

    def run_client(self, *args, mode='normal', prompt='hi', grace='0.5', delay='0'):
        env = dict(os.environ, FAKE_MODE=mode, FAKE_COMPACTION_DELAY=str(delay))
        command = [sys.executable, str(RUNNER), '--pi-executable', str(self.fake), '--grace', grace, *args]
        if prompt is not None:
            command += ['--', prompt]
        return subprocess.run(command, capture_output=True, text=True, timeout=30, env=env)

    def test_prompt_streams_text_and_exits_zero(self):
        result = self.run_client()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'HELLO\n')

    def test_compaction_that_starts_after_settlement_is_not_cut_off(self):
        # Pi emits agent_settled (aborted) before it emits compaction_start; the grace alone would exit.
        result = self.run_client(mode='compact', grace='0.3', delay='0.8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'HELLO RESUMED\n')

    def test_failed_compaction_exits_one(self):
        result = self.run_client(mode='compactfail', delay='0.3')
        self.assertEqual(result.returncode, 1)
        self.assertIn('compaction failed: summary failed', result.stderr)

    def test_prompt_file_supplies_the_message(self):
        prompt = self.dir / 'prompt.txt'
        prompt.write_text('from a file')
        result = self.run_client('--prompt-file', str(prompt), mode='echo', prompt=None)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'from a file\n')

    def test_pi_that_exits_before_reading_is_one_line_not_a_traceback(self):
        prompt = self.dir / 'prompt.txt'
        prompt.write_text('x' * 1_000_000)
        result = self.run_client('--prompt-file', str(prompt), mode='exit', prompt=None)
        self.assertEqual(result.returncode, 1)
        self.assertIn('pi-rpc: Pi exited before accepting the prompt', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_refused_prompt_exits_one(self):
        result = self.run_client(mode='error')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertIn('refused by fake', result.stderr)

    def test_missing_prompt_is_a_usage_error(self):
        result = self.run_client(prompt=None)
        self.assertEqual(result.returncode, 2)
        self.assertIn('a prompt is required', result.stderr)

    def test_deadline_bounds_a_stream_that_never_stops(self):
        result = self.run_client('--timeout', '1', mode='stream', grace='30')
        self.assertEqual(result.returncode, 1)
        self.assertIn('timed out after 1s', result.stderr)

    def test_repeated_mode_is_refused(self):
        result = self.run_client('--mode', 'rpc', '--mode', 'json')
        self.assertEqual(result.returncode, 2)
        self.assertIn('--mode may be given only once', result.stderr)


if __name__ == '__main__':
    unittest.main()
