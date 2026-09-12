# TDD — Host-owned document validation scope

## Rule digest
- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - init self-test failure
  - host document scope
  - Category B prose
  - 초기화 검증 경계
- Applies when:
  - checking bounded validation or policy machinery on a newly initialized or customized host
- Must:
  - keep both functional check functions registered as BOTH
  - validate framework test-strategy and generated README prose in framework scope
  - preserve host-owned test-strategy and generated README without reading them as framework prose contracts
  - retain framework-managed guidance and functional checks in host scope
- Must not:
  - fix host validation by overwriting Category B documents or skipping entire runtime checks
  - reinterpret this boundary as allowing malformed XML or disabling general document parsing
- Related records:
  - `.lazy-harness/decisions/0026-doctor-self-test-scope-separation.md`
  - `.lazy-harness/tests/bounded-validation-governor.md`
  - `.lazy-harness/tests/policy-machinery-v2.md`

## Confirmed repair boundary
The user selected validation-boundary separation rather than initial-template prose changes. `lazy-init` deliberately seeds a draft host test strategy and an empty-tolerant generated container. Exact framework prose is not their host schema. Existing host content and historical experimental failures must remain untouched.

## Protection
- Framework scope: valid documents reach functional execution; every required phrase and both file-presence requirements remain enforced.
- Host scope: custom, empty, or absent Category B documents are not inputs to these two framework-prose assertions. Other XML/record checks retain their own contracts.
- Missing framework-managed AGENTS or policy CLI guidance still fails in both scopes.
- `check_bounded_validation_governor_cli` and `check_policy_machinery_v2` remain BOTH; no deadline, functional assertion, or release permission is relaxed.
- Guard-level tests stop at the first external command and do not claim runtime functional coverage. Separately run actual standard validation in fresh and customized initialized hosts to exercise the complete functions.
- User also approved repairing the newly exposed fixture failures: disposable validation projects need an initial Git commit; the real policy-sync roundtrip uses a complete minimal manifest over its own fixture records rather than treating an installed host as a source checkout. All merge/id/audit assertions remain, with full target-owned policy preservation additionally asserted.
- The policy roundtrip no longer copies the host-owned generated README into its fixture; generated output creation is exercised by the real render command instead.

## Implementation map
- `.lazy-harness/scripts/self-test.py#check_bounded_validation_governor_cli`: checks Category A guidance everywhere, source test-strategy prose only in framework scope.
- `.lazy-harness/scripts/self-test.py#check_policy_machinery_v2`: reads/asserts generated README prose only in framework scope; functional policy checks remain shared.
- `.lazy-harness/scripts/self-test.py#check_host_document_validation_scope`: FRAMEWORK_ONLY regression wrapper, without reclassifying the two BOTH checks.
- `tests/lazy-harness/host-document-validation-scope.test.py#DocumentScopeTests`: guard-level positive/negative and registration tests.
- `.lazy-harness/scripts/lazy-init.ts#makeSeedFile` and `makeReadme`: unchanged Category B generation.
- `.lazy-harness/manifests/init-categories.json`: distributes this framework regression record, without changing Category B ownership.
- Graph id: `kg_host_document_validation_scope`.

## Layer completeness
| Layer | Judgment |
|---|---|
| SDD | No independent delta: CLI and functional validation contracts unchanged; correct existing framework/host scope. |
| BDD | No independent product-flow delta; fresh/custom host verification protects existing initialization behavior. |
| SSOT | No ownership/config semantic change; Category B remains host-owned. Manifest adds only this test record. |
| DDD | No independent delta. |

## Discovery capture / rule placement
This TDD is the primary regression narrative. ADR0026 receives a narrow scope-classification amendment as its existing completion rule requires. No new policy, template enforcement, host migration, or historical experiment regrading. Validation evidence is retained in `/tmp/lazy-harness-init-scope-e1MDLc9i/evidence/`; results are not inferred from this record.
