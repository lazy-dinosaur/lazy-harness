# Planning — Project Profile V2 Queue Router Implementation Plan

Status: implemented-promote-v2-update-loop-event-writer
Date: 2026-06-17
Layer: Planning
Related SDD: `.lazy-harness/spec/platform/project-profile-v2.md`
Related audit: `.lazy-harness/planning/project-profile-v2-baseline-gap-audit.md`
Related update loop: `.lazy-harness/spec/platform/project-map-update-loop-v2.md`
Related storage: `.lazy-harness/ssot/project-map-record-storage.md`
Related source: `.lazy-harness/scripts/project-profile.ts`

## Rule digest

- Status: implemented queue-v2 runtime, promote-v2 dry-run preview, confirmed queue-status writer, record target writer, candidate-row writer, rulebook writer, capability-binding writer, and update-loop-event writer slices
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
  - keep `promote-v2 --dry-run` preview-only: one `status=accepted` item, writes nothing
  - keep the first confirmed promote writer limited to queue status metadata in `.lazy-harness/project/profile-queue.json`
  - let the record target writer create deterministic `needs-interview` canonical records only for `promotionTarget.kind=record`
  - let the candidate-row target writer append stable rows to `.lazy-harness/knowledge/candidates.jsonl` only for `promotionTarget.kind=candidate-row`
  - let the rulebook target writer create deterministic `Status: draft` / `Level: discover` entries under `.lazy-harness/rules/**` only for `promotionTarget.kind=rulebook`
  - let the capability-binding target writer upsert deterministic `discover` checklist capabilities into `.lazy-harness/ssot/capabilities.json` only for `promotionTarget.kind=capability-binding`
  - let the update-loop-event target writer append stable non-canonical Project Map update event rows to `.lazy-harness/knowledge/project-map-update-events.jsonl` only for `promotionTarget.kind=update-loop-event`
  - separate target-specific canonical writers as explicit deferred effects for `record`, `project-map-branch`, `rulebook`, `capability-binding`, `candidate-row`, `update-loop-event`, and `queue-only`
- Must not:
  - make policy candidate the universal path for project knowledge
  - append directly to `.lazy-harness/knowledge/candidates.jsonl` from the first V2 apply slice
  - silently drop pending policy candidates or unresolved routed items
  - promote queue items without explicit confirmation or accepted evidence
  - let dry-run promotion mutate `.lazy-harness/project/profile-queue.json` or canonical targets
  - let the capability-binding writer create recommend/default/warn/block capabilities or hook enforcement
  - let non-update-loop target writers create/update update-loop event rows
  - let update-loop event rows become canonical truth without record-write policy
  - write confirmed project facts into record targets; generated record targets must remain `needs-interview` skeletons until answered

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

Use one category-first primary route plus optional related routes/facets. `primaryRoute` is not a layer/folder name.

This mirrors Project Map V2's `primary + facets` model:

```text
primaryRoute: the Project Map category or technical holding route for the item
facets: additional lenses/layers affected by the item
relatedRoutes: optional secondary Project Map category routes/promotions to create later
```

Available routes include:

- `facts` — domain terms/facts/business meaning
- `expectations` — user-visible behavior/workflows/Figma behavior
- `contracts` — API/component/design/system contract
- `validation` — validation/regression/test expectations
- `decisions` — trade-off/why decision
- `ownership` — ownership/config/source-of-truth
- `source-links` — implementation/source navigation and Project Map branch/link metadata
- `policies` — repeated/stage-specific operating behavior candidate or policy target
- `event-ready-metadata` — future update-loop event draft, not appended yet
- `queue-only` — queue holding item with no canonical promotion yet

Examples:

```json
{
  "primaryRoute": "expectations",
  "facets": ["BDD", "SDD", "TDD"],
  "relatedRoutes": ["contracts", "validation"],
  "summary": "Figma mobile modal behavior also affects component contract and regression coverage"
}
```

```json
{
  "primaryRoute": "contracts",
  "facets": ["SDD", "BDD"],
  "relatedRoutes": ["expectations"],
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

This schema is now implemented by `project-profile.ts#ProjectProfileQueueV1` and protected by `self-test.py#check_project_profile_v2_queue_runtime`.

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
  primaryRoute: 'facts' | 'expectations' | 'contracts' | 'validation' | 'decisions' | 'ownership' | 'source-links' | 'policies' | 'event-ready-metadata' | 'queue-only'
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

This lets one item carry many layer implications without losing the first Project Map category home. Layer/folder labels stay in `facets` and actual file targets stay in `promotionTarget`.

## First writer boundary

The first implementation writes only the queue file:

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
| `questionGroups[]` | one or more of `facts`/`expectations`/`contracts`/`validation`/`ownership`/`decisions`/`policies` | Preserve project knowledge questions as category-routed pending items. Layer labels stay in `facets`. |
| `projectMapSeeds[]` | `source-links` | Preserve anchor/branch/edge metadata without writing canonical Project Map output. |
| `policyCandidates[]` | `policies` | Preserve only repeated/stage-specific operating behavior candidates; source kind remains `policy-candidate`. |
| `unresolvedAmbiguities[]` | route by ambiguity topic, often `ownership`, `policies`, or `queue-only` | Keep ambiguous decisions visible. |
| `proposedWrites[]` | Project Map category route or `queue-only` | Record future write targets, still requiring confirmation. |
| `updateLoop` | `event-ready-metadata` | Preserve future `project-profile-refresh` event draft without appending it. |

The builder should be deterministic and idempotent: the same source packet should produce the same queue item ids. It should use Project Map categories for `primaryRoute`, not V1 layer/folder names.

## Writer mode plan

First writer command should be explicit, for example:

```bash
bun .lazy-harness/scripts/project-profile.ts --mode queue-v2 --dry-run --format json
bun .lazy-harness/scripts/project-profile.ts --mode queue-v2 --confirm --format json
bun .lazy-harness/scripts/project-profile.ts --mode promote-v2 --item <accepted-id> --dry-run --format json
bun .lazy-harness/scripts/project-profile.ts --mode promote-v2 --item <accepted-id> --confirm --format json
```

Boundary:

- `queue-v2 --dry-run` prints the queue only.
- `queue-v2 --confirm` writes only `.lazy-harness/project/profile-queue.json`.
- `promote-v2 --dry-run` reads `.lazy-harness/project/profile-queue.json`, rejects non-accepted items, emits a preview packet, and writes nothing.
- `promote-v2 --confirm` re-reads `.lazy-harness/project/profile-queue.json`, rejects non-accepted items, marks exactly one item `promoted`, records promoted metadata/effects, and writes only the queue file.
- Target-specific canonical writers remain deferred and separated by target kind.
- Existing V1 `inspect/plan/apply/interview/fill` behavior remains unchanged.
- `interview-v2` remains read-only and requires `--dry-run`.

## Why this resolves the concern

Most human implementation conversation is normal project knowledge, not policy material. The queue only preserves mixed interview/apply output so it does not vanish. Routing happens per item with one primary route and many facets/related routes:

```text
Figma behavior item → primaryRoute=expectations, facets=[BDD, SDD], relatedRoutes=[contracts]
API payload item → primaryRoute=contracts, facets=[SDD, BDD], relatedRoutes=[expectations]
Domain meaning item → primaryRoute=facts, facets=[DDD, SSOT]
Regression item → primaryRoute=validation, facets=[TDD, BDD]
Operating behavior item → primaryRoute=policies, facets=[Policy, SSOT]
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
6. Add `promote-v2 --dry-run` preview for one accepted queue item. The preview includes confirmation-gated planned writes and an accepted→promoted queue-update preview, but no queue/canonical mutation.
7. Add `promote-v2 --confirm` queue-status writer for one accepted queue item. The writer re-checks accepted state, writes only `.lazy-harness/project/profile-queue.json`, and records target-specific deferred effects without canonical target mutation.
8. Implement the `record` target writer first. It may create deterministic `needs-interview` canonical records from accepted queue items with `promotionTarget.kind=record`; it must not assert confirmed project facts.
9. Implement the `candidate-row` target writer. It may append stable, id-deduped rows to `.lazy-harness/knowledge/candidates.jsonl`; it must not promote those rows to canonical layer docs.
10. Implement the `rulebook` target writer. It may create deterministic draft/discover rulebook entries under `.lazy-harness/rules/**`; it must not create capability bindings or active warn/block rules.
11. Implement the `capability-binding` target writer. It may upsert deterministic `discover`/`checklist` capability entries to `.lazy-harness/ssot/capabilities.json`; it must not create enforcement, hooks, or warn/block/default levels.
12. Later, implement the `update-loop-event` target writer.

## Implementation map

- Status: promote-v2 capability-binding target writer slice implemented.
- Primary files:
  - `.lazy-harness/planning/project-profile-v2-queue-router-implementation-plan.md` — this plan.
  - `.lazy-harness/spec/platform/project-profile-v2.md` — SDD to update with queue schema.
  - `.lazy-harness/tests/project-profile-v2.md` — TDD to update with queue checks.
  - `.lazy-harness/scripts/project-profile.ts` — queue builder/writer implementation.
  - `.lazy-harness/scripts/self-test.py` — runtime protection.
  - `.lazy-harness/fixtures/project-profile-v2/profile-queue.json` — queue-v2 fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-preview.json` — promote-v2 preview fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-confirm.json` — promote-v2 confirm queue-status result fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-record.json` — promote-v2 record writer result fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-candidate-row.json` — promote-v2 candidate-row writer result fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-rulebook.json` — promote-v2 rulebook writer result fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-capability-binding.json` — promote-v2 capability-binding writer result fixture.
- Implemented symbols:
  - `ProjectProfileQueueV1`
  - `ProjectProfileQueueItem`
  - `primaryRoute`
  - `relatedRoutes`
  - `buildProfileQueueV1FromInterviewV2`
  - `buildProfileQueueV1`
  - `applyProfileQueue`
  - `ProjectProfilePromoteV2Preview`
  - `ProjectProfilePromoteV2Result`
  - `ProjectProfilePromotionTargetEffect`
  - `ProjectProfileRecordPromotionWrite`
  - `ProjectProfileCandidatePromotionWrite`
  - `ProjectProfileRulebookPromotionWrite`
  - `ProjectProfileCapabilityPromotionWrite`
  - `buildPromoteV2Preview`
  - `buildRecordPromotionWrite`
  - `buildCandidatePromotionWrite`
  - `buildRulebookPromotionWrite`
  - `buildCapabilityPromotionWrite`
  - `applyPromoteV2`
  - `renderPromoteV2Md`
  - `renderProfileQueueMd`
  - `check_project_profile_v2_queue_runtime`

## Validation checklist for implemented queue-v2 runtime

- `queue-v2 --dry-run` emits `schemaVersion == "project-profile-queue/v1"` and category-first primary routes.
- `queue-v2 --confirm` writes only `.lazy-harness/project/profile-queue.json`.
- `promote-v2 --dry-run` rejects pending/non-accepted queue items.
- `promote-v2 --dry-run` emits `project-profile-promote-preview/v1`, `plannedWrites`, and accepted→promoted queue-update preview metadata.
- `promote-v2 --dry-run` does not mutate the queue or write canonical targets.
- `promote-v2 --confirm` rejects pending/non-accepted queue items and already-promoted items.
- `promote-v2 --confirm` writes `.lazy-harness/project/profile-queue.json` and, for `promotionTarget.kind=record`, a deterministic `needs-interview` record target.
- `promote-v2 --confirm` records applied record/candidate-row effects and deferred rulebook/capability/update-loop effects.
- `promote-v2 --confirm` for `promotionTarget.kind=candidate-row` appends a stable row to `.lazy-harness/knowledge/candidates.jsonl` via `appendJsonlStable`.
- `promote-v2 --confirm` for `promotionTarget.kind=rulebook` creates a deterministic draft/discover rulebook entry under `.lazy-harness/rules/**`.
- `promote-v2 --confirm` for `promotionTarget.kind=capability-binding` upserts a deterministic discover/checklist capability in `.lazy-harness/ssot/capabilities.json`.
- The output includes at least one non-policy category-routed item and one policy-candidate source item under `primaryRoute=policies`.
- At least one item demonstrates a category-first `primaryRoute` with multiple `facets`/`relatedRoutes`.
- All `promotionTarget.requiresConfirmation` values are true.
- No direct write occurs to update-loop events.
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
- Planning: queue-v2 implementation, promote-v2 dry-run preview, promote-v2 confirmed queue-status writer, record target writer, candidate-row writer, rulebook writer, and capability-binding writer completed; update-loop writer remains deferred.
