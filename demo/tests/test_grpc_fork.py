"""Child processes of the controller must not inherit gRPC's restarted thread pool."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest

APP = Path(__file__).resolve().parents[1] / 'app'
sys.path.insert(0, str(APP))
from grpc_fork import VARIABLE, disable_grpc_fork_handlers

# A process with a live gRPC channel forks; the child reports its native thread count.
PROBE = r'''
import os, subprocess, sys, time, warnings
warnings.simplefilter("ignore")
import grpc
channel = grpc.insecure_channel("127.0.0.1:1")
channel.subscribe(lambda state: None, try_to_connect=True)
time.sleep(1.0)
pid = os.fork()
if pid == 0:
    time.sleep(1.0); os._exit(0)
time.sleep(0.5)
lines = subprocess.run(["ps", "-M", "-p", str(pid)], capture_output=True, text=True).stdout.splitlines()
os.waitpid(pid, 0)
print(len(lines) - 1)
'''


class GrpcForkTests(unittest.TestCase):
    def test_the_guard_forces_fork_support_off_even_when_enabled(self):
        self.assertEqual(disable_grpc_fork_handlers({VARIABLE: '1'})[VARIABLE], 'false')

    def test_the_controller_and_openshell_qualifier_apply_it_before_grpc(self):
        for path, marker in ((APP / 'server.py', 'from runner import'),
                             (APP.parent / 'openshell/qualify.py', 'from openshell import')):
            text = path.read_text()
            self.assertLess(text.index('disable_grpc_fork_handlers()'), text.index(marker), path)

    @unittest.skipUnless(sys.platform == 'darwin' and importlib.util.find_spec('grpc'), 'macOS with gRPC only')
    def test_a_forked_child_keeps_a_single_thread(self):
        child = disable_grpc_fork_handlers({'PATH': os.defpath, 'HOME': str(Path.home())})
        result = subprocess.run([sys.executable, '-c', PROBE], env=child, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr[-300:])
        self.assertEqual(result.stdout.strip(), '1')


if __name__ == '__main__':
    unittest.main()
