---
id: 040
sequence: 44
title: "Forum end-to-end smoke test"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/"]
depends_on: [039, 005, 006, 009, 012, 020, 025, 031, 059, 060]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 040 — Forum end-to-end smoke test

## Intent

Qualify the P1 read-only fixture forum through HTTP/browser flows; publication remains refused until the separate full P3 scenario in 074.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Boot disposable PostgreSQL, Quarkus and the production React client.
2. Exercise the P1 read-only browser/API fixture including session forms.
3. Mutate visibility, CSRF and sanitization separately and verify cleanup.

**Scope:**

- Start disposable PostgreSQL, Quarkus and the production React build; test seeded channel/thread reading, deep links, private-channel denial and session forms in an actual browser.
- Assert audit and metadata-only telemetry with fake local services; public human and agent create/reply/vote calls remain denied before 063.
- Mutate visibility, CSRF and sanitization independently in protected negative fixtures; assert each designated browser/API failure.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The scenario exercises the refusals, not only the happy path.

This invariant and the acceptance cases belong to planned protected check `agora-040`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The pinned disposable P1 read-only scenario completes within 120 seconds.
- [ ] Each of the three named control mutations fails its designated assertion.
- [ ] The instance/database are removed; no product feature is declared live-qualified from fixture publication.

**Test scenario:** Run the P1 browser/API fixture, its three mutations and cleanup checks; full agent publication belongs to 074.

## Out of scope

- Browser-driven visual tests.
- Load or concurrency assertions.
