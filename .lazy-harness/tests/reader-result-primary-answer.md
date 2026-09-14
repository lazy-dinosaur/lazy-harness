# TDD — Reader RESULT and primary-answer preservation

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - Reader RESULT parser
  - headless primary-answer preservation
  - synchronous Reader receipt
- Applies when:
  - changing Reader RESULT parsing, native receipt adaptation or post-response output delivery
- Must:
  - test quoted native and bare scripted identities through both delivery paths
  - retain distinct incomplete/conflict fallback and full trusted ledger authority
  - exercise actual headless CLI text/JSON with production capture and placement hooks after a multi-claim answer
  - keep advisories observable without replacing the answer; preserve required Reader continuation and action boundaries
- Must not:
  - count details-only finalOutput, process completion or status inspection as delivered content
  - modify frozen historical evidence, native packages, search lanes, budgets or default async grammar
- Related records:
  - `.lazy-harness/spec/platform/search-read-debt-contract.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`
  - `.lazy-harness/behavior/llm-owned-record-retrieval.md`

## Regression origin

Monitored-04 A packets quoted root/revision/epoch while the experimental synchronous host compared bare values. Nine packets were complete, two incomplete and one conflict; no historical result is rescored. B11/B20/B24 and A12 delivered full answers before production capture/placement advisories requested partial replacement answers. This is a host output seam defect, not evidence of lost native Reader content.

## Protection

- `reader-result.test.ts`: bare/quoted complete, incomplete and conflict; duplicate/conflicting/missing/status/delimiter negatives; exact quoted wrong identity; native run/session/agent/tool-call binding; duplicate result/completion identity; details-only, status-only, stale-steer rejection.
- Both transports retain terminal ledger root/revision/epoch/model/task/session checks, missing/nonterminal/impossible/over-budget/failed-read negatives, forged counters, unread/duplicate path assertions, and rehashing of omitted paths. Subsets still join all successful hashes; non-complete never caches.
- `reader-primary-answer-cli.test.ts`: actual Pi CLI Parent → original synchronous or existing repaired async native Reader → SDK read ledger → content receipt → full join → four-claim answer → unmodified production response.completed capture/placement helper. JSON/text both preserve every claim with no subsequent partial assistant answer or canonical writes. Upstream capture assessment is verified in actual native-session custom-entry delivery plus stderr as explicitly unverified, semanticStatus=llm-judgement-not-verified and approvalStatus=not-evaluated; obsolete keyword-driven capture STOP is forbidden. Independent placement advisories remain on stderr. Async waits for genuinely delayed child completion and proves Parent exit occurs after child termination.
- The deterministic provider deliberately emits a partial replacement if an unwanted continuation occurs; assertions inspect actual CLI stdout, native session/ledger, hook stderr and process traces, not only send counts.
- Historical suites remain unchanged; no remote provider requests, new Reader, native patch or performance claim is allowed.

## Layer completeness

| Layer | Judgment |
|---|---|
| SDD | Independent delta: shared RESULT grammar, explicit synchronous receipt support and typed headless print/JSON advisory delivery; update search-read-debt and Pi package contracts. |
| BDD | Independent delta: quoted packets behave identically across transports; headless JSON and text preserve the complete primary answer. |
| SSOT | No independent delta: ownership, runtime storage, configuration and full-ledger authority unchanged. |
| DDD | No independent delta: no new domain terms or business rule. |

## Implementation map

- Status: verified
- Primary files: `packages/lazy-harness-pi/extensions/lazy-harness/reader-result.ts` — `parseReaderResultPacket`; `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — `receiveReaderResult`, `observeReaderPacket`, synchronous `tool_result`, `lazy_reader_join`, `preservesHeadlessPrimaryAnswer`, `printModeAdvisory`.
- Flow: transport-owned delivery → shared packet grammar/exact identity → status → unchanged full terminal ledger validation → cache or bounded fallback; response.completed metadata → typed print/JSON stderr, without native-drain changes.
- Tests: `packages/lazy-harness-pi/tests/reader-result.test.ts`, `packages/lazy-harness-pi/tests/reader-primary-answer-cli.test.ts`, `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`.
- Test fixtures: `packages/lazy-harness-pi/tests/fixtures/native-reader-provider.ts`, `native-reader-network-guard.mjs`; native package paths are explicit read-only test inputs, not installed/configured globals.
- Ownership: original work/reader-runtime-v1 and separately approved disposable upstream+Reader candidate only; main, native sources, frozen benchmark files and global settings are not source mutation targets. TUI/RPC and user/action continuations retain prior behavior.
- Graph: `kg_reader_result_primary_answer_repair`; generated index mirrors that source-confirmed graph row.
- Evidence: `.lazy-harness/evidence/reader-result-primary-answer-repair.md` — one validation capsule; review remains required.

## Discovery capture / Rule placement

This primary TDD captures the approved regression scenarios. SDD/BDD updates above own their independent semantics; SSOT/DDD/ADR have no independent delta. Source organization is observe-only: one shared parser avoids transport drift without splitting unrelated code. No operating-policy registry changes or search-interface changes.

## Upstream integration regression checkpoint

The disposable candidate combines fixed upstream80cf3be with the exact Reader58fbcbf working delta. `tests/lazy-harness/pi-capture-evidence.test.ts` independently protects actual SDK typed receipts, LLM-owned judgement, stale/foreign/error rejection, non-steering capture and required safety followups; the Reader native CLI fixture above tests the same production hook after full Reader delivery. `self-test.py` retains both Reader guard/fallback/status tests and upstream Node cache, graph/sync and host-owned-document protections. The parser import uses `.ts` so the same component runs under upstream native Node stripping as well as Bun fixtures. New explicit print/JSON SDK cases preserve complete typed assessment entries (including linked receipts and error-hook reports), display pending/unverified stderr and prohibit conversation sends or followups. The original interactive safety-followup assertions remain unchanged under explicit SDK TUI mode; actual CLI tests reject capture custom messages, require all four stdout claims, and exercise delayed native continuation. Evidence: `.lazy-harness/evidence/upstream-reader-integration.md`; graph: `kg_upstream_reader_combined_regression`.

| Layer | Integration judgment |
|---|---|
| SDD | Independent transport reconciliation: headless full capture assessment uses runtime appendEntry plus relevant stderr, not sendMessage; search/read-debt contract records SDK context exclusion. Interactive typed capture and Reader ledger contracts are preserved. |
| BDD | Independent headless behavior clarification: even a non-steering custom message must not hide primary text output; runtime capture metadata and visible stderr coexist with actual native continuation. |
| SSOT | No independent policy delta: upstream pinned dependency targets and disposable mutation controls retained, no installed/global ownership change. |
| DDD | No independent domain delta. |
