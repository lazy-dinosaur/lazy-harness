# SDD — Search/Read Debt Contract

Status: accepted
Date: 2026-06-06
Layer: SDD
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related TDD: `.lazy-harness/tests/pre-action-search-evidence-guard.md`

## Current Pi transport — Fabric supersession

The approved current Pi path is `lazy_reader_request` → unchanged request to Pi Fabric `agents.spawn` → content-bearing `agents.wait`/`agents.join` → existing `lazy_reader_join`. Pi-subagents is not required or registered. The older isolated-integration and subagent-notify descriptions below are historical compatibility context, superseded for new Pi work units by the Fabric implementation map at the end of this record. The separate OMP native task transport is unchanged. Authenticated live retrieval is still blocked by the observed expired openai-codex token; offline regression is not a live success claim.

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
  - keep direct Parent map/read as the unavailable/non-complete/stale Reader fallback; never require pi-subagents as a fallback dependency
  - make the accepted target launch one dedicated Reader to inventory and read relevant canonical harness records across DDD/SDD/BDD/TDD/ADR/SSOT/Planning
  - use the one-shot Pi Fabric Reader without pi-subagents registration/installation; preserve explicit model/read budgets/packet/join and the separate OMP native task path
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

Current user-confirmed Reader default: use explicit `openai/gpt-6-luna:low` in both the launch and task envelope. Preserve the previously selected GPT-6 Luna and low thinking, but use the current openai provider rather than the obsolete openai-codex OAuth route. The active root session and model registry confirm the current provider and registered Luna model; registry presence is not a live inference result. `.lazy-harness/AGENTS.md`, `packages/lazy-harness-pi/prompts/lazy-harness.md`, `packages/lazy-harness-pi/README.md`, and `FABRIC_READER_DEFAULT_MODEL` carry the same default. Historical failed receipts retain their actual old provider and model; separate task-specific overrides remain explicit.


User correction — provider and transport parity: the user reported the provider change and rejected leaving the Reader on the old openai-codex authentication route. This is a default-routing correction, not a request to refresh obsolete-provider login credentials. Current active guidance is now changed to `openai/gpt-6-luna:low`. Global authentication, installed Fabric packages and their settings remain owned by the separate runtime-maintenance work unit and are not edited here.

The user reaffirmed transport-only parity: the dedicated Reader runs asynchronously in parallel with Parent source/test work, loads its existing dedicated prompt and canonical records, and supplies a content-bearing result at the join point. The first Fabric implementation shared only the prompt body and did not map all frontmatter. The restoration now parses and validates the existing definition, rejects unsupported/duplicate/changed fields, applies replace/no-project-context/no-skills prompt options, preserves fresh seed/read-only tool ceilings, validates the declared child guard module and records its contract hash in the runtime-owned ledger. Parent may read source while Reader is pending; mutation still waits for join. A discussion of serial self-test phases must not be presented as serializing Reader execution.

The user explicitly reapproved implementation with “정확하게 다시 가져와”. The restoration maps the canonical definition's soft 12 assistant turns plus 2 grace turns with wrap-up guidance and a hard abort before an additional tool cycle. This is separate from record-body budgets. The currently installed pi-subagents compatibility package marks its own turn-budget metadata deprecated/not enforced; it is a reference limitation, not proof that the framework's declared budget was actually enforced there. This restoration implements the existing canonical definition rather than claiming that obsolete metadata was previously guaranteed by that external package. No new concurrency model, Reader ownership, product behavior, global install or auth change is introduced.


### Exact declared-role mapping and protection

| Existing definition | Fabric adapter mapping |
| --- | --- |
| Dedicated name/package/body | Validated by `parseFabricReaderDefinition`; body reused verbatim, with tool-syntax encoding outside it. Unsupported/duplicate metadata fails preparation. |
| `systemPromptMode: replace` | `applyFabricReaderPrompt` sets the forced/custom system prompt and clears inherited append/section text. |
| `inheritProjectContext:false`, `inheritSkills:false` | SDK `contextFiles`, `skills`, inherited sections and guidelines are cleared before the first model call. |
| `defaultContext:fresh` | `seed:task`, no branch/snippet seed; no Parent conversation is supplied. |
| `acceptanceRole:read-only`, tools `read,grep,bash` | Fresh read-only Fabric request retains the exact tool ceiling; canonical record/bash checks remain hook-enforced. No separate writer/acceptance workflow is introduced. |
| `subagentOnlyExtensions` | The definition must name the canonical package guard; the actual child handler verifies its module path. Its contract hash/guard identity must appear in the runtime-owned ledger or Parent join rejects it. Missing bootstrap is not accepted as parity. |
| `output:false` | The model cannot write output files; Fabric's own process/session/runtime-meter artifacts remain native runtime scratch, not canonical proof artifacts. |
| `turnBudget:12+2` | Assistant messages, not body reads, are counted; soft wrap-up at 12, two grace responses, hard abort before another tool cycle at the ceiling. Exhaustion cannot be relabeled complete at join. |
| Parent/Reader parallel join | Spawn returns a handle immediately; Parent source reads remain admitted while Reader is pending; mutations remain blocked. Wait only at the merge point, then consume the outer-visible packet before join. |

Implementation map: `packages/lazy-harness-pi/extensions/lazy-harness/fabric-reader-policy.ts` owns `parseFabricReaderDefinition`, `applyFabricReaderPrompt`, `advanceFabricReaderTurn`, `validateFabricReaderPolicy`, and the current default constant. `fabric-reader.ts` uses that same definition instead of independently stripping metadata. The shared adapter's message/context/tool hooks enforce the policy; the launch-bound policy hash and guard path are checked in `readDeliveredReaderLedger`.

Protection: `packages/lazy-harness-pi/tests/fabric-reader.test.ts` covers metadata rejection, inherited-section removal, canonical provider guidance, Parent reads while pending, grace completion, hard-limit abort and missing guard stamps. `packages/lazy-harness-pi/tests/fabric-reader-policy-sdk.test.ts` uses a real SDK `ExtensionRunner` and in-memory fresh session with networking disabled to prove prompt replacement, 12+2 wrap-up/abort, and subsequent read denial. The first SDK run caught a hard-limit check accidentally nested inside the OMP normalization branch (60 other checks passed); the check was moved to the common Reader boundary, then the changed Fabric/SDK suite passed 29/29 in 1.438s and Pi typecheck passed. The earlier shared guidance/OMP focused checks passed; no OMP behavior change is introduced. Standard package validation invokes both Fabric regression files.

Live boundary: the separate runtime-maintenance session reported an incomplete global Fabric update and a stale project `/home/...` package binding on this macOS host. This source-restoration work does not install/repair/restart global tools, change those bindings or launch a child during that unstable installation state. Source/SDK parity checks are not an authenticated live Fabric success claim. User/provider correction and runtime-install recovery are separate owners.

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


## Discovery capture — Pi Fabric Reader migration request

- User-confirmed objective: migrate the existing Pi subagents-based dedicated Reader to Pi Fabric. The user selected the one-shot Fabric agent replacement option, preserving the model, read limits, result packet, and join checks rather than introducing a persistent actor.
- Additional user-confirmed constraint: the user intends to delete `pi-subagents`. The migrated Pi Reader must therefore work without that package being installed or loaded; keeping it as a required legacy launch, completion-notification, registration, or ledger dependency would not satisfy the request. Package removal itself remains user-owned; this statement does not authorize the agent to uninstall global packages or modify global settings.
- Implementation status: the user explicitly instructed continuing after the pi-subagents-removal constraint. Revised execution approval covers a dependency-free one-shot Fabric Reader, existing model/read limits/packet/join preservation and focused regression tests. OMP, unrelated subagent use and global uninstall remain outside the mutation scope. Direct Parent retrieval remains the non-complete/unavailable fallback; no pi-subagents fallback is required.
- Read-only investigation: the current package contains `extensions/lazy-harness/reader-transport.ts` (`ReaderTransport`, `ReaderLaunchIdentity`, `ReaderDelivery`), and `extensions/lazy-harness/index.ts` still handles `subagent-notify`, subagent admission and `lazy_reader_join`. These are the observed implementation seams, not a completed Fabric implementation.
- Current-session blocker: an explicit fresh asynchronous legacy Reader launch failed before startup because the installed Pi host did not provide `@earendil-works/pi-agent-core/node`, `@earendil-works/chord`, and `@earendil-works/chord/context`. Parent used the direct overview → concrete-node drill → canonical-read fallback; no complete Reader result or successful join is claimed.
- Discovery capture: this primary SDD owns the migration objective and implementation. Pi package subagent registrations are removed; OMP native transport and unrelated pre-existing working-tree changes are preserved. `lazy_reader_request` creates fixed fresh/read-only Fabric options; native spawn and visible wait proxies bind the host-issued run, while a hook-owned sessionless meter supplies the existing join checks. Legacy parser compatibility remains only for old fixtures/sessions, not a required runtime dependency.
- Parent delivery boundary: a nested Fabric wait result remains pending until its owning outer fabric_exec result. The adapter appends the exact owned packet to that actual Parent-visible result, so guest summary-only returns cannot hide the packet and same-program premature joins remain blocked. The regression includes this boundary.

### Implementation map — Fabric Reader

- `packages/lazy-harness-pi/extensions/lazy-harness/fabric-reader.ts`: `fabricReaderRequest` and `fabricReaderPrompt` construct the package-owned one-shot request; `validateFabricReaderSpawn` and `fabricReaderProxyResult` validate exact request/handle and visible native content; `persistFabricReaderLedger` mirrors the actual hook-owned meter for Fabric's `--no-session` workers under OS runtime scratch, keyed by host-issued lineage run id. Model prose cannot choose the ledger path or its counters.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`: `lazy_reader_request` registers preparation, native `agents.spawn`/`agents.wait`/`agents.join` proxies bind the current root/epoch/run; existing `readDeliveredReaderLedger`/`lazy_reader_join` revalidate terminal identity, budgets, successful record hashes and changed-file fingerprints. Wrong/failing/truncated/detail-only results never join. Spawn failure can explicitly enable direct fallback without a run id.
- `packages/lazy-harness-pi/package.json`: removes Pi subagents discovery metadata; `agents/record-reader.md` remains the shared canonical body consumed directly by Fabric preparation and OMP's unchanged definition generator.
- `.lazy-harness/AGENTS.md`, `packages/lazy-harness-pi/prompts/lazy-harness.md`, `packages/lazy-harness-pi/README.md`: document prepare → spawn → Parent source lane → visible wait → join, no old transport flags, and direct Parent fallback.
- Protection: `packages/lazy-harness-pi/tests/fabric-reader.test.ts` covers dependency-free registration, successful hook-meter join, changed options/model/runner, wrong-id/failed/indeterminate/detail-only results, read failures/over-cap, missing meter, fingerprint changes, pending mutation, failed spawn and post-steer stale results. Existing Reader and OMP tests protect shared behavior. `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` protects the new manifest/guidance.
- Validation evidence: first focused checkpoint had 206 pass / 1 fail (the over-cap read was correctly denied, but the test expected the later failed-budget error rather than the earlier positive-counter rejection). The assertion was corrected and that failure-only case passed. After completing the outer Parent-delivery boundary, the Fabric-focused suite passed 20/20 in 0.84s, and Pi typecheck passed. The earlier shared Reader/OMP suite's unchanged checks passed; lazy check passed. Final standard validation is the next checkpoint. No authenticated successful live retrieval/join is claimed.
- Historical Fabric smoke: native `agents.spawn` used `openai-codex/gpt-6-luna`, low thinking, and `agents.wait` reported token expiry before any tool call (one turn, zero tools). Preserve this as the actual prior failed run. The user has since corrected the provider to openai; refreshing the obsolete provider is not the current recovery instruction. A new live success must be observed on the corrected route after the separately maintained Fabric installation is stable.
- Actual native meter readback: the failed Fabric smoke did initialize the new child hook-owned ledger with matching root/revision/epoch/model and actual Pi session identity, a terminal flag and the exact Fabric run id. It contained zero body reads/lines/paths, consistent with the token-expiry failure before tools. Thus process launch, package child-hook loading and runtime-meter persistence were observed; successful record loading and live join were not.

### Layer impact — Fabric migration

| Layer | Decision |
| --- | --- |
| SDD | Independent delta recorded here: transport/request/result/ledger contract moves to Pi Fabric. |
| BDD | No independent product-flow delta; Parent/Reader ownership and final-answer behavior are preserved. Runtime usage guidance is updated in package prompts. |
| SSOT | No independent ownership/config delta; existing model and user-owned global package removal are preserved. Runtime scratch is non-canonical. |
| DDD | No independent delta; no new domain term or business rule. |
| TDD | Protection is linked above in this primary SDD; no separate bug narrative is promoted. |
