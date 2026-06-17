# TDD — Project Profile V2 / Project Interview Policy Discovery

Status: active-runtime-dry-run
Date: 2026-06-16
Updated: 2026-06-17
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/project-profile-v2.md`
Related plan: `.lazy-harness/plans/project-init-interview-v2-spec.md`
Related Project Map: `.lazy-harness/spec/platform/project-map-v2.md`

## Rule digest

- Status: active-runtime-dry-run
- Layer: TDD
- Scope: framework-global
- Applies when:
  - implementing Project Interview V2 runtime behavior
  - changing the desired V2 interview output packet
  - adding Pi/Jcode adapter consumption of project profile/interview output
- Must:
  - verify V2 interview output includes project-map seed candidates and policy candidates
  - verify question groups cover non-test dimensions
  - verify policy candidates are stage-aware and start at discover/recommend unless explicitly confirmed
  - verify Pi primary / Jcode compatibility adapter boundary
  - verify dry-run and confirmed-only write semantics
  - verify forbidden semantic-authority fields are absent
- Must not:
  - permit silent defaults
  - permit unconfirmed facts/policies to become canonical writes
  - center the model on tests only
  - require write/apply behavior before a separate approval
- Record completion:
  - runtime implementation updates this TDD, SDD, fixture, `project-profile.ts`, self-test, manifest, and graph rows together.

## Draft fixture

The design fixture is:

```text
.lazy-harness/fixtures/project-profile-v2/interview-output.json
```

## Regression cases for implemented dry-run runtime

| Case | Input | Expected |
|---|---|---|
| `project_profile_v2_packet_shape` | dry-run interview output | `schemaVersion`, `adapterBoundary`, `questionGroups`, `projectMapSeeds`, `policyCandidates`, `unresolvedAmbiguities`, `writes` present. |
| `project_profile_v2_pi_primary` | output packet | `adapterBoundary.primary == "pi"` and compatibility includes `jcode`. |
| `project_profile_v2_question_groups` | output packet | non-test groups exist: source ownership, system design, domain vocabulary, dependency policy, security/privacy, human confirmation. |
| `project_profile_v2_project_map_seeds` | output packet | seeds include Project Map V2 cluster fields and branches. |
| `project_profile_v2_policy_candidates` | output packet | policies include stage-aware levels and at least one non-test policy. |
| `project_profile_v2_no_silent_defaults` | output packet | unconfirmed answers remain candidates or unresolved ambiguities. |
| `project_profile_v2_no_forbidden_fields` | recursive packet walk | no `confidence`, `intent`, `risk`, `requiredRead`, `optionalRead`, `gate`, `nextAction`, or `candidateMeaning`. |
| `project_profile_v2_backward_compat` | existing V1 project-profile commands | `inspect`, `plan`, `apply`, `interview`, and `fill` still pass existing self-test until migration is explicitly approved. |

## Acceptance assertions for implemented dry-run runtime

`self-test.py#check_project_profile_v2_runtime` verifies:

1. `project-profile.ts` exposes V2 mode or V2 dry-run output without breaking V1 modes.
2. V2 output matches the fixture shape.
3. V2 output includes Project Map cluster seeds.
4. V2 output includes policy candidates for at least validation and a non-test dimension.
5. Initial policy candidate levels are only `discover` or `recommend` unless fixture marks a confirmed answer.
6. `fill --confirm` writes only confirmed answers.
7. Pi primary/Jcode compatibility appears in output.
8. Existing Project Profile tests still pass.

## Implementation map

- Status: first dry-run runtime slice implemented.
- Primary files:
  - `.lazy-harness/tests/project-profile-v2.md` — this TDD.
  - `.lazy-harness/spec/platform/project-profile-v2.md` — SDD output contract.
  - `.lazy-harness/plans/project-init-interview-v2-spec.md` — interview plan.
  - `.lazy-harness/fixtures/project-profile-v2/interview-output.json` — desired output fixture.
  - `.lazy-harness/scripts/project-profile.ts` — implements `interview-v2 --dry-run`.
  - `.lazy-harness/scripts/self-test.py` — protects runtime packet shape and V1 backward compatibility.
- Key symbols:
  - `project-profile.ts#ProjectProfileInterviewV2Packet`
  - `project-profile.ts#buildInterviewV2Result`
  - `project-profile.ts#renderInterviewV2Md`
  - `self-test.py#check_project_profile_v2_runtime`
- Protection now:
  - `bun .lazy-harness/scripts/project-profile.ts --mode interview-v2 --dry-run --format json`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`
- Runtime boundary:
  - `interview-v2` is read-only and requires `--dry-run`.
  - `interview-v2 --confirm` is blocked.
  - no canonical Project Map/profile/policy writes happen in this slice.

## Layer completeness impact

- DDD: domain vocabulary/invariant question groups protected as future fixture expectation.
- BDD: project expectations and workflow behavior protected as future fixture expectation.
- SDD: paired with Project Profile V2 SDD.
- TDD: this record and `self-test.py#check_project_profile_v2_runtime` protect the implemented dry-run packet.
- ADR: future ADR needed before replacing V1 mode semantics.
- SSOT: policy/capability/taxonomy SSOT inputs are referenced, not changed here.
- Planning: Phase 2 first dry-run runtime slice implemented; write/apply mode remains future work.

## Rule placement

- Rule: Project Profile V2 must be tested as a project-map and policy-discovery interview, not a test-only wizard or silent default generator.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/project-profile-v2.md`
- Why not AGENTS.md: this is a regression/acceptance contract, not prompt grammar.
- Why not `.jcode`: V2 is Pi-primary and agent-neutral.
- Confirmation: user-approved Phase 2 design draft and first read-only runtime slice on 2026-06-17.

## Discovery capture

- DDD: future domain branch coverage.
- BDD: future behavior/policy coverage.
- SDD: paired with SDD and implemented by `project-profile.ts#buildInterviewV2Result`.
- TDD: updated here and in `self-test.py#check_project_profile_v2_runtime`.
- ADR: none yet; ADR required only before replacing V1 behavior.
- SSOT: no SSOT mutation; uses Project Map ingestion source vocabulary.
- Planning: Phase 2 dry-run runtime slice implemented.
