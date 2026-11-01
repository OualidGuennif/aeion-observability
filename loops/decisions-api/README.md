# Decisions API (optional, off by default)

An external service of record for decisions — human or agent, with their reasons — that the loops
read before acting. JEV is the example service; any service with this contract fits.

## Contract

| Call | Body / query | Returns |
| --- | --- | --- |
| `GET /decisions?topic=<topic>` | — | `{ "topic", "decision", "reason", "decided_by", "decided_at", "status": "approved" \| "proposed" \| "rejected" }`, or 404 |
| `POST /decisions` | `{ "topic", "proposal", "reason", "proposed_by" }` | `{ "id", "status": "proposed" }` |

Every call carries `Authorization: Bearer $DECISION_API_SECRET`.

## Rules

- **Off until turned on:** `DECISION_API_ENABLED=false` in `env.local`; `client.sh` refuses to run.
- **The secret stays in `env.local`:** the client reads it itself; it never enters a prompt, a log,
  an issue or the agent's environment.
- **Agents read and propose; humans approve.** A missing, unreachable or `proposed` decision means
  *no*: the loop fails closed and opens a `needs-owner` issue.

## Use

```bash
loops/decisions-api/client.sh get dependency-upgrades
loops/decisions-api/client.sh propose dependency-upgrades "allow patch upgrades weekly" "low risk, CI covers it"
```

`example-jev.md` shows the settings for the JEV example.
