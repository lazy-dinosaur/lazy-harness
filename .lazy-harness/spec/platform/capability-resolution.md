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
- Multi-value options may be passed comma-separated or as repeated flags; repeated `--applies-when`, `--action`, and `--tag` values must accumulate.

## Candidate detection

`lazy capability candidates` is read-only. It inspects host-local evidence and returns candidate capability entries that are not yet registered or are partially registered.

Candidate detection must not mutate `.lazy-harness/ssot/capabilities.json` and must not promote candidates to `warn` or `block` automatically.

Current evidence detectors:

- package-script validation: if `package.json` exposes baseline validation scripts such as `lint`, `typecheck`, `test:run`, or `test:unit`, but no registered capability covers `validating_app_changes` with those actions, emit a `validation/recommend` candidate.
- release action coverage: if a release workflow capability resolves by intent but lacks concrete release action labels and `.lazy-harness/ssot/release-branch-policy.md` exists, emit a partial candidate with the suggested action coverage.

## Inputs

- `--intent <intent>`: semantic workflow label such as `validating_changes` or `creating_pull_request`.
- `--action <action>`: concrete tool/command/action label such as `gh pr create`.
- Optional `--format=json|md`.

At least one of `--intent` or `--action` is required for resolve.

## Matching

A capability matches when:

- `intent` exactly equals one of `appliesWhen`, or
- `action` exactly equals one of `actions`, `preferredActions`, or `discouragedActions`, or
- `action` contains one of those action strings for simple CLI labels.

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
- missing `rulebookRecord` files when provided
- malformed `preferredActions`, `discouragedActions`, or `requiresReasonForBypass` fields

Phase 1 audit is report-only and does not install hooks.

## Implementation map

- Status: `phase-2-implemented`
- Primary files:
  - `.lazy-harness/scripts/capability.ts` — add/list/resolve/candidates/audit implementation.
  - `.lazy-harness/ssot/capabilities.json` — registry input.
  - `.lazy-harness/scripts/self-test.py` — fixture coverage.
- Key symbols:
  - `upsertCapability`
  - `resolveCapabilities`
  - `capabilityActionLabels`
  - `auditRegistry`
  - `capabilityCandidates`
  - `printCandidates`
- Tests / protection:
  - `check_capability_registry_cli_phase1` in `.lazy-harness/scripts/self-test.py`, covering add/list/resolve/candidates/audit and repeated multi-value flags.
