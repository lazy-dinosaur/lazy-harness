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
  - testing analysis/correction LLM judgement plus successful current structural capture
  - evaluating real Pi callback, response hook and independent primary-answer delivery
  - verifying write/edit/insert/replace and namespaced transports
- Must:
  - when the gate fires, VERIFY capture completeness against records (not memory) before claiming false positive
  - distinguish current successful relevant record capture, failed/missing/unrelated proof, reuse, pending and no-record assertions; silence alone is not success
  - preserve both regressions: the verified before/after Pi mutation-transport matrix, the historical post-fix live recurrence, and the fresh source-linked controlled case that stays silent
  - keep counting recurrences via `lazy retro feedback --kind capture-gate-false-positive`
- Must not:
  - infer the post-fix live root cause from helper-only synthetic fixtures
  - treat IDs, fingerprints or no-record assertions as proof of semantic adequacy or execution approval
  - deploy the isolated B candidate without separate integration approval
- Record completion:
  - keep this as the primary B regression narrative; update the capture SDD only for independent packet/delivery deltas
- Related records:
  - `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
  - `.lazy-harness/spec/platform/retro-loop.md`

## B source-path repair — isolated candidate

The user approved real source repair after the corrected four-model pilot, not
another toy-prompt trial. Selected design1 keeps LLM-owned necessity/relevance,
mandatory durable capture, fact reasons/ownership and current approval; runtime
checks only actual structural evidence. Analysis and user-correction capture now
share that route; no other safety helper is removed. This section supersedes the
historical keyword STOP expectations below, not their recorded observations.

- Base: merged A `47db0958934b9d58151fd20ac976293f2c7764cc`, latest origin/main
  at isolated clone preparation. No dirty original or old experiment baseline imported.
- Adapter: typed `CaptureEvidence` joins real started/result callbacks to bounded
  canonical readback/fingerprints; no model-invented runtime fields.
- Response: complete raw main answer stays unchanged on valid, malformed, ambiguous
  or nonterminal markers. Capture assessment is a separate non-triggering custom
  message, not the caller's replacement answer or a new completion tool.
- Unchanged status: explicit no-record assertion does not force rewrite/reapproval.
  Missing packet is explicit unverified, never no-record. Required proof remains
  unverified on failed/missing/unrelated callbacks or changed bytes.
- Reuse: current canonical read plus current semantic judgement, without duplicate
  write. Bounded receipts survive unrelated last-40 projection; steer/session and
  work-unit invalidation clear them. Exact limits are in the capture SDD.

### Source-linked protection

`tests/lazy-harness/pi-capture-evidence.test.ts` exercises official Pi
ExtensionRunner dispatch, actual Pi read/write tools and real response hook/helper
processes. Third-party insert/replace names use mock completion events with real
fixture file mutation, not a claim of installed provider/native-question integration.
Tests include status/correction pollution, successful capture, failed insert/replace,
missing/args-only/unrelated receipts, epoch/steer, long history, current-read reuse,
changed bytes, malformed markers, trailing output-format text and separate delivery.
Existing destructive/option negatives use inert payloads; no hazardous command runs.
The standard self-test calls the source-side fixture; installed hosts without this
source test file run the shared transport checks only.

Baseline-negative export must preserve Git executable modes as well as bytes.
The first preparation mistakenly exported helper files as 0644, so initial missing
assessment failures are retained but are not capture-behavior evidence. Corrected
0755 baseline shows actual keyword STOP on unchanged status and no structural
assessment after actual successful write/read. Independent evidence logs retain
that preparation defect rather than replacing it with the corrected run.

### Validation boundary

The first focused source batch passed 20 adapter tests / 346 assertions. Later
root/error-delivery fixtures and bounded-history test refinement are checked by
the final standard gate, not retroactively included in that first count. The local
Bun source typecheck passed. At that prior B checkpoint, Pi SDK-target semantic checking reported five existing
diagnostics, independently reproduced against the untouched base export: two old
adapter signature mismatches and three locked dependency declaration diagnostics.
No dependency patch, skipLibCheck or ambient type suppression is used. Full final
state and gate outputs belong to the isolated external review evidence, not a
claim of live adoption or semantic-counterexample resolution.

The subsequent target-only follow-up is recorded in
`.lazy-harness/tests/pi-agent-package.md#pi-target-typecheck-closure`: all capture
cases now execute with actual Node22 and node:test, rather than claiming that
Node-only checking proves the previous Bun-hosted SDK test mode. Prior B results
and diagnostic evidence remain historical, not overwritten.

### Independent-review P2 correction

Review identified two concrete structural defects, reproduced through the real Pi
callback/full-hook fixture before correction: an extra closing marker was accepted
as `no-record-asserted`, and successful write → duplicate ID restart → failed
result retained an `evidence-linked` receipt. Both new regressions failed on the
previous frozen source; prior evidence is retained unchanged.

The parser now requires exactly one opening and one closing boundary. A duplicate
ID invalidates matching issued write/read receipts as well as a pending call;
unrelated receipts remain available. The bounded receipt scan also recognizes a
retained ID after recent-ID eviction. These changes enforce the existing SDD,
not new semantic or approval authority. The tests preserve the complete raw answer,
assert explicit unverified after failure with unchanged bytes, and retain valid
single-envelope/fresh-ID success controls. The final adapter suite has 25 cases;
exact-state results are kept in isolated review evidence, not inferred from the
previous 20-case green or the 300-second standard timeout.

The subsequent standard run ended with two failed checks, not a timeout. Read-only
triage found statically confirmed stale-contract expectations in the context-retry
fixture (forbidding any reused-work-unit system prompt) and lifecycle parity
fixture (requiring a prose-derived capture STOP). The governor retained only the
self-test tail, so these are not claimed as observed precise first-failure causes.
The approved fixture-only follow-up preserves reused fingerprint status, forbids
renewed grounding and positively requires capture guidance. Parity retains the
identical raw prose and all legacy/shadow/side-effect comparisons, but requires no
keyword-derived semantic STOP. Typed required/pending/success and other safety
controls remain protected by the existing adapter suite; a silent raw-prose case
alone is not evidence of successful capture. No production behavior was changed
in this follow-up, and prior failed validation evidence remains intact.

This review correction adds no independent SDD/BDD/SSOT/DDD delta; the existing
four-row matrix and implementation links below still govern. Final validation
uses the same standard checks with an explicitly approved 600-second budget,
not a release matrix or a changed permanent/default setting.

### Layer completeness — current B candidate

| Layer | Judgement |
|---|---|
| SDD | Independent packet/receipt/delivery delta in `spec/platform/analysis-discovery-capture-gate.md`; replaces the legacy cue-STOP contract only on two capture routes. |
| BDD | No independent product flow delta; main-answer/advisory transport is owned by the capture SDD and tested here. |
| SSOT | No independent ownership/config delta; CLI Tool Boundary already assigns semantic authority to the LLM. |
| DDD | No independent domain rule or vocabulary delta. |

### Current implementation map

- Status: `needs-review`
- Primary source: `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`,
  `packages/lazy-harness-pi/extensions/lazy-harness/capture-evidence.ts`.
- Lifecycle: `.lazy-harness/hooks/lifecycle/on-response-completed.sh`, both capture
  helpers, `.lazy-harness/scripts/lifecycle-check.py`.
- Tests: `tests/lazy-harness/pi-capture-evidence.test.ts`,
  `.lazy-harness/scripts/self-test.py#check_analysis_discovery_capture_helper`.
- Graph: `kg_b_capture_structural_impl`, `kg_b_capture_structural_test`.
- Limits: structural green cannot establish semantic relevance, truthful no-record,
  retention of all facts/reasons/ownership or real execution authorization. No new
  model sessions, C expansion, live sync or general superiority claim in this batch.

## Historical regression scenario (live occurrences, 2026-07-04)

The following sections preserve earlier observations and validation versions;
their legacy silence/keyword expectations are superseded by the B candidate above.

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
