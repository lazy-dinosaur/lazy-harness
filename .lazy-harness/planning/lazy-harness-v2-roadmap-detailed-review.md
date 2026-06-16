# Lazy-Harness V2 Roadmap Detailed Review

Status: review-draft
Date: 2026-06-16
Layer: Planning
Related roadmap: `.lazy-harness/planning/lazy-harness-v2-implementation-roadmap.md`
Related direction: `.lazy-harness/planning/lazy-harness-v2-direction-purpose.md`
Related context: `.lazy-harness/planning/lazy-harness-v2-evolution-context.md`
Related Project Map: `.lazy-harness/spec/platform/project-map-v2.md`, `.lazy-harness/ssot/project-map-taxonomy.md`
Related Project Profile review: `.lazy-harness/planning/project-profile-v2-design-review.md`
Related Pi: `.lazy-harness/spec/platform/pi-agent-package.md`
Related policy machinery: `.lazy-harness/ssot/capability-registry.md`, `.lazy-harness/ssot/harness-enforcement-policy.md`

## Review scope

This review checks whether the current V2 roadmap still matches the corrected V2 direction:

- V2 center is Project Map / Project Atlas, not Project Interview.
- Project Interview is only an install-time, mid-project adoption, or refresh channel.
- Pi is the primary future adapter; Jcode is compatibility.
- CLI/index/generated views must remain navigation aids, not semantic authority.
- Project/team policies should emerge, evolve, and execute differently by stage.

Runtime implementation is out of scope.

## Overall verdict

The roadmap is directionally good, but it needs a sequencing correction before further implementation.

The most important correction:

> Add a Project Map Update Loop / Knowledge Ingestion Model phase before Project Interview runtime, Policy Machinery runtime, generated map view, or adapter implementation.

The current roadmap still says Phase 2 should redesign Project Interview into the entry point for project understanding and policy discovery. That wording is now stale. Interview is useful, but it is only one ingestion/bootstrap channel. The broader update loop must come first.

## What is good

### 1. The north-star is correct

The roadmap correctly says V2 is not a rewrite for its own sake and should recover the original goal:

```text
maintain an expanding project map and let project/team-specific working rules emerge, change, and become optimized for each project.
```

### 2. Phase 1 was the right first move

Defining Project Map V2 schema/taxonomy before moving files or implementing runtime was correct.

Current Phase 1 is now stronger because it includes:

- one primary category plus facets,
- anchor/branch/edge clusters,
- generated view as cue-only,
- Pi primary / Jcode compatibility,
- no physical folder migration.

### 3. Policy Machinery has the right shape

The proposed policy model has the right concepts:

- scope,
- appliesTo,
- stage,
- level,
- evidence,
- rollback/demotion criteria,
- sourceRecord.

This aligns with the accepted capability registry principle that `kind` and `level` are independent.

### 4. Adapter split is necessary

The roadmap correctly identifies that Jcode must not be core. Pi adapter should consume shared core behavior without duplicating policy logic.

### 5. Lifecycle simplification is necessary

The roadmap correctly recognizes that V1 gates catch real issues but can make the framework feel like prompt grammar compliance instead of project map improvement.

## Main problems

### 1. Phase 2 is stale and too interview-centered

Current roadmap Phase 2 says:

```text
Turn Project Interview into the entry point for both project understanding and project/team policy discovery.
```

This conflicts with the corrected direction.

Correct framing:

```text
Project Interview is one installation/adoption/refresh channel for Project Profile bootstrap, missing-context detection, Project Map seeding, and policy discovery.
```

It should not be implemented next.

### 2. Missing phase: Project Map Update Loop / Knowledge Ingestion Model

The roadmap needs a phase before policy/runtime implementation that answers:

1. What events can create/update Project Map clusters?
2. How does a normal implementation turn update the map?
3. How do user corrections become canonical knowledge?
4. How do validation failures become evidence/validation branches?
5. How do ADR decisions become decision branches?
6. How do document ingestion and source/test inspection update the map?
7. How do policy candidates get promoted/demoted?
8. How do Pi/Jcode adapters consume/update the same core loop?
9. Where does Project Interview fit as one channel?

Without this, Project Interview, Policy Machinery, generated map, and Pi adapter work may each define their own update semantics and drift apart.

### 3. Policy Machinery should depend on the update loop

Phase 3 currently comes after Project Interview. It should come after the update loop model, because policy promotion/demotion is one kind of map update.

Policy Machinery needs to know:

- what creates a candidate,
- what confirms it,
- what evidence promotes/demotes it,
- where policy evidence lives,
- how policy branches connect to feature/topic anchors.

### 4. Generated Project Map view should not be designed before update semantics

Phase 4 generated map view is correct, but if built before update semantics, it risks becoming another attractive-but-shallow navigation layer.

It should be designed after the update loop defines canonical node/edge/candidate/evidence lifecycle.

### 5. Adapter split needs an earlier boundary spec

The Pi/Jcode adapter boundary is Phase 5, but some boundary decisions affect the update loop:

- how Pi observes events,
- how Pi submits evidence,
- how Pi triggers policy resolution,
- how Jcode compatibility maps existing hooks into the same core loop.

Recommended: add an early adapter boundary note inside the Update Loop phase, then keep full adapter implementation in Phase 5.

### 6. Lifecycle simplification depends on policy levels and update loop evidence

Phase 6 is correct, but it should not be planned only as hook simplification. It should be a consequence of:

- stage-aware policy levels,
- evidence availability,
- canonical map update requirements,
- high-risk mutation boundaries.

### 7. Dogfood should happen earlier in slices

Roadmap Phase 7 dogfoods after many phases. Better:

- dogfood a small slice after each major phase,
- especially after update loop design,
- before runtime implementation grows too large.

## Recommended revised order

Recommended corrected order:

```text
0. Freeze V1 learnings and keep repo stable                 [done]
1. Project Map V2 schema/taxonomy/fixture                   [done]
1.5 Project Map Update Loop / Knowledge Ingestion Model      [next]
2. Project Profile / Interview as one bootstrap channel      [draft exists, parked]
3. Policy Machinery V2 stage-aware model                    [after update loop]
4. Generated Project Map view/audit                         [after update loop + policy model]
5. Pi/Jcode adapter core boundary                           [design boundary during 1.5, implementation later]
6. Lifecycle/gate simplification                            [after policy/update loop]
7. Dogfood in small slices                                  [after each phase, not only at end]
8. Physical migration decision                              [last]
```

## Next concrete task

Create the Update Loop / Knowledge Ingestion Model records:

1. `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
2. `.lazy-harness/ssot/project-map-ingestion-sources.md`
3. `.lazy-harness/tests/project-map-update-loop-v2.md`
4. fixture showing events:
   - user correction,
   - implementation change,
   - validation failure,
   - ADR decision,
   - project interview/profile refresh,
   - policy promotion/demotion,
   - Pi adapter event.

This should be design-only first. No runtime code changes until review.

## Questions to settle before implementation

1. Should candidates and canonical nodes share one schema with a `status`, or separate candidate/canonical records?
2. What event types are controlled vocabulary in Phase 1.5?
3. Where do update events live before they become canonical records?
4. When does an update require user confirmation?
5. How does Pi submit evidence/update events without becoming policy authority?
6. How does response/completion audit feed the same update loop?
7. Should project interview output become one event type rather than its own special path?

## Recommended option

A. Amend the roadmap now to insert Phase 1.5 Project Map Update Loop before Project Interview/Policy runtime work.
B. Keep roadmap as-is and only remember this review informally.
C. Skip the update loop and continue with Project Interview implementation.
D. Move directly to Policy Machinery V2.
E. Direct input.

Recommended: A.

## Rule placement

- Rule: The V2 roadmap should insert a Project Map Update Loop / Knowledge Ingestion Model phase before Project Interview runtime, Policy Machinery runtime, generated map views, or adapter implementation.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/lazy-harness-v2-roadmap-detailed-review.md`
- Why not AGENTS.md: this is architecture planning/review, not immediate prompt grammar.
- Why not `.jcode`: V2 is Pi-primary and agent-neutral; Jcode is compatibility only.
- Confirmation: user requested detailed roadmap review; implementation is not approved yet.

## Discovery capture

- DDD: candidate only; update loop must model fact/domain branch updates.
- BDD: candidate only; update loop must model behavior/expectation branch updates.
- SDD: candidate; update-loop SDD is needed next.
- TDD: candidate; update-loop TDD/fixtures are needed next.
- ADR: candidate; revised roadmap sequencing may need future ADR if adopted.
- SSOT: candidate; ingestion source taxonomy SSOT is needed next.
- Planning: updated by this review record.
