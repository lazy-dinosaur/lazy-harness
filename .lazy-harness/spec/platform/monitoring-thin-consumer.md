# SDD — Inactive monitoring thin consumer (slices 1–2)

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
  - attest stage-1 full only for a whole-file request whose untruncated tool-result text, stripped only of known tool decoration, is byte-equal to the captured file
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

User-approved option C, slice 2 (2026-11-09): add a deterministic main-agent
read-result attestation producer in the monitoring adapter directory. Keep upstream
core, existing CaptureEvidence/Reader code, Pi settings and the live extension entry
unchanged. Only new commits in the consumer worktree are authorized; no push.

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
The original harness evidence tracker and Reader transport remain unchanged.

The adapter explicitly labels this source `tool-result-text-runtime-file` and maps
it to core `exposure.kind: unknown`. It therefore cannot suppress an exact document
version as already-read. Tool-success-only and Reader-joined-fingerprint evidence
also map to unknown. An explicit `context-full-record` attestation maps to full;
`context-partial-record` maps to partial. Slice 2 produces these through the
stage-1 seam below, without reinterpreting existing receipts as full exposure.
Official port conformance still exercises invented full/partial evidence.

Fresh capture evaluations must be supplied with the scope captured when the read
occurred. Current root/epoch bindings and Pi scope must match; old scopes cannot be
restamped after compaction. The owner must reevaluate CaptureEvidence before feed;
the adapter neither reads files nor restores session receipts. Metadata is volatile,
bounded, immutable on snapshot, exact-version-aware and fenced on session, branch,
compaction, binding, source, grant and availability changes. Overflow makes coverage
unavailable, never a complete truncated ledger. This is not a canonical read ledger.

## Stage-1 attestation: tool-result-full-text

`createReadResultAttestor` pairs `start(call, cwd, origin)` and
`complete(result, cwd, origin, cursor)`. Events use the existing extension shapes:
`toolCallId`, `toolName`, `input`, explicit `isError`/`is_error`, and
`content: [{type: 'text', text}]`; optional `details` and `structuredContent`
truncation flags are additional negative evidence. Extra event fields (such as
`type`) are not part of call identity. Call ID/name/input, invocation cwd and the
start-time generation must match; missing/error/unpaired results are not admitted.

The explicit caller owns provenance (`origin: main-agent`), root/epoch, the actual
read-tool format and source/grant/cursor bindings. Reader summaries and nested
agent/provider results must not be fed here. The producer installs no listeners and
uses no models or Fabric integration. `readTextFormat` is an owner-selected binding,
not guessed from returned prose; absent/unsupported format defaults to unknown.

| Evidence | exposure.kind | Exact version suppressed? |
| --- | --- | --- |
| Numeric whole-file request, one text part, known format, no notices/negative flags, stripped-body SHA-256 and bytes equal captured bytes | full | Yes |
| Valid numeric subset request and known-format body exactly equals the selected captured lines | partial | No |
| Notice/truncation/continuation, unknown/mixed decoration, anchored/invalid offset, changed content, lossy encoding, binary or mismatched bytes | unknown | No |
| Failed/unpaired/non-main result, out-of-root/unavailable capture or stale generation | No record admitted | No |

A whole-file request has no offset/limit, or numeric offset 1 with absent limit or
a limit covering all lines (plain Pi counts the terminal empty split row; hashline
counts visible rows). A subset request cannot become full just because its result
contains the whole file. No union of partial reads is promoted to full.

### Read-tool format evidence and stripping

- Native Pi package: `node_modules/@earendil-works/pi-coding-agent/dist/core/tools/read.js`,
  text branch and `truncateHead` in adjacent `truncate.js`: UTF-8 text, numeric
  line selection, one text content part; continuation text is appended for missing
  lines or byte/line truncation. Format `pi-read-text-v1` removes nothing.
- Installed package pi-hashline-edit-pro: src/hashline/alphabet.ts (`HASH_CLASS`)
  defines exactly five lowercase ASCII letters. src/hashline/resolve.ts
  (`fmtRow`, lines 73–84) prefixes each row with that anchor and U+2502;
  `fmtRegion` joins rows with LF. src/read.ts (`fmtReadPreview`, `regRead.execute`)
  supplies text content plus pagination/long-line/encoding notices and metadata.
  Format `pi-hashline-edit-pro-v1` requires every row to match five lowercase
  letters followed by U+2502 and removes exactly those six characters per row.
  It does not strip numbered/uppercase/longer/mixed prefixes, ANSI, prose, payload
  whitespace, embedded pipes, BOM, CR, or any notices.
- Package src/utils.ts (`splitLines`, `visLines`) omits the terminal empty row.
  Therefore a typical hashline result for a file ending in LF is NOT byte-equal.
  Stage 1 does not restore missing LF, normalize CRLF, or certify empty-file
  explanatory output. Such results stay unknown even when a human sees all lines.

At result completion the producer captures at most 1 MiB of root-bound regular-file
bytes via no-follow open, realpath checks and before/after file stats. It rejects
unstable captures and invalid UTF-8 roundtrips. Both body and file are hashed; full
also requires byte equality. Catalog identity remains exactly
`ReadRecordCatalog.resolve(relativePath, capturedSHA256)`; source record ID is that
path, source record revision is the captured hash, and source event ID is the tool
call ID. Every admitted record carries `tool-result-full-text:` plus a SHA-256
digest binding call, capture identity, start context, format, cursor, catalog
identity, captured hash and the classification/body hash (where decodable). The
prefix alone is not authorization: only exposure.kind full suppresses a version.

Pending state is volatile and bounded to 256 IDs per generation; duplicates reject
pending proof and overflow fences further production until a new generation. Tool
text processing is bounded to 2 MiB. Scope/source/grant/availability/root/epoch
changes reject in-flight proof; format changes also clear pending proof. The port
clears admitted records and invalidates snapshots on generation/root/epoch changes.
No receipt is restamped or persisted. Full for version A never suppresses version B.

### Limits and future stage 2

Stage 1 attests a particular untruncated read-tool result, not the provider request,
model attention, understanding, delivery after context transformation, or successful
report enqueue. It cannot detect a file changing away and back between observations.
The caller must use the serialization of the actual main-agent tool result; unknown
or transformed delivery stays unknown. Stage-2 `provider-input-observed` is future
work requiring separate authorization and actual provider-input observation, not a
stronger label inferred from these receipts. Live activation is still unapproved.

## Inactive composition and catalog seam

`createHarnessReferences` validates injected bindings, builds the read adapter,
uses official `createReferencesRegistration`, and preflights its required
`session.read-records` binding with `validateRequiredInputPorts`. It defaults to
`observe`; construction installs no listeners. A future explicit caller may invoke
its `extension` to attach only official `createPiInputPortGenerations` lifecycle
hooks. No input watcher, model selection, report delivery transport or live
registration is added. An observe trigger is skipped by the core runtime before
handlers or reports execute. `attestations.start`/`complete` explicitly feed the
producer into `reads.recordEvidence`, then official references consume the port.
`close` disposes runtime, attestor, port and generations.

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
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/read-attestation.ts` — `createReadResultAttestor`, `MainReadCall`, `MainReadResult`, `ReadTextFormat`; paired stage-1 capture/classification and explicit main-agent feed.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/read-record-port.ts` — `createHarnessReadRecordPort`, `ReadRecordCatalog`, `HarnessReadEvidence`; volatile source adapter.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/references.ts` — `createHarnessReferences`, explicit binding/preflight/composition owner.
- `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/monitoring.test.ts` — official `runReadRecordPortConformance`, invented CaptureEvidence fixture, fail-closed bindings, lifecycle fencing, exact/full/subset/decorated/stale/truncated fixtures, version-specific references suppression and no-report observe checks.
- `packages/lazy-harness-pi/extensions/lazy-harness/capture-evidence.ts` — unchanged upstream harness receipt source, not an exposure attestation.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — unchanged live entry; no import or activation of the composition.
- `.lazy-harness/tests/test-strategy.xml` — focused command `bun run test:monitoring-consumer`; also runnable via `bun run test:run ./packages/lazy-harness-pi/extensions/lazy-harness/monitoring/monitoring.test.ts`.
- `.lazy-harness/knowledge/graph.jsonl` — implementation/protection facts, including `kg_monitoring_stage1_attestation`; generated implementation index is derived, not proof.
- `.lazy-harness/generated/implementation-index.json` — source-read-derived cache entry for this record.
- Flow: explicit main-agent call → captured generation → matching result + current runtime bytes → catalog identity → exposure evidence → adapter port → official references exact-version lookup.
- Ownership: this host owns only glue/tests/SDD; upstream gitlink/core and original harness evidence source remain unchanged.

## Layer completeness

| Layer | Judgment |
| --- | --- |
| SDD | Primary delta here: inactive composition plus stage-1 exact-text attestation; provider-input exposure remains unproven. |
| BDD | No independent delta: no live user flow activated. |
| SSOT | No independent delta: workspace manifests/gitlink own the pin; no new environment/config authority. |
| DDD | No independent delta: existing read/exposure/version vocabulary is consumed unchanged. |

## Discovery capture and future work

Captured here, not promoted to new operating rules: stage-2 provider-input-observed,
proper catalog contract, separately approved activation and separate legacy
retirement. The fetched base has no tracked `.lazy-harness/scripts/monitoring-*.ts`
files. Do not remove legacy sources from a different checkout; inventory again on
integration, map callers/tests to upstream module APIs, verify parity, then seek
separate removal approval. Guided graph migration is outside this slice.

Code organization review: COP-03/04 keep adapter ownership and runtime cleanup in
one explicit composition; COP-01/02 keep pairing → capture → classification local
in one producer, and COP-05 keeps the version-aware port local. No untouched
source is rewritten and no architecture profile or enforcement is inferred.
