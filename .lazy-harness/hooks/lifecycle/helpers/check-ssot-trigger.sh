#!/usr/bin/env bash
# check-ssot-trigger.sh — 5c-4 SSOT helper/mapper/validator trigger detector
#
# Input: response.completed payload as argv[1]
# Output: deny reason containing structured ask, or empty.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

TRIGGER_TS=".lazy-harness/triggers/code-change.ts"
[ ! -f "$TRIGGER_TS" ] && exit 0

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
pattern = re.compile(r"(?:src/main|src/renderer/src|\.lazy-harness/triggers/fixtures)/[^\s\"'`,)}]+\.(?:ts|tsx)")

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
  [ -n "$file" ] || continue
  [ -f "$file" ] || continue
  case "$file" in
    *.test.ts|*.test.tsx|*.spec.ts|*.spec.tsx) continue ;;
  esac
  EXISTING_FILES="$EXISTING_FILES${EXISTING_FILES:+,}$file"
done <<EOF_FILES
$FILES
EOF_FILES

[ -z "$EXISTING_FILES" ] && exit 0

ASK=$(bun "$TRIGGER_TS" --files "$EXISTING_FILES" --layer ssot --format ask 2>/dev/null || true)
[ -z "$ASK" ] && exit 0
case "$ASK" in
  *"후보 없음"*) exit 0 ;;
esac

cat <<EOF_DENY
STOP. 5c-4 SSOT utility 후보가 검출되었습니다. 자동 반영하지 말고 사용자에게 아래 구조화 옵션으로 확인하세요.

$ASK

규칙: ssot/registry.xml 직접 수정 금지. 사용자가 A/B/C/D/E 중 선택하거나 직접 입력할 때까지 ask 하세요. ADR 0018 cross-ref + ADR 0019 force/recommend gate.
EOF_DENY

exit 0
