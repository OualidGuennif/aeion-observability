"""The author gets complete pinned public source, never host files or truncated context."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.target import TargetError, load_target
from test_factory_execution import write_profile

SOURCE = 'demo/forum-app/src/main/java/local/aeion/forum/ForumHealth.java'


class SourceContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.sha = write_profile(self.root)
        self.path = self.root / 'demo/forum/targets/forum-app-013.json'
        self.profile = json.loads(self.path.read_text())

    def target(self, paths):
        self.profile['context_files'] = paths
        self.path.write_text(json.dumps(self.profile))
        return load_target(self.path, self.root)

    def commit(self):
        for args in (['add', '-A'], ['commit', '-qm', 'context fixture']):
            subprocess.run(['git', '-C', str(self.source), *args], check=True,
                           capture_output=True)
        self.profile['base']['sha'] = subprocess.check_output(
            ['git', '-C', str(self.source), 'rev-parse', 'HEAD'], text=True).strip()

    def test_only_the_pinned_blob_is_sent_not_a_dirty_working_tree(self):
        original = (self.source / SOURCE).read_text()
        (self.source / SOURCE).write_text('HOST_ONLY_CANARY')
        context = self.target([SOURCE]).source_context()
        self.assertIn(SOURCE, context)
        self.assertIn(original, context)
        self.assertNotIn('HOST_ONLY_CANARY', context)

    def test_legacy_profiles_keep_an_empty_optional_context(self):
        self.assertEqual(load_target(self.path, self.root).source_context(), '')

    def test_paths_outside_public_main_java_are_refused(self):
        for path in ('.env', '../secret.java', SOURCE + '/../secret.java',
                     'demo/forum-app/src/main/resources/application.properties',
                     'demo/forum-app/src/test/java/Fake.java'):
            with self.subTest(path=path), self.assertRaises(TargetError):
                self.target([path])

    def test_duplicates_bad_types_missing_blobs_and_symlinks_are_refused(self):
        for paths in ([SOURCE, SOURCE], SOURCE, [1], [SOURCE.replace('ForumHealth', 'Missing')]):
            with self.subTest(paths=paths), self.assertRaises(TargetError):
                self.target(paths)
        (self.source / SOURCE).unlink()
        (self.source / SOURCE).symlink_to('/private/tmp/never-read-a-host-file')
        self.commit()
        with self.assertRaises(TargetError):
            self.target([SOURCE])

    def test_oversized_public_source_is_refused_at_profile_loading(self):
        (self.source / SOURCE).write_text('é' * 12001)
        self.commit()
        with self.assertRaisesRegex(TargetError, 'context'):
            self.target([SOURCE])

    def test_the_total_labeled_context_is_bounded(self):
        paths = []
        for index in range(3):
            path = SOURCE.replace('ForumHealth', 'Context' + str(index))
            (self.source / path).write_text('x' * 17000)
            paths.append(path)
        self.commit()
        with self.assertRaisesRegex(TargetError, 'context_too_large'):
            self.target(paths)

    def test_more_than_eight_context_files_are_refused(self):
        with self.assertRaisesRegex(TargetError, 'context'):
            self.target([SOURCE.replace('ForumHealth', 'Context' + str(i)) for i in range(9)])

    def test_an_oversized_brief_is_refused_before_target_advertisement(self):
        (self.root / 'brief.md').write_text('é' * 6001)
        with self.assertRaisesRegex(TargetError, 'brief_too_large'):
            load_target(self.path, self.root)



if __name__ == '__main__':
    unittest.main()
