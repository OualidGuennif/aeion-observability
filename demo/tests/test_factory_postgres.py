"""Disposable PostgreSQL command/cleanup boundary; no daemon is used in these unit tests."""
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory.isolation import IsolationError
from factory.postgres import DisposablePostgres, PostgresCheckRunner


class PostgresBoundaryTests(unittest.TestCase):
    def fake(self, command, **kwargs):
        self.commands.append((command,kwargs))
        self.assertEqual(set(kwargs['env']), {'PATH'})
        if command[1:3] == ['image','inspect']:
            output = 'sha256:'+'a'*64
        elif command[1] == 'run':
            output = 'b'*64
        elif 'pg_isready' in command:
            output = 'ready'
        elif 'psql' in command:
            output = '170006'
        else:
            output = ''
        return subprocess.CompletedProcess(command,0,stdout=output,stderr='')

    def setUp(self):
        self.commands=[]

    def test_ram_only_database_is_pinned_network_none_and_removed_after_candidate_failure(self):
        with patch('factory.postgres.subprocess.run',side_effect=self.fake):
            with self.assertRaisesRegex(ValueError,'candidate failed'):
                with DisposablePostgres() as database:
                    name=database.name
                    raise ValueError('candidate failed')
        start=next(command for command,_ in self.commands if command[1]=='run')
        self.assertEqual(start[start.index('--network')+1],'none')
        self.assertEqual(start[start.index('--user')+1],'postgres')
        self.assertIn('--read-only',start)
        self.assertIn('PGDATA=/tmp/aeion-postgres',start)
        self.assertIn('/var/run/postgresql:rw,size=1m,mode=1777',start)
        self.assertNotIn('-v',start)
        self.assertNotIn('-p',start)
        self.assertNotIn('postgres:17',start)
        self.assertIn('sha256:'+'a'*64,start)
        self.assertIn(['docker','rm','-f',name],[c for c,_ in self.commands])
        self.assertEqual(self.commands[-1][0][1:3],['ps','-aq'])

    def test_unconfirmed_teardown_is_a_failure(self):
        def remaining(command,**kwargs):
            result=self.fake(command,**kwargs)
            if command[1]=='ps':result.stdout='still-present'
            return result
        with patch('factory.postgres.subprocess.run',side_effect=remaining):
            with self.assertRaisesRegex(IsolationError,'teardown_unconfirmed'):
                with DisposablePostgres():pass

    def test_failed_start_still_reconciles_owned_container_absence(self):
        def fail(command,**kwargs):
            result=self.fake(command,**kwargs)
            if command[1]=='run':result.returncode=1
            return result
        with patch('factory.postgres.subprocess.run',side_effect=fail):
            with self.assertRaisesRegex(IsolationError,'start_failed'):
                with DisposablePostgres():pass
        self.assertEqual(self.commands[-1][0][1:3],['ps','-aq'])

    def test_checker_shares_only_owned_loopback_and_fixed_test_environment(self):
        runner=PostgresCheckRunner('/synthetic-controller')
        runner._database=DisposablePostgres()
        flags=runner._flags('/candidate',image='sha256:'+'a'*64)
        self.assertEqual(flags[flags.index('--network')+1],'container:'+runner._database.name)
        self.assertIn('QUARKUS_DATASOURCE_DEVSERVICES_ENABLED=false',flags)
        self.assertIn('QUARKUS_DATASOURCE_USERNAME=aeion_factory_app',flags)
        self.assertIn('QUARKUS_DATASOURCE_PASSWORD='+runner._database.passwords['application'],flags)
        for role in ('admin','migration'):
            self.assertFalse(any(runner._database.passwords[role] in flag for flag in flags))
        self.assertIn('--read-only',flags)
        self.assertNotIn('--publish',flags)
        self.assertEqual(flags[-1],'sha256:'+'a'*64)

    def test_each_database_has_distinct_random_role_credentials(self):
        first,second=DisposablePostgres(),DisposablePostgres()
        self.assertEqual(len(set(first.passwords.values())|set(second.passwords.values())),6)
        with self.assertRaisesRegex(IsolationError,'role_invalid'):
            first.sql('SELECT 1',role='untrusted')


if __name__=='__main__':unittest.main()
