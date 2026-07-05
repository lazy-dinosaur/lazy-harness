# ADR 0012 — Oracle/Sisyphus Audit Cascade Fix

**Date**: 2026-05-10
**Status**: Accepted
**Deciders**: Lazydino
**Trigger**: 사용자 발언 "이거 우리가 목표로하는게 지금 잘 진행되고 있는지 한번 전수조사 하고갈까??"

## Rule digest

- Status: needs-review
- Layer: ADR
- Scope: framework-global
- Aliases:
  - 감사 캐스케이드
  - audit cascade
- Applies when:
  - auditing whether framework state and "done" claims actually match reality
  - a phase or decision is declared closed and silent failures or stale living-docs may remain
  - adding or evaluating doctor checks for false-pass detection
- Must:
  - treat AI self-report as untrusted; verify framework truth by independent audit, not doctor-green alone
  - run periodic intent-gap plus mechanical silent-failure audits at phase boundaries
  - backfill audit findings into doctor checks and decision/action logs
- Must not:
  - treat a passing doctor or self-declared "closed" as proof of framework correctness
- Record completion:
  - new audit findings update doctor checks and this ADR; the named Oracle/Sisyphus process is historical
- Related records:
  - `.lazy-harness/decisions/0011-verification-discipline.md`
  - `.lazy-harness/decisions/0009-husky-integration.md`

## Discovery

Oracle (claude-opus 의도-실현 gap 점검) + Sisyphus (mechanical silent-failure 검출) 병렬 audit.

### Oracle 발견 (3 critical gap)

1. **Husky drift** — `.husky/<3>` 가 `.git/info/exclude` 에 등재 + untracked. ADR 0009 의 "framework public surface, commit to medivance origin" 결정과 정면 모순. handoff 의 "git tracked YES" 도 false claim.
2. **Doctor blind spots** — JSONL validity, result.schema conformance, handoff freshness, contract 0.3 cascade 미감지. doctor green 이 framework 진실성을 과대표시.
3. **Living document drift** — handoff stale (v1.2/10/5/93 vs 실 v1.3/11/6/107), AGENTS.md stale (9 checks/`.git/hooks/`/ADR 0006).

### Sisyphus 발견 (6 NEW silent failures)

| # | Severity | 영역 | 위치 |
|---|---|---|---|
| 1 | HIGH | init script 의 hook emit 이 옛 multi-line escape 버그 잔존 → fix wash-out | `init-lazy-harness.sh:567-573` |
| 2 | HIGH | pre-push URL grep 패턴 `medivance\|origin` 작동 안 함 → leak guard 우회 | `pre-push.sh:25` + init.sh:608 |
| 3 | MEDIUM | doctor C15 cwd-relative path → `--target /other` 시 false result | `doctor.sh:619-625` |
| 4 | MEDIUM | validations.jsonl 무한 누적 (8 분 사이 516 lines) | `pre-push.sh + doctor` |
| 5 | LOW | post-commit `\|\| echo 0` dead path | `post-commit.sh:31` |
| 6 | MEDIUM | decisions.jsonl 6 entry vs 11 ADR (5 ADR 의 conflict log 누락) | `logs/decisions.jsonl` |

## Decision

5/6 NEW + 3 Oracle gap 즉시 fix:

### 즉시 fix 완료

| 항목 | fix |
|---|---|
| Oracle Gap 2 | doctor C14 (JSONL validity), C15 (Husky tracked), C16 (handoff freshness) 추가 |
| Oracle Gap 3 (handoff) | handoff/00-current-state.md 갱신 (v1.3, ADR 11, decisions 6, actions 109) |
| Sisyphus bug-1 | `.lazy-harness/hooks/post-commit.sh` + `init-lazy-harness.sh` 의 hook emit 모두 python3 JSON encoding 으로 교체 |
| Sisyphus bug-2 | URL grep 제거, ALL push 에 leak guard 적용. `.husky/<3>` 는 framework public surface 로 ALLOW 명시 |
| Sisyphus bug-3 | doctor C15 path 를 `$TARGET/.husky/...` `git -C "$TARGET"` 으로 수정 |
| Sisyphus bug-5 | post-commit `\|\| echo 0` 제거 (의미 명확화) |
| Sisyphus bug-6 | decisions.jsonl backfill — 5 ADR (0001/0002/0003/0008/0009) entry 추가 |
| 기존 invalid 3 lines | `actions.jsonl` 복구 (107 → 106 → 109 정상화) |

### Pending — 사용자 결정 (Oracle Gap 1)

**Husky tracking** — 옵션:

- **A** (Recommended): exclude 빼고 commit. ADR 0009 enforce. C15 pass.
- **B**: ADR 0009 reverse → husky 도 personal. handoff 갱신.
- **C**: Hybrid (commit but generic skip-if-absent).
- **D**: 직접 입력.

→ 다음 user reply 에서 결정.

### Pending — 향후 처리

| 항목 | 시점 |
|---|---|
| Sisyphus bug-4 (validations retention) | ADR 0013 또는 5b-2a 묶어서 |
| AGENTS.md stale content (`.git/hooks/`, 9 checks, ADR 0006) | 5b close E2E review 시 |
| Living document continuous self-audit | Principle 1.1 자동화 (5d?) |

## Why this matters

> Principle 0 의 핵심: 사람도 AI 도 불완전. AI 자체 verify 는 self-report.

이번 audit 가 증명한 것:
- doctor green = framework correct **NOT TRUE**.
- AI 가 "5b CLOSED" 라고 자체 선언했지만 실제로:
  - JSONL 3 invalid lines (silent log corruption)
  - hook emit script 가 fix 미반영 (regression risk)
  - leak guard 가 실제로 작동 안 함 (security hole)
  - C15/C16 같은 진실 검출 doctor check 가 없었음 (false confidence)

→ Oracle + Sisyphus 가 framework 의 self-correcting capacity 를 검증. 이 audit cascade 자체가 **Principle 1.5 Self-Driving Loop 의 더 강한 형태** (자기 자신 audit + fix + 재audit).

## Cascade

| 파일 | 변경 |
|---|---|
| `framework/framework-contract.md` | (선택) Principle 22 — Periodic Audit (Oracle + Sisyphus) 추가 가능 |
| `decisions/0001~0011` | jsonl backfill (bug-6) |
| `framework/framework-contract.md` 의 `decisions/decisions-log.jsonl` 잘못된 path | 수정 (Oracle 발견) |
| `handoff/00-current-state.md` | 이미 갱신 |
| Doctor checks | C14/C15/C16 추가, 16 total |

## Consequences

### Positive
- Doctor false-pass 검출 capacity 강화 (16 checks)
- Init 도 fix 보존 (regression 안 됨)
- Leak guard 실 작동
- 정기 audit pattern (Oracle + Sisyphus 병렬) 정립

### Negative
- 매 phase close 시 audit 권장 → 시간 cost
- 검출 강화로 false fail 가능성 증가 (튜닝 필요)

### Risk
- Oracle/Sisyphus 도 catch 못한 더 깊은 silent failure 가 있을 수 있음 → 다음 audit cycle 에서

## References

- ADR 0009 — Husky Integration (이번 audit 가 그 cascade 미실현 검출)
- ADR 0011 — Verification Discipline (이번 audit 가 self-application 의 첫 사례)
- Principle 0 — 사람-AI 상호보완 (AI 자체 verify 한계 → audit 자동화 필요성)
- Principle 1.5 — Self-Driving Loop (이번 audit cascade 가 강화 형태)
- Sisyphus session: session_wolf_1778395541772_b9ecf1e87bc66fe3
- Oracle session: session_jaguar_1778394837157_0ccab9abadc4d4a6

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/scripts/doctor.py` — current doctor checks derived from old audit hardening.
  - `.lazy-harness/hooks/pre-push.sh` — leak guard and validation gate.
  - Global Jcode profile overlay — contains current oracle/sisyphus subagent profiles outside project records.
- Key symbols:
  - `check_external_dependency_invariant` (`doctor.py`) — C17 external dependency guard.
  - `check_jsonl_parse` (`doctor.py`) — JSONL validity guard.
- Flow:
  1. Some audit findings became doctor/hook hardening.
  2. Oracle/Sisyphus as named agent cascade is not an executable project-local source artifact in this repo.
  3. Keep needs-review as historical audit process record.
- Tests / protection:
  - Self-test covers doctor JSONL/C17/hook behavior, but not the full Oracle/Sisyphus social process.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0011-verification-discipline.md`
- Machine index:
  - graph ids: `kg_adr0012_audit_hardening_doctor`, `kg_adr0012_oracle_sisyphus_process`
  - generated index key: `pending`
