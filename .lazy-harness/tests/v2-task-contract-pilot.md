# 첫 연구 결과 — 태스크 하나로 진행과 기록을 함께 남기기

## Rule digest
- Status: advisory
- Layer: TDD
- Scope: host-project
- Aliases:
  - 업무 객체 첫 실험
  - 태스크 기록 계약 파일럿
- Applies when: 첫 업무 객체 고정 입력 실험의 결과를 해석하거나 후속 실제 모델 시험을 준비할 때.
- Must: 후보 계약의 기계적 동작과 실제 작업자 준수·증거 진위·토큰 절감 효과를 구별한다. 실제 모델·DB·훅 시험으로 과장하지 않는다.

## 1. 무엇을 했나?

사용자는 ‘태스크 하나, 정상 완료·검증 실패·요구 변경’부터 진행하고 결과를 보고하도록 승인했다. 이에 **Python 표준 라이브러리만 사용하는 작은 고정 입력 실험**을 만들었다. 기존 샌드박스·실제 서비스 코드는 수정하지 않았다.

1. 최소 태스크와 5개 이벤트 종류를 후보 계약으로 작성했다.
2. 세 상황의 입력과 각 단계 기대 상태를 먼저 fixture에 명시했다.
3. 이벤트를 처리하는 코드에는 기대 정답을 주지 않고 실행했다.
4. 18개 상태 확인 지점과 12개 단위 테스트를 검사했다.
5. 정상 동작뿐 아니라 ‘가짜 검증 영수증을 믿는가’라는 한계 탐색도 수행했다.

**모델 호출 0, 네트워크 호출 0, DB 생성 0.** Sol이 코드를 고치거나 Luna가 소화한 실험은 아니다. 실제 코드 변경/테스트 결과를 흉내 낸 영수증을 사용했다.

## 2. 후보 최소 조각

| 조각 | 이번 표현 | 목적 |
|---|---|---|
| 태스크 | task_id, goal, criteria | 무엇을 하고 무엇이면 끝나는가 |
| 현재 상태 | status | planned / working / blocked / done |
| 계획 버전 | plan_version | 완료 조건 변경 전후를 구별 |
| 작업 결과 버전 | revision | 검증이 어떤 결과에 대한 것인지 연결 |
| 검증 근거 | receipt_id, result, criteria, plan_version, revision | 현재 조건·작업 버전의 검증 여부 |
| 진행 이벤트 | id, task_id, kind, 필요한 payload | 상태 변경과 이력을 한 번의 제출로 연결 |

종류는 start / change / verify / complete / revise_plan이다. reason은 실패·계획 변경에 요구했다. 단순 정상 진행에서 목적을 매번 다시 쓰지는 않았다.

**업무 객체 전체나 제품 스키마를 확정한 것이 아니다.** 여기에는 실제 작업 영역·기준 snapshot·권한·PRD·여러 태스크 의존성·취소·배포·소화가 아직 없다. revision은 고정 문자열이며 실제 Git hash나 도구 receipt가 아니다. 조건 목록은 정확한 순서 일치를 요구하는 단순 계약이므로 일반적인 조건 포함/의미 충족 검사로 보지 않는다.

## 3. 실행 결과

| 상황 | 진행 | 결과 |
|---|---|---|
| 정상 완료 | 시작 → r1 변경 → 현재 계획·r1 검증 통과 → 완료 | done. 4개 이벤트 보존 |
| 검증 실패 | 시작 → r1 변경 → 검증 실패 → 완료 요청 | blocked. 완료 요청 거부, 이전 상태·3개 이벤트 보존 |
| 완료 뒤 요구 변경 | 30분 조건으로 완료 → 45분 조건으로 계획 수정 → 즉시 완료/과거 검증 재사용 시도 → r2 변경·새 검증 → 완료 | 과거 완료/검증 이력 보존. 재사용 2건 거부. 최종 plan_version=2, revision=r2, done. 8개 이벤트 보존 |

- 세 상황 **3/3**, 단계 확인 **18/18** 통과. 거부가 기대되는 단계도 포함한다.
- 단위 테스트 **12/12**, 0.007초. 세 상황 replay 약 0.0023초. 이 시간은 Python 고정 입력 처리 시간이지 AI 작업 속도 지표가 아니다.
- Python primary LSP: 3개 파일 진단 0.
- 18개 요청 중 15개 수락, 3개 의도한 거부. 거부 요청은 결과 trace에 남으며 태스크의 수락 이력에는 들어가지 않는다. 운영 감사 로그를 구현한 것은 아니다.

## 4. 어떤 보호를 시험했나?

- 검증 없이 완료 불가.
- 검증 이후 작업 revision이 바뀌면 이전 검증 무효화.
- 예전 revision 또는 계획 버전에 대한 검증 재사용 거부.
- 완료 조건 일부만 제출한 검증 거부.
- 타 태스크 이벤트 거부.
- 동일 이벤트 재전달은 no-op, 같은 ID의 다른 내용은 거부.
- 거부 시 상태·수락 이력 불변.
- 외부에서 입력/반환 snapshot을 수정해도 내부 이력에 영향 없음.
- 계획 변경 이유가 없으면 거부, 변경 후에도 과거 완료 이력 유지.
- 정답 fixture를 바꾸면 채점만 실패하고 실제 태스크 결과는 동일.
- 실패 후 재개만으로 완료할 수 없고 새 통과 기록 필요.

## 5. 중요하게 발견한 한계

### 가짜 ‘통과’도 현재 프로토타입은 받아들인다

없는 테스트 실행을 가리키는 receipt_id와 pass를 주면 완료된다. 이 동작을 **한계 확인 테스트**로 명시해 재현했다. 따라서 12/12 통과는 ‘증거가 진짜임을 보장했다’가 아니라, **정한 계약과 명시한 한계를 확인했다**는 뜻이다.

실제 준수 강제로 확장하려면 작업자가 임의로 만든 pass 문자열이 아니라 런타임이 발급·조회하는 실행 결과에 연결해야 한다. 그 경우에도 테스트가 충분한지와 의도가 모두 기록됐는지는 별도 평가가 필요하다. 이번에는 이를 몰래 추가 구현하지 않았다.

### 이벤트 하나가 상태와 이력을 함께 갱신할 수 있다

현재 상태는 코드가 이벤트에서 갱신하고, 해당 이벤트는 동시에 보존했다. 별도 ‘완료 보고서’ 문자열은 생성하지 않았다. 이것은 **중복 서술을 줄일 수 있는 기계적 구조**의 확인이다.

하지만 작업자가 이벤트를 얼마나 쉽게/빠짐없이 쓰는지, 보고서 방식보다 실제 토큰이 줄었는지는 측정하지 않았다. 입력 fixture는 사람이 구성했으므로 실제 모델의 준수율로 해석하면 안 된다.

### 계획 버전과 작업 결과 버전은 분리할 가치가 있다

코드가 같아도 완료 조건이 바뀌면 다시 판단해야 하고, 계획이 같아도 코드가 바뀌면 이전 검증이 낡을 수 있다. 이번 예시에서는 두 축을 분리해 오래된 검증을 차단했다. 제품 채택은 후속 검수 대상이다.

### 단일 프로세스의 복사 후 갱신은 DB 원자성이 아니다

메모리에서 검증 후 수락했을 뿐, 동시 writer·중단 복구·내구성·권한·로그 불변 저장을 구현하지 않았다. 실제 외부 입력용 완전 schema validator도 아니다. 신뢰된 로컬 fixture만 대상으로 한다. 계획 변경에 대한 사용자 승인 여부 역시 실행 환경에서 검증하지 않았다.

## 6. 판단과 다음 연구 후보

**이번에 확인:** ‘태스크 이벤트를 한 번 제출 → 현재 상태와 이력 함께 갱신’이라는 작은 구조는 세 상황에서 동작한다. 완료 조건 변경과 과거 검증 재사용을 구별할 수 있다.

**아직 미확인:** 실제 Sol의 기록 준수, Luna의 이해·소화, 중복 작성/토큰 절감, 실제 실행 증거 검증, DB·격리·병합, 데몬.

다음 후보는 두 가지이며 이번 보고로 자동 실행하지 않는다.
1. 이 최소 계약을 사용자 검수하고 불필요/누락 필드를 수정한다.
2. 실제 도구 receipt 연결 후 작은 Sol 작업에서 제출 누락·부실 이유·재촉·토큰을 측정한다. 이후 같은 기록을 Luna에 전달한다.

실패 자동 blocked 처리, 완료 후 변경 시 working 처리, 현재 조건 전체의 정확 일치 요구는 실험자가 택한 후보 규칙이다. 이 결과만으로 모든 업무에 적용할 규칙으로 승격하지 않는다.

## 7. 재현과 증거

```sh
cd experiments/v2-task-contract
python3 -m unittest -v
python3 run.py
```

- [시나리오별 실행 결과 JSON](../evidence/v2-task-contract-result.json): 입력/source SHA-256, 단계 trace, 마지막 상태, 수락 이력.
- [단위 테스트 출력](../evidence/v2-task-contract-tests.log).
- [브라우저용 결과 보고서](v2-task-contract-pilot.html): 이 문서의 파생 화면.
- 표준 검증 시도: `/tmp/v2-task-contract-standard.json`으로 출력 캡처를 요청했으나 외부 실행 도구의 180초 제한에 걸려 종료됐다. 캡처는 비어 있고 이후 해당 검증 프로세스는 관찰되지 않았다. 따라서 전체 표준 검증은 미완료이며 통과로 보고하지 않는다. focused 12개 시험의 성공과 구별한다.

## Rule placement
- Rule: 승인된 첫 태스크 고정 입력 실험의 후보 계약, 보호 케이스, 결과·한계.
- Scope: transient-plan
- Primary record: `.lazy-harness/tests/v2-task-contract-pilot.md`.
- Why not AGENTS.md: 범용 업무 완료 규칙으로 채택한 것이 아니라 작은 실험 계약이다.
- Why not local notes: 하네스 연구소의 재사용 가능한 실험 증거다.
- Confirmation: user-confirmed — 실험 진행 및 결과 보고 요청. 후보 규칙의 제품 채택은 미승인.

## Layer completeness / Discovery capture
- SDD: candidate contract captured here — Task.apply 입력·상태 전이의 실험 계약. 제품 API로 승격하지 않음.
- BDD: captured here — 정상 완료·실패·요구 정정의 합성 시나리오. 실제 모델 UI 흐름 아님.
- SSOT: no independent delta — 모델·DB·운영 정책·권한 설정 변경 없음.
- DDD: no independent delta — 업무 개념은 기존 연구 후보 유지. 신규 전역 도메인 정의 없음.
- TDD: 이 문서가 구현/검증 근거의 primary record. Planning은 링크로 연결. ADR: none.

## Implementation map
- `experiments/v2-task-contract/contract.py`: `ContractError`, `Task.__init__`, `Task.apply`, `Task._transition`, `Task._verify`, `Task.snapshot`. 고정 이벤트 → 후보 상태 검증 → 수락 이력·현재 상태 갱신.
- `experiments/v2-task-contract/run.py`: `evaluate`, `main`. fixture → 상태기계 → 기대 결과 채점 → stdout JSON. 정답을 상태기계에 전달하지 않음.
- `experiments/v2-task-contract/test_contract.py`: `TaskContractTests`의 12개 시험. 위 보호/한계 probe 대응.
- `experiments/v2-task-contract/scenarios.json`: 3개 시나리오·18개 확인 지점. synthetic receipt만 사용.
- `.local/render-v2-task-result.py`: 결과 Markdown을 HTML로 렌더링하는 파생 출력 도구. 제품 런타임과 무관.
- Graph: `kg_v2_task_contract_pilot` in `.lazy-harness/knowledge/graph.jsonl`.
- 관련 연구: [연구 시험 지도](../planning/v2-research-test-map.md) A/B/C 및 P0–P1. 현재 결과는 P2 실제 Sol 평가가 아니다.
