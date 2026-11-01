---
id: 099
title: "VPS deployment"
area: ops
size: M
parallel: false
depends_on: [098]
owner: builder
status: proposed
---

# 099 — VPS deployment

**Goal.** Ship one compose override and a runbook that stands the forum, the supervisor and the observability stack behind TLS on a single VPS, with only the forum exposed.

## Scope

- A compose override: forum, Postgres, Langfuse stack, collector, claude-mem, Hindsight.
- Caddy with automatic TLS, the cockpit and Langfuse bound to loopback.
- A deploy script that pulls, migrates, restarts and verifies readiness.

## Out of scope

- Kubernetes, autoscaling or multi-host.
- Any deploy executed by this repository.

## Acceptance

- [ ] From a clean VPS the runbook ends with a healthy ready endpoint over HTTPS.
- [ ] Cockpit and Langfuse answer only through the tunnel or the authenticated proxy.
- [ ] The deploy script is idempotent and refuses to run without the secrets present.

## Security

Secrets are generated on the host, never committed; the firewall allows 443 and SSH only.

## Test

A dry run against a local compose project plus a shellcheck pass; the real deploy is the owner's action.
