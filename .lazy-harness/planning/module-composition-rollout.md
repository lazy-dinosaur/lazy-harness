# Planning — 모듈 연결 계약 적용 계획

Status: documentation landed on branch `docs/module-composition-contract`; implementation out of scope — 사용자 정정(2026-11-10): “우리는 모듈과 어떤 식으로 계약할지만 정해서 문서화하는 게 목표다.” 이 세션의 범위는 연결 계약의 정의·문서화이며, 구현(어댑터 코드, 지식 RPC 서버·client, 연결)은 범위 밖이다. 범위 밖으로 만든 어댑터 초안 worktree `work/module-composition`은 사용자 선택으로 삭제했다. 이전의 “진행해줘봐”를 구현 승인으로 해석한 것은 잘못이었다.
Layer: Planning

## Rule digest

- Status: active
- Layer: Planning
- Scope: transient-plan
- Aliases:
  - 모듈 연결 적용
  - 공통 Fabric 어댑터
  - module composition rollout
- Applies when:
  - implementing the connection contract of `.lazy-harness/spec/platform/module-composition.md`
  - deciding who builds the common Fabric adapter, module manifests or module attachments
- Must:
  - follow the approved order: common Fabric adapter -> monitoring attachment -> knowledge manifest/RPC/TS client and attachment -> remove the old monitoring copy -> ADR 0063
  - work in a separate worktree based on origin/main, not in the shared main checkout
  - coordinate with the monitoring session (LH-1) and knowledge session (LH-4) before touching their lanes
- Must not:
  - edit monitoring records, PR #15/#16 files or the knowledge repository without the owner's agreement
  - add a pi-fabric dependency to any module repository
- Record completion:
  - update this record as each step lands or the plan changes
- Related records:
  - `.lazy-harness/spec/platform/module-composition.md`
  - `.lazy-harness/ssot/project-identity.md`

## 승인된 순서

사용자가 native 선택으로 승인했다. 공통 Fabric 어댑터는 이 세션(LH-5)이 만들고 모니터링 세션(LH-1)이 사용한다.

| 단계 | 내용 | 담당 | 상태 |
| --- | --- | --- | --- |
| 1 | 공통 Fabric 연결 방식 — SDD §6.7에 계약으로 문서화(구현은 모니터링 붙이기 PR에서) | 문서: LH-5 / 구현: 붙이기 PR | 문서화 완료, 초안 코드 삭제 |
| 2 | 모니터링 연결과 main의 옛 `packages/lazy-harness-pi/monitoring/` 정리 | LH-1이 자기 결정과 일정으로 진행(이 세션의 작업 아님) | LH-1 소관 |
| 3 | 지식 모듈 정렬(선언 파일, JSON-RPC 서버, TS client, 결과 형식 변환) | 지식 세션(LH-4) 자기 저장소에서 | 지식 세션 소관 |
| 5 | ADR 0063(역할·연결 계약 결정과 이유) | LH-5 | 작성 완료(`docs/module-composition-contract`); origin/main에서 PR #16 `2bb103f`·#17 `e0048e4` 머지와 ADR 0001–0062 연속을 직접 확인 |

사용자 정정: “모니터링은 알아서 진행하고 있는 거잖아. 우린 다른 거 하고 있는데 뭐가 문제인 거지.” 모니터링 연결·옛 복사본 정리는 LH-1 세션의 작업이고 그 세션의 결정(main에는 아직 submodule 포함만)을 따른다. 이 세션은 공통 Fabric 어댑터와 지식 초안을 진행하며, 두 세션 결정 사이에 이 세션이 해결할 충돌은 없다. 앞서 이 계획에 적은 ‘충돌(미해결)’은 이 정정으로 해소됐다.
세션 매니저는 이 계획 뒤에 별도 작업으로 진행한다.

## 확인한 사실

- 설치본 `pi-fabric/dist/protocol.d.ts`가 `FABRIC_PROGRAM_RUN_EVENT = "pi-fabric:program:run:v1"`을 export한다. 요청은 저장된 프로그램 `ref` 또는 TypeScript `code`(최대 65,536자)와 JSON `input`(최대 64 KiB), `signal`, 한 번만 불리는 `reply`를 갖는다. 응답은 `{ok:true, program, value, logs}` 또는 `{ok:false, error}`이다. 다른 확장이 Fabric 내부를 import하지 않고 설치된 Fabric을 쓰는 공개 경로 후보다.
- Fabric이 이 이벤트를 실제로 처리하는 조건(권한·승인·agents provider 사용 가능 여부)과 Fabric이 없을 때의 동작은 구현 전에 확인해야 한다.
- lazy-harness PR #16(모니터링 기록)과 #17(동기화)은 main에 머지됐다(`2bb103f`, `e0048e4`). #15(모니터링 thin consumer)는 draft 보류다.

## Implementation map

- Status: `planned` (문서화만; 코드 없음)
- Primary files: `.lazy-harness/spec/platform/module-composition.md`(연결 규약, §6.1 선언 필드·§6.3 보류·§6.7 Fabric 연결 방식), `.lazy-harness/decisions/0063-module-composition-contract.md`, `.lazy-harness/ssot/project-identity.md`(역할·모듈 조립 섹션).
- Key symbols: none.
- 범위 밖 초안 이력: 공통 Fabric 어댑터 초안(`packages/lazy-harness-pi/fabric/program-run.ts`와 시험 8개)을 worktree `work/module-composition`에 만들었다가 사용자 정정 뒤 사용자 선택으로 worktree와 브랜치를 삭제했다. 그 과정의 변경 검사 질문 Q-4760a2cd4ab56311은 B(기존 tests/ 경로 인정)로 닫혔다. 대응표는 SDD §6.7에 계약으로만 남았다.
- Tests / protection: 없음. 모듈 적합성 시험과 Fabric 연결 시험은 붙이기 작업에서 만든다.
- 문서 브랜치 검증(2026-11-10): `lazy test` 92개 통과(skipped 0), `lazy check` 7개 파일 통과, `record-lint` 0건. 처음 실패한 6개 검사의 원인은 두 가지였다. (1) 새 ADR을 추가하면서 `.lazy-harness/README.md`와 `handoff/00-current-state.md`의 ADR 개수 표기를 고치지 않았다. (2) 새 worktree에 의존성이 설치되지 않았다. `node_modules`는 git이 무시하지 않는 파일이라, `lazy check`는 `node_modules`가 없을 때, `lazy test`는 `bun install --frozen-lockfile` 뒤에 따로 돌려 확인했다.
## 동시 세션 조율 결과

- LH-1(모니터링): lazy-harness 쪽 Fabric 구현은 어디에도 없다. PR #15(draft, `feat/monitoring-thin-consumer`)와 커밋 전 브랜치 `feat/monitoring-submodule`(worktree `lazy-harness.submodule`)가 있다. 피해야 할 파일: `.gitmodules`, `vendor/lazy-harness-monitoring`, `vendor/README.md`, 루트 `package.json` workspaces와 `bun.lock`의 monitoring 항목, `packages/lazy-harness-pi/extensions/lazy-harness/monitoring/**`, `.lazy-harness/spec/platform/monitoring-thin-consumer.md`. knowledge submodule을 추가할 때 `.gitmodules` 순서를 맞춘다. 모니터링 `lazy-harness.module.json`은 LH-1이 추가하며 v1 필드 정의를 요청했다.
- 충돌(해소됨): LH-1 세션의 “lazy-harness main에는 아직 monitoring을 붙이지 않고 submodule 포함만 둔다” 결정은 LH-1 작업의 순서다. 사용자가 “모니터링은 알아서 진행하고 있고 우린 다른 걸 한다”고 정정해, 모니터링 연결·옛 복사본 정리를 LH-1 소관으로 옮겼고 이 세션과의 충돌은 없다.
- LH-1 순서 전달(2026-11-10, LH-1 세션 사용자 결정): monitoring은 “아직 붙이지 않음” 유지. 1) PR #16 머지 2) monitoring 연결 계약 확정(#14 정정 + `lazy-harness.module.json` 추가, #14·#11 머지) 3) 확정 커밋으로 submodule 포함 PR 4) 붙이기는 나중에 사용자 결정으로 PR #15 + 공통 Fabric 어댑터 + 옛 monitoring 복사본 정리를 한 PR로. LH-1은 매니페스트 작성을 위해 `lazy-harness-module/v1` 필드 정의를 요청했다. LH-5는 SDD §6.1의 현재 문구를 “v1 초안, 필수/선택 미확정”으로 전달했다. PR #16이 머지되면 LH-1이 알리고 그 뒤 ADR 0063을 진행할 수 있다.
- 사용자 지시(2026-11-10, LH-1·LH-4에 전달함): 모듈 세션들은 연결 규약이 정해지기 전에 모듈을 만들기 시작했다. lazy-harness main은 이제 연결 규약을 정하는 단계다. 그래서 모듈 저장소 작업은 각 모듈 세션이 맡고, 이 세션에 맡기지 않는다. LH-5는 지식 선언 파일·RPC 서버·TS client 초안 PR과 공통 Fabric 어댑터를 포함한 붙이기 작업을 맡지 않는다. LH-5는 main에서 연결 규약을 정의하고 문서화하는 일만 하며, 규약이 확정되면 커밋을 알린다.
- LH-1 회신(2026-11-10): LH-1은 LH-5에게 했던 요청(스키마 문단 전달, PR #16 머지 뒤 ADR 0063 순서 맞추기, Fabric 어댑터 조율)을 모두 거뒀다. 연결 규약이 main에 확정되기 전에는 monitoring의 규약 맞춤 작업(매니페스트, 계약 머지)을 하지 않고, 확정되면 커밋만 알려 달라고 했다. LH-1이 lazy-harness main에 올리는 것은 이미 승인된 monitoring 결정 기록 PR(#16, 동기화 PR)뿐이며, 이 PR은 연결 규약 문서를 건드리지 않는다.
- LH-4(지식): 지식 저장소의 선언 파일·RPC 서버·TS client는 아직 LH-4 담당이 아니며 LH-5가 초안 PR을 내도 충돌이 없다. 지식 `master`는 `d11eecf`, 열린 브랜치·PR은 없다. 조건: `packages/core` 배치 로직(`place_write.py`, `stagewise.py`)은 건드리지 않고 새 파일(루트 선언, 서버 진입점, TS client)로만 만든다. project-identity는 현재 수정하지 않으며 LH-5 섹션을 유지한다.
- LH-4가 알려준 지식 모듈 결과의 공통 형식 변환(core 변경 없이 RPC 서버 층에서): writer/worker 역할 호출은 `check_role_result`를 통과한 dict와 'done' ledger 행이면 확실한 완료, 결과가 불확실한 요청은 재전송하지 않는 불확실한 실패. 배치에서 자리를 찾지 못하면 `PlacementHeld(reason, trace)`로 HOLD(확실한 실패 아님). stage_run 결과는 'completed', 'DRYRUN: …', 상한 중단. 판정은 `host_defaults.install_judgement_http`, 임베딩은 `install_embedding_transport`로 연결층이 끼운다. LH-4는 예전에 LH-1에게 말한 “PYTHONPATH로 연결”을 철회했다.
- LH-4 추가 전달(2026-11-10): LH-4 세션의 사용자가 지식 저장소의 선언 파일·JSON-RPC 서버·TS client 초안 PR을 LH-5가 내고 LH-4가 검토하도록 정했다. 조건은 새 파일만 추가하고 `packages/core` 배치 로직은 건드리지 않는 것이다. 다만 이 세션의 사용자는 범위를 계약 정의·문서화로 한정했으므로, 이 세션 사용자의 승인 전에는 PR을 내지 않는다. 독립 검수에서 지식 모듈의 Jev 판정 경로(`capture_audit.request_answers`, `worker_tools.make_ask`)가 불확실한 요청을 자동으로 다시 보낼 수 있다는 지적이 나왔고 LH-4가 고칠 예정이다. 그러므로 계약 문서와 RPC 서버는 이 경로가 안전하다고 가정하지 않는다.
- 공통 결과 형식에 HOLD 같은 ‘보류’ 상태를 어떻게 담을지(완료의 value로 표현할지 별도 status로 둘지)는 아직 정하지 않았다.


## Rule placement

- Rule: 연결 계약 적용은 위 순서와 담당으로 진행하고, 다른 세션의 작업 영역은 조율 후에만 건드린다.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/module-composition-rollout.md`
- Why not AGENTS.md: 특정 작업의 진행 계획이다.
- Why not local notes: 여러 세션이 함께 따르는 공유 계획이다.
- Confirmation: user-confirmed
