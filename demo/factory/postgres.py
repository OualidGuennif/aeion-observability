"""Disposable PostgreSQL for protected checks, never the operator's database.

Spec: knowledge/components/factory-flue.md
Docker's container network mode shares only this owned network-none loopback namespace.
There is no host port, host database mount, Docker socket or provider credential.
"""
from contextlib import contextmanager
import os
import re
import secrets
import subprocess
import tempfile
import threading
import time
import uuid

from .isolation import DockerCheckRunner, IsolationError

POSTGRES_IMAGE = 'postgres:17'
DATABASE = 'aeion_factory_test'
USERNAME = 'aeion_fixture_admin'
MIGRATION_USERNAME = 'aeion_migration_owner'
APP_USERNAME = 'aeion_factory_app'


class DisposablePostgres:
    def __init__(self, docker='docker', image=POSTGRES_IMAGE):
        self.docker, self.image = docker, image
        self.name = 'aeion-check-pg-' + uuid.uuid4().hex[:16]
        self.image_id = None
        self.server_version = None
        # Random per fixture, never inherited from or usable against an operator database.
        self.passwords = {role: secrets.token_urlsafe(32) for role in ('admin','migration','application')}

    def _call(self, args, timeout=15):
        try:
            return subprocess.run([self.docker, *args], capture_output=True, text=True,
                timeout=timeout, env={'PATH': os.environ.get('PATH','/usr/local/bin:/usr/bin:/bin')})
        except (OSError, subprocess.TimeoutExpired):
            raise IsolationError('postgres_docker_unavailable') from None

    def __enter__(self):
        inspected = self._call(['image','inspect','--format','{{.Id}}',self.image])
        self.image_id = inspected.stdout.strip()
        if inspected.returncode or not re.fullmatch(r'sha256:[a-f0-9]{64}',self.image_id):
            raise IsolationError('postgres_image_unavailable')
        try:
            result = self._call(['run','-d','--rm','--name',self.name,'--network','none',
                '--read-only','--user','postgres','--cap-drop','ALL','--security-opt','no-new-privileges',
                '--pids-limit','128','--memory','512m','--cpus','1',
                '--tmpfs','/tmp:rw,size=384m,mode=1777',
                '--tmpfs','/var/run/postgresql:rw,size=1m,mode=1777',
                '--tmpfs','/var/lib/postgresql/data:rw,size=1m',
                '-e','PGDATA=/tmp/aeion-postgres','-e','POSTGRES_DB='+DATABASE,
                '-e','POSTGRES_USER='+USERNAME,'-e','POSTGRES_PASSWORD='+self.passwords['admin'],
                self.image_id,'postgres','-c','listen_addresses=127.0.0.1',
                '-c','max_connections=32'], timeout=30)
            if result.returncode:
                raise IsolationError('postgres_start_failed')
            deadline = time.monotonic()+45
            while time.monotonic() < deadline:
                ready = self._call(['exec',self.name,'pg_isready','-h','127.0.0.1','-U',USERNAME,'-d',DATABASE])
                if ready.returncode == 0:
                    version = self.sql('SHOW server_version_num;')
                    if not re.fullmatch(r'17[0-9]{4}', version):
                        raise IsolationError('postgres_version_mismatch')
                    self.server_version = version
                    self._roles()
                    return self
                alive = self._call(['inspect','--format','{{.State.Running}}',self.name])
                if alive.returncode or alive.stdout.strip() != 'true':
                    raise IsolationError('postgres_start_failed')
                time.sleep(0.2)
            raise IsolationError('postgres_start_timeout')
        except BaseException:
            self.close()
            raise

    def _roles(self):
        # The generated passwords contain only token_urlsafe's SQL-quote-free alphabet.
        for role in ('migration','application'):
            if not re.fullmatch(r'[A-Za-z0-9_-]{32,64}',self.passwords[role]):
                raise IsolationError('postgres_fixture_password_invalid')
        self.sql(f"CREATE ROLE {MIGRATION_USERNAME} LOGIN PASSWORD '{self.passwords['migration']}' "
                 'NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; '
                 f"CREATE ROLE {APP_USERNAME} LOGIN PASSWORD '{self.passwords['application']}' "
                 'NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; '
                 f'ALTER DATABASE {DATABASE} OWNER TO {MIGRATION_USERNAME}; '
                 f'REVOKE ALL ON DATABASE {DATABASE} FROM PUBLIC; '
                 f'GRANT CONNECT ON DATABASE {DATABASE} TO {APP_USERNAME}; '
                 'REVOKE ALL ON SCHEMA public FROM PUBLIC; '
                 f'GRANT USAGE ON SCHEMA public TO {APP_USERNAME}; '
                 f'ALTER DEFAULT PRIVILEGES FOR ROLE {MIGRATION_USERNAME} IN SCHEMA public '
                 f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_USERNAME}; '
                 f'ALTER DEFAULT PRIVILEGES FOR ROLE {MIGRATION_USERNAME} IN SCHEMA public '
                 f'GRANT USAGE, SELECT ON SEQUENCES TO {APP_USERNAME};')

    def sql(self, statement, role='admin'):
        # Supervisor-only SQL against its disposable fixture; no source-derived shell string.
        users={'admin':USERNAME,'migration':MIGRATION_USERNAME,'application':APP_USERNAME}
        if role not in users:raise IsolationError('postgres_fixture_role_invalid')
        result = self._call(['exec','-e','PGPASSWORD='+self.passwords[role],self.name,'psql','-h','127.0.0.1','-U',users[role],
                             '-d',DATABASE,'-v','ON_ERROR_STOP=1','-Atc',statement])
        if result.returncode:
            raise IsolationError('postgres_probe_failed')
        return result.stdout.strip()

    def close(self):
        self._call(['rm','-f',self.name], timeout=30)
        remaining = self._call(['ps','-aq','--filter','name=^/'+self.name+'$'])
        # A failed daemon read is not evidence of absence.
        if remaining.returncode or remaining.stdout.strip():
            raise IsolationError('postgres_teardown_unconfirmed')

    def __exit__(self, *_):
        self.close()


class PostgresCheckRunner(DockerCheckRunner):
    """The Java evaluator may reach only a fresh database over isolated loopback."""
    def __init__(self, *args, postgres_image=POSTGRES_IMAGE, **kwargs):
        super().__init__(*args, **kwargs)
        self.postgres_image = postgres_image
        self._database = None
        self._postgres_lock = threading.RLock()

    def _flags(self, workspace, image=None, name=None):
        flags = super()._flags(workspace, image=image, name=name)
        if self._database is not None:
            flags[flags.index('--network')+1] = 'container:'+self._database.name
            flags[-1:-1] = ['-e','QUARKUS_DATASOURCE_DB_KIND=postgresql',
                '-e','QUARKUS_DATASOURCE_JDBC_URL=jdbc:postgresql://127.0.0.1:5432/'+DATABASE,
                '-e','QUARKUS_DATASOURCE_USERNAME='+APP_USERNAME,
                '-e','QUARKUS_DATASOURCE_PASSWORD='+self._database.passwords['application'],
                '-e','QUARKUS_DATASOURCE_DEVSERVICES_ENABLED=false',
                '-e','AGORA_SESSION_SECRET=disposable-test-session-secret-32bytes']
        return flags

    @contextmanager
    def database(self):
        with self._postgres_lock:
            self.qualification()
            with DisposablePostgres(self.docker,self.postgres_image) as database:
                self._database = database
                try:
                    # Same image/mount/UID/capabilities/network as the candidate. Hostname/DNS
                    # overrides are deliberately absent in container networking mode.
                    with tempfile.TemporaryDirectory(prefix='aeion-pg-network-probe-') as workspace:
                        probe = super().__call__(['bash','-ec',
                            "test $(id -u) != 0; test ! -e /var/run/docker.sock; "
                            "timeout 2 bash -c 'exec 3<>/dev/tcp/127.0.0.1/5432'; "
                            "if timeout 2 bash -c 'exec 3<>/dev/tcp/1.1.1.1/443' 2>/dev/null; then exit 3; fi"],
                            cwd=workspace,timeout=15)
                    if probe.returncode:
                        raise IsolationError('postgres_network_probe_failed')
                    yield database
                finally:
                    self._database = None

    def __call__(self, command, cwd, env=None, timeout=None, **kwargs):
        with self.database() as database:
            result = super().__call__(command,cwd=cwd,env=env,timeout=timeout,**kwargs)
            result.qualification = {**result.qualification,'network':'owned_postgres_loopback',
                'postgres':{'image_id':database.image_id,'version':database.server_version,
                    'data':'disposable_tmpfs','published_ports':False,'external_network':'denied'}}
        result.qualification['postgres']['teardown_confirmed'] = True
        return result
