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
  - use `lazy policy upsert --from-json ... --confirm` for canonical policy write round-trips
  - keep `lazy policy resolve` advisory-only by default for `discover`, `recommend`, and `default` levels
  - keep warn runtime explicit-context and warn-only
  - require explicit confirmation and tests before `block` runtime enforcement
- Must not:
  - add new canonical policy semantics only to `.lazy-harness/rules/**`
  - treat LLM-generated explanation text as canonical truth
  - edit `.lazy-harness/generated/policy-rulebook.md` as policy source
  - write policy changes without explicit confirmation
  - auto-promote policies to warn/block from a registry entry alone
  - classify raw user or assistant text to trigger warn runtime
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

## Warn-only runtime

Warn runtime is a separate explicit-context mode:

- `lazy policy resolve --runtime warn` may surface warn-level policies as `warn-only`.
- `check-policy-warn-runtime.py` may emit a response.completed `WARN` only when payload contains structured `policy_context` / `policyContext` with `stage` and/or `appliesTo`.
- `acknowledgedPolicyWarnings` suppresses already-accepted warning ids.
- Warn output is not a block and cannot prevent work from continuing.
- Block output remains unimplemented.

## Relationship to capabilities

Capabilities bind policies to commands/actions/tools. Policies define behavior semantics. A capability can reference policy ids through `policyIds`, `sourceRecord`, or migration compatibility fields.

## Relationship to rulebook markdown

`.lazy-harness/rules/**` is a compatibility/generated/explain surface during Option B migration. It may remain for readability and host compatibility, but new semantic policy changes should land in `policies.json`.

## Generated policy rulebook view

The deterministic generated view is:

```text
.lazy-harness/generated/policy-rulebook.md
```

Regenerate with:

```bash
.lazy-harness/bin/lazy policy render-rulebook --write
```

The generated view is useful for human/LLM explanation, review, and compatibility, but it is non-canonical. If it disagrees with `policies.json`, regenerate it or fix `policies.json`.

## Policy writes

Canonical policy writes should go through:

```bash
.lazy-harness/bin/lazy policy upsert --from-json <policy.json> --confirm
```

Without `--confirm`, `upsert` is a dry-run and must not mutate `policies.json`.

The write path must validate the complete next registry, persist id-sorted policies, and be followed by audit/resolve/render validation before rulebook retire/deprecation work.

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
  - `.lazy-harness/hooks/lifecycle/helpers/check-policy-warn-runtime.py`
  - `.lazy-harness/generated/policy-rulebook.md`
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/self-test.py`
- Validation:
  - `lazy policy audit --format=json`
  - `lazy policy list --format=json`
  - `lazy policy resolve --stage turn --applies-to making_validation_claims --format=json`
  - `lazy policy resolve --runtime warn --stage turn --applies-to making_validation_claims --format=json`
  - `lazy policy render-rulebook --write --format=json`
  - `lazy policy upsert --from-json <policy.json> --confirm --format=json`
  - `lazy policy explain --id record-first-validation --format=md`

## Rule placement

- Rule: project/team behavior policy canonical source is typed policy registry.
- Scope: framework-global
- Primary record: `.lazy-harness/ssot/policy-registry.md`
- Why not AGENTS.md: AGENTS grammar can point to policy registry but should not carry policy storage truth.
- Why not `.jcode`: shared policy source must sync across hosts; `.jcode` is local/private.
- Confirmation: user-confirmed
