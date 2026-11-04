# Factory continuation — current handoff

Updated: **2026-11-03**. The owner has authorized completion of the real Flue/Pi factory,
protected PR-to-main automation and regeneration of the 100 product contracts. Earlier
November 1 instructions to await initial GitHub setup have been superseded. This does not
permit reading credentials, bypassing protections or declaring unqualified work complete.

Read [PLAN.md](PLAN.md), [ARCHITECTURE.md](ARCHITECTURE.md), [ECOSYSTEM.md](ECOSYSTEM.md),
[the ordered feature index](features/README.md), and current root work/validation records.

- Product: keep Quarkus/Java/Gradle; migrate SQLite to PostgreSQL; replace Expo/React Native
  with a React DOM/TypeScript browser client. Native mobile delivery is deferred.
- Product sources belong in `OualidGuennif/aeion-autonomous-forum`; observer sources remain
  separate. Feature write paths are relative to the product repository.
- Preserve all 100 IDs and historical receipts. Follow generated `sequence`, which places
  dependencies first. Every feature has three bounded delivery steps and protected acceptance.
- Modify only canonical `tools/specs_a.py` through `specs_f.py`, then run the generator; never
  edit generated MDs independently. Shared architecture digests invalidate stale contracts.
- 002/003/014 are the database migration, PostgreSQL harness and React shell. Historical
  SQLite/Expo receipts cannot mark their new contracts complete. Never delete the old volume.
- Factory execution: Python supervisor dispatches real Flue/Pi agents; coding tools use
  OpenShell tier 3, RPC copy, no host mounts, no workload credentials or arbitrary egress.
- Four allowed worker models: GLM 5.3 Flash, DeepSeek V4.1 Flash, Qwen 3.8 Flash,
  Claude Haiku 5.5 with medium reasoning. Measured routing is deterministic and cohort-bound;
  memory recall is advisory. Default telemetry contains metadata only.
- Two approving reviewers differ from the builder and each other. Review and protected checks
  bind the same frozen artifact. Isolated publisher/release roles verify required CI and exact
  base/head, reconcile uncertain effects and confirm the merge SHA on main.
- The cockpit remains held while the replacement engine is unqualified. No fake marker,
  one-shot fallback, direct-main push or permission expansion may turn it green.

```sh
python3 -B demo/forum/tools/generate_features.py
python3 -B demo/forum/tools/generate_features.py --check
python3 -B -m unittest discover -s demo/forum/tools -p 'test_*.py' -v
```

These commands validate contracts only. Real harness, PostgreSQL migration/restore, browser,
telemetry/memory and publication qualification remain separate. Preserve failures, unknown
usage, budget liabilities and concurrent work; never inspect `.env` or raw private transcripts.
