# External review bundle

Updated 2026-11-01 after the design review. PLAN.md and ECOSYSTEM.md here are generated snapshots;
only relative links are rebased. Canonical files are one level up. Feature definitions are under
`../tools/specs_*.py`; generated Markdown, manifest and index live under `../features/`.

Read [product plan](PLAN.md), [factory contract](ECOSYSTEM.md), then the
[DeepSeek handoff](../DEEPSEEK_HANDOFF.md) and [validation record](../VALIDATION.md).
This package describes future behavior, not a built factory, qualified sandbox or deployed forum.
Execution is held until the owner explicitly confirms GitHub credential setup; DeepSeek must
not start the local/fake slices merely because it wakes or finds configured credentials.

Review the product/factory boundary, exact-artifact qualification, cancellation/recovery,
three-category corpus, held-by-default storage, phase/dependency graph and disjoint parallel
scopes. No builder may modify the factory, its evaluator or its own permissions.

From the repository root:

```sh
python3 -B demo/forum/tools/generate_features.py
python3 -B demo/forum/tools/generate_features.py --check
python3 -B -m unittest discover -s demo/forum/tools -p 'test_*.py' -v
```

Root work/changelog documents were not updated: the owner limited this pass to `demo/`.
