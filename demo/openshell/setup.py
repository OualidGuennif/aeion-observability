"""Install a private, pinned OpenShell gateway; never launches an agent directly."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import tarfile
import time

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0,str(HERE))
try:
    from .reap import reap
except ImportError:  # setup.py is also a script or loaded by file path
    from reap import reap

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.local/openshell'
VERSION='0.1.8'
ARTIFACTS={
 ('Darwin','arm64'):{'openshell':('aarch64-apple-darwin','3c1f767d3afb55c308274da4a1b126542beecef5150b6c437727959b9bd01df8'),'openshell-gateway':('aarch64-apple-darwin','6a4ccc70a957ae30bfb0e8ef19d43cf03bba7b673309a6c4d95cd9831d65ec2e')},
 ('Linux','x86_64'):{'openshell':('x86_64-unknown-linux-musl','87f5c41d396dcd36b4c30a7b5e6f41643a656cb31a82b0edbb00319c9a719c2d'),'openshell-gateway':('x86_64-unknown-linux-gnu','d2e5e7f80811b7cfbad0d48f0b561ea5e301401d311e4402bbfc419b3d08cbd3')},
 ('Linux','aarch64'):{'openshell':('aarch64-unknown-linux-musl','9a2e8f522ccfb3fbd1ed1985a51191a60e083f3404903a56bd4813710a2c7080'),'openshell-gateway':('aarch64-unknown-linux-gnu','09de6844c014ed7fae7acfc91e9f1532ded1b3252a20261ad99e76ff8e26072f')},
}
# v0.1.6 changed the sandbox/supervisor control connection: both images move together.
SANDBOX_IMAGE='ghcr.io/nvidia/openshell/sandbox:0.1.8@sha256:f0fe7dbf18d833acb5da99c405231124718f23b524aa8e3c0108e6f37530033b'
SUPERVISOR_IMAGE='ghcr.io/nvidia/openshell/supervisor:0.1.8@sha256:deadeacfdba6d12ca27e538d0002696369d4de5a4fcad075ab503495503af9d1'


def command(args,**kwargs):
    return subprocess.run(args,check=True,**kwargs)


def normalize_tls_permissions(tls_dir):
    """Ensure Docker supervisor can read certificates without EPERM while keeping keys private."""
    if not tls_dir.exists():
        return
    for parent in (tls_dir.parent.parent, tls_dir.parent, tls_dir):
        if parent.exists():
            try:
                parent.chmod(0o755)
            except OSError:
                pass
    for path in tls_dir.rglob('*'):
        if path.is_dir():
            try:
                path.chmod(0o755)
            except OSError:
                pass
        elif path.is_file():
            try:
                if path.suffix == '.crt':
                    path.chmod(0o644)
                elif path.suffix == '.key':
                    path.chmod(0o600)
                if platform.system() == 'Darwin':
                    subprocess.run(['xattr', '-c', str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                pass


def gateway_running(pid,gateway):
    # Linux truncates `comm` to 15 characters; compare the launched executable path instead.
    try:
        line=subprocess.check_output(['ps','-p',str(pid),'-o','command='],stderr=subprocess.DEVNULL).decode().strip()
    except subprocess.CalledProcessError:
        return False
    return line==str(gateway) or line.startswith(str(gateway)+' ')


def install(name,arch,digest):
    directory=STATE/'downloads';directory.mkdir(parents=True,exist_ok=True)
    archive=directory/(name+'-'+arch+'.tar.gz')
    if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest()!=digest:
        command(['curl','-fLsS','--retry','2','--max-time','120',f'https://github.com/NVIDIA/OpenShell/releases/download/v{VERSION}/{archive.name}','-o',str(archive)])
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=digest:
        raise SystemExit('OpenShell release checksum mismatch')
    target=STATE/'bin'/name;target.parent.mkdir(exist_ok=True)
    with tarfile.open(archive) as source:
        member=next(m for m in source if m.isfile() and Path(m.name).name==name)
        temporary=target.with_suffix('.tmp')
        temporary.write_bytes(source.extractfile(member).read());temporary.chmod(0o755)
        temporary.replace(target)
    return target


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-build',action='store_true',help='Use an already built local agent image')
    args=parser.parse_args()
    os.umask(0o077);STATE.mkdir(parents=True,exist_ok=True);STATE.chmod(0o700)
    artifacts=ARTIFACTS.get((platform.system(),platform.machine()))
    if not artifacts:raise SystemExit('Unsupported OpenShell host platform')
    for name,(arch,digest) in artifacts.items():install(name,arch,digest)
    sdk=STATE/'sdk'
    if not (sdk/'bin/python').exists():
        command([sys.executable,'-m','venv',str(sdk)])
    installed=subprocess.run([str(sdk/'bin/python'),'-c',"import importlib.metadata as m;print(m.version('openshell'))"],
        capture_output=True,text=True).stdout.strip()
    if installed!=VERSION:
        command([str(sdk/'bin/python'),'-m','pip','install','openshell=='+VERSION],stdout=subprocess.DEVNULL)
    env=dict(os.environ,OPENSHELL_TELEMETRY_ENABLED='false',GRPC_VERBOSITY='ERROR',
        OPENSHELL_LOCAL_TLS_DIR=str(STATE/'tls'),XDG_DATA_HOME=str(STATE/'data'),
        XDG_STATE_HOME=str(STATE/'state'),XDG_CONFIG_HOME=str(STATE/'config'),
        OPENSHELL_DB_URL='sqlite:'+str(STATE/'gateway.db')+'?mode=rwc')
    host='host.docker.internal';bind='127.0.0.1'
    if platform.system()=='Linux':
        bridge=json.loads(subprocess.check_output(['docker','network','inspect','bridge']))[0]
        bind=bridge['IPAM']['Config'][0]['Gateway'];ipaddress.ip_address(bind);host=bind
    gateway=STATE/'bin/openshell-gateway'
    if not (STATE/'tls/ca.crt').exists():
        command([str(gateway),'generate-certs','--output-dir',str(STATE/'tls'),'--server-san','localhost',
            '--server-san','host.docker.internal','--server-san','host.openshell.internal','--server-san',bind],env=env,stdout=subprocess.DEVNULL)
    normalize_tls_permissions(STATE/'tls')
    configuration=f'''[openshell]
version = 2
[openshell.gateway]
bind_address = "{bind}:17670"
log_level = "info"
compute_driver = "docker"
[openshell.drivers.docker]
supervisor_network_mode = "bridge"
grpc_endpoint = "https://{host}:17670"
image_pull_policy = "if_not_present"
sandbox_label = "aeion-observability"
sandbox_runtime_image = "{SANDBOX_IMAGE}"
supervisor_image = "{SUPERVISOR_IMAGE}"
allow_driver_config = true
# Run directories are host folders mounted one per sandbox; nothing else is mounted.
enable_bind_mounts = true
sandbox_pids_limit = 192
'''
    config=STATE/'gateway.toml'
    active=STATE/'gateway.active.sha256'
    configuration_hash=hashlib.sha256(configuration.encode()).hexdigest()
    changed=not active.exists() or active.read_text()!=configuration_hash
    config.write_text(configuration)
    command([str(gateway),'config','preflight','--path',str(config)],env=env)
    pid_file=STATE/'gateway.pid';running=False
    if pid_file.exists():
        pid=int(pid_file.read_text())
        running=gateway_running(pid,gateway)
        if running and changed:
            os.kill(pid,signal.SIGTERM)
            for _ in range(50):
                try:os.kill(pid,0)
                except ProcessLookupError:break
                time.sleep(.1)
            running=False
    if not running:
        log=STATE/'gateway.log'
        if log.exists() and log.stat().st_size>5000000:log.replace(log.with_suffix('.log.1'))
        with log.open('ab') as output:
            process=subprocess.Popen([str(gateway),'--config',str(config)],env=env,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
        pid_file.write_text(str(process.pid))
        time.sleep(2)
        if process.poll() is not None:raise SystemExit('OpenShell gateway failed; inspect its private local log')
    active.write_text(configuration_hash)
    # A killed qualification or a gateway restart can leave supervisor/sandbox pairs running with
    # nothing tracking them. Reap only OpenShell-labeled containers older than the safety window,
    # and only while no factory build lease is active: a live build's sandbox may legitimately
    # outlive the window. The real sandbox lifetime is bounded by the 360-second agent deadline
    # and three agents.
    try:
        removed=reap(older_than=3600,execute=True)
        if removed:print(f"Reaped {len(removed)} stale OpenShell container(s).")
    except (OSError,subprocess.CalledProcessError):
        pass
    # Linux sandboxes run as the host user so bind-mounted files stay owned by it; Docker Desktop
    # maps ownership itself, so macOS keeps a dedicated UID. Never root.
    agent_uid=os.getuid() if platform.system()=='Linux' else 10001
    if agent_uid==0:raise SystemExit('Run the bootstrap as an unprivileged user')
    if not args.skip_build:
        command(['docker','build','--build-arg',f'AGENT_UID={agent_uid}','-f',str(ROOT/'agent/Dockerfile'),'-t','aeion-openshell-agent:local',str(ROOT)])
    image_id=subprocess.check_output(['docker','image','inspect','aeion-openshell-agent:local','--format','{{.Id}}']).decode().strip()
    if not image_id.startswith('sha256:'):raise SystemExit('Agent image must have an immutable ID')
    # OpenShell admits mounts by operator labels on a Docker volume, never a raw host path. This
    # labeled volume is backed by the host work folder; sandboxes mount one run subpath each.
    work=Path(os.environ.get('AEION_WORK_DIR',ROOT/'.local/work')).resolve()
    work.mkdir(mode=0o700,parents=True,exist_ok=True);(work/'published').mkdir(mode=0o755,exist_ok=True)
    volume='aeion-openshell-work'
    labels={'openshell.ai/sandbox-attachable':'true','openshell.ai/sandbox-attachable-workspace':'default'}
    existing=subprocess.run(['docker','volume','inspect',volume],capture_output=True)
    if existing.returncode==0:
        found=json.loads(existing.stdout)[0]
        options=found.get('Options') or {}
        if options.get('device')!=str(work) or options.get('o')!='bind' or (found.get('Labels') or {})!=labels:
            raise SystemExit(f'Docker volume {volume} is not the labeled host-backed work volume; after retiring its sandboxes '
                             f'and keeping any data you need, remove it with: docker volume rm {volume}')
    else:
        command(['docker','volume','create','--driver','local','--opt','type=none','--opt','o=bind','--opt',f'device={work}',
                 *[a for k,v in labels.items() for a in ('--label',f'{k}={v}')],volume],stdout=subprocess.DEVNULL)
    # Only non-secret host routing settings; the original provider credentials stay private.
    stack=ROOT/'.local/stack.env'
    if stack.exists():
        keys=('DEMO_RELAY_URL=','AEION_RELAY_PUBLISH_IP=','OPENSHELL_AGENT_IMAGE=','OPENSHELL_ENDPOINT=','AEION_AGENT_UID=','OPENSHELL_TELEMETRY_ENABLED=')
        text=stack.read_text();lines=[l for l in text.splitlines() if not l.startswith(keys)]
        stack.write_text('\n'.join(lines)+f'\nOPENSHELL_ENDPOINT={bind}:17670\nOPENSHELL_AGENT_IMAGE={image_id}\nAEION_AGENT_UID={agent_uid}\nOPENSHELL_TELEMETRY_ENABLED=false\n');stack.chmod(0o600)
    command([str(sdk/'bin/python'),str(ROOT/'openshell/qualify.py'),'--endpoint',bind+':17670','--state',str(STATE),'--image',image_id,'--uid',str(agent_uid),'--work',str(work)],env=env)
    print('OpenShell ready; NVIDIA telemetry=false. Qualification expires after 24 hours; rerun setup to refresh.')


if __name__=='__main__':main()
