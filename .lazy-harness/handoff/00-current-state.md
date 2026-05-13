# Lazy-Harness Current State (Live)

> 다음 세션이 즉시 이해하고 진행하기 위한 entry point.

## 즉시 실행할 것 (다음 세션 시작 시)

1. **framework 개발은 반드시 standalone source repo 에서 시작**:
   `cd /home/lazydino/dev/lazy-harness && jcode`

2. **수정 후 framework 자체 검증**:
   ```bash
   cd /home/lazydino/dev/lazy-harness
   .lazy-harness/scripts/self-test.py
   python3 .lazy-harness/scripts/doctor.py --profile smoke
   ```

3. **Medivance dogfooding host 반영/검증**:
   ```bash
   cd /home/lazydino/dev/medivance
   bun ~/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts \
     --from ~/dev/lazy-harness \
     --target ~/dev/medivance \
     --force
   .lazy-harness/bin/lazy test
   ```

4. **주의**: `/home/lazydino/dev/medivance.experimental-lazy-harness` 는 legacy extraction scaffold. 더 이상 framework 개발 기준 아님.

## 현재 상태 (2026-05-13)

| 항목 | 값 |
|---|---|
| **Source of truth** | `~/dev/lazy-harness` (`main`) — ADR 0027 |
| **Dogfooding host** | `~/dev/medivance` — `.lazy-harness/` installed copy, git-clean after sync |
| **Legacy scaffold** | `~/dev/medivance.experimental-lazy-harness` — 개발 기준 아님, 정리 예정 |
| **Origin push** | ❌ local only. DO NOT PUSH 기본 원칙 유지 |
| **ADRs** | **27** (0001~0027; 0024 AI-first redesign, 0025 portability single entry point, 0026 doctor/self-test scope separation, 0027 standalone source-of-truth repo) |
| **Decisions logged** | 27+ entries |
| **Framework self-test** | ✅ `~/dev/lazy-harness`: `lazy-harness self-test ok (scope=framework, ran=20, skipped=0)` |
| **Medivance sync validation** | ✅ `~/dev/medivance`: `lazy-harness self-test ok (scope=host, ran=10, skipped=10)` |
| **5c complete** | ✅ 5c-1~5c-9 all done, refactor/package health are post-5c hardening |
| **5c completion markers** | ✅ 5c-5 Cross-layer, 5c-6 Lint/typecheck, 5c-7 Structured ask, 5c-8 E2E, 5c-9 Doctor C17 |
| **5d Interview Loop** | ✅ done (5d-1~5d-6: collect, answer, TDD, aftershock, hooks, walkthrough depth ≥ 2) |
| **5e dogfooding** | ✅ standalone source extraction + Medivance sync/lazy test 완료 |
| **AGENTS governance** | ✅ §0 정체성 + §2.4 layer 규칙 + §2.5 epistemic baseline (165 lines, self-test cap 180) |
| **CLI/init/sync** | ✅ `.lazy-harness/bin/lazy`, `lazy-init.ts`, `lazy-sync.ts` source repo 에 정식 편입 |
| **user-level launcher** | ⏸ `~/.local/bin/lazy` 는 packaging 단계로 defer. 현재는 per-host dispatcher 만 소유 |
| **N4 Portability Entry Point** | 🟡 next: Project Init Interview (`project-init-interview-spec.md`) |

## Oracle Audit 결과 (2026-05-12)

위치: `.lazy-harness/retrospective/audits/2026-05-12-oracle-audit.md`

### Critical issues 3

1. **SSOT 문서 stale** — registry 가 실제 SSOT 와 mismatch → ✅ `ssot/registry.xml` 생성
2. **XML 파싱 실패** — 일부 XML 깨짐 → ✅ `bun run lazy:test` XML parse 통과
3. **Doctor false-green** — stale/XML/C17 blind spot → ✅ `lazy:test` + framework-owned `lazy:doctor` D01~D07 로 복구

→ 5c-4 SSOT detector 진입 시 동시에 해결.

## 다음 작업 우선순위

상세 계획:
- `.lazy-harness/plans/project-init-interview-spec.md`
- `.lazy-harness/plans/post-mvp-gap-map.md`
- `.lazy-harness/plans/extract-to-lazy-harness-repo.md` (completed historical checklist)

```
A. Source-of-truth 운영 고정
   - 개발 기준: ~/dev/lazy-harness
   - host 반영: lazy-sync --from ~/dev/lazy-harness --target <host>
   - Medivance host 는 sync + lazy test 이미 통과

B. Legacy worktree 정리
   - ~/dev/medivance.experimental-lazy-harness 는 더 이상 개발 기준 아님
   - 삭제/ worktree remove 는 destructive 이므로 사용자 confirm 후 진행

C. Project Init Interview (N4)
   - inspect/interview/apply 구현
   - host test-strategy/config 결정 ledger
   - ~/.local/bin/lazy 는 packaging 단계로 유지

D. Post-MVP hardening
   - decision consume/effect executor 확장
   - custom test command / Playwright routing beyond v1 package-script fallback
   - aftershock v0 heuristic 을 artifact diff 기반으로 강화
   - jcode lifecycle hook semantics 문서 최종화
```

## Repository 배치 (현재 기준)

```
/home/lazydino/dev/lazy-harness                      (main, ✅ framework source of truth)
/home/lazydino/dev/medivance                         (dev-ian, Medivance app + dogfooding host)
/home/lazydino/dev/medivance.experimental-lazy-harness (legacy extraction scaffold, 정리 예정)
/home/lazydino/dev/medivance.feat-*                  (각 feature branch)
```

→ framework 본체 개발은 `~/dev/lazy-harness` 에서만 한다 (ADR 0027).

## Source-of-truth 룰 (ADR 0027) — 절대 어기지 말 것

- `.lazy-harness/` framework body 수정은 `~/dev/lazy-harness` 에서 commit
- `~/dev/medivance/.lazy-harness` 는 installed copy. 직접 framework 개발 금지
- host 반영은 `lazy-sync --from ~/dev/lazy-harness --target <host>` 로 수행
- `~/.local/bin/lazy` user launcher 는 packaging 단계까지 defer
- legacy worktree 삭제/정리는 사용자 confirm 후 진행

## Swarm 위임 시 명세에 항상 포함

```
## 절대 금지
- git push ❌ (local only)
- ~/dev/medivance/.lazy-harness 직접 source-of-truth 수정 ❌
- legacy worktree 삭제 ❌ (사용자 confirm 전)
- host memory / logs / decisions 삭제 ❌

## 검증 명령
cd ~/dev/lazy-harness && .lazy-harness/scripts/self-test.py
cd ~/dev/medivance && .lazy-harness/bin/lazy test
→ framework scope 20 checks + host scope 10 checks 통과
```
