#!/usr/bin/env python3
"""Exercise the template update against a throwaway factory and a project that adopted it."""
import contextlib
import importlib.machinery
import importlib.util
import io
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
        code, output = self.run_tool('--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)  # AGENTS.md needs a human merge
        self.assertEqual((self.project / PLUGIN).read_text(), 'export const version = 2;\n')
        self.assertEqual((self.project / 'VERSION').read_text().strip(), '2.0.0')
        self.assertEqual((self.project / 'AGENTS.md').read_text(), 'the project owns this file\n')
        self.assertEqual((self.project / 'knowledge/note.md').read_text(), 'project knowledge\n')
        self.assertIn('merge     AGENTS.md', output)

    def test_check_writes_nothing(self):
        before = (self.project / PLUGIN).read_text()
        code, output = self.run_tool('--ref', 'v2.0.0', '--check')
        self.assertEqual(code, 1, output)
        self.assertIn(f'DRIFT     {PLUGIN}', output)
        self.assertEqual((self.project / PLUGIN).read_text(), before)
        self.assertEqual((self.project / 'VERSION').read_text().strip(), '1.0.0')

    def test_a_branch_is_a_valid_reference(self):
        code, output = self.run_tool('--ref', 'main')
        self.assertEqual(code, 1, output)
        self.assertEqual((self.project / PLUGIN).read_text(), 'export const version = 2;\n')

    def test_it_refuses_a_downgrade(self):
        self.project_file('VERSION', '3.0.0\n')
        code, output = self.run_tool('--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('refusing to downgrade 3.0.0 to 2.0.0', output)

    def test_it_refuses_a_project_with_no_version(self):
        (self.project / 'VERSION').unlink()
        code, output = self.run_tool('--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('not an adopted project', output)

    def test_it_refuses_the_factory_itself(self):
        code, output = self.run_tool('--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        with patch.object(update_tool, 'FACTORY', self.project):
            code, output = self.run_tool('--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('is the factory itself', output)


if __name__ == '__main__':
    unittest.main()
