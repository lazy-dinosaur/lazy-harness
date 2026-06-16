# Project Profile V2 Design Review

Status: review-draft
Date: 2026-06-16
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/project-profile-v2.md`
Related plan: `.lazy-harness/plans/project-init-interview-v2-spec.md`
Related TDD: `.lazy-harness/tests/project-profile-v2.md`
Related fixture: `.lazy-harness/fixtures/project-profile-v2/interview-output.json`
Related Project Map: `.lazy-harness/spec/platform/project-map-v2.md`, `.lazy-harness/ssot/project-map-taxonomy.md`

## Review scope

This review covers Phase 2 design only:

- Project Profile V2 SDD
- Project Init Interview V2 plan
- Project Profile V2 TDD
- interview output fixture
- relationship to Project Map V2 anchor/branch/edge model

Runtime implementation is out of scope.

## Corrected review result

The Phase 2 design is useful, but it is currently **too interview-centered**.

Project Interview should not become the center of V2. It is one input channel for seeding the project map and policies, especially during project initialization or profile refresh.

The V2 center should remain:

1. Project Map / Project Atlas
2. Policy Machinery
3. Evidence and validation loop
4. Adapter-neutral core with Pi primary and Jcode compatibility
5. Multiple knowledge ingestion/update paths

Project Interview is only one path among several:

- project interview / profile refresh
- lazy-harness installation on a new project
- mid-project adoption to discover missing profile/context
- normal implementation work
- user corrections
- source/test inspection
- design reviews
- failed validation / regressions
- ADR decisions
- policy/capability changes
- document ingestion
- Pi/Jcode adapter events

Therefore, **do not proceed directly from this Phase 2 draft into Project Interview runtime implementation** without first re-centering the roadmap around the broader Project Map update loop.

## What is still good in the Phase 2 draft

- It correctly avoids being a test wizard.
- It represents Pi primary / Jcode compatibility.
- It uses Project Map cluster seed candidates.
- It models stage-aware policy candidates.
- It keeps initial policy levels at `discover`/`recommend`.
- It preserves no-silent-defaults and confirmed-only writes.
- It includes at least one non-test policy path.

## What needs correction

### 1. Interview should be an ingestion channel, not the main architecture

The SDD phrase “Project Interview as the entry point” is too strong if read as the main V2 entry point.

Better wording:

```text
Project Interview V2 is one installation/adoption/refresh channel for Project Profile bootstrap, missing-context detection, Project Map seeding, and policy discovery.
```

The main architecture should describe the general Project Map update loop:

```text
observe / inspect / ask / implement / validate / decide
→ update project-map cluster
→ update policy/capability if confirmed
→ preserve evidence
```

### 2. SDD and fixture question group coverage differ

The SDD lists 14 expected question groups:

1. `project-purpose`
2. `stack-platform`
3. `source-ownership`
4. `system-design`
5. `domain-vocabulary`
6. `frontend-design`
7. `backend-data`
8. `validation-policy`
9. `workflow-policy`
10. `dependency-policy`
11. `security-privacy`
12. `documentation-policy`
13. `human-confirmation`
14. `agent-autonomy`

The current fixture includes 8 groups:

- `project-purpose`
- `source-ownership`
- `system-design`
- `domain-vocabulary`
- `validation-policy`
- `dependency-policy`
- `security-privacy`
- `human-confirmation`

This mismatch is acceptable for draft exploration, but not for implementation.

### 3. Plan and SDD grouping are not fully aligned

The plan currently uses 12 sections and combines some groups, while the SDD uses 14 named groups.

Examples:

- plan combines backend/data/security, while SDD separates `backend-data` and `security-privacy`.
- plan combines human confirmation and autonomy, while SDD separates `human-confirmation` and `agent-autonomy`.

### 4. Policy storage target remains intentionally unresolved

The fixture has an unresolved ambiguity:

```text
Should confirmed project policies be written first as Project Map candidates, .lazy-harness/rules records, or capabilities.json bindings?
```

This is good. Do not decide silently. It should remain an option gate before implementation.

### 5. Runtime mode decision is still open

Before coding, decide whether V2 should be:

- a new `interview-v2` / `plan-v2` mode, or
- an evolution of existing `interview` mode with compatibility output.

But this should happen only after deciding whether Project Interview should be implemented now at all.

### 6. Static fixture validation is currently ad hoc

Phase 2 design was validated manually/ad hoc and `lazy test` is green, but there is not yet a dedicated self-test function enforcing the Project Profile V2 fixture invariants.

This is acceptable for design review, but before runtime implementation lands, add static self-test coverage for:

- all required question groups,
- Pi primary / Jcode compatibility,
- Project Map cluster seed shape,
- stage-aware policy candidates,
- no forbidden semantic-authority fields,
- confirmed-only writes.

## Recommended next action

Do **not** implement Project Interview V2 next.

Recommended next step is to define the broader **Project Map Update Loop / Knowledge Ingestion Model** first.

That should answer:

1. What events can create/update Project Map clusters?
2. How do normal implementation turns update the map?
3. How do user corrections update the map?
4. How do validation failures become branches/evidence?
5. How do policy candidates get promoted/demoted?
6. How does Pi consume/update this without Jcode-specific assumptions?
7. Where does Project Interview fit among these channels?

### 7. Interview's proper role is project profile bootstrap/repair

User clarified that interview matters because lazy-harness may be installed on a project from scratch or introduced into an existing project midstream. In that context, interview should:

- find missing profile/map/policy areas,
- define baseline project conventions,
- capture system design and folder/source structure,
- capture tech stack and project goals,
- record how the project should be developed and collaborated on,
- and seed the profile/map so future work is standardized.

This reinforces that interview is useful, but still not the V2 center.

After that, Project Interview V2 can be implemented as one adapter/channel inside the broader model.

## Decision options for user review

A. Recommended: pause Project Interview runtime work and define `Project Map Update Loop / Knowledge Ingestion Model` first.
B. Keep Phase 2 interview design as a draft, but move to Phase 3 policy machinery next.
C. Amend Phase 2 interview design now, but still do not implement runtime code.
D. Ignore this concern and implement Project Interview V2 now.
E. Direct input.

## Rule placement

- Rule: Project Interview V2 is useful but must not become the center of V2; it should be treated as one Project Map/policy ingestion channel under a broader Project Map Update Loop.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/project-profile-v2-design-review.md`
- Why not AGENTS.md: this is a phase review and implementation planning note, not prompt grammar.
- Why not `.jcode`: Project Profile V2 is Pi-primary and agent-neutral, not Jcode-local.
- Confirmation: user-corrected direction; implementation is still awaiting user 검수.

## Discovery capture

- DDD: candidate domain-vocabulary question group alignment finding.
- BDD: candidate interview behavior and no-silent-defaults alignment finding.
- SDD: candidate SDD/fixture mismatch and scope correction.
- TDD: candidate self-test fixture validation gap.
- ADR: none yet; runtime mode and storage target may need future ADR if adopted.
- SSOT: candidate policy storage ambiguity remains unresolved.
- Planning: updated by this corrected review record.
