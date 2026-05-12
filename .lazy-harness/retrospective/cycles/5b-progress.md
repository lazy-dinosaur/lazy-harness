# Phase 5b — Lifecycle Hooks 진행 (재구성)

**Started**: 2026-05-10 15:01 KST
**Status**: in-progress (5b-2 deferred to 5b-2a per ADR 0008)
**Branch**: dev-ian

## 결정된 분할

| Criterion | 상태 | 산출물 |
|---|---|---|
| 5b-1 post-commit logs | ✅ done | `.lazy-harness/hooks/post-commit.sh` (49 줄) |
| 5b-2 AST contract diff | ⏸ deferred (ADR 0008) | `scripts/contract-diff.ts` skeleton only |
| 5b-3 pre-push schema | ✅ done | `.lazy-harness/hooks/pre-push.sh` (66 줄) |
| 5b-4 regression auto | ✅ done (beta) | post-commit 안에 inline + `regression/candidates.jsonl` |
| 5b-5 weekly snapshot | ✅ done | `.lazy-harness/hooks/weekly-snapshot.sh` + cron 안내 |
| 5b-6 1주 실측 | ⏳ passive | logs 누적 측정 — 시간 의존 |
| 5b-7 R2 fallback | ✅ done | `.hooks-disabled` lock 으로 모든 hook bypass |

## Wiring

| Layer | File | 역할 |
|---|---|---|
| git native | `.git/hooks/pre-commit` | safety guard (5a) + husky chain |
| git native | `.git/hooks/post-commit` | → lazy `post-commit.sh` + husky chain |
| git native | `.git/hooks/pre-push` | → lazy `pre-push.sh` + husky chain |
| husky existing | `.husky/commit-msg`, `.husky/prepare-commit-msg` | 기존 — 충돌 없음 |

## 검증 (E2E)

```
post-commit 1 회: actions.jsonl +1, regression/candidates.jsonl +1 (Fix 감지)
pre-push (success): validations.jsonl +1, exit 0
pre-push (.hooks-disabled): "skip" 메시지, exit 0
weekly-snapshot: 548K, ISO-week dir 생성, logs/ excluded
```

## Bug fixes

1. `grep -c` multi-line 결과 → `head -1 | tr -d ' \n'` + null check 추가 (post-commit.sh, pre-push.sh)

## ADR 추가

- **ADR 0008**: AST contract diff deferred (lazy 원칙 — measure first)

## Deferred to 5b-2a

- ts-morph 도입 결정은 medivance 1주 실사용 후 retrospective 에서
- 도입 trigger: contract drift 사고 ≥ 주 3회 또는 명백한 사람 시간 낭비
- 그 전까지 contract-diff.ts 는 skeleton + interface 만 유지

## 다음 단계

1. 1 주 실 commit log 누적 → 5b-6 측정
2. 그 후 5c (Figma adapter) 진입 검토
3. 5b-2 ts-morph 채택 여부는 측정 결과 기준
