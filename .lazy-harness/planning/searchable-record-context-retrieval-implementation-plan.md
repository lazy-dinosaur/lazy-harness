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

Layer package completed:

- Phase B: Record Index Header Layer Package complete: DDD, BDD, SDD, TDD, and SSOT/ADR review done.
- SCR-702 source implementation and validation complete: Pi/OMP mid-turn steering advances a root evidence epoch, clears prior evidence, excludes late pre-steer results, and requires fresh post-steer map/read evidence. User authorized commit, push, and all initialized downstream sync on 2026-07-13; rollout is in progress.

Remaining not-started / blocked work:

1. Phase C: record-index parser/cache implementation is next todo under ADR 0042 and no-semantic-authority constraints.
2. Phase D: record-audit advisory warnings.
3. Phase F: implementation-map backlog migration.

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
- `record-index` as the deterministic cache generator after ADR 0042 and SCR-402 Option A
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
- Created SDD for `## Index header` as record-authored metadata.
- Created TDD with parser/audit/behavior expectations.
- Reviewed SSOT/ADR boundary: existing CLI tool boundary is sufficient for SCR-303/304; no ADR needed now.
- SCR-401 option gate completed: canonical name is `record-index`.

### Phase C — Record-index parser/cache implementation

- Status: complete for SCR-402 Option A.
- Canonical command/cache/schema/source names are `record-index`, `record-index.json`, `record-index.schema.json`, and `record-index.ts`.
- No `context-index` compatibility alias remains.
- Implementation is deterministic record-authored cache parsing/listing only.
- No raw-message query interface or semantic-authority output fields.

### Phase D — Record audit warnings

- Add advisory warnings for missing searchable metadata and implementation-map gaps.
- No historical hard block.

### Phase E — Host sync validation

- Sync cleanup to hosts.
- Verify stale helper files are pruned.
- Run host tests/doctor.

### Phase F — Pi/OMP steer evidence re-arming
- Status: source-validated; commit/push/all-initialized-host rollout authorized on 2026-07-13 and in progress.

- Detect non-extension, non-empty mid-turn steering without inspecting message meaning.
- Advance a root evidence epoch and clear prior recent-tool evidence.
- Bind allowed tool calls to their start epoch and ignore late results from older epochs.
- Preserve read-only map/read access while the generic pre-action guard blocks later actions.
- Protect prior-evidence invalidation, late-result exclusion, and fresh-evidence recovery with a fake runtime.
- Validation: focused Pi contract smoke passed; full framework self-test passed (`ran=84`, `skipped=0`); record-lint clean; graph rows valid/unique.
- Evidence: `.lazy-harness/evidence/2026-07-13-pi-steer-evidence-epoch-source-validation.md`

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
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — root-scoped steer evidence epochs and tool-call start-epoch tracking.
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

- DDD: searchable record memory terminology/invariants added and cited by Index Header SDD/TDD.
- BDD: LLM-owned retrieval scenarios added and mapped by Index Header TDD.
- SDD: removed obsolete helper contracts; added static search/read-debt SDD; added Index Header SDD.
- TDD: self-test and pre-action/pre-response/Pi package records protect static debt plus post-steer invalidation/recovery.
- ADR: ADR 0042 records cache naming; ADR 0041 remains the guidance authority for steer hardening.
- SSOT: runtime/shared-state and CLI semantic-authority boundaries remain unchanged.
- Planning: contaminated plan remains replaced; SCR-702 tracks the approved steer evidence boundary.

## Rule placement

- Rule: searchable record memory must improve LLM-owned evidence retrieval, not introduce code-owned semantic query helpers.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
- Why not AGENTS.md: multi-phase implementation plan.
- Why not `.jcode`: shared framework source behavior.
- Confirmation: user-confirmed correction on 2026-06-06.


## Discovery capture — SCR-303/304/305

- DDD: `.lazy-harness/domain/searchable-record-memory.md` includes instruction-scoped evidence.
- BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md` includes the post-steer freshness scenario.
- SDD: search-read-debt/pre-response/Pi package contracts updated.
- TDD: pre-action/pre-response/Pi package regression records updated.
- ADR: no new ADR; ADR 0041/0024 semantics are applied generically.
- SSOT: CLI semantic-authority boundary remains unchanged.
- Planning: SCR-702 and this plan track implementation/validation.
