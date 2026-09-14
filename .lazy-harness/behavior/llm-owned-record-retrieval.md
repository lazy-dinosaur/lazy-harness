# BDD — LLM-Owned Record Retrieval

Status: accepted
Date: 2026-06-06
Layer: BDD
Related DDD: `.lazy-harness/domain/searchable-record-memory.md`
Related PRD: `.lazy-harness/prd/searchable-record-context-retrieval-prd.md`
Related SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: BDD
- Scope: framework-global
- Aliases:
  - LLM 검색 주체
  - 검색 행동 규약
  - retrieval behavior
  - 메타데이터 큐
  - Harness Reader retrieval
  - Reader/Parent parallel join
- Applies when:
  - a dedicated Harness Reader starts retrieval for a Parent work unit
  - the Reader inventories and searches stored harness records before Parent action
  - the Parent concurrently investigates source/tests or immediately needed behavior
  - retrieved metadata conflicts, is incomplete, or could be mistaken for semantic authority
- Must:
  - launch one dedicated Reader at the beginning of a Reader-managed work unit
  - make that Reader run `lazy map --overview`, select task-relevant records across DDD/SDD/BDD/TDD/ADR/SSOT/Planning, and read the real canonical bodies
  - let the Parent concurrently inspect source/tests, implementation reality, or immediately needed behavior
  - require the Parent to await and consume the Reader response before planning, mutation, or host-specific completion
  - treat a completion-only wait/status acknowledgement as insufficient: the content-bearing Reader result with `complete|incomplete|conflict` status must reach the Parent before the join is satisfied
  - preserve the Parent's substantive user-facing answer when a post-response advisory creates a continuation; an advisory-only final output is not a completed Reader-managed work unit
  - return applicable policies, facts, conflicts, missing information, record paths, and `complete|incomplete|conflict` status
  - use metadata as cue-only navigation inside the Reader; canonical record bodies remain the evidence
  - ask an option gate or perform bounded Parent follow-up when the Reader reports conflict/incomplete or fails
  - update durable records after user confirmation when missing host knowledge is found
  - after a non-extension mid-turn steer, invalidate an earlier Reader result before later action
- Must not:
  - answer or mutate based only on cache/header existence
  - require the Parent to preselect concrete record nodes for the Reader
  - require routine Parent rereads of Reader-covered records to satisfy search/read debt
  - treat the Reader as source-code investigator, semantic decision maker, writer, validator, or proof/audit system
  - rerun overview, reread unchanged records, or replay mapped record/catalog output solely because a normal message occurred
- Record completion:
  - changes to retrieval behavior update this BDD, DDD terminology, SDD contract, TDD fixtures, tasks, and HTML report together.

## Scenarios

### Scenario 1 — Metadata cue still requires real record read

Given a user request touches a host detail
And a future Record Index Header lists aliases or source/test hints
When the agent uses the metadata to choose where to start
Then the agent reads the actual record body and Rule digest
And reads implementation maps/source/tests when implementation facts matter
And only then answers, plans, or edits.

### Scenario 1a — Record Map narrows the first pass only

Given a user request touches a host detail
When the agent runs `lazy map --overview` first
Then the output shows whole record/feature/graph structure for choosing concrete feature ids, record paths, graph ids, source paths, or test paths
And when the agent repeatedly runs `lazy map <feature-id|record-path|graph-id|source-path>` for nodes copied from the map
Then the outputs may suggest dispersed feature, record, graph, source, and test candidates
And free-form natural-language query text is rejected because `lazy map` is traversal, not semantic search
But those candidates are cue-only
And the agent must still read all relevant actual record bodies, Implementation maps, source, and tests before answering or mutating.

### Scenario 2 — Conflicting meanings require option gate

Given metadata or grep finds multiple plausible records/layers
When the agent cannot establish one meaning from canonical records/source/tests
Then the agent presents 3-5 options with one recommended option
And does not choose on behalf of the user.

### Scenario 3 — Cache hit is not proof of evidence

Given a generated cache lists a record, alias, or source path
When pre-action search/read debt is still unsatisfied
Then the agent must perform root-bound record/source/test reads
And the cache hit alone must not satisfy evidence debt.

### Scenario 4 — Missing knowledge converges after confirmation

Given a needed host fact is missing from `.lazy-harness`
When source/docs/package/config provide one likely fact
Then the agent asks a short confirmation if needed
And writes the confirmed fact into the correct DDD/SDD/BDD/TDD/ADR/SSOT record.

### Scenario 5 — New retrieval concept triggers layer package

Given a new retrieval concept changes terminology, behavior, component contract, or regression fixtures
When planning the next phase
Then DDD, BDD, SDD, TDD, and SSOT/ADR impact must be considered together
And “SDD/TDD only” is insufficient unless DDD/BDD are explicitly judged not impacted.

### Scenario 6 — Search and final verification check for missing related layers

Given a retrieved record declares top-level `Related DDD`, `Related BDD`, `Related SDD`, `Related TDD`, `Related SSOT`, or similar layer links
When an agent/searcher uses `lazy map`, `record-index`, or `lazy retrieval-audit` during search or final validation
Then those related record paths must be surfaced as cue-only candidates
And the agent checks whether any impacted DDD/BDD/SDD/TDD/ADR/SSOT records are missing before writing records, committing, or reporting completion.

### Scenario 7 — Overview-first guidance is advisory, not a tool block

Given `lazy map --overview` is the required first inventory step
When an agent/searcher has not yet inspected the overview output
Then the agent/searcher should prefer a standalone sequential overview before choosing dependent `lazy map <node>`, grep, source reads, or record reads
But `batch` or `multi_tool_use.parallel` tool shapes containing `lazy map --overview` are not hard-blocked
And the generic search/read evidence guard still blocks mutation until root-bound record/source/test evidence exists.

### Scenario 7a — Mid-turn steer requires fresh evidence

Given an agent has valid root-bound evidence for the current instruction
And the user sends a non-extension mid-turn steer
When the agent next attempts a mutating action
Then the adapter invalidates the previous instruction's evidence cache
And ignores late tool results from tool calls that started before the steer
And the action remains blocked until a map/read tool call started after the steer produces fresh root-bound evidence
And this behavior does not classify the steered text or maintain command-specific rules.

### Scenario 7b — Normal follow-up reuses work-unit evidence

Given the agent completed one overview and directly read the governing records for the active work unit
And those record content fingerprints are unchanged
When the user sends another normal follow-up in the same runtime session
Then Pi/OMP reports `reused-work-unit`
And does not inject the full grounding prompt, rerun map/catalog commands, or require the same records to be read again
But a changed/deleted governing record or explicit steer invalidates reuse before the next mutation.

### Scenario 8 — Dynamic write/read loop treats graph as cue, not truth

Given an agent is iterating through search, record/source edits, validation, and follow-up reads
And generated graph/query/explain output suggests ranked candidates
When the agent has just changed records, source, tests, manifests, or graph rows
Then the agent may use graph output as a routing accelerator only
And must read the changed canonical records/source/tests directly before relying on the result
And must run focused validation when implementation or record truth changed
And must not treat generated graph state as fresher than the canonical files.

### Scenario 9 — Reader searches harness memory while Parent inspects code

Given a Parent starts a host-dependent work unit
When it launches one dedicated Harness Reader
Then the Reader inventories all stored `.lazy-harness` layers and selects/reads the task-relevant canonical policy and fact records
And the Parent concurrently inspects source/tests or immediately needed behavior
And the Parent does not preselect the Reader's record nodes.

### Scenario 9a — Reader completion is the join barrier, not read debt

Given the Reader returns applicable policies, facts, conflicts, missing information, record paths, and `complete` status
When the Parent reaches planning, mutation, or a host-specific completion claim
Then it waits for and consumes that response
And it does not reread the same records merely to clear a Parent debt journal
But it directly reads a record when the response is incomplete/conflicted, the Reader failed, or that exact record will be edited.

### Scenario 9b — Reader does not own implementation reality

Given the Reader's lane is canonical harness records
When implementation facts matter
Then the Parent's concurrent lane reads source/tests and reconciles code reality with the Reader's policies/facts after the join
And the Reader does not mutate, decide, validate, or fan out.

### Scenario 9c — Reader result content, not completion acknowledgement, closes the join

Given the Parent launched one asynchronous dedicated Reader
And the runtime reports that the child process completed
When the Parent reaches the join barrier
Then a `done`/`complete` acknowledgement without the Reader's content is not sufficient
And the Parent waits until the content-bearing Reader result is present in its context
And only that result's `complete`, `incomplete`, or `conflict` status controls the normal/fallback path.

### Scenario 9d — Post-response advisory cannot erase the joined Parent answer

Given the Reader result reached the Parent
And the Parent synthesized a substantive user-facing answer after the join
When `agent_end` emits a post-response advisory in headless text/print or JSON mode
Then the caller-visible final output still contains the complete substantive answer
And any advisory resolution is integrated into that answer or delivered out of band
But an advisory-only last assistant message must not replace the primary answer.
And the unresolved advisory remains observable on stderr without another assistant turn
And native Reader content continuation/drain, pending waits, user steers and required action blocks are not suppressed
And TUI/RPC behavior remains unchanged.
And a headless typed capture assessment is persisted as runtime metadata, not appended as the last conversation message
And pending/unverified capture remains visible on stderr with semantic relevance and approval explicitly not runtime-verified
And even `triggerTurn:false` capture must not hide the primary text output; interactive capture keeps its non-steering custom message.

### Scenario 9d.1 — Quoted Reader identity has transport-independent status

Given a native Reader RESULT has bare identity values or one balanced backtick pair
When its actual content reaches the Parent through a synchronous tool receipt or async notification
Then exact root/revision/epoch identity and the full trusted terminal ledger remain authoritative
And duplicate, conflicting, missing or malformed identity/status is rejected
And `incomplete` or `conflict` remains that distinct bounded-fallback outcome even if the caller asks for complete
And details-only finalOutput or wait/status acknowledgements never become delivered evidence.

### Scenario 9e — Parent read-only source lane stays available while Reader is pending

Given the dedicated Reader is running and its content join is not yet complete
When the Parent inspects implementation source/tests using native read/grep/find or one simple read-only shell command
Then the Reader pending barrier does not classify that inspection as an action
And actual mutation remains blocked until join or explicit fallback.

### Scenario 9f — Owned status is inspection, not completion

Given the current root/evidence epoch has one pending owned Reader run
When the Parent has a purposeful reason to inspect its ordinary status or bounded transcript
Then that exact run's one-shot read-only status call is available without prior canonical evidence
But wrong, unknown, stale, cross-root, launch, resume, steer, or mutation-like operations remain under the existing action boundary
And status/transcript text cannot satisfy canonical evidence, native content receipt, `lazy_reader_join`, or legacy evidence caches
And when no independent Parent work remains, the Parent yields runtime control for native async notification instead of status/shell polling or a premature user-facing final.

### Scenario 9g — Derived per-read cap makes the Reader total mechanically simple

Given the Parent selected `maxReadCalls` and `maxRequestedLines`
When it launches the Reader
Then `maxLinesPerRead` equals `floor(maxRequestedLines / maxReadCalls)` in the task and launch state
And every Reader body read uses an explicit limit no larger than that cap
And the result reports `maxObservedReadLimit` for join validation.

## Usability checks

- The behavior should make it obvious to an agent that metadata is a navigation aid, not an answer.
- The behavior should reduce repeated broad grep work without replacing evidence reads.
- The behavior should surface ambiguity early instead of silently ranking candidate meanings.

## R3 correction — pending failure and one final response

If Parent source inspection fails while the Reader is pending, stop new source work but drain the already-running child before the final response. A no-fallback canary consumes the packet and reports terminal failure once, without an incomplete join or a premature final response. Normal work retains bounded fallback. Prefer native source tools; `.lazy-harness/scripts/` is implementation source, while canonical record directories remain Reader-owned. Do not add shell redirection, including `2>/dev/null`.

This is guidance implemented in `.lazy-harness/AGENTS.md` and `packages/lazy-harness-pi/prompts/lazy-harness.md`, not a new runtime suppression of arbitrary Parent output. Live success remains unproven until separately observed.

## Implementation map

- Status: `live-r2-incomplete; adversarial static correction reviewed-ok-and-standard-green-in-isolated-worktree; new-live-approval-and-main-integration-pending`
- Core repair protection: `.lazy-harness/tests/reader-result-primary-answer.md`, `packages/lazy-harness-pi/tests/reader-result.test.ts` and `packages/lazy-harness-pi/tests/reader-primary-answer-cli.test.ts` exercise shared RESULT parsing and real production capture/placement after multi-claim answers in actual headless CLI text/JSON.
- Primary files:
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md` — this BDD behavior record.
  - `.lazy-harness/domain/searchable-record-memory.md` — DDD terms used by the scenarios.
  - `.lazy-harness/scripts/record-index.ts` — indexes top-level Related layer links into cue-only related-record metadata.
  - `.lazy-harness/scripts/record-map.ts` — read-only `lazy map` implementation that lists cue-only candidates.
  - `.lazy-harness/scripts/retrieval-coverage-audit.ts` — read-only coverage audit that surfaces related-record candidates plus structural coverage gaps.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` and `.lazy-harness/AGENTS.md` — advertise Reader-first grounding and bounded direct fallback.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` / `check-search-performed.sh` — accept exact joins and keep safe Parent source inspection available while Reader/search debt is pending.
  - `packages/lazy-harness-pi/agents/record-reader.md` — dedicated canonical-record-only Reader.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — validates Reader launch, narrowly classifies owned current status outside canonical evidence bookkeeping, tracks native content completion, closes explicit content join, caches record fingerprints, invalidates on steer, and preserves print-mode primary output.
  - `.lazy-harness/evidence/dedicated-reader-runtime-v1-20260906.md` — isolated validation/review evidence.
  - `.lazy-harness/evidence/dedicated-reader-live-canary-r2-20260906.md` — live delivery/join pass plus budget/source-lane incomplete evidence and selected correction.
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` — schedules the layer package.
- Key symbols:
  - `buildRecordMap` (`.lazy-harness/scripts/record-map.ts`) — emits candidate records/source/tests/graph ids without semantic-authority fields.
  - `extractTopLevelRelatedRecords` (`.lazy-harness/scripts/record-index.ts`) — parses `Related <Layer>:` links as cue-only related-record paths.
  - `buildAudit` (`.lazy-harness/scripts/retrieval-coverage-audit.ts`) — includes related-record paths during coverage audit without becoming semantic authority.
  - `ReaderRunState` / `readerLaunchValidationError` / `parseReaderRunId` / `lazy_reader_join` (`index.ts`) — implement launch identity, content-not-ack join, derived per-read cap/max-observed validation, budget/failure fallback, and fingerprint reuse.
  - `rearmEvidenceAfterSteer` / `toolResultBelongsToCurrentEvidenceEpoch` (`index.ts`) — invalidate prior Reader/direct evidence and accept only current-epoch results.
  - `check-overview-batch-order.py` — compatibility helper that intentionally emits no deny output; batching policy is advisory while mutation safety stays in `check-read-debt-permit.py`.
- Flow:
  1. For the accepted target, Parent launches one Reader at work-unit start.
  2. Reader runs complete harness overview, relevant drill-down, and real record reads across applicable canonical layers.
  3. Parent concurrently reads source/tests or immediately needed behavior.
  4. Parent joins the Reader response before planning/mutation/completion.
  5. `complete` supplies work-unit harness context without duplicate Parent debt reads; `incomplete`/`conflict`/failure triggers bounded follow-up or option gate.
  6. Confirmed missing knowledge is persisted into records.
  7. Isolated implementation lets a successful Reader join satisfy the transitional debt bridge; direct Parent map/read remains the non-complete/unavailable fallback until main integration.
  8. A non-extension mid-turn steer invalidates the prior Reader result for later action.
  - `.lazy-harness/tests/pre-action-search-evidence-guard.md` — protects evidence before action.
  - `.lazy-harness/tests/record-index-header.md` — includes `lazy map` drill-down output and no-semantic-authority checks.
  - `.lazy-harness/tests/retrieval-coverage-audit.md` — protects cross-layer related-record candidates and missing-completeness checks.
  - `.lazy-harness/scripts/self-test.py#check_tool_execute_before_hook` — protects complete Reader join allow versus incomplete join deny alongside direct fallback.
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — protects package registration, launch envelope, pending barrier, completion-not-join, cumulative budget, explicit join, fingerprint reuse, steer invalidation, and print output separation.
- Cross-layer links:
  - DDD: `.lazy-harness/domain/searchable-record-memory.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Machine index:
  - graph ids: `kg_llm_owned_retrieval_behaves_from_domain`, `kg_record_index_header_layer_package_planned`, `kg_record_index_top_level_related_parser_20260608`, `kg_retrieval_audit_cross_layer_related_self_test_20260608`, `kg_overview_batch_order_guard_20260608`, `kg_overview_batch_order_guard_self_test_20260608`, `kg_pi_steer_evidence_epoch_impl_20260713`, `kg_pi_steer_evidence_epoch_test_20260713`
  - generated index key: pending until index generator exists

## Layer completeness impact

- DDD: updated — `.lazy-harness/domain/searchable-record-memory.md` defines Harness Reader, Parent code lane, and Reader join.
- BDD: updated — this record owns the user/agent-visible parallel flow.
- SDD: updated — `.lazy-harness/spec/platform/search-read-debt-contract.md` records target Reader-join supersession and current transitional hooks.
- TDD: updated — Reader join/fallback and package delivery fixtures are focused-green in the isolated worktree; live model smoke remains pending.
- SSOT: updated — mandatory recall remains, with Reader completion as the target mechanism.
- ADR: updated — ADR 0055 supersedes Parent-global/child-scoped read-debt ownership.
- Planning: updated — v3 proof remediation is superseded.

## Rule placement

- Rule: LLM-owned retrieval behavior belongs in BDD because it describes how the agent/searcher should act across multi-step record/source/test discovery flows.
- Scope: framework-global
- Primary record: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- Why not SDD only: the behavior is user/agent flow, not merely a component contract.
- Why not `.jcode`: shared lazy-harness framework behavior.
- Confirmation: user-corrected on 2026-06-06 that BDD is required before SDD/TDD-only planning.
- Confirmation: user-corrected on 2026-08-26 that the Reader owns stored harness retrieval while the Parent concurrently owns code/behavior investigation and joins before action.
- Confirmation: user-reaffirmed after the 2026-09-04 topology run that subagent-based reading is the selected architecture; delivery/output defects require the implementation to conform to the Reader design rather than reverting retrieval to the Parent.

## Discovery capture — Harness Reader ownership correction

- DDD: updated.
- SDD: updated.
- BDD: updated here.
- TDD: updated with planned protections.
- ADR: updated.
- SSOT: updated.
- Planning: updated; isolated runtime implementation is focused-green, while live model smoke and main integration remain unapproved.

## Discovery capture — Reader result/output correction

- DDD: none; Harness Reader, Parent code lane, and join are already defined terms.
- SDD: candidate/updated in the linked search-read-debt and Pi package contracts for content-bearing join and primary-answer preservation.
- BDD: updated here with result-content and caller-output scenarios.
- TDD: candidate/updated in the linked pre-action and Pi package regressions; scenarios remain non-executable until implementation approval.
- ADR: updated in ADR 0055 to reaffirm the selected Reader architecture.
- SSOT: none; no deployed ownership, settings, or runtime state changed.
- Planning: updated in the orchestration pilot; direct Parent is only the non-complete/unavailable fallback.

## Discovery capture — Reader behavior implementation

- DDD: implementation status only; terms unchanged.
- SDD: updated with actual Reader/join/debt/output behavior.
- BDD: updated here because scenarios 9–9d now have an isolated focused-green implementation.
- TDD: updated with passing focused fixtures; no live model or integrated-main claim.
- ADR: ownership unchanged; implementation status updated.
- SSOT: direct debt remains a transitional fallback in the isolated implementation.
- Planning: isolated slice implemented; validation/review and integration gates remain.

## Native delayed-content and accounting follow-up — isolated only

Given the Parent finishes its independent turn before the Reader delivers,
when the native headless runtime drains work,
then it also flushes held content and awaits owned terminal result delivery,
and the Pi SDK continues with that content to a substantive answer without polling, sleeps, or repeated nudges.

Given a Reader requests a seventh body read under a six-read launch,
then the guard denies it before execution and records a failure; a failed admitted read retains its count and requested lines.
When the model reports inaccurate counters or confuses child execution identity with the outer run,
then Parent may omit join identity/counters and use runtime-owned defaults; explicitly supplied mismatches, stale/sibling notifications, or missing ledger enable bounded fallback rather than weakening the join.
Semantic record selection and answer quality remain LLM judgments, not consequences of count conformance.

Implementation map: `packages/lazy-harness-pi/agents/record-reader.md`, `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`; native copy sources/tests and offline SDK evidence are linked in `.lazy-harness/evidence/reader-coordination-repair-and-comparison.md`. Primary TDD: `.lazy-harness/tests/pi-agent-package.md`; contract: `.lazy-harness/spec/platform/pi-agent-package.md`. Installed runtime/main integration remain separately gated.

## Runtime-owned path handoff — isolated regression

Given the Reader successfully reads six canonical files and its trusted terminal ledger records all six,
when Parent omits `recordPaths` or reports only five distinct successful paths,
then complete join verifies and caches all six, exposes the effective paths, and does not fall back solely for omission.
An empty legacy list also cannot erase the successful read set.
When a supplied path was not read, escapes the canonical lane, is duplicated or malformed,
or any ledger-recorded file changed/disappeared (even one absent from the Parent list),
then the join remains fail-closed into bounded fallback. Existing run/root/epoch/model/task and budget/failure guards still apply.
This does not certify semantic completeness or whole-file reading.

Implementation map: `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#lazy_reader_join`; `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`; primary TDD `.lazy-harness/tests/pi-agent-package.md`; path contract `.lazy-harness/spec/platform/search-read-debt-contract.md`.
