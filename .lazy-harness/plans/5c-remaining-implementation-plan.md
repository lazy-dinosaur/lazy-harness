# Remaining Implementation Plan — Lazy-Harness after 5c-4

- Date: 2026-05-12
- Branch: `experimental/lazy-harness`
- Baseline commits:
  - `8bfe2a8b` — 5c-4 SSOT detector + lazy:test
  - `69ba010a` — ADR 0022 framework-owned lazy:test gate
  - `8283117d` — quality hardening for self-test, pre-push, SSOT confidence, framework contract

## Current verified baseline

```bash
bun run lazy:test
# XML parse ok
# JSONL parse ok
# trigger fixtures ok {'ddd': 5, 'sdd': 1, 'bdd': 1, 'ssot': 4}

.lazy-harness/hooks/pre-push.sh origin dummy
# lazy:test all green, no tracked log dirty on success
```

## Done

| Area | Status | Evidence |
|---|---:|---|
| 5c-1 DDD detector | ✅ | `code-change.ts --layer ddd`, fixture coverage in `lazy:test` |
| 5c-2 SDD detector + DDD cross-ref + acronym | ✅ | `orderItemSchema`, `EMR/Emr` ambiguous fixtures |
| 5c-3 BDD detector | ✅ | `PatientSearchAutocomplete` fixture, NL + UI heuristic |
| 5c-4 SSOT detector | ✅ | `--layer ssot`, `ssot/registry.xml`, SSOT lifecycle helper |
| 5c-5 Cross-layer consistency map | ✅ | `TriggerRunResult.crossLayer`, integrated ask, exact gap fixtures in `lazy:test` |
| Framework-owned gate | ✅ | ADR 0022, `bun run lazy:test`, pre-push uses lazy:test |
| Branch policy | ✅ basic | ADR 0021, branch-aware pre-commit/pre-push |

## Not done / partial

### Done in this branch

- **5c-4 SSOT detector**
  - shared registry suppression via `.lazy-harness/ssot/registry.xml`.
  - helper/mapper/validator/normalizer/formatter/parser detection.
  - `--layer ssot` CLI + lifecycle helper.
- **5c-5 Cross-layer consistency map**
  - `TriggerRunResult.crossLayer` with exact `summary` + deduped `gaps`.
  - Integrated `--format ask` section with A/B/C/D options.
  - `lazy:test` pins exact fixture counts and gaps.
- **5c-7 Structured ask validator**
  - `validateStructuredAsk(candidate)` and `validateStructuredAsks(...)` added.
  - `TriggerRunResult.structuredAskValidation` added.
  - `lazy:test` now validates every fixture candidate plus cross-layer integrated ask.
- **5c-9 Doctor C17 + framework-owned doctor**
  - `.lazy-harness/scripts/doctor.py` added with smoke/full profiles.
  - `bun run lazy:doctor` added.
  - D01 XML, D02 JSONL, D03 ADR sequence/docs count, D04 README/handoff/phase freshness, D05 branch/hook policy, D06 C17 external dependency invariant.
  - `lazy:test` runs doctor smoke and a temporary C17 negative fixture.
- **5c-6 Lint/typecheck drift detector**
  - `.lazy-harness/triggers/lint-output.ts` added.
  - `bun run lazy:lint-drift` added.
  - Fixtures classify environment issues (`missing-type-definition`, `missing-config`, `missing-module`) separately from code drift (`type-mismatch`, `property-missing`, `eslint-rule`).
  - `lazy:test` pins fixture summaries.

### P0 — must do before declaring 5c complete

1. **5c-8 E2E demonstration**
   - Status: not implemented.
   - Goal: one realistic medivance change produces DDD/SDD/BDD/SSOT + cross-layer map candidates.
   - Deliverables:
     - documented E2E scenario.
     - command transcript or reproducible fixture.

### P2 — maintainability / scale

3. **Refactor `code-change.ts` monolith**
   - Status: ~1920 lines after 5c-7 validator integration.
   - Goal: keep `code-change.ts` as orchestrator and split detectors.
   - Suggested layout:
     - `triggers/detectors/ddd.ts`
     - `triggers/detectors/sdd.ts`
     - `triggers/detectors/bdd.ts`
     - `triggers/detectors/ssot.ts`
     - `triggers/detectors/cross-layer.ts`
     - `triggers/registries.ts`
   - Constraint: refactor only after 5c-8 behavior is pinned by tests.

4. **Package/dependency health**
   - Status: `bun run typecheck:node` currently fails due missing `electron-vite/node` and `@electron-toolkit/tsconfig`.
   - Goal: separate environment setup failures from framework regressions.
   - Deliverables:
     - doctor check that reports missing dependency as environment issue.
     - optional install/bootstrap doc.

## Recommended next sequence

### Step 1 — 5c-8 E2E demonstration

Why now: 5c-1/2/3/4/5/6/7/9 are pinned, so a realistic medivance change can exercise the complete detector cascade.

Acceptance criteria:

- One reproducible scenario produces DDD/SDD/BDD/SSOT candidates.
- Lint/typecheck drift detector fixture or transcript is included.
- Cross-layer map and structured ask report are present.
- Transcript or fixture is committed.

### Step 2 — refactor after behavior pin

Why later: `code-change.ts` is 1928 lines, but detector behavior is now better pinned. Split only after 5c-8 acceptance tests are in place.

## Do not do yet

- Do not split `code-change.ts` before 5c-8 behavior has exact tests.
- Do not reintroduce `.jcode` as primary doctor path.
- Do not push `.lazy-harness/` changes from any branch except `experimental/lazy-harness`.
- Do not mark 5c complete until 5c-8 has explicit status and validation.
