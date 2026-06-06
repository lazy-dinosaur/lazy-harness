# Lifecycle Compare Mismatch Triage — 2026-06-04

Status: triaged
Layer: Planning
Date: 2026-06-04
Trigger: user approved Track A — lifecycle compare mismatch triage, with explicit reminder that lazy-harness is a framework and not Medivance-only.

## Scope

This triage uses Medivance as the high-volume primary dogfood signal, but does not treat Medivance as the framework target.

Cross-host scope:

- Primary signal: `/home/lazydino/dev/medivance`
- Secondary compare signal: `/home/lazydino/dev/medivance-pwa`
- Public/generic install signal: `/home/lazydino/dev/medivance-homepage` smoke/D07 observations; no prior normal-use compare wiring at triage time
- Source of truth: `/home/lazydino/dev/lazy-harness`

Boundary applied from `.lazy-harness/ssot/project-identity.md`:

```text
A Medivance finding may become a shared lazy-harness change only after classification as framework-general, host-specific, dogfood-only needing more cross-host validation, or no framework action.
```

## Evidence collected

Read first:

- `.lazy-harness/planning/lifecycle-compare-dogfood-handoff.md`
- `.lazy-harness/planning/dogfood-auto-recording-status-report.md`
- `.lazy-harness/ssot/project-identity.md`
- `.lazy-harness/planning/lifecycle-phase3-readiness-checklist.md`
- `.lazy-harness/spec/platform/hook-performance-measurement.md`

Implementation inspected:

- `.lazy-harness/hooks/lifecycle/on-response-completed.sh`
- `.lazy-harness/scripts/lifecycle-check.py`
- `.lazy-harness/scripts/lifecycle-parity-runner.py`
- `.lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh`
- `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py`
- `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh`
- `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh`
- `.lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh`
- `.lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh`

Code drift check:

```text
No lifecycle implementation file changes exist between installed host marker f7c31ec and source HEAD at triage time for the inspected lifecycle files.
Commits after f7c31ec are record/planning/candidate commits only for this lifecycle area.
```

## Compare log summary

At triage time:

| Host | Compare rows | Invalid | Mismatches | First | Last |
|---|---:|---:|---:|---|---|
| Medivance | 671 | 0 | 159 | 2026-05-31T06:44:08Z | 2026-06-04T08:45:11Z |
| Medivance PWA | 19 | 0 | 2 | 2026-05-31T06:44:08Z | 2026-06-04T06:25:44Z |

Readiness criteria still fail because mismatch counts are non-zero. However, all mismatches are now explained by known root-cause buckets and there were no unclassified rows.

## Root-cause buckets

### 1. Output normalization: trailing newline

Counts:

| Host | Count |
|---|---:|
| Medivance | 30 |
| PWA | 1 |

Pattern:

```text
legacyOutputEmitted=true
orchestratorOutputEmitted=true
legacyHelper == orchestratorHelper
legacyBodyBytes + 1 == orchestratorBodyBytes
bodyHashMatch=false
helperMatch=true
```

Observed helpers:

- `check-project-rule-placement.sh`
- `check-analysis-discovery-capture.sh`
- `check-tdd-cross-verify.sh`
- `check-affected-tests.sh`
- `check-layer-completeness.sh`

Likely cause:

- The legacy bash loop captures helper stdout with command substitution: `OUT=$(...)`, which strips trailing newlines.
- `lifecycle-check.py` stores `completed.stdout` as `firstOutput`, preserving the trailing newline.
- `lifecycle-parity-runner.py` already normalizes both sides with `.rstrip()`, but compare logging in `on-response-completed.sh` hashes raw `legacy_body` versus raw `firstOutput`.

Classification:

- Framework-general output normalization issue.
- Not Medivance-specific.
- Fix should be source-side and protected by tests.

Recommended fix candidate:

```text
Normalize orchestrator firstOutput to legacy semantics before compare hash/output body comparison, likely by rstrip-equivalent normalization in lifecycle-check or compare-log writer.
```

### 2. Sandbox fidelity: missing git commit context

Counts:

| Host | Count |
|---|---:|
| Medivance | 94 |
| PWA | 0 |

Pattern:

```text
legacyHelper=check-fix-regression.sh
orchestratorHelper=null
legacyOutputEmitted=true
orchestratorOutputEmitted=false
legacyBodyBytes=400
orchestratorBodyBytes=0
```

Relevant implementation:

- `check-fix-regression.sh` reads real host git metadata:
  - `git log -1 --pretty=%s`
  - `git rev-parse HEAD`
- `lifecycle-check.py --sandbox` currently copies only `.lazy-harness` into a temp directory and runs `git init -q`, so the sandbox has no real commit history.

Interpretation:

- These rows are compare-mode sandbox false negatives, not evidence that live orchestrator helper order differs.
- They occurred while Medivance's dogfood host state had a `Fix:` last commit; current Medivance HEAD at triage time is a merge commit, so recent `fix-regression` mismatch volume has dropped.

Classification:

- Framework-general sandbox-fidelity issue triggered by a git-dependent helper.
- Host signal comes from Medivance because Medivance had a relevant `Fix:` commit state, but the root cause is generic to any host with git-dependent response helpers.

Recommended fix candidate:

```text
Make sandbox lifecycle-check receive a minimal read-only git context, or make git-dependent helpers consume explicit env-provided git facts in compare sandbox mode. Do not copy Medivance-specific assumptions into the framework.
```

### 3. Sandbox fidelity: missing runtime/Jcode journals

Counts:

| Host | Count |
|---|---:|
| Medivance | 24 |
| PWA | 0 |

Pattern:

```text
legacyHelper=check-response-rule-audit.py
orchestratorHelper=null
legacyOutputEmitted=true
orchestratorOutputEmitted=false
legacyBodyBytes≈999-1021
orchestratorBodyBytes=0
```

Relevant implementation:

- `check-response-rule-audit.py` reads runtime state and tool-event journals:
  - `$LAZY_RUNTIME_ROOT/state/surfaced-rule-digests.jsonl`
  - `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl`
  - `.jcode/hooks/tool-events.jsonl`
- `lifecycle-check.py --sandbox` does not copy `.jcode` or runtime/shared state. It ignores `.lazy-harness/state` and logs/state-like paths.

Classification:

- Framework-general sandbox-fidelity issue for stateful audit helpers.
- Not Medivance-specific, but observed only in Medivance because it has high-volume stateful rule/search debt dogfood.

Recommended fix candidate:

```text
Create a sanitized sandbox state mirror for compare mode, or make lifecycle-check accept explicit read-only state inputs for stateful helpers. Avoid copying massive/raw `.jcode/hooks/tool-events.jsonl` wholesale unless privacy and performance are reviewed.
```

### 4. Sandbox fidelity: missing open-gates duplicate-suppression state

Counts:

| Host | Count |
|---|---:|
| Medivance | 11 |
| PWA | 1 |

Pattern:

```text
legacyHelper=null
orchestratorHelper=check-project-rule-placement.sh
legacyOutputEmitted=false
orchestratorOutputEmitted=true
legacyBodyBytes=0
orchestratorBodyBytes=1069
```

Relevant implementation:

- `check-project-rule-placement.sh` suppresses duplicate gate output with runtime `open-gates.json`.
- Current host state confirms open gate files exist:
  - `/home/lazydino/dev/medivance/.lazy-harness/state/open-gates.json`
  - `/home/lazydino/dev/medivance-pwa/.lazy-harness/state/open-gates.json`
- `lifecycle-check.py --sandbox` excludes `.lazy-harness/state`, so the sandbox does not see the duplicate-suppression fingerprint and re-emits the gate.

Classification:

- Framework-general sandbox-fidelity issue for stateful duplicate suppression.
- Cross-host evidence exists: both Medivance and PWA show the same failure mode.

Recommended fix candidate:

```text
Mirror or pass minimal open-gates state into the sandbox, or tag duplicate-suppression helpers as state-dependent and compare them with state fixtures rather than empty sandbox state.
```

## What this means for readiness

Current evidence is enough to stop passive collection and proceed to a source-side compare-fidelity patch. It is not enough to enable production/orchestrator mode.

Why not production yet:

- Compare mismatch count remains non-zero.
- The comparison tool itself is known to create false mismatches because sandbox state is incomplete and output body normalization differs.
- Therefore readiness cannot be judged until compare instrumentation is corrected.

Important nuance:

```text
The mismatches mostly indict compare-mode instrumentation/sandbox fidelity, not necessarily the live orchestrator algorithm.
```

Live orchestrator may match legacy better than the compare log suggests because live orchestrator would run in the real host root with real git/runtime state. But that should be proven by tests and/or improved compare mode, not assumed.

## Recommended next slice

Recommended implementation slice:

```text
Phase 3A — lifecycle compare fidelity patch
```

Subtasks:

1. Add a source-side `lazy lifecycle-compare-summary --format=md|json` CLI so future reviews do not depend on ad hoc Python snippets.
2. Normalize compare body hashing to legacy newline semantics.
3. Add sandbox fidelity fixtures for:
   - git-dependent `check-fix-regression.sh`
   - runtime/journal-dependent `check-response-rule-audit.py`
   - open-gates duplicate suppression in `check-project-rule-placement.sh`
4. Decide the minimal state mirror/env contract before copying runtime state:
   - git facts: safe minimal env/context recommended.
   - open-gates: safe minimal state copy likely acceptable.
   - `.jcode/hooks/tool-events.jsonl`: potentially large/raw; requires privacy/performance review before copying.
5. Re-run source self-test, host smoke, lifecycle parity, and compare dogfood after sync.

## Option gate for implementation

A. Implement Phase 3A compare fidelity patch: summary CLI + newline normalization + targeted state/git fixtures (Recommended)
B. Implement only `lazy lifecycle-compare-summary` first, no compare behavior changes
C. Implement only newline normalization first, then collect a smaller fresh dogfood window
D. Keep collecting compare logs without code changes
E. 직접 입력

Recommended: A, because mismatch root causes are already fully classified and passive collection will keep producing the same false mismatch categories.

## Implementation map

- Status: `verified-analysis`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — compare engine, compare log writer, legacy helper loop.
  - `.lazy-harness/scripts/lifecycle-check.py` — shadow/sandbox orchestrator, helper runner, sandbox root copy.
  - `.lazy-harness/scripts/lifecycle-parity-runner.py` — fixture parity runner that already rstrips bodies.
  - `.lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh` — git-dependent helper.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — runtime/Jcode journal-dependent helper.
  - `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` — runtime open-gates duplicate-suppression helper.
  - `.lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh` — runtime/shared path adapter.
- Flow:
  1. Compare mode runs sandbox `lifecycle-check.py` before legacy loop.
  2. Legacy loop records first helper output with bash command substitution semantics.
  3. Compare log hashes legacy body and orchestrator `firstOutput` without the same normalization/state context.
  4. Mismatch rows are emitted even when the underlying helper order is not necessarily wrong.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py` — existing opt-in compare/privacy coverage, needs new fidelity fixtures.
  - `.lazy-harness/scripts/lifecycle-parity-runner.py` — parity runner, already normalizes `.rstrip()`.
  - `.lazy-harness/bin/lazy lifecycle-parity --format=md --fail-on-mismatch`.
- Ownership boundaries:
  - Source changes belong in `/home/lazydino/dev/lazy-harness`.
  - Medivance/PWA/homepage are evidence hosts only.
  - Do not write Medivance-specific defaults into shared framework behavior without generalization proof.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/hook-performance-measurement.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`
  - Planning: `.lazy-harness/planning/lifecycle-compare-dogfood-handoff.md`
  - Planning: `.lazy-harness/planning/dogfood-auto-recording-status-report.md`
- Machine index:
  - graph ids: `kg_planning_lifecycle_compare_mismatch_triage_20260604`, `kg_lifecycle_compare_newline_mismatch`, `kg_lifecycle_compare_git_context_gap`, `kg_lifecycle_compare_runtime_state_gap`, `kg_lifecycle_compare_open_gates_gap`
  - generated index key: pending regeneration; generated index is derived, not canonical.

## Rule placement

- Rule: This is point-in-time lifecycle compare mismatch triage and implementation option framing.
- Scope: transient-plan / framework source triage.
- Primary record: `.lazy-harness/planning/lifecycle-compare-mismatch-triage-20260604.md`.
- Why not AGENTS.md: the findings are mutable dogfood evidence and implementation backlog, not universal grammar.
- Why not `.jcode`: this concerns shared framework source behavior and dogfood evidence, not private local Jcode workflow.
- Confirmation: user-confirmed request to proceed with Track A.

## Discovery capture

- DDD: none.
- SDD: candidate update needed for compare fidelity/state mirror contract if Phase 3A is approved.
- BDD: none; this is lifecycle instrumentation behavior, not user-visible app flow.
- TDD: new regression fixtures needed for newline normalization, git-dependent helper, runtime/journal helper, and open-gates duplicate suppression.
- ADR: no new ADR yet; if state mirror copies `.jcode` tool-event data, consider ADR or explicit option gate due privacy/performance trade-off.
- SSOT: project identity boundary already updated to prevent Medivance-only generalization.
- Planning: updated here with triage result and implementation option gate.

## 2026-06-04 Phase 3A source implementation

Status: source-implemented
Source state: pending commit at time of writing

Implemented the Recommended Phase 3A slice:

- added `lazy lifecycle-compare-summary --format=md|json`,
- normalized compare body hashes to legacy trailing-newline semantics,
- added sandbox-local runtime/shared roots,
- provided read-only git facts to sandbox helpers,
- mirrored bounded state tails for open-gates and response-rule journals,
- mirrored only message/session-correlated `.jcode/hooks/tool-events.jsonl` rows,
- added self-test fixtures for newline normalization, open-gates duplicate suppression, fix-regression git context, and bounded state/journal mirroring.

Validation:

```bash
python3 -m py_compile .lazy-harness/scripts/lifecycle-check.py .lazy-harness/scripts/lifecycle-compare-summary.py .lazy-harness/scripts/self-test.py
bash -n .lazy-harness/hooks/lifecycle/on-response-completed.sh .lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh
.lazy-harness/bin/lazy doctor --profile smoke --scope framework
.lazy-harness/bin/lazy lifecycle-parity --format=md --fail-on-mismatch
python3 .lazy-harness/scripts/self-test.py --scope framework
```

Result:

```text
Framework self-test green: ran=77, skipped=0.
```

Next dogfood step:

- Commit source patch.
- Sync `/home/lazydino/dev/medivance` and `/home/lazydino/dev/medivance-pwa` first, preserving compare-mode `.jcode` wiring.
- Run fresh compare-mode smoke rows and `lazy lifecycle-compare-summary` on new rows.
- Do not enable production orchestrator yet.

## 2026-06-04 Phase 3A downstream smoke result

Status: host-redogfood-smoke-passed
Source commit: `d5eba94c5600`

Completed the first downstream dogfood loop after the source patch:

- synced `/home/lazydino/dev/medivance`, `/home/lazydino/dev/medivance-pwa`, and `/home/lazydino/dev/medivance-homepage` to source commit `d5eba94c5600`,
- ran host self-test in all three hosts successfully,
- generated fresh isolated compare smoke logs in `/tmp/medivance-phase3a-compare.jsonl`, `/tmp/medivance-pwa-phase3a-compare.jsonl`, and `/tmp/medivance-homepage-phase3a-compare-rerun.jsonl`,
- summarized those logs with `lazy lifecycle-compare-summary --format=json --fail-on-mismatch`,
- all fresh smoke summaries reported `mismatches=0`, `failures=0`, and class `match-after-normalization:trailing-newline`,
- the interrupted homepage log `/tmp/medivance-homepage-phase3a-compare.jsonl` was also summarized and passed with `mismatches=0`.

Next readiness work:

- Continue collecting normal-use compare rows on synced hosts.
- Summarize only post-Phase-3A rows, because existing installed logs include old mismatch rows.
- Keep `LAZY_RESPONSE_COMPLETED_ENGINE=legacy` as production default until explicit replacement approval.

Discovery capture:

- DDD: none.
- SDD: no new contract.
- BDD: none.
- TDD: fresh three-host smoke validates Phase 3A compare-fidelity regression behavior.
- ADR: none.
- SSOT: source/dogfood boundary unchanged.
- Planning: immediate three-host redogfood smoke is closed; long-running compare readiness remains pending.
