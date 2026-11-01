#!/usr/bin/env python3
"""Exercise the connector drift check against real copies of the factory's own adapters."""
import contextlib
import importlib.machinery
import importlib.util
import io
import shutil
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


if __name__ == '__main__':
    unittest.main()
