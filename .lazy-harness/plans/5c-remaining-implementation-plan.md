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

### P0 — must do before declaring 5c complete

1. **Structured ask validator (5c-7)**
   - Status: partially implemented per detector.
   - Gap: no common validator ensuring each candidate has 3~5 options, recommended ID exists, confidence/gate rule consistent.
   - Deliverables:
     - shared `validateStructuredAsk(candidate)`.
     - `lazy:test` checks all fixture candidates.
     - cross-layer integrated ask checked for A/B/C/D options.

2. **Framework-owned doctor expansion**
   - Status: `lazy:test` is minimum gate only.
   - Goal: absorb C1~C17 style checks into `.lazy-harness/scripts/doctor.*`.
   - First checks to port:
     - ADR count/file sequence.
     - README/handoff/phase plan freshness.
     - XML parse.
     - JSONL parse.
     - branch policy.
     - external SaaS grep C17.
   - Deliverables:
     - `.lazy-harness/scripts/doctor.py` or `doctor.ts`.
     - `lazy:test` calls doctor smoke profile or doctor calls self-test.

3. **5c-9 Doctor C17 / External dependency invariant enforcement**
   - Status: not implemented.
   - Goal: grep `.lazy-harness/{triggers,hooks,framework,scripts}/` for external SaaS/API calls except allowed tools.
   - Validation:
     - fixture or temporary sample that fails C17.

### P1 — should do before real feature E2E

4. **5c-6 lint/typecheck drift detector**
   - Status: not implemented.
   - Goal: ingest tsc/eslint output and classify drift candidates.
   - Constraint: current `bun run typecheck:node` fails because dependencies/types are missing, so detector must distinguish environment-missing vs code drift.
   - Deliverables:
     - `triggers/lint-output.ts` or framework-owned equivalent.
     - fixtures for tsc error classification.

5. **5c-8 E2E demonstration**
   - Status: not implemented.
   - Goal: one realistic medivance change produces DDD/SDD/BDD/SSOT + cross-layer map candidates.
   - Deliverables:
     - documented E2E scenario.
     - command transcript or reproducible fixture.

### P2 — maintainability / scale

7. **Refactor `code-change.ts` monolith**
   - Status: 1720 lines.
   - Goal: keep `code-change.ts` as orchestrator and split detectors.
   - Suggested layout:
     - `triggers/detectors/ddd.ts`
     - `triggers/detectors/sdd.ts`
     - `triggers/detectors/bdd.ts`
     - `triggers/detectors/ssot.ts`
     - `triggers/detectors/cross-layer.ts`
     - `triggers/registries.ts`
   - Constraint: refactor only after 5c-5 behavior is pinned by tests.

8. **Package/dependency health**
   - Status: `bun run typecheck:node` currently fails due missing `electron-vite/node` and `@electron-toolkit/tsconfig`.
   - Goal: separate environment setup failures from framework regressions.
   - Deliverables:
     - doctor check that reports missing dependency as environment issue.
     - optional install/bootstrap doc.

## Recommended next sequence

### Step 1 — add structured ask validator

Why first now: cross-layer integrated ask exists, so enforce the output contract before more detectors are added.

Acceptance criteria:

- Every fixture candidate passes ask schema validation.
- recommended option ID exists.
- ambiguous/missing DDD cases recommend force gate path.

### Step 2 — framework-owned doctor skeleton

Why second: `lazy:test` can remain fast while doctor grows into broader C1~C17 audit.

Acceptance criteria:

- `doctor.py --profile smoke` equals current `lazy:test`.
- `doctor.py --profile full` includes ADR sequence + README/handoff stale checks.

### Step 3 — 5c-6/5c-9 and E2E

Why later: lint drift and external dependency enforcement are valuable but depend on clearer doctor profiles and environment classification.

## Do not do yet

- Do not split `code-change.ts` before 5c-5 behavior has exact tests.
- Do not reintroduce `.jcode` as primary doctor path.
- Do not push `.lazy-harness/` changes from any branch except `experimental/lazy-harness`.
- Do not mark 5c complete until 5c-5~5c-9 have explicit status and validation.
