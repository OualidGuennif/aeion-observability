"""Startup errors retain fixed causes without confusing ordinary log numbers with values."""
from pathlib import Path
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'app')]
from factory import product_startup
from factory.flue_session import check_evidence

class StartupDiagnosticsTests(unittest.TestCase):
    def test_negative_bound_is_not_confused_with_a_thread_number(self):
        key='AGORA_REQUEST_MAX_BYTES'
        self.assertFalse(product_startup.bound_disclosed(key+' is invalid [executor-thread-1]',{key:'-1'},key))
        self.assertTrue(product_startup.bound_disclosed(key+' is invalid: -1',{key:'-1'},key))
        self.assertTrue(product_startup.bound_disclosed('invalid value: public-invalid-fixture',
            {key:'public-invalid-fixture'},key))

    def test_role_completion_retains_only_a_bounded_checker_cause(self):
        result=check_evidence({'status':'failed','reason':'missing_secret_accepted','artifact_digest':'a'*64,
            'stderr':'private-canary','prompt':'private-canary'})
        self.assertEqual(result,{'status':'failed','reason':'missing_secret_accepted','artifact_digest':'a'*64})
        self.assertNotIn('reason',check_evidence({'status':'failed','reason':'private value with spaces'}))

if __name__=='__main__':unittest.main()
