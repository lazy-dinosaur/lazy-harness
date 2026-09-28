# Sol 실제 작업·기록 시험 01

## 후속 보존 안내
- 원래 결과/실패 이력은 아래 그대로 유지한다. 실행 상태 원본과 당시 표준검증 캡처의 로컬 사본은 [보존 manifest](../evidence/v2-research-preserved-originals-01/manifest.json)의 `02-sol-recording-pilot-01-status.md.bin`, `07-v2-sol-recording-standard.json.bin`에 있다. 원본 bytes/SHA-256을 대조했으며 원래 세션·임시 파일은 삭제하지 않았다.


## Rule digest
- Status: advisory
- Layer: TDD
- Scope: host-project
- Aliases:
  - Sol 실제 기록 시험
  - 업무 객체 기록 준수 P2
- Applies when: 첫 실제 Sol 업무 객체/기록 시험을 실행하거나 결과를 평가할 때.
- Must: 단일 표본의 기록 수행 가능성과 비용 절감·일반 준수율을 구별한다. 테스트 영수증은 실제 subprocess 결과로 생성하며, 프롬프트 기반 파일 경계를 보안 격리로 과장하지 않는다.

## 승인과 범위

사용자가 읽기 전용 실행 경로 확인 성공 후 연구 진행을 승인했다. 한 번의 fresh Sol medium 작업으로 작은 실제 Python 코드를 수정하고 기록을 남기는 시험이다. 전체 하네스 제품 구현·설치 변경·DB·네트워크·Luna 소화 실행은 제외한다.

- 대상: `experiments/v2-sol-recording-01/`.
- 모델: `openai-codex/gpt-5.6-sol:medium`, 한 writer만 실행.
- 시간 범위: child 최대 10분. 중단 시 결과를 실패/미완료로 보존하며 다른 모델로 대체하지 않는다.
- 목적: 세션 만료 설정 읽기 함수의 정확한 정수·범위 검사 및 테스트 구현.
- PRD/태스크는 parent가 사전 제공한다. Sol의 계획 생성 능력을 평가하는 시험은 아니다.
- 정상 작업과 시작 코드의 알려진 테스트 실패를 포함한다. 요구 변경·격리 병합·동시성은 이번 범위에 없다.

## 기록 계약 후보

`task.json`은 목적·범위·완료 조건을 담는다. Sol은 `record.py start`, `verify`, `decision/note`, `complete`를 사용한다. 현재 진행 상태는 이벤트에서 표시하고 별도 완료 보고서는 요구하지 않는다.

`verify`는 고정 unittest 명령을 실제로 실행해 exit code·출력·시간·소스 SHA-256을 receipts에 남긴다. `complete`는 현재 파일 해시에 대응하는 최근 통과 기록과 메모 존재를 확인한다. 이 장치는 모델이 직접 pass 문자열을 제출하는 앞선 모형의 한계를 줄인다.

그러나 child가 shell 접근을 갖기 때문에 파일 접근 금지 지시는 보안 경계가 아니다. parent는 task/recorder 보존 해시, 세션 tool trace, 이력과 receipt, 별도의 정답 검사를 대조한다. 파일 기반 단일 writer 도구이며 트랜잭션·재시작 복구·강한 위조 방지·숨은 의도 복원은 구현하지 않았다. 테스트 성공은 의미상 메모의 충실함을 보장하지 않는다.

## 사전 평가 기준

1. 코드: 기본값 60, 정확한 int 1..240, bool/float/str/None/범위 밖 거부, dict 아닌 입력 거부, 입력 불변.
2. 기록: 시작, 실제 baseline 실패, 실패 원인 또는 선택 이유, 최종 검증, 미해결 상태, 완료 연결을 확인한다.
3. 무결성: task.json/record.py 보존, 모든 receipt 해시 및 대응 코드 상태 확인. 범위 밖 변경은 별도 실패로 표시한다.
4. 준수: parent의 중간 재촉 없이 수행했는지, 별도 장문 완료 보고서/직접 receipt 조작이 있었는지 세션에서 확인한다.
5. 사용량: 실제 resolved model/thinking, 호출 수·턴·툴·토큰·비용·시간을 도구 증거로 보고한다. 단일 조건이므로 절감률은 산출하지 않는다.

고정 정답 검사는 child 완료 뒤 parent가 수행한다. 평가자 결과를 child에 미리 주거나 실패 결과를 몰래 보정하지 않는다. 실행 실패·일반 작업 테스트 실패·기록 부족을 구별한다.

## 실행 상태

첫 실제 Sol 시험 완료. 아래는 도구 실행 기록과 parent의 독립 확인을 대조한 결과다. 전체 framework 표준 검증 결과는 별도이며, 단일 표본의 가능성 확인을 일반적인 준수율로 확대하지 않는다.

## 결과를 쉬운 말로 요약

**Sol이 실제 코드를 고치면서 짧은 기록을 남겼고, 별도 장문 보고서 없이도 무엇을 왜 했는지 확인할 수 있었다.** 다만 요구와 기록 방법을 처음부터 자세히 제공한 아주 작은 작업 한 번의 결과다.

### 1. 어떤 일을 맡겼나?
- 세션 만료 설정을 읽는 작은 함수를 고치게 했다.
- 설정이 없으면 60분, 올바른 정수 1~240만 허용하도록 요구했다.
- True 같은 참/거짓 값이나 문자열을 숫자로 몰래 바꾸지 말고 거부하도록 했다.
- 코드와 테스트 파일 두 개만 수정할 수 있게 했다. 기존 제품 코드는 건드리는 과제가 아니었다.

### 2. Sol은 어떻게 진행했나?
1. 업무 설명과 기록 도구를 읽고, 현재 하네스가 요구하는 문서 확인을 수행했다.
2. 시작을 기록한 뒤 원래 코드의 테스트를 실제 실행했다. True가 숫자 1로 바뀌는 문제로 실패했다.
3. 실패 이유와 수정 방침을 짧게 기록했다.
4. 함수와 테스트를 수정했다.
5. 테스트를 다시 실행해 5개 테스트가 통과했다.
6. 남은 문제가 없다는 메모를 남기고 태스크를 완료했다. 최종 응답은 태스크 ID와 상태 두 줄뿐이었다.

중간에 parent가 기록을 다시 쓰라고 재촉하거나 코드를 보정하지 않았다. 이 표본의 child tool trace에서 source edit는 허용된 두 파일뿐이며, 별도 write는 런타임이 지정한 두 줄 상태 출력이었다. 기록·실행 결과 파일은 record.py가 생성했다.

### 3. 실제로 남은 기록
총 7개: 시작 → 실패한 검증 → 실패 설명 → 수정 결정 → 성공한 검증 → 남은 일 메모 → 완료.

Sol이 작성한 의미 기록은 다음 세 문장이다.
- “기준 테스트는 bool이 int로 변환되어 통과값 1이 되는 문제로 실패했다.”
- “bool 하위형 문제와 자동 변환을 막기 위해 값의 타입이 정확히 int인지 확인한 뒤 1..240 범위를 검사한다.”
- “요구된 허용·거부 경계와 입력 불변 테스트가 통과했으며 남은 문제는 없다.”

처음 두 문장은 원인과 이유, 마지막은 작업자의 미해결 판단이다. 마지막 문장을 절대적 무결점 보증으로 읽으면 안 된다. 실제 테스트 출력과 코드 상태를 가리키는 식별값은 도구가 자동으로 남겼다.

### 4. parent가 별도로 확인한 것
- Sol이 작성한 테스트 5개는 실제 실행 기록에서 통과했다.
- parent의 독립 코드 검사 266개 항목이 통과했다. 이 중 240개는 허용 범위의 정수를 하나씩 확인한 것이므로, 266개의 서로 다른 업무를 시험했다는 뜻은 아니다.
- 기록 순서·파일 보존·실행 결과 연결을 포함하면 총 280개 확인 항목이 통과했다. 정확한 7개 이벤트 순서 검사는 이 표본의 관찰 결과 확인이지 모든 업무의 고정 규칙은 아니다.
- task.json과 record.py의 파일 해시는 실행 전과 같았다.
- 시작 때의 실패 기록은 원래 코드, 마지막 성공 기록은 최종 코드에 연결돼 있었다.
- 최종 응답은 `task_id: T1` / `status: complete`로 끝났으며 별도 작업 보고서를 중복 작성하지 않았다.
- 완료 후 source/test primary LSP 진단은 0개였다.

### 5. 시간과 비용
| 항목 | 관측값 | 해석 |
|---|---|---|
| 실행 모델 | gpt-5.6-sol, medium | subagent status와 세션에서 확인 |
| child 실행 시간 | 약 96.7초 | 준비·평가·HTML 작성 시간은 제외 |
| 모델 응답 횟수 | 11 | 한 작업에서 여러 번 도구를 쓰며 진행 |
| 도구 호출 | 14 | 읽기·문서 확인·기록·수정·검증·짧은 결과 저장 포함 |
| 새 입력 토큰 | 32,141 | child 세션 usage 합계 |
| 출력 토큰 | 1,678 | child 세션 usage 합계 |
| 캐시에서 읽은 토큰 | 249,216 | 재사용 문맥도 비용 집계에 포함 |
| 도구 보고 비용 | 약 $0.336 | 보고된 usage 기준, 청구서 검증 아님. parent 비용 제외 |

문서 확인과 런타임 문맥도 이 비용에 들어 있다. 이전 읽기 확인용 canary와 실패한 실행 준비, parent의 준비·평가 비용은 포함하지 않았다. 따라서 전체 연구 비용이나 기록 방식의 절감률로 사용하면 안 된다.

### 6. 이번에 말할 수 있는 결론과 없는 결론
**말할 수 있는 것:** 이 작은 사례에서 Sol은 주어진 업무 객체와 기록 도구를 따라 실제 수정·검증·이유 기록·완료를 수행했다. 실패부터 완료까지의 흐름을 별도 보고서 없이 확인할 수 있었다.

**아직 말할 수 없는 것:** 항상 누락 없이 기록한다, 다른 방식보다 싸거나 빠르다, 복잡한 계획 변경도 잘 처리한다, Luna가 이 기록만으로 충분히 소화한다, 악의적 위조나 동시 작업에도 안전하다.

특히 이번에는 ‘왜 이렇게 해야 하는지’가 잘 적힌 과제를 제공했고 기록 시점도 상세히 지시했다. 애매한 요구, 새로운 결정, 작업 도중 정정, 여러 태스크, 실제 사용자 승인 경계는 다음 시험의 별도 조건이다.

### 다음 후보
- 같은 수준의 다른 작은 과제로 한 번 더 관찰하되, 중간 요구 변경 또는 보류 중 하나만 추가해 기록이 유지되는지 본다.
- 또는 이번 task.json·이벤트·검증 근거를 Luna에 주고 무엇을 왜 바꿨는지 질문한다. 먼저 코드/대화 원문을 추가로 보지 않고도 답할 수 있는지 평가한다.
- 비교 조건과 추가 호출은 이번 결과를 검수한 뒤 결정한다. 이번 보고가 다음 실험의 자동 승인은 아니다.

## 실행 증거
- workflow: `59029a8e-4937-4a54-adfc-5ba4c734d30d`; child: `496c5007-2c6c-4c0c-8e5f-0fef22a0a9b4`, completed/process terminal observed.
- outputReference: `/home/lazydino/.pi/agent/sessions/--home-lazydino-dev-lazy-harness--/subagent-artifacts/outputs/59029a8e-4937-4a54-adfc-5ba4c734d30d/sol-recording-pilot-01-status.md`.
- [parent 평가 JSON](../evidence/v2-sol-recording-evaluation.json): 요구별 결과, 기록 무결성, tool trace와 child usage.
- [recorder 사전 검사](../evidence/v2-sol-recording-preflight.json): 7/7, 원본 입력은 변경하지 않고 임시 복제에서 확인.
- `experiments/v2-sol-recording-01/events.jsonl` 및 `receipts/*.json`: Sol의 실제 진행/실행 결과.
- [HTML 결과 보고서](v2-sol-recording-pilot.html): 이 문서의 파생 화면.
- 최종 framework 표준 검증: **실패**. 129.008초, scoped fast-static-check는 통과했지만 full-self-test에서 `Policy Registry policies must be deterministic id-sorted`가 실패했다. fullRegression=false이며 전체 통과로 보고하지 않는다.
- 로그: `/tmp/v2-sol-recording-standard.json`. 기존 수정 중인 정책 파일과 관련된 정렬 검증 실패로 표시됐지만 이번 턴에 원인 diff나 수정 범위를 추가 조사하지 않았다. 기록 실험 자체의 결과와 분리하며, 승인 없이 policies.json을 재정렬하지 않는다.

## Layer completeness / Discovery capture
- SDD: candidate captured here — 이 실험 전용 태스크/기록 CLI 계약. 제품 API 미채택.
- BDD: captured here — 실제 코드 수정 중 baseline 실패 확인·진행 기록·완료 시나리오.
- SSOT: no independent delta — DB·설치·운영 정책 변경 없음. 명시한 모델 선택을 재사용.
- DDD: no independent delta — 업무/기록 구상의 첫 검증이며 도메인 정의 추가 없음.
- TDD: 이 문서를 primary record로 사용. Planning에는 링크만 추가. ADR none.

## Rule placement
- Rule: 사용자 승인된 단일 Sol 실제 작업·기록 시험의 절차와 평가 경계.
- Scope: transient-plan
- Primary record: `.lazy-harness/tests/v2-sol-recording-pilot.md`.
- Why not AGENTS.md: 일반 작업 규칙으로 승격하지 않는 실험이다.
- Why not local notes: 프로젝트 연구 산출물이다.
- Confirmation: user-confirmed — 연구 진행 승인, 결과/제품 채택은 아직 없음.

## Implementation map
- `experiments/v2-sol-recording-01/task.json`: 읽기 전용 과제·기록 규격.
- `experiments/v2-sol-recording-01/timeout_config.py`: `resolve_timeout`, child 수정 대상.
- `experiments/v2-sol-recording-01/test_timeout_config.py`: `TimeoutTests`, child 테스트 대상.
- `experiments/v2-sol-recording-01/record.py`: `hashes`, `load_events`, `append`, `verify`, `main`. CLI → 실제 unittest → receipt → 이벤트 → 완료 전 확인.
- `.local/evaluate-v2-sol-recording.py`: parent-only post-run 요구 검사·기록 해시·child 사용량/툴 추출. 280개 확인, 이 중 코드 동작 266개. 결과 JSON에 세부 보존.
- `.local/render-v2-sol-result.py`: 결과 Markdown의 HTML 파생 렌더링.
- 보호/증거: 준비 검사 7개, child 테스트 5개, parent 사후 평가 280항목과 tool trace. 실제 모델 단일 표본이며 일반 준수율은 미검증.
- Graph: `.lazy-harness/knowledge/graph.jsonl`의 `kg_v2_sol_recording_pilot`.
- 연구 연결: [연구 시험 지도](../planning/v2-research-test-map.md), [이전 고정 입력 시험](v2-task-contract-pilot.md).
