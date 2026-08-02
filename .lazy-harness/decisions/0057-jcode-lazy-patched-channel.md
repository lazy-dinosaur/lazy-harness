# ADR 0057 — Rebase-Maintained Lazy-Patched Jcode Channel

Status: accepted
Date: 2026-08-02
Layer: ADR
Related ADR: `.lazy-harness/decisions/0051-jcode-parity-grammar-regrounding.md`, `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`, `.lazy-harness/ssot/project-identity.md`
Related planning: `.lazy-harness/planning/jcode-lazy-patched-channel-plan.md`, `.lazy-harness/planning/jcode-native-lifecycle-parity-plan.md`

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Confidence: high
- Aliases:
  - lazy-patched Jcode
  - 하네스 패치 버전
  - Jcode 패치 채널
  - trusted-root 하네스 우선권
- Surface terms:
  - 다른 팀원 하네스 무시
  - 외부 하네스 충돌 격리
  - upstream rebase 유지
- Applies when:
  - maintaining Jcode capabilities that are not yet available in the official current binary
  - deciding instruction precedence for a trusted lazy-harness root and spawned agents
  - updating Jcode while preserving lazy-harness lifecycle parity
- Must:
  - reuse and modernize the existing `custom/lazydino-harness` patch-stack maintenance path
  - keep approved lifecycle primitives as separately removable patches
  - suppress project-root `AGENTS.md` only through an explicit private prompt-source flag
  - inject canonical `.lazy-harness/AGENTS.md` through the exact-trusted-root `before_model` adapter
- Must not:
  - hardcode lazy-harness records or project policy into Jcode core
  - replace the official stable channel before candidate validation passes
  - add semantic prompt-conflict detection or a redundant spawned-agent authority patch
- Record completion:
  - patch membership, precedence, rebase, or promotion changes update this ADR and its rollout plan
- Related records:
  - `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - `.lazy-harness/planning/jcode-native-lifecycle-parity-plan.md`
  - `.lazy-harness/ssot/harness-enforcement-policy.md`

## Context

The official Jcode current binary did not yet provide all capabilities needed for the user-confirmed lazy-harness parity direction. Four generic Jcode commits were therefore built and installed on the local current channel:

- `38036ca63` — synchronous `before_model` context transport,
- `eaa12fc30` — native ask transport,
- `6597ac650` — bounded ask interaction enforcement,
- `dcc8ed100` — bounded turn-followup controller.

The user also confirmed that the earlier Jcode reliability mechanism remains required: the active project's full `.lazy-harness/AGENTS.md` grammar must remain authoritative throughout the session and across spawned agents. Source review corrected the first design: Jcode already reloads project prompt sources from each session's working directory, and swarm children already inherit the coordinator working directory. A new semantic conflict engine and a separate spawn-authority patch are therefore unnecessary.

The historical private-harness patch (`150eee41e`) solved the strict-ignore case through deterministic source controls such as `ignore_project_agents`, not by interpreting prompt meaning. The accepted modern form keeps only the narrow behavior needed here: a gitignored `.jcode/config.local.toml` transport flag suppresses `<project>/AGENTS.md` for an explicitly trusted lazy-harness root, while the existing synchronous `before_model` adapter injects canonical `.lazy-harness/AGENTS.md`. Global personal overlays remain active.

Maintaining these changes by repeatedly editing whichever binary happens to be current would be fragile. A named patch channel with an explicit patch series, upstream rebase workflow, candidate validation, and reversible promotion is required.

## Decision

Adopt one rebase-maintained **lazy-patched Jcode channel** until the necessary generic primitives are available upstream.

1. The official stable/current builds remain independently recoverable.
2. Reuse and modernize the existing `custom/lazydino-harness`, `reapply-custom-stack.sh`, maintenance ledger, and install-helper model rather than creating a second custom-stack system.
3. The ordered patch series contains the approved generic lifecycle patches, native same-session cwd restoration while upstream lacks it, plus one narrow generic `ignore_project_agents` prompt-source control when required.
4. For each exact trusted lazy-harness root, a gitignored `.jcode/config.local.toml` may contain only the private runtime transport flag `[prompt] ignore_project_agents = true`; it must not contain canonical grammar or project policy.
5. The exact-trusted-root `before_model` adapter injects canonical `.lazy-harness/AGENTS.md` before every provider request. Untrusted and ordinary projects do not receive this injection.
6. Spawned agents require no separate authority patch: they inherit the coordinator working directory and therefore the same local prompt-source setting and trusted-root adapter behavior.
7. Global personal overlays, model preferences, and other non-project-policy configuration remain active.
8. Each upstream update is handled by replaying the explicit patch series onto a fresh candidate, running focused and full validation, and switching only the lazy-patched channel pointer after success.
9. When an equivalent capability lands upstream and passes parity validation, its local patch is removed independently.
10. After explicit user selection, the normal `~/.local/bin/jcode` launcher may atomically target the dedicated `~/.jcode/builds/lazy-patched/jcode` pointer. Official stable/current pointers remain unchanged, and rollback restores the launcher's exact prior symlink target.

## Rejected alternatives

- Modify the official current binary ad hoc after every update — rejected because provenance, rollback, and patch membership become unclear.
- Permanently fork Jcode as a lazy-harness-specific runtime — rejected because generic capabilities should remain upstreamable and Jcode core must not own canonical policy.
- Ignore every teammate or personal overlay unconditionally — rejected because it would remove legitimate non-conflicting user configuration and create surprising global behavior.
- Restore generated project-local `.jcode` policy wiring — rejected by ADR 0056 because it duplicates canonical policy.
- Add semantic conflict detection and root-authority metadata throughout Jcode — rejected because source classes are finite, semantic filtering is unreliable, and child working-directory inheritance already exists.

## Consequences

- There is one coherent local product to test and operate instead of several unrelated binary edits.
- Official Jcode updates require a controlled rebase/replay and validation step before promotion.
- Trusted-root behavior is implemented through deterministic source selection plus request-scoped canonical injection, not semantic prompt inspection.
- The patch channel is temporary infrastructure. Patch count should shrink as generic capabilities land upstream.
- The normal launcher may provide the same patched runtime across every project, while stable/current remain independent rollback targets.

## Implementation map

- Status: refreshed same-session cwd candidate installed and normal launcher verified with durable exact rollback; closing standard validation follows the final record mutation.
- Existing Jcode patch commits:
  - `38036ca63` — generic `before_model` transport.
  - `eaa12fc30` — generic native ask transport.
  - `6597ac650` — bounded ask controls.
  - `dcc8ed100` — generic bounded follow-up controller.
  - `71adb1853` — native same-session cwd commands, remote protocol, LLM cwd tool, client propagation, and target-root prompt rebuilding.
  - `2f44249d1` — transactional cwd save-failure rollback and success-side-effect suppression.
  - `d58409274` — live session cwd retention across same-session remote reconnects.
- Jcode implementation:
  - `/home/lazydino/dev/jcode` commit `15e87544c` implements the narrow `ignore_project_agents` prompt-source flag, working-directory local-config merge, project `AGENTS.md` suppression, prompt accounting, and regression tests.
  - `/home/lazydino/dev/jcode` commit `71adb1853` restores `/pwd`, `/cwd [path]`, `/cd <path>`, same-session persistence, remote `SetCwd`/`SessionCwd`, LLM cwd tool side effects, client propagation, skill/header refresh, and the post-conversation two-root AGENTS regression.
  - `/home/lazydino/dev/jcode` commit `2f44249d1` makes cwd persistence transactional and prevents failed save paths from publishing successful local, remote, or tool-visible cwd effects.
  - `/home/lazydino/dev/jcode` commit `d58409274` makes reconnect of the exact established remote session advertise its live cwd while preserving launch cwd for initial or different-session subscriptions.
  - `/home/lazydino/dev/jcode` commit `daf9d3d90` reconciles the root package's existing `jcode-provider-core` dev-dependency into `Cargo.lock`; the lock delta is one dependency-list line with no version, checksum, source, or transitive-package churn.
  - `/home/lazydino/dev/jcode/scripts/lazydino/install-custom-jcode.sh` builds exact-source candidates, stores strict data-only JSON provenance, prevents dirty-state reuse collisions, publishes immutable completed candidates, atomically switches only the dedicated pointer, and restores interrupted post-promotion changes.
  - `/home/lazydino/dev/jcode/LAZYDINO_MAINTENANCE.md` documents replay, provenance, validation, protected launchers, direct-candidate use, and rollback.
  - Channel commits: `4481df5f9` adds the isolated helper/docs, `b2e566586` hardens provenance/publication/rollback, and `04092f6de` makes signal-triggered cleanup nonzero and concurrency-safe.
- Lazy-harness implementation:
  - `.lazy-harness/scripts/jcode-local-config.ts` owns reversible exact-root local transport configuration.
  - `.lazy-harness/scripts/jcode-adapter.ts` injects bounded canonical grammar for exact trusted roots.
  - `.lazy-harness/scripts/jcode-package.ts` exposes install/trust/remove/doctor/smoke flows without moving canonical policy into `.jcode`.
- Installed candidate:
  - `~/.jcode/builds/lazy-patched/versions/daf9d3d90-b6ee0d1e472a-release-bb2f6034b9335651/jcode`.
  - `~/.jcode/builds/lazy-patched/jcode` points to that candidate.
  - `~/.local/bin/jcode` now points to `~/.jcode/builds/lazy-patched/jcode`; mode-0600 rollback state preserves its exact prior target `~/.jcode/builds/current/jcode`.
  - `~/.jcode/builds/stable/jcode` and `~/.jcode/builds/current/jcode` retain their exact pre-promotion targets.
  - Strict provenance records HEAD `daf9d3d90912223f2c765c1a6b0f081af46d8b4e`, source digest `bb2f6034b93356512eae791975383c479e24c8dd94372d932b2e607647db2dff`, Cargo.lock digest `b6ee0d1e472a9ca7d3bb0738ce5c873a7f189c8288db53535987bc84d725e474`, and binary digest `122e6637e8ca10f2e4bd5b209dbec7954b59efb856b28f070bd4e120d5a150d4`.
- Tests / protection:
  - Focused Jcode prompt/config tests, formatting, source checks/build, direct `version --json`, offline help, provenance round-trip, candidate reuse, and protected-pointer checks passed.
  - Cwd restoration passed `cargo check -p jcode-app-core -p jcode-tui -p jcode-protocol`, focused protocol/app-core cwd tests, and the post-visible-conversation target-root prompt regression.
  - Transactional failure injection and remote error-only event tests passed for `2f44249d1`; the exact TUI reconnect regression and `cargo check -p jcode-tui` passed for `d58409274`.
  - `.lazy-harness/scripts/self-test.py#check_jcode_agent_adapter` protects trusted/untrusted roots, reversible local config, bounded initial/post-tool injection, child/root isolation, and overlay preservation.
  - Normal launcher activation now passes candidate provenance/digest/version validation, offline help, trusted-root doctor, protected-pointer checks, and launcher status. Server reload, provider traffic, push, and rebase remain intentionally unperformed.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - Planning: `.lazy-harness/planning/jcode-lazy-patched-channel-plan.md`
  - SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`

## Rule placement

- Rule: maintain one validated custom Jcode patch channel using explicit prompt-source control and exact-root lifecycle injection.
- Scope: framework-global.
- Primary record: `.lazy-harness/decisions/0057-jcode-lazy-patched-channel.md`.
- Why not AGENTS.md: this is runtime distribution and precedence architecture, not per-turn grammar.
- Why not `.jcode`: local Jcode configuration is transport/personal state, not canonical team policy.
- Confirmation: user-confirmed original channel direction and corrected explicit-source option A on 2026-08-02.
- Launcher amendment: user-confirmed option A on 2026-08-02; atomically repoint only `~/.local/bin/jcode` to the dedicated lazy-patched pointer and preserve exact rollback plus official stable/current.

## Discovery capture

- DDD: no independent delta.
- SDD: implemented by the existing Jcode adapter/local-config contract; no additional independent contract delta from candidate packaging.
- BDD: no independent end-user product flow; runtime diagnostics may require a behavior record if made user-visible.
- TDD: existing adapter regression record covers source suppression, child inheritance, untrusted silence, overlay preservation, and reversible configuration; candidate packaging evidence remains in this ADR and rollout plan.
- SSOT: updated harness enforcement boundary; canonical grammar remains in `.lazy-harness`, never `.jcode`.
- Planning: staged rollout and completion evidence are captured in `.lazy-harness/planning/jcode-lazy-patched-channel-plan.md`.
