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

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'.local/openshell'
VERSION='0.1.5'
ARTIFACTS={
 ('Darwin','arm64'):{'openshell':('aarch64-apple-darwin','48d6f4b4a222dc0a120ee4d6a677cb931bcc57f9ac54aefb101588f99c9c7642'),'openshell-gateway':('aarch64-apple-darwin','8e6fd1b05999709a9042ec83fcd902e062507af3e817f28bcda181fb93b42e7a')},
 ('Linux','x86_64'):{'openshell':('x86_64-unknown-linux-musl','ca1ad6e6fbb4a6cd407e95763391b8ecff02912e7d9c467e7ca22696fe80af69'),'openshell-gateway':('x86_64-unknown-linux-gnu','6ed6a6aff420c65250082cc1db48dc6271a6f5eec0e0068133566ffae4aa788b')},
 ('Linux','aarch64'):{'openshell':('aarch64-unknown-linux-musl','30c949b4ac07a9c8245c1248eb82e4eb241615134fcabf3c9bf30dec7d00addf'),'openshell-gateway':('aarch64-unknown-linux-gnu','125f9f43b8d06da8280c78089904a6da2faa7c4cb03f82db3b31fc980cf6c62d')},
}
SANDBOX_IMAGE='ghcr.io/nvidia/openshell/sandbox:0.1.5@sha256:e9adf9ecde328122414ad2ee8c6fc5d5b389e4cf168daf4357c46f5a77d55851'
SUPERVISOR_IMAGE='ghcr.io/nvidia/openshell/supervisor:0.1.5@sha256:fabcd01f656e9d23df4386f82e80b4f48b90f3452d7d5c58889007643a069161'


def command(args,**kwargs):
    return subprocess.run(args,check=True,**kwargs)


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
        command([str(sdk/'bin/python'),'-m','pip','install','openshell==0.1.5'],stdout=subprocess.DEVNULL)
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
    # Linux sandboxes run as the host user so bind-mounted files stay owned by it; Docker Desktop
    # maps ownership itself, so macOS keeps a dedicated UID. Never root.
    agent_uid=os.getuid() if platform.system()=='Linux' else 10001
    if agent_uid==0:raise SystemExit('Run the bootstrap as an unprivileged user')
    if not args.skip_build:
        command(['docker','build','--build-arg',f'AGENT_UID={agent_uid}','-f',str(ROOT/'agent/Dockerfile'),'-t','aeion-openshell-agent:local',str(ROOT)])
    image_id=subprocess.check_output(['docker','image','inspect','aeion-openshell-agent:local','--format','{{.Id}}']).decode().strip()
    if not image_id.startswith('sha256:'):raise SystemExit('Agent image must have an immutable ID')
    # Only non-secret host routing settings; the original provider credentials stay private.
    stack=ROOT/'.local/stack.env'
    if stack.exists():
        keys=('DEMO_RELAY_URL=','AEION_RELAY_PUBLISH_IP=','OPENSHELL_AGENT_IMAGE=','OPENSHELL_ENDPOINT=','AEION_AGENT_UID=','OPENSHELL_TELEMETRY_ENABLED=')
        text=stack.read_text();lines=[l for l in text.splitlines() if not l.startswith(keys)]
        stack.write_text('\n'.join(lines)+f'\nOPENSHELL_ENDPOINT={bind}:17670\nOPENSHELL_AGENT_IMAGE={image_id}\nAEION_AGENT_UID={agent_uid}\nOPENSHELL_TELEMETRY_ENABLED=false\n');stack.chmod(0o600)
    command([str(sdk/'bin/python'),str(ROOT/'openshell/qualify.py'),'--endpoint',bind+':17670','--state',str(STATE),'--image',image_id,'--uid',str(agent_uid)],env=env)
    print('OpenShell ready; NVIDIA telemetry=false. Qualification expires after 24 hours; rerun setup to refresh.')


if __name__=='__main__':main()
