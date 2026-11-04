"""Native isolated PostgreSQL transaction, namespace and teardown proof; no product mutation.

Run with demo/.local/venv/bin/python demo/tests/qualify_postgres.py.
This qualifies a check boundary only, never feature 002/003 or factory activation.
"""
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'demo'))
from factory.postgres import PostgresCheckRunner
from factory.isolation import IsolationError


def main():
    runner=PostgresCheckRunner(ROOT)
    proof={'kind':'isolated_postgres_boundary','product_modified':False,
           'feature_qualified':False,'real_model_requests':0}
    with runner.database() as database:
        proof.update(postgres_image_id=database.image_id,version=database.server_version)
        database.sql('CREATE TABLE factory_canary (id integer PRIMARY KEY); INSERT INTO factory_canary VALUES (1);')
        database.sql('BEGIN; INSERT INTO factory_canary VALUES (2); ROLLBACK;')
        assert database.sql('SELECT count(*) FROM factory_canary;')=='1'
        proof['transaction_rollback']='passed'
        proof['isolated_loopback_and_denied_egress']='passed'
        database.sql('CREATE TABLE least_privilege_canary (id integer PRIMARY KEY);',role='migration')
        database.sql('INSERT INTO least_privilege_canary VALUES (1);',role='application')
        assert database.sql('SELECT count(*) FROM least_privilege_canary;',role='application')=='1'
        assert database.sql('SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls '
                            'FROM pg_roles WHERE rolname=current_user;',role='application')=='f'
        for statement in ('CREATE TABLE forbidden_ddl (id integer);',
                          'DROP TABLE least_privilege_canary;',
                          'CREATE ROLE forbidden_role;',
                          'CREATE DATABASE forbidden_database;',
                          'CREATE TEMP TABLE forbidden_temp (id integer);'):
            try:database.sql(statement,role='application')
            except IsolationError:pass
            else:raise AssertionError('Application role gained DDL/role authority')
        proof['application_dml_passed_and_ddl_roles_denied']=True
    proof['first_teardown_confirmed']=True
    try:
        with runner.database() as database:
            assert database.sql("SELECT to_regclass('public.factory_canary') IS NULL;")=='t'
            proof['fresh_database']='passed'
            raise ValueError('synthetic candidate failure')
    except ValueError as error:
        if str(error)!='synthetic candidate failure':raise
    proof['failure_teardown_confirmed']=True
    folder=Path(tempfile.mkdtemp(prefix='aeion-postgres-proof-',dir='/private/tmp'))
    (folder/'proof.json').write_text(json.dumps(proof,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'evidence':str(folder/'proof.json'),**proof}))


if __name__=='__main__':main()
