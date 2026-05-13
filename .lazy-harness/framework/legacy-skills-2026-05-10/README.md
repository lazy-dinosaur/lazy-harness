# Legacy Skills (2026-05-10 snapshot)

## 목적

새 `lazy-init` 구현 시 옛 `harness-init` (988 줄 bash) 의 검증된 패턴을 참고하기 위한 archive.

dogfooding 시작 전 dev-ian worktree 에 박혀있던 5월 10일 버전을 보존.

## 보존된 skill

| Skill          | 줄수 | 핵심                                                         |
| -------------- | ---- | ------------------------------------------------------------ |
| harness-init   | 988  | 30 container mkdir + README + 16 cross-layer map XML + git/info/exclude + pre-commit hook |
| harness-doctor | 729  | Unified Result Schema 출력, 폴더/파일 health audit             |
| harness-update | 366  | auto-backup + auto-rollback, framework-contract sync          |

## 옛 framework 와 현재 framework 의 차이 (왜 그대로 못 쓰나)

| 항목                                       | 옛 (5월 10일)         | 현재 (5월 13일)                                 |
| ------------------------------------------ | --------------------- | ----------------------------------------------- |
| framework-contract                         | v1.1 (18 principle)   | v1.4+ (23 principle)                            |
| AGENTS.md (얇은 grammar)                   | ❌ 없음               | ✅ 57줄 (ADR 0024)                              |
| `triggers/`, `state/`                      | ❌ 없음               | ✅ N1/N2.5 가 추가                              |
| `scripts/` 본체 (reference-resolver 등)    | ❌ 빈 폴더 + README   | ✅ 12+ TS/Python 스크립트                       |
| `hooks/lifecycle/` (on-tool-execute-before) | ❌ 없음               | ✅ N2.5 force-gate hook                         |
| Framework 본체 자동 sync                   | ❌ 사용자가 직접 박음 | ✅ 새 lazy-init 이 본 worktree 에서 자동 rsync |

## 재사용 가능한 부분 (새 lazy-init 작성 시 참고)

1. `mkdir_p`, `write_file`, `log_action` bash helper
2. `CONTAINERS=(...)` 배열 패턴 (단, 30 → 38 container 로 확장 필요)
3. `place_readme()` , `place_map()` 패턴
4. `--dry-run`, `--force`, `--gitignore`, `--tier` 옵션 처리
5. `.git/info/exclude` 자동 박기
6. pre-commit hook delegate 박기

## 버려야 할 부분

1. `framework-contract.md` 가 single source 라는 옛 가정 (이젠 record 가 vocabulary, AGENTS.md 가 grammar)
2. "Principle #N" 참조 (N 번호 바뀜)
3. 빈 `scripts/` , 빈 `hooks/` 만들고 사용자에게 가져오라는 메시지 (이젠 자동 sync)

## 참고

- 새 lazy-init 설계: ADR 0025
- 본 archive 가 적용된 cycle: `retrospective/cycles/pre-dogfooding-state.md`
