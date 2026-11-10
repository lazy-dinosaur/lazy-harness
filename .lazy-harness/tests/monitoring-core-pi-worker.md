# TDD — Source-local Pi worker Host adapter (offline protocol)

Status: experimental; offline and bounded native two-purpose Host-port consumption qualified; full C/D and server token budget unqualified
Layer: TDD

## Rule digest

- Status: advisory
- Layer: TDD
- Scope: host-project
- Confidence: medium
- Aliases:
  - Pi worker adapter
  - 실제 worker 연결부
  - offline worker protocol
- Applies when:
  - modifying or qualifying the source-local Pi worker adapter at the existing C1 Host execution boundary
- Must:
  - require explicit Host session admission and per-packet currentness, grants and binding revision
  - isolate in-memory worker resources/tools and expose only admitted material id/kind/version/text
  - require actual allowed read receipts, successful authoritative assistant message_end, matching SDK final text, schema AND Host semantic validation before target execution
  - retain raw creation/prompt/idle/abort and target work until physical settlement, including abort begun during cleanup
  - distinguish offline protocol proof from actual SDK/OAuth/model/provider request/token/cost and business qualification
- Must not:
  - infer actual worker qualification from a fake SDK/backend, valid JSON, acknowledgement or logical turn count
  - add Core purpose branches, another worker registry, public configuration/manifest changes or default live activation
- Related records:
  - `.lazy-harness/spec/platform/pi-monitoring-observation.md`
  - `.lazy-harness/ssot/monitoring-configuration.md`
  - `.lazy-harness/planning/monitoring-core-live-integration-plan.md`
  - `.lazy-harness/tests/test-strategy.xml`

## Approved slice and acceptance ledger

User selected the recommended step1 implementation/offline validation only (`ㅊ천대로 가줘`). Task130 owns it; task129 planning is complete. Do not repeat C1 CPU or task128 native-harness proof as new evidence. No real AgentSession/OAuth/provider/auth refresh/network/worker execution, real user data, business action or model-budget transfer was approved or performed. Source/API bindings are source-local experimental, not an installed/auto-loaded package feature.

- Factory construction does not discover configuration, load an SDK, create a session or invoke a model. Host explicitly supplies a Pi1.4-compatible SDK facade, model/runtime metadata, cwd/agentDir and session-admission callback; current global admission/grant/binding/source validity are rechecked and invalidity latches.
- SDK session recipe: explicit model/runtime, thinking off, only custom read_material active, empty discovered extensions/skills/prompts/themes/instructions, in-memory settings/history, automatic retry/compaction off and prompt expansion off. Unexpected active toolset or fallback-model warning prevents prompting. Wrong SDK/Host ABI is not supported by inference; Host/SDK honesty and native route remain a separate qualification.
- Worker sees a feature's instructions/schema and admitted material metadata, then exact allowed ID reads. Unknown/cross-module references, getters, exceeded read bounds and late post-cleanup reads reject without secret forwarding. Only id/kind/version/text crosses the material tool, not extra fields/provenance or entire packet/other-module state.
- Latest authoritative assistant message_end must have stopReason stop; error/aborted/length/toolUse, missing final or getter-vs-authoritative mismatch cannot promote partial/stale valid JSON into a target effect. Collect only bounded text; thinking content is not collected. Source parsing uses the existing bounded plain-JSON parser (effective parser ceiling128KiB; configured component bounds may be smaller), native typebox validation and strict Host meaning validation. No silent data truncation.
- Host resolveFeature owns feature identity/destination/schema/required material IDs/meaning and actual execute callback. C1 owns routing admission, execution/request/content correlation, deduplication and physical capacity. The adapter issues no second registry/queue, never takes effectId from model text, and only constructs the matching TriggerResult from an independently returned valid target effect receipt. Trusted effects cannot be rolled back after later revocation; no atomic business/sandbox guarantee.
- Raw session creation/prompt, idle/abort (including cleanup-time abort), disposal and target callback remain owned by the returned promise. Logical timeout/cancel does not recycle C1 capacity early. Worker is disposed before target work; failed cleanup stays unknown. Errors are fixed redacted codes. Logical maxTurns/read/byte/deadline guards do NOT prove actual model/provider request/token/cost caps.

## Actual validation capsule

Initial focused bootstrap failed before tests (0pass/1fail/1error,.055s) and TypeScript reported missing @sinclair modules. Corrected to the EXISTING native typebox/default Value imports matching repo/SDK; no install/manifest change. Initial31/124assertions/.309s green was not final: cleanup-time abort race was independently RED (1fail/.212s), then fixed by joining the newly started abort promise after cleanup idle.32/127/.267s passed. A second actual SDK-source inspection established getLastAssistantText can return unsuccessful/partial assistant text:4 non-success final regressions RED/.191s, then authoritative completion/text correlation added along with missing/stale-final protection. Preserve these failures, not first-pass-green.

Final affected offline suite:38 PASS/0FAIL,139 assertions,.281s, including two fixture purposes (counter/uppercase labels), third registration, explicit input/read/meaning/identity checks, allowed resources, output failures, permissions/revision/source/session-admission revocation, uncooperative creation/prompt/idle/abort, final-message status, cleanup, A/B→unchanged C1→new Host port→independent effect ledger and duplicate suppression. Direct source+test noEmit typecheck PASS with existing Bun/Node flags. Test report pi-worker-offline-focused.json records network0/actualSdkSessions0/actualModelCalls0/businessEffects0 and39 FAKE factory calls; fake calls are not native sessions. Actual OAuth/model/tool delivery is NOT qualified.

Final standard: PASS, actual task b9925818-4652-498f-9fa0-709792ece2ae exit0/436.54s; owned6 fast plus fresh framework91/skipped0/jobs4/errors0/cacheoff. Terminal `.lazy-harness/evidence/monitoring-core/pi-worker-offline-standard.json` and aggregate `.lazy-harness/evidence/monitoring-core/pi-worker-offline-checkpoint.json` own closure. Source/test hashes are unchanged from final38-case/typecheck snapshot. User-requested table→explicit four-layer bullet correction changed format only, not implementation/invariants; the four current judgements and final artifacts were read back. No full regression was repeated merely to update this capsule. Task130 step1 is offline-qualified after that readback, remaining[] within this scope; native SDK/OAuth model availability/request/token/cost/tool/effect consumption, actual worker execution and full C/D/live qualification are still separate and NOT approved by this completion.

## Actual worker run — direct execution approved; bounded synthetic trial

User rejected further proposal loops and explicitly directed actual results (`그냥 해보면 되잖아`, `빨리 진행`). Task131 executes only the already-described two synthetic-purpose worker trial, not a new global no-approval rule. Installed Pi1.4/local credential metadata identifies openai-codex OAuth gpt-6-luna chat/agent, not a Decisions classifier. Bounds:2 workers/4 SDK model dispatches/4 model HTTP requests/8 total HTTPS/120s/2 logical turns each; request1024 output tokens where supported and bound response bytes. No real user transcript, web/shell tool, business write, Core/guard/global setting change or old-budget transfer. The latest user direction supersedes the earlier step1-only boundary for THIS trial. Count actual transport and report unsupported token/invoice guarantees honestly; produce observed results, not another proposal.

Actual trial startup evidence: the first real SDK session was created, but the probe's fetch-accounting code treated the SDK's zstd Uint8Array request body as empty JSON. Actual first result:1 SDK dispatch attempt/1 session,0 HTTP/model HTTP,0 provider-reported tokens,0 target effects; WORKER_FINAL correctly withheld execution after the error. Preserve `.lazy-harness/evidence/monitoring-core/pi-worker-native-initial-failed.json`. Correct only the operational probe's bounded zstd inspection, leaving the ORIGINAL outgoing body/headers and source adapter unchanged. One controlled retry uses the same still-unused4 actual model-HTTP budget; bootstrap SDK attempts/session creations are counted separately and must not be hidden or relabelled paid requests. The current two synthetic-purpose inference cases remain pending; no success claim or new proposal loop.

Actual native result: controlled two-purpose Host-port consumption is 2/2 PASS after explicit Counter continuation. Real installed Pi1.4/openai-codex/gpt-6-luna OAuth agent called read_material for each own source, produced feature-specific input, passed authoritative final/schema/independent meaning checks, then executed each Host test target once with matching Host-issued request/execution/content/effect receipt. Labels: ALPHA BETA,4.399s,2 modelHTTP200,703 reported tokens. Counter:6 from abcdef,3.450s,2 modelHTTP200,705 reported tokens. Keep initial0-HTTP zstd bootstrap failure and expired-token401 failure, and normal SDK locked refresh200; do not relabel them successful or erase resource use. Cumulative6 SDK attempts/4 SDK session creations (incl bootstrap and expired401),5 modelHTTP (4success+1expired401),6 totalHTTP incl1refresh,1408 provider-reported tokens. Original4-SDK window and newly user-admitted2-SDK Counter window are accounted separately with no silent cap increase/old-budget transfer. These are synthetic Host-issued test correlations, NOT native SDK entry IDs or a full live native A/B/Core composition. No real user data/business action, source adapter/Core/guard change or prior green-suite rerun. Counter/Labels raw results and pi-worker-native-checkpoint.json passed/remaining[] are the final evidence after readback. Task131 completes this scoped actual-consumption qualification only. Requested1024 output cap is absent in observed Codex bodies: server-enforced token hardcap, invoice/OAuth quota, broader provider failure/cancel matrix and full C/D/main-context/live rollout remain explicitly unqualified.

Counter continuation approval/result: user `계속 진행해 얼른` admitted only a NEW Counter window1worker/2SDK/2modelHTTP/3totalHTTP/60s deadline. It actually used1 session/2SDK dispatches/2modelHTTP, both200, and passed expected numeric6 input/read/effect/receipt in3.450s. Green Labels/offline/full regression were NOT repeated. Its separate budget and prior ledgers are preserved; task132 blocker was merged into active131, not used to imply a fake completion. No further model execution is admitted by this result closure.

## Layer completeness

- SDD: independent semantic delta 있음. 신규 source-local Host worker/input/result API와 격리·최종응답·raw lifetime 계약은 `.lazy-harness/spec/platform/pi-monitoring-observation.md`의 Additive Pi-worker Host adapter 섹션에 반영·cross-link했다.
- BDD: no independent delta / 영향 없음. UI·사용자 동작·실제 관찰 또는 live consumer 활성화는 변경하지 않았다.
- SSOT: no independent semantic delta / 영향 없음. production schema·model 설정·credential 소유권/정책은 바꾸지 않았다. Step1은 auth/model 호출0이고, 별도 승인된 task131은 기존 OAuth를 사용해 SDK의 정상 잠금·refresh로 만료 token을 갱신했다(비밀값 미기록). 이는 운영 credential 회전이지 새 전역 설정/소유권 규칙이 아니다. 기존 `.lazy-harness/ssot/monitoring-configuration.md`를 재사용하며 component-local limits는 위 SDD 소유다.
- DDD: no independent delta / 영향 없음. judge/worker 역할, Host 기능 입력 소유권, 기술 receipt와 실제 효과의 구분은 기존 도메인 의미를 유지한다.

Format correction: 사용자 layer-completeness STOP에 따라 기존 4-row 표를 위의 네 개 명시적 layer bullet로 교정했다. 판단 내용이나 invariant는 새로 바꾸지 않았으며, 관련성만으로 다른 layer에 중복 서술하지 않는다.

## Implementation map

- `.lazy-harness/scripts/monitoring-core-pi-worker.ts`: verified exports PiWorkerSession/PiWorkerSdk/PiWorkerLimits/PiWorkerContext/PiWorkerFeature/PiWorkerHost and createPiWorkerExecutionPorts. SDK structural injection and one coherent execution lifecycle; no top-level SDK/session load.
- `tests/lazy-harness/monitoring-core-pi-worker.test.ts`:38 offline regression/Host composition cases. global fetch sentinel, no actual SDK import/session. Test-only PI_MONITORING_PI_WORKER_REPORT is an audit output, not a production model config.
- Existing `.lazy-harness/scripts/monitoring-core-realtime-execution.ts#RealtimeExecutionPorts` and `#RealtimeExecutionConsumer`: unchanged Host callback/raw ownership integration; existing model helper/router/Core/schema/guard/manifest untouched.
- SDD `.lazy-harness/spec/platform/pi-monitoring-observation.md` owns the independent experimental API delta; SSOT `.lazy-harness/ssot/monitoring-configuration.md` retains role/config authority. Planning owns approval/future native budgets only.
- Append verified source/symbol/protection/evidence rows in `.lazy-harness/knowledge/graph.jsonl`. Derived implementation-index is explicitly stale for these new symbols; no generator/global shared cache rewrite is claimed. Per storage SSOT, canonical MD/graph/source are the fallback until a suitable indexer regenerates it.

Discovery capture / Rule placement: this TDD is primary for implementation/regressions and one validation capsule; only independent component SDD updated. No new operating rule or extra DDD/BDD/SSOT narrative. Code-organization exact intent resolved recommend-only; new source stays chronological/local with one Host port owner; no untouched refactor or line-count split.
