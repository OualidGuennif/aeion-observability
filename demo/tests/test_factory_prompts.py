"""Unit tests for Centralized Prompt Management (demo/factory/prompts.py)."""
import unittest
from unittest.mock import MagicMock, patch

from factory.prompts import LOCAL_PROMPTS, compile_prompt, get_prompt_text


class FactoryPromptsTests(unittest.TestCase):
    def test_local_prompts_baseline_coverage(self):
        """Ensure all factory core roles have pinned local prompts."""
        for role in ("factory.author.instructions", "factory.reviewer.instructions", "factory.preparer.instructions"):
            prompt = get_prompt_text(role)
            self.assertIsInstance(prompt, str)
            self.assertGreater(len(prompt), 50)
            self.assertIn(role, LOCAL_PROMPTS)

    def test_unknown_prompt_uses_fallback(self):
        """Unknown prompt names should return provided fallback or empty string."""
        self.assertEqual(get_prompt_text("nonexistent.prompt", fallback="custom fallback"), "custom fallback")
        self.assertEqual(get_prompt_text("nonexistent.prompt"), "")

    def test_compile_prompt_variable_substitution(self):
        """Placeholders in format {{variable}} must be substituted safely."""
        with patch.dict(LOCAL_PROMPTS, {"test.template": "Hello {{name}}, welcome to {{task}}!"}):
            compiled = compile_prompt("test.template", {"name": "Agent-007", "task": "Modernization"})
            self.assertEqual(compiled, "Hello Agent-007, welcome to Modernization!")

    def test_compile_prompt_none_or_missing_variables(self):
        """Missing or None variables should be handled cleanly."""
        with patch.dict(LOCAL_PROMPTS, {"test.template": "Target: {{target}}, Details: {{details}}."}):
            compiled = compile_prompt("test.template", {"target": "Docker"})
            self.assertEqual(compiled, "Target: Docker, Details: {{details}}.")
            compiled_with_none = compile_prompt("test.template", {"target": "Docker", "details": None})
            self.assertEqual(compiled_with_none, "Target: Docker, Details: .")

    def test_remote_langfuse_prompt_integration(self):
        """When Langfuse prompt is returned, remote text should be used."""
        mock_client = MagicMock()
        mock_remote = MagicMock()
        mock_remote.prompt = "Remote instructions from Langfuse prompt manager"
        mock_client.get_prompt.return_value = mock_remote

        with patch("factory.prompts.get_langfuse_client", return_value=mock_client):
            prompt = get_prompt_text("factory.author.instructions", label="staging")
            self.assertEqual(prompt, "Remote instructions from Langfuse prompt manager")
            mock_client.get_prompt.assert_called_once_with(
                name="factory.author.instructions", label="staging", fallback=LOCAL_PROMPTS["factory.author.instructions"]
            )

    def test_remote_langfuse_failure_fails_closed_to_local(self):
        """If Langfuse client throws or fails, local template must be returned."""
        mock_client = MagicMock()
        mock_client.get_prompt.side_effect = RuntimeError("Langfuse timeout")

        with patch("factory.prompts.get_langfuse_client", return_value=mock_client):
            prompt = get_prompt_text("factory.author.instructions")
            self.assertEqual(prompt, LOCAL_PROMPTS["factory.author.instructions"])


if __name__ == "__main__":
    unittest.main()
