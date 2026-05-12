# ADR 0021 — Experimental Branch + Extract Strategy

- Status: Accepted
- Date: 2026-05-12
- Trigger: 사용자 catch — git rm 사고 위험, `.lazy-harness/`가 medivance 본 작업 branch에 섞이는 문제, 미래 별도 repo extract 필요
- Related: ADR 0009 (Husky Integration), ADR 0013 (Framework External Dependency Invariant), ADR 0010 (Plan Status Hygiene)

## Context

Lazy-Harness는 medivance 제품 코드와 같은 repository 안에서 자라고 있지만 성격은 다르다.

- medivance 제품 branch (`dev-ian`, `dev`, `test`, `main`, feature branches)는 제품 코드 변경을 담는다.
- `.lazy-harness/`는 framework 자체의 실험/진화 산출물이다.
- 일반 제품 branch에 `.lazy-harness/`가 tracked되면 배포 branch에 framework 내부 문서/상태/로그가 누출될 수 있다.
- 반대로 framework 작업 중 `git rm`을 잘못 쓰면 disk 파일까지 사라질 수 있다.

따라서 framework 작업과 제품 작업을 branch 수준에서 분리해야 한다.

## Decision

`.lazy-harness/` 작업은 **`experimental/lazy-harness` branch 전용**으로 한다.

| Branch | `.lazy-harness/` policy |
|---|---|
| `experimental/lazy-harness` | commit / push 허용 |
| `dev-ian`, `dev`, `test`, `main`, `feat/*`, `fix/*` | tracked 0 유지, commit / push 차단 |

### Cleanup rule

다른 branch에 `.lazy-harness/`가 잘못 staged/tracked되면:

```bash
git rm --cached <path>
```

만 사용한다. `git rm <path>`는 disk 파일까지 삭제하므로 금지한다.

### Hook policy

- `pre-commit-guard.sh`는 `experimental/lazy-harness`에서는 `.lazy-harness/` 변경을 허용한다.
- 그 외 branch에서는 `.lazy-harness/`, `.jcode/`, legacy framework 경로를 차단한다.
- `pre-push.sh`도 branch-aware여야 하며 `origin/HEAD..HEAD` 같은 기본 branch 기준 diff로 experimental branch를 오탐하면 안 된다.

### Future extract

Lazy-Harness가 충분히 안정되면 별도 repository 또는 package로 extract할 수 있게 유지한다.
현재는 medivance repo 안에 두되 branch와 hook으로 격리한다.

## Consequences

### Positive

- 제품 branch와 framework branch의 책임이 명확해진다.
- framework 작업을 정상 commit/push하면서도 제품 branch 누출을 막는다.
- future extract를 위한 portable boundary가 생긴다.

### Negative

- 작업자는 항상 현재 branch를 확인해야 한다.
- hook이 branch-aware가 아니면 정상 framework 작업을 막을 수 있다.
- handoff 문서가 stale하면 잘못된 worktree에서 작업할 위험이 있다.

## Verification

- L0: ADR 문서 생성
- L1: `.lazy-harness/README.md`, `handoff/00-current-state.md`, `planning/phase-5-plan.xml`가 ADR 0021을 참조
- L2: `pre-commit-guard.sh`가 `experimental/lazy-harness` branch 예외를 가진다
- L2: `pre-push.sh`가 `origin/HEAD..HEAD` 대신 branch-aware range를 사용한다
- L3: non-experimental branch에서 `.lazy-harness/` staged 시 차단되는지 검증 예정
- L4: future extract 시 별도 repo로 옮겨도 boundary가 유지되는지 검증 예정
