# TDD — Architecture Guidance Core and Refactor Skill

Status: active-pilot
Date: 2026-07-14
Updated: 2026-07-20
Layer: TDD
Related ADR: `.lazy-harness/decisions/0054-three-layer-cross-stack-architecture-guidance.md`
Related SDD: `.lazy-harness/spec/platform/architecture-guidance.md`
Related BDD: `.lazy-harness/behavior/architecture-refactor-flow.md`
Related SSOT: `.lazy-harness/ssot/architecture-guidance-storage.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - architecture guidance regression
  - host architecture map tests
  - 아키텍처 가이드 회귀
  - 호스트 맵 테스트
- Surface terms:
  - stale plan exact digest no silent default alias relation cardinality
  - architecture candidate delegation sync preservation skill discovery
  - host self-test missing project identity synthetic owner fixture
- Applies when:
  - changing architecture catalog, schemas, CLI, Project Profile adapter, or skill
  - changing Category A distribution for architecture guidance
- Must:
  - prove inspect and plan are read-only
  - prove apply rejects missing, mismatched, or stale plan confirmation
  - prove valid apply writes only one host map atomically
  - prove aliases, relations, scope references, and cardinality are checked
  - prove unknown properties, parent traversal, and planning semantic owners are rejected
  - prove confirmation binds catalog content and apply respects an exclusive writer lock
  - prove Project Profile defaults to no architecture candidates
  - prove candidate promotion delegates without claiming a map write
  - prove sync preserves host-owned architecture maps
  - prove host-scope architecture self-test does not require a pre-existing host-owned project identity record
- Must not:
  - accept folder/framework evidence as confirmed architecture
  - create policy enforcement or application-source edits in core tests
  - fold graph legacy migration into this regression slice
- Record completion:
  - implementation changes update this TDD, fixtures, self-test, and layer judgements
- Related records:
  - `.lazy-harness/tests/project-profile-v2.md`
  - `.lazy-harness/tests/pi-agent-package.md`
  - `.lazy-harness/tests/lazy-sync-dirty-false-positive.md`

## Regression matrix

| Case | Input | Expected |
|---|---|---|
| `architecture_inspect_missing_map` | valid catalog, no host map | exit 0, unclassified, no write |
| `architecture_plan_invalid_catalog` | top-level/nested unknown catalog property | exit 2, no write |
| `architecture_plan_read_only` | valid candidate proposal | deterministic plan/digests, no write |
| `architecture_plan_root_relative` | relative proposal plus `--root` | resolve inside the host root |
| `architecture_plan_alias_expansion` | versioned alias instance | explicit deterministic bindings |
| `architecture_plan_unknown_property` | unknown proposal/binding property | exit 2, no write |
| `architecture_plan_reference_traversal` | root-looking ref containing `..` | exit 2, no write |
| `architecture_plan_semantic_owner_boundary` | planning record as semantic owner | exit 2, evidence is not promoted to truth |
| `architecture_plan_catalog_bound_digest` | valid catalog content change without version change | digest changes; old approval is rejected |
| `architecture_plan_missing_scope` | binding to unknown scope | exit 2, no write |
| `architecture_plan_scope_cycle` | non-host scopes with cyclic parents | exit 2, no write |
| `architecture_plan_runtime_cardinality` | entrypoint with zero/two runtimes | exit 2 |
| `architecture_plan_organization_cardinality` | responsibility with zero/two primaries | exit 2 |
| `architecture_plan_relation_requires` | missing required value | exit 2 |
| `architecture_plan_relation_direction` | required pair with reverse binding-ID sort order | valid independent of ID order |
| `architecture_plan_explicit_cross_scope` | relation with/without matching project edge | only the explicit edge makes it applicable |
| `architecture_plan_relation_conflict` | conflicting overlapping values | exit 2 |
| `architecture_plan_unknown_pair` | undocumented overlapping pair | unresolved until decision ref |
| `architecture_apply_requires_digest` | bare or missing confirmation/reference | exit 2, no map/artifacts |
| `architecture_apply_digest_mismatch` | wrong digest | exit 2, no map/artifacts |
| `architecture_apply_stale_baseline` | map changed after plan | exit 2, preserve map |
| `architecture_apply_writer_lock` | pre-existing exclusive lock | exit 2, preserve lock/map, no temporary file |
| `architecture_apply_atomic` | exact plan and confirmation ref | one confirmed map write; lock/temp cleaned |
| `architecture_apply_side_effect_boundary` | valid apply with full-tree snapshot | only the canonical host map changes |
| `project_profile_architecture_default_empty` | interview-v2 without file | `architectureCandidates=[]` |
| `project_profile_architecture_candidate` | valid candidate file | candidate preserved, no authority |
| `project_profile_architecture_invalid_contract` | forbidden/unknown field, traversal, planning owner | rejected before queue mutation |
| `project_profile_architecture_queue` | queue-v2 with candidate | contracts route and delegated target |
| `project_profile_architecture_dry_run` | promote preview | no queue/map mutation |
| `project_profile_architecture_delegate` | accepted confirm | queue-only delegated effect, no map |
| `project_profile_omp_compatibility` | interview packet | Pi primary, OMP compatibility, no active Jcode |
| `architecture_skill_contract` | package skill | required records, gate, stop rules, structured edits |
| `architecture_sync_preserves_host_map` | temporary downstream sync | map byte-identical |
| `architecture_host_without_project_identity` | host-scoped self-test source has no host-owned project identity | synthetic sandbox owner record; architecture check passes without creating or requiring a real host identity |

## Fixture contract

`.lazy-harness/fixtures/architecture-guidance/` contains:

- canonical `.lazy-harness/ssot/architecture-profile-catalog.json` is validated directly;
- `host-map-proposal.json` — candidate proposal with scopes, base, direct bindings,
  alias instance, semantic-owner refs, and no enforcement;
- `project-profile-candidates.json` — evidence-backed candidate input;
- negative inputs are created inside the sandbox test for unknown properties, traversal,
  planning semantic owners, catalog mutation, scope-parent cycles, stale/missing
  confirmation, scope/cardinality, directional and explicit-cross-scope relations,
  writer locking, and Project Profile rejection.

Fixtures are framework-owned Category A test assets. They do not create a real host
map in the source repository. The architecture sandbox writes a minimal synthetic
`.lazy-harness/ssot/project-identity.md` inside its temporary root because fixture
`ownerRefs` need an existing SSOT path; it must not copy or require the invoking
host's optional, host-owned project identity record.

## Acceptance assertions

Architecture pilot self-tests verify:

1. canonical records, schemas, catalog, fixtures, scripts, skill, and manifest entries
   exist;
2. catalog and proposal IDs/references satisfy the storage grammar;
3. inspect and plan are full-tree read-only, deterministic, and resolve relative proposals
   against `--root`;
4. runtime validation rejects unknown properties, traversal, and planning semantic owners
   in both core and Project Profile inputs;
5. the plan digest changes with validated catalog content even when catalog identity/version
   stays fixed;
6. alias expansion materializes only declared normalized bindings;
7. cardinality, directional relation order, explicit cross-scope edges, conflicts, and unknown
   combinations are checked;
8. exact-digest apply writes one confirmed map with provenance and cleans lock/temp files;
9. missing, bare, mismatched, stale, or locked apply leaves the prior full-tree state intact;
10. successful apply changes only `.lazy-harness/project/architecture-map.json`;
11. Project Profile emits no default candidates and rejects malformed explicit candidates;
12. candidate promotion remains queue-only and delegates host-map handling;
13. Pi package checks protect the skill exposure and safety contract;
14. temporary downstream Category A sync leaves a host-owned map byte-identical;
15. host-scope execution remains compatible with an older downstream install that has no
    `.lazy-harness/ssot/project-identity.md`, using only the synthetic sandbox owner record.

`check_architecture_guidance_cli` owns the sandbox core/adapter assertions. Companion Project
Profile, Pi package, and lazy-sync checks protect their existing surfaces; actual installed
Pi/OMP runtime discovery remains a separate rollout validation before the implementation commit.

Existing Project Profile and package self-tests continue to protect all prior modes
and promotion target kinds.

## Layer completeness impact

| Layer | Impact | Independent delta |
|---|---|---|
| DDD | architecture terms and identity invariants | yes — `domain/architecture-guidance.md` |
| SDD | new CLI, schemas, catalog, adapter, and writer contract | yes — `spec/platform/architecture-guidance.md` |
| BDD | approval-batched map/refactor behavior | yes — `behavior/architecture-refactor-flow.md` |
| SSOT | canonical paths, sync ownership, and map mutability | yes — `ssot/architecture-guidance-storage.md` |

### 2026-07-20 compatibility amendment

| Layer | Impact | Independent delta |
|---|---|---|
| DDD | none; architecture vocabulary is unchanged | no independent delta |
| SDD | none; CLI, schema, and writer contracts are unchanged | no independent delta |
| BDD | none; user-visible architecture flow is unchanged | no independent delta |
| SSOT | host identity remains host-owned and optional for sync | no independent delta |

The TDD/self-test fixture alone changes: a framework-owned synthetic owner record replaces
the accidental dependency on the invoking host's project identity. No host record is
created, migrated, or promoted by this framework fix.

ADR 0054 is amended because the previously unapproved pilot implementation is now
explicitly approved. Existing planning records are linked and do not need mirrored
runtime prose.

## Project Map branch

- Anchor: `cross-stack-architecture-guidance`
- Branch: `validation`
- Node: `architecture-guidance-regression`
- Primary: `validation`
- Facets: `TDD`, `Evidence`
- Edges:
  - `cross-stack-architecture-guidance --has-validation--> architecture-guidance-regression`
- Related records:
  - `.lazy-harness/spec/platform/architecture-guidance.md`
  - `.lazy-harness/behavior/architecture-refactor-flow.md`
  - `.lazy-harness/ssot/architecture-guidance-storage.md`

## Implementation map

- Status: `implemented; source validation passed; rollout pending`
- Primary files:
  - `.lazy-harness/tests/architecture-guidance.md` — this contract.
  - `.lazy-harness/fixtures/architecture-guidance/**` — positive fixtures.
  - `.lazy-harness/scripts/self-test.py#check_architecture_guidance_cli` — sandbox
    CLI, Project Profile, ownership, digest, alias/relation/cardinality, and no-write coverage;
    writes a synthetic temporary identity owner without reading the invoking host identity.
  - `.lazy-harness/tests/project-profile-v2.md` — adapter regression amendment.
  - `.lazy-harness/tests/pi-agent-package.md` — skill availability amendment.
- Validation:
  - focused architecture self-test, including a copied host with project identity removed
  - Project Profile V2 runtime/queue tests
  - Pi package contract
  - `.lazy-harness/bin/lazy test --scope framework`
  - `.lazy-harness/evidence/2026-07-14-cross-stack-architecture-pilot-validation.md`

## Rule placement

- Rule: architecture core and skill changes require no-write, exact-plan, ownership,
  Project Profile delegation, package discovery, and sync-preservation regressions.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/architecture-guidance.md`
- Why not AGENTS.md: these are executable regression expectations.
- Confirmation: user-approved core+skill pilot on 2026-07-14.

## Discovery capture

- DDD: independent vocabulary impact recorded.
- BDD: independent approval/refactor flow recorded.
- SDD: independent interfaces and validation contract recorded.
- TDD: this record owns regression expectations and layer completeness.
- ADR: ADR 0054 pilot amendment required and included in the work unit.
- SSOT: independent storage/ownership impact recorded.
- Planning: no separate backlog; failed or deferred items remain in the final evidence.
