"""Bootstrap must recognize its own running gateway; Linux truncates process names."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("openshell_setup", Path(__file__).resolve().parents[1] / "openshell/setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class GatewayMatchTests(unittest.TestCase):
    def test_full_command_line_identifies_only_this_gateway(self):
        gateway = Path("/home/user/project/demo/.local/openshell/bin/openshell-gateway")
        for line, expected in [(f"{gateway} --config /x/gateway.toml\n", True), (f"{gateway}\n", True),
                               (f"{gateway}-old --config /x/gateway.toml\n", False),
                               ("openshell-gatew\n", False), ("/usr/bin/sleep 30\n", False)]:
            with self.subTest(line=line), patch("subprocess.check_output", return_value=line.encode()):
                self.assertIs(setup.gateway_running(1234, gateway), expected)
        with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "ps")):
            self.assertFalse(setup.gateway_running(1234, gateway))


@unittest.skipUnless(shutil.which("ps"), "ps required")
class GatewayProcessTests(unittest.TestCase):
    def test_real_long_named_process_is_detected(self):
        # A symlinked binary keeps the long argv[0]; multicall tools such as coreutils would exit.
        # A framework Python rewrites argv[0] on macOS, so `sleep` is preferred where it exists.
        with tempfile.TemporaryDirectory() as folder:
            gateway = Path(folder) / "bin/openshell-gateway"
            gateway.parent.mkdir()
            sleeper = shutil.which("sleep")
            if sleeper:
                gateway.symlink_to(sleeper)
                command = [str(gateway), "30"]
            else:
                gateway.symlink_to(Path(sys.executable).resolve())
                command = [str(gateway), "-c", "import time; time.sleep(30)"]
            process = subprocess.Popen(command)
            try:
                line = subprocess.check_output(["ps", "-p", str(process.pid), "-o", "command="]).decode().strip()
                if not line.startswith(str(gateway) + " "):
                    self.skipTest("this platform's interpreter launcher rewrites argv[0]")
                self.assertTrue(setup.gateway_running(process.pid, gateway))
                self.assertFalse(setup.gateway_running(process.pid, gateway.with_name("openshell-gateway-old")))
            finally:
                process.kill()
                process.wait()
            self.assertFalse(setup.gateway_running(process.pid, gateway))


class TlsPermissionsTests(unittest.TestCase):
    def test_normalize_tls_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tls = root / "local/openshell/tls"
            tls.mkdir(parents=True)
            # Create subdirs and files with restrictive 0600 / 0700 permissions
            (tls / "server").mkdir(mode=0o700)
            ca_crt = tls / "ca.crt"
            ca_crt.write_bytes(b"cert")
            ca_crt.chmod(0o600)
            server_crt = tls / "server/tls.crt"
            server_crt.write_bytes(b"cert")
            server_crt.chmod(0o600)
            server_key = tls / "server/tls.key"
            server_key.write_bytes(b"key")
            server_key.chmod(0o644)

            setup.normalize_tls_permissions(tls)

            # Certificates must be readable (0644)
            self.assertEqual(oct(ca_crt.stat().st_mode & 0o777), oct(0o644))
            self.assertEqual(oct(server_crt.stat().st_mode & 0o777), oct(0o644))
            # Keys must stay strictly private (0600)
            self.assertEqual(oct(server_key.stat().st_mode & 0o777), oct(0o600))
            # Directories must allow traversal (0755)
            self.assertEqual(oct(tls.stat().st_mode & 0o777), oct(0o755))
            self.assertEqual(oct((tls / "server").stat().st_mode & 0o777), oct(0o755))

    def test_normalize_tls_permissions_handles_missing_dir(self):
        setup.normalize_tls_permissions(Path("/nonexistent/tls/dir"))


if __name__ == "__main__":
    unittest.main()
