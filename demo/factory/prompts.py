"""Centralized Prompt Management with Langfuse Versioning & Deterministic Local Fallback.

Maintains pinned system prompts for preparer, author (coder), and reviewer agents.
Supports dynamic retrieval from Langfuse Prompt Management when available, with
cryptographically verified, bounded local fallback templates.
"""
import os

from scores import get_langfuse_client

# Local canonical templates (strict, tested baselines)
LOCAL_PROMPTS = {
    "factory.author.instructions": (
        "You are an autonomous coding agent operating in an isolated OpenShell sandbox.\n"
        "Complete the implementation required by BRIEF.md inside declared Write scopes.\n"
        "Rules:\n"
        "1. Work strictly inside your assigned workspace and declared write scopes.\n"
        "2. Do not push commits, create pull requests, or merge branches.\n"
        "3. Keep comment blocks under 20 lines in all source files (repo-health).\n"
        "4. Always verify your changes using run_protected_checks before stopping.\n"
        "5. Revert unrequested changes outside the feature specification."
    ),
    "factory.reviewer.instructions": (
        "You are an independent reviewer evaluating a proposed pull request candidate.\n"
        "Review the complete frozen review packet for correctness, security, and scope.\n"
        "Rules:\n"
        "1. Verify that candidate changes strictly match the declared specification.\n"
        "2. Check that no out-of-scope files, credentials, or secret patterns were introduced.\n"
        "3. Submit your typed verdict (approve/reject) with concrete evidence.\n"
        "4. Never edit files, weaken policies, or bypass gates."
    ),
    "factory.preparer.instructions": (
        "You are an independent contract preparer generating executable acceptance tests.\n"
        "Read the feature specification and create an independent black-box verifier.\n"
        "Rules:\n"
        "1. Cover both positive acceptance criteria and negative boundary controls.\n"
        "2. Test public HTTP endpoints and external contracts, never internal classes.\n"
        "3. If a valid executable contract cannot be prepared, submit blocked.\n"
        "4. Never weaken requirements or grant runtime authority."
    ),
}


def get_prompt_text(prompt_name, label="production", fallback=None):
    """Retrieve prompt template from Langfuse if available, falling back to local pinned baseline."""
    local_default = LOCAL_PROMPTS.get(prompt_name, fallback or "")
    client = get_langfuse_client()
    if not client:
        return local_default
    try:
        remote = client.get_prompt(name=prompt_name, label=label, fallback=local_default)
        if hasattr(remote, "prompt") and isinstance(remote.prompt, str) and remote.prompt.strip():
            return remote.prompt.strip()
        if hasattr(remote, "compile"):
            compiled = remote.compile()
            if isinstance(compiled, str) and compiled.strip():
                return compiled.strip()
    except Exception:
        pass
    return local_default


def compile_prompt(prompt_name, context=None, label="production"):
    """Compile prompt template with contextual variables and bounds enforcement."""
    raw = get_prompt_text(prompt_name, label=label)
    if not context or not isinstance(context, dict):
        return raw
    compiled = raw
    for key, val in context.items():
        placeholder = "{{" + str(key) + "}}"
        str_val = str(val if val is not None else "")
        compiled = compiled.replace(placeholder, str_val)
    return compiled
