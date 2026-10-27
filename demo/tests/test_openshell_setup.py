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
        # A symlinked interpreter keeps the long argv[0]; multicall tools such as coreutils would exit.
        with tempfile.TemporaryDirectory() as folder:
            gateway = Path(folder) / "bin/openshell-gateway"
            gateway.parent.mkdir()
            gateway.symlink_to(Path(sys.executable).resolve())
            process = subprocess.Popen([str(gateway), "-c", "import time; time.sleep(30)"])
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


if __name__ == "__main__":
    unittest.main()
