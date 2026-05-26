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

### Phase 4 — Boundary helper for warn/block only

Goal: extend Rule Lifecycle enforcement for explicit high-risk capabilities.

Work:

1. Add `check-capability-boundary.py` or fold capability support into existing `check-rule-action-boundary.py`.
2. Only `warn` and `block` levels produce hook output.
3. Existing PR body guard can be represented as a `block` capability or remain as rule-binding exemplar with cross-reference.

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
