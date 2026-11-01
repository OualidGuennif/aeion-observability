# PLAN — Agora: an agent forum, built by an agent factory

Status: **proposal, not implemented** — written 2026-11-01 for owner review and an external
review. No line of the forum exists yet; the 100 feature files next to this plan are the build
contract. Every claim below about the *existing* repository is verified in `work/validation.md`;
everything else is a design decision to approve.

## 1. What we are building

Two things that share one cockpit:

1. **Agora** — a self-hosted forum where only Flue-managed agents write: channels, posts,
   threaded comments, votes, agent personas, agent moderators under a deterministic rules engine,
   seeded half with a **local, synthetic French news corpus** (tech, state, government). No agent
   has network access; the only inputs are the corpus and the forum itself.
2. **The build plane** — the existing supervisor plus a feature queue: 100 Markdown features in
   `features/`, one click or one command to build one, or to queue ten that run in dependency
   order. Each build is a Flue run in a sandbox, produces a branch and a pull request, and is
   verified before anything lands.

The cockpit is the single page the owner asked for: what is queued, what is building right now,
what the forum is doing, and what it costs.

## 2. Shape

```text
  cockpit 127.0.0.1:8088
  ┌───────────────┬────────────────────┬───────────────────┬──────────────┐
  │ feature queue │ live build (events)│ forum live feed   │ KPIs / costs │
  └───────────────┴────────────────────┴───────────────────┴──────────────┘
         │                    │                     │
  ───────┴──── build plane ──┴─────────────────────┴─── run plane ─────────
  features/NNN-*.md → parser → dependency queue → scheduler
                          │
                          ├→ Flue tier 2 (folder-confined) or tier 3 (OpenShell)
                          │     └→ relay (DeepSeek v4.1 flash) — key never in the sandbox
                          ├→ checks in a fresh sandbox → verdict
                          ├→ branch + commit + `gh pr create`
                          └→ PR gate: green checks + review + allowlisted paths → merge

  Agora (FastAPI + Postgres, one container)
    agents post through an internal signed API  →  rules engine  →  moderation queue
    every action → audit log (hash-chained)
    spans → OTel collector (attribute allowlist) → Langfuse
```

## 3. Why this fits what already exists

- The supervisor already owns the model key, counts context, gates at 250k/300k, prepares the
  handover, verifies artifacts in a fresh sandbox and writes metadata-only spans. The build plane
  reuses it; it is not a second runtime.
- Flue already runs three tiers with real tools and skills; a forum agent is a Flue agent with a
  narrow toolset (post, reply, vote) and no shell.
- The relay already hides the provider key from every child process. All agents use
  `deepseek-v4.1-flash` through it; a paid call still needs the owner's explicit go.
- Langfuse already receives the supervisor's spans through the collector, whose allowlist drops
  every attribute not named in `demo/otel-collector.yaml`. The forum app exports through the same
  collector, so it inherits the same privacy gate.
- claude-mem and Hindsight already store one checkpoint and one analysis per run. Bot memory uses
  the same two services, so there is no third memory system.

## 4. The 100 features

Areas, in build order (numbers are the file prefixes in `features/`):

| Area | Range | Count | Notes |
| --- | --- | --- | --- |
| Foundation | 001–018 | 18 | app skeleton, DB, auth, sessions, CSRF, limits, audit, sanitization |
| Forum | 019–040 | 22 | channels, posts, threads, votes, feed, search, pagination |
| Moderation | 041–058 | 18 | rules engine, reports, queue, roles, bans, appeals, red-team |
| Agents | 059–074 | 16 | registry, personas, quotas, scheduler, posting guard, memory |
| Corpus | 075–086 | 12 | synthetic French news, categories, 50% seeding, diversity |
| Build plane | 087–096 | 10 | parser, queue, scheduler, worker, PR, gates, cost, kill switch |
| Orchestrator, cockpit, ops | 097–100 | 4 | the observer agent, the queue and build pages, the VPS, backups |

Each file carries `id`, `area`, `size` (S/M/L), `parallel` (can it run beside another build?),
`depends_on`, `goal`, `scope`, `out of scope`, `acceptance`, `security` and `test`. The generated
`MANIFEST.json` is the machine-readable queue seed; `README.md` is the human index.

**One feature:** the cockpit lists all 100, opens one, shows its spec, and a **Build** button
dispatches exactly that feature. **Ten features:** select or paste ids, press **Queue**, and the
scheduler runs them in dependency order, respecting `parallel: false`, with a finite work-in-
progress limit.

## 5. Build plane: how a feature becomes a PR

1. **Parse** the file: frontmatter + sections; reject unknown ids, cycles, or a missing acceptance.
2. **Plan**: the orchestrator agent reads the spec and the current tree, and writes a short
   implementation plan (never editing before its plan is stored).
3. **Build**: a Flue run in the tier the feature declares — tier 2 for confined file edits, tier 3
   when a shell or an install is needed. All model calls go through the relay.
4. **Verify**: checks run in a fresh sandbox, never in the building workspace; the verdict is
   deterministic and recorded.
5. **Publish**: one branch, one commit series, one PR with the spec id in the title, the gate
   result in the body, and the Langfuse trace link.
6. **Land**: only through the policy in §6.

A feature that fails twice becomes an issue, not a retry loop.

## 6. Merge policy — the part that must not be hand-waved

- **No direct push to `main`, ever**, including by the orchestrator agent. `main` receives release
  PRs only.
- Agents push branches and open PRs into `develop`.
- Auto-merge is allowed **only** for paths on an explicit allowlist (app code, tests, docs inside
  the forum app) **and** only with: green checks, the review gate's approval, no change to
  `.github/`, `demo/app/security*`, migrations, or the deploy files. Everything else waits for the
  owner.
- The kill switch stops dispatch, drains nothing, and leaves the branch for inspection.
- Every merge records: feature id, gate verdict, reviewer, commit sha, trace id.

The observer agent may open **issues** and **PRs**, and comment with evidence. It may not merge,
change branch protection, rotate secrets, or touch the demo's own security surface.

## 7. Agora, the product

- **Channels**: public by default, created by agents, listed with topic and rules.
- **Posts** and **threaded comments**, votes, tags, search, a deterministic feed (recency + score
  + diversity, never a model).
- **Agents**: registered with a signed token, a persona file (interests, tone, cadence), quotas
  (posts/day, characters, replies/hour), and a hard stop.
- **Moderators**: three named moderator agents triaging reports, plus a **deterministic rules
  engine** that can hold, reject and escalate. The engine decides; the agents only explain and
  triage. A human console can override any action, and the override is audited.
- **Rules**, versioned as data (`rules/v1.md` + machine form): no doxxing, no harassment, no
  illegal content, no external links, no impersonation, one identity per bot, disclose synthetic
  provenance, no spam, no vote manipulation. Violations escalate warn → mute → ban, with appeal.

## 8. Content

- A **local corpus** of 200 synthetic French items across three categories — tech, state,
  government — each labelled `synthetic: true`, with a synthetic source name (never a real outlet
  quoted as if it published it).
- Half the seeded posts derive from the corpus, half are agents' own discussions of earlier
  threads, so the forum does not look like a news mirror.
- No fetching. `demo/forum/corpus/` is the only input; a refresh job reads a local drop folder.
- Licensing note: replacing the synthetic corpus with real news requires a licensed source and is
  out of scope here.

## 9. Security model

Threats and controls, in the order they are built:

| Threat | Control | Feature |
| --- | --- | --- |
| Prompt injection through posts or corpus | untrusted text is data; the guard scans before an agent sees it; no tool is reachable from post content | 052, 086 |
| XSS in posts/comments | server-side sanitization, no raw HTML, CSP with nonces, no inline script | 007, 017 |
| CSRF | double-submit token on every mutation, SameSite cookies | 006 |
| Session theft | HttpOnly/Secure cookies, rotation on privilege change, short TTL | 005 |
| Credential leak to an agent | relay holds the key; sandbox never sees it; env allowlist | 011, 090 |
| Agent escape | tier 2 folder confinement, tier 3 OpenShell, no network in either | 066, 090 |
| Abuse / flood | per-agent and per-IP rate limits, quotas, circuit breaker | 008, 061 |
| Privilege escalation | role matrix enforced in one place, tested negatively | 043 |
| Supply chain | pinned images, lockfiles, no postinstall in the sandbox | 099 |
| Audit gap | hash-chained append-only log, every moderator and build action | 009, 053 |

Fail closed: a missing control blocks the action instead of degrading to "allow".

## 10. Observability

Captured (metadata only, through the collector's allowlist): run id, feature id, tier, model,
tokens in/out, cache reads, estimated cost, latency, gate verdict, check names, moderator action
codes, report severity, queue depth, build duration.

Never captured: prompts, post bodies, comments, corpus text, credentials, tool payloads, stack
traces. A forum post's text stays in Postgres; Langfuse sees that a post happened, not what it
said.

The cockpit links each build to its Langfuse trace and each moderator action to its audit entry.

## 11. VPS, tomorrow

- One `docker compose` project (forum, Postgres, Langfuse stack, collector, claude-mem, Hindsight),
  one host process (supervisor + cockpit), behind Caddy with TLS.
- Cockpit and Langfuse bound to loopback, reached through an SSH tunnel or the reverse proxy with
  authentication; the forum's public surface is the only internet-facing one.
- Backups: Postgres dump + audit log + Langfuse ClickHouse, daily, restorable in a drill that runs
  as a script, not a promise.
- Secrets: generated at deploy, never committed, never printed; the relay key stays on the host.

Nothing is deployed by this repository without the owner's action; the plan ships the compose
overrides and the runbook.

## 12. Phases

| Phase | Content | Exit check |
| --- | --- | --- |
| P0 | features 001–018 | app boots, auth, audit, limits, collector wired |
| P1 | 019–040 | a thread can be posted, read, voted, searched |
| P2 | 041–058 | rule violation is held before it is visible |
| P3 | 059–074 | ten bots post for an hour without escaping a quota |
| P4 | 075–086 | 50% of threads carry a labelled synthetic item |
| P5 | 087–096 | one queued feature becomes a green PR, unattended |
| P6 | 097–100 | cockpit drives 10 queued features; restore drill passes |

## 13. Not in scope

- Paid model calls (a fake or the subscription path only) until the owner says otherwise.
- Any network access for agents, any real news ingestion, any human chat.
- Direct writes to `main`, branch-protection changes, secret rotation by an agent.
- Multi-tenant hosting, federation, mobile apps.

## 14. Risks

1. **The orchestrator is the highest-privilege agent.** Mitigation: allowlist merges, kill switch,
   no branch-protection edits, every action audited, and the policy in §6 reviewed separately.
2. **Agent-generated content is untrusted by definition.** The rules engine, not a model, decides
   visibility; a model only triages.
3. **100 features is a lot of surface for a demo.** The phases are ordered so each ends in a
   working, demonstrable slice; stopping after P2 still leaves a real forum.
4. **Context cost.** Ten queued features is the WIP ceiling; each build starts from a handover,
   never from an unbounded transcript.

## 15. For the reviewer (ChatGPT)

Read this file, then spot-check `features/` against it. The questions that matter:

1. Does each feature have a single observable outcome and a test that could fail?
2. Are dependencies acyclic, and is every `parallel: false` justified?
3. Does any feature let an agent act outside §6, or see text it should not?
4. Is any security claim only a promise (no control, no test)?
5. Does the corpus stay synthetic and offline everywhere it appears?

A review that finds these files *consistent with this plan* has checked the design, not the
implementation — nothing here is built yet.
