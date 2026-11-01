---
id: 018
title: "No-JS baseline and accessibility"
area: foundation
size: S
parallel: false
depends_on: [014]
owner: builder
status: proposed
---

# 018 — No-JS baseline and accessibility

**Goal.** Keep every core action usable without JavaScript, with labelled controls and a readable contrast, so the forum works on the worst client and fails loudly when it does not.

## Scope

- Progressive forms with server-side validation and re-rendered errors.
- Labels, focus order, landmarks and a visible focus ring.
- A contrast check over the palette.

## Out of scope

- Screen-reader certification.
- Internationalization.

## Acceptance

- [ ] Posting, replying and voting work with JavaScript disabled.
- [ ] Every input has a label and every error is announced in text.
- [ ] The contrast check passes on the shipped palette.

## Security

No behaviour depends on client-side validation; the server is the only judge.

## Test

Run the flows with a JavaScript-disabled client and assert the server-side error paths.
