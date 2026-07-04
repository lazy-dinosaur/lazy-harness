# TDD — Analysis-Discovery-Capture Gate False Positive (fires on capture-complete turns)

Status: open
Date: 2026-07-04
Layer: TDD
Related ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
Related SDD: `.lazy-harness/spec/platform/retro-loop.md`
Related planning: `.lazy-harness/planning/analysis-discovery-capture-backlog.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 캡처 게이트 오발화
  - capture gate false positive
  - discovery capture 오탐
  - STOP 게이트 중복
- Applies when:
  - the analysis-discovery-capture STOP gate fires and the agent believes capture already happened in-turn
  - improving or testing `check-analysis-discovery-capture.sh` heuristics
  - evaluating post-hoc gate heuristics against in-turn record mutations
- Must:
  - when the gate fires, VERIFY capture completeness against records (not memory) before claiming false positive
  - keep this scenario as the regression case for any heuristic improvement: a turn that appends analysis results to a `.lazy-harness` record (and even commits it) must be distinguishable from a chat-only turn
  - keep counting recurrences via `lazy retro feedback --kind capture-gate-false-positive`
- Must not:
  - silence or weaken the gate before a heuristic improvement is approved (false positives are cheaper than silent capture loss)
- Record completion:
  - heuristic changes to the gate update this TDD, the hook helper, and the analysis-discovery-capture backlog together
- Related records:
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
  - `.lazy-harness/spec/platform/retro-loop.md`

## Regression scenario (from live occurrences, 2026-07-04 session)

Three same-session occurrences (retro feedback ids `fb-mr6dziod-05`, `fb-mr6e1fxn-aq`, `fb-mr6e9dol-0l` — first pattern to reach the 3-repeat threshold):

1. Turn appends batch results/queue to `.lazy-harness/planning/memory-device-implementation-plan.md` (in one case already committed, `ebdcb53`) → gate still fires with the full "chat-only" warning.
2. Turn is a pure record-recap (next-steps summary read FROM existing records, zero new knowledge) → gate fires.
3. Root cause: the gate is a post-hoc text classifier over the response; it does not check whether canonical/planning records were mutated during the turn.

Expected behavior after a future heuristic improvement: gate stays SILENT when the turn's discoveries were written to records in-turn (detectable via record file mtimes/git status delta within the turn window), and still FIRES on genuine chat-only analysis.

## Protection

- Reproduction: any turn that (a) performs analysis, (b) appends findings to a planning record, then (c) ends — current hook fires regardless.
- Guard test candidate (when heuristic work is approved): fixture transcript + record-mutation marker → expect no gate emission; chat-only fixture → expect emission.
- Until then: this record + retro loop counting protect the knowledge; the gate remains as-is (false-positive-tolerant by design).

## Layer completeness judgement (ADR 0033)

- SDD impact: none now; a heuristic change would update the hook helper contract (backlog owns it).
- BDD impact: none (internal gate behavior, no user-visible flow change beyond noise).
- SSOT impact: none.
- DDD impact: none ("false positive" is established vocabulary).

## Implementation map

- Status: `evidence-recorded; heuristic fix pending approval`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh` — the gate whose heuristic this regression targets.
  - `.lazy-harness/retrospective/feedback.jsonl` — the three counted occurrences.
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md` — improvement backlog item (same slice).
- Tests / protection:
  - future fixture pair described above; until then `lazy retro report` pattern surfacing.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
  - SDD: `.lazy-harness/spec/platform/retro-loop.md`
