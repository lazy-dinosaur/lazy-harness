# SDD — Hook Performance Measurement

Status: accepted
Date: 2026-05-21
Layer: SDD
Related: `.lazy-harness/planning/performance-optimization-plan.md`, `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`, `.lazy-harness/tests/response-completed-route-telemetry-large-payload.md`

## Contract

Phase 0 performance optimization is measurement-only.

`response.completed` lifecycle behavior must remain identical except for append-only timing telemetry. Timing data may be used to plan future optimization, but must not be used to skip gates until a later conservative fast-path phase has golden parity tests.

Phase 1 introduces one conservative fast-path: when `recent_tool_calls` is present, is a list, and every tool name is in the known read-only allowlist, the hook may skip helpers whose logic is exclusively triggered by file writes. Any unknown payload shape or unknown/non-read-only tool falls back to the full helper set.

Phase 2 adds a shadow lifecycle orchestrator. It runs outside the production hook, mirrors helper order and fast-path selection, and produces JSON for parity tests. It must not replace `on-response-completed.sh` until shadow parity covers STOP/no-STOP fixtures.

Phase 3 adds an opt-in lifecycle engine switch. Default behavior remains `legacy`; `orchestrator` and `compare` are explicit opt-in modes only.

## Hook timing log

Default path:

```text
$LAZY_RUNTIME_ROOT/logs/hook-timings.jsonl
```

Environment controls:

- `LAZY_HOOK_TIMING=0`: disables timing logging.
- `LAZY_HOOK_TIMING_LOG=/path/to/file.jsonl`: overrides the timing log path.
- `LAZY_RESPONSE_COMPLETED_ENGINE=legacy|orchestrator|compare`: selects the response.completed engine. Missing/unknown values fall back to `legacy`.
- `LAZY_RESPONSE_COMPLETED_COMPARE_LOG=/path/to/file.jsonl`: overrides compare-mode JSONL output. Default: `$LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl`.

Each JSONL row contains:

- `ts`: UTC timestamp.
- `event`: currently `response.completed`.
- `component`: `route-telemetry`, a helper path, or `hook-total`.
- `durationMs`: elapsed milliseconds.
- `exitCode`: component exit code where available.
- `outputEmitted`: whether the component emitted a user-visible STOP/reminder output.

## Summary CLI

```bash
.lazy-harness/bin/lazy hook-timings --format=md
.lazy-harness/bin/lazy hook-timings --format=json --limit=500
python3 .lazy-harness/scripts/hook-timing-summary.py --log $LAZY_RUNTIME_ROOT/logs/hook-timings.jsonl
```

The summary command is read-only and reports per-component count, total, average, p50, p90, p99, max, emitted count, and non-zero exit count.

## Safety constraints

- No timing failure may block or alter hook decisions.
- Timing rows must not contain raw user messages or payload bodies.
- Timing instrumentation must not change the helper order.
- Timing instrumentation must not suppress helper output.
- Unknown timing failures are swallowed, preserving the legacy hook behavior.
- Fast-path skip decisions must be based only on parsed payload facts, not natural-language guesses.
- Unknown payload shape, missing `recent_tool_calls`, or unknown tool names must run the full helper set.
- Phase 1 may skip only write-only helpers that already no-op unless write/edit tools are present.
- Phase 3 default must remain `legacy` until an explicit production replacement approval is recorded.
- `orchestrator` mode must fall back to the legacy loop if `lifecycle-check.py` exits non-zero or emits invalid JSON.
- `compare` mode must keep legacy output as user-visible truth and run the orchestrator in a sandbox copy to avoid real-host duplicate side effects.
- Compare logs must store hashes/lengths and helper names, not raw user messages, payloads, or hook bodies.
- User correction acknowledgement must converge into a durable record/correction ledger. The hook must stop turns where the user corrects a recurring mistake, the assistant acknowledges it, and no `.lazy-harness` record/correction capture is touched.

## Phase 1 read-only fast-path

Read-only allowlist:

- `read`, `Read`
- `grep`, `Grep`, `agentgrep`, `glob`, `Glob`, `ls`, `LS`
- `webfetch`, `websearch`
- filesystem read/list/search/get-info MCP tools

Skipped only for known read-only payloads:

- `check-layer-impact.sh`
- `check-ddd-trigger.sh`
- `check-ssot-trigger.sh`
- `check-layer-completeness.sh`
- `check-tdd-cross-verify.sh`
- `check-affected-tests.sh`

Not skipped:

- BDD trigger, because it can inspect natural-language user flow even without writes.
- analysis discovery, project rule placement, option-gate discipline, record-before-session-history, lazy CLI entrypoint, aftershock reanalysis, fix-regression, ADR sync, and handoff stale helpers.

## User correction capture gate

`check-user-correction-capture.sh` protects the recurring dogfood failure mode where an agent says “맞습니다/죄송/제가 잘못” after a user correction but only fixes the current chat context.

The helper triggers when:

- `last_user_message` contains concrete correction/repeated-mistake cues such as `아니`, `잘못`, `자꾸 실수`, `기록하는 게 아니`, `하네스 수정`, or `잊지마`.
- `assistant_response` acknowledges the correction with cues such as `맞습니다`, `죄송`, `제가 잘못`, `정정`, or `누락`.
- The same turn did not touch a durable `.lazy-harness/{ssot,spec,behavior,tests,decisions,planning}` record or `.lazy-harness/{knowledge,logs}/corrections.jsonl`.

Allowed resolutions:

- Add/update the appropriate layer record with a `Correction capture` or equivalent section.
- Append a candidate correction row to `.lazy-harness/knowledge/corrections.jsonl` or `.lazy-harness/logs/corrections.jsonl` when the final layer is not yet clear.
- For framework bugs, implement the source fix and update the primary record / implementation map in the same turn.

This gate is intentionally not skipped by read-only fast-path because corrections can happen without file writes.

## Structured validation evidence forwarding

Future lifecycle hook evidence forwarding, including Jcode `response.completed` validation output, must use the Project Map update-loop event packet contract instead of inventing hook-specific semantic authority.

Contract:

- The packet shape is defined by `.lazy-harness/spec/platform/project-map-update-loop-v2.md`.
- Hook-originated validation output uses existing controlled vocabulary: `source = jcode-adapter`, `eventType = validation-success|validation-failure`, and `evidence.kind = validation-output`.
- Hook-originated packets are compact evidence only. They must not include raw user text, raw assistant text, secrets, credentials, or semantic-authority fields such as confidence/intent/risk/requiredRead/nextAction/candidateMeaning.
- Hook-originated packets must not become canonical truth by themselves. They remain `candidate` or `needs-confirmation` until record-write policy or an explicit confirmation gate updates canonical records.
- Phase 1 is contract/fixture/static-test only. It does not add a production hook writer, new CLI, or automatic event-store append path.

## Phase 2 shadow orchestrator

CLI:

```bash
.lazy-harness/bin/lazy lifecycle-check --format=json < payload.json
.lazy-harness/bin/lazy lifecycle-parity --format=json --fail-on-mismatch
python3 .lazy-harness/scripts/lifecycle-check.py --format=md --payload '{"recent_tool_calls":[]}'
```

Contract:

- Read-only with respect to production hook wiring. It does not change `on-response-completed.sh` behavior.
- Mirrors the production helper order and Phase 1 fast-path selection.
- Stops at the first helper output, matching production hook semantics.
- Emits `firstOutput`, `firstOutputHelper`, `injectJson`, selected/skipped helpers, helper timing, and fast-path reason.
- May execute existing helpers and therefore uses the same queue/validation environment variables as legacy hook tests.
- Replacement is forbidden until self-test parity covers representative STOP/no-STOP cases.

Batch parity runner:

- `lazy lifecycle-parity` runs production `on-response-completed.sh` and shadow `lifecycle-check` in fresh temp host copies for each fixture.
- It compares output presence, first STOP/reminder body, expected helper, and expected marker text.
- It compares validation side-effect rows after removing volatile timestamp/id fields.
- `--fail-on-mismatch` exits `2` on any mismatch and is intended for self-test/CI.
- Fixtures must be self-contained enough to run in installed hosts; source-only fixture files need embedded fallbacks.

## Phase 3 opt-in engine switch

Default behavior:

```bash
LAZY_RESPONSE_COMPLETED_ENGINE=legacy .lazy-harness/hooks/lifecycle/on-response-completed.sh
```

`legacy` preserves the existing shell helper loop and is the default when the environment variable is unset or unknown.

Opt-in orchestrator primary mode:

```bash
LAZY_RESPONSE_COMPLETED_ENGINE=orchestrator .lazy-harness/hooks/lifecycle/on-response-completed.sh
```

`orchestrator` runs `lifecycle-check.py` as the primary helper engine after static timing setup. If it succeeds, its `injectJson`/no-output decision becomes the hook result. If it fails or cannot be parsed, the hook falls back to the legacy helper loop.

Opt-in compare/debug mode:

```bash
LAZY_RESPONSE_COMPLETED_ENGINE=compare \
LAZY_RESPONSE_COMPLETED_COMPARE_LOG=$LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl \
.lazy-harness/hooks/lifecycle/on-response-completed.sh
```

`compare` runs the orchestrator in a sandbox `.lazy-harness` copy, then runs the legacy helper loop in the real host. Legacy output remains user-visible truth. The compare log stores only metadata such as output booleans, helper names, body lengths, and body hashes.

Rollback:

```bash
unset LAZY_RESPONSE_COMPLETED_ENGINE
# or
export LAZY_RESPONSE_COMPLETED_ENGINE=legacy
```

Remove compare logs if desired:

```bash
rm -f $LAZY_RUNTIME_ROOT/logs/lifecycle-compare.jsonl
```

## Implementation map

- `.lazy-harness/hooks/lifecycle/on-response-completed.sh`
  - Emits timing rows around each lifecycle helper and total hook runtime.
  - Applies Phase 1 read-only fast-path only for known read-only payloads, with full-check fallback for unknowns.
  - Supports Phase 3 opt-in `legacy|orchestrator|compare` engine selection; default is legacy.
- `.lazy-harness/scripts/lifecycle-check.py`
  - Phase 2 shadow orchestrator. Parses payload once, mirrors helper order/fast-path selection, runs existing helpers, and reports first-output parity data.
  - Supports `--sandbox` for side-effect-safe compare/debug runs.
- `.lazy-harness/scripts/lifecycle-parity-runner.py`
  - Batch parity runner that compares production hook output with lifecycle-check shadow output across representative fixtures in fresh temp hosts.
  - Embeds a fallback aftershock decision fixture so installed hosts can run parity without framework-only `triggers/fixtures` files.
  - Includes real/sample read-only payload and layer-impact observation side-effect parity coverage.
- `.lazy-harness/scripts/hook-timing-summary.py`
  - Read-only timing summary CLI.
- `.lazy-harness/bin/lazy`
  - Exposes `lazy hook-timings`, `lazy lifecycle-check`, and `lazy lifecycle-parity`.
- `.lazy-harness/scripts/self-test.py`
  - `check_response_completed_no_auto_route_telemetry` verifies timing rows are emitted without route/user-text classifier telemetry and that the summary CLI works.
  - The same test protects fast-path safety: read-only payloads skip only write-only helpers, while unknown/missing payload shapes run the full helper set.
  - The same test protects Phase 3 opt-in modes: orchestrator timing, sandboxed compare logging, and no raw body storage.
  - The same test protects user-correction capture: acknowledgement without durable capture emits STOP, while a `.lazy-harness` record write satisfies the gate.
  - `check_lifecycle_hook_integration` verifies shadow parity for TDD cross-verify, aftershock, BDD, option-gate discipline, record-before-session-history, and read-only no-output cases.
  - `check_lifecycle_parity_runner` verifies the batch parity runner succeeds across the 12-fixture suite.

## Discovery capture

- DDD: none.
- SDD: this contract defines Phase 0 measurement-only behavior.
- BDD: user-visible behavior is unchanged except an explicit `lazy hook-timings` command.
- TDD: existing response.completed telemetry regression test extended to protect timing output.
- ADR: no replacement decision yet; Phase 2 shadow orchestrator is explicitly not a production replacement.
- SSOT: timing log path and env toggles are defined here.

## Lifecycle real payload fixture intake

`lazy lifecycle-fixture inspect|append|list` supports Phase 3 readiness by converting real `response.completed` payloads into sanitized parity fixture candidates.

Contract:

- Store no raw user message text.
- Store no raw assistant response text.
- Store hashes, lengths, boolean content signals, tool names, and sanitized argument previews only.
- Appended candidates live at `.lazy-harness/fixtures/lifecycle/real-payload-candidates.jsonl`.
- `lifecycle-parity-runner.py` may load these candidates to increase parity coverage.

Implementation map:

- `.lazy-harness/scripts/lifecycle-fixture-intake.py` — intake/list/append CLI.
- `.lazy-harness/scripts/lifecycle-parity-runner.py` — loads sanitized candidate fixtures.
- `.lazy-harness/bin/lazy` — dispatches `lazy lifecycle-fixture`.
- `.lazy-harness/scripts/self-test.py` — `check_lifecycle_fixture_intake_cli` protects privacy and parity inclusion.

## 2026-06-04 Phase 3A compare fidelity patch

Status: accepted
Related TDD: `.lazy-harness/tests/lifecycle-compare-fidelity.md`
Related Planning: `.lazy-harness/planning/lifecycle-compare-mismatch-triage-20260604.md`

Dogfood showed compare-mode mismatches caused by instrumentation/sandbox fidelity rather than Medivance-specific framework behavior. Phase 3A improves compare fidelity while keeping production default `legacy`.

Contract additions:

- `lazy lifecycle-compare-summary --format=md|json [--log=PATH] [--limit=N] [--fail-on-mismatch]` is a read-only summary CLI for `response.completed.compare` JSONL rows.
- Compare body hashing uses legacy-equivalent trailing-newline normalization because legacy bash command substitution strips trailing newlines. Raw byte lengths remain recorded as diagnostics.
- Compare logs must not store raw hook bodies, raw payloads, or raw user/assistant messages. They may store helper names, byte lengths, hashes, booleans, classes, and bounded metadata.
- `lifecycle-check.py --sandbox` must run helpers with sandbox-local `LAZY_RUNTIME_ROOT` and `LAZY_SHARED_ROOT` so debug compare runs do not write duplicate state to the real host runtime.
- Sandbox mode may provide read-only git facts through env variables (`LAZY_LIFECYCLE_GIT_LAST_SUBJECT`, `LAZY_LIFECYCLE_GIT_HEAD`) so git-dependent helpers can match real-host behavior without copying the real `.git` directory.
- Sandbox mode may mirror bounded runtime state tails for helper fidelity: `open-gates.json`, `surfaced-rule-digests.jsonl`, and `search-read-debt.jsonl`.
- Sandbox mode may mirror `.jcode/hooks/tool-events.jsonl` only after filtering to current message/session id. Wholesale raw tool-event history copying is forbidden.
- Production replacement remains forbidden until compare summary readiness is zero mismatch, no privacy issues, no orchestrator failures, and user approval is recorded.

Implementation map update:

- `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — normalized compare hash writer and compare metadata producer.
- `.lazy-harness/scripts/lifecycle-check.py` — isolated sandbox runtime/shared roots and bounded context mirror.
- `.lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh` — consumes read-only sandbox git facts.
- `.lazy-harness/scripts/lifecycle-compare-summary.py` — read-only summary CLI.
- `.lazy-harness/bin/lazy` — dispatches `lifecycle-compare-summary`.
- `.lazy-harness/scripts/self-test.py` — protects Phase 3A behavior.
- `.lazy-harness/tests/lifecycle-compare-fidelity.md` — TDD/regression record.

## 2026-06-04 timing and compare summary evaluation tooling

Status: accepted
Related Planning: `.lazy-harness/planning/lifecycle-compare-dogfood-handoff.md`
Related TDD: `.lazy-harness/tests/lifecycle-compare-fidelity.md`

The post-Phase3A compare evaluation found two low-risk tooling gaps: post-patch compare rows required manual JSONL filtering because `lifecycle-compare-summary` had no timestamp filter, and hook timing readiness required manual aggregation because `hook-timings` only read one default runtime log.

Contract additions:

- `lazy lifecycle-compare-summary --since <ISO-8601>` filters valid compare rows by `timestamp >= since` before summarizing. The JSON/Markdown output reports `since`, `sourceRows`, and `filteredRows` so post-patch evidence can be reproduced without temporary filtered JSONL files.
- `lazy hook-timings --since <ISO-8601>` filters timing rows by `ts` or `timestamp` before summarizing. Output reports `since`, `sourceRows`, `filteredRows`, `firstTimestamp`, and `lastTimestamp`.
- `lazy hook-timings --all-sessions` aggregates the selected/default timing log, legacy `.lazy-harness/logs/hook-timings.jsonl`, all worktree runtime session logs under `.git/lazy-harness/runtime/*/logs/hook-timings.jsonl`, and explicit `$LAZY_RUNTIME_ROOT/logs/hook-timings.jsonl` when present.
- Aggregation remains read-only and measurement-only. It must not change hook behavior or make timing data a gate-skipping authority.
- Invalid `--since` values fail argument parsing with a clear example.

Implementation map update:

- `.lazy-harness/scripts/lifecycle-compare-summary.py` — implements ISO timestamp parsing and `--since` filtering for compare logs.
- `.lazy-harness/scripts/hook-timing-summary.py` — implements ISO timestamp parsing, `--since`, and `--all-sessions` runtime log aggregation.
- `.lazy-harness/bin/lazy` — documents the new CLI flags in help output.
- `.lazy-harness/scripts/self-test.py` — protects `lifecycle-compare-summary --since` and `hook-timings --all-sessions --since` fixtures.
- `.lazy-harness/logs/README.md` — documents the new timing summary options.

Validation:

```bash
python3 -m py_compile .lazy-harness/scripts/lifecycle-compare-summary.py .lazy-harness/scripts/hook-timing-summary.py .lazy-harness/scripts/self-test.py
bash -n .lazy-harness/bin/lazy
python3 .lazy-harness/scripts/self-test.py --scope framework
```

Result on 2026-06-04: framework self-test passed (`ran=77`, `skipped=0`).
