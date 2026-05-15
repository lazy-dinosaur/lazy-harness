#!/usr/bin/env bash
# check-option-gate-discipline.sh — prevent option-gate loops and self-selection

set -euo pipefail
PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json, os, re, sys
try:
    payload = json.loads(os.environ.get('PAYLOAD_JSON', '{}'))
except Exception:
    sys.exit(0)

strings=[]
def walk(v):
    if isinstance(v, str): strings.append(v)
    elif isinstance(v, dict):
        for c in v.values(): walk(c)
    elif isinstance(v, list):
        for c in v: walk(c)
walk(payload)
blob='\n'.join(strings)
lower=blob.lower()
if not blob.strip(): sys.exit(0)

has_gate = (
    'needs-option-gate' in lower
    or '선택해주세요' in blob
    or '진행 선택 필요' in blob
    or '진행 선택:' in blob
)
if not has_gate:
    sys.exit(0)

# If any tool call happened in the same turn as an unresolved option gate, the
# agent did not actually stop for the user.
write_or_exec = False
for call in payload.get('recent_tool_calls', []) or []:
    name = str(call.get('name', '')).lower()
    if name in {'write','edit','multiedit','bash','apply_patch','patch'} or 'write_file' in name or 'edit_file' in name:
        write_or_exec = True
        break

self_selection_action_cues = [
    '자가선택', '알아서 선택', '진행하겠습니다', '실행하겠습니다', 'dispatch 하겠습니다',
    'dispatch 했', 'dispatch했습니다', '선택했습니다', '진행 선택:', '기록 완료', 'ssot 기록 완료',
]
completion_cues = [
    'user-confirmed', 'inferred-from-record', 'record에 이미', '기록 완료', '완료했습니다',
    '하겠습니다', '했습니다',
]
self_selected = any(cue.lower() in lower for cue in self_selection_action_cues) and any(cue in lower for cue in completion_cues)

if not write_or_exec and not self_selected:
    sys.exit(0)

print('STOP. Option gate discipline: `needs-option-gate` 는 사용자 선택 대기 상태입니다.\n')
print('문제: 옵션 게이트를 띄운 같은 turn 에 도구를 실행하거나 Recommended 를 자가선택한 정황이 있습니다.')
print('\n해야 할 일:')
print('  A. 도구 실행/record 작성/release dispatch 를 중단하고 사용자 선택을 기다림 (Recommended)')
print('  B. 사용자가 이미 선택했다면 Confirmation 을 `user-confirmed` 로 바꾸고 같은 옵션을 다시 묻지 않음')
print('  C. record 근거가 명확하면 Confirmation 을 `inferred-from-record` 로 쓰고 옵션 게이트를 띄우지 않음')
print('  D. 의식적 예외라면 .lazy-harness/logs/skipped.jsonl 에 사유 기록')
print('\n규칙: AGENTS §2.3, .lazy-harness/ssot/rule-sources.md option-gate discipline.')
PY
