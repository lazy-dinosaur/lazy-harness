#!/usr/bin/env bash
# on-message-received.sh — pre-turn lazy-harness context hook for Jcode message.received.
# Emits same-turn system reminder injection with compact relevant record digest.

set +e

PAYLOAD=$(cat || echo '{}')

ROOT_CANDIDATE="${LAZY_HOST_ROOT:-}"
if [ -z "$ROOT_CANDIDATE" ] || [ ! -d "$ROOT_CANDIDATE/.lazy-harness" ]; then
  ROOT_CANDIDATE=$(PAYLOAD="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json, os
try:
    data=json.loads(os.environ.get('PAYLOAD') or '{}')
except Exception:
    data={}
print(data.get('working_dir') or data.get('cwd') or '')
PY
)
fi
if [ -z "$ROOT_CANDIDATE" ] || [ ! -d "$ROOT_CANDIDATE/.lazy-harness" ]; then
  ROOT_CANDIDATE="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi
[ -z "$ROOT_CANDIDATE" ] || [ ! -d "$ROOT_CANDIDATE/.lazy-harness" ] && exit 0
cd "$ROOT_CANDIDATE" || exit 0

[ -f .lazy-harness/.hooks-disabled ] && exit 0
[ ! -f .lazy-harness/scripts/relevant-record-query.ts ] && exit 0
command -v bun >/dev/null 2>&1 || exit 0

python3 - "$ROOT_CANDIDATE" "$PAYLOAD" <<'PY'
import json
import os
import subprocess
import sys
import time
from pathlib import Path

root = Path(sys.argv[1])
payload_raw = sys.argv[2] if len(sys.argv) > 2 else '{}'
try:
    payload = json.loads(payload_raw) if payload_raw.strip() else {}
except Exception:
    payload = {}

message = str(payload.get('last_user_message') or '').strip()
if not message:
    raise SystemExit(0)

script = root / '.lazy-harness' / 'scripts' / 'relevant-record-query.ts'
if not script.exists():
    raise SystemExit(0)

limit = os.environ.get('LAZY_MESSAGE_RECEIVED_QUERY_LIMIT', '5')
budget = os.environ.get('LAZY_MESSAGE_RECEIVED_TOKEN_BUDGET', '600')
timeout_s = float(os.environ.get('LAZY_MESSAGE_RECEIVED_QUERY_TIMEOUT_SECONDS', '0.65'))

cmd = [
    'bun', str(script),
    '--root', str(root),
    '--message', message,
    '--format', 'md',
    '--token-budget', budget,
    '--limit', limit,
    '--require-digest',
]

recent_context = payload.get('recent_context') or payload.get('recentContext') or []
if isinstance(recent_context, list):
    for item in recent_context[:3]:
        if isinstance(item, str) and item.strip():
            cmd.extend(['--recent-context', item[:500]])

recent_tool_calls = payload.get('recent_tool_calls') or payload.get('recentToolCalls') or []
if isinstance(recent_tool_calls, list):
    for call in recent_tool_calls[-3:]:
        if not isinstance(call, dict):
            continue
        name = str(call.get('name') or '')
        args = str(call.get('args_preview') or call.get('argsPreview') or '')
        summary = ' '.join(part for part in [name, args[:240]] if part).strip()
        if summary:
            cmd.extend(['--recent-context', summary])

start = time.time()
try:
    completed = subprocess.run(cmd, cwd=str(root), text=True, capture_output=True, timeout=timeout_s, check=False)
except Exception:
    raise SystemExit(0)
finally:
    duration_ms = int((time.time() - start) * 1000)
    try:
        log = root / '.lazy-harness' / 'logs' / 'hook-timings.jsonl'
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps({
                'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'event': 'message.received',
                'component': 'relevant-record-query',
                'durationMs': duration_ms,
                'outputEmitted': False,
            }, ensure_ascii=False) + '\n')
    except Exception:
        pass

if completed.returncode != 0:
    raise SystemExit(0)

body = (completed.stdout or '').strip()
if not body:
    raise SystemExit(0)
if 'No matching rule digest found' in body:
    raise SystemExit(0)

print(json.dumps({
    'action': 'allow',
    'inject': {
        'body': body,
        'format': 'system_reminder',
    }
}, ensure_ascii=False))
PY
