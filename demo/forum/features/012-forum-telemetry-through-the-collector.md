---
id: 012
sequence: 12
title: "Forum telemetry through the collector"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [001, 011, 009]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 012 — Forum telemetry through the collector

## Intent

Export forum spans to the existing OTel collector with the same attribute allowlist, so the forum appears in Langfuse without adding a second pipeline.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Construct bounded metadata-only forum spans using the existing collector.
2. Keep export disabled until all OTLP content surfaces pass canary checks.
3. Verify stored-backend readback and bounded failure during collector outage.

**Scope:**

- Use the existing collector through a bounded OTLP/HTTP exporter; export remains disabled until all OTLP surfaces are qualified.
- Construct span names/routes/status from fixed code catalogs; remove content-bearing events/link attributes/resource fields and scrub log bodies before export.
- Enforce an attribute allowlist in production, not only development, and prove collector behavior with stored-backend readback; a needed collector edit is protected maintainer work.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

No content or arbitrary label reaches telemetry. Attribute filtering alone is insufficient. Export stays off if end-to-end privacy qualification is missing.

This invariant and the acceptance cases belong to planned protected check `agora-012`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A metadata-only synthetic request appears through the configured observations readback with its opaque run identity.
- [ ] Fake-secret/content canaries in attributes, names, status messages, events, links, resources and logs are absent from stored backend records.
- [ ] Collector failure leaves the request available; dropped/pending telemetry is recorded as incomplete, never successful zero usage.

**Test scenario:** Inject unique fake canaries into every OTLP surface and compare stored readbacks; use a fake backend for unit tests and real local-stack readback for qualification.

## Out of scope

- Content, identifiers of posts, or any user text in telemetry.
- A new collector or a new Langfuse project.
