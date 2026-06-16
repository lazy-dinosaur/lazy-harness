# TDD — Project Profile V2 / Project Interview Policy Discovery

Status: draft
Date: 2026-06-16
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/project-profile-v2.md`
Related plan: `.lazy-harness/plans/project-init-interview-v2-spec.md`
Related Project Map: `.lazy-harness/spec/platform/project-map-v2.md`

## Rule digest

- Status: draft
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
  - require runtime code changes before design 검수
- Record completion:
  - runtime implementation later updates this TDD, SDD, fixture, `project-profile.ts`, self-test, manifest, and graph rows together.

## Draft fixture

The design fixture is:

```text
.lazy-harness/fixtures/project-profile-v2/interview-output.json
```

## Regression cases for future implementation

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

## Acceptance assertions for future code phase

Future self-test should verify:

1. `project-profile.ts` exposes V2 mode or V2 dry-run output without breaking V1 modes.
2. V2 output matches the fixture shape.
3. V2 output includes Project Map cluster seeds.
4. V2 output includes policy candidates for at least validation and a non-test dimension.
5. Initial policy candidate levels are only `discover` or `recommend` unless fixture marks a confirmed answer.
6. `fill --confirm` writes only confirmed answers.
7. Pi primary/Jcode compatibility appears in output.
8. Existing Project Profile tests still pass.

## Implementation map

- Status: draft design only
- Primary files:
  - `.lazy-harness/tests/project-profile-v2.md` — this TDD.
  - `.lazy-harness/spec/platform/project-profile-v2.md` — SDD output contract.
  - `.lazy-harness/plans/project-init-interview-v2-spec.md` — interview plan.
  - `.lazy-harness/fixtures/project-profile-v2/interview-output.json` — desired output fixture.
- Future implementation files:
  - `.lazy-harness/scripts/project-profile.ts`
  - `.lazy-harness/scripts/self-test.py`
- Future key symbols:
  - `ProjectProfileInterviewV2Packet`
  - `buildInterviewV2Result`
- Protection now:
  - record/fixture validation and `lazy test`
- Protection future:
  - self-test runtime fixture after implementation.

## Layer completeness impact

- DDD: domain vocabulary/invariant question groups protected as future fixture expectation.
- BDD: project expectations and workflow behavior protected as future fixture expectation.
- SDD: paired with Project Profile V2 SDD.
- TDD: this record defines future tests.
- ADR: future ADR needed before replacing V1 mode semantics.
- SSOT: policy/capability/taxonomy SSOT inputs are referenced, not changed here.
- Planning: Phase 2 design only.

## Rule placement

- Rule: Project Profile V2 must be tested as a project-map and policy-discovery interview, not a test-only wizard or silent default generator.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/project-profile-v2.md`
- Why not AGENTS.md: this is a regression/acceptance contract, not prompt grammar.
- Why not `.jcode`: V2 is Pi-primary and agent-neutral.
- Confirmation: user-approved Phase 2 design draft; no runtime implementation approval yet.

## Discovery capture

- DDD: future domain branch coverage.
- BDD: future behavior/policy coverage.
- SDD: paired with SDD.
- TDD: updated here.
- ADR: none yet.
- SSOT: no SSOT mutation yet.
- Planning: Phase 2 design covered.
