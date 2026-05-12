#!/bin/bash
# Lazy-Harness pre-commit safety guard
# Triggered: husky chain via .husky/pre-commit
# Action: Block commit if .lazy-harness/, .jcode/, or framework/ files are staged.
#
# Defense-in-depth: .git/info/exclude is the 1st line, this hook is the 2nd.
#
# Bypass (DO NOT — last resort only): git commit --no-verify

set -e

[ -f ".lazy-harness/.hooks-disabled" ] && exit 0

# private 영역 staged 검사
LAZY_STAGED=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '^\.lazy-harness/' || true)
JCODE_STAGED=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '^\.jcode/' || true)

if [ -n "$LAZY_STAGED" ] || [ -n "$JCODE_STAGED" ] || [ -n "$FRAMEWORK_STAGED" ]; then
    echo ""
    echo "🚨 BLOCKED: Private 영역 파일이 staged 됐습니다!"
    echo ""
    echo "이 파일들은 medivance origin 에 절대 push 되면 안 됩니다."
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
    echo ""
    echo "정말 push 하고 싶다면 (절대 비추천):"
    echo "  1. .git/info/exclude 에서 해당 라인 제거"
    echo "  2. .git/hooks/pre-commit 우회: git commit --no-verify"
    echo ""
    exit 1
fi

exit 0
