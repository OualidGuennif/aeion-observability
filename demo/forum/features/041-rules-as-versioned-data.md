---
id: 041
title: "Rules as versioned data"
area: moderation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum/product/"]
depends_on: [002, 014]
owner: builder
status: proposed
---

# 041 — Rules as versioned data

## Intent

Keep the forum rules in one reviewed file that renders to prose and to a machine form, so a moderation decision always cites a version that can be re-read.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
Content and model output are untrusted. Canonical definition: `tools/specs_c.py`.

## Inputs

- `rules/rules.yaml` with stable codes, severities and the prose for each rule.
- A renderer that produces the public rules page and a hash of the version.
- A check that every code used by the engine exists in the file.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.

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
