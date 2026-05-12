#!/usr/bin/env bash
# check-aftershock-reanalysis.sh — 5d-4 aftershock gate helper
#
# Input: response.completed payload as argv[1]
# Output: deny reason containing structured ask, or empty.
# Runs only when decisions.jsonl was changed in this response payload.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

SCRIPT=".lazy-harness/scripts/aftershock-reanalysis.ts"
QUEUE="${LAZY_HARNESS_QUESTION_QUEUE:-.lazy-harness/questions/open.xml}"
DECISIONS="${LAZY_HARNESS_DECISIONS_FILE:-.lazy-harness/logs/decisions.jsonl}"
[ ! -f "$SCRIPT" ] && exit 0

TOUCHED=$(PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json, os
try:
    payload = json.loads(os.environ.get('PAYLOAD_JSON', '{}'))
except Exception:
    raise SystemExit(0)
allowed = {'Write','Edit','MultiEdit','write','edit','multiedit','mcp__filesystem__write_file','mcp__filesystem__edit_file'}
for call in payload.get('recent_tool_calls', []):
    if str(call.get('name', '')) not in allowed:
        continue
    if '.lazy-harness/logs/decisions.jsonl' in str(call.get('args_preview', '')):
        print('1')
        break
PY
)

[ "$TOUCHED" = "1" ] || exit 0

RESULT=$(bun "$SCRIPT" --decisions "$DECISIONS" --queue "$QUEUE" --format json 2>/dev/null || true)
[ -z "$RESULT" ] && exit 0
CREATED=$(printf '%s' "$RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("created", 0))' 2>/dev/null || true)
[ "${CREATED:-0}" = "0" ] && exit 0
ASKS=$(RESULT_JSON="$RESULT" python3 <<'PY' 2>/dev/null || true
import json, os
try:
    data=json.loads(os.environ.get('RESULT_JSON', '{}'))
except Exception:
    raise SystemExit(0)
for q in data.get('questions', []):
    print(f"- {q.get('id')}: {q.get('question')}")
    for opt in q.get('options', []):
        print(f"  {opt.get('id')}. {opt.get('label')}")
PY
)

cat <<EOF_DENY
STOP. 5d-4 Aftershock Re-analysis: 방금 기록한 decision 이 후속 정합성 질문을 만들었습니다.

$ASKS

규칙: A/B/C/D 중 하나를 사용자에게 확인하고, 답변은 interview-loop decision 으로 기록하세요. ADR 0018 cascade + ADR 0019 force gate.
EOF_DENY

exit 0
