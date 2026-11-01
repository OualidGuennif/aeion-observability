#!/usr/bin/env python3
"""Boundary, recovery and refusal regressions for the real budget implementation."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "budget.py"
spec = importlib.util.spec_from_file_location("budget", MODULE)
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "-qm", "initial", "--allow-empty"], check=True)
        self.transcript = self.root / "test-session.jsonl"
        self.event = {"session_id": "test-session", "hook_event_name": "PreToolUse", "tool_name": "Edit",
                      "tool_input": {"file_path": str(self.root / "src.py")}, "transcript_path": str(self.transcript)}
        self.observe(10)

    def observe(self, tokens):
        usage = dict.fromkeys(budget.FIELDS, 0)
        usage["input_tokens"] = tokens
        self.transcript.write_text(json.dumps({"type": "assistant", "message": {"usage": usage}}) + "\n")

    def call(self, **changes):
        return budget.handle(self.root, {**self.event, **changes})

    def test_warning_boundary_and_latched_closure(self):
        self.observe(249999)
        self.assertEqual(self.call(), {})
        self.observe(250000)
        first = self.call()
        self.assertIn("250k", first["systemMessage"])
        self.assertEqual(first["hookSpecificOutput"]["permissionDecision"], "deny")
        again = self.call()
        self.assertNotIn("systemMessage", again)
        self.observe(100)
        # A compaction the adapter never saw ends the latch instead of gating a 100-token session forever; the
        # closure it owed survives as a debt the settlement enforces.
        self.assertEqual(self.call(), {})
        self.assertIn("closure is still owed", self.call(hook_event_name="Stop")["stopReason"])

    def test_a_second_fall_clears_the_latch_while_the_debt_survives(self):
        # The first fall sets closure_owed; climbing back over 250k re-latches. A harness that compacts again
        # without a SessionStart must still be released, or the debt turns the latch into a permanent gate:
        # the debt is enforced by Stop, never by keeping the session latched.
        self.observe(260000)
        self.assertIn("250k", self.call()["systemMessage"])
        self.observe(100)
        self.assertEqual(self.call(), {})
        self.observe(260000)
        self.assertIn("250k", self.call()["systemMessage"])
        self.observe(100)
        self.assertEqual(self.call(), {})
        state = json.loads((self.root / ".aeion/context/test-session.json").read_text())
        self.assertEqual(state["state"], "RUNNING")
        self.assertEqual(state["closure_owed"], "due")

    def test_handover_is_created_only_when_closure_needs_it(self):
        handover = budget.handover_path(self.root, "test-session")
        start = self.call(hook_event_name="SessionStart", source="startup")
        self.assertNotIn("Recovery", start["hookSpecificOutput"]["additionalContext"])
        self.call()
        self.assertFalse(handover.exists())
        self.observe(250000)
        self.assertIn(str(handover.relative_to(self.root)), self.call()["systemMessage"])
        self.assertIn("TODO", handover.read_text())
        resume = self.call(hook_event_name="SessionStart", source="resume")
        self.assertIn("Recovery", resume["hookSpecificOutput"]["additionalContext"])

    def test_refused_compaction_and_checkpoint_create_the_skeleton_to_fill(self):
        handover = budget.handover_path(self.root, "test-session")
        self.call()
        with self.assertRaisesRegex(ValueError, "handover sections"):
            budget.checkpoint(self.root, "test-session", "HEAD")
        handover.unlink()
        self.assertIn(str(handover.relative_to(self.root)), self.call(hook_event_name="PreCompact")["reason"])
        self.assertTrue(handover.is_file())

    def test_observed_limit_forces_handover_and_compaction_without_stopping(self):
        self.observe(300000)
        first = self.call()
        self.assertIn("300k", first["systemMessage"])
        self.assertEqual(first["hookSpecificOutput"]["permissionDecision"], "deny")
        # At 300k only the handover and its checkpoint remain; task state and docs were 250k's closure.
        handover = budget.handover_path(self.root, "test-session")
        self.assertNotIn("hookSpecificOutput", self.call(tool_name="Write", tool_input={"file_path": str(handover)}))
        tasks = self.call(tool_name="Edit", tool_input={"file_path": str(self.root / "work/current.md")})
        self.assertEqual(tasks["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertFalse(self.call(hook_event_name="Stop")["continue"])
        self.assertNotIn("continue", self.call(hook_event_name="SessionStart", source="resume"))
        # Compaction ends the forced closure: the run continues instead of latching a stop.
        self.call(hook_event_name="SessionStart", source="compact")
        self.observe(1)
        self.assertEqual(self.call(), {})
        state = json.loads((self.root / ".aeion/context/test-session.json").read_text())
        self.assertEqual(state["state"], "RUNNING")

    def test_cache_counts_once_per_latest_request(self):
        usage = {"input_tokens": 1000, "cache_creation_input_tokens": 4000,
                 "cache_read_input_tokens": 244000, "output_tokens": 1000}
        record = json.dumps({"type": "assistant", "message": {"usage": usage}}) + "\n"
        self.transcript.write_text(record * 2)
        self.assertEqual(budget.native_usage(self.transcript, "test-session"), 250000)

    def test_synthetic_records_do_not_hide_the_latest_request(self):
        synthetic = json.dumps({"type": "assistant", "message": {"model": "<synthetic>",
                                                                 "usage": dict.fromkeys(budget.FIELDS, 0)}}) + "\n"
        self.observe(1000)
        self.transcript.write_text(self.transcript.read_text() + synthetic * 2)
        self.assertEqual(budget.native_usage(self.transcript, "test-session"), 1000)
        self.call(hook_event_name="UserPromptSubmit")
        self.assertEqual(self.call(hook_event_name="UserPromptSubmit"), {})
        self.transcript.write_text(synthetic)
        self.assertIsNone(budget.native_usage(self.transcript, "test-session"))
        # A compaction boundary still hides the older request, and a skipped record cannot lift a stop.
        boundary = json.dumps({"type": "system", "subtype": "compact_boundary"}) + "\n"
        self.observe(1000)
        self.transcript.write_text(self.transcript.read_text() + boundary + synthetic)
        self.assertIsNone(budget.native_usage(self.transcript, "test-session"))
        self.observe(300000)
        self.transcript.write_text(self.transcript.read_text() + synthetic)
        self.assertEqual(self.call()["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_missing_usage_stops_after_one_prompt_bootstrap(self):
        self.transcript.write_text("")
        self.assertEqual(self.call(hook_event_name="UserPromptSubmit"), {})
        self.assertFalse(self.call(hook_event_name="UserPromptSubmit")["continue"])

    def test_delayed_native_usage_blocks_work_without_poisoning_session(self):
        self.transcript.write_text("")
        self.call(hook_event_name="SessionStart", source="startup")
        self.assertEqual(self.call(hook_event_name="UserPromptSubmit"), {})
        # The tool call is denied, but the agent keeps running so it can retry the call.
        self.assertEqual(self.call()["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertNotIn("continue", self.call())
        self.assertEqual(self.call(hook_event_name="PostToolUse"), {})
        self.observe(1000)
        self.assertEqual(self.call(), {})

    def test_delayed_usage_after_compaction_can_recover_without_new_prompt(self):
        self.call(hook_event_name="SessionStart", source="compact")
        self.transcript.write_text(json.dumps({"type": "system", "subtype": "compact_boundary"}) + "\n")
        self.assertEqual(self.call()["hookSpecificOutput"]["permissionDecision"], "deny")
        self.observe(1000)
        self.assertEqual(self.call(), {})

    def test_precompact_latches_warning_and_delivers_it_at_next_supported_event(self):
        self.observe(250000)
        self.assertEqual(self.call(hook_event_name="PreCompact")["decision"], "block")
        state = json.loads((self.root / ".aeion/context/test-session.json").read_text())
        self.assertEqual(state["state"], "HANDOVER_REQUIRED")
        self.assertIn("250k", self.call(tool_name="Read")["systemMessage"])

    def test_resume_does_not_claim_an_unverified_compaction(self):
        self.observe(250000)
        self.call(hook_event_name="PreCompact")
        result = self.call(hook_event_name="SessionStart", source="resume")
        self.assertIn("closure remains required", result["systemMessage"])
        self.assertNotIn("verified handover was retained", result["systemMessage"])

    def test_untracked_code_requires_current_task_update_before_checkpoint(self):
        (self.root / '.gitignore').write_text('.aeion/\nwork/handovers/\n*.jsonl\n')
        (self.root / 'work').mkdir(exist_ok=True)
        current = self.root / 'work/current.md'
        current.write_text('# Current work\n')
        budget.git(self.root, 'add', '.gitignore', 'work/current.md')
        budget.git(self.root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'task fixture')
        self.call()
        handover = budget.ensure_handover(self.root, 'test-session')
        handover.write_text(handover.read_text().replace('TODO', 'Fixture evidence'))
        (self.root / 'new-feature.py').write_text('value = 1\n')
        actual_run = subprocess.run

        def run(command, **options):
            return actual_run(command, **options) if command[0] == 'git' else subprocess.CompletedProcess(command, 0)

        with patch.object(budget.subprocess, 'run', side_effect=run):
            with self.assertRaisesRegex(ValueError, 'work/current.md'):
                budget.checkpoint(self.root, 'test-session', 'HEAD')
            # Local play keeps no task entry, so its checkpoint does not ask for one.
            budget.git(self.root, 'config', 'aeion.mode', 'local')
            budget.checkpoint(self.root, 'test-session', 'HEAD')
            budget.git(self.root, 'config', '--unset', 'aeion.mode')
            # An included file cannot switch the mode: only the repository's own config counts.
            outside = tempfile.TemporaryDirectory()
            self.addCleanup(outside.cleanup)
            included = Path(outside.name) / 'mode.cfg'
            included.write_text('[aeion]\n\tmode = local\n')
            budget.git(self.root, 'config', 'include.path', str(included))
            with self.assertRaisesRegex(ValueError, 'work/current.md'):
                budget.checkpoint(self.root, 'test-session', 'HEAD')
            budget.git(self.root, 'config', '--unset', 'include.path')
            current.write_text('# Current work\nTask updated.\n')
            budget.checkpoint(self.root, 'test-session', 'HEAD')

    def test_checkpoint_command_uses_an_existing_base(self):
        # A clone without remotes must not be told to diff against a branch that does not exist.
        self.assertIn('--base HEAD --verify', budget.checkpoint_command(self.root, 'test-session'))
        budget.git(self.root, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
        self.assertIn('--base origin/main --verify', budget.checkpoint_command(self.root, 'test-session'))
        budget.git(self.root, 'update-ref', 'refs/remotes/origin/develop', 'HEAD')
        self.assertIn('--base origin/develop --verify', budget.checkpoint_command(self.root, 'test-session'))
        plain = tempfile.TemporaryDirectory()
        self.addCleanup(plain.cleanup)
        self.assertNotIn('--base', budget.checkpoint_command(Path(plain.name), 'test-session'))

    def test_plain_folder_checkpoints_without_git_or_base(self):
        # Many users have no git: the fingerprint is the files on disk and no diff check runs.
        plain = tempfile.TemporaryDirectory()
        self.addCleanup(plain.cleanup)
        root = Path(plain.name)
        (root / 'app.py').write_text('value = 1\n')
        (root / 'node_modules').mkdir()
        (root / 'node_modules/dep.js').write_text('x\n')
        before = budget.fingerprint(root)
        (root / 'node_modules/dep.js').write_text('y\n')
        self.assertEqual(budget.fingerprint(root), before)
        (root / 'app.py').write_text('value = 2\n')
        self.assertNotEqual(budget.fingerprint(root), before)
        budget.handle(root, {**self.event, 'transcript_path': str(self.transcript)})
        handover = budget.ensure_handover(root, 'test-session')
        handover.write_text(handover.read_text().replace('TODO', 'Fixture evidence'))
        commands = []
        actual_run = subprocess.run

        def run(command, **options):
            commands.append(command)
            return actual_run(command, **options) if command[0] == 'git' else subprocess.CompletedProcess(command, 0)

        with patch.object(budget.subprocess, 'run', side_effect=run):
            budget.checkpoint(root, 'test-session', None)
        self.assertFalse(any('--diff' in command for command in commands))
        # A folder that has a .git git cannot read is a broken repository, never a plain folder.
        (root / '.git').write_text('gitdir: /nonexistent\n')
        with self.assertRaises(subprocess.CalledProcessError):
            budget.fingerprint(root)

    def test_launcher_enters_its_project_before_executing_runtime(self):
        launcher = MODULE.parent / "run"
        fake = self.root / "claude"
        fake.write_text("#!/usr/bin/env python3\nimport os\nprint(os.getcwd())\n")
        fake.chmod(0o755)
        # The baseline subprocess is an independent gate, replaced only in this launcher fixture.
        code = "import runpy,subprocess; from unittest.mock import patch; "
        code += f"\nwith patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)):\n runpy.run_path({str(launcher)!r}, run_name='__main__')\n"
        result = subprocess.run(["python3", "-c", code], cwd=self.root,
                                env={**budget.os.environ, "PATH": str(self.root) + budget.os.pathsep + budget.os.environ["PATH"]},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(MODULE.parents[2]))

    def test_invalid_counts_and_cross_session_paths_are_refused(self):
        for value in (True, -1, "1"):
            self.transcript.write_text(json.dumps({"type": "assistant", "message": {
                "usage": {**dict.fromkeys(budget.FIELDS, 0), "input_tokens": value}}}) + "\n")
            with self.assertRaises(ValueError):
                budget.native_usage(self.transcript, "test-session")
        with self.assertRaises(ValueError):
            budget.native_usage(self.transcript, "other-session")
        with self.assertRaises(ValueError):
            budget.session_id("../../secret")

    def test_compaction_boundary_does_not_reuse_old_usage(self):
        self.transcript.write_text(self.transcript.read_text() + json.dumps({"type": "system", "subtype": "compact_boundary"}) + "\n")
        self.assertIsNone(budget.native_usage(self.transcript, "test-session"))

    def test_closure_alert_and_settlement_name_the_checkpoint_command(self):
        self.observe(250000)
        command = budget.checkpoint_command(self.root, 'test-session')
        # An agent that is never told the command cannot run it; exploration commands are denied in closure.
        self.assertIn(command, self.call()['hookSpecificOutput']['permissionDecisionReason'])
        stop = self.call(hook_event_name='Stop')
        self.assertIn(command, stop['stopReason'])
        # A claimed checkpoint without a receipt is named as missing, so the claim cannot pass as verification.
        self.assertIn('No verified checkpoint receipt', stop['stopReason'])

    def test_closure_admits_project_markdown_but_not_code(self):
        self.observe(250000)
        allowed = ('cockpit/README.md', 'docs/guide.mdx')
        for path in allowed:
            result = self.call(tool_name='Edit', tool_input={'file_path': str(self.root / path)})
            self.assertNotIn('permissionDecision', result.get('hookSpecificOutput', {}), path)
        denied = self.call(tool_name='Edit', tool_input={'file_path': str(self.root / 'cockpit/lib/app.ts')})
        self.assertEqual(denied['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_checkpoint_refusal_reports_the_failing_check_output(self):
        self.call()
        handover = budget.ensure_handover(self.root, 'test-session')
        handover.write_text(handover.read_text().replace('TODO', 'Fixture evidence'))
        failing = (budget.sys.executable, '-c', "print('FAIL knowledge/index.md: broken'); raise SystemExit(1)")
        with patch.object(budget, 'CHECKS', (failing,)):
            with self.assertRaisesRegex(ValueError, 'broken'):
                budget.checkpoint(self.root, 'test-session', 'HEAD')

    def test_precompact_requires_a_current_checkpoint_below_the_forced_band(self):
        result = self.call(hook_event_name="PreCompact")
        self.assertEqual(result["decision"], "block")
        handover = budget.handover_path(self.root, "test-session")
        state_file = self.root / ".aeion/context/test-session.json"
        state = json.loads(state_file.read_text())
        state["checkpoint"] = {"tree": budget.fingerprint(self.root),
                               "handover": budget.hashlib.sha256(handover.read_bytes()).hexdigest()}
        budget.atomic(state_file, json.dumps(state))
        self.assertEqual(self.call(hook_event_name="PreCompact"), {})
        (self.root / "new.py").write_text("print('change')\n")
        self.assertEqual(self.call(hook_event_name="PreCompact")["decision"], "block")

    def test_precompact_compacts_a_verified_handover_that_went_stale(self):
        # A receipt that verified this handover and then went stale must not make the compaction impossible: the
        # only work the gate admits is the checkpoint, so a session that edited once could never compact again.
        handover = budget.ensure_handover(self.root, "test-session")
        handover.write_text("".join(f"## {h}\nEvidence\n" for h in budget.HEADINGS))
        self.observe(260000)
        self.call()
        state_file = self.root / ".aeion/context/test-session.json"
        state = json.loads(state_file.read_text())
        state["checkpoint"] = {"tree": budget.fingerprint(self.root),
                               "handover": budget.hashlib.sha256(handover.read_bytes()).hexdigest()}
        budget.atomic(state_file, json.dumps(state))
        (self.root / "new.py").write_text("print('change')\n")
        result = self.call(hook_event_name="PreCompact")
        self.assertNotIn("decision", result)
        self.assertIn("compacting now", result["systemMessage"])
        self.assertEqual(json.loads(state_file.read_text())["closure_owed"], "due")

    def test_300k_stopgap_compacts_and_keeps_the_closure_owed(self):
        # The 300k profile freezes code, so a check that failed before this session would leave no verified
        # checkpoint and no way to repair it. The compaction runs; the closure stays owed.
        self.observe(300000)
        self.call()
        result = self.call(hook_event_name="PreCompact")
        self.assertNotIn("decision", result)
        self.assertIn("closure stays owed", result["systemMessage"])
        start = self.call(hook_event_name="SessionStart", source="compact")
        self.assertIn("Closure still owed", start["hookSpecificOutput"]["additionalContext"])
        # The new epoch admits the code edit that repairs the failing check.
        self.observe(1)
        self.assertEqual(self.call(tool_input={"file_path": str(self.root / "src.py")}), {})
        # A stop is refused while the closure is owed, and it names the command that settles it.
        stop = self.call(hook_event_name="Stop")
        self.assertFalse(stop["continue"])
        self.assertIn("closure is still owed", stop["stopReason"])
        self.assertIn("checkpoint --session test-session", stop["stopReason"])

    def test_a_verified_checkpoint_settles_the_owed_closure(self):
        self.observe(300000)
        self.call()
        self.call(hook_event_name="PreCompact")
        self.call(hook_event_name="SessionStart", source="compact")
        self.observe(1)
        self.call()
        handover = budget.ensure_handover(self.root, "test-session")
        handover.write_text(handover.read_text().replace("TODO", "Fixture evidence"))
        (self.root / "work").mkdir(exist_ok=True)
        (self.root / "work/current.md").write_text("# Current work\n\nFixture\n")
        state_file = self.root / ".aeion/context/test-session.json"
        with patch.object(budget, "CHECKS", ((budget.sys.executable, "-c", "pass"),)), \
                patch.object(budget, "git_active", lambda root: False):
            budget.checkpoint(self.root, "test-session", None)
            # The receipt settles the debt when the next event reads it, not when the command writes it.
            self.assertEqual(json.loads(state_file.read_text())["closure_owed"], "due")
            self.assertEqual(self.call(hook_event_name="Stop"), {})
        self.assertNotIn("closure_owed", json.loads(state_file.read_text()))

    def test_document_edits_allowed_and_shell_injection_denied_during_closure(self):
        self.observe(250000)
        self.assertNotIn("permissionDecision", self.call(tool_input={"file_path": str(self.root / "knowledge/policy.md")}).get("hookSpecificOutput", {}))
        for command in ("tools/knowledge/doc-links; touch /tmp/unsafe", "python3 -c 'print(1)'",
                        "git status --short && echo unsafe", "tools/knowledge/doc-links\nrm -rf x", "echo 'unterminated"):
            self.assertEqual(self.call(tool_name="Bash", tool_input={"command": command})["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(self.call(tool_name="Bash", tool_input={"command": "tools/knowledge/doc-links"}), {})

    def test_plain_shell_reads_are_closure_tools(self):
        # Codex reads only through its shell, so closure must let it read the handover it has to fill.
        self.observe(250000)
        for command in ("sed -n 1,200p work/handovers/x.md", "rg -n TODO work/handovers/x.md", "cat AGENTS.md",
                        "head -n 40 knowledge/index.md"):
            result = self.call(tool_name="Bash", tool_input={"command": command})
            self.assertNotIn("permissionDecision", result.get("hookSpecificOutput", {}), command)
        secret = "." + "env"
        for command in (f"cat {secret}", f"cat config/{secret}.local", "cat .e*", "rg --pre=sh x",
                        "sed -i s/a/b/ AGENTS.md", "sed -n 1w/tmp/x AGENTS.md", "cat AGENTS.md > copy.md",
                        "cat $HOME/x", "python3 -c 1"):
            result = self.call(tool_name="Bash", tool_input={"command": command})
            self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny", command)

    def test_checkpoint_is_admitted_from_any_folder_and_only_for_this_root(self):
        # A shell left in a subfolder at the alert must still reach this root's checkpoint.
        self.observe(250000)
        self.call()
        root = self.root.resolve()
        (root / "demo/copy").mkdir(parents=True)
        tail = "checkpoint --session test-session --base origin/develop --verify"
        allowed = [(f"python3 tools/context/budget.py {tail}", root),
                   (f"python3 {root}/tools/context/budget.py {tail}", root / "demo/copy"),
                   (f"cd {root} && python3 tools/context/budget.py {tail}", root / "demo/copy"),
                   (f"cd ../.. && python3 tools/context/budget.py {tail}", root / "demo/copy"),
                   ("python3 tools/context/budget.py checkpoint --session test-session --verify", root),
                   # The token is not compared to this session: `ready` opens the gate, never the spelling.
                   ("python3 tools/context/budget.py checkpoint --session other-session --verify", root),
                   (f"cd {root}", root / "demo/copy")]
        for command, cwd in allowed:
            self.assertEqual(self.call(tool_name="Bash", tool_input={"command": command}, cwd=str(cwd)), {}, command)
        refused = [(f"python3 tools/context/budget.py {tail}", root / "demo/copy"),
                   (f"cd /tmp && python3 {root}/tools/context/budget.py {tail}", root),
                   (f"cd {root} && python3 tools/context/budget.py {tail} && rm -rf x", root),
                   (f"cd {root}; python3 tools/context/budget.py {tail}", root),
                   (f"python3 tools/context/budget.py checkpoint --session a/b --verify", root),
                   (f"python3 tools/context/budget.py checkpoint --session test-session --base 'a;b' --verify", root),
                   ("cd /tmp", root)]
        for command, cwd in refused:
            result = self.call(tool_name="Bash", tool_input={"command": command}, cwd=str(cwd))
            self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny", command)

    def test_checkpoint_refusal_names_the_faulty_heading(self):
        handover = budget.ensure_handover(self.root, "test-session")
        self.call()
        handover.write_text(handover.read_text().replace("TODO", "Fixture").replace("## Completed\n", "## Completed (commits)\n"))
        with self.assertRaisesRegex(ValueError, r"missing heading: ## Completed \(exact line\)$"):
            budget.checkpoint(self.root, "test-session", "HEAD")
        handover.write_text(handover.read_text().replace("## Completed (commits)\n", "## Completed\n").replace("Fixture", "TODO", 1))
        with self.assertRaisesRegex(ValueError, "a section still reads TODO"):
            budget.checkpoint(self.root, "test-session", "HEAD")

    def test_alerts_name_the_handover_headings(self):
        # An agent that writes the handover itself never sees the template (Pi FB-002).
        self.observe(250000)
        self.assertIn("## Scope, ## Completed, ## Remaining, ## Constraints, ## Evidence", self.call()["systemMessage"])
        self.observe(300000)
        self.assertIn("## Evidence", self.call()["systemMessage"])

    def test_stale_receipt_names_the_changed_paths(self):
        # A live log in the tree stales every receipt; the refusal names it (dsh FB-007, OpenCode FB-003).
        self.call(hook_event_name="PreCompact")
        handover = budget.handover_path(self.root, "test-session")
        state_file = self.root / ".aeion/context/test-session.json"
        state = json.loads(state_file.read_text())
        files = budget.tree_files(self.root)
        state["checkpoint"] = {"tree": budget.fingerprint(self.root, files), "files": files,
                               "handover": budget.hashlib.sha256(handover.read_bytes()).hexdigest()}
        budget.atomic(state_file, json.dumps(state))
        self.assertEqual(self.call(hook_event_name="PreCompact"), {})
        (self.root / "run.jsonl").write_text("{}\n")
        self.assertIn("run.jsonl changed since it", self.call(hook_event_name="PreCompact")["reason"])

    def test_sessions_are_isolated(self):
        self.observe(300000)
        self.call()
        other = self.root / "other.jsonl"
        other.write_text(json.dumps({"type": "assistant", "message": {"usage": {
            **dict.fromkeys(budget.FIELDS, 0), "input_tokens": 100}}}) + "\n")
        self.assertEqual(self.call(session_id="other", transcript_path=str(other)), {})

    def test_strict_launcher_refuses_before_any_external_execution(self):
        run = subprocess.run([str(MODULE.parent / "run"), "--strict"], capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("UNSUPPORTED", run.stderr)

    def test_malformed_usage_latches_stop_and_hook_returns_processable_json(self):
        self.transcript.write_text('{"type":\n')
        self.assertFalse(self.call()["continue"])
        self.observe(1)
        self.assertFalse(self.call()["continue"])
        adapter = MODULE.parents[1].parent / ".claude/hooks/context-budget.py"
        result = subprocess.run(["python3", str(adapter)], input="invalid", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["continue"])

    def test_workflow_child_transcript_is_found_without_its_path(self):
        # Workflow agents write under subagents/workflows/<run>/ and their events may name only the parent.
        self.observe(1000)
        self.call()
        child = self.root / "test-session/subagents/workflows/wf_run-1/agent-child2.jsonl"
        child.parent.mkdir(parents=True)
        usage = {**dict.fromkeys(budget.FIELDS, 0), "input_tokens": 100}
        child.write_text(json.dumps({"type": "assistant", "message": {"usage": usage}}) + "\n")
        self.assertEqual(self.call(agent_id="child2", hook_event_name="PreToolUse"), {})

    def test_child_uses_own_usage_and_cannot_stop_or_inherit_parent_budget(self):
        self.observe(250000)
        self.call()
        child = self.root / "test-session/subagents/agent-child1.jsonl"
        child.parent.mkdir(parents=True)
        usage = {**dict.fromkeys(budget.FIELDS, 0), "input_tokens": 100}
        child.write_text(json.dumps({"type": "assistant", "message": {"usage": usage}}) + "\n")
        event = {"agent_id": "child1", "agent_transcript_path": str(child)}
        self.assertEqual(self.call(**event), {})
        usage["input_tokens"] = 300000
        child.write_text(json.dumps({"type": "assistant", "message": {"usage": usage}}) + "\n")
        self.assertEqual(self.call(**event)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertFalse(self.call(agent_id="agent-child1", agent_transcript_path=str(child), hook_event_name="SubagentStop")["continue"])
        self.assertEqual(len(list((self.root / ".aeion/context").glob("*.json"))), 2)
        parent = json.loads((self.root / ".aeion/context/test-session.json").read_text())
        self.assertEqual(parent["state"], "HANDOVER_REQUIRED")

    def test_missing_child_transcript_refuses_child_without_stopping_parent(self):
        self.assertEqual(self.call(agent_id="missing-child")["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(self.call(), {})


if __name__ == "__main__":
    unittest.main()
