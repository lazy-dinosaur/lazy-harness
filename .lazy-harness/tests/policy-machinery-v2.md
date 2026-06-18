# TDD — Policy Machinery V2

Status: active-regression
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/policy-machinery-v2.md`
Related ADR: `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
Related SSOT: `.lazy-harness/ssot/policy-registry.md`
Related fixture: `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json`
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md#phase-3--unify-rulebook--capability-registry-into-policy-machinery`

## Rule digest

- Status: active-regression / Option B typed policy canonical slice
- Scope: framework-global
- Applies when:
  - editing Policy Machinery V2 records or fixture
  - changing rulebook/capability/update-loop integration
  - preparing Phase 3 runtime/schema work
- Must:
  - validate the Phase 3 typed policy packet fixture
  - prove Policy Machinery V2 uses typed policy registry as canonical behavior policy storage
  - prove `lazy policy list/audit/explain` is read-only and deterministic
  - prove `lazy policy resolve` is advisory-only for discover/recommend/default and does not warn/block
  - prove warn-only runtime requires explicit structured policy context and does not block
  - prove rulebook markdown is compatibility/generated/explain surface during migration
  - prove generated rulebook views are deterministic, non-canonical, and generated from typed policies
  - prove actual policy write round-trips save and apply through audit/resolve/warn/render/sync
  - prove rulebook retire-readiness is non-destructive and blocks until active rulebook entries have typed policy coverage
  - prove policy packets use update-loop evidence without becoming canonical truth by themselves
- Must not:
  - add hook enforcement as part of this read-only policy registry slice
  - allow forbidden semantic-authority fields in policy fixture output
  - let `block` appear in the fixture without explicit confirmation and bypass/rollback evidence
- Record completion:
  - Phase 3 runtime/schema work must add focused tests before changing implementation.

## Regression cases

| Case | Evidence | Expected |
|---|---|---|
| `policy_machinery_contract_files` | SDD/TDD/audit/fixture/ADR/SSOT/schema | All Phase 3 Option B files exist and are synced by manifest. |
| `policy_machinery_fixture_shape` | `example-policy.json` | Fixture schema is `policy-machinery-v2/v1`, stage/level are controlled vocabulary, sourceRecord is root-relative, and updateLoop cannot canonicalize by packet alone. |
| `policy_machinery_no_semantic_authority_fields` | recursive fixture scan | Fixture contains no confidence/intent/risk/requiredRead/nextAction/candidateMeaning fields. |
| `policy_machinery_option_b_storage` | SDD + ADR + SSOT + fixture | Typed policy registry is canonical; rulebook markdown is compatibility/generated/explain surface during migration. |
| `policy_machinery_policy_cli_read_only` | `lazy policy list/audit/explain/resolve/render-rulebook` | CLI reads typed policy registry, emits deterministic JSON/Markdown, and only writes the generated rulebook view when `render-rulebook --write` is explicitly requested. |
| `policy_machinery_policy_resolve_advisory_only` | `lazy policy resolve --stage turn --applies-to making_validation_claims --format=json` | Resolver returns matching policies with `enforcement=advisory-only`, `recommendedAction=surface-guidance`, and no warn/block runtime decision. |
| `policy_machinery_warn_runtime_explicit_context` | `check-policy-warn-runtime.py` fixture payloads | Warn runtime emits `WARN` only for explicit structured `policy_context`, stays silent for raw text, supports acknowledgement, and never emits `STOP`. |
| `policy_machinery_no_block_runtime` | SDD/TDD text + helper output | Warn-only slice does not add block runtime or blocking output. |
| `policy_machinery_generated_rulebook_view` | `lazy policy render-rulebook --write --format=json` + `.lazy-harness/generated/policy-rulebook.md` | Generated view contains canonical-source disclaimer, policy sections, deterministic output, and path confinement under `.lazy-harness/generated/**`. |
| `policy_machinery_policy_write_roundtrip` | temp host + `lazy policy upsert --from-json ... --confirm` | Dry-run does not write; confirmed upsert inserts/replaces id-sorted policies; saved policy audits cleanly and appears in resolve/warn/render outputs. |
| `policy_machinery_policy_sync_roundtrip` | temp host + `lazy-sync --force --quiet` | Host-local saved policy survives policy seed merge and framework seed policies are merged without overwriting host-local policies. |
| `policy_machinery_rulebook_retire_readiness_source_host_ready` | source host + `lazy policy retire-readiness --strict --format=json` | Current host passes strict readiness after `.lazy-harness/rules/README.md` → `project-operating-rulebook` capability → `project-operating-rulebook-policy` typed policy link is complete. |
| `policy_machinery_rulebook_retire_readiness_positive_fixture` | temp host + `lazy policy retire-readiness --strict --format=json` | Strict readiness passes when active rulebook entry → capability → typed policy links are complete; missing policy ids fail deterministically. |

## Layer completeness gate

- DDD: no domain/business rule impact.
- SDD: `.lazy-harness/spec/platform/policy-machinery-v2.md`.
- BDD: agent guidance remains advisory unless a future confirmed policy level explicitly changes behavior.
- SSOT: `.lazy-harness/ssot/policy-registry.md` is canonical for behavior policy semantics; `.lazy-harness/ssot/capability-registry.md` stays canonical for kind/level bindings.
- ADR: `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md` records user-confirmed Option B.

## Implementation map

- Status: `option-b-selected-first-slice`
- Records:
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md` — source canonical ADR.
  - `.lazy-harness/framework/operational-adrs/0046-policy-machinery-typed-policy-canonical.md` — host sync target for the same framework ADR.
  - `.lazy-harness/ssot/policy-registry.md`
  - `.lazy-harness/planning/policy-machinery-v2-baseline-gap-audit.md`
  - `.lazy-harness/tests/policy-machinery-v2.md`
- Fixture:
  - `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json`
- Source/test:
  - `.lazy-harness/scripts/policy.ts`
  - `.lazy-harness/hooks/lifecycle/helpers/check-policy-warn-runtime.py`
  - `.lazy-harness/generated/policy-rulebook.md`
  - `.lazy-harness/ssot/policies.json`
  - `.lazy-harness/schemas/policies.schema.json`
  - `.lazy-harness/scripts/self-test.py#check_policy_machinery_v2`
  - `.lazy-harness/manifests/init-categories.json` — includes Policy Machinery V2 records plus `spec/platform/project-operating-rulebook.md` dependency for host validation.
- Validation:
  - `lazy policy audit --format=json`
  - `lazy policy resolve --stage turn --applies-to making_validation_claims --format=json`
  - `lazy policy resolve --runtime warn --stage turn --applies-to making_validation_claims --format=json`
  - `lazy policy render-rulebook --write --format=json`
  - `lazy policy upsert --from-json <policy.json> --confirm --format=json`
  - `lazy policy retire-readiness --format=json`
  - `lazy policy retire-readiness --strict --format=json`
  - `lazy policy explain --id record-first-validation --format=md`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`

## Rule placement

- Layer: TDD.
- Why: this record defines regression protection for the Policy Machinery V2 static contract slice.
