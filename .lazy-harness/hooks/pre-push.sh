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

# ADR 0022: framework-owned validation. Jcode skills are wrappers only.
TIMESTAMP=$(date -Iseconds)
RESULT_LOG="$LAZY/logs/validations.jsonl"
mkdir -p "$(dirname "$RESULT_LOG")"

if command -v bun >/dev/null 2>&1; then
    TEST_OUT=$(bun run lazy:test 2>&1 || true)
else
    TEST_OUT=$(.lazy-harness/scripts/self-test.py 2>&1 || true)
fi

if ! echo "$TEST_OUT" | grep -q 'lazy-harness self-test ok'; then
    SUMMARY=$(printf '%s' "$TEST_OUT" | tail -5 | tr '\n' '; ' | head -c 500)
    cat >> "$RESULT_LOG" <<JSON
{"timestamp":"$TIMESTAMP","id":"PRE-PUSH-001","status":"fail","category":"infra","humanRequired":true,"details":["lazy:test failed: $SUMMARY"],"suggestedFix":"run bun run lazy:test and address framework self-test failures","confidence":"high"}
JSON
    echo ""
    echo "🚨 pre-push blocked: lazy:test 실패"
    echo "→ bun run lazy:test 실행해서 fix 후 다시 push"
    exit 1
fi

cat >> "$RESULT_LOG" <<JSON
{"timestamp":"$TIMESTAMP","id":"PRE-PUSH-001","status":"pass","category":"infra","humanRequired":false,"details":["lazy:test all green"],"confidence":"high"}
JSON

exit 0
