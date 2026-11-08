"""The protected target check: external contract, host toolchain, bounded evidence."""
import os
import subprocess
import sys
import tempfile
import shutil
import hashlib
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory.checks import target_check
from factory.isolation import IsolationError
from factory.target import ProtectedCheck, Target


class TargetCheckTests(unittest.TestCase):
    def test_changed_acceptance_bytes_cannot_replace_the_frozen_contract(self):
        frozen=SimpleNamespace(acceptance_digest=hashlib.sha256(self.contract.read_bytes()).hexdigest())
        self.contract.write_text('// weakened after freeze\n')
        runner=mock.Mock(side_effect=AssertionError('changed contract must not execute'))
        passed,detail=target_check(self.target,runner=runner)(frozen,{'repo':str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail['reason'],'acceptance_changed')
        runner.assert_not_called()
    def test_symlinked_contract_parent_cannot_overwrite_host_files_before_execution(self):
        outside=self.root / 'outside';outside.mkdir()
        canary=outside / 'ContractTest.java';canary.write_text('SYNTHETIC_HOST_CANARY')
        self.destination.parent.parent.mkdir(parents=True)
        self.destination.parent.symlink_to(outside,target_is_directory=True)
        runner=mock.Mock(side_effect=AssertionError('unsafe check must not run'))
        passed,detail=target_check(self.target,runner=runner)(None,{'repo':str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(canary.read_text(),'SYNTHETIC_HOST_CANARY')
        runner.assert_not_called()

    def test_candidate_symlink_swap_cannot_make_cleanup_delete_a_host_file(self):
        outside=self.root / 'outside';outside.mkdir()
        canary=outside / 'ContractTest.java';canary.write_text('SYNTHETIC_HOST_CANARY')
        def runner(command,**kwargs):
            shutil.rmtree(self.destination.parent)
            self.destination.parent.symlink_to(outside,target_is_directory=True)
            return subprocess.CompletedProcess(command,0,'BUILD SUCCESSFUL','')
        passed,detail=target_check(self.target,runner=runner)(None,{'repo':str(self.repo)})
        self.assertFalse(passed)
        self.assertTrue(canary.is_file(),'cleanup must not follow a candidate-created parent symlink')
        self.assertEqual(canary.read_text(),'SYNTHETIC_HOST_CANARY')
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.destination = self.repo / "demo/forum-app/src/test/java/local/aeion/forum/ContractTest.java"
        self.contract = self.root / "ContractTest.java"
        self.contract.write_text("// protected contract\n")
        self.target = Target(
            id="fixture-013", feature_id="013", target_repo="example/forum",
            controller=self.root, base_source=self.root, base_sha="a" * 40,
            write_paths=["demo/forum-app/src/test/java/local/aeion/forum/"],
            brief=self.root / "brief.md",
            protected_check=ProtectedCheck(
                id="gradle_test",
                command=[sys.executable, "-c", "raise SystemExit(0)", "{repo}"],
                env={"GRADLE_USER_HOME": "{controller}/gradle-home"},
                contract_test=self.contract,
                contract_destination="demo/forum-app/src/test/java/local/aeion/forum/ContractTest.java",
                timeout_seconds=30,
            ),
        )

    def test_copies_the_contract_and_removes_it_after_a_pass(self):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            self.assertTrue(self.destination.is_file())
            return subprocess.CompletedProcess(command, 0, "BUILD SUCCESSFUL\n", "")

        passed, detail = target_check(self.target, runner=runner)(
            object(), {"accepted": True, "repo": str(self.repo)})
        self.assertTrue(passed)
        self.assertEqual(detail["returncode"], 0)
        self.assertEqual(detail["contract_sha256"], __import__("hashlib").sha256(
            self.contract.read_bytes()).hexdigest())
        self.assertFalse(self.destination.exists())
        command, kwargs = calls[0]
        self.assertEqual(kwargs["cwd"], str(self.repo))
        self.assertTrue(kwargs["env"]["GRADLE_USER_HOME"].endswith("/gradle-home"))
        self.assertIn(str(self.repo), command)

    def test_failure_keeps_only_bounded_test_names(self):
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(
                command, 1, "ContractTest > cspIsEnforced() FAILED\n  at candidate.Stack\n", "")

        passed, detail = target_check(self.target, runner=runner)(
            object(), {"repo": str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail["failed_tests"], ["ContractTest > cspIsEnforced() FAILED"])
        self.assertNotIn("candidate.Stack", str(detail))

    def test_a_gradle_failure_without_a_test_line_keeps_one_identifier(self):
        from factory.checks import _failed_tests
        self.assertEqual(_failed_tests("Execution failed for task ':test'.\nsecret log"), [":test"])
        self.assertEqual(_failed_tests("java.lang.AssertionError: secret value\n"), ["AssertionError"])
        self.assertNotIn("secret", str(_failed_tests("java.lang.AssertionError: secret value\n")))

    def test_compilation_failure_exposes_identifiers_without_source_or_values(self):
        def runner(command, **kwargs):
            output = ('/workspace/src/Filter.java:82: error: cannot find symbol\n'
                      '    PRIVATE_SOURCE_CONTENT\n'
                      '  symbol:   variable UNPROCESSABLE_ENTITY\n'
                      '  location: class Filter\nPRIVATE_VALUE\n')
            return subprocess.CompletedProcess(command, 1, output, '')
        passed, detail = target_check(self.target, runner=runner)(None, {'repo': str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail['failure_kind'], 'java_compilation_failed')
        self.assertEqual(detail['compiler_errors'], [
            {'file': 'Filter.java', 'line': 82, 'symbol': 'UNPROCESSABLE_ENTITY'}])
        self.assertNotIn('PRIVATE_', str(detail))

    def test_timeout_is_a_failed_check_not_a_crash(self):
        def runner(command, **kwargs):
            raise subprocess.TimeoutExpired(command, 30)

        passed, detail = target_check(self.target, runner=runner)(
            object(), {"repo": str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail["reason"], "timeout")

    def test_missing_repository_is_refused(self):
        passed, detail = target_check(self.target)(
            object(), {"repo": str(self.root / "missing")})
        self.assertFalse(passed)
        self.assertEqual(detail["reason"], "repository_missing")

    def test_an_absent_or_relative_repository_is_refused_before_any_effect(self):
        called = []
        for verdict in ({}, {"repo": ""}, {"repo": "relative/repo"}):
            passed, detail = target_check(
                self.target, runner=lambda *args, **kwargs: called.append(args))(
                    object(), verdict)
            self.assertFalse(passed)
            self.assertEqual(detail["reason"], "repository_missing")
        self.assertEqual(called, [])
        self.assertFalse((self.root / "demo").exists())

    def test_a_repository_outside_the_allowed_workspace_is_refused(self):
        passed, detail = target_check(self.target, work_root=self.root / "workspace")(
            object(), {"repo": str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail["reason"], "repository_outside_workspace")
        self.assertFalse(self.destination.exists())

    def test_a_preexisting_destination_is_restored(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.write_text("// candidate copy\n")

        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, "", "")

        passed, _ = target_check(self.target, runner=runner)(
            object(), {"repo": str(self.repo)})
        self.assertTrue(passed)
        self.assertEqual(self.destination.read_text(), "// candidate copy\n")

    def test_controller_secrets_do_not_reach_the_check_environment(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(kwargs["env"])
            return subprocess.CompletedProcess(command, 0, "", "")

        with mock.patch.dict(os.environ, {
                "OPENCODE_API_KEY": "fixture-sentinel",
                "AEION_REVIEW_ENDPOINT": "fixture-sentinel"}, clear=False):
            passed, _ = target_check(self.target, runner=runner)(
                object(), {"repo": str(self.repo)})

        self.assertTrue(passed)
        self.assertNotIn("OPENCODE_API_KEY", calls[0])
        self.assertNotIn("AEION_REVIEW_ENDPOINT", calls[0])
        self.assertIn("PATH", calls[0])
        self.assertTrue(calls[0]["GRADLE_USER_HOME"].endswith("/gradle-home"))

    def test_a_missing_isolation_boundary_holds_the_check(self):
        def runner(command, **kwargs):
            raise IsolationError("docker_unavailable")

        passed, detail = target_check(self.target, sandbox=runner)(
            object(), {"repo": str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail["reason"], "isolation_unqualified")
        self.assertFalse(self.destination.exists())

    def test_a_modified_contract_is_detected_and_restored(self):
        def runner(command, **kwargs):
            self.destination.write_text("// altered during the check\n")
            return subprocess.CompletedProcess(command, 0, "", "")

        passed, detail = target_check(self.target, runner=runner)(
            object(), {"repo": str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail["reason"], "contract_modified")
        self.assertFalse(self.destination.exists())

    def test_a_deleted_contract_is_tampering_not_a_missing_toolchain(self):
        def runner(command, **kwargs):
            self.destination.unlink()
            return subprocess.CompletedProcess(command, 0, "", "")

        passed, detail = target_check(self.target, runner=runner)(
            object(), {"repo": str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail["reason"], "contract_modified")
        self.assertFalse(self.destination.exists())

    def test_candidate_junit_interceptor_and_service_resources_are_refused(self):
        interceptor = self.repo / "demo/forum-app/src/test/java/local/aeion/forum/CandidateInterceptor.java"
        interceptor.parent.mkdir(parents=True, exist_ok=True)
        interceptor.write_text("package local.aeion.forum;\nimport org.junit.jupiter.api.extension.InvocationInterceptor;\n")
        runner = mock.Mock(side_effect=AssertionError("tampered grader must not execute"))
        passed, detail = target_check(self.target, runner=runner)(None, {"repo": str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail["reason"], "grader_tampered")
        runner.assert_not_called()
        interceptor.unlink()
        service = self.repo / "demo/forum-app/src/main/resources/META-INF/services/org.junit.jupiter.api.extension.Extension"
        service.parent.mkdir(parents=True, exist_ok=True)
        service.write_text("local.aeion.forum.CandidateInterceptor\n")
        passed, detail = target_check(self.target, runner=runner)(None, {"repo": str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail["reason"], "grader_tampered")
        runner.assert_not_called()

    def test_skipped_or_unreported_contract_test_is_refused_when_results_exist(self):
        results = self.repo / "demo/forum-app/build/test-results/test"
        results.mkdir(parents=True, exist_ok=True)
        report = results / "TEST-local.aeion.forum.ContractTest.xml"

        def skipped_runner(command, **kwargs):
            report.write_text('<testsuite tests="1" skipped="1" failures="0" errors="0">'
                              '<testcase classname="local.aeion.forum.ContractTest" name="oracle()">'
                              '<skipped/></testcase></testsuite>')
            return subprocess.CompletedProcess(command, 0, "BUILD SUCCESSFUL\n", "")

        passed, detail = target_check(self.target, runner=skipped_runner)(None, {"repo": str(self.repo)})
        self.assertFalse(passed)
        self.assertEqual(detail["reason"], "contract_not_executed")

        def executed_runner(command, **kwargs):
            report.write_text('<testsuite tests="1" skipped="0" failures="0" errors="0">'
                              '<testcase classname="local.aeion.forum.ContractTest" name="oracle()"/>'
                              '</testsuite>')
            return subprocess.CompletedProcess(command, 0, "BUILD SUCCESSFUL\n", "")

        passed, detail = target_check(self.target, runner=executed_runner)(None, {"repo": str(self.repo)})
        self.assertTrue(passed)


if __name__ == "__main__":
    unittest.main()
