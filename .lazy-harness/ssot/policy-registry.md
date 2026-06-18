# SSOT — Policy Registry

Status: active
Layer: SSOT
Date: 2026-06-18
Related ADR: `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
Related SDD: `.lazy-harness/spec/platform/policy-machinery-v2.md`
Related TDD: `.lazy-harness/tests/policy-machinery-v2.md`
Schema: `.lazy-harness/schemas/policies.schema.json`
Registry: `.lazy-harness/ssot/policies.json`

## Rule digest

- Status: active SSOT
- Scope: framework-global
- Applies when:
  - adding or changing project/team behavior policy
  - linking policy semantics to capability bindings
  - generating/explaining rulebook views
- Must:
  - treat `.lazy-harness/ssot/policies.json` as the canonical typed policy registry
  - keep policy `stage` and `level` explicit
  - keep policy evidence root-relative and source-record backed
  - keep generated/explain views derived and non-canonical
  - keep `lazy policy resolve` advisory-only for `discover`, `recommend`, and `default` levels
  - require explicit confirmation and tests before `warn`/`block` runtime enforcement
- Must not:
  - add new canonical policy semantics only to `.lazy-harness/rules/**`
  - treat LLM-generated explanation text as canonical truth
  - auto-promote policies to warn/block from a registry entry alone
- Record completion:
  - update ADR/SDD/TDD/schema/self-test/manifest together when registry shape changes.

## Canonical registry

The canonical typed policy registry is:

```text
.lazy-harness/ssot/policies.json
```

The registry stores behavior policies, not general project facts. General facts still belong in DDD/SDD/BDD/ADR/SSOT records and Project Map entries.

## Required fields

Each policy requires:

- `id`
- `title`
- `scope`
- `stage`
- `level`
- `appliesTo`
- `sourceRecord`
- `evidence`
- `promotion.requiresConfirmation`
- `rollback.criteria`
- `updateLoop.canonicalByPacketAlone = false`

## Advisory resolver

`lazy policy resolve` is the first runtime-facing registry reader. It is still read-only and advisory-only:

- `discover`, `recommend`, and `default` may be surfaced as guidance.
- `warn` and `block` are not enforced or emitted as runtime decisions by this slice.
- Resolver output is derived from `policies.json` and is not canonical truth by itself.

## Relationship to capabilities

Capabilities bind policies to commands/actions/tools. Policies define behavior semantics. A capability can reference policy ids through `policyIds`, `sourceRecord`, or migration compatibility fields.

## Relationship to rulebook markdown

`.lazy-harness/rules/**` is a compatibility/generated/explain surface during Option B migration. It may remain for readability and host compatibility, but new semantic policy changes should land in `policies.json`.

## Implementation map

- Status: `option-b-selected-first-slice`
- Records:
  - `.lazy-harness/ssot/policy-registry.md`
  - `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - `.lazy-harness/tests/policy-machinery-v2.md`
- Source files:
  - `.lazy-harness/ssot/policies.json`
  - `.lazy-harness/schemas/policies.schema.json`
  - `.lazy-harness/scripts/policy.ts`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/self-test.py`
- Validation:
  - `lazy policy audit --format=json`
  - `lazy policy list --format=json`
  - `lazy policy resolve --stage turn --applies-to making_validation_claims --format=json`
  - `lazy policy explain --id record-first-validation --format=md`

## Rule placement

- Rule: project/team behavior policy canonical source is typed policy registry.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/policy-registry.md`
- Why not AGENTS.md: AGENTS grammar can point to policy registry but should not carry policy storage truth.
- Why not `.jcode`: shared policy source must sync across hosts; `.jcode` is local/private.
- Confirmation: user-confirmed
