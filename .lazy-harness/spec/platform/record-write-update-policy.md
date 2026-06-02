# SDD — Record Write/Update Policy

Status: accepted
Date: 2026-06-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related plan: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`
Related spec: `.lazy-harness/spec/platform/record-digest-format.md`
Related spec: `.lazy-harness/spec/platform/project-rule-router.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - user confirms a rule, decision, source-of-truth correction, behavior, contract, or regression
  - 사용자가 새 규칙/결정/정정/기록을 어디에 어떻게 저장할지 말한다
  - deciding whether to update an existing record or create a new one
  - response.completed reports missing record completion
- Must:
  - search existing canonical records before writing
  - update the primary existing record when the subject matches
  - create a new record only for a distinct subject/layer/context
  - maintain Rule digest, Implementation map, graph links, and layer completeness when applicable
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
→ update existing record or create new record
→ maintain digest + implementation map + graph links as needed
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
- the new information belongs to a different layer or bounded context,
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

## Required sections by record class

### Records with reusable guidance

Add or maintain:

- `## Rule digest`
- `## Implementation map` when implementation exists or will exist
- `## Rule placement` when the record captures a user-confirmed rule/correction
- `## Discovery capture` for non-trivial analysis/plan discoveries

### Planning records

Planning records should include:

- status (`proposed`, `in-progress`, `implemented`, `reverted-experiment`, `blocked`, etc.)
- current phase or next slice
- validation criteria
- Rule placement
- Discovery capture

They may include `## Rule digest` only if the plan itself is active guidance future agents should consult.

### TDD/regression records

TDD records must include layer completeness judgement:

- SDD impact or none,
- BDD impact or none,
- SSOT impact or none,
- DDD impact or none.

If impacted records exist, update/cross-link them in the same slice.

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

A future implementation should add fixtures for:

1. update existing SSOT vs create duplicate SSOT,
2. create new SDD for distinct contract,
3. mark reverted experiment without active digest noise,
4. TDD layer completeness on bug/regression records,
5. digest maintenance when status/appliesWhen changes.

Until implementation exists, this SDD is validated by source self-test/doctor and review.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/spec/platform/record-write-update-policy.md` — this SDD contract.
  - `.lazy-harness/spec/platform/record-digest-format.md` — companion digest section contract.
  - `.lazy-harness/spec/platform/project-rule-router.md` — existing rule placement routing contract.
  - `.lazy-harness/spec/platform/implementation-map-standard.md` — implementation map requirements.
  - `.lazy-harness/planning/record-query-context-loop-transition-plan.md` — phase plan.
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — architecture decision.
- Future files:
  - `.lazy-harness/scripts/record-digest-audit.ts`
  - `.lazy-harness/scripts/relevant-record-query.ts`
  - `.lazy-harness/spec/platform/relevant-record-query.md`
- Flow:
  1. New confirmed information appears.
  2. Agent searches existing records.
  3. Agent updates primary record or creates a new one by decision tree.
  4. Agent updates digest/implementation map/cross-links as needed.
  5. Future relevant-record query surfaces the updated digest.
- Tests / protection:
  - Future fixtures listed above.
  - Current validation: `.lazy-harness/scripts/self-test.py`, `doctor.py --profile smoke`.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/record-digest-format.md`
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - Planning: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`

## Rule placement

- Rule: confirmed framework/host knowledge must update existing canonical records when appropriate, create new records only for distinct subjects, and maintain digest/implementation metadata to support future relevant-record query.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/record-write-update-policy.md`
- Why not AGENTS.md: this is a platform contract for record mutation behavior, not short operational grammar.
- Why not `.jcode`: record write/update policy is shared lazy-harness framework behavior, not local/private Jcode policy.
- Confirmation: user-confirmed direction via ADR 0041 and active transition plan.

## Discovery capture

- DDD: none.
- SDD: updated, this contract defines record write/update behavior.
- BDD: candidate, future behavior should avoid duplicate/stale record surfacing.
- TDD: future fixtures needed for update-vs-create, supersede/retire, and layer completeness.
- ADR: ADR 0041 selected organic hybrid guidance.
- SSOT: harness enforcement policy anchors mandatory record completion.
- Planning: record-query context loop transition plan Phase 1.
