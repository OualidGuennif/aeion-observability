---
id: 035
title: "Thread export for analysis"
area: forum
size: S
parallel: false
depends_on: [022]
owner: builder
status: proposed
---

# 035 — Thread export for analysis

**Goal.** Export one thread as JSON for offline analysis, with bodies and provenance but without identities beyond an opaque author id.

## Scope

- A CLI export for administrators writing to a file, never to HTTP.
- A schema with version, post, comments, votes aggregate and provenance.
- A refusal to export a private channel without an explicit flag.

## Out of scope

- A public API or a webhook.
- Bulk export of the whole forum.

## Acceptance

- [ ] The exported file validates against the documented schema.
- [ ] No handle, token or session identifier appears in the file.
- [ ] Exporting a private channel without the flag is refused.

## Security

The export is a local file written with 0600, and the audit log records who ran it.

## Test

Export a seeded thread, validate the schema and grep for handles and tokens.
