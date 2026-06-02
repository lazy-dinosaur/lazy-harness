#!/usr/bin/env bash
# on-message-received.sh — pre-turn lazy-harness direct-search prompt for Jcode message.received.
#
# This hook deliberately does not run relevant-record-query/context-delivery or any
# semantic search backend. It only detects likely host-dependent turns, injects a
# direct root-bound search protocol for the LLM/searcher, and journals sanitized
# search-debt so the generic evidence guard/audit can verify that search happened
# before action.

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
import re
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

message = str(payload.get('last_user_message') or '').strip()
if not message:
    raise SystemExit(0)

CHANGE_RE = re.compile(r'(고쳐|수정|변경|만들|구현|추가|삭제|디버그|확인|검증|fix|change|update|modify|build|implement|add|delete|debug|refactor|review|verify|release|deploy|publish|test)', re.I)
HOST_DETAIL_RE = re.compile(r'(코드|파일|함수|컴포넌트|화면|페이지|시트|표|그리드|목록|상세|관리|버그|테스트|기록|규칙|룰|결정|계약|스키마|hook|debt|context|search|jcode|lazy-harness|record|agent|framework|spec|ssot|adr|tdd|bdd|ddd|api|db|schema|env|config|workflow|release|deploy|build|test)', re.I)
AMBIGUOUS_RE = re.compile(r'(그거|이거|저거|그쪽|여기|저기|메세지|메시지|방금|아까|이렇게|그렇게|이 부분|저 부분)')
PATH_RE = re.compile(r'(`[^`]+`|\.lazy-harness/|\.jcode/|src/|tests?/|[A-Za-z0-9_.-]+\.(?:ts|tsx|js|jsx|py|sh|md|json|toml|yml|yaml|xml))')
PURE_SMALLTALK_RE = re.compile(r'^\s*(안녕|고마워|감사|ㅇㅋ|ok|okay|thanks|thank you|수고|좋아)\s*[.!?。]*\s*$', re.I)


def has_hangul(text: str) -> bool:
    return bool(re.search(r'[가-힣]', text))


def search_needed(text: str) -> bool:
    if PURE_SMALLTALK_RE.match(text):
        return False
    if PATH_RE.search(text):
        return True
    if CHANGE_RE.search(text):
        return True
    if HOST_DETAIL_RE.search(text):
        return True
    if AMBIGUOUS_RE.search(text):
        return True
    # Korean work requests are often host-detail dependent; avoid doing semantic
    # mapping in the hook and force the LLM to search/read directly instead.
    return has_hangul(text) and len(text) <= 120


if not search_needed(message):
    raise SystemExit(0)


def stable_hash(value: Any) -> str | None:
    text = str(value or '').strip()
    if not text:
        return None
    return hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()[:16]


level = 'self-resolve-before-change' if CHANGE_RE.search(message) else 'self-resolve-before-answer'
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
    'notes': ['directSearchPrompt=true', 'noSemanticBackend=true', 'llmSearchBaseline=true'],
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

body = '\n'.join([
    'STOP. Direct lazy-harness search-debt before response',
    f'- Instruction: {level}',
    '- Do not use a CLI/index/search backend as semantic authority for this turn.',
    '- Before answering, analyzing, planning, option-gating, or editing, the LLM/searcher must directly perform root-bound search/read with available tools.',
    f'- Search scope: `{search_hint}`',
    '- Framework structure to search first: DDD=`.lazy-harness/domain/` for terms/business rules; SDD=`.lazy-harness/spec/` for contracts/components/APIs; BDD=`.lazy-harness/behavior/` for UI/user flows; TDD=`.lazy-harness/tests/` for regressions/validation; ADR=`.lazy-harness/decisions/` for trade-offs; SSOT=`.lazy-harness/ssot/` for config/schema/ownership/source-of-truth; Planning=`.lazy-harness/planning/` or `.lazy-harness/plans/` for active backlog/handoffs.',
    '- Search protocol: (1) extract 2-5 candidate meanings and likely code/English/Korean aliases, (2) grep/agentgrep records by those tokens, (3) read matching `## Rule digest` and full records, (4) follow Related records / Implementation map / graph links, (5) search source/tests for confirmed files/symbols, (6) only then answer/plan/edit.',
    '- Required evidence examples: `grep -rli <token> .lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/`, `rg -n <expanded terms> .lazy-harness src tests`, `agentgrep`, then `read` concrete records/files.',
    '- If no record exists, search current host code/docs/package/config and converge missing durable knowledge into the right `.lazy-harness/<layer>/...` record after user confirmation.',
    '- If meanings or layer placement still conflict after search/read evidence, ask a 3-5 option gate with Recommended and a custom option; do not self-select.',
    '- Allowed before debt is satisfied: read/search tools and explicit read-only searcher handoff. Action/mutation tools remain blocked by the generic evidence guard.',
]).strip() + '\n'

print(json.dumps({
    'action': 'allow',
    'inject': {
        'body': body,
        'format': 'system_reminder',
    }
}, ensure_ascii=False))
PY
