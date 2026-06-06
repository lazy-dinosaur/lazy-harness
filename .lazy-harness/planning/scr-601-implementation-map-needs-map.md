# SCR-601 Implementation-map needs-map backlog

Status: captured; SCR-602 completed
Layer: Planning
Generated: 2026-06-06
Command: `.lazy-harness/bin/lazy impl-map --format=json`
Related task: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md#scr-601--produce-needs-map-backlog`

## Meaning

`needs-map` is not a static predeclared list. It is the read-only audit status emitted by `.lazy-harness/scripts/implementation-map-audit.ts` when a current Markdown record has implementation hints but lacks a `## Implementation map` section.

No implementation-map edits are made by SCR-601. This record captures the exact current audit output and proposes batches for SCR-602 review.

## Audit summary

- Initial `needs-map`: 31
- Initial `ok`: 80
- Initial `needs-review`: 0
- After SCR-602 Batch 1: `needs-map=29`, `ok=82`
- After SCR-602 Batch 2: `needs-map=21`, `ok=90`
- After SCR-602 Batch 3: `needs-map=16`, `ok=95`
- After SCR-602 Batch 4: `needs-map=0`, `ok=111`

### Needs-map by layer

- `adr`: 29
- `tdd`: 2

### Needs-map by hint

- `file extension`: 29
- `function mention`: 24
- `source path`: 19
- `test path`: 8
- `code fence`: 7

## Exact needs-map list

1. `.lazy-harness/decisions/0001-core-philosophy.md` — layer `adr`, hints: `function mention`, `file extension`
2. `.lazy-harness/decisions/0002-conflict-resolution-protocol.md` — layer `adr`, hints: `file extension`
3. `.lazy-harness/decisions/0003-recovery-path.md` — layer `adr`, hints: `function mention`, `file extension`
4. `.lazy-harness/decisions/0004-cross-layer-maps.md` — layer `adr`, hints: `source path`, `test path`, `function mention`, `file extension`
5. `.lazy-harness/decisions/0005-meaning-of-lazy.md` — layer `adr`, hints: `source path`, `file extension`
6. `.lazy-harness/decisions/0006-directory-bridge-architecture.md` — layer `adr`, hints: `source path`, `function mention`, `file extension`
7. `.lazy-harness/decisions/0007-agents-md-injection.md` — layer `adr`, hints: `source path`, `function mention`, `file extension`
8. `.lazy-harness/decisions/0008-ast-contract-diff-deferred.md` — layer `adr`, hints: `source path`, `function mention`, `file extension`
9. `.lazy-harness/decisions/0009-husky-integration.md` — layer `adr`, hints: `source path`, `function mention`, `code fence`, `file extension`
10. `.lazy-harness/decisions/0010-plan-status-hygiene.md` — layer `adr`, hints: `file extension`
11. `.lazy-harness/decisions/0011-verification-discipline.md` — layer `adr`, hints: `function mention`, `file extension`
12. `.lazy-harness/decisions/0012-oracle-sisyphus-audit-cascade.md` — layer `adr`, hints: `source path`, `function mention`, `file extension`
13. `.lazy-harness/decisions/0013-framework-external-dependency-invariant.md` — layer `adr`, hints: `function mention`, `file extension`
14. `.lazy-harness/decisions/0014-validations-retention.md` — layer `adr`, hints: `function mention`
15. `.lazy-harness/decisions/0015-doctor-c16-extend-plan-progress-freshness.md` — layer `adr`, hints: `source path`, `file extension`
16. `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md` — layer `adr`, hints: `source path`, `function mention`, `code fence`, `file extension`
17. `.lazy-harness/decisions/0017-user-input-as-universal-trigger.md` — layer `adr`, hints: `function mention`, `code fence`, `file extension`
18. `.lazy-harness/decisions/0018-cross-layer-cascade.md` — layer `adr`, hints: `test path`, `function mention`
19. `.lazy-harness/decisions/0019-ambiguous-detection-force-gate.md` — layer `adr`, hints: `source path`, `file extension`
20. `.lazy-harness/decisions/0020-tdd-cross-verify-gate-in-5d.md` — layer `adr`, hints: `source path`, `test path`, `function mention`, `file extension`
21. `.lazy-harness/decisions/0021-experimental-branch-and-extract-strategy.md` — layer `adr`, hints: `function mention`, `file extension`
22. `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md` — layer `adr`, hints: `source path`, `function mention`, `file extension`
23. `.lazy-harness/decisions/0023-n2-reference-resolver-host-pilot-validation.md` — layer `adr`, hints: `source path`, `function mention`, `code fence`, `file extension`
24. `.lazy-harness/decisions/0024-ai-first-framework-redesign.md` — layer `adr`, hints: `source path`, `function mention`, `code fence`, `file extension`
25. `.lazy-harness/decisions/0025-portability-single-entry-point.md` — layer `adr`, hints: `source path`, `function mention`, `code fence`, `file extension`
26. `.lazy-harness/decisions/0026-doctor-self-test-scope-separation.md` — layer `adr`, hints: `source path`, `test path`, `function mention`, `code fence`, `file extension`
27. `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md` — layer `adr`, hints: `test path`, `function mention`, `file extension`
28. `.lazy-harness/decisions/0029-generated-project-local-jcode-wiring.md` — layer `adr`, hints: `source path`, `file extension`
29. `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md` — layer `adr`, hints: `test path`, `function mention`, `file extension`
30. `.lazy-harness/tests/lazy-sync-dirty-false-positive.md` — layer `tdd`, hints: `source path`, `test path`, `file extension`
31. `.lazy-harness/tests/response-completed-route-telemetry-large-payload.md` — layer `tdd`, hints: `source path`, `test path`, `function mention`, `file extension`

## Proposed SCR-602 migration batches

These batches are planning only. Each record still requires source/test/graph read evidence before adding or verifying an `Implementation map`.

### Batch 1 — TDD regression records — completed in SCR-602

- Rationale: smallest surface, direct source/test hints, good first validation pass
- Count: 2
- Result: implementation maps added and graph rows recorded; `lazy impl-map` now reports both records as `ok`.
- Records:
  - `.lazy-harness/tests/lazy-sync-dirty-false-positive.md`
  - `.lazy-harness/tests/response-completed-route-telemetry-large-payload.md`

### Batch 2 — framework tooling/storage ADRs — completed in SCR-602

- Rationale: high implementation specificity with known scripts/hooks/lazy CLI relationships
- Count: 8
- Result: implementation maps added and graph rows recorded; `lazy impl-map` now reports all eight records as `ok`. Verified: ADR 0022/0026/0029/0030. Needs-review: ADR 0016/0023/0024/0025.
- Records:
  - `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`
  - `.lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md`
  - `.lazy-harness/decisions/0023-n2-reference-resolver-host-pilot-validation.md`
  - `.lazy-harness/decisions/0024-ai-first-framework-redesign.md`
  - `.lazy-harness/decisions/0025-portability-single-entry-point.md`
  - `.lazy-harness/decisions/0026-doctor-self-test-scope-separation.md`
  - `.lazy-harness/decisions/0029-generated-project-local-jcode-wiring.md`
  - `.lazy-harness/decisions/0030-implementation-map-three-layer-storage.md`

### Batch 3 — lifecycle/gate/graph ADRs — completed in SCR-602

- Rationale: cross-layer policy records that likely need graph/source/test evidence before verified maps
- Count: 5
- Result: implementation maps added and graph rows recorded; `lazy impl-map` now reports all five records as `ok`. All remain `needs-review` because they are broad/partial historical ADRs. ADR 0017 includes an explicit stale `triggers/external` framework-contract conflict.
- Records:
  - `.lazy-harness/decisions/0017-user-input-as-universal-trigger.md`
  - `.lazy-harness/decisions/0018-cross-layer-cascade.md`
  - `.lazy-harness/decisions/0019-ambiguous-detection-force-gate.md`
  - `.lazy-harness/decisions/0020-tdd-cross-verify-gate-in-5d.md`
  - `.lazy-harness/decisions/0028-progressive-knowledge-graph-backbone.md`

### Batch 4 — foundational/legacy ADR review — completed in SCR-602

- Rationale: older or broad ADRs; many may become `Status: none` or `needs-review` rather than verified implementation maps
- Count: 16
- Result: implementation maps added and graph rows recorded; `lazy impl-map` reports all records as `ok`. Verified: ADR 0008/0013. Needs-review: the rest, with explicit conflict/supersession notes for stale current-source divergences.
- Records:
  - `.lazy-harness/decisions/0001-core-philosophy.md`
  - `.lazy-harness/decisions/0002-conflict-resolution-protocol.md`
  - `.lazy-harness/decisions/0003-recovery-path.md`
  - `.lazy-harness/decisions/0004-cross-layer-maps.md`
  - `.lazy-harness/decisions/0005-meaning-of-lazy.md`
  - `.lazy-harness/decisions/0006-directory-bridge-architecture.md`
  - `.lazy-harness/decisions/0007-agents-md-injection.md`
  - `.lazy-harness/decisions/0008-ast-contract-diff-deferred.md`
  - `.lazy-harness/decisions/0009-husky-integration.md`
  - `.lazy-harness/decisions/0010-plan-status-hygiene.md`
  - `.lazy-harness/decisions/0011-verification-discipline.md`
  - `.lazy-harness/decisions/0012-oracle-sisyphus-audit-cascade.md`
  - `.lazy-harness/decisions/0013-framework-external-dependency-invariant.md`
  - `.lazy-harness/decisions/0014-validations-retention.md`
  - `.lazy-harness/decisions/0015-doctor-c16-extend-plan-progress-freshness.md`
  - `.lazy-harness/decisions/0021-experimental-branch-and-extract-strategy.md`

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/scripts/implementation-map-audit.ts` — read-only dynamic scanner that emits `needs-map`.
  - `.lazy-harness/bin/lazy` — exposes `lazy impl-map`.
  - `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md` — SCR-601 backlog status.
  - `.lazy-harness/planning/scr-601-implementation-map-needs-map.md` — captured SCR-601 audit output and batch proposal.
- Key symbols:
  - `auditRecord` (`implementation-map-audit.ts`) — assigns `needs-map` when hints exist and `## Implementation map` is absent.
  - `audit` (`implementation-map-audit.ts`) — scans current host layer Markdown records.
  - `printMarkdown` / `printJcodePrompt` (`implementation-map-audit.ts`) — renders migration guidance without editing files.
- Flow:
  1. `lazy impl-map --format=json` reads current `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}` Markdown records.
  2. Records with implementation hints but no `## Implementation map` become `needs-map`.
  3. SCR-601 captures exact output and proposes SCR-602 batches before edits.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` — validates lazy CLI and source feature navigation references for `implementation-map-audit.ts`.
  - `.lazy-harness/bin/lazy impl-map --format=json` — smoke-validates current audit output.
- Cross-layer links:
  - SDD: `.lazy-harness/spec/platform/implementation-map-migration.md`
  - SSOT: `.lazy-harness/ssot/implementation-map-storage.md`
  - Planning: `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- Machine index:
  - graph ids: `kg_scr601_needs_map_backlog`, `kg_scr601_impl_map_audit_command`, `kg_scr602_batch1_tdd_maps`, `kg_scr602_batch2_adr_maps`, `kg_scr602_batch3_adr_maps`, `kg_scr602_batch4_legacy_maps`, `kg_scr602_complete`

## Discovery capture

- DDD: none.
- SDD: `.lazy-harness/spec/platform/implementation-map-migration.md` already defines non-destructive dynamic audit semantics.
- BDD: none.
- TDD: no new executable test needed for list capture; existing self-test plus command smoke protect the audit command.
- ADR: none; no new trade-off beyond existing ADR 0030/SSOT storage rules.
- SSOT: `.lazy-harness/ssot/implementation-map-storage.md` confirms generated indexes are non-canonical and `lazy impl-map` is read-only.
- Planning: SCR-601 captured; SCR-602 completed all batches after source/test/graph evidence per record.

