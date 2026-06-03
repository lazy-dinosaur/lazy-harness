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
    journal = root / '.lazy-harness' / 'state' / 'context-delivery-packets.jsonl'
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
    lines.append('Harness inventory (actual files first, compact):')
    lines.append('- Actual record layers:')
    for label, folder, meaning in LAYER_INVENTORY:
        layer_path = root / '.lazy-harness' / folder
        count, samples = list_files_limited(layer_path)
        sample_text = ', '.join(f'`{sample}`' for sample in samples) if samples else 'none'
        lines.append(f'  - {label}=`.lazy-harness/{folder}/` ({meaning}): {count} file(s); sample: {sample_text}')

    generated = root / '.lazy-harness' / 'generated'
    index_names = ['implementation-index.json', 'reference-index.json', 'relevant-record-index.json', 'context-index.json']
    statuses = []
    for name in index_names:
        p = generated / name
        statuses.append(f'{name}={"present" if p.exists() else "missing"}')
    lines.append('- Generated indexes (derived, not canonical): ' + '; '.join(statuses))

    pointers = [
        ('.lazy-harness/knowledge/graph.jsonl', root / '.lazy-harness' / 'knowledge' / 'graph.jsonl'),
        ('.lazy-harness/knowledge/candidates.jsonl', root / '.lazy-harness' / 'knowledge' / 'candidates.jsonl'),
        ('.lazy-harness/project/feature-navigation.xml', root / '.lazy-harness' / 'project' / 'feature-navigation.xml'),
        ('.lazy-harness/generated/README.md', root / '.lazy-harness' / 'generated' / 'README.md'),
    ]
    pointer_text = '; '.join(f'{name}={"present" if path.exists() else "missing"}' for name, path in pointers)
    lines.append('- Canonical/derived pointers: ' + pointer_text)

    source_dirs = []
    for name in ['src', 'tests', 'test', 'packages', 'apps', 'lib', 'docs']:
        if (root / name).exists():
            source_dirs.append(name)
    lines.append('- Source/test/doc dirs present: ' + (', '.join(source_dirs) if source_dirs else 'none detected'))
    return lines


body = '\n'.join([
    'STOP. Harness-first lazy-harness search-debt before response',
    f'- Instruction: {level}',
    '- Static transport: this shell hook does not classify or interpret the user message; understanding belongs to the LLM/searcher or an explicit read-only searcher handoff.',
    '- Do not use a CLI/index/search backend as semantic authority for this turn.',
    '- Before answering, analyzing, planning, option-gating, or editing, the LLM/searcher must follow the harness and directly inspect stored records/files.',
    f'- Search scope: `{search_hint}`',
    *harness_inventory_lines(),
    '- Root-bound exploration affordances (examples, not a tool policy): use any read-only/search/query tool that follows the harness, stays in this host root, and inspects actual stored records/files. Examples include `ls`, `find`, `tree`/directory tree, `git ls-files`, `rg`, `grep`, `agentgrep`, `glob`, `read`, and read-only searcher handoff.',
    '- Search protocol: (1) inspect the actual inventory above and choose candidate records from real filenames/layers/index pointers, (2) list/read matching stored records and their `## Rule digest`, full body, Related records, Implementation map, and graph links, (3) search source/tests only for confirmed files/symbols, (4) only after inventory/content grounding expand multilingual/code aliases or broader string queries, (5) only then answer/plan/edit.',
    '- Evidence examples (examples, not a required tool list): `find .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning} -maxdepth 2 -type f`, `tree .lazy-harness | head -200`, `git ls-files`, `rg -n <confirmed terms> .lazy-harness src tests`, `agentgrep`, then `read` concrete records/files.',
    '- If no record exists, search current host code/docs/package/config and converge missing durable knowledge into the right `.lazy-harness/<layer>/...` record after user confirmation.',
    '- If meanings or layer placement still conflict after search/read evidence, ask a 3-5 option gate with Recommended and a custom option; do not self-select.',
    '- Before debt is satisfied: keep to read-only inventory/search/read or explicit read-only searcher handoff. Action/mutation tools remain blocked by the generic evidence guard.',
]).strip() + '\n'

print(json.dumps({
    'action': 'allow',
    'inject': {
        'body': body,
        'format': 'system_reminder',
    }
}, ensure_ascii=False))
PY
