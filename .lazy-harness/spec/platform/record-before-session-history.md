# Record Before Session History

Status: accepted
Layer: SDD
Related AGENTS: `.lazy-harness/AGENTS.md` §2.1, §2.5
Related SSOT: `.lazy-harness/ssot/project-identity.md`
Related SDD: `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - record 우선
  - 세션 검색 나중
  - session history fallback
- Applies when:
  - user asks about recorded, planned, or intended work (기록/계획/handoff, SSOT/ADR/spec/behavior)
  - choosing between searching `.lazy-harness` records and searching previous chat sessions
- Must:
  - search `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,plans,knowledge}` first
  - use `session_search`/`conversation_search` only as fallback when durable records are missing/insufficient
  - converge reusable session-history discoveries back into records, candidates, or planning
- Must not:
  - treat previous session transcripts as the source of truth for project plans, rules, or recorded work
- Record completion:
  - when history reveals reusable knowledge, converge it into the right `.lazy-harness` record or candidate
- Related records:
  - `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
  - `.lazy-harness/ssot/project-identity.md`
  - `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`

## Purpose

When a user asks for something that should have been recorded, planned, or left as intended work, agents must search durable lazy-harness records before searching previous chat sessions.

Previous session transcripts are fallback evidence, not the source of truth for project plans, rules, or recorded work.

## Trigger cues

This applies when the request or response mentions any of:

- `기록`, `record`, `recorded`, `레코드`
- `계획`, `plan`, `planning`, `backlog`
- `하려고`, `하려던`, `정리해둔`, `handoff`
- `SSOT`, `ADR`, `decision`, `spec`, `behavior`
- `.lazy-harness`

## Required order

1. Search/read `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,plans,knowledge}/` first.
2. Only if durable records are missing or insufficient, use `session_search` / `conversation_search` as fallback.
3. If session history reveals reusable knowledge, converge it into records, candidates, or planning artifacts.
4. If the user explicitly asks for chat transcript only, session history may be searched first.

## Anti-pattern caught from dogfooding

```text
User: 우리 기능패널 어떤거 수정하려고 계획했었지?
Agent: session_search first
User: 아니 기록해둔거 있었잖아
Agent: then searches .lazy-harness records
```

This is wrong because the user asked for recorded/planned project knowledge, not chat transcript recall.

## Lifecycle helper behavior

`check-record-before-session-history.sh` runs from `on-response-completed.sh`.

It emits STOP when:

- record/plan/intended-work cues are present,
- `session_search` or `conversation_search` appears in recent tool calls,
- no `.lazy-harness` record/planning/knowledge search happened earlier in the same recent-tool sequence,
- and the response does not explicitly say the user requested chat transcript only.

It allows:

- record-first search followed by session fallback,
- explicit chat-log-only requests,
- unrelated exact chat recall without durable-record cues.

## Discovery capture

- DDD: none.
- SDD: this contract defines retrieval ordering for recorded project knowledge.
- BDD: agent-visible behavior should feel like "check the project memory first, then chat logs only if needed".
- TDD: self-test fixtures cover session-first block and record-first pass.
- ADR: no new trade-off beyond ADR 0024 and ADR 0034.
- SSOT: project identity and record-first rules remain canonical.
- Planning: none.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/record-before-session-history.md` — this SDD contract.
  - `.lazy-harness/AGENTS.md` — grammar requiring records/planning before session history for recorded/planned work.
  - `.lazy-harness/hooks/lifecycle/helpers/check-record-before-session-history.sh` — response-completed guard.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — invokes the helper.
  - `.lazy-harness/scripts/self-test.py` — regression fixtures.
- Key symbols:
  - `check_record_before_session_history_helper` (`.lazy-harness/scripts/self-test.py`) — validates block/pass/chat-only cases.
  - `run_record_before_session_history_helper` (`.lazy-harness/scripts/self-test.py`) — helper runner.
- Flow:
  1. User asks for recorded/planned/intended work.
  2. Agent must search `.lazy-harness` records/planning/knowledge first.
  3. Session history is allowed only as fallback evidence.
  4. Any reusable history discovery converges back into records/candidates/planning.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `bash -n .lazy-harness/hooks/lifecycle/helpers/check-record-before-session-history.sh`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
  - SSOT: `.lazy-harness/ssot/project-identity.md`
  - ADR: `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
- Machine index:
  - graph ids: `kg_sdd_record_before_session_history`
  - generated index key: `pending until implementation-index generator exists`
