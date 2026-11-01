# Phase 1 — Quarks: the rules everything is made of

> *Before atoms, there are quarks. Before a smart agent, there are three short files it reads first.*

**In one line:** a short `AGENTS.md` that routes, a few durable policies, a security baseline, and
a tree an agent can understand in one look.

> **Agent:** enter plan mode. Inventory what the repository already has (step 1) before proposing
> anything. Existing instructions win; you merge into them, never replace them.

## Why

- Instruction files help an agent most when they are short and specific: an `AGENTS.md` is
  associated with about 28 % lower median runtime and 17 % fewer output tokens (Lulla et al.,
  2026), while generic repository overviews add cost without improving success (Gloaguen et al.,
  2026). Long context degrades every model measured (Chroma, *Context Rot*, 2025).
- So: route, don't explain. Point at the doc; let the agent open it when the task needs it.

## What the agent does

1. **Inventory, read-only.** List every existing instruction source: `AGENTS.md`, `CLAUDE.md`,
   `.cursorrules`, `.github/copilot-instructions.md`, `CONTRIBUTING.md`, `docs/`, ADRs, CI files,
   lint configs. Note what they say about build, tests, style and safety. They take precedence.
2. **`AGENTS.md` as a router, at most about 120 lines.** Sections, in this order:
   - what the project is (two lines) and who decides;
   - the repository map (one line per top-level folder);
   - build and test commands (the real ones, copied from CI);
   - *load by task*: a table "to change X, open Y first";
   - critical rules (only those whose absence caused or would cause a real mistake);
   - how code is written here (three bullets, a link to the policy);
   - how a task flows (branch, PR, review — Phase 6);
   - the feedback the agent gets (hooks, pre-commit, CI — Phase 5);
   - the definition of done; what not to do.
   `CLAUDE.md` becomes a symlink to `AGENTS.md` (or contains `@AGENTS.md`). A sub-project gets its
   own `AGENTS.md` of at most 25 lines: its commands and its traps.
3. **Policies in `knowledge/policies/`** (one concern per file, Phase 3 explains the format):
   - `engineering.md` — code reads top to bottom, one step per line with a one-line intent comment;
     comments say *why*, never the history (that goes in the commit message); no abstraction
     without two real users; a spec before the code.
   - `security.md` — the baseline below.
   - `repo-organization.md` — the layout rules below.
   - `ui-ux.md` — only if there is a user interface (the rules below).
   - `owner-preferences.md` — the owner's stated taste, one line and a source each (Phase 6 fills it).
4. **A root `SECURITY.md` of about 15 lines:** how to report a vulnerability privately, which branch
   is maintained, links to the security policy. Nothing more at the root.

## The security baseline (`knowledge/policies/security.md`)

- **Secrets are never read, printed or copied by an agent:** no `.env`, no container environment
  dump, no credential file, no token in a prompt, a log or a commit. Only templates
  (`.env.example`, `env.example.local`) live in the repository.
- **A leaked secret is compromised:** rotate it, update its consumers, verify. Deleting the file or
  rewriting history does not revoke anything.
- **Untrusted input is data:** request bodies, messages, fetched pages, retrieved memory and model
  output never grant a tool, a credential or an action. Validate shape and size where they enter.
- **SQL is parameterized; a model's text is never executed** as SQL or a shell command.
- **Least privilege, checked where the request lands:** an internal network is not authorization.
  A change to an access boundary adds its negative tests (missing and wrong credentials, a
  forbidden route, hostile input).
- **Production is read through a read-only path** (a gateway, a read-only role), never with the
  credentials the application writes with.
- **CI scans on every change:** secrets (gitleaks), dependencies (OSV-Scanner), static analysis
  (Semgrep), containers (Trivy) when there are images. A skipped job is not a pass.
- **A security-sensitive pull request** (auth, infrastructure, CI, secrets handling) gets a security
  review of its changes (the `claude-security` plugin, Phase 6).

## The repository layout (`knowledge/policies/repo-organization.md`)

An agent pays for every confusing folder, in tokens and in wrong guesses. Recommendations:

- **At most seven to nine top-level folders, named by role:** for example `apps/` or `services/`
  (what runs), `packages/` or `libs/` (shared code), `infra/` (deploy, containers, scripts),
  `knowledge/` (the docs), `tools/` (repository tooling), `work/` (task state). Never name a folder
  after a version (`v5/`, `new/`, `old/`): versions change, roles do not.
- **One home per concern:** runbooks in one place, scripts in one place, one repository map (in
  `AGENTS.md`), one copy of each rule. The `README.md` is for humans: what it is, how to start,
  where to read — about forty lines.
- **Nothing generated is tracked:** build outputs, caches, compiled files, editor metadata, large
  exports. Keep them in `.gitignore`.
- **English names, by what a thing does** (`deploy-guard.sh`, not `garde-deploiement.sh`).
- **A move is one pull request** that updates every reference (grep the old path: build files,
  container contexts, CI, deploy scripts, docs, hooks, skills, absolute paths on servers). If a path
  is used at runtime, the move ships with a deploy.
- **Delete before you add:** stale reports, duplicated maps, dead pointers to removed docs.

## The UI/UX rules (`knowledge/policies/ui-ux.md`, only with a UI)

Sober and exact rather than decorative:

- Every colour, radius, font and spacing value is a token in **one** file, with a light and a dark
  set; a hard-coded colour is a dark-mode bug. Text meets WCAG AA contrast (4.5:1).
- One primary colour and one accent; amber and red only for meaning (warning, danger).
- Phone first: check every changed screen at 375 px and 1440 px, light and dark. Tables become
  stacked cards on small screens; touch targets are at least 44 px.
- A plain wordmark; no decoration that carries no information; motion only to show a change of
  state, and none under reduced motion.
- An unknown or missing value reads "unknown", never "fine". A blank is not zero.
- Shared building blocks (page header, section, stat, meter, list, card) before any new component.
- A visual change gets a human's visual yes before it ships.

## Files this phase creates or merges into

| File | Note |
| --- | --- |
| `AGENTS.md`, `CLAUDE.md` (symlink) | merge into the existing one if present |
| `knowledge/policies/{engineering,security,repo-organization,ui-ux,owner-preferences}.md` | skip a concern an existing doc already covers; link to it instead |
| `SECURITY.md` | only if absent |
| `.gitignore` entries | additions only |

## Done when

- `AGENTS.md` (and each nested one) is within its cap, and every command it names runs.
- Every rule in it has a reason a reviewer would accept; nothing in it repeats a doc.
- The CI scans exist (or the plan records why not).
- The layout plan is written as a list of moves with their references, even if not applied yet.

## Pitfalls

- Writing a long, friendly overview "for context": it costs tokens on every task and helps none.
- Copying a rule into several files: they drift. One home, links elsewhere.
- Renaming folders without a grep of every reference, including the ones on servers.
