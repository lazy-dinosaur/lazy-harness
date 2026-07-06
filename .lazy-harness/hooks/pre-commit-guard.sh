#!/bin/bash
# Lazy-Harness pre-commit safety guard
# Triggered: husky chain via .husky/pre-commit
# Action: Block private-file leaks on host projects, then run the framework-owned
# commit-time gate (`.lazy-harness/bin/lazy test` or self-test fallback).
#
# Defense-in-depth: .git/info/exclude is the 1st line, this hook is the 2nd.
#
# Bypass (DO NOT — last resort only): git commit --no-verify

set -e

[ -f ".lazy-harness/.hooks-disabled" ] && exit 0

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
LAZY="$REPO_ROOT/.lazy-harness"
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
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
        printf '{"pid":%s,"action":"pre-commit","startedAt":"%s"}\n' "$$" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOCK_DIR/owner.json" 2>/dev/null || true
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
    echo "🚨 pre-commit blocked: same worktree already has a lazy-harness git action running"
    echo "→ 다른 세션의 commit/push/lazy-test gate가 끝난 뒤 다시 commit 하세요."
    [ -n "$OWNER" ] && echo "→ lock owner: $OWNER"
    return 1
}

IS_FRAMEWORK_REPO=0
if [ -f "$LAZY/framework/framework-contract.md" ] && [ -f "$LAZY/planning/phase-5-plan.xml" ]; then
    IS_FRAMEWORK_REPO=1
fi

run_commit_gate() {
    [ ! -d "$LAZY" ] && return 0
    [ -f "$LAZY/.hooks-disabled" ] && return 0

    if [ -x "$LAZY/bin/lazy" ]; then
        TEST_OUT=$(LAZY_HOST_ROOT="$REPO_ROOT" env -u GIT_DIR -u GIT_WORK_TREE "$LAZY/bin/lazy" test --light 2>&1 || true)
    elif [ -x "$LAZY/scripts/self-test.py" ]; then
        TEST_OUT=$(LAZY_HOST_ROOT="$REPO_ROOT" env -u GIT_DIR -u GIT_WORK_TREE "$LAZY/scripts/self-test.py" --light 2>&1 || true)
    else
        echo "ℹ️  pre-commit: lazy test not wired on this host yet — skipping gate"
        return 0
    fi

    if ! printf '%s' "$TEST_OUT" | grep -q 'lazy-harness self-test ok'; then
        echo ""
        echo "🚨 pre-commit blocked: .lazy-harness/bin/lazy test 실패"
        echo "→ .lazy-harness/bin/lazy test 실행해서 fix 후 다시 commit"
        echo ""
        printf '%s\n' "$TEST_OUT" | tail -40
        return 1
    fi

    echo "✅ .lazy-harness/bin/lazy test all green"
    return 0
}

# private 영역 staged 검사
LAZY_STAGED=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '^\.lazy-harness/' || true)
JCODE_STAGED=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '^\.jcode/' || true)
FRAMEWORK_STAGED=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '^packages/[^/]+-harness/|^framework/' || true)

if [ "$IS_FRAMEWORK_REPO" != "1" ] && [ "$BRANCH" != "experimental/lazy-harness" ] && { [ -n "$LAZY_STAGED" ] || [ -n "$JCODE_STAGED" ] || [ -n "$FRAMEWORK_STAGED" ]; }; then
    echo ""
    echo "🚨 BLOCKED: Private 영역 파일이 staged 됐습니다!"
    echo ""
    echo "이 파일들은 experimental/lazy-harness 외 branch 에서 commit/push 되면 안 됩니다."
    echo "(.git/info/exclude 에 등록돼 있지만 git add -f 등으로 우회됐을 가능성)"
    echo ""
    if [ -n "$LAZY_STAGED" ]; then
        echo "Staged .lazy-harness/ files (platform-independent framework):"
        echo "$LAZY_STAGED" | sed 's/^/  - /'
    fi
    if [ -n "$JCODE_STAGED" ]; then
        echo "Staged .jcode/ files (jcode 전용 설정):"
        echo "$JCODE_STAGED" | sed 's/^/  - /'
    fi
    if [ -n "$FRAMEWORK_STAGED" ]; then
        echo "Staged framework/ files (legacy):"
        echo "$FRAMEWORK_STAGED" | sed 's/^/  - /'
    fi
    echo ""
    echo "복구 방법:"
    echo "  git restore --staged <위 파일들>"
    echo "  또는 framework 작업이면 experimental/lazy-harness worktree 에서 진행"
    echo ""
    echo "정말 push 하고 싶다면 (절대 비추천):"
    echo "  1. .git/info/exclude 에서 해당 라인 제거"
    echo "  2. .git/hooks/pre-commit 우회: git commit --no-verify"
    echo ""
    exit 1
fi

acquire_worktree_lock || exit 1
run_commit_gate

exit 0
