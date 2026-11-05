"""Validate untrusted exported files before writing a product snapshot.

Spec: knowledge/components/factory-flue.md
"""
from pathlib import Path, PurePosixPath
import re

MAX_FILES = 32
MAX_FILE_BYTES = 100_000
MAX_TOTAL_BYTES = 250_000
GIT_CONTROL_NAMES = {'.git', '.gitignore', '.gitattributes', '.gitmodules'}
GRADER_PATTERNS = re.compile(
    r'\b(?:'
    r'org\.junit\.jupiter\.api\.extension|'
    r'org\.junit\.platform|'
    r'InvocationInterceptor|'
    r'TestExecutionExceptionHandler|'
    r'LifecycleMethodExecutionExceptionHandler|'
    r'ExecutionCondition|'
    r'TestInstancePostProcessor|'
    r'TestInstancePreDestroyCallback|'
    r'BeforeAllCallback|AfterAllCallback|BeforeEachCallback|AfterEachCallback|'
    r'BeforeTestExecutionCallback|AfterTestExecutionCallback|'
    r'ParameterResolver|TestWatcher|'
    r'LauncherSessionListener|TestExecutionListener|LauncherInterceptor|'
    r'junit\.jupiter\.extensions|junit\.platform|'
    r'Assumptions\b|org\.junit\.jupiter\.api\.Assumptions|'
    r'RestAssured\s*\.\s*(?:filters|requestSpecification|responseSpecification|baseURI|port)'
    r')\b'
)
FOREIGN_PACKAGE = re.compile(r'(?m)^\s*package\s+(?!local\.aeion\.forum\s*;)[^\r\n;]+;')


class BuilderError(ValueError):
    """Untrusted files cannot enter the frozen candidate snapshot."""


def grader_tampered(path, content):
    parts = [part.lower() for part in PurePosixPath(path).parts]
    if 'meta-inf' in parts or (parts and parts[-1] == 'junit-platform.properties'):
        return True
    if path.endswith(('.java', '.properties')) and GRADER_PATTERNS.search(content):
        return True
    if path.endswith('.java') and 'local/aeion/forum/' in path and FOREIGN_PACKAGE.search(content):
        return True
    return False


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
        # A textual prefix is not containment: `src/.../forum/../../../../../../.git/...`
        # starts inside a scope and resolves to the repository's own hooks, which `git diff`
        # and `git ls-files` never show. Scopes name directories, so no component may be a
        # relative step and no component may name the Git control directory.
        parts = path.split("/")
        if any(part in (".", "..") for part in parts):
            raise BuilderError("builder_path_escape")
        if any(part.lower() in GIT_CONTROL_NAMES for part in parts):
            raise BuilderError("builder_path_forbidden")
        normalized = str(PurePosixPath(path))
        if normalized.startswith("../") or normalized == ".." or normalized.startswith("./"):
            raise BuilderError("builder_path_escape")
        matched = None
        for scope in scopes:
            if (normalized == scope.rstrip("/")
                    or normalized.startswith(scope if scope.endswith("/") else scope + "/")):
                matched = scope
                break
        if matched is None:
            raise BuilderError("builder_path_out_of_scope")
        if normalized in seen:
            raise BuilderError("builder_path_duplicate")
        size = len(content.encode("utf-8"))
        if size > MAX_FILE_BYTES:
            raise BuilderError("builder_file_too_large")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise BuilderError("builder_output_too_large")
        if grader_tampered(normalized, content):
            raise BuilderError("builder_grader_tampered")
        if repo is not None:
            root = Path(repo).resolve()
            target = (root / normalized).resolve()
            if root != target and root not in target.parents:
                raise BuilderError("builder_path_escape")
            # The resolved path must stay in the scope that matched textually, so a symlinked
            # parent cannot redirect the write into `.git` or another unreviewed directory.
            scope_root = (root / matched).resolve()
            if target != scope_root and scope_root not in target.parents:
                raise BuilderError("builder_path_escape")
        seen.add(normalized)
        accepted[normalized] = content
    return accepted
