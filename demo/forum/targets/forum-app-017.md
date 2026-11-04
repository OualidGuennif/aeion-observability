# 017 — Strict JSON request validation for the existing Quarkus forum

Implement the feature in the pinned product, not in the controller. This is the Java adaptation of the canonical strict-request-validation feature: reject unknown fields, wrong types, missing required fields and oversized request bodies before endpoint handlers act. No dependency or build-file change is needed.

## Existing interfaces

The application uses Quarkus REST/JAX-RS with Jackson, Java 25. Existing JSON POST routes:

Existing source package is `local.aeion.forum`. The installed Jakarta REST API does not define
`Response.Status.UNPROCESSABLE_ENTITY`; return numeric HTTP 422 via `Response.status(422)`.
Use a small self-contained filter; no unused resource-info injection or reflection registration
is needed. The prior generated candidate failed compilation solely on that unsupported enum.
This is a verified toolchain constraint, not permission to weaken validation or the external test.

The last rejected candidate stripped the leading slash from incoming paths but kept leading
slashes in its route-map keys, so it skipped validation entirely. Whatever normalization you
choose, every configured route must match it: `/api/auth/login` must reach its shape validator.
The complete review envelope is 24000 characters including instructions and file labels. Keep
the implementation focused; do not duplicate the injected contract in an extra candidate test.

- /api/auth/register and /api/auth/login: exactly username and password, both required JSON strings. AuthResource currently takes Map<String,String>; do not rely on Jackson's implicit string coercion to validate JSON token types.
- /api/threads: exactly title and body, both required JSON strings. This route also requires its existing cookie and CSRF token; preserve them.
- /api/auth/logout: bodyless mutation; preserve its cookie/CSRF requirements.

AuthResource delegates business validation to AuthService. A valid-shaped wrong login still returns 401 with error=invalid_credentials; a valid-shaped weak password still follows the existing 400 business refusal. Do not weaken those existing tests. Existing QuarkusTestDatabase and @WithTestResource fixtures are required for every new @QuarkusTest.

## Required behavior

- Shape refusals return 422 with JSON {"error":"invalid_request","fields":["field_path"]}. Include field paths only, never supplied values, raw payloads, credentials or exception text.
- Unknown keys, missing required fields, non-string values and non-object JSON must be refused before the endpoint handler is invoked. Reject coercion rather than accepting numbers as strings.
- Enforce the existing 16384-byte body ceiling for every body-bearing route before authentication and JSON parsing; read at most cap+1 bytes if handling the stream. Never parse an unbounded stream. Restore a bounded validated entity stream for the actual endpoint; valid requests must keep working.
- An oversized unauthenticated POST /api/threads must return 413, not pass through to session/CSRF processing first.
- Preserve current session, CSRF, security headers, business refusal codes and all existing acceptance tests.
- No arbitrary body/exception logging. Keep the changes small and readable; they must fit the current complete-review envelope. A pre-matching validation filter is one possible implementation, not a required class name or a license to bypass handler security.

## Acceptance and scope

The external RequestValidationContractTest is injected by the controller and must not be edited. Gradle test must pass with this contract and all existing product tests. Write only inside the admitted Java main/test scopes; no controller, .git, toolchain, environment or build-file changes. Do not copy the protected contract into your returned artifact. Return only the complete changed/new implementation files and any small independent candidate test needed.
