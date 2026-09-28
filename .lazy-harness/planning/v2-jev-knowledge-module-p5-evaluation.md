# Planning — 지식 관리 모듈 P5 평가·채택 자료 (2026-09-24)

## Rule digest
- Status: active — 1차(P0~P4)·2차(C0~C4) 사이클 완주에 대한 평가 요약 (채택 결정 자료). 2차 병합 = C5 (2026-09-24)
- Layer: Planning
- Scope: Jev 기반 지식 관리 모듈 시험 1차(add 경로)·2차(update/deprecate 의도 + 구조 조항)의 결과 종합, 검증/미검증 경계, 채택 판단 자료
- Applies when: 모듈 채택 여부를 판단하거나, pi-fabric 반영을 준비하거나, 후속 실험 범위를 정할 때
- Must: 검증된 범위와 미검증 범위를 구분해 인용하고, 일반 신뢰성 주장으로 확대하지 않는다

## 단계별 결과
| 단계 | 결과 | exit |
|---|---|---|
| P0 규약 마감 | v0.2 정식 편입 + 개정 질문 재검 2/2 (factD 0.78, boundary 0.97) | ✅ |
| P1 확대 검증 | 타 프로젝트 unseen 8사례 25/30, durability 8/8, 중복 검출 0.08/0.11 | ✅ |
| P2 미니 러너 | lint 6종+decide+call 구현, 테스트 8/8 green, 결합 우선순위 확정 | ✅ |
| P3 이벤트 계약 | SDD draft (이벤트/중복 키/상태 머신/CompletionSource/소화자/실패 처리) | ✅ |
| P4 파일럿 | 실제 judgement 1건 전 구간 완주 → absorbed + L→정본 대응 | ✅ |

### 2차 사이클 (update/deprecate + 구조 조항)
| 단계 | 결과 | exit |
|---|---|---|
| C0 v0.3 온톨로지 | 규약 3c절: update(differs/correction_evidence, refutes=기대 해석 반전) + deprecate(invalidation/replacement) | ✅ |
| C1 v0.3 검증 | 실제 정정·폐기 5사례 14/16 — 정정 refutes 0.88/0.62, 양립 검출 consistent 0.94, deprecate invalidates 1.0×2 | ✅ |
| C2 스키마 델타 | work_unit/ledger_entry(judgement 내장)/check_receipt/absorption + 이벤트 append-only, fragment 계약 무변경 | ✅ (draft) |
| C3 러너 확장 | register/batch/complete/digest/stats + 의도 3종 + E_TARGET + deprecate 비활성화 + update CAS (Sol) | ✅ |
| C4 재파일럿 | judgement 1건(add/update/deprecate) v1→v3 전 구간 → 외부 조각 변경 시 needs_recheck·흡수 거부 → fresh 재검 후 absorbed 3건. 설계 결함 5개 발견·수정, 23/23 | ✅ |

## 사전 실험 포함 누적 (이 세션)
- Jev 호출 약 30회 (연결 1, ledger-review-01, replay-02/03/case2R/04, record-need-06, e2e-05, p0-retest-07, p1-expand-08, p4-pilot-09×3). 전부 소액(입력 토큰 과금), 정확 비용은 도구 미보고로 미실측.
- 실험별 기대 일치: replay-02 18/25 → 규약 수정 후 replay-03 24/30 → case2 수리 4/6, fan-out 3/4, record-need 12/12, e2e-05 12/14, p0 2/2, p1 25/30.
- 고신뢰(>=0.85) 답: replay-02/03 합산 28중 27 일치, e2e-05 16/16, 이후 실험에서 고신뢰 불일치 관찰 없음 (상관 표본, 통계 아님).
- 불일치의 주 원인은 일관되게 입력/온톨로지 결함이었고, 평평한 분포가 그 지점을 신호 (4회 독립 재현: replay-02 C, CASE-2 인용, P1 치환, P4 scope).
- 2차 추가: C1 Jev 5회 + C4 Jev 15회·Luna 6 run(소액). 불일치·회부 원인은 이번에도 입력 쪽 — 특히 **작업자 judgement 의 근거 누락**을 Jev 가 scope expanded/should_record 경계로 문면 그대로 검출(C4). 입력 결함 감지 누적 5회+(C1 D1 hold 0.49 포함).

## 검증된 것
1. **질문 규약**: 8개 작성 규칙 전부 실측 근거 보유. 결함→수정→개선의 인과 3회 재현.
2. **온톨로지 2종**: 원장 검수 v0 + 기록 필요성 v0.2 (durability 축 누적 11/11).
3. **결합·회부**: 고신뢰 자동 진행 / 평평·경계 회부, 우선순위(중복>transient>회부>record) — 러너 코드로 구현·회귀 테스트.
4. **회부 루프**: lint 거부→수정(P4), 경계→보충→통과(P4), 입력 수리→재검 개선(case2R) — 사람 개입 없이 작동.
5. **저가 조합**: Luna(패킷)+Jev(판정)+코드(결합·권한) 사이클이 unseen 사례(e2e-05)와 실전 judgement(P4)에서 동작.
6. **소화 단계**: 완료 신호→자격 판정→보수 제안서(과일반화 감지·한정 완화)→absorbed+L→정본 대응.
7. **안전 경계 유지**: 정본 자동 반영 없음, Jev 답≠권한, 원본 실패 보존, whole-batch/acceptance 계약 불변.
8. **의도 3종 (2차)**: add/update/deprecate 검수가 모두 작동. update 에서는 모순(refutes)이 기대 증거로 해석 반전됨(C1·C4), 양립 보강을 update 로 낸 오용은 consistent 로 검출. deprecate 는 물리 삭제 없이 비활성화+history.
9. **구조 조항 (2차 C4 실측)**: ① judgement 즉시 proposed 등록, ② 마이크로배치, ③ **정본 변경 시 fresh 재검 강제**(해당 영수증만 지목, 재검 전 흡수 거부) — 실측. ④ unit 일관성은 코드 경로만(충돌 사례는 단위 테스트).
10. **회부 재진입·상한**: resubmit(review_queue→proposed, 2회 초과 에스컬레이션), packet_digest 로 보충 패킷의 캐시 오염 방지.
11. **§7 유지보수 루프 첫 적용**: durability 정의/스펙 범주 부재를 분포(0.29~0.39 평평)로 발견 → 개정(v0.2.1/v0.3.1) → 0.68~0.98 회복. 템플릿 결함을 운영 신호로 고치는 루프가 실제로 돌아감.

## 미검증 / 남은 것
- 일반 신뢰성: 모든 표본이 상관·소규모. 운영 누적 통계 필요.
- threshold 수치(0.15 근접, noul 0.35~0.65)는 잠정 — 운영 데이터로 보정.
- 비용/지연 실측 부재 (공식 단가 기반 추정만: 판정 1회 0.01센트 단위).
- 적대적 입력(주입) 내성 미테스트 — 공식 명시 약점, 운영 전 별도 프로브 필요.
- 이벤트 계약 SDD·질문 규약은 draft — 사용자 최종 검토로 active 승격 필요.
- pi-fabric 미조사 — 실제 반영 경로 확정이나 패키지/계약/통합 방식 미확인.
- 완료 트래킹 어댑터(CompletionSource) 실구현 없음 — P4/C4 모두 명시적 complete 호출로 대체.
- (2차 추가) **add 의 조각 생성 계약 미정** — C4 에서 add 는 absorbed 되었으나 fragment_ref=null. 16필드 조각 생성 규칙 필요.
- (2차 추가) **acceptance_policy 미정** — --apply 는 명시적 승인 시뮬레이션. 자동 반영 트리거의 정책 언어 필요.
- (2차 추가) **파일 CAS ≠ 실 DB CAS** — 동시성 보장 없음. 파티션 액터 동시 소화 전 실 DB 이행 필수.
- (2차 추가) unit 내 **의미** 모순 검사(Jev 질문) 미설계, fresh 재검 패킷에 넣을 현재 발췌 범위 미정, 캐시 재사용 미관측, stats 분모 정책.
- (2차 추가) v0.3 개정 후보 2건(differs 문구 정교화, deprecate 용 hold 대체) 미반영.

## 채택 판단 자료 (Parent 의견, 결정은 사용자)
- **채택 권고 범위**: 규약(3/3b/3c)+온톨로지 3종(v0/v0.2.1/v0.3.1)+러너 결합 규칙(scope 가드 포함)+이벤트 계약의 상태 머신·fresh 재검·회부 재진입은 모듈 내부 계약으로 채택 가능 수준. 스키마 델타는 draft 검토 후 active.
- **채택 보류 범위**: 정본 자동 반영·acceptance 자동화는 acceptance_policy·add 조각 생성 계약·실 DB CAS·운영 통계·주입 내성 확인 전까지 보류 권고.
- **2차가 바꾼 우선순위**: 병목은 판정(Jev)이 아니라 **작업자 judgement 의 근거 품질**. 작업자가 인용을 제대로 붙이게 하는 가이드/템플릿이 회부율을 가장 크게 줄일 후보.
- **다음 마일스톤 후보**: (a) add 조각 생성 계약 + acceptance_policy 설계, (b) 실 DB(PostgreSQL) 이행과 진짜 CAS, (c) pi-fabric 조사·통합, (d) 작업자 judgement 작성 가이드, (e) 주입 내성 프로브, (f) 운영 파일럿 통계.

## Implementation map
- 계획: `.lazy-harness/planning/v2-jev-knowledge-module-testplan.md` (P0~P4 exit 전부 충족), `.lazy-harness/planning/v2-jev-knowledge-module-cycle2-plan.md` (C0~C5 완료)
- 규약: `.lazy-harness/spec/v2-jev-question-template-contract.md` / 이벤트: `.lazy-harness/spec/v2-knowledge-module-event-contract.md` / 스키마: `.lazy-harness/spec/v2-knowledge-module-schema-delta.md`
- 러너: `experiments/v2-knowledge-module-runner-01/`
- 증거: active root `.lazy-harness/evidence/jev-*-{plan,result,ledger,absorption-proposal}*.json` 전체
- 경위: `.lazy-harness/planning/v2-vision-feasibility-research.md` 2026-09-24 캡슐들
