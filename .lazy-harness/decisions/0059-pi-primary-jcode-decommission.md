# ADR 0059 — Pi Primary Runtime and Jcode Integration Decommission

Status: accepted
Date: 2026-08-22
Layer: ADR
Supersedes: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`, `.lazy-harness/decisions/0057-jcode-lazy-patched-channel.md`, `.lazy-harness/decisions/0058-jcode-typed-review-model-routing.md`
Related precedent: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`
Related SDD: `.lazy-harness/spec/platform/pi-agent-package.md`
Related TDD: `.lazy-harness/tests/jcode-decommission.md`, `.lazy-harness/tests/pi-agent-package.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Confidence: high
- Aliases:
  - Jcode 제거
  - Jcode decommission
  - Pi primary runtime
  - Pi 주력 런타임
- Surface terms:
  - Pi stable
  - OMP Experimental
  - remove Jcode integration
- Applies when:
  - installing, removing, auditing, or documenting Lazy-Harness agent runtime support
  - changing project activation, init, sync, lifecycle adapters, or subagent execution
- Must:
  - support Pi as the stable primary runtime
  - retain OMP as Experimental through the shared Pi/OMP package
  - remove active Lazy-Harness Jcode CLI, adapter, trust, hook, launcher-promotion, and project-transport integration
  - preserve runtime-neutral improvements produced during the Jcode work, including work-unit grounding, bounded validation, lifecycle payloads, project command boundaries, progress, and distribution-aware audits
  - preserve Jcode decisions and rollout records as superseded or retired history rather than deleting the chronology
  - keep one writer and use Pi Subagents for bounded read-only exploration and independent review
- Must not:
  - revert mixed commits wholesale or discard reusable Pi/OMP/framework improvements
  - reactivate ADR 0050 as if ADR 0056–0058 had never happened
  - remove Jcode binaries/source or the rescue branch before decommission validation and a separate cleanup decision
  - make OMP a stable-support claim
- Record completion:
  - runtime support changes update this ADR, Pi/OMP SDD/TDD, enforcement SSOT, decommission TDD, manifests, registries, and implementation map
- Related records:
  - `.lazy-harness/decisions/0055-agent-neutral-orchestration-core-pi-runtime.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/ssot/harness-enforcement-policy.md`
  - `.lazy-harness/planning/jcode-decommission-plan.md`

## Context

Jcode support was implemented through an exact-trusted-root adapter and a separately maintained patched channel. The work produced useful generic lifecycle, validation, grounding, progress, project-command, and distribution improvements. The user has now confirmed that Jcode will not be used and that the important next direction is effective subagent orchestration.

Removing the integration by reverting its mixed commits would also remove those generic improvements. The decommission must therefore cut only Jcode-specific dependency edges from the current tree while preserving the active Pi/OMP framework behavior and the full decision chronology.

## Decision

1. Pi is the stable primary Lazy-Harness runtime.
2. OMP remains Experimental and continues to share the Pi/OMP package core and separate install UX.
3. Jcode is unsupported and decommissioned from active Lazy-Harness integration.
4. Active Jcode CLI dispatch, lifecycle adapter, managed global hooks, exact-root trust registry, project-local prompt transport, launcher promotion, activation/init/sync coupling, typed swarm routing, and runnable adapter fixtures are removed.
5. Jcode ADR/SDD/TDD/BDD/planning/evidence files remain as historical records with superseded, retired, cancelled, or deprecated status where appropriate.
6. Runtime-neutral behavior remains active even when its original comments or fixtures used Jcode terminology; those names are rewritten to canonical lifecycle terminology without changing behavior.
7. Machine cleanup is reversible: exact pre-removal config, trust, local transport, excludes, launcher, pointers, provenance, and modes are backed up outside the repository; official/patched builds and the Jcode source checkout remain inert until separate post-validation cleanup approval.
8. Agent-neutral orchestration remains governed by ADR 0055. Pi Subagents is the first execution runtime; children provide bounded evidence while the parent owns discovery, decisions, writing, integration, and validation.

## Consequences

- `lazy agent activate`, `lazy init`, and `lazy sync` manage Pi/OMP without reading or requiring Jcode state.
- `lazy jcode` is no longer an active command.
- Hosts no longer receive active Jcode adapter/channel/typed-routing records or transport guides.
- Existing Jcode builds may still exist as inert rollback artifacts, but Lazy-Harness does not configure, trust, launch, or test them.
- Historical Jcode records remain searchable and explain why generic features exist.
- The next approved runtime work is Pi-first subagent operating-model design, not Jcode parity.

## Implementation map

- Status: implemented-focused-green-awaiting-final-standard
- Primary files:
  - `.lazy-harness/scripts/agent-activate.ts` — Pi/OMP-only project activation transaction.
  - `.lazy-harness/scripts/lazy-init.ts` — explicit target initialization followed by Pi/OMP activation.
  - `.lazy-harness/scripts/lazy-sync.ts` — Category A sync plus Pi/OMP activation repair without Jcode trust.
  - `.lazy-harness/bin/lazy` — Pi/OMP runtime commands; no active Jcode dispatcher.
  - `.lazy-harness/spec/platform/pi-agent-package.md` — active runtime contract.
  - `.lazy-harness/ssot/harness-enforcement-policy.md` — active enforcement delivery boundary.
  - `.lazy-harness/scripts/self-test.py` — Pi/OMP and decommission regression coverage.
- Removed active implementation:
  - `.lazy-harness/scripts/jcode-adapter.ts`
  - `.lazy-harness/scripts/jcode-package.ts`
  - `.lazy-harness/scripts/jcode-trust.ts`
  - `.lazy-harness/scripts/jcode-local-config.ts`
  - `.lazy-harness/hooks/lifecycle/helpers/check-agent-model-routing.py`
- Protected history:
  - ADR 0050 and ADR 0056–0058 plus linked Jcode records.
  - `rescue/main-dirty-20260818` commit `129e90c` until post-validation comparison is complete.
- Tests / protection:
  - `.lazy-harness/tests/jcode-decommission.md`
  - `.lazy-harness/tests/pi-agent-package.md`
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`
- Machine index:
  - Jcode implementation graph rows are retained as history and receive supersession edges; no bulk graph rewrite is part of this work unit.

## Rule placement

- Rule: Pi is the stable primary runtime, OMP is Experimental, and active Jcode integration is removed without reverting reusable framework improvements.
- Scope: framework-global.
- Primary record: `.lazy-harness/decisions/0059-pi-primary-jcode-decommission.md`.
- Why not AGENTS.md: this is runtime architecture and removal rationale, not per-turn grammar.
- Confirmation: user-confirmed on 2026-08-22.

## Discovery capture

- DDD: no independent business/domain delta.
- SDD: Pi/OMP activation and runtime contract remove Jcode coupling.
- BDD: Jcode-only visible ask/follow-up records become retired history; no Pi product flow changes.
- TDD: decommission and Pi/OMP non-regression coverage required.
- ADR: this record owns the new support boundary and supersession chronology.
- SSOT: enforcement delivery changes to Pi stable plus OMP Experimental.
- Planning: `.lazy-harness/planning/jcode-decommission-plan.md` owns execution and rollback state.
