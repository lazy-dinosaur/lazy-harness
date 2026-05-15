#!/usr/bin/env bash
# check-record-before-session-history.sh — prevent session-history-first lookup for recorded plans/rules

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

# Only care about cases where the task is asking for something that should have
# been recorded as durable project knowledge or planning, not pure chat recall.
record_intent_cues = [
    '기록', 'record', 'records', 'recorded', '레코드', '.lazy-harness',
    '계획', 'plan', 'planning', 'backlog', '하려고', '하려던', '정리해둔',
    'handoff', 'ssot', 'adr', 'decision', 'decisions', 'spec', 'behavior',
]
if not any(cue in lower for cue in record_intent_cues):
    sys.exit(0)

recent = payload.get('recent_tool_calls', []) or []
if not recent:
    sys.exit(0)

record_dirs = (
    '.lazy-harness/domain', '.lazy-harness/spec', '.lazy-harness/behavior',
    '.lazy-harness/tests', '.lazy-harness/decisions', '.lazy-harness/ssot',
    '.lazy-harness/planning', '.lazy-harness/plans', '.lazy-harness/knowledge',
)
history_tools = {'session_search', 'conversation_search'}
record_search_tools = {'agentgrep', 'grep', 'read', 'glob', 'bash'}

def call_blob(call):
    parts=[]
    for key in ('args_preview','args','query','path','file_path','command'):
        val=call.get(key)
        if val is None: continue
        parts.append(val if isinstance(val,str) else json.dumps(val, ensure_ascii=False))
    return '\n'.join(parts)

def is_history_call(call):
    name=str(call.get('name','')).lower()
    return name in history_tools or name.endswith('.session_search') or name.endswith('.conversation_search')

def is_record_call(call):
    name=str(call.get('name','')).lower()
    cb=call_blob(call)
    return (name in record_search_tools or any(name.endswith('.'+t) for t in record_search_tools)) and any(d in cb for d in record_dirs)

first_history = None
first_record = None
for idx, call in enumerate(recent):
    if first_history is None and is_history_call(call):
        first_history = idx
    if first_record is None and is_record_call(call):
        first_record = idx

if first_history is None:
    sys.exit(0)

# OK when durable records/planning were searched before session history.
if first_record is not None and first_record < first_history:
    sys.exit(0)

# OK when the response explicitly states the user asked for chat transcript only.
chat_only_cues = ['대화 로그만', 'previous chat only', 'session transcript only', '채팅 기록만']
if any(cue in lower for cue in chat_only_cues):
    sys.exit(0)

print('STOP. Record-before-session-history gate: 기록/계획/하려던 일을 찾을 때 session_search 가 .lazy-harness record 검색보다 먼저 실행되었습니다.\n')
print('문제: 이전 세션 대화는 보조 증거입니다. durable source-of-truth 는 `.lazy-harness` records/planning 입니다.')
print('\n해야 할 일:')
print('  A. 먼저 `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,plans,knowledge}/` 를 검색/Read (Recommended)')
print('  B. record 에 없을 때만 `session_search` 로 과거 대화를 fallback 검색')
print('  C. session_search 결과에서 새 사실을 찾으면 records/candidates/planning 으로 수렴')
print('  D. 사용자가 명시적으로 "대화 로그만" 요청한 경우에만 session_search 우선 허용')
print('\n규칙: AGENTS §2.1/§2.5, SDD record-before-session-history.')
PY
