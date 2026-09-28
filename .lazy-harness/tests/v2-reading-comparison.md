# TDD — V2 reading comparison preparation

## 후속 결과 연결 — 역사적 판정은 유지
- 이 문서의 본 비교01 결과 A1/3·B0/3은 그대로 보존한다. 마지막 절의 ‘투영 코드 미수정’은 당시 상태다. 후속 실제 수정과33개 집중검사 기록은 [요청 목록 투영 수정](v2-request-list-projection.md), 별도 변경 추적 비교03은 [후속 연구 정본](../planning/v2-change-tracking-reliability-plan.md)을 참조한다. 새 결과로 이 시험의 실패를 소급 통과시키지 않는다.


## Rule digest

- Status: advisory
- Layer: TDD
- Scope: host-project
- Aliases:
  - reading comparison
  - 읽기 비교 준비
- Applies when: Preparing or reviewing the approved staged V2 raw-record/digest pilot.
- Must: Preserve original research inputs/results; test deterministic offline mechanics before parent-controlled synthetic smoke and six-trial execution. Do not treat structural validation as semantic grading or model-runtime proof.
- Must not: Launch study models during preparation, repair original B or malformed answers, install/modify profiles or policies, or use a model/protocol fallback.

## Governing scope

`.lazy-harness/planning/v2-record-reading-comparison-plan.md` is primary planning authority, read in full including its final staged-exchange approval. The historical supervisor callback proposal is superseded. Preparation is confined to new `experiments/v2-reading-comparison/**` plus this TDD. Parent owns Planning/graph updates; existing dirty files are preserved.

Parent clarified the effective role is existing native `delegate`: independent minimal Git/input roots plus identical explicit read-only instructions and post-run complete trace verification, **not** an OS/tool-capability sandbox. Mutation-capable tools and normal runtime context may remain available. No unsupported per-call tools/fallback override or new profile is created. Fallback suppression and absence of research-context leakage require parent preflight evidence; missing metadata remains unknown.

## Protected contracts

- Source-request/final envelope and answers are runtime-validated without repair: exact keys/types/statuses, unique bounded requests, evidence basis/reference availability, answer limits and duplicate item IDs.
- One exact-ID lookup batch, at most three unique syntactically valid IDs; unknown IDs return only not_found. Recognizable malformed requests receive fixed invalid_request and consume the opportunity. Source data is copied, never executed. Second requests fail without another child.
- Initial answer and original initial runtime output are preserved before lookup; final initial_answer and requested IDs must match. Without lookup the two answers match.
- Per-trial300-second wall-clock budget; resume receives only the remaining time. Actual run IDs/references/artifacts and available native metadata are preserved for both stages. Six trials sequential S1A,S1B,S2B,S2A,S3A,S3B, <=12 child executions.
- Invalid environment/observed exposure outranks timeout; timeout outranks final format/content. No-final output, format failure, missing required items, and semantic-review pending are distinct.
- Original A/B byte hashes and per-source canonical-content hashes; evaluator key derived from raw final complete→verify→receipt with three hashes per file; key frozen before child input creation. Original B is byte-identical, not improved.
- Default generated scripts block pending preflight. Synthetic smoke contains no study answers; both generated scripts are self-contained standard JavaScript + runs.run only. Preparation CLI never invokes models and refuses existing output roots.
- Blinded/manual assessment packets remove arm/cost/order labels while preserving original results privately; deterministic checks never assign semantic pass.

## Implementation map

- `experiments/v2-reading-comparison/protocol.mjs`: `lookup`, `answerErrors`, `envelopeErrors`, `parseOutput`, `verdict`, `remaining`, `inspectRuntime`; shared pure mechanics compiled verbatim into sandbox scripts.
- `experiments/v2-reading-comparison/study.mjs`: `scenarios`, `order`, `prompt`, `answerKey`; current questions, identical arm instructions, evaluator-only expected meanings and raw chain derivation.
- `experiments/v2-reading-comparison/workflow-body.js`: chronological initial→snapshot→lookup→retained resume→assessment loop; actual native result retention and known-invalid stop.
- `experiments/v2-reading-comparison/prepare.mjs`: `loadSources`, `prepare`, `compile`, `preflight`, `verifyInputs`; exclusive output/independent input roots, hashes and workflow generation; no model launch.
- `experiments/v2-reading-comparison/assess.mjs`: `assessmentPackets`; preserves original collection and private provenance, produces deterministic manual-review packet and input rechecks.
- `experiments/v2-reading-comparison/failure-audit.mjs`: parent-only `auditFailure`/`auditFiles`, exact receipt→workflow step→original session linkage, raw byte/hash retention and conservative timeout-only classification; never compiled into child input.
- `experiments/v2-reading-comparison/runner.test.mjs`: dependency-free node:test fake runs/clock, original-session/native-metadata fixtures and offline preparation integration; actual model smoke is separate.
- `experiments/v2-reading-comparison/README.md`: commands, native source evidence, parent preflight and interpretation limits.
- Sources: `experiments/v2-luna-reader-01/records.json`, `experiments/v2-luna-reader-01/knowledge-candidate.json` (read only).
- Cross-layer: governing Planning above; `.lazy-harness/tests/test-strategy.xml`; `.lazy-harness/spec/platform/code-organization-profile.md` (creating_source_file policy/capability resolved, observe-only changed-source review).
- Machine graph/index: parent-owned update pending; no automatic graph or generated-index promotion by this worker.

## Validation evidence

Previous Fix2 bounded repair checkpoint: `node --test experiments/v2-reading-comparison/runner.test.mjs` — **18 passed, 0 failed, 0 skipped, 120.685934 ms**. Prior preparation checkpoint: 15 passed. Added receipt/inspection clock fixtures cover initial and resumed final receipt at299999ms with inspection completion at300001ms, format/invalid precedence, and an initial source request whose remaining resume budget expires during inspection (one launch only). `resultElapsedMs` now determines final deadline; total `elapsedMs` and `workflowProcessingMs` retain inspection cost. That prior checkpoint was 18 tests; its log has been superseded by the current failure-audit checkpoint. Tests include fake runs/clock and offline temporary-input generation, not actual models. No broad legacy harness regression or model CLI/workflow invocation. The user explicitly excludes unrelated policy-order full regression as a study blocker; standard validation would run that unrelated suite and is outside this approved focused checkpoint.

Current failure-audit checkpoint: same `node --test` command initially **23 passed / 1 failed / 0 skipped, 90.823036 ms** (`experiments/v2-reading-comparison/focused-test.initial.tap`). Failure: Node/V8 native Error.stack is a lazy accessor, so its original stack was not captured. Corrected only native engine getter handling; arbitrary overridden stack accessors remain uninvoked and a negative fixture protects this. Supervisor explicitly approved one corrective rerun: **24 passed / 0 failed / 0 skipped, 95.523453 ms** (`experiments/v2-reading-comparison/focused-test.tap`). No real runtime smoke/model launch or broad harness suite. Tests are offline fixtures, not six study trials.

## SDD/BDD/SSOT/DDD judgments

| Layer | Judgment |
|---|---|
| SDD | Experiment-only request/output/retained exchange contract already owned by approved Planning; no independent product API delta. |
| BDD | Experiment-only staged lookup and three scenarios already specified in Planning; no independent product-visible behavior delta. |
| SSOT | No independent config/ownership/policy delta; generated manifests are experiment evidence, not canonical runtime settings. |
| DDD | No independent domain vocabulary or business-rule delta; historical timeout requirements are read-only study inputs. |

- SDD: Experiment-only request/output/retained exchange contract already owned by approved Planning; no independent product API delta.
- BDD: Experiment-only staged lookup and three scenarios already specified in Planning; no independent product-visible behavior delta.
- SSOT: No independent config/ownership/policy delta; generated manifests are experiment evidence, not canonical runtime settings.
- DDD: No independent domain vocabulary or business-rule delta; historical timeout requirements are read-only study inputs.

## Historical native output blocker — prior repair scope (superseded below)

Supervisor narrowed this repair after source inspection: complete Fix2 only; do not redesign Fix1. No native-shaped success claim/fixture was fabricated for an unsupported raw channel. Existing format fixtures are offline protocol fixtures only.

Installed package `/home/lazydino/.pi/agent/local-packages/pi-subagents-readfix-1/node_modules/pi-subagents` evidence:

- `src/workflows/scripted-workflow.ts:2348–2358`: ordinary runs.run rejects failed children with a generic Error; only detached failure receives a typed marker. Mapping returned ok:false alone cannot solve native structured-output failures.
- `src/runs/background/subagent-runner.ts:1235–1248,1324–1348`: missing structured_output invocation fails the native run. Current outputSchema still invokes that requirement; format/no-output may be misclassified as infrastructure by the existing catch.
- `src/runs/foreground/subagent-executor.ts:3150–3181,4202–4295`: awaited async projection returns completed.output as finalOutput/top-level output and does not copy original messages.
- `src/runs/background/subagent-runner.ts:1461–1471` strips acceptance reports before persistence/display; `src/runs/shared/single-output.ts:finalizeSingleOutput` appends an inline saved-output footer. No verified original raw channel was established. No stripping, model JSON repair, error-string guessing, package change, or transport fallback was implemented.

Parent must resolve this exact output/failure contract and obtain further review before native static validation/smoke. Fix2's offline tests do not remove Fix1's BLOCK verdict.

## Approved failure-original audit implementation

The final 사용자 승인: 실패 원본 기록 사후 판정 in governing Planning supersedes the earlier Fix2-only restriction. Native object outputSchema successes remain; both stages explicitly require structured_output. Generic runs.run rejection and ambiguous/missing native payloads preserve trial/stage/stable key, raw exception properties/stack/cause, timing and any returned stage payload; collection stops with pending_native_failure_audit without an infrastructure/format/no-output guess. Successful receipt-time Fix2 and exhausted-resume-budget behavior remain protected.

Parent-only audit requires trusted original receipt workflow/key/latestRunId/continuation to match workflow status key/run/session and the operator's exact original session path before reading it. Full raw collection/metadata/session bytes and hashes are preserved without output scraping or repair. Only a linked failed timedOut step with consistent timestamps can receive provisional timeout classification; arbitrary native causes, normal model completion, format and no-output remain unresolved without further trustworthy evidence. Neither missing structured_output nor a failed status is normal-completion proof. No retry or automatic continuation; no runtime/package/profile/CLI changes. Source citations and audit commands are in experiment README.

Protected fixtures added: generic thrown initial/resume native errors; ambiguous metadata/missing payload stop; workflow/key/run/session mismatch rejects before read; original source/session bytes retained; known native timeout; ambiguous timestamps; no format/no-output attribution from error strings, displayed prose or missing structured_output; parent-only file report preservation and no overwrite. These are synthetic source-shaped metadata and session fixtures, not actual native run evidence.

Four-layer judgments for this approved narrow change:

- SDD: experiment-only snapshot/offline audit boundary implements approved Planning; no independent product API delta.
- BDD: stop-and-parent-audit flow implements approved Planning; no independent product-visible flow delta.
- SSOT: no config/profile/package/ownership delta; operator trust and original runtime artifacts remain authority, not model paths.
- DDD: no independent domain rule/vocabulary delta.

Discovery capture: this TDD is the sole worker-updated primary implementation/regression record; parent owns Planning/graph changes. No additional canonical promotion. Pending host migration remains separate: record-lint issues=1/advisories=0, legacy graph rows=37; guided migration can be resumed only with separate user approval, never auto-rewritten here.

## Limitations / remaining gates

Fake runs/clock prove generator logic, not native session fidelity, actual provider resolution or timeout cancellation. Parent must independently review code, confirm effective delegate model/fallback/tools/extensions/context, validate generated scripts through native tooling, run synthetic request→lookup→same-context resume smoke, inspect complete artifact traces and before/after input hashes, and perform blinded/manual meaning grading. Native metadata may omit messages/thinking; absence is pending, never success. Known invalidity stops later trials; artifact-only violations discovered later invalidate collection. Input top-level/hash checks are not a full filesystem or tool trace audit. Output schema is intentionally generic object-only; strict trial validation belongs to the runner, not native schema repair.

No actual six-trial result, semantic quality comparison, runtime smoke success or cost-saving conclusion is claimed. No profile/policy/installation/network/DB/commit change.

## Discovery capture / Rule placement

Primary implementation/regression record: this TDD; parent retains primary Planning and graph ownership. Approved contracts are implemented only in the experiment, not promoted into product rules or additional layers. Source organization preserves one chronological workflow owner and one shared pure validation authority; no untouched refactoring. Separate legacy graph migration remains outside this task and was surfaced to parent.

## 실제 합성 smoke01 — stopped_invalid, 재개 미실행
- workflow `accea2b1-ed47-41c2-8e71-d746855ff63c`, child `6ff86f6b-ed1c-4be5-a909-be9df9355ddb`. 최초 structured source_request는 반환됐으나 runner가 model_mismatch/model_fallback으로 중단. retained resume는 미실행; smoke 성공으로 세지 않는다.
- Parent가 원본 session의 model_change=`openai-codex/gpt-5.6-luna`, thinking_level_change=`medium` 및 assistant model을 확인했다. 실제 모델 변경/fallback 증거는 없고, native 결과 model/attemptedModels의 `:medium` suffix를 허용하지 않는 inspectRuntime 비교가 오탐 원인이다. 기존 invalid 원결과는 덮어쓰지 않는다.
- 별도 contract 문제: Planning은 item.evidence 배열을 요구하지만 common prompt는 evidence를 객체 표기로 설명했다. 실제 반환도 객체였고 item_shape 오류가 났다. 미제공 synthetic-card를 direct 근거로 든 표현도 원문에 보존한다. 답변을 배열로 고치거나 근거 유형을 사후 교정하지 않는다.
- 전체 원본 session에 모델 도구 호출은 read(input.json)1회와 structured_output1회. 입력 SHA256 불변. 생성 root `/tmp/reading-smoke-U2T8bX`에는 pi-lens startup 로그 `.pi-lens-probe-home/`도 생겼다. 확장 로그와 모델 파일쓰기 위반을 혼동하지 않으며 runtime tree/동등성 확인은 별도로 남긴다.
- 원본 status/receipt/session/collection, 당시 runner와 tracked diff/status: `.local/v2-reading-runtime-iInlC0/smoke-01-evidence/`. 약11.068초,2 model turns, child 비용$0.001641. 준비 비용이며 본시험 비용 아님.
- 후보 보완: 정확한 model+thinking 표현을 native contract대로 비교하고, 공통 prompt의 evidence 배열 명시를 canonical과 일치시킨다. 실제 payload 기반 회귀 검증 후 새로운 synthetic smoke로 재검증 필요. 현재 코드/원출력 자동 수정·재실행 없음.
- Discovery capture: TDD updated; SDD candidate(기존 출력 contract 표현 정렬), BDD no independent delta, SSOT no independent delta, DDD no independent delta, ADR no independent delta, Planning 기존 본시험 gate 유지. 모의검사/정적 독립 검수가 놓친 실제 연동 결함으로 보존한다.

### 사용자 승인 후 최소 보완 및 smoke02 준비
- 사용자 선택 ‘최소 수정 후 재검증’에 따라 parent가 protocol.mjs의 model/attemptedModels 비교에 정확한 Luna:medium 표기만 추가했다. 다른 suffix/provider/model은 계속 거부하고, 실제 thinking field가 없으면 pending을 유지한다.
- study.mjs의 공통 출력 안내에 item.evidence 배열을 명시했다. 원출력과 검증기는 느슨하게 바꾸지 않았다.
- 실제 smoke01 runtime 반환값을 `experiments/v2-reading-comparison/fixtures/smoke-01-native-runtime.json`에 source hash와 함께 보존하고 두 회귀검사를 추가했다. focused checkpoint26pass/0fail/86.204386ms, 로그 `.local/v2-reading-runtime-iInlC0/smoke-02-focused.tap`. lens cache는 해당 파일 진단이 없어 LSP 통과 증거로 세지 않는다.
- 새 generated root `.local/v2-reading-runtime-iInlC0/smoke-02/`. 변경2곳에 대한 독립 targeted review가 ready일 때만 새 합성 smoke를 실행하도록 같은 workflow에 묶었다. native 정적 validate ok. 기존24검사/이전review를 최신 변경의 검수로 대체하지 않는다. 본시험 gate는 smokePassed=false 유지.

### 실제 합성 smoke02 — 재개 연결 확인, 근거 검사 실패
- workflow `0f2b5e30-4295-4ab8-9fcb-091855233776`; targeted reviewer `7b717c7b-dfd2-4af5-beff-4a4038e5eeea` ready 뒤 initial `912bc16a-27bc-4719-b367-940b9ecfd52e` → resume `4f4a168f-6635-41b0-ac32-3071bb6f424c` 완료.
- 모델 오탐/배열 문제는 재현되지 않았다. 그러나 최초 답이 아직 받지 않은 synthetic-card를 direct 근거로 인용해 unread_direct_ref 발생. runner는 invalid_request를 회신했고, 모델은 재개 후 색을 모른다고 답했다. 요청 거절→동일 문맥 재개는 관찰했지만 exact source 전달→정답 연결 성공은 아님.
- 최초답 불변, 같은 native sessionFile/실제 Luna medium 유지, input SHA256 불변을 확인했다. 최초 timeout300000ms에서 재개287443ms로 감소. 전체25.864초, model turns3, 양 단계 비용 합계$0.00253884(child-only, 검수 제외). 기록의 errors3개는 동일 최초 근거 오류 재검사 및 최종 source_response 인용 검사를 포함하므로 독립 실패3건으로 세지 않는다.
- 전체 기록의 도구 호출은 read(input.json)1회와 structured_output2회. original workflow status/receipt/collection/session/inspection: `.local/v2-reading-runtime-iInlC0/smoke-02-evidence/`. 재개 workflow step에는 sessionFile이 누락돼 초기 수집 스크립트 KeyError 발생; 원본 runtime.results.sessionFile로 분석만 수행했다. status를 보정하거나 audit linkage gate를 우회하지 않았다.
- 현재 판정 fail/format_or_boundary. smokePassed=false 유지, 본시험0개. 원출력·채점 기준을 바꾸지 않는다.
- 다음 후보(미승인): 합성 연결시험의 최초 요청만 유효한 고정 JSON(items=[] 등)으로 명시해 자료 전달 경로를 따로 확인한다. 이는 본시험 질문/근거 규칙 완화가 아니며, 이번 자유 출력의 근거 실패는 별도 보존한다. Planning 후보이며 독립 도메인/설정/제품 flow 변경 없음.

### 사용자 승인: 고정 요청의 합성 연결시험03
- 사용자가 고정 요청으로 연결 확인을 선택했다. source-request의 최초 items=[]를 명시하고, 자료 도착 뒤 최종 color 항목을 답하게 하는 통제시험이다. 자발적 근거 판단 성공으로 해석하지 않는다.
- 본시험 common prompt/원본/검증 코드 변경 없음. parent-only `.local/v2-reading-runtime-iInlC0/build-fixed-smoke.mjs`가 기존 prepare/compile로 새 root와 fixed-manifest를 생성했다. 최초 고정 요청의 envelopeErrors=[] 확인, native script validate ok.
- script `.local/v2-reading-runtime-iInlC0/smoke-03/fixed-request.workflow.js`, 입력 root `/tmp/reading-smoke-exr9zg`. 원래 자유 출력 smoke01/02는 보존한다.

### 합성 연결시험03 결과 및 실패 회수 확인 준비
- workflow `9c7ac062-ef01-4539-a190-b44204e6153f`에서 고정 요청→synthetic-card(color=violet) 전달→같은 native session 재개→정확한 color/direct 인용을 확인했다. errors/invalid=[]; 부모가 최종 의미와 전달 원문 대조. 최초답/입력 불변, Luna medium 유지, read1회+structured_output2회.
- 전체19.431초, 재개 예산289682ms, model turns3, 양단계 비용$0.00215992(child-only). 증거 `.local/v2-reading-runtime-iInlC0/smoke-03-evidence/`. 고정 요청을 사용했으므로 자발적 근거 선택 능력 또는 A/B 품질 성공으로 일반화하지 않는다.
- 기존 승인된 원본 실패 회수 사전검증을 위해 별도 합성 native deadline5초 표본1회를 준비했다. `.local/v2-reading-runtime-iInlC0/timeout-smoke-01/timeout.workflow.js`만 test-only remaining budget5000으로 생성; runner/본시험300초는 변경하지 않았다. native validate ok. 이 표본은 모델에 실패를 가장시키는 것이 아니라 실제 타이머 종료와 원본 artifact 연결을 확인한다. 일찍 정상 종료하면 timeout 증거로 세지 않고 자동 반복하지 않는다.
- 본시험 gate는 아직 미개방. 실패 원문 회수·runtime metadata 동등성 확인을 마친 뒤 판정한다.

### 실제 timeout 원본 회수 확인 및 본 비교01 착수
- 예상된5초 timeout child `dc711221-49e6-4a7f-9e39-a7a8401a8f30`, workflow `c240604c-e6cc-4db3-a747-318a2b6fc761`가 pending_native_failure_audit로 중단되고 예외/시각을 보존했다. auditFiles가 원본 receipt/key/run/session을 연결하고 원본 session bytes를 회수했다.
- 자동 classifier는 workflow status에 endedAt/timedOut이 없어서 unresolved를 유지했다. Parent가 별도의 원본 child status에서 동일 run/parent/key/session, 명시 timedOut=true, failed, 시작/종료 시각 구간, processTerminal observed를 대조해 incomplete/timeout으로 별도 판단했다. 원래 status/audit를 보정하지 않았다. 증거 `.local/v2-reading-runtime-iInlC0/timeout-smoke-01-evidence/{audit,parent-classification}.json`. 보편 자동 분류 성공 주장은 아니다.
- 성공/실패 제어 시험과 최초·재개 tools/systemPrompt/context/launchResolvedExtensions 동등성을 확인했다. 기존 승인에 따라6개 본 비교를 준비했다. 준비 한계와 실행 전 결정: `.local/v2-reading-runtime-iInlC0/study-preflight-evidence.md`. 본시험은 고정 요청을 쓰지 않으며 원래 공통 질문/근거 규칙을 유지한다.
- 새 root `.local/v2-reading-runtime-iInlC0/study-01/`에 정답표·원본 입력 hash·6개 격리 cwd·script 생성, native validate ok. 순서 S1A/S1B/S2B/S2A/S3A/S3B; 최대12 child 실행. 수집 후 원본 trace·의미 정확성·비용을 판정하며 장애/미확정은 중단한다.

### 본 비교01 수집 완료 — 독립 의미 검수 중
- workflow `da4eb3d0-b0c7-4831-940f-c2e302b1034c`에서6조건/7child 실행 완료. S3B만 원문 요청 후 재개했고, 필수 evidence 필드 누락으로 invalid_request 응답을 받았다. 원답·실패를 고치거나 재실행하지 않았다.
- 구조 검사: S1A/S1B는 의미 검수 대기; S2A/S2B/S3A/S3B는 인용/필드/최초답 보존 규칙 오류로 fail. 중복 초기·최종 검사 오류 수를 독립 실패 수로 세지 않는다. 독립 content 판정은 아직 없음.
- Parent 원본 trace/child metadata 검사에서7실행의 동일 delegate/tool/context/launch extension 구성, 실제 Luna medium, 허용된 read(input.json)/structured_output 호출,6개 입력 SHA256 불변을 확인했다. 외부 연구 접근·모델 fallback·파일 수정의 관찰 증거 없음. OS 격리/ambient extension 부재의 증명은 아니다.
- 비용(실패 및 S3B 재개 포함, reported child usage): A3회$0.0136662; B읽기3회$0.01246992; 이전 소화비$0.00495008을 더한 B합계$0.01742. 준비·검수·부모 비용은 별도/미집계이며0으로 취급하지 않는다. 아직 소화 채택·절감 성공 결론 없음.
- 원본과 runtime audit: `.local/v2-reading-runtime-iInlC0/study-01-evidence/`; 독립 검수 packet: `study-01-assessment/blinded-packets.json`; 사전정답: `study-01/answer-key.json`. 새 reviewer workflow `af2ef4de-7b96-4afe-8497-8e0b2579072f`가 비용/arm mapping을 보지 않고 의미·근거를 검수 중(내용으로 arm 추론 가능).

### 独立 의미 검수 후 부모 교차 확인
- reviewer `2cabd381-ca7f-43b4-986f-0adf7d4ebfec`는 S1 두 답의 내용 정확성, S3 원문 답의 해시 비교 내용 정확성을 확인했고 S2 두 답/S3 소화본 답의 미완결 및 contract 실패를 구별했다. 최종 채택 기준 충족 주장은 불가.
- 부모가 검수 packet의 정보 손실을 발견: assess.mjs는 requested_source_ids를 요청 원문이 아니라 lookup.items에서 뽑아, 거절 응답이면 빈 배열로 보인다. 실제 S3B 첫 출력은 정확한3개 ID를 요청했고 재개도 그대로 보존했다. 거절 원인은 evidence 필수 필드 누락이다. 원본을 별도 `study-01-assessment/request-projection-clarification.json`에 제공했으며 원래 packet/응답은 덮어쓰지 않았다.
- S1B의 six_cases가 인용한 pointer에 기본값60이 없고 다른 item의 pointer에는 있는 점에 대해, 전체 답 내용 정확성과 item별 근거 충족을 구별해 재판정을 요청했다. 동일 reviewer retained challenge workflow `6b355500-9734-486b-a1db-da1ba93a4eaf`. 판정 숫자 최종 확정 전이며, 읽기 모델 재실행/정답 교정 아님.
- Discovery capture: TDD에 evaluator projection 회귀 후보와 판정 불확실성을 보존. 본시험 출력 contract/도메인/설정 변경 없음; 새로운 기준을 사후 추가하지 않는다.

## 본 비교01 최종 결론 — 채택 보류
- 독립 검수와 retained 정정 검수 완료: `2cabd381-ca7f-43b4-986f-0adf7d4ebfec`, `01e18e7e-396a-4cde-91e7-f4bd74e62b34`. S3B 요청 목록 결함 주장은 철회했고 S1B는 내용 정확성과 별개로 item별 근거 미충족을 적용했다.
- **사전 기준 완전 통과: A 1/3, B 0/3, 전체1/6.** 틀린 값을 답한 경우와 형식/근거 실패·필수 내용 미완결을 구분하며, 모든 답의 내용이 틀렸다는 뜻이 아니다.

| 상황 | A 원기록 | B 소화본 |
|---|---|---|
| S1 현재 입력 처리 | 내용·근거·형식 통과 | 내용은 맞음. six_cases가 인용한 pointer에는 기본값60이 없어 해당 주장 근거 실패 |
| S2 상한150 변경 | 핵심 방향은 맞지만 새 계획 보존 표현 누락 및 잘못된 완료 ID 인용 | 핵심 방향은 맞지만 필수 조건/후속 계획·이유 일부 누락, 읽지 않은 원문을 direct로 인용 |
| S3 세 기록 해시 대조 | 해시·연결 내용은 맞음. inference ref 및 조회 없는 최초/최종 답 일치 규칙 실패 | 필요한3개 ID는 정확히 요청. 근거 필드 누락으로 요청 거절되어 해시 대조 미완결 |

- A reported 읽기비$0.0136662. B reported 읽기비(재개 포함)$0.01246992 + 기존 소화비$0.00495008 = **$0.01742**. 이 표본에서는 소화비 포함 B가 약27.5% 더 컸다. 실패 표본을 비용 합계에서 제외하지 않았다.
- 준비/개발/검수/smoke/부모 비용은 위 금액에 포함되지 않으며 총액은 미집계다. 캐시·단가·출력 길이가 달라 이 차이를 소화 자체의 순수 효과나 일반 절감률로 해석하지 않는다.
- 결론: **현재 규격·입력·모델의 이3쌍에서는 품질 유지와 비용 절감을 동시에 입증하지 못했다. 소화 채택 판단은 보류한다.** 소화가 원천적으로 무용하다는 결론도 아니다.
- 확인한 것: 원기록/소화본을 분리한 실제6조건 실행, 동일 Luna medium·tool/context 구성, 정확한 source 전달/retained resume 제어시험, 실패 원문 회수와 부모 판정. 미확인: V1식 기록 생성 vs task-first 직접 비교, 반복 도메인, 지속 갱신·철회, 실제 코딩 효율, 장기 소화비 상각, 격리/병합/복구의 일반 성능.
- 남은 구현 후보: assess.mjs의 requested_source_ids 투영은 실제 요청 원문과 다를 수 있다. 이번 최종 판정은 별도 원본 확인으로 교정했지만 코드 자체는 미수정이다. 새 시험 전에 고칠 후보이며 기존 출력/packet을 덮어쓰지 않는다.
- Implementation map 추가: `fixtures/smoke-01-native-runtime.json`은 실제 suffix 사례와 원형식 실패를 보존; `runner.test.mjs`의 actual smoke01 / evidence arrays 검사가 회귀 보호. `.local/.../audit-study.mjs`는 이번 원본 trace/비용 집계용 재현 artifact이며 제품 기능이 아니다.
- Layer completeness: SDD=기존 실험 계약 적용/투영 회귀 후보, BDD=no independent delta, SSOT=no independent delta, DDD=no independent delta. Primary=TDD 결과, Planning에는 결론 링크만 둔다. 새 정책·데이터 소유권·제품 설계 채택은 없다.
