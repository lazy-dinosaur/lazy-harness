# SDD — Search/Read Debt Contract

Status: accepted
Date: 2026-06-06
Layer: SDD
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - 검색 빚
  - read debt
  - 리드 뎁트
  - 증거 게이트
  - evidence guard
  - Harness Reader join
  - Reader completion barrier
- Applies when:
  - changing `message.received` search/read debt journaling
  - changing the generic pre-action evidence guard
  - changing response audit handling of unsatisfied search/read debt
  - replacing direct Parent search/read debt with dedicated Reader launch/join semantics
- Must:
  - store only sanitized search/read debt rows in `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl`
  - keep debt rows static/protocol-level, not selected by a raw user-text classifier
  - use safe message/session hashes and bounded counters, never raw prompts or transcripts
  - keep direct Parent map/read as the unavailable/non-complete/stale Reader fallback while the isolated Reader implementation awaits main integration
  - make the accepted target launch one dedicated Reader to inventory and read relevant canonical harness records across DDD/SDD/BDD/TDD/ADR/SSOT/Planning
  - let the Parent concurrently inspect source/tests or immediately needed behavior
  - require the content-bearing Reader response—not only a child completion acknowledgement—before Parent plan, mutation, or host-specific completion
  - permit only one-shot read-only status/transcript inspection of the exact pending Reader run bound to the current root/evidence epoch; status output never supplies canonical evidence or closes the join
  - bind Reader completion to the current root, revision identity, work-unit/evidence epoch, and one dedicated Reader run without classifying raw user text
  - accept a successful `complete` Reader response as work-unit harness context without duplicate Parent reads solely for debt bookkeeping
  - route Reader `incomplete`, `conflict`, failure, or obvious omission to bounded Parent follow-up or option gate
  - invalidate an earlier work-unit result on a non-extension mid-turn steer
  - keep semantic selection and conflict resolution LLM-owned; lifecycle code must not classify raw user text
  - keep response audit advisory/backstop, not semantic routing
- Must not:
  - generate required-read lists, confidence scores, intent/risk/gate, or next-action from raw user text
  - make the Parent preselect concrete record nodes for the Reader
  - require routine duplicate Parent record reads after successful Reader completion
  - turn Reader completion into candidate admission, exact tool-sequence proof, independent audit, or agreement machinery
  - treat generated cache/helper output as canonical record evidence
  - replay full inventory or catalogs on every normal message
- Record completion:
  - changes to journal name, row shape, evidence tools, or guard semantics update this SDD, `.lazy-harness/spec/platform/pre-response-rule-context.md`, `.lazy-harness/tests/pre-action-search-evidence-guard.md`, `.lazy-harness/tests/pre-response-rule-context.md`, and implementation maps.

## Runtime row shape

The runtime journal is non-canonical and session-scoped:

```json
{
  "event": "message.received.search-read-debt",
  "instructionLevel": "harness-first-static",
  "messageIdHash": "16-char-hash",
  "sessionIdHash": "16-char-hash",
  "fallbackSearchCount": 1,
  "epochSeconds": 1780000000.0
}
```

Allowed fields are transport/evidence bookkeeping only. They are not semantic judgments.

## Flow

```text
first Pi/OMP work-unit boundary
→ append one sanitized static search/read-debt row
→ inject a pointer-only grounding reminder
→ LLM/searcher runs one overview, chooses a concrete node, and reads only governing records plus exact implementation evidence
→ adapter stores the overview marker and governing-record content hashes
→ generic pre-action guard allows mutation after concrete evidence exists

later normal message in the same work unit
→ adapter verifies governing-record hashes
→ valid: reuse grounding with a visible `reused-work-unit` status and no prompt/catalog replay
→ changed/deleted: arm one fresh grounding packet

explicit mid-turn steer
→ clear work-unit grounding and advance the evidence epoch
→ ignore results from tool calls started in an older epoch
→ require one fresh post-steer map/read grounding before mutation

response.completed
→ audit durable capture and strong misses as a backstop

## Accepted supersession direction — isolated implementation, integration pending

The user confirmed that the default target is not a Parent-owned debt journal. At work-unit start, one dedicated Reader searches the full stored harness memory and reads the task-relevant canonical records while the Parent concurrently inspects code/tests or immediately needed behavior. Parent action waits at a simple Reader-response join.

A successful `complete` response supplies the work-unit's harness policies/facts and does not require the Parent to repeat the same record reads. `incomplete`, `conflict`, Reader failure, an obviously omitted layer, or editing the canonical record itself requires bounded direct follow-up. No admission/provenance/audit/agreement proof stack is part of this baseline.

The isolated worktree now narrows current debt behavior with exact Reader launch/content join and direct fallback. Main still runs the prior direct journal/fingerprint path until separate integration approval.

### Reader result and join contract — isolated implementation, integration pending

The isolated Pi adapter exposes one dedicated `lazy-harness.record-reader` role through the package. Parent grammar launches it asynchronously and continues the source/test lane. The task binds lazy root, revision, model, evidence epoch, user task, `maxReadCalls`, `maxRequestedLines`, and derived `maxLinesPerRead=floor(maxRequestedLines/maxReadCalls)`; the Parent does not preselect record nodes.

The Reader returns a bounded packet with exact marker `complete|incomplete|conflict`, policies/facts/conflicts/missing/paths, cumulative budget values, `maxLinesPerRead`, `maxObservedReadLimit`, and failed-tool count. Every body read uses an explicit limit no larger than the derived cap. Process completion alone cannot close the join.

Sync and async delivered RESULT packets share `parseReaderResultPacket`: identity values (`root`, `revision`, `evidenceEpoch`) are bare or surrounded by exactly one balanced backtick pair, then compared exactly without path/epoch normalization. Duplicate, conflicting, missing or malformed identity/status fields fail closed. Launch-task parsing remains separate and does not acquire Markdown normalization. Default Parent grammar remains asynchronous; an explicitly selected `async:false` launch may use the native single-result tool receipt, bound to the launch tool-call ID, outer run ID, successful Reader result and session file. Only Parent-visible text content is delivery; `details.finalOutput` alone is not. Observed `incomplete` and `conflict` retain their distinct status even if a caller claims complete, enable bounded fallback and never cache fingerprints. Complete still requires the entire trusted runtime ledger and every existing identity/hash/budget check.

The Parent consumes native async `subagent-notify` content and calls `lazy_reader_join`. When its independent lane is exhausted, the Parent yields runtime control without a user-facing terminal answer rather than polling status/shell to pass time. The adapter may pass trusted root/run/evidence-epoch/current-epoch state outside model-owned status args so both adapter and Python guard independently allow only the exact pending owned Reader's ordinary/transcript inspection. Unknown, stale, cross-root, launch, resume, steer, or mutation-like forms retain the prior action boundary. Status is coordination-only: its call/result is excluded from epoch/recent-evidence bookkeeping, and even a fake complete marker or record path in status transcript cannot enable join or either modern/legacy evidence cache.

The tool verifies run/completion, root revision/evidence epoch/model/task-bound launch identity, canonical paths, exact lowered cumulative ceilings, derived per-read cap, maximum observed read limit, zero failed calls, and a positive internally consistent ledger (`recordPaths <= readCalls`, observed <= requested, requested <= calls × cap). The isolated native follow-up binds outer run identity structurally from launch `details.runId`/`asyncId`, never arbitrary UUIDs in prose. Join defaults omitted run/counter fields to adapter-owned identity and the terminal child runtime ledger; explicitly supplied identity/counter mismatches still fail. Canonical join paths are always the full own-key set of terminal `ledger.recordHashes`, not a Parent-reconstructed list. Omitted or empty `recordPaths`, or a distinct subset of actual successful-read paths, cannot narrow that set or trigger fallback solely for omission. Legacy assertions remain bounded string arrays of at most 16 relative paths; unread/outside/duplicate/malformed supplied paths still fail. Every ledger path is canonical-checked and rehashed, including paths omitted by the Parent, before all fingerprints are cached. Successful details expose the effective `recordPaths` and `recordCount`. The guard loads through agent-relative `subagentOnlyExtensions`, charges admitted reads before execution (failed reads retain count/lines), and records failures/denials and successful path fingerprints using SDK `pi.appendEntry`. Notification `details.completions` carries native run/session-file identity; Parent reads only those ledger entries, checking root/revision/epoch/model/task/session identity and unchanged hashes. Missing/nonterminal/stale ledgers fail closed into bounded fallback. Model counters or session-path prose cannot substitute. Storage is native runtime session state, not a canonical proof artifact; semantic completeness remains model judgment.

A valid `complete` join supplies record fingerprints to current and legacy debt paths without duplicate Parent reads. Non-complete or errored-complete joins discard all earlier source/map evidence for fallback, so only fresh post-failure direct grounding can satisfy debt. While join is pending, native `read`/`grep`/`find` and strictly simple shell `grep`/`rg` plus head/tail/wc output filters remain available. Shell chaining, redirection, substitution, find/tree, write-output git forms, `rg --pre` variants, unsafe filters, and nested namespaced forms remain actions.

Reader delivery and final-answer delivery remain separate barriers. The typed SDK output capability (`ExtensionContext.mode`) identifies headless `print` and `json`: response.completed advisories remain unresolved and observable on stderr without scheduling another assistant turn that could replace the primary answer. Native content notifications/drain, pending Reader waits, user steers and required tool-action blocks are untouched. TUI/RPC and unknown adapters retain existing bounded follow-up behavior; no prose classifier decides output routing.

Upstream typed capture assessments use the same output capability boundary. In headless print/JSON, `agent_end` persists the entire assessment (root/epoch, status, receipts and semantic/approval caveats) with `pi.appendEntry("lazy-harness-capture", assessment)`. Pending/unverified assessments, including missing/error hooks, remain visible on stderr. Neither a custom conversation message nor a replacement model turn is emitted: Pi text output selects the final conversation message, so even `sendMessage(triggerTurn:false)` would hide the assistant answer. Plain custom entries are excluded by the SDK's `sessionEntryToContextMessages`. TUI/RPC keeps upstream non-steering `sendMessage` metadata and existing safety followups. Capture judgement remains LLM-owned and cannot certify semantic relevance or renew stale approval. Protected by real headless native CLI cases and `tests/lazy-harness/pi-capture-evidence.test.ts` explicit print/JSON plus interactive fixtures; evidence `.lazy-harness/evidence/upstream-reader-integration.md`.

## Implementation map

- Status: `live-r2-terminal-incomplete; adversarial reader-ledger/child-boundary/shell/fallback correction reviewed-ok-and-standard-green; new-live-approval-pending`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — advertises the dedicated Reader/content-join path first and direct map/read fallback second while keeping the sanitized debt row.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` and `check-search-performed.sh` — exact join evidence, strict safe-shell parity, failed-join evidence truncation, incomplete/error denial, and fresh direct fallback.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — dedicated child tool boundary, exact owned-status transport/classification with status bookkeeping exclusion, launch-bound per-read cap/max-observed/positive-ledger checks, Reader join/fallback/steer state, record fingerprints, and print output separation.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — audits unsatisfied debt after response.
  - `.lazy-harness/scripts/lifecycle-check.py` — mirrors `search-read-debt.jsonl` in sandbox fidelity checks.
  - `packages/lazy-harness-pi/agents/record-reader.md` — dedicated canonical-record-only Reader packet producer.
  - `.lazy-harness/scripts/self-test.py` — protects direct fallback plus Reader launch, content join, budget, failure, reuse, steer, and output-mode behavior.
- Runtime state:
  - `$LAZY_RUNTIME_ROOT/state/search-read-debt.jsonl` — non-canonical sanitized journal.
- Shared result parser: `packages/lazy-harness-pi/extensions/lazy-harness/reader-result.ts#parseReaderResultPacket`; `receiveReaderResult` binds delivered identity/status before `lazy_reader_join` validates the full ledger.
- Primary regression: `.lazy-harness/tests/reader-result-primary-answer.md`; actual headless CLI/production-hook protection in `packages/lazy-harness-pi/tests/reader-primary-answer-cli.test.ts`.
- Protection:
  - focused `check_pi_package_layout_and_contract` and `check_tool_execute_before_hook` — passed in the isolated worktree.
  - `lazy validate --plan standard` attempt 2 — passed with full self-test; attempt 1 failure/correction retained in the evidence capsule.
  - `.lazy-harness/evidence/dedicated-reader-runtime-v1-20260906.md` — static validation/review capsule.
  - `.lazy-harness/evidence/dedicated-reader-live-canary-r2-20260906.md` — live terminal-incomplete evidence and user-selected correction.
  - `.lazy-harness/bin/lazy prompt-budget --format=md`

## Layer completeness impact

- DDD: updated — Harness Reader, Parent code lane, and Reader join vocabulary.
- SDD: updated here with the accepted supersession direction and explicit current/target split.
- BDD: updated — parallel retrieval/code behavior and join barrier.
- TDD: updated — isolated Reader success/failure/join regressions passed focused and full standard validation; direct fixtures remain fallback coverage.
- SSOT: updated — mandatory recall stays authoritative while debt transport becomes transitional.
- ADR: updated — ownership/trade-off correction.
- Planning: updated — proof-remediation v3 superseded by simple orchestration backlog.
## Rule placement

- Rule: runtime search/read-debt is static transport evidence, not candidate selection or semantic routing.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/search-read-debt-contract.md`
- Why not AGENTS.md: this is platform runtime contract with implementation map and tests.
- Why not `.jcode`: shared framework behavior, not local/private wiring.
- Confirmation: user-confirmed correction on 2026-06-06 for the current debt mechanism.
- Confirmation: user-corrected on 2026-08-26 that Reader completion/join, not duplicate Parent debt reads, is the accepted target.
- Confirmation: user-reaffirmed on 2026-09-04 that subagent-based reading remains the target and that implementation must fix result/content and final-output delivery rather than reverting to Parent-owned retrieval.

## Discovery capture — Harness Reader ownership correction

- DDD: updated.
- SDD: updated here; isolated implementation focused-green, main integration pending.
- BDD: updated.
- TDD: updated with planned protection.
- ADR: updated.
- SSOT: updated.
- Planning: updated.

## Discovery capture — Reader packet/join design

- DDD: none; no new domain vocabulary is required.
- SDD: updated here with the content-bearing packet, structural join state, cumulative budget, mismatch fallback, and final-answer delivery barriers.
- BDD: updated in `.lazy-harness/behavior/llm-owned-record-retrieval.md`.
- TDD: updated in `.lazy-harness/tests/pre-action-search-evidence-guard.md` and `.lazy-harness/tests/pi-agent-package.md`; planned only.
- ADR: updated in ADR 0055 to preserve Reader ownership after the failed generic-delegate run.
- SSOT: none; current runtime journal and ownership remain transitional and unchanged.
- Planning: isolated implementation is focused-green; live model smoke, main integration, commit/push/release remain gated.

## Discovery capture — Reader packet/join implementation

- DDD: implementation status only; no new term.
- SDD: updated here with actual launch, explicit join tool, budget/failure checks, debt bridge, fallback, and output-mode behavior.
- BDD: updated with implemented content and output scenarios.
- TDD: updated with focused passing fixtures; full standard and live model smoke remain pending.
- ADR: implementation status updated without changing ownership.
- SSOT: transitional direct fallback remains and Reader join is implemented only in the isolated worktree.
- Planning: updated; main integration, live model run, commit/push/release remain gated.

## Map-first search evidence

`lazy map --overview` and concrete `lazy map <feature-id|record-path|graph-id|source-path>` calls are cue-only traversal commands. The guard may count those tool events or command/output blobs as **search evidence** for search-debt rows because they inspect project-map inventory, but they are never read evidence for concrete `requiredRead` paths.

## Mid-turn steer evidence epoch

A non-extension Pi/OMP `input` event with `streamingBehavior === "steer"` is a generic instruction boundary. The adapter must advance a root-scoped evidence epoch and clear the recent evidence exposed to the pre-action guard. It does not inspect the steer text, select records, or generate a new semantic debt row.

Each allowed tool call is tagged in memory with the current evidence epoch. Its `tool_result` may enter the recent evidence cache only when the recorded start epoch still equals the current root epoch. This prevents a slow or parallel tool that started before the steer from repopulating the cache after invalidation. The existing pre-action guard then applies unchanged: read-only map/read work remains available, while a later action blocks until fresh post-steer evidence exists.

`lazy find --purpose ...`, long free-form `lazy map` input, invented `--query` syntax, and keyword grep/rg/find fallback are invalid retrieval evidence because they imply CLI/tool-owned semantic search.
