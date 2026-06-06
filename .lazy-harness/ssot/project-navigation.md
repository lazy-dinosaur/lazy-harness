# SSOT — Source project navigation map

Status: accepted
Layer: SSOT
Date: 2026-06-06
Related plan: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`
Related SDD: `.lazy-harness/spec/platform/project-profile.md`
Related SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
Related SSOT: `.lazy-harness/ssot/project-identity.md`

## Rule digest

- Status: active
- Layer: SSOT
- Scope: framework-source
- Applies when:
  - working in the lazy-harness source checkout and needing a compact project feature map
  - generating or inspecting `record-index.json` projectProfile metadata
  - changing source-level feature navigation, aliases, records, source paths, tests, or risk notes
- Must:
  - treat `.lazy-harness/project/feature-navigation.xml` as the canonical source-checkout feature navigation map
  - keep generated `record-index.json` optional and derived, never canonical
  - keep downstream host feature-navigation maps host-owned and do not sync this source map as downstream product truth
  - link each high-altitude source feature to records, source files, tests, and risk notes
- Must not:
  - use source feature aliases as hook-time semantic classification inside `message.received`
  - overwrite downstream host `.lazy-harness/project/feature-navigation.xml` without explicit host confirmation
  - store raw transcripts or raw user messages in the feature-navigation map
- Related records:
  - `.lazy-harness/spec/platform/project-profile.md`
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - `.lazy-harness/spec/platform/prompt-budget.md`
  - `.lazy-harness/ssot/project-identity.md`
- Implementation hints:
  - Files: `.lazy-harness/project/feature-navigation.xml`, `.lazy-harness/scripts/record-index.ts`, `.lazy-harness/scripts/self-test.py`
  - Tests: `.lazy-harness/scripts/self-test.py`

## Source of truth

`.lazy-harness/project/feature-navigation.xml` is the durable feature-navigation map for this lazy-harness source checkout.

It exists to let agents and direct LLM/searcher retrieval start from a compact source-project map instead of repeatedly dumping broad layer inventories. The map is not a generated cache. It is a canonical host/project record for this checkout.

Generated outputs such as `.lazy-harness/generated/record-index.json` are rebuildable caches derived from:

1. layer record `## Rule digest` sections,
2. layer record `## Implementation map` sections,
3. `.lazy-harness/project/feature-navigation.xml`,
4. `.lazy-harness/knowledge/graph.jsonl`,
5. referenced source files and tests.

## Source-checkout feature ids

The current high-altitude source features are:

- `prompt-runtime-lifecycle`
- `capability-registry`
- `context-delivery-indexing`
- `record-decision-broker`
- `implementation-map-graph-hygiene`
- `lifecycle-compare-parity`
- `sync-install-update`
- `test-doctor`

These ids are intentionally broad. They are retrieval/navigation anchors, not fine-grained task tickets.

## Ownership boundaries

- Owner/upstream: `/home/lazydino/dev/lazy-harness`
- Canonical source map: `.lazy-harness/project/feature-navigation.xml`
- Derived cache: `.lazy-harness/generated/record-index.json` when explicitly generated
- Downstream hosts: maintain their own `.lazy-harness/project/feature-navigation.xml` records

Do not treat this source map as Medivance, homepage, or any other downstream app's product map. Downstream dogfood evidence can motivate framework changes here, but downstream host maps remain host-owned.

## Implementation map

- Status: `phase-3-implemented`
- Primary files:
  - `.lazy-harness/ssot/project-navigation.md` — this SSOT for the source checkout project navigation map and ownership boundary.
  - `.lazy-harness/project/feature-navigation.xml` — canonical source-checkout feature map consumed by record-index projectProfile parsing.
  - `.lazy-harness/spec/platform/project-profile.md` — framework contract defining feature-navigation as retrieval source.
  - `.lazy-harness/spec/platform/search-read-debt-contract.md` — static search/read-debt contract that keeps direct retrieval evidence LLM-owned.
  - `.lazy-harness/scripts/record-index.ts` — parser/merger for `.lazy-harness/project/feature-navigation.xml` into `projectProfile.features` and record hints.
  - `.lazy-harness/schemas/record-index.schema.json` — output schema for feature entries and project profile metadata.
  - `.lazy-harness/scripts/self-test.py` — protects source feature ids, path existence, XML parsing, and record-index projectProfile output.
  - `.lazy-harness/knowledge/graph.jsonl` — graph rows linking this SSOT, the source map, record-index implementation, and self-test protection.
- Key symbols:
  - `parseFeatureNavigation` (`record-index.ts`) — reads `.lazy-harness/project/feature-navigation.xml`.
  - `mergeProjectProfile` (`record-index.ts`) — merges feature aliases/routes/components/files/tests into referenced record entries.
  - `buildRecordIndex` (`record-index.ts`) — emits the derived record index with `projectProfile` metadata.
  - `check_source_feature_navigation_phase3` (`self-test.py`) — verifies this source map remains complete enough for Phase 3.
- Flow:
  1. Agent or CLI builds record index.
  2. `record-index.ts` parses source feature navigation if present.
  3. Feature entries are emitted under `projectProfile.features`.
  4. Records referenced by feature entries receive `projectProfileFeatureIds`, aliases, surface terms, and implementation hints.
  5. Generated cache remains optional and may be absent.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `.lazy-harness/bin/lazy record-index --format=json`
  - `.lazy-harness/bin/lazy doctor --profile=smoke`
- Cross-layer links:
  - Planning: `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`
  - SDD: `.lazy-harness/spec/platform/project-profile.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`
- Machine index:
  - graph ids: `kg_project_navigation_ssot_sources_feature_map`, `kg_project_navigation_feature_map_indexed_by_record_index`, `kg_project_navigation_feature_map_protected_by_self_test`

## Rule placement

- Rule: the lazy-harness source checkout needs a canonical source-level feature-navigation map, while downstream hosts keep their own project maps.
- Scope: framework-source
- Primary record: `.lazy-harness/ssot/project-navigation.md`
- Why not AGENTS.md: this is project/source identity and navigation vocabulary, not universal operational grammar.
- Why not `.jcode`: the map is durable source-checkout context consumed by framework tooling, not private local Jcode wiring.

## Discovery capture

- DDD: none.
- SDD: existing Project Profile and search/read-debt contracts define feature-navigation and direct retrieval behavior.
- BDD: no user-visible UI flow change.
- TDD: self-test gains a source-map completeness fixture.
- ADR: no new decision; implements the prompt runtime compression Phase 3 plan under ADR 0041 direction.
- SSOT: this record owns source-checkout project navigation boundaries.
- Planning: Phase 3 of `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`.
