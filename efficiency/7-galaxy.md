# Phase 7 — Galaxy: memory, decisions, and a system that improves itself

> *Constellations drift into a galaxy: billions of small rules, one shape. The shape here is a
> repository that remembers what it learned, records why it decided, and gets cheaper every week.*

**In one line:** retrospectives turn sessions and reviews into rules, hooks and skills; an
optional Decisions API records and serves decisions; an optional memory service recalls what
mattered — and three numbers tell you whether any of it works.

> **Agent:** enter plan mode. Everything in this phase is optional and **off by default**. Propose
> turning on one piece at a time, with its cost and its privacy impact.

## Hindsight: learning from the sessions

Every coding session leaves a transcript (Claude Code keeps them locally, under
`~/.claude/projects/<project>/`). The skill `retro` reads the week's sessions and pull-request
comments and extracts four kinds of lesson:

| Lesson | Becomes |
| --- | --- |
| an error the agent repeated (a wrong command, a missed check) | a hook rule (`hookify`) or a line in a skill's red flags |
| a correction a human made twice | a hook if a regex can see it, otherwise a skill step |
| a stated preference (naming, style, UI, architecture) | a line in `owner-preferences.md` with its source |
| a procedure redone by hand | a new skill, drafted and evaluated with `skill-creator` |

It opens one pull request with the lessons; the middle loop reviews it like any other change.

**A memory service, if you want recall across sessions:** for example Hindsight
(`vectorize-io/hindsight`, MIT), which *retains* facts and experiences from conversations,
*recalls* them by combined vector, keyword, graph and time search, and *reflects* to form mental
models. It installs as Claude Code hooks (recall on each prompt, retain at the end). It stores
tool calls by default — keep it off for repositories with sensitive data, and never point it at
secrets. Keep the integration disabled until its data boundaries and benefit have been reviewed.

## A Decisions API: decisions as data

Some decisions should not live in a chat: "may agents upgrade this dependency?", "is this
threshold approved?", "who owns this area?". A Decisions API is an external service of record for
them — human or agent decisions with their reasons — that loops can read before acting.

- **The contract** (`loops/decisions-api/README.md`): `GET /decisions?topic=...` returns the
  current decision and its reason; `POST /decisions` records a proposed one for a human to approve.
  Every call carries `Authorization: Bearer $DECISION_API_SECRET`.
- **JEV is the example** in Æion Factory: an external decision service your loops can consult. Any
  service with that contract fits.
- **Off by default** (`DECISION_API_ENABLED=false`): the client refuses to run until it is turned
  on, and the secret lives only in the local env file, never in the repository or a prompt.
- **Authority stays explicit:** an agent may *read* a decision and *propose* one; only a human
  approves. A missing or unreachable decision means *no* — fail closed.

## The trinity, measured

The sweet spot is a balance, so measure it — weekly, in the retro:

| Measure | Why |
| --- | --- |
| tokens (or cost) per merged pull request | the price of a unit of work |
| time from branch to green merge | speed |
| share of pull requests merged with no human edit, and share of review findings that were real | how much review a human still has to do |

When cost rises, look for context bloat (a long `AGENTS.md`, skills loading too often). When time
rises, look for slow checks. When human edits rise, the retro has lessons to capture.

## How the galaxy turns

```
session  ──► hooks catch it now ──► sign-off ──► PR ──► review comment ──► merge
   ▲                                                         │
   │                                                         ▼
 skills / hooks / preferences  ◄── weekly retro ◄── sessions + PR comments + outer-loop issues
```

Each week the same mistake becomes a little rarer, because it now has a hook, a skill step or a
preference that the next review applies. That is the whole trick.

## Done when

One retro ran and its pull request merged; the trinity has a first measurement; any optional
service that was turned on has its cost, its data scope and its off switch written down.

## Pitfalls

- A memory service that recalls everything: noise is context rot with extra steps.
- A Decisions API that agents can approve themselves: it is no longer a record of decisions.
- Measuring only cost: the cheapest PR is the one nobody can trust.

---

*From quarks to a galaxy in seven phases. Credits: [CREDITS.md](../CREDITS.md).*
