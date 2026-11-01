# Evidence-led review checklist

Use the sections relevant to the actual diff. This is a checklist for the current
reviewer; it neither starts agents nor changes tool/model permissions.

## Establish the review target

For a local worktree review, inspect staged, unstaged and new files separately;
`git diff` alone omits untracked files. For a commit or PR, name the exact base/head
and read the changed contracts, callers, tests and configuration. Do not silently
replace an empty diff with unrelated recent commits. If the target is unclear, ask
or report no reviewable change rather than manufacture findings.

## A finding must survive four questions

- What exact changed location causes the problem?
- Which input/state reaches it, and what incorrect outcome follows?
- Why do callers, types, validation, framework behavior or tests not prevent it?
- Is the consequence worth changing under this project's requirements?

If evidence is missing, investigate or mark an unresolved hypothesis separately.
Do not give an uncalibrated confidence percentage. Zero findings is a valid result.

## Review by failure path

| Area | What to trace | Evidence that changes the verdict |
| --- | --- | --- |
| Correctness | Input → validation → state change → observable result | Boundary values, missing/empty input, error handling and contract compatibility |
| Authorization | Identity → tenant/object ownership → read/write/side effect | A real cross-user path; authentication alone is not authorization |
| Injection | Untrusted source → transformations → SQL/shell/HTML/path/URL sink | Whether parameterization, encoding, allowlists or confinement cover this sink |
| Async/state | Retry, duplicate, timeout, cancellation and concurrent writers | A lost update, repeated charge/action, partial write or broken recovery path |
| Persistence/API | Transaction boundary, schema/defaults, migrations, pagination | Existing callers or stored records that become unreadable or inconsistent |
| Tests | Relevant success/refusal paths and the actual assertion | A regression can fail for the intended reason; mocks do not bypass the failure |
| Maintainability | Existing owner/abstraction, local conventions, change scope | A concrete comprehension or maintenance cost, not a personal style preference |
| Performance | Cardinality, hot path, bounds and existing batching | Actual unbounded work or measured regression; small fixed loops are not N+1 evidence |

For security, load the native `security-scan` skill when the diff crosses a real
boundary. Dependency advisories must match the resolved version and reachable use;
never invent a CVE from an old package name. Do not print secret values as proof.

## Common false positives

- Missing error handling already implemented by the caller or framework.
- Missing input validation on an internal function whose boundary validates it.
- A deliberate asynchronous background task mistaken for a forgotten await.
- A size/line-count threshold mistaken for complexity or a high-severity bug.
- Caching, memoization or a new abstraction proposed without a concrete need.
- Findings in unchanged code presented as regressions from this diff.
- Missing security machinery for a route that is neither exposed nor state-changing.

A weak test is not automatically a production defect. Explain the behavioral
coverage gap and its consequence; do not inflate severity to justify invocation.

## Severity and output

Use the native review record format. High severity requires a concrete material
security, correctness or data-loss scenario and an explanation of why current
guards fail. Otherwise report the appropriate lower severity or no finding.
Group duplicate root causes, keep the project's five-finding cap, and put any
additional material blockers in a linked local evidence note rather than hide them.

For each finding: location, trigger, consequence, existing-guard analysis and the
smallest coherent correction. Distinguish a confirmed bug, an unanswered question
and optional polish. Report what ran and what was not covered. A local assessment
is not an independent review, a security certification or an exact-commit gate receipt.

## Adaptation sources

Technique sources: ECC `agents/code-reviewer.md` and Addy Osmani
`skills/code-review-and-quality/SKILL.md`, at the commits recorded by the lifecycle
catalog. Retained: surrounding-context checks, concrete failure evidence and noise
filtering. Rejected: mandatory agent spawning, fixed model, confidence percentages,
generic line-count gates and blanket severity labels. Attribution remains in CREDITS.
