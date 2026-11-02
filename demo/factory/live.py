"""One real authoring call for a pinned feature, bounded before and after transport.

The model chooses bytes; it never chooses write scopes or the checker. Its JSON answer is
validated against the frozen scopes, size and path rules, then written for the isolated
protected check. The provider's reported usage is kept so settlement can use measured cost;
an unreported cost leaves the reservation open, never free.
"""
from pathlib import Path, PurePosixPath

from .models import author_model
from .model_client import complete_with_usage

MAX_FILES = 8
MAX_FILE_BYTES = 100_000
MAX_TOTAL_BYTES = 250_000
MAX_PROMPT_BRIEF = 12_000


class BuilderError(ValueError):
    """The builder answer cannot be trusted or written inside the frozen scopes."""


def build_prompt(feature, brief, frozen):
    brief_text = brief.read_text(encoding="utf-8")[:MAX_PROMPT_BRIEF]
    scopes = "\n".join("- " + scope for scope in frozen.write_scopes)
    return (
        "You implement exactly one feature in an existing Quarkus Java repository.\n"
        "Answer with one JSON object and no prose, using this schema:\n"
        '{"files":[{"path":"relative/path/inside/a/write/scope","content":"complete file text"}]}\n'
        "Rules: only the files needed; complete file contents; no Markdown fences; no build-file "
        "changes; do not write outside the scopes. The protected checker runs `gradle test` with "
        "its own contract test after you answer, so every test you add must pass. When asserting "
        "that a header is absent, use org.hamcrest.Matchers.nullValue() as the value matcher; "
        "do not match an absent header against an empty-string matcher. Every @QuarkusTest in "
        "this repository must also carry @WithTestResource(QuarkusTestDatabase.class) and import "
        "io.quarkus.test.common.WithTestResource.\n\n"
        f"Feature: {feature['id']} — {feature['title']}\n\n"
        f"Write scopes:\n{scopes}\n\n"
        f"Brief:\n{brief_text}\n"
    )


def parse_files(answer, scopes, repo=None):
    if not isinstance(answer, dict) or not isinstance(answer.get("files"), list):
        raise BuilderError("builder_answer_not_files")
    files = answer["files"]
    if not files or len(files) > MAX_FILES:
        raise BuilderError("builder_file_count")
    scopes = [str(scope) for scope in scopes]
    seen = set()
    total = 0
    accepted = {}
    for entry in files:
        if not isinstance(entry, dict):
            raise BuilderError("builder_file_entry")
        path, content = entry.get("path"), entry.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise BuilderError("builder_file_fields")
        if "\\" in path or path.startswith("/") or path.endswith("/"):
            raise BuilderError("builder_path_invalid")
        normalized = str(PurePosixPath(path))
        if normalized.startswith("../") or normalized == ".." or normalized.startswith("./"):
            raise BuilderError("builder_path_escape")
        prefix_ok = any(
            normalized == scope.rstrip("/")
            or normalized.startswith(scope if scope.endswith("/") else scope + "/")
            for scope in scopes)
        if not prefix_ok:
            raise BuilderError("builder_path_out_of_scope")
        if normalized in seen:
            raise BuilderError("builder_path_duplicate")
        size = len(content.encode("utf-8"))
        if size > MAX_FILE_BYTES:
            raise BuilderError("builder_file_too_large")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise BuilderError("builder_output_too_large")
        if repo is not None:
            root = Path(repo).resolve()
            target = (root / normalized).resolve()
            if root != target and root not in target.parents:
                raise BuilderError("builder_path_escape")
        seen.add(normalized)
        accepted[normalized] = content
    return accepted


class LiveBuilder:
    """A paid authoring call, injected with the client so tests never touch the network."""

    paid = True

    def __init__(self, model=None, client=None):
        self.model = model or author_model()
        self.client = client or complete_with_usage
        self.last_usage = None

    def __call__(self, repo, frozen, feature, brief):
        answer = self.client(self.model, build_prompt(feature, brief, frozen), max_tokens=6000)
        self.last_usage = answer.get("usage")
        files = parse_files(answer.get("answer"), frozen.write_scopes, repo=repo)
        root = Path(repo)
        for relative, content in files.items():
            target = root / relative
            resolved = target.resolve()
            if root.resolve() != resolved and root.resolve() not in resolved.parents:
                raise BuilderError("builder_path_escape")
            if target.is_symlink():
                raise BuilderError("builder_path_escape")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return sorted(files)
