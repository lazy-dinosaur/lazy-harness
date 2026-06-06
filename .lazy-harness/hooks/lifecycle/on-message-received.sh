#!/usr/bin/env bash
# on-message-received.sh — pre-turn lazy-harness static inventory/search prompt for Jcode message.received.
#
# This hook deliberately does not run relevant-record-query/context-delivery or any
# semantic search backend. It also deliberately does not interpret user text with
# meaning-specific regex/classifier branches. It is a static transport: inject a
# compact harness inventory/search protocol for the LLM/searcher and journal
# sanitized search-debt so the generic evidence guard/audit can verify that
# harness-following search happened before action.

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

if [ -f .lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh ]; then
  # shellcheck disable=SC1091
  . .lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh
  lazy_export_runtime_env "$ROOT_CANDIDATE" "$PAYLOAD"
fi

python3 - "$ROOT_CANDIDATE" "$PAYLOAD" <<'PY'
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

root = Path(sys.argv[1])
payload_raw = sys.argv[2] if len(sys.argv) > 2 else '{}'
try:
    payload = json.loads(payload_raw) if payload_raw.strip() else {}
except Exception:
    payload = {}
if not isinstance(payload, dict):
    raise SystemExit(0)

has_message = bool(str(payload.get('last_user_message') or payload.get('message') or '').strip())
if not has_message:
    raise SystemExit(0)

def stable_hash(value: Any) -> str | None:
    text = str(value or '').strip()
    if not text:
        return None
    return hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()[:16]


level = 'harness-first-static'
message_id = payload.get('message_id') or payload.get('messageId')
session_id = payload.get('session_id') or payload.get('sessionId')
turn_count = payload.get('turn_count') or payload.get('turnCount')
epoch = int(time.time())

search_hint = '.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,plans,project,knowledge}/ + source + tests'
packet_hash_seed = json.dumps({
    'messageIdHash': stable_hash(message_id),
    'sessionIdHash': stable_hash(session_id),
    'turnCount': turn_count,
    'instructionLevel': level,
    'epochBucket': epoch // 60,
}, ensure_ascii=False, sort_keys=True)
row = {
    'schemaVersion': '1.0',
    'event': 'message.received.direct-search-debt',
    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(epoch)),
    'epochSeconds': epoch,
    'messageIdHash': stable_hash(message_id),
    'sessionIdHash': stable_hash(session_id),
    'packetHash': hashlib.sha256(packet_hash_seed.encode('utf-8')).hexdigest()[:16],
    'instructionLevel': level,
    'confidence': 0,
    'requiredReadCount': 0,
    'optionalReadCount': 0,
    'candidateMeaningCount': 0,
    'fallbackSearchCount': 1,
    'requiredRead': [],
    'optionalRead': [],
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
    journal = runtime_root / 'state' / 'context-delivery-packets.jsonl'
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
    index_names = ['implementation-index.json', 'reference-index.json', 'relevant-record-index.json', 'context-index.json']
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
    'STOP. Harness-first search/read debt before response.',
    f'- Instruction: {level}; static transport; no user-text classification; no CLI/index semantic authority.',
    '- Before answer/plan/edit: inspect real `.lazy-harness` records/source/tests in this host root; stay read-only until debt is satisfied.',
    f'- Search scope: `{search_hint}`',
    *harness_inventory_lines(),
    '- Protocol: choose real candidate records from inventory → read Rule digest/full body/Implementation map/graph links → inspect source/tests → answer, or ask a 3-5 option gate if meanings/layers still conflict.',
    '- Missing record: search current host code/docs/package/config; after user confirmation converge durable knowledge into the right `.lazy-harness/<layer>/...` record.',
    '- Guard: action/mutation remains blocked by the generic evidence guard until root-bound harness-following search/read evidence exists.',
]).strip() + '\n'

print(json.dumps({
    'action': 'allow',
    'inject': {
        'body': body,
        'format': 'system_reminder',
    }
}, ensure_ascii=False))
PY
