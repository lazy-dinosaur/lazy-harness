# Jev Context Engineering and Background Monitoring Research

Status: requirements-forming
Layer: Planning

## Rule digest

- Status: advisory
- Layer: Planning
- Scope: transient-plan
- Aliases:
  - Jev context injection
  - Jev background monitoring
  - 스킬 프롬프트 자동 주입 연구
  - 백그라운드 소화 및 누락 감지 연구
  - Pi 관찰 코어
  - 확장 연결 코어
  - 모니터링 기능 배선
- Applies when:
  - discussing the separate research into Jev-assisted context selection and background monitoring during agent work
- Must:
  - preserve the user-confirmed research scope and distinguish it from implementation or live-execution approval
  - keep the other session's knowledge-module implementation and its owned records/source untouched
  - distinguish a suggested two-axis research framing from an approved module, process or deployment design
  - preserve the user-confirmed framing: plan an extensible observation/connection core first, with knowledge/work/context capabilities as downstream uses rather than implementing every feature now
- Must not:
  - activate injection, observers, model calls, digestion, DB persistence or new enforcement on the basis of this note
  - replace the existing static grounding transport with a semantic classifier without a separately reviewed and approved contract
- Record completion:
  - update this primary note when the user confirms requirements or resolves research questions
- Related records:
  - `.lazy-harness/planning/organic-hybrid-rule-guidance-plan.md`
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - `.lazy-harness/ssot/cli-tool-boundary.md`

## User-confirmed research scope

The user states that another session is building the knowledge module. This session is to consider a separate context-engineering and monitoring concern, using Jev to support the agent while it performs requested work. This captures the requested scope, not independent verification of the other session's current implementation status.

The user identified these intended capabilities for research:

- Supply relevant skills, prompts, rules and other needed content to the agent automatically when useful.
- Monitor work rather than limiting the concern to initial prompt selection.
- Identify material that should be written or organized and potentially use the digestion module in the background to organize and absorb it.
- Help the agent follow applicable rules and agreed plans.
- Detect omissions in expected database persistence while plans are being carried out.

The user explicitly says the Jev monitoring system should be considered first. This is not limited to conversation compaction or a skill-name router.

## User-confirmed core framing — 확장 기능을 연결할 배선 기획

작업 모듈 논의에서 사용자는 native 선택으로 `관찰·기록 기반부터`를 골랐다. 선택한 설명은 Pi 이벤트의 수집·정규화와 공통 관찰 코어, 작업 모듈의 이력/로그 API 연결을 먼저 설계하고 Jev 판단·자동 개입은 후순위로 두며, 이벤트만으로 Task 완료나 실행 승인을 판정하지 않는다는 범위다. 이는 기획 우선순위 확인이지 observer 활성화·구현 승인이나 최종 활용 범위를 관찰 기록에만 제한하는 선택이 아니다.

이어서 사용자는 이 코어를 여러 용도로 활용하려는 의도를 구체화했다.

- **지식 모듈 연계:** 자동 저장이 필요한지 판단하고 관련 영역의 지식/자료를 바로 가져올 수 있도록 한다. 관련 영역의 정확한 식별·조회/저장 API·정본 수락은 아직 계약으로 정하지 않았다.
- **업무/태스크 연계:** 업무가 어디까지 진행됐는지 자동으로 판단·체크하는 데 활용한다. 판단 결과와 실제 진행 변경·완료 수락은 같은 것이 아니며 자동 반영 범위는 미정이다.
- **컨텍스트 연계:** 입력을 받거나 동작/수행할 때 필요한 컨텍스트를 검색해서 적절한 위치에 주입하는 데 활용한다. 관찰 데이터 범위·검색 주체·주입 시점/대상·비용·실행 권한은 추가로 정해야 한다.

사용자는 다시 `여러 기능들을 활용할 수 있도록 선을 빼놓는다, 그 코어를 구상하고 기획한다`고 명시했다. 즉 현재 범위는 특정 자동화 하나 또는 기능들을 한꺼번에 구현하는 것이 아니라, 향후 여러 기능을 붙일 공통 연결 지점과 입출력 경계를 기획하는 것이다. 기존 Jev 연구 맥락은 유지하되 코어 자체가 특정 모델·항상 켜진 프로세스·거대한 plugin registry·별도 DB를 요구한다고 해석하지 않는다.

### 설계 검토 후보 — 구조/계약은 아직 미채택

- **관찰 입력:** Pi 등 runtime adapter가 실제 사건과 출처를 전달할 수 있는 경계.
- **공통 맥락/연결:** project/session/run/tool-call과 Job/Task 등 실제 식별 정보를 연결한다. 제공되지 않은 ID나 연결 관계를 추정해 만들지 않는다.
- **판단 연결:** 저장 필요성·진척·필요 컨텍스트 등 의미 판단을 LLM/searcher 또는 별도 판단 모듈에 요청하고 근거 있는 결과를 받을 경계. deterministic hook의 사용자 문장 분류로 대체하지 않는다.
- **기능 실행/반환:** 지식·작업·컨텍스트 모듈의 공개 연산을 호출하고 실제 결과/저장 영수증을 받는 경계. 판단 결과는 실제 저장·완료 수락·사용자 승인의 영수증이 아니다.
- **수명/안전:** 처리 중단·오래된 맥락·중복·자기 발생 이벤트의 재처리·권한·데이터 노출을 어떻게 구별할지 계약 검토 대상으로 둔다. 승인 범위의 자동화와 별도 확인이 필요한 동작을 구분해야 하나 구체 정책은 선택하지 않았다.

위는 기획을 구체화하기 위한 후보일 뿐 schema·public symbol·module 수·프로세스 배치·모델/observer/자동 쓰기·주입 활성화 결정이 아니다. 기존 static grounding transport와 다른 세션이 소유한 지식 모듈/G16 source·MainPlanning은 변경하지 않는다.

## User-confirmed engine direction — Pi / Fabric / Jev / 저가 생성 모델

사용자는 Pi에서 Jev와 Luna 또는 다른 저렴한 모델을 활용하는 모니터링·백그라운드 엔진이 필요하며 Fabric도 활용해야 한다고 명시했다. 이는 사용 기술의 방향과 엔진 기획 요구를 확인한 것이다. 특정 Luna 버전/provider, 모델 호출 빈도·예산·전송 데이터, 프로세스 수명·배포, observer/자동 쓰기·주입을 지금 활성화할 승인으로 확대하지 않는다. 앞선 관찰 기반 우선은 토대이며 최종 기능을 단순 이벤트 기록에 제한하지 않는다.

사용자는 추가로 `Jev로 판단이 되면 Luna가 해당 영역을 검색하여 필요한 작업을 하게 하는 기능`이 필요하다고 설명했다. Luna를 요약에만 한정하지 않고 검색·작업 수행 worker로 연결할 수 있어야 한다는 활용 요구다. 이는 모든 이벤트에서 두 모델을 호출하라는 뜻이나 저장/수정의 무제한 권한 승인이 아니다. 이후 사용자가 역할 설명이 혼란스럽다고 밝혀 전달문 작성·실제 전달과 세부 구조 확정은 보류하고 개념을 다시 맞추는 단계다. 이 발언은 요구로만 보존하며 정식 모델 계약·스키마·자동화/실행 승인으로 승격하지 않는다.

사용자는 관련 영역을 검색할 수 있어야 하고, 모니터링 중 이벤트와 각각의 내용을 자동으로 확인해야 한다고 추가로 확인했다. 이벤트 이름/발생 여부만 보는 것이 아니라 실제 내용·연결된 작업 맥락을 확인하고 필요한 관련 자료를 더 찾아 판단할 수 있어야 한다는 요구다. 자동 확인의 범위·원문 보관·접근 권한·모델에 전송할 자료·조회/호출 한도는 아직 결정하지 않았으며 전체 자료의 무제한 수집/전송 승인으로 해석하지 않는다.

사용자는 지식 저장·지식 조회·규칙 주입 등에서 Jev를 통한 정확한 상황판단, 즉 필요한 기능의 트리거가 가능해야 하는 것이 핵심이라고 재확인했다. Jev가 단순 이벤트명/키워드가 아니라 주어진 내용·작업 맥락·근거를 바탕으로 기능 필요성을 판정하고, 필요한 경우 Luna의 검색·작업 흐름을 시작할 수 있어야 한다는 제품 요구다. 정확성은 검증할 목표이지 이미 확보된 성능 보장이 아니다. PoC의 핵심 평가도 기능별 트리거의 적중·놓침·불필요 호출·판단 시점을 확인하는 방향으로 좁힌다. 독립적인 여러 필요가 동시에 있을 수 있고 없음/근거 부족/추가 조회/보류를 표현하는 판단 계약을 검토하되 구체 질문·후보·threshold·예산은 아직 정하지 않았다. 트리거 판단과 실제 자동 저장/완료 수락/주입 권한은 구별하며 모델·observer·자동화를 이번 확인으로 실행하지 않는다.

사용자는 모듈의 트리거별 처리가 병렬 실행되는 방향을 추가로 확인했다. 서로 독립적인 모니터링 기능/프로세서가 같은 사건에서 여러 트리거를 받아 동시에 처리할 수 있어야 한다는 요구로 보존한다. 이는 기존에 후순위로 둔 Job/Task 자체의 병렬 실행 정책을 자동 채택한 것이 아니며 트리거마다 무제한 worker를 생성하라는 뜻도 아니다. Jev의 독립 질문은 batch할 수 있고, 각 기능의 Jev→Luna 등 선후 의존성은 유지해야 한다. 처리 병렬성과 동일 작업/지식/세션에 대한 결과 반영의 충돌·최신성·중복·주입 예산 검증은 구분하는 방향을 검토한다. Fabric 실행 관리, 공통 호출/비용 한도, 취소·격리, 같은 대상의 반영 순서와 PoC 병렬 사례는 아직 세부 설계 후보이며 실제 병렬 프로그램/모델은 실행하지 않는다.

### 사용자 제안 후보 — 모듈별 감시 규약과 짧은 능동 보고

사용자는 코어에 붙이는 기능마다 무엇을 감시할지 규약을 자유롭게 붙이고, hook/steer/응답 시점에 원하는 목표 관련 정보를 한두 문장 태그로 보고하게 하는 방식을 제안했다. 현재 record judgement와 유사한 능동 보고를 관찰 입력으로 활용하는 아이디어로 보존한다. `있을 것도 같다`는 탐색적 제안이며 모든 현재 응답에 새 태그를 강제하거나 기존 hook/정책을 바꾸라는 승인으로 해석하지 않는다.

검토 후보는 **모듈 계약→활성 규약 전달→에이전트의 짧은 보고→실제 이벤트/영수증 대조→필요 시 Jev/Luna 후속 처리**다. 수동 이벤트 감시와 대체 관계로 확정하지 않고 함께 활용할 수 있는 후보로 둔다. 보고는 관측/수행 내용의 요약이지 비공개 추론 공개가 아니며 저장·검증·완료 수락의 실제 증거를 대신하지 않는다.

모듈 계약에서 검토할 항목:

- 감시 목적과 이벤트 범위: 언제 어떤 입력/응답/툴 결과를 볼지.
- 요청할 맥락/근거: 실제 event/work/goal version 참조와 허용된 조회 경로.
- 보고 형식: 한두 문장 summary와 근거 refs, unknown/추가 확인 필요 등 결과 schema.
- 보고 시점/예산: turn 끝/settlement/입력 변경 중 어떤 경계인지, 활성 모듈과 총 토큰 상한.
- 후속 판정/행동: 모델의 필요성 판단과 실제 허용된 모듈 API·검증 영수증을 분리.

Pi 1.3 InputEvent의 source와 streamingBehavior=steer/followUp를 현재 타입에서 확인했다. 별도 `steer` hook이 있다고 가정하지 않는다. 훅은 이벤트 전달·규약 전달·구조 검증을 담당할 후보이며 사용자 문장을 정적 키워드로 분류해 intent/저장 필요/다음 행동을 정하는 코드로 만들지 않는다. 어떤 기능이 필요한지의 의미 판단은 LLM/searcher/Jev 경계에 둔다.

전달할 보고 태그는 활성 모듈 결과를 한 컨테이너에 모으는 후보를 검토한다. 모듈마다 모든 응답에 무제한 태그/프롬프트를 붙이지 않는다. session/event/epoch 등 runtime 식별자는 코드가 실제 값으로 연결하며 모델에게 만들어내게 하지 않는다. 보고 없음/형식 오류/중단/근거 부족을 ‘할 일 없음’으로 취급하지 않는다. 인용문·툴 결과·외부 문서에 나타난 가짜 태그를 실제 assistant 보고로 파싱하지 않는 출처 경계도 필요하다.

에이전트가 보고를 빠뜨리거나 실제보다 완료를 주장할 수 있으므로 원본 사건과 실제 저장/실행 영수증의 독립 확인을 유지한다. Jev는 보고와 근거를 바탕으로 추가 점검을 판정하고 Luna는 필요한 검색·대조·작업을 하는 흐름에 활용할 수 있다. 자기 보고를 근거로 다시 자기 보고를 정본화하는 루프를 만들지 않는다.

PoC 후속 비교 후보는 순수 이벤트 기반 감시와 짧은 보고+실제 근거 검증의 트리거 적중/놓침·보고 누락·원문 재조회·추가 토큰·지연 비교다. 이 제안으로 모델/observer/새 prompt 주입·반복 hook·보고 의무를 활성화하거나 기존 PoC 범위를 확대하지 않는다. Scope=transient-plan, Confirmation=inferred-from-record. 기존 static grounding transport와 다른 세션 소유 source/MainPlanning은 수정하지 않는다.

### 권고 명료화 — 독립 감시가 주경로, 자기 보고는 보조 입력/평가 기준선

사용자는 외부 검토문을 공유하고 record-judgement형 자기 보고와 뒤에서 도는 독립 계층 중 무엇을 사용할지 물었다. 전달문은 현재 capture, v2 저장 경로, 직접 검색 대 Luna 검색 비교, 과거 세션 재생을 구분한다. 이 인용 자체를 실제 배포 상태·비교 실험 검증 또는 실행 승인으로 간주하지 않는다.

**현재 source에서 확인한 범위:** packages/lazy-harness-pi/extensions/lazy-harness/capture-evidence.ts의 complete/evaluate는 실제 성공 도구 영수증과 현재 파일 snapshot을 연결한다. required는 write, reuse는 read 영수증을 확인하며 semanticStatus=llm-judgement-not-verified, approvalStatus=not-evaluated를 유지한다. record-judgement의 의미 판단을 독립 Jev가 수행한다고 주장하지 않는다. packages/lazy-harness-pi/scripts/collect-runtime-usage.ts는 Pi 세션 JSONL을 파싱하고 assistant usage/cost를 집계한다. 완성된 검색 재생기·정답 평가기로 확대하지 않으며 providerRequestCount=null 등 집계 한계도 있다.

**추천 후보의 주종 관계:** 앞선 혼합형 추천은 보고 태그에 의존하는 주경로로 해석하면 안 된다. 주경로는 허용된 실제 이벤트/작업 맥락을 입력으로 하는 독립 모니터링이다. record-judgement는 작업자 의도/자기 판단을 알려주는 보조 입력이자 knowledge.capture 비교 기준선으로 유지한다. 공통화할 것은 모듈별 감시 규약·구조화된 판단/근거 참조·검증 영수증 계약이지 모든 판단 주체를 작업 에이전트로 통일하는 것이 아니다. 응답 끝의 보고는 그 응답 전에 필요한 검색을 유일하게 시작하는 신호가 될 수 없다. 보고 누락/미완성에도 별도 관찰은 가능해야 하며 실제 제때 도착 가능성은 측정해야 한다.

‘은닉’은 사용자에게 감추는 자동화가 아니라 작업 수행과 분리된 백그라운드/비차단 처리를 뜻하는 후보로만 쓴다. 활성 모듈·판단 이유·근거·호출량/비용·중단 상태는 관찰 가능해야 한다. 독립 감시가 매 이벤트마다 Fabric/Luna worker를 새로 띄운다는 뜻도 아니다. 정적 hook은 관찰·전달을 하고 의미 판단은 LLM/Jev로 두며, 검색은 기존 소유 검색 API/SearchProvider를 재사용하는 방향이다.

**전달문에서 수용할 검토 후보:** context.retrieve를 첫 대상으로 두고 직접 검색→Jev 선별과 Luna 검색/읽기 경로를 같은 조건에서 비교한다. 직접 경로가 충분하면 Luna를 긴 원문 해석/복합 검색에 쓰는 안을 검토하되 승자를 미리 정하지 않는다. record-judgement와 독립 Jev capture의 불일치가 Jev의 정답을 뜻하지는 않으므로 사람의 라벨/실제 원문으로 대조한다. 전달문의 v2 원장/Luna/Jev 구현 주장과 Reader 47.6%·조각 81% 수치는 이번 읽기로 검증하지 않았으며 이를 확인된 성능/현재 API 계약으로 저장하지 않는다.

오프라인 재생→실제 세션 shadow 순서를 검토하되 시점 t에서 이용 가능했던 이벤트·보고·지식/index 버전만 사용한다. 응답 후 judgement, 이후 저장된 지식, 현재 수정된 파일을 이전 시점 검색에 쓰지 않는다. 과거 턴 간격을 이용한 도착 평가는 live 스케줄링/주입 지연의 실증이 아니므로 실제 shadow에서 별도 확인한다. 자료·정답·수용 기준·모델/provider·외부 전송·호출/비용 예산이 정해지기 전 실제 세션 수집/재생·모델 호출·주입/저장 자동화를 하지 않는다.

Discovery capture / Rule placement: 기존 Planning primary에 권고의 주종 관계와 전달문 검증 범위를 명료화했다. Scope=transient-plan, Confirmation=inferred-from-record. 채택 결정·실행 승인은 아니며 현재 record-judgement/hook/관찰 코어나 다른 세션 소유 v2 source는 변경하지 않았다.

### 추가 세션 참고 — 대조군 유지 후 선택적 자기 보고로 전환하는 후보

사용자는 다른 세션의 의견을 참고 자료로 전달했다. 제안은 독립 백그라운드 감시를 기본으로 두고, record-judgement는 PoC/그림자 단계에서 대조군으로 유지한 뒤 충분한 검증과 별도 전환 승인 후 필수 envelope 지시를 제거하고 선택적 직접 보고만 남기는 순서다. 사용자의 직전 ‘이 방향으로 해볼까, 테스트 먼저인가’ 질문과 함께 테스트 우선 논의로 보존한다. 참고 전달을 현재 prompt/hook 의무 해제나 실제 세션/모델 실험 승인으로 취급하지 않는다.

- **현재/첫 검증:** 첫 대상은 context.retrieve의 오프라인 비교 후 실제 shadow다. 현재 record-judgement는 유지하며 검색 발동의 필수 신호로 만들지 않는다. 검색 PoC 성공만으로 저장 감시의 품질이 입증되거나 envelope를 제거할 수 있는 것은 아니다.
- **별도 저장 검증:** knowledge.capture가 추가되면 같은 시점·같은 허용 맥락에서 작업자 보고와 독립 판단을 비교하고, 사람의 정답/사용자 원문/실제 근거로 함께 놓친 사례와 불필요 후보도 평가한다. 대조군을 포함한다거나 더 많이 생성한다는 이유만으로 더 정확하다고 수락하지 않는다. precision/recall·추가로 잡은 유효 후보·잡음·지연·호출/비용을 함께 본다. 수치/표본/허용 한도는 미정이다.
- **전환 후보:** 기준을 충족하고 별도 승인을 받은 다음에만 강제 보고 지시를 줄이는 변경을 검토한다. 선택적 직접 호출은 명시적 의도/후보 신호이지 사실 확정·최종 저장·권한 승인 자체가 아니다. 전달문에서 말한 v2 knowledge_record의 제공 위치/효과는 실제 계약을 확인한 뒤 연결해야 한다. 이번 packages 범위의 exact name 검색에서는 찾지 못했으며 부재를 증명한 것은 아니다.
- **관측성/복구:** 독립 감시도 누락·취소·초과 예산·전송 실패가 있을 수 있다. ‘매번 돈다/빠뜨리지 않는다’는 검증할 목표이며 보장으로 쓰지 않는다. 이벤트 수신/처리/미처리 상태와 판단 근거·비용·중단을 사용자가 확인할 수 있어야 한다. 에이전트의 비공개 내부 추론은 수집하거나 사실 확정 근거로 요구하지 않는다.
- **근거와 질문:** 사용자 원문은 요구·교정·결정의 권위를 제공하며 구현/실행 사실은 코드·실제 tool/test 영수증과 구분한다. 근거가 비어 있는 비긴급 이유/선호는 세션 마무리 확인 목록 후보로 보류하되 권한·안전·파괴적 변경·중대한 사실 충돌에 필요한 확인까지 뒤로 미루지 않는다. 현재 ask_user/queue/hook는 활성화하지 않는다.

전달문의 ‘Delivery, Not Storage 114턴’과 ‘v2 knowledge_record가 이미 있다’는 이번에 검증한 실험/구현 사실이 아니라 인용된 주장으로만 둔다. 독립 감시/전환의 필요성을 그 수치 하나로 입증했다고 하지 않는다. current record-judgement를 제거하는 source/config/가이드 변경은 하지 않았다.

Discovery capture / Rule placement: 기존 Planning primary에 비교 단계와 선택적 보고 전환의 후보·보완점을 모았다. Scope=transient-plan, Confirmation=inferred-from-record. 새 운영 규칙을 적용하거나 첫 PoC 범위를 확대하지 않았으며 테스트/세션 수집/모델 호출·상주화·저장/주입은 아직 실행하지 않았다.

### 착수 capsule — 합성자료 실측 선택, 검색 계약/예산은 선택 대기

사용자는 `좋아 진행해봐 한번` 이후 native 옵션에서 **합성자료·실제 모델**을 선택했다. 이 선택은 user-confirmed로 보존하고 다시 묻지 않는다. 과거 개인 세션/민감자료 수집, 지식 DB 쓰기, 실제 컨텍스트 주입, 현행 record-judgement 제거는 범위 밖이다.

착수 조사에서 현재 root에는 Pi 확장/세션 사용량 파서가 있고, Fabric 모델 목록에서 openai/gpt-6-luna와 Jev classifier 후보를 확인했다. 모델 목록 등재는 인증·실행 성공이나 가격 확인을 뜻하지 않는다. 분류/생성 요청을 실행하지 않았고 검색 API도 호출하지 않았다.

G16 소유 세션에 현재 root의 공개 검색/비영속 합성자료 계약을 문의했다. 소유 세션은 현재 root record에서 public context.retrieve 계약을 검증하지 못했다고 답했고, 별도 G16 worktree 내부를 근거로 대신 제시하지 않았다. 제시된 map-first-retrieval/project-map-v2/project-navigation은 navigation cue이지 확인된 retrieve API 계약이 아니다. Parent는 sibling worktree를 읽거나 변경하지 않았다. 따라서 A를 v2 임베딩+trigram 검색으로 가장해 실험하지 않는다.

추가 선택 게이트는 ① 고정 합성 코퍼스에서 Jev 단독 선별 대 Fabric/Luna+Jev 선별로 한정해 판단·연결을 먼저 실측, ② 현재 host SearchProvider 계약을 더 확인, ③ v2 공개 계약 대기 중 범위와, 가격/비용 상한 확인 대 최소 작업 수 허용 등 예산을 물었다. **이 추가 질문은 시간 초과되어 응답을 받지 못했다.** 어느 항목도 자가 선택하지 않았고 최초 합성자료 실측 선택을 번복한 것으로 취급하지 않는다.

현재 상태=needs-option-gate. TODO 28은 진행 중이며 TODO 29(비교 대상·호출 예산 확정)에 blocked다. 실제 Jev/Luna 추론·검색 호출·세션 수집·테스트 실행은 0회이며 실측 결과/성능 수치가 없다. 기존 code/config/runtime와 G16 source/DB는 변경하지 않았다. 다음 재개 시 확정할 것은 변경된 비교 대상과 집행 가능한 모델/작업 수·비용 상한이지 이미 답한 합성자료·실제 모델 여부가 아니다.

Discovery capture / Rule placement: 기존 Planning primary에 착수 선택과 실험 미실행 사유를 한 capsule로 보존한다. Scope=transient-plan, Confirmation=user-confirmed(합성자료 실측 선택만) / pending(대체 비교·예산). 구현·모델 실행 완료를 뜻하지 않는다.

### 직접 구현 확인 보완 — 현행 검색을 v2로 오인하지 않기

사용자는 준비 조사만 보고받은 뒤 `제대로 해봐야지`라고 지적했다. Parent는 기존 소유 세션의 API 미확인 답변만으로 끝내지 않고 현재 root의 실제 소스/records를 추가로 읽었다. .lazy-harness/scripts/search-provider.ts의 SearchProvider.search/SearchQuery/SearchResult와 DirectAISearch.search를 확인했다. DirectAISearch는 terms의 문자열 포함 여부와 매치 비율로 후보를 만들며 의미 판단은 호출자에게 둔다. SubagentSearch.search와 RAGSearch.search는 not implemented 예외를 던진다. 이를 v2 임베딩+trigram 검색의 구현/성능으로 제시하지 않는다. project-map-v2.md와 project-navigation.md 역시 공개 retrieve API 계약의 증거가 아니다.

native 게이트에 구체 실행 profile을 제시했다: ① 현행 검색 provider+합성자료의 실제 평가기/테스트와 Luna·Jev 실측(모델 요청 최대20회·사전 계산 비용 USD1, 가격/호출 상한을 집행할 수 없으면 실제 호출 중단; v2 성능으로 보고하지 않음), ② 평가기·모의 테스트 준비만, ③ 원래 v2 계약 공개를 기다려 비교 유지. 이 선택 질문은 300초 시간 초과로 결과를 받지 못했다. 어느 profile도 자가 선택하지 않았다. 앞선 합성자료·실제 모델 선호는 유지하되 대체 검색 경로/예산은 여전히 미확정이다.

기존 검색 소스·기록과 Fabric 실행 옵션을 읽은 것이 이번 실제 진행이며, 아직 PoC 파일 구현·테스트 실행·분류/생성 호출·성능 측정은 하지 않았다. 구현/실측 완료로 주장하지 않는다. TODO 28/29와 needs-option-gate 상태를 유지한다. 현재 envelope·runtime·지식/세션 데이터·타 worktree 변경 없음.

Discovery capture / Rule placement: 같은 Planning primary의 착수 capsule에 직접 확인한 구현 사실과 미실행 상태를 보완한다. Scope=transient-plan; user-confirmed 범위와 아직 응답 없는 실행 profile을 분리하며 별도 운영 규칙/승인을 만들지 않는다.

### Offline PoC

사용자는 구체 실행 profile(현행 검색+합성자료, 모델 요청 최대20·사전 계산 USD1, 집행 불가 시 실제 호출 중단) 제시 후 `계속 진행해야지`라고 지시했다. 직전 기본 권고 1번 범위의 실행 승인으로 수렴하며 다시 승인 질문을 반복하지 않는다. v2 자체의 품질·상주 코어 구현·기존 envelope 제거·실제 세션/DB/주입 변경 승인은 아니다.

오프라인 실험 코드를 실제 구현했다. A는 기존 DirectAISearch를 별도 합성 cwd의 `.lazy-harness/domain`에서 그대로 실행한 후보→Jev, B는 같은 시점 코퍼스의 catalogue와 search_records/read_chunks/finish_selection을 받는 유한 Luna SDK tool loop→Jev다. 새로운 검색 알고리즘은 구현하지 않았다. gold는 fixture 작성자가 호출 전에 정의했으며 사용자/독립 평가자가 라벨링한 production benchmark가 아니다. B는 **fabric_exec→pi.bash로 관리되는 bounded SDK worker**이며 Fabric agents.run 부트스트랩/전체 Reader-hop 오버헤드 실험으로 포장하지 않는다.

실제 진행: `lazy check` 성공. 보호 테스트는 최종 20개/0실패/717ms이며 모델 profile의 정확한 바인딩·대체 금지와 실제 C17 검사도 포함한다. direct provider 준비 probe를 실행했고, live-01의 출력 상한 사전 차단과 live-02의 미정산 예약액 차단을 감추지 않고 보존했다. 공시 최대 출력의 선예약, 완료·양수 usage만 정산, 미확인 usage 보수적 유지, 동일 fixture/누적 원장 재개를 구현했다. 첫 standard 검증은 428초 후 doctor D06/C17 때문에 실패했다: PoC runtime의 공급자 식별자 literal 3곳이 원인이었고 모델 실측 오류는 아니었다. doctor/규칙을 완화하지 않고 모델 선택을 실험 models.json에 분리했다. binding-check-01은 실제 SDK에서 같은 바인딩·8개 완료 branch·누적17요청을 재확인했고 새 추론은 0회였다. 마지막 변경 뒤 standard를 재검증하며 최종 결과는 실제 runtime capture/검증 artifact에 둔다.

실측 최종 결과: live-03=completed, 4사례×2경로=8 branch 완료. 직접 검색→Jev는 exact3/4·성공 시도 평균308.88590875ms, Luna 도구 읽기→Jev는 exact4/4·평균9599.31571775ms. 직접 경로는 의도적으로 넣은 release/배포 동의어 사례를 놓쳤고 Luna 경로는 찾았다. 누적 metered HTTP17회=Jev5+Luna12, 8235 tokens, SDK 견적 USD0.000832502(청구서 검증 아님), 최종 정산 예약 USD0.000832502. 원래 20회/USD1 한도를 올리지 않았다. 지연은 완료 시도 기준이며 초기 실패·프로세스 시작·전체 agents.run hop/실제 다음 턴 도착률의 측정이 아니다. 4개 fixture-author 라벨과 미보정 threshold0.5의 작은 연결/자료선별 실험이며 production 정확도, 자율 트리거 필요성 판정, 저장/주입/상주화를 입증하지 않는다. ‘직접 검색 기본·필요 시 Luna 추가’는 다음 검증 가설이지 채택된 정책이 아니다. C17 수정 후 실측 자체를 재실행하지 않고 설정 동등성만 무추론으로 확인했다.

### Implementation map — experimental offline PoC

- `.lazy-harness/scripts/monitoring-retrieval-poc.ts`: 재생/평가/명시적 CLI. visibleChunks, buildState, directCandidates, parseSelection, measure, Budget, outputTokenBound, resolveModelBindings가 시점·근거·예산·설정 경계를 소유한다. 공급자 선택은 설정으로 주입하고 SDK entry는 CLI로 명시한다. 인증정보를 출력/복사하지 않는다.
- `tests/lazy-harness/monitoring-retrieval-poc.test.ts`: 미래 버전 차단, gold 비노출, 실제 provider 격리, lexical miss, 허구/중복/미독해 선택 거절, 사전 예산, tier, 재개 원장, 출력 한도 fallback 보호.
- `.lazy-harness/fixtures/monitoring-retrieval-poc/fixture.json`: 소유권/팀 규칙/동의어/무관련 4개 합성 사례와 미래 버전 sentinel, 호출 전 expected IDs.
- `.lazy-harness/fixtures/monitoring-retrieval-poc/models.json`: 이번에 승인된 두 모델의 provider/id/api 바인딩만 담는 실험 설정이다. production 모델/인증 설정이 아니다. `.lazy-harness/evidence/monitoring-retrieval-poc/binding-check-01.json`은 SDK 바인딩 동등성 및 새 추론 0회 확인이다.
- `.lazy-harness/evidence/monitoring-retrieval-poc/prepared-01.json`: 실제 provider/snapshot 준비 결과. `.lazy-harness/evidence/monitoring-retrieval-poc/live-01.json`, `.lazy-harness/evidence/monitoring-retrieval-poc/live-02.json`, `.lazy-harness/evidence/monitoring-retrieval-poc/live-03.json`: 첫 실패·비용 예약 차단·최종 완료와 누적 원장. 준비/실패 artifact를 성공 결과로 덮어쓰지 않았다.
- `.lazy-harness/knowledge/graph.jsonl`: kg_monitoring_retrieval_poc_runtime_v1 / guards_v1 / fixture_v1이 구현·보호 테스트·fixture의 확인된 edge다. 이번 작업에서 만든 초기 envelope 3개만 명시적 supersession으로 metadata를 보완했고 기존 host legacy row는 변환/삭제하지 않았다.
- generated implementation index: 생성기가 아직 제공되지 않는 현행 SSOT 상태를 유지한다. 캐시를 수작업으로 canonical처럼 작성하지 않는다.

| Layer 판단 | 이번 independent delta |
|---|---|
| SDD | production/core 공개 API 변경 없음. 실험 내부 SDK/provider adapter만 추가. |
| BDD | 실제 사용자 flow·주입·세션 동작 변경 없음. |
| SSOT | 기존 모델/인증/설정/소유권 변경 없음. 실험 한도만 이 작업에 한정. |
| DDD | 실제 도메인 규칙 변경 없음. 합성 사례는 host 업무 사실이 아님. |

Discovery capture / Rule placement: 같은 Planning primary에 승인 범위·실제 구현·보호 테스트·실측 진행을 한 capsule로 수렴했다. Scope=transient-plan; 실행 승인과 품질 수락을 분리한다. 최종 standard 검증은 마지막 mutation 뒤 1회 실행한다.

### 목표 재확인 — 공통 코어와 기능을 붙이는 활용 규약

사용자는 `우리는 코어를 만들고 이거 활용법을 만드는 것`, `이걸 활용해서 여러 가지 붙일 수 있게 되는 것`이라고 제품 목표를 재확인했다. **주 산출물은 확장 가능한 독립 모니터링 코어와 그 코어의 연결 규약/사용법/참조 예제**다. 검색은 코어를 이용하는 첫 검증 사례이지 검색 엔진 최적화 자체가 제품 목표는 아니다. 검색 정확도/지연/비용을 계속 개선하는 것을 공통 코어 구현의 진행 기준으로 바꾸지 않는다.

**참조 예시의 신뢰성 요구(user-confirmed):** 사용자는 어떤 예시를 붙이든 신뢰도가 있어야 하며, 다만 완벽한 100%일 필요는 없다고 명시했다. 목표는 등록/연결 데모나 우연한 성공이 아니라 해당 기능의 정해진 사용 범위에서 반복해 활용할 만한 실용적 신뢰성이다. 모든 상황의 무오류나 모델 confidence 숫자 자체를 신뢰성 보장으로 요구하지 않는다.

검수 구체화 후보(inferred): 필요한/불필요한/애매한 상황과 실패·지연 사례에서 실제 공통 코어를 경유한 판단·근거·후속 동작을 대조한다. 단순 모의 처리기의 등록 성공은 공통 실행 기계 검증이고 실제 기능의 의미 판단 신뢰성을 대신하지 않는다. 4개 합성 사례의 정답 일치도 production 신뢰성 수락 근거로 확대하지 않는다. 정확도·놓침·불필요 작동과 비용/시점을 목적별로 평가하고, 근거 부족은 추가 조회/보류/미확인으로 드러내며 오류를 추적·수정할 수 있어야 한다는 방향을 검토한다. 권한·예산·오래된 결과·중복 반영 같은 코어 보호 경계는 의미 판단의 불완전성과 구별해 엄격히 검증한다.

아직 사례 구성·독립 정답·수용 수치·오류별 허용 범위는 확정하지 않았다. 90/95% 같은 임의 숫자를 합의된 기준으로 만들지 않으며, 이 이해 확인을 추가 구현·실측·모델 비용의 승인으로 처리하지 않는다. Rule placement: 같은 Planning primary의 제품 품질 요구; Scope=transient-plan, Confirmation=user-confirmed(실용적 신뢰성/100% 불요), 세부 평가 방법=inferred.

이 재확인 당시에는 현행 검색 provider·Jev·Luna의 고정 두 branch 오프라인 실험만 완료됐고 공통 코어는 없었다. 이후 사용자의 ‘좋아 맞춰서 진행’ 승인으로 공통 코어 v0·서로 다른 참조 모듈·사용 가이드를 구현했다. 현재 컴포넌트 계약과 검증의 primary는 `.lazy-harness/spec/platform/monitoring-core.md`, 활용 가이드는 `packages/lazy-harness-pi/examples/monitoring-core/README.md`다. 라이브러리/합성 참조 검증이며 실제 Pi 훅·상주화·DB/주입·기존 envelope 변경을 뜻하지 않는다.

공통 코어의 다음 검수 기준 후보(inferred, 구체 설계/실행 승인 아님):

1. 기존 공통 계약으로 표현되는 기능은 코어의 기능별 if/else를 고치지 않고 등록·교체·제거할 수 있어야 한다. 새로운 공통 능력은 별도의 검토/승인된 코어 확장으로 다룬다.
2. 모듈이 감시 시점/목표·필요 맥락/조회·Jev 의미 판정 질문/결과 형식·후속 동작/권한을 선언하고, 코어는 수신/출처·등록/전달·실행/예산/취소·검증/영수증의 공통 책임을 맡는 방향이다. 특정 기능의 의미 판단을 hook 키워드나 코어의 하드코딩으로 옮기지 않는다. 모든 기능을 항상 Jev→Luna라는 같은 호출 수/작업으로 고정하지 않는다.
3. 서로 다른 두 참조 모듈을 같은 입력/등록/반환 경계로 붙여 코어 재사용을 확인하고, 이후 기존 계약 안의 세 번째 모듈을 코어 수정 없이 추가하는 예로 활용법을 입증한다. 실제 지식/업무 사업 로직을 한꺼번에 구현할 필요는 없다.
4. 독립 트리거 처리의 병렬성·한 모듈 실패 격리·공통 호출/비용 한도·오래된 결과/중복/stop 뒤 반영 방지·사용자에게 보이는 판단/미처리 상태를 검증한다. 판단 제안과 실제 수락/반영 영수증을 분리한다.
5. ‘모듈 하나 붙이는 법’ 문서와 최소 참조 구현을 코어와 함께 산출한다. 구체 공개 API/스키마·배치·파일 구조는 기존 후보를 검토한 뒤 확정하며 미구현 심볼을 현재 API로 설명하지 않는다.

이 발언은 목적/진행 기준을 맞추는 요구 확인이지 코어 구현안·상주화·추가 모델 비용·기존 envelope 제거의 실행 승인이 아니다. 기존 지식 v2 소유 경계를 유지하고, 특정 검색 API가 미확인이라는 이유로 공통 코어/사용 계약 검토 전체를 막거나 대체 검색 실험을 코어 목표로 삼지 않는다. Discovery capture / Rule placement: 같은 Planning primary에 사용자 목표와 PoC/본 구현 경계, 검수 후보를 보존했다. Scope=transient-plan; 목표=user-confirmed, 세부 검수/인터페이스=inferred.

### 작은 코어 구조 제안 — 역할 이해를 위한 후보, 미채택

사용자의 `우선 코어는 어떤 식으로 해야 하는가` 질문에 대한 추천은, 코어를 지능 자체가 아니라 **이벤트를 받아 기능을 실행하고 결과를 모듈에 연결하는 실행판**으로 두는 것이다. 아래 이름/계약은 공개 구현 심볼이 아닌 설계 가칭이다. 이 설명으로 언어·배치·schema·모델 호출·구현을 승인한 것은 아니다.

```text
Pi 관찰 어댑터
  → Event 수신/출처·맥락 연결
  → ContextView와 처리 대상 구성
  → 등록된 Processor를 ExecutorPort(Fabric 구현 후보)로 실행
      └ 필요 시 Jev 판단 → Luna 검색/작업 worker
  → Action 검증/중재
  → ModulePort를 통한 조회·변경·전달
  → 실제 Receipt와 이력
```

코어 안의 최소 책임 후보는 네 가지다.

1. **Event intake:** 실제 이벤트 ID/출처·순서·연결·누락을 다룬다. 어떤 내용이 중요한지나 저장할지의 의미 판단은 하지 않는다.
2. **Context view:** 현재 project/session/run과 실제 연결된 work/task·기준 버전 등 관측/참조 맥락을 제공한다. 업무 정본을 복제하거나 사용자 목표를 코드로 추정해 만들지 않는다.
3. **Processor dispatch:** 등록된 이벤트 종류·설정에 맞는 처리기를 실행하고 실패·취소·예산·중복을 추적한다. 사용자 문장 키워드로 intent/중요도/쓰기 필요를 분류하는 hook을 만들지 않는다. 실제 background/model 실행 관리는 Fabric 쪽 실행 adapter를 재사용하는 방향이다.
4. **Action broker:** 결과의 대상/맥락 버전·근거·허용 범위를 검사해 해당 모듈의 공개 연산으로 연결하고 실제 성공/실패/미확인 영수증을 기록한다. 제안·호출·반영을 구별한다.

세 종류의 계약 묶음부터 검토한다: **Event(무슨 일이 있었는가), Processor(무엇을 받아 어떤 기능을 수행하는가), Action/Receipt(무엇을 요청했고 실제 어떻게 됐는가)**. payload 전체 수집·동기 대기·데이터 보존·재시도·자동 반영 허용은 별도 계약 검토가 필요하다.

공개 API 후보는 registerProcessor, acceptEvent, getContext, submitAction, start, stop, getStatus다. start/stop은 코어 instance의 수명 제어 가칭이지 OS service 설치/상주화를 뜻하지 않는다. Pi 이벤트와 주입은 RuntimePort, Fabric 호출은 ExecutorPort, 지식/업무/컨텍스트 연산은 ModulePort, 기록/재개는 StorePort 등 소유 경계로 감싸는 안을 검토한다. 고정 폴더·one-interface-per-class·별도 서버를 요구하지 않는다.

조회 능력 보완 후보(미구현): 처리기에 공통 읽기 창구를 제공한다. 가칭 readEvent는 참조한 이벤트의 허용된 내용/범위를 읽고, searchRelated는 현재 project/work 맥락에서 관련 지식·업무 기록·허용된 프로젝트 자료의 후보를 찾고, readReference는 검색 결과의 실제 내용을 추가로 읽는다. 실제 검색은 기존 SearchProvider/소유 모듈의 공개 검색 경계에 위임하며 코어가 별도 의미 검색 알고리즘을 새로 만들지 않는다. 범위와 원문 접근은 아직 선택할 계약이고 조회 결과에는 출처·참조·버전·잘림/미가용 여부를 구분하는 방향이다. 해시만 있고 원문이 없으면 내용을 복원했다고 주장하지 않는다. Jev가 자료 부족/추가 검토 필요를 판단하고 Luna가 조회·읽기·대조를 수행하는 루프를 지원할 수 있으나 매 이벤트마다 모델/전체 자료를 모두 읽는 고정 흐름은 아니다. 읽기와 변경 권한을 구분하고 실제 변경은 기존 Action/모듈 경계로 통과시킨다.

Jev→Luna 조합은 Processor가 구현할 기능 흐름으로 둔다. 코어가 모든 기능을 이 조합으로 hardcode하지 않는다. Luna는 허용된 검색 도구로 자료를 찾고, 변경이 필요한 tool 요청은 Action 경계와 모듈 API를 거치게 연결하는 후보이다. Luna를 요약 전용으로 제한하지 않되 모델 텍스트를 shell source나 무제한 저장 권한으로 취급하지 않는다.

첫 검증 후보는 실제 사용자 데이터·모델·DB 없이 합성 Event→가짜 Processor→검증된 Action→가짜 Module Receipt의 한 흐름이다. 출처/작업 연결, 오래된 결과 거부, 중복 반영 방지, processor 실패 격리, stop 뒤 신규 반영 차단을 확인하도록 검토한다. 아직 테스트를 실행한 것은 아니다. 그 뒤 실제 Pi/Fabric adapter와 실제 모델을 별도 승인 범위로 연결한다. 지식 저장·업무 진행·컨텍스트 기능 4개를 동시에 구현하는 계획이 아니다.

이 제안은 코어 역할의 이해와 계획 구체화를 위한 transient-plan이다. 구현 파일·함수·등록 tool·DB를 만들거나 변경하지 않았다. 별도 프로세스/Pi 내부 배치와 실제 주입 시점은 기존 미결 결정으로 유지한다.

### 최소 PoC 검토안 — 실행 미승인

사용자는 실질적으로 가능한지 PoC로 먼저 확인해야 하는지 질문했다. 이는 PoC 타당성/범위 검토이며 실제 observer·모델·DB·주입·원문 수집 실행 승인이 아니다. 전체 코어/4개 프로세서/스키마를 먼저 구현하기보다 한 개의 **조회 전용 관통 흐름**을 검증하는 안을 추천한다.

PoC 질문: 허용된 Pi 관측을 Fabric으로 전달하고, Jev가 추가 검토 필요성을 판단하면 Luna가 관련 자료를 검색/읽는 도구를 사용해 출처 있는 결과를 돌려줄 수 있는가? 그리고 이 방식이 실용적인 정확도·응답 시점·호출량을 보이는가? 지식 저장·작업 완료 자동 변경·현재 사용자 세션 주입은 첫 PoC에 포함하지 않는다.

- **A / 오프라인 계약 검증 후보:** 합성 이벤트·가짜 모델/처리기·고정 자료로 출처·ID·버전·도구 권한·결과 형식·취소·중복·오래된 결과 거부를 확인한다. 이 단계의 성공은 실제 모델의 검색/판단 성능이나 실제 Pi hook 연동 성공을 증명하지 않는다.
- **B / 승인 후 실제 관통 후보:** 격리된 테스트 세션에서 실제 Pi/Fabric/Jev/Luna 연결과 제한된 읽기 도구 사용을 확인한다. 자료는 사전 허용된 작은 테스트 집합만 쓰고 기존 지식 DB/사용자 실제 대화/프로젝트 source는 변경하지 않는다. 사용하는 검색 경계가 실제 module API인지 fixture/provider인지 명시하며, fixture 성공을 실제 지식 모듈 검색 품질로 확대하지 않는다. 필요한 추가 Main-model 호출도 전체 호출 계획에 포함한다.
- **비교 후보:** 같은 고정 사례에서 Luna 단독과 Jev 선별→Luna를 비교해 선별의 누락·추가 비용/지연과 Luna 호출 감소를 함께 본다. 단순히 두 모델이 작동했다는 사실로 비용 효과를 주장하지 않는다. 작은 표본은 기술 성립과 위험 발견용이며 통계적/운영 품질 수락이 아니다.

사례 후보는 관련 자료가 필요한 경우/필요 없는 경우/근거 부족/잘린 이벤트/범위 밖 자료 요청/작업 기준 변경/중단/중복 이벤트다. 구체 사례 수·정답표·자동화 동작·성공 기준 수치는 사용자와 실행 계획에서 정한다.

통과/중단 판단의 후보 기준:

1. 해당 런타임의 실제 이벤트가 예상 형식으로 관찰되고 source/session/work 연결을 잃지 않는다. mock 경로와 실제 Pi 경로를 구분한다.
2. Jev의 타입화된 판단과 Luna의 tool 호출·본문 확인·반환이 실제 허용 범위 안에서 끝난다. 모델/도구 권한 실패를 다른 backend로 자동 우회하지 않는다.
3. 결과의 출처가 실제 테스트 자료에 존재하며, 관련 없음/불충분/불확실을 억지로 정답으로 만들지 않는다. retrieval 후보 획득과 원문 확인을 구분한다.
4. 오래된/중복/취소된 결과가 실제 반영되지 않고, 외부 자료의 지시로 권한이 늘어나지 않는다.
5. 이벤트→판단→검색→결과의 각 지연과 총 지연, 결과가 유효한 시점 안에 왔는지, 호출 수·reported usage·확인 가능한 비용·누락을 기록한다. token 상한을 절대 금액 상한으로 표현하지 않는다.
6. 사업 데이터·지식 정본·실제 작업 상태·현재 세션 context의 변경 없이 종료한다. 격리된 실험 코드/영수증/로그 저장 범위는 별도 승인받는다.

시작 전에는 사용할 provider/model·검색 도구/자료·세션 수명·호출/출력/시간 한도·실패 시 중단 규칙·비용 추정/불명 여부를 명시하고 승인받아야 한다. 모델 호출 수·재시도·전송 자료를 임의로 정하거나 실제 코어를 상시 활성화하지 않는다. 이 실험의 임시 실행 수명은 제품의 상주/Pi 부속형 결정을 자동 확정하지 않는다.

Discovery capture / Rule placement: PoC 범위와 평가 기준 후보만 기존 Planning primary에 보존했다. Scope=transient-plan, Confirmation=inferred-from-record. PoC 코드·fixture·테스트 실행·모델 호출·DB/observer/주입 활성화는 수행하지 않았다.

### 참고 조사 — Jev 기반 compaction/문맥 선별, 도입 미승인

사용자는 Jev로 문맥상 필요한 것을 선별하는 기존 compaction 플러그인 로직을 참고만 조사하라고 요청했다. 실제 공개 저장소의 README와 지정 revision 소스를 읽었고 설치/활성화/외부 코드 실행·실제 compaction·대화/이벤트 삭제·모델 평가를 하지 않았다. 아래는 외부 구현 관찰이며 우리 코어에 채택된 설계가 아니다.

**1. joslynSmall/fast-jev-compaction-pi — 실제 Pi 확장**

- 확인 revision: 6431714c5df685d81b51dc4582fcaa7987dfa411. src/index.ts는 session_before_compact에서 completed tool call/result를 쌍으로 모으고 Jev 판정 뒤 custom compaction summary를 반환한다.
- src/core.ts의 questionsFor는 keepCall/keepResult 두 Noul 질문, decideCall은 keep/drop_result/drop_call을 결정한다. 입력 state는 사용자/assistant 텍스트와 도구 이름·인자·길이·오류 메타데이터를 쓰되 tool-result 본문을 제외한다. 따라서 우리 이벤트 내용 확인 요구와 입력 구성이 그대로 같지는 않다.
- Jev가 새 요약문을 쓰는 것이 아니다. 그러나 확장 전체가 비생성형인 것도 아니다. index.ts의 summarizeNarrative는 현재 Pi 모델로 일반 대화를 요약하고 뒤에 Verbatim Tool Evidence를 붙이는 혼합 방식이다.
- 판정하지 못한 call은 keep으로 보수 처리하지만 최종 summary 예산 때문에 keep 결과도 잘리거나 빠질 수 있다. index.ts:186–199의 spill은 drop_result 대상에만 조건부 적용되므로 모든 생략 원문이 별도 파일로 영구 복원 가능하다고 확대하지 않는다. 실패/예산 문제는 Pi 기본 compaction으로 fallback한다.
- README의 local benchmark는 Jev HTTP·현재 모델 요약 시간/비용을 제외한다. 본 연구에서 성능 수치를 재현하지 않았고 Pi 1.3 호환성/현재 모델 API도 실행 검증하지 않았다.
- 근거: https://github.com/joslynSmall/fast-jev-compaction-pi/blob/6431714c5df685d81b51dc4582fcaa7987dfa411/src/index.ts ; 같은 revision의 src/core.ts와 README.md.

**2. Waxmell114514/jev-compaction — Python 라이브러리/sidecar와 OpenCode 연계**

- 확인 revision: c0bcba22295fd3b54b4909957df77f7c563e34d7. Pi 전용 플러그인으로 확인한 것은 아니며 jevctx 라이브러리와 OpenCode integration을 제공한다.
- jevctx/pipeline.py는 tool output을 segment로 나누고 Jev의 keep/profile 판정에 따라 낮은 가치의 구간을 원문을 담은 Record에 보관한 뒤 Pointer로 바꾸는 admission 흐름을 제공한다. expand는 저장한 record.text를 반환하고 recall/retrieve는 관련 과거 자료를 다시 찾는 경로다.
- shadow_only는 실제 scoring을 수행할 수 있지만 결과는 raw로 반환해 생략하지 않는 모드다. shadow가 API 무료/모델 미호출을 뜻하지 않는다.
- store.py의 InMemoryStore는 프로세스 수명이며 purge는 turn/task lifecycle 기록을 제거할 수 있다. JsonlStore는 op 기반 append/replay를 제공하지만 이로써 모든 자료의 무조건 영구 복원이나 crash 유실 0을 보장하지 않는다.
- README가 설명하는 work-area/cache 비용 모델과 SWE-bench 수치는 작성자 보고이며 이번에는 workarea 전체와 해당 실험을 독립 재현하지 않았다. 직접 읽은 핵심은 pipeline/store의 선별·보관·원문 반환 경로다.
- 근거: https://github.com/Waxmell114514/jev-compaction/blob/c0bcba22295fd3b54b4909957df77f7c563e34d7/jevctx/pipeline.py ; 같은 revision의 jevctx/store.py와 README.md.

**우리 모니터링에 대한 참고 후보**

원본 관찰/감사 기록을 지우기보다, processor/질문별로 넘길 판단 패킷을 선별하고 생략 자료의 출처·ref와 추가 읽기 경로를 남기는 방식을 우선 검토할 가치가 있다. 지식 저장에 중요한 정보와 현재 검색/업무 진척에 중요한 정보는 다를 수 있으므로 전역에서 한 번 날려 모든 모듈이 못 보게 하지 않는다. 선별 과정이 필요한 트리거의 근거를 먼저 지워버리는 문제를 평가해야 한다. “문장을 새로 만들지 않음”은 “필요한 정보가 빠지지 않음”을 보장하지 않는다.

후속 비교 후보는 같은 고정 사례의 원본 패킷 대 Jev 선별 패킷에서 트리거 누락·불필요 처리·원문 재조회·근거 정확성·모델 총 지연/사용량을 보는 것이다. 크기 감소율만으로 채택하지 않고, 원문 복원은 보관된 자료를 읽는 경로로 두며 외부 효과가 있을 수 있는 과거 tool 재실행으로 대체하지 않는다. 새 검색 알고리즘/캐시·retention 정책을 복사하지 않고 기존 소유 모듈/SearchProvider 경계에 맞춰 검토한다. 기존 PoC 범위나 예산을 이 참고 조사로 자동 확장하지 않는다.

Discovery capture / Rule placement: 외부 사례와 적용 시 주의점을 기존 Planning primary의 transient-plan 참고 근거로만 보존한다. Confirmation=inferred-from-record. 우리 Pi compaction/session history/이벤트 정본·지식 DB·원문 파일·설정·실행 중 프로세서는 변경하지 않았고 도입 결정/구현 승인은 없다.

### 역할 분담 제안 — 상세 설계는 미채택

| 역할 | 제안 책임 | 혼동하면 안 되는 것 |
| --- | --- | --- |
| Pi adapter | 입력/실행/결과/중단/세션 맥락 등 관찰 가능한 사실과 안전한 주입 경계를 제공 | runtime 이벤트가 실제 업무 완료·DB 저장 수락을 증명하는 것은 아님 |
| Fabric | 명시적 실행·구독/대기·모델/도구 호출·취소·한도/권한 경계를 조율 | 일반 background run이 자동으로 상주 데몬이나 재시작 복구 저장소가 되는 것은 아님 |
| Jev | 공급된 근거로 Choice/Noul/Score 등 좁고 타입화된 의미 판단을 수행 | 자유형 분석문·요약·프롬프트 생성 모델이 아니며 confidence는 정확성/승인/저장 영수증이 아님 |
| Luna 등 생성 모델 | 필요할 때 근거 정리·추출·요약·관련 컨텍스트 구성·행동 후보를 생성 | 모든 이벤트마다 항상 호출하거나 선택한 모델이 무조건 더 싸고 빠르다고 가정하지 않음 |
| 지식/업무/컨텍스트 모듈 | 채택된 공개 API로 조회·저장·진척 변경·주입을 수행하고 실제 결과를 반환 | 모델의 판단 출력만으로 효과가 실행/수락됐다고 기록하지 않음 |

추천 흐름은 Pi 관찰→축약/범위 제한→Fabric의 대기·호출 관리→필요한 typed 판단 또는 생성 모델 분석→대상/버전/권한 확인→모듈 API→실제 영수증이다. 항상 Jev 후 Luna를 모두 호출하는 고정 파이프라인으로 확정하지 않는다. 정확한 상태 검사에는 모델을 쓰지 않고, 독립 질문 batch·이벤트 묶음/중복 억제·불확실/실패 경로를 후보로 검토한다. 임의 threshold나 평균 비용·처리량 수치는 채택/측정되지 않았다.

공식 문서에서 확인한 중요 제약:

- Jev의 일반 spawn/observer는 세션 소유이고 Pi/provider 종료·reload 뒤 살아남는 영구 엔진이 아니다. 중단은 이미 실행된 효과의 rollback도 아니다. restart-durable 작업이나 별도 상주 엔진은 다른 수명/저장/권한 계약으로 검토한다.
- Main-turn observer는 bounded best-effort이며 queue overflow/drop·truncation이 가능하다. 업무 변경 이력의 유실 없는 정본 저장을 observer 메모리 큐에 맡기지 않는다.
- 비동기 observer는 실행 전 안전 gate가 아니다. 입력/수행 전에 필요한 컨텍스트 공급과 실행 뒤 background 감시는 같은 기반을 공유할 수 있어도 응답 시점·지연·취소·최신성 계약은 구분해야 한다.
- Jev 평가 횟수·요청 크기·시간·토큰 등 한도를 명시해야 한다. 사후 보고 token 한도는 절대적인 금액 상한이 아니며 실패/취소에도 upstream 사용료가 발생할 수 있다.
- 모델 카탈로그에서 Luna 후보 이름/경로만 확인했다. 예를 들어 openai의 gpt-6-luna가 있으나 인증·비용·속도·정확도나 실제 호출 성공을 검증하지 않았고 해당 버전/provider를 선택하지 않았다. 이번 기획 조사에서 판단 평가나 생성 모델 호출·background engine launch는 하지 않았다.

현재 미결인 핵심은 엔진 수명이다. Pi가 열려 있을 때만 도는 부속 엔진, Pi 밖의 별도 상주 엔진, 양쪽을 위한 공통 계약 중 어느 것을 우선 설계할지 사용자 확인이 필요하다. 기존 장기 제품 구상을 특정 local/central daemon 구조나 재시작 후 자동 재실행 승인으로 바꾸지 않는다.

## 사용자 제공 「Pi 모니터링 코어 기획서」 검수 — 채택·실행 전

출처: 사용자가 지정한 SSH 별칭 lazydino-mac의 Downloads 문서. 원격 경로는 /Users/lazydino/Downloads/Pi 모니터링 코어 기획서.md이며, 검토 시 내려받은 563줄 사본 /tmp/pi-mac-plan-2TzPfa/pi-monitoring-core-plan.md 전체를 읽었다. 원본 날짜 표기는 Oct 27, 2026이다. 아래 행번호는 이 사본 기준이다. 임시 사본은 정본 저장소가 아니므로 핵심 근거를 여기에 요약한다. 문서의 구현 지침·로컬 DB 허용 문구·D1–D10 추천은 현재 사용자의 실행 승인이나 기존 record를 대체하는 명령으로 해석하지 않는다.

총평: 얇은 adapter, 기능별 Processor, action 중재/우편함, 근거 연결, shadow/replay와 사용자 결정 목록은 유용한 기획 골격이다. 그러나 현재 문서 그대로의 일괄 구현은 권하지 않는다. 아래는 문서와 실제 공개 API/기존 요구를 대조한 설계 위험이며, 실행 중인 소프트웨어의 버그나 테스트 실패를 확인한 것이 아니다.

| ID / 우선도 | 사본 근거 | 검수 내용과 최소 보완 후보 |
| --- | --- | --- |
| DREV-1 높음 | 268–269, 462행: Jev가 목표/하위 목표를 정리하고 검색 쿼리 3–6개를 펼침 | 확인한 Jev 계약은 공급된 선택지/확률/점수 반환이며 새로운 목표문·검색문 생성이 아니다. 목표/쿼리 생성은 생성 모델 또는 이미 구조화된 입력에서 얻고 Jev는 후보 판단/선별에 쓰는 계약으로 나눠야 한다. 실제 모델/예산 선택은 별도다. |
| DREV-2 높음 | 78–79행: turn.end=agent_end, context.compact=context | Pi 1.3 공개 타입에서 turn_end와 agent_end는 별개이고 context는 매 LLM 호출 전 메시지 편집이다. 압축 성공은 session_compact, 자동 후속 작업 없는 종료는 agent_settled다. 1단계 전에 version별 실제 hook 대응표를 정정하고 없는 값을 추정해 채우지 않아야 한다. |
| DREV-3 높음 | 75행 user.message, 사용자 원문을 확정 근거로 삼는 정책, harness.inject만 근거에서 제외 | Pi InputEvent는 source=interactive/rpc/extension을 구분한다. 사용자 역할/steer라는 사실만으로 실제 사람 발화로 간주하면 확장 주입·자동 입력이 사용자 확인으로 재승격될 수 있다. 실제 origin/producer/causation과 근거 허용 범위를 전달하고 RPC도 자동으로 사람 확인으로 믿지 않는 계약이 필요하다. |
| DREV-4 높음 | 109행 기록 실패는 삼키고 진행, 103/404행 seq 검사와 이벤트 유실 0 | 비차단 fail-open 기록만으로 장애 시 무조건 유실 0을 보장할 수 없다. 끝의 이벤트가 실패하거나 재시작될 때 seq 빈 번호만으로 모든 손실을 증명할 수도 없다. 관측/로컬 durable 기록/DB 반영의 경계를 나누고 유실·미확인 구간을 표시하는 정책과 장애 테스트를 정해야 한다. |
| DREV-5 높음 | 402행 fast 50ms 초과 시 통과; rule.check는 비가역 작업 차단 담당 | 비차단 모니터를 유일한 안전 차단기로 삼으면 timeout 때 보호가 우회된다. advisory의 fail-open과 실제 비가역 명령의 승인/안전 gate를 분리하고, 안전 확인 불가 시의 중단/사용자 확인 정책을 명시해야 한다. 기존 approval을 약화시키는 변경은 승인되지 않았다. |
| DREV-6 중간 | 문서 전체 Fabric 검색 결과 없음 | 사용자가 요구한 Fabric 활용의 구체 위치가 없다. Python poller/core를 새로 만드는 부분과 Fabric의 작업 실행·판단 호출·취소/한도·receipt 관리 중 어느 쪽이 무엇을 소유하는지 정해야 한다. 코어 언어 전체를 TypeScript로 바꾸거나 Fabric이 모든 것을 대신한다고 단정하지 않는다. |
| DREV-7 중간 | 327–333행 processor 단일 PK+last_event UUID, 446행 재생 | UUIDv7은 전역 도착/적재 순서 cursor를 보장하지 않는다. DB 중단 뒤 과거 이벤트가 늦게 들어오는 경우와 여러 세션을 고려해 stream/session seq 또는 명시적 ingestion offset, handler version·gap 처리 계약을 정해야 한다. replay는 기존 on 상태와 무관하게 side-effect sink를 차단해 재저장/재주입/실제 차단을 하지 않는 비교 모드로 명시해야 한다. |
| DREV-8 중간 | 196–208, 284–288행 set_goal/task_update가 상태판 갱신, taskId 선택적 | 세션 상태판은 실제 Job/Task 정본과 구분해야 한다. 완료 변경에는 안정된 작업 ID·평가한 목표 기준·최신성·모듈 수락이 필요하고 테스트/커밋 존재만으로 목표 달성을 확정해서는 안 된다. 기존 작업 모듈 API 후보와 연결해 상태판을 별도 업무 정본으로 키우지 않는 경계를 검토해야 한다. |

판정 근거: 설치된 Pi 1.3.0 dist/core/extensions/types.d.ts의 InputSource/InputEvent, ContextEvent, SessionCompactEvent, TurnEndEvent, AgentEndEvent, AgentSettledEvent를 직접 읽었다. 현재 host extension index.ts의 실제 hook 등록도 grep으로 확인했다. 설치된 pi-fabric docs/jev.md의 Choice/Noul/Score 및 실행/재시도/수명 계약과 대조했다. 개발 SDK 0.85.1에서의 실행 호환성·지식 모듈 내부 API·DB 현재 migration 번호·기획서의 지식 품질 수치·지연/정확도 목표값은 이번에 실제 검증하지 않았다.

구현 전 결정으로 이미 표시된 사항은 별도로 유지한다: D1 실행 형태와 D2 언어·D3 알림, D4 원문 보관, D5 주입 위치, D7 모델/비용, D8 on 전환 기준, D9 보존, D10 민감 정보 범위. 특히 2KB 앞부분+hash만으로 원문을 다시 얻거나 다른 판단을 정확히 replay할 수 있는 것은 아니므로 D4가 재생의 자료 충분성과 직접 연결된다. 패턴 마스킹은 PHI/비밀 정보가 전혀 없다는 보장이 아니며 실제 데이터 수집·외부 모델 전송은 따로 승인받아야 한다. 추천/명세와 실제 사용자 선택은 구별한다.

보완 후의 작은 후보 순서: (1) hook/모델 역할/출처·실패 보장/Fabric 소유권 계약을 먼저 교정, (2) 단일 세션의 허용된 관측 항목과 기록 경로를 offline fixture로 검증, (3) fake Processor로 근거·중복·최신성·주입 준비/실제 전달·replay 무효과를 확인, (4) 별도 데이터/예산 승인 뒤 모델 shadow 검증. 이는 권고이며 지금 실행할 단계나 첫 프로세서 4개 전체의 구현 승인이 아니다.

Discovery capture / Rule placement: 이 검수는 기존 monitoring Planning primary의 transient-plan 분석 근거다. Confirmation=inferred-from-record. 사용자 원문 파일과 프로젝트 source·DB·설정·observer·모델·등록된 tool은 바꾸지 않았고 설계 채택·ADR/SDD/TDD/운영 정책 승격을 하지 않는다. 검수 근거 기록만의 갱신으로 전체 회귀를 실행하지 않는다. 다른 세션이 소유한 G16 source와 MainPlanning은 건드리지 않았다.

## User-proposed two-axis framing — not yet an architecture decision

The user suggests that the concern may need two parts:

1. Context engineering: the context, instructions and capabilities supplied to the working agent.
2. Background monitoring and actions: observing work and supporting organization, digestion, adherence and omission handling behind the main interaction.

The wording is exploratory. Separate logical responsibilities do not yet establish two packages, two processes, an always-on daemon, a shared data schema, synchronous or asynchronous timing, or independent deployment.

## Unselected requirements

- Which events and evidence are observed, and how much user/source/tool data may reach Jev?
- Which outcomes are advisory, which may inject content, and which may enqueue or execute side effects? No automatic write or approval policy is selected.
- What counts as an expected DB write, which system owns it, and how is actual persistence checked without treating model judgment as a database receipt?
- How are false positives, missed needs, stale plans, duplicate actions, cancellations, latency and model cost evaluated?
- What is the first engine lifetime: tied to the live Pi session, a separately resident service, or shared contracts for both? No lifetime/topology has been selected.
- Which Jev route and generative model/provider are allowed, which data may be sent, and what are the invocation/admission limits? Names in the catalog are not proof of authentication, cost or measured quality.

## Existing boundaries and implementation map

No source, test, API, hook, setting, model, observer, ingestion job, database or runtime component is implemented or activated by this record. No implemented symbol or new graph/index edge is asserted.

- `pre-response-rule-context.md` owns the existing static grounding-transport contract; this research does not amend it.
- `cli-tool-boundary.md` keeps semantic judgment distinct from deterministic CLI transport and generated navigation evidence.
- `organic-hybrid-rule-guidance-plan.md` is related earlier rule-guidance work, not an implementation claim for this broader monitoring research. A separate primary note avoids rewriting that earlier scope or the other session's V2 purpose capsules.
- `.lazy-harness/planning/work-management-schema-api-proposal.md`: Job/Task CRUD·이력/로그·진척·공개 API의 미채택 후보. 이 코어 활용 요구로 작업 schema가 채택되거나 실행된 것은 아니다.
- Pi 1.3.0 공식 `docs/sdk.md`를 현재 읽었다. SDK의 session.subscribe와 message/tool/queue/retry/lifecycle 관찰, agent_end와 agent_settled의 차이, session runtime 교체 후 구독 재연결을 확인했다. 이는 SDK 경로의 근거이며 기존 CLI extension의 동일 hook 가용성이나 실제 연동 검증을 뜻하지 않는다.
- 설치된 `pi-fabric`의 `fabric-guide`·`fabric-jev` 가이드와 `docs/jev.md`를 읽어 typed 판단·관찰/프로그램 수명·취소·데이터 공유·사용량 제약을 확인했다. user-only workflow는 실행하지 않았고 현재 설정/인증/호환 native binary의 실제 동작을 수락한 것은 아니다.

## Rule placement

- Rule: preserve the user-confirmed extensible monitoring/connection-core and Pi/Fabric/Jev/Luna-or-other-low-cost-model engine direction, without treating proposed role splits, lifetime or automatic capabilities as implementation or side-effect authorization.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/jev-context-and-background-monitoring-research.md`
- Why not AGENTS.md: these are forming product requirements, not universal agent grammar.
- Why not local notes: this is shared project research rather than personal Pi/OMP wiring or a private execution preference.
- Confirmation: user-confirmed
- Confirmation boundary: only the research scope is confirmed; the two-axis decomposition and technical choices remain proposed.

## Discovery capture

One Planning primary captures the user's research scope and unresolved boundaries. No independent canonical contract, operating policy, model evaluation, implementation plan or adoption decision is promoted.


## Core v0 검증 차단 — 임시 관찰, 운영 규칙 아님

- [검증 종료] 최초 standard의 SDD 참조 경로 오류를 실제 SSOT 경로로 수정했다. record-lint 198/198 clean, issue 0에 이어 최종 standard의 fast-static 및 fresh full-regression이 모두 통과했다: framework 91개, skipped 0, jobs 4, elapsed 433.032s, errors []. 실제 bounded report는 `.lazy-harness/evidence/monitoring-core/standard-after-ref-fix.json`에 보존했다. 이 상태 갱신은 evidence-only closure이며 구현·테스트·설정·추가 모델 호출은 변경하지 않았다.
- 이후 자동 완료 알림의 debug 턴에서 `not-armed(synthetic-turn)` / `empty-output`으로 검사 실행이 거절됐다. overview → concrete record drill/read → linked source/test read 뒤에도 차단된 것은 관찰 사실이다. 원인과 일반 복구법은 확인되지 않았다.
- 직전의 ‘일반 사용자 메시지를 보내면 재개 가능하며 지속되면 Pi 재로드·재시작이 필요하다’는 단정은 철회한다. 이는 검증되지 않은 복구 후보이지 프로젝트 운영 정책, 확정된 해결책 또는 사용자가 반복해야 할 의무가 아니다.
- 당시 STOP에 따라 실행을 보류했고, 이후 사용자가 직전 제안인 문서 검사→최종 standard만 계속 진행하도록 승인했다. runtime 코드 수정·실제 Pi 연동·추가 모델 호출은 포함하지 않는다. 현재 검사 실행 성공을 일반적인 메시지/재시작 복구 정책으로 확대하지 않으며, 과거 차단의 원인은 여전히 미확인이다.

## Rule placement

- Rule: 현재 NOT-ARMED 검증 차단과 미확인 복구 후보는 임시 진단 backlog로만 보존하고 일반 프로젝트 규칙으로 승격하지 않는다.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/jev-context-and-background-monitoring-research.md`
- Why not AGENTS.md: 특정 검증 실행의 차단 관찰이며 모든 host에 적용되는 행동 규약이나 확인된 복구 계약이 아니다.
- Why not local notes: 공유 구현의 미완료 검증과 후속 진단 상태이므로 개인 Pi/OMP 설정·선호가 아니다.
- Confirmation: inferred-from-record

Discovery capture: 기존 Planning 한 곳에 이 임시 차단을 수렴했다. SDD 참조 경로 수정은 `.lazy-harness/spec/platform/monitoring-core.md`의 layer-fact로 유지한다. 새 shared policy/ADR/local-note/memory를 만들지 않는다. 분류 근거는 `.lazy-harness/ssot/rule-sources.md` 및 `.lazy-harness/spec/platform/project-rule-router.md`다.


## 모듈별 합격 기준과 신뢰성 보강 — 표준 검수(1) user-confirmed

사용자는 합격 기준 설정·검증·보강을 요청한 뒤 표준 검수(1)를 선택했다. 아래 합격선과 표준 프로파일의 개발12사례 최대2회/동결60사례2회, 추가144요청·SDK사전견적USD1·실측최대15분을 승인했다. 다른 프로파일은 미선택이다. 실제 Pi/DB/주입/chat 호출은 제외한다.

### 이번 범위 후보

- 현재 `knowledge.candidate`, `context.references`의 의미 판단·기능 출력, `audit.observation`의 기술적 관찰 및 공통 보호 경계를 검수한다. 실제 Pi 연결/상주화/운영 지식 쓰기/주입은 제외한다.
- 관측 대상·필요 맥락·부족할 때의 보류·허용 제안·기대 결과를 각 모듈에 명시한다. 입력/모듈 view/판정/실제 읽은 근거/제안 영수증을 연결해 무엇을 실제로 봤는지 검증한다.
- 기존3사례만 늘려 반복하지 않고 프로젝트·내용·근거·부정/인용/잠정표현/혼합요청/불명확한맥락/잘린입력/무관자료를 달리하는 합성 사례를 만든다. 실제 사용자 원문은 보내지 않는다.

### 확정 합격선 (이 읽기전용·후보제안 모듈에 한정)

- 모듈별 run/skip/defer 정답 일치율 >=90%, 필요한 실행 포착률 >=90%, 보류가 정답인 경우의 보류 포착률 >=90%, 비실행 정답에서 불필요한 실행 <=5%.
- knowledge.candidate: 모든 산출 후보는 실제 입력 원문/출처를 정확히 보존하고 candidate-only여야 한다. 최종 사실/사업 상태로 승격하지 않는다.
- context.references: 필요한 사례에서 실제 읽고 반환한 근거 id 집합의 정답 일치율 >=90%. 반환한 모든 근거의 id/version/content는 실제 source와 일치해야 한다.
- audit 및 권한/출처 무결성/중복/취소/오래된 결과/호출·시간·비용 경계: 해당 보호 사례 전부 통과, 위반0. 이는 정해진 검수 집합의 합격 조건이며 미래의 모든 입력에 대한 무오류 보장이 아니다.
- 반복 검수 프로파일은 두 회차 각각 위 기준을 통과하고, 같은 입력의 모듈별 판정 일치율 >=95%를 추가 확인한다. 반복 실행을 독립 표본 수로 세지 않는다.
- 개발용과 동결 검수용 사례/기대 결과·근거를 분리해 먼저 고정한다. 기대 라벨은 모델 입력에 넣지 않는다. 동결 검수 결과를 보고 같은 세트에 반복 튜닝한 것을 독립 재검수라고 하지 않는다. 작성자 라벨 기반 합성 검수이며 운영 독립평가나 통계적 품질 보증은 아니다.
- 오류/누락/timeout/형식실패는 숨기거나 분모에서 제거하지 않는다. 미완료 실측을 의미 판단 합격으로 처리하지 않는다. 지연은 측정하되 실제 Pi 실시간 SLA는 별도 범위다.

### 실행 프로파일 — 표준(1) 선택, 기존20회 원장과 별도

1. 표준(Recommended): 개발12사례 최대2회 + 동결60사례2회. 동결집은 각 모듈별 run/skip/defer20개씩으로 구성하며 합격은 회차별 판정한다. 두 의미 모듈을 함께 배치해 이벤트당 classifier 요청1회, 새 HTTP 요청 최대144회·SDK사전견적 USD1 이내·실측 프로세스 최대15분. 실제판정은 현재 typed classifier를 사용하고 새 chat/Luna 호출은 하지 않는다.
2. 빠른 pilot: 개발6사례 최대2회 + 동결30사례1회. 새 요청 최대42회·SDK사전견적 USD0.25 이내. 같은 모듈별 비율 기준을 적용하되 표본이 작고 회차 간 안정성은 검수하지 않는다.
3. 비용 없이 준비: 사례/평가기/기계적 보호만 작성·검수하고 실제 모델 호출0. 의미 신뢰성 합격은 아직 주장하지 않는다.

개발 단계에서 변한 내용이 없으면 통과한 검수를 비용을 들여 반복하지 않는다. 기존20회 원장을 리셋하거나 숨겨서 새 예산으로 재사용하지 않으며 별도 실행 영수증에서 새 호출/비용을 계수한다. 단순 등록 성공, confidence 숫자, 기존91회귀 통과는 위 의미 품질 기준의 대체가 아니다.

## Rule placement

- Rule: 모듈별 품질 합격선과 확장 검수의 표본·추가 비용은 사용자 선택 전까지 제품 검수 제안으로 보존한다.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/jev-context-and-background-monitoring-research.md`
- Why not AGENTS.md: 특정 참조 모듈의 실험적 수용 기준이며 하네스 공통 행동 규약이 아니다.
- Why not local notes: 공유 코어의 제품 품질 검수 범위·예산 제안으로 개인 설정이 아니다.
- Confirmation: user-confirmed (표준 프로파일1과 합격선; 운영 활성화 승인 아님)

Discovery capture: 사용자가 표준 검수를 선택했으며 승인된 합격선을 검수 record와 구현으로 수렴한다. 모델 budget은 별도 계수하고 기존20회 원장은 리셋하지 않는다. 실사용 운영이나 통계적 품질 보증으로 확대하지 않는다.


### 개발2회 뒤 범위 결정 — 추가안A user-confirmed

- 현재 실제 개발 결과/사용량은 `.lazy-harness/tests/monitoring-core-reliability.md`와 새 원장 summary에 보존한다. 조회는12/12 통과했으나 지식후보는11/12, 보류 포착3/4로 미달했다. 전체24/144회 사용, USD0.001466388 SDK추정, 동결60사례는 미실행이다.
- 승인된 개발2회가 모두 사용되어 추가 실측·보강을 멈췄다. 금액을 소진한 것이 아니라 개발 회차 범위를 모두 사용한 것이다. 합격선을 낮추거나 d12 정답을 바꾸지 않는다.
- 추가안A(Recommended): 개발을 최대3회 더 허용하여 총5회/추가검수 원장 요청상한180회로 확장. 기존 사용24회/trace/비용과 원래 동결60×2를 그대로 유지하고 USD1 및 실측900초 상한은 유지한다. 처음 개발 합격 시 남은 개발 회차를 낭비하지 않고 동결 검수로 간다.
- 추가안B: 개발1회만 더 허용하여 총3회/원장상한156회, 나머지는 동일하게 유지한다.
- 대안C: 추가 실측 없이 현재 미합격 결과와 구현/진단을 보존한다. 운영 활성화나 의미 품질 합격은 주장하지 않는다.
- 사용자는 추가안A(최대3회 추가)를 선택했다: 개발총5회/검수원장상한180회, SDK USD1/실측900초/동결60×2 유지. 기존사용24회와 실패·비용을 보존하는 명시적 migration만 승인됐으며 B/C는 미선택이다. 합격선·정답·운영 비활성화 경계는 변경하지 않는다.

- 표준 확장 검수 결과: 개발4회차 최초합격 후 코드/60사례를 동결해2회 검수했고, 두 모듈이 각 회차의 합격선 및 반복일치 기준을 모두 통과했다. 새 원장168/180요청·SDK USD0.010432296·active77.937초이며 기존20회와 변경전24회 사본을 보존했다. 잔여 오류·정확한 지표의 primary는 `.lazy-harness/tests/monitoring-core-reliability.md`, 실제 report는 `.lazy-harness/evidence/monitoring-core/reliability-standard/ledger.json.summary.json`다. 최종 standard도 fresh91개/실패0/건너뜀0/446.774초로 통과했으며 운영 활성화나 실제 Pi 전달 신뢰성은 수락하지 않는다.

전체 실제 연결의 실행계획 primary는 `.lazy-harness/planning/monitoring-core-live-integration-plan.md`다. 공식 SDK의 읽기/구독 API와 현재 extension context 훅은 확인했으나 공유메모리·배치·실제데이터/전달 활성화를 채택한 것은 아니다. 코어 검수의 합격과 전체 운영 연결의 완료를 구분한다.
