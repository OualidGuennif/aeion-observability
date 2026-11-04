---
id: 041
sequence: 19
title: "Rules as versioned data"
area: moderation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/"]
depends_on: [002, 014]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 041 — Rules as versioned data

## Intent

Keep the forum rules in one reviewed file that renders to prose and to a machine form, so a moderation decision always cites a version that can be re-read.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

**Delivery steps:**

1. Define immutable rule codes, prose, severity and retained versions.
2. Generate the machine form and safe React-readable rules data from one file.
3. Test shared hashes and refusal of missing or removed referenced codes.

**Scope:**

- `demo/forum-app/src/main/resources/rules/rules.yaml` with stable codes, severities and the prose for each rule.
- A renderer that produces the public rules page and a hash of the version.
- A check that every code used by the engine exists in the file.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The rules file is code-reviewed like code; no runtime write path exists.

This invariant and the acceptance cases belong to planned protected check `agora-041`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The rendered page and the machine form come from the same file and hash.
- [ ] A rule code referenced by code but missing from the file fails the build.
- [ ] Changing a rule changes the hash and the version shown on new posts.

**Test scenario:** Render, hash, then remove a referenced code and assert the check fails.

## Out of scope

- Editing rules through the web interface.
- Per-channel rule overrides beyond a channel's own text.
