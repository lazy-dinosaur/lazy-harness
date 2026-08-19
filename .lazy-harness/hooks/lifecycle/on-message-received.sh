#!/usr/bin/env bash
# on-message-received.sh — pointer-only first-grounding transport.
#
# The hook is static and user-text-agnostic. It writes sanitized first-grounding
# debt and emits only the compact work-unit protocol; inventory, map output, mapped
# records, and policy/capability catalogs stay explicit/on-demand and are never
# replayed into every normal model turn.

set +e

PAYLOAD_FILE="$(mktemp "${TMPDIR:-/tmp}/lazy-harness-message.XXXXXX.json" 2>/dev/null || true)"
if [ -z "$PAYLOAD_FILE" ] && [ "${TMPDIR:-/tmp}" != "/tmp" ]; then
  # A stale/missing caller TMPDIR must not silently erase a valid pre-turn payload.
  PAYLOAD_FILE="$(mktemp "/tmp/lazy-harness-message.XXXXXX.json" 2>/dev/null || true)"
fi
if [ -n "$PAYLOAD_FILE" ]; then
  cat > "$PAYLOAD_FILE" || true
  PAYLOAD_REF="@file:$PAYLOAD_FILE"
  trap 'rm -f "$PAYLOAD_FILE"' EXIT
else
  # Last-resort fallback if tmp creation fails. Keep the payload empty rather than
  # passing a potentially huge prompt through argv/env and tripping ARG_MAX.
  cat >/dev/null || true
  PAYLOAD_REF=""
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -n "$PYTHON_BIN" ] && { [ ! -x "$PYTHON_BIN" ] || [ -d "$PYTHON_BIN" ]; }; then
  PYTHON_BIN=""
fi
if [ -z "$PYTHON_BIN" ]; then
  if [ -x /usr/bin/python3 ] && [ ! -d /usr/bin/python3 ]; then
    PYTHON_BIN=/usr/bin/python3
  elif [ -x /opt/homebrew/bin/python3 ] && [ ! -d /opt/homebrew/bin/python3 ]; then
    PYTHON_BIN=/opt/homebrew/bin/python3
  else
    PYTHON_BIN="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
  fi
fi
if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ] || [ -d "$PYTHON_BIN" ]; then
  exit 0
fi

ROOT_CANDIDATE="${LAZY_HOST_ROOT:-}"
if [ -z "$ROOT_CANDIDATE" ] || [ ! -d "$ROOT_CANDIDATE/.lazy-harness" ]; then
  ROOT_CANDIDATE=$(PAYLOAD_FILE="$PAYLOAD_FILE" "$PYTHON_BIN" <<'PY' 2>/dev/null || true
import json, os
payload_file = os.environ.get('PAYLOAD_FILE') or ''
try:
    raw = open(payload_file, encoding='utf-8', errors='ignore').read() if payload_file else '{}'
    data=json.loads(raw or '{}')
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

if [ -f .lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh ]; then
  # shellcheck disable=SC1091
  . .lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh
  lazy_export_runtime_env "$ROOT_CANDIDATE" "$PAYLOAD_REF"
fi

"$PYTHON_BIN" - "$ROOT_CANDIDATE" "$PAYLOAD_REF" <<'PY'
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(sys.argv[1]) / '.lazy-harness' / 'hooks' / 'lifecycle' / 'helpers'))
try:
    from host_migration_state import migration_lines as _migration_lines
except Exception:  # pragma: no cover - lifecycle helper must fail open
    _migration_lines = None

root = Path(sys.argv[1])
payload_ref = sys.argv[2] if len(sys.argv) > 2 else '{}'
try:
    if payload_ref.startswith('@file:'):
        payload_raw = Path(payload_ref[6:]).read_text(encoding='utf-8', errors='ignore')
    else:
        payload_raw = payload_ref
except Exception:
    payload_raw = '{}'
try:
    payload = json.loads(payload_raw) if payload_raw.strip() else {}
except Exception:
    payload = {}
if not isinstance(payload, dict):
    raise SystemExit(0)

has_message = bool(str(payload.get('last_user_message') or payload.get('message') or '').strip())
if not has_message:
    raise SystemExit(0)

def stable_hash(value: Any):
    text = str(value or '').strip()
    if not text:
        return None
    return hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()[:16]


level = 'harness-first-static'
message_id = payload.get('message_id') or payload.get('messageId')
session_id = payload.get('session_id') or payload.get('sessionId')
turn_count = payload.get('turn_count') or payload.get('turnCount')
epoch = int(time.time())

search_hint = 'lazy map overview/drill-down + direct reads of concrete records/source/tests'
packet_hash_seed = json.dumps({
    'messageIdHash': stable_hash(message_id),
    'sessionIdHash': stable_hash(session_id),
    'turnCount': turn_count,
    'instructionLevel': level,
    'epochBucket': epoch // 60,
}, ensure_ascii=False, sort_keys=True)
row = {
    'schemaVersion': '1.0',
    'event': 'message.received.search-read-debt',
    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(epoch)),
    'epochSeconds': epoch,
    'messageIdHash': stable_hash(message_id),
    'sessionIdHash': stable_hash(session_id),
    'packetHash': hashlib.sha256(packet_hash_seed.encode('utf-8')).hexdigest()[:16],
    'instructionLevel': level,
    'fallbackSearchCount': 1,
    'notes': [
        'directSearchPrompt=true',
        'staticTransport=true',
        'noSemanticBackend=true',
        'noUserTextSemanticBranching=true',
        'llmSearchBaseline=true',
    ],
}
try:
    runtime_root = Path(os.environ.get('LAZY_RUNTIME_ROOT') or (root / '.lazy-harness' / '.runtime'))
    journal = runtime_root / 'state' / 'search-read-debt.jsonl'
    journal.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if journal.exists():
        existing = [line for line in journal.read_text(encoding='utf-8', errors='ignore').splitlines() if line.strip()][-199:]
    existing.append(json.dumps(row, ensure_ascii=False, sort_keys=True))
    journal.write_text('\n'.join(existing) + '\n', encoding='utf-8')
except Exception:
    pass

LAYER_INVENTORY = [
    ('DDD', 'domain', 'terms/business rules'),
    ('SDD', 'spec', 'contracts/components/APIs'),
    ('BDD', 'behavior', 'UI/user flows'),
    ('TDD', 'tests', 'regressions/validation'),
    ('ADR', 'decisions', 'trade-offs/why'),
    ('SSOT', 'ssot', 'config/schema/ownership/source-of-truth'),
    ('Planning', 'planning', 'active backlog/handoffs'),
    ('Plans', 'plans', 'active plans'),
    ('Project', 'project', 'project profile/navigation'),
    ('Knowledge', 'knowledge', 'graph/candidates'),
]


def list_files_limited(base: Path, limit: int = 4) -> tuple[int, list[str]]:
    if not base.exists() or not base.is_dir():
        return 0, []
    count = 0
    samples: list[str] = []
    try:
        for current, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if not d.startswith('.'))
            for name in sorted(files):
                if name.startswith('.'):
                    continue
                count += 1
                if len(samples) < limit:
                    try:
                        samples.append(str((Path(current) / name).relative_to(root)))
                    except Exception:
                        samples.append(str(Path(current) / name))
    except Exception:
        return count, samples
    return count, samples


def harness_inventory_lines() -> list[str]:
    lines: list[str] = []
    layer_bits: list[str] = []
    for label, folder, _meaning in LAYER_INVENTORY:
        layer_path = root / '.lazy-harness' / folder
        count, _samples = list_files_limited(layer_path, limit=0)
        layer_bits.append(f'{label}={count}(`.lazy-harness/{folder}/`)')
    lines.append('- Inventory counts: ' + ' '.join(layer_bits))

    generated = root / '.lazy-harness' / 'generated'
    index_names = ['implementation-index.json', 'reference-index.json']
    statuses = []
    for name in index_names:
        p = generated / name
        statuses.append(f'{name}={"present" if p.exists() else "missing"}')
    lines.append('- Derived indexes: ' + '; '.join(statuses))

    pointers = [
        ('.lazy-harness/knowledge/graph.jsonl', root / '.lazy-harness' / 'knowledge' / 'graph.jsonl'),
        ('.lazy-harness/knowledge/candidates.jsonl', root / '.lazy-harness' / 'knowledge' / 'candidates.jsonl'),
        ('.lazy-harness/project/feature-navigation.xml', root / '.lazy-harness' / 'project' / 'feature-navigation.xml'),
        ('.lazy-harness/generated/README.md', root / '.lazy-harness' / 'generated' / 'README.md'),
    ]
    pointer_text = '; '.join(f'{name}={"present" if path.exists() else "missing"}' for name, path in pointers)
    lines.append('- Pointers: ' + pointer_text)

    source_dirs = []
    for name in ['src', 'tests', 'test', 'packages', 'apps', 'lib', 'docs']:
        if (root / name).exists():
            source_dirs.append(name)
    lines.append('- Source/test/doc dirs: ' + (', '.join(source_dirs) if source_dirs else 'none detected'))
    return lines


body = '\n'.join([
    'REMINDER. Ground this work unit once before mutation or a host-specific completion claim.',
    f'- Mode: {level}; static transport; no user-text classification; generated indexes are navigation only.',
    '- First grounding only: run `lazy map --overview --complete`, drill into one copied concrete node, then read only the governing digest and exact linked source/test needed for this work unit.',
    '- Reuse unchanged grounding across later messages. Re-ground only for a genuinely new scope, an explicit steer, or a changed/deleted governing record; do not repeat map/read just because a new turn started.',
    '- Batch coherent mutations. Never validate between micro-edits; use one focused checkpoint when needed and one final `lazy validate --plan standard`.',
    '- Before a new decision, use the native option gate; capture confirmed durable knowledge once at work-unit closure.',
    *(_migration_lines(str(root / '.lazy-harness' / 'bin' / 'lazy'), str(root)) if _migration_lines else []),
]).strip() + '\n'

print(json.dumps({
    'action': 'allow',
    'inject': {
        'body': body,
        'format': 'system_reminder',
    }
}, ensure_ascii=False))
PY
status=$?
if [ "$status" -ne 0 ]; then
  printf '%s\n' '{"action":"allow","inject":{"body":"REMINDER. Ground this work unit once before mutation or a host-specific completion claim.\n- Hook fallback: run one lazy map overview, drill into a concrete node, and read only the governing evidence before mutation.\n","format":"system_reminder"}}'
fi
exit 0
