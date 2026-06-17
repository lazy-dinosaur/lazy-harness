# Planning — Project Profile V2 Queue Router Implementation Plan

Status: implemented-queue-v2
Date: 2026-06-17
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/project-profile-v2.md`
Related audit: `.lazy-harness/planning/project-profile-v2-baseline-gap-audit.md`
Related update loop: `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
Related storage: `.lazy-harness/ssot/project-map-record-storage.md`
Related source: `.lazy-harness/scripts/project-profile.ts`

## Rule digest

- Status: implemented queue-v2 runtime slice
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

## Proposed queue schema

This is the next implementation target. It remains planning-level until SDD/TDD/fixture are updated in the implementation slice.

```ts
type ProjectProfileQueueV1 = {
  schemaVersion: 'project-profile-queue/v1'
  sourcePacket: {
    schemaVersion: 'project-profile-interview-v2/v1'
    generatedAt: string
    mode: 'interview-v2'
  }
  createdAt: string
  updatedAt: string
  dryRunSource: true
  items: ProjectProfileQueueItem[]
  summary: {
    total: number
    pending: number
    byPrimaryRoute: Record<string, number>
    pendingPolicyCandidates: number
    pendingEventReadyMetadata: number
  }
}

type ProjectProfileQueueItem = {
  id: string
  status: 'pending' | 'accepted' | 'rejected' | 'promoted' | 'superseded'
  primaryRoute: 'ddd' | 'bdd' | 'sdd' | 'tdd' | 'adr' | 'ssot' | 'source-link' | 'project-map-branch' | 'policy-candidate' | 'event-ready-metadata'
  facets: Array<'DDD' | 'BDD' | 'SDD' | 'TDD' | 'ADR' | 'SSOT' | 'Policy' | 'Project' | 'Source' | 'Evidence'>
  relatedRoutes: string[]
  source: {
    kind: 'question-group' | 'project-map-seed' | 'policy-candidate' | 'unresolved-ambiguity' | 'proposed-write' | 'update-loop'
    id: string
  }
  summary: string
  evidence: Array<{ kind: string; path?: string; summary: string }>
  promotionTarget: {
    kind: 'record' | 'project-map-branch' | 'rulebook' | 'capability-binding' | 'candidate-row' | 'update-loop-event' | 'queue-only'
    path?: string
    requiresConfirmation: true
  }
}
```

Minimum invariant:

```text
Every item has status + primaryRoute + facets + source + evidence + promotionTarget.
```

This lets one item carry many layer implications without losing the first canonical home.

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

## Builder mapping plan

Build queue items from the existing `interview-v2 --dry-run` packet as follows:

| Packet source | Queue item route | Purpose |
|---|---|---|
| `questionGroups[]` | one or more of `ddd`/`bdd`/`sdd`/`tdd`/`ssot`/`adr` | Preserve project knowledge questions as layer-routed pending items. |
| `projectMapSeeds[]` | `project-map-branch` | Preserve anchor/branch/edge metadata without writing canonical Project Map output. |
| `policyCandidates[]` | `policy-candidate` | Preserve only repeated/stage-specific operating behavior candidates. |
| `unresolvedAmbiguities[]` | route by ambiguity topic, often `ssot` or `policy-candidate` | Keep ambiguous decisions visible. |
| `proposedWrites[]` | target layer route or `queue-only` | Record future write targets, still requiring confirmation. |
| `updateLoop` | `event-ready-metadata` | Preserve future `project-profile-refresh` event draft without appending it. |

The builder should be deterministic and idempotent: the same source packet should produce the same queue item ids.

## Writer mode plan

First writer command should be explicit, for example:

```bash
bun .lazy-harness/scripts/project-profile.ts --mode queue-v2 --dry-run --format json
bun .lazy-harness/scripts/project-profile.ts --mode queue-v2 --confirm --format json
```

Boundary:

- `queue-v2 --dry-run` prints the queue only.
- `queue-v2 --confirm` writes only `.lazy-harness/project/profile-queue.json`.
- Existing V1 `inspect/plan/apply/interview/fill` behavior remains unchanged.
- `interview-v2` remains read-only and requires `--dry-run`.

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

## Implemented concrete slices

1. Define `ProjectProfileQueueV1` schema/fixture and update Project Profile V2 SDD/TDD.
2. Add `project-profile.ts` queue builder from current `interview-v2` packet.
3. Add `queue-v2 --dry-run` and `queue-v2 --confirm` writer mode that writes only `.lazy-harness/project/profile-queue.json`.
4. Add self-test checks:
   - every queue item has `primaryRoute`, `facets`, `status`, `evidence`, and `promotionTarget`,
   - queue items may have multiple facets/related routes,
   - policy-candidate items are only operating-rule candidates,
   - non-policy knowledge items route to canonical layers,
   - update-loop data is event-ready only,
   - no direct candidates/rules/capabilities/event append occurs.
5. Run validation:
   - JSON parse fixture and emitted queue packet,
   - focused `project-profile` CLI tests,
   - `python3 .lazy-harness/scripts/self-test.py --scope framework`,
   - `.lazy-harness/bin/lazy test`.
6. Later, design promote commands for accepted queue items.

## Implementation map

- Status: queue-v2 runtime slice implemented.
- Primary files:
  - `.lazy-harness/planning/project-profile-v2-queue-router-implementation-plan.md` — this plan.
  - `.lazy-harness/spec/platform/project-profile-v2.md` — SDD to update with queue schema.
  - `.lazy-harness/tests/project-profile-v2.md` — TDD to update with queue checks.
  - `.lazy-harness/scripts/project-profile.ts` — queue builder/writer implementation.
  - `.lazy-harness/scripts/self-test.py` — runtime protection.
  - `.lazy-harness/fixtures/project-profile-v2/profile-queue.json` — queue-v2 fixture.
- Implemented symbols:
  - `ProjectProfileQueueV1`
  - `ProjectProfileQueueItem`
  - `primaryRoute`
  - `relatedRoutes`
  - `buildProfileQueueV1FromInterviewV2`
  - `buildProfileQueueV1`
  - `applyProfileQueue`
  - `renderProfileQueueMd`
  - `check_project_profile_v2_queue_runtime`

## Validation checklist for next implementation

- `queue-v2 --dry-run` emits `schemaVersion == "project-profile-queue/v1"`.
- `queue-v2 --confirm` writes only `.lazy-harness/project/profile-queue.json`.
- The output includes at least one non-policy layer-routed item and one policy-candidate item.
- At least one item demonstrates `primaryRoute` with multiple `facets`/`relatedRoutes`.
- All `promotionTarget.requiresConfirmation` values are true.
- No direct append/write occurs to candidates/rules/capabilities/update-loop events.
- V1 commands still pass existing tests.
- `interview-v2 --confirm` remains blocked.
- Full `lazy test` remains green.

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
- Planning: queue-v2 implementation completed here; next planning target is promote commands for accepted queue items.
