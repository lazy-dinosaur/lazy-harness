# Luna 기록 이해·소화 첫 시험

## Rule digest
- Status: advisory
- Layer: TDD
- Scope: host-project
- Aliases:
  - Luna 기록 소화 시험
  - 기록만 읽어 현재 요구 복원
- Applies when: 승인된 V2 연구 순서의 기록 읽기·소화 첫 표본을 실행·평가할 때.
- Must: 제공된 기록에서 확인한 사실과 모델의 추정을 구별하고 각 주장에 source_id를 연결한다. 결과를 제품 공통 지식에 자동 채택하지 않는다.

## 승인과 입력
사용자가 승인한 변경 대응 → Luna 이해·소화 → 반복/비교 → 격리/병합/복구 중 두 번째 단계. 앞선 입력분리 시험03의 검수된 자료를 사용한다. 저장소 정책 정렬 standard 실패 #16은 미해결이며 데이터 읽기 평가와 분리한다.

- reader: fresh `openai-codex/gpt-5.6-luna:medium`, 단일 읽기 역할, 최대10분.
- 독립 root `/tmp/v2-luna-record-reader-x7nl_d6g`의 records.json 한 개: 계획1/2, 진행 이벤트10개, 실제 테스트 영수증3개, parent 개입1개, 총16 source.
- 미제공: 함수 코드, Sol 대화, 연구 보고서, parent 평가 정답. 임의 외부 read/search 금지. 전체 tool trace로 관측된 입력 경계 준수를 확인한다. OS sandbox 아님.
- 작업: 현재 요구·현재 상태·변경 역사·변경 이유·무효화된 증거·남은 불확실성을 작은 지식 표현으로 소화하고 출처를 붙인다. 입력은 수정하지 않는다.
- output은 managed output binding으로 JSON 한 개 보존하며 공통 SSOT/graph fact 채택은 하지 않는다. 이는 정리된 지식 후보이지 DB/새 서비스 설계가 아니다.

## 사전 평가 기준 (parent 전용)
1. 현재 plan2, 정확한 int 1..90, default60, bool 등 거부, dict/불변 조건을 혼동하지 않는다.
2. plan1 상한240을 현재 사실로 잘못 채택하지 않는다. 120도 허용하지 않는다.
3. 업무적 변경 이유는 task-plan2 change_reason에서, 실제 변경·검증은 이벤트/receipt에서 출처를 구분한다.
4. parent의 stale complete 거부를 Sol의 실행으로 바꾸지 않는다.
5. 기존 pass는 당시 plan1에는 유효했지만 plan2 완료 근거로는 무효임을 구별한다. 과거를 실패로 덮어쓰지 않는다.
6. 최종 완료는 현재 plan2 검증에 연결되고 실행 테스트7개임을 근거로 답한다. 소스 코드의 모든 입력에 대한 정확성/보안/동시성을 기록만으로 확정하지 않는다.
7. source_id가 실제 존재하고 해당 주장을 지지해야 한다. 모르는 것은 모름/미확인으로 남긴다.
8. 짧은 소화 산출물과 질문 답이 일관되는지, 원문 복사만 했는지 별도 판단. 한 번 정리한 결과의 장기 갱신·철회·Luna 자체 읽기 지연은 미검증.

## 실행 상태
단일 Luna medium 읽기 시험과 parent 검수 완료. 입력 파일은 변경되지 않았고 관측된 도구 호출은 records.json 읽기1회와 지정된 JSON 출력 쓰기1회뿐이다. 소스·작업자 대화·연구 문서 추가 열람은 없었다.

## 쉬운 결과 요약
**Luna는 코드나 Sol의 대화를 보지 않고, 남긴 기록만으로 현재 요구·변경 이유·완료 근거를 구별했다.** 이번 표본에서 핵심 질문7개의 취지를 맞게 답했다. 문장 하나는 아래처럼 더 정확하게 쓸 필요가 있다.

| 확인한 질문 | Luna 답변의 핵심 | parent 판정 |
|---|---|---|
| 지금 어떤 값이 허용되나? | 정확한 int 1~90, 기본60 | 현재 요구와 일치 |
| 120도 허용되나? | 아니며 ValueError 대상 | 과거 상한과 혼동하지 않음 |
| 무엇을 왜 바꿨나? | 긴 세션을 막기 위해 상한240→90 | task change_reason과 일치 |
| 이전 통과면 지금도 완료인가? | plan1 통과는 현재 완료의 단독 근거가 아님 | 과거 사실과 현재 유효성을 구별 |
| 거부된 완료를 누가 시도했나? | parent | Sol의 행동으로 바꾸지 않음 |
| 최종 완료 근거는? | plan2 pass, 실제 테스트7개, 이를 가리키는 complete | 이벤트·receipt와 일치 |
| 모든 입력·동시성도 안전한가? | 이 자료만으로는 확인 불가 | 근거 없는 보장 없음 |

출처를 붙인 주장14개 모두 실제 존재하는 source_id를 사용했다. parent는 참조 존재 확인과 별도로 문장의 의미가 원문과 맞는지 읽고 검수했다. 출처 ID가 맞는 것만으로 내용의 진실성이 자동 인증되는 것은 아니다.

## 표현상 보완점
history에 ‘당시 현재 코드의 통과 기록이 없어’라고 썼다. 더 정확하게는 **동일 코드의 plan1 통과는 있었지만 새 계획 해시에 대응하는 통과가 없었다**이다. 다른 답에서는 이 차이를 올바르게 구별했으므로 핵심 이해를 뒤집는 오류로 보지는 않지만, 완벽한 문장 정확도라고 보고하지 않는다. 원출력은 수정하지 않고 보존했다.

## 이번에 확인한 것과 아직 못한 것
- 확인: 제공한 태스크 버전·이력·실행근거 묶음만으로 최신 의미를 복원하고 과거 사실·현재 요구·불확실성을 분리할 수 있었다.
- 아직 미검증: 이후 새 기록을 추가했을 때 기존 지식을 수정·통합·철회하는 지속 소화, 복잡한 상충, 여러 영역, 다음 작업자가 이 소화 결과만 읽는 효과, 반복 정확도, 전체 비용 절감.
- 이번 출력은 현재 지식·역사·답변·모름을 나눈 단발 지식 후보다. 공통 지식 DB에 채택하지 않았고 장기 소화 시스템 완성으로 보지 않는다.

## 시간과 비용
- resolved model: gpt-5.6-luna, medium. 약41.2초, 모델 응답3회, 도구2회.
- 입력13,106 / 출력1,753 / 캐시 입력11,264 토큰. 런타임 보고 비용 $0.00495008(약0.005달러). 청구서 대조 아님.
- parent의 입력 준비·정답 검수·보고 작성과 앞선 Sol 작업비용은 별도다. 읽기 호출이 저렴해 보이는 것과 전체 업무 비용이 줄었다는 주장은 다르다.

## 검증 범위 정정과 증거
사용자 정정으로 확인: 기존 하네스의 정책정렬 오류는 새 하네스 연구의 합격/불합격 기준이 아니다. 별도 유지보수 #16으로 남기며 이번 연구 완료를 막지 않는다. 기존 하네스 코드 수정·병합·배포 검증의 적용 여부는 그 작업 범위에서 따로 판단한다. 이는 검증 스크립트 비활성화나 기존 오류 수정 승인이 아니다.

- workflow `d894a1bd-6fe4-4cf9-8f1d-c7dbf5c1085d`; child `92ceb6b3-334f-4ce5-abf2-f0b648cc2f5f`, complete/process terminal observed.
- outputReference: `/home/lazydino/.pi/agent/sessions/--home-lazydino-dev-lazy-harness--/subagent-artifacts/outputs/d894a1bd-6fe4-4cf9-8f1d-c7dbf5c1085d/luna-record-reader-01.json`.
- `experiments/v2-luna-reader-01/records.json`, `knowledge-candidate.json`: 입력과 모델 원출력 보존.
- [평가·사용량·도구 호출 증거](../evidence/v2-luna-reader-01-evaluation.json), [입력 해시](../evidence/v2-luna-reader-01-input.json).
- [HTML 결과 보고서](v2-luna-record-reader.html).

## Layer completeness / Discovery capture
- SDD: candidate captured here — 읽기용 source bundle과 지식 후보 JSON, 제품 API 독립 변경 없음.
- BDD: captured here — 기록만 읽고 최신 요구/역사/한계를 구별하는 연구 시나리오, 제품 UI 변화 없음.
- SSOT: no independent delta — 기존 Luna medium 선택 재사용, 설치/DB/운영 정책 변화 없음.
- DDD: no independent delta — 기존 업무·계획·검증·소화 개념 평가.
- Discovery capture: 이 TDD primary, 결과와 단일 evidence capsule로 수렴.
- Rule placement: transient-plan, 일반 operating rule로 승격하지 않음.

## Implementation map
- `/tmp/v2-luna-record-reader-x7nl_d6g/records.json`: source_id를 붙인 원본 기록 묶음. 원본 의미 내용은 고치지 않고 포장했다.
- `.lazy-harness/evidence/v2-luna-reader-01-input.json`: 입력 목록/해시/제외 자료 기록.
- `experiments/v2-sol-recording-03/task.json`, `events.jsonl`, `receipts/*.json`: 연구 데이터 원본.
- `.lazy-harness/evidence/v2-sol-recording-03-intervention.json`: parent의 계획 변경과 완료 거부 증거.
- 보존본 `experiments/v2-luna-reader-01/records.json`과 `knowledge-candidate.json`: 입력16 source와 원출력. `.lazy-harness/evidence/v2-luna-reader-01-evaluation.json`: 입력 불변·참조 존재·사용량·툴 증거.
- 검수: parent가 사전 기준으로 질문7개·주장14개의 의미/출처와 전체2개 도구 호출을 확인. 표현 보완1개를 위에 남겼다.
- [변경 시험 정본](v2-sol-requirement-change.md), [연구 지도](../planning/v2-research-test-map.md).
