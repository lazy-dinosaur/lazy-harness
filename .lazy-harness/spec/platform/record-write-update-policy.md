# SDD — Record Write/Update Policy

Status: accepted
Date: 2026-06-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related plan: `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
Related spec: `.lazy-harness/spec/platform/record-digest-format.md`
Related spec: `.lazy-harness/spec/platform/project-rule-router.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 기록 정책
  - record 작성 규칙
  - update vs create
  - 중복 방지
  - 어디에 저장
- Applies when:
  - user confirms a rule, decision, source-of-truth correction, behavior, contract, or regression
  - 사용자가 새 규칙/결정/정정/기록을 어디에 어떻게 저장할지 말한다
  - deciding whether to update an existing record or create a new one
  - response.completed reports missing record completion
- Must:
  - search existing canonical records before writing
  - choose and update one primary narrative record for the logical work unit by default
  - promote an additional layer record only for an independent semantic delta; otherwise link or record `no independent delta`
  - keep repeated validation/progress detail in one evidence capsule when durable, otherwise no-record/transient
  - maintain Rule digest, Implementation map, graph links, and layer completeness only on records actually promoted
- Record completion:
  - changes to record mutation behavior update this SDD
- Related records:
  - `.lazy-harness/spec/platform/record-digest-format.md`
  - `.lazy-harness/spec/platform/project-rule-router.md`

## Purpose

Lazy-harness must write durable records when the user confirms rules, decisions, source-of-truth facts, behavior, contracts, or regressions.

The write/update policy defines how to choose between updating an existing record and creating a new one, how to avoid duplicate/stale guidance, and how to keep records queryable through the `## Rule digest` format.

This policy is the write-side companion to relevant-record query.

```text
confirmed information
→ route to layer
→ choose one primary canonical record by default
→ promote another layer only for an independent semantic delta
→ maintain digest + Project Map branch + implementation map + graph links on promoted records as needed
→ future query can surface it
```

## Non-goals

- Not a replacement for layer-specific record content.
- Not a license to write canonical records without user confirmation when confirmation is required.
- Not a generated index format.
- Not a tool-specific policy mechanism.

## Mandatory record completion triggers

Record completion is mandatory when user-confirmed or verified project/framework information fits any of these classes:

| Information type | Primary layer |
|---|---|
| domain terms, entities, business rules | DDD: `.lazy-harness/domain/` |
| API/component/IPC/contract/interface rules | SDD: `.lazy-harness/spec/` |
| UI/user journey/visible workflow behavior | BDD: `.lazy-harness/behavior/` |
| bug/regression/protection/validation cases | TDD: `.lazy-harness/tests/` |
| trade-off/why/architecture decision | ADR: `.lazy-harness/decisions/` |
| config/env/schema/source-of-truth/ownership/rule source | SSOT: `.lazy-harness/ssot/` |
| transient roadmap/backlog/implementation plan | Planning: `.lazy-harness/planning/` |

If the layer is ambiguous, stop with an option gate instead of guessing.

## Update vs create decision tree

### Step 1 — Search canonical records first

Before writing, search current host records for the subject:

```bash
grep -rli '<core token>' .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning}/
```

Use current root only. Do not search sibling hosts for canonical truth.

### Step 2 — Prefer updating an existing primary record when one exists

Update an existing record when:

- it is the accepted/active primary record for the same subject,
- the new information refines or corrects the same rule/contract/behavior,
- the record's `Scope` matches,
- updating avoids duplicate future query results,
- the user correction says “X is Y” for the same source-of-truth area.

Examples:

- User corrects project ownership → update existing ownership/project-identity SSOT.
- API contract changes for an existing endpoint/component → update existing SDD.
- Existing bug regression gets a new edge case → update existing TDD and layer completeness judgement.
- Existing ADR remains decision but rationale changes → update ADR with amendment if appropriate.

### Step 3 — Create a new record when the subject is distinct

Create a new record when:

- no existing record covers the subject,
- the information belongs to a different layer or bounded context **and** carries an independent semantic delta that the existing primary record cannot own,
- the new item is a separate decision/trade-off,
- mixing would make a record too broad to query usefully,
- the existing record is historical/reverted and should not become active again.

Examples:

- New workflow policy not covered by existing SSOT → create dedicated SSOT.
- New independent architectural decision → create new ADR.
- New UI flow → create BDD record.
- New bug class → create TDD regression record.

### Step 4 — Supersede/retire stale records explicitly

Do not silently edit history when an old rule becomes wrong.

Use a visible status change:

```md
Status: deprecated | reverted | superseded
Superseded by: `.lazy-harness/...`
Reason: ...
Date: YYYY-MM-DD
```

If the record has a `## Rule digest`, set digest status to `deprecated` or `reverted` so relevant-record query excludes it by default.

## Duplicate prevention

When a new candidate overlaps an existing record:

1. Update the primary record.
2. Add a cross-link from related records if needed.
3. Do not create a second record with equivalent active `Applies when` triggers.
4. If a duplicate already exists, mark one as primary and the other as deprecated/superseded.

Relevant-record query depends on duplicate control. Duplicate active digests create noisy context and reduce trust.

## Primary canonical record default

A logical work unit should have one primary narrative record by default. This is a promotion rule, not a hard one-file cap: a regression TDD plus an independently changed API contract or visible behavior record is valid, while copying the same invariant into SDD, BDD, and SSOT merely because each layer is related is not.

Before promoting each additional canonical record, answer:

1. What fact belongs uniquely to this layer?
2. What would future agents miss if this layer only linked to the primary record?
3. Did this layer's contract, visible flow, source-of-truth invariant, domain rule, or regression protection independently change?

If no independent semantic delta exists, keep a cross-link or write `no independent delta` in the primary/TDD completeness judgement. MultiCandidate packets may preserve every possible gap for review, but candidate enumeration never implies multi-record canonical promotion.

Required sections apply after promotion. Do not create a record merely to host Rule digest, Implementation map, Rule placement, Discovery capture, validation output, commit SHA, staging status, or review-round prose.

Repeated commands/results that are durable belong in at most one evidence capsule for the logical work unit; routine reruns and transient progress use `no-record-needed`.

## Required sections by record class

### Records with reusable guidance

Add or maintain:

- `## Rule digest`
- digest `Aliases`/`Surface terms` grep bait for new/updated reusable records — two sources: observed user vocabulary + LLM-generated variants (ADR 0053; advisory lint)
- same-topic cross-links so any entry piece reaches the rest — acceptance is reachability, audited by `lazy record-structure-audit` (ADR 0053); backlinks stay derived (`lazy backlink-index`), never hand-written
- `## Project Map branch` when the record participates in a Project Map V2 cluster
- `## Implementation map` when implementation exists or will exist
- `## Rule placement` when the record captures a user-confirmed rule/correction
- `## Discovery capture` for non-trivial analysis/plan discoveries

### Project Map branch records

When a confirmed record participates in a Project Map V2 cluster, add or maintain a `## Project Map branch` block following `.lazy-harness/ssot/project-map-record-storage.md`.

The block links the canonical record to its anchor/branch/edge metadata while keeping the record itself as the source of truth. Generated Project Map views may use this metadata, but generated views remain cue-only and non-canonical.

Do not add Project Map branch metadata for an unconfirmed host-specific fact unless it is clearly marked as candidate/planning or the user/source/test evidence confirms it.

### Planning records

Planning records should keep a compact current state rather than become chronological execution journals:

- status (`proposed`, `in-progress`, `implemented`, `reverted-experiment`, `blocked`, etc.)
- current phase or next slice
- validation criteria and residual risks
- one link to an evidence capsule when detailed repeated commands/results must remain durable
- Rule placement
- Discovery capture

They may include `## Rule digest` only if the plan itself is active guidance future agents should consult.

### TDD/regression records

TDD records must include layer completeness judgement:

- SDD independent delta or none,
- BDD independent delta or none,
- SSOT independent delta or none,
- DDD independent delta or none.

Update/cross-link another layer in the same slice only when its independent semantic delta exists; otherwise the local judgement is complete.

### ADR records

ADR records should preserve decision history. If a decision changes:

- add amendment/supersession when preserving old rationale matters,
- or create a new ADR and mark old one superseded/reverted.

ADR records that guide future behavior should include a digest.

## Digest maintenance rule

When updating a record that has `## Rule digest`, update the digest in the same edit if any of these changed:

- status,
- scope,
- appliesWhen / trigger cues,
- must/must-not behavior,
- record completion obligation,
- related primary records.

When creating a record that future agents should consult, add `## Rule digest` immediately rather than deferring to a later cleanup.

If the record is purely historical, a digest is optional and should usually be `reverted`, `deprecated`, or omitted.

## Implementation map maintenance rule

Use `.lazy-harness/spec/platform/implementation-map-standard.md`.

When implementation exists or changes:

1. Update the Markdown `## Implementation map` section.
2. Append/supersede graph edges in `.lazy-harness/knowledge/graph.jsonl` when confirmed.
3. Mark generated index stale or regenerate it when tooling exists.

Do not invent file/symbol facts.

## Record completion audit signals

`response.completed` audit should consider a response incomplete when:

- the user confirmed a rule/correction but no canonical record changed,
- a response says “I will record/update” but no write happened,
- a project/team rule is placed in `.jcode` or Jcode memory without canonical lazy-harness placement,
- a bug fix/regression is discussed but TDD/layer completeness was not considered,
- a design trade-off is decided but no ADR or planning record captures it,
- an existing surfaced digest required record completion and the response skipped it.

The audit should not request another canonical record only because a related layer or repeated validation output exists; `no independent delta` and `no-record-needed` are successful outcomes.

The audit should remain silent for normal turns with no record-completion trigger.

## Record update examples

### Source-of-truth correction

User: “아니 host-project-b도 dogfood host야.”

Expected:

- update `.lazy-harness/ssot/project-identity.md` or equivalent ownership/host list,
- add/update digest appliesWhen for dogfood host sync,
- include Rule placement with `Confirmation: user-confirmed`.

### Contract update

User confirms a component/API behavior.

Expected:

- update existing SDD if same contract,
- create new SDD if distinct contract,
- update implementation map if files/symbols changed,
- digest includes future intent cues.

### Reverted experiment

User rejects a previously implemented direction.

Expected:

- retain planning/ADR memory as `reverted-experiment` or `reverted`,
- mark digest `reverted` or omit digest if not future guidance,
- create/point to replacement plan.

## Validation expectations

Current protection covers:

1. every touched TDD Markdown record needs a non-empty four-layer judgement matrix, even when another layer record is also touched,
2. label-only completeness text does not satisfy the helper,
3. MultiCandidate packets preserve the exact candidate set, reject canonical mutation actions, and cap overflow at 20,
4. broker/AGENTS instructions surface one primary canonical record plus independent-delta guidance,
5. `primary-canonical-record` resolves as recommend/advisory-only and the portable framework-policy subset audits cleanly after downstream sync without requiring arbitrary host-local policy sources in the framework manifest.

Planned/retained coverage still needed for older write-policy branches:

- update existing SSOT vs create duplicate SSOT,
- create new SDD for a distinct contract,
- mark reverted experiment without active digest noise,
- digest maintenance when status/appliesWhen changes.

This SDD is protected by source self-test, policy resolution, record lint, graph hygiene, and review.

## Implementation map

- Status: `implemented; primary-canonical-record amendment active`
- Primary files:
  - `.lazy-harness/spec/platform/record-write-update-policy.md` — this SDD contract.
  - `.lazy-harness/spec/platform/record-digest-format.md` — companion digest section contract.
  - `.lazy-harness/spec/platform/project-rule-router.md` — existing rule placement routing contract.
  - `.lazy-harness/spec/platform/implementation-map-standard.md` — implementation map requirements.
  - `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md` — phase plan.
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — architecture decision.
  - `.lazy-harness/decisions/0033-layer-completeness-gate.md` — primary-record and independent-delta completeness decision.
  - `.lazy-harness/spec/platform/record-decision-broker.md` — candidate enumeration vs canonical promotion boundary.
  - `.lazy-harness/spec/platform/evidence-capsule-standard.md` — single durable evidence location for detailed validation.
  - `.lazy-harness/ssot/policies.json` — typed `primary-canonical-record` recommend policy.
  - `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md` — typed policy storage/co-change decision.
  - `.lazy-harness/spec/platform/policy-machinery-v2.md` — advisory resolver and downstream sync contract.
- Future file:
  - `.lazy-harness/scripts/record-digest-audit.ts`
- Existing supporting record:
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
- Flow:
  1. New confirmed information appears.
  2. Agent searches existing records and chooses one primary narrative record.
  3. Agent promotes another layer only when it owns an independent semantic delta; otherwise it links or records `no independent delta`.
  4. Agent updates digest/implementation map/cross-links only for promoted records.
  5. Repeated validation detail goes to one evidence capsule or remains transient.
  6. Future relevant-record query surfaces the compact canonical set.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_layer_completeness_helper`
  - `.lazy-harness/scripts/self-test.py#check_record_decision_broker_phase8`
  - `.lazy-harness/scripts/self-test.py#check_policy_machinery_v2`
  - `.lazy-harness/scripts/self-test.py#check_agents_md_invariants`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/record-digest-format.md`
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - ADR: `.lazy-harness/decisions/0033-layer-completeness-gate.md`
  - SDD: `.lazy-harness/spec/platform/evidence-capsule-standard.md`
  - SDD: `.lazy-harness/spec/platform/record-decision-broker.md`
  - Planning: `.lazy-harness/planning/workflow-churn-reduction-plan.md`

## Rule placement

- Rule: confirmed knowledge chooses one primary canonical record by default; additional layers require an independent semantic delta, and repeated validation/progress detail is consolidated into one evidence capsule or remains no-record/transient.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/record-write-update-policy.md`
- Why not AGENTS.md alone: AGENTS carries only the compact operational pointer; this SDD defines the complete mutation contract.
- Why not `.jcode`: record write/update policy is shared lazy-harness framework behavior, not local/private Jcode policy.
- Confirmation: user selected the guard → sample-cleanup rollout on 2026-07-13 after Medivance dogfood evidence.

## Discovery capture

- DDD: none.
- SDD: updated, this contract defines record write/update behavior.
- BDD: no framework-visible UI flow change.
- TDD: existing self-test fixtures gain primary-record/no-independent-delta cases; no separate narrative TDD record is needed.
- ADR: ADR 0033 amended — completeness is impact judgement, not layer mirroring.
- SSOT: typed `primary-canonical-record` recommend policy added to `.lazy-harness/ssot/policies.json`.
- Planning: `.lazy-harness/planning/workflow-churn-reduction-plan.md` records the approved rollout and dogfood baseline.
