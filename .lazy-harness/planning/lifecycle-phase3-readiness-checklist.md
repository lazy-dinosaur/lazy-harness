# Lifecycle Phase 3 Readiness Checklist

Status: active-readiness-checklist
Date: 2026-05-26
Scope: `response.completed` production hook replacement readiness
Related planning: `.lazy-harness/planning/performance-optimization-plan.md`
Related SDD: `.lazy-harness/spec/platform/hook-performance-measurement.md`

## Decision summary

Current dogfooding is positive but not enough for production hook replacement.

```text
Phase 3 may start with readiness cleanup and checklist work.
Phase 3 must not yet replace `.lazy-harness/hooks/lifecycle/on-response-completed.sh` with `lifecycle-check.py`.
```

## Current evidence snapshot

Checked roots:

- `/home/lazydino/dev/lazy-harness`
- `/home/lazydino/dev/medivance`
- `/home/lazydino/dev/medivance-pwa`

Positive evidence:

- `lazy lifecycle-parity --format=json --fail-on-mismatch` passes in all three roots.
- Current lifecycle parity suite: 12 fixtures, 0 failures.
- Hook timing evidence exists in all three roots:
  - source: 5326 timing rows.
  - Medivance: 10022 timing rows.
  - Medivance PWA: 1682 timing rows.
- Recent `hook-total` timing is stable enough for analysis:
  - source avg≈677ms, p90≈947ms, max≈1492ms.
  - Medivance avg≈687ms, p90≈850ms, max≈974ms.
  - Medivance PWA avg≈666ms, p90≈769ms, max≈838ms.
- `lazy graph-hygiene --format=json` reports `ok: true` across all three roots.

## Go/no-go checklist

### Required before production replacement

- [ ] Production hook replacement has an explicit ADR or checklist approval entry.
- [ ] `lazy lifecycle-parity --fail-on-mismatch` passes in source, Medivance, and Medivance PWA after latest source sync.
- [x] Lifecycle parity suite includes real payload categories beyond synthetic fixtures via sanitized candidate intake.
- [x] All current open gate state is closed, expired, or classified as synthetic/stale runtime state.
- [x] `record-audit` graph missing paths are classified as source-only/host-owned/stale or resolved when run with canonical source.
- [ ] Medivance and Medivance PWA have enough recent real-use rows after latest sync.
- [ ] Replacement plan includes a legacy comparison/debug fallback flag.
- [ ] Replacement plan includes rollback instructions.
- [ ] Full source validation passes:
  - `.lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- [ ] Host validation passes in Medivance and Medivance PWA:
  - `.lazy-harness/bin/lazy test`

### Nice-to-have before replacement

- [ ] Medivance Project Profile interview fields reduced or explicitly deferred.
- [ ] Medivance PWA Project Profile artifacts improved or explicitly deferred.
- [x] `record-audit` and `graph-hygiene` agree on source-only vs actionable graph path issues when `record-audit --source /home/lazydino/dev/lazy-harness` is used.
- [ ] Capability Registry dogfood has at least one real-use evaluation window complete.

## Current blockers

### B1 — open runtime gates cleaned

Cleanup result:

- Added `lazy gate-state list|clear-stale` runtime helper.
- Cleared stale open gates older than 1 hour across source, Medivance, and Medivance PWA.
- Verification after cleanup reports count=0 in all three roots.

Current classification:

- `.lazy-harness/state/open-gates.json` remains runtime state, not canonical memory.
- Future readiness runs should use `lazy gate-state list --format=json` before replacement decisions.

### B2 — record-audit graph paths require canonical source argument

Current corrected record-audit evidence:

- Medivance with `--source /home/lazydino/dev/lazy-harness`: missingPaths=0, sourceOnlyPaths=33.
- Medivance PWA with `--source /home/lazydino/dev/lazy-harness`: missingPaths=0, sourceOnlyPaths=34.

Classification:

- This is not an actionable graph hygiene blocker when record-audit is run with the canonical framework source.
- The earlier missingPaths result was caused by passing the host itself as `--source` during the check.
- Readiness checklist should require the canonical source argument for installed-host record audits.

Remaining cleanup:

1. Document canonical source usage in the readiness runbook.
2. Consider making `record-audit` warn when `--source` resolves to the same host `.lazy-harness` tree.
3. Optional: add a regression fixture for installed-host graph rows pointing to source-only operational records.

### B3 — PWA dogfood signal is still thinner than Medivance

Current evidence:

- PWA has 1682 hook timing rows, enough for timing, but only 0 actions rows and 18 validations rows.
- PWA was just synced to latest Capability Registry and received validation capabilities.

Required cleanup:

1. Let PWA run under normal dogfood for at least one evaluation window.
2. Re-check route/action/validation/capability evidence.
3. Do not block forever on PWA parity if source+Medivance are strong, but explicitly classify the risk.

### B4 — readiness checklist is new and not yet exercised

This file is the first explicit checklist. It needs one complete check-run after B1/B2 cleanup.

## Recommended next implementation slices

1. **Gate state cleanup helper** — implemented
   - `lazy gate-state list|clear-stale` inspects and clears stale runtime `open-gates.json`.
   - Synthetic self-test protects dry-run, prefix filtering, mutation, and non-canonical behavior.

2. **Record-audit source-argument guard** — implemented
   - `record-audit` warns when `--source` points at the same host instead of the canonical framework source.
   - Synthetic self-test protects the warning.

3. **Real payload parity fixture intake**
   - Add a documented way to snapshot safe metadata from real lifecycle payload categories into fixtures.
   - No raw user content.

4. **Phase 3 opt-in replacement plan**
   - Only after the above, draft the replacement patch with debug fallback.

## Rule placement

- Rule: Lifecycle Phase 3 production hook replacement is blocked until readiness checklist items are satisfied; current dogfooding is positive but still requires open-gate cleanup, record-audit graph classification, and at least one full checklist run.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/lifecycle-phase3-readiness-checklist.md`
- Why not AGENTS.md: this is a roadmap/readiness gate for a specific implementation track, not a permanent general agent rule.
- Why not `.jcode`: this concerns shared lazy-harness lifecycle implementation, not local/private Jcode wiring.
- Confirmation: validation evidence and user-approved readiness strengthening

## Discovery capture

- SDD: candidate gate-state cleanup helper and record-audit graph classification alignment.
- TDD: candidate fixtures for stale open-gates cleanup and installed-host graph path classification.
- ADR: replacement decision remains deferred.
- SSOT: no new source-of-truth change yet; runtime gate state remains governed by `.lazy-harness/ssot/gate-fingerprint-state.md`.
- Planning: this file is the active Phase 3 go/no-go checklist.

## 2026-05-26 readiness cleanup implementation result

Status: implemented-and-dogfooded
Confirmation: validation evidence

Implemented readiness cleanup slice A:

- `lazy gate-state list|clear-stale`
  - Lists runtime `.lazy-harness/state/open-gates.json` state.
  - Clears stale fingerprints by age and optional prefix.
  - Supports `--dry-run` and JSON/Markdown output.
  - Mutates runtime state only, never canonical records.
- `record-audit` self-source warning
  - Emits a warning when `--source` resolves to the inspected host's own `.lazy-harness` tree.
  - Prevents installed-host readiness checks from misclassifying source-only operational records as missing host paths.

Dogfood validation:

- Source:
  - `.lazy-harness/scripts/self-test.py` passed.
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke` passed.
- Medivance:
  - Synced 5 updated framework files.
  - `.lazy-harness/bin/lazy test` passed in host scope.
  - `lazy gate-state list --format=json` reports `count: 0`.
  - `record-audit --source .` warning appears as expected.
- Medivance PWA:
  - Synced 5 updated framework files.
  - `.lazy-harness/bin/lazy test` passed in host scope.
  - `lazy gate-state list --format=json` reports `count: 0`.
  - `record-audit --source .` warning appears as expected.

Current readiness delta:

- B1 open runtime gates: cleaned and helper protected.
- B2 record-audit source mistake: guarded and documented.
- Production `response.completed` replacement: still deferred.

Next remaining slice:

- Real payload parity fixture intake with safe metadata only.
- Then a full readiness run can decide whether to draft the opt-in replacement patch.

## Rule placement

- Rule: Lifecycle Phase 3 readiness cleanup slice A is implemented/dogfooded; production replacement remains deferred pending real payload fixture intake and final readiness run.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/lifecycle-phase3-readiness-checklist.md`
- Why not AGENTS.md: this is implementation status and roadmap evidence, not universal agent grammar.
- Why not `.jcode`: this is shared lifecycle framework behavior, not local/private Jcode wiring.
- Confirmation: validation evidence

## 2026-05-26 real payload fixture intake slice

Status: implemented-and-dogfooded
Confirmation: focused validation evidence

Implemented:

- `lazy lifecycle-fixture inspect|append|list`
  - Reads a response.completed payload from `--payload` or stdin.
  - Produces a sanitized lifecycle fixture candidate.
  - Omits raw user and assistant text.
  - Stores only hashes, lengths, boolean signals, tool names, and sanitized argument previews.
  - Writes candidates to `.lazy-harness/fixtures/lifecycle/real-payload-candidates.jsonl` when using `append`.
- `lifecycle-parity-runner.py` now loads appended sanitized candidates as additional parity fixtures.

Safety policy:

- Raw `last_user_message` and `assistant_response` are never persisted by the intake helper.
- Synthetic assistant text may be generated only from boolean signals such as lazy CLI or Rule placement presence.
- Candidate fixtures are for parity coverage and readiness evidence, not canonical project memory.

Validation:

- Focused self-test `check_lifecycle_fixture_intake_cli` passed.
- Source full self-test and doctor passed.
- The self-test verifies no leakage of sample raw user/assistant/secret content into inspect output or appended candidate JSONL.
- The self-test verifies appended candidates increase lifecycle parity fixture count.
- Medivance sync + host lazy test passed.
- Medivance lifecycle fixture append/list produced count=1 with leak=false; lifecycle parity passed 13/13.
- Medivance PWA sync + host lazy test passed.
- Medivance PWA lifecycle fixture append/list produced count=1 with leak=false; lifecycle parity passed 13/13.

Remaining before replacement:

- Run final readiness checklist after this commit/sync.
- Draft Phase 3 opt-in replacement plan with legacy debug fallback if checklist passes.

## Rule placement

- Rule: Real response.completed payloads may be converted into sanitized lifecycle fixture candidates, but raw user/assistant content must not be stored.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/lifecycle-phase3-readiness-checklist.md`
- Why not AGENTS.md: this is lifecycle readiness tooling behavior and validation status, not general agent grammar.
- Why not `.jcode`: this is shared lifecycle framework implementation, not local/private Jcode wiring.
- Confirmation: focused validation evidence

## 2026-05-26 host update follow-up — lifecycle fixture self-test tolerates existing candidates

Status: implemented-and-dogfooded
Confirmation: host validation failure and focused fix

Finding:

- After syncing latest framework to Medivance and Medivance PWA, host `lazy test` found that `check_lifecycle_fixture_intake_cli` assumed the temp host candidate list would contain exactly one fixture.
- Installed dogfood hosts can already contain lifecycle fixture candidates, and the self-test temp copy may preserve those candidates.
- The correct assertion is that the newly appended fixture is present, not that the total candidate count is exactly one.

Fix:

- Updated `check_lifecycle_fixture_intake_cli` to assert that `fixture-intake-smoke` exists in the list output.
- Focused PWA `check_project_rule_placement_helper` rerun passed, so the earlier project-rule-placement failure was treated as validation-order/transient rather than a code regression.

## Rule placement

- Rule: Lifecycle fixture intake self-tests must tolerate existing dogfood candidate fixtures in installed hosts and assert presence of the appended fixture rather than exact count.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/lifecycle-phase3-readiness-checklist.md`
- Why not AGENTS.md: this is test robustness/dogfood implementation evidence, not general agent behavior.
- Why not `.jcode`: this is shared lazy-harness self-test behavior, not local/private Jcode wiring.
- Confirmation: validation evidence

## 2026-05-31 Medivance-primary readiness run

Status: medivance-primary-readiness-passed-for-plan-drafting
Confirmation: user selected option A and confirmed PWA should be secondary/contextual because PWA development is not currently active.

Scope correction for this run:

```text
Use `/home/lazydino/dev/medivance` as the primary installed-host dogfood signal.
Do not block this readiness run on Medivance PWA signal thickness until active PWA development resumes.
```

Execution result:

- Synced `/home/lazydino/dev/medivance` from `/home/lazydino/dev/lazy-harness`.
  - Previous marker: `efede93f2586...`
  - New marker: `eb86fb8ed754...`
  - Sync updated 2 framework knowledge files plus marker.
- Cleared one stale runtime open gate in Medivance:
  - `project-rule-placement:facd67afecc6c37b`
  - age≈3.6h
  - remaining open gates: 0
- Source validation:
  - `.lazy-harness/scripts/self-test.py`: pass
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`: pass
  - `lazy lifecycle-parity --format=json --fail-on-mismatch`: pass, 12/12
- Medivance validation:
  - `.lazy-harness/bin/lazy test`: pass
  - `lazy record-audit --format=json --source /home/lazydino/dev/lazy-harness`: pass
  - `lazy lifecycle-parity --format=json --fail-on-mismatch`: pass, 13/13
  - `lazy capability audit --format=json`: pass, count=3, issues=[]
  - `lazy gate-state list --format=json`: pass, count=0
  - `lazy hook-timings --format=json --limit=1000`: pass, rows=1000, invalidRows=0
    - `hook-total`: count=58, avg≈858.9ms, p50≈692ms, p90≈994ms, p99≈3995ms, max≈4491ms, nonZeroExit=0

Record-audit warning triage:

- Project Profile warning:
  - Current warning: 0 missing artifacts, 26 fields still `needs-interview`.
  - Classification: deferred nice-to-have, not a lifecycle Phase 3 hard blocker.
  - Reason: artifacts are present; unanswered fields are project interview enrichment, not a runtime/lifecycle parity or response.completed replacement dependency.
- Skipped workflow warning:
  - Current warning: 7 skipped workflow entries exist.
  - Classification: historical/intentional audit trail, not an active blocker.
  - Evidence: entries are older Medivance workflow notes: existing-record discovery skip, duplicate option-gate skip, non-authored commit registry skip, user-choice pause, existing project-rule placement record, and two user-manual-verified affected-test skips.
  - Current runtime gate state is clean: open gate count=0.

Go/no-go conclusion:

```text
Medivance-primary readiness is sufficient to proceed to the next Phase 3 step: draft an opt-in response.completed replacement plan/patch with legacy comparison debug fallback and rollback instructions.
Do not directly replace `.lazy-harness/hooks/lifecycle/on-response-completed.sh` yet without the explicit replacement approval/patch review step.
```

Updated checklist interpretation:

- Production hook replacement explicit approval: still pending.
- Source lifecycle parity: passed.
- Medivance lifecycle parity after latest sync: passed.
- PWA lifecycle parity/signal: secondary for now by user-confirmed scope correction.
- Open gate state: passed, count=0 after stale runtime cleanup.
- Graph/record audit: passed; missingPaths=0, invalidRows=0, commaJoinedPaths=0.
- Recent real-use rows: passed for Medivance-primary evaluation.
- Replacement plan with debug fallback: next required work.
- Rollback instructions: next required work.
- Full source validation: passed.
- Medivance host validation: passed.
- Project Profile fields: explicitly deferred.
- PWA Project Profile artifacts: explicitly secondary/deferred until PWA resumes active development.

## Rule placement

- Rule: As of 2026-05-31, Medivance-primary lifecycle Phase 3 readiness is sufficient for drafting the opt-in replacement plan/patch, but not for directly replacing the production response.completed hook without an explicit approval/review step.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/lifecycle-phase3-readiness-checklist.md`
- Why not AGENTS.md: this is a point-in-time readiness decision for a specific lifecycle implementation track, not permanent agent behavior.
- Why not `.jcode`: this concerns shared lazy-harness framework lifecycle rollout, not local/private Jcode-only workflow.
- Confirmation: user selected option A and validation evidence passed.

## Discovery capture

- DDD: no new domain definitions.
- SDD: next work should draft the opt-in response.completed replacement plan/patch with fallback and rollback; no production contract change applied yet.
- BDD: PWA dogfood signal remains secondary until active PWA development resumes.
- TDD: validation evidence captured; no new regression fixture added in this run.
- ADR: explicit production replacement approval remains pending and should be captured before direct replacement.
- SSOT: sync marker source remains `.lazy-harness/state/synced-from-commit`; Medivance marker now points to `eb86fb8ed754...`.
- Planning: this section is the current readiness checkpoint and next-step gate.

## 2026-05-31 Phase 3 opt-in engine patch

Status: implemented-opt-in-not-production-default
Confirmation: user approved proceeding with the plan after clarifying the reason for Track B.

Purpose:

```text
Track B optimizes the response.completed safety-gate hot path. It does not add application features.
The goal is to keep the same STOP/no-STOP safety semantics while making the helper execution path easier to compare, debug, and later optimize.
```

Implementation summary:

- Added `LAZY_RESPONSE_COMPLETED_ENGINE=legacy|orchestrator|compare` to `.lazy-harness/hooks/lifecycle/on-response-completed.sh`.
- Default remains `legacy`; unknown values also fall back to `legacy`.
- `orchestrator` mode runs `.lazy-harness/scripts/lifecycle-check.py` as the primary helper engine after route telemetry.
- `orchestrator` mode falls back to the legacy shell-helper loop if `lifecycle-check.py` exits non-zero or emits invalid JSON.
- `compare` mode runs the orchestrator in a sandbox `.lazy-harness` copy, then runs legacy in the real host.
- `compare` mode keeps legacy output as user-visible truth and logs sanitized comparison metadata to `.lazy-harness/logs/lifecycle-compare.jsonl` or `LAZY_RESPONSE_COMPLETED_COMPARE_LOG`.
- Added `lifecycle-check.py --sandbox` to support side-effect-safe comparison.
- Added self-test coverage for orchestrator timing rows, sandboxed compare rows, and no raw hook body storage.

Rollback:

```bash
unset LAZY_RESPONSE_COMPLETED_ENGINE
# or
export LAZY_RESPONSE_COMPLETED_ENGINE=legacy
```

Optional cleanup:

```bash
rm -f .lazy-harness/logs/lifecycle-compare.jsonl
```

Checklist delta:

- Replacement plan includes legacy comparison/debug fallback: satisfied for opt-in patch.
- Rollback instructions: satisfied for opt-in patch.
- Production default replacement approval: still pending.
- Production default remains legacy: verified by implementation.

## Rule placement

- Rule: Phase 3 may provide opt-in orchestrator/compare modes, but production default must remain legacy until a later explicit replacement approval.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/lifecycle-phase3-readiness-checklist.md`
- Why not AGENTS.md: this is a rollout checkpoint for a lifecycle implementation track, not permanent agent grammar.
- Why not `.jcode`: this concerns shared lazy-harness lifecycle code, not private Jcode-only workflow.
- Confirmation: user-approved plan execution and implementation evidence.

## Discovery capture

- SDD: `.lazy-harness/spec/platform/hook-performance-measurement.md` updated with Phase 3 engine switch contract.
- TDD: `.lazy-harness/scripts/self-test.py` updated with opt-in engine coverage.
- ADR: production default replacement approval remains pending.
- SSOT: no source-of-truth default change; legacy remains the default engine.
- Planning: this section records the opt-in patch and rollback path.

## 2026-05-31 downstream sync after Phase 3 opt-in patch

Status: synced-and-validated

Source commit synced:

- `1bab3ef5c7cdb73ab4f52267ea1f7334408e381d` (`Add opt-in response lifecycle engine`)

Downstream validation:

- `/home/lazydino/dev/medivance`
  - `lazy-sync --force`: updated 5 framework files and marker.
  - marker reached `1bab3ef5c7cd...`.
  - `lazy test`: pass, host scope ran=40 skipped=16.
  - `LAZY_RESPONSE_COMPLETED_ENGINE=compare` smoke: pass.
  - compare row: `bodyHashMatch=true`, `helperMatch=true`, `orchestratorSandbox=true`, `orchestratorExitCode=0`.
  - `git status --short`: clean.
- `/home/lazydino/dev/medivance-pwa`
  - `lazy-sync --force`: updated 5 framework files and marker.
  - marker reached `1bab3ef5c7cd...`.
  - `lazy test`: pass, host scope ran=40 skipped=16.
  - `LAZY_RESPONSE_COMPLETED_ENGINE=compare` smoke: pass.
  - compare row: `bodyHashMatch=true`, `helperMatch=true`, `orchestratorSandbox=true`, `orchestratorExitCode=0`.
  - `git status --short`: clean.

Interpretation:

```text
The Phase 3 opt-in patch is now synced into both dogfood hosts and works in compare mode for a read-only no-output payload.
This is still not production-default replacement approval. Default remains legacy.
```

Next source-side note:

This record commit advances source HEAD beyond `1bab3ef`; downstream markers should be refreshed once more after committing this record.
