"""Disposable unit-test credentials stay separate from the graded production fixture."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.product_unit import ProductUnitRunner
from factory.postgres import USERNAME


class ProductUnitTests(unittest.TestCase):
    def test_only_the_owned_unit_fixture_administrator_is_exposed(self):
        runner=ProductUnitRunner('/public-fixture')
        runner._database=SimpleNamespace(name='owned-unit-fixture',passwords={
            'admin':'public-unit-admin-canary','application':'public-unit-app-canary',
            'migration':'public-migration-canary'})
        flags=runner._flags('/candidate',image='pinned-fixture-image')
        self.assertEqual(flags[flags.index('--network')+1],'container:owned-unit-fixture')
        self.assertIn('AEION_TEST_POSTGRES_USERNAME='+USERNAME,flags)
        self.assertIn('AEION_TEST_POSTGRES_PASSWORD=public-unit-admin-canary',flags)
        self.assertNotIn('public-migration-canary',str(flags))
        self.assertNotIn('OPENCODE_API_KEY',str(flags))
        self.assertNotIn('GH_API_KEY',str(flags))
        self.assertEqual(flags[-1],'pinned-fixture-image')

    def test_without_an_owned_fixture_no_test_database_access_is_added(self):
        flags=ProductUnitRunner('/public-fixture')._flags('/candidate')
        self.assertEqual(flags[flags.index('--network')+1],'none')
        self.assertNotIn('AEION_TEST_POSTGRES',str(flags))


if __name__=='__main__':unittest.main()
