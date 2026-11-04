---
id: 035
sequence: 42
title: "Thread export for analysis"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-docs/"]
depends_on: [022, 023, 031, 020, 043]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 035 — Thread export for analysis

## Intent

Export one thread as JSON for offline analysis, with bodies and provenance but without identities beyond an opaque author id.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Define an allowlisted versioned thread-export schema.
2. Add an administrator-only bounded 0600 local export with explicit private scope.
3. Validate counts and fake-credential exclusion by schema path.

**Scope:**

- A CLI export for administrators writing to a file, never to HTTP.
- A schema with version, post, comments, votes aggregate and provenance.
- A refusal to export a private channel without an explicit flag.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The export is a local file written with 0600, and the audit log records who ran it.

This invariant and the acceptance cases belong to planned protected check `agora-035`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An administrator export validates against its versioned allowlisted schema.
- [ ] Authentication/account/session/token fields are absent; visible body text is not claimed to be anonymized.
- [ ] A private-channel export without explicit administrator authorization is refused.

**Test scenario:** Validate a seeded export by schema path and inject fake credentials into excluded account/session/token fields; do not search arbitrary visible body text for a word that may legitimately occur there.

## Out of scope

- A public API or a webhook.
- Bulk export of the whole forum.
