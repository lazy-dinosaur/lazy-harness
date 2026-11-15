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
- `reader-primary-answer-cli.test.ts`: current actual Pi Parent → unchanged prepared Fabric spawn → real Reader process/SDK read ledger → content-bearing wait → full join → four-claim answer → unmodified production capture/placement hooks. JSON/text × wait-first/source-first × capture/placement protects the same answer and evidence barriers; both orders still spawn asynchronously. `fabric-reader-cli.test.ts` rejects an actual untrusted child without the declared guard/ledger.
- The deterministic provider deliberately emits a partial replacement if an unwanted continuation occurs; assertions inspect actual CLI stdout, native session/ledger, hook stderr and process traces, not only send counts.
- Historical suites remain unchanged; no remote provider requests, new Reader, native patch or performance claim is allowed.
- Current-vs-historical boundary: `reader-primary-answer-cli.legacy.fixture.ts` preserves the original native A/B test body (Git blob16c4aae32ed18ab76e9f01c2bae8f94e466014a5) behind explicit `bun run test:reader:legacy`. It is not skipped, rewritten with Fabric native paths or counted as current success; its original exact native input requirements remain. Current offline fixtures use independently pinned Pi1.5.2/Fabric0.136.0, never global bindings or the production0.85 SDK upgrade. Actual authenticated retrieval is outside these deterministic tests.

## Layer completeness

| Layer | Judgment |
|---|---|
| SDD | Independent delta: shared RESULT grammar, explicit synchronous receipt support and typed headless print/JSON advisory delivery; update search-read-debt and Pi package contracts. |
| BDD | Independent delta: quoted packets behave identically across transports; headless JSON and text preserve the complete primary answer. |
| SSOT | No independent delta: ownership, runtime storage, configuration and full-ledger authority unchanged. |
| DDD | No independent delta: no new domain terms or business rule. |

## Current verification alignment (2026-11-15)

The user approved moving verification to the already published Fabric contract after old native inputs were explicitly removed from current installation ownership. Current8 cases are real process coverage, not renamed historical A/B results. The historical body remains byte-preserved and explicit-only; missing approved historical inputs remain unexecuted, never counted green.

- `tests/runtime/fabric/{package.json,bun.lock}`: independently pinned test dependency graph (Pi1.5.2/Fabric0.136.0), no production SDK/global upgrade. `bun run test:fabric:setup` uses frozen install with lifecycle scripts disabled.
- `packages/lazy-harness-pi/tests/fixtures/fabric-cli-runner.ts#runFabricScenario`: private agent/auth/settings, network-denied actual Parent/child, real native proxy/ledger, preserved production hooks, exact full successful read hashes, output/capture metadata and no-write checks. Success cleans owned sandbox/ledger; failure preserves synthetic logs.
- `fixtures/fabric-reader-provider.ts`: deterministic zero-cost model only; compatible transcript encoding for actual pinned Parent1.5.2/worker1.5.0. It never supplies a forged proxy or trusted ledger. Missing `getCurrentSystemPrompt` on the worker caused the first pinned probe to hang; this test-only compatibility and proper terminal error handling repair are retained in the execution capsule.
- `reader-primary-answer-cli.test.ts`: JSON/text × wait-first/source-first × capture/placement (8 actual cases). Default Reader is still asynchronous. `fabric-reader-cli.test.ts`: actual untrusted child cannot load the project guard or join; private test trust is not global trust or a safety-check deletion.
- `scripts/test-runner.mjs`: all repository-owned Bun test files plus the Node-only SDK fixture in its correct engine. Vendor workspace and historical native fixture own explicit separate commands. Concrete affected-test forwarding and `1 passed` success compatibility remain.
- `scripts/test-pi-capture.mjs`: Node CLI capability probe selects a supported transform flag rather than assuming one; no test assertions disabled. Aggregate supplies canonical TMPDIR only to test subprocesses; existing private-writer symlink checks remain untouched.
- `tests/lazy-harness/test-runner-routing.test.ts`: exact archived Git blob preservation and real focused routing. `.lazy-harness/tests/test-strategy.xml` owns runnable command routing. Primary execution capsule: `.lazy-harness/tests/host-validation-isolation.md`.

| Layer | Current alignment judgement |
| --- | --- |
| SDD | No independent production delta: existing Fabric request/content/join and print metadata contracts are exercised. |
| BDD | No new flow: existing asynchronous Parent/Reader and headless answer protections, plus actual missing-guard refusal. |
| SSOT | Test-only pinned dependency graph/command routing; production SDK, model default and installed bindings unchanged. |
| DDD | No domain delta. |

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
