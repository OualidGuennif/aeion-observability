"""Fixed PostgreSQL migration/import/restore oracles over disposable public fixtures.

The application cannot select these probes or receive the administrator/owner credential.
Only public test rows enter the import/restore job; no operator database is read here.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile

from .isolation import IsolationError
from .postgres import DisposablePostgres, DATABASE, USERNAME, APP_USERNAME, MIGRATION_USERNAME

# The legacy product stored nanoseconds as integers. Preserve the exact values and IDs.
TABLES={
 'settings':('name','value','updated_ns'),
 'accounts':('id','username','password','role','created_ns','locked_ns','failures'),
 'sessions':('id','account_id','issued_ns','expires_ns','revoked_ns'),
 'threads':('id','title','body','author_id','created_ns'),
 'thread_outbox':('event_id','topic','payload','created_ns','attempts','published_ns','last_error'),
 'thread_event_log':('event_id','topic','received_ns','payload'),
 'schema_events':('id','at_ns','migration','detail'),
}
ROWS={
 'settings':[('fixture','preserved',1700000000000000000)],
 'accounts':[('public-account-1','fixture-alice','public-test-hash','member',1700000000000000000,None,0)],
 'sessions':[('public-session-hash-1','public-account-1',1700000000000000000,1700000000001000000,None)],
 'threads':[('public-thread-1','Public fixture','A normalized public fixture.','public-account-1',1700000000000000001)],
 'thread_outbox':[('public-event-1','forum.thread.created','{"id":"public-thread-1"}',1700000000000000001,0,None,None)],
 'thread_event_log':[('public-event-old','forum.thread.created',1700000000000000002,'{}')],
 'schema_events':[(1,1700000000000000000,'V1__initial.sql','public fixture')],
}


def sqlite_fixture(path):
    with sqlite3.connect(path) as db:
        for table,columns in TABLES.items():
            types=['INTEGER' if name.endswith('_ns') or name in ('attempts','failures') or
                table=='schema_events' and name=='id' else 'TEXT' for name in columns]
            db.execute('CREATE TABLE '+table+' ('+','.join('"'+name+'" '+kind for name,kind in zip(columns,types))+')')
            db.executemany('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in columns)+')',ROWS[table])
        db.execute('PRAGMA user_version=2')
    path.chmod(0o444)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(database):
    result={}
    for table,columns in TABLES.items():
        # All identifiers come from this fixed registry, never model output.
        sql='SELECT coalesce(json_agg(row_to_json(r) ORDER BY r."'+columns[0]+'"),\'[]\') FROM (SELECT '+','.join('"'+c+'"' for c in columns)+' FROM "'+table+'") r'
        result[table]=json.loads(database.sql(sql))
    return result


def expected_rows():
    return {name:[dict(zip(TABLES[name],row)) for row in rows] for name,rows in ROWS.items()}


def _dump(database):
    result=database._call(['exec','-e','PGPASSWORD='+database.passwords['admin'],database.name,
        'pg_dump','-h','127.0.0.1','-U',USERNAME,'-d',DATABASE,'--no-owner','--no-acl'],timeout=30)
    if result.returncode:raise IsolationError('postgres_backup_failed')
    return result.stdout


def _restore(database, dump):
    import os
    result=subprocess.run([database.docker,'exec','-i','-e','PGPASSWORD='+database.passwords['migration'],
        database.name,'psql','-h','127.0.0.1','-U',MIGRATION_USERNAME,'-d',DATABASE,'-v','ON_ERROR_STOP=1'],
        input=dump,capture_output=True,text=True,timeout=45,
        env={'PATH':os.environ.get('PATH','/usr/local/bin:/usr/bin:/bin')})
    if result.returncode:raise IsolationError('postgres_restore_failed')


def verify_migration(runner, product, database):
    """Return only fixed failure codes, never SQL diagnostics or imported row values."""
    operator=lambda args,**kw:runner._operator(product,database,args,**kw)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(operator,['migrate']) for _ in range(2)]
        if any(f.result().returncode for f in futures):return False,'concurrent_migration_failed'
    before=database.sql("SELECT string_agg(version||':'||checksum,',' ORDER BY installed_rank) FROM flyway_schema_history WHERE success")
    if not before or operator(['migrate']).returncode:return False,'migration_not_idempotent'
    if before!=database.sql("SELECT string_agg(version||':'||checksum,',' ORDER BY installed_rank) FROM flyway_schema_history WHERE success"):
        return False,'migration_not_idempotent'
    if database.sql("SELECT has_schema_privilege(current_user,'public','CREATE')",role='application')!='f':
        return False,'application_can_create_schema'
    # The runtime cannot change migration history, imported audit history or grant itself roles.
    for table in ('flyway_schema_history','schema_events'):
        for privilege in ('UPDATE','DELETE','TRUNCATE'):
            if database.sql("SELECT has_table_privilege(current_user,'"+table+"','"+privilege+"')",role='application')!='f':
                return False,'application_can_modify_history'
    if database.sql("SELECT has_table_privilege(current_user,'flyway_schema_history','INSERT')",role='application')!='f':
        return False,'application_can_modify_history'
    with tempfile.TemporaryDirectory(prefix='aeion-public-import-') as directory:
        folder=Path(directory);fixture=folder/'legacy.sqlite';original=sqlite_fixture(fixture)
        if operator(['import-sqlite','/fixtures/legacy.sqlite'],fixtures=folder).returncode:
            return False,'sqlite_import_failed'
        if snapshot(database)!=expected_rows():return False,'sqlite_import_integrity_failed'
        if operator(['import-sqlite','/fixtures/legacy.sqlite'],fixtures=folder).returncode or snapshot(database)!=expected_rows():
            return False,'sqlite_import_replay_failed'
        if hashlib.sha256(fixture.read_bytes()).hexdigest()!=original:return False,'sqlite_source_changed'
        dump=_dump(database)
        with DisposablePostgres(runner.docker) as restored:
            _restore(restored,dump)
            # Restored tables belong to the migration owner, never the fixture admin.
            # Idempotent migrate must reapply least-privilege grants after --no-acl restore.
            if runner._operator(product,restored,['migrate']).returncode:
                return False,'postgres_restore_permissions_failed'
            if snapshot(restored)!=expected_rows():return False,'postgres_restore_integrity_failed'
            for table in ('flyway_schema_history','schema_events'):
                if restored.sql("SELECT has_table_privilege(current_user,'"+table+"','UPDATE')",role='application')!='f':
                    return False,'restored_application_can_modify_history'
        database.sql("UPDATE threads SET body='deliberately altered fixture' WHERE id='public-thread-1'")
        if operator(['import-sqlite','/fixtures/legacy.sqlite'],fixtures=folder).returncode==0:
            return False,'altered_import_not_refused'
        if hashlib.sha256(fixture.read_bytes()).hexdigest()!=original:return False,'sqlite_source_changed'
        database.sql("UPDATE threads SET body='A normalized public fixture.' WHERE id='public-thread-1'")
    # Rollback a deliberately failing real Flyway migration from an extra classpath root.
    with tempfile.TemporaryDirectory(prefix='aeion-failing-migration-') as directory:
        folder=Path(directory);migration=folder/'db/migration';migration.mkdir(parents=True)
        (migration/'V999998__transaction_failure.sql').write_text(
            'CREATE TABLE forbidden_partial_migration(id integer);\nSELECT aeion_deliberate_missing_function();\n')
        if operator(['migrate'],fixtures=folder).returncode==0:return False,'failing_migration_not_refused'
        if database.sql("SELECT to_regclass('public.forbidden_partial_migration') IS NULL")!='t':
            return False,'partial_migration_not_rolled_back'
    # Tamper only this owned fixture's history; validation must reject both checksum drift
    # and a database version ahead of the packaged code, then restore for the API checks.
    database.sql('UPDATE flyway_schema_history SET checksum=checksum+1 WHERE installed_rank=1')
    if operator(['validate']).returncode==0:return False,'changed_checksum_not_refused'
    database.sql('UPDATE flyway_schema_history SET checksum=checksum-1 WHERE installed_rank=1')
    version=database.sql('SELECT version FROM flyway_schema_history WHERE installed_rank=1')
    if not version or not all(c in '0123456789._' for c in version):return False,'migration_version_invalid'
    database.sql("UPDATE flyway_schema_history SET version='999999' WHERE installed_rank=1")
    ahead_refused=operator(['validate']).returncode!=0
    database.sql("UPDATE flyway_schema_history SET version='"+version+"' WHERE installed_rank=1")
    if not ahead_refused:return False,'ahead_schema_not_refused'
    return True,'migration_import_restore_and_roles_passed'
