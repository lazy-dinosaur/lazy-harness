# Planning — Project Profile V2 Queue Router Implementation Plan

Status: draft-next-slice
Date: 2026-06-17
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/project-profile-v2.md`
Related audit: `.lazy-harness/planning/project-profile-v2-baseline-gap-audit.md`
Related update loop: `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
Related storage: `.lazy-harness/ssot/project-map-record-storage.md`
Related source: `.lazy-harness/scripts/project-profile.ts`

## Rule digest

- Status: active next-slice plan
- Layer: Planning
- Scope: framework-global
- Applies when:
  - implementing the next Project Profile V2 apply/write slice after `interview-v2 --dry-run`
  - designing profile queue entries and routing to DDD/BDD/SDD/TDD/ADR/SSOT/source-links/policy candidates
- Must:
  - keep normal implementation/Figma/domain/API/test knowledge routed directly to canonical layer records/Project Map branches when confirmed
  - use policy candidates only for repeated/stage-specific operating behavior
  - write a typed profile queue first, with every queue item carrying an explicit primary route, optional related routes/facets, and status
  - keep update-loop output as event-ready metadata in the first apply slice
  - avoid direct writes to candidates/rules/capabilities/update-loop events in the first queue-writer slice
- Must not:
  - make policy candidate the universal path for project knowledge
  - append directly to `.lazy-harness/knowledge/candidates.jsonl` from the first V2 apply slice
  - silently drop pending policy candidates or unresolved routed items
  - promote queue items without explicit confirmation or accepted evidence

## Recommended implementation shape

The next slice should be a **typed queue/router**, not a policy-candidate funnel.

```text
interview-v2 dry-run
→ user reviews packet
→ queue writer creates/updates profile queue
→ each queue item has primaryRoute + facets/relatedRoutes + status
→ later promote moves items to canonical targets
```

## Queue item routes

Use one primary route plus optional related routes/facets.

This mirrors Project Map V2's `primary + facets` model:

```text
primaryRoute: the first canonical home/promotion target
facets: additional lenses/layers affected by the item
relatedRoutes: optional secondary queue routes/promotions to create later
```

Available routes include:

- `ddd` — domain terms/facts/business meaning
- `bdd` — user-visible behavior/workflows/Figma behavior
- `sdd` — API/component/design/system contract
- `tdd` — validation/regression/test expectations
- `adr` — trade-off/why decision
- `ssot` — ownership/config/source-of-truth
- `source-link` — implementation/source navigation
- `project-map-branch` — Project Map metadata/branch edge
- `policy-candidate` — repeated/stage-specific operating behavior candidate
- `event-ready-metadata` — future update-loop event draft, not appended yet

Examples:

```json
{
  "primaryRoute": "bdd",
  "facets": ["BDD", "SDD", "TDD"],
  "relatedRoutes": ["sdd", "tdd"],
  "summary": "Figma mobile modal behavior also affects component contract and regression coverage"
}
```

```json
{
  "primaryRoute": "sdd",
  "facets": ["SDD", "BDD"],
  "relatedRoutes": ["bdd"],
  "summary": "Approval API contract also changes visible approval flow expectations"
}
```

## Queue item status

Every item should have a visible status:

- `pending` — needs human/agent review
- `accepted` — approved for promotion
- `rejected` — explicitly not adopted
- `promoted` — already moved to a canonical target
- `superseded` — replaced by a newer queue item or record

## First writer boundary

First implementation should write only the queue file, for example future path:

```text
.lazy-harness/project/profile-queue.json
```

It should not directly write:

- `.lazy-harness/knowledge/candidates.jsonl`
- `.lazy-harness/rules/**`
- `.lazy-harness/ssot/capabilities.json`
- update-loop event logs
- canonical DDD/BDD/SDD/TDD/ADR/SSOT records

Those writes belong to later explicit promote/apply phases.

## Why this resolves the concern

Most human implementation conversation is normal project knowledge, not policy material. The queue only preserves mixed interview/apply output so it does not vanish. Routing happens per item with one primary route and many facets/related routes:

```text
Figma behavior item → primaryRoute=bdd, facets=[BDD, SDD], relatedRoutes=[sdd]
API payload item → primaryRoute=sdd, facets=[SDD, BDD], relatedRoutes=[bdd]
Domain meaning item → primaryRoute=ddd, facets=[DDD, SSOT]
Regression item → primaryRoute=tdd, facets=[TDD, BDD]
Operating behavior item → primaryRoute=policy-candidate, facets=[Policy, SSOT]
Project refresh event draft → primaryRoute=event-ready-metadata, facets=[Project, Evidence]
```

So knowledge can still accumulate naturally in the correct layer records. Policy candidates remain narrow.

## Next concrete slices

1. Define `ProjectProfileQueueV1` schema/fixture and update Project Profile V2 SDD/TDD.
2. Add `project-profile.ts` queue builder from current `interview-v2` packet.
3. Add a first writer mode that requires explicit confirmation and writes only `.lazy-harness/project/profile-queue.json`.
4. Add self-test checks:
   - every queue item has `primaryRoute`, `facets`, `status`, `evidence`, and `promotionTarget`,
   - queue items may have multiple facets/related routes,
   - policy-candidate items are only operating-rule candidates,
   - non-policy knowledge items route to canonical layers,
   - update-loop data is event-ready only,
   - no direct candidates/rules/capabilities/event append occurs.
5. Later, design promote commands for accepted queue items.

## Implementation map

- Status: planning only, implementation pending.
- Primary files:
  - `.lazy-harness/planning/project-profile-v2-queue-router-implementation-plan.md` — this plan.
  - `.lazy-harness/spec/platform/project-profile-v2.md` — SDD to update with queue schema.
  - `.lazy-harness/tests/project-profile-v2.md` — TDD to update with queue checks.
  - `.lazy-harness/scripts/project-profile.ts` — future queue builder/writer implementation.
  - `.lazy-harness/scripts/self-test.py` — future runtime protection.
- Future symbols:
  - `ProjectProfileQueueV1`
  - `ProjectProfileQueueItem`
  - `primaryRoute`
  - `relatedRoutes`
  - `buildProfileQueueV1`
  - `check_project_profile_v2_queue_runtime`

## Rule placement

- Rule: Project Profile V2 apply should proceed through a typed profile queue/router, not through a universal policy-candidate funnel.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/project-profile-v2-queue-router-implementation-plan.md`
- Why not AGENTS.md: this is a Phase 2 implementation plan, not prompt grammar.
- Why not `.jcode`: Project Profile V2 is Pi-primary and adapter-neutral; Jcode is compatibility only.
- Confirmation: inferred from user correction and prior confirmed decisions on 2026-06-17.

## Discovery capture

- DDD: future queue route for domain facts defined.
- BDD: future queue route for Figma/user behavior defined.
- SDD: future queue route for contracts/API/design defined.
- TDD: future queue route for validation/regression defined.
- ADR: future route for trade-off decisions defined.
- SSOT: future route for ownership/source-of-truth and event-ready metadata defined.
- Planning: updated here.
