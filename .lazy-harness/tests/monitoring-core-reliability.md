# TDD — Module reliability acceptance

Status: experimental
Layer: TDD

## Rule digest

- Status: advisory
- Layer: TDD
- Scope: host-project
- Confidence: medium
- Aliases:
  - 모듈별 합격 기준
  - monitoring reliability
  - 동결 검수
- Applies when:
  - evaluating or strengthening the current monitoring reference modules under the user-approved standard profile
- Must:
  - use separate development and frozen acceptance examples with labels excluded from model input
  - evaluate actual input views, decisions, reference reads and proposal receipts, not registration or confidence alone
  - require each acceptance round to meet each module's thresholds and preserve all failures
  - preserve the prior extended180 HTTP/USD1 SDK-estimate/900s experiment and original144-envelope24-consumed/previous20 ledgers; enforce the NEW SDK-source experiment's separate144 HTTP/USD1 SDK-estimate/900s-active envelope without transferring unused requests
- Must not:
  - tune on a failed frozen acceptance set then claim independent acceptance on the same set
  - send actual user transcripts, activate Pi hooks, write business state or inject context
  - present author-labelled synthetic quality as production accuracy
- Related records:
  - `.lazy-harness/spec/platform/monitoring-core.md`
  - `.lazy-harness/planning/jev-context-and-background-monitoring-research.md`
  - `.lazy-harness/tests/test-strategy.xml`

## User-confirmed acceptance

Standard profile1 initially allowed two development12 rounds and144 HTTP. After both rounds and24 consumed requests, the user explicitly approved up to three additional development rounds (five total) and an extended180 HTTP ceiling. Frozen acceptance60 cases twice, USD1 SDK estimate and900s metered-process limits are unchanged. Migration must preserve the old ledger as an exclusive backup and retain consumed requests, trace, spend and failures. Stop development at first pass; never repeat unchanged passing development just to use the budget.

Per module and per acceptance round: mode accuracy>=90%, run recall>=90%, defer recall>=90%, false execution rate among expected non-run<=5%. Context-reference exact read/returned ID set>=90% on expected-run cases. Candidate quote/source/status and returned reference identity/version/content must always match actual supplied/read data. Audit, permissions, idempotency, cancellation, stale results and accounting tests must all pass. Cross-round mode agreement>=95% separately for each module. Error/timeout/malformed or absent results cannot masquerade as correct uncertainty or disappear from denominators.

The input-visible coverage is tested by recording actual JudgeTask views, model calls, core reports, readReference invocations and memory-sink records. Host identity authenticity and real Pi delivery remain outside this synthetic run. Holdout labels are written before development evaluation; the set is frozen by content digest, never sent as expected labels to the classifier. Author-labelled data is not independent human adjudication.

## Evidence capsule — synthetic acceptance and final standard passed

- Mechanical checkpoints:53 distinct protection cases across the changed-target checkpoints and strict typing PASS. Actual model quality is evaluated separately; repeated runs are not extra distinct cases.
- Development round1 (12 actual HTTP): knowledge11/12, references10/12; the reference module executed requests for unavailable source topics, and a quotation edit was confused with a tentative proposal. Input/source integrity and audit checks passed.
- Module-owned questions were strengthened for own-user commitment vs quotations and current source availability. HTTP redirect, invalid probability, cancelled/unpriced requests and technical tool-result dispatch have protection tests. No feature-specific keyword classifier/core branch was added.
- Development round2 (12 more HTTP): references12/12 with run/defer recall100%, unwanted0 and exact reference set100%; knowledge11/12, run recall100%, unwanted0, but defer recall3/4=75%, below the fixed90% requirement. d12's tentative log-format change was skipped instead of deferred. This is a known miss, not a pass.
- Development round3 still skipped d12. Round4 clarified the goal as actual project decisions including pending/underspecified changes. Both modules then achieved12/12 and all development criteria. Development stopped at that first pass. Code and60-case acceptance data stayed frozen throughout both acceptance rounds; no acceptance-result tuning occurred.
- At the original boundary24/144 HTTP were consumed. The approved migration preserved that ledger; after development round4 the extended ledger held48/180 HTTP, SDK estimate USD0.0029988 and active time22.869s. Original20-request experiment untouched. These are development-end values, not a live or final acceptance total.
- At the original two-development-round boundary, inference stopped and the user approved up to three more rounds/180 total requests. The old144-request ledger was preserved with24 consumed HTTP in ledger.json.before-extension.json; migration records its digest and consumed counts. The separate old20-request experiment remains untouched. Criteria, d12 label and frozen60×2 are unchanged.

## Frozen acceptance result — qualified synthetic gate

Actual report: `.lazy-harness/evidence/monitoring-core/reliability-standard/ledger.json.summary.json`; detailed views/read records/receipts and all development failures remain in the sibling ledger. Both60-case rounds completed with the same frozen code and unchanged dataset/model profile. Each round independently passed the preset gates; no averaging across rounds hides a failed gate.

| Module/metric | Round1 | Round2 | Gate |
|---|---|---|---|
| knowledge mode accuracy |58/60 (96.67%)|57/60 (95%)|>=90%|
| knowledge run recall |19/20 (95%)|18/20 (90%)|>=90%|
| knowledge defer recall |20/20|20/20|>=90%|
| knowledge unwanted run |1/40 (2.5%)|1/40 (2.5%)|<=5%|
| references mode accuracy |59/60 (98.33%)|59/60 (98.33%)|>=90%|
| references run recall |19/20 (95%)|19/20 (95%)|>=90%|
| references defer recall |20/20|20/20|>=90%|
| references unwanted run |0/40|0/40|<=5%|
| references exact read/returned set |19/20 (95%)|19/20 (95%)|>=90%|

Cross-round agreement: knowledge59/60 (98.33%), references60/60 (100%), both>=95%. Actual view/source integrity/audit checks passed for every observation; no timeout/missing/malformed result was discarded or counted as correct uncertainty.

Residual errors are intentionally retained: a08 deferred a two-source evidence request; a17 missed a committed responsibility decision; a24 treated a no-policy-change lookup request as a candidate. Round2 additionally missed a06's reaffirmed reporting decision. These are prediction errors, not fabricated-source/permission violations. Knowledge recall in round2 sits exactly on the90% boundary: the result has limited margin and is not a statistical or production guarantee. Do not patch these acceptance cases and claim fresh independent success on the same set.

Totals:48 development +120 acceptance =168 additional classifier HTTP of180 allowed, SDK estimate USD0.010432296 ofUSD1, active metered execution77.937s of900s. The remaining development slot was not consumed after a pass. No chat/Luna/Pi-hook/business-write/injection activation. The old20-request experiment and original144-limit/24-consumed ledger backup remain intact. Costs are estimates, not invoice verification. Final standard also passed: fresh framework91, skipped0, jobs4, errors[],446.774s. Actual bounded report: `.lazy-harness/evidence/monitoring-core/reliability-standard/standard.json`. This is evidence-only closure; code/fixtures/config are unchanged after the frozen experiment.

## Implementation map

- Status: `verified` (source/strict typing/53 mechanical cases, qualified frozen acceptance, fresh standard91 passed; no production qualification)
- Verified symbols: validateSuite, materialize, nativeValidity, probe, checkTrial, score, stability, phaseGuard, validateProfile, extendLedger and codeFingerprint. Source/strict checks and actual CLI stages validate these names; no unimplemented API is advertised.
- `.lazy-harness/scripts/monitoring-core-reliability.ts`: suite validation, per-round metrics, actual core probes, checkpointed stage ledger and summary.
- `.lazy-harness/fixtures/monitoring-core/reliability.json`:12 development/60 acceptance cases with synthetic source catalogues and gold labels.
- `.lazy-harness/fixtures/monitoring-core/reliability-profile.json`: explicit base/approved-extension limits. extendLedger preserves consumed accounting and phaseGuard enforces the selected development ceiling; CLI keeps an exclusive before-extension backup.
- `.lazy-harness/scripts/monitoring-core-examples.ts`: reference modules and typed classifier adapter, including invalid-probability fail-closed handling.
- `.lazy-harness/scripts/monitoring-retrieval-poc.ts`: shared Budget, createMeteredRequest and openMeteredClient; legacy20-request experiment remains unchanged in scope.
- `tests/lazy-harness/monitoring-core-reliability.test.ts`: evaluator falsification, split/balance/leakage checks, actual module observations and accounting protection.
- `tests/lazy-harness/monitoring-core.test.ts`: existing core boundaries.
- `.lazy-harness/scripts/monitoring-core-sdk-reliability.ts`: actual SDK fixture→original observer/settled bridge/core/modules→metered actual classifier→target/effect; independent gold/source/model-propagation/received-body oracle and frozen phase journal. Verified exports: validateSdkProfile, validateSdkSuite, auditSdkTrial, probeSdk, deliveredReferenceIds, scoreSdk, sdkStability, sdkFingerprint, sdkPhaseGuard.
- `.lazy-harness/fixtures/monitoring-core/sdk-reliability.json` and `sdk-reliability-profile.json`: separate new12/60 author gold and explicit144/USD1/900s-active approved envelope; no previous-ledger reuse.
- `tests/lazy-harness/monitoring-core-sdk-reliability.test.ts`:27 protection tests,72 actual SDK deterministic-oracle traces, source/model/material/effect/receipt falsification, missing-case and actual-delivery metrics. Scripted judge results here are not semantic quality.
- `.lazy-harness/evidence/monitoring-core/sdk-accuracy-standard/ledger.json.summary.json`: qualified frozen actual-Jev60×2 report and preserved residual errors; sibling ledger holds source/view/native answers/handoffs/effects. No actual-user activation.
- `.lazy-harness/knowledge/graph.jsonl`: append confirmed implementation edges only; `.lazy-harness/generated/implementation-index.json` mirrors them as derived navigation, not authority. Existing legacy rows remain untouched for the separate user-approved guided migration.

## Layer completeness

| Layer | Independent delta |
|---|---|
| SDD | Existing monitoring SDD now points to this acceptance record and documents shared metered-client accounting/serial boundaries. Module-owned commitment/source-availability questions changed; no live adapter or business API change. |
| BDD | No user-facing Pi flow, hook or injection delta. |
| SSOT | No production model/auth/config/ownership change; separate test-only profile. |
| DDD | Synthetic labels and references are not host business facts. |

## User correction — agent-driven SDK accuracy qualification required

User-confirmed correction: “아니 테스트해서 검증하면 되잔아 얼마나 정확한지 이런거”. The user wants the agent to run controlled tests and measure how accurately the monitoring system judges/selects/acts, not hand testing responsibility back to the user as a manual pilot. Manual observation is a later deployment check, not a prerequisite or substitute for quantitative semantic testing.

Reason: P3–P5 used scripted judgement or local diagnostic echoes to qualify transport, field minimization, cancellation and receipts. Their27/19/etc passing case counts and framework91 gates are not semantic accuracy measurements. The earlier frozen classifier results above are real but cover the prior directly supplied-core corpus, not the newly connected SDK path or a fresh independent sample. Preserve both boundaries and all prior failures.

No prior manual-start/data restriction is silently reversed: do not collect real conversations, activate a live observer, call chat/Luna or write business state. Previous execution approval is not reused for a new paid-classifier experiment. Existing168/180 and the old20-request ledger remain immutable; unused12 requests are not silently reassigned.

### Approved SDK-source measurement — executed; results below

- Drive actual Pi SDK sessions with authored synthetic user/assistant/tool traces and the official faux main provider. Feed the actual source-derived view through the existing core/bridge/modules and controlled receiver/test effects, replacing scripted semantic decisions with the real configured classifier (`openrouter/typesafe/jev-1.14`, typed `typesafe-system-one` API).
- Use new case identities/utterances and a separately frozen gold-labelled corpus, not retune/relabel the previous acceptance set. Recommended development12 up to2 rounds, then new held-out60 twice with unchanged code/profile. Labels/expected reference IDs stay out of classifier input. Freeze before acceptance and preserve incorrect predictions; repeated cases check stability, not120 independent samples or production truth. Author labels are not independent human adjudication.
- Report each module's confusion matrix, per-mode precision/recall/F1, mode accuracy, false runs, missed runs, incorrect defer/skip, exact selected reference IDs/versions/bodies, and source→judgement→received material→actual test-effect reconciliation. Operational missing/timeout/malformed results remain visible in denominators, never counted as correct uncertainty.
- Preserve the existing accepted gates for a standard qualification: accuracy/run recall/defer recall each>=90%, unwanted-run among non-run<=5%, expected-run reference exact set>=90%, cross-round agreement>=95%; source/permission/receipt integrity violations must be0. Precision/F1 are additionally measured, not a silently invented new acceptance threshold.
- Proposed NEW envelope: at most144 classifier HTTP, USD1 SDK estimate and900000ms active metered execution; actual chat/Luna requests0, real-user data0, external business effects0. Reuse the metered client and journal design, but use a separate new ledger/profile/case/code digest and no silent reset/replay of uncertain pending work.

The standard profile was explicitly approved, implemented and executed as recorded below. This existing TDD is the primary accuracy-work record; the integration plan carries only a priority pointer. Earlier pre-execution statements are historical, not current claims that no measurement exists. No real-user pilot or live deployment was activated.

User-confirmed execution choice: “표준 종단 실측 (Recommended)”. Approve the standard new SDK-source benchmark implementation/protection tests and actual classifier experiment: development12 up to2 rounds, fresh acceptance60 twice, NEW maximum144 classifier HTTP/USD1 SDK estimate/900000ms cumulative active metered execution. Use existing configured Jev only; actual chat/Luna0, real-user data0, business effects0. Preserve prior ledgers and unused12. Model/profile/corpus/code freeze and explicit partial/failure accounting remain required; no production or manual-pilot activation is authorized.

## Accuracy meaning and architecture clarification — before the SDK run

The user asked whether “accuracy” covers correct module attachment and receipt of all necessary information, and requested the exact current structure. Source-confirmed distinctions:

- Prior95–96.67% knowledge and98.33% references figures are run/skip/defer MODE accuracy in the earlier directly supplied-core60-case corpus, not live monitoring-to-module end-to-end completeness. Reference exact read/returned set was separately19/20 (95%) each round. Exact returned body/version/source integrity is another property, not semantic relevance/recall. No new SDK-chain semantic or joint-success rate has been measured yet.
- `MonitoringCore.view` passes the original normalized single event plus goal/scope/version and only references allowed by BOTH processor declaration and host grants. This is not an arbitrary full-agent-context read. Current reference views are host-supplied catalogues; `createContextReferences` selects/reads those IDs/bodies, not an automatically connected repository/DB search. The core filters event kinds and reference kinds, not a general per-module event-field redaction/whole-stream summarization system.
- Tested synthetic path: actual SDK session/source -> `PiMonitoringObserver` bounded frames -> `MonitoringObservationBridge` at agent_settled -> `MonitoringCore` -> optional module-owned typed JudgeBatchPort -> trusted processor proposals -> material receiver / `SyntheticTriggerRegistry` exact granted handler -> test effect/execution receipt. run is judgement, not an authority grant. P3–P4 SDK integration tests used scripted decisions; real Jev is required for the newly approved semantic qualification.
- The separately loadable `ManualMonitoringPilot` captures only post-start allowed text/tool metadata into local diagnostics. It imports/calls neither the core/bridge nor Jev or trigger registry. It is NOT a live version of that whole pipeline. Shared runtime entrypoint has no imports of the new core/observer/bridge/registry/pilot classes; no automatic live connection was implemented. Internal private model thoughts are not observable input. Async queues are in-process, not an independently deployed daemon or CPU-isolated service.
- For the new qualification, additionally report DIRECT JOINT end-to-end case success: source reaches the intended watch without identity loss; mode is gold-correct; required reference set is complete/relevant; exact selected bodies/versions arrive; permitted expected test effect and matching receipt occur for run; and skip/defer causes no unwanted effect. Count missing/error cases rather than multiplying independently measured percentages. Existing per-module gates stay unchanged; this descriptive joint metric does not silently create a new numeric threshold.

At this clarification point no new benchmark runner/corpus has been written and new actual classifier HTTP is0. The approved144/USD1SDK-estimate/900s-active profile remains bounded; answering the structure question does not imply a completed accuracy test or live activation.

## Core responsibility evaluation — user-confirmed priority

The user reaffirmed that the core's responsibilities must be concretely implemented and properly evaluated. Do not substitute counts of green tests, SDK startup, model-mode accuracy or a manual pilot for that contract evaluation. This clarifies the already approved benchmark; its144/SDK-USD1/900s-active envelope and existing semantic thresholds are unchanged. The question itself is not new execution approval.

| Owner / responsibility | Independent oracle / required observation | Qualification |
|---|---|---|
| Source adapter / delivery boundary | Actual SDK raw trace vs admitted source IDs/order/content and explicit omission; correct target observes selected ID/version/body and receipt | Invariant violations0 in the specified cases; report omissions rather than silently claim coverage |
| Core event/context lifecycle | Independent fixture scope/version/sequence, duplicate/conflict/out-of-order and replacement/stop transitions vs actual dispatch/effects | Every must-hold case passes; no stale/cross-scope/duplicate effect |
| Core routing and views | Declared event watches plus host reference/action grants vs actual processor views/read/proposals | No undeclared processor dispatch, unauthorized reference or action; do not confuse a model's wrong run decision with bypassed host grants |
| Core invalid judgement / failure isolation | Invalid/absent typed decision/evidence, thrown worker and timeout; compare each module's independent outcome/effect | No fabricated successful judgement or unwanted effect; one failure cannot erase another valid result |
| Core budgets / physical ownership | Before/after event/read/proposal/request counters, queue/concurrency limits and raw settlement | Stop/start cannot reset lifetime budgets; logical timeout must not free an uncooperative physical slot early |
| Target/registry (not the inner core alone) | Destination/content/source/execution identities and independent controlled effect ledger vs acknowledgements | Wrong/missing/late ack cannot be successful execution; no unconditional echo is used as the proof |
| Module semantic judgement / reference choice | Frozen gold modes and required source sets vs actual real-classifier decisions and ACTUALLY received selected bodies | Report accuracy/precision/recall/F1, FP/FN/defer errors and exact-set correctness; prior numeric gates apply here |
| Whole assembled path | Direct case-level source→view→decision→selected material→actual target effect/receipt comparison | Report joint case success and which boundary failed; never infer it by multiplying separate rates or averaging a failed layer away |

For the user's “necessary information is actually handed over” requirement, compute information recall from gold-required references that really reached the target, information precision from relevant received references/all received references, and exact-set success on expected-run cases. A missed run with no handoff is not excluded from recall; unrelated extra material hurts precision. Exact text/version/source match is a distinct hard integrity check.

Expected outcomes must come from independent authored fixtures/registration/grant/state definitions, not copied from the same core report/selected IDs under test. Evaluator falsification tests should demonstrate that tampered source/views/reference versions/acks, hidden missing cases or a wrong decision cannot score as a pass. “Every specified deterministic case passes” is a finite test claim, not a proof of universal100% or production reliability. No new numeric joint-success threshold is silently introduced.

## Completion goal and implementation flexibility

The user said “좋아 이대로진행해줘 우리의 목표는 이 모듈의 완성이야 이걸 fabric 을 통해 구현해도 좋고 아니면 따로 pi 를 위한 플러그인으로 만들어도 괜찮을것같아”. Confirmed goal is a usable completed module with evaluated responsibilities, not accumulating test scaffolds. Fabric integration and a Pi plugin are both acceptable implementation mechanisms; do not ask the same mechanism-preference question again merely because both were allowed. Reuse the existing pure-core/Pi-adapter boundaries while completing the approved responsibility/SDK accuracy qualification; Fabric is the current execution/orchestration path, not proof of a separately deployed monitoring daemon. Product/runtime wiring must be reconciled with measured results rather than advertise the local pilot as the full system.

This continues the already approved standard experiment and responsibility rubric. It adds no real-user-data disclosure, automatic live activation, chat/Luna use, business writes or classifier budget beyond144/USD1SDK-estimate/900s-active. Preserve old artifacts and report partial/failing results honestly.

## SDK-source benchmark implementation checkpoint

- Implemented `.lazy-harness/scripts/monitoring-core-sdk-reliability.ts`, `.lazy-harness/fixtures/monitoring-core/sdk-reliability.json`, `.lazy-harness/fixtures/monitoring-core/sdk-reliability-profile.json` and `tests/lazy-harness/monitoring-core-sdk-reliability.test.ts`. Existing core/modules/observer/bridge/trigger/pilot and prior experiment ledgers were not changed.
- New corpus:12 development +60 held-out author-labelled cases, each module's holdout modes20/20/20, no previous case ID/string reuse; four synthetic worlds include explicitly ungranted catalogue references. Gold is not sent to the classifier.
- Pre-inference protection checkpoint:27 PASS/0 FAIL,522 expectations,3.88s; strict typing PASS. One deterministic-oracle test exercises all72 actual SDK source traces. That result is core/evaluator conformance, NOT semantic accuracy. Falsifications of source, full model view, native answer, core propagation, grant/reference version, body digest, source binding, effect/execution/core receipts and hidden/duplicate trials are rejected. Information precision/recall is based on actual received effects, not model-selected IDs alone.
- Separate journal/profile enforces144 HTTP/USD1 SDK estimate/900000ms cumulative active execution, first-pass development stop, code/corpus/profile identity and frozen acceptance. No old budget transfer or implicit reset/replay. At this checkpoint paid classifier HTTP is0; next step is approved development12 with actual Jev, then frozen60×2 only if development passes.
- Independent semantic delta judgement: this is a test/evaluator/profile addition, not a runtime API change, new visible UI, new production ownership/config source or host business fact. The existing SDD/BDD/SSOT/DDD four-row judgement remains; primary evidence is this TDD.

## Actual SDK-source qualification result

Status: accepted-sdk-synthetic under the preset per-module gates, NOT universal/live reliability or completed production integration. Actual summary: `.lazy-harness/evidence/monitoring-core/sdk-accuracy-standard/ledger.json.summary.json`; full source/views/native model answers/core propagation/target material/effect/receipt ledger is its sibling `ledger.json`. The previous experiment artifacts are unchanged.

Development12 first round passed all gates: both module modes12/12, delivered information4/4, joint12/12, no invariant issues. Development stopped immediately; no second round was used. New acceptance60×2 completed under the identical frozen code `479160db0e8c10bfb6feee280f23967aad77931b517517e228146f7c0d8cc8ca` and corpus digest `c78b9b00920c69c88fb7e0ab0bc0dbc71a41f8c9da6bb9d3c5a698413b44f5b9`. No prompt/source/label/corpus tuning after seeing acceptance results.

| Metric | Round1 | Round2 |
|---|---:|---:|
| Knowledge mode accuracy |57/60 (95%)|57/60 (95%)|
| Knowledge run precision / recall |18/18 (100%) /18/20 (90%)|18/18 (100%) /18/20 (90%)|
| Knowledge defer recall |19/20 (95%)|19/20 (95%)|
| Knowledge unwanted run |0/40|0/40|
| References mode accuracy |57/60 (95%)|58/60 (96.67%)|
| References run precision / recall |19/20 (95%) /19/20 (95%)|19/20 (95%) /19/20 (95%)|
| References defer recall |19/20 (95%)|19/20 (95%)|
| References unwanted run |1/40 (2.5%)|1/40 (2.5%)|
| Expected-run exact received/read source set |19/20 (95%)|19/20 (95%)|
| Actually received information precision / recall |24/25 (96%) /24/25 (96%)|24/25 (96%) /24/25 (96%)|
| Direct joint source→mode→material→effect case success |54/60 (90%)|55/60 (91.67%)|
| Source/view/grant/body/version/receipt/effect invariant violations |0|0|

Knowledge run F1=94.74%; references run F1=95%; information F1=96% each round. Agreement: knowledge60/60 (100%), references59/60 (98.33%). All planned cases are present and operational; no timeout/malformed/missing result was dropped or counted as correct uncertainty. The joint metric is direct case scoring, not a product of independent percentages, and had no silently added numeric gate.

### Preserved failures and Contested gold boundary

- Both rounds: h06 knowledge skipped a firm UI-rule decision embedded with an evidence request; h20 knowledge skipped a confirmed same-day staffing-order statement; h25 references deferred an available handover-source request; h57 references ran an underspecified lookup and returned an extra cargo.access source; h58 knowledge skipped an unspecified/pending UI-rule change. Round1 additionally deferred the explicitly non-lookup h13. These are observed mode/reference mismatches under the frozen authored gold, not source corruption or permission bypass.
- Contested/needs-adjudication: h20 is a same-day staffing decision, while the knowledge module's declared run criterion says enduring project decisions/rules/processes. Its expected-run gold may be outside that module's intended scope. Keep the original label, error and reported denominator unchanged; do NOT relabel this held-out case to claim a better score. A later gold revision/independent qualification must record the reason and preserve this baseline.
- No claim that the classifier's internal reason is known: typed answers expose modes/probabilities, not a verified explanation of model cognition. Source wording and declared contracts support an error-pattern review, not invented model thoughts.

Total NEW experiment:12 development +120 acceptance =132 actual classifier HTTP of144; SDK estimated USD0.015068634 ofUSD1; cumulative active execution68136.031ms of900000ms; errors=[]; actual chat/Luna requests0 and real-user data0. Remaining12 requests are not consumed just because they exist. Cost is an SDK estimate, not invoice verification. Repeated60-case rounds are stability checks, not120 independent samples; author gold is not independent human adjudication.

### Completion boundary

The tested core/adapter/target contracts hold in the authored set, while semantic misses/false runs leave joint success90–91.67%. That is a concrete new SDK-chain result, not grounds to assert an always-correct hidden layer. A usable product surface must compose the same core and declared source/judge/module/target ports; the separate local-only pilot is not that surface. Fabric may orchestrate it and a Pi adapter may expose it, without duplicating the core. Remaining semantic/gold-scope issues and actual-data activation are not silently resolved by packaging.

Checkpoint after the coherent source/record/map batch: fast PASS (checked2636 files, errors0, warnings0), record-lint201/201 clean (issues0); focused27 PASS/0 FAIL/522 expectations/3.88s and strict typing PASS. Confirmed16 new graph/cache edges were added without rewriting existing rows. Final standard900 completed successfully: fresh framework91, skipped0, jobs4, errors[], total426.226s (full self-test402.648s), evidenceReused=false. Condensed actual receipt: `.lazy-harness/evidence/monitoring-core/sdk-accuracy-standard/standard.json`; original bounded runtime log `/tmp/pi-fabric-shell-dnd5Ra/output.log`. Evidence-only closure was deferred by the synthetic-turn guard and completed on the user's next armed continuation; it did not rerun validation or grant new execution authority. No further classifier calls or holdout tuning occurred; product integration and residual semantic/gold-boundary work are not marked complete.

## Explicit Pi module assembly protection checkpoint

Primary API contract: `.lazy-harness/spec/platform/pi-monitoring-observation.md`, “Explicit Pi module assembly API”. New factory source `packages/lazy-harness-pi/extensions/lazy-harness/monitoring-module.ts` composes the existing core/observer/bridge through explicit host ports; source-checkout composition is `packages/lazy-harness-pi/examples/monitoring-core/module.ts`; protection is `packages/lazy-harness-pi/tests/monitoring-module.test.ts`. The shared entrypoint/manifest and all frozen benchmark source/questions/corpus/ledgers remain unchanged.

Factory protection covers16 distinct cases across initial and targeted runs, not one claimed full-file16 run. Initial12 PASS +1 failure was a test receiver recordId exceeding the existing200-character acknowledgement bound, correctly rejected as unverified; only the fixture ID was corrected. Correction/new loader3 PASS/0 FAIL/28 assertions/0.775s (11 unchanged tests filtered); source-host entry3 PASS/0 FAIL/28 assertions/0.772s (12 filtered). Final hardening closes a reserved-callback→dispatch microtask race: running state/AbortSignal and receiver source lease are rechecked before invoking any host port. The targeted new race/raw judge+processor+receiver drain/actual SDK+file-loader run passed6/6,47 assertions,0.909s with10 unchanged cases filtered. Final strict PASS on helper/example/test. Bounded receipt: `.lazy-harness/evidence/monitoring-core/pi-module-factory-report.json`. Earlier source/grant/catalogue/unsubscribe/scope-stop protections remain; existing raw work is retained until actual settlement and late results are rejected. Three run/skip/defer native classifier-input comparisons match the earlier evaluator after independently tested provenance/timestamp normalization. These are component/parity tests, NOT a new model-quality score; new paid HTTP0, real-user data0. Earlier frozen baseline/failures/Contested label remain unchanged.

| Layer | Independent delta in this assembly work |
|---|---|
| SDD | yes: explicit module registration/start permission, one-lifetime lifecycle, host bridge/judge/receiver ports and physical-drain API; recorded in the existing observation SDD |
| BDD | no independent delta: no new user command/UI or real pilot activation; P5 narrow profile remains separate |
| SSOT | no independent delta: no env/manifest/model binding/production ownership change; permissions are component API declarations, not project operating rules |
| DDD | no independent delta: existing module/decision/reference meanings retained; Contested gold and prior semantic failures are not relabelled |

New assembly final standard completed: fresh framework91, skipped0, errors[], 434.654s, evidenceReused=false. Primary API/validation capsule: `.lazy-harness/spec/platform/pi-monitoring-observation.md`; actual condensed receipt `.lazy-harness/evidence/monitoring-core/pi-module-factory-standard.json`. Source/typed-host composition and16 protected cases are qualified within the declared synthetic scope. This does not reopen the closed132-request experiment, change semantic labels/scores, consume unused slots or activate real data.


## Public SDK and generic consumer conformance — primary proof

Confirmed scope: user selected public SDK + single configuration schema/validator + generic conformance, then explicitly chose Fabric-independent baseline/optional integration (ADR0061). New paid inference, real-user collection, automatic start/discovery, publishing/installing dependencies and a new Fabric connector remain excluded. Canonical core/observer/bridge implementations and the closed semantic corpus/questions/132-request ledger are not changed.

Qualified new cases: **177 distinct** across bounded focused runs:6 SDK/protocol/config probes,64 fixed independent-oracle cases,100 fixed-seed bounded schedules,6 actual SDK1.3.0 faux scenarios and1 isolated public consumer/runtime/typecheck. Existing Pi factory regression16 also passed after portable type-only imports. The164 generic+schedule run passed575 expectations/2.16s; the6 actual SDK scenarios passed61 expectations/0.864s. Strict public SDK/consumer/old factory/example API check passed. These are deterministic API/data/lifecycle proofs, not new semantic accuracy or independent third-party authorship. Final schema/example/protocol parity extension passed1 targeted/5 expectations/1.55s; declared artifact --check passed. Single fast checkpoint passed checked2665 of2667 changed files, errors0; canonical record-lint203/203 clean, issues0. The first final standard failed after430.413s/exit1 (no evidence reuse): doctor smoke/C17-negative/package-health subprocesses failed. An armed continuation isolated the only doctor FAIL to D03F: adding ADR0061 had not synchronized the internal README ADR count and handoff count/range. D08 existing Unicode warnings are not failures and are out of scope. The two count lines are mechanically synchronized; the affected original doctor3 checks now pass in48.486s. Corrected final standard remains pending.

User-confirmed TDD cross-verify association: Q-a18a9bfbfe1dab6d selected **B, existing verification**, applied in the same turn by `interview-loop --mode answer --answer B --apply` as decision `D-2026-10-28-073a3f10`; queue status is answered. Source `packages/lazy-harness-pi/scripts/generate-monitoring-contracts.ts` is directly protected by `packages/lazy-harness-pi/tests/monitoring-sdk-contracts.test.ts`. Command: `bun test packages/lazy-harness-pi/tests/monitoring-sdk-contracts.test.ts -t "derived public protocol"`; observed1 PASS/0 FAIL/5 expectations/1.55s, verifying canonical AST output, JSON schema artifact equality and schema-valid example. The name/location-based candidate matcher did not find this test; that matcher is not changed or falsely reported as passed. This is an explicit tested association, not skip/defer and not permission for unrelated implementation. Required final standard first failed on stale ADR-count documentation; corrected final validation remains pending, not silently passed.

Four public-only consumer implementations exercise: module-owned progress state; structured tool failure notice; judged test suggestion with a full checked code read; judged code/doc revision consistency with two checked references. Only the test host imports the canonical engine. The independent expectation contract verifies input sequence, module-scoped view/body, successful read identity/version/content, allowed actions/evidence, matching host/core receipts, actual observed proposal-recording effects and bounded physical work. Twelve falsification cases corrupt/miss these traces and must fail. Unsupported and physically pending outcomes are explicitly not functional success. Controlled receivers record proposal projections, not production business acceptance.

Schedules seed1–100 preserve authored valid source admission order while varying raw stage/receipt completion timing and injecting exact replays, conflicting IDs and stale source events. Expectations are authored from planned events, not copied from worker outputs. This does not establish global per-module serialization, OS/process stress, arbitrary business logic correctness or forced cancellation. Modules own internal state/ordering/effects.

Observed defects correctly found and closed: JSON-cloning a native TypeBox settings schema dropped non-enumerable kind metadata, omitted a default and produced a non-JSON worker payload; fixed with native `Value.Clone`, not a weakened core/oracle. The first new SDK fixture assumed core state stopped for a Pi component; actual Pi initial state is idle. Only the fixture/docs were corrected; baseline runtime behavior was retained. Readonly Bun table/readReference annotations were mechanical typing fixes. All failed affected probes were rerun green without repeating unchanged broad suites.

| Layer | Independent delta for this SDK work |
|---|---|
| SDD | yes: public imports/configuration/host factory/binding/conformance APIs; existing monitoring SDD updated |
| BDD | no independent delta: default-off/manual permission semantics unchanged; no command/UI/live collection enabled |
| SSOT | yes: configuration v1 native schema authority, generated artifact/default/bounds/version ownership; dedicated monitoring configuration SSOT |
| DDD | no independent delta: no production domain rule/model; four synthetic consumer functions do not redefine business acceptance |

### SDK Implementation map

- `packages/lazy-harness-pi/monitoring/README.md`: public field/default/version/import/host dependency/lifecycle/error/oracle definition.
- `packages/lazy-harness-pi/monitoring/schema.ts`, `bindings.ts`, `core.ts`, `pi.ts`, `conformance.ts`, `index.ts`: verified API and independent trace implementation; canonical classes are injected, not cloned.
- `packages/lazy-harness-pi/scripts/generate-monitoring-contracts.ts`: portable protocol and JSON schema build/check.
- `packages/lazy-harness-pi/tests/monitoring-sdk-contracts.test.ts`, `monitoring-sdk-generic.test.ts`, `monitoring-sdk-schedules.test.ts`, `monitoring-sdk-pi.test.ts`, `monitoring-sdk-isolated.test.ts`:177 distinct new proof cases; fixtures are under `tests/fixtures/monitoring-consumers` within the package.
- `.lazy-harness/evidence/monitoring-core/public-sdk-report.json`: condensed actual proof shards, limits and pending final gate.
- `.lazy-harness/ssot/monitoring-configuration.md`, `.lazy-harness/spec/platform/monitoring-core.md`, ADR0061: independent ownership/API/architecture deltas.
- Canonical graph prefix `kg_monitoring_sdk_`; generic generated-index generator remains pending, no manually authored cache truth or legacy migration.

Discovery capture / Rule placement: this existing TDD is the primary proof capsule, with only independent SDD/SSOT contract deltas. No global policy/capability is added. Existing semantic misses/Contested gold and pending graph legacy migration remain unchanged; no unused model allowance is spent.

## Corrected final standard — SDK scope closed

After the actual first-attempt D03F failure, only the internal README/handoff ADR count/range was synchronized to61/0001~0061. Existing doctor smoke, C17-negative and package-health protections passed3/3 in48.486s. The necessary corrected final standard then **passed** in428.417 seconds, evidenceReused=false. Actual bounded report: `.lazy-harness/evidence/monitoring-core/public-sdk-standard.json`; one primary summary capsule: `.lazy-harness/evidence/monitoring-core/public-sdk-report.json`. The first failure/root cause remain preserved, not overwritten as a first-pass success.

The selected source-local SDK/configuration/generic conformance boundary is complete:177 distinct new cases and16 prior factory regressions, strict public API/isolated consumer, actual SDK synthetic6, protocol/schema/example parity and current record checks qualified. This closes earlier pending-standard checkpoint wording in this section. It does not publish a package, ship another engine or a Fabric connector, activate real data, alter prior semantic scores/Contested gold, consume new paid model requests or claim business-state acceptance. Generic implementation-index generation remains separately pending per its SSOT; existing graph legacy migration is not performed.

## Configurable model profiles — free implementation proof

User native approval: model configuration/profile schema, classifier/structured-JSON adapters, default/module routing, optional explicit worker port, public usage and free/faux verification. Actual paid provider/model evaluation, real-user data, dependency installation and automatic fallback are excluded. A later>=95% semantic qualification remains separately pending model selection/budget approval. The completed core/SDK and old frozen Jev profile/questions/gold/scores/132-request ledger are not retuned by this implementation.

Focused proof: **91 distinct NEW cases** across bounded initial/targeted/new-boundary runs (not a claimed single91-case invocation):25 model-schema,6 additional schema/reservation boundaries,22 adapter/input cases,22 runtime/routing/worker/physical-ownership cases,7 shared JSON cases,5 actual SDK1.3.0 faux scenarios and4 public core-composition cases. Existing SDK contract6 and isolated public consumer1 also pass with the new models import/runtime/types; they are not counted as new. Strict model/public SDK/tests/host-composition typing passed. Initial malformed model-output diagnostics were incorrectly categorized MODEL_JSON; corrected to MODEL_OUTPUT and the failed case rerun green. Native dynamic-key and Reference callback type annotations/import narrowing corrected strict errors; the affected isolated proof now passes. No score/contract weakened.

Actual SDK controlled native/JSON/mixed routes preserve raw source identity/order, granted reference/body/material receipts, visibly missing failed-adapter decisions and default-off construction. Network is blocked; backend drivers are scripted and fake provider content is synthetic, not semantic inference. Isolated consumer copies only SDK/TypeBox/platform files, excludes Fabric/Pi SDK/private source tree and invokes an injected canonical host core plus controlled model drivers. These are adapter/configuration contracts, not proof that every provider/model is supported or that a real model reaches95%.

The model runtime preserves physical outer-core ownership: ignored AbortSignal does not release the raw model stage or let core physical slots appear idle; late outputs are discarded after actual settlement. Queue/call/token/cost limits and profile/route fingerprints are independently probed, including invalid estimates, decimal-cost ceilings, same-input settings/routing changes, exact worker output schema, scope/version/reference mismatches, unknown backends/versions/parameters and unsupported reasoning. Diagnostics count total failures while retaining only32 structural tail entries. Host calls are not equated with actual provider HTTP/token/billing usage; metered semantic evaluation must still audit real requests.

| Layer | Independent delta in configurable models |
|---|---|
| SDD | yes: separate model profiles, adapter normalization, routing/worker/status/lifetime API; existing monitoring SDD updated |
| BDD | no independent delta: no new command/UI, collection or automatic model execution; explicit opt-in remains |
| SSOT | yes: single model configuration schema/default/artifact and host capability/secret/ceiling ownership; existing monitoring configuration SSOT updated after user gate B |
| DDD | no independent delta: Monitoring is the existing SDK component context, not a new business domain; long-lived knowledge requirement unchanged |

### Model profile Implementation map

- `packages/lazy-harness-pi/monitoring/model-schema.ts` → `tests/model-schema.test.ts`, `tests/model-schema.contract.test.ts` within the package: versioned authority/admission/default/fingerprint/resource boundaries.
- `packages/lazy-harness-pi/monitoring/model-adapters.ts` → `tests/model-adapters.test.ts`: exact task/native/JSON decision/evidence protocol and malformed/missing-result rejection.
- `packages/lazy-harness-pi/monitoring/models.ts` → `tests/models.test.ts`, `tests/models-sdk.test.ts`: routing/typed workers/reservations/physical resource ownership/real SDK synthetic integration.
- `packages/lazy-harness-pi/monitoring/schema.ts` → `tests/schema.test.ts`, existing SDK contracts: one shared plain-JSON safety boundary and unchanged v1 defaults.
- `packages/lazy-harness-pi/examples/monitoring-core/configured-models.ts` → co-located test: identical stopped canonical engine, exact independent output, duplicate/misselected binding refusal and setup cleanup.
- `packages/lazy-harness-pi/tests/monitoring-sdk-isolated.test.ts`, `monitoring-sdk-contracts.test.ts`: no-Fabric/private-import model runtime/type closure and derived schema artifact parity.
- `.lazy-harness/evidence/monitoring-core/model-profiles-report.json`: single proof capsule. Canonical graph prefix `kg_monitoring_models_`, derived generic indexer still separately pending. SSOT registration gate B confirmed existing ownership; no queued IDs existed, no queue answer or direct registry edit fabricated.

Current state: focused proof complete; single fast checkpoint passed (2684 files,2682 checked), record-lint203/203 clean/0issues, and declared protocol/config/model-schema artifact check passed; final standard PASSED in433.493s (fresh fullRegression=true, evidenceReused=false). Actual receipt: `.lazy-harness/evidence/monitoring-core/model-profiles-standard.json`. This approved free model-configuration slice is complete. No actual model accuracy claim/paid calls/real data/installation/publication from this slice. Discovery capture / Rule placement: existing TDD is primary proof with independent SDD/SSOT API/authority deltas only, not new operating rules.

## Quality-v2 actual paid development — failed, correctly stopped

The user explicitly approved paid measurement for the immediately preceding recommended single exact model: openrouter/typesafe/jev-1.14/typesafe-system-one, NEW separate144 actual classifier HTTP/USD1 SDK-estimate/900s active; development12 at most2 stopping at first pass, then fresh60×2 unchanged only after development passes. Existing baseline, old processor questions/gold/scores/ledgers remain untouched. Real-user data/Chat/Luna requests0.

A separate semantic candidate uses existing processor handlers and tightens enduring-vs-one-off knowledge, independent decision/lookup judgement and current scoped evidence selection. The NEW quality-v2 corpus has12 development and60 fresh acceptance cases, five acceptance domain worlds with shared12 scenario structures, authored gold/partitions fixed before inference. Corpus IDs/texts are disjoint from both old corpora; gold is not sent to the model. This is author-labelled synthetic qualification, not independent human adjudication or general production coverage. No acceptance model answers have been collected or used for tuning.

Independent preflight reuses the original SDK raw-source/view/read/material/effect auditor and scorer plus the new public native model router. Actual SDK72 scripted traces passed exact integrity with network blocked; source/effect tampering fails scoring, missing cases cannot disappear and phase guards prevent paid reruns. Existing200-character question bounds initially rejected an overlong new candidate before any paid request; candidate text was shortened, the core guard was not weakened. Strict typing passed; all11 distinct evaluator/guard tests are green across original+affected shards, not a single claimed11-case run.

| Actual development result | Round1 | Round2 (criterion-only revision) |
|---|---:|---:|
| Knowledge mode accuracy |11/12 (91.67%)|12/12 (100%)|
| Knowledge run/defer recall |100%/75%|100%/100%|
| References mode accuracy |10/12 (83.33%)|11/12 (91.67%)|
| References run recall / exact received set |50%/50%|75%/75%|
| Actual information precision/recall |100%/60%|100%/80%|
| Direct joint success |9/12 (75%)|11/12 (91.67%)|
| Hard integrity violations / technical missing |0/0|0/0|

Round1 missed supported record-reading q2-dev-robotmuseum-05, supported immediate lookup amid a pending change -09, and pending enduring procedure addition -12. The separate final candidate makes read/explain requests and pending-process changes explicit and returns to the earlier English lookup criteria; Round2 fixes -05/-12, but -09 still returns retrieval skip instead of run. Its text says the entrance-guidance simplification is undecided but the existing entrance-confirmation standard is needed now. The requested available robotmuseum.rule material is therefore not delivered. This is a semantic missed run, not corrupted/unauthorized data or fabricated receipts; classifier internals/reasons are not claimed.

**Development limit2 exhausted without a pass. No acceptance60×2, no third dev round, no score/gold edits.** Although there are120 requests below the144 ceiling, those were reserved for acceptance after a passing development; unused capacity does not authorize an extra development round. Total actual24 classifier HTTP, SDK estimated USD0.002894304, active11959.576017ms. No billed-price claim. Round2 code fingerprint is preserved in the actual summary; frozenCode remains null because development did not pass. The overall>=95% quality goal is NOT complete.

| Layer | Independent delta for this experiment |
|---|---|
| SDD | no independent public API delta: separate candidate/evaluator reuses existing processor/router/source/material contracts; no production default replaced |
| BDD | no independent delta: synthetic SDK-only, no real session activation/UI/command flow change |
| SSOT | no independent production-config delta: user-approved experiment-only profile/ledger is separate from model config and old experiments |
| DDD | no independent delta: previously confirmed lasting-rule scope retained; old disputed temporary-fact gold/denominator unchanged |

### Quality-v2 Implementation map

- `.lazy-harness/scripts/monitoring-quality-candidate.ts`: versioned qualityProcessors factory, original handlers with separate bounded questions; not automatically activated.
- `.lazy-harness/scripts/monitoring-quality-runner.ts`: loadQualitySuite/qualityFingerprint/qualityScore/qualityPhaseGuard/probeQuality/runQuality; actual SDK→public model router→same core→observed test effects, old independent auditor, new>=95% joint gate and bounded exclusive journal.
- `.lazy-harness/fixtures/monitoring-core/quality-v2.json`, `quality-v2-profile.json`: frozen new synthetic gold and exact approved profile. No old fixture rewritten.
- `tests/lazy-harness/monitoring-quality-candidate.test.ts`:11 distinct shape/disjointness/field-bound/phase/missing/falsification/actualSDK72 protections across shards.
- `.lazy-harness/evidence/monitoring-core/quality-v2/ledger.json`: actual request/response/native-source/view/material/effect/receipt journal and reservations; sibling `ledger.json.summary.json`: actual two failed development rounds, denominators and consumed budget. Old ledgers retained.
- Canonical graph prefix kg_monitoring_quality_v2_; generic implementation index generation remains separately pending. Co-located monitoring-quality-candidate.test.ts and monitoring-quality-runner.test.ts entries delegate to the same real independent tests (routing probe passed); no duplicate cases are counted. Fast checkpoint checked2690 files and record-lint203/203 clean. Final mechanical standard pending; it cannot turn this semantic failure into a quality pass.

Discovery capture / Rule placement: this existing TDD is primary for the paid experiment evidence; the existing Planning records approval/progress/blocker only. No new operating policy, core bypass, model fallback or private runtime note is introduced. User choice is needed for further development/model changes beyond the approved two rounds.

### Quality-v2 mechanical closure (not semantic acceptance)

Final standard passed in462.76 seconds, evidenceReused=false; actual receipt `.lazy-harness/evidence/monitoring-core/quality-v2/standard.json`. This closes the preceding pending-mechanical checkpoint only. The source/evaluator/phase/meters are mechanically protected, while the actual semantic goal remains FAILED at development2 (11/12 joint; retrieval run recall3/4). No acceptance run or extra paid call is authorized by a green framework regression. Keep task79 incomplete/blocked by the next bounded user scope choice. The actual24-request journal/summary and both failed development scores remain unchanged.

## Quality-v2 approved extension — development passed, frozen acceptance FAILED

Native follow-up user instruction “추가로 진행해 얼른” approved the immediately recommended at most2 additional dev12 rounds: total4, cumulative max168 actual HTTP INCLUDING prior24, SDK-estimated USD1 and900s active unchanged. The original quality-v2 profile/journal/summary remain untouched. The extension uses a new profile and separate `quality-v2-extension/ledger.json`, seeded with every prior run/trace,24requests, cost and11959.576017ms. Seed validates old identity/profile, two complete failed rounds and exact24HTTP; source object digest/prior consumption are recorded under extendedFrom. Eight new deterministic extension/anti-reset/identity/repeat/limit guards plus strict typing passed. The old profile still enforces max2; only the explicitly selected extension admits4.

Additional development3 fixed the prior missed lookup but over-executed unresolved/unsupported lookups: joint10/12, knowledge12/12, references10/12 with2false runs. The last allowed candidate explicitly requires BOTH resolved target and directly supporting visible source while treating a current need separately from a postponed rule change. Development4 then passed12/12 for both modules, exact information P/R1, joint12/12 and no hard violations. Development stopped immediately and candidate code2a5919c81393ff560fb867b2467cbc8fcf3a444774315c179d465dc24e5e5594 was frozen before acceptance. The pre-authored corpus/hash/labels were not altered.

### Actual frozen60-case result (round1 only)

| Metric | Observed |
|---|---:|
| Direct joint source→mode→material→effect |54/60 (90%), FAIL against>=95% |
| Knowledge mode accuracy / run recall / defer recall |95% /100% /85%, FAIL defer>=90% |
| Knowledge unwanted run |1/40 (2.5%) |
| References mode accuracy / run recall / defer recall |95% /95% /100% |
| References unwanted run / exact received-read source set |0/40 /19/20 (95%) |
| Actually delivered information precision/recall |24/24 (100%) /24/25 (96%) |
| Operational cases / hard integrity violations |60/60 /0 |
| Cross-round stability |not measured: second acceptance round correctly not executed |

Failures preserved: pool-07 and musicroom-07 temporary operational facts caused retrieval defer instead of skip; observatory-09 and musicroom-09 pending rule changes caused knowledge skip instead of defer; cycle-09 pending rule change caused knowledge run instead of defer; musicroom-05 missed a supported usage-log lookup (defer instead of run). Exactly one requested source was missed, no extra reference body was delivered, but2uncertainty misclassifications plus3knowledge errors leave joint90%. These are observed mode/material mismatches; no verified private model explanation is asserted. Existing gold is not revised to improve the score.

**First frozen acceptance failed: stop, no second60 round or unchanged-input reroll, no tuning this holdout.** Cumulative quality-v2 experiment usage108 actual classifier HTTP = original24 + extension84 (additionaldev24 + acceptance60), SDK-estimated USD0.012588828, active56987.518803ms. Do not add the old24 again or mix in the separate earlier132-request benchmark. Of168 ceiling, remaining60 is not authority to rerun a failed holdout. No actual-user data/Chat/Luna. Joint>=95% remains incomplete, task79 stays blocked rather than marked complete; development12/12 is not an unseen-data success claim.

Proof: `.lazy-harness/evidence/monitoring-core/quality-v2-extension/ledger.json.summary.json` and sibling full journal; frozen source/suite/profile fingerprints and extendedFrom provenance are retained. Original quality-v2/ledger.json still records24requests and the first2failed dev rounds. Five fresh synthetic domain worlds share scenario structures, gold is author-labelled/model-withheld, not independently adjudicated; do not compare new90% directly to the old different-corpus90–91.67% as a controlled improvement. No claim that every configurable model is qualified.

Implementation map delta: `monitoring-quality-runner.ts#seedQualityExtension` and extension profile implement explicit anti-reset cumulative accounting; `monitoring-quality-runner.extension.test.ts` adds8 meaningful guards; current candidate only changes scoped semantic criteria and retains original handlers/core/receipts. Existing SDD/BDD/SSOT/DDD matrix above remains no independent production delta; this is experiment-only extension with no new global operating rule or default activation. Mechanical final standard PASSED in452.267s (evidenceReused=false), actual receipt `.lazy-harness/evidence/monitoring-core/quality-v2-extension/standard.json`; it cannot turn semantic acceptance into a pass.

## Fixed-candidate actual two-model comparison — both failed development

User explicitly approved the recommended exact paired comparison: CURRENT candidate questions frozen, new model-withhelddev12+holdout60, no tuning after results. Jev1.14 and GPT-6 Luna Decisions both use openrouter/typesafe-system-one classifier API; per-profile132HTTP/USD1SDKestimate/900sactive, new aggregate264/USD2/1800s. Old quality-v2 total108HTTP/USD0.012588828 and all old gold/ledgers remain separate. This approval was not for Chat/Luna worker execution or automatic model substitution.

Before paid inference, fresh exact IDs/texts/reference bodies were validated disjoint from all three prior corpora. The new60 acceptance cases have balanced modes, five domains sharing12 scenario structures and separate12 development cases. Candidate text was not edited. A single manifest freezes suite/profile/candidate-source/question/code hashes; both models attest that same manifest. New runner/model-specific atomic journals, exclusive process locks, permanent start claims, per-model/aggregate bounds and one-development/no-reroll guards prevent budget resets/repeated selection. Shared existing probe gained a backward-compatible explicit provider/model/price argument and records its actual immutable router profile; default remains Jev. Exact SDK metering still owns actual HTTP accounting.

Preflight8 distinct cases passed/0fail/450 assertions/6.53s, including144 controlled actual-SDK trials (72 per declared model identity), no network, identical independent source/view/read/material/effect oracle and tamper rejection. Strict comparison/probe types passed. A declared model's name is not just metadata: actual client resolves its exact registered classifier/API and recorded trial model profile must match; missing/malformed/provider errors cannot count as semantic defer.

### Actual same12 development cases, unchanged questions

| Metric | Jev1.14 | GPT-6 Luna Decisions |
|---|---:|---:|
| Knowledge modes |11/12 (91.67%)|9/12 (75%)|
| Knowledge run recall |3/4 (75%)|4/4 (100%)|
| Knowledge defer recall |4/4 (100%)|1/4 (25%)|
| Retrieval modes / expected read/source set |12/12 /4/4|12/12 /4/4|
| Actual delivered information precision/recall |5/5 /5/5 (100%/100%)|5/5 /5/5 (100%/100%)|
| Direct joint source→mode→material→effect |11/12 (91.67%), FAIL|9/12 (75%), FAIL|
| Hard invariant violations / technical missing |0/0|0/0|
| Actual classifier HTTP |12|12|
| SDK estimated USD |0.001378860|0.002732000|
| Active milliseconds |5871.624903|10533.923075|

Jev missed cmp1-dev-ceramiclab-4: a firm enduring insurance-guidance decision alongside an unsupported current policy lookup; knowledge returned skip instead of run. Luna Decisions skipped pending enduring changes in ceramiclab-9/-11/-12 instead of defer; retrieval decisions and exact material were correct. These are observed label/mode disagreements, not model cognition/reasons. This small12-case result does not establish a universal Jev/Luna ranking; the classifier named Luna Decisions is not the ordinary Luna chat/agent runtime.

Both profiles failed the single authorized development gate. **No60-case acceptance round was executed for either model, no prompt change or repeated same-input call followed.** Comparison-only24 actualHTTP, SDK estimateUSD0.004110860, active16405.547978ms; original quality-v2 total108 is preserved separately, not reset or counted inside the new24. Prior+current quality experiments sum132HTTP/USD0.016699688, but are different corpora/phases, not one accuracy denominator. There is no successful>=95% new profile yet.

The shared source transport/model swap works within the tested contracts; simply swapping these two classifiers with fixed current instructions did not close the knowledge-decision quality gap. Potential next contract-risk to inspect (not a proven model-internal cause): skip's 'No actual project-rule/process change' can overlap pending/no-commitment interpretations. A proposed future design would ask typed semantic primitives (lasting-rule relevance, commitment/pending status, temporary fact) and apply explicit module-owned mode policy, independently checked against gold. That is NOT implemented/approved here and must not become raw-text keyword classification, a core permission bypass, fabricated defer or retroactive gold relaxation.

| Layer | Independent delta |
|---|---|
| SDD | no independent public SDK delta: experiment-only paired runner/probe identity metadata; existing model/source/material contracts reused |
| BDD | no independent delta: no real collection/command/UI/default model activation |
| SSOT | no independent production-config delta: new user-approved experiment profile/manifest/journals only; secrets and real provider accounting remain host-owned |
| DDD | no independent delta: lasting-rule/defer requirements unchanged; no old gold relabelled |

### Paired comparison Implementation map

- `.lazy-harness/scripts/monitoring-model-comparison.ts`: comparisonSuite/comparisonProfile/comparisonIdentity/prepareComparison/comparisonPhaseGuard/runComparison; exact two-profile admission, fixed shared manifest, nonreplayable model journals and actual SDK/native calls via shared probe and existing HTTP meter.
- `.lazy-harness/scripts/monitoring-model-comparison.test.ts`:8 guard/admission/full144-SDK controlled proof cases.
- `.lazy-harness/scripts/monitoring-quality-runner.ts#probeQuality`: optional exact model identity/price injection, recorded immutable profile; canonical core/handlers/questions unchanged.
- `.lazy-harness/fixtures/monitoring-core/model-comparison-v1.json`, `model-comparison-profile.json`: new frozen author-labelled corpus and exact approved bounds/model definitions. Shared structures/author gold are limitations, not independent adjudication.
- `.lazy-harness/evidence/monitoring-core/model-comparison-v1/manifest.json`, `jev.json`, `luna.json` and sibling summaries: actual frozen identity, model inputs/results/trace/material/effect and failure/budget evidence. SDK provenance IDs/timing differ per real session, while semantic case/question/source bodies match.
- Graph prefix kg_monitoring_paired_; generic implementation indexer remains separately pending, not hand-authored as canonical truth. First mechanical standard failed458.930s on C17 duplicate provider/model literals; config-only admission correction and original doctor3 checks now pass83.816s; corrected mechanical standard PASSED in457.092s (evidenceReused=false), actual receipt `.lazy-harness/evidence/monitoring-core/model-comparison-v1/standard-corrected.json`; semantic>=95% goal and overall task remain incomplete.

Discovery capture / Rule placement: this existing TDD is the single proof primary; existing Planning captures only approved comparison/status and the explicitly unapproved next design candidate. No new operating rule, automatic fallback or semantic-score override is added.

### Paired comparison mechanical failure/correction provenance

First final standard failed458.930s: all three doctor wrappers failed because C17 found duplicated selected provider/model literals in the framework comparison source and test. The actual profile selection was explicitly authorized, but model identity must remain opt-in experiment configuration, not duplicated runtime vendor coupling (ADR0013). The checker/allowlist/negative regression was NOT modified; strings were not split/obfuscated to evade it.

Preserve original measured `manifest.json`, both24-request traces/results and source: `runner-measured.ts`, `probe-measured.ts`, `candidate-measured.ts` under the same comparison evidence directory. Hashline copy snapshots retain exact content. A new independent snapshot test reconstructs the ORIGINAL recorded codeHash from those source snapshots plus unchanged dependencies, and verifies current candidateSourceHash/questionHash/suiteHash/profileHash still equal the original manifest. Do not replace its measured codeHash with the post-correction source hash or rerun the models.

Correction: exact selected model/provider/API values remain solely in unchanged `model-comparison-profile.json`; new `model-comparison-profile.approved.sha256` pins its actual already-recorded profile digest. Active source checks generic binding shape and that exact approval digest, then SDK exact resolution checks runtime identities. Thus no other model/API or budget is newly admitted. The first actual-model sources remain reproducible in snapshots; completed comparison cannot be resumed with changed code. New proof2 PASS/0FAIL/13assert/0.182s (one updated admission test plus one new snapshot test), strict comparison typing PASS, original doctor smoke/C17-negative/package-health3 PASS83.816s. Total distinct comparison tests9 including earlier144 controlled actual-SDK trials; passing old tests/model calls were not repeated. The first failed standard receipt remains `standard.json`; corrected final receipt will be separate `standard-corrected.json`. This is a mechanical/source-ownership repair, not a semantic score/gold/question change or false-positive suppression.

## A-stage module audit and qualification contract — additive source seam approved

The user approved stage-by-stage goals/review, then explicitly confirmed the recommended separate A implementation with “좋아 그러면 추천대로 가보자 우선은”. This closes the previously unanswered/cancelled source choice: add the independent realtime lifetime/tap/mailbox while preserving existing observer/core/bridge contracts. Approval covers this A source/test/record batch with isolated SDK/faux and zero external inference/real-user data/live activation; it does not authorize B/C/D or real OAuth/model execution. Existing audit findings are source inspection, not fresh validation results.

| Existing module/seam | Source-backed audit finding | A-stage treatment |
|---|---|---|
| PiMonitoringObserver | Already registers streaming/context/lifecycle hooks; diagnostic work intentionally depends on its epoch and whole canonical snapshot | Preserve this public behavior and tests; do not weaken invalidation globally |
| MonitoringObservationBridge | consumes only agent_settled and scans finalized message_end windows | Keep this qualified settled baseline; add an independent immediate watch path rather than calling old baseline live-ready |
| MonitoringCore/receivers | Existing per-module scope/grants/duplicate/currentness and proposal/material receipt protections | Reuse later; do not equate A's prepared mailbox with a business effect or bypass core guards |
| Pi SDK fixture | Actual isolated AgentSession with native faux provider/tools, empty credential store, network-disabled model registry and blocked fetch acceptance | Reuse for explicit actual-SDK evidence; a missing/skipped SDK is not an A qualification pass |
| model router/worker | Explicit judge/structured-output ports, no automatic OAuth tool-using worker | Not changed in A; actual models, auth and worker semantics belong to later stages |

### Approved additive A source batch and rollback boundary

Implemented the approved seam in `.lazy-harness/scripts/monitoring-core-realtime.ts` and `tests/lazy-harness/monitoring-core-realtime.test.ts`; the new source-only controller/tap is now present and focused-qualified, not a future-file placeholder. It owns realtime preparation lifetime/mailbox separately from diagnostic snapshot work. Existing observer/core/bridge/shared entrypoint/SDK exports/auth/CLI/manifest were not modified. It is not auto-loaded, a published standalone engine or the complete B/C/D feature pipeline.

Rollback boundary: stop/detach the new opt-in component and leave the existing qualified path untouched; no shared state migration or file deletion is authorized by this proposal. Record/API additions after implementation are limited to this TDD primary, independently needed Pi component SDD semantics and verified implementation graph links; no graph edge will assert an implementation before it exists.

### Required pass/fail ledger

1. Default off/import-only creates no registrations, model work, timers or writes. Explicit opt-in and one-owner cleanup are observable.
2. Registered eligible user/assistant/tool/stream signals reach the injected async preparation port BEFORE agent_settled, without making a lifecycle/context handler await its result. No static raw-user-text intent/risk classifier is added.
3. Intent epoch and logical main-model step are distinct; ordinary context increments step without killing still-valid watch work. context_with_system is the same logical step, not a second request.
4. Session/binding/branch changes, explicit stop/dispose/abort, changed intent, revoked capability and changed source dependencies cannot release stale work. Advancing a conversation hash alone is not blanket watch-result invalidation; existing diagnostic behavior stays intact.
5. Prepared data retains exact source/job/scope identity; unavailable/malformed inputs and source-check failures fail closed. A synchronous dependency-version guard is host-owned, not a claim of automatic filesystem monitoring.
6. Queue, jobs, physical concurrency, timers, retained data/trace and mailbox are bounded. Timeout/logical cancellation does not release a raw operation's slot until actual settlement. Duplicate frames cannot repeat jobs or effects; restart cannot reset lifetime budgets.
7. Completion after agent_settled is not automatically cancelled: non-injection preparation can become ready while its own scope/permissions/sources remain valid. Context candidates wait if no next request; no automatic follow-up/steer/abort or cross-epoch cache is added.
8. Ready handoff distinguishes prepared/offered from actual context consumption/business success. The standalone component never silently injects, writes knowledge/tasks or performs external effects.
9. Deterministic disposal/pending reasons include intent/scope/source/permission change, explicit cancel, timeout, unavailable, overflow, malformed work and no-next-context pending. Tests assert exact reasons rather than just a green status.
10. Actual SDK/faux integration proves source order/provenance, early dispatch, ordinary multi-request step crossing, slow-job foreground progress and source/scope supersession. External fetch attempts0; no actual user data, credentials, auth change, real model call or production host activation. Compare observed events and outputs independently; do not report synthetic delay as real Jev latency.

Executed checkpoint: explicit required-SDK A tests plus affected existing observer/settled-bridge/module protections PASS95/0FAIL/641 assertions/2.81s; strict new source/test typing PASS. The installed SDK entry was supplied and4 actual SDK/faux cases executed; no skip is counted as qualification. Actual artifacts are under `.lazy-harness/evidence/monitoring-core/realtime-A/`. Source behavior is frozen after this green checkpoint; one lazy check and final standard follow after record/map closure. Generic standard alone does not replace this module proof.

| Layer | Independent delta judgement |
|---|---|
| SDD | independent additive realtime lifetime/tap/mailbox contract documented in existing pi-monitoring-observation SDD; original diagnostic observer and public SDK contracts remain unchanged |
| BDD | no independent live user/UI delta in this default-off synthetic batch; controlled scenarios are protected here |
| SSOT | no independent model/auth/data-consent/config-schema delta; current purpose-built judge and Pi OAuth Luna worker requirements remain unchanged |
| DDD | no independent business-domain rule delta |

Implementation map (verified additive A + preserved baseline): `.lazy-harness/scripts/monitoring-core-realtime.ts#RealtimeMonitoringCoordinator` owns epoch/step/generation, async preparation, dependency/grant validity and bounded mailbox; `#createPiRealtimeTap` owns explicit event subscriptions and cleanup after the existing observer. `tests/lazy-harness/monitoring-core-realtime.test.ts` protects mechanical/actual-SDK behavior using unchanged `packages/lazy-harness-pi/tests/support/monitoring-sdk-fixture.ts#createSdkFixture`. Existing observer/bridge/module tests remain part of the focused95 checkpoint. Cross-layer contract `.lazy-harness/spec/platform/pi-monitoring-observation.md`; graph prefix kg_monitoring_realtime_a_. The generic generated-index owner is still pending; it is not hand-authored as truth.

Discovery capture / Rule placement: this existing TDD is the one primary for A goals, module audit and eventual reproducible protection evidence (Scope=layer-fact). Planning points here and retains approval history. The user confirmed the staged process; a bounded native choice confirms the additive source seam before editing it.

### A measured evidence capsule — qualified synthetic realtime lifetime seam

New source/tap uses the separate lifetime seam approved by the user; current implementation was read and exported symbols/typechecked/behaviorally probed. Four actual SDK1.3.0/native-faux proofs are recorded in `.lazy-harness/evidence/monitoring-core/realtime-A/sdk-report.json`: streaming tool progress dispatched before agent_settled and remained current after normal completion; tool_result work crossed two request contexts; ready context data was offered exactly once at step2 without changing provider input; actual user steer produced epoch2 and no old ready material. These are controlled behavioral tests, NOT actual judgement/model quality or live data proof.

95 combined new/existing tests passed,0 failed,641 assertions,2.81s; strict source/tests passed. Fast check2720 PASS; standard PASS 468.26s, evidenceReused=false, fullRegression=true, ran=91, skipped=0. Actual network attempts0, model calls0, user-data collection0, main-agent injection0, business effects0, login/host activation0. `.lazy-harness/evidence/monitoring-core/realtime-A/focused.json`, `sdk-report.json`, `standard.json`, `identity.json` preserve actual commands/proofs/receipts and unchanged5-source identities. Task90/A is qualified for the stated synthetic/faux scope only; B/C/D, OAuth worker and live operation are not completed by it.

Limits/remaining stages: preparation is a trusted injected faux port, not Jev/Luna; no per-feature semantic worker/input quality claim. Source freshness/permissions rely on supplied fast host metadata; no filesystem watcher is claimed. Current observer does not copy tool_execution_update.partialResult body, so A proves progress-event/metadata dispatch only. B must qualify useful material and semantic selection; C must use Pi OAuth Luna worker; D must prove final request/target outcomes and performance. Cross-epoch cache, real main-context injection and live collection remain unimplemented/unapproved. Existing prior classifier/gold/ledgers remain unchanged.

Code organization review: new303-line lifetime flow remains local under one coordinator, one thin subscription owner and reused JSON/freeze authorities (COP-01..05). No line-count split, named-architecture inference, host-map change, blocking policy or untouched-source rewrite. Graph uses only current source/export/test facts, leaving legacy rows and derived-index ownership intact.

## B-stage goals and module audit — controlled material/selection qualification

After the A completion report the user said “좋아 진행해줘”, continuing the recorded staged B goal. This batch implements and mechanically qualifies B's data/view/selection/transfer composition with synthetic SDK/faux input only. It does NOT approve a new actual classifier profile/call/token budget, OAuth worker execution, actual-user capture, live injection or business effects. Real model semantic accuracy remains a separate, explicitly budgeted qualification, not a number inferred from scripted tests.

Module audit and implementation boundary:
- A is qualified and frozen. Its coordinator owns intent/step/source/permission/queue/mailbox. Existing observer intentionally omits tool_execution_update.partialResult; do not silently change that diagnostic contract.
- Existing MonitoringCore owns scoped views, grant checks, run/skip/defer validation, checked reference reads and proposal receipts. Reuse it rather than authoring another semantic decision validator or bypassing its action/read guards.
- Existing MonitoringModelRouter owns native question encoding/decoding, admitted profile/role identity, quotas and raw physical ownership. B uses only host-admitted native-classifier judge profiles; a structured-json general worker is not a classifier substitute. No brand whitelist or guessed Microsoft model is added.
- New bounded transient material owner projects explicitly allowed user/assistant/tool/progress text and admitted tool fields before its own copy/hash/buffer. It must never forward full observer snapshots/system prompts or ungranted tool/image/thinking/signature/details fields as default judgement payload.

Proposed additive files: `.lazy-harness/scripts/monitoring-core-realtime-material.ts`, `.lazy-harness/scripts/monitoring-core-realtime-selection.ts`, `tests/lazy-harness/monitoring-core-realtime-selection.test.ts`. The two source owners are distinct (bounded material/version lifecycle vs core/model/selection composition), not a line-count split. Existing A/observer/core/model-router/SDK/shared entrypoint/auth/manifest/pilot source stays unchanged.

### B required acceptance ledger

1. Default off; explicit host data-kind/tool-field/module grants and classifier profile admission. No private real-data/body collection or model call by import/constructor/default registration.
2. Native hook source IDs/session/binding/order and partial/final-hook stages are retained. A separately opted-in material tap may read tool partialResult TEXT only when explicitly admitted, before the A tap dispatches; original observer/frame content stays unchanged. Partial material is labelled, never promoted to persisted/canonical/business truth.
3. Dynamic bounded current-intent sources and explicitly supplied host refs form module views. Whole snapshots/system prompts and non-admitted bodies are not copied into core event payload or model requests; actual content is only in grant-filtered references.
4. Source versions reflect logical content/dependency changes, not ordinary context steps or an identical later copy of the same tool result. Source changes/removal/partial supersession invalidate stale work. Intent/scope reset clears transient material, not a new cross-epoch transcript cache.
5. No silent meaning-based truncation/search/ranking in hooks. Explicit limits/gaps/unavailable source fail closed and remain visible; no fake semantic skip/defer on technical failure. Selection relevance is delegated to the admitted judge through existing native mode/ref questions, not a handwritten keyword algorithm.
6. Each module sees only its granted current/recent sources; missing current material does not fall back to raw frame text or secretly widen grants. Multiple modules can judge in one scoped batch; no assumption of two model calls per event or a universal model-internal compaction pass.
7. Core handlers read only selected actual versioned references and produce exact material with provenance. Unknown/stale refs, malformed/missing model replies, source/permission cancellation and incorrect route/profile reject rather than fabricate a successful packet. Run without usable selected current material cannot qualify an action.
8. Prepared batches preserve module/destination/profile/source identity and exact read/receipt material; skipped/deferred/failed outcomes stay distinguishable. A ready handoff is not main-agent injection or business success. Stop/timeout keeps nested raw model work owned until it settles; request/context storage is explicitly bounded without resetting model budgets per event.
9. Existing A/core/model/observer protections remain qualified. Actual SDK/faux scenarios include assistant/tool/progress material, per-module isolation, context crossing/steer/source change and exact selected-body handoff; fake backend inputs/results and independent expected bodies are compared. Network attempts/actual models/user-data/OAuth/login/live effects0.
10. Focused/strict/fast/final standard receipts and source identity are recorded before completion. Scripted selection proves transport/contract behavior only, not real Jev/Microsoft semantic precision or latency. A separate named model/corpus/budget gate is required for that claim.

| Layer | Independent delta judgement |
|---|---|
| SDD | independent additive material/version/native-selection/packet contract is implemented and documented in the existing Pi observation SDD; original A/observer/Core/model/router/public package contracts remain unchanged |
| BDD | no independent live UI/default activation delta; controlled scenarios belong to this qualification |
| SSOT | no production auth/model selection/data-consent/schema authority change; classifier purpose and Pi OAuth Luna worker constraints remain unchanged |
| DDD | no independent business-domain rule delta |

Implementation map baseline: unchanged `.lazy-harness/scripts/monitoring-core-realtime.ts`, `.lazy-harness/scripts/monitoring-core.ts`, `packages/lazy-harness-pi/monitoring/models.ts`, `model-adapters.ts` and existing native profile/SDK test fixtures. New symbol/edge facts will be stored only after actual source exists and is inspected. Root policy/capability resolve matched code-organization observe-only guidance; no host-map, global enforcement or graph migration is included.

Discovery capture / Rule placement: this existing TDD is B's one proof primary; Planning records the bounded continuation only, SDD gets the independent implemented contract. Existing auth/role SSOT is reused, not duplicated. At this goal checkpoint B source/tests have not been written or run yet.

### B measured evidence capsule — controlled structure qualified; semantic stage still open

Implemented `.lazy-harness/scripts/monitoring-core-realtime-material.ts` and `monitoring-core-realtime-selection.ts`, protected by `tests/lazy-harness/monitoring-core-realtime-selection.test.ts`. Final B checkpoint:26 PASS/0FAIL/110 assertions/1.143s, including4 required actual installed SDK1.3.0/native-faux cases; strict source/tests PASS. At the initial combined checkpoint all95 existing A/observer/settled-bridge/module protections passed. Those unchanged passing checks were not rerun after B-only fixes; the5 baseline source hashes match the qualified A capsule. New source and actual receipts are frozen under `.lazy-harness/evidence/monitoring-core/realtime-B/`.

The first combined attempt failed115PASS/4FAIL (three B cases plus the required-four-proof afterAll) and two strict callback typings. `attempt-1.json` preserves it. Investigation found that admitted user/assistant text and event-meta from one frame shared a logical ID, so metadata overwrote text before grant filtering. Identity now includes material kind; progress supersession uses the same namespace. Original expected bodies were preserved, with explicit namespace and routed-profile failure-isolation regressions. A separate paired host-owned `pipeline.advanceIntent()` resets transient material and advances A without resetting lifetime budgets. No original gold/holdout/old model ledger or shared source was edited.

Actual SDK proofs: admitted tool_execution_update.partialResult text reaches the native question view and exact selected packet while the tool is still running, despite the unchanged observer omitting that body; final tool result invalidates the provisional offer. Assistant final text is selected from non-user hooks without common snapshot/system-prompt leakage or provider-input mutation. Tool-result selection remains valid across2 contexts and an identical final-hook copy. Native steer replaces transient input, holds old raw classifier work until settlement, and yields no stale packet. Mechanical probes independently verify two-module source isolation/selected exact bodies, explicit tool-field projection, per-route native profile identity/failure isolation, skip/defer vs missing technical replies, read/permission/source guards, bounds/default-off and nested timeout ownership. These are scripted native-classifier responses, NOT actual Jev/Microsoft semantic or latency measurements.

Implementation map: `RealtimeMaterialWindow` owns start/capture/advanceIntent/snapshot/setReference/read/sourceVersion/stop/dispose and bounded material versions; `createPiMaterialTap` admits explicitly allowed progress TEXT after the diagnostic observer. `RealtimeSelectionBridge` reuses `MonitoringCore` and `MonitoringModelRouter` for scoped module views, native questions, selected-reference reads and internal proposal receipts. `createRealtimeSelectionPipeline` installs material before A tap, exposes paired advanceIntent and drains/disposes owners. Existing SDK fixture and all baseline sources are reused. Graph IDs `kg_monitoring_realtime_b_*` contain only verified file/export/protection facts; generic derived-index generation remains pending with its existing owner, not hand-authored here. The B4-row layer matrix above applies; independent SDD contract is recorded, BDD/SSOT/DDD have no independent delta.

Limits retained: text-only admitted progress is the latest callback's supplied text, not a reconstructed complete stdout stream; event-hook/final-hook provenance is not persisted/native entry authority. Source guards validate captured dependencies, not a semantic completeness proof for every later unrelated message; no automatic filesystem watcher or hostile-code sandbox is claimed. Host-provided refs are explicit immutable/versioned inputs, not discovered private documents. Use the pipeline's paired advanceIntent for manual task changes, not the low-level A counter alone. The internal recorded proposal means staged material, not delivery/action success. Actual model calls, real-user collection, OAuth/login change, live activation, main injection and business effects remain0; actual judge profile/corpus/call/token/cost qualification is not approved by these tests. Whole B/task91 remains in progress at that gate; C/D have not begun.

Fast check PASS (2731 checked/2733 files); record-lint PASS203/203, issues0. Final actual standard PASS425.774s, fullRegression=true, evidenceReused=false, ran=91, skipped=0, jobs=4, errors[]. Complete actual governor receipt is `.lazy-harness/evidence/monitoring-core/realtime-B/standard.json`; resumed user-turn13-source hash comparison matches the focused snapshot in `post-standard-identity.json`. No frozen behavior/source changed after the green focused/strict checkpoint; tests/validation were not rerun to close receipts. This evidence-only closure qualifies B controlled structure, NOT actual classifier semantics/latency, whole-B/task91 completion, OAuth worker or production activation.

Discovery capture / Rule placement: current implementation/proof/failure/limit facts converge in this existing TDD primary (layer-fact), independent API semantics in the existing Pi observation SDD, and the existing Planning receives only a stage pointer. Existing judge/Luna/auth/data-consent ownership is reused; no operating-policy, migration, cache or new source authority is introduced.

### B actual-Jev pilot — executed once; semantic qualification FAILED

The native questionnaire selected “12사례 실측 (Recommended)”. Approve a NEW12-scenario actual SDK/faux-source -> existing realtime material/native Core -> real openrouter/typesafe/jev-1.14 (typesafe-system-one) -> exact selected-packet pilot for two distinct functions (long-term project-knowledge candidates and task-relevant reference preparation). Build the additive qualifier/corpus/controlled guards, freeze them before the first model request, then execute once. This does not authorize the alternative132-request formal envelope or a whole-B/production quality claim.

New envelope: <=12 actual HTTP attempts, USD0.10 SDK-estimate/reservation ceiling, <=300s active; conservative input reservation <=69632 per request/835584 cumulative,64KiB actual wire payload, <=64 native questions/answers, <=16KiB decoded response. Native classifier answers are not chat generation, so do not pretend a normal LLM maxTokens cap is enforced. Unknown/unpriced/native-output pricing, excessive requests/bytes/questions/time, raw transport failure or hard integrity violation stops; semantic mistakes remain in the denominator without retuning/reroll. Record actual SDK usage/cost (estimate, not invoice), actual views/raw typed decisions/selected-read material/SDK source provenance and failures. No gold/labels in model input, old case/holdout/ledger/budget reuse, automatic retry, source authority substitution or business receipt fabrication.

Implementation boundary: existing qualified A/B/observer/Core/router/SDK fixtures/shared entrypoint/auth/manifest remain frozen. New isolated qualifier may construct controlled SDK sessions/tools through already verified public APIs to provide real custom partial/final synthetic content; do not mutate captured observer frames or claim fabricated events as native. Source fields and model permissions are explicit. Actual-user collection, Luna/chat/OAuth/login change, main injection, business effects and active-host enablement remain0. Unapproved model substitution or131/132-call migration is forbidden. Whole B stays open after this small pilot; C/D remain pending.

| Layer | Independent delta judgement |
|---|---|
| SDD | no independent production component/API delta; qualifier consumes existing SDK/Core/router/material interfaces |
| BDD | no independent live UI/activation delta; isolated qualification scenarios only |
| SSOT | experiment-specific approved profile/ledger only, no production routing/auth/ownership authority change |
| DDD | no independent domain rule delta; previously confirmed long-term knowledge vs transient facts and task-relevant preparation goals are reused |

Implementation map (verified): `.lazy-harness/scripts/monitoring-core-realtime-pilot.ts#PilotBudget/checkPilotRequest` narrows the reused Budget/createMeteredRequest authority; `#runPilotCase` constructs isolated actual SDK source sessions/tools and consumes the unchanged realtime pipeline; `#evaluatePilotCase` independently compares raw native choices/ref probabilities, Core traces and exact staged packets; `#pilotIdentity/preparePilot/runRealPilot` bind the profile/corpus/source/questions, one-shot start claim, aggregate journal and summaries. `tests/lazy-harness/monitoring-core-realtime-pilot.test.ts` protects source/corpus/token/grant/secret/oracle guards. `.lazy-harness/fixtures/monitoring-core/realtime-B-pilot.json` holds the independent12 cases/evaluation-only labels; `realtime-B-pilot-profile.json` plus its approved SHA256 hold experiment identity/caps outside runtime policy. Actual receipts are in `realtime-B-pilot-v1/{manifest,ledger,summary,failure-analysis}.json`; graph prefix kg_monitoring_realtime_b_pilot_. Existing B13 baseline/source and prior gold/ledgers remain untouched. Generic derived-index ownership is unchanged, not hand-written. This existing TDD is the one proof primary; Planning is a concise execution pointer and no independent production SDD/BDD/SSOT/DDD delta is promoted.

### B pilot actual evidence capsule — semantic failure retained, no reroll

The approved actual SDK1.3.0/faux-main-and-tool -> unchanged B/Core/ModelRouter -> REAL fixed Jev native -> selected packet pilot completed12/12 actual HTTP attempts once. Actual result is `pilot-semantic-failed`: case-joint9/12=75%; knowledge.candidate mode+material10/12, references.prepare11/12. Raw mode agreement is22/24 (91.67%) but module mode+material agreement21/24 (87.5%); mode alone therefore overstates usefulness. No missing technical trial, pending work, fabricated skip/defer or hard source/grant/version/receipt violation: operational12/12, integrityIssues[]. This small author-labelled corpus is NOT full B acceptance or a production accuracy estimate.

Actual accounting:12 requests/12 HTTP, SDK estimated USD0.001748838 (not invoice), active6187.75365ms, conservative input reservation147359 <=835584. Native response caps/current source/privacy/gold preflight remained enforced. External real chat/Luna/OAuth/login change, actual-user collection, main injection, live activation and business effects0. Unspent dollar/time allowance is NOT authorization for a13th request. The one-shot started claim and original freeze/ledger remain intact; no model rerun, label rewrite, source/prompt retuning or budget transfer occurred after the first real call. Old failed semantic comparisons and their denominators remain untouched.

Observed mismatches, preserved against the original author expectations:
- b04 assistant final: expected knowledge run, actual skip; the exact lasting/user-approved-decision text IS present in the actual native view. Current-source reference probability0.10. No packet is produced. This is a missed candidate against the declared oracle, not proof of absent source transport.
- b06 assistant final: expected references defer for an underspecified request, actual skip; current-source probability0.15. This is a skip/defer boundary mismatch, not a technical fallback.
- b10 tool final: knowledge mode run is correct but only the storage-policy ref is selected; current actual fact probability0.18 is below the frozen0.5 threshold. B correctly rejects the unusable run with no_selected_current_material; there is no false success or storage. This is an end-to-end evidence-selection failure, not a data-integrity breach. `failure-analysis.json` binds raw views/answers/source IDs and all three cases.

Contested/interpretation review BEFORE any new tuning: the original b04 author assumes an assistant report of a user-approved enduring decision suffices to propose a knowledge candidate; actual approval records are not separately supplied in this pilot. b06 assumes an underspecified request is defer rather than absence-of-request skip. These are author-labelled expectations requiring independent/user adjudication if disputed, not universal truth. Preserve original labels and75% score regardless; do not relabel this run into a pass. Possible current-source/module-purpose/native-reference-question visibility issues are hypotheses, not established root causes. Native reference bool questions receive the visible context goal, not automatically the full module.question; this host explicitly declares the two input purposes in its <=200-character goal. No hidden gold was supplied and no codec/API was modified to improve this result.

Controlled/source validation before real dispatch:7 pure guards passed initially;9 SDK source cases passed before fixing a test-only final-tool gate; affected5 (including tool3 and oracle b01) passed in1.370s; final b01 oracle falsification passed1/0 in0.846s and final strict passed after readonly test-only typing fixes. These cover19 distinct cases across checkpoints, NOT a fictitious single19-pass run. All12 actual-model source trials later independently reconciled actual native SDK events/body/order and checked raw native decision -> selected read -> packet. Initial failures/causes remain in attempt-1/2 and controlled-checkpoints.json. Questions/goal were shortened to the existing Core200-character contract before freeze, not after model feedback. No production Core/B/observer/router/helper source was changed.

Qualification status: actual classifier path/controlled evidence integrity demonstrated; semantic usefulness failed, so whole B/task91 is not complete and C/D are not started. Any next source/question/gold-interpretation change or actual-model experiment requires a new bounded plan/confirmation; these12 can be development/regression evidence only, never rerolled as fresh acceptance. TDD4-row matrix above applies and one primary owns this outcome.

Positive-subset audit (class-capture.json): knowledge required-run3, mode-run2/3 but useful-packet1/3; reference preparation required-run4 and useful-packet4/4. These tiny synthetic class counts expose useful-work recall hidden by aggregate mode scores; they are not population estimates. Original12-case labels and75% denominator remain unchanged.
Mechanical checkpoint: fast PASS2750 checked/2752 files, record-lint PASS203/203/issues0. Final actual standard PASS428.063s, fullRegression=true, evidenceReused=false, ran=91, skipped=0, jobs=4, errors[]. Complete governor receipt is `.lazy-harness/evidence/monitoring-core/realtime-B-pilot-v1/standard.json`; post-standard prepare identity matches original pilot source/profile/questions/corpus and baseline13 (`post-standard-freeze.json`), with no real-model rerun or source change. This evidence-only mechanical closure does NOT change the retained9/12=75% semantic failure, complete task91/whole B, or authorize C/D/new requests.

### Sequential B audit0→1→2 — read-only evidence checkpoint

The user chose B internal sequence and confirmed stage0 forward criteria through native questions. Canonical component meaning is `.lazy-harness/spec/platform/monitoring-core.md#Forward B stage0 criteria`: input-visible original user approval/trusted approved-record evidence is required before knowledge run; approval reports alone defer. Admitted-source explicit but ambiguous reference requests defer; no request skips and clear supported requests run. These apply to a future revision only. Old b04/b10 run labels, all pilot source/questions/corpus and75% score remain unchanged; no counterfactual rescore was produced.

Existing-evidence audit is `.lazy-harness/evidence/monitoring-core/realtime-B-pilot-v1/sequence-audit.json`. No new inference, code/schema change or event/model replay occurred. No blanket Reader/map restart or passing test rerun was needed for this same B work unit.

| Logical stage | Measurement / denominator | Judgement |
|---|---|---|
| 0 purpose/criteria/approval boundary | user-confirmed forward contract | resolved as a specification, NOT implemented/retested |
| 1 native capture/projection | original operational source trials12/12, retained source metadata12/12; user/assistant/progress/tool3 each | reuse prior SDK body/order/identity reconciliation within this synthetic scope; full raw event arrays were not saved for a fresh replay |
| 2a admitted current body | exact current body present in24/24 actual module views; forbidden private/system/gold marker violations0 | body transport/privacy present; semantic completeness not inferred |
| 2b declared purpose | brief common goal names module24/24; decision question contains declared module instruction24/24 | explicit choice-question input is present |
| 2c ref-question local purpose | full module instruction explicitly in each reference question/its task state0/24 | other decision questions carry it in the same RPC; provider-internal cross-question sharing is not assumed |
| 2d current-source association | current reference explicitly contains its origin observation ID0/24 | event ID exists separately, ref IDs are opaque hashes; no first-class link is present in the model ref. Type/kind/body may still permit inference, so absence alone is not a proven error cause |
| 2e approval evidence | b04/b10 views supply approval reports, not the original approving utterance/independent approved-record body | not adequate to certify the NEW knowledge input criterion; old evaluation remains untouched |
| 3–5 future mode/ref/read/packet qualification | historical mode22/24 and B-joint9/12 only | not requalified under the forward criterion; safe rejection vs useful packet availability stay distinct |

Stop at stage2 for a concrete input-contract/representation plan before modifying the frozen path or remeasuring. Required meaning is current-evidence association, each module's relevant purpose/criteria visible to the question, and approval evidence/unknown status; field names, DTO/schema and adapter changes have NOT been selected. Logical measurement separation does not authorize two API calls, a new retrieval algorithm, worker invocation or more paid calls. Per-stage CPU/wait/wall latency remains UNMEASURED: the saved B trace is status-only and one native RPC batches mode/ref questions; total/transport elapsed cannot be split into invented phase times.

Rule placement / layer judgement: this TDD owns evidence/measurement gaps; the independent forward component semantics belong only to the linked SDD, Planning has a concise sequence pointer. No runtime/API implementation, production auth/config/ownership, live UI or lasting-knowledge domain definition changed. Record digest/ref lint is the appropriate read-only record check; no new behavior or full-regression rerun is needed for this requirements/evidence capsule. Future implementation will need its own coherent source validation and actual-model envelope. No new implemented_by graph facts are asserted for unimplemented fields.

### B stage2 controlled input-projection prototype — approved free implementation ledger

After the input-contract draft and explicit free-prototype next-step summary, the user said “좋아 다음 진행해봐”. Approve an isolated source-local projection helper and controlled fixtures around existing Core-filtered JudgeTasks, existing native encoder/decoder and A dependencies/lease; new source/test paths are `.lazy-harness/scripts/monitoring-core-input-projection.ts` and `tests/lazy-harness/monitoring-core-input-projection.test.ts`. The host/evidence-source implementation is synthetic fixture-only. No production proof collector, model client, timer/queue/lifecycle authority, public generated ABI change, package/entrypoint/auth/settings edit, actual SDK session or paid semantic skill-discovery/model call is included. Prior code/corpus/score/12-call ledger stay frozen.

Acceptance ledger: current-vs-background association and source origin/phase; full per-module contract explicit to both native question kinds; only visible-reference metadata copied/hashed; missing/denied/unverified/contradictory approval represented distinctly without source-role upgrades; original user evidence may overlap current; model output cannot manufacture approval; module-local required-evidence rejection preserves raw mode; exact input/ref/native output mapping and Core checked-read/receipt authority reused; malformed metadata/oversize/native-missing are technical failures; one module's metadata failure does not erase another's result; initial host evidence/catalog dependencies actually drive existing A stale/offer guards, while ordinary context/equivalent copies do not invalidate unchanged semantic snapshots. Scripted native envelopes establish protocol, not Jev accuracy or causal explanation for the old75%.

Per-stage measurements will report fixture counts, accepted/rejected task counts, current/contract visibility, required-evidence/packet availability vs conditional fidelity, and actual lifecycle guards. No invented per-question timing for one RPC. Keep the cheapest coherent-batch focused/strict checkpoint and one final standard after source/records/graph completion. Existing old passing behavior is not rerun unless a dependency truly changes.

| Layer | Independent delta judgement |
|---|---|
| SDD | experimental model-facing projection/owner/dependency/guard contract is this implementation's independent delta in existing Monitoring Core SDD |
| BDD | no independent live UI/activation delta; mechanical synthetic fixtures only |
| SSOT | no production model/auth/config/source ownership delta; registered host metadata/revisions remain trusted boundaries |
| DDD | no independent lasting-knowledge domain delta; already-confirmed stage0 eligibility is reused |

#### Implementation map — verified controlled prototype and evidence capsule

- Primary source: `.lazy-harness/scripts/monitoring-core-input-projection.ts`; directly read `buildInputProjection` and `InputProjectionError`. It only owns a bounded after-Core-filter metadata projection plus module required-input guard. No Core/A/codec/queue/timeout/read/receipt implementation was copied, and no public package export/schema/registration/config was added.
- Protection: `tests/lazy-harness/monitoring-core-input-projection.test.ts` —26 distinct controlled cases: initial25 PASS/0FAIL/112expect/308ms, then an additional independent-receiver case1PASS/25filtered/8expect/202ms, without rerunning the unchanged25. Initial strict found descriptor narrowing TS18048; a return-never-only correction and the final added test both passed current strict. Source behavior25PASS was not rerun merely for the typing correction. Coherent-batch fast2759checked PASS and record-lint203clean/0issues PASS; final standard is owned by the separate receipt below.
- Source/input proof: actual original Core filtered view/ref data preserved; current/module purpose2/2 and choice2/2+ref5/5 pointer bindings checked in the main two-task native fixture. Approval missing/unresolved/conflicting, partial and verified-origin distinction; user-current overlap; assistant-report source-role upgrade rejection; denied IDs/metadata/getters/private error values excluded before projection hash; only opaque evidence/catalog revision tokens influence its freshness binding. All original A dependencies are retained host-side without adding out-of-view source dependency IDs into model-facing hashes.
- Mode/read/packet proof: reuse native decoder/malformed-result validation; model-generated approval flags are ignored and cannot upgrade missing evidence. Wrong scripted run without approval is rejected as missing required input while raw mode remains run, not credited as model defer. Core checked reads, grants and exact receipts stay authorities. One module's metadata failure returns absent judgement/technical deferred outcome while the other completes. Independent positive structural oracle: expected2/delivered2 packets, conditional exactness2/2 across5 original ref bodies/IDs/kinds/versions and captured projection versions. This is structural availability/fidelity, NOT Jev accuracy or proof that a scripted semantic run is correct.
- Freshness proof: the actual existing Core/A fixture installs evidence/catalog tokens in initial A dependencies, holds raw scripted work, changes either token and observes source_changed/no packet/no ready result; normal context/context_with_system plus equivalent final-copy notification preserve an unchanged pinned snapshot, and a later metadata change invalidates an already offered result. No per-question/RPC timing, real SDK/provider acceptance, real source collection, deadline/noncooperative-raw model qualification or production activation is claimed.
- Trust/remaining boundary: synchronous host metadata ports and revision discipline are synthetic. `originVerified`/association are admitted data, not a model declaration or an authenticity implementation. A caller's capturedDependencies label is not proof they truly installed dependencies: actual A installation is tested, but a dishonest host is not sandboxed. The helper is not the fixture assembler promoted to production; actual source/grant/approval owners and existing B physical-drain integration must be reviewed before real wiring or calls.
- Evidence: `.lazy-harness/evidence/monitoring-core/input-projection-controlled.json` (actual fetch guard0, scripted-only, SDK/model0), `.lazy-harness/evidence/monitoring-core/input-projection-checkpoint.json` (commands/counts/limits) and `.lazy-harness/evidence/monitoring-core/input-projection-standard.json` (last-canonical-mutation standard terminal receipt; a pending/running receipt is NOT PASS). Green mechanical validation cannot change the frozen semantic75% or open C/D.

- Standard retry capsule: first attempt is preserved in `.lazy-harness/evidence/monitoring-core/input-projection-standard-attempt-1.json`: CLI default300s/elapsed300.1s, fast passed2.326s, full-self-test timeout275.717s/exit1. Outer shell900 did not override the inner governor; this is NOT full-regression success. Synthetic-turn `not-armed`/`hook=empty-output` remained blocked after required map/drill/read recovery, so no bypass or unapproved retry occurred. The user then answered **1**, confirming only the previous option1: retry existing standard with explicit `--max-seconds=900`, not release, no source/gold/model/settings change and no repeat of passing focused/strict/lint checks. New human turn is armed/reused-work-unit; one-shot process check found no remaining self-test/governor. Governing SDD permits explicit bounded standard budgets up to3600; this one-time900 cap is NOT a default-policy change. Current terminal status belongs to the linked standard receipt; retry approval/running is not completion, old75% and unapproved next scope remain unchanged.
- Graph: `kg_monitoring_input_projection_impl`, `kg_monitoring_input_projection_builder`, `kg_monitoring_input_projection_error`, `kg_monitoring_input_projection_protection`, `kg_monitoring_input_projection_codec`, `kg_monitoring_input_projection_lease`. Generated implementation index: **stale for these facts**, not rewritten; existing cache is an older records-array shape, the declared schema expects a records map, and current source search exposes no regeneration tooling. Per implementation-map-standard §6.4, use canonical Markdown/graph/source fallback rather than invent cache entries or silently migrate its unrelated format.
- Code organization observe-only: prior exact-intent creating_source_file policy resolve reused. New/changed surfaces only; one accountable projection owner; existing Core/A/native authorities reused; no line-count split/untouched rewrite or inferred system architecture. Discovery capture / Rule placement: this existing TDD is the free-proof primary, independent experimental component delta is in existing SDD, Planning is pointer-only; no operating-rule registry/private memory addition. The SDD/BDD/SSOT/DDD matrix immediately above still applies.

### B stage2 step1 Window-to-projection source provider — controlled proof

User **1** and **“추천대로 가자”** approved only the preceding recommended step1: two NEW source/test paths, synthetic Frames through real Window admission, existing13/Core/A/B/router/SDK/settings/old corpus/gold/75% untouched, SDK/model/network/record lookup/effects0. Steps2/3 remain unapproved. This is not source-unfreeze or new semantic trial approval.

#### Implementation map — verified local conversion owner

- Source `.lazy-harness/scripts/monitoring-core-source-projection.ts`: directly read `captureWindowProjection` and `MaterialSourceProjectionError`. The provider obtains existing Window.snapshot/getStatus, retains its already-owned frozen snapshot, validates only source frame header and bounded module metadata, and supplies the existing ProjectionHost/binding/project interface. It copies/hashes no whole diagnostic Frame or hidden model metadata; no caller code is evaluated.
- Source-role mapping uses admitted kind+provenance only for known user/assistant/tool text/progress; host-owned references stay neutral host containers even if kind/text claims user/approved. Unknown speaker or inconsistent frame/criteria/reference envelope is technical-unavailable, isolated by the existing projector, not fabricated semantic defer. Current IDs come from the retained Window association, not body matching. Body/kind/id/version are exact and Core actual filtered tasks remain the module authority.
- Source-local API delta: immutable catalogue and header capture; dependencies are Window scope + all admitted source versions + explicit host evidence/catalogue revision tokens (maximum32+3). Consumer MUST really install all initial deps and resolve Window versions plus the true revision owners before dispatch; labels are not registration proof. No watcher/approval store/currentness engine is supplied. Model-facing metadata remains per-task-visible; other source dependencies remain host-side.
- Approval conversion is intentionally conservative: a configured, visible original-user-body candidate can be unresolved only, with originVerified=false/association unresolved. No code path emits available or originVerified=true. Assistant/tool reports, generic host docs and approved-record kind labels cannot create genuine proof. No host role is upgraded to native user. The prototype's host-record enum denotes only a host-supplied reference container, not canonical/approved record authenticity. Native SDK authenticity, genuine record read/attribution and actual requester meaning remain outside this constructed-frame proof; existing R all-admitted-source rule is reused without narrowing.
- Protection `tests/lazy-harness/monitoring-core-source-projection.test.ts`: **33 distinct new cases PASS/0FAIL/146expect/708ms; strict for both files PASS**. The earlier26 green cases were not rerun. Actors/progress via real admission, task-local current/roles, exact original envelopes, generic-host/role/label spoofing, hidden IDs/hash noninterference, data/getter allowlisting, contract/ref/event/cursor mismatch isolation, unknown tool argument speaker and missing-current technical absence, source gap/scope/limits/revision collision are covered.
- Independent controlled receiver: expected R packet1/delivered1/conditional exactness1 across2 original refs and captured projectionVersion. K's wrong scripted run is safely rejected for missing approval while raw mode remains run; NOT credited as a correct model defer or semantic grade. Existing Core read/receipt authority and native codec are reused, fixture backend invocation remains0.
- Actual A seam: initial source/scope/evidence/catalogue deps invalidate raw pending work on metadata/catalogue/body/scope/permission/gap changes; raw slot stays active until deferred work settles, including a logical timeout. Real Window equal-body tool hook/final replacement changes latest provenance but not body version: an old immutable capture stays valid; a later capture uses only actually known frame associations. Partial→final removal invalidates the old dependency. Normal context/equivalent copy preserves a still-valid job; a later semantic metadata change invalidates its offer. This reuses existing A, not a new scheduler or a claim about production SDK raw work.
- Evidence `.lazy-harness/evidence/monitoring-core/source-projection-controlled.json`, `source-projection-checkpoint.json`, `source-projection-standard.json` under that directory. Standard pending/running is NOT PASS. Green mechanical evidence never changes old75% or authorizes C/D/SDK/models.
- Machine facts: `kg_monitoring_source_projection_impl`, `_capture`, `_error`, `_protection`, `_window`, `_projector`; derived implementation-index explicitly stale per documented §6.4 fallback, no fabricated cache entries or legacy migration.
- Code organization observe-only: exact-intent creating_source_file resolver matched the recommend-only profile. One bounded conversion owner; no line-count split/untouched rewrite, no duplicate Core/A/read/grant/router/quota authority, no inferred system architecture. Prior baseline files are imported, not edited.

| Layer | Independent delta judgement |
|---|---|
| SDD | experimental source-local capture/ProjectionHost/dependency/trust contract in existing Monitoring Core SDD |
| BDD | no independent live activation/UI flow delta; constructed Frames and controlled sink only |
| SSOT | no permanent model/auth/config/record-ownership store change; caller revision owners remain explicit trusted boundaries |
| DDD | no independent domain rule; existing knowledge/reference eligibility retained |

Discovery capture / Rule placement: this existing TDD is the one step1 proof primary; existing SDD holds its independent experimental interface delta and Planning points here. No new operating rule, private memory store or canonical knowledge write is introduced. Final terminal standard lives in the linked evidence capsule so status capture alone does not cause repeated full regression.

### B stage2 step2a Router input projection port — opt-in mock qualification

User **“추천대로 가줘 우선”** approved step2a only: preserve the current baseline, modify ONE existing router source plus ONE new mock test and necessary records, no Bridge/Core/A/Window/config/generated/auth change or live OpenRouter/model/SDK/Luna call. This is the explicit exception to the prior source freeze for that one file; original pilot questions/gold/approved digests/ledgers are not edited or rescored. Generic SDK remains backend-independent; current host OpenRouter=Jev / Luna=Pi OAuth is unchanged.

#### Implementation map — one accounting/routing/lifetime owner

- `packages/lazy-harness-pi/monitoring/models.ts`: directly read new exported `PreparedJudgeGroup` and `PrepareJudgeGroup` plus `projectedJudgeGroup`. `MonitoringModelRouter.judgeBatch(input,signal,prepare?)` is still assignable to JudgeBatchPort with the original two arguments. No-hook branch uses the SAME existing encoder and routing. The optional trusted synchronous host callback runs after grouping/before canonical perform; it does not authenticate sources, widen grants, own a worker or create another quota/lifetime engine.
- Accepted tasks MUST be an original-order, JSON-byte-exact subset of the routed group; no unknown/duplicate/reordered tasks or changed original question/view/ref/body/version. Empty accepted group omits request and incurs no backend estimate/reservation/invoke. Partial/empty results remain absent technical judgements, never invented semantic skip/defer; bounded MODEL_INPUT diagnostics record omissions. Decode uses the ACCEPTED task/index list, not original indices.
- Prepared data must be bounded plain JSON without accessors/functions/Promise or unknown result/request routing fields, with request.kind equal to the bound profile. Native state task identities/views and exact question key/type/criteria contract remain fixed; nonempty question instructions may point at host metadata. Structured tasks/outputSchema remain exact and instruction text stays nonempty. Extra metadata and instruction meaning remain the explicitly trusted host projection's responsibility, not a hostile-code/source/auth sandbox.
- Existing `perform` measures FINAL prepared request bytes before acquire/estimate/reservation, then estimates and invokes that same immutable request; existing totals/calls/output validation/error redaction/profile groups/abort/deadline/idle/raw-settle release remain authorities. Oversize projection fails before estimate/reservation/invoke, rather than secretly enlarging a backend request afterward. No hook receives credentials or a mutable router state.
- `packages/lazy-harness-pi/tests/model-projection-hook.test.ts` plus directly affected `packages/lazy-harness-pi/tests/models.test.ts`: combined **66PASS/0FAIL/225expect/441ms**, strict for all three files PASS. Covered native/JSON default parity and two-arg type compatibility, inert/identity hook, metadata availability, exact estimator/invoker payload and expanded-token accounting, accepted-index mapping, mutation/shape/criteria/schema/kind/routing rejection, per-profile error isolation, empty0calls, getters/private errors, signal/deadline/budget/driver/physical-slot ownership. The old26/33 source-conversion suites were NOT rerun for this checkpoint; mock backend invocations are not live model requests or semantic-quality evidence.
- Baseline archive: `.lazy-harness/evidence/monitoring-core/router-projection-baseline-models.ts.txt` contains the pre-edit98-line source copied with hashline line endings; temporary sentinel was removed and head/tail read back. This is preserved historical source, not a rewritten old pilot identity. Only the explicitly approved router runtime source was changed.
- Evidence `.lazy-harness/evidence/monitoring-core/router-projection-controlled.json`, `router-projection-checkpoint.json`, `router-projection-standard.json` in that directory. Pending/running standard is not PASS. Actual external provider/model/SDK/network/Luna calls0 and no credential/auth change, not a claim that Main/session cost is0.
- Machine facts `kg_monitoring_router_projection_contract`, `_prepared_type`, `_prepare_type`, `_protected`, `_codec`, `_evidence`; derived implementation index explicitly stale per existing §6.4 fallback, no invented regeneration or legacy migration. Verified methods/types are available through the existing public monitoring/models module (strict public imports pass); no export map/config schema/registration was changed.
- Code organization: exact-intent modifying_source_file resolve reused the recommend-only baseline; small bounded input contract helper and opt-in branch in the accountable router, no line-count split or untouched-flow rewrite. Core/Window/A/source provider remain unchanged; actual Bridge projection/dependency/packet guard wiring and native OAuth worker are NOT provided by this port.

| Layer | Independent delta judgement |
|---|---|
| SDD | additive public optional judge projection callback and accepted-group/protocol/accounting contract in existing Monitoring Core SDD |
| BDD | no independent live UI/activation flow delta; default behavior retained and only explicit mock opt-in used |
| SSOT | no JSON model settings, credentials/provider binding, budget ownership or host route change |
| DDD | no independent business/domain rule; existing module eligibility is unchanged |

Discovery capture / Rule placement: this TDD is the one step2a proof primary, independent additive interface contract is in existing SDD, and Planning links current checkpoint/next unapproved stage. Actual source authenticity/approval association, live host metadata revisions, Bridge guards, SDK payload acceptance and semantic95% remain unqualified; old75% is historical and unmodified. No new operating-policy registry or personal/local memory store is introduced. Final standard status lives in linked evidence so capturing green output alone does not cause repeated full regression.

## Step2b — approved opt-in Bridge projection and checked packet regression

The native option **Bridge만 연결 (Recommended)** and subsequent explicit continuation after the Main-provider correction approve this bounded exception to the source freeze: ONE existing Bridge source and ONE new mock test, not SDK/worker/provider execution. The current Main selector is owned by the existing provider SSOT; it is not changed here and extra-fixture-call0 is not a claim of total session cost0. Existing gold, questions, approved digests, historical75% and paid experiment ledgers are not edited or rescored.

### Implementation map — A/Window/Router/Core remain the authorities

- `.lazy-harness/scripts/monitoring-core-realtime-selection.ts`: exported `RealtimeInputProjection` is an OPTIONAL host callback port, not JSON configuration. Capture fixed evidenceId/contractId and callback identities; reject duplicate/reserved/colliding IDs and unavailable revisions. `RealtimeSelectionBridge.dependencies` adds those real owner revisions before A admission. `sourceVersion` delegates body/scope IDs to Window and exactly the two metadata IDs to their owner, failing closed on collisions. The factory requires maxSources+3 opt-in versus the unchanged maxSources+1 default.
- `perform` captures the source once within the existing Work, checks frame and EXACT metadata/body/scope dependency identities/versions plus currentness around capture, and incorporates metadata revisions into opt-in context version. No admission cache or new watcher, source store, approval authority or worker exists. A caller must provide genuine revision bumps when catalogue/association/semantic approval meaning changes.
- `judge` delegates the existing Router's synchronous per-profile prepare hook to `WindowProjectionSource.project`; store the bounded returned batch in Work by accepted processorId. Pass ONLY its plain `{tasks,request?}` projection to Router, not methods or internal keys. Existing accepted-subset/reindex/codec/bytes/estimate/reservation/decoder/raw drain remain Router-owned. A module's projection failure does not erase a successful sibling.
- An opt-in host backend wrapper only READS existing Work/lease/permission/material/metadata/profile/request currentness immediately before the ORIGINAL estimate and invoke, then delegates to those original bound methods with the SAME request. It neither enlarges input nor creates a second cost/queue/transport engine. Stale queued work cannot reach the original backend; work already invoked remains physically owned until raw settlement.
- Only after Core has actually read selected references does the existing `InputProjectionBatch.checkRunEvidence` guard a module packet. Required roles/approval omissions suppress the packet despite a scripted native run. Successful opt-in packets add `projectionVersion`; the absent-port packet and encoder path remain unchanged. Returned/ready dependencies retain both metadata revisions so A rejects stale offers.
- `tests/lazy-harness/monitoring-core-selection-projection.test.ts`:30 unique controlled mock cases cover final enriched estimate/invoke equality, private-source exclusion, old default packet/encoder, initial dependency ceiling and owners, fixed callback identities, bad capture/frame/dependencies/revisions, real required-role reads and approval status, genuine per-module builder failure/reindexing, distinct profile groups, final bytes and lifetime budgets, metadata/permission/intent fences, queued stale original-invoke0, metadata-ready invalidation and raw disposal/drain. Global fetch is forbidden. These are synthetic admitted Frames, NOT native SDK/authenticity or semantic quality.
- Baseline `.lazy-harness/evidence/monitoring-core/bridge-projection-baseline-selection.ts.txt` preserves the exact pre-edit193 source lines using hashline copy; head/tail readback confirms it. Existing Core/A/Window/Router/source-provider/model settings/auth and old consumer test remain unchanged (a mistaken import insertion into that old test was immediately undone, restoring it exactly).
- Evidence capsule `.lazy-harness/evidence/monitoring-core/bridge-projection-checkpoint.json` keeps actual validation runs and non-unified rollup: new30 plus reused directly affected B22 mechanical cases; actual-SDK4 cases excluded. `.lazy-harness/evidence/monitoring-core/bridge-projection-standard.json` owns the later terminal standard result; pending receipt is not a pass.
- Independent API contract: `.lazy-harness/spec/platform/pi-monitoring-observation.md`; provider ownership: `.lazy-harness/ssot/monitoring-configuration.md`. Four `kg_monitoring_bridge_projection_*` facts connect contract/source/export/test/evidence in `knowledge/graph.jsonl`. Generated index remains explicitly STALE pending a real indexer, per implementation-map standard; use this Markdown, graph and exact source rather than inventing regeneration.
- Organization review: exact-intent modifying_source_file policy resolved recommend-only; change stays local to the accountable Bridge. No line-count split, untouched rewrite, architectural profile inference or duplicate lifecycle/limit authority.

| Layer | Independent delta judgement |
|---|---|
| SDD | additive host Bridge runtime port, fixed metadata dependency resolver/ceiling and optional packet sidecar; existing observation component SDD updated |
| BDD | no independent human-visible activation/UI flow; live/default path not enabled, internal controlled packet qualification only |
| SSOT | no JSON config/schema/env/credential/provider choice or authority change; existing host binding reused |
| DDD | no independent business/domain rule; reuse existing current/approval/required-evidence eligibility |

Discovery capture / Rule placement: this existing TDD is the single proof primary, with only the independent component API delta in SDD. Real host revision sources/authenticity, actual SDK acceptance, Pi OAuth worker wiring and fresh semantic qualification remain outside step2b. No new operating-policy registry or local personal rule mirror.

## Step2c actual-SDK/faux regression — five mechanical cases passed; terminal standard separate

User **“추천대로 해줘”** approved the concrete existing Planning recommendation: one NEW `tests/lazy-harness/monitoring-core-selection-projection-sdk.test.ts`,5 cases/at most5 local SDK fixtures, synthetic data, isolated faux provider/scripted native driver, own-temp cleanup, existing Bridge/Core/A/Window/Router/source-provider/SDK fixture/auth/settings unchanged. Real provider/OpenRouter/Jev/Luna/Reader inference and worker/live/semantic activation remain unapproved.

### Implementation map and first evidence

- New SDK test reuses verified `createSdkFixture`, `captureWindowProjection` and unchanged selection factory. Installed package1.4.0 exports `dist/index.js`; only the test child selects that local entry. Fixture uses empty InMemoryCredentialStore, no host resources, allowModelNetwork:false, fauxProvider and synthetic tool; global fetch throws.
- Strict passed. First bounded --bail execution created3 local SDK fixtures: first2 passed (native source→metadata→same estimate/invoke→Core read→versioned packet/no injection, and native equivalent-copy/context survival). Third reached actual queue1/capturedJobs2 but failed an incorrect test expectation that original estimate should be called2 times; observed1. Existing `packages/lazy-harness-pi/monitoring/models.ts` directly inspected: `acquire` precedes backend estimate, so the readonly fence blocks stale queued work before that original estimate too. This is not justification to change the Router or another owner. Remaining2 cases did not execute; no full qualification/pass claimed.
- `.lazy-harness/evidence/monitoring-core/bridge-projection-sdk-attempt1.json` preserves the failure and budgets. Bun --bail did not emit the afterAll controlled report; final fetch-attempt count is therefore NOT claimed, although every fetch was blocked and no real inference backend is used.
- Original cap5 must not be silently widened:3 consumed; rerunning the corrected failed case plus2 unrun cases would total6 local SDK fixtures. Explicit user choice is required to add1; do not rerun passing2 or start another SDK fixture before that choice. Existing historical gold/ledgers/75% and Main/provider settings remain unchanged.


**Latest user-confirmed allowance:** the user answered **1** to the explicit recommendation to add exactly ONE local SDK fixture: original cap5→cumulative cap6. Three were consumed in attempt1; run ONLY the corrected queue case and the two previously unrun cases, at most3 further local fixtures. Passing first2 are reused, not rerun. A test-child-only fixture cap3 prevents accidental extra sessions in this selected run; full default remains5. This selection does NOT authorize provider/OpenRouter/Jev/Luna inference, existing source/auth changes, worker/pilot/semantic work or a further allowance reset.

### Completed controlled SDK proof — five UNIQUE cases, no paid inference

- The user-confirmed cap6 is fully accounted: attempt1 used3 local SDK fixtures (2 pass + one wrong assertion); the selected follow-up used exactly3 with child cap3 (3 pass,2 filtered out,19 expectations,1160ms). Total6/6, not a per-run budget reset. Passing first2 were not rerun. All FIVE distinct cases now have passing evidence, NOT one fresh unified five-case run.
- `.lazy-harness/evidence/monitoring-core/bridge-projection-sdk-controlled.json` is the actual follow-up report, with SDK1.4.0, fixturesStarted3/cap3, completeFiveCaseRun=false, fetchAttempts0, realProviderInferenceCalls0 and three concrete proofs: queue1/capturedJobs2/original classifier invocation1/stale packet0, two independent required/approval guarded modules with packet0, and native steer/shutdown physicalDrainObserved=true/stale packet0. Initial fetch-attempt counter is unavailable because --bail skipped afterAll; do not invent a cumulative fetch-attempt0.
- The new test's ONLY functional corrections were the correct original estimate count1 (the existing Router acquires BEFORE estimate) and a bounded integer1..5 test-child `PI_MONITORING_SELECTION_PROJECTION_FIXTURE_CAP`, set3 for the selected run. It controls local test resources, not model configuration or SDK credentials. Full default5 remains; missing explicit SDK entry skips rather than qualifies. Strict passed after this final coherent correction.
- `.lazy-harness/evidence/monitoring-core/bridge-projection-sdk-checkpoint.json` rolls up the two real runs; `.lazy-harness/evidence/monitoring-core/bridge-projection-sdk-standard.json` separately owns final standard state. No additional SDK fixture may be started by validation: final standard child unsets SDK entry/require/cap/report variables. No existing source/fixture/Core/A/Window/Router/auth/JSON settings/old gold or ledgers are changed.
- Confirmed implementation map: new SDK test's `composition` uses existing `createRealtimeSelectionPipeline`, `captureWindowProjection` and `createSdkFixture`; the latter owns in-memory credentials/model isolation/synthetic tool/temporary-root disposal. No new public API, transport/queue/budget owner or live activation. Graph kg_monitoring_bridge_projection_sdk_* connects existing contract→new protection→fixture/proof. Generated index remains explicitly stale per the existing standard; source/Markdown/graph are the fallback, no invented regeneration.
- Observe-only organization: one new test with one local composition helper, shared existing lifecycle fixture and explicit resource cap. No source splitting, untouched rewrite, provider selector changes or extra classifier/worker call. These SDK sessions use faux/scripted responses; authentic real-user approval, real host OAuth worker, semantic accuracy, old75% and live pilot are not promoted.

| Layer | Independent delta judgement |
|---|---|
| SDD | no independent API/component contract change; controlled SDK qualification of existing interface is recorded in this TDD primary |
| BDD | no human-visible activation or Main injection; isolated SDK synthetic data only |
| SSOT | no production env/config/schema/auth ownership change; test-child entry/report are proof parameters |
| DDD | no business/domain rule change; existing current/approval eligibility reused |

Discovery capture / Rule placement: this existing TDD is the single SDK proof primary; Planning owns the approved proposal and explicit cumulative cap6. Five unique mechanical SDK cases now pass within6/6 fixtures, with terminal standard tracked only in its linked capsule. No independent SDD/BDD/SSOT/DDD semantic delta or duplicate operating rule; no worker/pilot/semantic promotion.

## Step3a — new24 draft / CPU input and evaluator conformance

The user **“1 로 하자”** selected the preceding concrete recommended preparation scope: three NEW files (draft corpus, CPU helper, tests) plus necessary records/evidence. No existing Core/A/B/Window/Router/source-provider/SDK fixture/gold/ledger/auth/settings change; actual SDK/provider/OpenRouter/Jev/Luna/Reader requests0. This is PREPARATION, not label acceptance, a frozen holdout, production-source authentication or permission for actual model evaluation.

### Implementation map and current proof

- `.lazy-harness/fixtures/monitoring-core/realtime-B-input-v2-draft.json`:24 fresh fictional source scenarios, two module expected outcomes each (48 decisions), per-module8run/8skip/8defer. Explicit status=draft/review=author-labelled-unreviewed/independentAdjudication=false. Source declarations and evaluator expected modes/IDs/review notes are separate. Original pilot corpus/questions/gold/75% are preserved, not retuned/rescored.
- `.lazy-harness/scripts/monitoring-core-input-v2-evaluation.ts`: verified exports `DRAFT_SCOPE`, `DRAFT_MODULES`, `DraftEvaluationError`, `validateDraftInput`, `validateDraftCorpus`, `prepareDraftInput`, `scoreDraftRun`, `compareDraftModes` and typed draft structures. Scope is synthetic-evaluation-only. Source consistency checks bind declared body/version/case/actor/stage/authority and current↔approval association; byte equality/SHA consistency is NOT cryptographic real-host identity or semantic consent. User cannot inject originVerified. The local adapter derives fixture-only provenance after declarations validate; partial/conflicting/wrong-target evidence stays unresolved/conflicting.
- `prepareDraftInput` accepts ONLY input (whole case/gold rejected), asks isolated existing Core instances to issue each host-visible/granted module view, then reuses the existing projector/required-input guard. Preparation's Core judge port returns no decisions and its read/sink reject effects; no semantic classifier/search/worker/SDK is implemented. 24-case coverage emits48 Core-issued tasks. Synthetic snapshot lease is not a live A/watcher or host-authentication implementation.
- Core event/scope IDs are opaque hashes of the VISIBLE current source, NOT evaluator case ordinal, hidden content or gold. Out-of-view bodies/IDs/versions cannot influence model payload/digests. Requested-material input pool includes available distractors, not a preselected expected-answer list; available approval can accompany a transient expected-skip case. Input metadata is not a semantic classifier.
- `scoreDraftRun` keeps24 cases per module/48 total including missing/timeouts/malformed. Report mode accuracy, confusion with technical-outcome columns, per-mode precision/recall/F1, run/defer recall, false raw runs, exact selected/declared-checked IDs/versions/bodies, useful-run recall, guard-denied runs, unwanted usable packets and integrity failures. Raw incorrect run is not reclassified to defer even when a guard blocks it. Caller-supplied checkedReferences are byte-checked snapshots, NOT proof that actual Core readReference ran. `compareDraftModes` does not reward mutual missingness. All reports explicitly say offline arithmetic, semanticAccuracyMeasured=false, realHostAuthenticity=false and labelsIndependentlyAdjudicated=false.
- `tests/lazy-harness/monitoring-core-input-v2-evaluation.test.ts`:43 unique passing CPU protections across checkpoints, NOT one unified fresh43 run: initial40/284expect/1297ms; added confusion2/22expect/387ms; final identity-affected4 (3 relevant rechecks +1 new)/182expect/385ms. Initial two strict typing errors were corrected without JS semantics; final strict passes after identity/metric changes. Tests verify oracle arithmetic, not a real Jev accuracy result. Global fetch blocked; all three actual controlled reports fetchAttempts0, SDK0/model0.
- Evidence: `input-v2-controlled.json`, `input-v2-metrics-controlled.json`, `input-v2-identity-controlled.json`, `input-v2-checkpoint.json` under `.lazy-harness/evidence/monitoring-core/`; latest payload max10869bytes. Derived human review table `.lazy-harness/evidence/monitoring-core/input-v2-review.md` exposes expected labels for REVIEW ONLY and must never enter model input. `.lazy-harness/evidence/monitoring-core/input-v2-standard.json` separately owns terminal standard; pending is not success.
- Independent new local API contract is in existing `.lazy-harness/spec/platform/monitoring-core.md`; graph kg_monitoring_input_v2_* maps contract/source/corpus/verified prepare/score symbols/protection/evidence. Generated implementation index explicitly remains stale under the existing tolerance; Markdown/graph/exact source are fallback, no invented generator or legacy migration.
- Observe-only organization: exact-intent creating_source_file baseline resolved; one bounded new helper owns draft validation/projection preparation/offline metrics, no line-count split or untouched source rewrite. No second Core read/receipt, authority, queue, transport or cost engine. Test report env is child-only, not production configuration.

| Layer | Independent delta judgement |
|---|---|
| SDD | new draft-local typed input/preparer/offline evaluator interface; existing Core SDD adds evaluation-only contract, NOT public SDK/live API change |
| BDD | no human-visible live activation or context injection; derived review table is evaluation evidence only |
| SSOT | no production configuration/credential/ownership delta; fixture scope and child report path do not establish real host authority |
| DDD | no new business/domain rule; existing user-confirmed forward knowledge/reference meaning reused |

Discovery capture / Rule placement: this existing TDD is the single proof primary, with only the independent local-interface delta in existing SDD. Remaining work is independent label/source-assumption review, explicit freeze/profile/budget and actual Jev qualification; authentic real-host approval/association, Pi-OAuth worker and live effects are not claimed or auto-approved. No new operating-policy/local-memory mirror.

## Step3b — explicitly approved fresh24 Jev pilot, new qualifier and journal

The user answered **1** to the concrete next option: provisional acceptance of current24 synthetic author labels/owner assumptions FOR THIS PILOT ONLY; new runner/test/profile + CPU validation + source/corpus/question/profile/SDK identity freeze + ONE Jev pass <=24HTTP/USD0.10 SDK-estimate/reservation/600s active. OpenRouter typesafe/jev-1.14/typesafe-system-one ONLY. No automatic retry/tuning/label correction, old balance reuse, SDK AgentSession/Luna/Reader request, real-user collection, billing/account read, token export, live hooks/Main injection/business effects. SDK estimate is NOT an invoice guarantee or total Main/session cost. Corpus remains draft/independentAdjudication=false; separate manifest records user acceptance of provisional labels, not independently verified gold.

### Implementation map — actual reads/receipts and existing accounting owners

- NEW `.lazy-harness/scripts/monitoring-core-input-v2-pilot.ts`: verified exports `validateInputV2Profile`, `InputV2Budget`, `checkInputV2Request`, `exactInputV2Model`, `inputV2RouteFetch`, `runInputV2Case`, `evaluateInputV2Trial`, `inputV2Identity`, `assertInputV2Identity`, `prepareInputV2Pilot`, `claimInputV2Start`, `runApprovedInputV2Pilot`. Default/import does no inference. Existing Budget/createMeteredRequest own pricing/reservation/HTTP counting, serial transport, maxRetries0/redirect error/45s per-request deadline and cost-hold settlement. New InputV2Budget only narrows native input<=69632/request and1671168 cumulative/output generation0. Existing Router remains per-case codec/profile/bytes/raw-lifetime owner; global paid envelope is the existing Budget instance.
- Native request bound64KiB,64 answers/16KiB response; exact provider/model/API/pricing enforced with no model fallback. New route fence requires https://openrouter.ai/api/v1/ POST JSON and exact Jev model, rejects proxies/credential URLs/query secrets/oversize, supports both URL+init and Request without consuming its original body. SDK metadata initialization is fetch-blocked; credentials resolve inside Pi's existing SDK, never printed/exported. No new search or lifecycle engine.
- `runInputV2Case` obtains existing CPU helper's Core-issued immutable tasks/projected request, calls the existing Router once, and materializes those SAME native decoded decisions through isolated actual Core instances with byte-equal view checks. ReadReference callbacks independently record granted exact IDs/kinds/versions/bodies; handlers apply the existing batch required-evidence guard AFTER those reads; sink records only in-memory synthetic staged-proposal receipts whose materials equal actual reads. No gold determines dispatch/read IDs. This is controlled synthetic Core evidence, NOT live SDK-source authentication, real worker output or business-state acceptance.
- Preserve full rawDecisions/audit/actual Core reports. Native codec's automatically required eventRef remains raw; ONLY that context eventRef is excluded from the separate material-only scorer observation, because existing corpus material IDs exclude it. Mode/meaning/wrong source refs are not repaired. Synthetic receipt IDs are bounded hashes, not potentially oversized full request IDs. Two initial implementation errors (receiptID>200 and eventRef vs material-set representation) were corrected in NEW source only before freeze/any real request.
- Identity includes exact bytes of new runner/test/profile, existing corpus/helper/projector/Core/meter/model source, all24 prepared request/question hashes and explicit installed SDK entry/package hashes. `manifest.json` and exclusive `started.json` in the NEW evidence directory prevent drift/second run. Pending/uncertain started work cannot automatically resume/reset. Actual loop checks identity before every case, journals pending BEFORE dispatch and rejects technical/integrity/multiple HTTP outcomes without retry; semantic mismatches continue and remain in denominators24/module.
- NEW `.lazy-harness/fixtures/monitoring-core/realtime-B-input-v2-pilot-profile.json` owns this experiment's exact envelope, NOT a global SDK/provider whitelist. NEW `tests/lazy-harness/monitoring-core-input-v2-pilot.test.ts`:16 unique passing CPU protections across bounded checkpoints, not one fresh16 run. Initial11pass/3fail, affected3pass, new eventRef1pass, affected route3pass(2 rechecks+1 new), affected freeze1pass; latest strict green. Actual oracle Core coverage24 cases/29 read callbacks/16 in-memory staged receipts; fake transport only, external fetch0 and real inference0 before dispatch.
- Pre-dispatch validation: CPU/strict/doctor corrected-source protections are green. The user confirmed task318 belongs to a separate worktree/workstream and directed this pilot to proceed; official five-file `lazy check --files` passed. Final standard uses explicit owned pilot files/records (`--files`) while retaining full self-test. Prior unscoped failed attempts remain preserved and are not called globally green; no other-task key access/relocation or global exclusion change. Then prepare exact identity with the approved installed SDK and execute once. No source/label mutation after first real dispatch. New result authority stays `.lazy-harness/evidence/monitoring-core/input-v2-jev24-v1/summary.json`/adjacent journal; old12/75%/ledgers unchanged.
- Report actual per-module confusion/P/R/F1/false runs/useful-work/material exactness and joint correctness; any uncompleted cases stay missing, never correct uncertainty. `pilot-correct-all-provisional-labels` versus `pilot-completed-with-mismatches` describes observations only, NOT an invented formal95% gate. Small author-labelled synthetic24 is not independent adjudication, population reliability or production B acceptance. Genuine host approval/authentication, Pi-OAuth worker and live pilot remain separate.
- Graph kg_monitoring_input_v2_pilot_* maps verified contract/source/profile/case/meter/protection/evidence. Derived implementation index stays explicitly stale; exact source/Markdown/graph fallback applies, no generator or legacy rewrite invented. Organization resolve was recommend-only; one new qualifier coordinates existing authorities without a duplicated cost/transport/Core implementation or untouched source split.

| Layer | Independent delta judgement |
|---|---|
| SDD | additive evaluation-only qualifier/read/receipt/identity contract; existing Core SDD updated, production SDK API unchanged |
| BDD | no live UI, Main injection or business-effect flow; synthetic staged receipts only |
| SSOT | experiment profile/new journal own approved bounds; user-confirmed separate-worktree/task ownership is captured in project-identity.md; no production credential/config authority change |
| DDD | no new domain/business rule; user-confirmed forward candidate/reference meaning reused |

Discovery capture / Rule placement: existing TDD remains one proof primary and new independent local qualifier interface is in existing SDD; actual post-dispatch results remain the linked immutable journal/capsule. No global operating-rule or personal-memory duplication, no whole-B/worker/production promotion from this pilot.

### Pre-dispatch C17 failure and same-scope correction

First standard exited1 after448.311s: new runner's literal external URL violated D06/C17; the doctor-negative/package-health wrapper subprocesses both failed because full doctor aggregates that D06 failure (D07 itself was ok). This was OUR new source defect, not a peer file or a doctor bug. Complete first receipt is `input-v2-pilot-standard-attempt1.json`; direct diagnostic is `input-v2-pilot-doctor-blocker.json` under the existing evidence directory. No freeze/start/actual Jev HTTP occurred.

Correction stays inside the three approved new files: experiment profile now owns endpointOrigin/endpointPathPrefix; runtime validates/consumes those data, and a separate CPU test pins the approved destination. No doctor/allowlist/existing source edit, string splitting or regex bypass. Changed5 CPU cases pass (34 expectations/429ms), final strict passes, direct full doctor D06/D07 pass; old Unicode D08 is advisory and not fixed out of scope. A final standard is required on this corrected coherent batch before freeze/dispatch; no unchanged paid test is rerun and old failed receipt is preserved. The existing step3b four-row layer matrix applies; no new global policy/host ownership delta.

### User-confirmed worktree isolation — prior wait superseded

The user's explicit correction is that task318 is another worktree/workstream and irrelevant to this pilot's dependency chain. The owner confirmed key ownership; no bytes were accessed or changed. Official explicit five-file check passes. Continue with owned-file standard (full self-test still enabled), freeze, and the SAME approved once-only Jev budget, without waiting for relocation or changing global exclusions. Both initial failures remain truthful historical capsules. Independent ownership delta is in `.lazy-harness/ssot/project-identity.md`; this section supersedes earlier wording that required a globally clean scan before dispatch.

### Measured fresh24 pilot result — evidence capsule

Owned9-file standard retained full self-test: fresh91 ran/skipped0/errors0,449.183s. Exact source/corpus/questions/profile/installed SDK1.4.0 identity was frozen; actual one-shot OpenRouter Jev finished exit0. `input-v2-jev24-v1/summary.json` and `ledger.json` under `.lazy-harness/evidence/monitoring-core/` are the measured authority: completed24/24, jointCorrect24/24; knowledge24/24 and references24/24 modes correct, each run/skip/defer8; exact required reads and useful runs8/8 per module; false runs/missing/timeouts/malformed/integrity violations0. ActualHTTP24, SDK-estimated USD0.003633966, active12446.170145ms, pendingnull/error empty. No auto retries, additional model/SDK AgentSession/Luna/chat generation/live effects, source/gold/auth edits or other-task key access. Both prior failed attempts remain preserved; scoped pass does not claim the whole shared tree is globally clean.

This is provisional author-labelled synthetic24, NOT independent adjudication, population reliability, real host-origin/approval authentication, worker-Pi-OAuth validation, formal95% gate or production B acceptance. No post-result label tuning/second paid run. Existing SDD/BDD/SSOT/DDD judgement matrix above applies; independent worktree ownership correction is already in project-identity.md. Discovery capture: result is one linked TDD evidence capsule, not new multi-layer narratives; preparation/terminal task evidence is in input-v2-pilot-checkpoint.json and input-v2-pilot-scoped-standard.json.

## Step3d — CPU host-evidence adapter protection, not real-source authentication

The user's “좋아 진행해줘봐” approved the bounded CPU helper1/test1 following the contract design. NEW `.lazy-harness/scripts/monitoring-core-input-trust.ts` and NEW `tests/lazy-harness/monitoring-core-input-trust.test.ts` implement this local experimental seam; existing Core/projector/source/router/public schemas/frozen corpus/gold/auth/config are untouched. SDK/model/worker calls, real-user collection, live effects and signing-key handling0. This does not improve/regrade the completed author-labelled24/24 semantic pilot or qualify actual native approval authenticity.

### Implementation map

- Verified `buildTrustedInputProjection`, `InputTrustError`, `InputTrustAuthority`, `InputTrustCandidate` live in the new helper; runtime import probe exports only function/class, external calls0 and invocationfalse. Expected namespaces, injected trusted owner and already-captured authority dependency are explicit. Initial source/disclosure/inference denials occur before owner attestation or fake judge dispatch.
- Existing buildInputProjection is reused twice over immutable safe snapshots: suppress untrusted base.approval, then strict owner attestation to admitted visible refs. Original/record roles, native encoding, limits, uncertain statuses and required-read guards remain in the existing projector. Candidate digest is only a link fence, not proof. Honest revision-disciplined host code remains trusted; no sandbox/crypto/native entry authority is claimed.
- `MonitoringCore` and `RealtimeMonitoringCoordinator` remain actual grant/read/proposal/physical-lifetime owners in integration tests. C01 observes fake judge1, actual checked reads5 and independent review proposals2, comparing exact materials by module ID/ref ID rather than asynchronous arrival/role order. C18/C19 observes raw knowledge run preserved, guard APPROVAL_NOT_AVAILABLE, fake judge1 and only reference-module proposal. C16 tests pending authority change with physical slot retained until settle and no accepted late packet; C17 proves unrelated worktree/equivalent context-copy changes do not kill pinned work, while relevant revision change invalidates ready offers.

### Controlled evidence and failure history

Thirty distinct passing CPU cases across bounded checkpoints cover the20 design categories plus scope/namespace, owner exceptions, bounded malformed arrays and source-role mismatch. They are NOT one fresh30 run: initial26=25pass/1fail(164 expectations/358ms), affected7=6pass/1fail(44/268ms; includes2 prior rechecks+4 new), final failed C01 only=1pass(11/212ms). Unique union30, not a sum32. Initial strict2 narrowing diagnostics were fixed; final strict passes. Default import/export probe passes with external calls0. Initial receiver assertions incorrectly assumed module completion order, then material role order; corrections changed only NEW test verification to exact ID/body comparisons, not runtime behavior, old gold, raw evidence or user semantics. All failed checks are preserved in checkpoint history, not counted green.

Witness artifacts under `.lazy-harness/evidence/monitoring-core/`: input-trust-controlled.json (C18 raw run/guard), input-trust-affected.json, input-trust-receiver.json (actual read5/proposal2), input-trust-checkpoint.json (CPU/strict/probe/approval scope), input-trust-standard.json (the ONE final owned-source/records/graph standard terminal). SyntheticOwnerOnly=true, network0, realSourceAuthenticationQualified=false. Proposed design cases are now exercised by private CPU tests, not an actual SDK/provider/live acceptance run.

| Layer | Independent delta judgement |
|---|---|
| SDD | additive private trusted-owner port/admission/candidate binding/composed lease/safe replay contract; existing monitoring SDD updated, no adopted public SDK ABI |
| BDD | no real collection/UI/Main injection/business-effect flow enabled; review-only synthetic proposals |
| SSOT | existing explicit Host admission/grant/credential/capacity/worktree ownership reused; no new persistent config, real issuer registry or source-auth authority |
| DDD | existing source/candidate/approval meaning unchanged; available remains not approved and hashes/role strings are not proof |

Discovery capture / Rule placement: one reliability proof primary plus independent SDD interface delta. Policy resolve edit/creating_source_file returned code-organization-profile recommend-only; observe baseline applied to new files only, no architecture inference/untouched split. Canonical graph kg_monitoring_input_trust_* stores verified implementation facts, legacy rows unchanged; generated index explicitly stale for additions, canonical/source fallback used. The local verifier and scripts are not a new global operating policy. Real host bindings and another paid/worker/live scope require separate approval.

## Step3e — actual SDK original-input source owner, controlled profile only

The native option gate explicitly selected Pi original-input binding+controlled SDK after source/API investigation. Approved NEW helper/test2 and fresh SDK cap4creation attempts/12prompt submissions/600s active, official faux/in-memory/isolated scope. NEW `.lazy-harness/scripts/monitoring-core-pi-input-trust.ts` exports `createPiInputTrustBinding`/`PiInputTrustError`; NEW `tests/lazy-harness/monitoring-core-pi-input-trust.test.ts` implements CPU and actual-SDK qualification. Existing active package/observer/Core/source/projector/router/public schemas/gold/auth/settings and other-worktree artifacts are untouched. Live collection/real HTTP/Jev/Luna/Reader/worker/canonical effects0.

### Implementation map and meaningful guards

- Source-local factory is opt-in/default-off, input/session_start/session_shutdown only, always continues input. Explicit qualified honest Host registration/root/session/permission owner is required. Source tag/role/hash alone is never human authentication; unknown handler prefix returns no proof. It does not detect a dishonest Host asserting a false prefix guarantee.
- Source snapshot is one bounded text reference with LOCAL observation/ref IDs, not persisted SDK entries; no history/branch/system/image/credential body access in the binding. Extension source is ignored before body/getter access; private root/denied/malformed/oversize input cannot preserve stale original approval. Versioned permissions, session rebinding/late callbacks/disposal invalidate native truth. Other worktrees/context diagnostics leave pinned truth intact.
- InputTrustAuthority adapts real admitted native callback data through the unchanged CPU verifier. Attributed approval evidence only for that exact sole current native ref; authentic origin for another candidate remains unresolved. No approved-record or prior-proposal reply authority is fabricated. Available is still not approval; actual model semantics are not tested by scripted judge.
- Actual MonitoringCore is the read/effect authority. Controlled positive SDK delivery observes4 checked material reads/two in-memory review proposals/fake judge1. The qualified prefix preserves SDK input text even when a later transform changes model-visible user text; extension-source input cannot become new original proof. Actual SDK session replacement clears/rebinds source generations.
- Controlled negative SDK uses a real earlier transformer with owner configured unqualified. The actual model-visible `PRIOR_TRANSFORM:SYNTHETIC_UNQUALIFIED_RAW` body is carried as an ordinary unverified ref through checked reads to the reference receiver; knowledge raw run is retained and denied APPROVAL_NOT_AVAILABLE, refs still succeed. This is NOT a static user-intent classifier or silent repair of wrong model output.

### Observed CPU / SDK evidence — no changed-score claim

CPU checkpoint:17pass/2explicit SDK skips/0fail,49expectations/378ms. Actual selected SDK checkpoint:2pass/17filtered/0fail,19expectations/912ms. Affected negative SDK case was strengthened to use the actual SDK transformed body instead of a generic synthetic placeholder, then ONLY that changed case reran:1pass/18filtered/0fail,7expectations/714ms. Unique cases19 total (CPU17+SDK2), not a fresh19 run and not20. No failed CPU/SDK assertion occurred in this unit; final strict and default-import/export/no-network probe pass.

Cumulative authoritative `pi-input-sdk-ledger.json`: actual SDK1.4.0, SDK creations4/approved4 (includes runtime newSession and the changed negative oracle recheck), prompt submissions7/approved12, active1228.146428ms/600000ms, observed native session_start4, pendingnull. Original two-case report captured intermediate3/6; preserved strengthened report/ledger records final4/7. Never sum snapshots or reset cap. SDK capacity exhausted; no automatic extra attempt/fallback/old balance reuse. External fetch guards report network0. SDK faux assistant requests are local scripted responses, not paid model calls.

Artifacts under `.lazy-harness/evidence/monitoring-core/`: `pi-input-cpu-report.json`, `pi-input-sdk-report.json`, `pi-input-sdk-negative-report.json`, `pi-input-sdk-ledger.json`, `pi-input-checkpoint.json` and ONE final `pi-input-standard.json`. Shared SDK fixture's observer sees its own synthetic history/system content for an independent oracle; no current user conversation is observed and this binding itself does not read those APIs. RealHumanIntentQualified=false/liveActivation=false; controlled native callback/source qualification is not population semantic accuracy, human identity proof, hostile-host security, production B acceptance or worker-Pi-OAuth qualification. Old frozen24/24/corpus/gold remain unchanged.

| Layer | Independent delta judgement |
|---|---|
| SDD | additive private actual SDK input-owner/factory/local-source identity/current-only attribution/lifecycle contract; existing monitoring SDD updated; no public ABI adoption |
| BDD | controlled SDK synthetic events only; no live UI/collection/Main injection/business flow enabled |
| SSOT | existing Host permissions/admission/grants and experiment ledger own bounds; no new credential/config/global approval registry or live activation authority |
| DDD | existing candidate/approval semantics preserved; genuine origin does not approve any arbitrary candidate |

Discovery capture / Rule placement: existing reliability proof primary plus independent SDD source-owner interface. Exact edit/creating_source_file resolve returned code-organization-profile recommend-only; baseline observed only on new files. Append-only graph facts kg_monitoring_pi_input_trust_* preserve all legacy rows; implementation index explicitly stale for additions, no fabricated generator output. Actual SDK1.4.0 docs/examples/types/prompt dispatch were read before implementation. Stage3e is this bounded selected source profile, not a new generic operating policy. Real current-session activation or another SDK/model/worker source scope needs separate approval.

## Step3f — explicit question/proposal/reply link, CPU-only conformance

User chose1 after the concrete three-file A proposal. EXISTING `.lazy-harness/scripts/interview-loop.ts` adds readonly `readInterviewQuestion` only; NEW `.lazy-harness/scripts/monitoring-core-review-link.ts` + NEW `tests/lazy-harness/monitoring-core-review-link.test.ts`. Real question queue/logs, legacy CLI/collect/answer/ID/effects, current loader/native-input binding/Core/projector/router/gold/auth are unchanged. SDK/real-model/worker/real collection/UI/canonical effects0; old SDK4 cap remains exhausted and unconsumed here. Temp fixture queue writes/answer-close are controlled test setup via the existing owner, never current-host answers.

### Implementation map — identity, meaning, presentation and checked reads

- `readInterviewQuestion` delegates the sole existing parser, fresh lookup/missingundefined/duplicate rejection/no writes. Runtime imports preserve collectInterviewQuestions/answerInterviewQuestion and add only the lookup; no CLI runs at import.
- Verified new `captureReviewQuestion`, `createReviewLinkBinding`, `ReviewLinkError`, `ReviewLinkReceipt`, `ReviewLinkHost`. Q-id remains identity, while full options/effects/crossRef/proposal snapshot meaning is privately versioned; displayed text/options have a separate public reference/version. Private effects/IDs/hash never enter model request; exact private revision is forbidden in public evidence/contract deps.
- Explicit trusted Host receipt and native source proof are independent requirements. Missing link, pending/ambiguous/cancelled state, wrong question/version/scope/contract/candidate/native reply cannot become available approval merely through CLI answered flags, latest-message guessing or model confidence. No native UI/presentation issuer is implemented by these synthetic conformance ports. Available is not approval; fake judge does not prove semantic accuracy.
- Required review-context must be declared by the module, tied to the exact visible question and actually selected/checked-read. Hidden/denied question is not added through role metadata; cached now-denied material is technically rejected only after proper fresh capture, not forwarded. All-admitted R/other-module work/raw wrong run/technical failure distinction retained. Getter-based base approval or private revision values are never accessed.
- Actual MonitoringCore positive witness: fake judge1, checked source reads6, independent in-memory review proposals2 with exact proposal/policy/question/reply materials. Missing/unqualified link or missing required question read denies knowledge proposal while references can succeed. No canonical write, queue effects or actual business acceptance is inferred from receipts.
- Currentness composes admitted native/review/question revisions in existing lease/dependencies and observed monotonic sequence. Same-ID changed options/effects/proposal/native reply/cancellation/supersession revoke; normal open→answered bookkeeping, unrelated questions/root diagnostics and stable public data do not falsely invalidate. Observed ABA does not revive an old captured lease; unobserved changes still require honest owner revision discipline, not a new watcher.

### Actual checkpoints and residual limits

Unscoped checkpoint `lazy check` failed on a pre-existing other-workstream task318 local binary/NUL (2913files/2911checked), not this unit; it remains untouched and failure is preserved in checkpoint. Current earlier user-confirmed workstream boundary still applies: official owned --files7 check/standard, with full self-test retained and no global exclusion changes. This is not a claim of globally green all-changed-file validation.

Initial CPU34:33pass/1fail,93expectations/662ms. The failed cached-denial fixture reused an expired authority capture and correctly hit UNBOUND_AUTHORITY; NEW test now asserts that rejection, then re-prepares fresh deps to test no private forwarding. Failed-case-only recheck:1pass/33filtered/0fail,4expectations/188ms. Unique union34, not35 and not a single fresh34 run. Initial strict2 test-typing errors (optional expected ref/getter return annotation) fixed; final strict PASS. No implementation guard was weakened to satisfy the failed assertion.

Import/export probe PASS: new review exports3 (ReviewLinkError/captureReviewQuestion/createReviewLinkBinding), old question exports2 plus new readonly lookup, network0/invokedfalse. Controlled `review-link-controlled.json` records read6/proposals2/fakeCalls1/actualUiPresentedfalse; `review-link-affected.json` and `review-link-checkpoint.json` preserve checkpoint history; `review-link-standard.json` owns ONE final owned-file standard terminal. No repeated passing33-case run, SDK execution or changed old semantic24/24 score.

| Layer | Independent delta judgement |
|---|---|
| SDD | additive readonly question API/private explicit-review link, host-only vs public semantic-version fence and required checked question context; existing monitoring SDD updated |
| BDD | no actual question UI/presentation/reply collection/activation/Main injection/business flow enabled; synthetic explicit receipt only |
| SSOT | existing queue/close/native-source/grant ownership reused, no new approval registry/credential/config/SDK budget or altered queue close obligation |
| DDD | question identity ≠ reviewed semantic version, source/link availability ≠ actual approval; existing candidate/permission meanings preserved |

Discovery capture / Rule placement: this existing reliability record is one proof primary plus independent SDD interface delta. Exact edit/creating_source_file+modifying_source_file resolve is recommend-only code-organization baseline on new/narrow changed code, no untouched rewrite. Append-only kg_monitoring_review_link_* maps verified symbols/calls/protection/evidence, all legacy rows intact; implementation index explicitly stale for additions. Source contract is not a new global operating policy. Actual UI/presentation-reply source owner and any SDK qualification remain separately unapproved.

## C1 — current realtime ready offer → purpose handlers → independent execution result

User `좋아 진행해 얼른` approved this bounded next checkpoint, not the paused UI branch or compulsory search. NEW `.lazy-harness/scripts/monitoring-core-realtime-execution.ts` / NEW `tests/lazy-harness/monitoring-core-realtime-execution.test.ts`; no existing Core/A/B/observer/settled registry/router/provider/gold/auth/config/shared-loader source changed. No real SDK/model/worker/business/live invocation. Test-only Host targets produce bounded in-memory effects, not business writes.

### Implementation map and acceptance evidence

- Verified source-local class RealtimeExecutionConsumer and types RealtimeExecutionPorts/Invocation/Record/Limits. Host owns existing target registry/routing/version/grants/semantic input. New adapter checks current A/B candidate/body/batch/packet identity and current permission, forwards a frozen packet to an actual Host callback, reserves bounded physical identity before invocation, and reconciles the reused TriggerResult/TriggerInvocation contract. Old MaterialEnvelope requires a genuine settled source; it is deliberately not forged or rewritten for realtime.
- Actual CPU chain is existing createRealtimeSelectionPipeline→Window/A Coordinator/B SelectionBridge/Core checked material→new consume→two different registered target callbacks→independent effect ledger→exact execution/request/content/effect result. Positive: scripted judge1, targets2, independent effects2, selected material counts1/2, beforeAgentSettledtrue. No private canonical/system body or other module's policy/batch body/hash crosses a per-module callback. Third target configuration uses the same consumer/Core, no feature branches or hot-registration claim.
- Coverage includes run/skip/defer, exact/denied routes, existing conservative A/B whole-offer source revoke, malformed module isolation, tampered hash/batch identity, pending/completed duplicates/conflicts, redacted target error, rejected/unknown/mismatched/missing effect result, target-owned semantic input denial, stop-before-callback, caller/source/target-binding/grant revocation, observed grant ABA, ordinary-context survival, physical retention after logical abort, wait-only abort, lifetime/active/retained/byte/packet bounds and getter rejection.
- Post-green source review identified that a duplicate caller's separate abort must be checked at receipt time. Adapter now denies only the cancelled duplicate receipt while original physical work/effect stays valid. It does not claim a prior red test: first36 were green but did not cover this separate caller. New case plus affected existing duplicate case verified the change, without rerunning all passing36.

### Exact checkpoints and limits

Initial focused36 PASS/0FAIL/139expectations/549ms; initial strict PASS. Review change focused2 PASS/35filtered/0FAIL/13expectations/232ms (one old recheck+one NEW); final strict PASS.37 unique,38 testcase executions, NOT a single fresh37 run. Import probe exports exactly RealtimeExecutionConsumer, network0, instantiatedfalse. Original c1-controlled.json preserves the positive witness; c1-affected.json is separate. c1-checkpoint.json owns combined accounting; c1-standard.json owns ONE owned-file final standard terminal with SDK opt-ins/report outputs unset.

Counterexample limits: Host can lie about grant/source/routing/revision/receipt; no source-auth or sandbox claim. isCurrent must be checked by targets immediately before an effect; already committed/uncooperative effects cannot be undone. Caller/stop cancellation is signalled; arbitrary source/grant change is a checked guard, not a new automatic watcher. Per-module binding version discipline and explicit actual target operation deadline remain Host obligations. idle does not forcibly settle promises. Runtime source boundary/new real SDK/OAuth worker/semantic model accuracy/main injection/live action not qualified here. Search is optional; this is common execution wiring, not a new search/UI feature.

| Layer | Independent delta judgement |
|---|---|
| SDD | additive packet-native execution ports/lifetime/result contract; pi-monitoring-observation updated, generic Core/SDK public interface unchanged |
| BDD | no user UI, live collection, main-agent injection or business flow enabled; only CPU fixture callback/effect ledger |
| SSOT | existing Host routing/grants/revision and result ownership reused, no second registry/config/schema/credentials/budget authority |
| DDD | offered material ≠ actual callback ≠ verified controlled effect receipt ≠ external business success; existing domain meanings preserved |

Discovery capture / Rule placement: this existing TDD is the one proof primary with independent SDD contract delta. Exact creating_source_file/C1 policy resolve returned only recommend-level code-organization baseline; new source reviewed for narrow owner/local flow/lifecycle, no untouched rewrite. Source-local exports/dependency/protection graph7 appended, all legacy rows untouched; derived implementation index explicitly stale, exact source/MD/graph fallback. Separate workstream binary/NUL remains untouched and outside this unit; official owned-file checks retain full self-test without global exclusions. No new operating policy/capability or migrated legacy fact is claimed.

## Rule placement

- Rule: these are selected monitoring-component qualification conditions, realtime lifetime regression gates and experiment evidence boundaries, not a universal operating policy.
- Scope: layer-fact
- Primary record: `.lazy-harness/tests/monitoring-core-reliability.md`
- Why not AGENTS.md: module quality and benchmark contracts are not universal agent grammar.
- Why not local notes: shared reproducible component protection belongs in the harness records.
- Confirmation: user-confirmed
