# SDD — 지식 관리 모듈 이벤트·완료 추적 계약 (draft)

## Rule digest
- Status: needs-review
- Status note: draft — 사용자 검토 대기 (P3 산출물)
- Layer: SDD
- Scope: layer-fact
- Covers: judgement 완결 이벤트, 검수 호출 중복 방지, 임시원장 상태 머신, git 비의존 완료 추적, 소화자 기동 시점의 계약
- Aliases:
  - 지식 모듈 이벤트 계약
  - 완료 추적
  - 임시원장 상태 머신
- Applies when: 모듈이 judgement 를 받아 Jev 검수를 호출하거나, 임시원장 항목의 상태를 바꾸거나, 완료 신호를 등록/수신하거나, 소화자를 기동할 때
- Must: 검수는 구조화된 judgement 이벤트로만 트리거하고, 중복 키로 같은 판정의 재호출을 막고, 완료 신호 전의 원장 항목은 임시로 유지하며, 정본 반영은 acceptance 경계 뒤에 둔다
- Must not: 원시 사용자 문장을 코드가 분류해 트리거하거나, Jev 답으로 저장/acceptance 권한을 부여하거나, API 실패를 no-record 로 바꾸지 않는다

## 1. Judgement 완결 이벤트
- **발생원**: 작업자가 구조화된 judgement 를 등록/갱신하는 순간 (v1의 record-judgement envelope 가 원형). 자연어 대화 감시 아님.
- **이벤트 필드**: `judgement_id`, `version`(갱신마다 증가), `work_unit_id`, `disposition_candidate`, `facts[]`(후보 사실+근거 참조), `evidence_refs[]`, `emitted_at`.
- **judgement = 임시원장 항목의 본문이다 (사용자 확인 2026-09-24).** 작업자가 judgement 를 내는 순간 그 내용 그대로 원장에 proposed 로 즉시 앉는다(변환·복사 없음, 세션 사망에도 보존). 원장 행 = judgement 본문 + 상태 봉투(state 머신/검수 영수증/dedup 키, 코드 소유). 검수는 뒤따라오는 것이지 기록 생성의 전제가 아니다.
- **트리거·배치 정책**: 원장 등록은 즉시. Luna 변환+Jev 검수는 마이크로배치(work unit 단위 또는 N건/T초 창) — Luna 호출의 고정 프롬프트 오버헤드를 여러 judgement 에 분할상환(사용자 확인 2026-09-24). Jev 는 한 호출 다질문이라 묶음/개별 비용 차이 미미. 배치 창은 짧게 유지 — 회부가 작업자 맥락이 살아있을 때 도착해야 한다. 같은 judgement 의 갱신은 새 version 으로 재검수.
- **지식 본문의 1차 작성자는 작업자다.** 후보 사실·이유·근거 참조는 judgement 의 facts[] 에 작업자가 직접 적는다(맥락 재발견 금지 원칙). 작성 모델(Luna)은 내용 창작자가 아니라 변환기다 — 서술 정리, 사실별 fan-out 분해, 인용 발췌 문면 정리, 치환표 익명화, wire 질문 조립만 한다. facts 에 없는 사실을 패킷에 만들어 넣지 않는다 (사용자 확인 2026-09-24).
- **facts[] 항목의 의도(operation) (사용자 확인 2026-09-24)**: 각 fact 는 `add`(새 사실) / `update`(알던 것과 다름 — 대상 조각 참조 + 무엇이 어떻게 다른지) / `deprecate`(더 이상 유효 안 함 — 대상 참조 + 이유) 중 하나를 가진다. 작업자는 새 지식뿐 아니라 정정·폐기 발견도 그 자리에서 적는다(ADR 0032 사용자 정정 수렴의 자동화 경로).
  - 검수 해석은 의도별로 다르다: update fact 에서는 대상 조각과의 contradicted 가 오답 신호가 아니라 정정의 기대 증거다(템플릿에 의도 명시 필요). boundary 축(add/update/retain 조합, P1 CASE-3 실측)과 기존 원장 계약(retains/updates/adds)이 이 의도 체계의 검증된 받침이다.
  - deprecate 는 물리 삭제가 아니다 — 조각 저장소 규칙(“삭제로 기록을 지우지 않는다”) 그대로 비활성화+history 보존으로 소화된다. update/deprecate 의 소화는 대상 조각 revision CAS 를 거친다.

## 2. 중복 호출 방지 키
- `dedup_key = hash(judgement_id, version, fact_index, fact_evidence_digest, template_id, template_version, jev_model_version, stage, packet_digest)` — fact 단위·검수 단계(worktime/digestion)별 영수증. (C3 구현 중 발견된 충돌 수정 2026-09-24, 스키마 델타 §3 과 일치) packet_digest = hash(packet.state, packet.questions): 보충은 judgement 는 그대로 두고 패킷만 바꾸므로 패킷 내용이 키에 없으면 고친 패킷이 옛 회부 캐시에 걸린다 (C4 파일럿 발견 2026-09-24).
- 같은 키의 결과는 캐시 재사용. 구성요소 하나라도 바뀌면(근거 추가, 템플릿 개정, 모델 버전 변경) 새 호출.
- **stale 방지**: 결과 적용 직전 judgement version 재확인. 불일치 시 결과 폐기하고 새 version 으로 재검수.

## 3. 임시원장 항목 상태 머신
```text
proposed ──(lint fail)──▶ rejected_input (작성자 회부)
proposed ──(Jev+코드결합)──▶ checked{record} ──▶ provisional
                        ├─▶ checked{no_record|duplicate_skip} ──▶ closed
                        └─▶ checked{needs_review} ──▶ review_queue (작성자 보충 → proposed 재진입, 보충 상한 2회)
provisional ──(work unit 완료)──▶ eligible
provisional ──(work unit 폐기)──▶ expired
eligible ──(소화자 자격 판정 + acceptance)──▶ absorbed
eligible ──(자격 미달)──▶ retained_as_evidence (임시 증거로 보존, 정본 미반영)
```
- 상태 전이는 append-only 로 기록. 임시(provisional)는 미흡수 상태이지 사실의 잠정성이 아니다.
- API 실패/근거 부족은 `review_queue` 또는 재시도이며 절대 no_record 로 변환하지 않는다.

## 4. 완료 추적 추상화 (git 비의존)
- `CompletionSource` 인터페이스: work_unit_id 에 대해 완료 신호를 발행하는 등록형 어댑터.
  - 구현 예: `git_merge`(PR 머지 감지), `user_confirm`(사용자 확정), `acceptance_pass`(acceptance 통과), `external_event`(배포 등).
- work unit 상태: `active → completed | abandoned`. 신호는 어댑터가 발행하고 모듈은 수신만 한다(폴링/웹훅 무관).
- 한 work unit 에 복수 신호원이 등록되면 **모두 충족(AND)** 이 기본, 예외는 unit 생성 시 명시.
- PR 이 올라가도 머지 전이면 active 유지 — 신호 수신 전 어떤 provisional 도 eligible 이 되지 않는다.

### 4.1 브랜치 기준 완료 추적 — 기계적 감시 (사용자 설계 확정 2026-09-28, 구현 전)

경위(사용자): '메인 브랜치에 머지되는걸 기준으로 지식 확정을 해야겠는데?', '버려지는 브랜치가 있거나 할수도 있잔아', "
'동적으로 세션을 켰을때 작업하는 워크트리나 브랜치를 감지해서 감시에 붙혀버리는거야 감시자는 한명이고 여러 감시를 하는거지',
'중간에 세션에 꺼질수도 있으니까 … 훅을 사용해도 되겠다', 'jev 필요 없으려나?? hook 으로 하면', '기계적으로 할수 있을것같은데'.

1. **등록(훅)**: pi 확장 session_start(세션 시작·재연결) 때 워크트리·브랜치·HEAD 를 읽어 DB 감시 목록에 등록. git 이 아니거나 detached 면 등록하지 않음.
2. **연결 규칙(브랜치 하나 = 열린 작업 단위 하나)**: 같은 브랜치에 열린 작업 단위가 있으면 무조건 이어 씀(세션이 꺼져도 같은 브랜치의 새 세션이 이어 붙음), 없으면 첫 기록 때 만들고 브랜치에 연결. 기록마다 브랜치·마지막 커밋 갱신. 판단 모델(Jev) 쓰지 않음 — 규칙으로 애매한 경우를 없앰.
3. **감시자 하나**: 상주 폴러가 몇 분마다 감시 목록 전체 확인 — 프로젝트의 확정 브랜치에 들어감(git fetch 후 조상 관계, 스쿼시·리베이스는 gh PR merged) → git_merge 신호로 확정·소화 / PR 이 머지 없이 닫힘·브랜치 삭제 → abandoned(원장 보관, 정본 미반영, 알림, 필요한 항목만 사용자 확정으로 살림) / 오래 무활동 → '확인 필요' 표시만(예: 30일). 끝난 브랜치는 목록에서 빠짐.
4. **확정 브랜치에서 직접 작업**: 기계적 방식 — 커밋이 원격에 푸시되면 확정(사용자 '기계적으로' 를 푸시 확정으로 해석, 다르면 정정).
5. **git 이 없거나 커밋이 없는 작업**: user_confirm(사용자 확정 발언) 유지 — §4 git 비의존 원칙.
6. **프로젝트별 확정 브랜치** 설정(기본 main; 다단계 브랜치를 쓰는 프로젝트는 별도 지정).
조건: 감시자가 도는 컴퓨터에 저장소와 git fetch·gh 인증. 순서: G7(현재 user_confirm 방식) 먼저, 그다음 구현(임시 git 저장소로 일반 머지·스쿼시·버려짐·재연결 테스트).

## 5. 소화자 기동
- 트리거: work unit `completed` 이벤트 1회. (주기 스캔은 보조, 기본은 이벤트.)
  - **개정 (사용자 확정 2026-09-25): 기본은 DB 폴링이다.** 완료 신호 = DB 기록(`signal_completion` 이 work_unit.completion_sources·status 를 갱신). 소화자는 LLM 액터가 아니라 **일반 코드가 DB 에서 '완료됐고 아직 소화 안 된' work unit 을 주기적으로 찾아** `run_digestion` 을 실행한다(systemd 사용자 서비스/타이머, lh-embed 와 같은 운영 방식). 이유: 소화에는 LLM 판단이 필요 없고(Jev 는 HTTP), 폴링마다 LLM 을 부르면 비용이 계속 들며, DB 가 진실이면 신호 유실이 없고 신호를 누가 보내든(pi 세션·향후 PR 머지 감지) 들어오는 곳이 하나다. mesh 토픽 + LLM 액터 방식(실측 01)은 대안으로 보존. 이 줄 위의 '기본은 이벤트' 문구는 이력.
  - **중단 안전 요구 (사용자 2026-09-25):** 작업 도중 컴퓨터가 꺼지거나 일시 중지돼도 정본이 반쯤 쓰이거나 중복 흡수되면 안 되고, 재기동 후 이어서 처리돼야 한다. 다음 기동 때 **멈췄던 작업부터 먼저** 처리하고, 쌓여 있던 대기 항목(proposed·완료됐지만 미소화 unit·임베딩 미생성 조각)은 **하나도 유실되지 않아야** 한다. 설계 원칙: 큐 = DB 상태 자체(별도 메모리 큐 없음) → 꺼져도 유실 없음. 각 단계는 한 트랜잭션으로 쓰거나 아무것도 안 쓴다(부분 쓰기 없음), 다시 실행해도 결과가 같다(멱등).
- 절차: 해당 unit 의 provisional 전건 로드 → 자격 판정 템플릿(원장 검수 v0 + 필요 시 v0.2) Jev 호출 → 코드 결합 → absorption 제안서 생성.
- **소화 검수의 구성 (사용자 질의로 확정 2026-09-24)**: 충돌 탐지의 본진은 소화 단계다. (a) **fresh 정본 재검** — 작업 중 검수의 신규성/충돌 판정은 그 시점 발췌 기준이라 stale 가능. 소화 직전 현재 정본 스냅샷 대비 중복(is_new)·모순(contradicted) 재판정을 필수로 한다. 관련 조각 revision 이 작업 중 검수 이후 변했으면 재검 생략 불가. (b) **항목 간 일관성** — 같은 work unit 의 eligible 항목들끼리 모순 여부를 같이 검사(완료 후에만 가능). (c) **물리/의미 분담** — revision CAS 는 코드(동시 수정 충돌), 내용 모순은 Jev(contradicted 검사). 작업 중 검수의 충돌 신호는 조기 경보일 뿐 소화 검사를 대체하지 않는다.
- **정본 쓰기는 제안서까지.** 실제 반영은 acceptance 경계(별도 권한) 뒤. Jev 답·confidence 는 권한이 아니다.
- 소화 결과도 원장에 append: absorbed 항목은 L-ref → 정본 참조 대응을 남긴다 (Trial48 유형 누락 방지 — J→L 대응표 원칙).

## 6. 실패·재시도
- Jev API 실패: 지수 백오프 재시도(상한 3), 최종 실패 시 항목 `review_queue` + 실패 영수증 보존.
- lint 실패: 호출 없이 `rejected_input` — 작성자에게 오류 코드(E_SCHEMA/E_CLAIM_QUOTE 등)와 함께 회부.
- 회부 보충 상한 2회 초과 시 사람에게 에스컬레이션 (무한 루프 차단).

## 7. 템플릿 유지보수 루프 (사용자 질의로 명시 2026-09-24)
- 질문 템플릿의 결함(문구 모호, 축 부적합)은 나중에 잡아 고칠 수 있는 대상이며, 이를 위한 기반은 이미 계약에 있다: dedup 키의 template_version(개정 시 자동 재검수 경로), 전체 확률 분포 로그(질문별 회부율/평평 빈도 = 템플릿 건강 지표), 회부 큐(결함 표본 창고), evidence 보존+gold 소급 금지(개정 전후 비교 재검).
- **개선 루프**: 운영 통계에서 질문별 회부/평평 빈도가 높으면 개정 후보로 식별 → 개정안 검토 → template_version 증가 → 영향 judgement 재검수. 개정 전 결과는 원상 보존.
- **self-hosting 원칙**: 템플릿 결함 발견은 그 자체가 durable fact 다 — 모듈 자신의 파이프라인에 update fact 로 넣어 원장→소화로 규약에 반영한다(P4 테스트 지침 소화가 첫 사례). 현재 대기 개정 후보 2건(differs 문구 정교화, deprecate 용 hold 대체)이 이 루프의 첫 입력이 된다.

## 미확정
- threshold 수치(0.15/0.35~0.65 잠정, P5 실측 후 확정), 복수 신호원 AND/OR 정책의 세분화, absorption 제안서 포맷, pi-fabric 이벤트 연동 방식(미조사).
- 2026-09-24 문답으로 확정됐으나 아직 미검증인 구조 조항 4개(다음 파일럿/구현에서 검증): ① judgement 즉시 proposed 등록(검수 선행 아님) ② Luna 마이크로배치 분할상환(P1 한 run 8사례는 간접 근거) ③ 소화 시 fresh 정본 재검·revision 변경 시 재검 강제 ④ unit 내 항목 간 일관성 검사(P4는 1건이라 미성립).

## Implementation map
- 결합·lint 구현: `experiments/v2-knowledge-module-runner-01/runner.py` (P2, Sol 구현)
- 질문·해석 계약: `.lazy-harness/spec/v2-jev-question-template-contract.md`
- 상태 저장 정본: 기존 PostgreSQL 계약(fragment/relation/원장 namespace) 재사용 — whole-batch 원자성 유지
- 시험 계획: `.lazy-harness/planning/v2-jev-knowledge-module-testplan.md` (P3 산출물이 본 문서)
- 실측 근거: active root `.lazy-harness/evidence/jev-*-result.json` 시리즈