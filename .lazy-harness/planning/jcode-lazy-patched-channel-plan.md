# Planning — Lazy-Patched Jcode Channel

Status: in-progress
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
  - reuse the existing custom-stack maintenance scripts and ledger
  - add only a narrow `ignore_project_agents` source-control patch if upstream lacks it
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
- Suppress `<project>/AGENTS.md` only in exact trusted lazy-harness roots through private `.jcode/config.local.toml`.
- Inject canonical `.lazy-harness/AGENTS.md` through `before_model` on every provider request.
- Preserve global personal overlays and model preferences.
- Rely on existing child `working_dir` inheritance; add no separate spawn-authority patch.
- Maintain the channel by rebasing/replaying the patch series on official upstream.

## Exact execution plan

### Phase 0 — Patch-series and channel contract

1. Inventory the current Jcode branch, four existing patch commits, installed binary pointers, and unrelated dirty files.
2. Rebase or reconstruct the existing `custom/lazydino-harness` maintenance branch on current upstream rather than creating a parallel custom-stack architecture.
3. Modernize `LAZYDINO_MAINTENANCE.md`, `reapply-custom-stack.sh`, and the install helper with the current ordered patch SHAs, upstream base, validation status, and rollback target.
4. Add non-destructive doctor/status output that distinguishes official and lazy-patched builds.

### Phase 1 — Narrow prompt-source control

1. Confirm whether current upstream lacks an effective per-working-directory `ignore_project_agents` setting.
2. If missing, port only that generic boolean/config merge seam from the historical private-harness patch; do not restore `.jcode/AGENTS.md` or `.jcode/harness/*.md` loading.
3. Read the flag from gitignored `<trusted-root>/.jcode/config.local.toml` and skip only `<trusted-root>/AGENTS.md`.
4. Keep global `~/AGENTS.md`, global `.jcode/prompt-overlay.md`, model settings, and unrelated configuration unchanged.
5. Add prompt accounting/doctor evidence showing whether project AGENTS suppression is active without exposing prompt contents.

### Phase 2 — Trusted-root local transport configuration

1. Extend `lazy jcode trust/install` to TOML-parse and idempotently merge only `[prompt] ignore_project_agents = true` into `.jcode/config.local.toml` for the selected canonical root.
2. Preserve all unrelated user-owned TOML, create a backup before changing an existing file, and make remove/untrust delete only the managed key or managed empty section.
3. Keep the local file gitignored/private and never write grammar, records, trust policy, or model routing into it.
4. Verify existing swarm, ambient, overnight, remote, and headless child paths retain the parent working directory; fix only a proven missing inheritance path.

### Phase 3 — Lazy-harness adapter integration

1. Make `before_model` read/inject the canonical trusted root's `.lazy-harness/AGENTS.md` plus the current bounded re-grounding body on initial and post-tool requests.
2. Keep all grammar, records, trust registry, and lifecycle policy in `.lazy-harness`; `.jcode/config.local.toml` remains transport-only.
3. Add fixtures for trusted project-AGENTS suppression, canonical grammar injection, child working-directory inheritance, global-overlay preservation, untrusted silent no-op, and reversible config removal.
4. Update SDD/TDD/SSOT records only for independently proven semantic deltas.

### Phase 4 — Candidate build and promotion

1. Replay the ordered patch series with the modernized existing custom-stack helper onto the selected official upstream revision.
2. Run Jcode formatting, focused crate tests, checks, guardrails, and a source build.
3. Run lazy-harness focused adapter tests and one final `lazy validate --plan standard` after the last mutation.
4. Install to a versioned candidate path and run live trusted-root, ordinary-root, spawned-agent, ask, re-grounding, and follow-up smoke tests.
5. Switch only the lazy-patched channel pointer after all required evidence passes. Keep official stable/current rollback paths untouched.

## Stop conditions

Stop and request a revised decision if:

- implementation requires semantic prompt-conflict classification inside Jcode,
- the source-control patch suppresses global personal overlays or ordinary-project AGENTS,
- local config merge cannot preserve unrelated user TOML and reverse only managed state,
- root identity cannot remain isolated across server sessions,
- spawned-agent inheritance requires a breaking protocol change without compatibility,
- the upstream rebase conflicts with unrelated user-owned work,
- validation cannot distinguish official and patched build provenance,
- a new user constraint changes this confirmed scope.

## Execution evidence

### 2026-08-02 — Phases 0–3 implementation

- Jcode source commit `15e87544c` adds the narrow `[prompt] ignore_project_agents` control, working-directory `.jcode/config.local.toml` prompt-only merge, project `AGENTS.md` suppression, prompt accounting, and full/split prompt tests.
- Jcode maintenance commit `3f06d761a` restores `LAZYDINO_MAINTENANCE.md` and `scripts/lazydino/reapply-custom-stack.sh` from the existing `custom/lazydino-harness` provenance source.
- Jcode focused prompt/config tests, formatting, targeted check, clippy, and source build passed. The broad fast guardrail reported three unchanged repository-wide ratchet failures in pre-existing files; candidate promotion remains pending integrated evidence.
- Lazy-harness adds reversible trusted-root `.jcode/config.local.toml` management, private Git exclusion/backups, exact transaction rollback, doctor fields, and canonical `.lazy-harness/AGENTS.md` request-scoped injection.
- `check_jcode_agent_adapter` passes with trusted/untrusted roots, user-TOML preservation, remove/untrust reversal, failed install/untrust rollback, no trust creation from `remove --target`, exact 24,000-byte grammar bounds, failed dynamic-hook suppression, initial/post-tool injection, and root/session isolation.
- Independent GPT-5.6 Sol review found four release blockers; all four received focused fixes and regression fixtures. Final independent re-verification and Phase 4 candidate promotion are pending.

## Validation matrix

| Case | Expected result |
|---|---|
| trusted lazy root, main agent | project AGENTS skipped; canonical lazy grammar injected |
| trusted lazy root, spawned agent | inherited working dir applies the same behavior |
| ordinary/untrusted root | project AGENTS loads normally; adapter remains silent |
| global personal overlay | preserved in every root |
| untrusted or ordinary project | lazy-harness adapter remains silent |
| upstream candidate update | patch series applies and all gates pass before promotion |
| rollback | official and prior patched binary remain selectable |

## Implementation map

- Status: source execution approved by user option A on 2026-08-02; Phase 1/2/3 implementation and candidate validation in progress.
- Jcode repository: `/home/lazydino/dev/jcode` is the mapped implementation target already recorded by the lifecycle parity plan.
- Existing patches: `38036ca63`, `eaa12fc30`, `6597ac650`, `dcc8ed100`.
- Lazy-harness integration: `.lazy-harness/scripts/jcode-adapter.ts`, `.lazy-harness/scripts/jcode-package.ts`, `.lazy-harness/scripts/jcode-trust.ts`, `.lazy-harness/spec/platform/jcode-agent-adapter.md`, `.lazy-harness/tests/jcode-agent-adapter.md`.
- Existing maintenance assets to modernize: `custom/lazydino-harness`, `LAZYDINO_MAINTENANCE.md`, `scripts/lazydino/reapply-custom-stack.sh`, and the custom install helper.
- Protection: Jcode prompt/config/agent tests and guardrails plus lazy-harness focused fixtures and final standard validation.

## Rule placement

- Rule: execute the accepted patched-channel architecture through bounded, independently reversible phases.
- Scope: transient-plan.
- Primary record: `.lazy-harness/planning/jcode-lazy-patched-channel-plan.md`.
- Confirmation: corrected explicit-source requirements and source execution option A confirmed 2026-08-02.

## Discovery capture

- DDD: no independent delta.
- SDD: update after Phase 1/2 prove the source-control and local transport-config contracts.
- BDD: update only if diagnostics create a new visible interaction flow.
- TDD: required for source suppression, injection, inheritance, preservation, provenance, and rollback cases.
- ADR: `.lazy-harness/decisions/0057-jcode-lazy-patched-channel.md` is the canonical architecture decision.
- SSOT: independent enforcement transport delta recorded in `.lazy-harness/ssot/harness-enforcement-policy.md`.
