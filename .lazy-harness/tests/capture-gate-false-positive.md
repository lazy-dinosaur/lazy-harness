# TDD — Analysis-Discovery-Capture Gate False Positive (fires on capture-complete turns)

Status: active
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
  - verifying Pi `replace` / `functions.replace` tool-name recognition against legacy `Edit`
- Must:
  - when the gate fires, VERIFY capture completeness against records (not memory) before claiming false positive
  - keep this scenario as the regression case for any heuristic improvement: a turn that appends analysis results to a `.lazy-harness` record (and even commits it) must be distinguishable from a chat-only turn
  - preserve both regressions: the verified before/after Pi mutation-transport matrix, the historical post-fix live recurrence, and the fresh source-linked controlled case that stays silent
  - keep counting recurrences via `lazy retro feedback --kind capture-gate-false-positive`
- Must not:
  - infer the post-fix live root cause from helper-only synthetic fixtures
  - change helper thresholds, the Pi adapter, or the continuation path before a separately approved payload-trace seam
- Record completion:
  - heuristic changes to the gate update this TDD, the hook helper, and the analysis-discovery-capture backlog together
- Related records:
  - `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
  - `.lazy-harness/spec/platform/retro-loop.md`

## Regression scenario (from live occurrences, 2026-07-04 session)

Three same-session occurrences (retro feedback ids `fb-mr6dziod-05`, `fb-mr6e1fxn-aq`, `fb-mr6e9dol-0l` — first pattern to reach the 3-repeat threshold):

1. Turn appends batch results/queue to `.lazy-harness/planning/memory-device-implementation-plan.md` (in one case already committed, `ebdcb53`) → gate still fires with the full "chat-only" warning.
2. Turn is a pure record-recap (next-steps summary read FROM existing records, zero new knowledge) → gate fires.
3. Root cause: the gate is a post-hoc text classifier over the response; it does not check whether canonical/planning records were mutated during the turn.

Expected behavior after a future heuristic improvement: gate stays SILENT when the turn's discoveries were written to records in-turn (detectable via record file mtimes/git status delta within the turn window), and still FIRES on genuine chat-only analysis.

## 2026-07-14 Pi tool-name regression and focused fix

After three architecture planning records and a complete seven-layer judgement were
persisted, the gate fired again. The occurrence is recorded as retro feedback
`fb-mrkkh8kv-t0`.

A synthetic payload against the current helper reproduced the adapter gap:

| `recent_tool_calls[].name` | Eligible planning path | Before | After |
|---|---|---|---|
| `replace` | yes | STOP | silent |
| `functions.replace` | yes | STOP | silent |
| `Edit` | yes | silent | silent |
| none (chat-only) | no | STOP | STOP |

Source inspection confirmed the former `WRITE_TOOLS` set included legacy
`Write`/`Edit`/`MultiEdit` variants but not Pi's `replace` names. The user selected
**Honor SDD intent** and separately approved the focused seam. The helper now recognizes
`replace` and `functions.replace`; genuine chat-only STOP behavior remains unchanged.

## Protection

- Live reproduction: a capture-complete architecture turn received STOP before the fix;
  records were verified directly before classifying it as a false positive.
- Automated fixture: Pi `replace`, `functions.replace`, and legacy `Edit` with an eligible
  planning path are silent; a genuine chat-only payload still emits STOP.
- Focused helper check, shell syntax, Python compilation, and the full framework self-test
  pass.

## Layer completeness

- SDD: updated `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md` because
  the user confirmed its same-turn-silence contract as authoritative and the record now
  names Pi mutation-transport recognition plus the separate execution gate.
- BDD: no independent delta because no user-visible product workflow changed.
- SSOT: no independent delta because no config, storage, ownership, or source-of-truth
  invariant changed.
- DDD: no independent delta because no domain term or business rule changed.

## Implementation map

- Status: `verified`
- Validation: focused helper regression passed and framework self-test completed with
  `ran=85`, `skipped=0`.
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh` — the gate whose heuristic this regression targets.
  - `.lazy-harness/retrospective/feedback.jsonl` — counted live occurrences, including
    `fb-mrkkh8kv-t0`.
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md` — improvement backlog
    and exact Pi tool-name reproduction.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — opt-in structural trace for the unresolved live adapter path.
  - `.lazy-harness/ssot/runtime-and-shared-state.md` — runtime-only trace path and no-raw-content boundary.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_analysis_discovery_capture_helper` protects
    Pi `replace`, `functions.replace`, legacy `Edit`, candidate/planning capture, explicit
    judgement, and genuine chat-only STOP.
  - focused synthetic result: `replace` → silent, `functions.replace` → silent,
    `Edit` → silent, chat-only → STOP.
  - `.lazy-harness/bin/lazy test --scope framework` passed (`ran=85`, `skipped=0`).
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` protects trace default-off/privacy/runtime-root/follow-up behavior.
  - `.lazy-harness/evidence/2026-07-14-pi-agent-end-structural-trace.md` records the fresh source-linked current-source non-reproduction without raw conversation/tool content.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
  - SDD: `.lazy-harness/spec/platform/retro-loop.md`
  - SSOT: `.lazy-harness/ssot/runtime-and-shared-state.md`
- Machine index:
  - `kg_analysis_discovery_capture_pi_transport_impl_20260714`
  - `kg_analysis_discovery_capture_pi_transport_test_20260714`
  - `kg_pi_agent_end_structural_trace_impl_20260714`
  - `kg_pi_agent_end_structural_trace_test_20260714`

## Discovery capture

- DDD: none because no domain vocabulary or business rule changed.
- SDD: updated because `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
  now records the user-confirmed authoritative behavior, Pi transport requirement, and
  separate execution-approval boundary.
- BDD: none because no user-visible product flow changed.
- TDD: updated because this record now preserves the live recurrence, before/after Pi
  transport matrix, focused fixture, and full validation evidence.
- ADR: none because ADR 0034 already decides capture-before-completion and no new trade-off
  was approved.
- SSOT: none because no storage, ownership, configuration, or source-of-truth rule changed.
- Planning: updated because `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
  records the approved and completed focused seam.
- Candidate store: none because the mismatch was confirmed, approved, implemented, and
  validated through canonical SDD/TDD/Planning records.

## Rule placement

- Rule: capture-complete turns using the active Pi mutation transport must be silent, while
  genuine chat-only analysis must continue to emit STOP.
- Scope: framework-global analysis-discovery capture regression
- Primary record: `.lazy-harness/tests/capture-gate-false-positive.md`
- Contract owner: `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
- Why not AGENTS.md: this record owns the reproduced regression and fixture boundary, not
  the universal capture grammar.
- Confirmation: user selected `Honor SDD intent` and then approved the focused helper
  helper seam on 2026-07-14; the regression is now fixed and validated.

## 2026-07-14 post-fix recurrence

After the transport fix passed focused and framework tests, a later live Pi turn still received
STOP even though the assistant response contained all seven required `Discovery capture` buckets.
Running the current helper directly with the same assistant judgement, a STOP-shaped last-user
message, and todo-only recent tools is silent. This proves the earlier `replace` adapter gap is not
a sufficient explanation for the new occurrence; it does not yet prove whether the remaining fault
is `agent_end` response projection, stale/queued advisory delivery, root/runtime skew, or another path.

The recurrence is counted as `fb-mrkm4qyk-v0`. The unresolved cause lives in
`candidate-capture-gate-post-judgement-runtime-conflict-20260714`. The user selected
**Payload trace**: preserve the SDD contract and investigate the adapter/continuation payload before
weakening the gate, then separately approved the bounded instrumentation seam. The adapter now
writes an opt-in, content-free runtime trace and the fake-runtime fixture protects default-off
behavior, structural fingerprints, no raw content, and unchanged queued `followUp` delivery.
A fresh source-linked Pi retry completed normally with trace enabled. Its single structural row
contained non-empty assistant (`605` bytes) and last-user (`592` bytes) projections, recent
`bash`/`bash`/`read` tools, hook status `0`, empty hook stdout/stderr, and no advisory. The complete
seven-layer judgement received no continuation. The current source path therefore does not reproduce
the recurrence for this controlled case. The historical stale/queued/runtime cause is not canonical.
The user selected **Close current remediation**: retain this regression history, supersede the active
cause candidate, and authorize no helper-threshold or continuation change. See
`.lazy-harness/evidence/2026-07-14-pi-agent-end-structural-trace.md`.

## Discovery capture — post-fix recurrence

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated because the governing capture contract remains authoritative during investigation.
- BDD: none because no user-visible product flow changed.
- TDD: updated because this record now preserves the post-fix live recurrence, direct-helper
  counterexample, bounded trace fixture, and the boundary against claiming an unverified cause.
- ADR: none because ADR 0034/0051 already govern the contract and runtime bridge.
- SSOT: updated in `.lazy-harness/ssot/runtime-and-shared-state.md` for the runtime trace path.
- Planning: updated because instrumentation and fresh source-linked trace are complete and current
  remediation is user-closed.
- Candidate store: superseded without promoting a historical cause.
