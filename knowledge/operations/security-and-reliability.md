---
type: Runbook
title: "Telemetry security, accounting integrity and failure recovery"
description: "Trust boundaries, metadata-first capture, untrusted outcomes, atomic exposure admission, resilient collection and CROA evidence separation."
status: draft
sources:
  - id: references
    resource: ../references/sources.md
    title: "Official security, reliability and governance references"
---

# Security and reliability

This document specifies qualification requirements. None of these controls has been deployed
or penetration-tested by preparing this research folder.

## 1. Authority stays outside the optimization objective

The controller may select only profiles already permitted by the operator's OPS policy. It may
not add an endpoint, attach a secret, broaden a mount, relax tool permissions, change retention
or remove a Factory review gate to improve cost or speed. Capability validation is deterministic
and independent of model reasoning.

Æion CROA is a separate audit kit, adapted with attribution from The CROA Project. Its local
validator checks evidence packets; it is not a runtime firewall. A deployment claiming CROA
properties requires the actual governed execution path and evidence for its boundary/period.
Observability can export references for assessment, never silently grant conformance.
[Æion CROA](https://github.com/OualidGuennif/aeion-croa),
[CROA v1.0.1](https://github.com/CROA-Project/CROA/tree/v1.0.1)

Keep a required durable authorization/audit event distinct from best-effort sampled analytics.
The CROA specification's durable-before-transition requirement cannot be satisfied merely by
starting an OTel span or buffering a record for later export.
[Pinned CROA deployment architecture](https://github.com/CROA-Project/CROA/blob/4d59192da9a0d00412c9d2ccb9e5ab68176803ff/spec/parts/part-2-reference-architecture.md)

## 2. Trust model

| Component | Receives | Must not gain |
| --- | --- | --- |
| Workload | Task inputs and narrow inference/telemetry capabilities | Collector administration, ledger writes, promotion keys or arbitrary egress |
| Ingestion receiver | Bounded authenticated workload metadata | Automatic trust in claimed producer/run IDs |
| Trusted supervisor | Runtime lifecycle and effective policy | Authority inferred from repository text |
| Usage reconciler | Scoped provider accounting evidence | Unrestricted production/account administration in the agent sandbox |
| Evaluator | Bounded artifact and protected rubric | Tool execution or policy writes from artifact instructions |
| LLM analyst / dashboard assistant | Read-only sanitized evidence by default | Secret access, self-promotion or unreviewed runtime changes |
| Delivery workflow | Reviewed artifact and check evidence | Implicit production authority from a task-success score |

Bind producer/run identity during launch or authenticated ingestion. Segregate workload-origin
and trusted runtime/provider evidence. If a workload stops sending events, record unknown coverage;
its silence is not evidence of no forbidden action or no human help.

## 3. Default data policy

Collect bounded timings, counts, IDs, version digests, result/error classes and allowlisted usage.
Do not export raw prompts, source code, model outputs, hidden reasoning, tool arguments/results,
command strings, full URLs, request/response bodies or auth headers by default.

Native SDKs, plugins and providers have different content defaults. Configure each producer and
the collector. Apply an attribute **allowlist before export and before persistent buffering**;
regex scrubbing is defense in depth, not the primary content boundary. Check log bodies, span
events, resource attributes, exception strings and custom metadata as well as span attributes.

Claude's content switches and identity/cardinality behavior are documented. Disable content
capture explicitly in the qualified profile and filter identity metadata according to policy.
Do not enable detailed tracing modes simply to get a prettier waterfall without inspecting what
they export. [Claude monitoring/privacy](https://code.claude.com/docs/en/monitoring-usage#security-and-privacy)

OpenRouter Broadcast privacy mode removes input/output content per destination, while other
metadata remains. A `trace` metadata object can still contain secrets if the client puts them
there. Verify each configured destination, not just a global checkbox.
[Broadcast privacy](https://openrouter.ai/docs/guides/features/broadcast#privacy-mode)

For a content-bearing diagnostic or semantic evaluation, create a separate scoped data tier:
explicit approved purpose, minimum selected artifacts, access controls, storage location,
retention/deletion policy and audit of readers/exports. Use sanitized fixtures for development.
No raw session ingestion into a third-party judge is implied by enabling observability.

Hashing content is not anonymization. Low-entropy paths/commands can be guessed from hashes;
use tenant-scoped keyed fingerprints where necessary and keep keys outside workload access.
Avoid public usernames/repository names in resource labels or propagated baggage.

## 4. Ingestion and collector hardening

- Use authenticated, encrypted transport where traffic crosses a trust boundary. Keep backend
  exporter secrets in the collector/supervisor, not in workload environment dumps or repo settings.
- Expose only the receiver that is needed. A sandbox may send telemetry to a fixed ingest
  route; it must not use the collector as a general HTTP proxy or reach its admin/health internals.
- Bound payload size, rates, cardinality, decompression, parsing, queues and disk. Reject malformed
  events without terminating other sessions or leaking payloads in parser errors.
- Do not accept a user-supplied exporter URL, resource identity, file path or collector config
  as trusted run configuration. Protect config, extensions and credentials from workload writes.
- Keep processor/exporter versions pinned, reduce component inventory, verify release artifacts
  and monitor advisories. A collector and its storage are part of the attack surface.
- Test tenant/task isolation and query authorization before any shared deployment. A local
  dashboard bound to a public interface is not automatically authenticated.

These requirements align with Collector security guidance, but require local tests and effective
configuration evidence. [Collector security practices](https://opentelemetry.io/docs/security/config-best-practices/)

## 5. Atomic spending exposure

Post-response cost charts cannot enforce a hard pre-request budget. For API actuation use a
trusted transactional ledger with this invariant:

```text
known committed spend + unresolved held exposure + new request reservation <= budget
```

Compute a conservative request bound from input/tokenization, maximum billed output including
reasoning, cache write/uncached worst case, request/server-tool fees, service tier and current
qualified price. If a fee or provider behavior is unbounded/unknown, refuse a strict-budget claim
for that profile; use a declared soft budget or do not admit it.

Atomically reserve before dispatch, bind reservation to an attempt, and settle idempotently.
A timeout or client cancellation is not proof that inference stopped or that no bill is due.
Hold uncertain exposure until reconciled or resolved by an explicit accounting policy.
Crash recovery must distinguish a never-dispatched reservation from an uncertain dispatched call.

Concurrent tasks share the same account/project budget scope where appropriate. Two valid
individual admissions do not prove cumulative budget consistency. Never release every reservation
on process restart or independently subtract the same response twice.

Provider/key caps remain useful defense in depth. Measure races and in-flight/cancellation
semantics before claiming zero overshoot. Subscription profiles instead need supported quota/
rate/deadline controls and labelled allocations; no invented per-request invoice ceiling.

## 6. Retries, tools and side effects

Assign retry ownership. SDK retries × harness retries × gateway fallbacks can multiply paid work
and latency. Record visible attempts and aggregate hidden-retry uncertainty. Use bounded retry
count, jitter, retryable error classes and a single overall deadline; honor provider guidance.

Never automatically replay a tool with an uncertain external effect. The receiving service must
provide idempotency or reconciliation for that action. A provider inference cancellation cannot
undo files already edited, a message sent, or a transaction committed by a tool.

Prefer sequential failover for v0. Racing/hedging two model calls can spend twice and can trigger
duplicate tools if the harness consumes both outputs. Only qualify hedging later with a single
result consumer, effect-safe tools, cancellation evidence and both calls in accounting.

## 7. Resilient collection without inventing completeness

OTel Collector queues, retries and persistent storage can reduce loss; full queues, retry expiry,
disk failure or configuration errors can still lose data. Acknowledged ingestion is not necessarily
durable end-to-end acceptance in the final backend.
[Collector resiliency](https://opentelemetry.io/docs/collector/resiliency/)

Use bounded persistent queues where required, restricted permissions and monitoring of queue
occupancy, drops, exporter failures and disk space. Test recovery after abrupt termination.
Sampling can preserve diagnostic errors/slow tasks, but selection rules must be recorded and must
not bias the complete accounting/outcome cohorts.

| Failure | Required behavior |
| --- | --- |
| Trace backend unavailable | Buffer within limits; preserve complete local usage/outcome evidence; report gap |
| Collector overload/disk full | Bound impact; count losses; stop optimization from incomplete signals |
| Mandatory authorization audit unavailable | Follow governed fail-closed transition rule; analytics fallback cannot replace it |
| Controller unavailable | Fixed approved baseline only if all required enforcement/accounting still hold |
| Delayed/missing label | Pending/unknown outcome, no fabricated learning target |
| Late/duplicate/out-of-order event | Idempotent event/charge/outcome version handling; no irreversible double aggregation |
| Clock skew / process restart | Separate occurrence/receipt times, monotonic durations and boot identities |
| Provider price/model changes | Expire affected eligibility or requalify; no silent unsupported continuation |
| Rollback endpoint retired | Reassess eligible approved target; checkpoint if none remains |

## 8. Qualification evidence to retain

Keep sanitized failure fixtures, effective deployment/config digests, request/attempt identities,
ledger recovery results, cancellation uncertainty, exporter-drop tests, privacy canaries and
evaluator injection tests. Access and retention are scoped; no general secret dumps are needed.

A hash establishes artifact identity under the stated capture process. It does not prove that
capture was complete, the source honest, the checker independent or storage tamper-proof.
Represent each of those as its own tested claim and retain unresolved limitations.
