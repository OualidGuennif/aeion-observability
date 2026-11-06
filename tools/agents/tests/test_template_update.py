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
HOOK = 'tools/git-hooks/pre-push'
HOOK_V1 = '#!/bin/sh\n# gate\nif mode != "local"; then check; fi\nexit 0\n'
README_V1 = '# Title\n\nintro\n\n## Middle\n\ntext\n\n## End\n\nfooter\n'


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
        # Factory files outside the contract: the three-way update owns them.
        self.write(HOOK, HOOK_V1)
        (self.repo / HOOK).chmod(0o755)
        self.write('README.md', README_V1)
        self.write('efficiency/old.md', 'retired guide\n')
        self.write('knowledge/policies/security.md', 'policy 1\n')
        self.write('CHANGELOG.md', '# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2026-01-01\n\n- First.\n')
        self.commit('v1')
        self.git('tag', 'v1.0.0')
        self.write('VERSION', '2.0.0\n')
        self.write(PLUGIN, 'export const version = 2;\n')
        self.write('AGENTS.md', 'the factory instructions of 2.0.0\n')
        self.write(HOOK, HOOK_V1.replace('mode != "local"', 'mode != "team"'))
        self.write('README.md', README_V1.replace('footer', 'footer of 2.0.0'))
        (self.repo / 'efficiency/old.md').unlink()
        self.write('efficiency/new.md', 'new guide\n')
        self.write('knowledge/policies/security.md', 'policy 2\n')
        self.write('CHANGELOG.md', '# Changelog\n\n## [Unreleased]\n\n## [2.0.0] - 2026-02-01\n\n'
                                   '- **Run git config aeion.mode team.**\n\n## [1.0.0] - 2026-01-01\n\n- First.\n')
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
        self.project_file(HOOK, HOOK_V1)
        (self.project / HOOK).chmod(0o755)
        self.project_file('README.md', README_V1)
        self.project_file('efficiency/old.md', 'retired guide\n')

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

    def project_git(self, *arguments):
        return subprocess.run(
            ['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com', *arguments],
            cwd=self.project, check=True, capture_output=True, text=True,
        ).stdout.strip()

    def commit_project(self):
        self.project_git('init', '-q', '-b', 'main')
        self.project_git('add', '-A')
        self.project_git('commit', '-q', '-m', 'adopt')

    def test_an_untouched_factory_file_takes_the_target(self):
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)  # AGENTS.md and the knowledge doc still need a human
        # The git hook is outside the contract; 2.0.0 projects must not keep the 1.x gate.
        self.assertIn('mode != "team"', (self.project / HOOK).read_text())
        self.assertTrue((self.project / HOOK).stat().st_mode & 0o111)
        self.assertIn(f'updated   {HOOK}', output)
        self.assertFalse((self.project / 'efficiency/old.md').exists())
        self.assertEqual((self.project / 'efficiency/new.md').read_text(), 'new guide\n')
        self.assertIn('footer of 2.0.0', (self.project / 'README.md').read_text())

    def test_a_project_edit_merges_with_the_target(self):
        self.project_file('README.md', README_V1.replace('intro', 'our own intro'))
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        readme = (self.project / 'README.md').read_text()
        self.assertIn('our own intro', readme)
        self.assertIn('footer of 2.0.0', readme)
        self.assertIn('merged    README.md', output)

    def test_a_conflicting_edit_is_kept_with_a_proposal(self):
        self.project_file('README.md', README_V1.replace('footer', 'our footer'))
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        self.assertIn('our footer', (self.project / 'README.md').read_text())
        self.assertNotIn('footer of 2.0.0', (self.project / 'README.md').read_text())
        self.assertIn('conflict  README.md', output)
        proposal = (self.project / '.aeion/template-update/v2.0.0/README.md').read_text()
        self.assertIn('<<<<<<< project', proposal)
        self.assertIn('footer of 2.0.0', proposal)
        # A project that does not ignore .aeion/ must not see proposals as files to commit.
        self.assertEqual((self.project / '.aeion/template-update/.gitignore').read_text(), '*\n')

    def test_a_linked_proposal_folder_is_refused(self):
        self.project_file('README.md', README_V1.replace('footer', 'our footer'))
        outside = self.base / 'shared-aeion'
        outside.mkdir()
        (self.project / '.aeion').symlink_to(outside, target_is_directory=True)
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('refusing linked destination .aeion', output)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual((self.project / HOOK).read_text(), HOOK_V1)

    def test_a_file_the_project_deleted_stays_deleted(self):
        (self.project / HOOK).unlink()
        (self.project / 'efficiency').joinpath('old.md').unlink()
        (self.project / 'efficiency').rmdir()
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        self.assertFalse((self.project / HOOK).exists())
        # A folder the project never kept does not come back through a new file.
        self.assertFalse((self.project / 'efficiency').exists())

    def test_knowledge_is_listed_never_written(self):
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        self.assertIn('review    knowledge/policies/security.md', output)
        self.assertFalse((self.project / 'knowledge/policies/security.md').exists())
        self.assertFalse((self.project / 'CHANGELOG.md').exists())

    def test_the_marker_is_written_then_used(self):
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        marker = (self.project / '.aeion-factory').read_text().split()
        self.assertEqual(marker[0], 'v2.0.0')
        self.assertEqual(len(marker[1]), 40)
        code, output = self.run_tool('--ref', 'v2.0.0', '--check')
        self.assertEqual(code, 0, output)
        self.assertIn('(v2.0.0, .aeion-factory)', output)
        self.assertIn('nothing to do', output)

    def test_a_new_project_marker_names_its_release(self):
        self.project_file('.aeion-factory', 'v1.0.0\n')
        code, output = self.run_tool('--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        self.assertIn('(v1.0.0, .aeion-factory)', output)
        self.assertIn('mode != "team"', (self.project / HOOK).read_text())

    def test_an_unknown_marker_is_refused(self):
        self.project_file('.aeion-factory', 'v9.9.9\n')
        code, output = self.run_tool('--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('git fetch --tags', output)

    def test_an_exact_inference_writes(self):
        code, output = self.run_tool('--ref', 'v2.0.0')
        self.assertEqual(code, 1, output)
        self.assertIn(f'v1.0.0, inferred:', output)
        self.assertIn(f'{len(update_tool.CONTRACT)}/{len(update_tool.CONTRACT)} connectors match', output)
        self.assertEqual((self.project / PLUGIN).read_text(), 'export const version = 2;\n')

    def test_a_partial_inference_only_checks(self):
        self.project_file(update_tool.CONTRACT[0], '# edited connector\n')
        code, output = self.run_tool('--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('confirm it with --from-ref v1.0.0', output)
        self.assertEqual((self.project / HOOK).read_text(), HOOK_V1)
        code, output = self.run_tool('--ref', 'v2.0.0', '--check')
        self.assertEqual(code, 1, output)
        self.assertIn('inferred:', output)

    def test_a_dirty_project_refuses_a_write(self):
        self.commit_project()
        self.project_file('README.md', 'work in progress\n')
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0')
        self.assertEqual(code, 2, output)
        self.assertIn('uncommitted changes', output)
        self.assertEqual((self.project / HOOK).read_text(), HOOK_V1)
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0', '--check')
        self.assertEqual(code, 1, output)

    def test_notes_major_and_the_mode_migration(self):
        self.commit_project()
        self.project_git('branch', 'develop')
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0', '--check')
        self.assertEqual(code, 1, output)
        self.assertIn('MAJOR 1.x → 2.x', output)
        self.assertIn('## [2.0.0] - 2026-02-01', output)
        self.assertIn('**Run git config aeion.mode team.**', output)
        self.assertNotIn('## [1.0.0]', output)
        self.assertIn('migrate   ', output)
        # The tool names the switch; the owner runs it.
        unset = subprocess.run(['git', 'config', '--local', '--get', 'aeion.mode'], cwd=self.project)
        self.assertEqual(unset.returncode, 1)
        self.project_git('config', 'aeion.mode', 'team')
        code, output = self.run_tool('--from-ref', 'v1.0.0', '--ref', 'v2.0.0', '--check')
        self.assertNotIn('migrate   ', output)

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

    def test_it_refuses_to_update_a_repository_from_itself(self):
        # A project's own copy of the tool reads releases from the project, which lacks the new one.
        self.commit_project()
        code, output = self.run_tool('--ref', 'v2.0.0', '--repo', str(self.project))
        self.assertEqual(code, 2, output)
        self.assertIn(f'from its own repository {self.project.resolve()}; run template-update from the Æion Factory clone', output)
        self.assertEqual((self.project / HOOK).read_text(), HOOK_V1)

    def test_a_project_copy_names_the_factory_clone_before_a_mistyped_root(self):
        # Run from inside a project, `--root <its name>` resolves to a folder inside the project.
        self.project_file('.aeion-factory', 'v1.0.0\n')
        self.commit_project()
        code, output = self.run_tool('--ref', 'v2.0.0', '--repo', str(self.project),
                                     '--root', str(self.project / 'project'))
        self.assertEqual(code, 2, output)
        self.assertIn('run template-update from the Æion Factory clone', output)
        self.assertIn('--root <project>', output)
        self.assertNotIn('no such project', output)
        self.assertEqual((self.project / HOOK).read_text(), HOOK_V1)

    def release_2_1(self):
        """2.1.0 changes the README's intro and leaves the hook as 2.0.0 had it."""
        self.write('VERSION', '2.1.0\n')
        self.write('README.md', README_V1.replace('intro', 'intro of 2.1.0').replace('footer', 'footer of 2.0.0'))
        self.commit('v2.1')
        self.git('tag', 'v2.1.0')

    def test_an_older_untouched_copy_takes_the_target(self):
        # The project still holds 1.0.0's README and hook, as one updated before 2.0.1 does.
        self.release_2_1()
        code, output = self.run_tool('--from-ref', 'v2.0.0', '--ref', 'v2.1.0')
        self.assertEqual(code, 0, output)
        readme = (self.project / 'README.md').read_text()
        # A three-way merge from 2.0.0 would have dropped 2.0.0's footer without a conflict.
        self.assertIn('intro of 2.1.0', readme)
        self.assertIn('footer of 2.0.0', readme)
        self.assertIn('updated   README.md — untouched since v1.0.0', output)
        # The factory left the hook alone since 2.0.0; the project's 1.0.0 copy still catches up.
        self.assertIn('mode != "team"', (self.project / HOOK).read_text())
        self.assertIn(f'updated   {HOOK} — untouched since v1.0.0', output)

    def test_an_edited_older_copy_is_never_caught_up(self):
        self.release_2_1()
        self.project_file(HOOK, HOOK_V1 + '# our own step\n')
        code, output = self.run_tool('--from-ref', 'v2.0.0', '--ref', 'v2.1.0')
        self.assertEqual(code, 0, output)
        self.assertEqual((self.project / HOOK).read_text(), HOOK_V1 + '# our own step\n')
        self.assertNotIn(HOOK, output)

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
