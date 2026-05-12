#!/usr/bin/env bash
# check-tdd-cross-verify.sh — 5d-3 TDD cross-verify gate helper
#
# Input: response.completed payload as argv[1]
# Output: deny reason containing structured ask, or empty.
# 5d-5 wires this helper into on-response-completed.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

SCRIPT=".lazy-harness/scripts/tdd-cross-verify.ts"
QUEUE="${LAZY_HARNESS_QUESTION_QUEUE:-.lazy-harness/questions/open.xml}"
[ ! -f "$SCRIPT" ] && exit 0

FILES=$(PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json, os, re
try:
    payload = json.loads(os.environ.get('PAYLOAD_JSON', '{}'))
except Exception:
    raise SystemExit(0)
allowed = {'Write','Edit','MultiEdit','write','edit','multiedit','mcp__filesystem__write_file','mcp__filesystem__edit_file'}
pattern = re.compile(r'(?:src/renderer/src|\.lazy-harness/triggers/fixtures|\.lazy-harness/triggers/walkthrough-fixtures)/[^\s"\'`,)}]+\.(?:tsx|ts|jsx|js)')
paths = []
for call in payload.get('recent_tool_calls', []):
    if str(call.get('name', '')) not in allowed:
        continue
    for match in pattern.finditer(str(call.get('args_preview', ''))):
        paths.append(match.group(0))
print(','.join(dict.fromkeys(paths)))
PY
)

[ -z "$FILES" ] && exit 0

RESULT=$(bun "$SCRIPT" --files "$FILES" --queue "$QUEUE" --format json 2>/dev/null || true)
[ -z "$RESULT" ] && exit 0
FORCE=$(printf '%s' "$RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("forceGate", False))' 2>/dev/null || true)
[ "$FORCE" != "True" ] && [ "$FORCE" != "true" ] && exit 0
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
STOP. 5d-3 TDD Cross-Verify Gate: source 변경에 대응하는 test/spec 검증이 실패했습니다.

$ASKS

규칙: A/B/C/D 중 하나를 사용자에게 확인하고, 답변은 interview-loop decision 으로 기록하세요. ADR 0020 + ADR 0019 force gate.
EOF_DENY

exit 0
