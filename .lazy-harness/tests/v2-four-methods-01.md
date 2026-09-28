# Four methods 01 — four-arm maintenance regression

## Rule digest

- Status: active
- Layer: TDD
- Scope: host-project
- Scope note: host-specific experiment package
- Aliases:
  - four methods 01
  - 네 방식 유지보수 회귀
- Applies when: four storage treatments are prepared or reviewed
- Must: run identical source facts, ordered update batches, latest-only artifact carryover, and identical final questions; preserve uncertainty, history, version and scope.
- Must not: expose private gold/future facts, infer missing converse facts, reset cumulative budget, or claim participant results from offline checks.

## Regression contract

`experiments/v2-four-methods-01/runner.mjs --offline` must exercise exactly 16 interleaved calls: create A/B/C/D, update1 D/C/B/A, update2 B/A/D/C, final-read C/D/A/B. It must validate official catalog-shaped rates and the admission bound before any participant call. Live `--run` is hash-frozen and stores request/raw response/parsed receipts exclusively, stopping on failure without retry.

- SDD: no independent delta — no product API, component contract, or production schema is adopted.
- BDD: no independent delta — no product user flow changes.
- SSOT: no independent delta — existing cumulative USD3 cap and ownership remain unchanged.
- DDD: no independent delta — synthetic research facts do not promote domain rules.

## Parent correction and predeclared semantic assessment

- Preparation/review run `849a1ec3-8977-48fd-b41b-b067d7842201` was blocked before participants. Rejected runner/fixtures are preserved in `.local/v2-reading-display-01/four-methods-{runner,fixtures}-rejected.*`; old manifests/receipts remain, v2 files are new.
- Repair: explicit exclusive active/inactive/degraded state space; US active→degraded update; M04 distinguishes one-alone insufficiency from both-together unknown sufficiency; r1 OR sufficient rule vs r2 AND necessary rule; unknown auditor permission query. C-only semantic hint is now common to all arms.
- `run` now checks positive AuthCheck type, selected SDK file hashes and fixture/source hashes before inference, and saves monotonic per-call durationMs (request-file writing excluded), with ttftMs explicitly null. SDK dependency closure, ancestor race and provider invoice/cancellation guarantees are not verified.
- Structural completion is NOT semantic success. After live calls, a human/LLM evaluator reads all 12 actual saved artifacts against the facts available at that stage, and all 40 final answers against private gold. Artifact grading records omissions, incorrect additions, stale-current values, historical preservation, internal contradictions, and representation adherence separately; final grading records correct/partial/wrong, unsupported uncertainty and evidence-ID completeness with quotations. A representation miss is a reported treatment failure, never a retrial or forced schema correction.
- Private gold is not used by the runner to censor, retry or repair answers. In particular, both prerequisites necessary implies one alone insufficient, but does not entail both sufficient. Different versions/scopes are not automatically contradictory. Nonapplication of one prohibition does not establish general permission.
- Initial broad validator was run contrary to the bounded no-scan instruction and failed on old artifact parsing. Preserve that failure; do not repeat it. This is distinct from the known root-relative layer-checker path bug. No full framework pass is claimed.
- Known cumulative cost before corrected review/execution: $2.11300136 = $2.03873044 + preparation $0.05324692 + reviewer $0.02102400. New workflow reserve $0.15 and participant cap $0.50 keep admission below existing $3. Actual child/runtime receipts must replace reservations at settlement.

### User-approved v3 envelope correction

- After actual first-call `artifact required` failure, the user selected `문자열·JSON 모두 허용 (Recommended)` in the native option gate. Preserve failed v2 response and old frozen runner snapshot `.local/v2-reading-display-01/four-methods-runner-v2-string-only.mjs`; run a fresh complete 16-call study, not a hidden retry or reuse of that A response.
- All methods accept nonempty artifact strings, JSON objects or arrays. `parse` preserves parsed values; `artifactText` keeps strings unchanged and JSON-serializes objects/arrays into maintenance and final prompts. No `[object Object]`, field dropping, semantic correction, or arm-specific transport rule.
- Focused regression exercises all16 stages with object→array→string artifacts, checks complete latest-value carryover including final reads, rejects empty/null/scalar artifacts, and uses the actual failed response text to verify object acceptance and next-prompt value preservation. Raw response bytes remain immutable. Transport tests do not grade meaning.
- Prior `$2.13548016`, new workflow reserve `.15`, participant cap `.50`. Current freeze is v3 manifest/receipt; fixture unchanged from corrected v2. Manual 12-artifact/40-answer grading and no semantic retry remain mandatory.
- Failure evidence: [first-call capsule](../evidence/v2-four-methods-01.md).
- v3r1 review correction: reviewer `7fc979e7-f756-4535-8e43-8623be848a2e` found one mismatch: prompt requests exactly one outer artifact key, parser accepted extra keys. Enforce that outer envelope only; nested representation keys remain unrestricted. Added extra-outer-key rejection and nested-key acceptance tests. No new participant call occurred. Preserve original v3 receipt/manifest/runner snapshot. Current prior `$2.15261600` includes that reviewer `$0.01713584`; new reserve `.15`, participant cap `.50`, current freeze `*-v3r1.json`.

### Actual v3r1 result and Parent assessment

- Actual16/16 completed, 12 artifacts and40 answers inspected; raw/parsed values match16/16. [Final evidence, Parent section authoritative](../evidence/v2-four-methods-01-result-v3.md) and [Parent structured assessment](../evidence/v2-four-methods-01-parent-assessment-v3.json) preserve initial labels and corrections separately.
- Observed protections to retain: final-answer accuracy does not detect omitted historical values (A update2); one-alone insufficiency differs from both-together unknown sufficiency (C M04); unchanged facts do not become unknown merely from missing current tags (B M03/M08); explicit r1 scope is not current-r2 conflict; conditional-only permission must not become bare positive permission (D U13). These are measured outcomes, not instructions to repair participant artifacts.
- No independent SDD/BDD/SSOT/DDD delta: the four explicit layer dispositions above remain applicable; no production schema or behavior changes. Cost and model/run limitations are in the evidence capsule.


## Implementation map

- `experiments/v2-four-methods-01/fixtures.json`: 12 initial Korean facts, two change batches, private gold, ten final questions.
- `experiments/v2-four-methods-01/runner.mjs`: bounded no-follow reads, four-arm orchestration, treatment prompts, latest artifact replacement, catalog admission, frozen manifest, offline checks, and live receipt preservation.
- `experiments/v2-four-methods-01/README.md`: executable command and limits.
