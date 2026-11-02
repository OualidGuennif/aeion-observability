# Factory local VPS runbook — S4

Scope: run the Æion cockpit and the Agora factory board on one small VPS, locally, with fake
inference. Nothing here authorises paid inference, a remote push/PR/merge or a product
deployment. The default worker still simulates builds; the one pinned target profile below
runs the real Quarkus forum and its real Gradle check without a model call.

Honest limit: the backup/restore drill below qualifies the **factory state store** (SQLite).
It does **not** qualify a future product Postgres restore, which needs the real product schema.

## 1. What runs

One Python process serves two surfaces on loopback:

| Surface | Path | Purpose |
| --- | --- | --- |
| Cockpit | `/` | read-only task cockpit |
| Factory board | `/factory` | administrator board: login, catalog, queue, cancel, live events |

The factory owns a SQLite database (WAL) and a disposable work tree. Both live under
`demo/.local/`, which is ignored by Git and never inside the product output scope.

## 2. Prerequisites

- Python 3.13+ (the demo venv runs 3.15), `git` on `PATH`.
- No inference provider is contacted by the board. The GitHub publisher exists but stays in
  dry-run unless `--for-real` is passed and `GH_API_KEY` is present; the token is read at call
  time and never printed.
- A dedicated unprivileged user owns the checkout and `demo/.local/`.

## 3. Harness prerequisite: the Pi extension

Agents must be started with the factory extension, or **the skills and the hooks never load**:

```bash
pi -e .pi/extensions/factory/index.js
```

`flue run` (2.3.0) exposes no `-e`/`--extension` option, so the flag belongs to the Pi
invocation that Flue drives, not to the Flue command line. Cloning and installing the
architecture integrations do not register it.

The factory checks this when it prepares an agent workspace: `factory.analysis.prepare()`
returns `pi_extension: {"path": ".pi/extensions/factory/index.js", "present": true|false,
"required_flag": "pi -e .pi/extensions/factory/index.js"}`. A workspace reporting
`present: false` runs the agent without its skills and hooks — treat that as unqualified,
not as a cosmetic warning.

## 4. Trust boundary

Read `trust-model.md` before granting any new capability. Short version: the model produces data,
never authority. Generated code runs only inside OpenShell, the diff is validated as data, the
protected checks and the deterministic reviewer are outside the candidate's control, and the
publisher refuses anything unreviewed. Nothing auto-merges.

## 5. Configuration (allowlist only)

| Variable | Default | Meaning |
| --- | --- | --- |
| `AEION_COCKPIT_PORT` | `8088` | loopback port |
| `AEION_LOCAL_DIR` | `demo/.local` | owner-only state root (mode `0700`) |
| `AEION_DATA_DIR` | `demo/.local/data` | cockpit data |
| `AEION_WORK_DIR` | `demo/.local/work` | >= disposable work trees |

Never pass a secret on the command line or in a unit file. The factory prints nothing from the
environment. The first start writes `demo/.local/factory/admin.token` (mode `0600`); that token is
rotated on every successful login.

### 5.1 The credentials, one key per capability

Start from the committed root template `.env.example` and fill it locally. Three GitHub keys,
never one:

| Key | Role | Fine-grained permissions | Held by |
| --- | --- | --- | --- |
| `GH_BUILD_KEY` | build | Contents read-only, Pull requests read-only | build agents, and only if they must clone |
| `GH_API_KEY` | publish | Contents read/write, Pull requests read/write | the publisher process, for one publish |
| `GH_RELEASE_KEY` | release | Contents read/write, Pull requests read/write | a human, at release time |

Scope each key to `OualidGuennif/aeion-autonomous-forum` only, give it an expiry, and never export
it to an agent, a worker, the review circuit or CI. `demo/factory/keys.py` enforces the roles and
`demo/app/settings.py` scrubs the publish class at start-up; a missing key fails closed.

### 5.2 Branch protection and the required checks

Both `main` and `develop` require a pull request and these status checks, which the Æion Factory
CI produces: `Knowledge, links and repository health`, `Product artifacts`, `secret-scan`,
`dependency-scan`, `sast-scan`. Linear history, resolved conversations, no force-push, no deletion,
admins included. `main` also requires the branch to be up to date before merging; `develop` does
not, so parallel builds can merge without a rebase race.

`Product artifacts` runs `.github/scripts/check_product.py`, which is deliberately independent of
the factory's own reviewer: a worker that approved its own output still faces a second opinion.

## 6. Start and stop

Foreground (manual, easiest to watch):

```bash
cd /srv/aeion-observability
python3 demo/run.py
```

The launcher re-executes `demo/.local/venv/bin/python`, so `jinja2` resolves. Run it once to
create the venv if it is missing.

`systemd` unit (Linux VPS), adapted paths and user:

```ini
[Unit]
Description=Aeion cockpit and Agora factory board (local, fake inference)
After=network.target

[Service]
Type=simple
User=aeion
WorkingDirectory=/srv/aeion-observability
Environment=AEION_COCKPIT_PORT=8088
ExecStart=/usr/bin/python3 demo/run.py
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/srv/aeion-observability/demo/.local

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now aeion-factory
curl -fsS http://127.0.0.1:8088/api/health     # {"status":"ok"}
```

Stop with `sudo systemctl stop aeion-factory`. The service binds loopback; the board refuses a
foreign `Host` or a mismatched `Origin`, so a tunnel or proxy must preserve both.

## 7. Health and inspection

```bash
curl -fsS http://127.0.0.1:8088/api/health          # cockpit health
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8088/factory   # 200
```

The board itself requires an administrator session; `/api/factory/board` without a cookie returns
`401`. Read the admin token from the file as the owner — never copy it into a ticket, a chat or a
log.

## 8. Backup (verified, not assumed)

The drill uses SQLite's online backup API, safe while WAL is live, then re-verifies the copy:

```bash
cd /srv/aeion-observability/demo
.local/venv/bin/python -m factory.restore \
  .local/factory/factory.db \
  /var/backups/aeion/factory-$(date -u +%Y%m%dT%H%M%SZ).db
```

It prints a JSON receipt and exits non-zero when the copy is unusable (`source_missing`,
`not_a_database`, `integrity:…`, `missing_tables:…`). A backup **without** that receipt is not a
backup. Retention: keep the last 14 daily files plus the first of each month; the store is small.

Schedule it from `systemd` timers or cron, and fail the job on a non-zero exit.

## 9. Restore (drill and real)

1. Stop the service so no writer is live.
2. Verify the backup **before** touching the live file:
   ```bash
   cd /srv/aeion-observability/demo
   .local/venv/bin/python -c \
     "from factory.restore import verify_db; import json; print(json.dumps(verify_db('/var/backups/aeion/factory-XXXX.db')))"
   ```
3. Move the current database aside (never delete it):
   `mv demo/.local/factory/factory.db demo/.local/factory/factory.db.pre-restore`
   and the same for any `-wal` / `-shm` siblings.
4. Copy the verified backup into place and `chmod 0600` it.
5. Start the service, then confirm: `/api/health` is `ok`, `/factory` is `200`, and the board
   lists the expected builds (a restored `simulated_complete` build keeps its receipt).
6. Only after a successful verification, remove the `.pre-restore` files.

The factory's `Store` also reconciles expired leases at startup: a build that was dispatched when
the process died returns to `queued` and is re-claimed, never blindly duplicated.

## 10. Rollback

Code and state are separate. To roll back a bad run: stop the service, restore the last verified
backup, start the service, and confirm the board and health as in §7. Roll back the checkout with
Git only after the state is consistent; never restore a database under a different schema version
without a migration.

## 11. Failure modes the runbook assumes

| Symptom | Meaning | Action |
| --- | --- | --- |
| build held `dependency_missing` | a prerequisite is not merged | admit the prerequisite first |
| build held `qualification_missing` | frozen spec or bound missing | fix the spec/bounds, re-admit |
| build held `owner_review_required` | the diff touches a sensitive scope | owner reviews, then re-admits |
| build held `reconciliation_needed` | a stale base/head was refused | reconcile before retrying |
| publisher `uncertain` | forge effect unknown | the publisher reconciles; never re-publish |

## 12. What this runbook does not qualify

- Real tier-3 sandbox containment (the macOS transport is still unqualified, handoff §6).
- The GitHub publisher: `GH_API_KEY` is not loaded, no branch, PR or merge is created.
- The product forum, its Postgres schema, its restore, its moderation or its telemetry.
- Any paid model call, any deployment, any external exposure of the board.

## 13. Release plane

Start the cockpit and open `http://127.0.0.1:8088/factory`. The **Release plane** panel is above the
build panels.

| Action | Endpoint | What it does |
| --- | --- | --- |
| Stage | `POST /api/factory/release {"action":"stage","features":[…]}` | creates the release and serves it on the **staging** slot only |
| Validate | `{"action":"validate"}` | promotes it to production at **25%** |
| Advance | `{"action":"advance"}` | next step, only when the dwell is over **and** the canary gate says `continue` |
| Immediate full deploy | `{"action":"deploy_now"}` | 100% now, recorded as `immediate_full_deploy` |
| Rollback | `{"action":"rollback","reason":"…"}` | 0%, state `rolled_back` |
| Flag | `{"action":"flag","name":"dark_mode","enabled":true}` | recorded in the release history |

`AEION_RELEASE_SCALE` compresses the 6 h/12 h dwells for a local drill and is stored on the release;
`AEION_REDIS_URL` selects the real cache (otherwise the file fallback is named in the response).
A real Redis for the playground:

```bash
docker run -d --name aeion-redis -p 6399:6379 redis:7-alpine
AEION_REDIS_URL=redis://127.0.0.1:6399 python3 demo/run.py
```

Agent sessions (workers, never forum users) are issued and revoked through
`POST /api/factory/session` with `{"action":"issue","agent_id":"…","build_id":"…"}`. The token is
shown once; the gateway stores only its digest and every call lands in `gateway-audit.jsonl`.

## 14. Pinned forum target (offline)

The default worker writes a simulated Markdown diff. A target profile binds one catalog
feature to the runnable Quarkus forum instead: an exact base commit, two literal source
scopes, an adapted brief, and a protected Gradle check whose contract test lives outside both
scopes. The first profile is feature 013 in
`demo/forum/targets/forum-app-013.json`; the 100-feature plan is untouched.

```bash
demo/.local/venv/bin/python demo/tests/qualify_forum_build.py
# or, without the Collector/Langfuse export:
demo/.local/venv/bin/python demo/tests/qualify_forum_build.py --no-telemetry
```

It clones the product repository at `37417ab` (`demo/.local/factory/agents/aeion-autonomous-forum`),
runs an injected fake-model builder (no inference, no cost), validates the artifact, runs the real
`gradle test --offline` suite with the external contract copied in, takes two fake review votes,
records the fake-forge PR shape and emits one metadata-only `factory.build` span. The script then
reads the trace back from Langfuse and fails if the build, feature, attempt, artifact or session
identity differs. The build appears on `/factory`; its receipt shows the four ids and links the
trace. This is an offline qualification: it does not authorise a paid model run, a real pull
request or a deployment. The local Docker image is documented in the product repository at
`demo/forum-app/DOCKER.md`.
