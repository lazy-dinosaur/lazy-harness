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
- [ ] Lifecycle parity suite includes real payload categories beyond synthetic fixtures.
- [ ] All current open gate state is closed, expired, or classified as synthetic/stale runtime state.
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

### B1 — open runtime gates remain

Current runtime state:

- source: `project-rule-placement:06be2de14403abdb`
- Medivance: `project-rule-placement:1126e416349d8ec4`
- Medivance PWA: `bdd:d0c41fdf3381c81d`

Classification:

- `.lazy-harness/state/open-gates.json` is runtime state, not canonical memory.
- These are likely stale/synthetic from previous lifecycle tests or dogfood turns, but they should not be ignored when deciding production replacement.

Required cleanup:

1. Add or use a safe expiry/cleanup helper for stale runtime gate state, or document manual reset criteria.
2. Re-run lifecycle parity after cleanup.
3. Confirm no new real gate opens during the readiness run.

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

1. **Gate state cleanup helper**
   - Add `lazy gate-state list|clear-stale` or a narrow helper for runtime `open-gates.json` cleanup.
   - Must not delete canonical records.
   - Must be tested with synthetic state.

2. **Record-audit source-argument guard**
   - Make `record-audit` warn when `--source` points at the same host instead of the canonical framework source.
   - Optional: add a fixture for installed-host source-only operational paths.

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
