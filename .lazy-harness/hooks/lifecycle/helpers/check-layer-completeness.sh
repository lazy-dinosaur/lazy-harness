#!/usr/bin/env bash
# check-layer-completeness.sh — prevent TDD/regression-only record completion
#
# If an agent writes a TDD/regression record, it must also document the cross-layer
# impact check in the same turn. Either update SDD/BDD/SSOT/DDD records or add a
# `Layer completeness` section to the TDD record that explicitly mentions all four.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

FILES=$(PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json, os, re
try:
    payload = json.loads(os.environ.get('PAYLOAD_JSON', '{}'))
except Exception:
    raise SystemExit(0)
allowed = {'Write','Edit','MultiEdit','write','edit','multiedit','mcp__filesystem__write_file','mcp__filesystem__edit_file'}
pattern = re.compile(r'\.lazy-harness/(?:domain|spec|behavior|tests|decisions|ssot|regression)/[^\s"\'`,)}]+\.(?:md|jsonl|xml|json)')
paths = []
for call in payload.get('recent_tool_calls', []):
    if str(call.get('name', '')) not in allowed:
        continue
    for match in pattern.finditer(str(call.get('args_preview', ''))):
        paths.append(match.group(0))
print('\n'.join(dict.fromkeys(paths)))
PY
)

[ -z "$FILES" ] && exit 0

TOUCHED_TDD=0
TOUCHED_OTHER_LAYER=0
MISSING_COMPLETENESS=()

while IFS= read -r file; do
  [ -n "$file" ] || continue
  case "$file" in
    .lazy-harness/tests/test-strategy.xml) continue ;;
    .lazy-harness/tests/*.md|.lazy-harness/regression/*.jsonl|.lazy-harness/regression/*.md)
      TOUCHED_TDD=1
      ;;
    .lazy-harness/spec/*|.lazy-harness/spec/**/*|.lazy-harness/behavior/*|.lazy-harness/behavior/**/*|.lazy-harness/ssot/*|.lazy-harness/domain/*|.lazy-harness/domain/**/*)
      TOUCHED_OTHER_LAYER=1
      ;;
  esac
done <<EOF_FILES
$FILES
EOF_FILES

[ "$TOUCHED_TDD" = "1" ] || exit 0
[ "$TOUCHED_OTHER_LAYER" = "1" ] && exit 0

# If no cross-layer record was touched, every TDD markdown record in the payload
# must carry an explicit local completeness judgement.
while IFS= read -r file; do
  [ -n "$file" ] || continue
  case "$file" in
    .lazy-harness/tests/*.md)
      if [ ! -f "$file" ]; then
        MISSING_COMPLETENESS+=("$file")
        continue
      fi
      TEXT=$(cat "$file")
      case "$TEXT" in
        *"Layer completeness"*"SDD"*"BDD"*"SSOT"*"DDD"*) ;;
        *) MISSING_COMPLETENESS+=("$file") ;;
      esac
      ;;
    .lazy-harness/regression/*.jsonl|.lazy-harness/regression/*.md)
      # Regression-only writes are incomplete unless paired with another layer.
      MISSING_COMPLETENESS+=("$file")
      ;;
  esac
done <<EOF_FILES
$FILES
EOF_FILES

[ "${#MISSING_COMPLETENESS[@]}" -eq 0 ] && exit 0

printf 'STOP. Layer completeness gate: TDD/regression record 만 쓰고 SDD/BDD/SSOT/DDD 영향 판단이 빠졌습니다.\n\n'
printf '누락 후보:\n'
printf '  - %s\n' "${MISSING_COMPLETENESS[@]}"
printf '\n해야 할 일:\n'
printf '  A. 관련 SDD/BDD/SSOT/DDD record 를 같은 turn 에 추가/갱신 (Recommended)\n'
printf '  B. TDD record 에 `Layer completeness` 섹션을 추가하고 SDD/BDD/SSOT/DDD 각각 영향 없음/있음 판단 기록\n'
printf '  C. layer 가 애매하면 사용자에게 옵션 게이트로 확인\n'
printf '  D. 직접 입력 / skip 사유를 .lazy-harness/logs/skipped.jsonl 에 기록\n'
printf '\n규칙: AGENTS §2.4 Layer completeness gate. TDD 만 추가하고 끝내면 안 됩니다.\n'
