# Trusted product CI bootstrap candidate — 2026-11-03

The product workflow has no job emitting the required `Product artifacts` check, and its SAST
step excludes the product's `demo/` sources. This candidate adds backend tests/package build,
React type/tests/build when feature 014 introduces the web package, and includes product code
in SAST. The new actions use verified official full commit SHAs, checkout credentials are not
persisted, permissions remain Contents read-only, caches are disabled and the job is bounded.
The session key is an explicit disposable CI fixture, never an operator credential.

Artifacts: [candidate workflow](ci.yml), [exact patch](ci.patch), [identities](identity.json).
The patch applies cleanly to the separate product checkout at `a50d6075b7aecff8f7c54fa47b5f385c16f4ccbb`.
The exact workflow was published in [PR3](https://github.com/OualidGuennif/aeion-autonomous-forum/pull/3)
after two real reviews. Hosted backend tests/package and the three security scans passed;
doc-diff and architecture coverage failed because the owning template documents were unchanged.
The corrected51-file198356-byte lot adds those documents and passed fresh complete GLM/Qwen
reviews, backend tests/package, knowledge checks, Graphify/Archify and all three security scans.
[PR4](https://github.com/OualidGuennif/aeion-autonomous-forum/pull/4) merged into protected main
as `63bdece8056136209e0e3d2e68dbf0879005fec9`; PR3 is closed and its evidence preserved.
These checks do not qualify PostgreSQL cutover or real browser behavior.

This is a trusted maintainer change. Worker scopes still forbid `.github/`; publisher credentials
were not broadened by an agent: the owner explicitly enabled temporary publisher Workflows
write for the reviewed maintainer CI import. Remote main now includes the committed backend.
Do not publish a workflow-only PR and call its missing-application failure a product success,
skip the required context, forge a check or infer authorship/reviews for the historical delta.

Official interfaces checked: [setup-java](https://github.com/actions/setup-java),
[setup-gradle](https://github.com/gradle/actions/blob/main/docs/setup-gradle.md),
[setup-node](https://github.com/actions/setup-node). Public `git ls-remote` resolved setup-java v5
to `b6effb05e454b25005698d916606bdc6ffcbf961`, Gradle actions v4 to
`0b6dd653ba04f4f93bf581ec31e66cbd7dcb644d`, and setup-node v4 to
`49933ea5288caeca8642d1e84afbd3f7d6820020` on 2026-11-03.
