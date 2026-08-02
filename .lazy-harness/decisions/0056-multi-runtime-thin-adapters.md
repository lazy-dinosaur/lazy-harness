# ADR 0056 — Multi-Runtime Thin Adapters for Pi, OMP, and Jcode

Status: accepted
Date: 2026-08-01
Layer: ADR
Supersedes: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`
Related SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`, `.lazy-harness/spec/platform/pi-agent-package.md`
Related TDD: `.lazy-harness/tests/jcode-agent-adapter.md`, `.lazy-harness/tests/pi-agent-package.md`
Related planning: `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`
Related ADR: `.lazy-harness/decisions/0057-jcode-lazy-patched-channel.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Confidence: high
- Aliases:
  - Jcode 기본 적용
  - Jcode 공식 지원
  - 다중 런타임 어댑터
  - thin runtime adapter
- Surface terms:
  - lazy jcode
  - Jcode hooks
  - Pi OMP Jcode parity
- Applies when:
  - adding, installing, removing, or auditing an agent-runtime integration
  - deciding how Pi, OMP, or Jcode deliver lazy-harness lifecycle behavior
- Must:
  - keep canonical policy and lifecycle meaning in `.lazy-harness`
  - implement each runtime as a thin adapter over shared hooks
  - preserve Pi/OMP behavior while Jcode support is introduced independently
  - activate automatically only inside a user-trusted lazy-harness project
- Must not:
  - restore the generated `.jcode` directory bridge or duplicate policy in runtime config
  - treat Jcode memory as project or team policy authority
  - confuse the thin adapter boundary with the separately governed generic Jcode patch channel in ADR 0057
- Record completion:
  - runtime adapter changes update this ADR and the affected SDD/TDD records
- Related records:
  - `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`
  - `.lazy-harness/decisions/0051-jcode-parity-grammar-regrounding.md`
  - `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - `.lazy-harness/decisions/0057-jcode-lazy-patched-channel.md`

## Context

ADR 0050 removed the old generated Jcode directory bridge after Pi/OMP achieved parity. That decision correctly eliminated duplicate generated policy and obsolete Jcode-specific wiring, but it assumed Jcode lacked a stable official adapter surface.

Jcode `v0.64.114-dev` (`0ffe9f484`, inspected 2026-08-01) now exposes official lifecycle hooks in `[hooks]`: `turn_start`, `turn_end`, `session_start`, `session_end`, `pre_tool`, and `post_tool`. `pre_tool` is a synchronous gate: exit `0` allows, exit `2` blocks with stderr as the model-visible reason, and other failures fail open. Jcode also loads project-root `AGENTS.md` and project `.jcode/prompt-overlay.md`.

The user confirmed a two-stage pilot: establish the contract first, then implement a thin Jcode adapter with `lazy jcode install|doctor|smoke|remove`, automatic lazy-root activation, and no effect in ordinary projects.

## Decision

Adopt an agent-neutral lazy-harness core with separate thin runtime adapters:

1. Pi and OMP continue using `packages/lazy-harness-pi` unchanged unless an independently required co-change is proven.
2. Jcode receives a separate adapter that translates official `JCODE_HOOK_*` events into the canonical lazy-harness lifecycle payloads.
3. Jcode installation is explicit once and registers the current lazy root in a user-owned trust registry; runtime application is automatic only for exact trusted roots.
4. Outside a trusted lazy-harness root, every Jcode hook exits successfully without mutation, output, state creation, or repository script execution.
5. Global Jcode configuration is changed only through an explicit install command, with backup, idempotent merge, doctor, smoke, and reversible remove behavior.
6. Project/team policy remains in canonical records. Jcode config, prompt overlay, skills, and memory are transport or personal surfaces only.
7. Parity claims are capability-specific. Unsupported Jcode surfaces such as Pi-style `context` reinjection, bounded `agent_end` continuation, or native selectable `ask` are reported honestly and require live evidence before equivalence is claimed.
8. A new lazy project requires one explicit `lazy jcode trust` before global hooks may execute its lifecycle scripts; `untrust` is reversible and does not modify the project.

## Rejected alternatives

- Restore `.jcode` generation and the old directory bridge — rejected because it duplicates policy and revives superseded infrastructure.
- Fold Jcode into `pi-package.ts` — rejected because Jcode uses global TOML hooks rather than Pi/OMP package manifests and extension events.
- Configure all projects with project-owned Jcode policy — rejected because canonical policy belongs in `.lazy-harness`; global hooks only transport policy for explicitly trusted roots.
- Trust every directory containing `.lazy-harness/bin/lazy` — rejected because an arbitrary checkout could otherwise trigger execution of repository-controlled hook scripts.
- Claim full parity from static inspection — rejected because observer ordering, mid-turn interleaving, and turn-end continuation require live verification.

## Consequences

- Users perform one explicit Jcode adapter install; the current trusted lazy project then auto-activates, while each new project needs one `lazy jcode trust`.
- Pi/OMP remain independently installable and unaffected by Jcode configuration.
- The adapter must preserve root-scoped evidence and avoid cross-project contamination in the long-lived Jcode server.
- Jcode observer hooks cannot be treated as synchronous prompt-injection or blocking surfaces.
- ADR 0050 remains decision history for the removed directory bridge but is no longer the active runtime-support boundary.

## Implementation map

- Status: focused implementation, independent security review, installation, live Jcode smoke, and focused Pi/OMP non-regression complete; final standard validation pending
- Primary files:
  - `.lazy-harness/scripts/jcode-adapter.ts` — normalize Jcode hooks, enforce exact trusted-root activation, isolate secret-free state, and bridge canonical lifecycle hooks.
  - `.lazy-harness/scripts/jcode-trust.ts` — own canonical trusted-root registry reads/writes.
  - `.lazy-harness/scripts/jcode-package.ts` — TOML-validated install/remove/doctor/smoke plus trust management.
  - `.lazy-harness/bin/lazy` — dispatch `lazy jcode ...`.
  - `.lazy-harness/scripts/self-test.py` — protect adapter/config/trust/CLI behavior.
- Flow:
  1. `lazy jcode install` validates and merges managed global hooks, backs up config, and registers the selected canonical root.
  2. Jcode invokes the adapter with official hook environment and tool input.
  3. The adapter canonicalizes root evidence and exits silently unless the exact root is user-trusted.
  4. Trusted hooks invoke canonical lifecycle scripts and store only bounded secret-free evidence in canonical runtime state.
- Key symbols:
  - `activeRoot` / `statePath` / `withState` / `preTool` (`jcode-adapter.ts`) — trust gate, canonical runtime path, owned locks, and deny translation.
  - `loadTrustRegistry` / `updateTrustedRoot` / `writeTrustRegistry` (`jcode-trust.ts`) — exact canonical root trust.
  - `installText` / `removeText` / `trustCommand` / `doctor` (`jcode-package.ts`) — TOML-safe reversible config and trust diagnostics.
- Tests / protection:
  - `.lazy-harness/tests/jcode-agent-adapter.md`
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter`
- Ownership boundaries:
  - Lazy-Harness owns adapter semantics and shared lifecycle hooks.
  - Jcode owns hook dispatch, environment fields, timeout, and observer/gate semantics.
  - The adapter must not modify Jcode runtime internals or make Jcode memory canonical.
  - Generic Jcode-core patches, when temporarily required, are maintained separately under ADR 0057 and must not move lazy-harness policy into Jcode.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
  - Planning: `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
- Machine index:
  - graph ids: `kg_jcode_agent_adapter_runtime_20260801`, `kg_jcode_agent_adapter_install_20260801`, `kg_jcode_agent_adapter_test_20260801`, `kg_jcode_agent_adapter_trust_20260801`
  - generated index key: pending regeneration

## Rule placement

- Rule: support Pi, OMP, and Jcode through separate thin adapters over one canonical lazy-harness core.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
- Why not AGENTS.md: this is a runtime architecture decision, not per-turn operating grammar.
- Why not `.jcode`: Jcode configuration is transport, not canonical framework policy.
- Confirmation: user-confirmed 2026-08-01

## Discovery capture

- DDD: no independent delta; no business vocabulary or invariant changed.
- SDD: independent delta — new Jcode hook/config adapter contract.
- BDD: no independent user-product flow; this is agent runtime integration.
- TDD: independent delta — Jcode adapter and Pi/OMP non-regression protection.
- SSOT: independent delta — `.lazy-harness/ssot/harness-enforcement-policy.md` now owns the multi-runtime delivery boundary.
- Planning: independent transient rollout state in `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`.
