---
id: 014
sequence: 14
title: "React browser application shell"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "demo/forum-web/", "demo/forum-docs/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [001]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 014 — React browser application shell

## Intent

Replace the active Expo/React Native client with one React DOM/TypeScript web application using the existing Quarkus API; ship a browser product with no native mobile target.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Create the React DOM/TypeScript shell with one pinned browser build.
2. Wire relative API calls and visible loading, empty and error states.
3. Prove browser parity and retire the active Expo/mobile startup path.

**Scope:**

- Create demo/forum-web/ with a small Vite production build, pinned npm lock, semantic DOM components, navigation and locally bundled assets; no extra frontend server.
- Use same-origin relative API calls in production and a constrained local development proxy; reuse existing JSON interfaces and preserve session/CSRF behavior.
- Provide loading, empty, unavailable and retry states; request cancellation and duplicate-click protection must not turn a failed mutation into an automatic replay.
- Centralize sanitizer-produced HTML in one reviewed rendering component; all other content uses escaped JSX and no arbitrary HTML sink.
- Retire active Expo/React Native startup/build paths after equivalent browser flows pass. Remove unused mobile-only dependencies in that reviewed change; do not keep a second client running.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Browser validation is advisory. Quarkus authorizes every API request; session cookies stay HttpOnly and browser bundles contain no secret. Freeze the API/UI origin and CSP before enabling authenticated mutations.

This invariant and the acceptance cases belong to planned protected check `agora-014`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The pinned frontend type check, tests and production build pass; the production server deep-links the browser routes and serves fingerprinted local assets.
- [ ] The browser shell loads and renders API health, loading, empty and failure/retry states without any remote CDN request.
- [ ] Untrusted text is escaped; only the centralized component can render HTML from the server sanitizer, and injection fixtures remain inert.
- [ ] After cutover only the React web startup path is active; no native/mobile build or Expo service is needed.

**Test scenario:** Build the React production client, exercise it against a disposable Quarkus API in a browser and verify deep links, escaping, loading/failure states and retirement of the Expo startup path.

## Out of scope

- Native mobile apps, Expo, React Native, SSR, a frontend backend or a new authentication system.
- A requirement that an interactive React application work with JavaScript disabled.
