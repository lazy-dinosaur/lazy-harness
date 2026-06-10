# Project Operating Rulebook

Status: accepted
Layer: SDD
Date: 2026-06-10
Related ADR: `.lazy-harness/decisions/0044-project-operating-rulebook.md`
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related TDD: `.lazy-harness/tests/project-operating-rulebook.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - adding project/team development operating policy
  - deciding whether information is a project fact or an agent behavior rule
  - resolving canonical commands, discouraged commands, validation workflows, or bypass rules
- Must:
  - store human-readable operating rules under `.lazy-harness/rules/**`
  - link machine-readable action surfaces through `.lazy-harness/ssot/capabilities.json`
  - keep default/warn/block behavior explicit and bypass-aware
  - keep `.jcode/**` pointer/local-only
- Must not:
  - store shared project/team operating rules only in `.jcode` or Jcode memory
  - treat factual records alone as sufficient to change agent behavior
  - promote a rule to hard-stop only because it exists
- Record completion:
  - changes to rulebook sections, CLI behavior, capability fields, or audit criteria update this SDD, SSOT, ADR, and TDD together

## Contract

`lazy rules` provides a rulebook-oriented view over:

```text
.lazy-harness/rules/**/*.md
.lazy-harness/ssot/capabilities.json
```

Commands:

```bash
lazy rules list [--format=json|md]
lazy rules audit [--format=json|md] [--strict]
lazy rules resolve --intent <intent> [--format=json|md]
lazy rules resolve --action <command-or-action> [--format=json|md]
```

## Rulebook entry shape

Each active entry should include:

- top-level metadata:
  - `Status: active|draft|retired`
  - `Layer: Rulebook`
  - `Scope: framework-global|host-project|team-policy|jcode-local`
  - `Level: discover|recommend|default|warn|block`
  - `Related capability: <id>` when a capability binding exists
- `## Rule digest`
- `## Operating rule`
- `## Examples`
- `## Capability binding`
- `## Implementation map`

`default|warn|block` entries must link to a capability unless explicitly draft/retired. `warn|block` entries must document bypass behavior.

## Capability binding

Capability entries may use these optional fields:

- `rulebookRecord`: canonical `.lazy-harness/rules/**` path
- `preferredActions`: canonical commands/actions to use
- `discouragedActions`: commands/actions that should resolve to guidance
- `requiresReasonForBypass`: boolean marker for bypass-aware default/warn/block rules

Resolution must match exact intent labels and action labels using the same deterministic matching boundary as `lazy capability resolve`.

## Audit behavior

`lazy rules audit --strict` fails when:

- active rulebook metadata is missing or invalid
- `## Rule digest` is missing
- default/warn/block active rules have no related capability
- linked capability ids are absent
- linked capability source/rulebook records are missing
- a rule with Avoid entries has no linked `discouragedActions`
- a warn/block rule has no bypass note

Non-strict audit reports the same issues but only exits non-zero for errors.

## Implementation map

- Status: `phase-0-2-implemented`
- Source files:
  - `.lazy-harness/scripts/rulebook.ts`
  - `.lazy-harness/scripts/capability.ts`
  - `.lazy-harness/schemas/capabilities.schema.json`
  - `.lazy-harness/bin/lazy`
- Records:
  - `.lazy-harness/rules/README.md`
  - `.lazy-harness/ssot/capability-registry.md`
  - `.lazy-harness/spec/platform/capability-resolution.md`
- Tests:
  - `.lazy-harness/tests/project-operating-rulebook.md`
  - `.lazy-harness/scripts/self-test.py`
