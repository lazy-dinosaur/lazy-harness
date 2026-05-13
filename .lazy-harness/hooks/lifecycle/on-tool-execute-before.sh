#!/usr/bin/env bash
# on-tool-execute-before.sh — lifecycle hook for jcode tool.execute.before event
#
# Triggered: Edit / Write / MultiEdit 도구가 실행되기 직전 (모든 호출)
# Purpose: ADR 0024 의 Layer 2 (Force Gate). AGENTS.md §1 따라 능동 검색을
#          했는지 session-cache 확인. 안 했으면 deny + 검색 명령 출력.
#
# Stdin / argv: JSON payload
#   {
#     "event": "tool.execute.before",
#     "session_id": "...",
#     "tool": { "name": "Edit" | "Write" | "MultiEdit", "args": {...} }
#   }
#
# Deny: stdout 에 deny 메시지, exit 1
# Allow: stdout 비움, exit 0
#
# 본 hook 은 silent skip 을 막는 framework safety net. 정상 흐름에선 invisible.

set +e

[ -f .lazy-harness/.hooks-disabled ] && exit 0

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_ROOT" ] || [ ! -d "$REPO_ROOT/.lazy-harness" ] && exit 0
cd "$REPO_ROOT" || exit 0

# Stdin OR argv1
PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && PAYLOAD=$(cat 2>/dev/null || echo '{}')

# Chain through helpers — Layer 2 (Force Gate) checks
for helper in \
  .lazy-harness/hooks/lifecycle/helpers/check-search-performed.sh
 do
  [ -x "$helper" ] || continue
  OUT=$("$helper" "$PAYLOAD" 2>/dev/null || true)
  [ -z "$OUT" ] && continue
  HOOK_BODY="$OUT" python3 <<'PY'
import json
import os

print(json.dumps({"action": "deny", "reason": os.environ.get("HOOK_BODY", "")}, ensure_ascii=False))
PY
  exit 1
done

exit 0
