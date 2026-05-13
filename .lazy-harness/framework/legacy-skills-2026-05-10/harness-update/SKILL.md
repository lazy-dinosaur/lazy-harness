---
name: harness-update
description: Sync framework-contract.md from canonical source. Supports dry-run, rollback, version drift detection. Auto-backup before apply, auto-rollback on doctor failure.
allowed-tools: bash, read, write, edit, grep, ls
---

# harness-update

Use this skill to sync `.lazy-harness/framework/framework-contract.md` from a canonical source.

This is the **only** safe way to update framework-contract — it auto-backs up before apply and auto-rolls back if `harness-doctor` fails after.

> **Principle 0 reminder**: 사람도 AI 도 불완전하다. update 는 framework 의 핵심 의지결정 (single source of truth) 을 다루므로 가장 강력한 안전망 (backup + auto-rollback) 이 필요.

## Default behavior

```bash
.jcode/skills/harness-update/scripts/update.sh [--from PATH] [--dry-run] [--rollback] [--target DIR] [--force]
```

## Source priority (auto-detected)

```
1. --from <path>                                  # 명시적 source
2. $LAZY_HARNESS_SOURCE                           # 환경 변수
3. ~/.jcode/framework-contract.md                 # 글로벌 canonical (recommended)
4. ~/.lazy-harness-canonical/framework-contract.md  # offline canonical
```

`--from` 없이 source 가 모두 부재 시 에러 (절대 추측 안 함).

## Modes

### Apply (default)
```bash
update.sh
```
1. source 결정 + 비교
2. 변경 있으면 backup → apply → doctor
3. doctor fail 시 자동 rollback
4. backup path 기록

### Dry-run
```bash
update.sh --dry-run
```
diff 출력만, 실제 변경 X. 5a-6 success criterion.

### Rollback
```bash
update.sh --rollback              # 가장 최근 backup 으로
update.sh --rollback <ISO-date>   # 특정 backup 으로
update.sh --rollback --list       # backup 목록
```
5a-7 success criterion.

## Backup strategy (Principle #18 R1)

```
.lazy-harness-backup/
  <ISO-date>/
    framework-contract.md    # 변경 전 버전
    .meta.json               # source / target / doctor result
```

위치: 프로젝트 루트의 `.lazy-harness-backup/` (gitignored, `.git/info/exclude` 자동 추가).

자동 보관 정책:
- 최근 5 개 유지 (FIFO)
- 7 일 이상 된 것은 archive/ 하위 이동 (M3 에서 구현)

## Version drift detection

framework-contract.md 의 `## Versioning` 섹션을 파싱하여:
- patch: doctor 자동 실행 후 apply
- minor: 변경 사항 출력 + 사용자 확인
- major: 사용자 확인 + ADR draft 강제

## Safety contract

```
- 절대 source 추측 안 함 (없으면 에러)
- 적용 전 항상 backup
- 적용 후 항상 doctor 자동 실행
- doctor fail → 자동 rollback (5초 내)
- rollback 자체 실패 시 사용자에게 명시적 에러
- --force 도 backup 은 절대 skip 안 함
```

## Exit codes

```
0   apply 성공 또는 dry-run 정상 종료
1   apply 실패 (rollback 자동 실행됨)
2   source 없음 또는 doctor 검증 실패
3   rollback 실패 (사람 개입 필요)
```

## Related

- Companion: `harness-init`, `harness-doctor`
- Spec: framework-contract Principle #18 (Recovery), Section 18.2 (Backup)
- Schema: `.lazy-harness/schemas/result.schema.json`
