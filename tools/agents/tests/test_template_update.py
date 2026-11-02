#!/usr/bin/env python3
"""Exercise the template update against a throwaway factory and a project that adopted it."""
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
loader = importlib.machinery.SourceFileLoader('factory_template_update', str(ROOT / 'tools/agents/template-update'))
spec = importlib.util.spec_from_loader('factory_template_update', loader)
update_tool = importlib.util.module_from_spec(spec)
loader.exec_module(update_tool)

PLUGIN = '.dsh/plugins/factory/index.js'
LAUNCHER = 'tools/agents/run'


class TemplateUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.repo = self.base / 'factory'
        self.repo.mkdir()
        self.git('init', '-q', '-b', 'main')
        # A release carries the whole contract set; a thin fixture would test a factory that cannot exist.
        for relative in update_tool.CONTRACT:
            self.write_bytes(relative, (ROOT / relative).read_bytes())
        (self.repo / LAUNCHER).chmod(0o755)
        self.write('VERSION', '1.0.0\n')
        self.write('AGENTS.md', 'the factory instructions of 1.0.0\n')
        self.commit('v1')
        self.git('tag', 'v1.0.0')
        self.write('VERSION', '2.0.0\n')
        self.write(PLUGIN, 'export const version = 2;\n')
        self.write('AGENTS.md', 'the factory instructions of 2.0.0\n')
        self.commit('v2')
        self.git('tag', 'v2.0.0')

        self.project = self.base / 'app'
        self.project.mkdir()
        self.project_bytes('VERSION', b'1.0.0\n')
        for relative in update_tool.CONTRACT:
            self.project_bytes(relative, (ROOT / relative).read_bytes())
        # An adopted project has a runnable launcher already; mode repair is tested on its own.
        (self.project / LAUNCHER).chmod(0o755)
        self.project_file('AGENTS.md', 'the project owns this file\n')
        self.project_file('knowledge/note.md', 'project knowledge\n')

    def write(self, name, text):
        target = self.repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def write_bytes(self, name, data):
        target = self.repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def project_bytes(self, name, data):
        target = self.project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def project_file(self, name, text):
        target = self.project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def git(self, *arguments):
        subprocess.run(
            ['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com', *arguments],
            cwd=self.repo, check=True, capture_output=True, text=True,
        )

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', message)

    def run_tool(self, *arguments):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['template-update', '--root', str(self.project),
                                        '--repo', str(self.repo), *arguments]):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                code = update_tool.main()
        return code, output.getvalue()

    def test_writes_the_reference_and_keeps_the_project_text(self):
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)  # AGENTS.md needs a human merge
        self.assertEqual((self.project / PLUGIN).read_text(), 'export const version = 2;\n')
        # VERSION belongs to the application; the update must not rewrite it as factory provenance.
        self.assertEqual((self.project / 'VERSION').read_text().strip(), '1.0.0')
        self.assertEqual((self.project / 'AGENTS.md').read_text(), 'the project owns this file\n')
        self.assertEqual((self.project / 'knowledge/note.md').read_text(), 'project knowledge\n')
        self.assertIn('merge     AGENTS.md', output)

    def test_check_writes_nothing(self):
        before = (self.project / PLUGIN).read_text()
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0', '--check')
        self.assertEqual(code, 1, output)
        self.assertIn(f'DRIFT     {PLUGIN}', output)
        self.assertEqual((self.project / PLUGIN).read_text(), before)
        self.assertEqual((self.project / 'VERSION').read_text().strip(), '1.0.0')

    def test_a_branch_is_a_valid_reference(self):
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'main')
        self.assertEqual(code, 1, output)
        self.assertEqual((self.project / PLUGIN).read_text(), 'export const version = 2;\n')

    def test_the_application_version_is_never_written(self):
        # The public new-project flow starts an application at 0.1.0, which is not a factory release.
        self.project_file('VERSION', '0.7.0\n')
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        self.assertEqual((self.project / 'VERSION').read_text().strip(), '0.7.0')

    def test_a_merge_only_check_keeps_naming_the_merge(self):
        first, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(first, 1, output)
        self.assertIn('merge     AGENTS.md', output)
        # Repeating the same from/to pair must still name the unpaid merge, even with every connector matching.
        second, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0', '--check')
        self.assertEqual(second, 1, output)
        self.assertIn('merge     AGENTS.md', output)
        self.assertNotIn(f'DRIFT     {PLUGIN}', output)
        self.assertEqual((self.project / 'AGENTS.md').read_text(), 'the project owns this file\n')

    def test_it_requires_an_explicit_from_ref(self):
        with self.assertRaises(SystemExit) as stopped:
            self.run_tool('--ref', 'v2.0.0')
        self.assertEqual(stopped.exception.code, 2)

    def test_it_refuses_a_downgrade(self):
        code, output = self.run_tool('--from-ref', 'v2.0.0', '--ref', 'v1.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('refusing to downgrade 2.0.0 to 1.0.0', output)

    def test_a_downgrade_with_force_is_allowed(self):
        code, output = self.run_tool('--from-ref', 'v2.0.0', '--ref', 'v1.0.0', '--force')
        self.assertIn('merge     AGENTS.md', output)
        self.assertEqual(code, 1, output)

    def test_it_refuses_a_project_with_no_connector(self):
        for relative in update_tool.CONTRACT:
            (self.project / relative).unlink()
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('not an adopted project', output)

    def test_it_refuses_the_factory_itself(self):
        with patch.object(update_tool, 'FACTORY', self.project):
            code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('is the factory itself', output)

    def test_a_missing_launcher_is_written_executable(self):
        (self.project / LAUNCHER).unlink()
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        launcher = self.project / LAUNCHER
        self.assertTrue(launcher.is_file())
        self.assertTrue(launcher.stat().st_mode & 0o111, oct(launcher.stat().st_mode))
        # The repaired launcher must start, not raise permission denied before its own usage message.
        completed = subprocess.run([str(launcher)], capture_output=True, text=True)
        self.assertNotEqual(completed.returncode, 13)

    def test_a_launcher_that_lost_its_mode_is_repaired(self):
        launcher = self.project / LAUNCHER
        launcher.chmod(0o644)
        check, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0', '--check')
        self.assertEqual(check, 1, output)
        self.assertIn(f'MODE      {LAUNCHER}', output)
        self.assertEqual(launcher.stat().st_mode & 0o111, 0)  # --check is write-free
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        self.assertIn(f'mode      {LAUNCHER}', output)
        self.assertTrue(launcher.stat().st_mode & 0o111)

    def test_a_linked_connector_is_refused_before_any_write(self):
        late = update_tool.CONTRACT[-1]
        target = self.project / late
        target.unlink()
        outside = self.base / 'outside-owned-file.txt'
        outside.write_text('PROJECT OWNED SENTINEL\n')
        target.symlink_to(outside)
        plugin = self.project / PLUGIN
        plugin.write_text('local drift\n')
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('refusing linked connector destination', output)
        self.assertIn(late, output)
        self.assertTrue(target.is_symlink())
        self.assertEqual(outside.read_text(), 'PROJECT OWNED SENTINEL\n')
        # The earlier drifted connector was not written before the preflight refused the linked one.
        self.assertEqual(plugin.read_text(), 'local drift\n')

    def test_a_linked_parent_is_refused(self):
        hooks = self.project / '.claude/hooks'
        outside = self.base / 'linked-hooks'
        shutil.move(str(hooks), outside)
        hooks.symlink_to(outside, target_is_directory=True)
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('refusing linked connector destination .claude/hooks', output)
        self.assertTrue(hooks.is_symlink())


if __name__ == '__main__':
    unittest.main()
