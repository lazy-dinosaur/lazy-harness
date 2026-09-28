# Follow-up 01 — 입력 공정성과 실행 보존 회귀

## Rule digest

- Status: active
- Layer: TDD
- Scope: host-project
- Scope note: host-specific
- Aliases:
  - follow-up 01
  - 입력 공정성 회귀
- Applies when: 두 후속 연구의 입력·실행·결과를 검수할 때
- Must: 같은 사례·질문으로 F/S를 비교하고 문서/명제 저장 처치를 실제로 구분한다. 미확인은 거짓이 아니다. 기존 비용·실패를 보존하며 정답은 참가자에게 제공하지 않는다.
- Must not: 준비 완료나 더미 출력, assertion 이름만으로 실제 실험 성공을 주장하지 않는다.

## 승인과 범위

사용자는 읽기 약점 확인 후 추가·수정 전체 관리 비용을 따로 비교하고, 준비에서 멈추지 말고 실제 결과까지 진행하라고 확인했다. 기존 총 $3 목표를 유지한다. 제품 스키마 채택은 아니다. 주 기록: [V2 연구 계획](../planning/v2-vision-feasibility-research.md).

## 거절된 준비 보존

Workflow `dd451188-690b-4ee0-a487-1694863b23c2`의 reviewer `644913bf-2da1-43f4-a630-72e9ee2e5467`는 입력을 blocked로 판정했다. 참가자 호출은 없었다. 서로 다른 필요조건을 모순으로 판정, 미확인 역방향을 false 처리, current 버전 누락, 4+4 대신 6+2 분배가 있었다. Parent는 다른 사례를 각 F/S 호출에 배정한 코드, 실제 저장 형식 처치/최종 질문 누락, 단순 이벤트 누적, 실행 전 외부 hash 검증 누락, 종료 시에만 raw 저장, bytes/4를 상한으로 쓴 비용 계산도 발견했다.
원본 두 파일은 `.local/v2-reading-display-01/followup-runner-rejected.mjs`, `followup-fixtures-rejected.json`에 각각 1개씩 보존했다. 기존 offline receipt는 수정하지 않았다.

## 교정 프로토콜

- 읽기: 한국어 신규 8사례(범위/충돌 4, 필요/충분조건 4), 동일 전체 사례를 F/S 각 3회, 순서 F,S,S,F,F,S. 각 사례 자체의 명시된 배경만 적용한다. positive/negative/unknown 통제를 구분한다.
- 갱신: 동일 초기 10사실과 순차 2변경 묶음. A는 자유로운 Markdown 문서(표/목록/ID 허용), B는 자연어 문장 구성 명제(선택 필드 허용). 각 생성→갱신1→갱신2→독립 최종 읽기, 총 8호출. 각 갱신은 직전 실제 반환 artifact만 받는다. 원문 이력은 실험 증거로 외부 보존하되 숨은 fallback으로 재주입하지 않는다.
- 같은 모델 Luna medium, tool-free fresh requests, output 4096 tokens, prompt 24000 UTF-8 bytes 제한. token 예약은 bytes/4 대신 byte 수+system prompt+4096 framing margin을 쓴다. 예약 범위/실제 사용량을 매 호출 확인하며 실제 tokenizer/remote billing hard guarantee로 주장하지 않는다.
- 이전 비용 $1.92524732는 거절된 준비/검수 $0.07794288 포함. 다음 workflow $.30, 참가자 $.50 예약; 합계 $2.72524732. 실제 catalog worst 14호출 $0.25445434. SDK 추정치이며 부모 대화·청구서 제외.
- 실행 전 외부 fixture/runner manifest hash 검증. 각 request와 raw response를 즉시 exclusive 저장한 후 terminal/usage/format 검사. 의미 오류는 재실행하지 않는다. 실패 시 이미 완료된 호출도 보존한다. 최종 답변 누락과 거짓 주장을 구분해 평가한다.

## 검증

Parent 실행: `node /home/lazydino/dev/lazy-harness.v2/experiments/v2-followup-01/runner.mjs --offline`, exit 0, checks 22. 정확한 출력은 tool receipt와 `experiments/v2-followup-01/offline-receipt-v2.json`에 남았다. 실제 공식 catalog 메타데이터와 동일 orchestration의 dummy 호출 검증이며 유료 참가자 추론은 아니다. LSP primary 파일 1개 errors 0.

- fixture SHA256 `37acb8755a5c32129d11d4169e68a6f7eea1f2fee47b420553407d26f35c5a7d`
- runner SHA256 `1e8fc8b8c19eda9783a5d9d8ade1edb165c7c0361dc38d498f63fce395325a72`
- manifest `experiments/v2-followup-01/review-manifest-v2.json` — 독립 검수 통과 그 자체는 아니다.
- Broad check/standard validator는 기존 특수 파일 위험으로 보류. 조상 directory 교체 race와 remote abort billing 한계는 남는다. 독립 source/입력 검수 뒤에만 live 실행한다.

## Layer completeness

- SDD: no independent delta — 제품 API·컴포넌트 계약·스키마 채택 변화 없음. 합성 연구 protocol 교정은 이 기록에 한정한다.
- BDD: no independent delta — 제품 사용자 흐름 변화 없음.
- SSOT: no independent delta — 전역 config·ownership 변화 없음. 연구의 기존 누적 예산을 유지한다.
- DDD: no independent delta — 도메인 규칙 채택 없음. 합성 과제의 정답 교정에 한정한다.

## Implementation map

- `experiments/v2-followup-01/fixtures.json`: 공개 입력·private gold, 서로 다른 두 연구.
- `experiments/v2-followup-01/runner.mjs`: `readingPrompt`, `maintenancePrompt`, `finalPrompt`는 표시/갱신/읽기 경계. `studies`는 실제 14호출 순서와 artifact replacement. `worstCall`은 catalog admission, `invoke`는 공식 SDK 단일 요청, `run`은 frozen gate와 즉시 영수증 보존, `offline`은 22개 focused checks, `parseResult`는 의미 정답과 분리된 형식 검사.
- 이전 연구: [pilot03](../evidence/v2-reading-display-pilot03.md). 새 결과는 별도 evidence로 남기며 과거 결과를 덮어쓰지 않는다.
- 실제 실행 결과: [v2-followup-01 evidence](../evidence/v2-followup-01.md) 및 [assessment JSON](../evidence/v2-followup-01-assessment.json).
