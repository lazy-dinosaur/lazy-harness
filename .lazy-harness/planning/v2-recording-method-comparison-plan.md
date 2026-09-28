# 기록 생성 방식 직접 비교 — 실제 후속 작업 연구 설계

## Rule digest

- Status: advisory
- Layer: Planning
- Scope: host-project
- Applies when: V1식 문서 기록과 목적·태스크·완료조건 중심 기록의 직접 비교를 준비할 때.
- Must: 동일한 요구 정보·초기 코드·모델·도구를 제공한다. 기록 절차와 전체 하네스 성능을 구별한다. 실제 후속 작업과 근거로 평가하고 실패·원답·비용을 보존한다. 설계 검수와 실행 승인 전 실험을 시작하지 않는다.
- Aliases: 기록 방식 직접 비교, task-first 기록, 후속 작업 인계, V1 V2 기록 실험

## 후속 연구 질문 — 병렬 작업의 영역·책임 분리 (실행 미승인)

사용자는 HTML16번의 중요성을 워크트리/병렬 subagent 위임에서 영역과 책임을 명확히 분리할 수 있는 가능성에 연결하고, 이를 다음 시험으로 볼지 물었다. 확정된 것은 이 관심·질문이며 협업 효과 자체는 아직 가설이다. 기존 pilot02는 단일 과제의 순차 초기→fresh 후속 수정으로, 동시 작업의 책임 준수·협업 비용·통합 정확성을 검증하지 않았다.
논의 후보: 동일한 영역·권한·요구·작업 분할을 두 조건 모두에 주고, 일반 문서 인계와 지속 작업 카드 갱신을 비교한다. 작업 공간의 분리와 책임/의미 경계는 구별한다. 작은 의존 관계가 있는2개 작업에서 경계 밖 변경 요청, 진행 중 요구 변경의 전달, 결과 통합을 관찰하는 후보와 담당자 교체·재개의 별도 후보를 구별한다. 관측 후보는 무단 영역 수정·누락/중복·낡은 조건 사용·거짓 완료·통합 검사·부모 재설명/개입·재작업·전체 시간/비용이다. 과제·조건·모델·반복·예산·실행 장치는 미확정이며 이 기록은 설계/구현/유료 실행 승인이 아니다.
Discovery capture: Planning=사용자 연구 질문과 비채택 후보 수렴; DDD/SDD/BDD/TDD/ADR/SSOT=독립 변경 없음, 향후 검토 후보일 뿐 제품 계약/운영 규칙 채택 아님. Implementation map: 기존 [pilot02 결과](../evidence/v2-recording-method-pilot02-result.md)와 [연구 지도 G·H 및 시험 수준](v2-research-test-map.md)을 근거로 한 후속 질문; 새 source/test/workflow 없음.

### 사용자 선택: 두 AI 협업 시험 설계 — 초안01
User-confirmed: native 옵션 ‘두 AI 협업 시험 설계 (Recommended)’을 선택했다. 설계만 승인했으며 참가자 실행·실험 코드 작성·환경 변경·지출은 승인하지 않았다. 위 담당자 교체 후보는 이번 초안에서 제외한다.
최신 준비 승인(user-confirmed): 사용자가 ‘좋아 진행해줘’ 이후 native 옵션 **‘독립 작업 병렬·의존 작업 순차 (Recommended)’**를 선택했다. 업무 분할은 두 조건에 동일하게 주고, 카드가 책임·대기·변경 전달에 도움이 되는지 시험할 공통 입력·조건 지시·검사를 준비한다. 모든 카드를 전부 순차 처리하거나 업무 분할 능력까지 비교하는 의미가 아니다. 준비 작업과 별도 검수는 허용하되 실험 참가자 호출은 모델·예산 확인 후 별도 승인이다. 작업 위치는 신규 `experiments/v2-parallel-collaboration-01/`; 기존 비교/SDK/원본은 읽기 전용이다. 부모는 단일 준비 writer 후 fresh 검수를 연결하고 새 범위 결정은 직접 수렴한다. 대량 감사 사본·전체 artifact 재귀 검사·전역 설정 변경·설치·삭제·commit은 하지 않는다.

#### 질문과 조건
- 핵심 질문: 같은 목적·담당 범위·공유 약속을 받은 두 AI가 의존 작업을 병렬로 수행하고 요구를 바꿀 때, 지속 작업 카드가 일반 문서 기록보다 책임 누락·낡은 조건·통합 오류·부모 개입을 줄이는가?
- 비교군 이름은 AI 담당 번호와 분리한다. 문서형(A)과 카드형(B) 각각 담당1/담당2를 두며, 양 조건의 모델·도구·권한·공유 요구·담당 분할·교신 기회·검사·실행 공간은 같다. A도 완전한 요구/계획/완료 기준을 받고 표를 쓸 수 있다. B에만 작업별 지속 카드의 생성·갱신 의무를 더한다.
- 비교 대상은 ‘문서를 기록하는 절차’와 ‘같은 의무에 지속 카드가 추가된 절차’의 협업 전체 효과다. 문서형에 나쁜 지시/통신 금지를 줘서 약한 대조군을 만들지 않는다. 카드 자체가 쓰기 권한을 집행한다고 주장하지 않는다.

#### 작은 과제 후보 — 설정 읽기와 재시도 실행
- 담당1: 재시도 설정 해석과 그 검사만 소유한다. 담당2: 설정 결과에 따라 가짜 작업을 반복 실행하는 부분과 그 검사만 소유한다. 두 담당은 각자 분리된 쓰기 공간을 가지며 상대 파일/공유 약속은 직접 수정하지 않는다. 구체 파일/함수명과 실행 장치는 준비 승인 뒤 확정한다.
- 공통 약속 초안: 최초 작업 시도와 재시도를 구별한다. 재시도0이면 최초 시도1회만 한다. 실제 외부 서비스/네트워크 대신 정해진 성공·실패를 돌려주는 가짜 작업을 사용한다.
- 1단계: 설정 누락 또는 잘못된 설정이면 기본 재시도2회로 처리하는 초기 요구를 둘이 구현한다. 유효 설정 범위는 정확한 정수0..3 후보이며 bool 등은 잘못된 설정으로 분류한다. 초기 요구·정답·검사 기준은 사전에 고정한다.
- 2단계 변경: 설정 누락은 기본값2를 유지하되, 명시된 잘못된 설정은 조용히 기본값을 쓰지 않고 설정 오류로 처리하며 작업을 한 번도 실행하지 않아야 한다. 담당1은 오류를 전달하고 담당2는 그 오류를 구별해 작업 미실행/설정 오류 결과를 보장해야 하므로 양쪽 책임이 만난다.
- 각 조건에서 두 담당은1단계를 병렬 수행한다. 중간 경계에서 산출물·현재 상태·검사 결과를 고정하고2단계 요구를 두 담당 모두에게 동일하게 전달한다. 이는 임의 시점에 한쪽만 힌트를 받는 시험이 아니다. 같은 담당이 변경을 이어가며 담당자 교체 효과는 섞지 않는다.

#### 연락·인계와 통합
- 두 조건 모두 상대에게 질문·변경 요청·진행 상태를 전달할 수 있다. 상대 구현을 봐야 하는 경우에도 같은 시점의 고정된 산출물만 같은 규칙으로 전달한다. 카드형에만 최신 상대 코드를 보게 해서는 안 된다.
- 관측용 식별 정보(담당/요구 버전/전달 시점)는 양쪽 런타임 근거에 똑같이 보존한다. A의 기록을 평가자가 사후 카드형으로 보정해 다음 작업자에게 넘기지 않는다.
- 담당 산출물은 서로 덮어쓰지 않고 평가용 공간에서 합친 뒤 함께 검사한다. 부모는 승인·정해진 전달·검사 집계만 맡고, 몰래 코드를 고치거나 의미 충돌을 해결해 성공시키지 않는다. 필요한 부모 해결·추가 설명은 개입으로 집계한다.
- 각자 검사 통과와 합친 프로그램 통과를 별도로 판정한다. 자기 부분 완료, 상대 대기, 통합 완료를 구별한다. 소유권을 지켜 필요한 변경을 요청하거나 기다린 것은 그 자체로 실패가 아니다.

#### 미리 세울 판정
- 우선 지표: 잘못된 설정에서 가짜 작업 호출0회, 올바른 설정의 최초/재시도 횟수, 요구 누락·상대 영역 수정·중복 작업·낡은 요구 사용·근거 없는 전체 완료 여부. 정답표와 실패 조건은 참가자 입력 제작 전에 고정한다.
- 협업 비용: 부모의 내용 개입·재설명, 되돌려 고친 작업, 메시지/상대 대기, 전체 완료 시간과 기록·읽기·조율을 포함한 보고비용. 메시지 수가 적다는 이유만으로 우수 판정하지 않고 적절한 변경 요청과 불필요한 왕복을 구별한다.
- 보조 지표: 카드/문서의 최신 목적·범위·의존 관계·완료 근거 일치. 카드 칸을 채웠다는 사실만으로 효과를 판정하지 않는다. 코드가 다른 파일에서 깨지는 의미 불일치도 검사하며 Git 충돌 개수만 보지 않는다.
- 처음에는 두 조건 각1팀의 예비시험 후보로 제한한다. 이 한 쌍은 실행 가능성과 실패 패턴 탐색이지 통계적 우월성 증명이 아니다. 순서·캐시 영향과 반복 필요성은 남긴다. 사전 검수에서 과제가 너무 쉬워 차이를 볼 수 없거나 너무 복잡해 원인을 분리할 수 없으면 수정 제안 후 확정한다.

#### 아직 결정/실행하지 않은 것
- 실제 병렬 런타임/격리/교신 지원, 정해진 Python 검사 명령이 실제 환경에서 실행되는지, 승인 원문 보존과 감사 사본 선택 오류 방지는 이전 실험에서 이어지는 준비 확인 사항이다. 지원한다고 추정하거나 기존 승인/비용 한도를 재사용하지 않는다.
- 모델·도구 한도·반복·시간·예산, 실제 필드/오류 형식, 새 입력/테스트/준비 파일, 실행 시점은 미확정이다. 변경2단계 전체 요구는 평가자 계획에 보존하되 참가자에게는 정해진 변경 시점 전 노출하지 않는다.
- 이 초안은 결과가 아니다. 새 모델 실행·worktree 생성·새 코드/테스트 실행·설치·삭제·대량 복사 없음. Discovery capture와 Implementation map은 위 primary의 기존 결과/연구 지도 참조를 재사용하며 새 구현 edge를 주장하지 않는다.


## 1. 목적과 현재 승인

사용자는 두 기록 방식 직접 비교를 다음 연구로 선택했고, 보존 정리 이후 다시 진행을 요청했다. 현재 단계는 구체 설계다. 아래 과제·반복수·시간 예산은 제안이며 실행 승인은 아직 없다. 보존 미확인 항목은 기존 연구 지도에 남기고 과거 실험을 다시 돌리지 않는다.

추가 사용자 확인: 독립 검토 [design-review-01](../evidence/v2-recording-method-design-review-01.md) 이후 옵션 ‘준비 진행 (Recommended)’을 선택했다. 승인 범위는 설정 해석 단일 과제의 공통 입력·A/B 기록 지시·후속 요청·채점 도구를 만들고 격리 및 예산 제한의 실제 지원 여부를 확인하는 준비 작업이다. 실험 참가자4세션 실행, 예산값 채택, 새로운 runtime/보안 장치 구현·설치·배포는 승인하지 않았다. 검수 제안은 준비안으로 구체화하되 검증되지 않은 실행 가능성을 확정하지 않는다.

최신 상태: 준비 수정본 v2의 두 결함은 [독립 정적 재검수](../evidence/v2-recording-method-preparation-fix-review-01.md)에서 수용됐다(새 P0/P1/P2 준비 결함 없음). 저장된 수정 검사 결과는8 tests/0.068s, 잘못된 구현14개 배제다. 검수자가 테스트나 해시를 새로 실행한 것은 아니다. 변경된 캐시 사본2개와 승인된 별도 복구 사본의 증거는 보존하며 원인은 미확정이다. 아래의 ‘검수 대기’ 문구는 과거 단계 상태다. **실제 참가자 실행은 계속 BLOCKED**: 접근 격리·한도/취소의 집행 확인과 실험/예산 승인은 별도로 남았다. 이번 준비 batch의 부모 checkpoint는 `.lazy-harness/evidence/v2-recording-method-preparation-parent-checkpoint-01.json`에 별도 저장하며, 정적 검수 수용과 표준검증 통과를 혼동하지 않는다.

사용자 추가 승인: 실행 가능성01 보고와 정지 상태 설명 후 ‘진행해야지 그러면’으로 **실험 전용 격리 실행 연결 구현 및 무과금 검증**을 승인했다. 기존 bwrap를 사용한 프로젝트 실험 영역의 최소 연결·검사·독립 검수로 한정한다. 참가자/유료 모델 호출, 지출 위험 수용, 전역 Pi/runtime 변경·설치·동기화·배포·커밋·업로드는 포함하지 않는다. 실제 전체 참가자 도구/초기 입력과 분리 채점 경계의 연결을 입증하지 못하면 부분 기능만 보고하고 실행 차단을 유지한다.

## Final execution card 01 — 일반 개발 비교 운영 개정 / 승인 대기

추가 사용자 승인: 위 카드 제출과 실제 모델 연결 미구현 상태 설명 후 사용자가 ‘계속 진행해줘야지’로 **프로젝트 로컬 실제 모델 연결 구현·무과금 검증**을 지시했다. 이제 adapter/controller 준비는 승인된 작업이다. 네 참가자의 실제 호출·유료 availability probe·지출 위험 수용은 별도 실행 승인 전 금지한다. 기존 sandbox/영수증/일반개발 평가/정확한 과제 조건은 유지하며 전역 설치·설정·런타임 교체는 하지 않는다. 기존 mock-only 성과를 실제 provider 연결 성공으로 소급하지 않는다.
Discovery capture: Planning=updated(연결 구현 승인과 범위), SDD/BDD/TDD=candidate(live entrypoint·중립 계획 승인·실행허가/계량/중단의 구체 연결 및 무과금 검사), DDD/ADR/SSOT=none(새 제품규칙·보안구조·전역설정 채택 없음).

### Live SDK connection 01 — 실제 코드 구현 / 무과금 wiring 검사 완료, 독립 검수 대기

독립 검수 결과: [live-sdk-connection-review-01](../evidence/v2-live-sdk-connection-review-01.md)는 실제 live-capable adapter/controller/CLI 존재와463개 artifact 무결성을 확인했으나 같은 승인 범위의 세 결함을 지적했다. P1: grader cleanup 미확인에도 다음 행을 진행함. P2: row wall이 setup/freeze/grade/persistence를 포함하지 않음. P2: 비밀이 포함된 config/model/URL을 허용해 원시 config 보존에 유입 가능. 관찰된 실제 credential 유출이나 provider 실패라고 주장하지 않는다.
기존 연결 구현 승인 범위에서 위 세 경로의 stop/시간 의미/비밀 없는 입력 검증과 보호 테스트를 보완·재검수한다. 연구 기준/시간 의미를 낮추지 않고 실제 유료호출·credential 조회·전역설정 변경은 하지 않는다. 정상 기능 실패와 cleanup/인프라 실패를 구분하고 기존 결과는 보존한다.
Discovery capture: Planning=updated; SDD/TDD=candidate(행 lifecycle/cleanup, 범위 전체 시간, 명시적 비밀 없는 config schema와 회귀), BDD=candidate(실패 후 다음 행 차단), DDD/ADR/SSOT=none(새 도메인·보안구조·실제 모델/요율/환경설정 채택 없음).

#### Live SDK correction 01 — 세 reviewed 경로 보완 / 독립 재검수 필요

최신 closure: [독립 재검수](../evidence/v2-live-sdk-correction-review-01.md)가 세 수정(cleanup/인프라 후속 차단, 전체 row wall 관찰·중단, 지원하는 비밀 없는 설정 schema)을 수용했다. 같은 범위의 신규 P0/P1/P2는 없었다. 저장된 실제 모델 호출 없는23검사/4.884초 결과와2044개 명시 artifact 무결성,17개 native receipt/34개 raw stream 연결을 검수가 대조했다. 검수자의 신규 테스트 실행이나 실제 provider 검증은 아니다.
남은 것은 추가적인 동일 코드 보완 승인이 아니라 **실제 owner runtime/auth·중립 계획 승인 bridge·유효 모델/thinking/요율/accounting 확인과 실행/지출·초과위험 승인**이다. 현재 이 입력/권한은 미확인·미승인이다. 제안10분/40tools/12000output/$20을 자동 채택하지 않는다. 보존본을 재수정하거나 hostile grading 보장을 다시 도입하지 않는다. 현재 구현·검수 workflow는 종료됐고 실제 비교 실험은 미실행이다.

실제 연결 확인 승인: 사용자가 ‘다음단계얼른 진행해줘야지’로 기존 Pi 로그인·모델·요율의 실제 연결 확인을 진행하도록 지시했다. trusted SDK의 기존 설정/인증 인터페이스를 이용해 비밀이 아닌 effective metadata와 인증 자료 존재 여부를 확인한다. credential 원문 출력·artifact 복사·재로그인/토큰 갱신·전역설정 변경·모델 endpoint 호출은 하지 않는다. 필요한 실험 로컬 runtime 연결은 기존 adapter 구현 범위에서 구체화하되 인증 존재를 실제 provider 성공으로 바꾸어 주장하지 않는다. 실행/비용 승인은 그대로 별도다.
Discovery capture: Planning=updated; SDD/TDD=candidate(기존 runtime의 안전한 metadata/preflight 연결), SSOT=candidate(실제 모델·요율·인증 소유 근거 확인 전), DDD/BDD/ADR=none.

##### Existing runtime connection 01 — 실제 metadata 확인 / 실행 미승인

최신 검수 closure: [existing-runtime 독립 검수](../evidence/v2-existing-runtime-connection-review-01.md)는 실제 metadata CHECK와 local runtime/TTY 승인 연결을 수용했다. 신규 P0/P1 구현 blocker는 없고, P2 문서의 과거 prerequisite/Git-ignore 혼동은 현재 `LIVE-SDK.md`에서 원래 adapter 시점 및 diagnostic-only라고 명확히 고쳤다. primary의 URL 서식 drift는 역사 closure와 검수 보고에 보존하며 원래 snapshot을 고치거나 equality를 소급 주장하지 않는다.
다음 실행 승인 제안: 실험 전용 SDK/owner TTY 경로로 A initial→B initial→B followup→A followup 4행, `openai-codex/gpt-6-astra` thinking high 동일 적용. 행당 wall600000ms(계획 승인 대기 포함), tools40, 보고 output12000 tokens, tool timeout10000ms, abort grace1000ms, revision1/retry0. 4행 합계 SDK 보고비용 USD20에 도달하면 다음 호출을 막고 진행 중 abort를 요청한다. in-flight 초과/원격취소 및 실제 invoice 불일치는 가능하며 준비/독립검수 비용은 별도다. 시작 전 실제 stdin/stderr TTY를 확인한다. 각 행 계획은 사용자가 중립 범위/기준만 승인한다. 인증/provider 유효성은 첫 실제 호출까지 미확인; 실패 시 원본 보존 후 자동 재시도/토큰 갱신 없이 멈춘다. 아직 사용자 실행 승인을 받지 않았으므로 config flags를 켜거나 provider를 호출하지 않는다.
Discovery capture: Planning=updated(검수 closure/실행승인 제안); SDD/BDD/TDD=기존 조건 재사용; SSOT=candidate(승인 전 모델 thinking/정확한 한도값); DDD/ADR=none. 실제 모델·요율 metadata는 retained evidence를 재사용하며 새 조회로 주장하지 않는다.

User-confirmed execution approval: 사용자가 구조화 질문에 **‘네 작업 실행 승인 (Recommended)’**을 선택했다. 위 Astra-high/4행/모든 수치 한도/SDK 보고비용 USD20/진행 중 초과·실청구 차이/준비·검수 별도/owner TTY 계획 승인 조건을 그대로 승인했다. 기존 OAuth의 실제 인증·provider 호출을 이 예비시험 범위에서 허용하며 자동 갱신/재시도/전역 수정은 금지한다. 이 승인은 개별 행의 계획 승인을 대신하지 않는다. 승인 전 metadata-only의 모든 결과와 denied config는 보존한다. 신규 approved config와 fresh run destination을 별도로 사용한다. Discovery capture: Planning=updated, SSOT=이 실행의 확정 config로 수렴, 나머지 DDD/SDD/BDD/TDD/ADR은 기존 비교 규약에 independent delta 없음.

첫 실제 실행 중단/사용자 정정: 사용자가 별도 shell이 열린 이유를 묻고 ‘쉘에 아무것도 안보여’라고 보고했다. Parent가 실제 승인 화면을 확인하지 않고 `/attach`와 계획 승인을 안내한 것은 부정확했다. 세션 `v2-recording-pilot-01`의 중지/출력 조회는 이미 inactive/not-found였고, 이후 완료 알림은46초/exit0/210 lines를 보고했다. 이는 실험 성공이 아니다. `experiments/v2-isolated-execution-01/artifacts/live-sdk-connection-01/owner-approved-pilot-01/result.json`은 A-initial failed(reason=`owner decision rejected`), 이후3행 not-run, infra-or-scope-failure 중단을 기록한다. 첫 행 계획 단계의 retained accounting은5개 model response, 합계 SDK reported USD0.08496000000000001이며 invoice는 unknown이다. 실제 provider 실행0이라는 이전 상태는 이 시도 이전에만 해당한다. 화면이 비어 보인 원인/승인 거절의 입력 원인은 아직 판정하지 않으며 사용자에게 거절 책임을 전가하지 않는다. 새 실행/별도 shell 재개는 보류하고 승인 인터페이스의 요구를 재확인하기 전 이전 실행 승인을 재사용하지 않는다.
Discovery capture: Planning=updated(실패·사용자 UI 관측·승인 stale), BDD=candidate(보이는 승인 경로), SDD/TDD=candidate(승인 UI/종료코드와 실제실패 구별), SSOT=기존 실행 config·보고비용 참조, DDD/ADR=none. 구현 수정/재시도/새 모델 호출 없음; 원래 실행 결과·승인·snapshot은 덮어쓰지 않는다.

진행 재요청 뒤 읽기 전용 진단: 사용자가 ‘아니 진행해봐야지’라고 재요청했다. 새 provider 호출 없이 `existing-runtime.mjs#terminalDecision/#parseOwnerDecision/#approvePlan`, `live-controller.mjs#approveScope`와 첫 행 마지막5개 numbered records를 확인했다. 현재 터미널 방식은 nonce·decision·reason 세 토큰을 정확히 입력해야 하며 형식이 다르면 `owner decision rejected`로 throw한다. 마지막 SDK event(01032.json,1789371817806) 뒤4ms에 failure(01033.json,1789371817810)가 저장됐다. 모델 계획을 기다리다5분 timeout된 사례가 아니며, accepted owner reply 없이 승인 경로가 즉시 실패했다. 실제 입력 문자열/빈 화면의 UI 원인은 아직 미확정이다. 제안(candidate): 별도 shell 대신 이 대화의 구조화 질문으로 같은 중립 승인 내용을 표시하고 명시 응답만 실험 controller에 전달하는 연결로 변경; 자동 승인은 금지한다. 변경·무과금 검증 후 새 실행 여부/기존 비용을 포함한 한도를 user-confirmed로 확정한다. Discovery capture: Planning=updated, BDD/SDD/TDD=candidate(visible chat 승인·nonce binding·실패 보호), DDD/SSOT/ADR=independent delta 없음; 첫 실행의 실패·raw1034개 numbered records는 그대로 유지한다.

User-confirmed chat continuation: 사용자가 **‘채팅 승인으로 계속 (Recommended)’**을 선택했다. 별도 shell UI 없이 이 대화에서 계획을 표시하고 명시 승인을 전달하도록 실험 로컬 연결을 수정·무과금 검사·독립 검수한 뒤, 동일 Astra-high/4행/기존 행별 한도로 새 시도를 실행한다. 첫 실패는 별도 시도로 보존하며 SDK 보고비용 총 USD20 기준에 기존 USD0.08496000000000001을 포함한다(새 시도 허용 reportedDollars는 잔액 이하). 기존 overshoot/invoice 차이/준비·검수 별도 한계는 유지한다. 자동 승인·과제 힌트 제공·토큰 갱신·전역 수정·자동 재시도는 금지한다. 개별 계획 승인은 실제 질문 응답이 있어야 하며 이 계속 승인으로 대체하지 않는다. Parent가 준비/검수를 수용한 뒤 실제 실행을 연결한다. Discovery capture: Planning=updated; SDD/BDD/TDD=승인된 실험 로컬 chat 승인 연결 delta, SSOT=새 시도 비용 잔액 config, DDD/ADR=independent delta 없음.

### Chat approval bridge 01 — 구현·무과금 검사 완료 / 새 독립 검수 후 Parent 실행

승인된 chat continuation을 실험 로컬 파일 bridge로 구현했다. `chat-launch.mjs` → 기존 `live-launch.mjs`의 optional signal 전달(유일한 기존 source 변경) → 기존 controller/SDK 흐름을 보존한다. 새 `chat-runtime.mjs`는 기존 SDK resolver를 그대로 re-export하고 genuine owner reply를 기다리는 `chat-approval.mjs`만 연결한다. fresh evaluator control directory에 run/row/revision/nonce-bound request와 verbatim final assistant text blocks·현재 user scope/criteria context를 저장하고 bounded `V2_CHAT_APPROVAL_REQUIRED` marker를 stdout에 낸다. Parent는 headless monitor native wake를 받아 현재 request만 읽고 원문 계획을 표시한 뒤 native ask_user_question의 실제 응답만 `chat-reply.mjs`로 전달한다. 자동 승인·model/auth/endpoint 호출·별도 shell UI·extension/global 수정은 하지 않았다. native monitor 실제 wake/UI 전달은 **미검증**이며 Parent가 첫 pending marker를 시간 안에 받았는지 확인해야 한다. 파일 테스트 통과를 실제 UI 성공으로 바꾸지 않는다.

원래 실패/원답/1034 numbered records/모든 snapshots와 이전 보고는 historical로 보존한다. 실제 거절 입력 문자열·빈 화면의 원인은 여전히 unknown이다. 새 config `experiments/v2-isolated-execution-01/artifacts/chat-approval-bridge-01/owner-chat-pilot-02.config.json`은 동일 Astra-high/fresh4행/wall600000(승인대기 포함)/tool10000/grace1000/tools40/output12000/revision1/retry0이며 reportedDollars **19.91504**다. 첫 실패 **0.08496000000000001**과 합해 total20; `lineage.json`과 run metadata에 carry-in을 보존한다. in-flight overshoot/invoice unknown/준비·검수 별도는 그대로다. 실행은 이 child에서 하지 않으며 독립 검수 전 Parent가 시작하지 않는다. 실행·marker·request/reply schema·helper·PID cancellation의 정확한 운영 명령은 [CHAT-APPROVAL.md](../../experiments/v2-isolated-execution-01/CHAT-APPROVAL.md)에 있다. 첫 실패를 resume하거나 재시도하지 않는다.

검사: 새 bounded diagnostic-only artifact subtree에서 **focused1회/18 grouped checks/935ms(process 약1초), exit0**. synthetic plan→request→explicit injected helper reply→approveScope authorization 순서, denial/unknown/malformed/stale/run-row-revision mismatch/replay/timeout/cancel, non-TTY, no-auth/no-stream pure preflight, carry-in config, actual SIGINT/SIGTERM→wrapper abort→pending watcher cleanup와 exit130/143, actual bwrap tool mount의 control-plane 비가시성을 확인했다. 실제 owner approval0/provider calls0이며 실제 SDK/remote cancel 성공 증거는 아니다. watch 등록 후 marker와 즉시 재검사로 lost wakeup을 막고 timer/signal/closed file을 정리하며 request/reply 원본은 삭제하지 않는다. 원본11개 explicit regular .bin baselines를 수정 전에 저장했다. broad lazy check/standard validators는 사용자 금지·기존 FIFO/symlink 재귀 위험 때문에 실행하지 않았다. 오류/세부 로그·finite post-return hash 증거는 [assigned evidence](../evidence/v2-chat-approval-bridge-01.md)에 수렴한다.

Parent native transport checkpoint: 독립 [chat review](../evidence/v2-chat-approval-bridge-review-01.md)는 새 P0/P1/P2 없이 source를 수용했고103 manifest files/11 baseline copies가 안정적이었다. 실제 UI 전달은 여전히 별도다. 첫 native headless stream probe `v2-chat-transport-probe`는 `printf`로 단일 marker를 내고 즉시 종료했으나 completion은 exit0/events0였다. 모델 호출 없이 수행한 이 probe는 **전달 확인 실패**로 보존한다. 설치 monitor의 subscribe는 live data listener를 연결하며 completion은 pending buffer를 flush 후 dispose한다; 이 소스만으로 실제 누락 원인을 확정하지 않는다. 같은 승인·같은 monitor protocol에서 살아 있는 대기 프로세스의 단일 지연 marker(유한한 타이머, polling 없음)로 재확인하며, provider 실행은 native event를 실제 받기 전 금지한다. 전역 tool 수정/다른 UI/자동 승인으로 우회하지 않는다. Discovery capture: Planning=updated, BDD/TDD=candidate(native live-event delivery), SDD/DDD/SSOT/ADR=no independent delta.

Parent native live-event 확인: `v2-chat-transport-live-probe`의 단일 marker가 native **Monitor Event #1 / chat-live-transport / V2_CHAT_TRANSPORT_LIVE_PROBE_OK**로 이 대화에 실제 도착했다(2026-09-14T13:11:08.036Z). 이후 exit0/events1로 종료했다. 이 무과금 알림 확인은 실제 승인 질문/사용자 응답/provider 성공을 대신하지 않는다. 즉시 종료 probe(events0)는 실패로 남긴다. 독립 검수 수용 및 위 user-confirmed chat continuation에 따라 fresh `owner-chat-pilot-02`/`owner-chat-pilot-02-control`로 실제 실행을 시작하며 marker 수신 때 각 계획을 원문 표시하고 사용자 답만 전달한다. 비용은 기존 시도 포함 보고기준20이며 추가 자동 재시도는 없다. Discovery capture: Planning/BDD=actual event 전달 확인, 나머지 layer는 기존 계약 재사용.

실제 chat 시도 종료 관측: native `v2-owner-chat-pilot-02`의 event6(2026-09-14T13:34:03.244Z)는 run-finished/exit0 및4행 `completed-unreviewed`를 보고했다. stream도 events6/exit0으로 종료했다. `owner-chat-pilot-02-control/completion.json`의 runId=`c581462e-b20f-4807-857c-4d74f68f6332`, halted/stopped=null, 동일4행 상태를 read로 확인했다. A-initial/B-initial/B-followup/A-followup 각각 실제 native 사용자 ‘계획 승인’을 받아 nonce-bound helper가 `V2_CHAT_REPLY_STORED`를 반환했으며 자동 승인은 없었다. 이 완료는 기능/기록 합격이 아니므로 독립 source·raw logs·인계·비용 검수 전 결과 우열을 주장하지 않는다. 첫 TTY 실패 비용과 새 run 비용, 준비/검수 비용을 분리한다. Discovery capture: Planning=updated, BDD=실제 chat 질문/응답4회 관측; 기능/기록 품질은 TDD/SDD/SSOT candidate 검수 대기, DDD/ADR=no independent delta.

### Actual pilot02 audit closure — finite functional support, not unconditional success

최종 Parent 종합: [pilot02-result](../evidence/v2-recording-method-pilot02-result.md)에 독립 검수의 조건부 수용과 정정을 수렴했다. 네 기능은 유한 기준 수용, 전체 절차는 literal python3 실행 미충족으로 unverified다. A USD1.097326/628.081초, B USD1.605958/706.184초(승인대기 포함). 이전 실패 포함 SDK 보고 USD2.788244이며 준비·검수/청구서는 별도 unknown. B의 T1은 실제 구현 전 생성·후속 갱신됐으나 이번 한 쌍에서 추가 기능 이점/인과 우월성은 입증하지 못했다. Audit의 A-followup 대기 전38.504초 오기는41.343초로 최종 종합에서 정정하고 원문은 유지한다. 상대링크 의심은 검수자 오판으로 철회됐으며 실제 결함이 아니다. UI 원답 별도 보존 한계, CLI 환경 차이, 사본49,993개/522,030,411bytes 사고와 최초 큰3개 hash 한계도 최종 종합에 유지했다. Discovery capture는 해당 all7 matrix에 수렴; 후속 환경/보존/반대순서 반복은 후보이며 새 실행/수정/삭제/commit 없음.

보고서 전달 형식 정정(user-confirmed): 사용자는 Markdown 기본 앱 열기가 아니라 **HTML로 만들어 브라우저에서 열기**를 요청했다. [pilot02 HTML 보고서](../evidence/v2-recording-method-pilot02-result.html)를 최종 종합 Markdown의 읽기용 표현으로 추가했다. 비교 수치·전체 절차 미검증·정정·보존 한계와 근거 링크를 유지하며 원래 결과/원본을 변경하지 않는다. Discovery capture: Planning=delivery updated; 나머지 layer는 의미 변경 없음.

사용자 승인된 actual run `c581462e-b20f-4807-857c-4d74f68f6332`의 원본 source/tests·terminal usage·native SDK tools·승인 binding·frozen 인계를 read-only 검수했다. 원래4행 `completed-unreviewed`, halted/stopped null, exit0는 유지한다. A/B 초기 및 fresh 후속 모두 사전 고정한 유한 기능 계약을 코드와 실제 public4/private71·320 및 참가자 regression receipts가 지지한다. 이를 universal correctness/기록만의 인과효과/전체 완료 합격으로 승격하지 않는다. 최초 TTY approval 실패와 기존 보존 실패는 그대로다.

새 run terminal usage 합계 USD **2.703284**, 첫 실패 **0.08496000000000001** 포함 **2.788244**; invoice·준비·검수 비용은 unknown이다. A initial/followup 각각 wall322.235/305.846초(승인대기119.262/57.681초), 보고비용0.495010/0.602316. B initial/followup 각각357.173/349.011초(54.135/59.549초), 0.706412/0.899546. 마지막 final persistence 관측은 추가1ms이며 전체1334.266초. A가 이 pair에서 짧고 저렴하지만 B의 더 많은 regression·다른 복구·산출물·순서·캐시 차이를 분리할 수 없다.

A는 strong primary/evidence 정책과 실패·제약·변경 이유를 보존했다. B는 승인 뒤 구현 전 T1을 실제로 저장하고 same-ID 후속 재개/closure를 수행했다. CLI 실패 원인은 raw stderr의 missing `python3`; A는 실제 `/usr/bin/python3.14` subprocess로 초기4+8, 후속4+14를 검증했고 B는 in-process compile/exec로 초기4+11, 후속4+20을 검증했다. B 후속 pre-fix의 실제1 TypeError와 CLI 미검증은 그대로 남긴다. B의 in-process 성공은 CLI 성공이 아니며, 비교 규약에 없던 executable-name 합격기준을 새로 만들지 않는다. A followup 계획은 interpreter-path recovery이며 in-process라는 서술은 적용되지 않는다. 독립 의미 검수에서 조작 근거는 찾지 못했지만 unsupported/suspicious 영역을 성공으로 추정하지 않는다.

Audit 보존 실수도 유지: 새 `experiments/v2-isolated-execution-01/artifacts/pilot02-audit-01/`의 directory-name filter가 flat numbered streams를 제외하지 못해 **49,993 baseline copies / 522,030,411 bytes**를 만들었다. `baseline-manifest.json`이 정확한 원본→사본→hash를 열거한다. 삭제/수선/추가 bulk copy 없이 보존하며 audit overhead이고 participant cost가 아니다. 이후 검수자는 이 finite manifest와 derived references를 재사용해야 한다. 원본 trial 전체가 아니라 이 actual trial/control만 lstat/no-follow/bounded read로 열거했다. 새 provider/auth/participant/test/grader/validator 실행이나 Git mutation은 없다.

| Audit Discovery/completeness layer | 판단 / 소유권 |
|---|---|
| DDD | reuse / no independent product delta — exact-int/ASCII/Mapping/zero/default3 과제 의미 불변 |
| SDD | reuse + evidence assessment — frozen source의 초기·override 계약 지지; API 수정 없음 |
| BDD | reuse + observed evidence — four fresh identities, own-condition handoff, native4 승인은 기존 confirmed completion과 file binding으로 연결 |
| TDD | retained evidence audited — public/regression code와 evaluator origin/counts/raw receipts 검수, 새 test/grader 실행 없음; SDD/BDD/SSOT/DDD 판단을 이 matrix에 함께 보존 |
| ADR | no independent delta — 새 설계/과학 기준/보안 보장 채택 없음 |
| SSOT | reuse — 실제 Astra-high, catalog reported accounting 및 carry-in을 검증; invoice/auth/global ownership 변경 없음 |
| Planning | updated — 이 primary에 pilot 결과·제약·audit 보존 실수·다음 bounded recommendation 수렴 |

Implementation/evidence map: `live-controller.mjs#runComparison,#approveScope` → `live-sdk.mjs#createLiveSession` / `sdk-receipts.mjs#dispatchWithReceipt` → actual `owner-chat-pilot-02/{result.json,persistence-final.json,<row>/row.json,<row>/frozen/,<row>/receipts/}` 및 sibling control request/reply/closed/completion. `isolation.mjs#followup,#Workspace.freeze,#grade` → `grade.py.txt` + frozen `evaluator/hidden_checks.py#cases,#snapshot,#check` + common `test_public.py#PublicTests`. Audit-only scripts `pilot02-audit-01/{audit.py,extract.py,analyze.py,final-checks.py,close-result.py}`는 파일 parsing/hash만 수행하며 participant Python을 import/execute하지 않는다. Reusable [derived-result.json](../../experiments/v2-isolated-execution-01/artifacts/pilot02-audit-01/derived-result.json), `trial-manifest.json`, `baseline-manifest.json`, `final-checks.json`, per-row timeline JSON 및 [audit report](../evidence/v2-recording-method-pilot02-audit.md)가 정확한 원본 경로·hash·unknown을 연결한다. 최종 finite post-return manifest와 staged-empty evidence는 같은 audit directory에 둔다. Rule placement: existing Planning primary only, graph/index/global policy 승격 없음.

Next bounded recommendation only: 다음 승인 연구에서는 같은 작은 과제의 새로운 counterbalanced pair와 검증 실행환경을 사전에 명확히 정의하고, 현재 실패/한계는 역사로 유지하면서 기록 fidelity와 code/test/recovery overhead를 분리해 관측한다. 이번에는 시작하지 않는다. Guided migration(record-lint2 / legacy graph37)은 pending·미변경이며 별도 승인 시 재개 가능하다.

| Chat Discovery layer | 판단 / 소유권 |
|---|---|
| DDD | reuse / no independent delta — 기존 과제·조건·채점 의미 유지 |
| SDD | experiment-local implemented — bounded evaluator request/reply transport, optional controller signal injection, exact binding/enum fail-closed; 이 primary와 실험 source 소유 |
| BDD | implemented locally — separate shell 대신 native chat 질문의 실제 답만 전달; 실제 monitor wake는 Parent 확인 전 untested |
| TDD | added — chat-approval.test.mjs18 checks; 위 SDD/BDD 및 아래 SSOT/DDD 판단을 함께 보존 |
| ADR | no independent delta — 새 global/runtime/security architecture·protocol 채택 없음, 기존 cooperative isolation 한계 유지 |
| SSOT | confirmed execution-local config — remaining19.91504 + carry-in0.08496000000000001, lineage 명시; credentials/global ownership·요율 변경 없음 |
| Planning | updated — 승인된 bridge 구현과 no-network 검사 완료, fresh independent review/Parent actual launch 별도 |

Implementation map: `experiments/v2-isolated-execution-01/chat-launch.mjs#main,#checkContinuation,#resultCode` → `live-launch.mjs#main(args,{signal})` → unchanged `live-controller.mjs#runComparison,#approveScope`; `chat-runtime.mjs#configureChat,#approvePlan` reuses `existing-runtime.mjs#resolveRuntime` and owns `chat-approval.mjs#createChatApproval,#readJSON,#validateReply,#submitReply` → Parent native monitor/question → `chat-reply.mjs#main` → exclusive reply publication → existing adapter approval gate. `chat-approval.test.mjs` protects file transport, ordering, preflight/carry-in, actual local signal handler and isolated tool mount; `CHAT-APPROVAL.md` gives exact ready-to-run commands without implementation TODO. Evidence: `artifacts/chat-approval-bridge-01/{baseline.json,baseline-*.bin,focused-run.json,focused-stdout.bin,focused-stderr.bin,owner-chat-pilot-02.config.json,lineage.json}` and new `artifacts/live-sdk-connection-01/chat-approval-tests-01/`. Rule placement: 이 existing primary에만 confirmed experiment delta를 수렴; 별도 canonical graph/index/global rule 승격 없음. Discovery capture는 위7행에 포함한다. Record-lint2/legacy graph37 guided migration은 pending·미변경; 별도 승인 시 guided migration을 재개할 수 있다.

사용자 승인된 기존 Pi 연결 확인을 수행했다. 직전 syntax-only dispatch failure64a4456c/children0 및 `.lazy-harness/evidence/v2-runtime-connection-dispatch-failure-01/`는 보존했다. 아래는 최신 관측이며 과거 ‘모델/요율 unknown·dependency 없음’ 문구를 그 당시 상태로 유지한다. [이번 evidence](../evidence/v2-existing-runtime-connection-01.md)는 실제 provider 성공이나 실행 허가가 아니다.

- **실제 metadata-only preflight (331ms, exit0)**: 설치 Pi SDK **0.85.1**, `ModelRuntime.getModel('openai-codex','gpt-6-astra')`가 정확히 **GPT-6 Astra / openai-codex-responses / <https://chatgpt.com/backend-api**를> 반환했다. reasoning true, text/image, contextWindow272000, maxTokens128000. **Standalone target mismatch 없음**(builtin+models.json 범위). USD/백만 token catalog rates는 **input10 / output50 / cacheRead1 / cacheWrite12.5**다. invoice·구독 과금 방식·외부/준비 비용은 unknown이며 0으로 환산하지 않는다.
- SDK `SettingsManager`의 merged defaults는 provider openai-codex/model gpt-6-astra/thinking **medium**이다. parent session override/effective thinking의 증거가 아니고 실험의 thinking 선택 승인도 아니다. `ReadOnlyAuthStorage.list()`의 provider/type metadata만으로 **OAuth 자료 존재 true**를 확인했다. credential 유효성/expiry·provider availability는 unknown이다. credential read/getAuth/checkAuth/getAvailable/login/refresh/model endpoint 호출은 하지 않았다. SDK 내부 trusted memory load 이외 auth 파일 도구 read/dump/hash/copy 없음.
- Side-effect 검토 후 `refreshOnCreate:false, allowModelNetwork:false`로 생성했다. DefaultAuthStorage.create는 auth 파일 생성/lock 가능성이 있어 사용하지 않는다. FileModelsStore.read도 없는 cache 생성/lock 가능성이 있어 remote cached catalog 복원은 하지 않았다; parent extension registrations도 가져오지 않는다. SettingsManager.create는 기존 settings의 일시 lock/read만 하며 setter/save/global 설정 변경은 없다. ModelConfig와 provider composition은 metadata를 읽되 auth command를 resolve하지 않는다.
- `existing-runtime.mjs`는 실제 설치 SDK를 지연 연결하는 `resolveRuntime`와 genuine owner `approvePlan`을 제공한다. accepted live-launch/controller/SDK source는 그대로다. 모델·요율 drift/target 미해결은 거절하고 별칭/다른 모델 fallback 없음. 기존 실행/spend/overshoot preflight 뒤에만 live dependency가 사용된다. ReadOnlyAuthStorage.modify는 OAuth refresh callback 실행 전에 거절하므로 near-expiry auth도 자동 refresh 대신 실패한다. owner bridge는 TTY 필수, 현 행 메시지만 JSON escaping 표시, fresh nonce+정확한 decision/reason 선택, default 없음, 최대64KiB view/5분 또는 더 짧은 row cancel, revision1 제한이다. 실제 owner TTY 입력은 이번에 실행하지 않았다.
- **새 glue focused check 1회:7 passed/303ms** (process367ms), injected no-network metadata/resolver/neutral decisions/cancel와 actual SDK의 expired synthetic OAuth refresh-before-callback 차단을 보호했다. synthetic auth는 실제 로그인 성공 증거가 아니며 기존 credential 접근0/network attempts0/provider calls0. 실제 metadata preflight와 분리 보존한다.
- `artifacts/existing-runtime-connection-01/metadata-config.bin`은 관측된 실제 모델/요율/default thinking으로 만든 **비밀 없는 denied config**다. execution/spend/overshoot false, owner UNAPPROVED, 미채택 한도0은 launch를 차단하기 위한 값이다. 제안10분/40tools/12000/$20을 채택하지 않았다. 실제 `live-launch --preflight`는 exit2/not-run, 권한 및 양수 한도7항목 누락으로 거절했고 dependency import/auth resolution을 하지 않았다. 다음 구체 invocation은 아래 map의 evidence/LIVE-SDK.md에 있다. 허가 없는 --run 자동 실행 없음.
- 보존: 명시 regular 원본9개를 `.bin` baseline, Git status/diff/index/head를 새 diagnostic-excluded artifacts에 보존했다. 최종 `git check-ignore`는 exit1이었다: 기존 `.pi-lens.json` 진단 제외이지 Git ignore가 아니다. ignore/config는 바꾸지 않았다; 첫 최종 snapshot과 failed audit command를 보존하고 이 표현만 정정했다. 별도 tool-return 이후9 copies stable, run raw4 streams hash drift0, fresh manifest23 files; 당시 baseline original 차이는 의도한 LIVE-SDK.md 하나뿐이었다(이 primary closure는 이후 변경). 기존 reports/failure/accepted task/SDK/grader 원본 수선·재귀/FIFO/symlink 접근 없음. staged-empty/index unchanged. broad validators/install/global edits/delete/commit/upload 없음.

| Connection Discovery layer | 판단 / 소유권 |
|---|---|
| DDD | reuse / no independent delta — exact int/Mapping/public4/private71·320 기준 유지 |
| SDD | experiment-local implemented — existing-runtime metadata/resolver/owner TTY bridge; 이 primary와 LIVE-SDK.md 소유 |
| BDD | experiment-local implemented — genuine neutral owner decision 없으면 fail closed; 실제 participant/TTY flow 성공 주장 없음 |
| TDD | added — existing-runtime.test.mjs7 grouped checks; SDD/BDD/SSOT/DDD 판단을 이 표에 함께 보존 |
| ADR | no independent delta — 새 runtime/security/grader architecture·study protocol 채택 없음 |
| SSOT | observed metadata only — 실제 로컬 catalog/model/defaults와 auth 자료 존재 확인; credentials/global config ownership·값 변경 없음, invoice/유효성 unknown |
| Planning | updated — 실제 연결 CHECK 승인 이행과 실제 실행/spend/limits/thinking 채택·독립 검수 미완료를 분리 |

Implementation map: `experiments/v2-isolated-execution-01/existing-runtime.mjs#loadInstalled,#inspectMetadata,#resolveRuntime,#terminalDecision,#parseOwnerDecision,#approvePlan` → installed SDK `ModelRuntime.create/getModel`, `ReadOnlyAuthStorage.list/modify`, `SettingsManager` default getters → unchanged `live-launch.mjs#main` / `live-sdk.mjs#createLiveSession` / `live-controller.mjs#approveScope`; protection `existing-runtime.test.mjs` → fresh `{run.json,focused-stdout.bin,metadata-stdout.bin,metadata-config.bin,launch-preflight-run.json,manifest.json,post-return-audit.json}` → [assigned evidence](../evidence/v2-existing-runtime-connection-01.md). 최종 primary/report/source snapshot과 별도 return audit는 같은 새 artifact directory에서 구분한다. Rule placement: 기존 primary에만 실험-local 사실을 수렴, 별도 canonical layer/graph/policy 승격 없음. Record-lint2/legacy graph37 guided migration pending·미변경이며 별도 승인 시 재개 가능하다.

Discovery capture: Planning=updated(세 수정 수용과 실제 연결/실행 전제 분리); SDD/BDD/TDD=기존 범위의 검수 근거 재사용; DDD/ADR/SSOT=none(실제 인증·요율·운영설정이나 새 규칙을 확정하지 않음).

- 같은 명시 승인 범위의 세 결함만 수정했다. `live-controller.mjs#runComparison`은 반환된 grader raw stdout/stderr와 metadata를 보존한 뒤 code0/groupGonefalse도 `cleanup-unconfirmed`로 latch한다. spawn/timeout/signal/error는 `grading-infrastructure-failure`, capture 자체 throw는 `integrity-or-grading-failure`로 나머지 runtime/행을 막는다. cleanup 확인·reason 없는 nonzero exit는 `functional-failure`로 별도 유지하고 faithful followup 가능하다. 실패한 역사 결과나 public4/private71·320/exact-int/Mapping 과제는 바꾸지 않았다.
- Row wall은 controller가 row directory/packet setup 전부터 소유하며 SDK/import/setup·approval wait·실행·close·freeze·grade·row/result/final persistence를 포함한다. `live-sdk.mjs#createLiveSession`에 같은 deadline/signal을 전달하고, `isolation.mjs#captured`에는 동기 준비 직후 process 생성 전 `beforeSpawn` checkpoint만 추가했다. 동기 filesystem/SDK 작업은 preempt 불가하므로 전후 검사로 overrun을 검출한다. SDK async 기다림은 abort+grace, 실제 local grader는 capture close/cleanup 반환까지 기다리며 child를 Promise race로 버리지 않는다. 숫자 wall 내 hard 종료/OS hang·원격 요청·청구 종료 보장은 없다. 마지막 exclusive write 도중 초과는 returned status에만 남을 수도 있으며 earlier snapshot을 소급 rewrite하지 않는다; `persistence-final.json`과 returned status를 함께 검수한다.
- `live-sdk.mjs#supportedConfig,#preflight`: clone/persistence/resolver 전 config/model/metadata/approval/limits/rates exact key schema, bounded strings/numbers/input enum 및 endpoint HTTP(S)/userinfo·query·fragment 금지를 집행한다. credential/header/extra fields와 arbitrary query는 generic value-free 오류로 거절한다. 실제 auth/config 조사 없음; 허용된 설명 문자열/path에 비밀을 숨기지 않을 책임과 provider raw diagnostics sanitation은 trusted runtime/owner 소유다. 실제 secrets는 runtime interface로만 주입한다.
- **한 coherent focused batch 23 passed / 0 failed / 4884ms**, actual installed SDK + injected NO-NETWORK runtime. 기존16 checks와 새7 grouped protections에서 schema17 variants, grade metadata5 faults, functional/throw 분리, lifecycle15 checkpoints, resolver/approval 실제 timer, actual captured local timeout/cancel/pre-spawn abort/row-wall을 검사했다. Metadata/expiry seams는 synthetic이며 해당 failures를 live에서 관찰했다고 주장하지 않는다. 실제 local child가 있는 새3 cases는 groupGone true, pre-spawn case는 spawned false; actual participant/provider/paid calls0. Native17 receipts/34 raw streams 연결 확인. 연구 조건/중립 승인/five tools/영수증 및 별도 실행·지출 승인 불변.
- `artifacts/live-sdk-correction-01`: 명시 regular 원본16개를 `.bin` baseline으로 먼저 보존했다(이전 reports/results/diagnostic config 포함). 한 번의 별도 tool-return 이후 audit에서 fresh manifest **2044 files / drift0**, baseline copies16 unchanged, 당시 original 변경은 의도한 source/test/docs5개뿐이다. 이후 이 primary/report는 최종 source snapshot으로 구분한다. 과거 tree 재귀/FIFO/symlink/원본 수선/삭제 없음. 기존 `.pi-lens.json` artifact-only diagnostic ignore 불변이며 Git ignore라고 주장하지 않는다. Git staged-empty/기존 dirty state 유지; full validators/install/global config/commit/upload 없음.

| Correction Discovery layer | 판단 / 소유권 |
|---|---|
| DDD | reuse / no independent delta — exact int(bool/subclasses 제외), general Mapping 구조·타입·입력 불변 및 합격 case 기준 유지 |
| SDD | experiment-local correction — cleanup latch, 전체 lifecycle wall, supported nonsecret input schema; 이 primary와 `LIVE-SDK.md` 소유 |
| BDD | experiment-local correction — infra/cleanup/wall 후 다음 행 차단, 정상 기능 실패와 구분; 실제 participant flow 실행 아님 |
| TDD | updated — `live-sdk.test.mjs`23 grouped protections; 이 표로 SDD/BDD/SSOT/DDD 판단을 함께 보존 |
| ADR | no independent delta — security/grader/runtime architecture·protocol 변경 없음 |
| SSOT | reuse / no independent delta — 실제 auth/model/rates unknown, diagnostic config 및 credential ownership 유지 |
| Planning | updated — 승인된 세 수정과 실제 무과금 evidence를 수렴; 독립 검수와 live dependencies/execution/spend 승인은 미완료 |

Implementation map: `live-controller.mjs#runComparison` → `live-sdk.mjs#supportedConfig,#preflight,#createLiveSession` → `isolation.mjs#captured`의 checkpoint → `live-sdk.test.mjs` → [correction evidence](../evidence/v2-live-sdk-correction-01.md) 및 fresh `{run.json,focused/summary.json,focused/manifest.json,post-return-audit.json}`. Rule placement: 기존 primary 하나에만 bounded experiment correction을 수렴; 별도 canonical layer/graph/policy 승격 없음. Record-lint2 / legacy graph37 guided migration은 pending·미변경이며 별도 승인 시 재개 가능하다.

이 최신 checkpoint는 아래 카드의 ‘live adapter 없음/연결 준비 승인 요청’ 시점 설명을 대체한다. 과거 카드/동결 protocol/실패·영수증은 수정하지 않는다. 승인된 **project-local adapter/controller 구현**은 수행했다. 실제 참가자/인증/provider availability/지출 성공으로 승격하지 않는다. **현재 live model/thinking/auth/가격은 unknown이고 실제 4행 실행은 여전히 미승인**이다.

- `experiments/v2-isolated-execution-01/live-sdk.mjs#preflight,#createLiveSession`: 명시적 owner execution/spend/overshoot 승인, 모델·thinking·비밀 없는 pricing/accounting metadata, 양수 한도와 resolver/approval callback을 검증한 뒤에만 trusted runtime resolver를 호출한다. Default auth/catalog/provider fallback은 만들지 않았다. 실제 SDK `createAgentSession` + injected runtime `streamSimple` 경로, empty loader, fresh in-memory session, builtin0/custom5, retry0. Read/list 이외 write/edit/python은 명시적 계획 승인 전 dispatch하지 않는다. 기존 sandbox/`dispatchWithReceipt` 원시 영수증을 재사용한다.
- `live-controller.mjs#approveScope,#runComparison`: A-initial → B-initial → B-followup → A-followup, 매번 fresh session. 실제 의존성인 중립 scope/criteria callback의 structured 승인/거절/최대 revision1만 상태에 반영하고 임의 prose를 권한/해법으로 해석하거나 모델에 전달하지 않는다. 승인 응답·시각·session/context/events/usage/실패/not-run을 보존한다. 기존 `initial/followup/Workspace.freeze/grade`로 own-condition allowed 파일만 그대로 인계; 초기 대화/평가 피드백·연구자 수선 없음. grader 실제 command와 raw 양 stream을 보존하고 모든 score는 independent-review-required; 의심/조작은 성공 제외다. 일반 개발 비교 범위는 확정됐으나 hostile same-interpreter grading은 해결하지 않았다.
- `live-launch.mjs#main` / `LIVE-SDK.md`: 실제 CLI `--preflight CONFIG.json TRUSTED.mjs`와 별도 승인 후 `--run CONFIG.json TRUSTED.mjs FRESH_ARTIFACT_DIR`; config 검증 전에 dependency import/auth/provider 접근 없음. Owner가 실험-local trusted runtime/auth resolver와 실제 human approval bridge, 비밀 없는 model/rates/accounting과 정확한 limit 승인 입력을 제공해야 한다. 이 파일들은 현재 제공되지 않았으며 credentials를 조사/출력하거나 placeholders를 ready 상태로 포장하지 않았다. Production runtime의 provider serialization/auth internals는 실제 호출 미검증이다.
- Limits는 채택값이 아닌 필수 승인 parameter다. Row wall에 setup·approval wait 포함, tool count/timeout 집행, reported usage 누락/threshold면 다음 호출·행 차단 및 abort 요청, output/dollar overshoot 원문 보존. $20/12000/40/10분은 계속 제안이다. In-flight hard dollar/output cap·원격 취소/청구 종료는 보장하지 않는다. Participant reported total과 invoice/외부 승인·검수·준비 비용 unknown을 분리한다.
- `live-sdk.test.mjs`: **한 번의 coherent no-model batch 16 passed / 0 failed / 4587ms**, actual installed SDK + 실제 bwrap + injected non-network stream/auth/metadata. 이전 no-cost factory를 호출하지 않았다. 신규 adapter의 37 injected stream/auth dispatch와19 runtime resolutions에서 five tools/원시 invalid UTF8/operation failure/사전 거절/중립 승인·거절·revision/missing usage/overshoot/tool/time/cancel/storage collision/4행 identity·faithful handoff/not-run을 검사했다. Real providers/paid probes/실참가자 호출0. 이는 wiring 증거이며 fixture 승인을 사용자 live 승인으로 보지 않는다. 별도 재시도나 broad validators 없음.
- `artifacts/live-sdk-connection-01/{baseline.json,baseline-*.bin,run.json,stdout.bin,stderr.bin,focused/summary.json,focused/manifest.json,post-return-audit.json}`: tool-return 이후 명시 fresh regular463파일과 baseline 사본9개 무결성 확인, baseline original drift0(이 primary checkpoint 추가 전), Git index unchanged/empty. 과거 FIFO/symlink 또는 old tree 재귀 read/수선 없음. 이 시점 이후 primary 의도 변경과 새 source/report는 별도 final snapshot 대상으로 구분한다.

| Discovery capture layer | 판단 / 소유권 |
|---|---|
| DDD | reuse / no independent delta — exact int(bool/subclass 제외), general Mapping 입력 구조/타입·불변, 공개4/private71·320 기준 불변 |
| SDD | experiment-local implemented delta — live factory/preflight/trusted dependency/receipt gate 계약, 이 primary와 `LIVE-SDK.md` 구현 map 소유 |
| BDD | experiment-local implemented delta — four-row fresh own-condition handoff 및 중립 승인 상태, 실제 사용자/모델 실행 성공 주장 없음 |
| TDD | experiment-local added protection — `live-sdk.test.mjs`16개 focused checks; 이 표의 SDD/BDD/SSOT/DDD 판단 포함 |
| ADR | no independent delta — 새 security/grader/runtime architecture 채택 없음 |
| SSOT | no independent delta — 전역/프로젝트 config 변경 없음; actual runtime/auth/pricing unknown 유지 |
| Planning | updated — local implementation 완료와 독립 검수/실제 launch 의존성·별도 실행/한도/지출 승인 미완료를 분리 |

Implementation map은 위 실제 source symbols → `live-sdk.test.mjs` → [assigned live evidence](../evidence/v2-live-sdk-connection-01.md)로 연결한다. 이 bounded experiment-local delta는 primary에만 수렴하며 다른 canonical layer/graph/policy로 승격하지 않는다. Accepted [SDK receipt review](../evidence/v2-sdk-receipt-completion-review-01.md)의 기존 두 P2 수용/취소 한계를 재사용했고 역사 결과를 소급 수정하지 않았다. Record-lint2 / legacy graph37 migration은 미변경·pending; 별도 승인 시 guided migration 재개 가능하다.

이 절은 최신 사용자 선택을 실행 절차로 구체화하는 **Planning amendment**다. 아래 과거 protocol/history와 동결 pilot manifest/`evaluator/PROTOCOL.md`는 수정하지 않는다. 일반 개발 비교 선택은 확정됐지만 transport·계량 위험·참가자/지출 승인은 확정되지 않았다. 과거 hostile-grade 실패는 그대로 실패이며 보안 문제가 해결됐다는 뜻이 아니다.

### 운영 개정 (참가자 실행 전 채택할 제안)

- 순서는 **A initial → B initial → B followup → A followup**, 한 과제·4개 배정 행·각각 fresh SDK session이다. 모델/thinking/도구/요구·합격기준은 동일하다. 초기에는 future/evaluator/상대 조건/history를 주지 않는다. 후속에는 같은 조건의 허용된 frozen code/tests/records/evidence만 정확히 인계하고 초기 대화·평가 결과·연구자 요약/수선은 제외한다. B는 T1을 이어가며 A의 좋은 task table도 금지하지 않는다.
- 승인자는 양쪽에 같은 scope/criteria-only 기준을 적용한다. 구현 전 계획 승인, 최대 1회 중립적인 revision 요청, 승인 답변·대기/수정 시간·usage 원문 보존. 해법/숨은 case hint/조건별 조언은 금지한다. 해결 못한 scope 이탈은 정지·해당 행 실패/미실행 사유로 남긴다. 비밀 평가 결과로 후속 참가자를 코칭하지 않는다.
- host sandbox·평가/미래 정보 비노출·원본 보존을 유지한다. 실제 공개4개 및 private 초기71/후속320 cases와 **exact Python int(bool/subclass 제외), 일반 Mapping의 구조/타입·입력 불변** 기준은 그대로다. 값만 비교하는 JSON 대체나 fake pass receipt는 불가하다. 별도 bwrap 채점도 participant와 oracle가 같은 Python이므로 출력은 advisory이며 의도적 위조 방어를 보장하지 않는다.
- 평가자 전용 raw response/context/events, 실제 command/status, 분리 stdout/stderr 원시 bytes·hash·truncation·exit/signal/timeout/abort/cleanup, 승인 대화와 frozen 산출물을 보존한다. 독립 검수자는 코드/공개검사 수정/기록 시점과 실제 로그를 대조한다(코드는 가능하면 조건명 익명화, 기록 형식은 완전 blind 불가). stdout의 pass만으로 성공을 부여하지 않는다. 조작 증거는 `tampering-failure`, 의심이나 근거 부족은 `suspicious-unverified`로 **성공 제외**, 정상 기능 실패·infra·leakage·미실행과 구분한다. 전체4행을 유지하고 성공 조건만 재표집하지 않는다. 초기 코드가 깨져도 실행/인계 가능하면 그대로 후속에 주며, 불가능하면 후속 not-run 및 원인을 남긴다. 노출/오염/증거 손실/중단 실패 시 나머지는 not-run으로 보존한다.
- 제안 한도: 행마다 wall 10분(승인 대기도 포함), tool dispatch 40회, 보고된 누적 output 12,000 tokens, 승인 revision 1회, 자동 retry 0회. 총 US$20는 **보고 usage 기준 다음 호출 중단 threshold 제안이지 최대 청구액이 아니다**. 승인 대화·실패·취소·검수의 비용도 포함/분리 명시하고 미보고 비용은 unknown이다. 타이머 abort와 다음 dispatch 차단은 연결 구현/검수가 필요하며 현재 factory의 3초 tool timeout·64KiB capture를 이 한도와 혼동하지 않는다. 보고 token/비용 threshold 도달 또는 계량 누락 시 다음 호출/행을 시작하지 않고 진행 중 abort를 요청한다. In-flight dollar/output cap·원격 과금 종료는 미지원/미입증이다. 실제 synthetic abort 뒤 두 번째 context/한 native result가 발생했으므로 완전 종료를 약속하지 않는다. 이 위험 완화는 아직 사용자가 승인하지 않은 별도 protocol 제안이다.

### 지금 가능한 경로와 ONE next approval bundle

**지금 4개 참가자 작업을 실행할 수 없다.** `experiments/v2-isolated-execution-01/no-cost-sdk.mjs#createNoCostSession`은 실제 설치 Pi SDK `createAgentSession`을 사용하지만 synthetic-only다: scrubbed env, network fetch 차단, empty credentials/modelsPath:null, 가짜 모델/0 usage, real provider methods 거절, script stream, thinking off. `isolation.mjs`의 packet/tools/freeze/followup/grade와 `sdk-receipts.mjs` 영수증은 재사용 후보이지 live adapter가 아니다. 이 경로는 pi-subagents child launch와 다르며 기존 부모/검수 transport를 바꾸지도 않는다. 참가자용 project-local SDK transport의 사용자 승인이 필요하다.

비밀 없는 metadata lookup은 이 작업에서 기존 feasibility의 문서화된 `/subagents-models` registry inspection 경로와 현재 제공 tool interface 확인까지만으로 제한했다. 이 worker에는 그 registry command/tool이 직접 노출되지 않아 실행하지 않았다. 사용자 제공 parent registry의 `openai-codex/gpt-6-astra` 등재는 선택 단서만이다. 실제 experiment SDK effective model/thinking, auth 가용성 및 input/output/cache 요율·청구 방식은 **unknown**. synthetic cost 0은 가격 증거가 아니다. auth 파일/전역 settings dump/paid availability probe/추가 catalog source dig를 하지 않았다.

**다음 승인 요청 하나: project-local SDK 실모델 연결 준비만 승인 (Recommended).** 범위는 새 실험-local live-provider adapter/controller에 기존 sandbox 5 tools·empty context loader·receipt·fresh session·중립 승인 흐름·사전 dispatch count/시간/보고 usage 중단을 연결하고, 기존 no-cost factory/동결 pilot/역사 산출물은 그대로 두는 최소 변경이다. 실제 provider 접근과 credential resolution은 참가자 도구가 아니라 신뢰 controller 소유로 한정한다. 안전한 기존 credential interface 및 비밀 없는 effective model/요율 metadata가 직접 제공되지 않으면 추정/파일 조사 없이 해당 prerequisite에서 정지한다. 설치·전역 설정·pi-subagents patch·새 grader/security framework는 제외한다.

- 준비 예산 제안: 구현+무과금 focused 검사 **1 batch** 최대40분/구현 도구 호출40회, 독립 source/log 검수 **1회** 최대20분/검수 read-only 도구 호출20회; 실모델/provider/참가자 호출 **0**, 유료 probe **0**, 새 live adapter는 **이 카드 작성으로 승인되지 않음**. 실패 시 재시도/추가 연구 대신 원인과 현재 산출물만 반환한다.
- 이 한 묶음은 **연결 준비 승인만** 요청한다. 위 4행/40분 작업·US$20 reported threshold·overshoot 위험·model/thinking/가격의 실제 선택은 준비 검수와 비밀 없는 metadata 확인 뒤 실행 승인 대상이다. 지금 알 수 없는 가격/인증을 채워 넣거나 조건부 유료 실행을 자동 시작하지 않는다. 이는 불가피한 live connection prerequisite이며 일반 보안 연구를 재개하는 제안이 아니다.

### Discovery capture — all 7 / source and evidence map

| Layer | 판단 | 범위/소유권 |
|---|---|---|
| DDD | reuse / no independent delta | exact-type/Mapping 과제 기준 불변 |
| SDD | proposed operational amendment | SDK 참가자 transport·승인/계량 연결은 위 단일 승인안; 소스 변경 없음 |
| BDD | proposed operational amendment | A initial/B initial/B followup/A followup, 중립 승인·fresh 인계·4행 유지 |
| TDD | reuse + audit proposal | 실제 기존 checks 유지; 조작 의심 성공 제외·독립 코드/log 대조; 새 검사/실행 없음 |
| ADR | no independent delta | 보안 구조/전역 runtime 결정 없음; 일반 개발 범위 선택의 이유는 이 primary 소유 |
| SSOT | no independent delta | 모델/가격/auth unknown; 환경/정책 변경 없음 |
| Planning | updated | 사용자 확정 범위와 아직 미승인 운영 threshold/최소 연결 승인안을 구분 |

Implementation/evidence map: `experiments/v2-recording-method-pilot-01/evaluator/PROTOCOL.md`(동결 순서·승인·채점/한도 역사), `experiments/v2-isolated-execution-01/{README.md,no-cost-sdk.mjs#createNoCostSession,isolation.mjs#initial,#followup,#Workspace.freeze,#grade}`(현재 연결과 한계), `.lazy-harness/tests/test-strategy.xml`(불필요 재검증 금지), [SDK receipt completion review](../evidence/v2-sdk-receipt-completion-review-01.md)(두 P2 수용, 실제 post-abort continuation 및 raw stream audit), [feasibility](../evidence/v2-recording-method-execution-feasibility-01.md)(documented registry inspection와 비용 의미), [최종 카드 보고](../evidence/v2-general-development-execution-card-01.md). 기존 preparation/hostile-grade/무결성 실패 근거는 아래 역사 링크를 그대로 재사용하며 이번에 재검사했다고 주장하지 않는다.

Rule placement: 이 primary의 실험-local 계획만 수정; 다른 canonical layer/graph/policy로 승격하지 않는다. 기록 전용 지시로 tests/model/provider/참가자/전역 validators 실행 없음. 기존 dirty state와 staged-empty 상태를 보존한다. record-lint2 / legacy graph37 이주는 pending이며 이 작업에서 손대지 않았다; 별도 승인 시 guided migration을 재개할 수 있다.

## Discovery capture — 격리 연결 검수 후 보완 계획 / STOP 반영

현재 판단의 정본 근거는 [격리 연결 독립 검수](../evidence/v2-isolated-execution-review-01.md)와 [구현·사건 보고](../evidence/v2-isolated-execution-implementation-01.md)다. 아래는 구현 완료나 새 전역 정책의 채택이 아니라 검수 발견과 보완 backlog의 Planning 캡처다.

### 확인된 발견과 미확인 경계

- 검수 P1: `experiments/v2-isolated-execution-01/grade.py.txt`의 검색 경로 순서로 참가자의 `test_public.py`를 고른다. 평가자 원본 파일이 읽기 전용이어도 그 원본이 실제 실행됐다는 증거는 아니다. 같은 인터프리터의 참가자 import/채점 위조 위험은 별개의 미해결 문제다.
- 검수 P2: `no-cost-sdk.mjs`의 SDK 도구 반환 경로는 stdout/stderr를 문자열로 합치고 실패를 예외로 바꿔 원시 바이트·스트림 구분·전체 종료 영수증을 보존하지 못한다. 직접 tool 검사 경로의 보존을 SDK 전체로 일반화하지 않는다.
- 동결 원본: 새 합성 A/B 자료의 `evidence/validation.md` 두 파일이 도구 반환 뒤 변경됐다. 검수는 현재 해시 불일치를 확인했다. 기능 검사13개 통과와 현재 동결본의 불일치를 함께 유지하며 과거 원본을 수선/정규화하지 않는다.
- 자동 진단의 자료 변경 경계를 통제해야 한다. 제외 설정/보관 방식의 실제 지원·효과는 아직 선택/검증되지 않았다. SDK controller 전체·실제 provider·참가자 프로토콜/비용 통제의 실행 가능성도 미확인이다.

### 순서가 있는 보완 backlog — 경계·공개 출처·SDK 보완 완료, hostile grading BLOCKED

1. 실험 산출물에 한정한 자동 진단 쓰기 경계를 조사하고, 최소 지원 방식의 무과금 canary를 도구 반환 뒤 해시까지 확인한다. 전역 진단 중단·실제 source 오류 은폐는 하지 않는다.
2. 1이 확인된 뒤 평가자 공개 검사 출처 고정 및 신뢰하는 채점기와 참가자 실행 분리를 보완한다. 기존 과제/정답은 바꾸지 않는다.
3. SDK 각 도구의 성공·실패에 evaluator-only 원시 stdout/stderr·해시·전체 종료 상태·호출 연결을 보존한다. 표시용 문자열과 원시 증거를 구별한다.
4. 한 coherent 무과금 검증과 독립 검수로 실제 동작·원본 보존·잔여 한계를 확인한다. 참가자/유료 실험 실행 승인은 포함하지 않는다.

### 승인 및 중지 상태

사용자 ‘진행해봐봐’는 위 보완 순서 진행 승인으로 받았으나, 이어진 **STOP / Discovery capture 요구로 현재 구현은 중단 상태**다. `e52db036-0c81-49b5-865b-324dba294ad4`의 writer `cf081da5-9728-4fb8-975e-fb455848ee61`에 중지 지시 후 interrupt했고 상태 조회에서 `paused`, `Process terminal: observed`를 확인했다. 최종 workflow 실패는 사용자 중지에 따른 것이며 새로운 코드/기능 실패로 해석하지 않는다. 후속 reviewer는 실행되지 않았다.
하위 작업자는 source/config/probe/test/primary/evidence의 의도적 변경 없이 조사만 수행했다고 보고했다. map의 생성 cache rebuild는 별도 자동 부수 효과다. 기존 dirty `candidates.jsonl`, `graph.jsonl`, `logs/validations.jsonl`, `ssot/policies.json`은 이번 수정으로 귀속하거나 되돌리지 않는다. 기록 보완 뒤 자동 재개하지 않는다.

재개 승인: 위 Discovery capture 보완 후 사용자가 ‘빨리 제대로 진행하라고’로 명시적으로 재개를 지시했다. 기록된 보완 순서와 기존 범위/금지사항을 그대로 유지하여 중단된 writer 맥락에서 이어간다. 이미 확보한 근거를 재사용하며, 새 범위·권한 결정이나 실제 실행 차단이 없는 한 중복 승인 질문으로 멈추지 않는다.

### Correction 01 재검수 후 같은 범위의 잔여 보완

최신 SDK closure: [receipt-completion 독립 검수](../evidence/v2-sdk-receipt-completion-review-01.md)가 저장 실패 노출/취소 native 연결의 두 P2를 수용했고 같은 범위의 신규 P0/P1/P2는 없었다. 첫 실행의 취소 context 개수 가정 실패는 보존했고, 별도 승인된 무과금 재검증은 실제 SDK+합성 provider13 dispatch로 통과했다. 검수는113개 명시 artifact 무결성과10 receipt/20 raw streams의 연결을 대조했다. 참가자 실험/가격/전체 종료 보장이나 악성 Python 채점까지 승인한 결과는 아니다.
남은 실질 결정 후보: 본 연구를 일반 개발 작업의 후속 활용에 한정하여 코드·로그 독립 검수와 조작 의심 결과의 별도 분류를 사용하는 제한된 예비시험으로 재정의할지, 의도적 Python 채점 위조까지 견디는 독립 채점기 개발을 먼저 승인할지 사용자 확인이 필요하다. 전자는 현재 hostile-grading gate의 명시적 변경이며 자동 채택하지 않는다. 후자는 새 보안/평가 구조의 범위 승인이다. 양쪽 모두 host sandbox·원본 보존·실행/지출 승인까지 없애는 안은 아니다.

사용자 확정: 옵션 **‘일반 개발 비교 (Recommended)’**를 선택했다. 이후 예비시험은 일반 개발 작업의 기록·후속 활용 비교로 한정하며, 의도적인 Python 채점 위조를 완전히 방어한다는 보장은 제외한다. host sandbox·평가 자료 비노출·원본 보존·실제 기능검사·코드/로그 독립 검수는 유지한다. exact Python int 및 Mapping 입력 보존 등 기존 과제 기준은 바꾸지 않는다. 조작 의심 결과는 성공으로 처리하지 않고 실패/미확인의 근거를 보존한다. 이전 hostile-grading 실패를 해결/통과로 소급 판정하지 않으며, 실험 질문/위험 범위의 명시적 변경으로 기록한다. 실제 참가자 SDK/모델 경로와 실행·비용 조건은 아직 별도로 확정해야 하고 유료 실행은 시작하지 않는다.
Discovery capture(선택 반영): Planning=updated; SDD/BDD/TDD=candidate(일반 개발 인계·검증·조작 의심 처리의 protocol 개정 필요); DDD/ADR/SSOT=none(제품 규칙·새 보안 구조·환경설정 변경 없음).
Discovery capture: Planning=updated(두 P2 closure 및 다음 결정 후보), SDD/TDD=candidate(평가 신뢰 범위/조작 의심 처리 또는 독립 채점 계약), DDD/BDD/ADR/SSOT=none(아직 선택/정책/설정 변경 없음).

[독립 correction 검수](../evidence/v2-isolated-execution-correction-review-01.md)는 실험 artifact-only 진단 경계의 관찰과 공개 검사 출처 고정을 수용했다. 저장된 focused4검사 통과와 post-return165파일 무결성을 실제 참가자 성공으로 승격하지 않는다. SDK 원시 영수증 보완은 두 P2가 남았다: (1) `sdk-receipts.mjs` 저장 실패가 SDK에 평가자 절대경로를 노출할 수 있음, (2) 취소 분기에서 native call/event/context 및 종료 연결 근거를 저장하지 않아9개 정상분기와 같은 주장을 할 수 없음. 이는 기존 승인된 ‘SDK 성공·실패 원문/전체 receipt 연결’의 미완료 경로로서 같은 범위에서 수정·무과금 검사·재검수를 이어간다. 새로운 C/RPC/악성 Python 채점 구조나 유료실험·프로토콜 전환을 승인한 것으로 해석하지 않는다.
Discovery capture: Planning=updated; SDD=candidate(저장 실패의 안전한 오류 경계·취소 호출 연결), TDD=candidate(저장 실패 주입·취소 native 증거 보호), DDD/BDD/ADR=none, SSOT=none(기존 artifact-only config 변경 없음). 검수가 확인한 primary의4개 빈 줄 차이는 과거 해시와 함께 유지하고 과거 closure를 소급 수정하지 않는다. 원문 검수 report와 이전 실패/사건은 유지한다.

| Layer | 판단 | 이유 / 남길 위치 |
|---|---|---|
| DDD | none | 새로운 제품 도메인 개념/규칙을 확정하지 않음 |
| SDD | candidate | 공개 검사 출처, SDK 원시 영수증, oracle/participant 경계의 계약 보완 후보 |
| BDD | candidate | 같은 조건 인계→분리 채점 및 실패/원본 유지 흐름 후보 |
| TDD | candidate | 공개 테스트 교체·원시 UTF-8/실패 로그·post-return 무결성 회귀 보호 후보 |
| ADR | none | 전역 runtime/참가자 프로토콜/저장 방식 채택 없음 |
| SSOT | candidate | 실험 산출물의 진단 제외/보존 경계 설정은 선택·검증 전 |
| Planning | updated | 검수 근거, 보완 순서, 승인 범위와 STOP/미수행 상태를 이 primary에 누적 |

Rule placement: 기존 AGENTS §2.4/ADR0034를 따르는 캡처이며 새 operating rule을 복제하지 않는다. 후보를 각 layer의 확정 규약으로 승격하지 않는다. #24 바이너리 정적 검증과 legacy graph migration은 이 보완과 분리한다.

### SDK receipt completion 01 — same-scope P2 correction checkpoint

- User-approved scope remains only evaluator persistence-error sanitization and cancellation-native receipt linkage. `sdk-receipts.mjs#dispatchWithReceipt` now latches persistence failure, retains evaluator-only in-memory diagnostics/result with explicit `incomplete`/`failed` status, and throws a path-free error. This is not complete disk preservation: partial exclusive writes remain, no failed receipt is added to the complete list. `no-cost-sdk.mjs#createNoCostSession` prevents subsequent synthetic provider context/dispatch after that latch. No grader, config, exercise or provider protocol change.
- First focused run: failed / 1371ms at the new cancellation `contexts.length === 1` assertion (actual 2). Nine normal dispatch checks passed; cancellation raw receipt remained, but native cancellation export was not reached and storage-fault cases were **not run**. Old failed artifacts are preserved, not retroactively filled. Supervisor expressly authorized one additional bounded no-cost run, correcting the unsupported one-context assumption and exporting actual cancellation evidence before assertions.
- Additional focused run (`artifacts/sdk-receipt-completion-01/retry-01`): passed / 1478ms; 13 actual SDK synthetic dispatches: five successful tools, two operation errors, timeout, output limit, cancellation, three exclusive-write storage failures (`stdout.bin`, `stderr.bin`, receipt JSON). EEXIST diagnostics remain evaluator-only; each failed-persistence session retained zero complete receipts, one incomplete failure, one context and one dispatch; native tool error is path-free and scripted continuation did not execute. No real disk exhaustion/permissions change, provider/participant/model calls or broad validators.
- Cancellation now retains actual calls/messages/events/all contexts, native result presence, abort-request/return and prompt-return chain; receipt call ID/tool/request hash matches the native call, and any native result/end event is compared rather than invented. **Observed native result is present (one), with two contexts**: the second contains user/assistant/toolResult after cancellation. This synthetic post-abort continuation is retained explicitly; it is not proof of complete provider/spend termination. Receipt reports aborted, cancellationRequested and groupGone, with separate capped raw stdout/stderr.
- Separate post-return audit: first-run 62 named regular files and retry 51 all unchanged; 15 baseline `.bin` copies unchanged; live baseline drift was exactly the three intended source files before this primary update; Git index unchanged. No old tree recursion/FIFO/symlink reads, old closure repair, or four-blank-line history normalization. Actual baseline-relative diffs and detailed checks are retained in the completion artifact directory; report: [SDK receipt completion evidence](../evidence/v2-sdk-receipt-completion-01.md).

| Layer | SDK completion assessment |
|---|---|
| SDD | experiment-local completion of approved safe persistence boundary and truthful native cancellation linkage; primary owns this bounded delta |
| BDD | no independent delta; no real participant/product flow, same synthetic exercise/tools |
| SSOT | no independent delta; existing artifact-only ignore unchanged |
| DDD | no independent delta; exact-type/Mapping and expected grading cases unchanged |
| TDD | updated `correction-sdk-probe.mjs` protects native cancellation chain and three actual-SDK storage collision paths; first failed assumption and retry evidence preserved separately |

Discovery capture: reuse approved Correction01 remaining-work scope; same primary updated with observed results and correction reason, no layer promotion/new operating rule/graph migration. Implementation map: `sdk-receipts.mjs#dispatchWithReceipt` → evaluator failure latch/diagnostics; `no-cost-sdk.mjs#createNoCostSession` → fail-closed stream/dispatch boundary; `correction-sdk-probe.mjs` → normal/error/abort/storage-failure native protection; `artifacts/sdk-receipt-completion-01/{focused.mjs,focused-retry.mjs,post-return-audit.json}` → bounded runs and separate integrity evidence. Independent review is still required. Hostile same-interpreter grading, real participant/controller protocol, provider serialization/auth/accounting, remote cancellation and US$20/12000/40/10min approval remain BLOCKED/unproven. Record-lint2/legacy graph37 remain untouched; guided migration can resume only under separate approval.

### Correction 01 — partial correction / hostile grading still BLOCKED

- 최신 재개 승인은 위 문서 상단에 있음을 직접 재확인했다. tail만 읽고 누락으로 질문했던 것은 위치 탐색 오류이며 새 승인/중복 capture가 필요했던 사실이 아니다.
- 실제 설치된 `pi-lens/docs/globalconfig.md`의 project `ignore`와 `dist/clients/runtime-tool-result.js`의 `isPathIgnoredByProject` 선행 return, `file-utils.js#getProjectIgnoreMatcher`를 확인했다. 새 root `.pi-lens.json`은 `experiments/v2-isolated-execution-01/artifacts/**` 하나만 제외한다. 전역 설정/설치 runtime은 읽기 전용이며 실제 source 3개는 matcher상 제외되지 않는다.
- `artifacts/correction-01/canary-before.json`→별도 tool-return 이후 `canary-after.json`: harmless Markdown/Python 두 canary의 원시 해시 유지, bounded baseline 16개 사본 및 원본 모두 일치. Python canary는 실행/import하지 않았다. 이 결과는 해당 도구 반환 구간의 제외/보존 증거이며 모든 미래 host writer나 agent_end의 면책 증명이 아니다.
- 새 채점 분석 blocker: 기존 expected-value checks는 정확한 int 타입 및 일반 Mapping 입력의 구조/타입 불변까지 검사한다(`evaluator/hidden_checks.py#check,#snapshot`). 단순 subprocess JSON RPC로 parent가 기대값만 비교하면 이 두 조건을 신뢰하지 못한다. 참가자와 같은 Python의 직렬화/after-snapshot 보고를 신뢰하면 monkeypatch/introspection 또는 forged protocol로 관측을 위조할 수 있다. 기존 71/320 cases와 공개 4개를 값 비교만으로 축소하지 않는다. 안전한 bounded separation의 구체 구현/증명이 없어 grader/receipt 변경 전 정지 판단을 supervisor에 전달했다. Supervisor는 exact-type/입력 구조 조건을 약화하지 않고 **공개 출처 고정과 독립 SDK 영수증만 계속 완료**하도록 승인했다. 새 RPC/C/runtime 설계는 하지 않으며 hostile grading은 BLOCKED다.
- Preservation: old artifact tree를 재귀 읽기/복사하지 않고 명시한 regular 파일 16개만 ancestor lstat + O_NOFOLLOW/O_NONBLOCK + descriptor fstat로 `.bin` 보존했다. FIFO/symlink 내용은 열지 않았고 historical mismatch/log/receipt를 수선하지 않았다. Git 원상태는 `git-{status,diff,index,head}.bin`에 보존했다.

| Layer | Correction checkpoint assessment |
|---|---|
| SDD | bounded independent experiment delta: explicit evaluator public source/count and per-SDK-dispatch raw receipt contract; trusted hostile observation separation remains blocked |
| BDD | no independent product/participant flow delta; same five tools, synthetic dispatch only, errors displayed separately from evaluator receipts |
| SSOT | bounded independent delta: project `.pi-lens.json` excludes only this experiment's artifact tree; source findings retained |
| DDD | no independent delta; exercise rules/expected cases unchanged |

- Implementation map: `grade.py.txt`의 explicit `spec_from_file_location`은 `/trusted/test_public.py`를 선택하고 source/4-test count를 검사한다. 참가자 공개 파일 교체/삭제에도 초기71/후속320 unchanged private cases + 공개4개를 수행했다. 동일 Python의 oracle 위조 위험은 해결하지 않았고 `advisory_only: true`, `trustworthy_hostile_grade: false`를 유지한다.
- `sdk-receipts.mjs#createReceiptWriter,#dispatchWithReceipt`가 callId/tool/request hash와 별도 stdout/stderr `.bin`/SHA256 및 exit/signal/timeout/cancellation/spawn/cleanup metadata를 evaluator-only 저장한다. `no-cost-sdk.mjs#createNoCostSession`은 모든 실제 dispatch에서 표시용 UTF-8 변환/실패 전에 이를 호출한다. `sdk-probe.mjs`는 해당 receipt directory/행을 evaluator output에 연결한다. `isolation.mjs#captured`는 pre-abort/프로세스 실패도 구조화하고 관측 byte count/truncation을 명시하며 `#regular`는 no-follow/nonblocking descriptor type/identity를 재검사한다.
- Focused correction-only 실행 1회: `correction-verify.mjs`, 4 passed / 0 failed / 2.184s. `correction-sdk-probe.mjs` 실제 SDK dispatch 10개: success5, operation error2, timeout1, output-limit1, cancellation1; 양 스트림 invalid UTF8 bytes/hash 및 call 연결을 검사했다. pre-spawn abort/closed-workspace rejection/bwrap exec failure는 별도 direct supplements이며 실제 SDK coverage로 부풀리지 않는다. Synthetic provider만 사용했고 실제 모델/참가자/유료 호출은 없다.
- 별도 post-return safe audit: 새 focused regular artifacts 165개 전부 해시 유지; baseline `.bin`16개 전부 유지, 의도한 source/primary 변경 외 기존 원본 drift0; canary2 유지; Git index unchanged. 기존 FIFO/symlink와 옛 mismatches는 재귀 접근/수선하지 않았다. Source diagnostic clean 메시지는 형식 관찰이며 grader의 신뢰성 판정이 아니다.
- Remaining: trusted parent-side hostile Python grading 미구현; arbitrary host/agent_end writer/TOCTOU와 총자원/원격 취소 보증 없음. Native SDK controller는 host이며 synthetic stream 검사는 actual model serialization/auth/price 증거가 아니다. US$20/output12000/tools40/10min은 여전히 제안이고 participant/spend/protocol 승인 없음. Parent check/standard/full test 및 #24 repair는 실행하지 않았다.

Discovery capture: 새 blocker를 supervisor 보고 전에 이 primary에 먼저 누적했고, 위 제한적 계속 승인과 완료한 독립 delta를 같은 primary에서 갱신했다. Configuration 소유권은 host의 실험 artifact 제외만이며 global diagnostic policy가 아니다. 상세 closure는 [correction evidence](../evidence/v2-isolated-execution-correction-01.md)에 연결한다. Record-lint2/legacy graph37은 미변경이며 별도 승인 시 guided migration을 재개할 수 있다.

질문: **작업 중 만들어진 기록의 구조와 작성 절차를 바꾸면, 새로운 AI가 실제 후속 작업을 더 정확하게 이어가는가?**

소화·검색 모델·DB·분산 구조는 이번 비교에 추가하지 않는다. 이전 변경 추적03은 정리된 원문과 소화본의 읽기 실험이었다. 이번에는 실제 작업자가 기록을 만들고 다음 작업자가 실제 코드를 변경한다.

## 2. 확인한 V1 기준 — 약한 대조군 금지

현재 checkout의 `.lazy-harness/spec/platform/record-write-update-policy.md`는 다음을 요구한다.

- 기존 canonical record를 먼저 찾는다.
- 한 논리 작업의 primary narrative record를 기본으로 삼고, 독립 의미 변화가 있을 때만 다른 layer로 승격한다.
- 확인된 결정·계약·회귀·소유권 등을 저장하고, 필요한 digest·Implementation map·근거 연결을 유지한다.
- 반복 진행/검증 상세는 evidence capsule로 모으고 불필요한 중복 기록을 피한다.

또한 ADR0038은 기존 방식에도 요구사항 정리→계획→승인→구현을 요구한다. 따라서 **A에는 목적·완료조건을 주지 않고 B에만 주는 시험은 불공정**하다. 'V1=대충 쓰기/무계획'으로 정의하지 않는다.

이것은 현재 checkout에서 확인한 규약이다. 과거 특정 버전 V1 전체를 복원한 것이 아니며, 실제 에이전트가 언제나 준수한다는 실행 증명도 아니다.

## 3. 두 조건의 조작 — 검수 전 제안

| 항목 | A: 기존 문서 중심 기록 절차 | B: 목적·태스크 중심 기록 절차 |
|---|---|---|
| 요구사항·목적·합격 기준 | 동일하게 제공 | 동일하게 제공 |
| 작업 전 이해·계획 | 기존 requirements-first 절차 | 동일한 이해·계획에 더해 목적/태스크/완료조건의 지속 기록을 먼저 명시 |
| 진행 중 보존 | 확인된 정보를 적절한 primary 문서와 근거에 연결; 기록 위치·묶음은 기존 규약 범위에서 작업자가 판단 | 태스크 식별자·현재 계획/상태·변경 이유·결과/검증 참조를 같은 작업 단위에서 갱신 |
| 완료 판단 | 공통 외부 검증으로 평가 | 같은 외부 검증으로 평가 |
| 후속 AI가 받는 것 | 해당 조건의 코드·테스트·기록·공통 실행 근거 | 해당 조건의 코드·테스트·기록·공통 실행 근거 |

B의 파일명/스키마는 아직 고정하지 않는다. B에만 진짜 검증 영수증이나 더 강한 완료 차단기를 제공하지 않는다. A에 문서 수를 늘리도록 강제하거나 B에 기록 분량 상한의 특혜를 주지 않는다.

최초 비교는 **선별한 기록 절차의 효과**이며 설치된 V1 전체와 완성된 V2 제품의 비교가 아니다. A의 규약 추출이 부실하거나 양쪽 절차가 실질적으로 같으면 실행 전에 설계를 수정한다.

## 4. 실제 수행할 과제 후보

Python 표준 라이브러리만 쓰는 작은 실험용 코드로 시작한다. 실제 제품 필요 기능이라고 주장하지 않으며 테스트 실행을 흉내 낸 receipt는 쓰지 않는다.

| 과제 유형 | 최초 작업 | 후속 작업에서 확인할 것 |
|---|---|---|
| 설정 해석 | 값의 우선순위·허용 타입·기본값 처리 구현 | 정책 한 항목 변경 시 나머지 규칙·변경 이유를 보존하는가 |
| 배치 갱신 | 여러 입력 중 오류가 있으면 부분 반영하지 않는 동작 구현 | 중복 요청 대응을 추가하면서 원자적 동작·실패 보존을 유지하는가 |
| 결과 표시 | 입력 순서·중복·실패 결과를 구분하는 출력 구현 | 새 표시 요구를 반영하되 원래 입력과 처리 결과를 혼동하지 않는가 |

기존 Sol/Luna/변경 추적 시험의 정답이나 코드를 그대로 재사용하지 않는다. 구체 API·fixture·평가용 테스트는 실행 전 새로 검수하고 고정한다. 시드 코드에 필요한 요구 근거는 두 조건에 동일하게 제공한다.

## 5. 한 쌍의 실행 절차

1. 동일 초기 코드와 동일 요구 자료에서 A/B 전용 작업 디렉터리를 만든다.
2. 같은 모델·thinking·도구 접근·시간 한도로 fresh 작업자 둘이 각각 구현·기록한다. 조건 실행 순서는 교차/사전 고정하고 실패한 조건만 골라 교체하지 않는다.
3. 최초 결과의 코드·테스트·기록·실행 근거·실패를 그대로 캡처한다. 부모가 기록을 더 좋게 고쳐주지 않는다.
4. 별도의 fresh 후속 작업자에게 해당 결과와 동일한 후속 요청을 준다. 앞 작업자의 대화와 평가자 정답은 주지 않는다. 코드·테스트·기록은 실제 인계처럼 모두 볼 수 있다.
5. 후속 작업자는 실제 변경·검증을 수행한다. 평가자는 결과물과 공통 검증으로 정확성·제약 보존·완료 주장을 판정한다.
6. 원본→검수→집계→연구 기록을 보존한다. 기록 품질과 최초 코드 품질 차이를 따로 보고한다.

후속 요구와 평가용 정답은 최초 작업자에게 노출하지 않는다. 요구를 작업 도중 몰래 바꾸는 시험은 이번 첫 설계에서 제외한다. 이후 별도 변경 대응 단계로 분리한다.

최초 작업 실패도 표본에 남긴다. 실패 결과로 후속 작업이 성립하지 않으면 그 사실을 end-to-end 실패로 보고하며 성공한 쌍만 골라 비교하지 않는다. 기록의 이해 가능성에 대한 별도 평가는 가능하지만 전체 성공으로 승격하지 않는다.

## 6. 평가 기준 후보

우선순위는 신뢰도다. 형식 미준수·내용 누락·실행 오류·인프라 실패를 분리한다.

- 실제 작업 성공: 사전 고정한 동작 검사와 기존 회귀 검사가 충족되는가.
- 안전성: 제약 위반, 승인 없는 범위 확대, 근거 없는 완료/검증 주장이 있는가.
- 기록 충실도: 목적·변경 이유·현재 상태·실패·검증 범위가 실제 실행과 맞는가.
- 후속 활용: 필요한 이유/제약을 회수하여 실제 변경에 반영하는가. 필요한 확인과 불필요한 보류를 구분한다.
- 절차 준수: A/B에 지시한 기록 절차가 실제로 달랐고 수행됐는가. 불이행을 숨기지 않는다.
- 비용·시간: 최초 작업/기록과 후속 작업을 합산하고 준비·검수·중단 비용은 별도로 보고한다. 누락 usage를0으로 두지 않는다.

실제 코드 결과가 다르므로 후속 차이를 '기록 형식만의 순수 인과효과'로 단정하지 않는다. 코드 품질이 공통으로 통과한 쌍에 대한 보조 분석을 하더라도 전체 표본 결과를 함께 보고한다.

## 7. 예비시험과 본비교 경계

- 제안 예비시험: 한 과제 A/B 각1회, 최초 작업자2명+후속 작업자2명 = 실제 작업 호출4개. 검수/평가 호출은 별도다.
- 예비시험 목적: 규약 추출·차이·입력 비노출·원본 보존·실제 작업 평가가 공정하게 작동하는지 확인한다. 이 결과만으로 A/B 우월성을 주장하지 않는다.
- 예비시험에서 기준을 바꾸면 이전 결과는 그대로 보존하고 탐색 표본으로 남긴다.
- 본비교 후보: 서로 다른3과제×3반복×2조건×2작업 단계=36작업 호출. 별도 실행 승인을 받으며 예비시험을 편의상 섞지 않는다.
- 모델 후보: 양쪽 같은 `openai-codex/gpt-6-astra:high`. 이전 연구와의 비교 가능성보다 조건 간 동등성을 우선한다. 실제 가용성/해결된 설정은 실행 전 native preflight로 확인한다.
- 시간 후보: 작업 호출별 최대10분. 슬립/통신 오류의 원본과 수신 경과를 보존하며 실패 뒤 자동 재시도·다른 CLI 우회는 하지 않는다. 비용 상한과 전체 예산은 아직 미확정이다.

## 8. 보존 계획

연구 ID와 목적, 사전 규약/입력/검사 해시, 실제 요청/수행/원답/출력, 검증 결과, 실패/정정, 해석 한계, 다음 판단을 프로젝트 내부 record와 근거 묶음으로 연결한다. 모델 원본 답을 표시 파일에서 복구하거나 수정하지 않는다. 외부 세션 경로만 링크하지 않고 실제 보존 사본을 연결한다. 원격 업로드·커밋·삭제는 별도 권한이다.

## 9. 미해결 설계 질문 — 실행 전 검수 대상

- 현재 V1의 규약을 얼마만큼 추출해야 문서 중심 대조군으로 충실한가? 설치 runtime 전체 비교와 구별해야 한다.
- B의 최소 지속 태스크 표현은 무엇이며 A와 실질적으로 어떤 차이를 만드는가?
- 최초 실패가 후속 과제를 불가능하게 할 때의 채점·중단 기준은 무엇인가?
- 과제의 숨겨진 검사와 실제 의미 검수가 잘못된 해법/기록을 판별하는가?
- 예비시험의 시간·비용 한도와 적절한 첫 과제는 무엇인가?

## Implementation map

- `.lazy-harness/spec/platform/record-write-update-policy.md`: 현재 A 규약 근거; 본문 Rule digest/Purpose/mandatory triggers를 확인했다.
- `.lazy-harness/decisions/0038-requirements-first-change-gate.md`: 양쪽 모두 목적/요구/계획 정보가 필요하다는 근거.
- `.lazy-harness/tests/v2-task-contract-pilot.md`: 이전 합성 계약은 가짜 pass 허용 한계가 있어 실제 검증 대체물로 사용하지 않는다.
- `.lazy-harness/tests/v2-sol-recording-pilot.md`, `v2-sol-requirement-change.md`: 실제 작업·이력과 사전 정보 노출의 선행 관찰.
- `.lazy-harness/planning/v2-change-tracking-reliability-plan.md`: 이번 방향의 사용자 선택과 이전 읽기 시험의 한계.
- `.lazy-harness/planning/v2-research-test-map.md`: 전체 연구 목적/결과 및 보존 점검의 상위 연결.
- `experiments/v2-recording-method-pilot-01/README.md`: 승인된 evaluator-only 준비 묶음의 실제 파일/함수 map. 참가자 runtime/실행기는 만들지 않았다.
- `common/retries.py#resolve_retries`, `common/test_public.py#PublicTests`, `common/.lazy-harness/spec/retries.md`: 공통 stub·공개 검사·기존 primary seed (위 실험 경로 기준).
- `conditions/A.md`, `conditions/B.md`, `common/COMMON-PROCEDURE.md`, `evaluator/V1-EXTRACTION.md`: 동일 canonical 의무와 A 자유 본문/B 추가 T1 구조; 원규약 절 대응·생략 명시.
- `followup/REQUEST.md`, `evaluator/allowlists.json`, `manifest.json`: 후속 비노출 packet, 선언적 파일 범위, 사전 입력/검사 해시. 보안 집행이나 미래 참가자 산출물 해시가 아니다.
- `evaluator/examples.py#initial,#followup`, `evaluator/hidden_checks.py#cases,#check`, `evaluator/test_preparation.py#PreparationTests`: trusted reference·잘못된 mutation·독립 기대값을 비교하는 오프라인 검증. 참가자 코드를 host에서 안전 실행하는 sandbox가 아니다.
- `.lazy-harness/evidence/v2-recording-method-preparation-01.md`: 준비 검증·Git 보존·잔여 blocker의 단일 evidence capsule. 기존 host graph/index/이전 실험을 갱신·이주하지 않는다.

## Discovery capture

| Layer | 판단 | 범위 |
|---|---|---|
| DDD | none | 새 제품 도메인 규칙 없음 |
| SDD | prepared fixture | 공통 API/seed와 조건별 기록 지시·인계 범위 파일 준비; 제품 contract 승격 아님 |
| BDD | proposed execution | 최초 작업→fresh 인계 흐름은 문서화했으나 실제 참가자 실행 없음 |
| TDD | prepared offline | 독립 hidden 기대값·reference/negative mutation 판별 검사; 실제 결과는 evidence 참조 |
| ADR | none | 제품 구조나 저장 기술 채택 없음 |
| SSOT | none | 실제 환경/모델 프로필/운영 정책 변경 없음 |
| Planning | updated | 선택된 연구 방향의 첫 구체 설계 및 미해결 질문 보존 |

Rule placement: 이 연구 설계가 primary다. 기존 정책은 비교 근거로 읽었으며 수정/복제하여 전역 운영 규칙으로 승격하지 않는다.

## Preparation 01 — 현재 상태와 실행 전 잔여 gate

- Status: offline-prepared / execution-blocked; 독립 준비 검수 대기. 사용자 ‘준비 진행’ 범위만 수행하며 네 참가자 세션·유료 실험 호출은 0이다.
- 구체 범위: Python stdlib `resolve_retries(file_config, env)`의 env 존재 > file 존재 > 기본 3, bool/int-subclass 제외 정확한 int 0..9, ASCII 한 자리 env, 선택 invalid의 ValueError/no fallback, 무시한 하위값 미검증, 입력 불변. 공개 테스트는 예시이며 seed는 의도적으로 미구현이다. 별도 후속 packet은 선택적 `override=None`/키 누락을 기존 동작으로 두고 같은 file 규칙의 최우선 값과 old-call 호환성을 준비했다. 명시적 None 처리와 mapping-container 비검증은 준비 구체화이며 실행 전 packet 검수 대상이지 새 host 제품 규칙이 아니다.
- A는 canonical primary 우선 갱신·확인/candidate 구분·옛 지침 대체 이유·digest/map/필요 graph·독립 layer 승격·compact 계획/위험·실제 evidence를 유지한다. A의 좋은 태스크 표를 금지하지 않는다. B는 같은 의무 위에 구현 전/승인된 계획 변경/종료 때 같은 T1의 목적→완료조건→계획/상태→이유→결과 연결만 추가한다. 추출표는 `evaluator/V1-EXTRACTION.md`; 설치 V1 전체 비교가 아니다.
- 검증 기준: 동일 초기 5개 공통 파일 + 각 조건 지시 1개, 초기에서 evaluator/후속 정보 제외, 정확한 SHA256, 올바른 두 단계가 통과하고 `or`·bool·invalid fallback 등 잘못된 11 mutation이 판별되어야 한다. 실제 한 번의 focused 결과와 상세 Git before/after는 단일 evidence capsule에 보존한다. 코드 실패 이력을 버리거나 참가자 기록을 연구자가 보충하지 않는다.
- read-only 근거: `.lazy-harness/spec/platform/runtime-and-shared-state.md` Contract는 durable record 공유를 의도한다. `packages/lazy-harness-pi/README.md` What it wires/Trust boundary는 read-debt와 extension 권한이지 평가자 파일 접근 차단이 아니다. 기존 `experiments/v2-reading-comparison/prepare.mjs#preflight,#prepare`, `protocol.mjs#inspectRuntime,#remaining`는 attestation/cwd/사후 trace/시간 계산이지 hard dollar/output 보장이 아니다. pi/omp/bwrap/docker binary 발견만으로 usable/configured 격리를 주장하지 않는다.
- 실행 blocker: host/상대 조건/evaluator/history 실제 접근 불가 증명 없음; 누적 달러/출력/tool/time hard cap 및 취소 보장 없음; 실제 모델·가격·usage 확정 없음; 유료 예산/네 세션 실행 승인 없음; 독립 준비 검수 미완료. US$20·출력12000·tools40·10분은 검토 제안 그대로이며 승인/입증된 cap이 아니다. 새 도구·runtime wrapper·보안 장치·설치·환경 변경으로 보충하지 않았다.
- 실제 focused 결과: `python3 -B experiments/v2-recording-method-pilot-01/evaluator/test_preparation.py` 1회, 7 tests / 0.060s / pass. Reference 초기 71·후속 318 cases 모두 통과, 잘못된 11 mutation은 모두 거절, seed 미구현은 통과로 오인하지 않았다. 두 reference 각각 공개 4 tests도 통과했다. 이는 준비 oracle 판별 증거이며 참가자/학습 결과가 아니다.
- Validation ownership: 최종 lazy check/standard는 parent 담당. 기존 dirty tree와 HEAD/index 보존; commit/push/upload/delete 없음. 도구 provider가 write마다 자동 diagnostics를 출력했고 manifest 동결 전에 `common/__pycache__/` bytecode 2개가 생긴 것을 관찰했다(생성 주체 미확정, writer는 pytest를 실행하지 않음). 삭제하지 않고 evaluator-only 해시 목록에 보존했으며 participant allowlist에는 포함하지 않았다.

### Regression code — same-record 4-layer assessment

| Layer | 판단 | 근거/소유권 |
| --- | --- | --- |
| SDD | bounded fixture delta only | 새 exercise API와 primary seed는 실험 common/ 안에 존재한다. host API/runtime contract에는 no independent delta; 이 Planning이 준비 소유권을 보존한다. |
| BDD | no independent product delta | 최초/후속 흐름은 평가 protocol 제안이며 실제 사용자 UI/제품 행동이나 참가자 세션을 변경하지 않았다. |
| SSOT | no independent host delta | manifest/allowlist는 평가자 payload metadata이지 enforcement/config 정책이 아니다. 기존 env/config/registry/auth는 변경하지 않았다. |
| DDD | no independent delta | retries는 합성 과제 명칭/값 규칙이며 제품 도메인 용어·entity·비즈니스 규칙으로 승격하지 않았다. |

Discovery capture: 새로운 준비 artifact와 미해결 실행 blocker만 이 기존 primary에 누적했다. 기존 migration 알림(record-lint 2건, graph legacy 37행)은 이번 범위 밖이며 재검증/자동 이주하지 않았다; 별도 승인 시 guided migration 재개 제안을 유지한다.

## Preparation revision 2 — bounded P1/P2 correction

- User approval: workflow `2dadcce6-f0cd-4cce-a7ec-8ba83d711f8f` failed before launching children; user approved same-protocol retry for ONLY public output/handoff disclosure (P1) and general-Mapping exact-type/input-preservation checks (P2) from [preparation-review-01](../evidence/v2-recording-method-preparation-review-01.md). This is preparation approval, not participant execution/spend approval. Existing failure receipt/dirty state were not overwritten.
- P1: `common/COMMON-PROCEDURE.md` now enumerates precisely the unchanged `participantWritable` / `followupFromFrozenOwnOutput` names and shallow patterns from `evaluator/allowlists.json`. The same common export reaches both conditions/stages; instructions remain read-only, rejected output categories are disclosed, no evaluator/hidden/future/other-condition material is added. Permissions and exercise requirements are unchanged.
- P2 Implementation map: `evaluator/hidden_checks.py#snapshot` traverses general Mapping structurally; `#check` supplies fresh UserDict/MappingProxyType rows to the same exact-int and before/after assertions as ordinary rows. `evaluator/examples.py#wrong_userdict_false,#wrong_userdict_mutates,#wrong_mapping_float_override` add three wrong specimens. `evaluator/test_preparation.py#PreparationTests.test_general_mapping_exact_type_and_preservation` checks labelled rejection and independent mutations of each mutable argument; existing parity/freeze tests now protect exact public disclosure and original-manifest provenance. COP-01/02/05: single local assertion path, no architecture/untouched-source refactor needed.
- Re-freeze: pilot `manifest.json` version 2 links the exact preserved version-1 manifest (SHA256 `ca4cdd251575a928dd4d335008028692b32130697fa16350d6c58d92d29177fb`), review and revision log. Original 7-pass/11-mutant log remains unchanged. New [offline revision log](../evidence/v2-recording-method-preparation-fix-01-offline-validation.log): one trusted offline run, 8 tests / 0.068s / PASS; references initial 71 and followup 320 calls, 14 named wrong specimens rejected, public 4 tests pass for both references. Followup count now counts the two general-mapping override calls previously bundled under container counts; it is not a new API requirement. Finite probes do not prove all Mapping behavior and cannot detect transient mutation reverted before return. No participant/model experiment ran.
- Preservation incident: pre-edit [baseline inventory](../evidence/v2-recording-method-preparation-fix-01-baseline/inventory.json) captured 23 files with original path/bytes/hash plus dirty Git. Post-run audit found only two copied bytecode snapshots changed; all 21 text/log/manifest/review baseline copies remain exact and both live original bytecodes still match initial inventory. Tool-provider diagnostics were observed, but attribution is unconfirmed. The focused test passed; the enclosing command failed on the subsequent snapshot integrity assertion. Nothing was silently repaired or deleted.
- Recovery approval: after read-only investigation the user selected `사본 추가 후 재검수 (Recommended)`, relayed by supervisor. Two new `.bin` recovery copies were added only after immediate original hash verification and re-read size/SHA256 checks. Changed snapshots, original inventory, manifest, log and [incident](../evidence/v2-recording-method-preparation-fix-01-snapshot-incident.json) are retained. [Append-only recovery manifest](../evidence/v2-recording-method-preparation-fix-01-recovery/manifest.json) links original→inventory→changed snapshot→recovery; reviewer MUST read incident and recovery manifest. No code/test rerun followed this approval; only copy integrity was checked.
- Current status: revised offline-prepared / fresh independent review pending / execution-blocked. Isolation, hard cumulative budget/cancellation, model/accounting and paid-session approval blockers remain unchanged; US$20 / 12000 output / 40 tools / 10 minutes are proposals only. No runtime/security wrapper, installs, auth/env changes, sync/commit/push/upload/delete or migration. Full regression and parent check/standard were not run. Detailed findings/Git/artifacts: [fix evidence](../evidence/v2-recording-method-preparation-fix-01.md).

### Revision 2 regression — same-record layer assessment

| Layer | Assessment | Ownership / reason |
| --- | --- | --- |
| SDD | bounded fixture clarification only | Public procedure discloses existing paths; oracle enforces existing exact-int/input-preservation contract. No independent host API delta. |
| BDD | no independent product delta | Same two-condition handoff flow; neither participant sessions nor product UI changed. |
| SSOT | no independent host delta | Revised manifest is evaluator metadata/provenance, not permissions expansion, environment/config or access-control implementation. |
| DDD | no independent delta | Synthetic retries rules unchanged; no host domain/entity change. |

Discovery capture / Rule placement: this existing primary owns the approved correction and preservation/recovery facts; detailed evidence remains linked, not duplicated into new canonical layers or graph migration. Existing migration notice (record-lint 2 / legacy graph 37) remains out of scope and unmodified; guided migration may resume only as a separately approved task.

## Isolated execution connection 01 — partial / execution still blocked

- User-approved scope: experiment-local integration and no-cost verification only. Supervisor explicitly confirmed a local SDK factory with synthetic provider is within that scope, not a change to current writer/reviewer subagent transport or approval to run future participants through a different protocol. No model endpoint, paid probe, runtime/global config patch, installation, fallback agent CLI, sync/deploy/commit/push/upload/delete was performed by this writer.
- Implementation map: `experiments/v2-isolated-execution-01/isolation.mjs#verifyPilot,#initial,#Workspace.request,#Workspace.freeze,#followup,#grade,#captured` connects the unchanged accepted v2 declarations to curated files, all-tool namespace execution, exact same-condition handoff and separate RO grading. `tools.py.txt#safe,#main` performs read/write/edit/list/Python only inside bwrap. `no-cost-sdk.mjs#createNoCostSession` connects actual installed Pi SDK custom tools with explicit allowlist, no ambient built-ins/extensions/resources/history and in-memory configuration; only provider/auth response behavior is simulated. `sdk-probe.mjs` and `verify.mjs` protect native dispatch/context and OS boundaries. `grade.py.txt` uses unchanged trusted pilot checks inside a separate network-disabled namespace; its output remains advisory against hostile interpreter manipulation.
- Evidence: [implementation report](../evidence/v2-isolated-execution-implementation-01.md), `experiments/v2-isolated-execution-01/README.md`, `artifacts/run-pXpEwN/summary.json`, `artifacts/post-return-audit.json` (artifact paths relative to the new experiment). One focused batch: 13 checks passed / 4.611s; four synthetic SDK rows each produced 9 real dispatched tool results and 10 native contexts, with zero observed ambient discovery attempts. This is neither four participant calls nor actual provider payload/price evidence. Existing pilot/evidence 161 files remained exact after the tool returned.
- **Post-return integrity incident:** after the green process exit, the tool provider explicitly reported `pi-lens applied autofix` on nine synthetic Markdown evidence files, including both A/B frozen originals. Safe lstat/open/fstat audit confirmed frozen `evidence/validation.md` changed from 21 to 22 bytes in each condition (two mismatches among 14 frozen files). Original freeze receipts, changed snapshots, raw `.bin` logs and appended current-byte `.bin` copies are retained; no repair or rerun. Supervisor approved only read-only audit plus append-only reporting. Green in-process checks do not establish post-tool retention integrity.
- **Special-file warning:** `artifacts/run-pXpEwN/fifo/test_fifo.py` is a retained FIFO and `artifacts/run-pXpEwN/symlink/test_link.py` a retained symlink. Stat-only; never blindly read, follow, import, format or execute artifact Python in a host interpreter. Parent check/standard must wait if their special-file/untrusted-artifact behavior is not known safe. Provider Python diagnostic messages were observed; code execution by those diagnostics is an unresolved risk, not a proven fact from the messages alone.
- Remaining blockers: ambient diagnostic writer/host postprocessing exclusion; hostile-code grading can monkeypatch/forge same-interpreter oracle output despite immutable files; no in-flight dollar/output-token cap, complete resource exhaustion/remote cancellation guarantee, effective paid model/pricing, approved participant protocol or spend authority. Local 64 KiB capture/3s timeout and observed detached-child cleanup are no-cost safety controls only. US$20/output12000/tools40/10min remain proposals, not adopted caps. No claim of complete native-runtime process isolation or pi-subagents integration.

### Connection 01 — same-record 4-layer assessment

| Layer | Assessment | Ownership / reason |
| --- | --- | --- |
| SDD | bounded experiment component delta | Project-local packet/tool/SDK/grading connection only, with explicit partial guarantees; accepted exercise API and global runtime contract unchanged. This Planning owns scope and blockers. |
| BDD | no independent product delta | No participant/user UI flow executed; deterministic SDK rows test mechanics only. Future execution-protocol selection still needs user approval. |
| SSOT | no independent host delta | Frozen declarations read unchanged; no global settings, policy registry, auth, environment ownership or runtime installation changed. Local safety numbers are not research budget adoption. |
| DDD | no independent delta | No synthetic retries rule or product entity changed. |

Discovery capture / Rule placement: confirmed local-SDK approval boundary, tested mechanics and post-return diagnostic mutation are captured once in this primary with one detailed evidence capsule. No new global policy or graph migration. Record-lint 2 / legacy graph 37 migration remains pending; guided migration can resume only under separate user approval.

## Condition-preservation transfer 27 — test-only findings capsule

User-confirmed scope retained strict schema enforcement and permitted exactly two sequential Recorder→Digester cases over two different already exposed frozen rules. The new sibling `experiments/v2-agentic-wiki-fragment-01/tr-record-digest-condition-preservation-27/` preserves sibling26 bytes and reuses its reinforced common guidance verbatim. CASE-1 uses frozen Chat memo maintenance rule `D04-F037-A02` plus an AUTHORED compatible experiment-only audit-correlation addition. CASE-2 uses frozen recurrence deletion rule `D05-F006-A04` plus an AUTHORED conflicting observation without amendment authority. Sibling26 CASE-3 ambiguity remains held and unresolved.

Actual guarded Luna-medium calls were sequential Recorder→Digester for each case only: receipts 1718–1721, all settled, SDK-reported added cost USD 0.0070914; ledger moved spent 32.29080731→32.29789871, held 2.04543422 unchanged, unknown holds 1/895/989 unchanged. Four strict required `submit_stage_result` tool outputs passed transport/schema validation; Reader/Work/grader/retry/repair/fallback calls were zero. This is not semantic acceptance. Preliminary worker review finds CASE-2's record and source-assisted proposal appear to preserve all recurrence branches and authority limits; CASE-1 preserves the core memo/Chat exception but may omit the source Planning row's explicit pending validation/contamination-audit/commit/push/merge/production-dispatch list in both standalone `record_text` and candidate. Parent direct semantic review remains required. No canonical/product apply, production workflow, human apply approval, DB, SDK/global config, install, migration, commit, or product code execution occurred.

Evidence: `actual-run-01/{summary.json,evidence-capsule.json,report-ko.html,link-check.json}`, exact per-case input/request/raw/actual/normalization/render/comparison files, and source-linked freezes. The Korean HTML is a preliminary worker report, human-first in source→synthetic fact/observation→actual record→actual proposal→preserved/lost order.

| TDD completeness layer | Assessment |
| --- | --- |
| DDD | no independent delta — synthetic experiment facts do not change product vocabulary or rules |
| SDD | no independent delta — strict tool transport is experiment-local reuse; no product/component API changed |
| BDD | no independent delta — no real user/product/apply/rollback workflow executed |
| TDD | test-only evidence added — 7 focused offline checks plus four bounded participant calls; not full-flow or general-stability proof |
| SSOT | no independent delta — ledger evidence retained; no config/schema ownership or canonical product fact changed |
| ADR | no independent delta — no architecture/trade-off adoption |
| Planning | updated here once with bounded findings and Parent-review requirement |

Known host migration debt remains out of scope and unmodified: record-lint issues 15 and legacy graph rows 37; guided migration can resume only with separate approval.

## Status/modality preservation 28 — power-loss recovery capsule

After the PC power loss, native workflow `83f3b60a-f032-42c1-aa6b-7d2b83a70270` was reported `runnotfound`; this was a same-role recovery audit, not a native resume. The original `actual-run-01` partial files were not overwritten. A 0700 recovery sibling preserves byte copies and SHA-256 for all 26 pre-recovery artifacts, the current shared-ledger readback, process/Git audit, direct semantic review, link check, and Korean HTML at `experiments/v2-agentic-wiki-fragment-01/tr-record-digest-status-modality-preservation-28/actual-run-01/recovery-20260922-power-loss-01/`.

The four-call allowance was already exhausted by request IDs 1722–1725. Requests 1722–1724 are settled and have durable outputs: CASE-1 Recorder and Digester preserve the historical pending validation/contamination-audit/commit/push/merge/production-dispatch list as history rather than current authorization, keep obligation/permission/prohibition distinct, and make audit-identifier inclusion mandatory rather than optional; CASE-2 Recorder preserves normalization, permission, the three-part `this_only` conjunction, deduplicated exception update, alternative soft delete, observation-only authority, and unknown cause/reproducibility. Request 1725 (CASE-2 Digester) remains `dispatched`, reserved at USD 0.16945639, with no durable response, usage, settlement, or provider wall time. Therefore recovery stopped with zero new model calls: no replay, synthetic settlement, alternate route, retry, or inferred success. CASE-2 Digester and overall semantic result remain unresolved.

Ledger readback is spent USD 32.30457371, held USD 2.21489061, latest 1725; the three settled study28 calls add USD 0.006675 and request 1725 accounts for the new hold. Historical unknown-held IDs 1/895/989 remain. Original provider receipt UTC times are preserved, but cross-reboot monotonic duration is not computed; UTC elapsed wall includes PC downtime and is not model latency. The original preflight captured the guarded Luna-medium route but not its SDK package version, so version change across the outage is unknown and was not silently reinterpreted. Original summary/report absence remains absence, not an inferred completed run. Held ambiguous CASE-3 stays held; no canonical/product/workflow/DB/settings/install/download/commit/migration action occurred.

Layer completeness: Planning updated with this recovery fact; TDD evidence is the experiment-local recovery capsule; DDD/SDD/BDD/SSOT/ADR have no independent delta. Known record-lint issues 15 and legacy graph rows 37 remain unmodified and need separate guided-migration approval.

## Fresh related counterexample 29 — test-only capsule

The approved fresh trial created `experiments/v2-agentic-wiki-fragment-01/tr-record-digest-fresh-counterexample-29/` without changing sibling28. It used the same frozen recurrence source but a genuinely new AUTHORED hypothetical conflict: `deleteScope="series"` (outside the `this_only` conjunction) nevertheless updated one occurrence exception and left the series active. Cause and reproducibility remain unknown; this is not an actual product observation and grants no amendment, apply, recovery, or workflow authority. Frozen private expectations preceded dispatch and were not sent; sibling28 generic status/modality guidance was byte-equal at the string level. Zero-call readiness confirmed `@earendil-works/pi-coding-agent` 0.87.0 and the guarded Luna-medium Codex Responses ChatGPT backend route with SSE, manual redirect denial, and maxRetries 0.

Exactly two sequential actual-upstream calls ran, Recorder then Digester, with strict required `submit_stage_result`: settled receipts 1726/1727, provider-reported added USD 0.003413, no Reader/Work/grader/retry/repair/fallback calls. Ledger moved spent 32.30457371→32.30798671, held remained 2.21489061 within floating serialization, and latest became 1727. Protected rows 1/895/989 and unresolved dispatched request 1725 remained value-identical; sibling28's 126 regular files remained byte-identical. Request 1725 was not retried, settled, released, or retroactively completed. Trial29 proves only that the last-stage chain returned for this related case, not that trial28 recovered or succeeded.

Worker-only direct review (Parent final grade pending) finds the standalone Recorder preserves ID normalization, virtual occurrence/date extraction, the creator-or-permission condition, all three conjoined `this_only` conditions, deduplicated exception update, otherwise series soft delete, observation-only authority, and unknown cause/reproducibility. The source-assisted Digester received the actual Recorder plus exact source, retained the source's normative force against the conflicting observation, and returned `needs_review` with no candidate. Evidence, raw schema appendix, exact requests/responses, cost/time ledger, semantic comparison, link check, and Korean HTML are under `actual-run-01/`.

Layer completeness: Planning is the one primary compact capsule and experiment-local TDD evidence was added. DDD/SDD/BDD/SSOT/ADR have no independent delta because no product vocabulary, API, visible workflow, canonical ownership/configuration, or architecture decision changed. No policy apply, DB/product execution, workflow action, install/download/settings change, commit, or migration occurred. Known record-lint issues 15 and legacy graph rows 37 remain unmodified and require separate guided-migration approval.

## Frozen-guidance mixed suite 30 — test-only capsule

The approved non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-record-digest-frozen-mixed-suite-30/` froze four newly authored synthetic cases before dispatch: compatible mandatory addition, authority-free conflicting observation, explicit experiment-copy-only clause-4 replacement, and no-change control. CASE-A through CASE-D used the same nonrevealing task and two raw frozen rules (`D04-F037-A02`, `D05-F006-A04`) from the already exposed nine-document corpus. The exact generic guidance was byte-equal at the string level to sibling29 (`ae2b0aeca76664ed8011402634b078644c1fbc088247868dd68e1d16887291bf`); sibling29 tool/wire/stage payload schemas were reused, and private keep/change/drop clause matrices with reasons were frozen and not sent. This remains a content test rather than independent holdout, read→code→test flow, operational workflow, product decision, or canonical apply.

Zero-call readiness confirmed `@earendil-works/pi-coding-agent` 0.87.0 and the guarded Luna-medium `openai-codex-responses` ChatGPT backend SSE route, manual redirect denial, maxRetries 0, private mode-0700 owned runtime, and unchanged ledger. Eight sequential Recorder→Digester calls settled as receipts 1728–1735 with no retry, repair, fallback, Reader, Work, grader, or extra call. Provider-reported added cost was USD 0.0173382; ledger spent moved 32.30798671→32.32532491, held stayed 2.21489061, latest became 1735, and protected rows 1/895/989/1725 remained byte-value identical. Sibling28 (126 files) and sibling29 (49 files) remained byte-identical. Provider wall sum was 230136.257862ms, first-call-to-last-response wall 230314.275076ms, and preparation-to-report end 241929.177031ms. Empty stderr and lifecycle `calls=8`, `socketAfterClose=false` show the sequential batch completed rather than hitting a single-call 240-second broker timeout.

Worker-provisional direct review, with Parent final review still pending: CASE-A Recorder and Digester preserve D04 conditions, ownership/prohibitions, historical pending items, and mandatory-not-optional response classification; its supplement candidate fully restates the source, so append rendering has a duplication concern without semantic loss. CASE-B preserves all D05 branches and keeps the authority-free conflict unresolved. CASE-C changes only clause 4 in the experiment-copy proposal and preserves clauses 1–3 plus real-product non-authority. CASE-D Recorder preserves no-change semantics and invents no completion; its settled Digester raw output returned `retain` with a non-null candidate, so the frozen validator rejected it with `CANDIDATE_MUST_BE_NULL`. No repair or semantic credit was granted. Thus call completion is 8/8 settled, strict output acceptance is 7/8, and semantic findings remain separate from both.

Evidence entrypoints are `actual-run-01/{artifact-index.json,matrices.json,summary.json,evidence-capsule.json,request-integrity.json,report-ko.html,link-check.json}` plus per-case input/private freezes, exact requests, raw transports, accepted actual outputs, rejected CASE-D failure/raw output, render files, and clause comparisons. Actual outputs were not edited; rendering was not applied to any canonical record or product.

| TDD completeness layer | Assessment |
| --- | --- |
| DDD | no independent delta — all events and authorities are explicitly synthetic experiment inputs |
| SDD | no independent delta — frozen strict tool/schema transport was reused without product/component API change |
| BDD | no independent delta — no real user, approval/apply/rollback, or product workflow executed |
| TDD | test-only evidence added — nine focused contract tests, eight bounded settled participant calls, and separate acceptance/semantic/completion matrices; not whole-flow or broad reliability proof |
| SSOT | no independent delta — ledger and old request 1725 were preserved; no ownership/configuration or canonical product fact changed |
| ADR | no independent delta — no architecture or operational workflow decision adopted |
| Planning | updated here once with the frozen design, exact bounded result, failures, limits, and Parent-review requirement |

Known host migration debt remains unmodified and outside this trial: record-lint issues 15 and legacy graph rows 37. Guided migration requires separate approval.

## Public-contract alignment 31 — offline serializer stop capsule

Parent30's correction is governing for this follow-up: CASE-D's original `retain` plus non-null candidate satisfied the disclosed trial30 JSON Schema and failed only the host-only cross-field check. The old rejection and all raw outputs remain immutable and are not retroactively counted as success. The prior 7/8 figure is host acceptance, not public-schema compliance or semantic accuracy.

The new non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-public-contract-alignment-31/` tested a single candidate JSON Schema whose four mutually exclusive Digester payload branches encode `retain|needs_review → null` and `supplement|replacement → non-empty string`; the same generic schema evaluator supplies candidate host validity, with no duplicated hidden operation/candidate check. Twenty-four offline combinations cover all four operations against null, non-empty string, empty string, missing candidate, wrong type, and an extra property. Posthoc replay of all eight unmodified trial30 raw transports shows only CASE-D Digester differs: old public schema accepts, old host rejects, and the candidate schema rejects; the other seven retain their expected acceptance. Raw-file hashes and ledger bytes are unchanged.

The installed `@earendil-works/pi-coding-agent` 0.87.0 strict serializer recursively rejects this necessary structured union before network access: `object and array unions are unsupported`. Its source also rejects `oneOf`, `if/then/else`, and structured `anyOf` branches. Because changing to a scalar re-encoding, weakening the host checker, adding text-only guidance, changing the SDK, or gambling on provider behavior was outside approval, the controller stopped offline. No provider call, retry, fallback, Recorder, Digester, grader, canonical apply, SDK/global change, or added provider cost occurred; the planned CASE-D and CASE-C calls were not run. The schema remains explicitly `blocked-not-emitted`, and no backend `minLength` enforcement is claimed.

Implementation map: `contract-candidate.json` is the single blocked contract candidate; `offline_audit.py` builds exhaustive/replay evidence and invokes the installed no-network serializer; `test_contract_feasibility.py` protects the 24-row relation, exact four examples, immutable eight-raw replay, and serializer stop; `report-ko.html` explains the correction and boundary in Korean; `offline-evidence/{summary.json,serializer-probe.json,old30-three-column-replay.json,old30-raw-files-hash-proof.json,ledger-readiness.json}` preserves exact evidence.

| TDD completeness layer | Assessment |
| --- | --- |
| DDD | no independent delta — operations retain their established experiment-local meaning |
| SDD | no emitted contract delta — the aligned schema candidate is blocked before transport |
| BDD | no independent delta — no paid or product workflow ran |
| TDD | offline evidence added — 24 combinations, four exact examples, eight immutable raw replays, and installed serializer rejection |
| SSOT | no independent delta — ledger/config ownership unchanged; candidate is not canonical or emitted |
| ADR | no independent delta — no SDK, provider, or architecture alternative was adopted |
| Planning | updated here once with Parent30 correction, implementation map, exact stop, and remaining blocker |

Known host migration debt remains outside this work: record-lint issues 15 and legacy graph rows 37 are unchanged and still require separately approved guided migration.

## Supported flat strict result tools 32 — bounded actual-run capsule

Parent30 correction and the user's explicit supported-SDK re-encoding approval govern this sibling. `experiments/v2-agentic-wiki-fragment-01/tr-supported-flat-tools-suite-32/` keeps suite30 and suite31 bytes immutable and uses four flat Digester result tools: `retain_result` and `needs_review_result` omit `proposed_candidate`; `supplement_result` and `replacement_result` require a string candidate. Tool name is the disposition, exact cardinality is one, the tools are inert result channels, and host-owned approval/apply metadata remains outside model fields. The adapter retains the raw tool response separately, deterministically derives disposition from the selected name, derives candidate null only when the selected declared schema omits it, and explicitly does not call that model-content repair. Recorder remains a single flat strict result tool. Suite30 source-semantic guidance is byte-identical; only mechanical protocol text changed.

No-network use of installed `@earendil-works/pi-coding-agent` 0.87.0 serialized all five flat strict tools together and independently preserved each strict object schema, enum, const, required list, `additionalProperties:false`, and `minLength`. The public local validator still independently enforces non-empty strings; this evidence does not assert a broad backend constraint guarantee. Focused tests cover every branch plus missing fields, wrong types, extras, host-forged fields, mismatched names, empty strings, and zero/two-call cardinality. The renderer now treats a candidate as a full standalone reconciled state: supplement/replacement display original and candidate separately without concatenation; retain shows the original; needs-review shows original plus concerns and invents no patch.

The same four authored, already-exposed suite30 cases ran sequential Recorder→Digester on the same guarded Luna-medium Codex Responses ChatGPT route, SSE, manual redirect denial, and maxRetries 0. Eight calls (1736–1743) settled with no retry, repair, fallback, Reader, Work, grader, or extra calls. Provider-reported added cost was USD 0.0176038; ledger spent moved 32.32532491→32.34292871, held remained 2.21489061, latest became 1743, and protected rows 1/895/989/1725/1735 remained value-identical. Provider wall sum was 199542.842722ms, first-call-to-last-response wall was 199768.610685ms, and worker preparation-to-report-end was 211116.270528ms. CASE-A selected supplement, CASE-B needs-review, CASE-C replacement, and CASE-D retain; all eight outputs passed public schema and host validation. Direct post-run worker review found all eight semantically supported against the frozen clause boundaries, including mandatory-not-optional classification, the exact recurrence conjunction and alternative, experiment-copy-only clause-4 replacement, and no-change preservation. This is an authored exposed-case test with a new protocol confound, not independent holdout or model-improvement evidence. The old30 posthoc mapping remains compatibility-only and does not retroactively turn its rejected CASE-D into success.

Evidence entrypoints: `actual-run-01/{summary.json,report-ko.html,direct-semantic-review.json,link-check.json,immutability-after.json}`, the exact SDK serialization and structural matrix under `offline-evidence/`, and each case's frozen input, request, raw tool response, deterministic adapter output, derived actual result, and render. No product/DB/operational workflow, canonical apply, SDK/global modification, install/download, commit, migration, or approval workflow occurred.

| TDD completeness layer | Assessment |
| --- | --- |
| DDD | no independent delta — cases remain synthetic and do not change product vocabulary or rules |
| SDD | no product/component API delta — the strict result contract is experiment-local |
| BDD | no real user/apply/approval workflow; render-only experiment display changed locally |
| TDD | experiment-local contract and renderer tests plus eight bounded actual calls |
| SSOT | no ownership/configuration delta; ledger and protected rows are evidence only |
| ADR | no architecture adoption or SDK/provider/global change |
| Planning | this single capsule records the approved design, actual result, limits, and evidence |

Known host migration debt remains outside this work and unchanged: record-lint issues 15 and legacy graph rows 37. Guided migration still requires separate approval.

## Target-fixed Digester correction 41 — two-attempt bounded result capsule

User-confirmed continuation addressed trial40's specific target/action ambiguity without rerunning its code or tests. The new non-overwriting sibling `experiments/v2-agentic-wiki-fragment-01/tr-target-digest-41/` fixed one target before dispatch: the exact 39 Recorder `payload.record_text`, artifact path plus SHA-256 `a7dabe47d78ed9b05a8c282a206fd36343e2ae3d3f4eed8f2dffecb38cc61530`. D05-F006-A04 remained a source reference, not a target. Direct evidence was the actual trial40 old-five pass, expanded-before failure, expanded-after ten-pass, exact diff, and public fixture API; authority was the user's correction of the experimental claim only, never a product-policy amendment. Unlike trial40, no Recorder output mediated Digester input.

Four flat strict tools gave literal operations. `retain` meant exact target text unchanged and serialized `changed_assertions.maxItems=0`; `supplement` and `replacement` required a complete standalone `candidate_text`; `needs_review` had no candidate or materialized state. Every Digester and Answer tool required constant `case_id` and `target_id`, rejected extra properties, and was sent with `tool_choice=required`. Offline serializer evidence preserved all five strict schemas. The deterministic selector separately proved retain→literal old text and replacement→literal model candidate, with no hidden repaired state. Answer saw only the selected materialized state and the same three neutral questions.

Attempt1 receipts 1793/1794 selected replacement, but the record-only Answer incorrectly said the three-condition conjunction was missing from the 39 candidate, conflating the original pre-39 baseline with trial40 expanded-before. This precise ambiguity was published in attempt2's freeze before dispatch; target, source, evidence, questions, operation meanings, and success criteria did not change. Attempt2 receipts 1795/1796 again selected replacement. Direct worker review found the standalone candidate internally inconsistent: it still called the old append-if-absent implementation the current changed fixture, then later described trial40 expanded-after as whole-list stable deduplication. Its Answer Q1 again mixed the original missing-conjunction history into the current 39-candidate duplicate correction. Therefore both attempts are structurally valid observations but the requested end-to-end semantic correction is **not successful**; raw outputs were not edited and no third attempt ran. Parent final manual review remains required.

Across both attempts, four calls settled with provider-reported USD 0.0083156 and provider wall 148029.77622ms; first preparation start to final report was 280602.208ms. Ledger moved spent 32.397905109999925→32.40622070999993, held remained 2.2253968900000007, latest 1792→1796, and unknown held IDs 1/895/989/1778 remained. Trial40's 95 regular files and protected ledger rows 1/895/989/1725/1778 were unchanged. Invoice and orchestration costs remain unknown. No Work/Recorder/grader/product/DB/operational workflow, canonical apply, install/download, SDK/global change, commit, push, or migration occurred.

Evidence entrypoints: `report-ko.html`, `study-summary.json`, `manual-review.json`, and each attempt's `design-freeze.json`, exact Digester/Answer requests and raw transports, `selected-state.json`, strict schema/wire proof, selector proof, guarded preflight, summary, HTML, artifact index, and link check. The report presents the required human sequence: old false record → correction evidence → Digester's actual choice and literal selected state → Answer reading only that state.

| Completeness layer | Assessment |
| --- | --- |
| DDD | no independent delta — product vocabulary and rule meaning unchanged |
| SDD | no product/component API delta — strict flat tools and selector are experiment-local |
| BDD | no product workflow/apply delta — only a bounded model observation ran |
| TDD | experiment-local offline schema/selector proofs and retained trial40 receipts; trial40 tests were not rerun |
| SSOT | no ownership/config delta — ledger and immutable artifact identities are evidence only |
| ADR | no architecture adoption — reused the guarded broker and supported SDK transport |
| Planning | updated here once with current approval, trial40 failure reason, both trial41 attempts, costs, limits, and final semantic failure |

Known host migration debt remains unmodified and outside this trial: record-lint issues 15 and legacy graph rows 37. Guided migration requires separate user approval.
