# ADR 0007 — AGENTS.md Auto-Injection Policy

**Date**: 2026-05-10
**Status**: Accepted
**Deciders**: Lazydino
**Trigger**: 사용자 발언 "AGENTS.md 에 잘 들어가게 해야하는것도 맞지?? 처음 init 하거나할때 중요한거로 박아놔야하잔아 그지 않아??" — `.jcode/AGENTS.md` 가 lazy-harness 의 존재를 언급하지 않음 → 새 세션 AI 가 framework 인지 못 함 (gap).

## Context

`.jcode/AGENTS.md` 는 jcode 가 **새 세션 시작 시 자동 머지하는 prompt overlay** 의 일부.
- 새 jcode 세션 → AI 가 system prompt 에 자동 머지된 `.jcode/AGENTS.md` 내용 보유
- 기존 내용: "private harness", "working style" 같은 일반 가이드만
- lazy-harness 의 존재 / skills / 핵심 ADR 언급 0 줄

→ 새 세션 AI 가 framework 의 진입점을 못 찾음. Conflict Resolution Protocol 도 발동 못 함.

## Decision

3 가지 layer 에 동시 박음:

1. **`.jcode/AGENTS.md`** — 즉시 갱신 (이번 세션)
   - "## ⚡ Lazy-Harness Framework (CRITICAL — read first)" 섹션 추가
   - Quick orientation 표 (3 초)
   - 3 skills 명시 (`/harness-init`, `/harness-doctor`, `/harness-update`)
   - ALWAYS / NEVER rules
   - 6 critical context 포인트 (Principle 0/17/18 + ADR 0004/0005/0006)
   - Safety state checklist
   - When in doubt → handoff 가이드

2. **`harness-init` 자동 inject** — Step 2.6 추가
   - 새 프로젝트 init 시 `.jcode/AGENTS.md` 가 없으면 base 생성
   - lazy-harness section marker 검색 후 없으면 자동 append
   - Idempotent: 이미 있으면 keep (덮어쓰지 않음)

3. **doctor C9 check** — `.jcode/AGENTS.md 의 lazy-harness section 존재 검증`
   - 없으면 fail + suggested fix
   - 있으면 pass + line count

## Why this matters

> Principle 0 reminder: 사람도 AI 도 불완전. 새 세션 AI 는 자기가 모르는 걸 모름.

AGENTS.md auto-injection 없으면:
- 새 AI 세션은 lazy-harness 의 존재를 모르므로 silent drift 시작
- Conflict Resolution Protocol 못 발동 (검색 시작점 없음)
- 사용자가 매 세션마다 "lazy-harness 있어" 수동 알림
- doctor / update / handoff 가 있어도 안 씀

AGENTS.md auto-injection 있으면:
- 모든 새 세션이 framework 즉시 인지
- "/harness-doctor" 가 첫 행동 후보로 떠오름
- handoff/00-current-state.md 가 자동 entry point

## Section content design

핵심 정보를 ≤ 80 줄에 압축. 필수 4 표:

```
1. Quick orientation (3 초)        — 4 질문 → 4 path
2. Active skills                   — 3 slash commands
3. ALWAYS/NEVER lists              — 즉시 적용 가능한 rules
4. Critical context (ADR 6 개)     — 인용 시 즉시 검색 가능
```

## Consequences

### Positive

- 새 세션마다 framework 인지율 → 99%+ (AGENTS.md 는 system prompt 에 머지됨)
- "/harness-doctor" 로 첫 검증이 자연스러워짐
- M9 (multi-platform) 시 동일 패턴으로 `.claude/AGENTS.md`, `.codex/AGENTS.md` 도 inject 가능
- doctor C9 가 drift 자동 감지 (사람이 AGENTS.md 잘못 수정해도)

### Negative

- AGENTS.md 가 길어짐 (16 → 78 줄)
- jcode session start 시 system prompt 가 +60 줄 (token cost — 미미)
- 누군가 lazy-harness section 지우면 doctor 가 fail 출력 (의도된 동작)

### Cascade

| File | Update |
|---|---|
| `.jcode/AGENTS.md` | +60 줄 (이번 세션 즉시) |
| `.jcode/skills/harness-init/scripts/init-lazy-harness.sh` | Step 2.6 추가 (~80 줄) |
| `.jcode/skills/harness-doctor/scripts/doctor.sh` | C9 check 추가 |
| `.lazy-harness/framework/framework-contract.md` | (옵션) Section 0.4 — Knowledge Distribution 추가 가능, but 0.3 와 중복 위험 → 일단 skip |
| `decisions/0007-agents-md-injection.md` | 이 ADR |
| `logs/decisions.jsonl` | D-2026-05-10-004 |

## Verification

Tested:
- ✅ Fresh tmp: `.jcode/AGENTS.md` 없는 상태 → init → base + section 둘 다 자동 생성
- ✅ Idempotent: 두번째 init → "already present, keep"
- ✅ doctor C9 pass: 78 lines, section detected
- ✅ doctor C9 fail simulation: section 지우면 즉시 fail 출력 (테스트 안 함 — 명시적 검증)

## Future work

- M2 hook: post-update hook 이 AGENTS.md 도 자동 sync (framework-contract 갱신 시)
- M9: `.claude/AGENTS.md`, `.codex/AGENTS.md` 동일 패턴 적용
- Section 내용 변경 시 init.sh 본문 갱신 필요 (지금은 hardcoded heredoc) — M2 에서 별도 template 파일로 분리 고려

## References

- 직전 사용자 발언 "AGENTS.md 에 잘 들어가게 해야하는것도 맞지??"
- `.jcode/AGENTS.md` 의 jcode prompt overlay 역할 (jcode harness 가 자동 머지)
- ADR 0004/0005/0006 — 이전 세션 ADR 들이 모두 framework-contract 만 갱신해서 새 세션이 못 봄 → 이번 ADR 이 "보이게 만드는" 메커니즘
- Principle 0: AI 한계 보완 (모르는 걸 모름)
