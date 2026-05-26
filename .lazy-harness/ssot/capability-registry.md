# Capability Registry

Status: accepted
Layer: SSOT
Date: 2026-05-26
Related SDD: `.lazy-harness/spec/platform/capability-resolution.md`
Related ADR: `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md`
Related TDD: `.lazy-harness/tests/capability-registry.md`

## Purpose

The Capability Registry records project/framework affordances that agents should discover, recommend, prefer, warn about, or enforce at the right moment.

A capability is not only a script. It can be a script, skill, prompt/template, hook, command, tool adapter, validation command, checklist, or audit reminder.

## Principle

Capability kind and enforcement level are independent.

```text
kind = what the thing is
level = how strongly lazy-harness steers or enforces it
```

## Capability kinds

Supported initial kinds:

- `script`
- `skill`
- `prompt`
- `hook`
- `command`
- `tool-adapter`
- `validation`
- `checklist`
- `audit`

## Capability levels

Supported initial levels:

- `discover` — visible in lookup/audit only.
- `recommend` — suggested when intent matches.
- `default` — used as the default path, but bypassable with reason.
- `warn` — bypass emits warning.
- `block` — action is denied unless the capability is used or the action satisfies its binding.

New capabilities should default to `discover` or `recommend` unless the user/team confirms a stronger level. `block` is reserved for explicit high-risk mutation boundaries or confirmed hard policy.

## Canonical registry

The canonical machine-readable registry is `.lazy-harness/ssot/capabilities.json`.

Generated indexes may live under `.lazy-harness/generated/**`, but generated files are derived cache only.

## Required fields

Each capability entry requires:

- `id`
- `kind`
- `level`
- `sourceRecord`
- `appliesWhen`
- `description`
- `owner`

`sourceRecord` must point at a canonical `.lazy-harness` record unless the capability is still a draft.

## Phase 1/2 behavior

Phase 1/2 remains intentionally non-blocking:

- `lazy capability add`
- `lazy capability list`
- `lazy capability resolve --intent <intent>`
- `lazy capability audit`

No hook is added by Phase 1/2. Warn/block boundary enforcement is a later phase.

## Implementation map

- Status: `phase-2-implemented`
- Primary files:
  - `.lazy-harness/ssot/capability-registry.md` — this policy.
  - `.lazy-harness/ssot/capabilities.json` — canonical registry.
  - `.lazy-harness/spec/platform/capability-resolution.md` — resolver contract.
  - `.lazy-harness/decisions/0040-capability-registry-kind-level-separation.md` — ADR.
  - `.lazy-harness/tests/capability-registry.md` — regression record.
  - `.lazy-harness/scripts/capability.ts` — CLI implementation for add/list/resolve/audit.
  - `.lazy-harness/bin/lazy` — dispatches `lazy capability`.
  - `.lazy-harness/scripts/self-test.py` — fixtures.
- Key symbols:
  - `loadRegistry` (`capability.ts`) — reads canonical registry.
  - `saveRegistry` (`capability.ts`) — writes deterministic id-sorted registry updates.
  - `upsertCapability` (`capability.ts`) — creates or updates capability entries idempotently.
  - `auditRegistry` (`capability.ts`) — validates schema/source records.
  - `resolveCapabilities` (`capability.ts`) — finds intent/action matches and sorts by level.
  - `check_capability_registry_cli_phase1` (`self-test.py`) — protects Phase 1/2 CLI behavior.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
