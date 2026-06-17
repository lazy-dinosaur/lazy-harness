# Lazy-Harness V2 Implementation Roadmap

Status: draft
Date: 2026-06-16
Layer: Planning
Related direction: `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
Related context: `.lazy-harness/planning/lazy-harness-v2-evolution-context.md`
Related north-star: `.lazy-harness/plans/north-star-accuracy-and-no-regression.md`
Related project profile: `.lazy-harness/plans/project-init-interview-spec.md`, `.lazy-harness/spec/platform/project-profile.md`
Related policy machinery: `.lazy-harness/ssot/capability-registry.md`, `.lazy-harness/decisions/0044-project-operating-rulebook.md`
Related Pi: `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md`, `.lazy-harness/spec/platform/pi-agent-package.md`

## Purpose

This roadmap describes how to move from the current V1/V1.5 lazy-harness into V2 without losing the useful record-first memory, validation, and project policy machinery already built.

V2 is not a rewrite for its own sake. V2 should recover the original goal more cleanly:

> maintain an expanding project map and let project/team-specific working rules emerge, change, and become optimized for each project.

## Planning constraints

- Do not physically move existing DDD/SDD/BDD/TDD/ADR/SSOT records first.
- Do not add another semantic-authority CLI like the rolled-back graph query/path/explain prototype.
- Do not make testing the center of the model; testing is only one policy dimension.
- Do not make Jcode the core runtime assumption; Jcode should become an adapter.
- Keep V1 self-tests green after every phase.
- Prefer compatibility layers and generated views before irreversible structure changes.

## Target mental model

V2 should expose a simple project-map model:

```text
Project Map / Atlas
  facts          # project facts, domain concepts, business rules
  expectations   # user expectations, behavior, requirements
  contracts      # APIs, data, component/system contracts
  decisions      # why/trade-off/ADR
  validation     # tests, checks, evidence, regression protection
  ownership      # SSOT, boundaries, source of truth, forbidden areas
  source links   # code, tests, config, routes, packages
  policies       # project/team working rules and staged enforcement
```

DDD/BDD/SDD/TDD/ADR/SSOT remain useful facets/lenses. A node can have:

```yaml
primary: expectations
facets: [BDD, SDD, TDD]
stages: [turn, commit, push]
links:
  source: [...]
  tests: [...]
  decisions: [...]
  owners: [...]
```

## Phase 0 — Freeze V1 learnings and keep the repo stable

Status: mostly done.

### Goals

- Keep the branch in a known-good state.
- Preserve the lessons from V1 before designing V2.
- Remove misleading experimental surfaces that harm record-first behavior.

### Already completed

- Graph query/path/explain CLI rollback.
- V2 direction record.
- V2 evolution context record.
- Dynamic project/team policy direction clarified.
- Project interview as policy discovery clarified.
- Stage-aware execution clarified.
- Self-test green after each committed direction update.

### Exit criteria

- `.lazy-harness/bin/lazy test` green.
- No active graph query/path/explain command route.
- Direction/context records exist and are committed.

## Phase 1 — Define the V2 Project Map information model

### Goal

Define the canonical V2 knowledge node model before moving folders or rewriting tools.

### Deliverables

1. `.lazy-harness/spec/platform/project-map-v2.md`
   - Node shape.
   - Primary category.
   - Facets.
   - Links.
   - Stage metadata.
   - Evidence metadata.
   - Ownership metadata.

2. `.lazy-harness/ssot/project-map-taxonomy.md`
   - Canonical categories: facts, expectations, contracts, decisions, validation, ownership, source links, policies.
   - Relationship to existing DDD/BDD/SDD/TDD/ADR/SSOT records.
   - Rule that existing layer folders are compatibility/canonical-storage for now, not removed.

3. `.lazy-harness/tests/project-map-v2.md`
   - Regression cases for node schema.
   - Compatibility examples from current records.
   - Forbidden case: generated indexes or CLI output cannot become canonical truth.

4. Optional schema fixture:
   - `.lazy-harness/fixtures/project-map-v2/example-node.json` or XML equivalent.

### Design decisions to settle

- YAML/JSON/XML for node metadata.
- Whether metadata lives in Markdown frontmatter or sidecar index.
- Whether one record has exactly one primary category.
- Whether facets are freeform or controlled vocabulary.

### Recommended answer

- Use **one primary category + many facets**.
- Keep current Markdown/XML records.
- Add lightweight metadata blocks/frontmatter first.
- Generate V2 map views from existing records instead of moving files.

### Exit criteria

- V2 taxonomy is documented.
- At least 5 current records can be represented as V2 nodes without moving files.
- Self-test includes static validation for the schema fixture.

## Phase 1.5 — Project Map Update Loop / Knowledge Ingestion Model

Status: design records added on 2026-06-17; runtime implementation intentionally not added yet.

### Goal

Define how Project Map clusters are created, updated, confirmed, linked to evidence, and consumed by adapters before implementing Project Interview runtime, Policy Machinery runtime, generated map views, or adapter-specific behavior.

### Why this phase exists

Project Map V2 now has anchor/branch/edge clusters, but the roadmap still needs the lifecycle for how those clusters change over time. Without this phase, Project Interview, Policy Machinery, generated map, Pi adapter, and Jcode compatibility could each invent their own update semantics and drift apart.

### Core questions

1. What events can create/update Project Map clusters?
2. How does a normal implementation turn update the map?
3. How do user corrections become canonical knowledge?
4. How do validation failures become evidence/validation branches?
5. How do ADR decisions become decision branches?
6. How do document ingestion and source/test inspection update the map?
7. How do policy candidates get promoted/demoted?
8. How do Pi/Jcode adapters consume/update the same core loop?
9. Where does Project Interview fit as one bootstrap/refresh channel?

### Initial event vocabulary

Design-only Phase 1.5 should cover at least these update event types:

- `user-correction`
- `implementation-change`
- `source-discovery`
- `validation-failure`
- `validation-success`
- `adr-decision`
- `project-profile-refresh`
- `policy-promotion`
- `policy-demotion`
- `document-ingestion`
- `adapter-event`

### Deliverables

1. `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
   - event packet shape
   - candidate/canonical transition model
   - evidence attachment rules
   - adapter-neutral update semantics
   - forbidden semantic-authority fields

2. `.lazy-harness/ssot/project-map-ingestion-sources.md`
   - controlled event source vocabulary
   - event-to-branch mapping
   - confirmation requirements
   - Pi/Jcode adapter source boundary

3. `.lazy-harness/tests/project-map-update-loop-v2.md`
   - regression cases for update events
   - candidate vs canonical transitions
   - no-silent-defaults and no generated-authority checks

4. `.lazy-harness/fixtures/project-map-update-loop-v2/events.json`
   - user correction
   - implementation change
   - validation failure
   - ADR decision
   - project interview/profile refresh
   - policy promotion/demotion
   - Pi adapter event

### Adapter boundary note

Phase 1.5 should include an early adapter boundary note even though full adapter implementation remains Phase 5:

- Pi can submit observations/evidence/update events.
- Jcode can submit compatibility events through existing hooks.
- Neither adapter becomes semantic authority.
- Core update loop owns candidate/canonical transition semantics.

### Exit criteria

- Update-loop SDD, SSOT, TDD, and fixture exist.
- Fixture demonstrates all required event types.
- Static validation protects event vocabulary and forbidden fields.
- No runtime implementation is added before review.
- `lazy test` remains green.

### Current design records

- `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
- `.lazy-harness/ssot/project-map-ingestion-sources.md`
- `.lazy-harness/tests/project-map-update-loop-v2.md`
- `.lazy-harness/fixtures/project-map-update-loop-v2/events.json`

## Phase 2 — Project Profile / Interview as one bootstrap channel

### Goal

Keep Project Interview as an install-time, mid-project adoption, or refresh channel for Project Profile bootstrap, missing-context detection, Project Map seeding, and policy discovery. Do not implement Project Interview runtime until the Phase 1.5 update loop defines shared update semantics.

### Audit status

Baseline/gap audit completed on 2026-06-17: `.lazy-harness/planning/project-profile-v2-baseline-gap-audit.md`.

Next recommended implementation slice is read-only `project-profile.ts --mode interview-v2 --dry-run --format json`; it must preserve all V1 modes and must not write canonical records.

### Current baseline

`project-profile.ts` already supports:

- inspect,
- plan,
- apply,
- interview,
- fill,
- explicit confirmed answers,
- missing artifact detection,
- needs-interview fields.

### V2 changes

Project Interview should be one ingestion channel among many and should discover more than test strategy:

1. Project purpose and constraints.
2. Stack/platform.
3. Folder/source ownership.
4. System design and architecture boundaries.
5. Domain boundaries and vocabulary.
6. Frontend design system and accessibility baseline.
7. Backend API/data/persistence/error/logging/auth boundaries.
8. Testing and validation strategy.
9. Commit/push/PR/review/release workflow.
10. Dependency addition policy.
11. DB/schema migration policy.
12. Security/compliance/privacy policy.
13. Documentation/update policy.
14. Human confirmation boundaries.
15. Agent autonomy/refactor policy.

### Deliverables

1. Update `.lazy-harness/spec/platform/project-profile.md` for V2 output model.
2. Update `.lazy-harness/plans/project-init-interview-spec.md` or create a V2 replacement.
3. Extend `project-profile.ts` output to emit:
   - project map seed,
   - policy/capability seed candidates,
   - stage-aware policy questions,
   - unresolved ambiguity queue.
4. Add `.lazy-harness/tests/project-profile-v2.md`.

### Important behavior

- Interview output is not a frozen preset.
- Initial policies start as `discover` or `recommend` unless user confirms stronger enforcement.
- No silent defaults.
- If a team says “turn = focused checks, push = full gate,” that becomes a stage-aware policy.

### Exit criteria

- Project Interview V2 design is aligned with the update-loop event model.
- `project-profile.ts --mode interview-v2 --dry-run` or equivalent can produce V2 policy questions only after runtime implementation is approved.
- Project/profile refresh output is represented as a Project Map update event, not a special authority path.
- `fill --confirm` writes only confirmed answers.
- Existing Project Profile tests still pass.

## Phase 3 — Unify Rulebook + Capability Registry into Policy Machinery

### Goal

Make project/team rules practical, flexible, and stage-aware without keeping a heavy separate rulebook surface if it does not help. This phase depends on Phase 1.5 because policy promotion/demotion is a Project Map update event.

### Current baseline

- `capabilities.json` supports kinds and levels.
- `lazy capability list/resolve/audit/add` exists.
- `lazy rules list/resolve/audit` exists.
- Rulebook may be too heavy as a separate user-facing layer.

### V2 model

Introduce a policy/capability model with:

```text
Policy
  id
  title
  scope: project | team | framework | adapter
  appliesTo: actions/intents/stages/file areas
  stage: turn | edit | commit | push | release | high-risk-mutation
  level: discover | recommend | default | warn | block
  evidence: observations, user confirmations, successful runs
  rollback/demotion criteria
  sourceRecord
```

### Deliverables

1. `.lazy-harness/spec/platform/policy-machinery-v2.md`
2. `.lazy-harness/ssot/project-policy-registry.md`
3. Update or replace `.lazy-harness/ssot/capabilities.json` schema carefully.
4. Decide whether `.lazy-harness/rules/**` remains:
   - Option A: lightweight human-readable policy docs.
   - Option B: absorbed into policy records and `capabilities.json`.
   - Option C: deprecated after migration.
5. Extend `capability.ts` to understand stages.
6. Make `rulebook.ts` either simpler or deprecated/manual-only.

### Exit criteria

- A project can express: “on turn, focused validation; on push, full validation.”
- A project can express non-test policies: “dependency additions require review” or “DB migrations require explicit confirmation.”
- Resolver output stays advisory unless level is `warn` or `block`.
- No policy is promoted to `block` without user/team confirmation or explicit migration.

## Phase 4 — Build Project Map navigation as a generated view, not a new authority

### Goal

Make the expanding project map useful without creating another graph-query failure mode.

### Approach

- Keep canonical records/source/tests as truth.
- Build only after the update loop defines node/edge/candidate/evidence lifecycle.
- Generate a V2 project map view from records, feature-navigation, implementation maps, graph.jsonl, and capabilities.
- The generated view is a navigation aid only.

### Deliverables

1. `project-map` generator command or script.
2. `.lazy-harness/generated/project-map.json` or equivalent.
3. Map audit command to detect:
   - orphan records,
   - missing source links,
   - missing test links,
   - stale ownership,
   - policies without source records,
   - source files not represented in the map.
4. TDD record protecting generated-map boundaries.

### Guardrails

- The map must say “read real records/source/tests.”
- No intent/risk/required-read semantic classification.
- No automatic hard blocking from generated map alone.

### Exit criteria

- A V2 map can answer “what does this project know about X?” with links, not final judgments.
- At least 10 current features/records appear as linked nodes.
- Generated-map self-test passes.

## Phase 5 — Adapter split: core first, Pi-first runtime, Jcode compatibility

### Goal

Stop treating Jcode as the core. Make Pi a first-class adapter while preserving current Jcode usefulness.

### Current baseline

Pi package exists under:

```text
packages/lazy-harness-pi/
```

It bridges:

- `before_agent_start` → message.received lifecycle hook,
- `tool_call` → tool execute guard,
- `tool_result` → recent evidence cache.

### V2 direction

1. Define core APIs independent of agent runtime:
   - project map read/audit,
   - policy resolve,
   - evidence capture,
   - validation dispatch,
   - record update recommendation.
2. Keep adapter packages thin:
   - Pi adapter maps Pi events/tools to core lifecycle.
   - Jcode adapter maps Jcode hooks/tools to core lifecycle.
3. Avoid duplicating policy logic in adapters.

### Deliverables

1. `.lazy-harness/spec/platform/adapter-core-boundary-v2.md`
2. Update Pi package docs/tests.
3. Jcode wiring marked as compatibility adapter.
4. Smoke tests:
   - Jcode self-test still green.
   - Pi package static test green.
   - Manual Pi smoke checklist.

### Exit criteria

- The same project policy can be resolved from Jcode or Pi.
- Adapter differences are normalized at boundary.
- Pi shell aliases cannot bypass mutation guard.

## Phase 6 — Lifecycle and gate simplification

### Goal

Reduce friction while preserving safety.

### Problem

V1 accumulated many gates. They caught real issues, but can make the agent feel like it is satisfying a prompt grammar rather than improving the project map.

### V2 approach

1. Hard-block only clear high-risk or evidence-missing mutation cases.
2. Make most discovery/policy guidance advisory during normal turns.
3. Keep commit/push validation stronger.
4. Let project policy decide enforcement level.
5. Make reminders shorter and action-oriented.

### Deliverables

1. Lifecycle policy matrix:
   - turn,
   - read-only analysis,
   - edit/write,
   - commit,
   - push,
   - release,
   - destructive/high-risk mutation.
2. Update harness enforcement policy SSOT.
3. Update self-tests for advisory vs blocking behavior.
4. Add dogfood checklist for false positive/false negative rates.

### Exit criteria

- Normal planning conversations no longer trigger unnecessary blocking loops.
- Mutating actions still require evidence/record context.
- Commit/push catches missed record/test updates.

## Phase 7 — Dogfood on current repo, then host projects

### Goal

Prove V2 on lazy-harness itself before pushing to other hosts.

### Steps

1. Use current lazy-harness repo as the first V2 project map pilot.
2. Convert a small subset of records into V2 node metadata.
3. Run project interview V2 on this repo and compare output against existing records.
4. Generate project map view.
5. Resolve policies for common stages:
   - turn planning,
   - focused implementation,
   - commit,
   - push,
   - release-like operation.
6. Fix friction before syncing to external hosts.

### Exit criteria

- V2 map improves rediscovery without replacing real reads.
- Policies are clear enough to explain to a new agent.
- At least one non-test policy is represented and exercised.
- No regression in `lazy test`.

## Phase 8 — Decide final structure and migration path

### Goal

Only after pilots, decide whether to physically change folders.

### Options

A. Keep V1 folders as canonical, add V2 metadata/view.
B. Add `.lazy-harness/records/**` while keeping V1 folder compatibility.
C. Migrate to V2 physical folders after automated migration exists.

### Recommended initial choice

Start with **A**. Do not physically move records until V2 map/schema proves useful.

### Exit criteria

- Migration plan exists.
- Backward compatibility story exists.
- Rollback path exists.
- Old records remain readable.

## Suggested execution order

```text
1. Project Map V2 schema                                      [done]
1.5 Project Map Update Loop / Knowledge Ingestion Model        [next]
2. Project Interview as bootstrap/profile-refresh channel      [draft exists, parked]
3. Policy Machinery V2 stage-aware model                       [after update loop]
4. Generated Project Map view/audit                            [after update loop + policy model]
5. Pi/Jcode adapter boundary cleanup                           [design boundary during 1.5, implementation later]
6. Lifecycle/gate simplification                               [after policy/update loop]
7. Dogfood in small slices on lazy-harness
8. Host pilot and physical migration decision
```

## First concrete next task

Create the Update Loop / Knowledge Ingestion Model records:

1. `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
2. `.lazy-harness/ssot/project-map-ingestion-sources.md`
3. `.lazy-harness/tests/project-map-update-loop-v2.md`
4. `.lazy-harness/fixtures/project-map-update-loop-v2/events.json` showing:
   - user correction,
   - implementation change,
   - validation failure,
   - ADR decision,
   - project interview/profile refresh,
   - policy promotion/demotion,
   - Pi adapter event.

This should be design-only first. No runtime code changes until review.

## Success criteria for V2

V2 is successful if:

- A new agent can recover project understanding faster and more accurately.
- Project/team policies can emerge from interview and real use.
- Policies can differ by stage and enforcement level.
- Testing is one policy dimension, not the center of the framework.
- Pi can run the same core behavior as Jcode through an adapter.
- Generated maps help navigation without becoming semantic authority.
- Record/source/test truth remains canonical.
- The project becomes clearer after work, not more cluttered.

## Risks

| Risk | Mitigation |
|---|---|
| V2 becomes another heavy taxonomy | Keep simple user-facing Project Map categories and compatibility with V1 records. |
| Generated map repeats graph CLI mistake | Explicit cue-only boundary, no semantic authority, no hard blocking from generated map alone. |
| Policy machinery becomes test-centric | Include non-test policy fixtures from the start. |
| Rulebook remains unused | Decide in Phase 3 whether to simplify, absorb, or deprecate. |
| Pi adapter duplicates Jcode logic | Define core/adapter boundary before adding Pi-specific policy logic. |
| Physical migration breaks records | Delay folder moves until generated view is proven. |

## Rule placement

- Rule: Lazy-Harness V2 should be implemented through a staged roadmap: define Project Map schema, define the Project Map Update Loop / Knowledge Ingestion Model, keep Project Interview as one bootstrap/profile-refresh channel, then build policy machinery, generated map views, adapter boundaries, lifecycle simplification, dogfood, and migration decisions.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`
- Why not AGENTS.md: this is an implementation roadmap and architecture plan, not immediate prompt grammar.
- Why not `.jcode`: V2 explicitly reduces Jcode coupling and applies to the shared framework.
- Confirmation: user-requested detailed plan; not implementation approval.

## Discovery capture

- DDD: candidate only; update loop must model fact/domain branch updates.
- BDD: candidate only; update loop must model expectation/behavior branch updates and stage-aware policy behavior.
- SDD: candidate; Phase 1.5 requires a new update-loop SDD before runtime work.
- TDD: candidate; Phase 1.5 requires tests/fixtures before code changes.
- ADR: candidate; major V2 trade-offs need ADR once user approves direction.
- SSOT: candidate; project-map ingestion source taxonomy and policy registry need SSOT records.
- Planning: updated by this roadmap amendment.
