# Analysis Discovery Capture Gate

Status: accepted
Layer: SDD
Related ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
Related plan: `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
Related graph spec: `.lazy-harness/spec/platform/progressive-knowledge-graph.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 캡처 게이트
  - capture gate
  - 발견 기록 강제
- Applies when:
  - a non-trivial analysis/planning turn surfaces multiple layer concepts or multi-step plans
  - reviewing whether discovered facts stayed only in chat history
- Must:
  - capture discovered DDD/SDD/BDD/TDD/ADR/SSOT facts or plans the same turn into a record, candidate/draft store, planning artifact, or explicit `Discovery capture` judgement
  - stay silent when the turn already shows record/candidate/planning capture
  - recognize the active Pi `replace` / `functions.replace` transport as write evidence when it targets an eligible capture path
  - preserve STOP behavior for genuine chat-only analysis with no capture evidence
- Must not:
  - leave substantial analysis or multi-step plans only in chat history
  - treat an unrecognized Pi edit transport as proof that no same-turn capture occurred
- Record completion:
  - trigger cues or completion conditions change → update this SDD, ADR 0034, and the capture helper
  - mutation-transport recognition changes → update this SDD, the false-positive TDD, the
    analysis-discovery backlog, helper fixtures, and implementation map together
- Related records:
  - `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
  - `.lazy-harness/tests/capture-gate-false-positive.md`
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md`

## Purpose

Prevent substantial analysis/planning turns from leaving discovered DDD/SDD/BDD/TDD/ADR/SSOT facts or multi-step implementation plans only in chat history.

This gate complements the TDD layer-completeness gate. Layer completeness protects a record-writing path; analysis discovery capture protects the earlier analysis/planning path where the agent has not yet written records.

## Trigger

The gate applies when a response-completed payload strongly suggests that the agent performed non-trivial analysis/planning and mentioned multiple layer concepts or plan/backlog cues.

High-confidence cues include both:

1. Layer terms: at least three of `DDD`, `SDD`, `BDD`, `TDD`, `ADR`, `SSOT`, `Planning`, or their record directories.
2. Analysis/plan terms: `analysis`, `plan`, `planning`, `backlog`, `implementation plan`, `discovered`, `계획`, `분석`, `목차`, `코드분석`, or numbered multi-step work.

The helper should remain silent when the payload already shows record/candidate/planning capture.

## Completion contract

A triggered turn is complete only if at least one condition is true:

1. The same turn updates an affected layer record:
   - DDD: `.lazy-harness/domain/**`
   - SDD: `.lazy-harness/spec/**`
   - BDD: `.lazy-harness/behavior/**`
   - TDD: `.lazy-harness/tests/**`
   - ADR: `.lazy-harness/decisions/**`
   - SSOT: `.lazy-harness/ssot/**`
2. The same turn updates a planning artifact:
   - `.lazy-harness/planning/**`
3. The same turn updates a candidate/draft store:
   - `.lazy-harness/knowledge/candidates.jsonl`
   - `.lazy-harness/knowledge/graph-drafts.jsonl`
4. The response includes an explicit `Discovery capture` judgement naming DDD, SDD, BDD, TDD, ADR, SSOT, and Planning.
5. The agent stops and asks an option-gated question because layer ownership or plan scope is ambiguous.

## Required judgement

When facts are judged but not promoted to records yet, use:

```md
## Discovery capture

- DDD: updated/candidate/none because ...
- SDD: updated/candidate/none because ...
- BDD: updated/candidate/none because ...
- TDD: updated/candidate/none because ...
- ADR: updated/candidate/none because ...
- SSOT: updated/candidate/none because ...
- Planning: updated/candidate/none because ...
```

If any item is `candidate`, append structured lines to `.lazy-harness/knowledge/candidates.jsonl` or create/update a `.lazy-harness/planning/` backlog. When multiple DDD/SDD/BDD/TDD/ADR/SSOT/Planning discoveries are present, capture each distinct candidate; do not satisfy the gate by recording only the first missing layer.

## Candidate queue behavior

Unconfirmed discoveries may be captured as `KnowledgeCandidate` records per `.lazy-harness/spec/platform/progressive-knowledge-graph.md`.

Minimum candidate fields for manual capture:

- `id`
- `createdAt`
- `source`
- `utterance`
- `detectedLayers`
- `candidateType`
- `status`
- `confidence`
- `graphDraftIds`
- `evidence`
- `questions`

Canonical promotion still requires explicit confirmation or a future validated safe rule.

Multi-candidate turns may also be represented by the Record Decision Broker MultiCandidate Packet (`recordDecision.recommendedRecords`) when the turn evidence is only safe paths/tool summaries. That packet is journal/advisory evidence, not canonical record mutation.

## Lifecycle helper behavior

`check-analysis-discovery-capture.sh` runs from `on-response-completed.sh`.

It emits STOP text when:

- high-confidence analysis/planning + layer cues are detected,
- no DDD/SDD/BDD/TDD/ADR/SSOT/planning/candidate/draft file was touched,
- and the response does not contain a complete `Discovery capture` judgement.

The STOP options are:

- update affected layer records,
- append candidates or graph drafts,
- create/update planning backlog,
- add a local `Discovery capture` judgement,
- ask the user when ambiguous,
- or record an intentional skip in `.lazy-harness/logs/skipped.jsonl`.

## Examples

### Incomplete

A response says: "I analyzed the appointment redesign and found DDD/SDD/BDD/TDD/SSOT impacts. Plan: 1... 2... 3..." but touches no records or planning/candidate files.

### Complete with planning

The same analysis also creates a planning/backlog record with layer candidates and implementation map.

### Complete with judgement

The response includes a `Discovery capture` block naming all required layers and explaining `none` or `candidate` for each.

## Confirmed Pi mutation-transport direction

On 2026-07-14 the user selected **Honor SDD intent** after reviewing the verified
record/code conflict:

- canonical truth remains that same-turn record/candidate/planning capture silences the gate;
- Pi `replace` and `functions.replace` must be recognized as eligible mutation evidence;
- genuine chat-only analysis must continue to emit STOP;
- the user separately approved the focused transport seam; the helper now recognizes both
  Pi transport names without changing trigger thresholds or chat-only STOP behavior;
- focused fixtures, Python compilation, shell syntax, and the full framework self-test pass.

## Implementation map

- Status: `verified`
- Validation: Pi `replace`, `functions.replace`, and legacy `Edit` are silent for eligible
  capture paths; the otherwise identical chat-only payload still emits STOP.
- Primary files:
  - `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md` — this SDD operating standard.
  - `.lazy-harness/AGENTS.md` — concise grammar for ADR 0034.
  - `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh` — response-completed guard.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the helper.
  - `.lazy-harness/scripts/self-test.py` — protects helper behavior and AGENTS wording.
  - `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md` — architectural decision.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — projects Pi `agent_end` payloads and provides the opt-in structural trace.
- Key symbols:
  - `check_analysis_discovery_capture_helper` (`.lazy-harness/scripts/self-test.py`) — validates block/pass cases.
  - `run_analysis_discovery_capture_helper` (`.lazy-harness/scripts/self-test.py`) — fixture runner.
  - `Discovery capture` judgement — completion signal.
  - `agentEndTracePath` / `writeAgentEndTrace` (`index.ts`) — bounded content-free evidence for the unresolved live adapter path.
- Flow:
  1. Agent performs non-trivial analysis/planning.
  2. Helper detects layer + plan cues from response-completed payload strings.
  3. Helper checks same-turn record/planning/candidate capture or explicit judgement.
  4. Missing capture injects STOP text into the next assistant turn.
- Tests / protection:
  - `.lazy-harness/tests/capture-gate-false-positive.md` — live regression and verified Pi transport fixture.
  - `.lazy-harness/scripts/self-test.py#check_analysis_discovery_capture_helper` — protects `replace`, `functions.replace`, legacy `Edit`, explicit judgement, candidate capture, and genuine chat-only STOP.
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh`
  - `python3 -m py_compile .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy test --scope framework` — `ran=85`, `skipped=0`.
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — trace default-off/privacy/runtime-root/follow-up protection.
  - `.lazy-harness/evidence/2026-07-14-pi-agent-end-structural-trace.md` — privacy-reviewed fresh source-linked trace evidence and limits.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
  - SDD: `.lazy-harness/spec/platform/layer-completeness-gate.md`
  - TDD: `.lazy-harness/tests/capture-gate-false-positive.md`
  - SSOT: `.lazy-harness/ssot/knowledge-graph-storage.md`, `.lazy-harness/ssot/runtime-and-shared-state.md`
  - Planning: `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
- Machine index:
  - graph ids: `kg_sdd_analysis_discovery_capture_gate`,
    `kg_analysis_discovery_capture_pi_transport_impl_20260714`,
    `kg_analysis_discovery_capture_pi_transport_test_20260714`,
    `kg_pi_agent_end_structural_trace_impl_20260714`,
    `kg_pi_agent_end_structural_trace_test_20260714`
  - generated index key: `pending until implementation-index generator exists`

## Rule placement

- Rule: a same-turn DDD/SDD/BDD/TDD/ADR/SSOT/Planning record, candidate/draft, or
  planning mutation is authoritative capture evidence and must silence the capture gate;
  genuine chat-only analysis remains blocked.
- Scope: framework-global response-completed capture behavior
- Primary record: `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
- Why not AGENTS.md alone: AGENTS carries the concise capture obligation; this SDD owns
  transport recognition and completion semantics.
- Confirmation: user selected `Honor SDD intent`, then separately approved the focused
  helper-and-fixture seam on 2026-07-14.

## Discovery capture

- DDD: none because no domain vocabulary or business rule changed.
- SDD: updated because this record now documents the user-confirmed and validated Pi
  mutation-transport implementation while preserving genuine chat-only STOP behavior.
- BDD: none because no user-visible product workflow changed.
- TDD: updated because `.lazy-harness/tests/capture-gate-false-positive.md` owns the exact
  transport regression and now-verified fixture boundary.
- ADR: none because ADR 0034 already decides capture-before-completion and no new
  architectural trade-off was introduced.
- SSOT: none because no storage, ownership, configuration, or source-of-truth boundary changed.
- Planning: updated because `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
  records the approved seam, completed implementation, and validation evidence.
- Candidate store: none because the user resolved the truth and execution gates and the
  implementation is verified canonical behavior, not uncertain candidate knowledge.

## 2026-07-14 post-fix live conflict

A later live Pi turn received the same STOP after the assistant response itself contained the
complete seven-layer `Discovery capture` judgement. Direct execution of the current helper with
the same judgement, a STOP-shaped last user message, and todo-only recent tools emitted no output.
Therefore the earlier mutation-transport seam is verified, but it does not explain this recurrence.

The user selected **Payload trace** as the next direction: this SDD remains authoritative while the
Pi `agent_end` projection / queued-advisory path is investigated without weakening trigger thresholds.
The user separately approved the bounded instrumentation seam. The Pi adapter now provides an
opt-in, content-free `agent_end` structural trace under the canonical runtime root, with a fake
runtime regression covering default-off behavior, privacy, payload shape, and unchanged `followUp`
delivery. Focused, full-framework, and fake-runtime validation pass. A fresh source-linked Pi retry
then projected non-empty assistant/user text, recent `bash`/`bash`/`read` tools, and hook status `0`;
hook stdout/stderr were empty and no advisory was produced. The controlled complete seven-layer
judgement therefore does not reproduce the recurrence in current source. This does not identify the
historical stale/queued/runtime condition. The user selected **Close current remediation**: preserve
the historical occurrence, supersede the active cause candidate without promoting a cause, and make
no helper-threshold or continuation change. Durable structural evidence is summarized in
`.lazy-harness/evidence/2026-07-14-pi-agent-end-structural-trace.md`.

## Discovery capture — post-fix recurrence

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated because this contract remains authoritative and now records the confirmed
  contract-first payload-trace direction plus the unresolved runtime conflict.
- BDD: none because no user-visible product workflow changed.
- TDD: updated in `.lazy-harness/tests/capture-gate-false-positive.md` with the post-fix live
  recurrence, direct-helper counterexample, and bounded trace protection.
- ADR: none semantic because ADR 0034/0051 behavior is unchanged; ADR 0051's implementation map
  now points to the diagnostic symbols.
- SSOT: updated in `.lazy-harness/ssot/runtime-and-shared-state.md` for the runtime-only trace path.
- Planning: updated in `.lazy-harness/planning/analysis-discovery-capture-backlog.md` with the
  implemented trace seam and fresh current-source non-reproduction.
- Candidate store: the runtime-cause candidate was superseded by the user-confirmed remediation
  closure without promoting any historical cause; see
  `candidate-capture-gate-post-judgement-runtime-conflict-20260714`.
