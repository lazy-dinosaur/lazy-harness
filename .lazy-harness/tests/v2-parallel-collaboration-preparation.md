# TDD — 병렬 협업 비교01 준비

## Rule digest

- Status: advisory
- Layer: TDD
- Scope: host-project
- Aliases:
  - parallel collaboration preparation
  - 병렬 협업 준비
- Applies when: 동일 담당 분할의 문서형 A와 문서+지속카드 B 협업 비교01 준비물을 검사할 때.
- Must: 초기와 미래 요구/정답/채점을 분리한다. 유한 fixture 검사를 실제 참가자·병렬 협업·권한 집행 성공으로 승격하지 않는다. 기존 연구 source/artifacts와 Planning/graph는 이 준비 writer가 수정하지 않는다.

## 승인 경계와 보호

[Planning 최신 준비 승인](../planning/v2-recording-method-comparison-plan.md)의 독립 병렬·의존 순차와 같은 업무 분할을 구현한 준비 패키지다. 참가자/provider 호출, credential 접근, 설치/전역 설정/SDK 수정, worktree/복사/삭제/commit은 승인되지 않았으며 수행하지 않는다. 모델·예산·실행 장치·반복은 부모/사용자 소유다.

supervisor 확인으로 최소 계약을 구체화했다: plain dict retries, 정확한 int0..3, phase1 누락/무효 default2, owner1 resolve_retries와 owner2 execute/결과 dict. **phase1에는 미래 ConfigError/config_error 의무를 주지 않는다.** phase2 동일 전달 때 새 읽기전용 shared.py와 오류/operation0회 계약을 공개하여 두 책임의 만남을 보존한다. bool/None/문자/float/범위 밖 값은 무효 시험 대상이며 config dict 밖/operation 예외·non-bool은 제외한다.

## 검사 전략

명령: `python3 -B experiments/v2-parallel-collaboration-01/evaluator/test_preparation.py`. 결과는 새 package `preparation-result.json` 및 [준비 evidence](../evidence/v2-parallel-collaboration-preparation-01.md)에 수렴한다. 8 grouped tests: visibility/선언 파일 전수 대조, AST starter/ownership, private 정상2단계(각96), wrong10개 배제, literal Python starter3 예상 NotImplementedError, 공개 실제 내용3+4 reference 검사, 금지 수정 digest-map4사례/15파일 해시, 혼합 버전2개 배제. 세부 유한 횟수는 결과 JSON과 대조한다.

실패 보호: bool/int, 누락/무효·None 혼동, 최초/재시도 off-by-one, 성공 후 계속 호출, 오류 삼킴/누출, validation 전 operation, v2에서 stale v1. 구조 검사는 책임 의미/정당한 대기/거짓 팀 완료/부모 재설명을 판단하지 않는다. evaluator/GRADING.md의 사람 검수로 따로 판정한다. 자기 검사와 두 구현 통합 결과도 분리한다.

기존 FIFO/symlink/binary retained artifacts 위험과 명시 금지 때문에 `lazy check`/`lazy validate --plan standard`는 deferred. 원래 test-strategy의 broad checkpoint를 green으로 주장하지 않는다. 명시 regular15개만 bounded/no-follow 읽고 사본은 만들지 않는다. 자동 편집 진단은 별도이며 offline checkpoint 결과가 아니다.

## SDD/BDD/SSOT/DDD completeness

| Layer | 판단 |
|---|---|
| SDD | 실험-local 최소 인터페이스/visibility 준비 delta는 이 TDD와 common/TASK.md·evaluator/PHASE2.md에 한정; framework API 변경 없음, 별도 canonical SDD 승격 없음 |
| BDD | 예정 병렬 담당·동일 staged 변경 절차, 실제 참가자 flow 미실행; 제품 BDD 독립 delta 없음 |
| SSOT | 명시 export/쓰기 경계는 실험-local manifest 소유; runtime/config/credential/전역 규칙 독립 delta 없음 |
| DDD | 작은 fake retry 과제만 사용; 제품 도메인 정의 독립 delta 없음 |

## Discovery capture / all7

DDD=no independent product delta; SDD=experiment-local preparation above; BDD=proposed flow only; TDD=this primary records finite preparation protections; ADR=no new architecture adoption; SSOT=experiment-local manifest only; Planning=부모 소유 최신 승인 재사용, 실행 장치·모델·예산·guided migration 후보를 부모에게 반환. 부모가 Planning/graph/index 갱신을 판단하며 이 writer는 변경하지 않는다. Rule placement: 새 global operating rule이나 개인 memory 작성 없음.

## Implementation map

- `experiments/v2-parallel-collaboration-01/common/{TASK.md,settings.py,runner.py,test_public.py}`: 같은 phase1 요구, resolve_retries/execute 미완성 starter, PublicTests3검사.
- `conditions/{A.md,B.md}`: 공통 의무 대비 카드 추가만 차이.
- `evaluator/{manifest.json,PHASE2.md,shared.py,test_change.py}`: export/ownership, 동일 change 전달, ConfigError, ChangeTests1검사.
- `evaluator/grade.py#grade,#prohibited_changes`: 독립 expected CASES16 ×6 판정 및 finite digest 비교.
- `evaluator/reference.py#resolver,#executor,#wrong_fixtures`: 정상/잘못된 유한 local fixtures; 초기 export 금지.
- `evaluator/test_preparation.py#read_regular,#load,#public_suite,#PreparationTests`: actual package source 로딩→구조/finite 기능 검사→exclusive result. 15개 명시 파일과 함수는 작성 source를 확인했으며 추정 symbol 아님.
- `README.md`/`evaluator/GRADING.md`: barrier/원문 relay/승인·read 동등성의 미구현 실행 요건 및 사람 의미 채점.
- Read-only feasibility: `experiments/v2-isolated-execution-01/live-controller.mjs#ROWS,#runComparison,#approveScope`, `CHAT-APPROVAL.md`; old 순차 controller는 새 병렬 지원의 증거가 아님.
- Cross-layer: [Planning](../planning/v2-recording-method-comparison-plan.md), [test strategy](test-strategy.xml), [code organization](../spec/platform/code-organization-profile.md), [record policy](../spec/platform/record-write-update-policy.md).

Observe-only code organization: 새 source는 starter 두 책임, finite grader, reference, prep checkpoint로 좁혀져 있으며 중복 실행 권한/framework abstraction을 추가하지 않았다. 파일 길이 기준 분할/기존 코드 정돈 없음. source-work capability와 policy 모두 recommend/advisory로 확인했다. policy 첫 잘못된 --intent 호출은 실패 보존 후 부모 허용하에 --applies-to=creating_source_file로 수정 해소했다.
