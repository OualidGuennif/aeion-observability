---
id: 041
title: "Rules as versioned data"
area: moderation
size: M
parallel: false
depends_on: [002]
owner: builder
status: proposed
---

# 041 — Rules as versioned data

**Goal.** Keep the forum rules in one reviewed file that renders to prose and to a machine form, so a moderation decision always cites a version that can be re-read.

## Scope

- `rules/rules.yaml` with stable codes, severities and the prose for each rule.
- A renderer that produces the public rules page and a hash of the version.
- A check that every code used by the engine exists in the file.

## Out of scope

- Editing rules through the web interface.
- Per-channel rule overrides beyond a channel's own text.

## Acceptance

- [ ] The rendered page and the machine form come from the same file and hash.
- [ ] A rule code referenced by code but missing from the file fails the build.
- [ ] Changing a rule changes the hash and the version shown on new posts.

## Security

The rules file is code-reviewed like code; no runtime write path exists.

## Test

Render, hash, then remove a referenced code and assert the check fails.
