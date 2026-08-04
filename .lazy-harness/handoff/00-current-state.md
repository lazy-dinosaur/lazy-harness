# Lazy-Harness Current State (Live)

> 다음 세션이 즉시 이해하고 진행하기 위한 entry point.

## 즉시 실행할 것 (다음 세션 시작 시)

1. **framework 개발은 반드시 standalone source repo 에서 시작**:
   `cd /home/lazydino/dev/lazy-harness && jcode`

2. **수정 후 framework 자체 검증**:
   ```bash
   cd /home/lazydino/dev/lazy-harness
   python3 .lazy-harness/scripts/self-test.py --scope framework
   python3 .lazy-harness/scripts/doctor.py --profile smoke
   ```

3. **Medivance dogfooding host 반영/검증**:
   ```bash
   cd /home/lazydino/dev/medivance
   .lazy-harness/bin/lazy update --dry-run --force
   .lazy-harness/bin/lazy test
   ```

4. **참고**: `~/dev/medivance.experimental-lazy-harness` legacy scaffold 는 2026-05-17 worktree remove + branch 삭제 완료. 더 이상 존재하지 않음.

## 현재 상태 (2026-05-13)

| 항목 | 값 |
|---|---|
| **Source of truth** | `~/dev/lazy-harness` (`main`) — ADR 0027 |
| **Dogfooding host** | `~/dev/medivance` — `.lazy-harness/` installed copy, git-clean after sync |
| **Legacy scaffold** | (removed 2026-05-17 — `medivance.experimental-lazy-harness` worktree + branch 모두 삭제) |
| **Origin push** | ✅ public repo: `https://github.com/lazy-dinosaur/lazy-harness` (`origin/main`) |
| **ADRs** | **58** (0001~0058; 0024 AI-first redesign, 0025 portability single entry point, 0026 doctor/self-test scope separation, 0027 standalone source-of-truth repo, 0028 progressive knowledge graph backbone, 0029 generated project-local Jcode wiring, 0030 implementation map three-layer storage, 0031 root-bound record convergence, 0032 user-correction ownership SSOT convergence, 0033 layer completeness gate, 0034 analysis discovery capture gate, 0035 interview queue close mandate, 0036 record-search trigger by intent not keyword, 0037 workflow compression not safety reduction, 0038 requirements-first change gate, 0039 rule lifecycle bindings, 0040 capability registry kind/level separation, 0041 organic hybrid rule guidance, 0042 record-index cache naming, 0043 Pi native package in source repo, 0044 project operating rulebook, 0045 purpose-scoped retrieval, 0046 policy machinery typed policy canonical, 0047 Pi/OMP shared package separate install UX, 0048 operating-rule storage+apply repair, 0049 discovery-vs-loading complete lean discovery, 0050 Pi/OMP-only runtime supersedes 0006/0007/0029, 0051 jcode-parity grammar re-grounding, 0052 external context-extension non-adoption, 0053 memory-device storage discipline, 0054 three-layer cross-stack architecture guidance, 0055 agent-neutral orchestration core + Pi Subagents runtime, 0056 multi-runtime thin adapters for Pi/OMP/Jcode, 0057 rebase-maintained lazy-patched Jcode channel, 0058 Jcode typed review model routing) |
| **Decisions logged** | 28+ entries |
| **Framework self-test** | ✅ `~/dev/lazy-harness`: `lazy-harness self-test ok (scope=framework, ran=23, skipped=0)` |
| **Medivance sync validation** | ✅ `~/dev/medivance`: synced to source `caa2a2b` on 2026-05-20, `lazy-harness self-test ok (scope=host, ran=30, skipped=11)` |
| **5c complete** | ✅ 5c-1~5c-9 all done, refactor/package health are post-5c hardening |
| **5c completion markers** | ✅ 5c-5 Cross-layer, 5c-6 Lint/typecheck, 5c-7 Structured ask, 5c-8 E2E, 5c-9 Doctor C17 |
| **5d Interview Loop** | ✅ done (5d-1~5d-6: collect, answer, TDD, aftershock, hooks, walkthrough depth ≥ 2) |
| **5e dogfooding** | ✅ standalone source extraction + Medivance sync/lazy test 완료 |
| **AGENTS governance** | ✅ §0 정체성 + §2.4 layer 규칙 + §2.5 epistemic baseline (176 lines, self-test cap 180) |
| **CLI/init/sync/update** | ✅ `.lazy-harness/bin/lazy`, `lazy-init.ts`, `lazy-sync.ts`, `lazy-update.ts`, public `install.sh` source repo 에 정식 편입 |
| **user-level launcher** | ⏸ `~/.local/bin/lazy` 는 packaging 단계로 defer. 현재는 per-host dispatcher 만 소유 |
| **N4 Portability Entry Point** | 🟡 next: Project Init Interview (`project-init-interview-spec.md`) |

## Oracle Audit 결과 (2026-05-12)

위치: `.lazy-harness/retrospective/audits/2026-05-12-oracle-audit.md`

### Critical issues 3

1. **SSOT 문서 stale** — registry 가 실제 SSOT 와 mismatch → ✅ `ssot/registry.xml` 생성
2. **XML 파싱 실패** — 일부 XML 깨짐 → ✅ `.lazy-harness/bin/lazy test` XML parse 통과
3. **Doctor false-green** — stale/XML/C17 blind spot → ✅ `.lazy-harness/bin/lazy test` + `.lazy-harness/bin/lazy doctor` D01~D07 로 복구

→ 5c-4 SSOT detector 진입 시 동시에 해결.

## 다음 작업 우선순위

상세 계획:
- `.lazy-harness/plans/project-init-interview-spec.md`
- `.lazy-harness/plans/post-mvp-gap-map.md`
- `.lazy-harness/plans/extract-to-lazy-harness-repo.md` (completed historical checklist)
- `.lazy-harness/plans/legacy-experimental-worktree-audit.md`

```
A. Source-of-truth 운영 고정
   - 개발 기준: ~/dev/lazy-harness
   - host 반영: lazy-sync --from ~/dev/lazy-harness --target <host>
   - Medivance host 는 sync + lazy test 이미 통과

B. Legacy worktree 정리
   - ✅ 2026-05-17 완료: `git worktree remove --force` + `git branch -D experimental/lazy-harness`
   - 잔여 큐: fixture baseline drift(BDD expected 3 actual 2) + decisions.jsonl Unicode replacement warning

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
(removed) /home/lazydino/dev/medivance.experimental-lazy-harness — 2026-05-17 삭제
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
