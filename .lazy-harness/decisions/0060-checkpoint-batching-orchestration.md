# ADR 0060 — 위임 배포의 checkpoint 일괄화 (왕복 비용 최소화)

Status: accepted (사용자 확정 2026-09-17)
Date: 2026-09-17
Layer: ADR

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases: checkpoint batching, 위임 왕복 비용, 배포 오케스트레이션
- Applies when:
  - subagent worker로 다단계 배포(게시→릴리스→호스트 적용)를 위임할 때
  - coordinator quiet window 등 외부 대기가 필요할 때
- Must:
  - 대기는 작업자 안에서 하지 않는다 — checkpoint에서 즉시 보고하고 종료/보류, 승인은 이벤트(후속 resume/신규 좁은 실행)로 전달
  - quiet window 요청은 게시 단계와 **병렬**로 사전 확보한다
  - 작업자 timeoutMs는 실제 작업량 기준 상향(게이트+클론+의존성 ≈ 25분 → 60분)하거나, 단계를 분할한다
  - checkpoint 수는 목적별 최소(통상 1회: live 적용 직전)로 묶는다
- Must not:
  - 작업자 내부에서 sleep/폴링으로 승인을 기다리게 하지 않는다
  - 하나의 작업자에 게시+대기+적용을 몰아넣어 제한시간 초과·재실행 낭비를 유발하지 않는다
- Surface terms:
  - checkpoint 일괄화
  - 위임 배포 왕복
  - quiet window 사전 확보
- Related: `.lazy-harness/planning/grounding-read-scope-optimization-experiment.md`(측정), Task366/368/371/372 배포 기록

## 배경: 측정된 문제

토큰 비용 표면 검수(2026-09-17)에서 **자식 checkpoint 왕복이 최대 비용 표면**으로 확인됨. 배포 3회 실측:

| 배포 | 패턴 | 결과 |
|---|---|---|
| Task366 | 다수 단계별 checkpoint + 작업자 내 대기 | 정상 완료, 왕복 다수 |
| Task368 | 30분 기본 제한 + 작업자 내 대기(quiet window) | **대기 타임아웃 2회 = 약 340k 토큰 순낭비**, 회복 재실행 추가 |
| Task371/372 | 사전 quiet window 병렬 확보 + 60분 timeoutMs + checkpoint 즉시 보고·이벤트 승인 + 좁은 범위 복구 실행 | **대기 타임아웃 0회**, 체크포인트 1회로 적용 완료 |

구조적 원인 2가지:
1. **대기 위치 오류**: 승인 대기를 작업자 세션 안에서 하면, 자식은 매 턴 누적 컨텍스트(10만+)를 재전송하며 기다리고, 30분 기본 제한에 걸려 그간의 컨텍스트 전체가 폐기됨.
2. **왕복 원가**: 각 checkpoint 왕복마다 자식이 자기 대화 전체를 재전송. 체크포인트 수 자체가 선형 비용.

## 결정

1. **이벤트 기반 승인**: 작업자는 checkpoint에서 상태를 디스크 영수증으로 남기고 즉시 보고后 대기하지 않는다. Parent는 승인 조건(coordinator READY 등)이 성립되면 후속 resume 또는 신규 좁은 범위 실행으로 전달한다. Task372의 phase-5-only resume이 표준 패턴.
2. **병렬 사전 조율**: quiet window 요청은 게시(게이트·PR)와 동시에 발송해, checkpoint 도달 시 승인이 이미 준비되게 한다.
3. **예산 기반 제한시간**: gates(약 9분)+클론+의존성 복사(약 15분)를 포함하는 실행은 timeoutMs ≥ 60분. 또는 게시/적용을 분할 실행한다. 기본 30분은 "대기 없는 순수 작업"에만 유효.
4. **checkpoint 최소화**: 필수 checkpoint는 live 적용 직전 1회. 게시·릴리스·dry-run은 영수증으로事后 검증한다(이미 Task371/372에서 실증).

## 결과

- 예상 효과: 배포 1회당 대기 타임아웃 폐기 컨텍스트 제거(최대 수십만 토큰), checkpoint 왕복 수 최소화.
- 리스크: Parent 조율 부담 증가(quiet window 사전 관리). 이는 intercom 1건으로 해결됨을 Task371/372가 입증.
- 적용 범위: 오케스트레이션 규율이므로 코드 변경 불요. 이 ADR + 배포 실행 템플릿(작업자 task 문구)으로 유지.

## Implementation map

- 이 ADR 자체가 규범 문서. 실행 템플릿(작업자 task에 포함할 "batched single-checkpoint" 문구)은 이 ADR의 결정 1–4를 인용해 조립한다.
- 측정 근거: `.lazy-harness/planning/grounding-read-scope-optimization-experiment.md` §토큰 비용 표면 전면 검수(#11) 및 Task368/371/372 배포 기록(SSOT).
- 보호: 본 ADR의 효과 측정은 다음 실제 배포에서 왕복 수·타임아웃 발생 수로 검증한다.

## Discovery capture

- DDD/BDD/SSOT: 독립 의미 변화 없음(오케스트레이션 절차).
- TDD: 코드 아님 — 회귀 부재. 효과 검증은 운영 측정(다음 배포)으로.
- Planning: 측정 상세는 기존 planning record에 있음(중복 작성 안 함).
