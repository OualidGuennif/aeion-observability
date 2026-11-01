"""Where a build agent stops: on its own branch, before review, before any GitHub write.

The factory runs three different jobs in three different processes, and the boundary between
them is what makes the review worth anything:

1. a **build agent** writes code on ``aeion/build-<attempt>`` and stops there;
2. **two review models** from other families read the frozen diff and vote;
3. the **publisher** pushes that exact branch and opens the pull request; a human merges.

An agent that could push, open a PR or review its own work would collapse all three into one
actor, and the two other models would be decoration. So the build brief below ends every task
with an explicit stop, and the coder agent in ``demo/flue/src/agents/coder.ts`` carries the same
rules verbatim (``test_factory_boundary.py`` proves the two copies still agree).

Stopping is enforced, not requested: the freeze digest pins the branch contents, the publisher
re-verifies that digest before it pushes, and any commit after the freeze invalidates the receipt.
"""
RULES = (
    "Work only inside your workspace and only inside the write scope named in the task.",
    "Commit to your own branch only: push nothing, open no pull request, merge nothing.",
    "Never review your own work. Two models from other families review it after you stop.",
    "Stop when the task's checks pass, or when you cannot continue; say why in HANDOVER.md.",
    "Do not wait for a reviewer, do not poll for one, and never merge on anyone's behalf.",
)

STOP = "Stop now and end your turn: no push, no pull request, no review, no merge."


def contract():
    """The five rules as one block, for a system prompt or a task brief."""
    return "\n".join(f"{number}. {rule}" for number, rule in enumerate(RULES, start=1))


def build_brief(feature_id, title, branch):
    """The closing block of every build task: what to build, where it stops, who owns the branch."""
    return "\n".join((
        f"Feature {feature_id}: {title}",
        f"Your branch is {branch}. It is yours to write; it is not yours to publish or review.",
        contract(),
        STOP,
    ))
