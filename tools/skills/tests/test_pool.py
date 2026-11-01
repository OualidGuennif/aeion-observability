"""Behavioral tests using tiny local source fixtures; no network or upstream execution."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("lifecycle_pool", Path(__file__).resolve().parents[1] / "pool.py")
pool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pool)
MIT = "MIT License\nPermission is hereby granted, free of charge\n"


class PoolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        lifecycle = self.workspace / "aeion-factory"
        lifecycle.mkdir()
        for name, value in (("WORKSPACE", self.workspace), ("ROOT", lifecycle), ("POOL", lifecycle / "skills")):
            replace = patch.object(pool, name, value)
            replace.start()
            self.addCleanup(replace.stop)
        pool.POOL.mkdir()
        (pool.POOL / "README.md").write_text("# Pool policy")
        self.lock = {}
        for name, (repository, folder, _, _) in pool.SOURCES.items():
            root = self.workspace / "third-party" / folder
            root.mkdir(parents=True)
            (root / "LICENSE").write_text(MIT)
            pin = {"repository": repository, "commit": "a" * 40, "tag": "v1", "selection": "release", "archive_sha256": "b" * 64}
            (root / ".aeion-upstream.json").write_text(json.dumps(pin))
            self.lock[name] = pin
        (self.workspace / "third-party/sources.lock.json").write_text(json.dumps(self.lock))
        self.skill = self.write("ecc", "skills/review/SKILL.md", '---\nname: review\ndescription: Code review for real failure evidence\n---\n# Review\n')
        self.agent = self.write("ecc", "agents/code-reviewer.md", '---\nname: code-reviewer\ndescription: Review code\nmodel: external-model\n---\n# Reviewer\nDo not execute !`touch executed`\n')

    def write(self, source, relative, text):
        path = self.workspace / "third-party" / pool.SOURCES[source][1] / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def test_canonical_inventory_excludes_translations_and_external_partners(self):
        self.write("ecc", "docs/fr/skills/mirror/SKILL.md", "# Translated duplicate")
        self.write("knowledge-work-plugins", "partner-built/skills/demo/SKILL.md", "# Third party")
        self.write("claude-plugins-official", "external_plugins/demo/skills/example/SKILL.md", "# External")
        self.assertEqual(len(pool.source_catalog()["entries"]), 2)

    def test_scanner_annotation_is_exact_source_bound_and_keeps_both_hashes(self):
        import hashlib
        source_hash = pool.digest(self.agent)
        registry = pool.ROOT / "tools/skills/annotations.json"
        registry.parent.mkdir(parents=True)
        annotation = {"file": self.agent.relative_to(self.workspace).as_posix(),
                      "source_sha256": source_hash, "needle": "Do not execute !`touch executed`",
                      "reason": "Reviewed fixture, never executed.", "rule": "example.rule"}
        registry.write_text(json.dumps([annotation]))
        data = pool.source_catalog()
        entry = next(e for e in data["entries"] if e["kind"] == "agent")
        info = entry["files"][self.agent.name]
        self.assertEqual(info["source_sha256"], source_hash)
        self.assertNotEqual(info["sha256"], source_hash)
        self.assertEqual(info["sha256"], hashlib.sha256(pool.materialized_bytes(self.agent)).hexdigest())
        self.agent.write_text(self.agent.read_text() + "\nchanged upstream")
        with self.assertRaisesRegex(ValueError, "changed upstream source"):
            pool.source_catalog()

    def test_refresh_copies_real_files_and_supporting_resources_deterministically(self):
        self.write("ecc", "skills/review/references/case.md", "# Real case")
        data = pool.source_catalog()
        pool.refresh(data)
        before = (pool.POOL / "catalog.json").read_bytes()
        pool.refresh(pool.source_catalog())
        self.assertEqual((pool.POOL / "catalog.json").read_bytes(), before)
        entry = next(e for e in data["entries"] if e["kind"] == "skill")
        self.assertEqual((pool.POOL / entry["link"] / "references/case.md").read_text(), "# Real case")
        self.assertFalse(any(path.is_symlink() for path in pool.POOL.rglob("*")))
        pool.verify(data)

    def test_plugin_specific_restriction_wins_over_root_license(self):
        self.write("claude-plugins-official", "plugins/restricted/LICENSE", "All rights reserved. Solely with Anthropic products.")
        self.write("claude-plugins-official", "plugins/restricted/skills/demo/SKILL.md", "# Restricted")
        data = pool.source_catalog()
        restricted = next(e for e in data["entries"] if e["source"] == "claude-plugins-official")
        self.assertFalse(restricted["portable_reference"])
        self.assertIsNone(restricted["link"])
        pool.refresh(data)
        self.assertFalse((pool.POOL / restricted["id"]).exists())

    def test_source_provenance_mismatch_stops_before_pool_change(self):
        pool.refresh(pool.source_catalog())
        before = (pool.POOL / "catalog.json").read_bytes()
        marker = self.skill.parents[2] / ".aeion-upstream.json"
        marker.write_text("{}")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            pool.source_catalog()
        self.assertEqual((pool.POOL / "catalog.json").read_bytes(), before)

    def test_escaping_source_alias_is_refused(self):
        outside = self.workspace / "outside.md"
        outside.write_text("# Not an allowed source")
        self.skill.unlink()
        self.skill.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "escaping"):
            pool.source_catalog()

    def test_refresh_does_not_overwrite_unmanaged_local_content(self):
        pool.refresh(pool.source_catalog())
        custom = pool.POOL / "owner-note.md"
        custom.write_text("Keep this")
        with self.assertRaisesRegex(ValueError, "Unmanaged"):
            pool.refresh(pool.source_catalog())
        self.assertEqual(custom.read_text(), "Keep this")

    def test_finder_metadata_does_not_block_refresh_or_get_deleted(self):
        pool.refresh(pool.source_catalog())
        metadata = pool.POOL / ".DS_Store"
        metadata.write_bytes(b"finder metadata")
        pool.refresh(pool.source_catalog())
        pool.verify(pool.source_catalog())
        self.assertEqual(metadata.read_bytes(), b"finder metadata")

    def test_agent_alias_and_metadata_search_do_not_execute_embedded_commands(self):
        pool.refresh(pool.source_catalog())
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            pool.search("review", 3, source="ecc", kind="agent")
        self.assertIn("code-reviewer", output.getvalue())
        self.assertNotIn("[skill;", output.getvalue())
        self.assertFalse((self.workspace / "executed").exists())
        self.assertFalse(Path("executed").exists())

    def test_published_pool_search_and_verification_need_no_third_party_folder(self):
        pool.refresh(pool.source_catalog())
        import shutil
        shutil.rmtree(self.workspace / "third-party")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            pool.search("review", 3, source="ecc", kind="agent")
        self.assertIn("code-reviewer", output.getvalue())
        pool.verify(json.loads((pool.POOL / "catalog.json").read_text()))

    def test_modified_materialized_file_is_preserved_and_blocks_refresh(self):
        data = pool.source_catalog()
        pool.refresh(data)
        entry = next(e for e in data["entries"] if e["kind"] == "skill")
        local = pool.POOL / entry["link"] / "SKILL.md"
        local.write_text("Owner edit")
        with self.assertRaisesRegex(ValueError, "Locally modified"):
            pool.refresh(pool.source_catalog())
        self.assertEqual(local.read_text(), "Owner edit")

    def test_edit_during_copy_is_preserved_and_refuses_replacement(self):
        data = pool.source_catalog()
        pool.refresh(data)
        entry = next(e for e in data["entries"] if e["kind"] == "skill")
        local = pool.POOL / entry["link"] / "SKILL.md"
        original_copy = pool.shutil.copyfile
        edited = False

        def edit_during_copy(source, destination):
            nonlocal edited
            if not edited:
                local.write_text("Concurrent owner edit")
                edited = True
            return original_copy(source, destination)

        with patch.object(pool.shutil, "copyfile", side_effect=edit_during_copy):
            with self.assertRaisesRegex(ValueError, "Locally modified"):
                pool.refresh(data)
        self.assertEqual(local.read_text(), "Concurrent owner edit")

    def test_interrupt_immediately_after_backup_rename_restores_pool(self):
        data = pool.source_catalog()
        pool.refresh(data)
        original_rename = Path.rename

        def interrupt_after_move(path, target):
            result = original_rename(path, target)
            if path == pool.POOL:
                raise KeyboardInterrupt()
            return result

        with patch.object(Path, "rename", interrupt_after_move):
            with self.assertRaises(KeyboardInterrupt):
                pool.refresh(data)
        pool.verify(data)

    def test_policy_edit_during_copy_is_preserved(self):
        data = pool.source_catalog()
        pool.refresh(data)
        original_copy = pool.shutil.copyfile

        def edit_policy(source, destination):
            (pool.POOL / "README.md").write_text("Owner's new policy")
            return original_copy(source, destination)

        with patch.object(pool.shutil, "copyfile", side_effect=edit_policy):
            with self.assertRaisesRegex(ValueError, "policy changed"):
                pool.refresh(data)
        self.assertEqual((pool.POOL / "README.md").read_text(), "Owner's new policy")

    def test_edit_to_new_active_pool_is_retained_when_validation_rolls_back(self):
        data = pool.source_catalog()
        pool.refresh(data)
        entry = next(e for e in data["entries"] if e["kind"] == "skill")
        relative = Path(entry["link"]) / "SKILL.md"
        original_rename = Path.rename

        def edit_after_install(path, target):
            result = original_rename(path, target)
            if path.parent.name.startswith("skill-build-") and Path(target) == pool.POOL:
                (pool.POOL / relative).write_text("Edit to newly active pool")
            return result

        with patch.object(Path, "rename", edit_after_install):
            with self.assertRaisesRegex(ValueError, "Locally modified"):
                pool.refresh(data)
        pool.verify(data)
        retained = list((pool.ROOT / ".aeion").glob("skill-pool-backup-*/failed-new"))
        self.assertEqual(len(retained), 1)
        self.assertEqual((retained[0] / relative).read_text(), "Edit to newly active pool")

    def test_agent_directory_symlink_is_refused(self):
        pool.refresh(pool.source_catalog())
        (pool.POOL / "agents").rename(pool.POOL.parent / "saved-agents")
        outside = self.workspace / "outside"
        outside.mkdir()
        (pool.POOL / "agents").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "[Ss]ymlink"):
            pool.refresh(pool.source_catalog())


if __name__ == "__main__":
    unittest.main()
