# External review bundle

`PLAN.md` here is a verbatim snapshot of [`../PLAN.md`](../PLAN.md), prepared for an outside review
(ChatGPT). The canonical file is the one above this folder; if the two ever differ, the canonical
one wins.

What is in the bundle:

- `PLAN.md` — the design: two planes, the 100 features, the merge policy, the security model, the
  VPS plan, the risks, and a review checklist at the end.

What is not:

- Any implementation. Nothing in `demo/forum/` runs; the 100 feature files are specifications.
- Any paid run, any deployment, any network access by an agent.

Regenerate after a plan change:

```bash
cp demo/forum/PLAN.md demo/forum/openAI/PLAN.md
python3 demo/forum/tools/generate_features.py --check
```
