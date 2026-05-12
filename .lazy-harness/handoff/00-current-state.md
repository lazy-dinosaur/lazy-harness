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
   ls .lazy-harness/triggers/  # code-change.ts (376 lines, orchestration only)
   bun run lazy:test  # XML + JSONL + trigger fixtures
   ```

## 현재 상태 (2026-05-12)

| 항목 | 값 |
|---|---|
| **활성 branch** | `experimental/lazy-harness` |
| **Origin push** | ✅ pushed (`experimental/lazy-harness` clean/synced at `ebee2671`; current edits pending validation) |
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
| **Post-5c detector refactor** | ✅ done (`code-change.ts` 376 lines + `detectors/{ddd,sdd,bdd,ssot}.ts`) |
| **Post-5c package health D07** | ✅ done (`typecheck:node` missing package/config is classified as environment warning, not framework regression) |
| **5c complete** | ✅ 5c-1~5c-9 all done, refactor/package health are post-5c hardening |
| **Framework self-test/doctor** | ✅ `bun run lazy:test` primary gate + `bun run lazy:doctor` full profile D01~D07 (ADR 0022). `.jcode` doctor 는 wrapper/future migration 대상 |
| **code-change.ts** | 376 lines (CLI/orchestration only; detector bodies extracted) |
| **5d Interview Loop** | ✅ done (5d-1~5d-6: collect, answer, TDD, aftershock, hooks, walkthrough depth ≥ 2) |
| **5e host-project pilot** | ✅ complete (inside-out pilot commit `ba162ab1`; command-routing gap found and remediation in progress) |
| **Framework v1.4** | 983 lines, 23 principles |
| **Affected regression test gate** | ✅ done (`lazy:test:affected`, response.completed helper, project test-strategy/package-script routing or structured interview) |

## Oracle Audit 결과 (2026-05-12)

위치: `.lazy-harness/retrospective/audits/2026-05-12-oracle-audit.md`

### Critical issues 3

1. **SSOT 문서 stale** — registry 가 실제 SSOT 와 mismatch → ✅ `ssot/registry.xml` 생성
2. **XML 파싱 실패** — 일부 XML 깨짐 → ✅ `bun run lazy:test` XML parse 통과
3. **Doctor false-green** — stale/XML/C17 blind spot → ✅ `lazy:test` + framework-owned `lazy:doctor` D01~D07 로 복구

→ 5c-4 SSOT detector 진입 시 동시에 해결.

## 다음 작업 우선순위

상세 계획:
- `.lazy-harness/plans/post-5c-refactor-and-package-health.md`
- `.lazy-harness/plans/5d-interview-loop-implementation-spec.md`
- `.lazy-harness/retrospective/e2e/5e-mvp-proof.md`
- `.lazy-harness/plans/post-mvp-gap-map.md`
- `.lazy-harness/plans/extract-to-lazy-harness-repo.md`
- `.lazy-harness/plans/project-init-interview-spec.md`

```
A. 5e host-project pilot 결과 반영
   - pilot branch `feature/pilot-lazy-harness-5e` 완료
   - pattern: `inside-out`
   - product/test only commit: `ba162ab1`
   - 결과 artifact: `.lazy-harness/retrospective/e2e/5e-host-project-pilot.md`
   - 발견 gap: affected runner command routing. Vitest direct call 금지, project test-strategy/package script 사용

B. Standalone lazy-harness repo extract 준비 (잊지 말 것)
   - 여기 repo 는 incubation/validation worktree 일 뿐
   - framework internals 는 `lazy-harness` 독립 repo 로 이동 예정
   - 상세 체크리스트: `.lazy-harness/plans/extract-to-lazy-harness-repo.md`
   - standalone 첫 핵심 기능: Project Init Interview (`project-init-interview-spec.md`)

C. Post-MVP hardening
   - decision consume/effect executor 확장
   - custom test command / Playwright routing beyond v1 package-script fallback
   - aftershock v0 heuristic 을 artifact diff 기반으로 강화
   - jcode lifecycle hook semantics 문서 최종화
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
- code-change.ts wipeout ❌ (376 lines orchestration-only 상태 보존)

## 검증 명령
bun run lazy:test
bun run lazy:doctor
.lazy-harness/hooks/pre-push.sh origin dummy
→ XML/JSONL/DDD/SDD/BDD/SSOT fixture + interview loop + affected project-test gate + D07 package health 통과
```
