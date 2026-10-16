# Runtime continuation and partial-bootstrap regression

## Rule digest
- Status: active
- Layer: TDD
- Scope: framework-global
- Confidence: high
- Aliases:
  - synthetic not-armed recovery
  - async completion continuation
  - partial worktree dry-run
  - missing target CLI activation
- Applies when: an owned asynchronous continuation resumes the same grounded work unit, or sync previews a target whose managed CLI has not yet been installed.
- Must: preserve real valid root/revision/governing evidence and a pending Reader's pinned epoch; require actual successful native map/read before recovering an unarmed packet; represent deferred dry-run activation as planned, not checked.
- Must not: grant permission from an empty prompt, failed/foreign/stale read, status-only Reader result or a fabricated human source; overwrite host facts, bypass Reader join, or publish an activation failure as success.

## Confirmed failures and approval

After final394 rollout, actual synthetic shell completions entered `not-armed(synthetic-turn)/empty-output`. A current overview, concrete drill and canonical body read still could not pass the packet's unconditional action denial. Separate peers reported the same failure. The operator explicitly requested solving both this and partial bootstrap, then corrected an unnecessary order-only approval pause and told the owner to proceed.

The old `before_agent_start` advanced the evidence epoch before checking reuse. A pending Reader was pinned to the earlier epoch. The corrected empty SDK continuation preserves the existing epoch only for current governing fingerprints or the exact current pending Reader; the pending/content-join barrier remains. Otherwise the packet remains fail-closed until actual successful native map/read recovers it. Cache entries bind the root-local record paths and current revision; unsuccessful, foreign-path, changed/deleted evidence and new sessions/real steers do not supply permission. Current-turn audit results remain separate from retained work-unit proof.

A source sync preview of a record/artifact-only test worktree tried to run the absent target CLI before copying it, then masked the spawn failure with missing stderr.trim. Missing-target dry-run activation now returns a labelled **planned after managed CLI installation (not checked)** result, matching the initializer's existing planned-preview boundary. Existing-target previews still invoke actual activation validation, and actual apply still requires success before publishing the final marker. Nonzero/spawn failures retain useful diagnostics. This does not turn CategoryA sync into a full institutional-memory initializer or invent shared-overlay wiring; CategoryB initial containers and canonical seed content remain governed by the initializer and the explicit setup scope.

## Protection scenarios

- Real SDK ExtensionRunner: grounded synthetic continuation admits ordinary action without another human message; an ungrounded synthetic packet blocks until actual successful local overview/read; failed read, canonical-looking foreign path, changed governing text, new revision and new session remain negative cases.
- Existing Fabric Reader adapter fixture: synthetic completion preserves the pending epoch and mutation barrier, then actual child ledger/content join succeeds; real non-extension steer invalidates rather than rebinding the old Reader.
- Real synthetic Git sync CLI: partial dry-run is byte-identical and leaves the CLI absent while honestly planning activation; independent apply preserves tracked host/artifact bytes, existing registry facts and Git tracked delta; spawn failure is nonzero, diagnostic, and does not advance the marker.

## Layer completeness

| Layer | Judgement |
| --- | --- |
| SDD | No independent public API/component delta: existing event/status/activation interfaces and successful-evidence contract are repaired; no new flag or shared-overlay API. |
| BDD | No independent intended user-flow delta: existing same-work-unit continuation and honest dry-run behavior are restored, not a permission to resume paused product work. |
| SSOT | No independent ownership/config/schema delta: active package/host records remain preserving; no blanket CategoryB initialization or graph overwrite. |
| DDD | No independent domain-rule delta. |

## Implementation map

- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`: `workUnitEvidenceValid`, `observeEvidenceCall`, `observeWorkUnitEvidence`, `rememberToolCall`, `before_agent_start` and `tool_result` callbacks; local path/revision fingerprints, successful-result packet recovery, pending Reader epoch preservation and separate current-turn audit results.
- `.lazy-harness/scripts/lazy-sync.ts#reconcileAgentActivation`: planned missing-CLI preview and retained failure diagnostics; initialized/apply activation paths remain real.
- `tests/lazy-harness/pi-capture-evidence.test.ts`: real native SDK regression, included by existing `check_analysis_discovery_capture_helper` standard/typecheck routing.
- `packages/lazy-harness-pi/tests/fabric-reader.test.ts`: pending Reader continuation and explicit-steer barrier regression alongside existing ledger/content/budget negatives.
- `tests/lazy-harness/test_lazy_sync_integrity.py#run_case`: actual isolated CLI partial-preview/apply/spawn cases, invoked by existing `check_implementation_correctness_repairs`.
- `.lazy-harness/manifests/init-categories.json`: explicit CategoryA distribution of this record.
- `.lazy-harness/knowledge/graph.jsonl` and generated implementation index: source-evidenced mapping and rebuildable AST cache.
- Related contracts: `.lazy-harness/spec/platform/search-read-debt-contract.md`, `.lazy-harness/tests/pre-action-search-evidence-guard.md`, `.lazy-harness/spec/platform/host-root-resolution.md`.

## Validation boundary

Assertions above define regression requirements, not passing receipts. Source/installed results are owned by the current primary planning evidence capsule only after actual terminal outputs are consumed. No paid inference, in-memory forced reload, product work or remote publication is certified by this record.
