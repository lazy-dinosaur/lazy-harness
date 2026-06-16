# SDD — Project Profile V2 / Project Interview Policy Discovery

Status: draft
Date: 2026-06-16
Layer: SDD
Related SDD: `.lazy-harness/spec/platform/project-profile.md`, `.lazy-harness/spec/platform/project-map-v2.md`
Related plan: `.lazy-harness/plans/project-init-interview-v2-spec.md`, `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`
Related TDD: `.lazy-harness/tests/project-profile-v2.md`
Related SSOT: `.lazy-harness/ssot/project-map-taxonomy.md`, `.lazy-harness/ssot/capability-registry.md`
Related ADR: `.lazy-harness/decisions/0044-project-operating-rulebook.md`

## Rule digest

- Status: draft
- Layer: SDD
- Scope: framework-global
- Applies when:
  - redesigning Project Interview as the entry point for V2 Project Map seeds and project/team policy discovery
  - extending `project-profile.ts` interview/plan/fill behavior in a future implementation phase
  - designing Pi-primary adapter output for project profile/interview data
- Must:
  - treat Project Interview as project understanding + policy discovery, not a test-strategy wizard
  - emit Project Map cluster seed candidates that use Project Map V2 anchor/branch/edge semantics
  - emit policy/capability seed candidates with stage-aware levels
  - keep initial policy levels at `discover` or `recommend` unless user/team explicitly confirms stronger enforcement
  - preserve no-silent-defaults behavior
  - keep Pi as primary future adapter and Jcode as compatibility adapter
  - keep existing Project Profile V1 behavior compatible until implementation migration is approved
- Must not:
  - write confirmed project facts, policies, or block-level capabilities without user-confirmed answers
  - treat interview output as a frozen preset
  - promote a policy to `warn` or `block` only because a generated fixture or adapter suggests it
  - make tests the center of the policy model
- Record completion:
  - changes update this SDD, V2 interview plan, TDD, fixture, manifest sync entries, and graph rows together.

## Purpose

Project Profile V2 turns Project Interview into the entry point for:

1. project understanding,
2. Project Map cluster seed discovery,
3. project/team policy discovery,
4. stage-aware capability candidates,
5. unresolved ambiguity capture.

The output should help a Pi-first or Jcode-compatible agent start from the project map instead of guessing file edits or applying universal workflow defaults.

## Current baseline

The existing `project-profile.ts` supports:

- `inspect`
- `plan`
- `apply`
- `interview`
- `fill`
- explicit confirmed answers
- missing artifact detection
- needs-interview fields

Phase 2 design must not break this baseline. Runtime implementation comes after user 검수.

## V2 interview output model

The desired dry-run/interview output packet is JSON-compatible:

```json
{
  "schemaVersion": "project-profile-interview-v2/v1",
  "mode": "interview-v2",
  "adapterBoundary": { "primary": "pi", "compatibility": ["jcode"] },
  "projectMapSeeds": [],
  "policyCandidates": [],
  "questionGroups": [],
  "unresolvedAmbiguities": [],
  "writes": { "dryRun": true, "confirmedOnly": true }
}
```

### Required top-level fields

| Field | Meaning |
|---|---|
| `schemaVersion` | `project-profile-interview-v2/v1`. |
| `mode` | `interview-v2`, `plan-v2`, or future compatible mode. |
| `adapterBoundary` | Pi primary, Jcode compatibility, core semantics adapter-neutral. |
| `projectMapSeeds` | Draft Project Map V2 anchor/branch/edge seed candidates. |
| `policyCandidates` | Draft project/team policy or capability candidates. |
| `questionGroups` | Interview question groups by project dimension. |
| `unresolvedAmbiguities` | Things that must stay candidate until answered. |
| `writes` | Dry-run/confirmed-only behavior declaration. |

Forbidden semantic-authority fields anywhere in the packet:

```text
confidence intent risk requiredRead optionalRead gate nextAction candidateMeaning
```

## Question groups

Project Interview V2 should cover at least these dimensions:

1. `project-purpose` — product goal, users, constraints, quality priorities.
2. `stack-platform` — runtime, framework, platform, deployment assumptions.
3. `source-ownership` — source roots, generated files, forbidden edit areas, ownership boundaries.
4. `system-design` — architecture style, layering, ports/adapters, vertical slices, module boundaries.
5. `domain-vocabulary` — bounded contexts, terms, invariants, domain/ownership facts.
6. `frontend-design` — design system, UI conventions, accessibility, Figma/design tokens.
7. `backend-data` — API style, persistence, validation, auth, error/logging, migrations.
8. `validation-policy` — test strategy and validation commands as one policy dimension.
9. `workflow-policy` — commit/push/PR/review/release flow.
10. `dependency-policy` — package addition, supply-chain boundaries, dependency review.
11. `security-privacy` — security, compliance, data/privacy boundaries.
12. `documentation-policy` — docs/record update expectations.
13. `human-confirmation` — irreversible actions, high-risk mutation, when to ask.
14. `agent-autonomy` — refactor autonomy, cleanup policy, allowed/forbidden initiative.

Each group should be able to produce:

- Project Map anchor/branch seed candidates,
- policy candidates,
- source/record output targets,
- unresolved ambiguity questions.

## Project Map seed candidates

Project Interview V2 should produce **candidates**, not confirmed facts, unless the answer is explicitly confirmed.

Example seed shape:

```json
{
  "id": "project-validation-policy",
  "primary": "policies",
  "facets": ["Policy", "TDD", "Project"],
  "cluster": {
    "role": "anchor",
    "anchorId": "project-validation-policy",
    "branches": [
      { "id": "project-validation-turn", "primary": "validation", "facets": ["TDD", "Policy"] },
      { "id": "project-validation-push", "primary": "validation", "facets": ["TDD", "Policy"] }
    ],
    "edges": [
      { "from": "project-validation-policy", "to": "project-validation-turn", "relation": "has-validation" },
      { "from": "project-validation-policy", "to": "project-validation-push", "relation": "has-validation" }
    ]
  }
}
```

The same pattern must support non-test clusters, such as dependency additions, DB migrations, UI accessibility, release policy, or human confirmation boundaries.

## Policy candidates

Project Interview V2 should emit policy candidates using the same stage/level vocabulary as Project Map V2:

Stages:

- `turn`
- `read-only-analysis`
- `edit`
- `commit`
- `push`
- `release`
- `high-risk-mutation`

Levels:

- `discover`
- `recommend`
- `default`
- `warn`
- `block`

Initial candidate rule:

- Default initial level is `discover`.
- If the user explicitly says “normally do X,” initial level may be `recommend` or `default`.
- `warn` and `block` require explicit confirmation or existing canonical policy evidence.

## Output targets

V2 interview should plan writes into canonical records, but not write them without confirmation.

Possible output targets:

- `.lazy-harness/project/profile.xml` or future V2 equivalent
- `.lazy-harness/project/feature-navigation.xml`
- `.lazy-harness/ssot/project-map-taxonomy.md` only for framework taxonomy changes, not host facts
- `.lazy-harness/tests/test-strategy.xml`
- `.lazy-harness/rules/**` or future policy records
- `.lazy-harness/ssot/capabilities.json` only for machine-readable policy/capability bindings
- DDD/BDD/SDD/TDD/ADR/SSOT records as project-map branches

## Adapter boundary

Project Profile V2 is core framework data.

- Pi is the primary future adapter.
- Jcode remains compatibility adapter.
- Adapter-specific wrappers must not own policy semantics.
- The same interview packet should be consumable by Pi and Jcode adapter surfaces.

## Implementation map

- Status: draft design only
- Primary files:
  - `.lazy-harness/spec/platform/project-profile-v2.md` — this SDD contract.
  - `.lazy-harness/plans/project-init-interview-v2-spec.md` — detailed interview plan.
  - `.lazy-harness/tests/project-profile-v2.md` — TDD expectations.
  - `.lazy-harness/fixtures/project-profile-v2/interview-output.json` — desired output packet fixture.
  - `.lazy-harness/spec/platform/project-profile.md` — V1 baseline and V2 pointer.
- Future implementation files, not changed in this design phase:
  - `.lazy-harness/scripts/project-profile.ts`
  - `.lazy-harness/scripts/self-test.py`
- Key future symbols:
  - `ProjectProfileInterviewV2Packet`
  - `buildInterviewV2Result`
  - `validateInterviewV2Packet`
- Protection:
  - current: record/fixture validation + `lazy test`
  - future: self-test fixture after implementation phase

## Layer completeness impact

- DDD: domain-vocabulary question group seeds facts/DDD branches.
- BDD: expectations and user/team behavior are captured through question groups and policy stages.
- SDD: this record defines the V2 output contract.
- TDD: `.lazy-harness/tests/project-profile-v2.md` defines acceptance before runtime code changes.
- ADR: future ADR needed before replacing V1 Project Profile behavior or deprecating rulebook.
- SSOT: capability registry and taxonomy remain the controlled vocabulary sources.
- Planning: Phase 2 design draft only; runtime code changes need user 검수.

## Rule placement

- Rule: Project Interview V2 must seed Project Map clusters and stage-aware project/team policy candidates for Pi-primary, adapter-neutral use, without silently defaulting or writing unconfirmed facts/policies.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/project-profile-v2.md`
- Why not AGENTS.md: this is an SDD output contract, not immediate prompt grammar.
- Why not `.jcode`: V2 is Pi-primary and agent-neutral; Jcode is only compatibility adapter.
- Confirmation: user-approved Phase 2 design draft; no runtime implementation approval yet.

## Discovery capture

- DDD: candidate domain-vocabulary branch discovery.
- BDD: candidate expectation/policy behavior discovery.
- SDD: updated by this SDD.
- TDD: updated by `.lazy-harness/tests/project-profile-v2.md`.
- ADR: none yet.
- SSOT: uses existing taxonomy/capability registry; no SSOT schema change yet.
- Planning: Phase 2 design started.
