# Capability Resolution

Status: accepted
Layer: SDD
Related SSOT: `.lazy-harness/ssot/capability-registry.md`
Related ADR: `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`
Related TDD: `.lazy-harness/tests/capability-registry.md`

## Contract

Capability resolution and registration answer:

```text
Given an intent/action, which registered capabilities are relevant, and how strongly should the agent consider them?
```

The resolver must not convert a soft capability into a hard block. Enforcement level remains explicit.

## Registration

`lazy capability add` creates or updates `.lazy-harness/ssot/capabilities.json` deterministically.

Phase 2 requirements:

- Required fields must be supplied.
- `sourceRecord` must exist unless `--allow-missing-source-record` is passed.
- Repeating the same add command must be idempotent and return `unchanged`.
- Registry output must be sorted by id for stable diffs.
- A knowledge graph capability row must be upserted for non-dry-run writes.

## Inputs

- `--intent <intent>`: semantic workflow label such as `validating_changes` or `creating_pull_request`.
- `--action <action>`: concrete tool/command/action label such as `gh pr create`.
- Optional `--format=json|md`.

At least one of `--intent` or `--action` is required for resolve.

## Matching

A capability matches when:

- `intent` exactly equals one of `appliesWhen`, or
- `action` exactly equals one of `actions`, or
- `action` contains an action string with word-ish boundaries for simple CLI labels.

Phase 1 intentionally avoids complex semantic matching.

## Sorting

Output order:

1. `block`
2. `warn`
3. `default`
4. `recommend`
5. `discover`

Within the same level, preserve registry order.

## Audit

`lazy capability audit` must report:

- registry JSON parse failure
- missing/invalid required fields
- unsupported kind or level
- duplicate ids
- missing source records
- warn/block entries that do not declare an enforcement surface

Phase 1 audit is report-only and does not install hooks.

## Implementation map

- Status: `phase-2-implemented`
- Primary files:
  - `.lazy-harness/scripts/capability.ts` — add/list/resolve/audit implementation.
  - `.lazy-harness/ssot/capabilities.json` — registry input.
  - `.lazy-harness/scripts/self-test.py` — fixture coverage.
- Key symbols:
  - `upsertCapability`
  - `resolveCapabilities`
  - `auditRegistry`
  - `printMarkdown`
- Tests / protection:
  - `check_capability_registry_cli_phase1` in `.lazy-harness/scripts/self-test.py`, covering add/list/resolve/audit.
