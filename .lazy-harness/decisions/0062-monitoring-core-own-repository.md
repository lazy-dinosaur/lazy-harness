# ADR 0062 — Monitoring core in its own repository (lazy-harness monitoring monorepo)
> Pre-migration record: code/script/test/fixture paths below describe the layout of lazy-harness branch `work/monitoring-engine-v2` (221553d) before the monitoring implementation moved to `lazy-dinosaur/lazy-harness-monitoring`; evidence stays in lazy-harness (ADR 0062). Canonical monitoring records now live on lazy-harness main (see `.lazy-harness/ssot/monitoring-records-ownership.md`).

Status: accepted (user-confirmed option A, task154)
Layer: ADR
Date: 2026-11-08
Related ADR: `.lazy-harness/decisions/0061-monitoring-core-fabric-optional.md`
Related planning: `.lazy-harness/planning/monitoring-engine-concept-v2.md`, `.lazy-harness/planning/monitoring-core-live-integration-plan.md`
Related SDD: `.lazy-harness/spec/platform/monitoring-core.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - monitoring repository split
  - 모니터링 저장소 분리
  - lazy-harness monitoring monorepo
- Applies when:
  - changing where the monitoring core, its Pi host binding, the shared evaluation tool or monitoring modules live
  - developing or releasing a monitoring package or module
- Must:
  - develop the monitoring core as the lazy-harness monitoring core in `/home/lazydino/dev/lazy-harness-monitoring` (packages/core, packages/pi-host, packages/eval, modules/*), each part built, tested and completed separately
  - keep the core TypeScript and Fabric-independent (ADR 0061) with language-neutral boundaries (configuration schema, `monitoring-trace/v1`, canonical JSON)
  - keep design, decisions and measurement records in lazy-harness `.lazy-harness/` and point them at the new repository
  - leave a thin consumer in lazy-harness only after the migrated packages pass their own tests
  - keep host adapters on the host side (`hosts/<agent>`, user-confirmed task154): the core defines the Host Adapter contract (frame vocabulary, capabilities, support check, frame-sequence conformance) and never imports a host, so Pi, opencode, OMP or Jcode attach through the same contract
- Must not:
  - hand monitoring output to a knowledge/memory consumer before the core is finished (user correction, task154)
  - copy real session content or private traces into the new repository
- Record completion:
  - update this ADR when the repository location, package split or consumer boundary changes

## Context

The monitoring work lived across `packages/lazy-harness-pi/monitoring` (public SDK) and `.lazy-harness/scripts/monitoring-*` (engine, runners), and was developed in the shared main tree. Other sessions' uncommitted files leaked into its gates (policy record), unrelated harness checks blocked its commits, and every module needed its own measurement runner.

## Decision

Move the monitoring core into its own monorepo, named and positioned as the lazy-harness monitoring core, and complete each part separately: core (engine + inspection ports), Pi host binding, one shared evaluation tool, and modules (references, rule-steering, memory). Source of the first migration: branch `work/monitoring-engine-v2` at `18bd0c8`.

## Consequences

- Monitoring commits no longer depend on unrelated harness state; each package carries its own tests.
- lazy-harness records remain the institutional memory; the new repository has no `.lazy-harness` unless installed later by a separate decision.
- Evidence (`.lazy-harness/evidence/monitoring-core/**`) stays in lazy-harness; only fixtures needed by migrated tests are copied.

## Implementation map

- New repository: `/home/lazydino/dev/lazy-harness-monitoring` (`README.md` layers, `MIGRATION.md` order), scaffold commit `d726b77`.
- Source branch/worktree: `work/monitoring-engine-v2` at `/home/lazydino/dev/lazy-harness.monitoring`.
