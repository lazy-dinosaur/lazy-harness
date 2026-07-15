# Analysis Discovery Capture Backlog

Status: complete; Pi transport and bounded trace validated; current remediation closed; historical cause retained
Date: 2026-05-14
Updated: 2026-07-14
Related ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`

## Problem

During large change analysis, an agent may discover many DDD/SDD/BDD/TDD/ADR/SSOT facts and create a useful implementation plan, but leave both the discovered facts and the plan only in chat.

This breaks lazy-harness's record-as-output promise. Future agents cannot reliably recover the layer discoveries or the plan.

## Backlog

### 1. Grammar update

- Add an `Analysis discovery capture` rule to `.lazy-harness/AGENTS.md`.
- Trigger: non-trivial analysis/planning, code analysis with layer discoveries, multi-step plan/backlog generation.
- Required output: write affected records, write candidate queue entries, or include/persist `Discovery capture` judgement.

### 2. SDD standard

- Create `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`.
- Define trigger cues, required judgement shape, candidate queue behavior, warning vs stop thresholds.

### 3. Candidate queue

- Introduce `.lazy-harness/knowledge/candidates.jsonl` if absent.
- Store unconfirmed discovered layer facts before promotion to canonical records.
- Link candidates to graph drafts where possible.

### 4. Lifecycle helper

- Add `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh`.
- Detect high-confidence analysis/planning responses with no touched layer/planning/candidate records.
- Start as warning unless explicit layer terms and multi-step plan are present.

### 5. Self-tests

- Extend `.lazy-harness/scripts/self-test.py` with fixtures:
  - discovered DDD/SDD/BDD/TDD/ADR/SSOT terms + no records → fail/warn expected.
  - discovered terms + `Discovery capture` judgement → pass.
  - discovered terms + candidate/planning file touched → pass.

### 6. Manifests/sync

- Ensure new ADR/SDD/helper/candidate convention syncs to hosts via manifest if applicable.

### 7. Pi mutation-transport adapter (implemented and validated)

User-selected truth: **Honor SDD intent**. The user then approved one independently
reviewable helper-and-fixture seam:

1. Add focused helper fixtures for `replace`, `functions.replace`, legacy `Edit`, and a
   genuine chat-only payload.
2. Update only mutation-transport recognition needed for eligible capture paths; do not
   weaken layer/plan trigger thresholds or chat-only STOP behavior.
3. Run the focused helper fixtures, shell syntax check, framework self-test, record lint,
   graph hygiene, and diff check.
4. Update SDD/TDD/implementation-map evidence and graph facts only if implementation is
   separately approved and applied.
5. Stop on any payload-shape ambiguity or broader lifecycle redesign pressure and return
   to a new option gate.

The focused seam was implemented without changing layer/plan thresholds or genuine
chat-only STOP behavior.

## Acceptance criteria

- Agents cannot finish a high-confidence analysis/planning turn that mentions discovered layer facts and a plan without either records, candidates, or an explicit judgement.
- The planned change is protected by self-tests.
- `python3 .lazy-harness/scripts/self-test.py` passes.
- `python3 .lazy-harness/scripts/doctor.py --profile smoke` passes.
- Pi `replace`, `functions.replace`, and legacy `Edit` with eligible capture paths are silent.
- A genuine chat-only analysis payload still emits STOP.

## Discovery capture

- DDD: none because this gate/backlog introduces no domain vocabulary or business rule.
- SDD: updated because `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
  now records the user-confirmed `Honor SDD intent` direction, Pi mutation-transport
  requirement, and separate execution-approval boundary.
- BDD: none because no user-visible product flow changed.
- TDD: updated because `.lazy-harness/tests/capture-gate-false-positive.md` now preserves
  the live recurrence, exact Pi `replace`/`functions.replace` versus `Edit` reproduction,
  and the future fixture boundary.
- ADR: none because ADR 0034 already decides the capture requirement and no new trade-off
  was approved.
- SSOT: none because no storage, ownership, configuration, or source-of-truth boundary changed.
- Planning: updated because this backlog records the repeated false positive, the
  user-confirmed contract direction, the approved focused seam, and completed validation.
- Candidate store: none because the false-positive mechanism and desired behavior are already
  recorded; there is no new unconfirmed fact requiring candidate promotion.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md` — this backlog and completion state.
  - `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md` — authoritative contract.
  - `.lazy-harness/tests/capture-gate-false-positive.md` — regression and before/after evidence.
  - `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh` — Pi transport recognition.
  - `.lazy-harness/scripts/self-test.py` — focused and framework regression coverage.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — opt-in, content-free `agent_end` trace and canonical runtime-path resolution.
  - `.lazy-harness/ssot/runtime-and-shared-state.md` — runtime-only trace path and privacy boundary.
- Key symbols:
  - `Discovery capture` judgement — completion/capture signal.
  - `WRITE_TOOLS` (`check-analysis-discovery-capture.sh`) — recognizes Pi and legacy mutation transports.
  - `check_analysis_discovery_capture_helper` (`self-test.py`) — protects capture and chat-only cases.
  - `agentEndTracePath` / `writeAgentEndTrace` (`index.ts`) — collect bounded structural evidence without changing gate behavior.
- Flow:
  1. ADR defines framework direction.
  2. Backlog breaks it into grammar, spec, candidate queue, lifecycle helper, tests, and sync work.
  3. Implementation promotes this plan into code and validation.
- Tests / protection:
  - focused helper check passed.
  - shell syntax and Python compilation passed.
  - `.lazy-harness/bin/lazy test --scope framework` passed (`ran=85`, `skipped=0`).
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`, `.lazy-harness/ssot/runtime-and-shared-state.md`
- Machine index:
  - graph ids: `kg_plan_analysis_discovery_capture_backlog`,
    `kg_analysis_discovery_capture_pi_transport_impl_20260714`,
    `kg_analysis_discovery_capture_pi_transport_test_20260714`,
    `kg_pi_agent_end_structural_trace_impl_20260714`,
    `kg_pi_agent_end_structural_trace_test_20260714`
  - generated index key: `pending until implementation-index generator exists`

## 2026-07-04 — retro-loop promoted improvement: detect in-turn record writes (false-positive suppression)

Source: first retro-loop pattern promotion (capture-gate-false-positive ×3, user-approved via option gate; regression record `.lazy-harness/tests/capture-gate-false-positive.md`).

- Problem: `check-analysis-discovery-capture.sh` is a post-hoc text classifier; it fired three times in one session on turns whose discoveries were ALREADY appended to planning records in-turn (once even committed before the gate ran).
- Improvement candidate: before emitting, check whether `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,knowledge}` files were mutated during the turn window (mtime/git-status delta); stay silent when in-turn capture is detected, keep firing on genuine chat-only analysis.
- Constraint: do not weaken the gate before the improvement is approved and fixture-tested (false positives are cheaper than silent capture loss); fixture pair specified in the TDD record.
- Status: backlog — implementation needs its own approval slice.

## 2026-07-14 — repeated capture-complete false positive

- Evidence: retro feedback `fb-mrkkh8kv-t0` (`capture-gate-false-positive`, level 1).
- Reproduction: three architecture planning records were modified and the response named
  DDD, SDD, BDD, TDD, ADR, SSOT, and Planning, yet the next turn still received the STOP.
- Confirmed adapter gap: with the same planning path, synthetic payloads named `replace`
  and `functions.replace` emit STOP while legacy `Edit` is silent because the helper's
  `WRITE_TOOLS` set does not include the active Pi replace transport.
- Verification: the records were inspected directly; this is not a memory-only claim.
- User-confirmed truth: **Honor SDD intent** — same-turn capture silence is authoritative,
  Pi `replace` / `functions.replace` recognition is required, and genuine chat-only STOP
  remains required.
- Execution: the user approved the focused fixture + transport seam; the helper now
  recognizes Pi `replace` / `functions.replace` while preserving chat-only STOP.
- Validation: focused helper check, shell syntax, Python compilation, and framework
  self-test passed (`ran=85`, `skipped=0`).

## 2026-07-14 — post-judgement payload-trace proposal

### Confirmed evidence

- A live Pi follow-up repeated STOP after the assistant response contained a complete seven-layer
  `Discovery capture` judgement.
- Direct execution of the current helper with the same judgement, a STOP-shaped last user message,
  and todo-only recent tools is silent.
- Therefore the earlier `replace` / `functions.replace` recognition fix is verified but does not
  explain the new live recurrence.
- The user selected **Payload trace**: keep the current SDD completion contract authoritative and
  investigate the Pi adapter / queued-advisory path before considering any gate weakening.
- Candidate: `candidate-capture-gate-post-judgement-runtime-conflict-20260714`.
- Recurrence feedback: `fb-mrkm4qyk-v0`.

### Approved bounded seam — implemented and live-validated

1. Implemented: opt-in, runtime-local structural trace around Pi `agent_end` projection and
   `on-response-completed.sh` invocation.
2. Implemented: no conversation prose; only message role/content-kind metadata, assistant/user
   byte counts and hashes, recent-tool names, hook status/fingerprints, and advisory fingerprints.
3. Implemented and focused-tested: default-off, content-free, runtime-root-scoped trace plus
   unchanged standard Pi message extraction and queued `followUp` behavior.
4. Completed: a fresh source-linked Pi retry exited normally with tracing enabled; the helper
   returned status `0` with empty output and no advisory after a complete seven-layer judgement.
5. Stop boundary retained: do not change helper thresholds, completion semantics, or continuation
   behavior unless the trace establishes a concrete cause and a new seam is approved.

### Approval state

- Direction: user-confirmed (`Payload trace`).
- Instrumentation/source execution: separately user-approved and implemented.
- Downstream sync, canary work, and application source: out of scope.

### Closure decisions

- Historical recurrence: user selected **Close current remediation**. Preserve the occurrence and
  evidence, supersede the active cause candidate, and make no helper-threshold or continuation change.
- Legacy graph migration: user selected **Keep deferred**. The 37 legacy-schema rows remain untouched
  and outside this work unit; any future migration still requires `lazy-graph-migrate` batch approval.

### Current validation

- Focused `check_pi_package_layout_and_contract`: passed.
- Python compilation: passed.
- Bun syntax bundle: passed with package imports externalized because this checkout has no local
  package dependency install.
- Full framework self-test: passed (`ran=85`, `skipped=0`) after reviewer-blocker corrections.
- Reviewer closure matrix: canonical runtime resolver, forced trace-write failure with preserved
  `followUp`, 12-of-16 content-kind truncation, and newest-50-row retention all passed.
- Fresh source-linked live trace: passed on the normal-exit retry. The row recorded non-empty
  assistant/user projections, `bash`/`bash`/`read`, hook status `0`, empty hook output, and no
  advisory; the complete seven-layer judgement received no continuation. The first quiet-auto-exit
  attempt ended before `agent_end` and is excluded from behavioral evidence. Durable summary:
  `.lazy-harness/evidence/2026-07-14-pi-agent-end-structural-trace.md`.
- An earlier `lens_diagnostics mode=full` result reported two blocking `bare-except` findings,
  while direct reads showed explicit `except json.JSONDecodeError:` clauses. A fresh exact-path
  full scan now reports no errors and an anchored bare-except search is empty, strongly narrowing
  this to stale cache/line mapping. The append-only
  `candidate-pi-lens-bare-except-diagnostic-mismatch-20260714` history preserves both observations;
  final candidate closure remains separate from this trace seam.

### Reviewer blockers — closed

- Trace rows now cap retained message shapes, content-kind entries, metadata string lengths,
  recent tool names, and runtime-log rows; retention is atomic and keeps the newest 50 rows.
- The fake runtime now executes canonical `runtime_paths.py` fallback, forces an unwritable trace
  root while proving `followUp` still proceeds, and verifies content-shape and row retention bounds.
- Append-only candidate history now contains a latest-state event resolving SDD authority and
  leaving only the concrete runtime-cause question open.
- The resumed independent review supplied these blockers; the correction matrix and full framework
  test pass. Fresh source-linked reproduction passes without an advisory; the user closed current
  remediation while retaining the historical occurrence as non-canonical history.

## Discovery capture — post-fix recurrence

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated because the existing completion contract remains authoritative during tracing.
- BDD: none because no user-visible product workflow changed.
- TDD: updated because the live recurrence and helper counterexample require durable protection.
- ADR: none because this proposal remains inside ADR 0034/0051 and introduces no approved trade-off.
- SSOT: updated because the opt-in trace is now canonically routed to `LAZY_RUNTIME_ROOT`.
- Planning: updated because this record owns the completed trace seam, current-source non-reproduction,
  user-confirmed remediation closure, and separate graph-migration deferral.
- Candidate store: the capture-gate runtime-cause candidate is superseded without promoting a cause;
  the independent pi-lens diagnostic mismatch remains a candidate outside this seam.
