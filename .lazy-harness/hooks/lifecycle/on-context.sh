#!/usr/bin/env bash
# on-context.sh — mid-turn re-grounding reminder for the Pi/OMP `context` event.
#
# Jcode parity: the jcode native runtime re-injects "the following AGENTS/.jcode
# instructions are relevant to files just read/searched/edited in this turn —
# read and follow them for the next steps." Pi/OMP load AGENTS.md only once at
# session start, so long turns drift. This hook re-surfaces the harness
# interactive grammar (AGENTS §0/§2.3/§2.4) after the agent touches files.
#
# Static transport only: no user-text classification, no semantic backend. The
# Pi/OMP extension decides WHEN to call this (after file-touching tool results);
# this hook just emits the compact re-grounding body as a system_reminder inject.

set +e

PAYLOAD=$(cat || echo '{}')

ROOT_CANDIDATE="${LAZY_HOST_ROOT:-}"
if [ -z "$ROOT_CANDIDATE" ] || [ ! -d "$ROOT_CANDIDATE/.lazy-harness" ]; then
  ROOT_CANDIDATE=$(PAYLOAD="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json, os
try:
    data = json.loads(os.environ.get('PAYLOAD') or '{}')
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

PAYLOAD_JSON="$PAYLOAD" python3 <<'PY'
import json, os, re, subprocess

try:
    payload = json.loads(os.environ.get('PAYLOAD_JSON') or '{}')
except Exception:
    payload = {}

MANDATE = [
    'REMINDER (mid-turn re-grounding — you just read/searched/edited files this turn). Re-apply the harness grammar before the next step:',
    '- Ground in the RELEVANT records for what you just touched: reading code/tests is NOT record-grounding. The records/policies relevant to the files you touched are listed below — read and follow them before any action (AGENTS §2.1/§2.5). Host rules (config/runtime/ownership/DB/workflow) live in records, not in the code.',
    '- record↔code conflict: record=intent, code=reality → ask the user which is the truth; never silently pick (AGENTS §0).',
    '- ambiguous / new design decision: stop and ask a 3-5 option gate + Recommended, RENDERED via the runtime interactive `ask` tool (native choices, not plain A/B/C text); never self-select or jump to implementation before approval (AGENTS §2.3, ADR 0019/0038).',
    '- Capture before you finish the turn: new decisions, user corrections, repeated-mistake fixes, or host learnings (policy/workflow/ownership/runtime/DB) → record them in the right `.lazy-harness/<layer>` record NOW, not just in chat. The keyword-gated capture advisories will NOT catch natural-language learnings, so this is on you (AGENTS §2.4, ADR 0032/0034).',
    '- stay read-only until search/read evidence covers the RELEVANT records (not just any file read) this work touches; mutation is guarded.',
]

LAZY = '.lazy-harness/bin/lazy'

def run(args):
    try:
        r = subprocess.run([LAZY] + args, capture_output=True, text=True, timeout=8)
        return r.stdout or ''
    except Exception:
        return ''

# Touched source/test paths from this turn's tool calls.
paths = []
for call in (payload.get('recent_tool_calls') or []):
    raw = str(call.get('args_preview') or '')
    for tok in re.split(r'[\s,]+', raw):
        tok = tok.strip().strip('`"\'')
        if '/' in tok and not tok.startswith('-') and re.search(r'\.(ts|tsx|js|jsx|py|md|json|sh|vue|svelte|go|rs|java|kt)$', tok):
            if tok not in paths:
                paths.append(tok)
paths = paths[-3:]

# jcode (b) parity: surface the ACTUAL records relevant to what was touched.
records = []
seen = set()
rec_re = re.compile(r'^- `(\.lazy-harness/(?:domain|spec|behavior|tests|decisions|ssot|planning)/[^`]+\.md)`(.*)')
for p in paths:
    if len(records) >= 6:
        break
    for line in run(['map', p, '--format=md', '--limit=6']).splitlines():
        m = rec_re.match(line)
        if not m or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        rest = re.sub(r'^\s*[-\u2014]\s*', '', m.group(2))
        rest = re.sub(r'^(?:SDD|DDD|BDD|TDD|ADR|SSOT|Planning)\b\s*[-\u2014]?\s*', '', rest)
        title = re.sub(r'\s*\(.*$', '', rest).split(', `')[0].strip().rstrip(',').strip()
        records.append('  - `%s`%s' % (m.group(1), (' — ' + title) if title else ''))
        if len(records) >= 6:
            break

# Operating policies in effect (audit work against these).
policies = []
for line in run(['policy', 'list', '--format=md']).splitlines():
    line = line.strip()
    if line.startswith('- **'):
        policies.append('  ' + line)
    if len(policies) >= 10:
        break

# Operating capabilities (intent-keyed conventions — resolve the matching one before acting).
capabilities = []
try:
    cap_data = json.loads(run(['capability', 'list', '--format=json']) or '{}')
except Exception:
    cap_data = {}
for cap in (cap_data.get('capabilities') or [])[:12]:
    cid = str(cap.get('id') or '').strip()
    if not cid:
        continue
    lvl = str(cap.get('level') or '').strip()
    intents = ', '.join(str(x) for x in (cap.get('appliesWhen') or []))
    capabilities.append('  - %s (%s): %s' % (cid, lvl, intents))
lines = list(MANDATE)
if records:
    lines.append('- Relevant records for the files you just touched (read/follow before acting):')
    lines.extend(records)
elif paths:
    lines.append('- No mapped record for the touched paths — run `.lazy-harness/bin/lazy map <path>` yourself, or create/converge the missing record (AGENTS §2.5).')
if policies:
    lines.append('- Operating policies in effect (audit your work against each — `lazy policy list` / `lazy capability list`):')
    lines.extend(policies)
if capabilities:
    lines.append('- Operating capabilities — if your current task matches an intent below, resolve it FIRST via `lazy capability resolve --intent <intent>` and follow its convention; do not improvise (e.g. PR body, release, validation):')
    lines.extend(capabilities)

body = '\n'.join(lines).strip() + '\n'
print(json.dumps({'action': 'allow', 'inject': {'body': body, 'format': 'system_reminder'}}, ensure_ascii=False))
PY
