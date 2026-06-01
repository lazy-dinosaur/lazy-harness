# Capability Registry Implementation Plan

Status: proposed
Date: 2026-05-26
Confirmation: user-confirmed direction, implementation pending approval
Related records:

- `.lazy-harness/ssot/rule-lifecycle.md`
- `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
- `.lazy-harness/decisions/0039-rule-lifecycle-bindings.md`
- `.lazy-harness/planning/dogfood-auto-recording-status-report.md`

## Problem

Lazy-harness can now turn some stored rules into enforced action-boundary checks. Dogfooding showed a broader need:

```text
When a host/project adds a workflow rule or project-specific tool, agents need a structured way to discover, prefer, invoke, warn about, or block around that capability at the right moment.
```

This should not mean every recorded project rule becomes a hard hook. Many project-specific rules are better modeled as capabilities with different levels of strength.

Examples:

- Worktree bootstrap script for a project.
- Required or preferred lint/test command.
- Project-specific Jcode skill.
- Prompt template for PR/release/review bodies.
- Hook guard for high-risk mutation.
- Validation checklist.
- MCP/tool adapter.
- Audit-only reminder.

## Core design principle

Capability kind and enforcement level are independent.

```text
kind = what the thing is
level = how strongly lazy-harness should steer or enforce it
```

### Capability kinds

Initial supported kinds:

- `script`
- `skill`
- `prompt`
- `hook`
- `command`
- `tool-adapter`
- `validation`
- `checklist`
- `audit`

### Capability levels

Initial supported levels:

- `discover` — make it visible in lookup/audit only.
- `recommend` — suggest it when intent matches.
- `default` — use it by default, but allow reasoned bypass.
- `warn` — warn when bypassed.
- `block` — deny unsafe/noncompliant action unless the capability is used or the body/command satisfies the binding.

Default policy:

- New capabilities should default to `discover` or `recommend` unless explicitly confirmed otherwise.
- `block` must require a user/team-confirmed hard policy or high-risk mutation boundary.
- `default` should be preferred over `block` for workflow convenience scripts.

## Proposed files

### Canonical records

- `.lazy-harness/ssot/capability-registry.md`
  - Human-readable policy and lifecycle.
  - Defines kind/level semantics and when escalation is allowed.
- `.lazy-harness/ssot/capabilities.json`
  - Canonical machine-readable host/framework capability registry.
  - Host-specific capability entries live here in installed hosts.
- `.lazy-harness/spec/platform/capability-resolution.md`
  - Resolver contract: input intent/action, output matching capabilities sorted by level/specificity.
- `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`
  - ADR for capability registry over forcing everything into hooks/rules.
- `.lazy-harness/tests/capability-registry.md`
  - Regression expectations.

### Implementation files

- `.lazy-harness/scripts/capability.ts`
  - CLI: `lazy capability list|add|resolve|audit`.
- `.lazy-harness/hooks/lifecycle/helpers/check-capability-boundary.py`
  - Optional helper for `warn`/`block` boundaries.
  - Should reuse or compose with `check-rule-action-boundary.py` rather than duplicate PR-specific logic.
- `.lazy-harness/scripts/self-test.py`
  - Fixture coverage for registry parse, resolver, add/list/audit, and hook behavior.
- `.lazy-harness/bin/lazy`
  - Dispatch `lazy capability ...`.
- `.lazy-harness/manifests/init-categories.json`
  - Sync new scripts/helpers/specs/SSOT to hosts.
- `.lazy-harness/scripts/jcode-wiring.ts`
  - Only if default generated wiring needs to expose capability helper or wrapper skill.

### Generated/cache files

- `.lazy-harness/generated/capability-index.json`
  - Derived lookup cache if needed.
  - Not canonical.

## Data model draft

```json
{
  "version": 1,
  "capabilities": [
    {
      "id": "project-lint",
      "kind": "command",
      "level": "default",
      "sourceRecord": ".lazy-harness/ssot/test-strategy.xml",
      "appliesWhen": ["validating_changes", "before_commit"],
      "entrypoint": "bun lint",
      "description": "Preferred project lint command",
      "owner": "host-project",
      "fallback": "Use another lint command only with reason",
      "tags": ["validation", "lint"]
    }
  ]
}
```

Required fields:

- `id`
- `kind`
- `level`
- `sourceRecord`
- `appliesWhen`
- `description`
- `owner`

Kind-specific optional fields:

- `entrypoint` for `script`, `command`, `validation`, `hook`.
- `skillName` for `skill`.
- `templatePath` or `template` for `prompt`.
- `tool` / `adapter` for `tool-adapter`.
- `checklistPath` for `checklist`.
- `auditCommand` for `audit`.
- `fallback` for `default`, `warn`, `block` levels.

## Resolver behavior

Input examples:

- `intent=starting_pr_work`
- `intent=validating_changes`
- `action=gh pr create`
- `action=git commit`
- `action=release_dispatch`

Output should group matches:

1. `block`
2. `warn`
3. `default`
4. `recommend`
5. `discover`

The resolver should never silently convert `recommend` into `block`.

## CLI proposal

### `lazy capability list`

Shows registered capabilities grouped by kind/level.

### `lazy capability resolve --intent <intent>`

Prints matching capabilities in markdown or JSON.

### `lazy capability add`

Creates or updates a capability entry. It should be non-interactive-first for agents but support option-gate style prompts later.

Example:

```bash
lazy capability add \
  --id project-lint \
  --kind command \
  --level default \
  --applies-when validating_changes \
  --entrypoint 'bun lint' \
  --source-record .lazy-harness/ssot/test-strategy.xml \
  --description 'Preferred project lint command'
```

### `lazy capability audit`

Reports:

- invalid JSON/schema
- missing source records
- unsupported kind/level
- `warn`/`block` capabilities with no enforcement surface
- likely duplicate capabilities
- capabilities with missing tests when level is `warn` or `block`

## Phased implementation

### Phase 1 — Registry and resolver, no new blocking

Goal: make capabilities discoverable and queryable without increasing enforcement.

Work:

1. Add SSOT/SDD/ADR/TDD records.
2. Add `capabilities.json` schema expectations.
3. Implement `lazy capability list|resolve|audit`.
4. Add self-tests.

Validation:

- `python3 .lazy-harness/scripts/self-test.py`
- `python3 .lazy-harness/scripts/doctor.py --profile smoke`

### Phase 2 — Add capability creation helper

Goal: make registering capabilities easy and consistent.

Work:

1. Implement `lazy capability add`.
2. Ensure it updates `.lazy-harness/ssot/capabilities.json` deterministically.
3. Require `sourceRecord` to exist unless `--allow-missing-source-record` is passed.
4. Append knowledge graph entries.
5. Add fixtures for script, skill, prompt, validation entries.

Validation:

- Self-test fixture for idempotent add/update.
- JSONL/JSON validity checks.

### Phase 3 — Gentle agent integration

Goal: use capability lookup as memory/routing, not force.

Work:

1. Add resolver guidance to AGENTS/lifecycle only for lookup moments.
2. Optionally add a generated Jcode wrapper skill `/lazy-capability`.
3. Add response.completed audit that detects when a high-confidence `default`/`recommend` capability was ignored, but only reports, not blocks.

Validation:

- Self-test fixture verifies no hard block for `discover/recommend/default`.

### Phase 4 — Organic hybrid capability guidance candidate

Goal: explore whether capabilities can support C+ v2 organic hybrid guidance without becoming one-off tool adapters.

User-confirmed on 2026-06-01:

- Do not solve PR/runtime/release/DB policy recall by attaching custom logic to `bash`, `gh`, `dev-cli`, GitHub MCP, or similar individual tool surfaces.
- Do not make broad edit/write/multiedit blocking the primary solution if it slows normal flow.
- Compare organic/free alternatives before implementation.

Candidate work, not yet approved for implementation:

1. Use capabilities as one possible input to ambient rule context ranking.
2. Map capability levels to a graduated guidance ladder: ambient, nudge, warn, ask, hard stop.
3. Keep tool hooks as generic carriers only if needed; do not encode policy in tool-specific branches.
4. Migrate any existing PR/runtime exemplar into the chosen framework-level model only after the ADR/design comparison selects an architecture.

Validation:

- `recommend/default` bypass allowed.
- `warn` emits warning.
- `block` denies.

### Phase 5 — Dogfood host examples

Goal: prove the model on real hosts.

Potential examples:

- Medivance PR body prompt/default/block capability.
- Medivance validation command capability.
- Worktree start script capability if host policy confirms it.
- Release checklist capability.

Validation:

- Sync to Medivance.
- Run host lazy test.
- Manually resolve sample intents.

## Non-goals for first pass

- Do not auto-create hooks for every capability.
- Do not auto-promote project scripts to `block`.
- Do not replace existing skills.
- Do not require every record to have a capability entry.
- Do not implement cross-host capability marketplace/discovery.

## Open questions / option gate needed

1. Should canonical machine-readable registry be `.lazy-harness/ssot/capabilities.json` or `.lazy-harness/knowledge/capabilities.jsonl`?
   - Recommended: SSOT JSON for canonical registry, JSONL only for logs/history.
2. Should PR body guard migrate into capability registry immediately or stay as Rule Lifecycle exemplar until Phase 4?
   - Recommended: keep current guard stable, cross-reference it, migrate later.
3. Should `lazy capability add` be in Phase 1 or Phase 2?
   - Recommended: Phase 2, after schema/resolver stabilizes.

## Rule placement

- Rule: Capability Registry implementation should separate capability kind from enforcement level, start with discover/resolve/audit behavior, and reserve warn/block hooks for explicit high-risk or user/team-confirmed hard policies.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/capability-registry-implementation-plan.md`
- Why not AGENTS.md: this is an implementation plan pending user approval and later SDD/ADR promotion.
- Why not `.jcode`: this is shared lazy-harness framework architecture, not local/private Jcode-only workflow.
- Confirmation: user-confirmed direction, implementation pending approval

## Discovery capture

- SDD: candidate `.lazy-harness/spec/platform/capability-resolution.md`.
- SSOT: candidate `.lazy-harness/ssot/capability-registry.md` and `.lazy-harness/ssot/capabilities.json`.
- ADR: candidate `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`.
- TDD: candidate `.lazy-harness/tests/capability-registry.md`.
- Planning: this file is the active proposal.

## 2026-05-26 note — adjacent backlog captured separately

During Phase 1 approval, the user identified three adjacent framework needs that should not block Capability Registry Phase 1:

1. Parallel initial harness record search.
2. Work transparency / resumable progress logging.
3. Parallel-safe record writes.

These are captured in `.lazy-harness/planning/harness-throughput-and-transparency-backlog.md`.

## 2026-05-26 Phase 1 implementation status

Status: implemented-pending-full-validation
Confirmation: user-approved Phase 1 implementation.

Implemented:

- `.lazy-harness/ssot/capability-registry.md`
- `.lazy-harness/ssot/capabilities.json`
- `.lazy-harness/spec/platform/capability-resolution.md`
- `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`
- `.lazy-harness/tests/capability-registry.md`
- `.lazy-harness/schemas/capabilities.schema.json`
- `.lazy-harness/scripts/capability.ts`
- `.lazy-harness/bin/lazy` dispatch for `lazy capability`
- `.lazy-harness/scripts/self-test.py` Phase 1 fixture

Focused validation passed:

- `lazy capability audit --format=json`
- `lazy capability list --format=json`
- `lazy capability resolve --intent finding_project_capabilities --format=json`
- focused `check_capability_registry_cli_phase1`

Phase 1 intentionally adds no new blocking hooks.

## 2026-05-26 Phase 1 dogfood validation

Status: validated
Confirmation: validation evidence

Validation completed:

- Source:
  - `.lazy-harness/scripts/self-test.py` passed, including `capability registry Phase 1 CLI ok`.
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke` passed with ADR count 40 / 0001~0040 fresh.
- Medivance dogfood host:
  - `lazy-sync --force` from source completed.
  - `.lazy-harness/bin/lazy test` passed in host scope.
  - `.lazy-harness/bin/lazy capability audit --format=json` returned `ok: true` with `count: 0`, confirming empty host-owned capability registries are valid.
  - `.lazy-harness/bin/lazy capability list --format=md` returned `No capabilities registered.`

Dogfood fix made during validation:

- The first self-test version assumed every host has the framework seed capability. That was wrong because `capabilities.json` is host-owned. The fixture now allows empty host registries and tests seed list/resolve behavior inside an isolated temp host.

## Rule placement

- Rule: Capability Registry Phase 1 is implemented and validated as non-blocking list/resolve/audit; empty host-owned registries are valid.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/capability-registry-implementation-plan.md`
- Why not AGENTS.md: this is implementation status and validation evidence, not a universal agent rule.
- Why not `.jcode`: this is shared framework capability infrastructure, not local/private Jcode-only workflow.
- Confirmation: validation evidence

## 2026-05-26 Phase 2 implementation and Medivance dogfood

Status: implemented-and-dogfooded
Confirmation: validation evidence

Implemented Phase 2:

- `lazy capability add`
- deterministic id-sorted upsert into `.lazy-harness/ssot/capabilities.json`
- required source record validation by default
- `--allow-missing-source-record` for drafts
- `--dry-run`
- idempotent repeated adds returning `unchanged`
- graph row upsert for non-dry-run capability registration
- fixtures for `script`, `skill`, `prompt`, and `validation` capability kinds

Source validation passed:

- `.lazy-harness/scripts/self-test.py`
- `python3 .lazy-harness/scripts/doctor.py --profile smoke`

Medivance dogfood:

- Synced framework source to `/home/lazydino/dev/medivance` sequentially before host validation.
- Registered three real host capabilities:
  - `medivance-pr-body-template` (`prompt`, `default`, applies to `creating_pull_request`, `writing_pr_body`)
  - `medivance-release-workflow-skill` (`skill`, `recommend`, applies to `preparing_release`, `release_dispatch`)
  - `medivance-lazy-test-validation` (`validation`, `default`, applies to `validating_changes`, `before_commit`)
- `lazy capability audit --format=json` returned `ok: true`, `count: 3`.
- `lazy capability resolve --intent creating_pull_request --format=json` returns `medivance-pr-body-template`.
- `lazy capability resolve --intent validating_changes --format=json` returns `medivance-lazy-test-validation`.
- Registry and graph capability ids had no duplicates.
- Medivance `.lazy-harness/bin/lazy test` passed in host scope.

Important parallel track reminder:

The previous harness strengthening Phase 3 that must not be forgotten is lifecycle/response.completed production hook replacement, not Capability Registry Phase 3:

- Current lifecycle status: Phase 2 shadow orchestrator/parity runner exists.
- Production `response.completed` hook still uses the legacy helper loop.
- Phase 3 production hook replacement remains blocked until readiness work, more real payload evidence, graph/open-gate cleanup, and explicit opt-in checklist.
- Canonical records: `.lazy-harness/planning/dogfood-auto-recording-status-report.md` and `.lazy-harness/planning/performance-optimization-plan.md`.

## Rule placement

- Rule: Capability Registry Phase 2 is implemented and dogfooded; the separate lifecycle production-hook replacement Phase 3 remains blocked and must be tracked as an independent roadmap item.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/capability-registry-implementation-plan.md`
- Why not AGENTS.md: this is implementation/dogfood status and roadmap reminder, not universal agent grammar.
- Why not `.jcode`: this is shared framework architecture and dogfood status, not local/private Jcode-only preference.
- Confirmation: validation evidence plus user reminder

## 2026-05-26 requirement — automatic capability candidate accumulation

Status: user-confirmed requirement
Confirmation: user-confirmed

Requirement:

```text
Capability knowledge should accumulate automatically as the user builds/uses a project. The system should log candidate capabilities and evidence during normal work. Later, when the user asks the agent to check the project, the agent should judge the accumulated evidence and promote/adjust capabilities as appropriate.
```

Corrected interpretation:

- The long-term goal is automatic capability confirmation/promotion, not a permanently manual candidate-only system.
- The framework should automatically accumulate evidence, infer likely capabilities, and eventually write/update canonical `.lazy-harness/ssot/capabilities.json` when confidence and safety criteria are met.
- Dogfooding is the calibration loop: the agent inspects the accumulated evidence, checks false positives/false negatives, tunes thresholds/rules, and records what should become automatic.
- Until the auto-confirmation policy is proven, candidates/evidence logs are the safe staging layer, but they are a stepping stone toward automatic canonical updates.

Proposed follow-up design:

1. Add a capability candidate log, e.g. `.lazy-harness/knowledge/capability-candidates.jsonl`.
2. Capture candidate evidence from:
   - repeated validation commands
   - repeated project scripts used by agents
   - skills invoked in project-specific contexts
   - PR/release/test workflow records already read by agents
   - hook/action telemetry with safe metadata only
3. Add `lazy capability candidates --format=md|json` to summarize candidate entries.
4. Add `lazy capability promote <candidate-id>` or extend `lazy capability add --from-candidate <id>`.
5. Add agent workflow: when the user asks “프로젝트 상태/하네스 확인해줘”, run capability audit/candidate summary and decide what to promote.

Safety / noise policy:

- Automatic accumulation is evidence-only, not enforcement.
- Candidate entries must avoid raw sensitive payloads.
- Promotion to `default`, `warn`, or `block` still requires source record and confirmation/strong evidence.
- `block` remains explicit hard-policy only.

## Rule placement

- Rule: Capability Registry should automatically accumulate capability candidates/evidence during normal project use, while canonical capabilities remain curated and promoted after agent review/user confirmation.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/capability-registry-implementation-plan.md`
- Why not AGENTS.md: this is a new implementation requirement for future Capability Registry phases, not current universal agent behavior yet.
- Why not `.jcode`: this is shared lazy-harness framework behavior, not local/private Jcode-only workflow.
- Confirmation: user-confirmed

## Discovery capture

- SDD: candidate capability candidate accumulation and promotion contract.
- TDD: candidate tests for evidence-only accumulation, no auto-enforcement, and promotion workflow.
- SSOT: possible candidate log storage SSOT.
- ADR: possible decision on automatic candidate accumulation vs direct canonical writes.
- Planning: captured here as next Capability Registry direction.


## 2026-05-26 correction — automatic confirmation is the target

Status: user-corrected requirement
Confirmation: user-confirmed correction

Correction:

```text
Capability accumulation should not stop at candidate logging. The target is automatic confirmation/promotion into canonical capabilities, with dogfooding used to verify and tune that automatic behavior.
```

Implication for implementation:

1. Start with evidence/candidate logging for observability.
2. Add confidence scoring and source-record checks.
3. Allow low-risk capabilities to auto-promote once criteria are met.
4. Keep higher-risk `default`/`warn`/`block` promotions behind stronger evidence or confirmation until dogfood proves safety.
5. When the user asks for a project check, the agent should review auto-promotions, missed candidates, and false positives, then tune the policy.

## Rule placement

- Rule: Capability Registry's target state is automatic capability confirmation/promotion, with dogfooding used to calibrate and tune the auto-confirmation policy.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/capability-registry-implementation-plan.md`
- Why not AGENTS.md: this is a corrected implementation requirement and roadmap item, not current universal behavior yet.
- Why not `.jcode`: this is shared lazy-harness framework behavior, not local/private Jcode-only workflow.
- Confirmation: user-confirmed correction

## 2026-05-26 dogfood window — user will use normally before evaluation

Status: active-dogfood-window
Confirmation: user-confirmed

Plan:

- User will use Medivance / Medivance PWA normally for roughly 1-2 days.
- The agent should later evaluate Capability Registry dogfooding rather than asking the user to manually register capabilities.
- Evaluation should inspect actual usage evidence, capability registry state, logs, graph/candidate records, and false positive / false negative patterns.

Future evaluation checklist:

1. Sync lazy-harness source to dogfood hosts if source advanced.
2. Run host `lazy capability audit --format=json`.
3. Run representative `lazy capability resolve` queries:
   - `creating_pull_request`
   - `validating_changes`
   - `validating_app_changes`
   - `preparing_release`
   - `release_dispatch`
4. Compare registered capabilities against recent real commands/skills/workflows.
5. Identify missing capabilities that should have auto-promoted.
6. Identify incorrect/noisy capabilities that should not auto-promote.
7. Tune the automatic evidence/candidate/auto-confirmation plan accordingly.
8. Keep lifecycle/response.completed Phase 3 production replacement as a separate blocked roadmap item.

## Rule placement

- Rule: Capability Registry dogfooding enters a 1-2 day real-use window; after that, the agent should evaluate evidence and tune automatic confirmation/promotion behavior.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/capability-registry-implementation-plan.md`
- Why not AGENTS.md: this is a time-bound dogfood/evaluation plan, not a permanent agent instruction.
- Why not `.jcode`: this is shared lazy-harness framework dogfood planning, not local/private Jcode-only workflow.
- Confirmation: user-confirmed

## 2026-05-31 Medivance-primary capability evaluation

Status: evaluated-next-registry-updates-identified
Confirmation: user asked to proceed with the parallel Track A Capability Registry evaluation after Track B Medivance-primary readiness.

Scope:

```text
Use `/home/lazydino/dev/medivance` as primary evidence.
Use `/home/lazydino/dev/medivance-pwa` only as secondary/contextual evidence because PWA development is not currently active.
```

Commands run in Medivance:

- `lazy capability audit --format=json`
- `lazy capability list --format=json`
- `lazy capability resolve --intent creating_pull_request --format=json`
- `lazy capability resolve --intent validating_changes --format=json`
- `lazy capability resolve --intent validating_app_changes --format=json`
- `lazy capability resolve --intent preparing_release --format=json`
- `lazy capability resolve --intent release_dispatch --format=json`
- Concrete action resolves:
  - `gh pr create`
  - `gh pr edit`
  - `.lazy-harness/bin/lazy test`
  - `bun run lint`
  - `bun run typecheck`
  - `bun run test:run`
  - `bun release main`
  - `bun release test`

Observed Medivance registry state:

- `lazy capability audit`: `ok=true`, `count=3`, `issues=[]`.
- Registered capabilities:
  - `medivance-lazy-test-validation` — `validation/default`, applies to `validating_changes`, `before_commit`.
  - `medivance-pr-body-template` — `prompt/default`, applies to `creating_pull_request`, `writing_pr_body`; actions `gh pr create`, `gh pr edit`.
  - `medivance-release-workflow-skill` — `skill/recommend`, applies to `preparing_release`, `release_dispatch`.
- Representative intent results:
  - `creating_pull_request`: matched `medivance-pr-body-template`.
  - `validating_changes`: matched `medivance-lazy-test-validation`.
  - `validating_app_changes`: no matches.
  - `preparing_release`: matched `medivance-release-workflow-skill`.
  - `release_dispatch`: matched `medivance-release-workflow-skill`.
- Concrete action results:
  - `gh pr create`: matched `medivance-pr-body-template`.
  - `gh pr edit`: matched `medivance-pr-body-template`.
  - `.lazy-harness/bin/lazy test`: matched `medivance-lazy-test-validation`.
  - `bun run lint`: no matches.
  - `bun run typecheck`: no matches.
  - `bun run test:run`: no matches.
  - `bun release main`: no matches.
  - `bun release test`: no matches.

Secondary PWA context:

- PWA audit passed: `ok=true`, `count=2`, `issues=[]`.
- PWA has `medivance-pwa-baseline-validation` for `validating_app_changes`, covering lint/typecheck/unit test commands.
- This confirms that a baseline app-validation capability shape is already useful in a dogfood host, but PWA thinness should not block Medivance decisions.

Evaluation:

- False positives: none found. Existing matches resolve to the expected PR, validation, and release capabilities.
- Missing auto-promotion / registry gap 1:
  - Medivance has canonical app validation commands in `.lazy-harness/tests/test-strategy.xml` and `package.json`: `bun run lint`, `bun run typecheck`, `bun run test:run`.
  - `validating_app_changes` currently resolves to no capability.
  - Concrete lint/typecheck/test actions also resolve to no capability.
  - Recommended registry addition: `medivance-baseline-app-validation` as `validation/recommend`, not `block`, applying to `validating_app_changes,before_commit` with actions `bun run lint,bun run typecheck,bun run test:run`.
- Missing action coverage / registry gap 2:
  - `medivance-release-workflow-skill` resolves by intent but not by concrete `bun release ...` actions.
  - Recommended registry update: add actions `bun release,bun release test,bun release staging,bun release main` while keeping level `recommend`.
- CLI ergonomics observation:
  - `lazy capability add` help documents comma-separated multi-values. Repeating `--applies-when`, `--action`, or `--tag` currently keeps the last value only via the generic option parser.
  - This is not a correctness bug when callers follow the documented comma-separated syntax, but supporting repeated flags would reduce agent mistakes in future hardening.

Dry-run candidates verified:

```bash
lazy capability add \
  --id medivance-baseline-app-validation \
  --kind validation \
  --level recommend \
  --applies-when validating_app_changes,before_commit \
  --action 'bun run lint,bun run typecheck,bun run test:run' \
  --entrypoint 'bun run lint && bun run typecheck && bun run test:run' \
  --source-record .lazy-harness/tests/test-strategy.xml \
  --description 'Use Medivance baseline lint, typecheck, and Vitest validation for app changes.' \
  --owner host-project \
  --tag validation,vitest,medivance
```

```bash
lazy capability add \
  --id medivance-release-workflow-skill \
  --kind skill \
  --level recommend \
  --applies-when preparing_release,release_dispatch \
  --action 'bun release,bun release test,bun release staging,bun release main' \
  --source-record .lazy-harness/ssot/release-branch-policy.md \
  --description 'Use the project release workflow skill for Medivance release/build/publish/hotfix work.' \
  --owner host-project \
  --tag release,skill \
  --skill-name /release-workflow
```

Go/no-go conclusion:

```text
Capability Registry Track A is functioning correctly for existing Medivance entries.
The next safe implementation step is source-side harness improvement: detect these gaps as read-only capability candidates from dogfood evidence, not manual downstream host registry edits.
Do not promote either gap directly to warn/block, and do not commit direct Medivance registry changes unless explicitly requested.
```

## Rule placement

- Rule: Capability Registry evaluation should keep existing soft levels and convert Medivance-discovered gaps into lazy-harness source improvements such as read-only candidate detection; avoid manual downstream host registry edits and avoid warn/block promotion from this evidence alone.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/capability-registry-implementation-plan.md`
- Why not AGENTS.md: this is a point-in-time Capability Registry dogfood evaluation and next registry-update recommendation, not permanent agent grammar.
- Why not `.jcode`: this concerns shared lazy-harness framework dogfood and host capability registry state, not local/private Jcode-only workflow.
- Confirmation: validation evidence plus user-approved Track A evaluation.

## Discovery capture

- DDD: no new domain term.
- SDD: source-side candidate detection and repeated `lazy capability add` flag ergonomics are the correct follow-up contract changes.
- BDD: no user-facing app behavior change.
- TDD: add source self-test cases for read-only candidate detection and repeated multi-value flags.
- ADR: no new architecture decision; levels remain soft (`recommend/default`) unless separately confirmed.
- SSOT: `/home/lazydino/dev/medivance/.lazy-harness/ssot/capabilities.json` remains downstream evidence only; source work belongs in `/home/lazydino/dev/lazy-harness`.
- Planning: this section is the current Track A evaluation checkpoint.

## 2026-05-31 correction — source-side implementation, not downstream registry patch

Status: user-corrected-and-implemented
Confirmation: user-corrected

Correction:

```text
Medivance capability gaps should drive lazy-harness framework changes in the source repo. They should not be solved by manually committing registry edits in the Medivance downstream host.
```

Source changes made:

- Added read-only `lazy capability candidates --format=json|md`.
- Candidate detection now finds:
  - missing app-validation capabilities from package scripts such as lint/typecheck/test.
  - release capabilities that resolve by intent but are missing concrete release action labels.
- Added repeated multi-value flag support for `lazy capability add`, so repeated `--applies-when`, `--action`, and `--tag` accumulate instead of silently keeping only the last value.
- Added self-test coverage for both candidate detection and repeated flag preservation.

Medivance verification target:

```bash
bun .lazy-harness/scripts/capability.ts candidates --target /home/lazydino/dev/medivance --format=json
```

Expected current Medivance candidates from source script:

- `medivance-baseline-app-validation`
- `medivance-release-workflow-skill-action-coverage`

These are read-only suggestions. They are not downstream commits.

## 2026-05-31 downstream sync after source-side candidate detection

Status: synced-and-validated
Confirmation: user asked whether both downstream dogfood hosts were updated after harness source changes.

Source commit synced:

- Initial implementation commit: `878a92c8099d59fcb468f673c5e44cfa406bf540` (`Add read-only capability candidate detection`)

Downstream sync results:

- `/home/lazydino/dev/medivance`
  - `lazy-sync --force`: updated 7 framework files and marker.
  - marker reached `878a92c8099d59fcb468f673c5e44cfa406bf540`.
  - `lazy test`: pass, host scope ran=40 skipped=16.
  - `lazy capability candidates --format=json`: pass, candidates:
    - `medivance-baseline-app-validation`
    - `medivance-release-workflow-skill-action-coverage`
  - `git status --short`: clean.
- `/home/lazydino/dev/medivance-pwa`
  - `lazy-sync --force`: updated 7 framework files and marker.
  - marker reached `878a92c8099d59fcb468f673c5e44cfa406bf540`.
  - `lazy test`: pass, host scope ran=40 skipped=16.
  - `lazy capability candidates --format=json`: pass, candidates:
    - `medivance-pwa-baseline-app-validation`
  - `git status --short`: clean.

Interpretation:

```text
Both downstream dogfood hosts were updated to the source-side candidate detection implementation and validated.
Medivance remains the primary dogfood signal; PWA remains secondary/contextual but is no longer stale relative to the synced framework implementation.
```

Next source-side note:

This record commit itself advances the source HEAD beyond `878a92c`; after committing it, downstream markers should be refreshed once more so host markers equal the final source HEAD.
