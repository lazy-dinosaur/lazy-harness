# TDD — Project Profile V2 / Project Interview Policy Discovery

Status: active-runtime-promote-v2-confirm-queue
Date: 2026-06-16
Updated: 2026-06-17
Layer: TDD
Related SDD: `.lazy-harness/spec/platform/project-profile-v2.md`
Related plan: `.lazy-harness/plans/project-init-interview-v2-spec.md`
Related Project Map: `.lazy-harness/spec/platform/project-map-v2.md`

## Rule digest

- Status: active-runtime-promote-v2-confirm-queue
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
  - verify queue-v2 emits typed queue items and writes only `.lazy-harness/project/profile-queue.json`
  - verify promote-v2 dry-run preview requires `status=accepted` and does not mutate queue/canonical targets
  - verify promote-v2 confirmed writer requires `status=accepted`, writes only the queue file, and records deferred target effects
  - verify forbidden semantic-authority fields are absent
- Must not:
  - permit silent defaults
  - permit unconfirmed facts/policies to become canonical writes
  - permit promote-v2 preview to write records/rules/capabilities/update-loop events or queue status changes
  - permit first promote-v2 confirm writer to write canonical records/rules/capabilities/candidates/update-loop events
  - center the model on tests only
  - require write/apply behavior before a separate approval
- Record completion:
  - runtime implementation updates this TDD, SDD, fixtures, `project-profile.ts`, self-test, manifest, and graph rows together.

## Draft fixture

The design fixture is:

```text
.lazy-harness/fixtures/project-profile-v2/interview-output.json
```

## Regression cases for implemented runtime

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
| `project_profile_v2_queue_shape` | `queue-v2 --dry-run` output | `schemaVersion == "project-profile-queue/v1"`, queue path, source packet, summary, and typed items present. |
| `project_profile_v2_queue_write_boundary` | `queue-v2 --confirm` | writes only `.lazy-harness/project/profile-queue.json`; no candidates/rules/capabilities/update-loop append. |
| `project_profile_v2_queue_routes` | queue items | uses Project Map category-first `primaryRoute` values, includes non-policy/category-routed items, policy source items under `policies`, event-ready metadata, and at least one multi-facet item. |
| `project_profile_v2_promote_requires_accepted` | `promote-v2 --dry-run` on pending item | command fails and reports that only `status=accepted` items can be previewed. |
| `project_profile_v2_promote_preview_boundary` | accepted item + `promote-v2 --dry-run` | emits `project-profile-promote-preview/v1`, echoes accepted item, shows accepted→promoted preview update, exposes confirmation-gated planned writes, and writes nothing. |
| `project_profile_v2_promote_requires_mode` | `promote-v2` without `--dry-run` or `--confirm` | command is blocked because one explicit mode is required. |
| `project_profile_v2_promote_confirm_queue_only` | accepted item + `promote-v2 --confirm` | emits `project-profile-promote-result/v1`, writes only profile queue, marks exactly one item promoted, records promoted metadata, and records deferred target effects. |
| `project_profile_v2_promote_confirm_rejects_reuse` | already promoted item + `promote-v2 --confirm` | command fails because only `status=accepted` items can be promoted. |

## Acceptance assertions for implemented runtime

`self-test.py#check_project_profile_v2_runtime` verifies:

1. `project-profile.ts` exposes V2 mode or V2 dry-run output without breaking V1 modes.
2. V2 output matches the fixture shape.
3. V2 output includes Project Map cluster seeds.
4. V2 output includes policy candidates for at least validation and a non-test dimension.
5. Initial policy candidate levels are only `discover` or `recommend` unless fixture marks a confirmed answer.
6. `fill --confirm` writes only confirmed answers.
7. Pi primary/Jcode compatibility appears in output.
8. Existing Project Profile tests still pass.
9. `queue-v2 --dry-run` emits `project-profile-queue/v1`.
10. `queue-v2 --confirm` writes only `.lazy-harness/project/profile-queue.json`.
11. Queue items all include `status`, `primaryRoute`, `facets`, `relatedRoutes`, `source`, `evidence`, and `promotionTarget`.
12. Queue output uses category-first `primaryRoute` values such as `facts`, `expectations`, `contracts`, `validation`, `ownership`, `source-links`, and `policies`; layer labels remain in `facets`; output includes event-ready metadata and a multi-facet item.
13. `promote-v2 --dry-run` rejects pending items and accepts only `status=accepted` queue items.
14. `promote-v2 --dry-run` emits `project-profile-promote-preview/v1` with accepted→promoted preview metadata and confirmation-gated `plannedWrites`.
15. `promote-v2 --dry-run` does not mutate `.lazy-harness/project/profile-queue.json` or write any canonical target.
16. `promote-v2 --confirm` rejects pending/already-promoted items and accepts only `status=accepted` queue items.
17. `promote-v2 --confirm` emits `project-profile-promote-result/v1`, writes only `.lazy-harness/project/profile-queue.json`, and marks exactly one item promoted.
18. `promote-v2 --confirm` records target-specific deferred effects and does not write canonical targets.

## Implementation map

- Status: promote-v2 confirmed queue-status writer slice implemented.
- Primary files:
  - `.lazy-harness/tests/project-profile-v2.md` — this TDD.
  - `.lazy-harness/spec/platform/project-profile-v2.md` — SDD output contract.
  - `.lazy-harness/plans/project-init-interview-v2-spec.md` — interview plan.
  - `.lazy-harness/fixtures/project-profile-v2/interview-output.json` — desired interview output fixture.
  - `.lazy-harness/fixtures/project-profile-v2/profile-queue.json` — queue-v2 output fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-preview.json` — promote-v2 preview fixture.
  - `.lazy-harness/fixtures/project-profile-v2/promote-confirm.json` — promote-v2 confirm queue-status result fixture.
  - `.lazy-harness/scripts/project-profile.ts` — implements `interview-v2 --dry-run`, `queue-v2 --dry-run|--confirm`, `promote-v2 --dry-run`, and first `promote-v2 --confirm` queue-status writer.
  - `.lazy-harness/scripts/self-test.py` — protects interview/queue/promote runtime packet shapes, write boundaries, and V1 backward compatibility.
- Key symbols:
  - `project-profile.ts#ProjectProfileInterviewV2Packet`
  - `project-profile.ts#buildInterviewV2Result`
  - `project-profile.ts#renderInterviewV2Md`
  - `project-profile.ts#ProjectProfileQueueV1`
  - `project-profile.ts#ProjectProfileQueueItem`
  - `project-profile.ts#buildProfileQueueV1FromInterviewV2`
  - `project-profile.ts#buildProfileQueueV1`
  - `project-profile.ts#applyProfileQueue`
  - `project-profile.ts#ProjectProfilePromoteV2Preview`
  - `project-profile.ts#ProjectProfilePromoteV2Result`
  - `project-profile.ts#ProjectProfilePromotionTargetEffect`
  - `project-profile.ts#buildPromoteV2Preview`
  - `project-profile.ts#applyPromoteV2`
  - `project-profile.ts#renderPromoteV2Md`
  - `self-test.py#check_project_profile_v2_runtime`
  - `self-test.py#check_project_profile_v2_queue_runtime`
- Protection now:
  - `bun .lazy-harness/scripts/project-profile.ts --mode interview-v2 --dry-run --format json`
  - `bun .lazy-harness/scripts/project-profile.ts --mode queue-v2 --dry-run --format json`
  - `bun .lazy-harness/scripts/project-profile.ts --mode queue-v2 --confirm --format json`
  - `bun .lazy-harness/scripts/project-profile.ts --mode promote-v2 --item <accepted-id> --dry-run --format json`
  - `bun .lazy-harness/scripts/project-profile.ts --mode promote-v2 --item <accepted-id> --confirm --format json`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`
  - `.lazy-harness/bin/lazy test`
- Runtime boundary:
  - `interview-v2` is read-only and requires `--dry-run`.
  - `interview-v2 --confirm` is blocked.
  - `queue-v2 --confirm` writes only `.lazy-harness/project/profile-queue.json`.
  - `promote-v2 --dry-run` requires `status=accepted` and previews only, with no queue/canonical mutation.
  - `promote-v2 --confirm` writes only queue status/promoted metadata and emits deferred target effects.
  - no candidates/rules/capabilities/update-loop event append happens in this slice.

## Layer completeness impact

- DDD: domain vocabulary/invariant question groups protected as future fixture expectation.
- BDD: project expectations and workflow behavior protected as future fixture expectation.
- SDD: paired with Project Profile V2 SDD.
- TDD: this record, `self-test.py#check_project_profile_v2_runtime`, and `self-test.py#check_project_profile_v2_queue_runtime` protect the implemented interview, category-first queue, promote preview, and confirmed queue-status promotion packets.
- ADR: future ADR needed before replacing V1 mode semantics.
- SSOT: policy/capability/taxonomy SSOT inputs are referenced, not changed here.
- Planning: Phase 2 interview dry-run, queue-v2 writer, promote-v2 dry-run preview, and first confirmed queue-status promotion writer implemented; canonical target writers remain future work.

## Rule placement

- Rule: Project Profile V2 must be tested as a project-map and policy-discovery interview, not a test-only wizard or silent default generator.
- Scope: framework-global
- Primary record: `.lazy-harness/tests/project-profile-v2.md`
- Why not AGENTS.md: this is a regression/acceptance contract, not prompt grammar.
- Why not `.jcode`: V2 is Pi-primary and agent-neutral.
- Confirmation: user-approved Phase 2 design draft, first read-only runtime slice, queue-v2 writer slice, A/A/A/B/A promote preview decisions, and A→B→C confirmed-writer sequence on 2026-06-17.

## Discovery capture

- DDD: future domain branch coverage.
- BDD: future behavior/policy coverage.
- SDD: paired with SDD and implemented by `project-profile.ts#buildInterviewV2Result`, category-first `project-profile.ts#buildProfileQueueV1FromInterviewV2`, `project-profile.ts#buildPromoteV2Preview`, and `project-profile.ts#applyPromoteV2`.
- TDD: updated here and in `self-test.py#check_project_profile_v2_runtime` plus `self-test.py#check_project_profile_v2_queue_runtime`.
- ADR: none yet; ADR required only before replacing V1 behavior.
- SSOT: no SSOT mutation; uses Project Map ingestion source vocabulary.
- Planning: Phase 2 interview dry-run, queue-v2 writer, promote-v2 dry-run preview, and first confirmed queue-status promotion writer implemented; canonical target writers deferred.
