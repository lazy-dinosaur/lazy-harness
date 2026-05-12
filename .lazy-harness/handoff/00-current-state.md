# Lazy-Harness Current State (Live)

> 다음 세션이 즉시 이해하고 진행하기 위한 entry point.

## 즉시 실행할 것 (다음 세션 시작 시)

1. **반드시 새 jcode 창은 이 위치에서 시작**:
   `cd /home/lazydino/dev/medivance.experimental-lazy-harness && jcode`
   (이 worktree 가 없으면 아래 setup 진행)

2. **옛 worktree 정리** (있다면):
   ```bash
   cd /home/lazydino/dev/medivance
   git worktree remove /home/lazydino/dev/medivance.experiment-medivance-harness 2>/dev/null
   ```

3. **새 worktree 생성** (한 번만):
   ```bash
   cd /home/lazydino/dev/medivance
   git worktree add /home/lazydino/dev/medivance.experimental-lazy-harness experimental/lazy-harness
   ```

4. **검증**:
   ```bash
   cd /home/lazydino/dev/medivance.experimental-lazy-harness
   git branch --show-current  # experimental/lazy-harness
   ls .lazy-harness/triggers/  # code-change.ts (1502 lines)
   bun run lazy:test  # XML + JSONL + trigger fixtures
   ```

## 현재 상태 (2026-05-12)

| 항목 | 값 |
|---|---|
| **활성 branch** | `experimental/lazy-harness` |
| **Origin push** | ⚠ local commit/push 확인 필요 (`git status -sb`) |
| **ADRs** | **22** (0001~0022) |
| **Decisions logged** | 23+ entries |
| **5c-1 DDD** | ✅ done (137 candidates, 8/8 pass) |
| **5c-2 SDD + acronym** | ✅ done (724 candidates, 8/8 pass) |
| **5c-3 BDD** | ✅ done (NL + UI heuristic, 8/8 pass) |
| **5c-4 SSOT** | ✅ done (`--layer ssot`, registry suppression, lifecycle helper) |
| **5c-5 Cross-layer map** | ✅ done (`crossLayer.gaps`, integrated ask, exact fixture 검증) |
| **5c-6 Lint/typecheck drift** | ✅ done (`lint-output.ts`, environment vs code drift fixtures) |
| **5c-7 Structured ask** | ✅ done (`structuredAskValidation`, shared validator, `lazy:test` fixture gate) |
| **5c-8 E2E** | ✅ done (referral intake fixture + lint drift + cross-layer + structured ask transcript) |
| **5c-9 Doctor C17** | ✅ done (`lazy:doctor` D06 + `lazy:test` negative fixture) |
| **5c complete** | ✅ 5c-1~5c-9 all done, refactor/package health are post-5c hardening |
| **Framework self-test/doctor** | ✅ `bun run lazy:test` primary gate + `bun run lazy:doctor` full profile (ADR 0022). `.jcode` doctor 는 wrapper/future migration 대상 |
| **code-change.ts** | ~1920 lines (DDD + SDD + acronym + BDD + SSOT + cross-layer map + structured ask validator 통합) |
| **Framework v1.4** | 975 lines, 23 principles |

## Oracle Audit 결과 (2026-05-12)

위치: `.lazy-harness/retrospective/audits/2026-05-12-oracle-audit.md`

### Critical issues 3

1. **SSOT 문서 stale** — registry 가 실제 SSOT 와 mismatch → ✅ `ssot/registry.xml` 생성
2. **XML 파싱 실패** — 일부 XML 깨짐 → ✅ `bun run lazy:test` XML parse 통과
3. **Doctor false-green** — stale/XML/C17 blind spot → ✅ `lazy:test` + framework-owned `lazy:doctor` D01~D06 로 복구

→ 5c-4 SSOT detector 진입 시 동시에 해결.

## 다음 작업 우선순위

상세 계획: `.lazy-harness/plans/5c-remaining-implementation-plan.md`

```
A. Post-5c refactor `code-change.ts` monolith
   - plan: `.lazy-harness/plans/post-5c-refactor-and-package-health.md`
   - 현재 1928+ lines
   - 5c behavior 는 `lazy:test`로 pin 됨

B. Package/dependency health
   - plan: `.lazy-harness/plans/post-5c-refactor-and-package-health.md`
   - `typecheck:node` fails on missing `electron-vite/node` + `@electron-toolkit/tsconfig`
   - 5c-6 classifies this as environment/package health, not code drift

C. 5d Interview Loop 진입 준비
   - TDD cross-verify gate (ADR 0020)
   - 양방향 conflict resolution
```

## Worktree 배치 (최종 상태)

```
/home/lazydino/dev/medivance                       (dev-ian, medivance 본 작업)
/home/lazydino/dev/medivance.experimental-lazy-harness  (★ framework 작업)
/home/lazydino/dev/medivance.feat-*                 (각 feature branch)
```

→ medivance 본 작업과 framework 작업 완전 격리 (ADR 0021).

## Branch 룰 (ADR 0021) — 절대 어기지 말 것

- `.lazy-harness/` 작업은 **`experimental/lazy-harness` branch 전용**
- 다른 branch 에서 `.lazy-harness/` 가 staged 되면 pre-commit-guard 가 차단
- Cleanup 필요 시 `git rm --cached` (disk 유지)
- 절대 `git rm` 사용 안 함 (disk 파일까지 잃음)

## Swarm 위임 시 명세에 항상 포함

```
## 절대 금지
- git commit ❌ (.lazy-harness 는 experimental branch 에서만, ADR 0021)
- 옛 fixture 삭제 ❌
- code-change.ts wipeout ❌ (1502 lines 보존)

## 검증 명령
bun run lazy:test
→ XML/JSONL/DDD/SDD/BDD/SSOT fixture 통과
```
