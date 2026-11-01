#!/usr/bin/env python3
"""Exercise the tag-pinned desktop install against a throwaway repository."""
import contextlib
import importlib.machinery
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
loader = importlib.machinery.SourceFileLoader('factory_dsh_install', str(ROOT / 'tools/agents/dsh-install'))
spec = importlib.util.spec_from_loader('factory_dsh_install', loader)
install_tool = importlib.util.module_from_spec(spec)
loader.exec_module(install_tool)

PLUGIN = '.dsh/plugins/factory'


class DshInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.write('index.js', 'export const name = "aeion-factory";\n')
        self.write('compaction.js', 'export const name = "aeion-factory-compaction";\n')
        self.commit('v1')
        self.git('tag', 'v1.0.0')
        self.write('index.js', 'export const name = "aeion-factory";\nexport const version = 2;\n')
        self.commit('v2')
        self.git('tag', 'v2.0.0')
        self.profiles = self.base / 'profiles'
        self.profile = self.profiles / 'desktop'
        self.profile.mkdir(parents=True)
        self.entry = self.profile / 'aeion-factory'

    def write(self, name, text):
        target = self.repo / PLUGIN / name
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
        with patch.object(sys, 'argv', ['dsh-install', '--repo', str(self.repo),
                                        '--profile-dir', str(self.profiles), *arguments]):
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                code = install_tool.main()
        return code, output.getvalue()

    def target_of(self):
        return os.readlink(self.entry)

    def test_installs_the_tag_bytes(self):
        code, output = self.run_tool('--tag', 'v1.0.0')
        self.assertEqual(code, 0, output)
        self.assertEqual(self.target_of(), 'vendor/aeion-factory-v1.0.0')
        copy = self.profile / 'vendor/aeion-factory-v1.0.0'
        for name in ('index.js', 'compaction.js'):
            expected = subprocess.run(
                ['git', 'show', f'v1.0.0:{PLUGIN}/{name}'],
                cwd=self.repo, capture_output=True, check=True,
            ).stdout
            self.assertEqual((copy / name).read_bytes(), expected)
        self.assertNotIn('version = 2', (copy / 'index.js').read_text())

    def test_a_second_tag_repoints_the_link(self):
        self.assertEqual(self.run_tool('--tag', 'v1.0.0')[0], 0)
        self.assertEqual(self.run_tool('--tag', 'v2.0.0')[0], 0)
        self.assertEqual(self.target_of(), 'vendor/aeion-factory-v2.0.0')
        self.assertTrue((self.profile / 'vendor/aeion-factory-v1.0.0/index.js').is_file())

    def test_a_failed_copy_keeps_the_old_link(self):
        self.assertEqual(self.run_tool('--tag', 'v1.0.0')[0], 0)
        original = install_tool.ref_bytes

        def failing(repository, tag, relative):
            if relative.endswith('compaction.js'):
                raise RuntimeError('object store unavailable')
            return original(repository, tag, relative)

        with patch.object(install_tool, 'ref_bytes', failing):
            code, output = self.run_tool('--tag', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertEqual(self.target_of(), 'vendor/aeion-factory-v1.0.0')
        self.assertFalse((self.profile / 'vendor/aeion-factory-v2.0.0').exists())

    def test_unknown_tag_refuses(self):
        code, output = self.run_tool('--tag', 'v9.9.9')
        self.assertEqual(code, 2, output)
        self.assertIn('no such tag: v9.9.9', output)
        self.assertFalse(self.entry.exists())
        self.assertFalse((self.profile / 'vendor').exists())

    def test_unmanaged_entry_refuses(self):
        self.entry.mkdir()
        (self.entry / 'index.js').write_text('unmanaged\n')
        code, output = self.run_tool('--tag', 'v1.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('is not a link', output)
        self.assertEqual((self.entry / 'index.js').read_text(), 'unmanaged\n')

    def test_force_refuses_a_second_displacement(self):
        self.entry.mkdir()
        (self.entry / 'index.js').write_text('unmanaged\n')
        self.assertEqual(self.run_tool('--tag', 'v1.0.0', '--force')[0], 0)
        self.assertEqual(self.target_of(), 'vendor/aeion-factory-v1.0.0')
        self.assertTrue((self.profile / 'aeion-factory.replaced/index.js').is_file())
        # A second hand-made entry cannot displace the copy the first one left behind.
        self.entry.unlink()
        self.entry.mkdir()
        code, output = self.run_tool('--tag', 'v1.0.0', '--force')
        self.assertEqual(code, 2, output)
        self.assertIn('aeion-factory.replaced', output)

    def test_reinstalling_a_tag_replaces_its_copy(self):
        self.assertEqual(self.run_tool('--tag', 'v1.0.0')[0], 0)
        copy = self.profile / 'vendor/aeion-factory-v1.0.0/index.js'
        copy.write_text('a hand edit that must not survive\n')
        self.assertEqual(self.run_tool('--tag', 'v1.0.0')[0], 0)
        self.assertNotIn('hand edit', copy.read_text())
        self.assertEqual(self.target_of(), 'vendor/aeion-factory-v1.0.0')

    def test_check_names_a_hand_edited_copy(self):
        self.assertEqual(self.run_tool('--tag', 'v1.0.0')[0], 0)
        edited = self.profile / 'vendor/aeion-factory-v1.0.0/index.js'
        edited.write_text(edited.read_text() + '// local edit\n')
        code, output = self.run_tool('--check')
        self.assertEqual(code, 1, output)
        self.assertIn('DRIFT', output)
        self.assertIn('index.js', output)

    def test_check_passes_a_clean_install(self):
        self.assertEqual(self.run_tool('--tag', 'v1.0.0')[0], 0)
        code, output = self.run_tool('--check')
        self.assertEqual(code, 0, output)
        self.assertIn('ok v1.0.0', output)

    def test_check_refuses_a_foreign_link(self):
        os.symlink(self.repo / PLUGIN, self.entry)
        code, output = self.run_tool('--check')
        self.assertEqual(code, 2, output)
        self.assertIn('does not name a vendored tag', output)


if __name__ == '__main__':
    unittest.main()
