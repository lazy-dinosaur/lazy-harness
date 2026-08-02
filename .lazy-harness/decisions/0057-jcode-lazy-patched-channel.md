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
  - keep one separate lazy-patched channel rebased on official upstream
  - bundle approved generic lifecycle primitives and trusted-root instruction precedence
  - make spawned agents inherit the same trusted-root harness authority
  - block only conflicting foreign harness authority, not all personal configuration
- Must not:
  - hardcode lazy-harness records or project policy into Jcode core
  - replace the official stable channel before candidate validation passes
  - let sibling, downstream, or foreign-root overlays override the active trusted root
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

The user also confirmed that the earlier Jcode reliability mechanism remains required: the active project's full `.lazy-harness/AGENTS.md` grammar must remain authoritative throughout the session and across spawned agents. The desired behavior is not a global deletion of teammate or personal configuration. It is exact trusted-root precedence: instructions originating from another root, downstream host, or conflicting harness surface cannot override the canonical active root.

Maintaining these changes by repeatedly editing whichever binary happens to be current would be fragile. A named patch channel with an explicit patch series, upstream rebase workflow, candidate validation, and reversible promotion is required.

## Decision

Adopt one rebase-maintained **lazy-patched Jcode channel** until the necessary generic primitives are available upstream.

1. The official stable/current builds remain independently recoverable.
2. The lazy-patched channel is built from an explicit upstream commit plus an ordered patch series.
3. The patch series contains the already approved generic lifecycle primitives and one generic trusted-root harness-authority capability.
4. Lazy-harness policy stays in `.lazy-harness`; Jcode exposes only generic transport, root identity, instruction-source precedence, inheritance, and conflict isolation.
5. The active exact trusted root is authoritative for project/team harness instructions. Spawned agents inherit that authority and may not replace it with a foreign-root harness.
6. Personal model preferences and non-conflicting overlays remain allowed. Only instructions that claim conflicting project/team authority are suppressed, with diagnostic evidence rather than silent global deletion.
7. Each upstream update is handled by rebasing or replaying the patch series onto a fresh candidate, running focused and full validation, and switching the lazy-patched pointer only after success.
8. When an equivalent capability lands upstream and passes parity validation, its local patch is removed independently.

## Rejected alternatives

- Modify the official current binary ad hoc after every update — rejected because provenance, rollback, and patch membership become unclear.
- Permanently fork Jcode as a lazy-harness-specific runtime — rejected because generic capabilities should remain upstreamable and Jcode core must not own canonical policy.
- Ignore every teammate or personal overlay unconditionally — rejected because it would remove legitimate non-conflicting user configuration and create surprising global behavior.
- Restore generated project-local `.jcode` policy wiring — rejected by ADR 0056 because it duplicates canonical policy.

## Consequences

- There is one coherent local product to test and operate instead of several unrelated binary edits.
- Official Jcode updates require a controlled rebase/replay and validation step before promotion.
- Trusted-root authority is explicit, inherited, scoped, and diagnosable rather than implemented as a broad “ignore teammates” switch.
- The patch channel is temporary infrastructure. Patch count should shrink as generic capabilities land upstream.

## Implementation map

- Status: decision accepted; exact implementation plan awaiting execution approval.
- Existing Jcode patch commits:
  - `38036ca63` — generic `before_model` transport.
  - `eaa12fc30` — generic native ask transport.
  - `6597ac650` — bounded ask controls.
  - `dcc8ed100` — generic bounded follow-up controller.
- Planned Jcode responsibilities:
  - represent canonical active-root identity separately from incidental working-directory discovery,
  - preserve instruction source/root metadata through main and spawned-agent sessions,
  - apply deterministic project/team authority precedence,
  - expose conflict diagnostics without storing canonical lazy-harness policy.
- Lazy-harness responsibilities:
  - own trusted-root registration and canonical records,
  - configure/use generic Jcode capabilities through the thin adapter,
  - validate exact-root activation, inheritance, foreign-root isolation, and non-conflicting overlay preservation.
- Tests / protection:
  - Jcode instruction precedence and spawned-agent inheritance tests.
  - Lazy-harness Jcode adapter and trusted-root regression fixtures.
  - Candidate build, focused crate tests, guardrails, live trusted/untrusted-root smoke, and final `lazy validate --plan standard`.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0056-multi-runtime-thin-adapters.md`
  - Planning: `.lazy-harness/planning/jcode-lazy-patched-channel-plan.md`
  - SDD: `.lazy-harness/spec/platform/jcode-agent-adapter.md`
  - TDD: `.lazy-harness/tests/jcode-agent-adapter.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`

## Rule placement

- Rule: maintain one validated, rebase-managed lazy-patched Jcode channel with trusted-root harness precedence.
- Scope: framework-global.
- Primary record: `.lazy-harness/decisions/0057-jcode-lazy-patched-channel.md`.
- Why not AGENTS.md: this is runtime distribution and precedence architecture, not per-turn grammar.
- Why not `.jcode`: local Jcode configuration is transport/personal state, not canonical team policy.
- Confirmation: user-confirmed option A on 2026-08-02.

## Discovery capture

- DDD: no independent delta.
- SDD: candidate delta for generic root-aware instruction precedence; update after approved implementation establishes the contract.
- BDD: no independent end-user product flow; runtime diagnostics may require a behavior record if made user-visible.
- TDD: candidate regression coverage for inheritance, conflict isolation, and overlay preservation.
- SSOT: existing harness enforcement and project identity records remain canonical; no ownership transfer to Jcode.
- Planning: exact staged rollout is captured in `.lazy-harness/planning/jcode-lazy-patched-channel-plan.md`.
