# Sol 요구 변경 시험 02

## 후속 보존 안내
- 아래 시험02의 사전 노출과 시험03의 제한된 결과는 역사적 기록으로 유지한다. 당시 표준검증 원본은 [보존 manifest](../evidence/v2-research-preserved-originals-01/manifest.json)의 `06-v2-sol-change-standard.json.bin`으로 byte/hash 사본을 남겼다.
- 후속 연구와 현재 상태는 [연구 전체 지도](../planning/v2-research-test-map.md)를 따른다. 아래의 초기 ‘아직 착수하지 않음/결과 없음’ 문구는 해당 시점의 상태이며 시험03 이후까지 미실행이라는 뜻이 아니다.


## Rule digest
- Status: advisory
- Layer: TDD
- Scope: host-project
- Aliases:
  - Sol 요구 변경 시험
  - 이전 통과의 재사용 차단
- Applies when: 승인된 V2 연구의 요구 변경 단일 표본을 실행·평가할 때.
- Must: 이전 계획 통과와 새 계획 완료를 구별하고 이전 이력을 보존한다. 실험 강제 절차의 효과를 모델의 자발적 준수로 과장하지 않는다.

## 승인과 순서
사용자는 변경/실패 대응 → Luna 기록 이해·소화 → 반복/비교 → 격리/병합/복구 순서로 진행을 승인했다. 이번 문서는 첫 단계의 단일 표본 정본이다. 앞선 시험의 정책 ID 정렬 standard 실패는 별도 #16 미해결이며 이 시험에서 policies.json을 변경하지 않는다. DB 배포·실제 공통 병합·데이터 삭제 승인은 아니다.

## 실험 설계
- Sol medium 한 writer, fresh 문맥. 대상 `experiments/v2-sol-recording-02/`, W2/T2.
- 이전 보존 baseline에서 시작하며 기존 실험 기록/코드는 수정하지 않는다.
- 계획 1: 세션 만료 기본 60, 정확한 정수 1..240, 잘못된 타입 거부, dict 요구, 입력 불변.
- 계획 1 검증 통과 뒤 완료 전에 native contact_supervisor로 중지한다. 이는 승인된 시험의 개입 경계이지 사용자에게 전체 진행을 재질문하는 게이트가 아니다.
- parent는 이력/실제 검증을 확인하고 계획 1 파일과 코드를 보존한 뒤 계획 2를 전달한다. 변경: 과도하게 긴 세션을 막기 위해 상한을 240에서 120으로 낮춘다. 나머지 요구는 그대로다.
- child가 기다리는 동안만 parent가 task.json의 plan_version=2와 요구/변경 이유를 수정한다. 이후 parent는 recorder complete를 한 번 시도하여 이전 통과가 거부되는 실제 exit/output을 증거로 보존한다. 거부가 안 되면 실험을 중단하고 결함으로 기록한다.
- parent 개입을 별도 증거 파일에 기록하며 Sol 기록으로 위장하지 않는다. 검사 실패를 숨겨서 새 코드까지 진행하지 않는다.
- child에게 변경 이유와 수정된 task.json을 알려 준다. 이전 결과의 유효성 판단, 필요한 테스트/코드 수정, 변경·미해결·검증 기록을 요청한다. 121..240을 어떤 테스트로 다룰지는 child가 작성한다.
- 최종 독립 평가: 1..120 허용, 121..240 거부, 기존 타입/기본/불변 요구 유지, 양쪽 계획 해시·검증 이력과 변경 이유가 남았는지 확인.

## 해석 경계
두 표본만으로 일반 성공률·절감률을 산출하지 않는다. checkpoint와 기록 도구는 제공했다. 작업자가 스스로 요구 변경을 발견하는 능력, 제품 승인 시스템, 강한 위조 방지·동시성은 미검증. parent의 알려진 요구 변경은 사전에 승인된 합성 실험 입력이며 실제 제품 정책이 아니다. 코드/테스트 수정이 늦거나 실패하면 그 사실을 결과로 보존한다.

## 실행 상태
실제 작업과 parent의 사후 확인은 끝났다. 그러나 아래 사전 정보 노출을 발견하여 **불시에 바뀐 요구에 대한 대응 시험으로는 판정할 수 없다.** 전체 standard는 이번 후속 검수에서 아직 실행하지 않았고 마감하지 않는다.

## 쉬운 결과 요약
- Sol은 첫 조건(1..240)으로 실제 테스트 6개를 통과한 뒤 요청한 지점에서 기다렸다.
- parent가 상한을 120으로 바꾸자, 이전 통과를 재사용한 완료 시도는 exit 2로 거부됐다. 이는 parent의 기계적 확인이며 Sol 스스로 거부를 발견한 것으로 세지 않는다.
- Sol은 이전 통과가 새 요구의 검증이 아니라는 메모, 필요한 수정, 120/121 및 240 경계 테스트, 실제 새 검증과 완료를 남겼다.
- 최종 테스트 6개 통과, parent 확인 279항목 통과(코드 260 + 연결/이력 확인 19). 코드 확인 중 240개는 정수 범위를 하나씩 점검한 것이며 서로 다른 240개 업무가 아니다.
- 계획별 이력 11개가 보존됐다. recorder는 변경되지 않았고 task.json은 parent가 전달한 계획2 그대로였다. Sol의 별도 완료 보고서는 없었다.
- 모델 gpt-5.6-sol, 응답 15회, 도구 호출 20회. 입력 42,669 / 출력 2,649 / 캐시 입력 361,344 토큰. 보고 비용 $0.473487은 child만의 합계이며 parent 준비·개입·평가 비용과 실제 청구 검증은 제외한다.

## 중요한 한계: 변경 내용을 미리 볼 수 있었다
사후 tool trace에서 Sol이 시작할 때 이 연구 문서 전체를 읽은 사실을 확인했다. 이 문서에는 이후 상한을 120으로 낮춘다는 실험 설계가 이미 적혀 있었다. 따라서 **나중에 전달할 변경 내용이 작업자에게 미리 노출됐다.** parent가 과제 파일을 뒤에 변경한 것은 사실이지만, 작업자가 변경을 처음 알게 된 시점이 그때라고 주장할 수 없다.

이는 실험 준비 시 parent가 작업용 설명과 평가자용 계획을 같은 접근 가능한 저장소에 둔 한계다. child의 악의나 일반적인 기록 능력 실패를 뜻하지 않는다. 프롬프트의 접근 안내만으로 평가 정보 격리를 보장하지 못했다.

확인 가능한 결론은 **알려진 절차에서 계획 버전·이력·실행 연결과 실제 재작업이 작동했다**는 것이다. 예상하지 못한 요구 변경의 발견·대응 능력은 미검증으로 남긴다. 모델 준수 효과와 도구 강제 효과도 분리한다.

## 다음 결정이 필요한 부분
- 격리된 작업 입력으로 같은 단계 재실행: 평가자용 계획을 child가 읽는 저장소에 두지 않고 문서 확인 경로도 분리한다. 아직 착수하지 않았다.
- 또는 현재 결과를 절차 연습으로만 채택하고 승인된 다음 단계 Luna 기록 읽기로 이동한다. 예상하지 못한 변경 시험은 뒤에 남긴다.
- 전체 정책 정렬 검증 실패 #16은 별도 유지한다.

## 증거
- workflow `5308a24e-45fb-40a0-a4e6-e477389d2c5e`; child `7f6898d4-ee58-472a-b867-83773e4ca095`, 완료 알림 수신.
- [parent 요구 변경 개입](../evidence/v2-sol-recording-02-intervention.json): task 변경 후 stale complete 거부, 이력 불변.
- [독립 평가와 전체 tool trace](../evidence/v2-sol-recording-02-evaluation.json): 세 번째 호출이 이 실험 문서 read임을 확인.
- `.local/evaluate-v2-sol-change.py`: parent-only 사후 코드·이력·해시·사용량 평가. 체크 통과는 사전 정보 노출을 자동 검출한 결과가 아니며, 노출은 parent가 trace를 읽고 판단했다.
- `.local/v2-sol-recording-02-baseline` 및 `.local/v2-sol-recording-02-plan1-checkpoint`: 원래 입력과 변경 전 코드/이력 보존.
- [HTML 보고서](v2-sol-requirement-change.html).

## 사용자 승인된 입력 분리 재시험 03
- 사용자 선택: ‘입력을 분리해 재시험’. 동일 단계 보완으로 승인; 현재 표본 02를 삭제하거나 성공으로 재분류하지 않는다.
- 작업자 root: `/tmp/v2-sol-change-isolated-tpg0re7o`, 별도 빈 Git root. 제품 repo·연구 문서·평가 계획을 복사하지 않는다. 입력 파일은 task.json, record.py, 원래 함수와 테스트뿐이다.
- fresh Sol medium, W3/T3. 부모 문맥을 fork하지 않으며 프롬프트에 연구 repo 경로나 평가 계획을 전달하지 않는다. child에는 현재 요구와 완료 전 검토 지점만 전달한다.
- 평가자 전용 개입(이 문서는 작업 root 밖에 있음): 최초 상한240 → 검토 지점 후 상한90. 기본60 및 나머지 요구 유지. 이전 노출된 120 값을 그대로 정답으로 재사용하지 않는다.
- 전후 스냅샷과 parent의 stale-complete 시도는 시험02와 같은 방식으로 별도 증거에 저장한다. 최종 평가에서 90 허용·91/120/240 거부 및 기존 요구 유지 확인.
- 시작 파일 목록·해시와 실제 tool trace를 대조하여 외부 연구/평가 내용 읽기 여부를 평가한다. 평가 내용을 읽었거나 상위 repo 문서 확인이 강제되면 중단하고 재실행을 자동 우회하지 않는다.
- 이 분리는 실수로 연구 문서를 읽게 되는 경로를 줄이는 작업 디렉터리 분리다. shell을 가진 child에 대한 OS 접근 통제나 악의적 열람 방지 보장은 아니다.
- 완료한 작업 파일·이력·실행 근거를 `experiments/v2-sol-recording-03/`에 보존했다. 원래 임시 작업 폴더는 삭제하지 않았다.

## 입력 분리 재시험 03 결과
**이번에는 미리 바뀔 조건을 읽은 흔적 없이, 변경된 요구에 맞춰 다시 작업하고 기록을 남겼다.** 다만 단일 과제이고 변경 통지와 기록 방법을 명확히 제공한 조건이다.

1. Sol은 현재 과제와 로컬 코드·기록 도구만 읽고 상한240 기준의 테스트를 통과했다.
2. 검토 지점에서 parent가 상한90으로 바꿨다. 기존 통과로 완료하려는 parent 시도는 거부됐고 이전 이력은 보존됐다.
3. Sol은 “계획1 검증은 상한 240 기준이라 계획2에는 유효하지 않으며 상한을 90으로 낮춘다”는 결정을 기록했다.
4. 90 허용·91 거부 등의 테스트와 코드를 수정한 뒤 실제 테스트 7개가 통과했다. 계획2 검증을 가리키는 완료가 남았다.
5. parent의 독립 코드/이력 확인 271항목이 통과했다. 코드 동작 256항목 중 240개는 정수 범위를 하나씩 검사한 것이다. 다수 업무 성공률로 해석하지 않는다.

### 정보 노출 검수
전체 child tool trace 17개를 parent가 읽었다. 과제 root의 ls, 로컬 입력 read, 허용된 코드/테스트 수정, record.py 명령, supervisor 연락, 최종 두 줄 출력 저장만 확인했다. 원본 연구 저장소·평가 계획·이전 실험을 읽거나 검색하는 도구 호출은 없었다. 변경값90은 supervisor 응답과 갱신된 task.json 읽기 뒤에 작업에 등장했다. 이는 관측된 도구 경로의 확인이지 모델 내부 지식이나 OS 보안의 증명은 아니다.

### 기록의 충분성과 한계
진행 이력 10개에 두 계획의 검증과 완료가 연결됐다. 변경 이유의 업무적 설명(너무 긴 세션을 막기 위함)은 task.json의 change_reason에 있고, Sol 메모에는 이전 검증 무효와 새 경계/남은 일이 있다. 따라서 **태스크 설명과 진행 이력을 함께 읽어야 한다.** 메모만 떼어내면 이유가 모두 담겨 있지 않다. 다음 Luna 시험은 이 묶음을 읽는 조건으로 평가한다.

### 비용
Sol 응답 15회, 도구17회. 입력26,921 / 출력2,163 / 캐시입력83,456 토큰, 보고 비용 $0.241223. parent 준비/검수/중간 개입 비용 제외. 앞선 표본과 문맥·실행 환경·조건이 달라졌으므로 이 차이를 기록 방식의 비용 절감률로 주장하지 않는다.

### 보존 증거와 검증 상태
- workflow `b3941918-f3d6-495b-950f-315ede91ec23`; child `8ef9fead-1067-43d9-a691-f7a383640ba5`, 완료 알림 수신.
- [입력 파일 목록/해시](../evidence/v2-sol-recording-03-input.json), [parent 개입](../evidence/v2-sol-recording-03-intervention.json), [사후 평가/전체 도구 호출](../evidence/v2-sol-recording-03-evaluation.json).
- `.local/evaluate-v2-sol-isolated.py`: parent 요구·코드·이력 해시 평가와 사용량/툴 추출. 정보 노출 판정은 parent 수동 trace 검수다.
- 보존본 `experiments/v2-sol-recording-03/`: `resolve_timeout`, `TimeoutTests`, `IntSubclass`, recorder `append`/`verify`/`main` 등. 코드를 부모가 보정하지 않았다.
- source/test primary LSP 진단0. 최종 framework standard는 **실패**: 128.258초, scoped fast-static 통과, full-self-test의 `Policy Registry policies must be deterministic id-sorted` 실패. `/tmp/v2-sol-change-standard.json`에 보존. 이는 기존 #16과 같은 메시지이며 정책 파일은 수정하지 않았다. 실험 결과와 전체 저장소 마감 상태를 구별한다.

## Layer completeness / Discovery capture
- SDD: candidate captured here — 실험 기록에 plan_version을 추가, task.json 해시 변경으로 기존 검증이 무효화되는 기존 recorder 계약 관찰. 제품 API 독립 변경 없음.
- BDD: captured here — 계획 1 통과 → 대기 → 명시적 요구 변경 → 기존 완료 거부 → 계획 2 재작업/검증. 실험 이외 UI 변경 없음.
- SSOT: no independent delta — 모델 선택 재사용, 운영 정책·DB·설치 변경 없음.
- DDD: no independent delta — 기존 업무·계획·이력 개념을 검증, 새 도메인 정의 없음.
- Discovery capture: TDD primary; 후속 Luna/비교/복구는 승인된 backlog #18–20, 시험 지도에는 링크만 둔다.
- Rule placement: transient-plan, 이 primary record에만 보존. 운영 규칙 채택 아님.

## Implementation map
- `experiments/v2-sol-recording-02/task.json`: 현재 요구와 checkpoint, 부모가 개입 시 변경.
- `experiments/v2-sol-recording-02/timeout_config.py`: `resolve_timeout`, Sol 수정 대상.
- `experiments/v2-sol-recording-02/test_timeout_config.py`: `TimeoutTests`, Sol 테스트 대상.
- `experiments/v2-sol-recording-02/record.py`: `append`에 현재 plan_version을 기록. `hashes`, `verify`, `main`은 이전 도구를 재사용. task.json과 소스 해시를 함께 검사한다.
- 보호: parent checkpoint의 stale-complete 거부 실험과 완료 후 독립 검증. 결과는 아직 없음.
- [이전 실제 시험](v2-sol-recording-pilot.md), [연구 시험 지도](../planning/v2-research-test-map.md).
- Graph: `.lazy-harness/knowledge/graph.jsonl`, `kg_v2_sol_requirement_change`.
