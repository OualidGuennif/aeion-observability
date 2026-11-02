#!/usr/bin/env python3
"""Exercise the connector drift check against real copies of the factory's own adapters."""
import contextlib
import importlib.machinery
import importlib.util
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
loader = importlib.machinery.SourceFileLoader('factory_adapter_check', str(ROOT / 'tools/agents/adapter-check'))
spec = importlib.util.spec_from_loader('factory_adapter_check', loader)
check = importlib.util.module_from_spec(spec)
loader.exec_module(check)


class AdapterCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name).resolve()
        for relative in check.VENDORED:
            source = ROOT / relative
            target = self.project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        shutil.copy2(ROOT / '.claude/settings.json', self.project / '.claude/settings.json')

    def run_check(self, *arguments):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['adapter-check', '--root', str(self.project), *arguments]):
            with contextlib.redirect_stdout(output):
                code = check.main()
        return code, output.getvalue()

    def test_a_full_copy_is_reported_as_matching(self):
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        self.assertIn(f'{len(check.VENDORED)} connectors: {len(check.VENDORED)} matching', output)
        self.assertIn('adapter-check: PASS', output)

    def test_a_linked_connector_fails_even_when_its_bytes_match(self):
        # Reading through a symlink would compare bytes the project does not own and call it a match.
        target = self.project / '.pi/extensions/factory/index.js'
        target.unlink()
        target.symlink_to(ROOT / '.pi/extensions/factory/index.js')
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn('LINKED    .pi/extensions/factory/index.js', output)
        self.assertIn('adapter-check: FAIL', output)

    def test_a_linked_parent_fails(self):
        folder = self.project / '.pi'
        outside = Path(tempfile.mkdtemp(prefix='linked-pi-')) / 'pi'
        self.addCleanup(shutil.rmtree, outside.parent, True)
        shutil.move(str(folder), str(outside))
        folder.symlink_to(outside, target_is_directory=True)
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn('LINKED    .pi/extensions/factory/index.js', output)
        self.assertIn('adapter-check: FAIL', output)

    def test_a_launcher_without_its_executable_bit_fails(self):
        launcher = self.project / 'tools/agents/run'
        launcher.chmod(0o644)
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn('MODE      tools/agents/run', output)
        self.assertIn('chmod +x', output)
        self.assertIn('adapter-check: FAIL', output)
        launcher.chmod(0o755)
        code, output = self.run_check()
        self.assertEqual(code, 0, output)

    def test_a_reference_mode_is_checked(self):
        factory = self.tagged_factory()
        (self.project / 'tools/agents/run').chmod(0o644)
        code, output = self.run_check('--ref', 'v1.0.0', '--repo', str(factory))
        self.assertEqual(code, 1, output)
        self.assertIn('MODE      tools/agents/run', output)

    def test_a_hand_edited_copy_fails_and_names_its_repair(self):
        edited = self.project / '.dsh/plugins/factory/index.js'
        edited.write_text(edited.read_text() + '\n// a local hand edit\n')
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn('DRIFT     .dsh/plugins/factory/index.js', output)
        self.assertIn(f'cp {ROOT / ".dsh/plugins/factory/index.js"} {edited}', output)
        self.assertIn('adapter-check: FAIL', output)

    def test_an_absent_connector_is_a_note_unless_strict(self):
        shutil.rmtree(self.project / '.pi')
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        self.assertIn('1 absent', output)
        self.assertNotIn('.pi/extensions/factory/index.js', output)
        strict, strict_output = self.run_check('--strict')
        self.assertEqual(strict, 1, strict_output)
        verbose, verbose_output = self.run_check('--verbose')
        self.assertIn('missing   .pi/extensions/factory/index.js', verbose_output)

    def test_a_config_that_names_a_deleted_script_fails(self):
        (self.project / '.claude/hooks/guard-bash.py').unlink()
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn('UNWIRED   .claude/settings.json → .claude/hooks/guard-bash.py', output)

    def test_invalid_json_fails_without_hiding_the_drift(self):
        (self.project / '.codex/hooks.json').write_text('{"hooks": ')
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn('invalid   .codex/hooks.json', output)
        self.assertIn('DRIFT     .codex/hooks.json', output)

    def test_a_missing_root_is_a_usage_error(self):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['adapter-check', '--root', str(self.project / 'absent')]):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                code = check.main()
        self.assertEqual(code, 2)

    def test_a_copy_that_compares_with_itself_is_refused(self):
        # A project that copied this script would compare its connectors with themselves and always pass.
        with patch.object(check, 'FACTORY', self.project):
            code, output = self.run_check()
        self.assertEqual(code, 2, output)
        with patch.object(check, 'FACTORY', self.project):
            code, output = self.run_check('--self')
        self.assertEqual(code, 0, output)

    def test_a_command_in_a_merged_config_is_checked(self):
        config = self.project / '.codex/config.toml'
        config.write_text((ROOT / '.codex/config.toml').read_text() + '\nnotify = ["python3", "tools/agents/removed-hook.py"]\n')
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn('UNWIRED   .codex/config.toml → tools/agents/removed-hook.py', output)

    def test_steer_without_id_is_unidentified(self):
        self.assertEqual(check.unidentified("  agent.steer({ content: [], source: { kind: 'x' } });\n"), [1])
        self.assertEqual(check.unidentified("  agent.steer({ id: randomUUID(), content: [] });\n"), [])

    def test_steer_without_role_is_unroled(self):
        self.assertEqual(check.unroled("  agent.steer({ id: randomUUID(), content: [] });\n"), [1])
        self.assertEqual(check.unroled("  agent.steer({ id: randomUUID(), role: 'user', content: [] });\n"), [])
        # inject and followup share the message shape, so their object literals owe a role too.
        self.assertEqual(check.unroled("  agent.inject({ id: randomUUID(), content: [] });\n"), [1])
        self.assertEqual(check.unroled("  agent.followup({ id: randomUUID(), content: [] });\n"), [1])
        self.assertEqual(check.unroled("  agent.inject({ id: randomUUID(), role: 'user' });\n"), [])

    def test_a_steering_copy_fails_the_check(self):
        # A steered message with no id is persisted as history dsh cannot reopen.
        target = self.project / '.dsh/plugins/factory/index.js'
        target.write_text(target.read_text().replace(
            "agent.steer({ id: globalThis.crypto.randomUUID(), role:",
            'agent.steer({ role:'))
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn('UNIDENTIFIED .dsh/plugins/factory/index.js — steer() without an id at line', output)
        self.assertIn('adapter-check: FAIL', output)

    def test_a_roled_steering_copy_fails_the_check(self):
        # A steered message without a role is persisted as history dsh cannot reopen either.
        target = self.project / '.dsh/plugins/factory/index.js'
        target.write_text(target.read_text().replace(
            "role: 'user', content:",
            'content:'))
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn('UNROLED .dsh/plugins/factory/index.js — steer()/inject()/followup() without a role at line', output)
        self.assertIn('adapter-check: FAIL', output)

    def tagged_factory(self):
        """A repository holding the connectors at v1.0.0, with a dirty working tree on top."""
        factory = Path(self.tmp.name) / 'factory'
        for relative in check.VENDORED:
            target = factory / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        shutil.copy2(ROOT / 'VERSION', factory / 'VERSION')

        def git(*arguments):
            subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com', *arguments],
                           cwd=factory, check=True, capture_output=True, text=True)

        git('init', '-q')
        git('add', '-A')
        git('commit', '-q', '-m', 'release')
        git('tag', 'v1.0.0')
        (factory / '.dsh/plugins/factory/index.js').write_text('a dirty working tree\n')
        return factory

    def test_a_reference_wins_over_a_dirty_working_tree(self):
        factory = self.tagged_factory()
        code, output = self.run_check('--ref', 'v1.0.0', '--repo', str(factory))
        self.assertEqual(code, 0, output)
        self.assertIn('reference v1.0.0', output)
        self.assertIn(f'{len(check.VENDORED)} connectors: {len(check.VENDORED)} matching', output)

    def test_a_copy_that_differs_from_the_reference_fails(self):
        factory = self.tagged_factory()
        (self.project / '.pi/extensions/factory/index.js').write_text('a hand edit\n')
        code, output = self.run_check('--ref', 'v1.0.0', '--repo', str(factory))
        self.assertEqual(code, 1, output)
        self.assertIn('DRIFT     .pi/extensions/factory/index.js', output)
        self.assertIn('git show v1.0.0:.pi/extensions/factory/index.js', output)

    def test_an_unknown_reference_is_refused(self):
        factory = self.tagged_factory()
        output_text = io.StringIO()
        with patch.object(sys, 'argv', ['adapter-check', '--root', str(self.project),
                                        '--ref', 'v9.9.9', '--repo', str(factory)]):
            with contextlib.redirect_stdout(output_text), contextlib.redirect_stderr(output_text):
                code = check.main()
        self.assertEqual(code, 2)
        self.assertIn('no such reference: v9.9.9', output_text.getvalue())

    def test_the_shipped_adapters_are_identified(self):
        for relative in check.VENDORED:
            if relative.endswith('.js'):
                text = (ROOT / relative).read_text(encoding='utf-8')
                self.assertEqual(check.unidentified(text), [], relative)
                self.assertEqual(check.unroled(text), [], relative)


if __name__ == '__main__':
    unittest.main()
