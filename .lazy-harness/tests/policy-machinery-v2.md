# TDD — Policy Machinery V2

Status: active-regression
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/policy-machinery-v2.md`
Related ADR: `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
Related SSOT: `.lazy-harness/ssot/policy-registry.md`
Related fixture: `.lazy-harness/fixtures/policy-machinery-v2/example-policy.json`
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md#phase-3--unify-rulebook--capability-registry-into-policy-machinery`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 정책 V2 회귀
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
  - prove `lazy rules` remains only compatibility/advisory after rulebook semantic retirement
  - prove block runtime readiness is a preflight only and does not install hard-stop hooks
  - prove dry-run block runtime helper only reacts to explicit structured dry-run context and never installs blocking hooks
  - prove policy packets use update-loop evidence without becoming canonical truth by themselves
- Must not:
  - add hook enforcement as part of this read-only policy registry slice
  - allow forbidden semantic-authority fields in policy fixture output
  - let `block` appear in the fixture without explicit confirmation and bypass/rollback evidence
- Record completion:
  - Phase 3 runtime/schema work must add focused tests before changing implementation.

## Source-host policy fixture dependency regression

사용자 승인: 정책을 유지하고 테스트의 근거 문서 복사 처리를 수정하는 A안 (`a로 해줘`).

- 원인: `check_policy_machinery_v2`의 policy-write-roundtrip 임시 호스트가 실제 policies.json은 복사하면서 고정 파일 목록 밖의 sourceRecord는 누락했다. `plain-language-research-reports`의 `.lazy-harness/planning/v2-vision-feasibility-research.md`가 재현 사례다.
- 보호: 기존 scope별 정책 필터를 유지하고, 임시 레지스트리에 남은 모든 정책의 sourceRecord를 현재 호스트 루트 안에서만 찾아 복사한다. 특정 프로젝트의 정책·문서를 하드코딩하지 않는다.
- 실제 sourceRecord 누락이나 절대/부모 경로·루트 밖 symlink는 실패한다. 잘못된 정책을 제거해 통과시키지 않는다.
- Implementation map: `.lazy-harness/scripts/self-test.py`의 `check_policy_machinery_v2` → scope별 fixture registry → sourceRecord 복사 → 기존 upsert dry-run/confirm/audit/resolve/warn/render/sync 검사. 정책 정본과 런타임 동작은 변경하지 않는다.

### Layer completeness — this regression

| Layer | 판단 |
|---|---|
| SDD | no independent delta — 공개 정책 계약 유지 |
| BDD | no independent delta — 사용자 흐름 유지 |
| SSOT | no independent delta — 정책/설정 정본 유지 |
| DDD | no independent delta — 용어·업무 규칙 유지 |

### Discovery capture

DDD/SDD/BDD/ADR/SSOT/Planning: none (독립 변경·새 backlog 없음). TDD: updated (본 절). 기존 실패 분석을 본 회귀 보호 기록으로 수렴한다.

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
| `policy_machinery_no_block_hook_runtime` | SDD/TDD text + helper output | Block policy readiness exists, but no lifecycle hard-stop hook or blocking output is installed. |
| `policy_machinery_generated_rulebook_view` | `lazy policy render-rulebook --write --format=json` + `.lazy-harness/generated/policy-rulebook.md` | Generated view contains canonical-source disclaimer, policy sections, deterministic output, and path confinement under `.lazy-harness/generated/**`. |
| `policy_machinery_policy_write_roundtrip` | temp host + `lazy policy upsert --from-json ... --confirm` | Dry-run does not write; confirmed upsert inserts/replaces id-sorted policies; saved policy audits cleanly and appears in resolve/warn/render outputs. |
| `policy_machinery_policy_sync_roundtrip` | temp host + `lazy-sync --force --quiet` | Host-local saved policy survives policy seed merge and framework seed policies are merged without overwriting host-local policies. |
| `policy_machinery_primary_canonical_recommend` | `primary-canonical-record` registry entry + synced temp host | Policy resolves as recommend/advisory-only, uses synced evidence paths, and the portable framework-seed + fixture-policy subset audits cleanly while an unsynced-source host-local policy remains preserved but outside portability audit scope. |
| `policy_machinery_rulebook_retire_readiness_source_host_ready` | source host + `lazy policy retire-readiness --strict --format=json` | Current host passes strict readiness after `.lazy-harness/rules/README.md` → `project-operating-rulebook` capability → `project-operating-rulebook-policy` typed policy link is complete. |
| `policy_machinery_rulebook_retire_readiness_positive_fixture` | temp host + `lazy policy retire-readiness --strict --format=json` | Strict readiness passes when active rulebook entry → capability → typed policy links are complete; missing policy ids fail deterministically. |
| `policy_machinery_rulebook_semantic_retirement_boundary` | `lazy rules list|audit|resolve --format=json` | Rulebook outputs expose `rulebook-compatibility/v1`, `retiredCanonicalSemantics=true`, `canonicalPolicySource=.lazy-harness/ssot/policies.json`, and resolve is `compatibility-advisory`. |
| `policy_machinery_block_runtime_readiness_preflight` | source host + temp hosts + `lazy policy block-readiness --strict --format=json` | Current source reports ready for `validation-evidence-block` with no hook mutation; positive fixture with promotion evidence passes; missing runtime fixture fails. |
| `policy_machinery_first_block_policy_readiness` | `.lazy-harness/ssot/policies.json`, `.lazy-harness/tests/policy-block-validation-evidence.md`, hard-stop audit | `validation-evidence-block` has user confirmation, validation-output evidence, hard-stop promotion metadata, runtime fixture, bypass, rollback, and passes readiness without installing hooks. |
| `policy_machinery_block_runtime_dry_run_helper` | `check-policy-block-runtime.py` payload fixtures + response.completed/lifecycle-check parity | Helper emits DRY-RUN STOP/ALLOW/BYPASS for explicit structured `policy_context.blockRuntimeDryRun=true`, stays silent for raw/no-dry-run payloads, is wired into lifecycle as dry-run/fail-open only, and does not install a blocking hook. |

## Layer completeness gate

- DDD: no independent delta; no domain term or business rule changed.
- SDD: updated `.lazy-harness/spec/platform/policy-machinery-v2.md` to define the portable framework-policy audit subset.
- BDD: no independent delta; agent-visible guidance and user flow are unchanged.
- SSOT: updated `.lazy-harness/ssot/policies.json` with the framework-global `primary-canonical-record` recommend policy; the later portable-subset fixture fix adds no further registry delta.
- ADR: `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md` clarifies the downstream fixture boundary.

## Implementation map

- Status: `option-b-selected-first-slice`
- Records:
  - `.lazy-harness/spec/platform/policy-machinery-v2.md`
  - `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md` — source canonical ADR.
  - downstream manifest targetPath `framework/operational-adrs/0046-policy-machinery-typed-policy-canonical.md` — synced framework ADR location.
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
  - `lazy policy block-readiness --format=json`
  - `lazy policy block-readiness --strict --format=json`
  - `.lazy-harness/hooks/lifecycle/helpers/check-policy-block-runtime.py <payload-json>`
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` with explicit dry-run payload
  - `.lazy-harness/scripts/lifecycle-check.py --format=json` with explicit dry-run payload
  - `lazy policy explain --id record-first-validation --format=md`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`

## Rule placement

- Layer: TDD.
- Why: this record defines regression protection for the Policy Machinery V2 static contract slice.
