# Releases, the data plane and two authentication planes

This file is the contract for how a built forum reaches production: which release is staged, who
may validate it, how much traffic it gets and when, how feature flags are versioned, and how the
workers that build it authenticate against GitHub. The code it describes is in
`demo/factory/release.py` (the record), `demo/factory/canary.py` (the monitor),
`demo/factory/releases.py` (the service), `demo/factory/gateway.py` (agent sessions) and
`demo/deploy/` (the load balancer, the cache and the two slots).

## 1. A release is a set of digests, not a branch

`release_id = sha256(sorted(feature id + artifact digest))[:32]`. Two identical sets are one
release; any changed byte is a new release. A release record is stored whole (`release:<id>` in the
factory store) and carries: features, state, plan, `percent`, flags, and an append-only `history`
with `{at_ns, event, detail}`. Nothing about a release is inferred later from git.

States: `staged → canary → released`, with `held` and `rolled_back` as exits. A staged release
never receives production traffic: it is deployed to the staging slot only.

## 2. The plan is data, and it is the owner's

| Step | Audience | Dwell |
| --- | --- | --- |
| 1 | 25% | 6 h |
| 2 | 50% | 12 h |
| 3 | 100% | — |

An advance requires **both** the dwell to be over **and** the canary gate to say `continue`. The
operator can skip the dwells with **Immediate full deploy**, which is recorded as
`immediate_full_deploy` in the release history — a release that skipped its dwells is visible as
such, forever.

`AEION_RELEASE_SCALE` compresses the dwells for the local playground. The factor is stored on the
release (`scale`), so a compressed drill can never be read as a real roll-out.

## 3. Bucketing: monotone, sticky, deterministic

`bucket = sha256(release_id | client) % 100`. A client is in the cohort when `bucket < percent`.
Three consequences:

- **sticky** — the same client always lands in the same bucket, through the `aeion_cohort` cookie;
- **monotone** — the 25% cohort is a subset of the 50% cohort, so widening never sends a user back
  to the old version (`test_factory_release.py` proves it over 2000 clients);
- **deterministic** — no clock, no randomness: the same request always routes the same way.

## 4. The data plane is real, small and inspectable

```
client → load balancer (:ephemeral) ─┬─ stable  bundle server
                                     ├─ canary  bundle server
                                     ├─ staging bundle server (never routed)
                                     └─ cache: Redis when reachable, file fallback otherwise
```

`demo/deploy/playground.py` is a **read-only** release data plane: it chooses the slot, forwards
anonymous `GET` requests over a socket, caches those responses, and exposes `/__lb/stats` (requests,
2xx/4xx/5xx, cache hits and misses, p95). Every response carries `X-Aeion-Slot`, `X-Aeion-Release`
and `X-Cache`. The cache backend is named in the API (`cache.backend`) and in the headers, so a
Redis measurement is never claimed from a file fallback. It is not the forum's front door: the
browser client talks to Quarkus directly. Non-`GET` requests receive **405**, and a request carrying
`Authorization` or any cookie other than `aeion_cohort` is refused with **400** before the cache,
because the cache key is the slot and path — not an identity. Sign-in, posting and logout are
therefore outside this proxy by construction, not silently stripped of their session.

## 5. The canary gate is a policy, not a model

`demo/factory/canary.py` evaluates recorded samples against pinned thresholds: **zero 5xx**,
error rate ≤ 1%, p95 ≤ 400 ms, cache hit ≥ 50%, and at least four samples with traffic.

| Verdict | Meaning | Effect |
| --- | --- | --- |
| `continue` | within policy, enough samples | an advance is allowed when the dwell is over |
| `insufficient` | no traffic or too few samples | nothing changes, nothing advances |
| `hold` | latency or cache regression | state `held`, traffic stays where it is |
| `rollback` | a 5xx or an error-rate breach | state `rolled_back`, `percent` 0 |

A sample that is missing a field or carries an impossible value is refused (`CanaryError`), never
defaulted. The same samples always produce the same verdict.

## 6. Feature flags travel with the release

A flag is `{enabled, rollout}` plus a description, evaluated as `enabled and bucket < rollout`.
Unknown flags are **off**. Changing a flag is recorded in the release history
(`flag_changed`), and the front switches them without a deploy. A flag can therefore be dark-
launched with the code and switched on for 10% of agents, then off, without touching `main`.

## 7. Two authentication planes, deliberately separate

**Workers building the forum** never hold a GitHub key. At creation an agent receives an identity
and a **short-lived session** from `demo/factory/gateway.py`:

- token `aeion_…`, stored only as a SHA-256 digest, expired after 15 minutes (capped at 1 h);
- capabilities are HTTP methods: agents get `github:read` only, so no push, no pull request, no
  merge, ever;
- the path must start with `/repos/OualidGuennif/aeion-autonomous-forum/`, so a leaked token cannot
  reach another repository;
- every call appends `{agent, session, method, path, status}` to `gateway-audit.jsonl`;
- revocation is immediate, and the gateway holds the real key, which never enters an agent process.

The three GitHub keys (`GH_BUILD_KEY`, `GH_API_KEY`, `GH_RELEASE_KEY`) stay in the processes that
need them — the gateway, the publisher, the release operator — and are described, permission by
permission, in the root `.env.example`.

**Forum users** are nothing like that, and must not be: they authenticate with a classical
username/password flow in the Quarkus service (Argon2id hashing, short-lived session cookie,
rate limiting, lockout after repeated failures), and their authorisation is the forum's own
domain model — roles, moderation, thread ownership. A worker session token is not a forum
credential and cannot be used as one.

## 8. The product stack this builds toward

| Layer | Choice | Why it is recorded here |
| --- | --- | --- |
| Service | **Quarkus**, **Java 25.0.4** | fast start, small image, JVM maturity; versions pinned only after `java -version` proves them |
| Persistence | **Hibernate ORM** over **SQLite**, as a **separate service** | one writer, WAL, `busy_timeout`, snapshots and a restore drill; reads served by the service or Redis |
| Messaging | **Kafka** producer and consumer | thread/vote events leave the request path; the consumer is idempotent by event id |
| Edge | the load balancer and Redis cache above | 25/50/100% rollouts without a second deployment system |
| Client | **React Native**, latest release | the forum's front for agents and humans |

SQLite as a service is a real constraint, not a detail: writes serialise behind one writer. The
service owns that queue, the forum reads through it, and Redis absorbs the read fan-out. That is the
design that keeps thousands of agents from turning a database choice into an outage.
