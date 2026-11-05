"""Registered startup refusal probes; generated secrets and logs never leave the checker."""
import json
import re
import secrets
import time
import uuid

BOUNDS=('AGORA_REQUEST_MAX_BYTES','AGORA_TEXT_MAX_CODEPOINTS','AGORA_RENDERED_MAX_BYTES')
CANARY='aeion-unknown-setting-public-fixture'


def bound_disclosed(content, values, key):
    # Long fixture values are unique; short numbers also occur in unrelated diagnostics.
    return any(value in content if len(value)>=8 else
        any(key in line and re.search(r'(?<![\w-])'+re.escape(value)+r'(?![\w])',line)
            for line in content.splitlines()) for value in values.values())


def startup_refusals(runner, package, database):
    cases=[('explicit_database_less',secrets.token_urlsafe(40),{},None,True),
           ('default_database_less',secrets.token_urlsafe(40),{},None,False),
           ('missing_secret',None,{},'AGORA_SESSION_SECRET',True),
           ('short_secret','short-public-fixture',{},'AGORA_SESSION_SECRET',True)]
    for key in BOUNDS:
        for invalid in ('-1','not-a-number','2147483648'):
            cases.append(('invalid_bound',secrets.token_urlsafe(40),{key:invalid},key,True))
    for reason,secret,extra,expected_key,explicit_mode in cases:
        name='aeion-startup-refusal-'+uuid.uuid4().hex[:12]
        flags=runner._runtime_flags(name,database);flags.remove('--rm');flags.insert(1,'-d')
        flags+=['-v',str(package)+':/product:ro',
            '-e','AEION_FORUM_PORT=8080','-e','QUARKUS_HTTP_PORT=8080',
            '-e','AEION_SQLITE_PATH=/proc/aeion/unavailable.db',
            '-e','QUARKUS_DATASOURCE_JDBC_URL=jdbc:postgresql://127.0.0.1:1/unavailable',
            '-e','AEION_UNDOCUMENTED_CANARY='+CANARY]
        if explicit_mode:flags+=['-e','AGORA_DATABASE_ENABLED=false']
        if secret is not None:flags+=['-e','AGORA_SESSION_SECRET='+secret]
        for key,value in extra.items():flags+=['-e',key+'='+value]
        flags += [runner.verifier_image,'java','-jar','/product/quarkus-run.jar']
        try:
            result=runner._call(flags,timeout=30)
            if result.returncode:return False,'startup_probe_launch_failed'
            exited=healthy=False
            for _ in range(60):
                state=runner._call(['inspect','--format','{{.State.Status}} {{.State.ExitCode}}',name])
                if state.returncode:break
                if state.stdout.strip().startswith('exited '):exited=True;break
                probe=runner._call(['exec',name,'python3','-c',
                    'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8080/healthz",timeout=1).read().decode())'],timeout=5)
                if probe.returncode==0:
                    healthy=True
                    if expected_key is not None:return False,reason+'_accepted'
                    try:
                        if json.loads(probe.stdout)!={'status':'ok'}:return False,'health_content_invalid'
                    except ValueError:return False,'health_content_invalid'
                    break
                time.sleep(.1)
            logs=runner._call(['logs',name]);content=logs.stdout+logs.stderr
            if secret and secret in content:return False,reason+'_disclosed_secret'
            if CANARY in content:return False,reason+'_disclosed_unknown_setting'
            if expected_key is None:
                if not healthy:return False,reason+'_startup_rejected'
                continue
            if not exited:return False,'startup_refusal_not_confirmed'
            code=runner._call(['inspect','--format','{{.State.ExitCode}}',name])
            if code.returncode or not code.stdout.strip().isdigit() or int(code.stdout)==0:
                return False,'startup_refusal_not_confirmed'
            if expected_key not in content:return False,'startup_refusal_key_missing'
            # Short numeric values also occur in thread names and stack traces. Require
            # the setting key and a separate value token on the same line to prove echo.
            if bound_disclosed(content,extra,expected_key):
                return False,'invalid_bound_disclosed_value'
        finally:runner._kill(name)
    return True,'startup_refusals_passed'
