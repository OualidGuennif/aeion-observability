# Example: JEV as the Decisions API

```bash
# env.local (never committed)
DECISION_API_ENABLED=true
DECISION_API_URL=https://jev.example.com/api
DECISION_API_SECRET=<issued by JEV>
```

A loop then asks before an action that needs a standing decision:

```bash
loops/decisions-api/client.sh get release-freeze      # e.g. {"decision": "no releases on Fridays", "status": "approved"}
```

Topics worth recording: dependency upgrades, release freezes, data retention, who owns an area,
which risks are accepted. The URL above is a placeholder for your JEV instance.
