"""Behavioral tests for tools/skills/lint against tiny fixtures; no network, no model."""

import contextlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest


PATH = Path(__file__).resolve().parents[1] / "lint"
loader = importlib.machinery.SourceFileLoader("native_lint", str(PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
lint = importlib.util.module_from_spec(spec)
loader.exec_module(lint)
GOOD = "Formats a file. Use when a file needs formatting."


class LintTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.skills = Path(self.temporary.name) / "skills"
        self.skills.mkdir()

    def write_skill(self, folder, name=None, description=GOOD, body="# Body\n"):
        directory = self.skills / folder
        directory.mkdir(parents=True, exist_ok=True)
        head = f"---\nname: {name or folder}\ndescription: {description}\n---\n"
        (directory / "SKILL.md").write_text(head + body)

    def run_lint(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = lint.check(self.skills)
        return code, stream.getvalue().splitlines()

    def test_one_clean_skill_passes_and_reports_the_count(self):
        self.write_skill("format")
        self.write_skill("review", description="Reads a diff. Review before a push.")
        self.assertEqual(self.run_lint(), (0, ["PASS: 2 skills"]))

    def test_missing_description_fails(self):
        self.write_skill("format", description="")
        code, lines = self.run_lint()
        self.assertEqual(code, 1)
        self.assertEqual(lines, ["FAIL format: front matter lacks description"])

    def test_name_must_match_the_folder(self):
        self.write_skill("format", name="formatter")
        code, lines = self.run_lint()
        self.assertEqual(code, 1)
        self.assertEqual(lines, ["FAIL format: name 'formatter' differs from the folder name 'format'"])

    def test_description_must_say_when_to_use_it(self):
        self.write_skill("format", description="Formats a file and returns it.")
        code, lines = self.run_lint()
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("FAIL format: description does not say when to use it"))
        self.assertIn("when, whenever, before, after, monthly, weekly, periodic", lines[0])

    def test_description_cap_is_1024_characters(self):
        self.write_skill("format", description="Use when. " + "x" * 1025)
        code, lines = self.run_lint()
        self.assertEqual(code, 1)
        self.assertEqual(lines, [f"FAIL format: description is {len('Use when. ' + 'x' * 1025)} "
                                 f"characters, the cap is 1024"])

    def test_body_cap_is_150_lines(self):
        self.write_skill("format", body="\n".join(["# Body"] * 151) + "\n")
        code, lines = self.run_lint()
        self.assertEqual(code, 1)
        self.assertEqual(lines, ["FAIL format: body is 151 lines, the cap is 150"])

    def test_two_skills_cannot_declare_the_same_name(self):
        self.write_skill("format")
        self.write_skill("second", name="format")
        code, lines = self.run_lint()
        self.assertEqual(code, 1)
        # A duplicate name also breaks the folder rule; the duplicate is still named on its own.
        self.assertIn("FAIL second: name 'format' is already declared by format", lines)

    def test_missing_front_matter_fails(self):
        directory = self.skills / "format"
        directory.mkdir()
        (directory / "SKILL.md").write_text("# Format\n")
        code, lines = self.run_lint()
        self.assertEqual(code, 1)
        self.assertEqual(lines, ["FAIL format: no YAML front matter block"])

    def test_the_repository_skills_pass(self):
        code, lines = self.repository_lint()
        folders = [path for path in lint.SKILLS.iterdir() if (path / "SKILL.md").is_file()]
        self.assertEqual(code, 0, lines)
        self.assertEqual(lines, [f"PASS: {len(folders)} skills"])

    def repository_lint(self):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = lint.check()
        return code, stream.getvalue().splitlines()


if __name__ == "__main__":
    unittest.main()
