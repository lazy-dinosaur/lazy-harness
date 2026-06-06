# Planning — Record-index parser/cache migration plan

Status: needs-option-gate
Date: 2026-06-06
Layer: Planning
Related task: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md#scr-402--record-index-parsercache-implementation`
Related ADR: `.lazy-harness/decisions/0042-record-index-cache-naming.md`
Related SDD: `.lazy-harness/spec/platform/record-index-header.md`
Related TDD: `.lazy-harness/tests/record-index-header.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Applies when:
  - starting SCR-402 record-index parser/cache implementation
  - deciding how to migrate existing `context-index` source/CLI/schema/generated cache references
  - deciding whether compatibility aliases are allowed without reintroducing context-helper architecture
- Must:
  - keep `record-index` as canonical future name
  - keep scope limited to deterministic record-authored metadata listing/cache generation
  - preserve no raw-user-message query input
  - preserve no semantic authority outputs
  - preserve cache/header-hit-not-evidence behavior
  - require tests before code migration
  - ask an option gate before changing compatibility behavior for existing `context-index`
- Must not:
  - implement parser/cache code before the compatibility option is selected
  - reintroduce `context-*` as canonical naming
  - make `context-index` visible as a primary feature if retained only for compatibility
- Record completion:
  - user choice updates this plan, SCR-402 task status, SDD/TDD fixtures, SSOT/ADR if needed, and implementation map.

## Current implementation inventory

Existing active implementation still uses `context-index` names:

- CLI command: `.lazy-harness/bin/lazy` exposes `context-index [--write] [--format=json|md]`.
- Source: `.lazy-harness/scripts/context-index.ts`.
- Schema: `.lazy-harness/schemas/context-index.schema.json`.
- Generated cache: `.lazy-harness/generated/context-index.json` when written.
- Self-test: `.lazy-harness/scripts/self-test.py` protects the current `context-index` generator.
- Project feature map and manifest records refer to record/source indexing, but still reference the current source file while migration has not happened.

This is allowed only as current-state evidence. ADR 0042 says future canonical naming is `record-index`.

## Direction constraints

Every option below must satisfy:

1. No raw user-message query input.
2. No requiredRead/confidence/intent/risk/gate/nextAction/candidateMeanings output fields.
3. Cache/listing output is non-canonical.
4. Cache/listing hit does not satisfy search/read debt.
5. LLM/searcher still reads real records/source/tests before relying on facts.
6. `record-index` is canonical in new docs/contracts.

## Compatibility options

### A — Replace with record-index only

- Rename command/source/schema/generated cache to `record-index` / `record-index.ts` / `record-index.schema.json` / `record-index.json`.
- Remove active `context-index` command and generated cache path.
- Update all self-tests and docs to canonical `record-index` only.

Pros:

- Cleanest directionally.
- Eliminates context-name contamination.
- Simplest future mental model.

Cons:

- Highest compatibility risk for hosts/scripts that may call `lazy context-index` or expect `context-index.json`.
- Requires sync validation across hosts after migration.

### B — Canonical record-index plus hidden deprecated context-index alias

- Add canonical `record-index` command/source/schema/generated cache.
- Keep `lazy context-index` as a hidden/deprecated alias for one migration cycle.
- Do not advertise `context-index` as primary help/docs.
- Self-test proves alias is deprecated, no raw-message query, same deterministic output semantics.

Pros:

- Lower compatibility risk than A.
- Still keeps canonical docs on `record-index`.
- Lets downstream hosts migrate gradually.

Cons:

- Leaves a `context-index` executable path temporarily.
- Requires stricter tests to prevent alias from becoming canonical again.

### C — Canonical record-index plus visible deprecated alias

- Similar to B, but help output shows `context-index` as deprecated.

Pros:

- Clearer for users with old command muscle memory.

Cons:

- More visible context-name contamination.
- Higher chance future agents keep using old name.

### D — Defer SCR-402 and do SCR-501 record-audit warnings first

- Do not touch parser/cache implementation yet.
- Implement advisory warnings for missing Index Header metadata first.

Pros:

- Avoids compatibility decision now.
- Improves record quality before cache migration.

Cons:

- Leaves existing `context-index` naming in place longer.
- Delays canonical `record-index` migration.

### E — Custom

User specifies a different migration policy.

## Recommended option

Recommended: **A if the priority is maximum directional cleanliness**, because the user explicitly warned that direction-opposing changes must not remain.

Pragmatic alternative: **B** if host compatibility is more important than removing the old command immediately.

Because this choice changes executable compatibility behavior, this plan stops at option gate before code mutation.

## Proposed SCR-402 test mapping after option selection

Common tests for all options:

- `check_record_index_command_no_raw_message_query`
- `check_record_index_output_has_no_semantic_authority_fields`
- `check_record_index_cache_hit_not_evidence`
- `check_record_index_complete_header_fixture`
- `check_record_index_legacy_rule_digest_fallback`
- `check_record_index_generated_cache_noncanonical`

Option-specific tests:

- Option A:
  - `check_context_index_command_absent_after_record_index_migration`
  - `check_context_index_generated_cache_absent_or_pruned`
- Option B:
  - `check_context_index_hidden_deprecated_alias`
  - `check_context_index_alias_does_not_appear_as_canonical_help`
- Option C:
  - `check_context_index_visible_deprecation_notice`
- Option D:
  - no parser/cache tests; record-audit tests move first.

## Implementation phases after option selection

1. Update task status from blocked/needs-option-gate to in-progress.
2. Update SDD/TDD to selected compatibility policy.
3. Add executable self-test fixtures first.
4. Migrate CLI/source/schema/generated docs.
5. Validate no raw-message query and no semantic-authority outputs.
6. Run self-test, prompt-budget, graph-hygiene.
7. Sync/dogfood selected hosts if command compatibility changed.

## Implementation map

- Status: `needs-option-gate`
- Primary files to be considered after option selection:
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/context-index.ts` or future `.lazy-harness/scripts/record-index.ts`
  - `.lazy-harness/schemas/context-index.schema.json` or future `.lazy-harness/schemas/record-index.schema.json`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/generated/README.md`
  - `.lazy-harness/spec/platform/record-index-header.md`
  - `.lazy-harness/tests/record-index-header.md`
- No code is changed by this plan.
- Machine index:
  - graph ids: `kg_record_index_scr402_option_gate`, `kg_record_index_migration_plan`

## Layer completeness impact

- DDD: no new term required; existing searchable record memory terms apply.
- BDD: no new behavior required yet; existing LLM-owned retrieval scenarios apply.
- SDD: candidate update after option choice to selected compatibility policy.
- TDD: candidate update after option choice to option-specific self-test fixtures.
- ADR: ADR 0042 already decides canonical name; a new ADR is not needed unless user chooses an option that changes ADR 0042.
- SSOT: candidate update after option choice if compatibility alias policy needs to be recorded.
- Planning: this plan records the option gate.

## Discovery capture

- DDD: none, existing record sufficient.
- BDD: none, existing record sufficient.
- SDD: candidate update after option choice.
- TDD: candidate update after option choice.
- ADR: none unless option conflicts with ADR 0042.
- SSOT: candidate update after option choice.
- Planning: updated by this plan.
