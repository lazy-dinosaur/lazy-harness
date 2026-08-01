# Planning — Jcode Runtime Adapter Pilot

Status: in-progress
Date: 2026-08-01
Layer: Planning
Primary ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Related SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
Related TDD: `.lazy-harness/tests/jcode-agent-adapter.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: transient-plan
- Confidence: high
- Aliases:
  - Jcode 2단계 파일럿
  - Jcode adapter rollout
  - lazy jcode implementation
- Applies when:
  - implementing or reviewing the approved Jcode runtime adapter pilot
- Must:
  - finish contract records before source implementation
  - keep Pi/OMP behavior unchanged unless focused evidence requires a co-change
  - stop short of unsupported parity claims without live evidence
- Must not:
  - restore the deprecated directory bridge or bulk-generate `.jcode` policy files
- Record completion:
  - update phase state and residual risks when the pilot completes or stops
- Related records:
  - `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - `.lazy-harness/tests/jcode-agent-adapter.md`

## Objective

Ship a bounded Jcode adapter pilot using official hooks so one explicit installation registers the current lazy root and hooks auto-apply only in exact user-trusted projects; new projects require one `lazy jcode trust`.

## Approved phases

### Phase 1 — contract and decision

- [x] Audit Jcode `v0.64.114-dev` official prompt/hook/config surfaces.
- [x] Confirm the two-stage thin-adapter approach with the user.
- [x] Supersede the Pi/OMP-only support boundary while retaining ADR 0050 as history.
- [x] Define Jcode adapter SDD and regression matrix.

### Phase 2 — bounded implementation

- [x] Add dedicated Jcode hook adapter.
- [x] Add reversible Jcode config installer/doctor/smoke/remove.
- [x] Add `lazy jcode ...` dispatch/help.
- [x] Complete the expanded adversarial fake-root/config/trust/lock/correlation suite.
- [x] Correct the Pi fake-runtime peer-resolution defect with hermetic fixture stubs and pass the focused Pi/OMP non-regression fixture.
- [ ] Run one green final standard validation after the final record/source mutation.
- [x] Run fresh installed live Jcode sessions for trusted read, destructive-command deny, untrusted silence, and root/session isolation evidence.

### Independent-review remediation

- [x] Remove the initially installed unsafe marker-only global hooks.
- [x] Close relative-`JCODE_HOME` trust-registry injection while preserving silent runtime no-op.
- [x] Restrict persisted path evidence to canonical root-contained filesystem paths.
- [x] Make lock acquisition owner-atomic, stale recovery owner-revalidated, and session-end ownership-safe.
- [x] Byte-preserve unrelated TOML formatting/line endings across install/remove.
- [x] Expand fixtures for every above attack plus ambiguous/stale correlation and true deny cleanup failure.
- [x] Re-run independent security review after focused fixtures pass; no blocker/high/medium finding remained.
## Acceptance criteria

- One explicit install registers the current trusted root; each new lazy project uses one explicit trust command.
- Silent no-op outside lazy roots and inside marker-only untrusted roots.
- Canonical pre-tool denial maps to Jcode exit 2.
- Successful evidence is isolated by root and session.
- Install/remove round trip preserves unrelated Jcode configuration.
- Doctor reports missing binary, managed state, conflicts, and capability gaps.
- Pi/OMP focused regressions remain green.
- Unsupported mid-turn reinjection, continuation, and native ask surfaces remain explicit residual gaps unless live evidence closes them.

## Stop conditions

Stop and ask before continuing if:

- safe TOML preservation requires rewriting unrelated user configuration,
- Jcode observer ordering cannot support successful-read evidence without false proof,
- implementation requires modifying Jcode source or memory semantics,
- Pi/OMP behavior must change for Jcode support,
- a new security, config ownership, or lifecycle architecture decision appears.

## Validation plan

- Edit loop: `.lazy-harness/bin/lazy check`.
- Focused: Jcode adapter self-test fixture plus TypeScript diagnostics.
- Final: `.lazy-harness/bin/lazy validate --plan standard` once after the final mutation.
- Live: fresh Jcode session in this repository after static/fake-runtime checks pass.

## Residual risks

- Installation and live trusted/untrusted Jcode smoke are complete. The focused Pi/OMP fixture now passes without repository-local or machine-global peer lookup; only final standard validation remains before pilot closure.
- `post_tool` observers are detached, so correlation stays conservative: one fresh unambiguous match only.
- Jcode baseline has no verified Pi-style `context` re-injection or bounded turn-end continuation.
- Jcode native selectable option-gate UI is not verified.
- Global config conflict composition is intentionally deferred; the pilot stops on conflicting hook values.

## Rule placement

- Rule: execute the approved Jcode adapter as a bounded two-stage pilot with explicit stop conditions and honest capability-specific parity.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`
- Why not AGENTS.md: this is implementation rollout state, not permanent grammar.
- Why not `.jcode`: rollout state belongs to canonical project planning.
- Confirmation: user-confirmed 2026-08-01

## Discovery capture

- DDD: no independent delta.
- SDD: adapter contract promoted.
- BDD: no independent delta.
- TDD: adapter regression contract promoted.
- ADR: multi-runtime thin-adapter decision promoted.
- SSOT: multi-runtime enforcement delivery boundary updated in `.lazy-harness/ssot/harness-enforcement-policy.md`.
- Planning: this record owns transient rollout state and residual risks.
