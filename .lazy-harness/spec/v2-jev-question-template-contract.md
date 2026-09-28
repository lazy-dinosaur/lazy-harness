# SDD — Jev 질문 템플릿 규약 (V2 judgement 검수용)

## Rule digest
- Status: needs-review
- Status note: draft — 사용자 검토 대기, 운영 계약 미채택
- Layer: SDD
- Scope: layer-fact
- Covers: V2 judgement/원장 검수에 Jev(System One)를 쓸 때의 질문·입력·해석 규약
- Aliases:
  - Jev 질문 템플릿
  - Jev question template
  - 검수 질문 규약
- Applies when: Jev 호출용 질문 템플릿을 작성/수정하거나, judgement 검수 입력 패킷을 만들거나, Jev 응답을 분기 처리할 때
- Must: 질문 하나에 문자 그대로 판정 가능한 조건 하나만 담고, 규범(해야 하나)과 서술(그랬나)을 분리하며, choice에 escape 옵션을 두고, 평평한 분포는 자동 진행이 아니라 작성자 회부로 처리한다
- Must not: Jev 답을 저장/acceptance 권한으로 취급하거나, 수치·날짜·ID 대조를 질문에 넣거나, 처방문이 섞인 서술을 state로 보내지 않는다

## 근거 (실측)
- `jev-offline-replay-02` 18/25 → 결함 수정 후 `-03` 24/30, CASE-2 수리 재검 2/6→4/6.
- 고신뢰(>=0.85) 답 합산 28건 중 27건 기대 일치 (상관 표본, 일반 신뢰성 주장 아님).
- 불일치 주원인은 일관되게 입력/온톨로지 결함이었고 평평한 확률 분포가 그 지점을 신호했다.
- 공식 근거: TypeSafe failure-modes(문자 그대로 읽기·복합판단 금지·수치/날짜는 코드), agent 가이드(보존 필요성 판단은 공식 사용례, 코드가 권한·집행 소유), 과금(입력 토큰만, 한 호출 다질문 병렬).

## 1. 질문 작성 규칙
1. **1질문 = 1문면 조건.** 판정 조건을 문자 그대로 읽어도 오해가 없게 쓴다. 지시문은 지침("~단정하지 않는다")이 아니라 직접 질문/명령("~인지 고르라")으로.
2. **규범/서술 분리.** "기록해야 하나"(need)와 "기록됐나"(state)는 반드시 별도 질문. 실측: 혼합 enum은 2/5, 분리 후 4/5(확신 0.9~1.0).
3. **choice에는 escape 필수.** `none_or_uncertain` 류 옵션이 없으면 확률 질량이 가장 덜 틀린 옵션에 높은 확신으로 실린다. 실측: CASE-5 record_state가 '자료만으로 알 수 없음'을 0.93으로 정확 선택.
4. **noul criteria는 true/false 쌍만.** 임의 키(hold/proceed)는 계약 위반. noul 답은 yes 확률이며 confidence 필드가 없다.
5. **한 판단은 한 형식으로만.** 같은 판단을 noul과 choice로 겹쳐 묻지 않는다(공식: 두 형식은 불일치할 수 있음).
6. **수치 계산·날짜 비교·ID/hash 대조 금지.** 코드 몫이다.
7. **다중 새 사실은 사실별 fan-out.** "근거의 새 사실"처럼 단수 지칭으로 여러 사실을 묶으면 판정이 흔들린다(CASE-3). 사실 하나당 질문 세트를 복제한다. 한 호출 다질문은 비용·시간이 거의 같으므로 아끼지 않는다. 실측(replay-04): 혼재로 틀렸던 record_state가 분리 후 FACT-A recorded 0.82로 교정, 미확인 FACT-B는 confirmed 0.21로 정확 분리.
8. **질문 안에 조건부 지시 금지.** "~이면 ~을 고르라" 형태는 같은 호출의 다른 질문 답을 참조할 수 없는 Jev 제약과 충돌한다(실측: replay-04 factB_record_state 분산). 질문은 단일 조건만 묻고, 질문 간 결합(예: 미확인 사실은 record_state 와 무관하게 기록 대상 제외)은 코드가 수행한다.

## 2. 입력 패킷 규칙
1. **narrative는 서술만.** "~해야 한다" 처방문 금지. 실측: 처방문 제거로 CASE-1 scope가 preserved 0.65→narrowed 0.90 교정.
2. **atomized_claims = 주장 + 원문 인용.** 인용은 원문 그대로, 주장 문구는 인용과 문면상 일치해야 한다. 실측: 주장-인용 상충이 CASE-2를 2/6으로 붕괴시켰고 수리로 4/6 회복.
3. **state는 질문에 필요한 최소만.** 무관 문맥은 정확도를 떨어뜨린다(공식). 질문 지시문이 참조하는 키 이름은 state에 실제로 존재해야 한다.
4. **외부 전송 전 치환표 익명화.** 원본 식별자·경로·키는 승인된 치환표(anonymization map)로 치환하고, 치환표를 plan에 기록하며, 치환 후 문자열을 '익명화된 원문'으로 취급한다(규칙 2-2의 문면 일치는 치환 후 기준). 누출 검사를 통과해야 한다. 인용 원문성과 익명화의 우선순위 충돌은 이 치환표 방식으로 해소(e2e-05 Luna 지적 반영). source_files 같은 비전송 메타데이터는 plan에만 남기고 state에 넣지 않는다.
5. **근거 원문은 인용 데이터로만.** state 내 적대적 텍스트에 취약함이 공식 명시. 비가역 동작의 마지막 관문으로 Jev 답 하나만 두지 않는다.
6. **wire JSON 스키마.** 질문은 정확히 `{"type": "choice|noul", "instructions": "...", "criteria": {...}}` 형태만 유효하다. choice criteria는 `{옵션키: 설명또는null}` map(배열 금지), noul criteria는 `{"true":..,"false":..}` 쌍만. 다른 필드명(prompt/choices 등)은 lint 거부 대상이다(e2e-05 표류 실측 반영).

## 3. 검증된 질문 세트 v0 (원장 검수용)
| key | type | 판정 | 실측 |
|---|---|---|---|
| new_fact_exists | noul | 근거에 기존 항목에 없는 새 사실이 있는가 (저장 여부 무관) | 4/5, 거부 사례에서 0.45~0.46 모호 신호 |
| record_state | choice | 새 사실이 최종 처리에 실제 기록됐는가 (recorded/not_recorded/no_new_fact/escape). **질문 instructions에 기록 대상을 반드시 명시한다: 정본(canonical)/임시원장/결과 보고서 중 하나.** 대상 미명시가 e2e-05 factD 불일치 원인 | 4/5+재검 1, 일치 시 0.9~1.0 |
| support | choice | 인용 근거가 주장을 직접 지지하는가 (supported/contradicted/insufficient/escape) | 주장-인용 일치 시 안정 |
| scope | choice | 처리 결과가 근거가 정당화하는 범위 대비 (preserved/expanded/narrowed/escape) | 서술형 narrative 전제, 처리 미확정 사례엔 재정의 필요 |
| hold | noul | 미확인 결론(저장/제품/하류)이 남아 있는가 — 존재 확인만 | 5/5 (0.84~0.93) |
| boundary | choice | 근거 기준 올바른 처리 방식 (add/update/retain 조합 + escape). **질문 instructions에 판단 단계를 반드시 명시한다: 작성 단계 제안 기준인지 최종 처리 결과 기준인지.** 단계 미명시가 e2e-05 boundary 불일치 원인 | 명확 사례 0.85~0.99 |

## 3b. 검증된 질문 세트 v0.2 (기록 필요성 판정용)
| key | type | 판정 | 실측 |
|---|---|---|---|
| is_new | noul | candidate_fact 가 제시된 기존 기록 발췌에 없는 새 내용인가 | record-need-06: 0.93/0.10/0.83 세 유형 정확 |
| is_supported | choice | 근거 인용이 후보 사실을 직접 지지하는가 (supported/contradicted/insufficient/escape) | 3/3, 인용 문면 한계 시 평평 신호 |
| durability | choice | durable_fact/transient_progress/explanation_only/escape — 지속 사실인가 진행 정보인가 재설명인가. **durable_fact 설명은 '이후 작업에서도 유효한 사실·결정·제약·정의/스펙(공식·키·스키마 포함)'** (§7 유지보수 루프 첫 적용 2026-09-24: C4 에서 키 정의 공식이 durable .29~.39 / explanation .31~.33 으로 반복 평평 — 정의/스펙 범주 부재가 원인. 이 개정으로 record-need v0.2→v0.2.1, intent v0.3→v0.3.1) | 3/3 (0.82~1.0), 핵심 축 |
| impact (v0.2.2, should_record 대체) | choice | 'candidate_fact 는 이후 작업의 결정이나 행동에 어떤 영향을 주는가?' — changes_decisions(이후 작업의 결정·설계·구현 방식을 바꾸거나 제약한다)/reference_only(참고는 되지만 결정이나 행동을 바꾸지 않는다)/no_future_use(이후 작업에 쓰이지 않는다)/none_or_uncertain | should-record-13 긍정 3/3·부정 3/3, impact-stability-14 긍정 5/5·오판 0·반복 흔들림 ≤0.07 |
| ~~should_record~~ (v0.2.1 까지) | noul | 제시 자료 기준 영구 기록 보존 가치 | 폐기(v0.2.2): 1질문 다조건, 긍정에서 반복 경계 0.55~0.70 |
- 입력 state 필수 키: narrative, candidate_fact, evidence_quote, existing_records_excerpt. 기존 기록 발췌의 검색 품질이 is_new 판정의 상한이다(검색은 코드/검색기 몸).
- 코드 결합 규칙(확정 2026-09-24, 우선순위 있음; 4항 v0.2.2 개정): 1) is_new가 확실한 no(비회부 구간) → duplicate_skip 이 다른 축 회부보다 우선. 2) durability가 확실한 transient_progress/explanation_only → no_record 가 경계 회부보다 우선. 3) 남은 회부 신호 → needs_review. 4) is_new>=0.5 ∧ durable_fact ∧ **impact=changes_decisions** 전부 비회부일 때만 record. impact 가 확실한 no_future_use → no_record. impact 가 확실한 reference_only → 처분은 acceptance_policy 가 정한다(정책 미정 동안 needs_review). 근거: record-need-06 12/12 + P1 durability 8/8, P2 러너 회귀 테스트, should-record-13·impact-stability-14.

**v0.2.2 채택 (사용자 승인 2026-09-24)**: should_record(noul)를 `impact`(choice)로 대체한다(위 표·결합 규칙 4). template_id record-need, template_version v0.2.2. 이유: should_record 는 1질문 다조건(새로움+지속성+가치)이고 긍정에서 반복 경계(0.55~0.70). 실측: should-record-13(V0 긍정 1/3, 반사실 noul 2/3, impact 3/3·부정 3/3), impact-stability-14(새 긍정 5/5, 부정 오판 0/5, 반복 3회 1위 동일·흔들림 ≤0.07, 캐시 아님). 알려진 약점과 완화(함께 채택): ① 맥락 없는 사소한 사실은 none_or_uncertain 회부 → 작업자 가이드 규칙 9 '결정에 쓰였는지를 사실로 적기'. ② 과장 서술이 changes_decisions 를 끌어올림(0.43) → 입력 규칙: narrative 에 평가형 표현('매우 중요', '핵심', '결정적', '사소한' 등 중요도 판단어) 금지, 러너 lint E_EVALUATIVE 로 거절. 미확정: reference_only 처분 정책((a) acceptance_policy). 증거: active evidence jev-should-record-13-*, jev-impact-stability-14-*.
- 결합 우선순위 검증 테스트 지침 (AP-P4-001 소화, 2026-09-24): 이 모듈의 escape/경계 회부 라우팅을 검증하는 테스트는 비중복 사례 기반으로 작성한다 — 확실한 중복 라우팅이 다른 축 회부보다 우선하므로 중복 사례에서는 회부 경로가 가려진다. 근거: P2 러너 X1 기반 escape 테스트 실패→D4 전환 8/8 green (소화 경로: 임시원장 L-P4-001 → 본 줄).

## 3c. 질문 세트 v0.3 (update/deprecate 검수) — C0 설계 2026-09-24
**공통 전제**: facts.operation 이 update/deprecate 인 항목은 state 에 `target_excerpt`(대상 조각 발췌, 치환표 익명화)가 필수다. 대상 참조 실존/ID 대조는 Jev 가 아니라 코드 lint(E_TARGET)가 검사한다. durability/scope/boundary/hold 는 v0/v0.2 정의 그대로 재사용.

**update 전용 (state: narrative, candidate_fact=정정 내용, target_excerpt, evidence_quote)**
| key | type | 판정 | 해석 주의 |
|---|---|---|---|
| differs_from_target | noul | candidate_fact 가 target_excerpt 의 내용과 실질적으로 다른 주장인가 (기대 yes; no 확실이면 정정 불필요=duplicate) | is_new 의 update 판 |
| correction_evidence | choice | evidence_quote 가 target_excerpt 내용이 더 이상 정확하지 않음을 직접 보여주는가 — refutes(반증함)/consistent(기존과 양립—정정 근거 아님)/insufficient/none_or_uncertain | **해석 반전: refutes(=모순)가 기대 증거다.** v0 의 contradicted 나쁬 신호와 부호 반대 |

**deprecate 전용 (state: narrative, deprecate_reason, target_excerpt, evidence_quote)**
| key | type | 판정 | 해석 주의 |
|---|---|---|---|
| invalidation_evidence | choice | evidence_quote 가 target_excerpt 지식이 더 이상 유효하지 않음을 직접 보여주는가 — invalidates/still_valid(여전히 유효—폐기 부당)/insufficient/none_or_uncertain | still_valid 확실 = 폐기 기각 신호 |
| replacement_exists | choice | 대체 지식 상황 — replacement_provided(대체 제시됨)/no_replacement_needed(대체 없이 폐기 정당)/missing_replacement(대체 필요한데 없음)/none_or_uncertain | missing_replacement = 회부 신호 |

**코드 결합 v0.3 (잠정, C1 실측 후 확정)**:
- update: differs>=0.5 ∧ correction_evidence=refutes ∧ 전축 비회부 → update 기록. differs 확실한 no → duplicate_skip(정정 불필요). consistent 확실 → needs_review(정정 근거 없음 — no_record 아님, 작성자 재확인). 경계/escape → needs_review.
- deprecate: invalidates ∧ replacement 축 비회부(missing 아님) → deprecate 기록. still_valid 확실 → needs_review(폐기 기각). missing_replacement 또는 경계 → needs_review.
- 기록된 update/deprecate 의 소화는 대상 조각 revision CAS 필수 + 소화 시 fresh 재검(이벤트 계약 §5).
- 실측 상태: **v0.3 은 설계만 완료, 미검증 (C1 대상)**.

## 4. 응답 해석 규칙
1. **분기는 label/enum으로.** confidence·확률은 라우팅 신호이지 정답 보증·권한이 아니다.
2. **평평한 분포(최상위 두 옵션 근접 또는 escape 선택) → 자동 진행 금지, 작성자 회부.** 실측 3회 일관 작동.
3. **전체 확률 분포·요청/응답 모델 버전을 로그.** rationale이 없으므로 분포가 유일한 진단 수단. 프로덕션은 버전 고정(`jev-1.13.0` 형태).
4. **Jev 답은 저장·acceptance 권한을 만들지 않는다.** whole-batch 원자성, 별도 acceptance 경계는 기존 계약 그대로.
5. **근거 부족/API 실패 ≠ no-record.** 보류 상태로 작성 모델 보충 회부.

## 미확정 (이 규약이 정하지 않는 것)
- 이벤트 트리거 계약(judgement 완결 시점 정의, 중복 호출 키), 상호 보강 루프의 자동화, 처리 미확정 사례의 scope 재정의, threshold 수치. 모두 후속 결정.
- e2e-05에서 드러난 공백 4개는 본문에 반영 완료(2026-09-24): wire 스키마 → 입력 규칙 6, 익명화 치환표 → 입력 규칙 4, record_state 대상 명시·boundary 단계 명시 → 질문 세트 v0 표. 반영 후 재검증은 미수행(다음 반복 후보).

## Implementation map
- 실측 근거: `lazy-harness(active root)/.lazy-harness/evidence/jev-offline-replay-02-{plan,result}.json`, `jev-offline-replay-03-{plan,result}.json`, `jev-offline-replay-03-case2-repair-{plan,result}.json`, `jev-offline-replay-04-fanout-{plan,result}.json`, `jev-e2e-05-{packet.draft,plan,result}.json`, `jev-ledger-review-01-{plan,result}.json`
- 빌드/정규화 스크립트: `lazy-harness(active root)/.lazy-harness/state/jev-replay02-finalize.py`, `jev-replay03-build.py`, `jev-e2e05-finalize.py`
- 호출 경로: Pi `jev_evaluate` (pi-jev 0.5.0, OpenRouter transport, `TYPESAFE_BASE_URL`)
- 공식 근거: jevtypesafeai.com/docs, learnjev.com failure-modes·three-primitives, agent 통합 가이드
- 관련 primary: `.lazy-harness/planning/v2-vision-feasibility-research.md` (replay 캡슐)
