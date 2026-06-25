# ADR 0006 — Directory Bridge Architecture (.jcode ↔ .lazy-harness)

**Date**: 2026-05-10
**Status**: superseded
**Superseded on**: 2026-06-24
**Superseded by**: .lazy-harness/decisions/0050-pi-omp-only-runtime.md
**Deciders**: Lazydino
**Trigger**: 사용자 질문 ".jcode 랑 .lazy-harness 랑 어떻게 연결되는게 가능해??" → framework-contract 에 connection 메커니즘이 명시 안 되어 있음 발견 (gap).

## Rule digest

- Status: deprecated
- Layer: ADR
- Scope: framework-global
- Applies when:
  - questioning how `.jcode` and `.lazy-harness` connect, or whether to merge/relocate them
  - documenting the directory bridge between private wiring and framework body
- Must:
  - keep `.jcode` (private wiring) and `.lazy-harness` (framework body) separate at their bound locations
  - rely on the defined bridge mechanisms (positional binding, doctor lookup, canonical source, safety guard)
- Must not:
  - merge the two directories or move them to non-bound paths
- Record completion:
  - changes to the directory bridge or its wiring update this ADR and `.lazy-harness/decisions/0029-generated-project-local-jcode-wiring.md`
- Related records:
  - `.lazy-harness/decisions/0029-generated-project-local-jcode-wiring.md`
  - `.lazy-harness/framework/framework-contract.md`

## Context

> Superseded by ADR 0050 (Pi/OMP-only runtime, 2026-06-24): jcode wiring is decommissioned. This record is preserved as decision history.

framework 가 두 디렉토리로 분리되어 있음:
- `.jcode/` — jcode harness 영역 (skill, hook, config)
- `.lazy-harness/` — framework 본체 영역 (ADR, logs, maps)

이 분리는 의도적이지만 **어떻게 연결되는지** 가 framework-contract 에 명시 안 되어 있었음. 결과:
- 미래 AI 가 "왜 분리됨?" 다시 물어봄
- 미래 AI 가 위치를 임의로 바꿈 (~/.lazy-harness, .jcode/lazy-harness 등)
- positional binding 깨질 수 있음

## Verified working state

테스트로 현재 구조 동작 확인:
- ✅ 같은 프로젝트 내: `cd medivance && .jcode/skills/harness-doctor/scripts/doctor.sh` → 자동 인식
- ✅ 다른 위치: PWD 기반이라 실패하지만 정확한 에러 메시지 제공
- ✅ `--target` 명시 시: 어디서든 동작
- ✅ update.sh 가 ~/.jcode/framework-contract.md 를 default canonical 로 사용

## Decision

framework-contract.md `Section 0.3 Directory Policy` 추가 (하기는 0.1 lazy 정의 / 0.2 size heuristic 패턴 그대로).

명시 내용:
1. **트리 구조**: `.jcode/` + `.lazy-harness/` + `.lazy-harness-backup/` 의 정확한 layout
2. **5 가지 연결 메커니즘**: Positional binding / Slash command discovery / Preferred doctor lookup / Canonical source bridge / Safety guard coverage
3. **3 가지 분리 이유**: M9 multi-platform / Framework lifespan / 멘탈 모델 분리
4. **Forbidden combinations 4 가지**: 합치거나 위치 바꾸면 안 되는 패턴

## Consequences

### Positive

- 미래 AI 가 connection 다시 안 물어봄 (검색 시 즉시 답)
- 위치 변경 유혹 차단 (Forbidden combinations 명시)
- M9 시점에 마이그레이션 자동 — `.claude/skills/` 추가하면 끝
- 디버깅 시 5 가지 메커니즘 따라 추적 가능

### Negative

- framework-contract.md 가 길어짐 (+115 줄, 현 689 줄)
- 미래에 mechanism 변경 시 두 곳 동기화 (코드 + 문서)

### Cascade

| Document | Update |
|---|---|
| `framework/framework-contract.md` Section 0.3 | +115 줄 (이번 결정) |
| `decisions/0006-directory-bridge-architecture.md` | 이 ADR |
| `logs/decisions.jsonl` | D-2026-05-10-003 |
| `~/.jcode/framework-contract.md` | 동기화 필요 |

## Verification

doctor 가 5 가지 메커니즘 모두 검증함:
- C1 Structure: positional binding 검증 (`.lazy-harness/` 존재)
- C4 Safety: safety guard coverage 검증 (`.lazy-harness/` ignored)
- C5 Pre-commit: safety guard 동작 검증
- C8 Cross-Layer Maps: framework 본체 무결성

slash command discovery 만 jcode 세션 시작 시 검증 가능 (5a-1 deferred).

## References

- 직전 사용자 질문 + AI 다이어그램 응답 (mermaid)
- ADR 0004 (Cross-Layer Maps) — 같은 패턴 (사용자 질문 → framework gap 발견 → Section 추가)
- ADR 0005 (Meaning of Lazy) — 동일 (정의 명시 안 했더니 오해 반복)
- Principle #17 Conflict Resolution (이 ADR 도 Step 1-8 거쳤음)

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/scripts/lazy-init.ts` — installs `.lazy-harness`, git hook delegate, and Jcode wiring.
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated `.jcode` wiring.
  - `.lazy-harness/scripts/lazy-sync.ts` — sync/repair of generated wiring.
- Key symbols:
  - `postInitPreCommitHook` (`lazy-init.ts`) — installs git pre-commit delegate.
  - `installJcodeWiring` (`jcode-wiring.ts`) — installs project-local Jcode config/hooks/harness/skills.
- Flow:
  1. Modern bridge is implemented through lazy-init/lazy-sync/Jcode wiring.
  2. The old `.jcode/skills/harness-*` bridge in this ADR is legacy and superseded by `.jcode/skills/lazy-*` wrappers.
  3. Keep needs-review until the ADR is rewritten or explicitly marked historical.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` protects Jcode wiring and LAZY_HOST_ROOT/root detection.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0029-generated-project-local-jcode-wiring.md`
- Machine index:
  - graph ids: `kg_adr0006_directory_bridge_current`, `kg_adr0006_legacy_skill_names`
  - generated index key: `pending`
