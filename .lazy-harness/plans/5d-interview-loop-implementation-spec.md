# 5d Interview Loop Implementation Spec

Date: 2026-05-12
Branch: `experimental/lazy-harness`
Status: draft-ready for implementation
Owner boundary: `.lazy-harness/` framework work only

## 0. Verified starting point

Before 5d planning, the 5c/post-5c foundation has been verified:

```bash
bun run typecheck:node
python3 .lazy-harness/scripts/doctor.py --profile full --format json # D07 ok
bun run lazy:test
bun run lazy:doctor
.lazy-harness/hooks/pre-push.sh origin dummy
```

Current known-good state:

- 5c-1~5c-9 complete.
- DDD/SDD/BDD/SSOT detectors extracted from `code-change.ts`.
- `code-change.ts` is orchestration-only, 376 lines.
- `lazy:doctor` full profile has D01~D07.
- D07 package health is `ok` after `bun install` + Prisma generated client.
- `node_modules/` and `prisma/generated/` are intentionally ignored generated/runtime artifacts.

## 1. Purpose

5d turns the 5c detectors from “candidate detection” into an actual **human-AI interview loop**:

```text
trigger/candidate/conflict
→ structured options
→ human answer
→ durable decision/spec update
→ aftershock re-analysis
→ repeat until stable or depth cap
```

The goal is not to ask more questions. The goal is to make every unavoidable question:

1. structured,
2. traceable,
3. answerable once,
4. replay-safe,
5. capable of updating DDD/SDD/BDD/SSOT/TDD consistency.

## 2. Inputs and source rules

### Primary inputs

- 5c detector candidates from `.lazy-harness/triggers/code-change.ts --layer all`.
- Cross-layer gaps from `crossLayer.gaps`.
- Structured asks already attached to candidates and integrated cross-layer ask.
- User answer text from the next turn or a recorded answer file.
- Current registries/specs:
  - `.lazy-harness/domain/ubiquitous-language.xml`
  - `.lazy-harness/spec/spec-language.xml`
  - `.lazy-harness/behavior/*`
  - `.lazy-harness/ssot/registry.xml`
  - `.lazy-harness/questions/open.xml` or successor file
  - `.lazy-harness/logs/decisions.jsonl`

### Ownership rules

- `.lazy-harness/` owns the loop.
- `.jcode/` may inject/remind/wrap, but cannot be the primary source of truth.
- Do not put operational state only in chat history.
- Every accepted answer must be written to a durable lazy-harness artifact.

## 3. Core model

### 3.1 Interview question

A question is a structured gate created from a trigger candidate, cross-layer gap, or aftershock conflict.

Required fields:

```ts
interface InterviewQuestion {
  id: string;
  criterionId: '5d-1' | '5d-2' | '5d-3' | '5d-4' | '5d-5' | '5d-6';
  source: 'trigger-candidate' | 'cross-layer-gap' | 'tdd-cross-verify' | 'aftershock';
  status: 'open' | 'answered' | 'superseded' | 'deferred';
  depth: number;
  candidateName?: string;
  layer?: 'ddd' | 'sdd' | 'bdd' | 'ssot' | 'tdd';
  question: string;
  recommended: string;
  options: InterviewOption[];
  crossRef?: object;
  createdAt: string;
  answeredAt?: string;
  decisionId?: string;
}

interface InterviewOption {
  id: string;
  label: string;
  description?: string;
  effects: InterviewEffect[];
}
```

### 3.2 Interview effect

An effect is a planned durable change. It must be previewable before write.

```ts
type InterviewEffect =
  | { kind: 'ddd-register-term'; term: string; aliases?: string[]; reason: string }
  | { kind: 'sdd-register-contract'; name: string; endpoint?: string; reason: string }
  | { kind: 'bdd-register-scenario'; name: string; given: string; when: string; then: string }
  | { kind: 'ssot-register-utility'; name: string; domain: string; kindHint: string }
  | { kind: 'tdd-require-test'; target: string; suggestedPath: string }
  | { kind: 'decision-log'; summary: string; reason: string }
  | { kind: 'defer'; reason: string };
```

### 3.3 Decision record

Every applied answer creates a JSONL entry:

```json
{
  "id": "D-YYYY-MM-DD-NNN",
  "source": "interview-loop",
  "questionId": "Q-...",
  "selectedOption": "A",
  "summary": "Register 자동완성 as DDD term and autocomplete as SDD gap",
  "effects": [],
  "aftershockDepth": 1,
  "createdAt": "..."
}
```

## 4. Implementation phases

### 5d-0: Spec and fixtures

Deliverables:

```text
.lazy-harness/plans/5d-interview-loop-implementation-spec.md
.lazy-harness/questions/open.xml                    # if missing, create empty valid container
.lazy-harness/questions/answered.jsonl              # optional durable answer log
.lazy-harness/schemas/interview-question.schema.json
```

Success criteria:

- Spec exists.
- Existing `lazy:test` and `lazy:doctor` stay green.
- Remaining work is explicit and staged.

### 5d-1: Open question queue

Deliverables:

```text
.lazy-harness/scripts/interview-loop.ts
.lazy-harness/questions/open.xml
.lazy-harness/triggers/fixtures/interview-loop/cross-layer-gap.json
```

Behavior:

1. Read a trigger result JSON from stdin or `--input`.
2. Convert candidate asks and cross-layer integrated ask into question entries.
3. Deduplicate by stable fingerprint:
   ```text
   source + layer + candidateName + question + normalized crossRef
   ```
4. Write/update `.lazy-harness/questions/open.xml`.
5. Print structured summary.

CLI:

```bash
bun .lazy-harness/scripts/interview-loop.ts \
  --input /tmp/trigger-result.json \
  --mode collect \
  --format json
```

Acceptance:

- Given a fixture cross-layer result, it creates expected open questions.
- Re-running does not duplicate questions.
- `lazy:test` pins question count and IDs/fingerprints.

### 5d-2: Human answer ingestion

Deliverables:

```text
.lazy-harness/scripts/interview-loop.ts --mode answer
.lazy-harness/logs/decisions.jsonl append path
.lazy-harness/questions/open.xml status transition
```

Behavior:

1. Accept `--question-id` and `--answer A|B|C|...`.
2. Resolve option effects.
3. Preview effects by default.
4. Apply only with explicit `--apply`.
5. Append decision log.
6. Mark question answered.

CLI:

```bash
bun .lazy-harness/scripts/interview-loop.ts \
  --mode answer \
  --question-id Q-... \
  --answer A \
  --apply \
  --format json
```

Acceptance:

- No apply without `--apply`.
- Invalid option fails with structured error.
- Decision log appends valid JSONL.
- Answered question is no longer open.

### 5d-3: TDD cross-verify gate

Based on ADR 0020.

Deliverables:

```text
.lazy-harness/scripts/tdd-cross-verify.ts
.lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh
.lazy-harness/triggers/fixtures/tdd-cross-verify/missing-test.ts
.lazy-harness/triggers/fixtures/tdd-cross-verify/covered-feature.test.ts
```

Cross-checks:

| Check | Meaning |
|---|---|
| Test exists | Changed src code has matching test/spec file or explicit deferral. |
| Test ↔ BDD | Test name/body references scenario given/when/then. |
| Test ↔ DDD | Test domain nouns are known DDD terms or force-gated. |
| Test ↔ SDD | Test input/output matches SDD contract/procedure/schema. |
| Test ↔ SSOT | Helpers/mappers under test are registered or force-gated. |

Initial implementation may start with only “test exists” plus structured ask, then expand to all 5 checks.

Acceptance:

- Missing test fixture produces force-gate question.
- Covered fixture passes.
- Ambiguous mapping produces structured ask, never silent skip.

### 5d-4: Aftershock re-analysis

Deliverables:

```text
.lazy-harness/scripts/aftershock-check.ts
.lazy-harness/retrospective/metrics/aftershock-depth.jsonl
```

Behavior:

After an answer applies effects:

1. Re-run relevant detector scope.
2. Rebuild cross-layer map.
3. Compare old vs new gaps.
4. If new conflict/gap appears, create follow-up question at `depth + 1`.
5. Stop at `maxDepth=3` and escalate to human.

Acceptance:

- Fixture answer creates second-level question.
- Depth cap prevents infinite loop.
- Aftershock metrics are appended.

### 5d-5: Hook integration

Deliverables:

```text
.lazy-harness/hooks/lifecycle/helpers/check-interview-loop.sh
.lazy-harness/hooks/lifecycle/on-response-completed.sh update
```

Behavior:

- `response.completed` hook runs sync checks.
- If trigger/cross-layer/TDD has force gate question, it denies stop and injects continuation context.
- If only recommendations exist, it warns but allows stop.
- Loop guard prevents repeated identical denials.

Acceptance:

- Force question creates deny payload.
- Repeated same question does not create infinite deny loop.
- Hook output is concise and cites question ID.

### 5d-6: Real medivance feature walkthrough

Deliverables:

```text
.lazy-harness/intent/active/<feature>.xml
.lazy-harness/retrospective/e2e/5d-<feature>-interview-loop.md
.lazy-harness/traceability/<feature>.xml
```

Acceptance:

- One actual feature reaches depth >= 2.
- At least one user answer updates a durable artifact.
- TDD gate either passes or produces explicit deferred decision.
- Retrospective records time cost, saved ambiguity, and friction.

## 5. Gate policy

Use ADR 0019 confidence × gate rule:

| Case | Gate | Behavior |
|---|---|---|
| high | auto+review | Apply if safe, log review marker. |
| medium | recommend | Ask optional, do not block stop. |
| low | force | Stop requires answer. |
| ambiguous | force + structured ask | Never silent skip. |

5d must treat TDD missing coverage as force when feature code was changed and no explicit deferral exists.

## 6. Validation strategy

Minimum gates per implementation slice:

```bash
git diff --check
bun run lazy:test
bun run lazy:doctor
.lazy-harness/hooks/pre-push.sh origin dummy
```

Additional targeted checks:

```bash
bun .lazy-harness/scripts/interview-loop.ts --mode collect --input <fixture> --format json
bun .lazy-harness/scripts/interview-loop.ts --mode answer --question-id <id> --answer A --format json
bun .lazy-harness/scripts/tdd-cross-verify.ts --scope <fixture> --format json
```

Self-test additions should pin:

- open question count,
- stable fingerprints,
- duplicate suppression,
- answer transition,
- decision JSONL validity,
- TDD missing-test force gate,
- aftershock depth cap.

## 7. Non-goals

- Do not implement DB migrations.
- Do not touch medivance feature code during 5d framework build, except fixture/e2e phase.
- Do not use `.jcode` as primary state store.
- Do not make `pre-push` depend on external SaaS/network.
- Do not auto-edit DDD/SDD/BDD/SSOT registries without preview/apply split.

## 8. Remaining roadmap after this spec

### Immediate remaining work

1. Implement `interview-loop.ts --mode collect`.
2. Add `.lazy-harness/questions/open.xml` if absent.
3. Add interview-loop fixture and self-test pin.
4. Implement `--mode answer` preview/apply.
5. Add decision log schema check.

### Next remaining work

6. Implement TDD cross-verify v0: test existence + force gate.
7. Add TDD fixtures and hook helper.
8. Implement aftershock-check with max depth 3.
9. Integrate response.completed hook once CLI behavior is stable.

### Later remaining work

10. Optimize doctor profiles if pre-push cost is too high:
    - `smoke`: cheap structural checks.
    - `full`: includes D07 typecheck.
    - optional `ci`: full + slow e2e.
11. Run one medivance feature through 5d depth >= 2.
12. Enter 5e real feature release flow.
13. Prepare framework extract/portability plan.
14. Push/PR after final audit.

## 9. Definition of done for 5d

5d is done when:

- Open questions are durable and deduplicated.
- Human answers can be ingested and logged.
- Applied answers update or explicitly defer framework artifacts.
- Aftershock re-analysis can create follow-up questions with depth cap.
- TDD cross-verify gate covers at least test existence and one cross-layer check.
- Hook integration can block stop only for force gates.
- One real medivance feature completes an interview loop with depth >= 2.
- `lazy:test`, `lazy:doctor`, and pre-push all pass.
