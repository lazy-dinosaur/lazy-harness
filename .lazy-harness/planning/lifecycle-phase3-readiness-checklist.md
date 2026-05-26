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
