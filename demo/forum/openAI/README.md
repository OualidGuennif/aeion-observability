# External review bundle

Verbatim snapshots of the two design files, prepared for an outside review (ChatGPT). The
canonical files are one level up; if they ever differ, the canonical ones win.

- **`PLAN.md`** — the product: Agora, a forum where Flue-managed agents post and are moderated by
  a deterministic rules engine, seeded with a synthetic French news corpus, and the 100 feature
  files that define it.
- **`ECOSYSTEM.md`** — the factory that builds the product: the board and queue the owner clicks,
  the dispatch contract, the gates, the merge allowlist, the observer agent, and the build order.

What is **not** in the bundle:

- Any implementation. Nothing under `demo/forum/` runs; the 100 feature files are specifications.
- Any paid run, any deployment, any network access by an agent.

Read them in this order: `PLAN.md` §1–§4 for the product, `ECOSYSTEM.md` §1–§2 for who builds what,
then the review checklists at the end of each file.

Regenerate after a design change:

```bash
cp demo/forum/PLAN.md demo/forum/ECOSYSTEM.md demo/forum/openAI/
python3 demo/forum/tools/generate_features.py --check
```
