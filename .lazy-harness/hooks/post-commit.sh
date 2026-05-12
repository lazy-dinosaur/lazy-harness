#!/bin/bash
# Lazy-Harness post-commit hook
# Triggered: every successful git commit
# Action: append entry to logs/actions.jsonl
#
# This hook never fails the commit (commit already done).
# Errors are silenced to avoid annoying user.

set +e  # Never fail post-commit

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_ROOT" ] && exit 0

LAZY="$REPO_ROOT/.lazy-harness"
[ ! -d "$LAZY" ] && exit 0  # No lazy-harness — skip silently

# R2 fallback: respect disable lock
[ -f "$LAZY/.hooks-disabled" ] && exit 0

LOG="$LAZY/logs/actions.jsonl"
mkdir -p "$(dirname "$LOG")"

COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null)
COMMIT_MSG=$(git log -1 --pretty=%s 2>/dev/null | head -c 200)
COMMIT_TYPE=$(echo "$COMMIT_MSG" | grep -oE '^[A-Z][a-z]+:' | tr -d ':')
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
FILES_CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null | wc -l)
TIMESTAMP=$(date -Iseconds)

# Detect if commit touched lazy-harness paths
TOUCHED_LAZY=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null | grep -cE '\.lazy-harness/|\.jcode/' | head -1 | tr -d ' \n' || echo 0)
[ -z "$TOUCHED_LAZY" ] && TOUCHED_LAZY=0

# Construct JSON line — use python for proper JSON encoding (handles newline, tab, unicode)
JSON_LINE=$(COMMIT_MSG="$COMMIT_MSG" \
  TIMESTAMP="$TIMESTAMP" \
  COMMIT_SHA="$COMMIT_SHA" \
  BRANCH="$BRANCH" \
  COMMIT_TYPE="$COMMIT_TYPE" \
  FILES_CHANGED="$FILES_CHANGED" \
  TOUCHED_LAZY="$TOUCHED_LAZY" \
  python3 -c '
import os, json
print(json.dumps({
  "timestamp": os.environ["TIMESTAMP"],
  "actor": "git",
  "action": "commit",
  "sha": os.environ["COMMIT_SHA"],
  "branch": os.environ["BRANCH"],
  "type": os.environ["COMMIT_TYPE"],
  "filesChanged": int(os.environ["FILES_CHANGED"]),
  "touchedLazy": int(os.environ["TOUCHED_LAZY"]),
  "message": os.environ["COMMIT_MSG"].split("\n")[0]
}, ensure_ascii=False))
' 2>/dev/null) || JSON_LINE=""

if [ -n "$JSON_LINE" ]; then
  echo "$JSON_LINE" >> "$LOG"
fi

# Bug-fix detection → suggest regression entry
if [ "$COMMIT_TYPE" = "Fix" ]; then
    REG="$LAZY/regression/candidates.jsonl"
    mkdir -p "$(dirname "$REG")"
    CAND=$(COMMIT_MSG="$COMMIT_MSG" TIMESTAMP="$TIMESTAMP" COMMIT_SHA="$COMMIT_SHA" python3 -c '
import os, json
print(json.dumps({
  "timestamp": os.environ["TIMESTAMP"],
  "sha": os.environ["COMMIT_SHA"],
  "message": os.environ["COMMIT_MSG"].split("\n")[0],
  "status": "candidate",
  "action": "review-and-promote-to-regression-entry"
}, ensure_ascii=False))
' 2>/dev/null) || CAND=""
    [ -n "$CAND" ] && echo "$CAND" >> "$REG"
fi

exit 0
