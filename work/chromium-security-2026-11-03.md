# Chromium checks and security — 2026-11-03

The owner requested continued Chrome/security research while the factory is completed.
This is a local evaluator boundary qualification, not proof of the React application,
an implemented feature, model quality or factory activation.

## Verified upstream behavior

- [Playwright Docker](https://playwright.dev/docs/docker) provides browser binaries/system
  libraries but requires a separately installed matching Playwright package. It recommends
  a separate non-root user and seccomp for untrusted sites. Its image is intended for testing;
  this work does not qualify unrestricted web browsing.
- [BrowserType.launch](https://playwright.dev/docs/api/class-browsertype) exposes the
  `chromiumSandbox` option. The protected check sets it explicitly to `true`.
- [Chromium's user namespace guidance](https://chromium.googlesource.com/chromium/src/%2B/main/docs/security/apparmor-userns-restrictions.md)
  explains that disabling the sandbox removes critical protections. We did not use
  `--no-sandbox`, a privileged container, `SYS_ADMIN`, host IPC or AppArmor unconfined.
- [Docker seccomp](https://docs.docker.com/engine/security/seccomp/) is a default-deny
  syscall allowlist. Namespace calls are normally restricted. Current rules also protect
  against dangerous syscall families such as `io_uring`, `bpf`, keyrings and `AF_ALG` sockets.
  Replacing the default with an old browser example can silently lose newer protections.

These are primary sources, checked 2026-11-03. The exact locally derived profile is pinned
to [Moby profiles commit 4b8214fc](https://github.com/moby/profiles/blob/4b8214fc4971e06172938a1f1554ccff6647ee80/seccomp/default.json),
not claimed to be byte-identical to Docker Engine's built-in profile.

## Local design and measured results

The trusted checker toolchain contains Java25, pinned public React/TypeScript/Vite/Vitest
packages and Playwright1.64.1. Its Dockerfile uses immutable upstream image digests and
`npm ci --ignore-scripts` with a committed lockfile, without product source or credentials.
Locally inspected image: `sha256:86d317a94a95fba3bf9e773e02ed308c72e11f0d17a3b4e214f8ae0594d7986f`.

With non-root execution, all capabilities dropped, read-only root, no-new-privileges and
network none, Chromium initially refused startup with no usable sandbox. Allowing the
namespace syscalls advanced startup but chroot was still denied. The dedicated browser
profile adds only `clone`, `setns`, `unshare` and `chroot` allow rules to the pinned modern
profile. It retains the other rules and kernel capability checks. No daemon or host security
setting changed. Hashes/provenance and the upstream license are in
[checker-tools](../demo/factory/checker-tools/browser-seccomp-source.json).

Chromium156.0.8078.80 then reported namespace isolation, PID/network namespaces,
Seccomp-BPF and TSYNC enabled in `chrome://sandbox`. External TCP failed. Yama ptrace
protection was **not enabled**; do not claim it is. User namespaces add kernel attack
surface, so this is an explicit compatibility/security trade-off inside a bounded disposable
Docker VM container, not a claim of immunity to kernel/browser vulnerabilities.

## Acceptance and remaining work

Reproduce with `demo/.local/venv/bin/python demo/tests/qualify_chromium.py` after provisioning
the pinned checker image. The probe uses trusted inline input, no product/host mounts,
no published port or provider key. It verifies the sandbox diagnostics, non-root identity,
zero effective capabilities, no-new-privileges, denied network and a simple browser action.
Only metadata is written to a fresh private temporary proof folder.
The repeated probe passed and recorded
`/private/tmp/aeion-chromium-proof-cb60uewh/proof.json`. The isolated public checker lockfile
also passed `npm audit --package-lock-only` with zero known vulnerabilities on 2026-11-03;
metadata proof: `/private/tmp/aeion-public-checker-audit-gvu60zpc/proof.json`. This is a dated
registry result, not a guarantee about browser/kernel vulnerabilities or untested product code.

Do not run arbitrary candidate Node configuration in the protected browser verifier.
Compilation/tests must finish and their container must be removed before a fresh verifier
starts with read-only static output and supervisor-owned finite assertions. In particular,
the absent Yama protection is a reason to keep untrusted same-UID Node processes out of
that verifier. Candidate Java API execution belongs in another isolated container with a
disposable PostgreSQL database, without operator data or external network.

The image and browser boundary are now available locally. The React build/browser/API
adapter, negative controls and actual product acceptance still need qualification before
this becomes a runtime feature check. No factory activation receipt follows from this probe.
