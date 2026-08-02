# Planning — Lazy-Patched Jcode Channel

Status: needs-execution-approval
Date: 2026-08-02
Layer: Planning
Primary ADR: `.lazy-harness/decisions/0057-jcode-lazy-patched-channel.md`
Related plan: `.lazy-harness/planning/jcode-native-lifecycle-parity-plan.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: transient-plan
- Confidence: high
- Aliases:
  - Jcode 패치 버전 통합
  - lazy-patched 유지 계획
  - trusted-root precedence rollout
- Applies when:
  - implementing or updating the user-confirmed lazy-patched Jcode channel
  - rebasing the patch series onto a newer official Jcode revision
- Must:
  - preserve the four existing lifecycle patches as separately reviewable commits
  - add trusted-root authority as a generic, independently removable patch
  - validate a candidate before switching the installed lazy-patched pointer
  - keep official stable/current rollback targets recoverable
- Must not:
  - mutate unrelated dirty work in either repository
  - push, release, or replace the official stable channel without separate approval
  - begin source implementation before explicit approval of this exact plan
- Record completion:
  - record each phase commit, validation result, residual gap, rebase, and promotion outcome here
- Related records:
  - `.lazy-harness/decisions/0057-jcode-lazy-patched-channel.md`
  - `.lazy-harness/planning/jcode-native-lifecycle-parity-plan.md`
  - `.lazy-harness/spec/platform/jcode-agent-adapter.md`

## Confirmed scope

User-confirmed option A on 2026-08-02:

- Maintain one separate lazy-patched Jcode version.
- Include the existing `before_model`, native ask, bounded ask, and bounded follow-up patches.
- Restore the previously required full lazy-harness grammar authority for the active trusted project.
- Make spawned agents inherit the same trusted-root authority.
- Suppress only conflicting foreign-root project/team harness instructions.
- Preserve personal and non-conflicting overlays.
- Maintain the channel by rebasing/replaying the patch series on official upstream.

## Exact execution plan

### Phase 0 — Patch-series and channel contract

1. Inventory the current Jcode branch, four existing patch commits, installed binary pointers, and unrelated dirty files.
2. Define the lazy-patched channel metadata: upstream base SHA, ordered patch SHAs, build provenance, validation status, and rollback target.
3. Add non-destructive doctor/status output that distinguishes official and lazy-patched builds.

### Phase 1 — Generic trusted-root harness authority

1. Trace Jcode instruction loading for root `AGENTS.md`, prompt overlays, global overlays, and spawned-agent prompts.
2. Add generic instruction source metadata and precedence based on canonical root identity and authority class.
3. Ensure the active trusted root's project/team instructions cannot be replaced by sibling/downstream/foreign-root instructions.
4. Preserve system/user priority and non-conflicting personal preferences.
5. Emit bounded diagnostics identifying suppressed source class/root without leaking prompt contents.

### Phase 2 — Spawn inheritance and isolation

1. Pass active-root authority into swarm/subagent creation explicitly.
2. Reject or quarantine a spawned agent's conflicting foreign-root harness authority.
3. Protect root/session isolation so a long-lived server cannot leak authority between projects.
4. Cover local, remote, and headless paths honestly according to supported capabilities.

### Phase 3 — Lazy-harness adapter integration

1. Extend the thin adapter/config only enough to select and verify generic Jcode capabilities for exact trusted roots.
2. Keep all grammar, records, trust registry, and lifecycle policy in `.lazy-harness`.
3. Update SDD/TDD/SSOT records only for independently proven semantic deltas.
4. Add fixtures for trusted-root precedence, spawned inheritance, foreign-root isolation, untrusted silent no-op, and non-conflicting overlay preservation.

### Phase 4 — Candidate build and promotion

1. Rebase/replay the ordered patch series onto the selected official upstream revision.
2. Run Jcode formatting, focused crate tests, checks, guardrails, and a source build.
3. Run lazy-harness focused adapter tests and one final `lazy validate --plan standard` after the last mutation.
4. Install to a versioned candidate path and run live trusted-root, foreign-root, spawned-agent, ask, re-grounding, and follow-up smoke tests.
5. Switch only the lazy-patched channel pointer after all required evidence passes. Keep official stable/current rollback paths untouched.

## Stop conditions

Stop and request a revised decision if:

- instruction precedence requires embedding lazy-harness-specific policy in Jcode core,
- the implementation would suppress all personal overlays rather than only conflicting authority,
- root identity cannot remain isolated across server sessions,
- spawned-agent inheritance requires a breaking protocol change without compatibility,
- the upstream rebase conflicts with unrelated user-owned work,
- validation cannot distinguish official and patched build provenance,
- a new user constraint changes this confirmed scope.

## Validation matrix

| Case | Expected result |
|---|---|
| trusted lazy root, main agent | full canonical grammar remains authoritative |
| trusted lazy root, spawned agent | same root authority is inherited |
| conflicting foreign-root harness | conflicting project/team authority is suppressed and diagnosed |
| non-conflicting personal overlay | preserved |
| untrusted or ordinary project | lazy-harness adapter remains silent |
| upstream candidate update | patch series applies and all gates pass before promotion |
| rollback | official and prior patched binary remain selectable |

## Implementation map

- Status: plan approved in direction, exact execution approval pending.
- Jcode repository: `/home/lazydino/dev/jcode` is the mapped implementation target already recorded by the lifecycle parity plan.
- Existing patches: `38036ca63`, `eaa12fc30`, `6597ac650`, `dcc8ed100`.
- Lazy-harness integration: `.lazy-harness/scripts/jcode-adapter.ts`, `.lazy-harness/scripts/jcode-package.ts`, `.lazy-harness/scripts/jcode-trust.ts`, `.lazy-harness/spec/platform/jcode-agent-adapter.md`, `.lazy-harness/tests/jcode-agent-adapter.md`.
- Protection: Jcode focused tests/guardrails plus lazy-harness focused fixtures and final standard validation.

## Rule placement

- Rule: execute the accepted patched-channel architecture through bounded, independently reversible phases.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/jcode-lazy-patched-channel-plan.md`.
- Confirmation: requirements confirmed 2026-08-02; source execution not yet approved.

## Discovery capture

- DDD: no independent delta.
- SDD: update after Phase 1 proves the generic precedence contract.
- BDD: update only if diagnostics create a new visible interaction flow.
- TDD: required for precedence, inheritance, isolation, preservation, provenance, and rollback cases.
- ADR: `.lazy-harness/decisions/0057-jcode-lazy-patched-channel.md` is the canonical architecture decision.
- SSOT: no independent ownership delta; existing trusted-root and project identity records remain authoritative.
