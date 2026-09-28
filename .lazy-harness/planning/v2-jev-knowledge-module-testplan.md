# Planning — 지식 관리 모듈 시험 계획 (Jev 기반, 실제 반영 수준까지)

## Rule digest
- Status: completed — P0~P5 전 단계 exit 충족 (2026-09-24). 평가·채택 자료는 v2-jev-knowledge-module-p5-evaluation.md
- Layer: Planning
- Scope: 지식 관리 모듈(judgement 검수·기록 필요성 판정·임시원장·완료 추적·소화)을 실제 반영 가능 수준으로 끌어올리는 단계별 시험 계획
- Applies when: 이 모듈 관련 다음 실험/설계/위임을 시작하거나 진행 상태를 판단할 때
- Must: 단계별 exit 기준을 통과해야 다음 단계로 가고, 각 단계 시작은 사용자 승인을 받으며, 정본 자동 반영·acceptance 자동화는 전 단계에서 금지 유지

## 확정된 역할 분담 (사용자 정정 반영 2026-09-24)
- **설계**: Parent(현재 세션 모델)가 직접 한다. Sol에게 설계를 넘기지 않는다.
- **실제 모듈 런타임**: openai-codex/gpt-6-luna(작성) + Jev(typesafe/jev-1.13, 판정) **만** 사용한다. 모듈 동작에 다른 모델은 들어가지 않는다.
- **제작(구현)**: openai-codex/gpt-6-sol:medium 에게 위임하는 것이 기본이다(토큰 절약). Parent는 설계서를 주고 결과를 검수한다. Sol은 모듈 구성요소가 아니라 제작 도구다.
- **테스트/검증**: 사용자와 Parent가 함께 한다(사용자 승인 + Parent 검수).
- **결합·권한·집행**: 코드 (Jev 답은 권한을 만들지 않음)
- **검수·게이트**: Parent 검수 + 사용자 승인. 실제 반영 경로는 추후 pi-fabric(미조사).

## 전제 자산 (검증 완료)
- 규약: `.lazy-harness/spec/v2-jev-question-template-contract.md` (draft, 공백 4개 반영됨)
- 템플릿: 원장 검수 v0 (replay-02/03/04, e2e-05), 기록 필요성 v0.2 (record-need-06, 12/12)
- 분기 신호: 고신뢰 자동 진행 / 평평한 분포 회부 (합산 고신뢰 44답 중 43 일치, 표본 한정)
- 운영 흐름: 입력→검색→전달→작업+임시원장→완료 추적(git 비의존)→소화자 선별 (사용자 확정)

## 단계 계획

### P0. 규약 마감 (문서 + 소액 재검)
- 내용: v0.2 온톨로지를 규약에 정식 추가. e2e-05에서 개정한 record_state 대상/boundary 단계 명시 질문으로 factD/boundary 재검 1회(Jev 1호출) — 공백 해소 효과 확인.
- exit: 규약에 미검증 조항 없음. 재검에서 개정 질문이 이전 불일치 2건을 해소하거나, 실패 시 원인 기록.
- 예산: Jev 1호출.

### P1. 확대 검증 — 자기참조성 제거
- 내용: 타 세션/타 프로젝트의 실제 judgement·기록 사례 6~10건(예: medivance .lazy-harness records, 과거 v2 세션 캡슐)으로 v0/v0.2 템플릿 검증. 패킷 생성은 Luna, 사례 선정·기대값은 Sol 설계+Parent 검수. gold는 실제 처분/실제 기록 여부.
- exit: label 일치율과 회부율을 기록하고, 불일치의 원인 분류(입력 결함/온톨로지 공백/Jev 한계)가 전부 가능할 것. 수치 목표는 첫 결과 후 사용자와 확정.
- 예산: Luna 1~2 run + Jev 6~10호출.

### P2. 미니 러너 — 결합·lint의 코드화 (오프라인)
- 내용: Sol(medium)에게 설계·구현 위임: 파일 기반 오프라인 러너 1개 — packet lint(wire 스키마/escape/조건부/익명화 누출) + Jev 호출 + 코드 결합 분기(자동 진행/회부/보류)를 코드로. Parent가 지금까지 손으로 하던 일을 전부 코드화. 실 Jev 호출은 기존 frozen 사례 재사용.
- exit: 기존 사례 재실행 시 손작업 결과와 동일 분기. lint가 e2e-05의 결함 4종을 자동 검출.
- 예산: Sol 1~2 run + Jev 2~4호출(재실행 검증).

### P3. 이벤트·완료 트래킹 계약 설계 (문서만)
- 내용: Sol 설계 위임: (a) judgement 완결 이벤트 계약 — 트리거 시점, 중복 호출 키(judgement id/version+evidence digest+template ver+model ver), 상태 머신(임시/완료/폐기), (b) git 비의존 완료 추적 추상화 — 완료 신호 등록(머지/사용자 확정/acceptance), (c) 소화자 자격 판정 시점. Parent+사용자 검토 후 SDD record로 확정.
- exit: 사용자 승인된 이벤트 계약 SDD 1건. 구현 없음.
- 예산: Sol 1 run. Jev 0회.

### P4. 파일럿 — 실제 작업 1건 end-to-end
- 내용: 실제 작은 작업 1건을 모듈 흐름으로: 작업(작업자)→judgement→Luna 패킷→러너(P2) lint+Jev+분기→임시원장 파일→완료 신호(사용자 확정으로 대체)→소화 자격 판정(Jev)→소화 제안서 출력. **정본 반영은 제안서까지만, 실제 반영은 사용자 확인.**
- exit: 전 구간이 코드+모델로 흐르고 사람 개입이 승인 게이트 2곳(완료 신호, 소화 반영)뿐임을 확인.
- 예산: Luna 1~2 run + Jev 3~6호출.

### P5. 평가·채택 결정
- 내용: P0~P4 결과 종합, 실측 비용/회부율/오류 유형 정리, 규약·템플릿 최종본, 채택 여부와 pi-fabric 적용 조사를 사용자와 결정.
- exit: 채택/보류 결정 기록. pi-fabric 조사는 별도 승인.

## 안전 원칙 (전 단계 공통)
- 정본 자동 반영·acceptance 자동화·자동 승인 금지. Jev 답은 권한 아님.
- 모든 실험은 호출 전 기대값/plan 고정, 원본 실패 보존, 소급 성공화 금지.
- 외부 전송은 치환표 익명화 + 누출 검사 통과 후.
- 각 단계 시작 전 사용자 승인. 단계 내 소액 Jev 호출은 해당 단계 승인에 포함.
- Trial57 STOP·보호 holds·기존 장부는 이 계획과 무관하게 그대로 유지.

## 미확정 (계획이 정하지 않는 것)
- P1 일치율 수치 목표(첫 결과 후 확정), threshold 수치(0.15 근접 규칙은 잠정), pi-fabric 통합 상세, 소화자 원장 병합 계약(whole-batch 원자성과의 접합).

## Implementation map
- 규약: `.lazy-harness/spec/v2-jev-question-template-contract.md`
- 실측: `lazy-harness(active root)/.lazy-harness/evidence/jev-*-{plan,result}.json` (ledger-review-01, replay-02/03/03-case2/04, e2e-05, record-need-06)
- 운영 흐름·역할 확정 경위: `.lazy-harness/planning/v2-vision-feasibility-research.md` 2026-09-24 캡슐들
- 호출 경로: Pi `jev_evaluate` (pi-jev 0.5.0, OpenRouter, `TYPESAFE_BASE_URL`)
