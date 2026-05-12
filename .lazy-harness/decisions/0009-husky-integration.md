# ADR 0009 — Husky Integration Policy

**Date**: 2026-05-10
**Status**: Accepted
**Deciders**: Lazydino
**Trigger**: 사용자 발언 "husky 도 우선 추가해둬야하는게 맞지?? 근데 프로젝트에서 사용하고 있는게 있어서 그런거잔아 그지?? 이거 고민이 되네"
**Discovery**: `git config core.hooksPath = .husky/_` → `.git/hooks/` 가 가로채여서 호출 안 됨. 5a/5b 의 git-native hook 들 모두 dead code 였음.

## Context

medivance 본체는 husky v9 사용중:

```json
"prepare": "husky",
"husky": "^9.1.7"
```

husky 가 `git config core.hooksPath = .husky/_` 로 hook directory 자체를 가로챔. 즉:
- `.git/hooks/post-commit` → **호출 안 됨** (husky 가 path 변경)
- `.husky/_/post-commit` → wrapper 자동 생성 → `.husky/post-commit` 호출 (없으면 silent skip)

5a 에서 `.git/hooks/pre-commit` 에 safety guard 작성했지만 **한 번도 실행 안 됨**. 5b 에서 `.git/hooks/post-commit + pre-push` 도 동일하게 dead.

검증: 직접 marker 작성 실험으로 "실 commit 시 .git/hooks/pre-commit 호출 0 회" 확인 (`Bash` 도구 출력 / 2026-05-10 15:11).

## Conflict Resolution

사용자 발언 분석:

> "husky 도 우선 추가해둬야하는게 맞지?? 근데 프로젝트에서 사용하고 있는게 있어서 그런거잔아 그지?? 이거 고민이 되네"

→ 핵심 갈등: lazy-harness 의 wiring 이 husky 안에 들어가야 한다는 직감 vs 그 wiring 이 medivance origin 에 push 되는 것.

A/B/C/D 옵션 중 사용자 응답:

> "이게 프레임워크이기 때문에 들어가야하는 내용이잔아 맞지??"

→ **사용자 결정: A — husky chain, framework wiring 은 origin 에 push 되어 마땅**.

논리:
- `.husky/post-commit` 의 한 줄 (`bash .lazy-harness/hooks/post-commit.sh`) 은 **누출이 아닌 framework wiring**
- 다른 dev 도 lazy-harness 도입 시 동일 wiring 활용 가능
- guard (`[ -x ".lazy-harness/..." ] && ...`) 로 lazy 없는 환경 silent skip
- private 데이터는 여전히 `.lazy-harness/` 안 → origin push 안 됨

## Decision

**husky 안에 lazy-harness wiring 박는다. 6 번째 Directory Bridge 메커니즘으로 정착.**

### 파일 구성 (medivance origin 에 push 됨)

```
.husky/pre-commit                    11 lines (chain entry)
.husky/post-commit                    9 lines (chain entry)
.husky/pre-push                      12 lines (chain entry)
```

각 파일은 단순 위임자:

```bash
#!/usr/bin/env sh
if [ -x ".lazy-harness/hooks/<name>.sh" ]; then
    .lazy-harness/hooks/<name>.sh "$@" || <fail-policy>
fi
```

### `.lazy-harness/hooks/` 안의 실 logic (private)

```
pre-commit-guard.sh    safety guard (block .lazy-harness/ leak)
post-commit.sh         actions.jsonl append + Fix → regression candidate
pre-push.sh            doctor gate + private leak guard + Unified Result Schema
weekly-snapshot.sh     manual / cron
```

### 정리

- `.git/hooks/pre-commit` → 삭제 (dead — husky 가 가로챔)
- `.git/hooks/post-commit` → 삭제 (없었음, 5b 에서 만든 dead 파일)
- `.git/hooks/pre-push` → 삭제 (없었음, 5b 에서 만든 dead 파일)

## Why this matters

> Principle 0: AI 도 사람도 불완전. 5a/5b 내내 hook 이 동작한다고 믿었지만 한 번도 안 됐음.

검증 없이 진행한 것의 비용:
- safety guard 가 실제로는 보호 안 했음 → `.git/info/exclude` 만이 단일 방어선
- post-commit 의 actions.jsonl 자동 기록도 안 됨 → 직접 sh 실행만이 entry 만들었음
- 이 ADR 의 검증 실험 (marker file) 없었으면 영영 모를 뻔

→ **새 hook 추가 시 항상 marker 실험으로 진짜 호출 검증**.

## What changes

### Files (committed to medivance origin)

| File | Lines | 역할 |
|---|---|---|
| `.husky/pre-commit` | 17 | guard chain entry |
| `.husky/post-commit` | 9 | logger chain entry |
| `.husky/pre-push` | 12 | validator chain entry |

### Files (private, .lazy-harness/)

| File | Status | 역할 |
|---|---|---|
| `pre-commit-guard.sh` | NEW (이전: `.git/hooks/pre-commit`) | safety guard logic |
| `post-commit.sh` | 5b 작성 | actions.jsonl logger |
| `pre-push.sh` | 5b 작성 | doctor + leak gate |

### Files (deleted as dead)

| File | 상태 |
|---|---|
| `.git/hooks/pre-commit` | 삭제 (husky 가 가로챔, 5a 부터 dead) |
| `.git/hooks/post-commit` | 삭제 (5b 에서 만든 dead) |
| `.git/hooks/pre-push` | 삭제 (5b 에서 만든 dead) |

## Cascade

### `harness-init` Step 추가 (Step 2.7)

새 프로젝트 init 시 husky 환경 감지:

```bash
if [ -f "package.json" ] && grep -q '"husky"' package.json; then
    # husky 환경 → .husky/<hook> 생성
    write .husky/pre-commit (chain entry)
    write .husky/post-commit
    write .husky/pre-push
else
    # husky 없음 → .git/hooks/<hook> 생성 (legacy fallback)
    write .git/hooks/pre-commit
    ...
fi
```

### `harness-doctor` 새 check (C11)

```
C11: Husky integration
  - husky 환경인데 .husky/post-commit 없으면 fail
  - husky 없는 환경에서 .git/hooks/pre-commit 없으면 warn
```

### Framework-contract Section 0.3 갱신

Directory Bridge 의 6 번째 메커니즘 추가:

> 6. **husky chain bridge**: `.husky/<hook>` 가 lazy hook 위임. 한 줄짜리 framework wiring 은 framework 의 일부로 origin 에 commit. 단 guard 로 lazy 없는 환경 silent skip.

## Verification

E2E (2026-05-10 15:12):

```
[Test 1] 실 commit 시 .husky/post-commit → lazy post-commit.sh 호출
   → actions.jsonl 67 → 68 entries (자동 추가)
   → JSON entry sha = 실제 commit sha 일치

[Test 2] git add -f .lazy-harness/... → commit 시도
   → .husky/pre-commit → pre-commit-guard.sh
   → "🚨 BLOCKED: Private 영역 파일이 staged 됐습니다!"
   → exit 1 (commit 차단)
```

## Consequences

### Positive

- hook 이 진짜 동작 (5a/5b 의 dead code 문제 해결)
- 다른 dev 가 medivance pull 시 husky 가 자동 wire
- `.git/info/exclude` (1) + `pre-commit-guard` (2) 양 방어선 활성화
- framework wiring reproducible across team

### Negative

- `.husky/<hook>` 3 파일이 origin 에 commit 됨 (lazy-harness 라는 단어가 origin 에 노출)
- 누군가 husky 표준 따르지 않고 `.git/hooks/` 직접 쓰면 wiring 깨짐
- 이미 다른 husky hook (`commit-msg`, `prepare-commit-msg`) 과 공존 — chain 순서 변경 시 주의

### Risk mitigation

- `.husky/<hook>` 가 lazy 없는 환경에서 silent skip 보장 (모든 명령에 `[ -x "..." ]` guard)
- doctor C11 가 husky integration 자동 검증
- 다른 dev 의 medivance pull 시 hook 이 silent 라서 surprise 없음

## References

- 사용자 발언 chain: "husky 도 우선 추가해둬야하는게 맞지" → "프레임워크이기 때문에 들어가야하는 내용이잔아"
- ADR 0006: Directory Bridge Architecture (5 메커니즘 → 6 메커니즘으로 확장)
- Principle 0 (Core Philosophy): 검증 없이 진행한 5a/5b 의 dead code 발각 사례
- Principle 17 (Conflict Resolution Protocol): A/B/C/D/E 선택지로 사용자 결정 유도 → A 선택
