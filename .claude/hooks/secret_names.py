# Spec: knowledge/policies/security.md
"""The one list of secret file names that the guards, checks and analyses never open."""
import fnmatch
import os
import re
from pathlib import Path

TEMPLATES = {".env.example", ".env.sample", ".env.template", ".env.dist", "env.example.local"}
NAMES = {"auth.json", "credentials", "credentials.json", ".credentials.json", ".git-credentials", "env.local",
         ".netrc", ".npmrc", ".pypirc", ".pgpass", ".envrc", ".dev.vars", ".htpasswd", "terraform.tfstate",
         "terraform.tfstate.backup"}
SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".ppk", ".jks", ".keystore", ".tfvars")
# Dotenv files (.env, .env.prod, .env-prod, prod.env) and private SSH keys, never their .pub halves.
PATTERN = re.compile(r"\.env([.-].+)?|.+\.env|id_(rsa|dsa|ecdsa|ed25519)(_sk)?")
# Code that reads the environment (process.env, import.meta.env) names no file.
CODE_ENV = re.compile(r".*(process|meta|this|self|ctx|context|deno|bun)\.env")
BRACES = re.compile(r"\{[^{}]*(,|\.\.)[^{}]*\}")
WALK_LIMIT = 10000


def is_secret(name):
    # Case folded: APFS and NTFS open .env.local for ENV.LOCAL.
    name = name.lower()
    if name in TEMPLATES or CODE_ENV.fullmatch(name):
        return False
    return bool(PATTERN.fullmatch(name)) or name in NAMES or name.endswith(SUFFIXES)


def secret_under(directory, follow=False, hidden=True, keep=None):
    """The first secret file name under directory, a link judged by its target too, "" when there is none,
    None when it is too large to check. follow walks linked folders, as grep -R does; hidden=False skips
    dot files and folders, as plain rg does; keep, when given, says which file names are read at all."""
    seen = 0
    for top, folders, files in os.walk(directory, followlinks=follow):
        folders[:] = [f for f in folders if f != ".git" and (hidden or not f.startswith("."))]
        files = [f for f in files if (hidden or not f.startswith(".")) and (keep is None or keep(f))]
        seen += len(folders) + len(files)
        if seen > WALK_LIMIT:
            return None
        for name in files:
            path = os.path.join(top, name)
            target = os.path.basename(os.path.realpath(path)) if os.path.islink(path) else name
            if is_secret(name) or is_secret(target):
                return target
    return ""


def inside_git(folder):
    """Whether folder lies in a git work tree, the only place rg honours .gitignore."""
    path = Path(folder).resolve()
    return any((p / ".git").exists() for p in (path, *path.parents))


def brace_variants(word):
    """The words bash brace expansion makes of word; a sequence ({a..z}) widens to a wildcard."""
    match = BRACES.search(word)
    if not match:
        return [word]
    inner = match.group(0)[1:-1]
    options = inner.split(",") if "," in inner else ["*"]
    variants = [v for option in options for v in brace_variants(word[:match.start()] + option + word[match.end():])]
    if len(variants) > 256:
        raise ValueError("too many brace variants to verify")
    return variants


EXAMPLES = sorted(NAMES | {".env", ".env.local", ".env-prod", "prod.env", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
                           "id_ed25519_sk", "key.pem", "server.key", "cert.p12", "cert.pfx", "putty.ppk",
                           "release.jks", "app.keystore", "prod.tfvars"})
# Ordinary files that a generic glob (*, *.json, c*, *_*, .*) also matches; none shares a secret's stem.
ORDINARY = ("README.md", "main.py", "test_main.py", "package.json", "config.yml", "index.js", "app.tsx",
            "data", "docs", "go.sum", "Makefile", "notes.txt", "eslint.config.js", "setup.py",
            "kustomization.yaml", "build.gradle.kts")
DOT_ORDINARY = (".git", ".github", ".gitignore", ".editorconfig", ".vscode", ".claude")


def shell_pattern(pattern):
    """The glob as Python's fnmatch and glob read it: bash, zsh and ripgrep take [^x] for [!x], and a
    bracket with a POSIX class ([[:lower:]]) widens to one wildcard, since fnmatch reads it literally."""
    pattern = re.sub(r"\[[^\[\]]*(\[:\w+:\][^\[\]]*)+\]", "?", pattern)
    return pattern.replace("[^", "[!")


def named_secrets(pattern):
    """The secrets a glob's last part names wherever it expands: a dotfile glob with a literal first
    letter (.e*) by its name; any other glob when it matches a secret and no ordinary name, so *.json
    and .* stay allowed and id_*, .*rc and *env do not. Case folded, as is_secret is."""
    pattern = shell_pattern(pattern).lower()
    if pattern.startswith(".."):
        return set()
    dotted = pattern.startswith(".")
    # A leading wildcard (*env, [.]env) matches dotfiles in Grep, rg and fnmatch, though not in the shell.
    wild = pattern[:1] in ("*", "?", "[")
    secrets = {n for n in EXAMPLES if (wild or n.startswith(".") == dotted) and fnmatch.fnmatchcase(n, pattern)}
    ordinary = DOT_ORDINARY if dotted else ORDINARY + DOT_ORDINARY if wild else ORDINARY
    # A literal or a positive class after the dot names its letter (.e*, .[e]nv); a negated class (.[!.]*) does not.
    if re.match(r"\.([^*?.\[]|\[(?![!^]))", pattern) or not any(fnmatch.fnmatchcase(n.lower(), pattern) for n in ordinary):
        return secrets
    return set()
