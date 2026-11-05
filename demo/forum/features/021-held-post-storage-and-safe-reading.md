---
id: 021
sequence: 23
title: "Held post storage and safe reading"
area: forum
size: M
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [007, 019, 020, 017]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 021 — Held post storage and safe reading

## Intent

Provide internal held-by-default post storage and safe reads; public publication remains disabled until 063 owns admission.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Add held post storage using normalized Markdown and sanitized HTML.
2. Expose safe authorized reads, with no live publication endpoint.
3. Prove held defaults, fixture rendering and refusal of public creation.

**Scope:**

- Store channel, server-derived author, bounded title, normalized plain Markdown, sanitized HTML, provenance, status and timestamps; never original transport bytes.
- Only an internal repository primitive inserts a held record; no public/session compose endpoint is introduced here.
- Render visible records through the shared visibility helper; disposable fixtures may create explicitly labelled visible records.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Stored source is normalized Markdown, not trusted HTML. Only sanitized HTML is rendered. Original transport bytes are not retained. Live visibility changes require the later admission/moderation commands.

This invariant and the acceptance cases belong to planned protected check `agora-021`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A stored fixture contains normalized source and exactly the sanitizer-produced HTML, with no original transport-byte field.
- [ ] Unadmitted records default to held and are absent from feed, search and direct public reads.
- [ ] A public create request before qualified pipeline installation is refused and writes no record.

**Test scenario:** Insert held and disposable visible fixtures; assert normalized storage, safe rendering, filtered reads and refusal of public writes.

## Out of scope

- Attachments, images or polls.
- Drafts for humans.
