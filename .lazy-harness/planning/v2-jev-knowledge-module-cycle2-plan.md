# Planning — 지식 관리 모듈 2차 사이클 계획 (update/deprecate + 구조 검증)

## Rule digest
- Status: completed — C0~C5 전 단계 exit 충족 (2026-09-24). 평가는 v2-jev-knowledge-module-p5-evaluation.md 에 병합
- Layer: Planning
- Scope: 의도 체계(add/update/deprecate) 완성과 1차에서 미검증으로 남은 구조 조항 4개의 검증 사이클(C0~C5)
- Applies when: 2차 사이클의 단계 시작/진행/exit 판단 시
- Must: 각 단계 exit 통과 후 다음 단계, 단계 시작은 사용자 승인, 정본 자동 반영·acceptance 자동화 금지 유지, gold 는 호출 전 고정·소급 수정 금지

## 역할 (1차 확정 그대로)
- 설계 = Parent · 제작(구현) = gpt-6-sol:medium 위임 · 모듈 런타임 = Luna+Jev만 · 결합/권한 = 코드 · 검증 = 사용자+Parent

## 입력 (1차 사이클 산출)
- 검증 완료: add 경로 전체(규약 8규칙, v0/v0.2 온톨로지, 결합 우선순위, 러너, 회부 루프, 소화 제안서)
- 미검증 구조 조항 4: ① 즉시 proposed 등록 ② Luna 마이크로배치 ③ fresh 정본 재검·revision 감지 ④ unit 내 일관성
- 신규 설계 필요: update/deprecate 검수(v0.3), 스키마 델타

## 단계

### C0. v0.3 온톨로지 설계 (설계=Parent, 문서만)
- 내용: update용 — `differs_from_target`(기존과 다른가, is_new 대체), `correction_evidence`(새 근거가 기존 내용을 반증하는가 — contradicted가 기대 증거임을 질문에 명시), 공통 durability/scope/boundary 재사용. deprecate용 — `invalidation_evidence`(대상이 더 이상 유효하지 않다는 근거), `replacement_exists`(대체 지식 유무, escape 포함). 대상 참조 실존 검증은 코드 lint(E_TARGET 신설 후보). 규약 3c절로 추가.
- exit: 규약에 v0.3 질문 세트가 wire 스키마로 명시되고 의도별 해석 반전이 문서화됨.
- 예산: 없음 (문서).

### C1. v0.3 오프라인 검증
- 내용: 실제 정정/폐기 사례 4~6건으로 gold 고정 후 Jev 검증. 소재 후보(실제 발생분): 이 세션 Fable 경위 정정(사용자 정정 사례), replay-02→03 gold 재정의(기준 변경 사례), 폐기 후보는 v2 연구에서 superseded 된 과거 결론(deprecated 계열 record)에서 익명화 발췌. 대조군으로 add 사례 1건 포함(의도 오분류 검사). 패킷 생성 Luna 1 run(배치 — 조항 ② 간접 검증 겸용).
- exit: 의도별 해석(특히 update의 contradicted=기대)이 작동하는지 확인, 불일치 전건 원인 분류 가능. add 때와 동일한 결함→수정 1회 반복 허용.
- 예산: Luna 1 run + Jev 5~7회.

### C2. 스키마 델타 SDD (설계=Parent, 문서만)
- 내용: ledger_entry(= judgement 본문 내장 + 상태 봉투) / work_unit(+CompletionSource 등록) / 검수 영수증(분포·모델버전·dedup) / partition_key. 기존 fragment 16필드·CAS·history 계약과의 접합점(absorbed→조각 쓰기, update/deprecate→대상 revision CAS, deprecate→비활성화+history) 명시. fragment store 초안(needs-review)과 동시 검토 대상.
- exit: 사용자 검토 통과한 SDD 1건. DB 생성 없음.
- 예산: 없음.

### C3. 러너 확장 구현 (제작=Sol 위임)
- 내용: 파일 기반 유지(실 PG는 이번 사이클 범위 밖 — 새 컨테이너 승인 별도). 확장: (a) 즉시 proposed 등록(조항 ①) (b) 마이크로배치 창(조항 ②, N건/T초) (c) fresh 재검 훅 — 대상 revision 스탬프 비교, 변경 시 재검 강제(조항 ③) (d) unit 다항목 일관성 검사 자리(조항 ④) (e) facts operation(add/update/deprecate) 지원 + E_TARGET lint (f) deprecate 비활성화+history 파일 시뮬레이션. 기존 테스트 8건 유지 + 신규 회귀.
- exit: 전체 테스트 green, 조항 ①~④와 의도 체계가 코드로 검증 가능 상태.
- 예산: Sol 1~2 run + Jev 0~2회(재실행 fixture).

### C4. 재파일럿 P4′ — 다항목·정본 변경 시나리오
- 내용: 실제 작은 work unit 1건에서 add+update+deprecate 혼합 facts 3~4건을 쭈욱 적고 전 구간 실행. 중간에 대상 조각(파일 시뮬레이션) revision 을 의도적으로 변경해 fresh 재검 강제 경로를 실측. unit 내 일관성 검사 포함. 사람 게이트는 정본 반영 승인 1곳만(완료 신호는 자동 어댑터).
- exit: 조항 ①~④ + 의도 3종 + 정본 변경 시나리오가 한 파일럿에서 관측됨. 전 이력 원장 보존.
- 예산: Luna 1~2 run(+resume) + Jev 3~6회.

### C5. 사이클 평가
- 내용: 1차 평가 문서에 2차 결과 병합, 의도 체계 포함 전체 검증 지도 갱신, threshold/비용 관측치 축적. 이후 남는 것(스키마 실 DB화, pi-fabric 조사) 재확인.
- exit: 갱신된 평가 문서. 채택 확대 여부는 사용자 결정.

## 안전 (1차 그대로 + 추가)
- gold 호출 전 고정·원본 실패 보존·치환표 익명화·누출 검사. 정본 자동 반영 금지.
- deprecate 시뮬레이션 포함 어떤 단계도 실제 canonical record 를 비활성화하지 않는다(파일 fixture 만).
- Trial57 STOP·보호 holds·기존 장부 불변. 실 PG 컨테이너 신설은 이 계획 밖(별도 승인).

## 미확정
- v0.3 질문 문구(C0 산출), 배치 창 수치(N/T), E_TARGET 검증 범위, 실 DB 적용 시점.

## Implementation map
- 1차 계획/평가: `v2-jev-knowledge-module-testplan.md`(completed), `v2-jev-knowledge-module-p5-evaluation.md`
- 계약: `.lazy-harness/spec/v2-jev-question-template-contract.md`, `.lazy-harness/spec/v2-knowledge-module-event-contract.md`
- 러너: `experiments/v2-knowledge-module-runner-01/`
- 증거 수렴처: active root `.lazy-harness/evidence/jev-*`
