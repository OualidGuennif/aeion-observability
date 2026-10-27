"""Bootstrap must recognize its own running gateway; Linux truncates process names."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("openshell_setup", Path(__file__).resolve().parents[1] / "openshell/setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


@unittest.skipUnless(shutil.which("ps") and shutil.which("sleep"), "ps and sleep required")
class GatewayDetectionTests(unittest.TestCase):
    def test_long_gateway_name_is_detected_and_other_processes_are_not(self):
        with tempfile.TemporaryDirectory() as folder:
            gateway = Path(folder) / "bin/openshell-gateway"
            gateway.parent.mkdir()
            shutil.copy2(shutil.which("sleep"), gateway)
            try:
                process = subprocess.Popen([str(gateway), "30"])
            except PermissionError:
                self.skipTest("temporary directory is not executable")
            other = subprocess.Popen([shutil.which("sleep"), "30"])
            try:
                self.assertTrue(setup.gateway_running(process.pid, gateway))
                self.assertFalse(setup.gateway_running(other.pid, gateway))
                self.assertFalse(setup.gateway_running(process.pid, gateway.with_name("openshell-gateway-old")))
            finally:
                for child in (process, other):
                    child.kill()
                    child.wait()
            self.assertFalse(setup.gateway_running(process.pid, gateway))


if __name__ == "__main__":
    unittest.main()
