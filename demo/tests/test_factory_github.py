import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.github import GitHubError, GitHubForge, branch_name


class FakeTransport:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def __call__(self, method, url, payload, headers):
        self.calls.append((method, url, payload))
        for (m, fragment), response in self.responses.items():
            if m == method and fragment in url:
                return response
        return 200, {}

    def methods(self):
        return [c[0] for c in self.calls]

    def urls(self):
        return [c[1] for c in self.calls]


BASE = {
    ("GET", "/git/ref/heads/main"): (200, {"object": {"sha": "base123"}}),
    ("GET", "/git/ref/heads/aeion/build-"): (404, {"message": "Not Found"}),
    ("POST", "/git/refs"): (201, {"ref": "refs/heads/x"}),
    ("GET", "/contents/demo/forum/product/x.md"): (404, {"message": "Not Found"}),
    ("PUT", "/contents/demo/forum/product/x.md"): (201, {"content": {"sha": "c1"}}),
    ("GET", "/pulls?state=open"): (200, []),
    ("GET", "/pulls?state=all"): (200, []),
    ("POST", "/pulls"): (201, {"number": 7, "html_url": "https://github.com/o/r/pull/7"}),
}


def forge(**kwargs):
    transport = FakeTransport(dict(BASE))
    instance = GitHubForge("o/r", token="tok", transport=transport,
                           dry_run=kwargs.pop("dry_run", False), **kwargs)
    return instance, transport


def request(**overrides):
    base = {"attempt_id": "a" * 32, "feature_id": "001", "title": "Feature 001",
            "files": {"demo/forum/product/x.md": "hello\n"}}
    base.update(overrides)
    return base


class ConfigTests(unittest.TestCase):
    def test_missing_token_is_refused(self):
        instance = GitHubForge("o/r", token=None)
        instance.token = None
        with self.assertRaisesRegex(GitHubError, "publisher_unconfigured"):
            instance.base_sha()

    def test_branch_name_is_deterministic(self):
        self.assertEqual(branch_name("a" * 32), branch_name("a" * 32))
        self.assertNotEqual(branch_name("a" * 32), branch_name("b" * 32))
        self.assertTrue(branch_name("a" * 32).startswith("aeion/build-"))

    def test_dry_run_makes_no_call(self):
        instance, transport = forge(dry_run=True)
        result = instance.publish(request())
        self.assertTrue(result["pr"]["dry_run"])
        self.assertEqual(transport.calls, [])

    def test_missing_content_is_refused(self):
        instance, _ = forge()
        with self.assertRaisesRegex(GitHubError, "publisher_no_content"):
            instance.publish(request(files={}))


class PublishTests(unittest.TestCase):
    def test_publish_creates_branch_commits_and_opens_pr(self):
        instance, transport = forge()
        result = instance.publish(request())
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["pr"]["pr_number"], 7)
        self.assertFalse(result["pr"]["merged"])
        methods = transport.methods()
        self.assertIn("POST", methods)
        urls = " ".join(transport.urls())
        self.assertIn("/git/refs", urls)
        self.assertIn("/contents/demo/forum/product/x.md", urls)
        self.assertIn("/pulls", urls)

    def test_merge_requires_the_explicit_flag(self):
        instance, transport = forge()
        instance.publish(request())
        self.assertNotIn(("PUT", "https://api.github.com/repos/o/r/pulls/7/merge"), transport.calls)

    def test_merge_runs_only_when_allowed_and_requested(self):
        transport = FakeTransport({**BASE, ("PUT", "/pulls/7/merge"): (200, {"merged": True})})
        instance = GitHubForge("o/r", token="tok", transport=transport, dry_run=False, allow_merge=True)
        result = instance.publish(request(merge=True))
        self.assertTrue(result["pr"]["merged"])

    def test_token_is_never_echoed_in_the_result(self):
        instance, _ = forge()
        result = instance.publish(request())
        self.assertNotIn("tok", repr(result))

    def test_existing_branch_is_reused(self):
        transport = FakeTransport({**BASE, ("GET", "/git/ref/heads/aeion/build-"): (200, {"object": {"sha": "s"}})})
        instance = GitHubForge("o/r", token="tok", transport=transport, dry_run=False)
        result = instance.publish(request())
        self.assertEqual(result["status"], "published")
        self.assertNotIn("POST", transport.methods()[:2])


class ReconcileTests(unittest.TestCase):
    def test_reconcile_finds_the_existing_pull_request(self):
        transport = FakeTransport({**BASE,
            ("GET", "/pulls?state=all"): (200, [{"number": 9, "html_url": "x", "merged_at": None}])})
        instance = GitHubForge("o/r", token="tok", transport=transport, dry_run=False)
        result = instance.reconcile("a" * 32)
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["pr"]["pr_number"], 9)

    def test_reconcile_absent(self):
        instance, _ = forge()
        self.assertEqual(instance.reconcile("a" * 32)["status"], "absent")

    def test_reconcile_reports_unknown_on_error(self):
        transport = FakeTransport({**BASE, ("GET", "/pulls?state=all"): (500, {"message": "boom"})})
        instance = GitHubForge("o/r", token="tok", transport=transport, dry_run=False)
        self.assertEqual(instance.reconcile("a" * 32)["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
