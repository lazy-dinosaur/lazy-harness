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
  - keep human-readable operating rulebook markdown under `.lazy-harness/rules/**` as a compatibility/explain surface
  - store canonical behavior policy semantics under `.lazy-harness/ssot/policies.json`
  - link machine-readable action surfaces through `.lazy-harness/ssot/capabilities.json`
  - keep default/warn/block behavior explicit and bypass-aware
  - keep Pi/OMP local notes (`.pi/`/`.omp/`) pointer/local-only
- Must not:
  - store shared project/team operating rules only in Pi/OMP local notes
  - treat factual records alone as sufficient to change agent behavior
  - promote a rule to hard-stop only because it exists
- Record completion:
  - changes to rulebook sections, CLI behavior, capability fields, or audit criteria update this SDD, SSOT, ADR, and TDD together

## Contract

`lazy rules` provides a compatibility/explain view over:

```text
.lazy-harness/rules/**/*.md              # compatibility/explain surface
.lazy-harness/ssot/capabilities.json     # action/capability bindings
.lazy-harness/ssot/policies.json         # canonical behavior policy semantics
```

`lazy rules` output must identify this boundary with `schemaVersion = rulebook-compatibility/v1`, `retiredCanonicalSemantics = true`, and `canonicalPolicySource = .lazy-harness/ssot/policies.json`.

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
  - `Scope: framework-global|host-project|team-policy|local-only`
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

- `rulebookRecord`: compatibility/explain `.lazy-harness/rules/**` path
- `policyIds`: canonical typed policy ids from `.lazy-harness/ssot/policies.json` that cover the rulebook compatibility surface
- `preferredActions`: canonical commands/actions to use
- `discouragedActions`: commands/actions that should resolve to guidance
- `requiresReasonForBypass`: boolean marker for bypass-aware default/warn/block rules

Resolution must match exact intent labels and action labels using the same deterministic matching boundary as `lazy capability resolve`.

During Policy Machinery Option B migration, active rulebook entries that are candidates for semantic retirement must also be covered by typed policy links. The framework source entry `.lazy-harness/rules/README.md` is covered by capability `project-operating-rulebook` and policy `project-operating-rulebook-policy`. Semantic authority is retired from `.lazy-harness/rules/**`; typed policies are the source of truth.

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
- Semantic-retirement status: `rules-compatibility-surface-policy-canonical`
- Source files:
  - `.lazy-harness/scripts/rulebook.ts`
  - `.lazy-harness/scripts/capability.ts`
  - `.lazy-harness/scripts/lazy-sync.ts`
  - `.lazy-harness/manifests/init-categories.json`
  - `.lazy-harness/schemas/capabilities.schema.json`
  - `.lazy-harness/ssot/policies.json`
  - `.lazy-harness/bin/lazy`
- Records:
  - `.lazy-harness/rules/README.md`
  - `.lazy-harness/ssot/capability-registry.md`
  - `.lazy-harness/ssot/policy-registry.md`
  - `.lazy-harness/spec/platform/capability-resolution.md`
- Tests:
  - `.lazy-harness/tests/project-operating-rulebook.md`
  - `.lazy-harness/tests/policy-machinery-v2.md`
  - `.lazy-harness/scripts/self-test.py`

## Response audit missed-action advisory

Rulebook-backed capabilities can participate in advisory-only response audit. When a capability is `warn` or `block` and declares `discouragedActions`, `response.completed` can detect matching recent tool evidence. If no prior `lazy rules resolve` / `lazy capability resolve` evidence exists for the same action/capability, the helper emits an advisory that points to preferred actions and source/rulebook records.

This is not a hard block. Hard stops still require Guidance Ladder promotion.
