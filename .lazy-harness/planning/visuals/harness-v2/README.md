# V2 확정 개념 시각화

## Rule digest
- Status: advisory
- Layer: Planning
- Scope: host-project
- Applies when: 이 대화에서 확인한 V2 구상을 시각 자료로 검토할 때.
- Must: 사용자 확인 방향, 후보, 미정을 구분한다. 실행 토폴로지나 구현 승인을 추정하지 않는다.

## 사용자 확인 범위
- 읽기: 파티션 ID 안의 지식 ID들을 병렬 탐색할 수 있다. 기존 지식과 내 작업의 미소화 원장을 함께 읽어 임시 이해를 만든다.
- 작업 중 임시 기록: 발견, 요구사항, 결정, 정책, 결과를 작업별로 디스크에 남긴다. 모든 기록이 확정된 지식은 아니다.
- 소화·정리: 원장에 기반해 책임 영역에 배분하고 담당 모델 액터가 기존 지식을 수정·통합한다. 무조건 문서 추가가 아니다. 영역 내 순차·배치와 영역 간 병렬의 방향이다.
- 작업 격리는 Git·워크트리에 종속되지 않아야 한다. Git의 통합 상태와 하네스의 지식 반영은 동일하지 않다.
- 지식의 개념·관계와 영역별 규격은 동적으로 발전하는 방향이다.

## 후보와 미정
- 후보: 임베딩, 전문 읽기 에이전트, 기존 레이어 의미를 소화 내부에서 처리.
- 미정: 파티션 생성·분리·통합, 구체 ID와 템플릿, 툴, 원장 단위·발행 시점, 소화 트리거·완료, 권한·일관성, DB·큐·모델·프로세스 배치.
- 도식의 박스와 줄은 개념 관계다. 물리적 서비스 개수나 실행 단계, 즉시 반영을 확정하지 않는다.

## 산출물과 근거
- `three-roles.workflow.json`: 편집 가능한 Archify 입력.
- `index.html`: 자체 포함 인터랙티브 HTML. 읽기/임시 기록/소화 뷰 선택 가능.
- Archify: https://github.com/tt-a1i/archify, 검토용 다운로드 commit `6db72a9aea3d0f67a6a034e41f8a5491476a11c1`.
- `.local/archify-inspect/`는 로컬 도구 사본이며 전역 설치 없음.
- 사용자 요청에 따라 기존 CLI가 종료되고 활성 target 세션이 없음을 확인한 뒤 부모가 인계받음.
- 이전 초안의 명시적 return 경로 교차 실패를 단순한 비교차 개념 배치로 수정하고 한국어로 재작성.
- 고정 Viewer UI와 html lang은 Archify 제한상 영어 fallback. 작성된 설명은 한국어.

## Validation evidence
- Archify deliver: showcase 9/9, errors 0, warnings 0.
- specification SHA-256: `484a7f9f74d360a2bb5e41fd079012fcf1893c4ee03d23fd2896220393a5abbe`.
- artifact SHA-256: `ee71ee6c850a59b2bdb47fead9068af0571c4ddb3221328f5d76020b85e19ca6`.
- Automated browser visual-check: pass. Perceptual image review pending; browser automation is not user approval of the concepts.
- Local receipts: `.local/archify-delivery.json`, `.local/archify-browser.json` (worktree-root-relative).

## Rule placement
- Rule: V2 시각화는 사용자 확인 범위만 확정으로 표현한다.
- Scope: transient-plan
- Primary record: 이 문서.
- Why not AGENTS.md: 실행 규칙 추가가 아닌 시각 자료의 범위 기록이다.
- Why not local notes: 프로젝트 설계 논의의 근거이기 때문이다.
- Confirmation: user-confirmed — 시각화 제작과 이 세션 인계 승인. 런타임 구현 승인은 아니다.

## Discovery capture
- Planning: updated — 확인 범위와 산출물 근거 보존.
- DDD/SDD/BDD/TDD/ADR/SSOT: none — 이번 작업에서 새로운 실행 계약이나 구현을 확정하지 않음.
