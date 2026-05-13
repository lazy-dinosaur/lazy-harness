#!/usr/bin/env bash
# on-context-first.sh — Jcode tool.execute.before wrapper for context-first gate.
# Converts helper text output into a Jcode hook decision JSON deny.

set +e

[ -f .lazy-harness/.hooks-disabled ] && exit 0

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_ROOT" ] || [ ! -d "$REPO_ROOT/.lazy-harness" ] && exit 0
cd "$REPO_ROOT" || exit 0

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && PAYLOAD=$(cat 2>/dev/null || echo '{}')

HELPER=.lazy-harness/hooks/lifecycle/helpers/check-context-first.sh
[ -x "$HELPER" ] || exit 0

OUT=$("$HELPER" "$PAYLOAD" 2>/dev/null || true)
[ -z "$OUT" ] && exit 0

HOOK_BODY="$OUT" python3 <<'PY'
import json
import os
print(json.dumps({"action": "deny", "reason": os.environ.get("HOOK_BODY", "")}, ensure_ascii=False))
PY
exit 1
