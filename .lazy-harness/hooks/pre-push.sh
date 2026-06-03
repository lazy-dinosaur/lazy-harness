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

LOCK_DIR=""
release_worktree_lock() {
    [ -n "$LOCK_DIR" ] && rm -rf "$LOCK_DIR" 2>/dev/null || true
}

acquire_worktree_lock() {
    GIT_DIR_ABS=$(git rev-parse --absolute-git-dir 2>/dev/null || echo "")
    [ -z "$GIT_DIR_ABS" ] && return 0
    LOCK_DIR="$GIT_DIR_ABS/lazy-harness/locks/git-action.lockdir"
    mkdir -p "$(dirname "$LOCK_DIR")"
    if mkdir "$LOCK_DIR" 2>/dev/null; then
        printf '{"pid":%s,"action":"pre-push","startedAt":"%s"}\n' "$$" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOCK_DIR/owner.json" 2>/dev/null || true
        trap release_worktree_lock EXIT INT TERM
        return 0
    fi
    OWNER=$(cat "$LOCK_DIR/owner.json" 2>/dev/null || true)
    OWNER_PID=$(printf '%s' "$OWNER" | python3 -c 'import json,sys; print((json.loads(sys.stdin.read() or "{}").get("pid") or ""))' 2>/dev/null || true)
    if [ -n "$OWNER_PID" ] && ! kill -0 "$OWNER_PID" 2>/dev/null; then
        rm -rf "$LOCK_DIR" 2>/dev/null || true
        acquire_worktree_lock
        return $?
    fi
    echo ""
    echo "🚨 pre-push blocked: same worktree already has a lazy-harness git action running"
    echo "→ 다른 세션의 commit/push/lazy-test gate가 끝난 뒤 다시 push 하세요."
    [ -n "$OWNER" ] && echo "→ lock owner: $OWNER"
    return 1
}

[ -f "$LAZY/.hooks-disabled" ] && {
    echo "⚠️  lazy-harness hooks disabled (.hooks-disabled present) — skip pre-push"
    exit 0
}

# Read remote name from stdin (git supplies)
REMOTE="${1:-origin}"
URL="${2:-}"
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
IS_FRAMEWORK_REPO=0
if [ -f "$LAZY/framework/framework-contract.md" ] && [ -f "$LAZY/planning/phase-5-plan.xml" ]; then
    IS_FRAMEWORK_REPO=1
fi

# CRITICAL: ALL push 에서 private file leak 차단 (URL 무관 — bug-2 fix from Sisyphus 2026-05-10)
# .husky/<3 hooks> 는 ADR 0009 에 의해 framework public surface 로 ALLOW.
LEAKED=""
if [ "$IS_FRAMEWORK_REPO" != "1" ] && [ "$BRANCH" != "experimental/lazy-harness" ]; then
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
    echo "→ framework 작업이면 standalone lazy-harness source repo 에서 push"
    echo "→ remote: $REMOTE ($URL)"
    exit 1
fi

# ADR 0022: framework-owned validation. Jcode skills are wrappers only.
TIMESTAMP=$(date -Iseconds)
RESULT_LOG="$LAZY/logs/validations.jsonl"
mkdir -p "$(dirname "$RESULT_LOG")"

# Detect whether this host has a runnable canonical lazy-harness gate.
# Execution paths, in order of preference:
#   1) .lazy-harness/bin/lazy test (per-host CLI dispatcher, current)
#   2) .lazy-harness/scripts/self-test.py directly (fallback for transitional hosts)
# Never call historical package-script aliases from this hook. They are stale
# and can point agents at the wrong diagnosis path.
HAS_CLI=0
if [ -x ".lazy-harness/bin/lazy" ]; then
    HAS_CLI=1
fi

HAS_SELFTEST=0
if [ "$HAS_CLI" = "0" ] && [ -x ".lazy-harness/scripts/self-test.py" ]; then
    HAS_SELFTEST=1
fi

if [ "$HAS_CLI" = "0" ] && [ "$HAS_SELFTEST" = "0" ]; then
    echo "ℹ️  pre-push: .lazy-harness/bin/lazy test not wired on this host yet — skipping gate"
    exit 0
fi

acquire_worktree_lock || exit 1

if [ "$HAS_CLI" = "1" ]; then
    TEST_OUT=$(LAZY_HOST_ROOT="$REPO_ROOT" env -u GIT_DIR -u GIT_WORK_TREE "$LAZY/bin/lazy" test 2>&1 || true)
else
    TEST_OUT=$(LAZY_HOST_ROOT="$REPO_ROOT" env -u GIT_DIR -u GIT_WORK_TREE "$LAZY/scripts/self-test.py" 2>&1 || true)
fi

if ! echo "$TEST_OUT" | grep -q 'lazy-harness self-test ok'; then
    SUMMARY=$(printf '%s' "$TEST_OUT" | tail -5 | tr '\n' '; ' | head -c 500)
    TIMESTAMP="$TIMESTAMP" SUMMARY="$SUMMARY" python3 - <<'PY' >> "$RESULT_LOG"
import json
import os

print(json.dumps({
    "timestamp": os.environ["TIMESTAMP"],
    "id": "PRE-PUSH-001",
    "status": "fail",
    "category": "infra",
    "humanRequired": True,
    "details": [f".lazy-harness/bin/lazy test failed: {os.environ.get('SUMMARY', '')}"],
    "suggestedFix": "run .lazy-harness/bin/lazy test and address framework self-test failures",
    "confidence": "high",
}, ensure_ascii=False))
PY
    echo ""
    echo "🚨 pre-push blocked: .lazy-harness/bin/lazy test 실패"
    echo "→ .lazy-harness/bin/lazy test 실행해서 fix 후 다시 push"
    exit 1
fi

# Success intentionally does not write to tracked validations.jsonl.
# A successful push gate should not dirty the working tree.
echo "✅ .lazy-harness/bin/lazy test all green"

exit 0
