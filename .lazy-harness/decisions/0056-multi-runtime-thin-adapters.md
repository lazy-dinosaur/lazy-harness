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
  - session cwd
  - /cwd
- Applies when:
  - adding, installing, removing, or auditing an agent-runtime integration
  - deciding how Pi, OMP, or Jcode deliver lazy-harness lifecycle behavior
- Must:
  - keep canonical policy and lifecycle meaning in `.lazy-harness`
  - implement each runtime as a thin adapter over shared hooks
  - preserve Pi/OMP behavior while Jcode support is introduced independently
  - activate automatically only inside a user-trusted lazy-harness project
  - keep any project-local Jcode file transport-only, private, reversible, and free of canonical policy
  - when a runtime changes the active session cwd, preserve the existing conversation while re-grounding hooks, tools, grammar, and evidence against the new live root
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
3. Jcode machine bootstrap is explicit once; project activation is unified through lazy-harness and runtime application remains automatic only for exact trusted roots.
4. Outside a trusted lazy-harness root, every Jcode hook exits successfully without mutation, output, state creation, or repository script execution.
5. Global Jcode configuration is changed only through an explicit install command. An exact trusted root may additionally receive a gitignored `.jcode/config.local.toml` containing only a reversible managed transport flag such as `[prompt] ignore_project_agents = true`, with TOML-safe backup/merge/remove behavior.
6. Project/team policy remains in canonical records. Jcode config, prompt overlay, skills, and memory are transport or personal surfaces only; the local flag must not duplicate grammar or policy.
7. Parity claims are capability-specific. Unsupported Jcode surfaces such as Pi-style `context` reinjection, bounded `agent_end` continuation, or native selectable `ask` are reported honestly and require live evidence before equivalence is claimed.
8. `lazy agent activate --target <root>` is the explicit project-consent surface for Pi, OMP, and Jcode. It may register the exact canonical root in the Jcode trust registry and manage only reversible runtime transport state.
9. `lazy init --target <root>` may invoke the unified activation because the user explicitly selected the target and requested installation. `lazy sync` must never create trust for an untrusted root; it may validate or repair already trusted roots and report that explicit activation is required otherwise.
10. Machine-level selection of the lazy-patched Jcode executable is separate from project trust and must not silently replace official stable/current or the normal launcher.
11. Project-folder movement is a runtime-native same-session cwd transition, not worktree creation or a new project session. Jcode exposes `/pwd`, `/cwd [path]`, and `/cd <path>`; Pi/OMP retain their native same-session move surface. The next provider boundary must use the target directory's instructions, and lazy-harness evidence from the prior root must be cleared before it can authorize target-root work.

## Rejected alternatives

- Restore `.jcode` generation and the old directory bridge — rejected because it duplicates policy and revives superseded infrastructure.
- Fold Jcode into `pi-package.ts` — rejected because Jcode uses global TOML hooks rather than Pi/OMP package manifests and extension events.
- Configure projects with Jcode-owned policy — rejected because canonical policy belongs in `.lazy-harness`; a private source-selection flag is transport, not policy.
- Trust every directory containing `.lazy-harness/bin/lazy` — rejected because an arbitrary checkout could otherwise trigger execution of repository-controlled hook scripts.
- Claim full parity from static inspection — rejected because observer ordering, mid-turn interleaving, and turn-end continuation require live verification.

## Consequences

- Users perform one explicit machine bootstrap. New projects activate Pi, OMP, and Jcode through `lazy init` or `lazy agent activate`; `lazy sync` does not silently expand trust.
- Pi/OMP remain independently installable and unaffected by Jcode configuration.
- The adapter must preserve root-scoped evidence and avoid cross-project contamination in the long-lived Jcode server.
- A same-session cwd transition preserves messages and session identity but invalidates prior-root adapter evidence and project grammar.
- Jcode observer hooks cannot be treated as synchronous prompt-injection or blocking surfaces.
- ADR 0050 remains decision history for the removed directory bridge but is no longer the active runtime-support boundary.
- One machine-global lazy-patched candidate may be shared by every trusted project, but launcher promotion remains a separately approved machine-level action.

## Implementation map

- Status: unified Pi/OMP/Jcode activation, init/sync rollout, normal launcher promotion, native same-session cwd restoration, independent review, refreshed candidate installation, and focused regressions complete; closing standard validation follows the final record mutation
- Primary files:
  - `.lazy-harness/scripts/jcode-adapter.ts` — normalize Jcode hooks, enforce exact trusted-root activation, isolate secret-free state, and bridge canonical lifecycle hooks.
  - `.lazy-harness/scripts/jcode-trust.ts` — own canonical trusted-root registry reads/writes.
  - `.lazy-harness/scripts/jcode-package.ts` — TOML-validated install/remove/doctor/smoke plus trust management.
  - `.lazy-harness/bin/lazy` — dispatch `lazy jcode ...`.
  - `.lazy-harness/scripts/self-test.py` — protect adapter/config/trust/CLI behavior.
- Flow:
  1. `lazy jcode install` validates and merges managed global hooks, backs up config, and registers the selected canonical root.
  2. Unified activation makes `lazy agent activate` the explicit Pi/OMP/Jcode project activation surface, installs/repairs global hooks against the stable synced framework source, and transactionally manages exact-root trust/local transport.
  3. `lazy init` activates its explicit new target; `lazy sync` repairs only trusted roots and publishes its marker after successful repair.
  4. Jcode invokes the adapter with official hook environment and tool input.
  5. The adapter canonicalizes root evidence and exits silently unless the exact root is user-trusted.
  6. Trusted hooks invoke canonical lifecycle scripts and store only bounded secret-free evidence in canonical runtime state.
  7. Native `/cwd` mutates the existing Jcode session working directory; the following request supplies the target cwd, and the adapter replaces the state envelope before injecting the target root's canonical grammar.
- Key symbols:
  - `activeRoot` / `statePath` / `withState` / `preTool` (`jcode-adapter.ts`) — trust gate, canonical runtime path, owned locks, and deny translation.
  - `/home/lazydino/dev/jcode` commit `71adb1853` — shared cwd resolver, local `/pwd`/`/cwd`/`/cd`, remote protocol/client propagation, persisted `Agent::set_working_dir`, LLM cwd tool, and post-conversation target-root prompt regression.
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
  - Planning: `.lazy-harness/planning/unified-project-context-move.md`
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

### 2026-08-02 amendment — unified multi-project activation

- Confirmation: user-confirmed option A on 2026-08-02.
- `lazy init` and `lazy agent activate` form the explicit project-consent path for all three runtimes.
- `lazy sync` repairs/checks existing trusted activation but never auto-trusts an untrusted checkout.
- Projects share one machine-global lazy-patched Jcode candidate instead of rebuilding Jcode per project.
- The user selected normal-launcher option A on 2026-08-02: atomically point `~/.local/bin/jcode` at the dedicated lazy-patched pointer, preserve official stable/current, and retain exact launcher rollback.

### 2026-08-02 amendment — context-preserving project folder move

- Confirmation: user corrected the earlier worktree-first interpretation and approved restoration after comparison with the historical Jcode cwd implementation.
- Movement accepts only an explicit existing directory and does not create a branch, worktree, directory, process, or new conversation session.
- Jcode commit `71adb1853` restores native same-session `/pwd`, `/cwd [path]`, `/cd <path>`, remote `SetCwd`/`SessionCwd`, and the LLM cwd tool.
- Future provider requests rebuild project instructions from the updated session working directory. The lazy-harness adapter treats request payload cwd as current authority, replaces stale root state, and injects only the target trusted root's `.lazy-harness/AGENTS.md`.
- Pi/OMP source is unchanged in this work unit because their native same-session move path already exposes the required live cwd semantics. The separate custom new-session `/lazy-move` remains outside this decision.

## Discovery capture

- DDD: no independent delta; no business vocabulary or invariant changed.
- SDD: independent delta — new Jcode hook/config adapter contract.
- BDD: no independent user-product flow; this is agent runtime integration.
- TDD: independent delta — Jcode adapter and Pi/OMP non-regression protection.
- SSOT: independent delta — `.lazy-harness/ssot/harness-enforcement-policy.md` now owns the multi-runtime delivery boundary.
- Planning: independent transient rollout state in `.lazy-harness/planning/jcode-runtime-adapter-pilot.md`.
