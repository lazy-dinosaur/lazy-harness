# SDD — Project Profile V2 / Project Interview Policy Discovery

Status: active-runtime-promote-v2-candidate-row-writer-implemented
Date: 2026-06-16
Updated: 2026-06-17
Layer: SDD
Related SDD: `.lazy-harness/spec/platform/project-profile.md`, `.lazy-harness/spec/platform/project-map-v2.md`
Related plan: `.lazy-harness/plans/project-init-interview-v2-spec.md`, `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`
Related TDD: `.lazy-harness/tests/project-profile-v2.md`
Related SSOT: `.lazy-harness/ssot/project-map-taxonomy.md`, `.lazy-harness/ssot/capability-registry.md`
Related ADR: `.lazy-harness/decisions/0044-project-operating-rulebook.md`

## Rule digest

- Status: active-runtime-promote-v2-candidate-row-writer-implemented
- Layer: SDD
- Scope: framework-global
- Applies when:
  - redesigning Project Interview as an install-time, mid-project adoption, or refresh channel for V2 Project Map seeds and project/team policy discovery
  - extending `project-profile.ts` interview/plan/fill behavior
  - using `project-profile.ts --mode interview-v2 --dry-run --format json`
  - using `project-profile.ts --mode queue-v2 --dry-run|--confirm --format json`
  - using `project-profile.ts --mode promote-v2 --item <id> --dry-run|--confirm --format json`
  - designing Pi-primary adapter output for project profile/interview data
- Must:
  - treat Project Interview as project understanding + policy discovery, not a test-strategy wizard
  - emit Project Map cluster seed candidates that use Project Map V2 anchor/branch/edge semantics
  - emit policy/capability seed candidates with stage-aware levels
  - keep initial policy levels at `discover` or `recommend` unless user/team explicitly confirms stronger enforcement
  - preserve no-silent-defaults behavior
  - keep Pi as primary future adapter and Jcode as compatibility adapter
  - keep existing Project Profile V1 behavior compatible until a migration is explicitly approved
  - keep `interview-v2` read-only and dry-run only
  - keep `queue-v2 --confirm` limited to `.lazy-harness/project/profile-queue.json`
  - keep `promote-v2 --dry-run` preview-only and `status=accepted` required
  - keep the queue-status writer limited to accepted queue items
  - let `promotionTarget.kind=record` create deterministic `needs-interview` canonical record skeletons
  - let `promotionTarget.kind=candidate-row` append stable rows to `.lazy-harness/knowledge/candidates.jsonl`
  - keep rulebook/capability/update-loop writers separated and deferred by target kind until explicitly implemented
- Must not:
  - write confirmed project facts, policies, or block-level capabilities without user-confirmed answers
  - let `promote-v2 --dry-run` mutate the queue or write canonical records/rules/capabilities/update-loop events
  - let the record writer assert confirmed project facts without explicit answers
  - let candidate-row writer promote candidate rows to canonical layer docs
  - let rulebook/capability/update-loop target writers create/update rules/capabilities/update-loop events in the candidate-row writer slice
  - treat interview output as a frozen preset
  - promote a policy to `warn` or `block` only because a generated fixture or adapter suggests it
  - make tests the center of the policy model
- Record completion:
  - changes update this SDD, V2 interview/queue/promote plan, TDD, fixtures, `project-profile.ts`, self-test, manifest sync entries, and graph rows together.

## Purpose

Project Profile V2 treats Project Interview as an installation/adoption/refresh channel for:

1. project understanding,
2. Project Map cluster seed discovery,
3. project/team policy discovery,
4. stage-aware capability candidates,
5. unresolved ambiguity capture.

The output should help a Pi-first or Jcode-compatible agent bootstrap or repair the project profile: identify missing parts, capture system design and folder/source structure, record tech stack and ownership, define basic project/team conventions, and start future work from the project map instead of guessing file edits or applying universal workflow defaults.

Project Interview is not the V2 core engine. The core remains Project Map, policy machinery, evidence/validation loop, and adapter-neutral update paths. Interview is one structured channel for creating or refreshing the profile when lazy-harness is installed on a new project, introduced into an existing project midstream, or asked to audit/profile missing project context.

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

Phase 2 design must not break this baseline. The first runtime slice is now implemented as read-only `project-profile.ts --mode interview-v2 --dry-run --format json`; broader write/apply behavior still needs separate approval.

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

When used for installation, mid-project adoption, or project profile refresh, Project Interview V2 should cover at least these dimensions:

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

Plain-language role:

- A policy candidate is a **draft suggestion card**, not a rule.
- It says: “The project might want a rule here. Should we confirm it?”
- It is safe to generate from interview answers or source evidence because it does not change agent behavior by itself.
- If confirmed as an operating policy, the human-readable rule belongs in `.lazy-harness/rules/**`.
- If that rule should steer commands/actions, `.lazy-harness/ssot/capabilities.json` links it to machine-readable actions and an explicit level.
- Therefore the usual path is: `policy candidate → confirmed rulebook record → optional capability binding`.

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

Candidate creation criteria:

- Create a policy candidate when interview/source/user evidence says how the agent or project should behave repeatedly, conditionally, or at a lifecycle stage.
- Typical signals: “always”, “normally”, “before push”, “when editing DB/schema”, “must ask”, “must not”, “prefer X”, “avoid Y”, “needs approval”, security/privacy/compliance constraints, dependency/tooling rules, validation gates, release gates, or ownership boundaries.
- Do not create a policy candidate for a one-off task instruction, a plain factual fact, an API/component contract, a bug report, or an unresolved question with no proposed operating behavior.
- If evidence is ambiguous, keep it as `unresolvedAmbiguities` or `discover`, not `warn`/`block`.
- A candidate must carry enough context for a human to decide: source question/evidence, suggested stage, suggested level, and intended behavior.

No-silent-pass-through rule:

- Future `interview-v2 apply` must not drop policy candidates silently.
- Confirmed or pending policy candidates should first be written to a profile queue file with status such as `pending`, `accepted`, `rejected`, or `promoted`.
- The queue summary should show remaining pending candidates so humans/agents can revisit them.
- Promotion from the queue follows: `policy candidate → confirmed rulebook record → optional capability binding`.
- `promote-v2 --dry-run` previews one `status=accepted` item only, exposes confirmation-gated `plannedWrites`, and previews the queue status transition to `promoted` without writing it.
- Update-loop event append remains a later confirmed promote step; the first promote slice only previews event-ready/update-loop promotion plans.

Non-policy project knowledge routing:

- Policy candidates are a narrow subset of project knowledge, not a gate for all knowledge.
- Implementation details, Figma/design details, product branches, domain terms, behavior expectations, API/component contracts, validation cases, and source links should accumulate through their normal canonical layer records and Project Map branches.
- Examples:
  - Figma/UI behavior → BDD/SDD plus Project Map `expectations` or `contracts` branch.
  - API/component shape → SDD plus Project Map `contracts` branch.
  - business/domain vocabulary → DDD plus Project Map `facts` branch.
  - test/regression expectation → TDD plus Project Map `validation` branch.
  - implementation navigation/source ownership → SSOT/source-links branch or implementation map.
- Queue routing should mirror Project Map V2: one category-first `primaryRoute` plus many layer `facets` and related Project Map routes.
- `primaryRoute` uses Project Map categories such as `facts`, `expectations`, `contracts`, `validation`, `decisions`, `ownership`, `source-links`, and `policies`, not layer/folder names such as `bdd` or `sdd`.
- `facets` uses layer/lens labels such as `BDD`, `SDD`, and `TDD`.
- Example: Figma/UI behavior may use `primaryRoute=expectations`, `facets=[BDD, SDD, TDD]`, and `relatedRoutes=[contracts, validation]` when the same item affects visible behavior, component contract, and regression coverage.
- Only repeated/stage-specific operating behavior becomes a policy candidate.
- Therefore natural implementation/design conversation should become layered project knowledge directly when confirmed, while only “how we should repeatedly work” becomes policy-candidate material.

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

- Status: promote-v2 candidate-row target writer slice implemented.
- Primary files:
  - `.lazy-harness/spec/platform/project-profile-v2.md` — this SDD contract.
  - `.lazy-harness/plans/project-init-interview-v2-spec.md` — detailed interview plan.
  - `.lazy-harness/tests/project-profile-v2.md` — TDD expectations.
  - `.lazy-harness/fixtures/project-profile-v2/interview-output.json` — desired interview packet fixture.
  - `.lazy-harness/fixtures/project-profile-v2/profile-queue.json` — category-first queue-v2 output fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-preview.json` — accepted-item promote-v2 dry-run preview fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-confirm.json` — accepted-item promote-v2 confirm queue-status result fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-record.json` — accepted record-target promote-v2 result fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-candidate-row.json` — accepted candidate-row promote-v2 result fixture.
  - `.lazy-harness/spec/platform/project-profile.md` — V1 baseline and V2 pointer.
  - `.lazy-harness/scripts/project-profile.ts` — implements read-only `interview-v2 --dry-run`, typed `queue-v2` queue output/writer, `promote-v2 --dry-run` preview, queue-status promotion, record target writer, and candidate-row writer.
  - `.lazy-harness/scripts/self-test.py` — protects V2 interview/queue/promote runtime packets, write boundaries, and V1 backward compatibility.
- Key symbols:
  - `project-profile.ts#ProjectProfileInterviewV2Packet`
  - `project-profile.ts#buildInterviewV2Result`
  - `project-profile.ts#renderInterviewV2Md`
  - `project-profile.ts#ProjectProfileQueueV1`
  - `project-profile.ts#ProjectProfileQueueItem`
  - `project-profile.ts#buildProfileQueueV1FromInterviewV2` — category-first queue route builder
  - `project-profile.ts#buildProfileQueueV1`
  - `project-profile.ts#applyProfileQueue`
  - `project-profile.ts#ProjectProfilePromoteV2Preview`
  - `project-profile.ts#ProjectProfilePromoteV2Result`
  - `project-profile.ts#ProjectProfilePromotionTargetEffect`
  - `project-profile.ts#ProjectProfileRecordPromotionWrite`
  - `project-profile.ts#ProjectProfileCandidatePromotionWrite`
  - `project-profile.ts#readProfileQueue`
  - `project-profile.ts#buildPromoteV2Preview`
  - `project-profile.ts#buildRecordPromotionWrite`
  - `project-profile.ts#buildCandidatePromotionWrite`
  - `project-profile.ts#applyPromoteV2`
  - `project-profile.ts#renderPromoteV2Md`
  - `self-test.py#check_project_profile_v2_runtime`
  - `self-test.py#check_project_profile_v2_queue_runtime`
- Protection:
  - `bun .lazy-harness/scripts/project-profile.ts --mode interview-v2 --dry-run --format json`
  - `bun .lazy-harness/scripts/project-profile.ts --mode queue-v2 --dry-run --format json`
  - `bun .lazy-harness/scripts/project-profile.ts --mode queue-v2 --confirm --format json`
  - `bun .lazy-harness/scripts/project-profile.ts --mode promote-v2 --item <accepted-id> --dry-run --format json`
  - `bun .lazy-harness/scripts/project-profile.ts --mode promote-v2 --item <accepted-id> --confirm --format json`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`
- Runtime boundary:
  - `interview-v2` requires `--dry-run`.
  - `interview-v2 --confirm` is blocked.
  - `queue-v2 --confirm` writes only `.lazy-harness/project/profile-queue.json`.
  - `promote-v2 --dry-run` rejects non-accepted queue items and writes nothing.
  - `promote-v2 --confirm` rejects non-accepted queue items, writes queue status/promoted metadata, writes only deterministic `needs-interview` record targets for `promotionTarget.kind=record`, and appends only stable candidate rows for `promotionTarget.kind=candidate-row`.
  - No rulebook, capability, or update-loop event append occurs in this slice.

## Layer completeness impact

- DDD: domain-vocabulary question group seeds facts/DDD branches.
- BDD: expectations and user/team behavior are captured through question groups and policy stages.
- SDD: this record defines the V2 interview and queue output contracts.
- TDD: `.lazy-harness/tests/project-profile-v2.md`, `self-test.py#check_project_profile_v2_runtime`, and `self-test.py#check_project_profile_v2_queue_runtime` protect the interview, queue, promote preview, confirmed queue-status promotion, record target writer, and candidate-row writer runtime packets.
- ADR: future ADR needed before replacing V1 Project Profile behavior or deprecating rulebook.
- SSOT: capability registry and taxonomy remain the controlled vocabulary sources.
- Planning: Phase 2 interview dry-run, queue-v2 writer, promote-v2 dry-run preview, confirmed queue-status promotion, record target writer, and candidate-row writer slices are implemented; rulebook/capability/update-loop target writers remain future work.

## Rule placement

- Rule: Project Interview V2 must seed Project Map clusters and stage-aware project/team policy candidates for Pi-primary, adapter-neutral use, without silently defaulting or writing unconfirmed facts/policies.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/project-profile-v2.md`
- Why not AGENTS.md: this is an SDD output contract, not immediate prompt grammar.
- Why not `.jcode`: V2 is Pi-primary and agent-neutral; Jcode is only compatibility adapter.
- Confirmation: user-approved Phase 2 design draft, first read-only runtime slice, queue-v2 writer slice, promote-v2 dry-run preview, and A→B→C confirmed-writer sequence on 2026-06-17.

## Discovery capture

- DDD: candidate domain-vocabulary branch discovery.
- BDD: candidate expectation/policy behavior discovery.
- SDD: updated by this SDD and implemented by `project-profile.ts#buildInterviewV2Result`, `project-profile.ts#buildProfileQueueV1FromInterviewV2`, `project-profile.ts#buildPromoteV2Preview`, `project-profile.ts#buildRecordPromotionWrite`, `project-profile.ts#buildCandidatePromotionWrite`, and `project-profile.ts#applyPromoteV2`.
- TDD: updated by `.lazy-harness/tests/project-profile-v2.md`, `self-test.py#check_project_profile_v2_runtime`, and `self-test.py#check_project_profile_v2_queue_runtime`.
- ADR: none yet; ADR required only before replacing V1 mode semantics.
- SSOT: uses existing taxonomy/capability registry and Project Map ingestion source vocabulary; no SSOT schema change.
- Planning: Phase 2 interview dry-run, category-first queue-v2 writer, promote-v2 preview, confirmed queue-status promotion, record target writer, and candidate-row writer slices implemented; rulebook/capability/update-loop target writers deferred.
