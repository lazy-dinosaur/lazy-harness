# TDD — Analysis-Discovery-Capture Gate False Positive (fires on capture-complete turns)

Status: active
Date: 2026-07-04
Layer: TDD
Related ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
Related SDD: `.lazy-harness/spec/platform/retro-loop.md`
Related planning: `.lazy-harness/planning/analysis-discovery-capture-backlog.md`

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 캡처 게이트 오발화
  - capture gate false positive
  - discovery capture 오탐
  - STOP 게이트 중복
- Applies when:
  - the analysis-discovery-capture STOP gate fires and the agent believes capture already happened in-turn
  - testing analysis/correction LLM judgement plus successful current structural capture
  - evaluating real Pi callback, response hook and independent primary-answer delivery
  - verifying write/edit/insert/replace and namespaced transports
- Must:
  - when the gate fires, VERIFY capture completeness against records (not memory) before claiming false positive
  - distinguish current successful relevant record capture, failed/missing/unrelated proof, reuse, pending and no-record assertions; silence alone is not success
  - preserve both regressions: the verified before/after Pi mutation-transport matrix, the historical post-fix live recurrence, and the fresh source-linked controlled case that stays silent
  - keep counting recurrences via `lazy retro feedback --kind capture-gate-false-positive`
- Must not:
  - infer the post-fix live root cause from helper-only synthetic fixtures
  - treat IDs, fingerprints or no-record assertions as proof of semantic adequacy or execution approval
  - deploy the isolated B candidate without separate integration approval
- Record completion:
  - keep this as the primary B regression narrative; update the capture SDD only for independent packet/delivery deltas
- Related records:
  - `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
  - `.lazy-harness/spec/platform/retro-loop.md`

## Anchor-only edit recurrence — current-session investigation

The current session persisted two epoch-6 `lazy-harness-capture` assessments with valid `required` judgements but unverified facts for the OMP planning and parity records. Their edits used anchor-only `insert`/`replace` inputs without a path; subsequent reads supplied explicit paths. The later epoch-8 `judgement-absent-or-malformed` assessment followed an empty terminal response while yielding to a Reader, and is a distinct missing-envelope event.

Source inspection: `CaptureEvidence.target` accepts only path/file_path/filePath; `normalizePiTool` does not resolve anchor-only targets. Such an edit therefore cannot issue a write receipt through this path. `evaluate(required)` selects only a write receipt; a subsequent successful read does not convert that into write evidence. `evaluate(reuse)` selects the current read receipt instead. The earlier assistant repeatedly used `required` after readback, which cannot resolve the missing path-bound write receipt.

Controlled, read-only helper replay against development source, Task366 and reader-gpt6 release copies produced the same three outcomes: anchor-only insert + required = unverified; explicit-path read + required = unverified; the same current read + reuse = evidence-linked. Synthetic callbacks establish this mechanism, not the exact live receipt ledger or active module identity. No gate, installed runtime, hook or approval boundary was changed.

Current recovery uses the already-stored, actually read canonical facts with a `reuse` judgement under the existing SDD. It does not invent a write receipt, suppress assessment or rewrite unchanged facts for a green result. A bounded read-only watcher will inspect the next actual session assessment; live recovery remains pending until that entry is observed.

The actual watcher subsequently observed session entry `7c5218a6` at epoch 8: `unverified`, reason `capture response hook unavailable or missing assessment`, with no fact receipts. Thus the proposed reuse recovery did not establish live success. An isolated copy of the real response hook and capture helper then returned a capture object for a 1,423-byte payload but empty stdout for a 180,423-byte payload, with Bash reporting an argument-list-too-long error at the capture-helper invocation. Both exited zero. Evidence is retained at `/var/tmp/lh-capture-transport-5bnla1tx/results.json`. This reproduces a transport defect, distinct from anchor receipt admission; it does not alone establish the exact byte size of the failed live payload.

The existing `self-test.py#check_response_completed_no_auto_route_telemetry` large-payload case checks exit status but does not require capture output. Proposed repair scope: preserve full payloads and safety helper ordering while replacing oversized argv/environment transport with file/stdin handoff, and assert capture delivery plus safety-helper execution on large inputs. Do not truncate safety evidence, disable helpers, or infer success from exit zero. Source repair and regression validation precede any separately authorized installed-runtime/global deployment.

The user approved the source transport repair and regression-validation batch, without global installation or deployment. Implemented lossless `@file:` handoff above 65,536 UTF-8 bytes in the response hook and orchestrator helper runner, backward-compatible decoding in response helpers, and file-backed capture/injection/compare output. Shared decoder: `.lazy-harness/hooks/lifecycle/helpers/payload_transport.py#read_payload_text`; it is covered by the existing manifest `hooks/lifecycle/helpers/*.py` distribution glob. No installed package, guard or semantic classification was replaced.

Focused regression: `python3 tests/lazy-harness/capture-payload-transport.test.py` — 5 passed in 3.517s. Cases cover large UTF-8 input across legacy/orchestrator/compare, full-tail safety-helper execution, large capture plus safety output, legacy small-inline compatibility, and nonzero failure/cleanup when the decoder is missing. The suite is also invoked by `tests/lazy-harness/pi-capture-evidence.test.ts` so the existing capture self-test route exercises it. Final standard and live response acknowledgement remain pending.

Final source checkpoint passed standard **90/90**, including the SDK capture suite's new transport regression (`.lazy-harness/state/capture-transport-standard-validation-fixed.json`). The first run is retained at `.lazy-harness/state/capture-transport-standard-validation.json`: a static forbidden-substring check matched the new decoder name `read_payload_text(` inside the shadow helper. That helper now imports it as `decode_payload_reference`; decoding behavior is unchanged and no classifier or assertion was removed. A concurrent session encountered that intermediate state and was informed of the correction and completed gate. Active LSP did not establish all-clean: Python reported an unresolved dynamic `runtime_paths` import and an auxiliary throwing-call finding, with three paths inconclusive; successful executable validation is not described as clean LSP evidence. Live current-session acknowledgement is still the remaining recovery gate.

Live recovery acknowledgement is now verified: the bounded watcher observed session entry `7a76bd9d` at `2026-09-23T13:06:17.883Z`, and a direct read of the actual session JSONL confirmed root `/home/lazydino/dev/lazy-harness`, epoch 1, status `evidence-linked`, disposition `reuse`, and a successful `read` receipt for this canonical record (`readback: runtime-file`, SHA-256 `ec318873bf021114af111b135c55c1284bbefe061298d8ae7f1c1b7aa4a851eb`, 25,570 bytes). This closes the current-session missing-assessment recovery check; it is not merely helper silence or a synthetic callback. The receipt refers to the preceding record revision, before this acknowledgement was appended. Semantic relevance remains LLM-owned (`llm-judgement-not-verified`), approval remains `not-evaluated`, and no global deployment or paid benchmark is authorized. Exact historical live payload sizing and anchor-only write-receipt admission remain separate limitations, not claims fixed by this transport repair.

Follow-up recurrence: actual session entry `3d1c0851` (`2026-09-23T13:10:34.941Z`, epoch 1) rejected the next `reuse` judgement with `capture-unverified: missing successful current relevant tool/readback`. Thus `7a76bd9d` proves one successful acknowledgement, not stable recovery; the broader completion claim is withdrawn and follow-up task 10 remains open. The intervening `read` call requested offset 55/limit 14, while its successful tool-result metadata reported offset 41/nextOffset 67. Its snapshot and the subsequent on-disk file both had 26,560 bytes and mtime `1790169008006.2476`; the current SHA-256 was `3953c948beaf21276c4e548c32abf76ee773a7aa870f0d4d4c471b475e0271e9`. No later file modification is established by those observations. `CaptureEvidence.complete` requires identical start/result input hashes, so argument transformation is an investigation candidate, not yet a proven live cause. Unlike the earlier missing-assessment transport failure, this response contains a valid assessment rejecting its receipt. Source transport regression results remain valid; no semantic/approval gate is weakened.

User-selected follow-up: isolated callback reproduction, followed by a proposed fix rather than installed-runtime changes. `.lazy-harness/state/capture-read-argument-repro.mts` runs the current harness through the actual Pi `ExtensionRunner` and native `createReadTool`, with a controlled input-transform extension in a private temporary host. The final run passed four expected outcomes: unchanged inputs → evidence-linked; output-range metadata changed without callback-input changes → evidence-linked; range mutation before the harness's start callback → evidence-linked; identical range mutation after that callback → unverified with the observed missing-readback reason. Result: `.lazy-harness/state/capture-read-argument-repro.json`; fetch attempts 0, no provider invocation, temporary hosts removed. Initial fixture runs failed because its envelope lacked required newlines; these are fixture errors, not additional product failures.

This reproduces an order-sensitive input-hash rejection in source, but does not prove that the installed live extension mutated callback inputs. In particular, range metadata alone is insufficient, as the fourth control dimension demonstrates. Proposed next batch (not executed/approved): add bounded rejection diagnostics that distinguish missing start, input mismatch, epoch/path mismatch and snapshot drift without accepting altered inputs or weakening receipt validation; protect these through the isolated callback cases. Actual live identity/callback tracing remains necessary before attributing the recurrence or declaring stable recovery. Discovery capture: primary TDD evidence capsule; SDD/BDD/SSOT/DDD have no independent semantic delta from this diagnosis.

Actual-runtime read-only investigation (user selected, then explicitly requested uninterrupted follow-through): configured packages place Lazy-Harness before `pi-lens`. Installed `pi-lens/dist/clients/runtime-tool-call.js#getReadToolInput` returns the original `event.input` object; its read-expansion branch assigns `readInput.offset` and `readInput.limit` in place. The shipped `dist/index.js` contains the same assignments and `EXPANSION_LIMIT_LINES = 100`. Crucially, existing `/home/lazydino/.pi-lens/sessionstart.log` records at `2026-09-23T13:10:12.591Z`: `ts expanded read: capture-gate-false-positive.md lines 55–68 → Anchor-only edit recurrence — current-session investigation (41–66)`. At `.596Z` the next line names the exact failed read call prefix `call_ycWypGPtoSBrWZZHfJeDEEDY`; the session tool result is timestamped `.598Z`. This ties the previously isolated transform to the actual failing call, rather than inferring it from return metadata alone.

The configured release capture implementation still hashes the whole input at start and rejects a changed hash at completion (capture-evidence.ts lines 140/150; index.ts start/complete at 1214/1238). Thus opportunistic read expansion and strict receipt binding are incompatible when expansion runs after capture start; production expansion evidence and the four-case actual-SDK reproduction agree. This is distinct from the repaired large-payload hook transport. No installed package, source implementation, configuration or guard was changed during this investigation. Non-mutating operational recovery uses an explicit 101-line bounded read: above the inspected expansion branch's 100-line eligibility threshold, without disabling validation or fabricating receipts. Its live acknowledgement still needs observation; a permanent integration patch is not claimed. Reader pre-launch attempts were rejected first for missing explicit async, then for stale epoch after steering; no child ran, and direct map-first canonical fallback was used.

Operational readback verified: session entry `1d5f48d9` at `2026-09-23T13:41:51.798Z` returned `evidence-linked` at epoch 4. Direct session-file inspection matched its receipt to actual call `call_N2dgFEwdRq0G4xFqcxcTYjTx`, with requested arguments `{path: .lazy-harness/tests/capture-gate-false-positive.md, offset: 41, limit: 101}`. Independently hashing the serialized requested arguments reproduced receipt inputHash `c08110fee9974feaadebedcebc21a375a037870e211ead6ad39c5f0c2d12b1f9`; the read was successful, runtime-file backed, and fingerprinted the then-current 31,421-byte record. Unlike the earlier success-only inference, this acknowledgement is tied to the identified expansion condition and unchanged input hash. Read-only diagnosis and this operational workaround are verified; permanent inter-extension compatibility remains unimplemented, not silently approved. Later reads must remain actual current reads; no fabricated write receipt or relaxed hash check is introduced.

Post-removal-report verification: the existing `bun run test:pi-capture` native SDK suite completed **29/29 passed, 0 skipped, 68.01s**, with full output retained at `/tmp/capture-native-check-58y_uxbk.log`. These isolated fixtures do not load pi-lens; they exercise real SDK capture callbacks and the large-payload transport regression. This is controlled no-expansion validation, not proof that the current process unloaded pi-lens. A fresh settings check still found `npm:pi-lens` at global settings line 11. No implementation/configuration changes were made for this run; only runtime/validation artifacts and this capsule were produced. Runtime-removal ownership and the reported token-overhead reason remain in the existing deployment-binding SSOT.

Implementation map addition: `on-response-completed.sh` owns file lifetime, `lifecycle-check.py#run_one_helper` owns orchestrator subprocess handoff, response helper parsers consume the shared decoder, and `tests/lazy-harness/capture-payload-transport.test.py` protects transport/output/safety behavior. SDD has an independent file-reference transport contract update; BDD/SSOT/DDD have no independent product, configuration/ownership or domain delta. An attempted self-test registration edit exposed non-UTF-8 rewrite risk and was immediately undone; test registration uses the existing TypeScript capture suite instead.

Layer completeness: SDD — no independent contract delta; BDD — no product flow delta; SSOT — no installation/configuration/ownership delta; DDD — no independent delta. Implementation references remain `packages/lazy-harness-pi/extensions/lazy-harness/capture-evidence.ts` (`target`, `start`, `complete`, `evaluate`) and `index.ts#normalizePiTool`; no new graph relationship or operating policy is introduced.

## B source-path repair — isolated candidate

The user approved real source repair after the corrected four-model pilot, not
another toy-prompt trial. Selected design1 keeps LLM-owned necessity/relevance,
mandatory durable capture, fact reasons/ownership and current approval; runtime
checks only actual structural evidence. Analysis and user-correction capture now
share that route; no other safety helper is removed. This section supersedes the
historical keyword STOP expectations below, not their recorded observations.

- Base: merged A `47db0958934b9d58151fd20ac976293f2c7764cc`, latest origin/main
  at isolated clone preparation. No dirty original or old experiment baseline imported.
- Adapter: typed `CaptureEvidence` joins real started/result callbacks to bounded
  canonical readback/fingerprints; no model-invented runtime fields.
- Response: complete raw main answer stays unchanged on valid, malformed, ambiguous
  or nonterminal markers. Capture assessment is a separate non-triggering custom
  message, not the caller's replacement answer or a new completion tool.
- Unchanged status: explicit no-record assertion does not force rewrite/reapproval.
  Missing packet is explicit unverified, never no-record. Required proof remains
  unverified on failed/missing/unrelated callbacks or changed bytes.
- Reuse: current canonical read plus current semantic judgement, without duplicate
  write. Bounded receipts survive unrelated last-40 projection; steer/session and
  work-unit invalidation clear them. Exact limits are in the capture SDD.

### Source-linked protection

`tests/lazy-harness/pi-capture-evidence.test.ts` exercises official Pi
ExtensionRunner dispatch, actual Pi read/write tools and real response hook/helper
processes. Third-party insert/replace names use mock completion events with real
fixture file mutation, not a claim of installed provider/native-question integration.
Tests include status/correction pollution, successful capture, failed insert/replace,
missing/args-only/unrelated receipts, epoch/steer, long history, current-read reuse,
changed bytes, malformed markers, trailing output-format text and separate delivery.
Existing destructive/option negatives use inert payloads; no hazardous command runs.
The standard self-test calls the source-side fixture; installed hosts without this
source test file run the shared transport checks only.

Baseline-negative export must preserve Git executable modes as well as bytes.
The first preparation mistakenly exported helper files as 0644, so initial missing
assessment failures are retained but are not capture-behavior evidence. Corrected
0755 baseline shows actual keyword STOP on unchanged status and no structural
assessment after actual successful write/read. Independent evidence logs retain
that preparation defect rather than replacing it with the corrected run.

### Validation boundary

The first focused source batch passed 20 adapter tests / 346 assertions. Later
root/error-delivery fixtures and bounded-history test refinement are checked by
the final standard gate, not retroactively included in that first count. The local
Bun source typecheck passed. At that prior B checkpoint, Pi SDK-target semantic checking reported five existing
diagnostics, independently reproduced against the untouched base export: two old
adapter signature mismatches and three locked dependency declaration diagnostics.
No dependency patch, skipLibCheck or ambient type suppression is used. Full final
state and gate outputs belong to the isolated external review evidence, not a
claim of live adoption or semantic-counterexample resolution.

The subsequent target-only follow-up is recorded in
`.lazy-harness/tests/pi-agent-package.md#pi-target-typecheck-closure`: all capture
cases now execute with actual Node22 and node:test, rather than claiming that
Node-only checking proves the previous Bun-hosted SDK test mode. Prior B results
and diagnostic evidence remain historical, not overwritten.

### Independent-review P2 correction

Review identified two concrete structural defects, reproduced through the real Pi
callback/full-hook fixture before correction: an extra closing marker was accepted
as `no-record-asserted`, and successful write → duplicate ID restart → failed
result retained an `evidence-linked` receipt. Both new regressions failed on the
previous frozen source; prior evidence is retained unchanged.

The parser now requires exactly one opening and one closing boundary. A duplicate
ID invalidates matching issued write/read receipts as well as a pending call;
unrelated receipts remain available. The bounded receipt scan also recognizes a
retained ID after recent-ID eviction. These changes enforce the existing SDD,
not new semantic or approval authority. The tests preserve the complete raw answer,
assert explicit unverified after failure with unchanged bytes, and retain valid
single-envelope/fresh-ID success controls. The final adapter suite has 25 cases;
exact-state results are kept in isolated review evidence, not inferred from the
previous 20-case green or the 300-second standard timeout.

The subsequent standard run ended with two failed checks, not a timeout. Read-only
triage found statically confirmed stale-contract expectations in the context-retry
fixture (forbidding any reused-work-unit system prompt) and lifecycle parity
fixture (requiring a prose-derived capture STOP). The governor retained only the
self-test tail, so these are not claimed as observed precise first-failure causes.
The approved fixture-only follow-up preserves reused fingerprint status, forbids
renewed grounding and positively requires capture guidance. Parity retains the
identical raw prose and all legacy/shadow/side-effect comparisons, but requires no
keyword-derived semantic STOP. Typed required/pending/success and other safety
controls remain protected by the existing adapter suite; a silent raw-prose case
alone is not evidence of successful capture. No production behavior was changed
in this follow-up, and prior failed validation evidence remains intact.

This review correction adds no independent SDD/BDD/SSOT/DDD delta; the existing
four-row matrix and implementation links below still govern. Final validation
uses the same standard checks with an explicitly approved 600-second budget,
not a release matrix or a changed permanent/default setting.

### Layer completeness — current B candidate

| Layer | Judgement |
|---|---|
| SDD | Independent packet/receipt/delivery delta in `spec/platform/analysis-discovery-capture-gate.md`; replaces the legacy cue-STOP contract only on two capture routes. |
| BDD | No independent product flow delta; main-answer/advisory transport is owned by the capture SDD and tested here. |
| SSOT | No independent ownership/config delta; CLI Tool Boundary already assigns semantic authority to the LLM. |
| DDD | No independent domain rule or vocabulary delta. |

### Current implementation map

- Status: `needs-review`
- Primary source: `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`,
  `packages/lazy-harness-pi/extensions/lazy-harness/capture-evidence.ts`.
- Lifecycle: `.lazy-harness/hooks/lifecycle/on-response-completed.sh`, both capture
  helpers, `.lazy-harness/scripts/lifecycle-check.py`.
- Tests: `tests/lazy-harness/pi-capture-evidence.test.ts`,
  `.lazy-harness/scripts/self-test.py#check_analysis_discovery_capture_helper`.
- Graph: `kg_b_capture_structural_impl`, `kg_b_capture_structural_test`.
- Limits: structural green cannot establish semantic relevance, truthful no-record,
  retention of all facts/reasons/ownership or real execution authorization. No new
  model sessions, C expansion, live sync or general superiority claim in this batch.

## Historical regression scenario (live occurrences, 2026-07-04)

The following sections preserve earlier observations and validation versions;
their legacy silence/keyword expectations are superseded by the B candidate above.

Three same-session occurrences (retro feedback ids `fb-mr6dziod-05`, `fb-mr6e1fxn-aq`, `fb-mr6e9dol-0l` — first pattern to reach the 3-repeat threshold):

1. Turn appends batch results/queue to `.lazy-harness/planning/memory-device-implementation-plan.md` (in one case already committed, `ebdcb53`) → gate still fires with the full "chat-only" warning.
2. Turn is a pure record-recap (next-steps summary read FROM existing records, zero new knowledge) → gate fires.
3. Root cause: the gate is a post-hoc text classifier over the response; it does not check whether canonical/planning records were mutated during the turn.

Expected behavior after a future heuristic improvement: gate stays SILENT when the turn's discoveries were written to records in-turn (detectable via record file mtimes/git status delta within the turn window), and still FIRES on genuine chat-only analysis.

## 2026-07-14 Pi tool-name regression and focused fix

After three architecture planning records and a complete seven-layer judgement were
persisted, the gate fired again. The occurrence is recorded as retro feedback
`fb-mrkkh8kv-t0`.

A synthetic payload against the current helper reproduced the adapter gap:

| `recent_tool_calls[].name` | Eligible planning path | Before | After |
|---|---|---|---|
| `replace` | yes | STOP | silent |
| `functions.replace` | yes | STOP | silent |
| `Edit` | yes | silent | silent |
| none (chat-only) | no | STOP | STOP |

Source inspection confirmed the former `WRITE_TOOLS` set included legacy
`Write`/`Edit`/`MultiEdit` variants but not Pi's `replace` names. The user selected
**Honor SDD intent** and separately approved the focused seam. The helper now recognizes
`replace` and `functions.replace`; genuine chat-only STOP behavior remains unchanged.

## Protection

- Live reproduction: a capture-complete architecture turn received STOP before the fix;
  records were verified directly before classifying it as a false positive.
- Automated fixture: Pi `replace`, `functions.replace`, and legacy `Edit` with an eligible
  planning path are silent; a genuine chat-only payload still emits STOP.
- Focused helper check, shell syntax, Python compilation, and the full framework self-test
  pass.

## Layer completeness

- SDD: updated `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md` because
  the user confirmed its same-turn-silence contract as authoritative and the record now
  names Pi mutation-transport recognition plus the separate execution gate.
- BDD: no independent delta because no user-visible product workflow changed.
- SSOT: no independent delta because no config, storage, ownership, or source-of-truth
  invariant changed.
- DDD: no independent delta because no domain term or business rule changed.

## Implementation map

- Status: `verified`
- Validation: focused helper regression passed and framework self-test completed with
  `ran=85`, `skipped=0`.
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh` — the gate whose heuristic this regression targets.
  - `.lazy-harness/retrospective/feedback.jsonl` — counted live occurrences, including
    `fb-mrkkh8kv-t0`.
  - `.lazy-harness/planning/analysis-discovery-capture-backlog.md` — improvement backlog
    and exact Pi tool-name reproduction.
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — opt-in structural trace for the unresolved live adapter path.
  - `.lazy-harness/ssot/runtime-and-shared-state.md` — runtime-only trace path and no-raw-content boundary.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_analysis_discovery_capture_helper` protects
    Pi `replace`, `functions.replace`, legacy `Edit`, candidate/planning capture, explicit
    judgement, and genuine chat-only STOP.
  - focused synthetic result: `replace` → silent, `functions.replace` → silent,
    `Edit` → silent, chat-only → STOP.
  - `.lazy-harness/bin/lazy test --scope framework` passed (`ran=85`, `skipped=0`).
  - `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` protects trace default-off/privacy/runtime-root/follow-up behavior.
  - `.lazy-harness/evidence/2026-07-14-pi-agent-end-structural-trace.md` records the fresh source-linked current-source non-reproduction without raw conversation/tool content.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
  - SDD: `.lazy-harness/spec/platform/retro-loop.md`
  - SSOT: `.lazy-harness/ssot/runtime-and-shared-state.md`
- Machine index:
  - `kg_analysis_discovery_capture_pi_transport_impl_20260714`
  - `kg_analysis_discovery_capture_pi_transport_test_20260714`
  - `kg_pi_agent_end_structural_trace_impl_20260714`
  - `kg_pi_agent_end_structural_trace_test_20260714`

## Discovery capture

- DDD: none because no domain vocabulary or business rule changed.
- SDD: updated because `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
  now records the user-confirmed authoritative behavior, Pi transport requirement, and
  separate execution-approval boundary.
- BDD: none because no user-visible product flow changed.
- TDD: updated because this record now preserves the live recurrence, before/after Pi
  transport matrix, focused fixture, and full validation evidence.
- ADR: none because ADR 0034 already decides capture-before-completion and no new trade-off
  was approved.
- SSOT: none because no storage, ownership, configuration, or source-of-truth rule changed.
- Planning: updated because `.lazy-harness/planning/analysis-discovery-capture-backlog.md`
  records the approved and completed focused seam.
- Candidate store: none because the mismatch was confirmed, approved, implemented, and
  validated through canonical SDD/TDD/Planning records.

## Rule placement

- Rule: capture-complete turns using the active Pi mutation transport must be silent, while
  genuine chat-only analysis must continue to emit STOP.
- Scope: framework-global analysis-discovery capture regression
- Primary record: `.lazy-harness/tests/capture-gate-false-positive.md`
- Contract owner: `.lazy-harness/spec/platform/analysis-discovery-capture-gate.md`
- Why not AGENTS.md: this record owns the reproduced regression and fixture boundary, not
  the universal capture grammar.
- Confirmation: user selected `Honor SDD intent` and then approved the focused helper
  helper seam on 2026-07-14; the regression is now fixed and validated.

## 2026-07-14 post-fix recurrence

After the transport fix passed focused and framework tests, a later live Pi turn still received
STOP even though the assistant response contained all seven required `Discovery capture` buckets.
Running the current helper directly with the same assistant judgement, a STOP-shaped last-user
message, and todo-only recent tools is silent. This proves the earlier `replace` adapter gap is not
a sufficient explanation for the new occurrence; it does not yet prove whether the remaining fault
is `agent_end` response projection, stale/queued advisory delivery, root/runtime skew, or another path.

The recurrence is counted as `fb-mrkm4qyk-v0`. The unresolved cause lives in
`candidate-capture-gate-post-judgement-runtime-conflict-20260714`. The user selected
**Payload trace**: preserve the SDD contract and investigate the adapter/continuation payload before
weakening the gate, then separately approved the bounded instrumentation seam. The adapter now
writes an opt-in, content-free runtime trace and the fake-runtime fixture protects default-off
behavior, structural fingerprints, no raw content, and unchanged queued `followUp` delivery.
A fresh source-linked Pi retry completed normally with trace enabled. Its single structural row
contained non-empty assistant (`605` bytes) and last-user (`592` bytes) projections, recent
`bash`/`bash`/`read` tools, hook status `0`, empty hook stdout/stderr, and no advisory. The complete
seven-layer judgement received no continuation. The current source path therefore does not reproduce
the recurrence for this controlled case. The historical stale/queued/runtime cause is not canonical.
The user selected **Close current remediation**: retain this regression history, supersede the active
cause candidate, and authorize no helper-threshold or continuation change. See
`.lazy-harness/evidence/2026-07-14-pi-agent-end-structural-trace.md`.

## Discovery capture — post-fix recurrence

- DDD: none because no domain vocabulary or business invariant changed.
- SDD: updated because the governing capture contract remains authoritative during investigation.
- BDD: none because no user-visible product flow changed.
- TDD: updated because this record now preserves the post-fix live recurrence, direct-helper
  counterexample, bounded trace fixture, and the boundary against claiming an unverified cause.
- ADR: none because ADR 0034/0051 already govern the contract and runtime bridge.
- SSOT: updated in `.lazy-harness/ssot/runtime-and-shared-state.md` for the runtime trace path.
- Planning: updated because instrumentation and fresh source-linked trace are complete and current
  remediation is user-closed.
- Candidate store: superseded without promoting a historical cause.


## macOS hook tempfile collision repair — 2026-10-15

The user approved a bounded source fix and regression validation after reporting tmp failures on every hook. Installed-project rollout, global package changes, tmp cleanup and sourceRoot rebinding are not included. Diagnostic evidence on macOS: a `mktemp` template ending in `.XXXXXX.json` kept the Xs literal, and the already-existing `lazy-lifecycle-check.XXXXXX.json` caused `File exists`. This proves the temporary-file defect; it does not prove that every full hook abort has the same cause because the response hook has a fallback.

Source repair: message primary and `/tmp` fallback templates now end in `XXXXXX`; response `run_orchestrator_check` writes `orchestrator.json` inside the hook's existing unique private payload directory instead of allocating a second suffix-template/pid-fallback path. The existing EXIT trap owns result cleanup. Existing payload bytes, capture output, safety helpers and engine ordering are preserved; no helper is disabled and no pre-existing temp file is deleted.

### Implementation map — tempfile ownership

- `.lazy-harness/hooks/lifecycle/on-message-received.sh`: primary/fallback payload creation uses randomized portable templates; its EXIT trap retains ownership.
- `.lazy-harness/hooks/lifecycle/on-response-completed.sh#run_orchestrator_check`: response invocation's `PAYLOAD_DIR` owns the orchestrator result and cleanup.
- `tests/lazy-harness/capture-payload-transport.test.py#CapturePayloadTransport`: existing large/small payload, safety and decoder-failure protection remains registered through `tests/lazy-harness/pi-capture-evidence.test.ts`. New `test_message_temp_templates_generate_distinct_names`, `test_message_hooks_repeat_and_overlap_without_touching_old_tempfile`, and `test_response_hooks_repeat_and_overlap_in_private_directories` protect both templates, real repeated/concurrent hooks, old-file sentinel preservation and private-file cleanup.
- Canonical graph: `kg_hook_portable_tempfile_ownership`; generated implementation index remains a derived cache, not a new authority.

### Layer completeness — bounded tempfile repair

| Layer | Judgement |
| --- | --- |
| SDD | No independent API/packet/engine contract delta; existing full-payload and capture contracts remain unchanged. |
| BDD | No independent user-flow delta; this restores existing hook behavior under repetition/concurrency. |
| SSOT | No config, sourceRoot, package or deployment ownership change; installed-host state remains in the existing binding SSOT. |
| DDD | No independent domain vocabulary or business-rule delta. |

Code organization review: keep allocation next to each hook's existing lifetime owner; no new abstraction, file splitting or unrelated cleanup is needed. Discovery capture: this TDD is primary for the approved fix and regression; the migration audit SSOT owns only rollout status. Checkpoint on this Mac: `lazy check` passed (1,886 checked; two warnings refer to missing paths in the pre-existing node_modules backup), and `python3 tests/lazy-harness/capture-payload-transport.test.py` passed 8 tests in 4.855s. The focused suite includes native repeated/concurrent hook runs, sentinel preservation, random names and cleanup. One final `lazy validate --plan standard` follows this canonical-record checkpoint; its actual runtime receipt owns that result, not this pre-run note. Source validation is not installed-host rollout or universal live-hook acceptance.


Final standard result for the approved tmp batch: **not passed**. `.lazy-harness/bin/lazy validate --plan standard` exhausted its default 300s budget (300.005s elapsed); fast-static passed in 0.894s, then full-self-test was terminated after the remaining 287.822s. Runtime log: `/var/folders/97/c1s7nf4s6jq_l8zjmzbpp0640000gn/T/pi-fabric-shell-oSZZ3Y/output.log`. The native focused 8-test success remains valid, but full regression and completion remain unverified; timeout is not evidence of a specific functional assertion failure. No automatic rerun, time-budget increase, downstream deployment or validation-policy change was performed. The independent v1 hook-efficiency analysis is retained in the existing performance plan.
