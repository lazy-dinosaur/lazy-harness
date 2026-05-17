# TDD — TDD/Affected forceGate ask-loop regression

Status: protected
Date: 2026-05-17
Layer: TDD (regression case for interview gate dedup)

## Bug

Symptoms observed on host `medivance` while editing `src/renderer/src/screens/Appointment/context/AppointmentProvider.tsx`:

- `5d-3 TDD Cross-Verify Gate` STOP block re-appeared on every `response.completed`.
- Same question ID `Q-0dbf1eab9e51ffee` was re-surfaced again and again.
- User answered (`A 로 하자`), but the gate kept firing because `recent_tool_calls` still mentioned the same source path.
- The chat scrollback filled with identical STOP blocks, blocking real work.

The dual symptom existed in `affected-test-runner` (`5d-3 Affected Test Gate`, question `Q-8e866d44709ff49c`) because it shared the same `forceGate` design.

## Root cause

Two scripts owned the same flawed pattern:

1. `.lazy-harness/scripts/tdd-cross-verify.ts`
   - `forceGate = failed > 0`
   - `failed` was derived from "source file has no matching test", which does not change between response.completed events. Even after the question was persisted to `open.xml`, the gate kept firing because `failed > 0` stayed true.
2. `.lazy-harness/scripts/affected-test-runner.ts`
   - `needsInterview = filePlans.some(plan => plan.question !== undefined)`
   - `plan.question` was assigned even when the question's fingerprint was already in the queue (`existing.has(fp)` was only used to skip pushing to `questions[]`, not to suppress `plan.question`).

In both cases the persistence dedup (`seenQueue.has(fp)`) only stopped duplicate XML rows; it never stopped the gate from re-firing. Result: ask-loop until the agent stopped editing or the source path fell out of `recent_tool_calls`.

The self-test even encoded the loop-causing behavior as expected:

- `tdd-cross-verify`: dedup run was checked with `expect_code=2` (i.e. the second run was expected to keep firing the gate).
- `affected-test-runner`: hook test asserted that a second `response.completed` for the same file kept surfacing `5d-3 Affected Test Gate` and the previously-queued question ID.

So both the implementation and the protection encoded "ask every time the source file is mentioned" — which is exactly the ask-loop.

## Fix

Ask-once policy:

- `tdd-cross-verify.ts`: `forceGate = questions.length > 0`. `questions[]` is populated only with brand-new (unseen) fingerprints, so `forceGate` is false once the question has been recorded.
- `affected-test-runner.ts`: `needsInterview` requires the file's question to be in the newly-pushed `questions[]`, not merely defined on the plan.
- self-test:
  - dedup `tdd-cross-verify` run expects `expect_code=0` and `forceGate=false`.
  - affected hook re-surface check now expects silence when the fingerprint is already queued, plus a fresh sanity case (new path → gate fires once → second response stays silent).

`failed` is still reported accurately so reporters/loggers can see the underlying state, but the user-facing gate fires once per fingerprint.

## Why this is correct under ADR 0019 / ADR 0020

- ADR 0019 (구조화된 옵션 ask) requires that the agent ask the user once with a clear A/B/C/D set.
- ADR 0020 (TDD Cross-Verify) requires that any source change without a matching test surface a structured ask.
- Neither ADR mandates that the same fingerprint be re-asked every turn. The ask-loop was an unintended emergent behavior.
- Persistence into `open.xml` is the canonical record that the question is open. Closing/answering it should happen through the interview-loop CLI (`scripts/interview-loop.ts`) or by deleting the entry from `open.xml`. The hook is for surfacing **new** items only.

## Implementation map

- Affected scripts:
  - `.lazy-harness/scripts/tdd-cross-verify.ts` — `verifyTddCrossReferences` return shape
  - `.lazy-harness/scripts/affected-test-runner.ts` — `needsInterview` derivation
- Affected lifecycle helpers (unchanged in code, but rely on the new contract):
  - `.lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh`
  - `.lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh`
- Protection:
  - `.lazy-harness/scripts/self-test.py` — `check_tdd_cross_verify`, `check_affected_test_runner`
  - Fresh-fingerprint sanity test added so the dedup never silently swallows a brand-new ask.

## Manual reproduction proof

```
$ for i in 1 2 3; do bun .lazy-harness/scripts/tdd-cross-verify.ts \
    --files .lazy-harness/triggers/fixtures/tdd-cross-verify/missing-test.ts \
    --queue /tmp/test-q.xml --format json; done
run 1: forceGate=true  questions=1  failed=1   # asks once
run 2: forceGate=false questions=0  failed=1   # stays silent
run 3: forceGate=false questions=0  failed=1   # stays silent
```

Before the fix, all three runs reported `forceGate=true` (the loop).

## Discovery capture

- DDD: none — no domain term changes. The "interview gate" / "ask-once" idea is part of the existing ADR 0019/0020 ubiquitous language.
- SDD: candidate — should formalize the `verifyTddCrossReferences` and `runAffectedTests` return contracts, especially the `forceGate` semantics ("new unanswered question exists this response"). Tracked under follow-up; not blocking this fix.
- BDD: none — no visible user flow; the change is internal gate semantics.
- TDD: updated — this record + new dedup/fresh-fingerprint assertions in `self-test.py`.
- ADR: none — ADR 0019 / 0020 intent unchanged; this is a defect fix that brings code back in line with intent.
- SSOT: none — no config/schema/ownership change.
