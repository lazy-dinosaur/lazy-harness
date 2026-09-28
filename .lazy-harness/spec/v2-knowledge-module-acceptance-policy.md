# SDD — 지식 모듈 add 조각 생성 계약 + acceptance_policy (마일스톤 (a))

## Rule digest
- Status: needs-review
- Status note: draft — 정책 결정 사용자 확정(2026-09-24), 구현·실측 전
- Layer: SDD
- Scope: layer-fact
- Covers: 소화 단계에서 원장 항목을 정본 조각으로 반영할지 정하는 규칙(acceptance_policy)과, add 가 새 조각 16필드를 채우는 방법
- Aliases:
  - acceptance_policy
  - 반영 규칙
  - add 조각 생성 계약
- Applies when: digest 가 eligible 항목을 처리할 때, 작업자가 judgement fact 를 쓸 때(kind·근거 유형), 러너/소화자 구현 시
- Must: 정책은 코드가 집행하고 첫 일치 규칙이 이긴다. 기본값은 hold. 조각 text 는 작업자 fact 원문 그대로. 충돌은 항상 사람
- Must not: Jev confidence 를 권한으로 쓰지 않는다. 생각 중인 사용자 발언이나 AI 추론 결정을 확인 없이 정본에 넣지 않는다. reference_only 를 정본에 넣지 않는다

## 1. 사용자 확정 결정 (2026-09-24)
1. **reference_only 처분** — 정본에 넣지 않고 원장 증거로만 보존(retained_as_evidence). 삭제 아님. 예: 실행 id, 점수 하나, 기존 규칙 재설명.
2. **자동 반영 조각의 confidence = confirmed** — Jev 검수 + 소화 시점 최신 정본 재검 + 완료 사건(PR 머지 등)을 모두 통과한 것은 확인된 지식. candidate 는 작업 중 workspace 조각에만. contested 는 충돌 표시.
3. **근거 유형에 따른 자동/확인 구분 (v1 규칙 계승)**
   - 자동 반영: 공식 문서·코드/테스트 근거, 또는 **사용자 확정 발언**(옵션 게이트에서 고른 답, 'X로 가자'·'이거로 가자' 같은 명확한 지시, '아니, X가 맞아' 같은 정정).
   - 확인 필요: **사용자 생각 중 발언**(물음표, '~것 같다', '~인가?', '안 그래?')과 **AI 추론**만 근거인 decision/constraint.
   - 근거: v1 AGENTS.md §2.3(고른 답은 user-confirmed, 다시 묻지 않음), §2.5/ADR 0032(정정은 confirmed override), §2.3 게이트(여러 해석 가능 시 멈춤), ADR 0038('맞지?'는 승인 아님). 실제 사례: 'duckdb가 맞겠는데??'(생각 중) → 몇 분 뒤 메인 PG 로 바뀜. 발언을 그대로 결정으로 기록했다면 틀린 정본.
4. **확인 시점 = 둘 다** — 작업자가 대화 중이면 그 자리에서 옵션 게이트(답이 확정 발언 근거가 되어 자동 반영). 대화 불가(배경 작업자·pi-fabric 프로세스·세션 종료)면 확인 대기 목록 → 다음 세션 시작 때 모아서 묻기. 목록은 빈틈을 막는 안전망.
5. **충돌은 항상 사람** — 소화 재검에서 의미 모순(Jev) 또는 CAS 실패 후 재검 불가.

## 2. judgement fact 추가 필드 (작업자 작성)
| 필드 | 값 | 비고 |
|---|---|---|
| kind | fact/decision/rationale/rejected/constraint/procedure/term/question | 조각 kind enum 그대로. lint 로 값 검사 |
| evidence_source | user_confirmed / user_tentative / official_doc / code_test / observed_output / ai_inference | 근거 유형. user_* 는 evidence_quote 가 사용자 발언 원문이어야 함 |
- user_confirmed/user_tentative 구분은 작업자가 원문을 보고 선언한다. 오선언 검출용 Jev 질문 `utterance_status`(choice): 'user_utterance 는 결정을 확정한 발언인가, 아직 검토 중인 의견·질문인가?' — confirmed_decision(선택·지시·정정으로 결정을 확정한 발언이다)/tentative_opinion(의견·추측·질문이며 결정을 확정하지 않은 발언이다)/none_or_uncertain, state={preceding_context(중립 서술), user_utterance(원문)}. **검증 통과(jev-utterance-status-15, 이 세션 실제 발언, Jev 14회)**: 확정 6/7 auto(0.99~1.0), 생각 중 6/6 auto tentative(0.97~1.0), 생각 중의 확정 누출 0. 회부 1건('안정적인지 확인해야해' — 지식 결정이 아닌 행동 지시). 경계('…가능한거 잔아 맞지?' 정정)는 tentative 0.99 → 확인으로 감(v1 §2.3 과 같은 보수성). 사용안(러너 구현 대상): evidence_source=user_confirmed 선언 시 이 질문 실행 → auto tentative 이면 user_tentative 로 강등, 회부면 확인 필요, auto confirmed 면 선언 유지.
- observed_output(실행 로그·측정 출력)은 fact/procedure 에만 자동 근거. decision/constraint 근거로는 확인 필요 취급.

## 3. acceptance_policy 정책 언어
- 형식: 순서 있는 규칙 목록 `{id, when: {조건...}, then: 처분}`. **첫 일치 규칙이 이긴다. 아무 규칙도 맞지 않으면 hold.**
- 조건 키(코드가 계산 가능한 값만): combined(러너 결합 결과), review_reasons, operation, kind, evidence_source, conflict(소화 재검 모순/CAS), can_ask_now(대화 창구 존재), completion(완료 사건 도착).
- 처분: absorb(정본 반영, confirmed) / retain_as_evidence(원장 보존) / reject / ask_now(옵션 게이트) / queue_for_human(확인 대기 목록) / hold.
- 정책은 **DB 에 저장**한다(v2 는 모든 것을 DB 에 둠 — 사용자 확정 2026-09-24). host 별 정책 행 + 버전. Jev·Luna 는 정책을 수정하지 않는다.

### 기본 정책 v0.1 (위 확정 결정을 옮긴 것)
```
P01 when completion=false                                         then hold
P02 when conflict=true                                            then queue_for_human   # 충돌은 항상 사람
P03 when combined=duplicate_skip                                  then reject
P04 when combined=no_record                                       then retain_as_evidence
P05 when combined=needs_review, reason='impact: reference_only'   then retain_as_evidence   # 결정 1
P06 when combined=needs_review, can_ask_now=true                  then ask_now
P07 when combined=needs_review                                    then queue_for_human
P08 when kind in (decision,constraint), evidence_source in (user_tentative,ai_inference,observed_output), can_ask_now=true then ask_now
P09 when kind in (decision,constraint), evidence_source in (user_tentative,ai_inference,observed_output)                   then queue_for_human
P10 when combined in (record,update_record,deprecate_record)      then absorb
(기본) hold
```
- P05 는 러너 v0.2.2 가 reference_only 를 needs_review + 'impact: reference_only (policy pending)' 로 내는 현재 구현과 맞물린다. 사유가 그것 하나일 때만 적용(다른 회부 사유가 섞이면 P06/P07).
- ask_now 의 답이 확정이면 evidence_source=user_confirmed 로 judgement 를 resubmit 해 정책을 다시 탄다(자동 반영). 거절이면 reject.

## 4. add → 새 조각 16필드
| 필드 | 채우는 쪽 | 규칙 |
|---|---|---|
| id | 코드 | 새 ULID |
| host_id | 코드 | work_unit.host_id |
| workspace_id | 코드 | absorb 시 NULL(= host 정본) |
| alias | 코드 | domain + seq |
| domain | 코드 | partition_key |
| seq | 코드 | (host_id, domain) 다음 번호. 동시 발급은 PG 시퀀스/잠금((b)) |
| text | 작업자 | judgement fact 원문 그대로. 코드가 원장 fact 와 바이트 일치 검사 |
| keywords | Luna | fact·evidence_quote 에 실제 있는 어휘만. lint: 각 keyword 가 둘 중 하나의 부분 문자열 |
| kind | 작업자 | judgement fact.kind |
| group_id | 코드 | 같은 judgement(판 번호 무관)의 조각끼리 동일 값 |
| revision | 코드 | 1 |
| active | 코드 | true |
| confidence | 정책 | absorb → confirmed (결정 2) |
| source | 코드 | {evidence_refs, evidence_source, ledger entry_id, fact_index, check receipt ids, completion event, captured_by} |
| valid_from | 코드 | 소화 시각 |
| superseded_at | 코드 | NULL |
- create 는 fragment_history 에 전체 행 스냅샷(기존 Trial 51~53 계약 재사용). update/deprecate 는 기존 계약 그대로(revision CAS, deprecate 는 active=false + history).

## 5. 미확정
- utterance_status 는 13+1 사례·단일 사용자 구어체·단일 반복 검증 — 다른 사용자 문체에서 재확인 필요.
- 확인 대기 목록 저장소·세션 시작 시 보여주는 방식(pi-fabric 통합과 함께).
- 정책 테이블 스키마·버전 관리, host 별 덮어쓰기 범위 — (b).

## Rule placement
- Rule: 지식 모듈 acceptance_policy(근거 유형별 자동 반영/확인, reference_only 원장 보존, 자동 조각 confirmed, 확인 시점 둘 다, 충돌은 사람)와 add→16필드 생성 규칙, judgement fact 의 kind·evidence_source 입력 계약
- Scope: layer-fact (연구 host lazy-harness.v2 의 지식 모듈 component/data contract)
- Primary record: .lazy-harness/spec/v2-knowledge-module-acceptance-policy.md (보조 반영: v2-worker-judgement-authoring-guide.md, v2-knowledge-module-schema-delta.md 미확정 포인터)
- Why not AGENTS.md: 에이전트 전역 행동 규칙이 아니라 모듈 코드가 집행할 계약이다. AGENTS.md 는 포인터/프레임워크 문법만 둔다.
- Why not ssot/policies.json: rule-sources.md — 프로젝트 사실·계약은 DDD/SDD/… 레이어에, 개발 중 에이전트 행동 규칙만 policies.json. 이 규칙은 모듈 런타임의 데이터/컴포넌트 계약('API/component/data/IPC contract → spec/**')이다. 운영 시 정책 값 자체는 v2 DB 에 저장(사용자 확정 '모든 것을 DB 에'), 이 문서는 그 계약.
- Why not local notes: 팀/다음 세션이 공유해야 하는 계약이라 .pi/APPEND_SYSTEM.md·memory 는 부적합. memory 에 저장한 적 없음.
- Confirmation: user-confirmed(정책 내용 5건, 2026-09-24 옵션 게이트·'좋아 그렇게 하도록 하자') / 위치는 inferred-from-record(rule-sources.md 표 'API/component/data/IPC contract → .lazy-harness/spec/**' 와 사실·운영규칙 구분 문단)

## Implementation map
- 관련 계약: .lazy-harness/spec/v2-knowledge-module-event-contract.md(원장·소화·CompletionSource), .lazy-harness/spec/v2-knowledge-module-schema-delta.md(absorption.decided_by=acceptance_policy), .lazy-harness/spec/v2-jev-question-template-contract.md(v0.2.2 impact·결합 규칙), .lazy-harness/spec/platform/v2-fragment-knowledge-store.md(16필드·kind/confidence enum·§6.2 위험 등급 — 본 정책이 decision/constraint '사람 판단 유지'를 근거 유형 기준으로 구체화), .lazy-harness/spec/v2-worker-judgement-authoring-guide.md(kind·evidence_source 작성)
- 코드(예정): experiments/v2-knowledge-module-runner-01/store.py digest(정책 집행), runner.py lint(kind·evidence_source·keywords)
- v1 근거: AGENTS.md §2.3·§2.5, ADR 0032, ADR 0038
