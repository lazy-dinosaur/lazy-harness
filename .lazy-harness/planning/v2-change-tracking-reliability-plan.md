# 변경 추적 신뢰도 연구 — 실제 요청 목록 손실 사례

## Rule digest

- Status: advisory
- Layer: Planning
- Scope: host-project
- Applies when:
  - 비용보다 신뢰도를 우선하는 V2 변경 추적 연구의 기준과 실행 범위를 검토할 때
- Must:
  - 현재 요구, 현재 구현, 검증된 범위를 구별한다.
  - 원본/실패/기존 판정을 보존하고 후보를 승인된 구현으로 표시하지 않는다.
  - 실제 코드 변경·모델 시험 전에 사례와 사전 판정표를 검수하고 실행 범위를 확인한다.
- Aliases:
  - 변경 추적 신뢰도
  - 요청한 자료와 받은 자료

## 사용자 확인과 이번 범위

- 확정: 가격보다 신뢰도가 우선이며, 변경 추적부터 연구한다. 사용자가 연구 지속을 요청했다.
- 세션 시간 제한은 앞선 합성 입력의 소재였을 뿐, V2가 필요로 하는 제품 기능이 아니다. 다음 사례에 자동 승계하지 않는다.
- 현재 수행 범위: 실제 결함의 원문·코드 확인, 읽기 전용 재현, 정답/실패 기준안 작성과 독립 검토. 아래 사례 채택·수정·새 모델 시험의 세부 실행 승인은 아직 받지 않았다.
- **최신 실행 승인(user-confirmed):** 사용자가 옵션 ‘수정·검증·비교까지 (Recommended)’를 선택했다. `assessmentPackets`의 요청 목록 손실 최소 수정, 실제 사례 보호 검사와 원문/소화본3회 반복 비교를 승인했다. 위 ‘아직 승인 전’ 표시는 이 선택 이전의 역사다.
- 승인 원문 질문: ‘이 실제 오류의 수정까지 포함해서 변경 추적 연구를 진행할까?’ / 선택 설명: ‘요청 목록 손실을 최소 수정하고 실제 검사 증거로 소화본을 갱신한다. 원문 대조군과3회 반복 비교한다. 새 범용 실행기·프로필은 만들지 않는다.’
- 순서: 수정 전 자료·승인·기준 보존 → 최소 수정/보호 검사 → 독립 검수 → 격리된 시험 입력/조건 고정 및 확인 → 소화9단계·후속 판단18개 → 독립 의미 검수/보고. 새 범위·미확정 실행 장애는 정지하며, 이 범위 안의 정상 단계마다 같은 승인을 다시 요청하지 않는다.
- 추가 사용자 확인: ‘해결방법도 여러방면으로 찾아봐도 좋고’라고 연구 범위 확대를 허용했다. 현재 승인된 최소 수정·검증은 유지하고, 대안은 읽기 전용 문헌 조사/비교 후보로 수집한다. 새 대조 조건을 이미 승인된 시험에 몰래 추가하지 않는다.
- Discovery capture: Planning=updated(다방면 해결책 조사 허용); DDD/SDD/BDD/TDD 후보는 기존 분류 유지; ADR/SSOT=none. 이 추가 허용은 모델·저장소·프로필 변경이나 새 해결책의 채택이 아니다.

## 왜 이 사례인가 — 제안

앞선 연구에서 실제로 **자료3개를 요청했는데, 평가 자료에는 요청0개처럼 표시**됐다. 요청이 거절되어 받은 자료는0개였지만, ‘요청한 것’과 ‘받은 것’을 같은 것으로 취급한 결과다. 검수자가 그 표시를 믿고 요청 목록이 바뀌었다고 오판했고, 부모가 원본을 다시 확인해 바로잡았다.

이 결함은 단순 문자열 정돈이 아니라 연구 결과의 신뢰도에 영향을 준 실제 작업 후보다. 다만 이를 고치는 일과 하네스의 변경 추적 능력을 검증하는 일은 구별해야 한다.

## 확인한 현재 사실

- `assessmentPackets`는 requested_source_ids를 최초 요청에서 꺼내지 않고 `t.lookup.items`에서 만든다.
- 실제 S3B 첫 응답에는 정확한3개 source ID가 있었다. invalid_request 응답의 items는 빈 배열이었다.
- 읽기 전용 재현에서도 실제 요청3개 / 표시된 요청0개를 관찰했다. 원본 바이트 불변 확인. 소스 수정이나 새 보호 테스트 통과를 주장하지 않는다.
- 관찰 artifact: `.local/v2-reading-runtime-iInlC0/request-list-current-behavior.json`.
- 기존26개 검사 통과는 당시 검사 범위의 사실이다. 이 결함이 해결됐다는 증거가 아니다.

## 연구 질문

**새 개선 요구를 받은 뒤, 소화된 지식과 후속 작업자가 ‘요구는 생겼지만 구현은 아직 잘못돼 있다’를 유지할 수 있는가? 수정과 검증이 실제로 이뤄진 뒤에만 그 상태를 갱신하는가?**

가격은 기록하되 신뢰도 실패를 상쇄하는 점수로 쓰지 않는다.

## 사전 판정표 초안 — 아직 실행 전

| 시점 | 주어질 증거 | 구별해야 할 상태 | 금지할 단정 |
|---|---|---|---|
| T0 현재 결함 | 현재 코드·원래3개 요청·0개 표시 재현 | 요청과 반환 목록이 혼동되며 미수정 | 기존 검사 통과만으로 목록이 정확하다고 선언 |
| T1 개선 요구 승인 후 | 요청/반환을 구별하라는 새 요구, 코드 미변경 증거 | 새 요구는 유효하나 기존 구현과 보호 검사는 아직 미완료 | 요구 승인만으로 수정 완료·테스트 통과 선언 |
| T2 실제 수정·검증 후 | 승인 후 만들어질 실제 diff와 실행 결과 | 확인된 변경과 해당 검증 범위만 완료로 갱신; 과거 오류는 보존 | 실행 전 가짜 T2 증거 작성, 제한된 검사로 모든 경우 정확성 보장 |

T2는 미래 계획이며 아직 실제 사실이 아니다. 코드 변경 없이 첫 연구를 하려면 T0/T1만으로 제한하고 그 한계를 보고한다.

## 분리할 검사

1. **원문 기준 정답**: 사례별 요구/구현/검증/미확인/이유를 사람이 검수 가능한 표로 확정한다.
2. **소화 결과 검사**: 원문 사실을 누락·왜곡했는지, 과거 완료와 새 요구를 합쳐 버렸는지 확인한다.
3. **후속 판단 검사**: 새 세션이 필요한 다음 행동을 판단하고, 증거 없는 완료 선언을 피하는지 확인한다.
4. **오류 귀속**: 원문 부족 / 소화 오류 / 후속 판단 오류 / 전달·평가 도구 오류를 구별한다. JSON·인용 실패는 별도 기록하되 의미 신뢰도 점수와 하나로 뭉개지 않는다.

소화와 후속 판단은 서로 다른 세션으로 둬 부모의 정답표를 공유하지 않는다. 원문을 직접 읽는 대조 조건을 둘지는 독립 검토 후 범위를 확정한다. 한 번의 성공을 일반 신뢰도 증명으로 세지 않는다. 반복 수·순서·모델·출력 계약은 실행 전 고정한다.

## 아직 정해야 할 것

- T0/T1의 승인만 된 요구 추적부터 할지, 실제 수정 T2까지 포함할지.
- 소화 오류와 후속 추론 오류를 구분하기 위한 최소 대조 조건과 반복 수.
- ‘모름/추가 확인 필요’가 올바른 답인 경우와 불필요한 보류의 구분.
- 같은 사실의 다른 표현은 허용하되, 완료 상태·증거 범위의 왜곡은 허용하지 않는 의미 채점 기준.

이번에는 새 범용 runner나 엄격한 문자열 복사 기능부터 만들지 않는다. 기존 실행 경로를 재사용할 수 있는지 먼저 검토한다. 지원 불가/실행 장애는 보존하고 다른 모델/CLI로 몰래 전환하지 않는다.

## 독립 검토 결과와 권고 실행안 — 승인 대기

- 독립 read-only reviewer `2a5e9097-5f2a-489a-99a0-2c6769541898`, workflow `6ec48dd4-d7e9-4279-8d67-c077dd8e4012`, completed. 산출물: `/home/lazydino/.pi/agent/sessions/--home-lazydino-dev-lazy-harness--/subagent-artifacts/outputs/6ec48dd4-d7e9-4279-8d67-c077dd8e4012/change-tracking-research-design-review.md`.
- P2: T0/T1은 둘 다 미수정이므로 조기 완료 방지만 시험한다. 실제 수정·검증의 T2를 포함해야 낡은 상태를 갱신하는 능력을 볼 수 있다.
- P2: 원문 대조군 없이 소화 실패를 분리하기 어렵다. 원문 이력 대조군을 선택사항으로 두지 않는 실행안을 권고한다.
- 부모 제안: 실제 `assessmentPackets` 최소 수정과 보호 검사를 연구에 포함하되, 실행 승인 후에만 수행한다. 새 범용 runner/프로필/OS 격리 구현은 포함하지 않는다.
- 정확한 후속 질문: ‘지금 유효한 요구, 실제 구현 상태, 확인된 검증 범위는 무엇인가? 이 결함을 완료 처리할 수 있는가? 아니라면 무엇이 남았으며, 이전 판단에서 무엇이 왜 바뀌었는가? 근거 위치를 제시하라.’
- 권고 비교: A=시점별 누적 원문을 읽는 fresh 작업자, B=그 시점 소화본만 읽는 fresh 작업자. D0은 최초 원문으로 생성하고 D1/D2는 이전 소화본+새 증거로 갱신한다. 전체 원문을 매번 재요약하거나 이전 작업자 답을 넘겨 기억 갱신을 대체하지 않는다.
- 권고 반복: 독립3회 ×3시점 ×2읽기조건 = 후속 판단18개, 별도 소화9단계(총27개 논리 모델 단계). 구현자/검수/준비 실행은 별도 계수한다. 이는 모델 호출 수 확정이나 통계적 일반화 근거가 아니며 모델·순서·실행 계약은 첫 시험 전에 고정한다.
- 입력 경계: 실제 승인 원문, 실제 시점별 코드/검사/실행 근거만 사용한다. 미래 결과·부모 정답표·관찰 artifact의 interpretation 같은 답 해설은 child 입력에서 제외하고 원본과 입력 투영을 각각 보존한다. T2 실패도 실제 증거로 남기며 성공을 꾸며내지 않는다.
- 판정: 위험한 완료/상태 왜곡은 한 건도 평균에 숨기지 않는다. 근거 없는 단정을 피하는 안전성과 주어진 핵심 사실을 회수하는 유용성을 따로 채점한다. 무조건 ‘모름’이라고 답해서 통과하지 못한다. 실질적 근거 부족은 인용 형식 완화로 면제하지 않는다.
- Discovery capture: Planning=updated(독립 검토·권고안); DDD/SDD/BDD/TDD=candidate 유지; ADR/SSOT=none. 초안의 미정사항은 이 권고안으로 제안이 구체화됐을 뿐 사용자 확정으로 승격하지 않는다.

## 다방면 해결책 탐색 — 1차 문헌 근거, 채택 전

- 사용자 허용에 따라 후보를 넓힌다. 아래 외부 문헌은 이 호스트의 성능 증명이나 즉시 구현 명령이 아니다. 검색 합성 답변만으로 주장하지 않고 해당 원문 구간을 확인했다.
| 후보 | 기대하는 방어 | 남는 한계 / 확인할 점 |
|---|---|---|
| 필요한 순간 원문 재조회 | 소화본에서 빠진 근거나 오래된 사실을 중요한 판단 전에 다시 확인 | 잘못된 원문 선택·시점 해석은 남는다. 항상 조회/불확실할 때 조회는 별도 비교 후보 |
| 요구·구현·검증 상태의 명시적 분리 | 승인·변경·테스트 통과를 하나의 완료 문장으로 합치는 오류 방지 | 올바른 형식의 잘못된 내용도 가능. 구체적 상태 구조는 아직 제안 |
| 이력 보존과 현재 상태 재구성 | 과거 이유·철회·갱신을 남기고 시점별 상태를 추적 | 투영 자체의 오류, 동시성, 갱신 지연과 복잡성은 별도 검증 필요 |
| 원문/실행 결과를 받은 독립 검수 | 요약 작성자의 누락과 근거 없는 완료 단정을 별도 확인 | 단순 자기 재검토나 같은 모델의 동의만으로 정답 보장 불가 |
| 더 강한 모델 / 역할별 모델 비교 | 소화·판단 능력 차이를 따로 측정하는 후보 | 현재 조사로 어느 모델이 충분한지 미확인. 기억 구조 변화와 모델 교체를 동시에 해 효과를 섞지 않음 |
- Anthropic, Effective context engineering: lightweight identifiers를 유지하고 just-in-time으로 자료를 읽는 방식, structured note-taking, compaction을 설명한다. 과도한 압축이 중요한 맥락을 잃을 수 있다고 경고한다. <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- LongMemEval(ICLR2025), abstract: 정보 추출·여러 세션 추론·시간 추론·지식 갱신·답변 보류를 나눠 평가하고 indexing/retrieval/reading을 구분한다. 이 연구의 성능 수치를 V2에 전이하지 않는다. <https://arxiv.org/abs/2410.10813>
- AWS Event sourcing: immutable append-only 사건 기록으로 상태를 재구성할 수 있으나 충돌·복잡성·eventual consistency로 투영이 최신 상태와 다를 수 있음을 명시한다. 로그 보존이 의미 정확성 보장은 아니다. <https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing-pattern.html>
- Large Language Models Cannot Self-Correct Reasoning Yet(ICLR2024), abstract: 외부 피드백 없는 intrinsic self-correction이 당시 추론 실험에서 어렵거나 악화될 수 있었다. 현재 모든 모델/독립 검수의 무용성으로 일반화하지 않고, 원문·실행 피드백 없이 자기 동의를 검증으로 세지 않는 근거로 참고한다. <https://arxiv.org/abs/2310.01798>
- 검색/원문 artifact IDs: web_search `mtztppsdoeookf`, fetch_content `mtztq65ewskwcm`. 연구 후보 비교이지 새 시험군 등록은 아니다.
- Discovery capture: Planning=updated(조사와 후보표); SDD/BDD/TDD=candidate(상태 분리·원문 확인·대안 검증); DDD=none(이번 문헌 조사에 새 제품 용어 없음); ADR/SSOT=none(채택·config 변경 없음). 기존 승인된 수정과 대조 실험의 조건은 몰래 바꾸지 않는다.

## 승인된 비교의 실행 파라미터 준비

- 수정/독립 검수 완료, 실제33개 focused 검사 통과 및 부모6개 hash 재확인. 전체 check/standard는 기존 이미지·과거 native 표시 artifact 검증 문제로 실패했고 원본 로그를 보존했다. 새 소스/회귀 테스트 오류는 보고되지 않았다. 기존 유지보수와 연구 상태를 분리한다.
- 모델 registry를 현재 도구로 확인했다. 이번 새로운 비교는 현재 세션 모델 `openai-codex/gpt-6-astra:high`를 소화/읽기 양쪽에 동일하게 고정하는 실행안을 준비한다. 이전 Luna 보조시험과 사례·모델·출력 방식이 달라 결과 차이를 특정 개선의 효과라고 직접 비교하지 않는다. 이 모델의 우월성을 미리 입증했다고 주장하지 않는다.
- 결과는 native structured output의 단일 자연어 text 필드로 보존하는 최소 계약을 준비한다. 의미/근거는 독립 채점하며 긴 ID 복사 여부만으로 의미 신뢰도를 결정하지 않는다. 실행 중 모델 교체·결과 추출/보정·자동 재시도는 없다.
- 입력 준비·독립 검수는 기존 승인 실행의 의존 단계다. 시점별 입력과 정답 경계, 순서, hash를 첫 실험 호출 전에 고정한다. 새 범용 실행기 대신 이 연구 전용의 얇은 native workflow만 사용한다.
- Discovery capture: Planning=updated(동일 모델·입력 준비); TDD/SDD=candidate(실행 계약·검사표 구체화); DDD/BDD/ADR/SSOT=no independent delta. 추가 해결책 시험군은 아직 추가하지 않는다.
- 입력 준비 child `94b0569b-a4e7-4a50-ba4e-a973935571a0` completed; workflow `fe6a18d2-ef16-44e9-9087-cc2bb791c004`의 독립 검수 진행 중. 준비물은 `.local/v2-change-tracking-01/study-preparation/`에 있으며 보고된 offline27개 통과/164개 fake invocation은 실제 모델 시험 횟수가 아니다. 본 비교 미실행.
- Preflight 발견: 준비 workflow는 inline `runtime.cwd`와 `results[0].thinking`을 필수로 요구하지만 그 공개 반환 위치는 아직 확인되지 않았다. 현재 준비 child의 원본 status에는 cwd 및 steps[0].thinking=high가 있고, 이전 `audit-study.mjs`도 status/descriptor/session을 대조했다. 정보 자체 부재와 잘못된 투영 위치를 구별해야 한다. 독립 검수자에게 이 근거를 전달했으며 수신/반영은 별도 확인 대상이다.
- Discovery capture: Planning=updated(준비 결과·preflight 미확인); SDD/TDD=candidate(실제 native metadata 위치와 gate 적합성); DDD/BDD/ADR/SSOT=none. 검증 조건을 낮추거나 본 비교를 시작하지 않았다.
- 독립 입력 검수 `3db46f67-5a7c-4318-9675-43421ffb72c3` 완료: source/input wiring은 적절하나 inline-only metadata gate는 P1로 BLOCK. `fe6a18d2-ef16-44e9-9087-cc2bb791c004` completed; 본 비교0회. 최종 검수 artifact가 이전 no-issues 중간판정을 대체한다.
- Parent exact native source 확인: installed `src/workflows/scripted-workflow.ts:1053–1077`의 WorkflowScriptChildResult에는 cwd가 없고, `src/runs/foreground/subagent-executor.ts:4271–4294` 반환 객체도 cwd를 넣지 않는다. 같은 파일3149–3175의 async child SingleResult 투영은 model/attemptedModels/sessionFile을 넣지만 thinking을 넣지 않는다. 따라서 이 native 경로에서 그 두 inline 필드를 무조건 요구하는 현재 준비 gate는 적합하지 않다. 존재하는 원본 sidecar 정보를 없는 것으로 취급하면 안 된다.
- 상태: 코드/모델/CLI를 바꿔 우회하지 않으며 기존 준비 script·manifest·27개 mock 검사 결과를 보존한다. root=/home/lazydino/dev/lazy-harness.v2, branch=design/harness-v2, HEAD=58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b; dirty 기존 자료 보존. 기존 file-inventory/manifest가 준비 산출물 기준이다.
- 최소 수정 후보(미승인): inline에서 실제 제공되는 불일치/실패는 즉시 중단하고, cwd/thinking/context/tools는 run ID에 연결된 native status/descriptor/session 원본을 부모가 검수한다. 각 완료 알림에서 검수하고 불일치/미확정이면 중단; 최종 원본 대조가 끝나기 전에는 채점/채택하지 않는다. 요청값이나 모델 suffix로 실제 설정을 대신하지 않는다. 이는 검증 증거 위치와 시점 조정이므로 사용자에게 경계를 확인한다.
- Discovery capture: Planning=updated(P1·native source 증거·정지 및 수정 후보); SDD/TDD=candidate(실제 반환 계약과 원본 검수); DDD/BDD/ADR/SSOT=none. 실험 출력 또는 성공률은 아직 없다.
- **후속 사용자 승인(user-confirmed):** ‘실행 설정을 원본 기록과 대조하는 방식으로 검사기를 수정하고 계속할까?’에 ‘수정 후 비교까지 계속 (Recommended)’를 선택했다. 원본 대조 방식으로 최소 수정·독립 검수 후 이미 승인된 비교를 이어간다. 불일치/미확정 발견 시 중단하고 최종 대조 전 채점하지 않는다.
- 기존 미실행 script/manifest와 준비 결과를 보존한다. 승인 시점 workspace 상태/추적파일 diff는 `.local/v2-change-tracking-01/metadata-gate-approval-state.txt`, `metadata-gate-approval-diff.patch`; untracked 준비 파일의 기준은 기존 manifest/file-inventory다. 동일 native 경로의 검사기 수정이지 모델/CLI/설치 우회가 아니다.
- 수정본 독립 검수 `6eda2489-da17-4217-a4cc-a4894e550f32` 완료, ready-for-parent-native-preflight/no issues. Native static validate ok(동적 spawn 개수는 runtime budget으로 제한). 부모가 기존46개 준비 hash, 새 workflow/auditor hash,27개 빈 입력 root·미생성 출력 경로를 재확인했다.
- 부모 preflight 정본: `.local/v2-change-tracking-01/parent-native-preflight/preflight.json`. 이전 실제 delegate `a04b7d2f-c816-4e96-9812-7a6ae0abc1df`의 tools/prompt/inheritance/extensions를 현재 delegate 정의와 대조해 기준 원본으로 고정했다. 이전 Luna 실행의 model/thinking을 새 Astra 실행 증거로 사용하지 않는다. 새27개 각각 원본 설정을 검수한다.
- 실행 대상은 `metadata-gate-revision/study.workflow.js`, SHA256 `4809fb289196c9452c00d9d4a0523fa084d370081971f99c44846449c1df1d7d`. 호출 budget27, 단일 순차 workflow, 부모 최상위 임의 짧은 timeout 없음. 불일치 발견 시 native stop; 본 비교 결과는 최종 원본 대조까지 pending이다.
- **본 비교01 중단:** workflow `ec13321e-b9a0-41e3-926b-d10faa62e402`, ct01-step-01=`894e8ea2-3b7b-4d9f-848e-7b300df23024` completed. 부모 원본 검수는 `invalid: outside_tool:write`. 즉시 native stop을 요청하고 정지 알림을 확인했다. step02는 runId unavailable/stopped이며 완료로 세지 않는다. 의미 채점 없음.
- 관찰된 write 대상은 할당된 `native-outputs/ct01-step-01.md`뿐이며 이후 structured_output을 호출했다. 이 관찰로 임의의 원문 변경이나 외부 원문 참조가 있었다고 주장하지 않는다.
- Parent native source 확인: `src/runs/shared/single-output.ts:94–107`은 mutation-capable agent에게 지정 output path에 write하도록 지시한다. 반면 시험은 structured_output 외 도구를 모두 금지했다. 실행 기반의 출력 저장 지시와 시험 경계의 불일치를 확인했다. 기존 중단 결과를 소급 합격시키지 않는다.
- 정지 증거/원본 status·receipt·session·audit·output 및 workspace status/diff/branch/HEAD: `.local/v2-change-tracking-01/study-01-stopped/capture.json`과7개 byte/hash 복사본. 다음 시험은 재승인 후 별도 run·새 출력 경로를 사용하는 후보이며 아직 미실행이다.
- Discovery capture: Planning=updated(정지·근거·보존); SDD/TDD=candidate(할당 결과 저장과 원문 변경 금지의 경계); DDD/BDD/ADR/SSOT=none. 다른 모델/CLI로 fallback하거나 자동 재시도하지 않았다.
- **출력 경계 수정·재시험 승인(user-confirmed):** ‘결과 파일만 허용 후 재시험 (Recommended)’을 선택했다. 각 단계에 지정된 결과 파일 write만 허용하고 원문 변경·외부 읽기·다른 파일 쓰기는 계속 금지한다.
- 기존 중단 run/결과는 그대로 보존한다. 새 실행은 별도 출력 경로와 fresh roots를 사용하고 기존 D0 답을 재사용하지 않는다. 원문·정답 기준·모델·반복/질문은 유지하며 출력 저장 경계 변경을 명시한다.
- 출력 경계 수정본 독립 검수 `a2276a5b-58cc-49d5-ad95-fabaac2c473f` 완료/no issues. 부모 native static validate ok, 이전247개 파일 hash·새 script/config/auditor hash·27개 fresh root와 빈 출력 경로 재확인. 승인된55개 운영/경계 pointer를 되돌리면 이전 config와 완전히 같음을 부모가 확인했다.
- 재시험 preflight: `.local/v2-change-tracking-01/study-02-audits/preflight.json`; 실행 script=`output-boundary-revision/study.workflow.js`, SHA256 `55fa61431b0c5a3dcca4db16600cde00a04f4c46afc1cf5225f49905ec671237`. 새 결과는 원본 검수 전까지 pending.
- **재시험02 중단:** workflow `0b33517a-418c-44ee-9c23-aef546dbab66`의 실행 기반 상태는 complete지만 연구 반환값은 `stopped_ungraded`. 계획27단계 중5개 native child만 완료했고 이후 단계는 실행하지 않았다. 처음4개는 잠정 원본 대조에서 불일치/미확정 없음이며 최종 합격으로 승격하지 않는다.
- 5번째 `92a9dd08-b4b5-4815-aec7-47a7fb897ab2`의 수신 경과는31,181,387ms로 사전300,000ms 예산 초과; workflow 원예외 `Error: receipt_deadline`. 원본 세션에는 `terminated`, `fetch failed` assistant 오류와 미연결 tool call이 남았고, 부모 감사도 terminal_error/toolCount 불일치/linked_tool_result 미완결을 확인했다. 긴 경과시간의 원인이 네트워크·호스트 중단·시계 변화 중 무엇인지는 아직 확정하지 않는다.
- 원본 status/receipt/events,5개 session/descriptor/audit와 실제 반환 collection의28개 byte/hash 사본 및 workspace status/diff/branch/HEAD는 `.local/v2-change-tracking-01/study-02-stopped/capture.json`에 보존했다. Native 성공 표시나 읽을 수 있는 답변만으로 오류/예산 초과를 지우지 않는다. 의미 채점/원문 대 소화본 최종 비교는 미수행.
- Discovery capture: Planning=updated(중단·미확정 원인·보존); TDD=candidate(수신 경과/부분 응답·실행 오류와 의미 정확성의 분리); SDD=candidate(원본 실행/연구 완료 상태 구별); DDD/BDD/ADR/SSOT=none. 자동 재시험이나 다른 모델/CLI 우회 없음.
- **재개 승인(user-confirmed):** 사용자가 ‘계속해줘야지’라고 연구 지속을 요청했다. 슬립모드 전환이 원인일 수 있다는 설명은 사용자 가설로 기록하며 확정 원인으로 취급하지 않는다.
- 같은 조건의 별도 재시험03을 시작한다. 기존 중단02/첫4개 잠정 대조/5번째 오류는 모두 보존하고 재사용 성공 처리하지 않는다. 새27개 fresh 세션·출력 경로로 처음부터 실행하며 모델·입력·채점·5분 예산은 바꾸지 않는다. 슬립/전원 설정은 변경하지 않는다.
- **재시험03 수집 및 최종 원본 대조 완료:** workflow `b8ab6649-1753-4fa5-b942-80eedd4d352a`의27개 native child, 각 단계 잠정 대조와 최종 collection/receipt/session/descriptor 연결을 확인했다. `.local/v2-change-tracking-01/study-03-restart/final-audit/report.json`=`verified_native_records`. 이는 실행 증거의 확인이며 의미 품질 합격이 아니다.
- 의미 검수 입력은 기존 opaque review_id 순서로18개 후속 답변과9개 소화본을 분리했다. 답변은 `runtime.structuredOutput.text`만 투영한다. condition/repetition/model/cost 명시 메타데이터는 제외하되 내용·상속 참조에서 조건을 추론할 수 있어 완전 맹검이 아니다. 두 fresh read-only 검수에서 안전성·필수 의미별0/1/2·근거·실패 귀속을 별도 판단한다. 원본 답·기존 채점 기준은 변경하지 않는다.
- 준비 과정의 첫 `source.id` 조회는 실제 필드가 `source_id`여서 KeyError로 중단했고 파일은0개 생성됐다. 실제 스키마를 읽고 필드명을 바로잡아 준비했으며 이 이력은 `semantic-review/manifest.json`에 남겼다. 모델 시험 재실행이나 답변 복구가 아니다. Discovery capture: 기존 Planning evidence capsule 갱신; 별도 canonical 승격 없음.
- **검수 중 원본 wrapper 보완:** 두 독립 검수자가 읽기용 `sources/*.md`에 originalBytesSha256/originalBytes가 없어 메타데이터 인용을 판정할 수 없다고 각각 감독 질의했다. 부모가 기존 `source-corpus.json`=frozen config deltas 및27개 invocation의 공급 source 항목 일치를 확인하고 해당 완전 wrapper 읽기를 양쪽에 허용했다. Markdown projection hash와 원본 hash를 구별한다. 채점자료 투영 누락이며 실험 입력/답변/기준 변경·재시험·unblinding은 없다. 질의 및 확인은 `semantic-review/wrapper-clarification.json`에 보존; 의미 판정은 아직 pending. Discovery capture: 동일 Planning capsule 갱신, TDD 후보=검수 자료의 wrapper 보존; 나머지 layer 독립 변화 없음.

## 재시험03 결과 — 제한된 변경 추적 비교 완료

- 독립 검수 점수를 잠근 뒤 기존 private key와 연결했다. 원문 누적 이력 A는 **안전9/9, 필수 의미 충족9/9(60/60점)**, 갱신 소화본 B도 **안전9/9, 필수 의미 충족9/9(60/60점)**. 별도 소화본9개도 안전9/9 및60/60점이다. 숫자의 단위는 한 사례의3반복×3시점이며 독립 사례9개가 아니다.
- 양쪽 모두 미수정(T0)→승인됐지만 미구현(T1)→국소 수정·33개 집중검사/실제 재현 확인(T2)을 구별했다. 이번 rubric에서 불필요한 보류·요청/반환 혼동·조기 완료·과거 상태 고착은 발견되지 않았다. **소화 방식이 원문보다 우수하다는 증거는 아니다.**
- Native 보고 비용: A 읽기 **$3.033250**, B 읽기 **$1.964366**, 소화 생성·갱신 **$2.868460**. B 읽기만35.2% 낮지만 소화 포함 **$4.832826**, A 대비59.3% 높다. 비용으로 신뢰도 결함을 상쇄하거나 채택을 결정하지 않는다.27단계 수신 기준 전체 경과 약46.1분; A 읽기 합14.0분/B 읽기 합14.0분/소화 합18.1분이며 서로 다른 실행을 합산한 경과이지 병렬 서비스 지연이 아니다.
- 독립 검수 overhead는 reader **$1.767016**, digest **$1.539102**로 별도다. 위 비용은 native 보고값이며 과거 중단 시험·준비·부모 작업을 포함한 총운영비가 아니다.27개 실험 usage 누락은0개다.
- 검수자 원본 trace에서 각각 read23회/contact_supervisor1회, assistant terminal error0건을 관찰했다. Reader는 wrapper 메타데이터를 부모 확인에 의존했다고 명시했고 digest 검수자는 허용된 완전 corpus를 직접 읽었다. 이 차이와 wrapper 보완 이력을 보존한다.
- 한 실제 결함·정리된 입력·동일 Astra-high 계열·부분 맹검 범위다. 대규모 이력/장기 반복 갱신/실제 코딩 생산성으로 일반화하지 않는다. 과거 Luna 비교(A1/3/B0/3)는 사례·모델·출력 계약이 달라 직접 개선 효과로 환산하지 않는다. **V1식 작업자 판단 기록 vs 목적·태스크·완료조건 선행 기록의 주 비교는 여전히 미완료**다.
- 최종 집계: `.lazy-harness/evidence/v2-change-tracking-study03-result.json`; 상세 원답/원본대조/잠금 검수: `.local/v2-change-tracking-01/study-03-restart/{final-audit,locked-grading}/`; HTML: `v2-change-tracking-study03-result.html`. 기존 중단01·02와 실패 원본은 유지했다.

### Layer completeness / Discovery capture

| Layer | 이번 결과의 판단 |
|---|---|
| SDD | no independent delta — 기존 투영 수정 contract는 `.lazy-harness/tests/v2-request-list-projection.md` 참조; 이번 수집/채점은 contract 변경 아님 |
| BDD | no independent delta — 제품 사용자 흐름 변경 없음 |
| SSOT | no independent delta — 모델/설정/소유권 변경 없음; 슬립 원인은 여전히 미확정 |
| DDD | no independent delta — 새 도메인 규칙 없음 |

Planning=본 primary record에 제한된 결과·비용·한계 누적. TDD=기존 연구 rubric에 대한 실행/검수 증거 보존 및 evaluator wrapper 보존 후보 유지. ADR=새 채택 결정 없음. 이 결과만으로 framework 구조나 운영 정책을 변경하지 않는다.

### 다음 연구 후보 — 사용자 선택·실행 승인 전

- 추천 후보: 미완료인 **V1식 기록 절차 vs 목적·태스크·완료조건 선행 기록 절차**를 같은 실제 개발 과제에서 직접 비교한다. V1 조건은 현재 실제 절차를 확인해 고정하며, 단순히 ‘대충 기록’하는 약한 대조군으로 만들지 않는다.
- 공정성 후보: 양쪽에 동일한 요구사항·합격 기준·초기 코드·모델·도구 접근을 제공하고 기록 절차 차이를 명시한다. 요구 정보 자체를 한쪽에만 주거나 소화기까지 동시에 바꾸지 않는다. 첫 비교에서는 소화를 빼서 기록 생성·후속 활용을 먼저 관찰한다.
- 활용 평가 후보: 처음 일한 AI와 별개의 fresh AI가 각 조건의 코드·기록으로 후속 변경/회귀 대응을 수행한다. 정답 설명만이 아니라 실제 변경 결과와 별도 검증으로 작업 성공, 제약 위반, 거짓 완료, 필요한 근거 회수 여부를 본다. 초기 코드 품질 차이와 기록 품질 차이는 별도 관찰하며 기록 형식만의 인과효과로 단정하지 않는다.
- 단계 후보: 서로 다른 유형의 소수 과제로 예비시험 → 평가 기준이 두 조건을 공정하게 구분하는지 확인 → 기준을 고정하고 복수 과제·반복으로 본비교. 구체 과제·표본 수·합격 기준·예산은 아직 미정이며 이 문단은 실행 승인이 아니다.
- 대안 후보: 장기 이력·상충 근거에서 소화 갱신 스트레스 시험, 또는 현재 결과의 다른 모델/검수자를 통한 독립 재현. 둘 다 가치 있지만 기록 생성 방식의 주 비교를 대신하지 않는다.
- Discovery capture: Planning=위 추천/대안 후보를 보존; TDD=candidate(실제 후속 작업 기반 비교 설계), SDD=candidate(두 조건의 정보·도구·기록 경계), BDD=candidate(fresh AI 인계 후 변경 수행), DDD/SSOT/ADR=none. 사용자 선택·세부 계획 검수·실행 승인 전 새 실험/구현 없음.
- **사용자 선택(user-confirmed):** 다음 연구 방향으로 ‘두 기록 방식 직접 비교 (Recommended)’를 선택했다. 승인 범위는 해당 방향의 세부 설계 구체화이며 모델 실험·제품 구현 실행 승인은 아니다. 장기 기억/다른 모델 재현은 이번 주 비교와 구별해 보류한다.

## 의미 손실 보강 재시험 34 — 제한된 결과

- 사용자가 확인한 두 실제 의미 손실만 대상으로 기존 32/33 산출물은 변경하지 않고 새 sibling `tr-meaning-repair-34`에서 고정 8호출을 실행했다. Recorder 2회, 기존 33 질문·중립 지침의 원문/새 기록 비교 4회, Chat 사례의 범용 수식어 해석 보강 원문/새 기록 비교 2회이며 자동 재시도·수리·grader는 없었다.
- 범용 기록 지침은 제공된 필드·함수·조건의 원래 식별자와 이름, actor/action/object에 대한 수식어 부착을 보존하고, object restriction에서 exclusive actor를 추론하지 않으며 근거 부족은 불충분으로 남기도록 했다. 특정 사례 정답 이름은 지침에 넣지 않았다.
- 실제 새 기록은 반복 일정 사례의 `recurrenceExceptions`를 정확히 보존했다. 기존 중립 답변 지침으로 새 기록을 읽은 fresh 답도 그 이름을 정확히 회수했다. 이 표본에서는 관찰된 필드 이름 손실이 개선됐다.
- Chat 사례의 새 기록은 Dashboard의 편집 **대상** 제한을 보존하고 다른 actor 전부의 금지를 추론하지 말라고 명시했다. 그러나 기존 중립 답변 지침의 fresh AI는 원문과 새 기록 양쪽에서 여전히 다른 화면이 허용되지 않는다고 잘못 추론했다. 기록 개선만으로 reader 오류가 사라지지 않았다.
- 범용 답변 해석 보강을 적용한 별도 두 호출은 원문과 새 기록 모두에서 다른 화면의 허용·금지는 정보 부족이라고 올바르게 답했다. 원문 reader 오류는 Recorder 탓으로 돌리지 않는다.
- 8개 결과는 모두 strict flat schema를 통과했으나 이는 의미 합격과 별도다. provider 비용은 `$0.0086172`, 장부는 latest 1747→1755, spent 32.34609431→32.35471151, held 2.21489061 및 unresolved 1/895/989는 유지됐다. 보호 행과 기존 32/33 tree hash도 유지됐다.
- 한계: 이미 알려진 두 사례의 arm당 단일 fresh 표본이며 blind novel generalization이나 인과 증명이 아니다. “모든 것을 그대로 복사하면 성공”이라는 결론도 내리지 않는다. 상세 원문·요청·응답·동결 기준·hash·비용·시간·직접 의미 검수는 `experiments/v2-agentic-wiki-fragment-01/tr-meaning-repair-34/actual-run-02/`에 보존했다. `actual-run-01/`은 live call 전 allocation preflight 실패 이력으로 보존한다.
- Layer completeness: SDD/BDD/SSOT/DDD=no independent delta; TDD=기존 알려진 사례의 제한된 연구 증거이고 새 제품 회귀 contract 없음; Planning=이 primary evidence capsule만 갱신; ADR=채택 결정 없음.

## Implementation map

- `experiments/v2-reading-comparison/assess.mjs` — `assessmentPackets`의 요청/반환 분리 수정 완료. 초기 미수정 상태는 T0/T1 보존 증거이며 현재 상태가 아니다.
- `experiments/v2-reading-comparison/runner.test.mjs` 및 `request-list-projection.test.mjs` — 기존26개+추가7개 집중검사 및 실제 재현 증거. 상세는 `.lazy-harness/tests/v2-request-list-projection.md` 참조.
- `.lazy-harness/tests/v2-reading-comparison.md` — 실제 첫 비교, 평가 자료 오류 발견 및 원본 정정 이력.
- `.local/v2-reading-runtime-iInlC0/study-01-evidence/collection.json` — 원래 요청과 응답을 포함하는 보존된 실제 실행 자료.
- `.local/v2-reading-runtime-iInlC0/request-list-current-behavior.json` — 현재 동작의 읽기 전용 재현.
- `.lazy-harness/planning/v2-record-reading-comparison-plan.md` — 신뢰도 우선/변경 추적 선택 및 이전 비용 중심 보조시험의 역사.
- 이 문서는 초기 후보 계획부터 승인·실행·제한된 결과까지의 이력을 보존한다. 실행 전 상태는 역사적 캡처로 구별하며 최신 결과는 위 재시험03 절 및 `.lazy-harness/evidence/v2-change-tracking-study03-result.json`을 따른다.

## Discovery capture

| Layer | 판단 | 내용 |
|---|---|---|
| DDD | candidate | 요청한 자료와 실제 반환된 자료의 의미 구분; 제품 도메인 규칙 채택 전 |
| SDD | candidate | 평가 자료에서 원래 요청/반환을 보존할 인터페이스와 상태 구분 |
| BDD | candidate | 요구 승인→미수정→실제 수정/검증 사이의 후속 판단 |
| TDD | candidate | 상태 왜곡·증거 없는 완료·이력 손실 방지 기준 및 실제 목록 손실 회귀 |
| ADR | none | 저장소/모델/실행 구조 채택 없음 |
| SSOT | none | config/소유권/운영 정책 변경 없음 |
| Planning | updated | 사용자 우선순위, 실제 근거, 미확정 기준안과 실행 경계 보존 |

Rule placement: 연구 사례와 기준은 이 Planning이 primary. 사용자 확정과 제안을 구별하며 AGENTS·개인 메모·새 운영 정책에 복제하지 않는다.
