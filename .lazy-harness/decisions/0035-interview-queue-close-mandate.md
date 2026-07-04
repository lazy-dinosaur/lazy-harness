# ADR 0035 — Interview Queue Close Mandate

- Status: Accepted
- Date: 2026-05-17
- Layer: ADR (cross-cutting: AGENTS.md §2.3, interview-loop, tdd-cross-verify)
- Related: ADR 0019 (option-gate), Principle 21, tests/tdd-cross-verify-forcegate-loop.md

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - 인터뷰 큐
  - interview queue
  - 질문 닫기
  - open.xml
  - queue close
- Applies when:
  - user answers or picks an option for a queued question (e.g. "Q1=A", "go with C", "A")
  - working with `.lazy-harness/questions/open.xml`, interview-loop, or tdd-cross-verify gates
- Must:
  - close the queue entry the same turn via `interview-loop.ts --mode answer --question-id <id> --answer <A-D> --apply`
  - close each open question before generating new ones
  - count only newly created questions for `forceGate`, never the persisted queue
- Must not:
  - treat preview-mode (no `--apply`) invocations as satisfying the close obligation
- Record completion:
  - changes to queue-close flow or forceGate counting update this ADR and `.lazy-harness/tests/tdd-cross-verify-forcegate-loop.md`
- Related records:
  - `.lazy-harness/decisions/0019-ambiguous-detection-force-gate.md`
  - `.lazy-harness/tests/tdd-cross-verify-forcegate-loop.md`
  - `.lazy-harness/ssot/rule-sources.md`

## Context

`.lazy-harness/questions/open.xml` is the single source of truth for outstanding option-gate questions raised by triggers like `tdd-cross-verify`, `affected-test-runner`, and `interview-loop` itself. Questions only leave the queue when `interview-loop.ts --mode answer ... --apply` runs and writes:

1. `status="answered"` (or `superseded`/`deferred`) on the question element
2. A `decisions/<id>.jsonl` row in the decision log
3. Side effects from the chosen option (e.g. `tdd-require-test`, `defer`, `decision-log`)

Without those three side effects the queue still says "open". `tdd-cross-verify` previously treated *any* open question as `forceGate=true`, so the loop never terminated even after the user typed an answer in chat.

Observed failure mode (medivance host, 2026-05-17): user answered four cross-verify questions verbally in chat. None were piped through `interview-loop.ts`. Every subsequent tool call hit the `5d-3` trigger again, re-opened the same fingerprint (cache miss after fingerprint churn), and re-asked. AI followed the "looks fine, will close later" silent-skip path that §3 forbids.

## Decision

Treat `interview-loop.ts --mode answer --question-id <id> --answer <A|B|C|D> --apply` as the **only** way to close a queue entry. AGENTS.md §2.3 now states the rule explicitly:

> Queue close 의무: `.lazy-harness/questions/open.xml` 에 박힌 question 의 답을 사용자에게 받으면 같은 turn 안에서 반드시 close 처리한다. `--apply` 없으면 preview-only.

Practical contract for the AI agent:

1. When the user picks an option in chat (e.g. "Q1=A", "go with C", "A"), the AI must, in the same turn, run the CLI with `--apply` before any other tool call.
2. Preview-mode invocations without `--apply` do not satisfy the obligation. They are debugging aids.
3. If multiple questions are open, close each one before generating new ones.
4. `forceGate` triggers must only count *newly created* questions in the current trigger run, never the persisted queue. See `tests/tdd-cross-verify-forcegate-loop.md`.

## Consequences

**Positive**:
- The queue stays consistent with the conversation. No stale "open" entries.
- `tdd-cross-verify` and `affected-test-runner` can rely on the queue being trim, so `forceGate` is only true when *this* invocation surfaced new questions.
- Decision log captures every accepted option, making aftershock re-analysis deterministic.

**Negative**:
- The AI must remember the CLI invocation. Forgetting reproduces the loop. Mitigated by AGENTS.md §2.3 and the smoke test in `self-test.py` (`check_tdd_cross_verify`).
- The CLI requires `--apply` explicitly. Earlier silent-preview habits no longer suffice.

## Implementation map

Records and code touched:

- **AGENTS.md §2.3** — rule body (`.lazy-harness/AGENTS.md` lines ~64–73). Also mirrored into `.jcode/harness/05-lazy-harness.md` symlink target.
- **interview-loop CLI** — `.lazy-harness/scripts/interview-loop.ts`
  - `parseCliArgs` (line ~125): `--mode answer`, `--question-id`, `--answer/--option`, `--apply` flags.
  - `answerInterviewQuestion` (line ~451): writes status, decision log, returns effects.
  - `main` (line ~516): dispatches collect vs answer, gates persistence on `--apply`.
- **tdd-cross-verify** — `.lazy-harness/scripts/tdd-cross-verify.ts`
  - `forceGate: questions.length > 0` only counts *new* questions surfaced by the current run (post-2026-05-17 fix).
- **affected-test-runner** — `.lazy-harness/scripts/affected-test-runner.ts`
  - `needsInterview` checks `newQuestionFiles`, not persisted queue.
- **Smoke test** — `.lazy-harness/scripts/self-test.py`
  - `check_tdd_cross_verify` runs the trigger 3× and asserts run2/run3 forceGate=false even with an open `Q-*` queue entry left over.

### Cross-layer links

- SDD: `spec/lazy-sync-drift-detection.md` (companion contract for source-side dirty detection).
- TDD: `tests/tdd-cross-verify-forcegate-loop.md` (regression case).
- SSOT: `ssot/rule-sources.md` keeps the rule body anchored in AGENTS.md, not in host-local notes.

## Operational examples

```bash
# Close a single question with option C (defer):
bun .lazy-harness/scripts/interview-loop.ts \
  --mode answer --question-id Q-0dbf1eab9e51ffee --answer C --apply

# Inspect what would happen first (preview only — does NOT satisfy the rule):
bun .lazy-harness/scripts/interview-loop.ts \
  --mode answer --question-id Q-0dbf1eab9e51ffee --answer C
```

Treat the second form as a sanity check. The first form is the contract.
