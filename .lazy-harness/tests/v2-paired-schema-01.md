# V2 paired schema 01 — focused transport and treatment regression

## Rule digest

- Status: advisory
- Layer: TDD
- Scope: host-project
- Scope note: host-specific experiment package
- Aliases:
  - paired schema 01
  - 짝 스키마 회귀
- Applies when: paired natural-language/relation-expression preparation is reviewed.
- Must: keep semantic slots, update/history rules, questions, order, and transport envelope identical across arms; exclude private gold and future facts; preserve failures and raw evidence.

## Regression contract

`node experiments/v2-paired-schema-01/runner.mjs --offline` performs one bounded, model-free checkpoint over exactly eight calls: create A,B; update1 B,A; update2 A,B; final-read B,A. It checks mixed object/array/string carryover, fixed A template versus fixed B relation form, 12 identical questions, no cross-arm leakage, exact outer envelope, arbitrary inner keys, selected SDK hashes, catalog admission, and the cumulative USD3 calculation. It makes no participant calls. Live results require separate manual semantic review and never turn structural pass into semantic pass.

- SDD: no independent delta — no product API, component contract, or production schema is adopted.
- BDD: no independent delta — no product user flow changes.
- SSOT: no independent delta — existing cumulative USD3 cap and ownership remain unchanged.
- DDD: no independent delta — synthetic research facts do not promote domain rules.

## Parent correction before live

- Original prep/review workflow `03dea501-9f5e-4cc0-bddd-620d4123cafd` blocked with zero participants. Preserve initial manifest/receipt/preservation manifest and `.local/v2-reading-display-01/paired-schema-{runner,fixtures}-rejected.*`. First source read attempted a directory; no content was read or mutation made; actual review status was then read directly.
- A now uses fixed Korean grammatical sentences, not key=value; B uses relation with named arguments. Nine equivalent semantic placeholders are checked exactly once in each. Same common meaning/history rules and identical per-stage facts/questions remain. Inner adherence and meaning are manually graded, never used for semantic retries.
- M11/M12 ask previous US state and previous maximum explicitly, in addition to current values. Gold requires old active and old30 days; correct current values alone cannot pass history retrieval.
- Restored inherited gates: stop terminal, unique answer IDs, finite/nonnegative token categories, input/output/context bounds, finite tier thresholds, per-call cost ceiling and remaining admission. Focused tests exercise duplicate IDs and invalid terminal/usage/catalog inputs.
- Current freeze is `review-manifest-v2.json`, `offline-receipt-v2.json`, `preservation-manifest-v2.json` (exact six files, no recursive copying). Manual result review must cover all6 artifacts and24 answers; no live calls yet is expected at prereview, not evidence of semantic correctness or a reason to require earlier unreviewed calls.
- Known prior `$2.28961740` = `$2.22667620` + preparation `.04539116` + reviewer `.01755004`; new reserve `.15`, participant cap `.20`. Missing/failed usage must remain explicit. No broad validator.


## Implementation map

- `experiments/v2-paired-schema-01/runner.mjs`: bounded runner, shared-slot prompts, two-arm order, envelope parser, official runtime/auth/catalog checks, receipts.
- `experiments/v2-paired-schema-01/fixtures.json`: 12 initial facts, two update batches, 12 questions, private gold excluded from prompts.
- `experiments/v2-paired-schema-01/README.md`: purpose, rationale, measurement, limits, and commands.
- `experiments/v2-paired-schema-01/preservation-manifest-v2.json`: current exact source/fixture/protocol/receipt identities and hashes; original `preservation-manifest.json` remains historical.
- Primary research: `../planning/v2-vision-feasibility-research.md`; test map: `../planning/v2-research-test-map.md`.
