"""Real GitHub forge behind the publisher policy.

The token is read from ``GH_API_KEY`` at call time and never printed, logged or stored.
Every write is idempotent against a deterministic branch name derived from the attempt
id, so an uncertain result is reconciled by looking the pull request up, never by
re-publishing. ``dry_run`` defaults to true: no remote object is created until the
operator explicitly disables it, and merging is a separate explicit flag.
"""
import json
import os
import ssl
import urllib.error
import urllib.request

API = "https://api.github.com"
MAX_FILE_BYTES = 512 * 1024


class GitHubError(ValueError):
    """A GitHub operation that cannot be trusted or completed."""


def tls_context():
    """The demo venv ships no OS trust store; prefer certifi when it is installed."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except (ImportError, OSError):
        return ssl.create_default_context()


def branch_name(attempt_id):
    return f"aeion/build-{attempt_id[:24]}"


def _urllib_transport(method, url, payload, headers, timeout=30):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    for key, value in headers.items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=tls_context()) as response:
            body = response.read().decode("utf-8")
            return response.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except ValueError:
            parsed = {"message": body[:200]}
        return exc.code, parsed


class GitHubForge:
    """Forge adapter with the same ``publish``/``reconcile`` contract as ``FakeForge``."""

    def __init__(self, repo, token=None, transport=None, base_branch="main",
                 dry_run=True, allow_merge=False):
        self.repo = repo
        self.token = token if token is not None else os.environ.get("GH_API_KEY")
        self.transport = transport or _urllib_transport
        self.base_branch = base_branch
        self.dry_run = bool(dry_run)
        self.allow_merge = bool(allow_merge)
        self.calls = []

    # ------------------------------------------------------------------ plumbing
    def _request(self, method, path, payload=None):
        if not self.token:
            raise GitHubError("publisher_unconfigured")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "aeion-factory",
        }
        url = path if path.startswith("https://") else f"{API}{path}"
        self.calls.append((method, url))
        status, body = self.transport(method, url, payload, headers)
        return status, body

    def _ref(self, branch):
        return f"/repos/{self.repo}/git/ref/heads/{branch}"

    # ------------------------------------------------------------------ operations
    def base_sha(self):
        status, body = self._request("GET", self._ref(self.base_branch))
        if status != 200 or "object" not in body:
            raise GitHubError(f"base_unreadable:{status}")
        return body["object"]["sha"]

    def ensure_branch(self, branch, sha):
        status, _ = self._request("GET", self._ref(branch))
        if status == 200:
            return "exists"
        if status != 404:
            raise GitHubError(f"branch_probe_failed:{status}")
        status, body = self._request("POST", f"/repos/{self.repo}/git/refs",
                                     {"ref": f"refs/heads/{branch}", "sha": sha})
        if status not in (200, 201):
            raise GitHubError(f"branch_create_failed:{status}")
        return "created"

    def commit_files(self, branch, files, message):
        """Commit each reviewed file on the branch; the content is what the gate approved."""
        committed = []
        for path, text in sorted(files.items()):
            if len(text.encode("utf-8")) > MAX_FILE_BYTES:
                raise GitHubError(f"file_too_large:{path}")
            status, current = self._request("GET", f"/repos/{self.repo}/contents/{path}?ref={branch}")
            sha = current.get("sha") if status == 200 else None
            payload = {"message": message, "content": _b64(text), "branch": branch}
            if sha:
                payload["sha"] = sha
            status, body = self._request("PUT", f"/repos/{self.repo}/contents/{path}", payload)
            if status not in (200, 201):
                raise GitHubError(f"file_commit_failed:{path}:{status}")
            committed.append(path)
        return committed

    def open_pull_request(self, branch, title, body):
        status, existing = self._request("GET", f"/repos/{self.repo}/pulls?state=open&head={self.repo.split('/')[0]}:{branch}")
        if status == 200 and existing:
            return existing[0]
        status, body_json = self._request("POST", f"/repos/{self.repo}/pulls", {
            "title": title, "head": branch, "base": self.base_branch, "body": body,
        })
        if status not in (200, 201):
            raise GitHubError(f"pr_open_failed:{status}")
        return body_json

    def find_pull_request(self, branch):
        status, existing = self._request("GET", f"/repos/{self.repo}/pulls?state=all&head={self.repo.split('/')[0]}:{branch}")
        if status != 200:
            raise GitHubError(f"pr_probe_failed:{status}")
        return existing[0] if existing else None

    # ------------------------------------------------------------------ forge contract
    def publish(self, request):
        branch = branch_name(request["attempt_id"])
        files = request.get("files") or {}
        if not files:
            raise GitHubError("publisher_no_content")
        if self.dry_run:
            return {"status": "published", "pr": {"simulated": False, "dry_run": True,
                                                  "branch": branch, "pr_number": None, "merged": False}}
        sha = self.base_sha()
        self.ensure_branch(branch, sha)
        self.commit_files(branch, files, request.get("title") or f"Feature {request.get('feature_id')}")
        pr = self.open_pull_request(branch, request.get("title") or f"Feature {request.get('feature_id')}",
                                    "Produced by the Aeion factory. Reviewed diff, frozen base and protected checks passed.")
        merged = False
        if self.allow_merge and request.get("merge"):
            merged = self.merge(pr["number"])
        return {"status": "published", "pr": {"simulated": False, "dry_run": False, "branch": branch,
                                              "pr_number": pr.get("number"), "html_url": pr.get("html_url"),
                                              "merged": merged}}

    def merge(self, number):
        status, _ = self._request("PUT", f"/repos/{self.repo}/pulls/{number}/merge", {"merge_method": "squash"})
        if status != 200:
            raise GitHubError(f"merge_failed:{status}")
        return True

    def reconcile(self, attempt_id):
        branch = branch_name(attempt_id)
        try:
            pr = self.find_pull_request(branch)
        except GitHubError as exc:
            return {"status": "unknown", "reason": str(exc)}
        if pr is None:
            return {"status": "absent"}
        return {"status": "published", "pr": {"simulated": False, "branch": branch,
                                              "pr_number": pr.get("number"),
                                              "html_url": pr.get("html_url"),
                                              "merged": bool(pr.get("merged_at"))}}


def _b64(text):
    import base64
    return base64.b64encode(text.encode("utf-8")).decode("ascii")
