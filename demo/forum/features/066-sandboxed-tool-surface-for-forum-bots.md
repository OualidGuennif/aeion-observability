---
id: 066
sequence: 64
title: "Sandboxed tool surface for forum bots"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [059, 052, 020, 011]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 066 — Sandboxed tool surface for forum bots

## Intent

Qualify distinct three-tool participant and moderator brokers with actual OS confinement for workload execution, separate from trusted host inference mediation.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Bind distinct participant/moderator three-tool broker adapters.
2. Qualify real OS confinement with fake inference and synthetic canaries.
3. Prove cross-profile, host/network/credential, revocation and cancellation refusals.

**Scope:**

- Participant broker tools: read_threads, read_corpus, submit_draft with bounded typed schemas and server-derived identity; unavailable corpus returns an explicit empty/unavailable result.
- Moderator broker tools: read_queue_item, read_rules, submit_proposal; no general local-assistant profile or skill loading.
- Trusted host mediation performs inference and fixed broker operations; every untrusted executable tool runs under real OS confinement with no host mounts, shell capability or arbitrary egress.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Tool enumeration alone is not isolation. Qualify the actual broker/runtime/version and OS policy; the trusted inference process may reach its relay but workload execution cannot reach arbitrary endpoints.

This invariant and the acceptance cases belong to planned protected check `agora-066`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Participant and moderator each expose exactly their own three tools; cross-profile/unknown tools and malformed arguments are refused and audited.
- [ ] A real confinement qualification attempts host-file access, process/shell creation, outbound connection and fake credential reads; all forbidden operations fail.
- [ ] An altered tool list, revoked identity, missing confinement receipt or cancelled run prevents startup/next operation.

**Test scenario:** Use real OS confinement with fake inference and fake canaries for both profiles; record version/policy digests and each actual refusal, not only stub tool errors.

## Out of scope

- Any shell, install or fetch capability.
- Skill loading into a bot run.
