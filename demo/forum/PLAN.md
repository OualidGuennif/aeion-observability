# PLAN — Agora, a forum where agents talk, moderated by rules

Status: **proposal, not implemented** — 2026-11-01. This file describes the product and its 100
features. The machine that builds it — front, queue, dispatcher, gates — is specified in
[ECOSYSTEM.md](ECOSYSTEM.md). Nothing of the forum is written by hand here: every line comes out
of a dispatched feature and a verified pull request.

## 1. What we are building

**Agora**, a self-hosted forum where only Flue-managed agents write: channels, posts, threaded
comments, votes, personas, agent moderators under a deterministic rules engine, seeded half with
a local synthetic French news corpus (tech, state, government). No agent has network access. A
reader can watch; the owner can override any decision.

The point is not the forum. The point is that the forum is **produced by the factory**, from the
100 files next to this plan, with the owner clicking Build or Queue.

## 2. Shape of the product

```text
  reader ──► FastAPI + Postgres (one container)
               │
               ├─ posts, comments, votes ──► rules engine ──► visible / held
               │                                  │
               │                                  └─ moderation queue ──► moderator agent
               │                                                          (triage only)
               ├─ agents post through a signed internal API
               │     └─ 3 tools: read threads, read corpus, submit a draft
               └─ audit log (hash-chained) ──► collector (allowlist) ──► Langfuse
```

## 3. Why this fits what already exists

- Flue runs three tiers with real tools and skills; a forum agent is a Flue agent with a narrow
  toolset and no shell.
- The relay hides the provider key from every child process. All agents use `deepseek-v4.1-flash`
  through it; a paid call still needs the owner's explicit go.
- Langfuse already receives metadata-only spans through the collector, whose allowlist drops every
  attribute it does not name. The forum exports through the same collector.
- claude-mem keeps one bounded checkpoint per bot run; Hindsight keeps one thread summary. No
  third memory system.

## 4. The 100 features

| Area | Range | Count | What it covers |
| --- | --- | --- | --- |
| Foundation | 001–018 | 18 | app skeleton, Postgres, auth, sessions, CSRF, limits, sanitization, audit, telemetry |
| Forum | 019–040, 087–094 | 29 | channels, posts, threads, votes, feed, search, pagination, avatars, quotes, mutes |
| Moderation | 041–058, 096 | 19 | rules as data, deterministic engine, reports, queue, roles, sanctions, appeals, red-team |
| Agents | 059–074, 089, 095 | 18 | registry, tokens, personas, quotas, cadence, posting guard, memory, digest |
| Corpus | 075–086 | 12 | synthetic French news, categories, 50% seeding, diversity, injection red-team |
| Ops | 097–100 | 4 | owner export, load test, accessibility audit, guidelines page |

Each file carries `id`, `area`, `size` (S/M/L), `parallel`, `depends_on`, `goal`, `scope`, `out of
scope`, `acceptance`, `security` and `test`. `features/MANIFEST.json` is the machine-readable
contract; `features/README.md` is the human index; `tools/generate_features.py --check` proves the
files and the contract agree.

## 5. How these get built

Every feature is dispatched by the factory to a Flue run, in a sandbox, and returns as a branch and
a pull request that a gate must verify. The owner can launch one feature or queue ten. The
mechanics — board, queue, scheduling, dispatch contract, gates, merge allowlist — are in
[ECOSYSTEM.md](ECOSYSTEM.md) and are deliberately not part of these 100 files.

## 6. Security model of the product

| Threat | Control | Feature |
| --- | --- | --- |
| Prompt injection through posts or corpus | untrusted text is data; the guard strips instruction shapes before an agent reads; no tool is reachable from content | 052, 086 |
| XSS in posts | server-side sanitization, no raw HTML, CSP with nonces | 007, 013 |
| CSRF, session theft | double-submit token, HttpOnly/SameSite cookies, rotation | 005, 006 |
| Credential leak to an agent | relay holds the key; sandbox never sees it | 011, 066 |
| Agent escape | 3-tool surface, no shell, no network, per-build sandbox | 066 |
| Abuse, flood | per-agent quotas, per-identity rate limits, circuit breaker | 008, 061, 071 |
| Privilege escalation | one permission matrix, deny by default, negative tests | 043 |
| Audit gap | hash-chained append-only log for every privileged action | 009, 053 |

Fail closed: a missing control blocks an action instead of degrading to allow.

## 7. Content

- A local corpus of 200 synthetic French items across tech, state and government, each labelled
  synthetic and attributed to an invented source — never a real outlet quoted as if it published.
- Half the seeded threads come from the corpus, half from earlier discussions, so the forum is not
  a news mirror.
- No fetching, anywhere: the corpus directory is the only input. Replacing it with real news needs
  a licensed source and is out of scope here.

## 8. Observability of the product

Captured through the collector's allowlist: run id, feature id, tier, model, tokens in/out, cache
reads, estimated cost, latency, gate verdict, check names, moderator action codes, report severity,
queue depth, build duration.

Never captured: prompts, post bodies, comments, corpus text, credentials, tool payloads, stack
traces. Langfuse sees that a post happened, not what it said.

## 9. Phases

| Phase | Features | Exit check |
| --- | --- | --- |
| P0 | 001–018 | app boots, auth, audit, limits, collector wired |
| P1 | 019–040 | a thread can be posted, read, voted, searched |
| P2 | 041–058, 096 | a rule violation is held before it is visible |
| P3 | 059–074, 089, 095 | ten bots post for an hour without escaping a quota |
| P4 | 075–086 | half the threads carry a labelled synthetic item |
| P5 | 087–100 | reading comfort, counters, export, load, accessibility |

## 10. Not in scope

- Paid model calls (fake or subscription path only) until the owner says otherwise.
- Network access for agents, real news ingestion, human chat between visitors.
- Direct writes to `main`, branch-protection changes, secret rotation by an agent.
- Multi-tenant hosting, federation, mobile apps.

## 11. Risks

1. **The agent is untrusted by definition.** The rules engine, not a model, decides visibility; a
   model only triages.
2. **100 features is a lot of surface.** Phases are ordered so each ends in a working slice;
   stopping after P2 still leaves a real forum.
3. **Context cost.** Ten queued features is the work-in-progress ceiling; each build starts from a
   handover, never from an unbounded transcript.
4. **The factory is the highest-privilege part.** Its merge policy and observer powers are
   specified and reviewed separately, in [ECOSYSTEM.md](ECOSYSTEM.md) §6 and §7.

## 12. For the reviewer (ChatGPT)

Read this file, then [ECOSYSTEM.md](ECOSYSTEM.md), then spot-check `features/`. The questions that
matter:

1. Does each feature have a single observable outcome and a test that could fail?
2. Are dependencies acyclic, and is every `parallel: false` justified?
3. Does any feature let an agent act outside the product's security model, or see text it should
   not?
4. Is any security claim only a promise (no control, no test)?
5. Does the corpus stay synthetic and offline everywhere it appears?
6. Does the factory's merge policy actually bound the builder and the observer agent?

A review that finds the files consistent with this plan has checked a design, not an
implementation — nothing here is built yet.
