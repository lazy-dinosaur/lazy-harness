# SDD — Context Tier Manifest

Status: accepted
Date: 2026-06-06
Layer: SDD
Related plan: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`
Related SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
Related SDD: `.lazy-harness/spec/platform/project-profile.md`
Related SSOT: `.lazy-harness/ssot/project-navigation.md`
Related schema: `.lazy-harness/schemas/context-tier-manifest.schema.json`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - defining or auditing optional context-tier hints for Context Delivery or Project Profile retrieval
  - adding `.lazy-harness/project/context-tiers.yaml` or a host equivalent
  - grouping records/source files into always, phase, task, or optional context buckets
- Must:
  - treat context tiers as advisory pointer hints, not canonical truth
  - require every entry path to point at an existing current-host file when a manifest is present
  - keep the default `message.received` hook static and unchanged by context tier manifests
  - read canonical records/source after a tier points at them; tier membership alone is not sufficient evidence
  - keep source checkout manifests under `.lazy-harness/project/` host/source-owned, not Category A framework truth for downstream product maps
- Must not:
  - let a context tier manifest bypass `.lazy-harness` record reads
  - use context tiers as a raw user-message classifier or semantic authority
  - store raw user messages, transcript chunks, or assistant responses in tier entries
  - fail normal runtime when the optional manifest is absent
- Record completion:
  - changes to tier keys, entry kinds, required fields, pointer-audit semantics, or runtime consumers update this SDD, schema, and self-test coverage
- Related records:
  - `.lazy-harness/spec/platform/context-delivery-contract.md`
  - `.lazy-harness/spec/platform/project-profile.md`
  - `.lazy-harness/ssot/project-navigation.md`
  - `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`
- Implementation hints:
  - Files: `.lazy-harness/schemas/context-tier-manifest.schema.json`, `.lazy-harness/project/context-tiers.yaml`, `.lazy-harness/fixtures/context-delivery/context-tier-manifest.sample.json`, `.lazy-harness/scripts/self-test.py`
  - Tests: `.lazy-harness/scripts/self-test.py`

## Contract

A Context Tier Manifest is an optional project/source-local map of context pointers. It answers:

```text
Which compact records/files are generally useful for a class of work before a full Context Delivery Packet or direct search narrows the task?
```

It is deliberately weaker than `feature-navigation.xml`:

- `feature-navigation.xml` maps user-facing surfaces to records, source, and tests.
- `context-tiers.yaml` groups already-known pointers by retrieval posture: always, phase, task, optional.

## Tier keys

The stable tier keys are:

| Tier | Meaning | Expected use |
| --- | --- | --- |
| `always` | Tiny context that is broadly useful for the project/source checkout. | Manual read checklist, future optional context tools. |
| `phase` | Context for an active roadmap/phase/workstream. | Plan execution and validation scopes. |
| `task` | Context for a narrower feature/task family. | Focused implementation or debugging. |
| `optional` | Helpful background, never required by tier membership alone. | Discovery, reviewer hints, or later packet candidates. |

## Entry kinds

Allowed entry `kind` values:

- `record`
- `plan`
- `project-profile`
- `source-file`
- `test`
- `schema`
- `fixture`
- `graph`

## Manifest shape

The logical schema is defined in `.lazy-harness/schemas/context-tier-manifest.schema.json` and shown as JSON in `.lazy-harness/fixtures/context-delivery/context-tier-manifest.sample.json`.

The sample fixture is synced to downstream hosts and is validated by BOTH-scope self-test. Therefore sample `path` values must reference framework-synced/common files, not source-checkout-only records such as `.lazy-harness/ssot/project-navigation.md`.

Source checkouts may store the same logical data as restricted YAML at `.lazy-harness/project/context-tiers.yaml` so it remains human-editable. The Phase 4 pointer audit intentionally supports a conservative YAML subset: it extracts `path:` scalar lines and verifies the referenced files exist. More complex YAML must wait for an explicit parser dependency and updated SDD/TDD.

## Runtime behavior

Phase 4 is Option A from the prompt runtime compression plan:

- documentation + schema + pointer audit only,
- no context-index ingestion,
- no `message.received` behavior change,
- absence of `.lazy-harness/project/context-tiers.yaml` is valid.

Future phases may ingest the manifest into `context-index.source.canonicalInputs` or derived metadata, but only after dogfooding and an explicit SDD/schema update.

## Pointer audit

When a source/host manifest is present, audit checks should:

1. parse the JSON sample fixture against the schema's expected stable keys,
2. verify sample fixture paths resolve in both framework source and synced downstream hosts,
3. extract all `path:` scalar values from `.lazy-harness/project/context-tiers.yaml`,
4. fail if any path is absolute, escapes the host root, or does not exist,
5. fail if tier keys outside `always`, `phase`, `task`, `optional` are introduced,
6. fail if raw message/transcript/response fields are introduced.

The audit is a validation guard. It does not mean every tier path is required-read for every turn.

## Implementation map

- Status: `phase-4-implemented`
- Primary files:
  - `.lazy-harness/spec/platform/context-tier-manifest.md` — this SDD contract.
  - `.lazy-harness/schemas/context-tier-manifest.schema.json` — JSON Schema for the logical manifest model and sample fixture.
  - `.lazy-harness/fixtures/context-delivery/context-tier-manifest.sample.json` — schema/sample fixture used by self-test.
  - `.lazy-harness/project/context-tiers.yaml` — advisory source-checkout manifest in restricted YAML subset.
  - `.lazy-harness/scripts/self-test.py` — validates schema/sample invariants and pointer existence.
  - `.lazy-harness/manifests/init-categories.json` — syncs the SDD and fixture/schema framework assets while keeping project manifests host-owned.
  - `.lazy-harness/knowledge/graph.jsonl` — records implementation/protection links.
- Key symbols:
  - `check_context_tier_manifest_phase4` (`self-test.py`) — checks schema/sample/source manifest pointers and no raw transcript fields.
- Flow:
  1. Author keeps context tier entries as pointers to existing files.
  2. Self-test validates the sample logical model and source YAML pointers.
  3. Agents may use the manifest as a manual hint after reading the SDD, but canonical truth remains in pointed records/source.
  4. Runtime hooks ignore the manifest by default.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 -m py_compile .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy doctor --profile=smoke`
- Cross-layer links:
  - Planning: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`
  - SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
  - SDD: `.lazy-harness/spec/platform/project-profile.md`
  - SSOT: `.lazy-harness/ssot/project-navigation.md`
- Machine index:
  - graph ids: `kg_context_tier_manifest_sdd_defines_contract`, `kg_context_tier_manifest_schema_specifies_shape`, `kg_context_tier_manifest_protected_by_self_test`

## Discovery capture

- DDD: none.
- SDD: this record defines optional context-tier manifest semantics.
- BDD: no user-visible behavior change.
- TDD: self-test gains schema/sample/pointer audit coverage.
- ADR: no new decision; implements Phase 4 Option A from the approved compression plan.
- SSOT: no source-of-truth change; `.lazy-harness/project/context-tiers.yaml` is advisory and source/host-owned.
- Planning: Phase 4 of `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`.
