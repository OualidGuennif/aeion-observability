"""Credential capabilities: one GitHub key per capability, never one key for everything.

The AI writes the code, so the AI must not hold the key that merges it. Each credential carries
exactly one role, and a process is allowed to hold exactly the roles it needs:

| Credential | Role | Capabilities | Who may hold it |
| --- | --- | --- | --- |
| ``GH_BUILD_KEY`` | build | ``contents:read`` | trusted source synchronizer, never model workers |
| ``GH_API_KEY`` | publish | ``contents:write``, ``pull_requests:write`` | one short-lived publisher process |
| ``GH_RELEASE_KEY`` | release | ``contents:write``, ``pull_requests:write``, ``administration:read`` | isolated deterministic release process |
| ``OPENCODE_API_KEY`` | inference | inference only | the supervisor, the relay, the review circuit |

``GH_TOKEN`` and ``GITHUB_TOKEN`` are ambient aliases of the publish role: they are scrubbed like
it, because a CI runner or a shell may inject one without the factory asking.

The application scrubs every publish-class credential from its own environment at start-up, so a
worker, an agent, or anything it spawns cannot read or inherit it. The publisher reloads its key
from the owner's private file for the duration of one operation, and nothing else. Branch protection
independently requires exact-head CI. PAT scopes alone cannot distinguish publication from merging;
the process boundary enforces those roles, not a claim about stolen-token immunity.
"""
import os

ROLES = ("build", "publish", "release", "inference")

# name -> (role, GitHub permissions the key must be restricted to)
CREDENTIALS = {
    "GH_BUILD_KEY": ("build", ("contents:read",)),
    "GH_API_KEY": ("publish", ("contents:write", "pull_requests:write")),
    "GH_RELEASE_KEY": ("release", ("contents:write", "pull_requests:write", "administration:read")),
    "OPENCODE_API_KEY": ("inference", ()),
}

# Ambient GitHub tokens that behave like the publish key: same role, same scrub.
ALIASES = {"GH_TOKEN": "publish", "GITHUB_TOKEN": "publish"}

PUBLISH_CREDENTIALS = ("GH_API_KEY", "GH_RELEASE_KEY", "GH_TOKEN", "GITHUB_TOKEN")
INFERENCE_CREDENTIALS = ("OPENCODE_API_KEY",)
CAPABILITIES = {"GH_API_KEY": {"publish"}, "OPENCODE_API_KEY": {"inference"},
                "GH_BUILD_KEY": {"build"}, "GH_RELEASE_KEY": {"release"},
                "GH_TOKEN": {"publish"}, "GITHUB_TOKEN": {"publish"}}


class CredentialError(ValueError):
    """A component that holds a credential it must not hold, or lacks the one it needs."""


def role_of(name):
    """The role a credential name belongs to, or ``None`` for an unknown name."""
    if name in CREDENTIALS:
        return CREDENTIALS[name][0]
    return ALIASES.get(name)


def scopes(name):
    """The GitHub permissions the key must be restricted to; empty for a non-GitHub key."""
    return CREDENTIALS.get(name, (None, ()))[1]


def names_for(role):
    return [name for name, (owner, _) in CREDENTIALS.items() if owner == role]


def present(environ=None):
    """Report which known credentials the environment holds — names only, never values."""
    environ = environ if environ is not None else os.environ
    found = {role: [] for role in ROLES}
    for name in list(CREDENTIALS) + list(ALIASES):
        if environ.get(name):
            found[role_of(name)].append(name)
    return found


def held_roles(environ=None):
    """The roles this environment can act as, sorted for a stable error message."""
    return sorted(role for role, held in present(environ).items() if held)


def for_role(role, environ=None):
    """The credential this process must use for ``role``; fail closed when it is absent."""
    environ = environ if environ is not None else os.environ
    for name in names_for(role):
        if environ.get(name):
            return name, environ[name]
    raise CredentialError(f"credential_missing:{role}")


def assert_only(roles, environ=None):
    """Fail closed when the environment holds a role outside ``roles``.

    ``roles`` is the set of roles this process is allowed to act as; inference and build may
    coexist, publish and release never do, and neither may sit next to inference.
    """
    allowed = {roles} if isinstance(roles, str) else set(roles)
    extra = [role for role in held_roles(environ) if role not in allowed]
    if extra:
        raise CredentialError("credential_role_conflict:" + ",".join(extra))
    return True


def scrub_publish_credentials(environ=None):
    """Remove every publish-class credential from this process and from everything it spawns."""
    environ = environ if environ is not None else os.environ
    removed = []
    for name in PUBLISH_CREDENTIALS:
        if environ.pop(name, None) is not None:
            removed.append(name)
    return removed


def assert_worker_isolated(environ=None):
    """Fail closed when a code-writing component can see a publish or release credential."""
    held = present(environ)
    forbidden = held["publish"] + held["release"]
    if forbidden:
        raise CredentialError("worker_holds_publish_credential:" + ",".join(forbidden))
    return True


def capabilities(name):
    return set(CAPABILITIES.get(name, set()))


def describe():
    """The credential table as data, so the `.env.example` and the docs cannot drift."""
    rows = []
    for name, (role, permissions) in CREDENTIALS.items():
        rows.append({"name": name, "role": role, "permissions": list(permissions)})
    return rows
