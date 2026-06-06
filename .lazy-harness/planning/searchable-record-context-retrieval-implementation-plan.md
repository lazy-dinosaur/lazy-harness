# Implementation Plan — Searchable Record Memory without Query Helper Authority

Status: proposed
Date: 2026-06-06
Layer: Planning
Related PRD: `.lazy-harness/prd/searchable-record-context-retrieval-prd.md`
Related tasks: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
Related HTML report: `.lazy-harness/planning/searchable-record-context-retrieval-report.html`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related DDD: `.lazy-harness/domain/searchable-record-memory.md`
Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
Related SDD:
- `.lazy-harness/spec/platform/search-read-debt-contract.md`
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/spec/platform/record-digest-format.md`
- `.lazy-harness/spec/platform/implementation-map-standard.md`

## Summary

The corrected plan is cleanup-first. The previous plan was contaminated because it let helper code appear to choose candidate records from raw user text. That violates the user-confirmed boundary: LLM/searcher owns meaning and read priority after real evidence reads.

Correct architecture:

```text
user message
→ static harness-first search/read-debt reminder
→ LLM/searcher root-bound grep/read/source/test inspection
→ LLM/searcher decides relevant records, ambiguity gate, and next action
→ confirmed knowledge is stored in records with searchable metadata
→ deterministic caches may be regenerated from records only
```

## Current status — 2026-06-06

Completed:

- Phase A decontamination in source.
- Deleted helper absence protection.
- Static search/read-debt contract replacement.
- PRD/tasks/HTML report rewrite around LLM-owned retrieval.
- Graph/generated stale row cleanup.
- Phase E host sync validation across 13 initialized downstream hosts.

Evidence:

- `.lazy-harness/evidence/2026-06-06-searchable-record-memory-host-sync.md`
- Source validations: self-test, prompt-budget, graph-hygiene.
- Host smoke: sync exit 0, stale helper files 0, deleted helper help entries 0, stale hook output 0 for all 13 hosts.

Next not-started work:

1. Phase B: Record Index Header Layer Package: DDD/BDD done, SDD/TDD and SSOT/ADR review next.
2. Phase C: cache/parser naming and scope decision gate after layer package acceptance.
3. Phase D: record-audit advisory warnings.
4. Phase F: implementation-map backlog migration.

## Non-negotiable boundary

Allowed deterministic code:

- lifecycle transport and sanitized debt journaling
- evidence guard that checks whether search/read happened
- validation, hygiene, measurement, manifest sync
- generated caches from already-authored records/source/graph

Forbidden code behavior:

- raw user message → semantic candidate decision
- raw user message → requiredRead/confidence/intent/risk/gate/nextAction
- lifecycle hook invoking query helpers
- generated cache treated as proof of evidence read

## Immediate change set

### 1. Delete obsolete helper architecture

Remove:

- `context-delivery` helper source/schema/spec/test/fixtures
- `relevant-record-query` helper source/schema/spec/test
- `context-broker-dogfood` collector that depended on the deleted helper
- stale native query-helper planning record
- CLI commands that dispatched those helpers

Keep:

- `record-decision` explicit packet generator for supplied evidence flags
- `context-index` only as an existing deterministic cache generator until a naming/scope decision is made
- generic search/read-debt guard and response audit

### 2. Rename runtime debt journal

Rename the runtime state stream from the obsolete helper name to its actual purpose:

```text
$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl
```

This stream stores static protocol/evidence rows only.

### 3. Correct records and reports

Rewrite:

- PRD
- task backlog
- implementation plan
- HTML report
- pre-response/search-read-debt records
- runtime/shared-state records
- generated/schema README text
- graph/candidate stale rows

### 4. Add protection

Add self-test coverage so the deleted helper files and commands cannot reappear unnoticed.

## Phase plan

### Phase A — Decontamination

- Delete obsolete helper artifacts.
- Remove CLI commands.
- Rename runtime debt journal.
- Remove stale graph/candidate rows.
- Rewrite PRD/tasks/plan/report.
- Validate with grep, self-test, prompt-budget, graph-hygiene.

### Phase B — Record Index Header Layer Package

- Create/maintain DDD terminology for Searchable Record Memory and semantic authority.
- Create/maintain BDD scenarios for LLM-owned retrieval behavior.
- Create SDD for `## Index header` as record-authored metadata.
- Create TDD with parser/audit/behavior expectations.
- Review SSOT/ADR boundary before any cache/parser implementation.
- Do not implement parser yet unless separately approved.

### Phase C — Cache/parser decision gate

- Decide whether current `context-index` name is acceptable or should become `record-index`.
- Approve exact fields and output shape.
- Implement only deterministic record-authored cache parsing.
- No raw-message query interface.

### Phase D — Record audit warnings

- Add advisory warnings for missing searchable metadata and implementation-map gaps.
- No historical hard block.

### Phase E — Host sync validation

- Sync cleanup to hosts.
- Verify stale helper files are pruned.
- Run host tests/doctor.

## Validation commands

```bash
git ls-files | grep -E 'context-delivery|relevant-record-query|context-broker-dogfood|relevant-record-index|context-delivery-packet' && exit 1 || true
python3 .lazy-harness/scripts/self-test.py
.lazy-harness/bin/lazy prompt-budget --format=md
bun .lazy-harness/scripts/graph-hygiene.ts --format=json
```

## Implementation map

- Primary files:
  - `.lazy-harness/bin/lazy` — removes obsolete helper dispatch commands.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — static reminder and `search-read-debt.jsonl` writer.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — generic evidence guard.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — audit/backstop reader.
  - `.lazy-harness/scripts/self-test.py` — validates cleanup and guard behavior.
  - `.lazy-harness/spec/platform/search-read-debt-contract.md` — replacement SDD.
  - `.lazy-harness/prd/searchable-record-context-retrieval-prd.md` — corrected PRD.
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` — corrected backlog.
- Removed files:
  - obsolete query-helper source/schema/spec/test/fixtures listed in SCR-001.
- Protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - prompt-budget and graph-hygiene.

## Layer completeness impact

- DDD: searchable record memory terminology/invariants added; future Index Header SDD must cite it.
- BDD: LLM-owned retrieval scenarios added; future TDD must protect them.
- SDD: removed obsolete helper contracts; added static search/read-debt SDD; Index Header SDD planned.
- TDD: self-test and pre-action/pre-response records updated; Index Header TDD planned.
- ADR: no new ADR; implements accepted CLI boundary correction.
- SSOT: runtime/shared-state and CLI boundary updated.
- Planning: contaminated plan replaced.

## Rule placement

- Rule: searchable record memory must improve LLM-owned evidence retrieval, not introduce code-owned semantic query helpers.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
- Why not AGENTS.md: multi-phase implementation plan.
- Why not `.jcode`: shared framework source behavior.
- Confirmation: user-confirmed correction on 2026-06-06.
