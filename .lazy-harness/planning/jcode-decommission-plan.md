# Planning — Jcode Integration Decommission

Status: implementation-complete-awaiting-final-validation
Date: 2026-08-22
Layer: Planning
Primary ADR: `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`
Related TDD: `.lazy-harness/tests/jcode-decommission.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: transient-plan
- Confidence: high
- Aliases:
  - Jcode 제거 계획
  - preserve generic improvements
- Applies when:
  - executing the user-approved Jcode integration decommission
- Must:
  - preserve non-Jcode and runtime-neutral improvements path-by-path
  - capture exact machine rollback state before mutation
  - split Pi/OMP activation from Jcode before deleting Jcode implementation
  - keep patched builds/source, backups, rescue branch, and provenance until final validation and separate cleanup approval
  - run one coherent source batch, focused checkpoint when needed, and one final standard validation
- Must not:
  - revert mixed commits wholesale
  - mutate downstream product files or branches
  - combine the separate 37-row graph migration with this work unit
- Record completion:
  - update phase status, receipt path, validation evidence, downstream rollout, and residual risks

## Confirmed scope

User-confirmed on 2026-08-22:

- Completely remove active Lazy-Harness Jcode integration.
- Preserve all reusable changes made during the Jcode work.
- Pi is stable primary; OMP remains Experimental.
- Retain Jcode builds/source temporarily as inert rollback artifacts.
- Prior shared-cwd freeze is lifted and this exact plan is approved for execution.

## Execution phases

1. Capture exact machine config, trust, local transport, excludes, launcher, pointer, provenance, modes, and running-process state in a private backup.
2. Add ADR/TDD/planning records and supersede current Jcode support authority.
3. Decouple `agent activate`, `init`, and `sync` so Pi/OMP never read or require Jcode state.
4. Use the still-present Jcode package rollback/remove paths to restore the launcher and remove managed machine state.
5. Remove active Jcode CLI/scripts/helper, registries, manifests, runnable fixtures, and current support claims.
6. Preserve historical records with retired/deprecated/cancelled status; preserve runtime-neutral behavior under canonical names.
7. Run focused source checks and one final standard validation.
8. Sync hosts sequentially only after source is green; protect product branches and dirty files.
9. Keep rollback artifacts until a separate cleanup approval.

## Stop conditions

- Exact machine state cannot be captured or launcher rollback state conflicts with the live launcher.
- Removing Jcode would remove or change Pi/OMP grounding, lifecycle, validation, progress, or command-boundary behavior.
- Source requires a broad commit revert rather than path-level separation.
- Downstream product state would need reset, checkout, clean, or revert.
- A new user requirement changes the confirmed scope.

## Implementation map

- Status: implemented-focused-green-awaiting-final-standard
- Primary files: ADR 0059 and TDD record plus the source/registry/manifest paths listed there.
- Rollback assets: private machine backup, Jcode build/source/provenance, and `rescue/main-dirty-20260818` commit `129e90c`.
- Validation: focused Pi/OMP activation/init/sync/package tests, policy/manifest/reference audits, then `lazy validate --plan standard`.

## Rule placement

- Rule: execute the approved Jcode decommission reversibly while preserving generic improvements.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/jcode-decommission-plan.md`.
- Confirmation: user-approved on 2026-08-22.

## Discovery capture

- ADR: ADR 0059 is the canonical runtime-support decision.
- SDD: Pi/OMP package and activation contract changes.
- BDD: Jcode-only behavior retired as history.
- TDD: decommission matrix added.
- SSOT: enforcement delivery boundary changes.
- Planning: this record owns execution and rollback state.
