#!/usr/bin/env python3
"""Run the real token-feedback hook on transcripts shaped like Claude Code's and Codex's."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "token-feedback.py"
PROSE = ("Now I am going to look at the configuration files to understand how the hooks are wired together, "
         "then I will compare them with the adapter.")


def claude_user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def claude_assistant(*parts):
    content = [{"type": "text", "text": p} if isinstance(p, str) else {"type": "tool_use", "id": "t", "name": p[0], "input": {}}
               for p in parts]
    return {"type": "assistant", "message": {"role": "assistant", "content": content}}


def tool_result():
    return {"type": "user", "toolUseResult": {}, "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t", "content": "ok"}]}}


class TokenFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        # The hook writes its Stop record under its own root: run a copy inside the temporary project.
        (self.tmp / ".claude/hooks").mkdir(parents=True)
        shutil.copy(HOOK, self.tmp / ".claude/hooks/token-feedback.py")
        self.session = "s" + uuid.uuid4().hex
        self.transcript = self.tmp / f"{self.session}.jsonl"

    def write(self, *records):
        self.transcript.write_text("".join(json.dumps(r) + "\n" for r in records))

    def run_hook(self, event_name="PostToolUse", **extra):
        event = {"session_id": self.session, "hook_event_name": event_name,
                 "transcript_path": str(self.transcript), "tool_name": "Bash", **extra}
        result = subprocess.run([sys.executable, str(self.tmp / ".claude/hooks/token-feedback.py")],
                                input=json.dumps(event), capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_prose_between_tools_warns_once_per_turn(self):
        self.write(claude_user("fix it"), claude_assistant(PROSE, ("Bash",)), tool_result())
        first = self.run_hook()
        self.assertIn(f"narration: {len(PROSE)} chars", first)
        self.assertEqual(self.run_hook(), "")
        # A new prompt is a new turn.
        self.write(claude_user("fix it"), claude_assistant(PROSE, ("Bash",)), tool_result(),
                   claude_user("and now this"), claude_assistant(PROSE, ("Bash",)))
        self.assertIn("narration:", self.run_hook())

    def test_silent_tools_and_one_required_status_line_pass(self):
        self.write(claude_user("go"), claude_assistant(("Bash",)), tool_result(),
                   claude_assistant("Running the tests now.", ("Bash",)), tool_result(), claude_assistant(("Read",)))
        self.assertEqual(self.run_hook(), "")

    def test_json_progress_notes_are_counted_even_before_the_first_tool(self):
        note = '{"s":"test","n":"fix"}'
        self.write(claude_user("go"), claude_assistant(note, ("Bash",)), tool_result())
        feedback = self.run_hook()
        self.assertIn(f"narration: {len(note)} chars", feedback)
        self.assertNotIn("write one-line {json}", feedback)

    def test_silent_tools_and_final_answer_record_zero_narration(self):
        self.write(claude_user("go"), claude_assistant(("Bash",)), tool_result(),
                   claude_assistant(("Read",)), tool_result(), claude_assistant("Checks passed."))
        self.assertEqual(self.run_hook(), "")
        self.run_hook("Stop")
        record = json.loads((self.tmp / f".aeion/context/narration-{self.session}.json").read_text())
        self.assertEqual(record["chars"], 0)
        self.assertEqual(record["turns_with_narration"], 0)

    def test_second_status_line_is_counted_as_narration(self):
        self.write(claude_user("go"), claude_assistant("Running the tests now.", ("Bash",)), tool_result(),
                   claude_assistant("Reading the next file.", ("Read",)))
        self.assertIn("narration: 22 chars", self.run_hook())

    def test_injected_context_does_not_start_a_turn_and_compaction_does(self):
        self.write(claude_user("go"), claude_assistant(PROSE, ("Bash",)), tool_result(),
                   claude_user("<system-reminder>note</system-reminder>"))
        self.assertIn("narration:", self.run_hook())
        self.write(claude_user("go"), claude_assistant(PROSE, ("Bash",)), {"type": "system", "subtype": "compact_boundary"},
                   claude_assistant(("Bash",)))
        self.assertEqual(self.run_hook(), "")

    def test_stop_records_the_turn_without_counting_the_final_answer(self):
        self.write(claude_user("go"), claude_assistant(PROSE, ("Bash",)), tool_result(),
                   claude_assistant("Here is the long final answer, which is allowed to be prose." * 5))
        self.run_hook("Stop")
        self.run_hook("Stop")
        record = json.loads((self.tmp / f".aeion/context/narration-{self.session}.json").read_text())
        self.assertEqual(record["chars"], len(PROSE))
        self.assertEqual(record["turns_with_narration"], 1)

    def test_codex_rollout_shape(self):
        records = [
            {"type": "response_item", "payload": {"type": "message", "role": "user",
                                                  "content": [{"type": "input_text", "text": "<environment_context/>"}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "user",
                                                  "content": [{"type": "input_text", "text": "fix it"}]}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant",
                                                  "content": [{"type": "output_text", "text": PROSE}]}},
            {"type": "response_item", "payload": {"type": "function_call", "name": "shell", "arguments": "{}"}},
        ]
        self.write(*records)
        self.assertIn(f"narration: {len(PROSE)} chars", self.run_hook())

    def test_unknown_missing_or_hostile_input_is_silent(self):
        self.transcript.write_text("not json\n{\"other\": 1}\n")
        self.assertEqual(self.run_hook(), "")
        self.transcript.unlink()
        self.assertEqual(self.run_hook(), "")
        link = self.tmp / "link.jsonl"
        self.write(claude_user("go"), claude_assistant(PROSE, ("Bash",)))
        link.symlink_to(self.transcript)
        self.assertEqual(self.run_hook(transcript_path=str(link)), "")
        result = subprocess.run([sys.executable, str(HOOK)], input="[", capture_output=True, text=True, timeout=10)
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        bad = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"session_id": "../x"}),
                             capture_output=True, text=True, timeout=10)
        self.assertEqual((bad.returncode, bad.stdout), (0, ""))

    def test_symlinked_state_and_record_are_never_written_through(self):
        self.write(claude_user("go"), claude_assistant(PROSE, ("Bash",)), tool_result(), claude_assistant("Done."))
        target = self.tmp / "target.txt"
        target.write_text("keep\n")
        state = Path(tempfile.gettempdir()) / f"aeion-narration-{self.session}"
        state.symlink_to(target)
        self.addCleanup(state.unlink)
        self.assertEqual(self.run_hook(), "")
        (self.tmp / ".aeion/context").mkdir(parents=True)
        (self.tmp / f".aeion/context/narration-{self.session}.json").symlink_to(target)
        self.run_hook("Stop")
        self.assertEqual(target.read_text(), "keep\n")

    def test_full_rewrite_of_an_existing_file_is_named(self):
        self.write(claude_user("go"))
        big = "line\n" * 250
        note = self.run_hook(tool_name="Write", tool_input={"file_path": "a.py", "content": big},
                             tool_response={"type": "update"})
        self.assertIn("rewrite: Write resent 251 lines", note)
        self.assertEqual(self.run_hook(tool_name="Write", tool_input={"file_path": "a.py", "content": big},
                                       tool_response={"type": "create"}), "")
        self.assertEqual(self.run_hook(tool_name="Write", tool_input={"file_path": "a.py", "content": "x\n"},
                                       tool_response={"type": "update"}), "")


if __name__ == "__main__":
    unittest.main()
