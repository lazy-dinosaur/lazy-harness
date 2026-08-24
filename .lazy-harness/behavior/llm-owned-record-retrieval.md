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
- Applies when:
  - an agent/searcher uses searchable record memory before answering, planning, or editing
  - an agent/searcher starts a retrieval flow with `lazy map --overview`
  - an agent/searcher runs `lazy map <feature-id|record-path|graph-id|source-path>` to inspect a concrete map node
  - `## Index header` or other metadata suggests records/source/tests
  - retrieved metadata conflicts, is incomplete, or could be mistaken for semantic authority
- Must:
  - use metadata as a starting cue only
  - prefer `lazy map --overview` as the first inventory call for a new work unit, not for every normal message
  - treat `lazy map` output as drill-down candidates, not evidence that anything was read
  - read the real governing record body/Rule digest/Implementation map before the first mutation or host-specific completion claim
  - reuse directly read governing-record evidence across later normal messages while its content fingerprint remains unchanged
  - inspect source/tests when a plan or mutation depends on implementation facts
  - ask a 3-5 option gate when meanings/layers still conflict after evidence reads
  - create or update durable records after user confirmation when missing host knowledge is found
  - after a non-extension mid-turn steer, treat prior work-unit evidence as stale for later actions and gather fresh root-bound map/read evidence
  - when delegating record loading, keep complete overview discovery and semantic authority with the Parent; use explicit `candidate-map` only for non-authoritative evidence-question proposals and `claim-evidence` only for one Parent-approved bundle
  - for rule-recall questions, let the Parent supply behavior/guidance coverage facets and concrete canonical nodes, let the Reader return bounded records-backed questions plus `parentMustRead`, and keep the final guidance-versus-hard-stop interpretation and direct governing read with the Parent
  - conserve Parent-supplied objective facets/inventory entries through candidate assignment, explicit Parent exclusion, or blocking unmapped status; reopen the map when evidence loading discovers a new question, overlap, or dependency
  - treat compact output size accuracy-first: exceeding the 6,000 soft target may warn but must not delete evidence; inability to fit the 12,000 hard cap returns `overflow` with split detail
  - selectively reread governing, conflicting, high-risk, decision-critical, and sampled packet evidence before action
- Must not:
  - answer or mutate based only on cache/header existence
  - treat batched `lazy map --overview` output as proof that dependent follow-up calls were evidence-informed or read-satisfying
  - treat metadata field names as requiredRead, confidence, risk, gate, or next-action output
  - skip DDD/BDD impact when a new retrieval concept or behavior appears
  - rerun overview, reread unchanged records, or replay mapped record/catalog output solely because a normal message or read operation occurred
  - let a Reader run complete overview, self-certify task-global claim completeness, silently drop an input facet, recursively fan out, or return bundle `complete` while new evidence questions remain
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

### Scenario 9 — Parent discovery delegates scoped record loading

Given the Parent has run complete lean overview discovery for the work unit
And directly read the operating or governing records that control its own action
When bounded record loading may benefit from context sharding
Then the Parent freezes root/revision/canonical snapshot/overview/evidence-epoch identity
And supplies concrete nodes, objective facets, selected inventory entries, explicit exclusions, allowed layers, and hard budgets
And no Reader may run overview or satisfy Parent read debt.

### Scenario 9a — Candidate map proposes questions, not claims

Given the Parent supplies a `candidate-map` Work Packet
When the Reader drills the supplied nodes and reads bounded canonical evidence
Then every Parent facet/inventory entry is assigned to an unverified evidence question, remains blocking-unmapped, or matches a Parent-authored exclusion
And every proposed question carries direct path/content-hash/range provenance
And cycles or strong evidence overlap are proposed as one bundle
And any unmapped facet, unresolved overlap/cycle, overflow, or gap prevents `proposal-ready`
And the Parent approves or rewrites every evidence bundle.

### Scenario 9b — Approved evidence bundles may load independently

Given the Parent has approved an input-relative candidate map
When at least two evidence bundles are dependency-safe and sufficiently disjoint
Then separate `claim-evidence` Reader instances may load those bundles in parallel through the existing runtime
And each packet echoes immutable work/map/bundle identity and returns direct path/hash/range provenance
And the Parent waits for one accepted terminal packet per approved bundle
And shared evidence has one Parent-approved owner rather than accidental duplicate authority.

### Scenario 9c — Newly discovered evidence reopens the map

Given a claim-evidence Reader discovers an exception, term, conflict, overlap, dependency, or out-of-bundle evidence question
When it prepares its packet
Then it returns `needs-remap` plus `newEvidenceQuestions` and provenance
And it does not recursively launch another Reader or silently widen scope
And the Parent rechecks freshness, reopens or invalidates the candidate map, and chooses the next bounded action
And bundle `complete` is permitted only when every approved question/facet is addressed with no blocking gap, conflict, overflow, or new question.

### Scenario 9d — Small or overlapping work does not require decomposition

Given candidate routing produces one bundle, strong overlap/cycles, or Parent verification cost comparable to direct loading
When the Parent reviews the non-authoritative routing recommendation
Then the Parent uses one Reader or loads the evidence directly
And no automatic admission threshold or production fan-out is inferred from this contract-only implementation.

### Scenario 9e — Rule recall uses the Reader as evidence, not policy authority

Given a stored harness rule may have been skipped or misclassified as code enforcement
And the Parent has directly read the governing grammar and supplied behavior/guidance facets plus concrete BDD/ADR/SDD/SSOT nodes
When the existing `candidate-map` or approved `claim-evidence` flow loads the bounded rule evidence
Then the Reader returns direct path/hash/range provenance and `parentMustRead` for the relevant canonical rules
And the Parent directly reads those records and decides whether the obligation is agent behavior, ordinary guidance, or an independently promoted hard stop
And the Reader neither receives the full Parent grammar nor becomes a second policy resolver nor clears Parent read debt
And a new rule-candidate field or role is added only if this exact bounded shadow demonstrates that the existing evidence-question contract cannot carry the needed records.

Measured 2026-08-24 shadow: run `a9c9bf32-7dd5-4a01-80c7-73acd90b2f33` used the unchanged fields to identify skipped retrieval as the failure class, separate organic guidance/search-read evidence from a new tool-specific L5, preserve Parent rule authority, return ADR 0041 plus enforcement SSOT in `parentMustRead`, and recommend one overlapping bundle. This supports the responsibility split and demonstrates no semantic need for a new rule-specific role/field on this case. The packet itself was not admitted—8,310/6,000 characters and one range-inventory mismatch—so it remains qualitative behavior evidence only.

### Scenario 9f — Soft target never causes evidence trimming

Given compact v2 has a 6,000 output target and 12,000 hard cap
When complete, accurate evidence exceeds the target but still fits the hard cap
Then the Reader preserves the evidence and Parent admission returns a visible over-target warning without invalidating it
But when accurate closure cannot fit the hard cap
Then the Reader returns `overflow` with bounded split detail rather than deleting claims, exceptions, risks, conflicts, coverage, or provenance.

Measured compact canary `79dd9d1c-0ff8-4a62-b929-8e189e678d0c`: v2 admission accepted `proposal-ready` at 3,143 characters with no warning, down 62.2% from the prior 8,310. It retained both rule-recall questions, all eight inputs, direct evidence, risks, Parent rereads, verification, overlap, one bundle, and single-reader routing with no decision-relevant loss. One non-material protocol deviation remains: both bodies were read before both hashes rather than immediate read→hash interleaving; hashes matched before output. The over-target branch remains fixture-only.
## Usability checks

- The behavior should make it obvious to an agent that metadata is a navigation aid, not an answer.
- The behavior should reduce repeated broad grep work without replacing evidence reads.
- The behavior should surface ambiguity early instead of silently ranking candidate meanings.

## Implementation map

- Status: `verified-behavior-compact-v2-canary-admitted`; one bounded rule-recall canary preserved semantic routing below target, with one hash-order residual and no claim/main promotion.
- Primary files:
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md` — this BDD behavior record.
  - `.lazy-harness/domain/searchable-record-memory.md` — DDD terms used by the scenarios.
  - `.lazy-harness/scripts/record-index.ts` — indexes top-level Related layer links into cue-only related-record metadata.
  - `.lazy-harness/scripts/record-map.ts` — read-only `lazy map` implementation that lists cue-only candidates.
  - `.lazy-harness/scripts/retrieval-coverage-audit.ts` — read-only coverage audit that surfaces related-record candidates plus structural coverage gaps.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — injects static search/read debt reminder.
  - `.lazy-harness/hooks/lifecycle/helpers/check-overview-batch-order.py` — retired compatibility no-op for the old overview batch hard block.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — guards mutation until evidence exists.
  - `packages/lazy-harness-pi/agents/record-reader.md` — defines explicit candidate-map and claim-evidence Work Packet/Evidence Packet behavior, coverage conservation, fixed-point reopening, freshness, hard budgets, and provenance.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — enforces the shared v2 canonical-record-only role boundary, concrete-node-only map, canonical content hashing, evidence isolation, and Parent lifecycle bypass.
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` — schedules the layer package.
- Key symbols:
  - `buildRecordMap` (`.lazy-harness/scripts/record-map.ts`) — emits candidate records/source/tests/graph ids without semantic-authority fields.
  - `extractTopLevelRelatedRecords` (`.lazy-harness/scripts/record-index.ts`) — parses `Related <Layer>:` links as cue-only related-record paths.
  - `buildAudit` (`.lazy-harness/scripts/retrieval-coverage-audit.ts`) — includes related-record paths during coverage audit without becoming semantic authority.
  - `rearmEvidenceAfterSteer` / `toolResultBelongsToCurrentEvidenceEpoch` (`packages/lazy-harness-pi/extensions/lazy-harness/index.ts`) — invalidate prior-instruction evidence and accept only results from tool calls started in the current evidence epoch.
  - `check-overview-batch-order.py` — compatibility helper that intentionally emits no deny output; batching policy is advisory while mutation safety stays in `check-read-debt-permit.py`.
- Flow:
  1. Static reminder tells the agent to inspect real records/source/tests.
  2. `lazy map --overview` shows whole structure before concrete node selection.
  3. Standalone sequential overview remains preferred, but read-only batch/parallel tool shapes are allowed and must not be treated as evidence reads by themselves.
  4. Repeated `lazy map <feature-id|record-path|graph-id|source-path>` calls on copied concrete nodes may suggest dispersed candidate records or files.
  5. Agent reads canonical evidence across the dispersed candidates and resolves or gates ambiguity.
  6. Confirmed missing knowledge is persisted into records.
  7. Search-time and final verification-time checks include related layer records so “SDD/TDD only” does not silently pass when DDD/BDD/SSOT are linked.
  8. In dynamic write/read loops, map/index/graph cues may narrow candidate paths, but canonical records/source/tests and validation remain the source of truth after mutation.
  9. A non-extension mid-turn steer advances the evidence epoch; mutation stays blocked until fresh post-steer map/read evidence exists.
  10. Parent-owned complete discovery may delegate a candidate-map proposal from supplied facets/nodes, approve bounded evidence bundles, load independent bundles through claim-evidence Readers, reopen on new questions, and selectively reread before deciding.
  11. Rule-recall work keeps Parent interpretation and Reader evidence carriage; compact v2 normalizes the wire without adding a new authority.
  12. Output above the soft target remains usable with a warning; only hard-cap inability reopens/splits work, never silent trimming.
- Tests / protection:
  - `.lazy-harness/tests/pre-action-search-evidence-guard.md` — protects evidence before action.
  - `.lazy-harness/tests/record-index-header.md` — includes `lazy map` drill-down output and no-semantic-authority checks.
  - `.lazy-harness/tests/retrieval-coverage-audit.md` — protects cross-layer related-record candidates and missing-completeness checks.
  - `.lazy-harness/scripts/self-test.py#check_tool_execute_before_hook` — protects removal of the overview-batch hard block while preserving generic mutation evidence denial.
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — protects post-steer evidence isolation, explicit two-mode contract text, Reader overview denial, canonical hash allowance, mode/fixed-point outcomes, and unchanged Parent lifecycle.
- Cross-layer links:
  - DDD: `.lazy-harness/domain/searchable-record-memory.md`
  - SDD: `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`
  - SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Machine index:
  - graph ids: `kg_llm_owned_retrieval_behaves_from_domain`, `kg_record_reader_rule_recall_shadow_result_20260824`, `kg_record_reader_compact_contract_implementation_20260824`, `kg_record_reader_compact_contract_review_closure_20260824`, `kg_record_reader_compact_rule_recall_canary_result_20260824`
  - generated index key: pending until index generator exists

## Layer completeness impact

- DDD: no independent delta; existing searchable-record-memory terms already cover cue, evidence, and scoped loading.
- BDD: compact canary validates the Parent/Reader rule-recall split and no-trim representation on one below-target candidate case; general accuracy and over-target behavior remain unproven live.
- SDD: Search/Read Debt keeps Parent debt unchanged; Pi package SDD owns compact wire/admission and output budgets.
- TDD: Pi package fixtures protect compact soft/hard behavior plus existing mode/tool/lifecycle boundaries.
- SSOT: CLI boundary remains canonical for code/tool authority; no machine packet schema or queue is promoted.
- ADR: ADR 0055 owns the bounded canary and further rollout gates.

## Rule placement

- Rule: LLM-owned retrieval behavior belongs in BDD because it describes how the agent/searcher should act across multi-step record/source/test discovery flows.
- Scope: framework-global
- Primary record: `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- Why not SDD only: the behavior is user/agent flow, not merely a component contract.
- Why not `.jcode`: shared lazy-harness framework behavior.
- Confirmation: user approved exactly one compact rule-recall canary. It was admitted below target with no decision-relevant semantic loss, but one read/hash ordering deviation remains. No retry, claim, integration canary, main merge, or promotion is inferred.
