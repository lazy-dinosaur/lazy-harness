# D-2026-05-10-003 — Principle 18: Recovery Path

## Status

Accepted (2026-05-10)

## Rule digest

- Status: needs-review
- Layer: ADR
- Scope: framework-global
- Applies when:
  - the framework or its hooks are damaged or malfunctioning, or trust is lost
  - planning backups or recovery for `.lazy-harness`
- Must:
  - follow the matching recovery level R1–R4 (container damage, hook malfunction, trust loss, catastrophic)
  - keep backups gitignored and freeze immediately on R3 trust loss
  - manually record unreflected work on R4 catastrophic damage
- Must not:
  - push backups to git, since a leaked backup is a security breach
- Record completion:
  - changes to recovery levels or backup strategy update this ADR and `.lazy-harness/framework/framework-contract.md`
- Related records:
  - `.lazy-harness/framework/framework-contract.md`
  - `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`

## Context

lazy-harness 가 시간 갈수록 medivance 작업의 핵심 의존성이 됨.
framework 자체가 깨졌을 때의 회복 절차가 framework-contract 에 명세 없으면:
- backup 정책 즉흥적 → 데이터 유실 위험
- 깨진 후 어디까지 rollback 할지 결정 못함
- AI 자율성 정책 (#5 self-loop) 과 충돌 시 대응 모름
- 점진적 부패 (silent corruption) 방지 못함

특히 우리 framework 는 self-loop 가 spec 수정 금지 같은 hard rule 을 가지므로,
framework 자체가 깨지면 AI 가 어떻게 행동할지 명세돼 있어야 함.

## Decision

**Principle 18 — Recovery Path** 를 framework-contract 에 추가.

4 단계 recovery level:

```
R1 (Container Damage)     — 단일 컨테이너 손상, 다른 부분 정상
R2 (Hook Malfunction)     — hook 오작동 반복
R3 (Trust Loss)           — 사람이 framework 신뢰 잃음
R4 (Catastrophic)         — .lazy-harness/ 자체 손상
```

각 level 마다:
- Trigger (감지 조건)
- Detection (자동 감지 방법)
- Fallback (즉시 동작)
- Recovery (회복 절차)

Backup 전략:
- Weekly snapshot (자동, .lazy-harness-backup/)
- Pre-major-change snapshot (각 milestone 시작 전)
- Offsite copy (월 1 회 권장)

## Consequences

### Positive
- framework 장기 사용 가능 (1 년+ 의존성 됐을 때 안전망)
- 깨졌을 때 panic 안 함 — 명세된 절차 따름
- backup 데이터로 진짜 복구 가능 (특히 R4)
- post-mortem ADR 의무 → 재발 방지

### Negative / Trade-offs
- backup 디스크 사용량 (.lazy-harness 크기 × 4 weeks rolling + milestone 영구)
- backup 자동화 구현 비용 (M2 lifecycle hook 의 일부)
- offsite copy 는 사용자 수동 작업 필요

### Mitigations
- backup 은 .gitignored (git push 금지) — 보안 보장
- weekly snapshot 자동 정리 (4 weeks 이상 자동 삭제)
- harness-doctor 가 backup 상태 검증 (M1 milestone)

## Hard Rules

- backup 은 .gitignored (보안 위반 시 backup 자체가 leak)
- R3 발생 시 freeze 즉시 (debate 불가, 신뢰 회복 우선)
- R4 발생 시 미반영 작업 manual 기록 의무 (영원히 남는 데이터 유실 방지)

## Related

- framework-contract.md Principle 18
- D-2026-05-10-001 (Principle 0 — recovery 도 사람-AI 보완의 일부)
- D-2026-05-10-002 (Principle 17 — conflict resolution 결정도 backup 대상)
- M1 (harness-doctor 에 backup 검증 포함)
- M2 (lifecycle hook 에 weekly snapshot 자동화)

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/framework/framework-contract.md` — current Principle 18 Recovery Path text.
  - `.lazy-harness/hooks/pre-commit-guard.sh` and `.lazy-harness/hooks/pre-push.sh` — current git-action locks and validation fallback gates.
- Key symbols:
  - `acquire_worktree_lock` (`pre-commit-guard.sh`, `pre-push.sh`) — prevents concurrent git-action corruption.
- Flow:
  1. Recovery Path is documented in framework-contract.
  2. Current active hooks include lock/fallback behavior for git actions.
  3. Weekly snapshot automation referenced by this ADR is not present in current active hooks.
- Tests / protection:
  - No current self-test verifies weekly snapshot/recovery-level automation; keep needs-review.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0016-lifecycle-hook-strategy.md`
- Machine index:
  - graph ids: `kg_adr0003_recovery_contract`, `kg_adr0003_weekly_snapshot_missing`
  - generated index key: `pending`
