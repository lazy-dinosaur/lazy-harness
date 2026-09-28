# SDD — 작업자 judgement 작성 가이드 (draft, 마일스톤 (d))

## Rule digest
- Status: needs-review
- Status note: draft — 사용자 검토 대기
- Layer: SDD
- Scope: layer-fact
- Covers: 작업자가 judgement 의 facts[] 에 지식 후보를 적는 방법 — 사실 문장, 근거 인용, 이유, 의도(add/update/deprecate)
- Aliases:
  - judgement 작성 가이드
  - worker judgement authoring
  - 작업자 facts 작성
- Applies when: 작업 중 기록할 사실을 발견해 judgement 를 등록하거나 회부를 받아 정정할 때
- Must: 사실 하나에 주장 하나만 적고, 인용이 주장의 모든 부분을 문면 그대로 뒷받침하게 하며, 주장을 인용보다 넓히지 않는다
- Must not: 새 사실을 reason 에만 적지 않는다. 인용에 없는 식별자·일반화·함의를 주장에 넣지 않는다. 진행 상황을 사실로 적지 않는다

## 왜 필요한가 (실측)
2차 사이클 C4 파일럿에서 회부 원인의 다수가 Jev 판정이 아니라 **작업자 judgement 의 근거 부족**이었다. Jev 는 그 부족을 문면 그대로 검출했다. 즉 모듈 품질의 병목은 작업자 근거 품질이다.

## 규칙
> **단일 규격 (2026-09-25):** 작업자가 쓰는 fact 는 `.lazy-harness/spec/platform/v2-fragment-knowledge-store.md` §1.1 조각 저장 품질 규격 v1 을 따른다. §1.1.1 의 구조 칸(subject 필수·decision/constraint 근거 2개 이상·decision why·user_confirmed 는 되묻지 않은 확정 발언 인용)은 러너 lint 가 강제한다. 아래 규칙은 그 규격을 쓰는 방법이다.

### 1. 사실 하나 = 주장 하나
- 여러 주장을 한 fact 에 넣지 않는다. 필요하면 fact 를 나눈다(Luna 가 fan-out 하지만, 작업자가 처음부터 나누는 게 가장 정확).
- operation(add/update/deprecate)을 반드시 적는다.
- kind(fact/decision/rationale/rejected/constraint/procedure/term/question)와 evidence_source(user_confirmed/user_tentative/official_doc/code_test/observed_output/ai_inference)를 적는다. 사용자 발언이 근거면 원문을 인용하고, 옵션 게이트 답·명확한 지시·정정은 user_confirmed, 물음표·'~것 같다'·'안 그래?' 같은 생각 중 발언은 user_tentative. 근거 유형에 따라 자동 반영/확인이 갈린다(acceptance-policy §1·§3).

### 2. 인용은 주장의 모든 부분을 덮어야 한다
- 주장에 A·B·C 세 요소가 있으면 인용에도 세 요소 각각의 근거가 보여야 한다.
- 실측(C4 fact1 v1·v2): 주장은 키 공식 전체였는데 인용은 "무엇이 충돌한다"는 **문제 설명만** 있었다 → scope expanded 0.92 로 회부. v3 에서 **공식 자체가 적힌 원문**(이벤트 계약 §2)을 인용에 넣자 통과.
- 규칙: "왜 필요한가"만 인용하지 말고 **"그래서 무엇인가"가 적힌 원문**도 인용한다.

### 3. 주장을 인용보다 넓히지 않는다
- "모든", "항상", "보장한다" 같은 일반화, 인용에 없는 함의를 넣지 않는다.
- 실측(C4 fact0 v2): 주장 "다중 작성자 동시성을 보장하지 않는다" vs 인용 "동시 경쟁은 원자적이지 않다" → should_record 0.60 경계. v3 에서 "다중 작성자 보장은 없음" 원문을 추가하자 1.0 지지.
- 실측(1차 P4): "모든 escape 테스트"라는 과일반화를 소화자가 scope 평평으로 감지.

### 4. 인용은 원문 그대로, 이름은 주장과 똑같이
- 인용 문자열을 요약·의역하지 않는다. 주장에 쓴 식별자·이름은 인용에도 같은 표기로 있어야 한다(러너 lint E_CLAIM_QUOTE).
- 실측(1차 P1): 주장 `E5` / 인용 `SCEN-1` → contradicted. (1차 C1 CASE-2): 주장 문구와 인용이 어긋나 판정 붕괴.

### 5. 새 사실은 fact 에 적는다, reason 에만 두지 않는다
- reason 은 "왜 기록하는가"다. 새 사실을 reason 에만 쓰면 기록되지 않는다.
- 실측(Trial48 C2): 격리 검사 4개 통과라는 새 사실이 reason 에만 있어 retain-only 로 정본에서 누락.

### 6. update 는 새 값과 대상을 명시한다
- target_ref(고칠 조각)와 **바뀐 뒤의 내용 전체**를 fact 에 적는다. 인용은 새 값을 직접 뒷받침해야 한다(규칙 2).
- reason 에 기존 내용이 왜 틀렸는지 적는다.

### 7. deprecate 는 이유와 대체를 적는다
- 무효가 된 근거와 대체 지식(없으면 "대체 불필요"와 그 이유)을 적는다. 대체가 필요한데 없으면 회부된다.

### 8. 진행 상황은 사실이 아니다
- "실행 시작함", "배치 완료" 같은 일시 정보는 기록 대상이 아니다(durability transient → no_record).
- 정의·스펙은 공식·키·스키마를 그대로 적는다(durable_fact 로 판정됨).

### 9. 결정에 쓰였는지를 사실로 적고, 중요도는 평가하지 않는다
- reason 에 이 사실이 작업에서 무엇을 바꿨는지/바꾸지 않았는지를 사실로 적는다(예: 'DB 선택을 PG 로 확정하게 했다', '판단에 쓰이지 않았다').
- '매우 중요', '핵심', '결정적', '사소한' 같은 중요도 평가어는 쓰지 않는다 — 판정을 끌어당기고(실측 0.43) 러너 lint E_EVALUATIVE 로 거절된다.
- 실측(impact-stability-14): 맥락 없는 사소한 사실은 '불확실'로 회부됐고, '판단에 쓰이지 않았다'를 적은 사례는 확실히 걸러졌다.

## 제출 전 자가 점검 (30초)
1. fact 하나에 주장 하나인가?
2. 주장의 각 요소가 인용에 문면으로 보이는가? (문제 설명만 있고 결론 원문이 빠지지 않았나)
3. 주장이 인용보다 넓지 않은가? (일반화·함의 없음)
4. 인용이 원문 그대로이고, 이름 표기가 주장과 같은가?
5. 새 사실이 reason 이 아니라 fact 에 있는가?
6. update/deprecate 면 target_ref·새 값·대체가 있는가?
7. reason 에 결정에 쓰였는지가 사실로 있고, 중요도 평가어가 없는가?

## 코드가 돕는 부분 (현재/후보)
- 현재: 러너 lint E_CLAIM_QUOTE(식별자 표면 일치), E_TARGET(target 존재·발췌 일치), E_STATE.
- 후보(미구현): 주장 요소별 인용 커버리지 휴리스틱, reason 에만 있는 새 명사구 경고.

## 미확정
- 회부율 감소 효과: **1차 측정 동률(jev-d-guide-12)** — 가이드 없음 A 1/2, 가이드 있음 B 1/2, 인용 원문 일치 2/2 동률. A 는 주장을 확대했고('어렵다'→'할 수 없다') B 는 인용 표현을 유지했으나 Jev 판정 차이로 이어지지 않았다. 과제가 쉬워(근거가 한 문장에 모여 있음) 천장 효과. 다음 측정은 근거가 여러 곳에 흩어진 어려운 과제가 필요. 두 팀 add 는 모두 should_record 경계(0.61/0.57)로 회부 — 이 병목은 작업자 문장이 아니라 질문 쪽 후보.
- 가이드를 작업자에게 전달하는 경로(프롬프트/스킬/규약 참조).

## Implementation map
- 실측 근거: active root .lazy-harness/evidence/jev-c4-pilot-11-result.json (v1→v3 회부 이력), jev-p1-expand-08-result.json (E5/SCEN-1), jev-offline-replay-03-case2-repair-result.json, Trial48 C2 원장 누락(primary 캡슐)
- 관련 계약: .lazy-harness/spec/v2-knowledge-module-event-contract.md §1 (작업자=지식 본문 1차 작성자, facts 의도), .lazy-harness/spec/v2-jev-question-template-contract.md (입력 규칙 2)
- 코드: experiments/v2-knowledge-module-runner-01/runner.py (lint)