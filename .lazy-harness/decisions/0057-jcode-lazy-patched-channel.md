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
3. The ordered patch series contains the four approved generic lifecycle patches plus, only if current upstream still lacks it, one narrow generic `ignore_project_agents` prompt-source control.
4. For each exact trusted lazy-harness root, a gitignored `.jcode/config.local.toml` may contain only the private runtime transport flag `[prompt] ignore_project_agents = true`; it must not contain canonical grammar or project policy.
5. The exact-trusted-root `before_model` adapter injects canonical `.lazy-harness/AGENTS.md` before every provider request. Untrusted and ordinary projects do not receive this injection.
6. Spawned agents require no separate authority patch: they inherit the coordinator working directory and therefore the same local prompt-source setting and trusted-root adapter behavior.
7. Global personal overlays, model preferences, and other non-project-policy configuration remain active.
8. Each upstream update is handled by replaying the explicit patch series onto a fresh candidate, running focused and full validation, and switching only the lazy-patched channel pointer after success.
9. When an equivalent capability lands upstream and passes parity validation, its local patch is removed independently.

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

## Implementation map

- Status: decision accepted; exact implementation plan awaiting execution approval.
- Existing Jcode patch commits:
  - `38036ca63` — generic `before_model` transport.
  - `eaa12fc30` — generic native ask transport.
  - `6597ac650` — bounded ask controls.
  - `dcc8ed100` — generic bounded follow-up controller.
- Planned Jcode responsibilities:
  - expose the narrow generic `ignore_project_agents` prompt-source flag if upstream lacks it,
  - merge the flag from gitignored project-local `.jcode/config.local.toml`,
  - keep existing working-directory inheritance for spawned sessions unchanged.
- Lazy-harness responsibilities:
  - own trusted-root registration and canonical records,
  - safely merge/remove only the managed local transport flag for exact trusted roots,
  - inject `.lazy-harness/AGENTS.md` through `before_model`,
  - validate trusted activation, untrusted silence, child inheritance, and personal-overlay preservation.
- Tests / protection:
  - Jcode prompt-source config and working-directory loading tests.
  - Lazy-harness local-config merge/remove, adapter, and trusted-root regression fixtures.
  - Candidate build, focused crate tests, guardrails, live trusted/untrusted-root smoke, and final `lazy validate --plan standard`.
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

## Discovery capture

- DDD: no independent delta.
- SDD: candidate delta for local transport-flag merge/remove and prompt-source control; update after approved implementation establishes the contract.
- BDD: no independent end-user product flow; runtime diagnostics may require a behavior record if made user-visible.
- TDD: candidate regression coverage for source suppression, child inheritance, untrusted silence, and overlay preservation.
- SSOT: updated harness enforcement boundary; canonical grammar remains in `.lazy-harness`, never `.jcode`.
- Planning: exact staged rollout is captured in `.lazy-harness/planning/jcode-lazy-patched-channel-plan.md`.
