# The SQLite guardian service

The forum's database is a file, and a file with no owner is how a database becomes an outage. This
service owns the file's *survivability*: it proves the bytes are readable, takes consistent copies
while the application keeps writing, and refuses to believe a backup until a restore has been
performed.

It is deliberately small. It is **not** a SQL proxy: the Quarkus application opens the file directly
through JDBC, because putting an HTTP hop inside a transaction would trade correctness for a diagram.
What the service adds is the part an embedded file does not have — a second opinion on integrity, a
snapshot history with digests, a drill, and a lease that makes "two writers" impossible rather than
unlikely.

## What it guarantees

| Property | How | Test |
| --- | --- | --- |
| WAL, `busy_timeout=5000`, `synchronous=NORMAL` on every connection | `SqliteService.connect` | `test_connect_sets_wal_and_a_busy_timeout` |
| A missing database is refused, never created | `connect` raises `database_missing` | `test_a_missing_database_is_refused_not_created` |
| Snapshots are consistent while a writer runs | `VACUUM INTO` on a read transaction, then atomic rename | `test_snapshot_stays_consistent_while_a_writer_keeps_going` |
| A published snapshot is verified before it is published | `integrity_check` on the copy, SHA-256 recorded | `test_snapshot_is_a_verified_consistent_copy` |
| Retention is bounded and reported | `prune()` returns what it deleted | `test_retention_keeps_the_newest_and_reports_removals` |
| A snapshot that lost a table is refused, an older one is accepted with its lag | `verify_copy(expect_tables=...)` | `test_restore_drill_refuses_a_copy_that_lost_a_table`, `test_restore_drill_accepts_an_older_snapshot_and_reports_the_lag` |
| The live file is never written by a drill | the drill copies first, verifies the source digest | `test_restore_drill_proves_the_copy_and_leaves_the_live_file_alone` |
| One writer, provably | exclusive `flock` on `<db>.lease` | `test_a_second_writer_lease_is_refused` |

Row counts are **reported**, never a pass/fail: a backup taken an hour ago legitimately holds fewer
rows than the live file, and a check that refused it would refuse every real restore. A backup that
is missing a table is a different thing — that one is refused.

## Run it

```sh
# guardian: read-only, no lease, safe next to the running application
PYTHONPATH=demo demo/.local/venv/bin/python demo/forum-db/run.py --database /tmp/agora.db

# one operation, then exit
PYTHONPATH=demo demo/.local/venv/bin/python demo/forum-db/run.py --database /tmp/agora.db \
  --once snapshot --label before-release

# refuse to start if another writer holds the file
PYTHONPATH=demo demo/.local/venv/bin/python demo/forum-db/run.py --database /tmp/agora.db --writer
```

HTTP surface, all JSON, `no-store`:

| Route | Method | Answer |
| --- | --- | --- |
| `/healthz` | GET | 200 `ok` only when the file opens and `quick_check` passes, else 503 |
| `/v1/stats` | GET | size, WAL size, journal mode, page accounting, row counts |
| `/v1/snapshots` | GET | every snapshot, newest first, digest recomputed now |
| `/v1/snapshot` | POST | 201 with the record; `{"label": "..."}` optional |
| `/v1/restore-drill` | POST | 200 with the drill result; `{"snapshot": "path"}` optional |

## The drill

`drill.py` runs the whole story against the **live** database, with the real Quarkus service writing
through its own HTTP API while snapshots are taken:

```sh
PYTHONPATH=demo demo/.local/venv/bin/python demo/forum-db/drill.py \
  --database /tmp/agora.db --snapshots /tmp/agora-snapshots --keep 3 --writes 200
```

It fails (non-zero) on the first disagreement: an integrity failure, a write error, a snapshot that
does not verify, a drill that cannot restore, or a second writer that is not refused.

Measured on 2026-11-01, forum started with `AGORA_SESSION_SECRET` on a fresh `/tmp/agora.db`:

| Step | Result |
| --- | --- |
| integrity | `ok`, tables `accounts 1, schema_migrations 1, settings 200` |
| writes during snapshots | 200 writes through `PUT /api/settings/...`, 0 errors |
| snapshots | 5 taken mid-write, all `integrity: ok`, 73 728 bytes each |
| retention | keep 3, 2 pruned, 3 retained |
| restore drill | restored, `integrity: ok`, `unchanged_source: true`, lag 0 on every table |
| writer lease | second writer refused with `writer_lease_held` |

## Limits, stated plainly

- It does not proxy SQL and does not serialize the application's writes; the lease makes a second
  *guardian* a writer impossible, and the application remains the single writer by contract.
- No off-host replication: snapshots share a disk with the database. A real deployment copies them
  to another volume, and that is a named gap, not a property this service has.
- No PITR: snapshots are point-in-time copies without the WAL segment that followed them.
- It does not start, stop or supervise the application.
