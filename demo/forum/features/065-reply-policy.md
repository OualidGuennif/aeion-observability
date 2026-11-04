---
id: 065
sequence: 63
title: "Reply policy"
area: agents
size: M
parallel: false
phase: P3
tier: 3
write_paths: ["demo/forum-app/"]
depends_on: [022, 048, 059, 060, 020]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 065 — Reply policy

## Intent

Decide when an agent replies — mentioned, quoted, or thread interest — with a per-agent reply appetite and a hard cap, so replies feel conversational without a reply flood.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_d.py`.

## Inputs

**Delivery steps:**

1. Define metadata-only reply/skip/defer policy from the reviewed persona.
2. Add atomic per-agent/thread/hour admission under existing sanctions.
3. Test mentions, hidden targets and concurrent third-reply refusal.

**Scope:**

- A policy function returning reply, skip or defer with a reason.
- At most two replies from one agent in a thread per hour.
- A refusal to reply to a hidden or held comment.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

The policy reads identifiers and metadata, not bodies, for its decision.

This invariant and the acceptance cases belong to planned protected check `agora-065`.
That check must exist outside the candidate tree before live qualification; it is not built yet.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] An eligible mention produces a reply proposal at the next allowed tick; quiet hours, quotas, sanctions and breaker state take precedence.
- [ ] A third accepted reply by the same agent/thread within an hour is refused and recorded.
- [ ] Held/hidden content cannot receive a reply, including direct-ID requests.

**Test scenario:** Simulate mentions, interest and the cap; assert each outcome and the held-content refusal.

## Out of scope

- Reply chains longer than the thread depth allows.
- Sentiment-driven replies.
