# SDD — Record Digest Format

Status: accepted
Date: 2026-06-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related plan: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`
Related spec: `.lazy-harness/spec/platform/record-write-update-policy.md`

## Purpose

Lazy-harness records must be searchable and injectable as compact working context before an agent answers or plans.

The record digest format defines a small, stable section that lets tooling produce relevant-rule digests without dumping full records into context.

This supports the C+ v2 active memory loop:

```text
record creation/update
→ digest/index
→ relevant context before response
→ response.completed audit
→ record update again
```

## Non-goals

- Not a replacement for full DDD/SDD/BDD/TDD/ADR/SSOT records.
- Not a generated implementation index.
- Not a tool-specific guide.
- Not required on every historical record immediately.
- Not a place to duplicate long explanations or implementation maps.

## Required Markdown section

Records that carry reusable guidance SHOULD include a `## Rule digest` section.

A reusable guidance record is any record that future agents may need to apply before answering, planning, editing, validating, releasing, documenting, or deciding.

Minimal shape:

```md
## Rule digest

- Status: active | advisory | deprecated | reverted | needs-review
- Layer: DDD | SDD | BDD | TDD | ADR | SSOT | Planning
- Scope: framework-global | host-project | team-policy | layer-fact | transient-plan | jcode-local
- Applies when:
  - natural-language trigger or intent cue
  - artifact/action/context cue
- Must:
  - 1 concise rule bullet
  - 1 concise rule bullet
- Must not:
  - 1 concise anti-rule bullet, if useful
- Record completion:
  - when confirmed facts from this area appear, update `path/to/record.md`
- Related records:
  - `.lazy-harness/...`
```

Recommended compact example:

```md
## Rule digest

- Status: active
- Layer: SSOT
- Scope: host-project
- Applies when:
  - user asks about project identity, source of truth, ownership, runtime, DB, release, or validation
  - implementation touches this host's owned boundary
- Must:
  - consult this SSOT before deciding or implementing
  - update this SSOT when the user confirms an ownership/source-of-truth correction
- Must not:
  - store project/team policy only in `.jcode` or Jcode memory
- Record completion:
  - confirmed corrections update this record or a more specific SSOT
- Related records:
  - `.lazy-harness/spec/platform/project-rule-router.md`
```

## Field contract

### Status

| Value | Meaning | Query behavior |
|---|---|---|
| `active` | should be surfaced when relevant | include normally |
| `advisory` | helpful but not mandatory | include only when high relevance or low budget pressure |
| `deprecated` | no longer preferred, retained for history | exclude by default, include only for migration/debug |
| `reverted` | tried and intentionally backed out | exclude by default, include when user asks about history/why-not |
| `needs-review` | uncertain or stale | include with warning when directly relevant |

### Layer

Use the canonical layer label matching the record path:

- `DDD` → `.lazy-harness/domain/`
- `SDD` → `.lazy-harness/spec/`
- `BDD` → `.lazy-harness/behavior/`
- `TDD` → `.lazy-harness/tests/`
- `ADR` → `.lazy-harness/decisions/`
- `SSOT` → `.lazy-harness/ssot/`
- `Planning` → `.lazy-harness/planning/`

### Scope

Use the same scope vocabulary as Project Rule Router:

- `framework-global`
- `host-project`
- `team-policy`
- `layer-fact`
- `transient-plan`
- `jcode-local`

If ambiguous, do not guess. Use an option gate before committing canonical scope.

### Applies when

`Applies when` is the main retrieval surface for relevant-record query.

It should include user/task language, not tool names.

Good:

- `user asks to draft or update a PR description`
- `user discusses test database, runtime instance, dev server, or dogfood run`
- `user corrects ownership or source of truth`
- `implementation changes API/component contract`
- `bug fix or regression protection is requested`

Avoid as primary triggers:

- `when bash runs gh pr create`
- `when dev-cli is called`
- `when GitHub MCP create_pull_request is called`

Tool names may appear only as secondary examples if the underlying intent/artifact is also stated.

### Must / Must not

`Must` and `Must not` bullets are the digest payload that can be injected into the agent context.

Rules:

1. Keep each bullet under ~20 words where possible.
2. Prefer behavior over implementation detail.
3. Do not duplicate the entire record.
4. Include at most 5 total `Must`/`Must not` bullets by default.
5. If more are needed, the query should surface the path and require deliberate read.

### Record completion

This field tells response audit how to detect missing canonical writes.

Examples:

- `confirmed source-of-truth corrections update this SSOT`
- `new API contract decisions update the SDD record and cross-link ADR if trade-off exists`
- `bug fixes add or update TDD regression record plus layer completeness judgement`
- `new UI flow discoveries update BDD behavior record`

### Related records

Use paths, not prose-only references. These paths help query expand context without loading full documents.

## Digest output format

Relevant-record query should render digest entries like this:

```md
Relevant lazy-harness rules
- `.lazy-harness/spec/platform/project-rule-router.md` — Project Rule Router
  - Route confirmed project/team rules to canonical `.lazy-harness` records, not `.jcode` or memory.
  - If placement is ambiguous, stop with an option gate.
- `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — Organic Hybrid Rule Guidance
  - Use pre-response record query and response audit, not tool-specific project-policy branches.
```

Output limits:

- default target: 200–600 tokens,
- normal hard ceiling: 1,000 tokens,
- include path, title, and 1–3 bullets per record,
- never inject full records by default.

## Backwards compatibility

Existing records without `## Rule digest` remain valid.

Relevant-record query may fall back to headings, file path, status line, and first paragraphs while Phase 1 migration is incomplete.

However, records with enforcement language such as `must`, `required`, `source of truth`, `STOP`, `forbidden`, `confirmed`, or `mandatory` should gradually receive a digest.

## Migration guidance

Prioritize adding digests to records that:

1. encode user-confirmed policy,
2. are repeatedly missed in dogfood,
3. affect source-of-truth ownership,
4. define contracts or validation requirements,
5. contain negative constraints or forbidden actions,
6. would be expensive to miss.

Do not add digests to purely historical records unless they explain why a rejected path should not be repeated.

## Query/audit requirements

A relevant-record query implementation MUST:

- parse `## Rule digest` sections when present,
- respect `Status`, especially `deprecated` and `reverted`,
- use `Applies when` for natural intent matching,
- emit compact bullets only,
- include record paths for deliberate follow-up reads,
- stay root-bound to the current host.

A response audit implementation SHOULD:

- compare surfaced digest entries against the response,
- remain silent when no surfaced rule was ignored,
- flag missing record completion when the response confirms a fact/rule but no canonical record changed,
- avoid turning every advisory digest into a hard stop.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/spec/platform/record-digest-format.md` — this SDD contract.
  - `.lazy-harness/spec/platform/record-write-update-policy.md` — companion policy for updating records without duplicates/stale drift.
  - `.lazy-harness/planning/record-query-context-loop-transition-plan.md` — phase plan.
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md` — architecture decision.
- Future files:
  - `.lazy-harness/spec/platform/relevant-record-query.md`
  - `.lazy-harness/scripts/relevant-record-query.ts`
  - `.lazy-harness/generated/relevant-record-index.json`
  - `.lazy-harness/scripts/record-digest-audit.ts`
- Flow:
  1. A canonical record declares a digest.
  2. Relevant-record query ranks matching digests for the current user message/context.
  3. The agent receives a compact digest before responding.
  4. `response.completed` audits whether surfaced digest/record completion obligations were ignored.
- Tests / protection:
  - Future Phase 2/3 fixtures for PR/runtime/source-of-truth/API/BDD/TDD/release queries.
  - Current validation: `.lazy-harness/scripts/self-test.py`, `doctor.py --profile smoke`.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - Planning: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`
  - SDD: `.lazy-harness/spec/platform/record-write-update-policy.md`

## Rule placement

- Rule: records that carry reusable future guidance should expose a compact `## Rule digest` section so relevant-record query can surface them before response without full-document dumps.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/record-digest-format.md`
- Why not AGENTS.md: this is a platform contract for record format, not operational grammar for all turns.
- Why not `.jcode`: digest format is shared lazy-harness framework behavior, not local/private Jcode policy.
- Confirmation: user-confirmed direction via ADR 0041 and active transition plan.

## Discovery capture

- DDD: none.
- SDD: updated, this contract defines record digest format.
- BDD: candidate, future behavior should show agents receiving compact relevant rules before response.
- TDD: future fixtures needed for digest parsing/query output/token budget.
- ADR: ADR 0041 selected organic hybrid guidance.
- SSOT: harness enforcement policy anchors mandatory record vs organic guidance split.
- Planning: record-query context loop transition plan Phase 1.
