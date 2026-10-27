# AEion agent handover

Task: shipping-js-v1
Agent: 1
Context (native_report, active_context): 250000
Gate: 250000 tokens
Hard admission budget: 300000 tokens

## Objective

Implement export function shippingCents(country, weightGrams, subtotalCents). country must be FR, DE or ES (exact case). weightGrams is a positive safe integer and subtotalCents a nonnegative safe integer; reject all invalid values/types with TypeError. For FR shipping is free when subtotal>=5000; otherwise weight<=500 costs350, weight<=2500 costs550, heavier costs900. For DE/ES shipping is free at subtotal>=10000; otherwise weight<=1000 costs800, heavier costs1400. Validate all arguments before applying free shipping. Edit only src/pricing.js. No imports, files or tests. The supervisor executes protected checks in OpenShell after you stop.

## Preserved artifact

- File: `src/pricing.js`
- SHA-256: `c5b00e821d5a38519b019eb89a5eddb93f299646c6eff754ca001ff468704a90`

## Independent verification

- Passed: 0/14
- Remaining checks: fr_light, fr_boundary, fr_heavy, fr_free, eu_light, eu_heavy, eu_free, unsupported, bad_case, zero_weight, negative, float, boolean, unsafe

## Next action

Read this document and the preserved source. Complete or verify the implementation; the supervisor runs immutable Deno checks and probes the Hono API. Edit only src/pricing.js. This is a new session: no prior transcript, resumed session, compaction summary or tool state is required.
