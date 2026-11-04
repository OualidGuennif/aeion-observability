"""Native Chromium sandbox proof, with trusted input only and no product/host mounts.

This qualifies one browser boundary, not a React feature or factory activation.
See work/chromium-security-2026-11-03.md for the boundary and primary sources.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'sha256:86d317a94a95fba3bf9e773e02ed308c72e11f0d17a3b4e214f8ae0594d7986f'
PROFILE = ROOT / 'demo/factory/checker-tools/browser-seccomp.json'
PROFILE_SHA = '774438438b227aba0fafed72591e37bfc68f5718585cc1da28d8d8f2ac53eaea'
SCRIPT = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { chromium } = require('playwright');
(async () => {
  assert.notEqual(process.getuid(), 0);
  assert.equal(process.env.AEION_BROWSER_SENTINEL, undefined);
  assert.equal(fs.existsSync('/var/run/docker.sock'), false);
  const status = fs.readFileSync('/proc/self/status', 'utf8');
  assert.match(status, /^CapEff:\s+0+$/m);
  assert.match(status, /^NoNewPrivs:\s+1$/m);
  await assert.rejects(fetch('http://1.1.1.1', { signal: AbortSignal.timeout(2000) }));
  const browser = await chromium.launch({ chromiumSandbox: true, channel: 'chromium' });
  try {
    const page = await browser.newPage();
    await page.goto('chrome://sandbox');
    const sandbox = await page.locator('body').innerText();
    for (const label of ['PID namespaces', 'Network namespaces', 'Seccomp-BPF sandbox',
                         'Seccomp-BPF sandbox supports TSYNC']) {
      assert.match(sandbox, new RegExp(label + '\\s+Yes'));
    }
    assert.match(sandbox, /Layer 1 Sandbox\s+Namespace/);
    await page.goto('about:blank');
    await page.setContent('<!doctype html><button id="probe">Ready</button>');
    await page.locator('#probe').click();
    assert.equal(await page.locator('#probe').innerText(), 'Ready');
    console.log(JSON.stringify({ browser: browser.version(), sandbox: {
      namespace: true, pid: true, network: true, seccomp_bpf: true, tsync: true,
      yama_broker: /Ptrace Protection with Yama LSM \(Broker\)\s+Yes/.test(sandbox),
      yama_non_broker: /Ptrace Protection with Yama LSM \(Non-broker\)\s+Yes/.test(sandbox)
    }, non_root: true, capabilities: 'none', no_new_privileges: true,
       external_network: 'denied', docker_socket: 'absent', host_environment: 'absent',
       browser_interaction: 'passed' }));
  } finally { await browser.close(); }
})().catch((error) => {
  console.error('BROWSER_QUALIFICATION_FAILED', String(error.message).slice(0, 2000));
  process.exitCode = 1;
});
'''


def main():
    if hashlib.sha256(PROFILE.read_bytes()).hexdigest() != PROFILE_SHA:
        raise ValueError('browser_profile_changed')
    name = 'aeion-browser-probe-' + uuid.uuid4().hex[:12]
    environment = {'PATH': '/usr/local/bin:/usr/bin:/bin',
                   'AEION_BROWSER_SENTINEL': 'synthetic-must-not-enter-container'}
    flags = ['docker', 'run', '--rm', '-i', '--name', name, '--network', 'none',
             '--read-only', '--user', '1000:1000', '--cap-drop', 'ALL',
             '--security-opt', 'no-new-privileges', '--security-opt', 'seccomp=' + str(PROFILE),
             '--tmpfs', '/tmp:rw,exec,nosuid,nodev,mode=1777,size=1g', '--shm-size', '256m',
             '--memory', '3g', '--cpus', '2', '--pids-limit', '512',
             '-e', 'HOME=/tmp', '-w', '/opt/aeion-checker', IMAGE, 'node', '-']
    try:
        result = subprocess.run(flags, input=SCRIPT, capture_output=True, text=True,
                                timeout=120, env=environment)
        if result.returncode:
            folder = Path(tempfile.mkdtemp(prefix='aeion-chromium-failed-', dir='/private/tmp'))
            (folder / 'diagnostic.log').write_text(result.stderr[-8000:])
            raise RuntimeError('browser_qualification_failed: ' + str(folder / 'diagnostic.log'))
        proof = json.loads(result.stdout)
    finally:
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30,
                       env={'PATH': environment['PATH']})
    proof.update(kind='isolated_chromium_boundary', image_id=IMAGE, profile_sha256=PROFILE_SHA,
                 host_mounts=False, host_ports=False, product_modified=False,
                 feature_qualified=False, real_model_requests=0)
    folder = Path(tempfile.mkdtemp(prefix='aeion-chromium-proof-', dir='/private/tmp'))
    evidence = folder / 'proof.json'
    evidence.write_text(json.dumps(proof, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': 'passed', 'evidence': str(evidence), **proof}))


if __name__ == '__main__':
    main()
