#!/usr/bin/env bash
# check-bdd-trigger.sh — 5c-3 BDD scenario candidate detector
#
# Input: response.completed payload as argv[1]
# Output: empty. BDD trigger candidates are accumulated as non-blocking
# `.lazy-harness/knowledge/candidates.jsonl` entries instead of repeatedly
# interrupting the user with A/B/C/D gates.
#
# Rationale:
# - BDD scenario discovery is institutional-memory capture, not product code
#   mutation approval.
# - Canonical behavior/domain/spec records still require explicit user-confirmed
#   promotion, but raw candidates should be captured automatically.
# - Repeated STOP asks for the same pending candidate break the conversation and
#   were observed in dogfooding. See TDD records for BDD option-gate loops.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

TRIGGER_TS=".lazy-harness/triggers/code-change.ts"
[ ! -f "$TRIGGER_TS" ] && exit 0

PARSED=$(PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import hashlib
import json
import os
import re

try:
    payload = json.loads(os.environ.get('PAYLOAD_JSON', '{}'))
except Exception:
    raise SystemExit(0)

last = payload.get('last_user_message') or ''
message_id = str(payload.get('message_id') or '')
paths = []
allowed = {'Write', 'Edit', 'MultiEdit', 'write', 'edit', 'multiedit',
           'mcp__filesystem__write_file', 'mcp__filesystem__edit_file'}
pattern = re.compile(r'(?:src|app|packages|\.lazy-harness/triggers/fixtures)/[^\s"\'`,)}]+\.(?:tsx|ts)')
for call in payload.get('recent_tool_calls', []) or []:
    if str(call.get('name', '')) not in allowed:
        continue
    args = str(call.get('args_preview', ''))
    for match in pattern.finditer(args):
        paths.append(match.group(0))

files_sorted = sorted(dict.fromkeys(paths))
fp_input = '|'.join(files_sorted) + '||' + last.strip()
fingerprint = hashlib.sha1(fp_input.encode('utf-8')).hexdigest()[:16]
message_hash = hashlib.sha256(message_id.encode('utf-8')).hexdigest()[:16] if message_id else ''

print(json.dumps({
    'last': last,
    'files': files_sorted,
    'messageIdHash': message_hash,
    'fingerprint': fingerprint,
}, ensure_ascii=False))
PY
)
[ -z "$PARSED" ] && exit 0

LAST_USER_MESSAGE=$(printf '%s' "$PARSED" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("last", ""))' 2>/dev/null || true)
FILES=$(printf '%s' "$PARSED" | python3 -c 'import json,sys; print("\n".join(json.load(sys.stdin).get("files", [])))' 2>/dev/null || true)
MESSAGE_ID_HASH=$(printf '%s' "$PARSED" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("messageIdHash", ""))' 2>/dev/null || true)
FINGERPRINT=$(printf '%s' "$PARSED" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("fingerprint", ""))' 2>/dev/null || true)

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

ARGS=("$TRIGGER_TS" --layer bdd --format json)
[ -n "$EXISTING_FILES" ] && ARGS+=(--files "$EXISTING_FILES")
[ -n "$LAST_USER_MESSAGE" ] && ARGS+=(--last-user-message "$LAST_USER_MESSAGE")

# Run when either the user utterance is a likely NL flow or renderer TSX files were touched.
[ -z "$EXISTING_FILES" ] && [ -z "$LAST_USER_MESSAGE" ] && exit 0

RESULT=$(bun "${ARGS[@]}" 2>/dev/null || true)
[ -z "$RESULT" ] && exit 0

RESULT_JSON="$RESULT" MESSAGE_ID_HASH="$MESSAGE_ID_HASH" INPUT_FINGERPRINT="$FINGERPRINT" python3 <<'PY' 2>/dev/null || true
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    result = json.loads(os.environ.get('RESULT_JSON', '{}'))
except Exception:
    raise SystemExit(0)

candidates = result.get('candidates') or []
if not isinstance(candidates, list) or not candidates:
    raise SystemExit(0)

path = Path('.lazy-harness/knowledge/candidates.jsonl')
existing_ids = set()
if path.exists():
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        row_id = row.get('id')
        if isinstance(row_id, str):
            existing_ids.add(row_id)

now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
message_id_hash = os.environ.get('MESSAGE_ID_HASH') or None
input_fingerprint = os.environ.get('INPUT_FINGERPRINT') or None
rows = []
for candidate in candidates:
    if candidate.get('layer') != 'bdd':
        continue
    scenario = candidate.get('scenario') or {}
    stable = json.dumps({
        'name': candidate.get('name'),
        'kind': candidate.get('kind'),
        'filePath': candidate.get('filePath'),
        'scenario': scenario,
        'source': candidate.get('source'),
    }, ensure_ascii=False, sort_keys=True)
    cid = 'cand_bdd_' + hashlib.sha1(stable.encode('utf-8')).hexdigest()[:16]
    if cid in existing_ids:
        continue
    cross_ref = ((candidate.get('metadata') or {}).get('crossRef') or {})
    rows.append({
        'id': cid,
        'createdAt': now,
        'source': 'lifecycle-bdd-trigger',
        'candidateType': 'bdd-scenario',
        'status': 'needs-confirmation',
        'confidence': candidate.get('confidence'),
        'detectedLayers': ['BDD'],
        'topic': candidate.get('name'),
        'summary': f"BDD scenario candidate '{candidate.get('name')}' captured for later user-confirmed promotion.",
        'scenario': scenario,
        'evidence': {
            'reason': candidate.get('reason'),
            'source': candidate.get('source'),
            'filePath': candidate.get('filePath'),
            'line': candidate.get('line'),
            'inputFingerprint': input_fingerprint,
            'messageIdHash': message_id_hash,
        },
        'crossRef': cross_ref,
        'promotionPolicy': 'Do not modify behavior/domain/spec records automatically. Promote only after explicit user confirmation.',
    })
    existing_ids.add(cid)

if rows:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
PY

exit 0
