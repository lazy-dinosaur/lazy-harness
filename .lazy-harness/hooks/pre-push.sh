#!/bin/bash
# Lazy-Harness pre-push hook
# Triggered: before git push
# Action: run final harness validation, output Unified Result Schema
# Exit non-zero blocks the push.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_ROOT" ] && exit 0

LAZY="$REPO_ROOT/.lazy-harness"
[ ! -d "$LAZY" ] && exit 0

[ -f "$LAZY/.hooks-disabled" ] && {
    echo "⚠️  lazy-harness hooks disabled (.hooks-disabled present) — skip pre-push"
    exit 0
}

# Read remote name from stdin (git supplies)
REMOTE="${1:-origin}"
URL="${2:-}"
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

# CRITICAL: ALL push 에서 private file leak 차단 (URL 무관 — bug-2 fix from Sisyphus 2026-05-10)
# .husky/<3 hooks> 는 ADR 0009 에 의해 framework public surface 로 ALLOW.
LEAKED=""
if [ "$BRANCH" != "experimental/lazy-harness" ]; then
    UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
    if [ -n "$UPSTREAM" ]; then
        RANGE="$UPSTREAM..HEAD"
    elif git rev-parse --verify "$REMOTE/$BRANCH" >/dev/null 2>&1; then
        RANGE="$REMOTE/$BRANCH..HEAD"
    else
        RANGE="HEAD~1..HEAD"
    fi
    LEAKED=$(git diff --name-only "$RANGE" 2>/dev/null | grep -E '^\.lazy-harness/|^\.jcode/' || true)
fi
if [ -n "$LEAKED" ]; then
    echo ""
    echo "🚨 BLOCKED: Push 시도에 lazy-harness/jcode private 파일 포함됨!"
    echo "$LEAKED" | sed 's/^/  - /'
    echo ""
    echo "→ 해당 파일 git rm --cached 로 제거 후 다시 push"
    echo "→ framework 작업이면 experimental/lazy-harness branch 에서 push"
    echo "→ remote: $REMOTE ($URL)"
    exit 1
fi

# Run doctor (concise output) — fail blocks push
DOCTOR="$LAZY/.jcode-skills-link/harness-doctor/scripts/doctor.sh"
[ ! -x "$DOCTOR" ] && DOCTOR="$REPO_ROOT/.jcode/skills/harness-doctor/scripts/doctor.sh"

if [ -x "$DOCTOR" ]; then
    DOCTOR_OUT=$("$DOCTOR" 2>&1 || true)
    FAILS=$(echo "$DOCTOR_OUT" | grep -cE '^\[C[0-9]+\].*✗ fail' | head -1 | tr -d ' \n' || echo 0)
    [ -z "$FAILS" ] && FAILS=0

    # Emit Unified Result Schema
    TIMESTAMP=$(date -Iseconds)
    RESULT_LOG="$LAZY/logs/validations.jsonl"
    mkdir -p "$(dirname "$RESULT_LOG")"

    if [ "$FAILS" -gt 0 ]; then
        cat >> "$RESULT_LOG" <<JSON
{"timestamp":"$TIMESTAMP","id":"PRE-PUSH-001","status":"fail","category":"infra","humanRequired":true,"details":["doctor reports $FAILS fail check(s)"],"suggestedFix":"run /harness-doctor and address fails before push","confidence":"high"}
JSON
        echo ""
        echo "🚨 pre-push blocked: doctor 가 $FAILS 개 check 실패 보고"
        echo "→ /harness-doctor 실행해서 fix 후 다시 push"
        exit 1
    else
        cat >> "$RESULT_LOG" <<JSON
{"timestamp":"$TIMESTAMP","id":"PRE-PUSH-001","status":"pass","category":"infra","humanRequired":false,"details":["doctor all green"],"confidence":"high"}
JSON
    fi
fi

exit 0
