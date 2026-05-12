#!/usr/bin/env bash
# check-ddd-trigger.sh — 5c-1 DDD term trigger detector
#
# Input: response.completed payload as argv[1]
# Output: deny reason containing structured ask, or empty.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

TRIGGER_TS=".lazy-harness/triggers/code-change.ts"
[ ! -f "$TRIGGER_TS" ] && exit 0

# Only run when the response payload indicates code/file writes in triggerable scopes.
# ADR 0017: user input channels are represented by payload + tool calls, no external adapter.
FILES=$(PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json
import os
import re

try:
    payload = json.loads(os.environ.get("PAYLOAD_JSON", "{}"))
except Exception:
    raise SystemExit(0)

paths = []
allowed_names = {
    "Write",
    "Edit",
    "MultiEdit",
    "write",
    "edit",
    "multiedit",
    "mcp__filesystem__write_file",
    "mcp__filesystem__edit_file",
}
pattern = re.compile(r"(?:src/main|\.lazy-harness/triggers/fixtures)/[^\s\"'`,)}]+\.(?:ts|tsx)")

for call in payload.get("recent_tool_calls", []):
    name = str(call.get("name", ""))
    args = str(call.get("args_preview", ""))
    if name not in allowed_names:
        continue
    for match in pattern.finditer(args):
        paths.append(match.group(0))

print("\n".join(dict.fromkeys(paths)))
PY
)

[ -z "$FILES" ] && exit 0

EXISTING_FILES=""
while IFS= read -r file; do
  [ -f "$file" ] || continue
  case "$file" in
    *.test.ts|*.test.tsx|*.spec.ts|*.spec.tsx) continue ;;
  esac
  EXISTING_FILES="$EXISTING_FILES${EXISTING_FILES:+,}$file"
done <<EOF
$FILES
EOF

[ -z "$EXISTING_FILES" ] && exit 0

ASK=$(bun "$TRIGGER_TS" --files "$EXISTING_FILES" --format ask 2>/dev/null || true)
[ -z "$ASK" ] && exit 0

case "$ASK" in
  *"후보 없음"*) exit 0 ;;
esac

cat <<EOF
STOP. 5c-1 DDD trigger 후보가 검출되었습니다. 자동 반영하지 말고 사용자에게 아래 구조화 옵션으로 확인하세요.

$ASK

규칙: ubiquitous-language.xml 직접 수정 금지. 사용자가 A/B/C/D 중 선택하거나 직접 입력할 때까지 ask 하세요. Principle 17/21/23.
EOF

exit 0
