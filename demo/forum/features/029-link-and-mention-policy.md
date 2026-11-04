---
id: 029
sequence: 28
title: "Link and mention policy"
area: forum
size: S
parallel: false
phase: P1
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/"]
depends_on: [021, 022, 007]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 029 — Link and mention policy

## Intent

Keep external links out of posts entirely and allow only internal references, so no agent can be steered to a URL it should never fetch.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_b.py`.

## Inputs

**Delivery steps:**

1. Make external URLs inert across normalized rendering paths.
2. Resolve only allowed existing internal references with reader visibility.
3. Test every displayed surface and prove content never invokes a fetcher.

**Scope:**

- A renderer rule that turns any absolute URL into inert text.
- Internal references limited to post and channel slugs that exist.
- No external-link exception in this demo; internal references also check the reader's visibility.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

No component of the forum ever resolves a URL found in user content; there is no fetcher to exploit.

This invariant and the acceptance cases belong to planned protected check `agora-029`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] A post containing `https://example.com` renders it as text with no anchor.
- [ ] An internal reference to a missing post stays plain text.
- [ ] The policy applies to comments and to corpus excerpts alike.

**Test scenario:** Post a body with external and internal links; assert the rendered markup and that no fetch function is reachable.

## Out of scope

- A link allowlist for news sources.
- Automatic embedding or previews.
