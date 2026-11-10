# SDD — Inactive monitoring thin consumer (slice 1)

## Rule digest

- Status: advisory
- Layer: SDD
- Scope: framework-global
- Aliases:
  - monitoring thin consumer
  - version-aware read-record adapter
- Applies when:
  - integrating the monitoring submodule into the Pi package
- Must:
  - retain monitoring as a gitlink at vendor/lazy-harness-monitoring pinned to 2066a10
  - keep this composition unregistered in the live extension, defaulting to observe
  - require explicit exposure evidence before marking an exact document version fully read
  - supply catalog identity, source/grant/cursor, capture root/epoch and Pi generation bindings explicitly
- Must not:
  - infer full-context exposure from tool success, file hashes, Reader completion or report enqueue
  - add model calls, a catalog implementation, copied monitoring source, or a Fabric integration in this slice
- Record completion:
  - update this record when the evidence seam, activation boundary or submodule pin changes
- Related records:
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - `.lazy-harness/tests/test-strategy.xml`

## Approval and ownership

User-approved option A, slice 1 (2026-11-09): root Bun workspaces consume only
monitoring core, hosts/pi and modules/references; the Pi package uses workspace:*
dependencies. The upstream repository owns module code and contracts. This host
owns only the adapter/composition/tests and gitlink. Knowledge integration is
future work, not another workspace/submodule in this slice. No live Pi settings
or extension entry changes are authorized. Experiment results are not canonical
records and must not be committed.

## Existing read evidence and honest gap

`index.ts` maintains private `WorkUnitEvidence.recordHashes`; successful read-like
tool results populate current file hashes through `observeEvidenceCall` and
`observeWorkUnitEvidence`. The Reader meter also fingerprints successful canonical
reads; `lazy_reader_join` validates delivered packet identity, terminal ledger,
budgets, failures and current record hashes before caching them. These are useful
retrieval/freshness receipts, not proof that an entire canonical record was served
verbatim into the main model's context. A Reader summary is not that record body.

`capture-evidence.ts#CaptureEvidence` is the existing exported evidence surface.
`start` binds tool ID/root/epoch/path/input; `complete` requires a successful result
with nonempty text and snapshots the runtime file; `evaluate` rechecks the hash
for relevant reuse facts. It does not compare returned text to the file or certify
full/partial coverage. Its successful read `CaptureValidation` receipts are the
adapter's source, passed by a future owner rather than extracted from private maps.
No source file, original evidence tracker, or Reader transport is changed here.

The adapter explicitly labels this source `tool-result-text-runtime-file` and maps
it to core `exposure.kind: unknown`. It therefore cannot suppress an exact document
version as already-read. Tool-success-only and Reader-joined-fingerprint evidence
also map to unknown. Only an independently supplied `context-full-record`
attestation maps to full; `context-partial-record` maps to partial. Those kinds are
an injected future-host seam, not a claim that current Pi provides full attestation.
The conformance test supplies invented full/partial attestations to exercise it.

Fresh capture evaluations must be supplied with the scope captured when the read
occurred. Current root/epoch bindings and Pi scope must match; old scopes cannot be
restamped after compaction. The owner must reevaluate CaptureEvidence before feed;
the adapter neither reads files nor restores session receipts. Metadata is volatile,
bounded, immutable on snapshot, exact-version-aware and fenced on session, branch,
compaction, binding, source, grant and availability changes. Overflow makes coverage
unavailable, never a complete truncated ledger. This is not a canonical read ledger.

## Inactive composition and catalog seam

`createHarnessReferences` validates injected bindings, builds the read adapter,
uses official `createReferencesRegistration`, and preflights its required
`session.read-records` binding with `validateRequiredInputPorts`. It defaults to
`observe`; construction installs no listeners. A future explicit caller may invoke
its `extension` to attach only official `createPiInputPortGenerations` lifecycle
hooks. No input watcher, model selection, report delivery transport or live
registration is added. An observe trigger is skipped by the core runtime before
handlers or reports execute. `close` disposes runtime, port and generations.

`ReadRecordCatalog.resolve(path, sha256)` is identity-only injection with a TODO for
the future catalog contract. There is no discovery/index/catalog implementation.
Catalog mappings and source/grant/cursor values are trusted owner bindings, not
inferred from session prose or git HEAD.

## Implementation map

- `vendor/lazy-harness-monitoring` — upstream gitlink; official port, registration and Pi generations.
- `package.json`, `bun.lock` — minimal root workspace resolution and focused test command.
- `.gitignore` — excludes Bun-installed node_modules at all workspace depths; dependency artifacts are not source changes.
- `packages/lazy-harness-pi/package.json` — three workspace dependencies.
- `packages/lazy-harness-pi/tsconfig.json` — excludes only the adjacent Bun test from the Node-only Pi source check; the Bun runner owns its test globals.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/read-record-port.ts` — `createHarnessReadRecordPort`, `ReadRecordCatalog`, `HarnessReadEvidence`; volatile source adapter.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/references.ts` — `createHarnessReferences`, explicit binding/preflight/composition owner.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/monitoring.test.ts` — official `runReadRecordPortConformance`, invented CaptureEvidence fixture, fail-closed bindings, lifecycle fencing and no-report observe checks.
- `packages/lazy-harness-pi/extensions/lazy-harness/capture-evidence.ts` — unchanged upstream harness receipt source, not an exposure attestation.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — unchanged live entry; no import or activation of the composition.
- `.lazy-harness/tests/test-strategy.xml` — focused command `bun run test:monitoring-consumer`; also runnable via `bun run test:run ./packages/lazy-harness-pi/extensions/lazy-harness/monitoring/monitoring.test.ts`.
- `.lazy-harness/knowledge/graph.jsonl` — implementation/protection facts; generated implementation index is derived, not proof.

## Layer completeness

| Layer | Judgment |
| --- | --- |
| SDD | Primary delta here: inactive port/composition and explicit exposure gap. |
| BDD | No independent delta: no live user flow activated. |
| SSOT | No independent delta: workspace manifests/gitlink own the pin; no new environment/config authority. |
| DDD | No independent delta: existing read/exposure/version vocabulary is consumed unchanged. |

## Discovery capture and future work

Captured here, not promoted to new operating rules: future full-context attestation,
proper catalog contract, separately approved activation and separate legacy
retirement. The fetched base has no tracked `.lazy-harness/scripts/monitoring-*.ts`
files. Do not remove legacy sources from a different checkout; inventory again on
integration, map callers/tests to upstream module APIs, verify parity, then seek
separate removal approval. Guided graph migration is outside this slice.

Code organization review: COP-03/04 keep adapter ownership and runtime cleanup in
one explicit composition; COP-05 keeps the version-aware port local. No untouched
source is rewritten and no architecture profile or enforcement is inferred.
