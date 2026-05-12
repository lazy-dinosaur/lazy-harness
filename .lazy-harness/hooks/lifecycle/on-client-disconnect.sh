#!/usr/bin/env bash
# on-client-disconnect.sh — lifecycle hook for jcode client.disconnect event
#
# Triggered: TUI 창 닫기 / ctrl-c / crash 시 (M11 Stage 4 신규)
# Purpose: 세션 종료 cleanup — progress / handoff / final snapshot
#
# Stdin: JSON payload
#   {
#     "event": "client.disconnect",
#     "session_id": "...",
#     "working_dir": "...",
#     "reason": "...",
#     "message_count": N,
#     "last_user_message": "...",
#     "recent_tool_calls": [...],
#     "turn_count": N,
#     "session_age_seconds": N
#   }
#
# Non-blocking: 결과는 무시됨 (이미 disconnect 진행)
# Errors: silenced (사용자 짜증 방지)

set +e  # Never fail

[ -f .lazy-harness/.hooks-disabled ] && exit 0

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_ROOT" ] || [ ! -d "$REPO_ROOT/.lazy-harness" ] && exit 0
cd "$REPO_ROOT"

PAYLOAD=$(cat || echo '{}')
TIMESTAMP=$(date -Iseconds)
TODAY=$(date +%Y-%m-%d)

# Parse payload (silent fail)
SESSION_ID=$(echo "$PAYLOAD" | python3 -c "import json,sys; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null || echo "")
TURN_COUNT=$(echo "$PAYLOAD" | python3 -c "import json,sys; print(json.load(sys.stdin).get('turn_count',0))" 2>/dev/null || echo "0")
SESSION_AGE=$(echo "$PAYLOAD" | python3 -c "import json,sys; print(json.load(sys.stdin).get('session_age_seconds',0))" 2>/dev/null || echo "0")

# === 1. last-session.json 기록 (다음 세션 진입 시 SessionStart hook 이 읽음) ===
mkdir -p .lazy-harness/state
python3 -c "
import json
data = {
    'session_id': '$SESSION_ID',
    'ended_at': '$TIMESTAMP',
    'turn_count': $TURN_COUNT,
    'session_age_seconds': $SESSION_AGE,
    'reason': $(echo "$PAYLOAD" | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin).get(\"reason\",\"\")))' 2>/dev/null || echo '""')
}
with open('.lazy-harness/state/last-session.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
" 2>/dev/null

# === 2. progress/<today>.md 에 session summary append ===
PROGRESS_FILE=".lazy-harness/progress/$TODAY.md"
mkdir -p .lazy-harness/progress
if [ -f "$PROGRESS_FILE" ]; then
  cat >> "$PROGRESS_FILE" 2>/dev/null <<EOF

---

## $TIMESTAMP — Session disconnect

- session_id: $SESSION_ID
- turn_count: $TURN_COUNT
- session_age: ${SESSION_AGE}s ($((SESSION_AGE/60)) min)
- reason: $(echo "$PAYLOAD" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("reason",""))' 2>/dev/null)
EOF
fi

# === 3. actions.jsonl 에 disconnect 이벤트 기록 ===
LOG=".lazy-harness/logs/actions.jsonl"
mkdir -p "$(dirname "$LOG")"
python3 -c "
import json
print(json.dumps({
    'timestamp': '$TIMESTAMP',
    'actor': 'jcode-hook',
    'action': 'client.disconnect',
    'sessionId': '$SESSION_ID',
    'turnCount': $TURN_COUNT,
    'sessionAgeSeconds': $SESSION_AGE
}, ensure_ascii=False))
" >> "$LOG" 2>/dev/null

exit 0
