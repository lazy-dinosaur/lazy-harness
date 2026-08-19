#!/usr/bin/env bash
# on-context.sh — pointer-only Pi/OMP work-unit continuation reminder.
#
# The adapter invokes this only after the first successful mutation batch boundary.
# It deliberately performs no map, policy, capability, or record lookup: those
# results belong to the work-unit grounding cache and must not be replayed into
# the conversation after every file operation.

set +e

PAYLOAD=$(cat || echo '{}')
ROOT_CANDIDATE="${LAZY_HOST_ROOT:-}"
if [ -z "$ROOT_CANDIDATE" ] || [ ! -d "$ROOT_CANDIDATE/.lazy-harness" ]; then
  ROOT_CANDIDATE=$(PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json, os
try:
    data = json.loads(os.environ.get('PAYLOAD_JSON') or '{}')
except Exception:
    data = {}
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

python3 <<'PY'
import json
body = '\n'.join([
    'REMINDER. Continue the approved work unit without restarting discovery.',
    '- Reuse the map/record evidence already collected; do not reread unchanged records after each file operation.',
    '- Re-ground only for a genuinely new scope, an explicit steer, or a changed/deleted governing record.',
    '- Finish the coherent mutation batch before validation; keep green output to a short summary.',
    '- Stop only for a real record↔code conflict or a new user decision.',
]) + '\n'
print(json.dumps({'action': 'allow', 'inject': {'body': body, 'format': 'system_reminder'}}, ensure_ascii=False))
PY
