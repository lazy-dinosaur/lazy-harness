#!/usr/bin/env bash
# on-tool-execute-before.sh — lifecycle hook for jcode tool.execute.before event
#
# Triggered: tool.execute.before for all tool calls.
# Purpose: generic packet-scoped search/read evidence guard. It does not perform
#          semantic search and does not encode concrete-tool project policy.
#          If message.received produced search/read debt and the LLM/searcher has
#          not left root-bound search/read evidence yet, emit deny guidance.
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
# This hook is a framework safety net. Normal record-first/search-first flows stay silent.

set +e

ROOT_CANDIDATE="${LAZY_HOST_ROOT:-}"
if [ -z "$ROOT_CANDIDATE" ] || [ ! -d "$ROOT_CANDIDATE/.lazy-harness" ]; then
  ROOT_CANDIDATE="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi
[ -z "$ROOT_CANDIDATE" ] || [ ! -d "$ROOT_CANDIDATE/.lazy-harness" ] && exit 0
cd "$ROOT_CANDIDATE" || exit 0

[ -f .lazy-harness/.hooks-disabled ] && exit 0

# Stdin OR argv1
PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && PAYLOAD=$(cat 2>/dev/null || echo '{}')

# Chain through helpers — read-debt permit first, then legacy Layer 2 checks.
for helper in \
  .lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py \
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
