# Planning — 차단 훅을 모니터링으로 옮기는 단계 계획

Status: stage 1 implementing on branch `work/hooks-advisory` (user execution approval 2026-11-10: “read debth 도 변경하고 훅도 다 빼버리자 진행해”)
Layer: Planning

## Rule digest

- Status: active
- Layer: Planning
- Scope: transient-plan
- Aliases:
  - 훅 모니터링 전환
  - read-debt 대체
  - hook to monitoring transition
- Applies when:
  - changing a blocking lazy-harness hook (read-debt, search-debt, rule placement STOP, affected test gate, capture notices)
  - letting monitoring modules search, inject or store records instead of blocking the agent
- Must:
  - follow the three stages in order: blocking -> advisory, monitoring searches/injects/stores, remove hooks only after the measured real-session recall passes the agreed threshold
  - keep the agent's behaviour rules in lazy-harness (separation rule ①); monitoring modules stay Fabric-free capabilities (②)
- Must not:
  - remove a hook before monitoring recall on real sessions is measured and accepted
  - change hook source without a separate execution approval
- Record completion:
  - update this record when a stage starts, lands or the threshold is decided
- Related records:
  - `.lazy-harness/spec/platform/monitoring-core.md`
  - `.lazy-harness/spec/platform/module-composition.md`

## 사용자 방향 (2026-11-10)

사용자: “read-debt 같은 개념을 그냥 뒤에 모니터링이 보고 바로 검색을 하거나 주입해주거나 저장하고 알아서 관리되게 할 생각”. 기존 측정(모니터링 SDD: U1 references는 합성 100%, 실제 세션 약 57% 탐지, 사용자가 정한 역할은 비차단 보조 알림)을 근거로 단계적 전환을 제안했고 사용자가 “그렇게 하자 우선은”으로 골랐다. 실행 승인은 아니다.

| 단계 | 내용 | 상태 |
| --- | --- | --- |
| 1 | 막기 → 알리기: 아래 차단 훅을 경고로 바꾼다. 놓친 사실은 기록에 남긴다 | 대상 목록 작성, 실행 승인 전 |
| 2 | 모니터링이 관련 기록을 찾아 넣어 주고(references), 규칙 어김을 알리고(rule-steering), 저장할 것을 정리한다(memory) | 모니터링 세션의 모듈 작업과 연결 규약 확정 뒤 |
| 3 | 실제 세션 탐지율이 기준(예: 90%, 미확정)을 넘으면 훅을 없애고 모니터링을 주된 경로로 한다 | 기준 미확정 |

## 단계 1 대상 훅 (source 위치 확인, origin/main 기준)

| 훅 | 지금 동작 | 위치 |
| --- | --- | --- |
| read-debt not armed | 턴 시작 알림이 켜지지 않으면(자동 이벤트 턴 포함) 도구 실행을 막는다 | `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` (`readDebtNotArmedReason`, tool guard) |
| search-debt gate | map/read 증거 없이 행동하면 막는다 | 같은 tool guard의 lifecycle reason 경로(정확한 생성 함수는 단계 1 착수 때 확인) |
| Project rule placement STOP | 규칙·정정으로 보이는 응답 뒤 판정을 요구하며 멈춘다 | lifecycle hook(`.lazy-harness/scripts/lifecycle-parity-runner.py` 보호 시험) |
| 5d-3 Affected Test Gate | 변경 파일 옆에 시험이 없으면 멈추고 질문한다 | `.lazy-harness/scripts/affected-test-runner.ts`, `index.ts` |
| capture-unverified 알림 | 기록 판단을 매 턴 확인시키는 알림 | `packages/lazy-harness-pi/extensions/lazy-harness/capture-evidence.ts` |

- 시험 자동 실행 제외(사용자 결정 2026-11-10, “머지하기전에 하네스 테스트 돌리는것도 다 훅에서 빼버리고 권장을 하던가 하자”): 훅이 시험을 자동으로 돌리거나 시험 때문에 멈추게 하지 않는다. 대상은 응답 종료 lifecycle(`.lazy-harness/hooks/lifecycle/on-response-completed.sh`)이 부르는 `helpers/check-affected-tests.sh`(5d-3 Affected Test Gate, `affected-test-runner.ts`)와 `helpers/check-tdd-cross-verify.sh`(5d-3 TDD Cross-Verify Gate)다. 대신 머지 전 `lazy check`·`lazy test`/`lazy validate`는 권장 안내로 바꾸고, `.lazy-harness/AGENTS.md` §4의 검증 의무 문구와 record-lint “framework=commit gate” 문구도 권장으로 맞춘다. Git hook 자동 실행은 PR #14(`d81f304`)에서 이미 없앴고 CI workflow는 없다.
- 대상이 아닌 것: Reader boundary 차단(Reader 하위 agent의 예산·모델 보호)은 Reader 자신에게만 적용되므로 유지 후보다.
- 근거: 2026-11-10 한 세션에서 위 훅이 반복해서 도구 실행을 막거나 멈췄다(자동 이벤트 턴의 셸 차단, map 재접지 요구, Rule placement STOP 반복).

## Implementation map

- Status: `partial` (1단계 구현, worktree `../lazy-harness.hooks-advisory`, 브랜치 `work/hooks-advisory`, 미커밋)
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh`: `check-overview-batch-order.py`·`check-read-debt-permit.py`·`check-search-performed.sh`를 체인에서 뺐다. `check-destructive-command.py`·`check-project-command-boundary.py` 안전 검사만 차단한다.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh`: `check-tdd-cross-verify.sh`·`check-affected-tests.sh`를 helper 루프에서 뺐다(시험 자동 실행 없음).
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`: read-debt 미무장 차단 제거. capture 판정은 `appendEntry` 런타임 기록으로만 남기고 대화 메시지·출력 알림을 보내지 않는다. 응답 종료 helper 출력은 후속 턴(`sendUserMessage followUp`) 대신 UI 알림(`ctx.ui.notify`)·headless는 stderr 알림만 한다. advisory 후속 턴 카운터(`lastAdvisoryByRoot`, `MAX_ADVISORY_*`)를 지웠다.
  - `.lazy-harness/AGENTS.md` §4와 record-lint 문구: hook은 막지 않고 시험을 자동 실행하지 않으며 머지 전 `lazy check`/`lazy test`는 권장.
- 유지한 것: 파괴적 명령·프로젝트 경계 안전 차단, Reader 하위 agent 예산·join 보호, 턴 시작 read-debt 안내.
- ADR: framework-global 동작 변경이므로 ADR 0016 개정 또는 새 ADR을 PR #22(ADR 0063) 머지 뒤 번호를 정해 추가한다.
- Key symbols: `readDebtNotArmedReason` (index.ts) — 위치만 확인.
- Tests / protection: 단계 1 착수 때 `self-test.py`의 read-debt·search-debt·rule placement·affected test 시험을 함께 고친다.

## Rule placement

- Rule: 차단 훅은 막기→알리기, 모니터링 검색·주입·저장, 측정된 기준 통과 후 제거 순서로 모니터링에 넘긴다.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/hook-to-monitoring-transition.md`
- Why not AGENTS.md: 진행 중인 전환 계획이다. 각 단계가 끝나면 해당 SDD·ADR에 반영한다.
- Why not local notes: 모니터링 세션과 함께 따르는 공유 계획이다.
- Confirmation: user-confirmed (direction); execution not approved
