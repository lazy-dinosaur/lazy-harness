#!/usr/bin/env bash
# check-bdd-trigger.sh — 5c-3 BDD scenario trigger detector
#
# Input: response.completed payload as argv[1]
# Output: deny reason containing structured ask, or empty.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

TRIGGER_TS=".lazy-harness/triggers/code-change.ts"
[ ! -f "$TRIGGER_TS" ] && exit 0

PARSED=$(PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json, os, re
try:
    payload = json.loads(os.environ.get('PAYLOAD_JSON', '{}'))
except Exception:
    raise SystemExit(0)

last = payload.get('last_user_message') or ''
paths = []
allowed = {'Write','Edit','MultiEdit','write','edit','multiedit','mcp__filesystem__write_file','mcp__filesystem__edit_file'}
pattern = re.compile(r'(?:src/renderer/src|\.lazy-harness/triggers/fixtures)/[^\s"\'`,)}]+\.(?:tsx|ts)')
for call in payload.get('recent_tool_calls', []):
    if str(call.get('name', '')) not in allowed:
        continue
    args = str(call.get('args_preview', ''))
    for match in pattern.finditer(args):
        paths.append(match.group(0))

print(json.dumps({'last': last, 'files': list(dict.fromkeys(paths))}, ensure_ascii=False))
PY
)
[ -z "$PARSED" ] && exit 0

LAST_USER_MESSAGE=$(printf '%s' "$PARSED" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("last", ""))' 2>/dev/null || true)
FILES=$(printf '%s' "$PARSED" | python3 -c 'import json,sys; print("\n".join(json.load(sys.stdin).get("files", [])))' 2>/dev/null || true)

EXISTING_FILES=""
while IFS= read -r file; do
  [ -n "$file" ] || continue
  [ -f "$file" ] || continue
  case "$file" in
    *.test.tsx|*.spec.tsx) continue ;;
  esac
  EXISTING_FILES="$EXISTING_FILES${EXISTING_FILES:+,}$file"
done <<EOF_FILES
$FILES
EOF_FILES

ARGS=("$TRIGGER_TS" --layer bdd --format ask)
[ -n "$EXISTING_FILES" ] && ARGS+=(--files "$EXISTING_FILES")
[ -n "$LAST_USER_MESSAGE" ] && ARGS+=(--last-user-message "$LAST_USER_MESSAGE")

# Run when either the user utterance is a likely NL flow or renderer TSX files were touched.
[ -z "$EXISTING_FILES" ] && [ -z "$LAST_USER_MESSAGE" ] && exit 0

ASK=$(bun "${ARGS[@]}" 2>/dev/null || true)
[ -z "$ASK" ] && exit 0
case "$ASK" in
  *"후보 없음"*) exit 0 ;;
esac

cat <<EOF_DENY
STOP. 5c-3 BDD scenario 후보가 검출되었습니다. 자동 반영하지 말고 사용자에게 아래 구조화 옵션으로 확인하세요.

$ASK

규칙: behavior-map.xml 직접 수정 금지. 사용자가 A/B/C/D 중 선택하거나 직접 입력할 때까지 ask 하세요. ADR 0018 cross-ref + ADR 0019 force/recommend gate.
EOF_DENY

exit 0
