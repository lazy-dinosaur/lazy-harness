# Planning — Record-index parser/cache migration plan

Status: accepted — Option A selected and implemented
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
  - understanding the completed SCR-402 Option A migration from old cache names to canonical `record-index`
  - deciding whether any future compatibility alias proposal would violate the record-index-only outcome
- Must:
  - keep `record-index` as canonical future name
  - keep scope limited to deterministic record-authored metadata listing/cache generation
  - preserve no raw-user-message query input
  - preserve no semantic authority outputs
  - preserve cache/header-hit-not-evidence behavior
  - keep executable self-test coverage for record-index generation and old command absence
  - follow the user-selected Option A policy: remove active `context-index` command/source/schema/generated cache path
- Must not:
  - reintroduce `context-*` as canonical naming
  - make `context-index` visible as a primary or compatibility command without a new option gate and tests
- Record completion:
  - SCR-402 Option A completion keeps this plan, task status, SDD/TDD fixtures, SSOT/ADR, generated docs, and graph rows aligned.

## Completed implementation inventory

SCR-402 Option A replaced the old cache/listing surface with canonical `record-index` only:

- CLI command: `.lazy-harness/bin/lazy` exposes `record-index [--write] [--format=json|md]`.
- Source: `.lazy-harness/scripts/record-index.ts`.
- Schema: `.lazy-harness/schemas/record-index.schema.json`.
- Generated cache: `.lazy-harness/generated/record-index.json` when written.
- Self-test: `.lazy-harness/scripts/self-test.py#check_record_index_generator_phase3` protects generation, determinism, output shape, old command absence, and no old source/schema files.
- Project feature map, generated docs, manifest records, and graph rows now refer to record-index paths.
- Lazy sync prunes old managed `.lazy-harness/scripts/context-index.ts`, `.lazy-harness/schemas/context-index.schema.json`, and `.lazy-harness/generated/context-index.json` paths from downstream hosts.

Historical references to `context-index` are allowed only in ADR/plan history or absence/regression tests.

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

User selected Option A. SCR-402 implementation removes active `context-index` executable/cache paths and keeps only canonical `record-index`.

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

## Implementation phases for selected Option A

1. Update task status from blocked/needs-option-gate to in-progress/done.
2. Update SDD/TDD to Option A no-alias policy.
3. Add executable self-test checks for record-index command and context-index absence.
4. Migrate CLI/source/schema/generated docs to record-index.
5. Validate no raw-message query and no semantic-authority outputs.
6. Run self-test, prompt-budget, graph-hygiene.
7. Sync/dogfood selected hosts because command compatibility changed.

## Implementation map

- Status: `implemented; Option A selected`
- Primary files changed/covered by Option A:
  - `.lazy-harness/bin/lazy`
  - `.lazy-harness/scripts/record-index.ts`
  - `.lazy-harness/schemas/record-index.schema.json`
  - `.lazy-harness/scripts/self-test.py`
  - `.lazy-harness/generated/README.md`
  - `.lazy-harness/spec/platform/record-index-header.md`
  - `.lazy-harness/tests/record-index-header.md`
- Code migration completed by SCR-402 Option A; no compatibility alias remains.
- Machine index:
  - graph ids: `kg_record_index_scr402_option_a_selected`, `kg_record_index_migration_plan`

## Layer completeness impact

- DDD: no new term required; existing searchable record memory terms apply.
- BDD: no new behavior required yet; existing LLM-owned retrieval scenarios apply.
- SDD: updated to Option A record-index-only policy.
- TDD: updated to Option A context-index-absent fixtures.
- ADR: ADR 0042 already decides canonical name; a new ADR is not needed unless user chooses an option that changes ADR 0042.
- SSOT: updated to record-index-only policy.
- Planning: this plan records the selected option and completed migration.

## Discovery capture

- DDD: none, existing record sufficient.
- BDD: none, existing record sufficient.
- SDD: updated by `.lazy-harness/spec/platform/record-index-header.md`.
- TDD: updated by `.lazy-harness/tests/record-index-header.md` and executable self-test coverage.
- ADR: none unless option conflicts with ADR 0042.
- SSOT: updated by `.lazy-harness/ssot/cli-tool-boundary.md`.
- Planning: updated by this plan and SCR-402 task status.
