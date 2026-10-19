# TDD — Runtime session usage collection

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - Pi OMP token accounting
  - Parent Reader token totals
- Surface terms:
  - collectRuntimeUsage
  - input output cacheRead cacheWrite totalTokens
- Applies when:
  - collecting explicitly inventoried Pi/OMP session JSONL usage
- Must:
  - validate every assistant usage entry, duplicate identity and safe aggregate
  - retain reported totalTokens independently of cache components and include error/aborted entries
  - label omitted attempts, unlogged retries, task success and billing as unverified
- Must not:
  - publish real session/usage reports as fixtures or treat scripted zero usage as efficiency evidence

## Approved scope and contract

The user approved the read-only offline collector and synthetic tests. The eventual comparison uses common blocking Reader scope and GPT-6 Sol medium, not a silently substituted model. This preparation grants no live benchmark, credential use, paid execution, global update or stable-support promotion.

`bun packages/lazy-harness-pi/scripts/collect-runtime-usage.ts <manifest.json>` emits `runtime-session-usage/v1`. Input: runtime=pi|omp, measurement=offline|live (caller-declared), sessions=[{role:parent|reader,path}]. Exactly one Parent is required. Relative paths resolve from the manifest directory. Caller inventory is not attestation.

Require one leading session header, unique canonical file paths/session ids/assistant entry ids, nonnegative safe integer counters and safe sums. For OMP only, `ompSessionHeader` permits one v1 title prelude immediately before the unique session header; Pi admission is unchanged. Missing usage fails; missing cost remains an incomplete runtime estimate. Do not re-add cache fields to reported totals. Output omits message/title content; paths and identities still make real outputs private. `inventoryCompletenessVerified=false`, `providerRequestCount=null`, `unloggedRetryUsage=unknown`, `taskSuccess=not-evaluated`. Estimated cost is not a receipt.

## Implementation map

- `packages/lazy-harness-pi/scripts/collect-runtime-usage.ts#collectRuntimeUsage`: manifest validation, per-file/per-role aggregation; `decodeUsage` validates counters.
- `packages/lazy-harness-pi/omp/session-header.ts#ompSessionHeader`: common OMP identity decoder for accounting and Reader join.
- `packages/lazy-harness-pi/scripts/collect-runtime-usage.test.ts`: synthetic sessions only; counters, caches, errors, title/header negatives, duplicate/symlink/copied inputs, malformed usage/cost, overflow, CLI relative paths and input preservation.
- `.lazy-harness/spec/platform/pi-agent-package.md`: public CLI contract and Experimental boundary.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`: offline suite registration.
- Fresh results: `.lazy-harness/planning/repository-publication-review.md`; no copied real reports or historical validation promoted to fresh evidence.

## Layer completeness

- SDD: independent read-only CLI/manifest/output interface, recorded in `.lazy-harness/spec/platform/pi-agent-package.md`.
- BDD: no independent delta; no product UI or paid-run flow.
- SSOT: no independent delta; no installed/runtime/global configuration or ownership change.
- DDD: no independent delta; preserves native usage field meanings.
