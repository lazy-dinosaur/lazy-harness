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
import re
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
context_script = root / '.lazy-harness' / 'scripts' / 'context-delivery.ts'

limit = os.environ.get('LAZY_MESSAGE_RECEIVED_QUERY_LIMIT', '5')
budget = os.environ.get('LAZY_MESSAGE_RECEIVED_TOKEN_BUDGET', '600')
timeout_s = float(os.environ.get('LAZY_MESSAGE_RECEIVED_QUERY_TIMEOUT_SECONDS', '0.65'))

cmd = [
    'bun', str(script),
    '--root', str(root),
    '--message', message,
    '--format', 'json',
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
                'outputEmitted': bool(('completed' in locals()) and getattr(completed, 'stdout', '').strip()),
            }, ensure_ascii=False) + '\n')
    except Exception:
        pass

if completed.returncode != 0:
    raise SystemExit(0)

try:
    result = json.loads(completed.stdout or '{}')
except Exception:
    raise SystemExit(0)

digest = result.get('digest') if isinstance(result, dict) else {}
entries = digest.get('entries') if isinstance(digest, dict) else []
if not isinstance(entries, list):
    entries = []

def run_context_delivery():
    if not context_script.exists():
        return None
    context_timeout_s = float(os.environ.get('LAZY_MESSAGE_RECEIVED_CONTEXT_DELIVERY_TIMEOUT_SECONDS', '0.45'))
    context_cmd = [
        'bun', str(context_script),
        '--root', str(root),
        '--message', message,
        '--format', 'json',
        '--limit', os.environ.get('LAZY_MESSAGE_RECEIVED_CONTEXT_LIMIT', '6'),
        '--journal',
    ]
    message_id = payload.get('message_id') or payload.get('messageId')
    session_id = payload.get('session_id') or payload.get('sessionId')
    turn_count = payload.get('turn_count') or payload.get('turnCount')
    if message_id:
        context_cmd.extend(['--message-id', str(message_id)])
    if session_id:
        context_cmd.extend(['--session-id', str(session_id)])
    if turn_count:
        context_cmd.extend(['--turn-count', str(turn_count)])
    try:
        context_completed = subprocess.run(
            context_cmd,
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=context_timeout_s,
            check=False,
        )
    except Exception:
        return None
    if context_completed.returncode != 0:
        return None
    try:
        packet = json.loads(context_completed.stdout or '{}')
    except Exception:
        return None
    return packet if isinstance(packet, dict) else None

def compact_bullets(entry):
    bullets = entry.get('bullets') if isinstance(entry, dict) else []
    if not isinstance(bullets, list):
        return []
    return [' '.join(str(b).split()) for b in bullets if str(b).strip()][:3]

def render_markdown(entries, truncated):
    lines = ['Relevant lazy-harness rules']
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        record_path = str(entry.get('recordPath') or '').strip()
        title = str(entry.get('title') or '').strip()
        status = str(entry.get('status') or 'active')
        if not record_path:
            continue
        suffix = '' if status == 'active' else f' [{status}]'
        lines.append(f'- `{record_path}` — {title}{suffix}')
        for bullet in compact_bullets(entry):
            lines.append(f'  - {bullet}')
        record_completion = str(entry.get('recordCompletion') or '').strip()
        if record_completion:
            lines.append(f'  - Record completion: {record_completion}')
    if truncated:
        lines.append('- ... truncated by token budget')
    return '\n'.join(lines).strip() + '\n'

def render_context_packet(packet):
    if not isinstance(packet, dict):
        return ''
    required = packet.get('requiredRead') if isinstance(packet.get('requiredRead'), list) else []
    optional = packet.get('optionalRead') if isinstance(packet.get('optionalRead'), list) else []
    instruction_level = str(packet.get('instructionLevel') or '').strip()
    confidence = packet.get('confidence')
    should_render = bool(required) or instruction_level in {'self-resolve-before-answer', 'self-resolve-before-change'}
    if not should_render:
        return ''
    lines = ['STOP. Context Delivery read-debt before response' if required else 'STOP. Context Delivery search-debt before response']
    if instruction_level:
        lines.append(f'- Instruction: {instruction_level}')
    try:
        lines.append(f'- Confidence: {float(confidence):.2f}')
    except Exception:
        pass
    if required:
        lines.append('- Required read/search before answering, analyzing, planning, option-gating, or action:')
        for item in required[:6]:
            if not isinstance(item, dict):
                continue
            path_value = str(item.get('path') or '').strip()
            if not path_value:
                continue
            kind = str(item.get('kind') or 'record')
            reason = ' '.join(str(item.get('reason') or '').split())
            lines.append(f'  - `{path_value}` ({kind})')
            if reason:
                lines.append(f'    - {reason}')
    else:
        lines.append('- No concrete requiredRead found; perform root-bound semantic search before answering, analyzing, planning, option-gating, or action.')
        lines.append('- LLM/searcher must expand user terms into likely record/code/test aliases, then search `.lazy-harness`, source, and tests.')
        lines.append('- Do not answer, analyze, propose options, or plan until that search evidence exists; ask an option gate only after search if ambiguity remains.')
    instruction = ' '.join(str(packet.get('instruction') or '').split())
    if instruction:
        lines.append(f'- Instruction detail: {instruction}')
    return '\n'.join(lines).strip() + '\n'

def is_change_intent(text):
    return bool(re.search(r'(고쳐|수정|변경|만들|구현|추가|삭제|디버그|fix|change|update|modify|build|implement|add|delete|debug|refactor)', text, re.I))

def is_surface_like(text):
    return bool(re.search(r'(예약|시트|페이지|화면|표|그리드|목록|상세|관리|sheet|table|grid|page|screen|surface|component|flow|ui|route)', text, re.I))

def render_self_resolve_protocol(text):
    if not is_surface_like(text):
        return ''
    level = 'self-resolve-before-change' if is_change_intent(text) else 'self-resolve-before-answer'
    return '\n'.join([
        'STOP. Context Delivery self-resolution before response',
        f'- Instruction: {level}',
        '- Before answering, analyzing, planning, option-gating, or editing, generate 2-5 candidate meanings and multilingual/code query expansions.',
        '- Run root-bound searches in `.lazy-harness`, source, and tests with available read/grep/bash tools.',
        '- Read high-confidence records/files before answering or acting; if candidate meanings still conflict after search/read evidence, ask an option gate.',
        '- Do not answer, analyze, propose options, or plan before root-bound search evidence exists.',
        '- Use main-agent self-search first; delegate search only when broad, risky, or parallel search would reduce risk.',
    ]).strip() + '\n'

context_packet = run_context_delivery()
context_body = render_context_packet(context_packet)
self_resolve_body = '' if context_body else render_self_resolve_protocol(message)
digest_body = render_markdown(entries, bool(digest.get('truncated'))) if entries else ''
body = '\n'.join(part.strip() for part in [digest_body, context_body, self_resolve_body] if part.strip()).strip() + '\n'
if not body.strip() or 'No matching rule digest found' in body:
    raise SystemExit(0)

def stable_hash(value):
    import hashlib
    text = str(value or '').strip()
    if not text:
        return None
    return hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()[:16]

def sanitized_entries(entries):
    out = []
    for entry in entries[:10]:
        if not isinstance(entry, dict):
            continue
        out.append({
            'recordPath': str(entry.get('recordPath') or ''),
            'title': str(entry.get('title') or ''),
            'layer': str(entry.get('layer') or ''),
            'status': str(entry.get('status') or ''),
            'scope': str(entry.get('scope') or ''),
            'recordCompletion': str(entry.get('recordCompletion') or ''),
            'bullets': compact_bullets(entry),
        })
    return [entry for entry in out if entry.get('recordPath')]

try:
    if entries:
        state_path = root / '.lazy-harness' / 'state' / 'surfaced-rule-digests.jsonl'
        state_path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            'schemaVersion': '1.0',
            'event': 'message.received.digest',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'epochSeconds': int(time.time()),
            'messageIdHash': stable_hash(payload.get('message_id') or payload.get('messageId')),
            'sessionIdHash': stable_hash(payload.get('session_id') or payload.get('sessionId')),
            'turnCount': payload.get('turn_count') or payload.get('turnCount'),
            'estimatedTokens': digest.get('estimatedTokens'),
            'truncated': bool(digest.get('truncated')),
            'injected': True,
            'entries': sanitized_entries(entries),
        }
        existing = []
        if state_path.exists():
            existing = [line for line in state_path.read_text(encoding='utf-8', errors='ignore').splitlines() if line.strip()][-199:]
        existing.append(json.dumps(row, ensure_ascii=False, sort_keys=True))
        state_path.write_text('\n'.join(existing) + '\n', encoding='utf-8')
except Exception:
    pass

print(json.dumps({
    'action': 'allow',
    'inject': {
        'body': body,
        'format': 'system_reminder',
    }
}, ensure_ascii=False))
PY
