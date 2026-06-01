# Record Query Context Loop Transition Plan

Status: proposed
Date: 2026-06-01
Layer: Planning
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`

## Problem statement

The goal is not to add more tool-specific guides or hard gates.

The goal is:

```text
lazy-harness records are complete and searchable
→ relevant rules are surfaced before a response/plan
→ the agent answers naturally using a compact digest
→ response.completed audits missed rules/record writes
→ confirmed facts/rules/decisions converge into canonical records
```

User-confirmed distinction:

- **Record completion is mandatory.** Confirmed rules, decisions, source-of-truth corrections, contracts, behavior scenarios, and regressions must be written to the right layer.
- **Action guidance should be organic.** Do not encode project policy as `when bash`, `when gh`, `when dev-cli`, or `when GitHub MCP`. Use pre-response relevant-record query and post-response audit instead.

## Current-state inventory

### 1. Record storage is canonical but not query-shaped enough

Current canonical layers exist:

- `.lazy-harness/domain/`
- `.lazy-harness/spec/`
- `.lazy-harness/behavior/`
- `.lazy-harness/tests/`
- `.lazy-harness/decisions/`
- `.lazy-harness/ssot/`
- `.lazy-harness/planning/`

Existing record standards emphasize:

- correct layer placement,
- Implementation map sections,
- graph edges,
- generated implementation indexes.

Gap:

- Records do not yet have a consistent compact **rule digest** shape optimized for pre-response injection.
- Trigger/context phrases are not consistently declared.
- Some rules are human-readable but not easy to retrieve by natural intent like “PR 작성”, “test instance”, “source of truth correction”, or “release”.

### 2. SearchProvider exists but is not ready for relevant-record query

`.lazy-harness/scripts/search-provider.ts` exists under ADR 0024, but current observed gaps include:

- It maps old layer paths (`.lazy-harness/ddd`, `.lazy-harness/sdd`, etc.) while current canonical paths are `domain`, `spec`, `behavior`, `tests`, `decisions`, `ssot`.
- It is a substring prefilter, not a digest generator.
- It does not know record layer metadata, trigger contexts, token budgets, or output shape.

Implication:

- We should not build C+ v2 on top of current SearchProvider without updating the path model and output contract.

### 3. Generated implementation index is not the right index

`.lazy-harness/generated/implementation-index.json` is a derived cache for implementation maps and file/symbol retrieval.

It is not a relevant-rule index.

Gap:

- We need either a new generated index, for example `.lazy-harness/generated/relevant-record-index.json`, or an extension that keeps rule/query metadata separate from implementation symbol metadata.

### 4. record-audit is useful but read-only dashboard, not query engine

`record-audit` reports layer counts, host-owned changes, markers, graph hygiene, and recent files.

It does not:

- rank records for a user message,
- produce compact rule digests,
- track surfaced/read rules for response audit.

It can contribute quality signals but should not become the query engine.

### 5. response.completed exists and is the correct audit/backstop surface

Current lifecycle wiring includes `response.completed`.

This is suitable for:

- checking whether surfaced rules were ignored,
- detecting missing record placement/capture,
- updating guidance/journal state,
- remaining silent when no issue exists.

Gap:

- There is no confirmed true `response.before` event in current wiring.
- First implementation may need a closest available pre-response mechanism or a CLI/side-channel prototype until Jcode supports a true pre-response hook.

### 6. tool-attached policy still exists and needs migration

Current inventory shows tool-attached policy surfaces remain:

- `.jcode/hooks/check-bash.sh` calls `check-rule-action-boundary.py`.
- `check-rule-action-boundary.py` includes PR body policy tied to `gh pr create/edit`.
- `.lazy-harness/spec/platform/rule-binding-action-boundary.md` describes the bash/GH PR exemplar.
- `.lazy-harness/ssot/rule-lifecycle.md` includes binding metadata with `tool: bash` and `commandRegex`.
- self-test has PR body guard fixtures.

These are existing, not new. C+ v2 should migrate/deprecate them after response-lifecycle coverage exists.

## Framework operating-model shift

This is a change to the basic lazy-harness loop, not an isolated feature.

Old practical failure mode:

```text
records are written
→ agent later depends on memory/manual grep
→ stored rule may be missed
→ response.completed complains after the fact
```

Target model:

```text
records are written in queryable/digestible form
→ records are indexed for natural intent/context
→ relevant digest is surfaced before response/plan
→ agent acts with the rule in working context
→ response.completed audits whether records were used or new records are required
→ records/indexes update again
```

This makes `.lazy-harness` not just institutional memory, but an active memory loop.

## Target architecture

### Loop

```text
1. Pre-response relevant-record query
2. Compact rule digest injection/surfacing
3. Normal agent answer or plan
4. response.completed audit/backstop
5. Record completion/update if confirmed info exists
6. Index regeneration or stale marker update
```

### Record completion vs action guidance

| Class | Mechanism | Strength |
|---|---|---|
| confirmed rule/decision/correction/scenario/contract/regression | canonical record write/update | mandatory |
| relevant rule for current answer/action | pre-response query + digest | organic guidance |
| ignored surfaced rule or missing record | response.completed audit | feedback/backstop |
| destructive or repeatedly failed boundary | narrow promoted hard stop | exceptional |

### Digest format target

A digest must be small enough for normal turns:

```md
Relevant lazy-harness rules
- `.lazy-harness/ssot/pr-description-format.md` — PR description format
  - Use Why / What / Task sections.
  - Applies when drafting PR body, regardless of tool.
- `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — no tool-specific project policy
  - Use record/artifact context, not gh/bash/dev-cli branches.
```

Budget:

- default: 200–600 tokens,
- hard ceiling: 1,000 tokens,
- include paths and 1–3 bullets, not full documents.

## Proposed phases

### Phase progress

- Phase 0 — Baseline and inventory: completed as planning/inventory in this record.
- Phase 1 — Record digest/write standard: SDD contracts written on 2026-06-01.
- Phase 2 — Relevant record index/query contract: SDD/schema/SearchProvider path fix written on 2026-06-01.
- Phase 3 — Pre-response surfacing prototype: implemented on 2026-06-01 using Jcode `message.received`.
- Phase 4 — response.completed audit against surfaced digest: implemented on 2026-06-01.

### Phase 0 — Baseline and inventory

Goal: measure and inventory before implementation.

Tasks:

1. Inventory tool-attached policy surfaces.
2. Inventory record types and fields needed for relevant query.
3. Measure current `response.completed` latency and output frequency.
4. Identify whether Jcode has or needs a true pre-response lifecycle surface.

Outputs:

- `.lazy-harness/planning/tool-attached-policy-migration-inventory.md`
- timing baseline or hook-timings summary
- decision on pre-response surface: native hook, prompt/message route, or CLI prototype

Validation:

- self-test and doctor pass.
- No behavior change yet.

### Phase 1 — Record digest/write standard

Goal: make records queryable and injectable without full-document dumps.

Tasks:

1. Define `Rule digest` section or frontmatter-like block for records that carry reusable guidance.
2. Define fields:
   - title
   - layer
   - scope
   - appliesWhen / trigger phrases
   - required behavior
   - record completion obligation if any
   - status: active/advisory/deprecated/reverted
   - token summary bullets
3. Define record update policy:
   - update existing record vs create new record,
   - supersede/retire stale guidance,
   - avoid duplicates,
   - mandatory layer completeness for TDD/bug records.

Outputs:

- `.lazy-harness/spec/platform/record-digest-format.md`
- `.lazy-harness/spec/platform/record-write-update-policy.md`

Status:

- completed on 2026-06-01 as SDD contracts.
- implementation/audit fixtures still belong to later phases.

Validation:

- fixtures over existing PR/runtime/SSOT correction records.
- record-audit marker for records with enforcement words but no digest.

### Phase 2 — Relevant record index/query contract

Goal: query records by natural intent/context, not by tool.

Tasks:

1. Fix/replace stale SearchProvider path model.
2. Add relevant-record query contract:
   - input: user message, recent context, optional touched files/layers,
   - output: ranked digest entries,
   - constraints: root-bound, token budget, no full doc dump.
3. Add generated cache design:
   - `.lazy-harness/generated/relevant-record-index.json` or equivalent.
   - canonical source remains Markdown records + graph.
4. Support fallback grep/read only in prototype/measurement mode.

Outputs:

- `.lazy-harness/spec/platform/relevant-record-query.md`
- `.lazy-harness/schemas/relevant-record-index.schema.json`
- future script: `.lazy-harness/scripts/relevant-record-query.ts`

Status:

- completed on 2026-06-01 as SDD + generated index schema.
- `SearchProvider` direct fallback path model updated to current canonical layer directories, including Planning.
- query CLI implementation remains future work.

Validation:

- query “PR 작성” finds PR description record without `gh`.
- query “test database instance” finds runtime/dogfood record without `dev-cli`.
- query “source of truth correction” finds SSOT/rule-placement rules.
- output stays under token budget.

### Phase 3 — Pre-response surfacing prototype

Goal: get digest into the agent before answer/plan.

Tasks:

1. Confirm available Jcode lifecycle surfaces.
2. If no native `response.before`, prototype with the closest safe mechanism:
   - CLI `lazy context --message ...`,
   - prompt/message route integration,
   - side-channel/system reminder if supported.
3. Keep it advisory/ambient at first.
4. Do not attach policy to tools.

Outputs:

- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/scripts/relevant-record-query.ts`
- `.lazy-harness/hooks/lifecycle/on-message-received.sh`
- `.lazy-harness/bin/lazy context --message ...`

Status:

- implemented on 2026-06-01 after Jcode added `message.received` in commit `3eb71ddb`.
- generated Jcode wiring includes bounded `message.received` hook with `blocking = true`, `timeout_ms = 800`.
- automatic injection uses `--require-digest` so noisy fallback records do not enter the prompt by default.

Validation:

- PR/runtime/correction fixture shows digest is surfaced before the answer.
- no broad edit/write blocking.
- latency measured.

### Phase 4 — response.completed audit against surfaced digest

Goal: check whether the agent ignored surfaced rules or failed record completion.

Tasks:

1. Store a lightweight journal of surfaced digest ids for the turn.
2. In `response.completed`, audit:
   - surfaced rule ignored,
   - mandatory record completion missing,
   - rule placement missing,
   - confirmed fact not captured.
3. Keep normal successful turns silent.
4. Escalate only via guidance ladder.

Outputs:

- `.lazy-harness/spec/platform/response-rule-audit.md`
- journal state design under `.lazy-harness/state/` or logs, non-canonical.

Status:

- implemented on 2026-06-01.
- `message.received` writes sanitized surfaced digest rows to `.lazy-harness/state/surfaced-rule-digests.jsonl`.
- `response.completed` runs `check-response-rule-audit.py` in both legacy hook and `lifecycle-check.py` shadow/orchestrator chains.
- First conservative audit cases: surfaced PR description rule ignored, and surfaced record-completion obligation missing.

Validation:

- no issue → no user-visible output.
- surfaced PR rule ignored → concise audit feedback.
- confirmed correction not recorded → mandatory record completion feedback.

### Phase 5 — Migrate/deprecate tool-attached policy

Goal: remove project policy from concrete tool branches after response lifecycle coverage works.

Tasks:

1. Mark current PR body bash/GH guard as legacy compatibility.
2. Replace PR body enforcement with artifact/context digest + response audit.
3. Remove `check-rule-action-boundary.py` policy branches or shrink them to generic transport if still needed.
4. Update ADR 0039/rule-lifecycle SDD/SSOT to point to organic guidance model.
5. Keep only minimal destructive shell safety in `.jcode/hooks/check-bash.sh`.

Status:

- implemented on 2026-06-01.
- `check-rule-action-boundary.py` is now a no-op legacy compatibility shim.
- generated `.jcode/hooks/check-bash.sh` is destructive shell safety only and does not call the action-boundary helper.
- PR body structure coverage moved to `message.received` digest surfacing plus `response.completed` response-rule audit.
- ADR 0039, rule lifecycle SSOT, action-boundary SDD, and PR body guard TDD record were updated to point to ADR 0041/Phase 5.

Validation:

- no `gh`/bash-specific PR policy required for normal compliance.
- PR body rule still surfaces and audit catches misses.
- Medivance and PWA dogfood pass.

### Phase 6 — Narrow hard-stop promotion only after evidence

Goal: hard stop only when justified.

Promotion criteria:

- user-confirmed mandatory rule,
- repeated dogfood miss,
- high-cost or irreversible action,
- fixture exists,
- record explains why ambient/warn was insufficient.

Outputs:

- guidance ladder spec update,
- hard-stop fixtures,
- user-confirmed ADR/SSOT update.

## File impact map

Likely new specs:

- `.lazy-harness/spec/platform/record-digest-format.md`
- `.lazy-harness/spec/platform/record-write-update-policy.md`
- `.lazy-harness/spec/platform/relevant-record-query.md`
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/spec/platform/response-rule-audit.md`
- `.lazy-harness/spec/platform/guidance-ladder.md`

Likely scripts later:

- `.lazy-harness/scripts/relevant-record-query.ts`
- `.lazy-harness/scripts/record-digest-audit.ts`
- maybe updates to `.lazy-harness/scripts/search-provider.ts`
- maybe updates to `.lazy-harness/hooks/lifecycle/on-response-completed.sh`

Likely migrations later:

- `.lazy-harness/spec/platform/rule-binding-action-boundary.md`
- `.lazy-harness/ssot/rule-lifecycle.md`
- `.lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py`
- `.jcode/hooks/check-bash.sh` template in `jcode-wiring.ts`

## Open questions

1. Resolved: Jcode `message.received` provides same-turn pre-response context injection.
2. Resolved for Phase 2: relevant-record index has a generated JSON schema; prototype currently parses records directly.
3. Resolved for Phase 1: digest metadata starts as Markdown `## Rule digest` sections.
4. Resolved for Phase 3: native pre-response query exists; mandatory record completion remains handled by response audit/backstop.
5. Resolved in Phase 5: legacy PR body guard migration/removal completed after response audit fixtures proved replacement coverage.

## Recommended next immediate slice

Do **not** implement the full loop yet.

Next slice should be read-only and measurable:

1. Extend `response.completed` audit to know which digest entries were surfaced.
2. Add fixtures across stored-rule classes, not only PR:
   - project identity / source-of-truth correction,
   - API/component contract work,
   - UI/user-flow behavior work,
   - bug/regression/fix work,
   - runtime/test instance reasoning,
   - release/deploy/build workflow,
   - PR/body drafting as one example only.
3. Track a lightweight turn journal for surfaced digests.
4. Keep successful turns silent.
5. Measure latency and token size during dogfood.

## Rule placement

- Rule: the organic C+ v2 transition should focus on record digest quality, relevant-record indexing/query, pre-response digest surfacing, response.completed audit, and mandatory record completion; tool-attached project policies should be migrated out after coverage exists.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`
- Why not AGENTS.md: this is a multi-phase implementation plan, not final operating grammar.
- Why not `.jcode`: this is shared lazy-harness framework design, not local/private Jcode-only workflow.
- Confirmation: user-confirmed direction, implementation details pending future option gates.

## Discovery capture

- DDD: none.
- SDD: candidates for record digest, relevant-record query, pre-response context, response audit, guidance ladder.
- BDD: desired agent behavior is organic rule recognition before response and silent success when no issue exists.
- TDD: future fixtures required for PR/runtime/correction digest retrieval and audit behavior.
- ADR: ADR 0041 is active design direction.
- SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md` anchors mandatory record vs organic guidance split.
- Planning: this record is the comprehensive transition plan.
