# Harness Enforcement Restoration Plan

Status: implemented
Date: 2026-05-31
Scope: lazy-harness framework enforcement restoration
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`

## Implementation result

Implemented on 2026-06-01:

- Restored generated Jcode `edit` / `write` / `multiedit` blocking `tool.execute.before` hooks.
- Added mandatory Layer 2 patching for existing user-owned `.jcode/config.toml` files so local preferences are preserved but mandatory force-gates cannot silently disappear.
- Added runtime/dev-instance action-boundary guard for dev commands when matching runtime/dogfood policy records exist.
- Added self-test coverage for restored blocking wiring, user-owned config patching, PR body guard preservation, and runtime record-first enforcement.
- Updated SSOT/SDD/TDD/ADR/docs and implementation graph edges.

Validation completed:

- Source `.lazy-harness/scripts/self-test.py`: pass, ran 58, skipped 0.
- Source `python3 .lazy-harness/scripts/doctor.py --profile smoke`: pass.
- Source `git diff --check`: pass.
- Downstream Medivance sync: pass, user-owned `.jcode/config.toml` patched with `BEGIN lazy-harness mandatory Layer 2 force-gates`.
- Downstream Medivance `.lazy-harness/bin/lazy test`: pass, ran 42, skipped 16.

## User-confirmed direction

The user chose to keep the current HEAD improvements and re-add the missing enforcement strength rather than rolling the framework back to 2026-05-19.

Implementation direction:

- Do not revert post-5/19 features.
- Restore the 5/19-era Layer 2 edit/write/multiedit blocking force-gate on top of current HEAD.
- Add runtime/dev-instance action-boundary enforcement for the observed dogfood failure.
- Keep speed optimization as a later pass after correctness is restored and tested.

## Goal

Restore lazy-harness as mandatory enforcement infrastructure without reintroducing excessive friction on every mechanical edit.

The target is not "make every hook blocking". The target is:

1. Core grammar and layer duties are always wired and visible.
2. Prevention-grade rules are enforced at the relevant action boundary.
3. Confirmed discoveries keep accumulating into DDD/SDD/BDD/TDD/ADR/SSOT.
4. Response completion remains a guaranteed backstop, not best-effort noise.
5. The exact dogfood failure is covered by regression tests.

## Evidence baseline

Validated on 2026-05-31:

- `.lazy-harness/scripts/self-test.py` passes with 56 checks.
- `python3 .lazy-harness/scripts/doctor.py --profile smoke` passes.
- Current source wiring registers:
  - `tool.execute.before` for bash as blocking.
  - `response.completed` as non-blocking.
  - no edit/write/multiedit development-time blocking gates.
- Git history shows:
  - `42150ea Move Jcode edit gates to commit time` moved edit-time record checks to commit-time validation.
  - `8438cc5 Add read-only hook fast path` skips write-only helpers for confirmed read-only response payloads.
  - `684b390 Add rule lifecycle action-boundary guard` adds PR body guard as first exemplar, not a general record-first preflight.
  - `1bab3ef Add opt-in response lifecycle engine` keeps legacy default and adds opt-in compare/orchestrator path.
- Focused helper check shows simple "project rule" language alone does not trigger project-rule placement STOP. Placement cues like `.jcode` or `.lazy-harness/ssot` do.

## Proposed plan

### Phase 0 — Freeze and baseline

- Do not change Medivance or other host app code while diagnosing this source-level enforcement drift.
- Keep the newly added SSOT policy as the canonical user-confirmed requirement.
- Add a minimal planning/checkpoint trail for every enforcement change.

Validation:

- `git status --short`
- `self-test.py`
- `doctor.py --profile smoke`

### Phase 1 — Wiring truth reconciliation

Make docs, ADR, generated Jcode config, and actual `.jcode/config.toml` agree on the intended semantics.

Decide explicitly whether `response.completed` should be:

A. blocking/deny-style again,
B. non-blocking but guaranteed inject/wake semantics,
C. split: hard blockers for enforcement failures, non-blocking for telemetry/advice.

Recommended: C.

Rationale:

- Telemetry and route compression should not block.
- Rule placement, user correction capture, stale execution approval, and missing record-as-output are enforcement failures and should be hard/guaranteed.
- This avoids both extremes: noisy every-edit blocking and toothless after-the-fact advice.

Expected files:

- `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`
- `.lazy-harness/JCODE-INTEGRATION.md`
- `.lazy-harness/scripts/jcode-wiring.ts`
- possibly a new ADR if semantics are materially changed.

### Phase 2 — Add an enforcement tier model

Classify lifecycle checks by severity instead of treating all output as one kind of reminder.

Suggested tiers:

- `block`: must stop or guarantee next-turn injection before continuing.
- `interrupt`: important user-visible reminder, not always a tool denial.
- `advisory`: telemetry, routing suggestions, optimization hints.
- `audit`: commit-time/doctor/self-test checks.

Required property:

Any rule that says "must", "STOP", "do not continue", or protects canonical records must not silently degrade to advisory.

Expected files:

- `.lazy-harness/spec/platform/lifecycle-enforcement-tiers.md`
- `.lazy-harness/hooks/lifecycle/on-response-completed.sh`
- `.lazy-harness/scripts/lifecycle-check.py` if orchestrator path is kept.
- self-test fixtures.

### Phase 3 — Record-first action-boundary bindings

Generalize the rule lifecycle binding beyond PR body format.

Add supported bindings for high-risk or high-miss actions:

1. Runtime/dev-server/test-instance commands:
   - before `bun run dev`, `bun dev:*`, `scripts/dev-cli.ts`, or host runtime commands,
   - require lookup of relevant `.lazy-harness/ssot/*runtime*`, `*dogfood*`, or project profile records when present.
2. External mutations:
   - PR creation/editing,
   - DB migrations,
   - release dispatch,
   - deployment commands.
3. Project/team rule corrections:
   - if user corrects ownership/source-of-truth, require same-turn SSOT capture.

Expected files:

- `.lazy-harness/ssot/rule-lifecycle.md`
- `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
- `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py`
- `.lazy-harness/scripts/jcode-wiring.ts`
- `.lazy-harness/scripts/self-test.py`

### Phase 4 — Record-as-output pressure restoration

Improve capture gates so DDD/SDD/BDD/TDD/ADR/SSOT accumulation does not depend only on the model remembering instructions.

Focus checks:

- User-confirmed correction without SSOT record.
- Non-trivial analysis/backlog without planning/candidates capture.
- Bug/regression discussion without TDD plus cross-layer impact classification.
- API/component/behavior/config discoveries without SDD/BDD/SSOT route.

Expected files:

- existing lifecycle helpers under `.lazy-harness/hooks/lifecycle/helpers/`
- self-test fixtures for minimal positive and negative cases.

### Phase 5 — Regression fixture for the observed failure

Add a focused fixture that reproduces the screenshot failure mode:

- User asks to run app connected to test database.
- Agent inspects generic commands/env files.
- Agent reasons about instance/worktree without consulting canonical dogfood runtime SSOT.
- Expected result: STOP or mandatory reminder requiring `.lazy-harness/ssot/medivance-dogfood-runtime-policy.md` lookup before runtime command/recommendation.

Important: the fixture should live in source framework tests and use synthetic paths/content, not depend on the real Medivance checkout.

### Phase 6 — Dogfood sync validation

After source tests pass:

1. Run source validation:
   - `.lazy-harness/scripts/self-test.py`
   - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
2. Sync to Medivance dogfood host:
   - `bun ~/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts --from ~/dev/lazy-harness --target ~/dev/medivance --force`
3. Run host validation:
   - `cd /home/lazydino/dev/medivance && .lazy-harness/bin/lazy test`
4. Only then consider committing source changes.

## Success criteria

- Source self-test and doctor pass.
- Generated Jcode wiring and docs agree about lifecycle enforcement semantics.
- At least one test proves enforcement failures are not merely advisory.
- At least one test covers runtime/test-instance record-first lookup.
- PR body guard still passes.
- Read-only fast-path does not skip enforcement-grade helpers.
- Dogfood host lazy test passes after sync.

## Non-goals

- Do not re-enable blocking edit/write/multiedit for every mechanical file change unless a test proves it is necessary.
- Do not store project/team policy in `.jcode` or Jcode memory.
- Do not make route telemetry blocking.
- Do not hardcode Medivance-only content into the framework source outside synthetic fixtures or host-provided records.

## Open decision gate

Choose the enforcement semantics for `response.completed` and lifecycle helper outputs:

A. Make `response.completed` blocking again for all helper output.
B. Keep `response.completed` non-blocking, but improve reminders and docs only.
C. Split helper output by severity: block/guarantee enforcement failures, keep telemetry/advice non-blocking. (Recommended)
D. Restore edit/write/multiedit blocking gates as well as response blocking.
E. Type your own direction.

## Rule placement

- Rule: restore lazy-harness enforcement through wiring reconciliation, severity-tiered lifecycle outputs, action-boundary bindings, record-as-output pressure, regression fixtures, and dogfood validation.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/harness-enforcement-restoration-plan.md`
- Why not AGENTS.md: this is an implementation plan and decision gate, not final operational grammar yet.
- Why not `.jcode`: this is shared framework source behavior, not local/private Jcode-only workflow.
- Confirmation: needs-option-gate

## Discovery capture

- DDD: none.
- SDD: lifecycle enforcement tiers and action-boundary binding contracts need updates.
- BDD: observed agent workflow failure should become a dogfood behavior fixture.
- TDD: regression fixtures needed for response severity, runtime record-first lookup, and record-as-output capture.
- ADR: likely needed if response.completed semantics change from generated non-blocking to split severity/blocking.
- SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md` is the user-confirmed policy anchor.
- Planning: this document is the proposed execution plan.
