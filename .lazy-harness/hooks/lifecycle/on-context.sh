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
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.lazy-harness/hooks/lifecycle/helpers').resolve()))
try:
    from operating_rule_catalog import catalog_lines as _catalog_lines
    from operating_rule_catalog import context_guidance_lines as _context_guidance_lines
except Exception:
    _catalog_lines = None
    _context_guidance_lines = None

try:
    payload = json.loads(os.environ.get('PAYLOAD_JSON') or '{}')
except Exception:
    payload = {}

MANDATE = [
    'REMINDER (mid-turn re-grounding — you just read/searched/edited files this turn). Re-apply the harness grammar before the next step:',
    '- Ground in the RELEVANT records for what you just touched: reading code/tests is NOT record-grounding. The records/policies relevant to the files you touched are listed below — read and follow them before any action (AGENTS §2.1/§2.5). Host rules (config/runtime/ownership/DB/workflow) live in records, not in the code.',
    '- Map-first BEFORE reading/editing more: if you have not run `.lazy-harness/bin/lazy map --overview` and drilled into the governing records (decisions/ssot/behavior/domain per §1) for what you are working on, do that FIRST — do not keep working off memory or off code alone. Review/audit request: enumerate the governing records + operating policies first, THEN read code to check compliance (AGENTS §2.1).',
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

# Touched source/test paths and mechanical source-work intents from this turn's tool calls.
SOURCE_RE = re.compile(r'\.(ts|tsx|js|jsx|py|sh|vue|svelte|go|rs|java|kt|c|h|cc|cpp|hpp|cs|rb|php|swift|scala|ex|exs|dart)$', re.IGNORECASE)
PATH_RE = re.compile(r'\.(ts|tsx|js|jsx|py|md|json|sh|vue|svelte|go|rs|java|kt|c|h|cc|cpp|hpp|cs|rb|php|swift|scala|ex|exs|dart)$', re.IGNORECASE)
READ_TOOLS = {'read', 'grep', 'find', 'ls', 'search', 'symbol_search', 'module_report', 'read_symbol', 'read_enclosing'}
CREATE_TOOLS = {'write', 'create'}
MODIFY_TOOLS = {'edit', 'replace', 'multiedit', 'patch', 'apply_patch', 'write'}

paths = []
source_intents = set()
for call in (payload.get('recent_tool_calls') or []):
    raw = str(call.get('args_preview') or '')
    call_paths = []
    for tok in re.split(r'[\s,]+', raw):
        tok = tok.strip().strip('`"\'')
        if '/' in tok and not tok.startswith('-') and PATH_RE.search(tok):
            if tok not in paths:
                paths.append(tok)
            call_paths.append(tok)
    if any(SOURCE_RE.search(path) for path in call_paths):
        tool_name = str(call.get('name') or call.get('tool') or '').strip().lower().rsplit('.', 1)[-1]
        if tool_name in READ_TOOLS:
            source_intents.add('reviewing_code_organization')
        if tool_name in CREATE_TOOLS:
            source_intents.add('creating_source_file')
        if tool_name in MODIFY_TOOLS:
            source_intents.add('modifying_source_file')

paths = paths[-3:]
source_paths = [path for path in paths if SOURCE_RE.search(path)]
if source_paths and not source_intents:
    # Legacy/minimal payloads may omit tool names. Keep the exact-intent path
    # deterministic and conservative rather than classifying user text.
    source_intents.add('modifying_source_file')

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

# Operating rules/capabilities in effect — jcode parity: surface stored rules before action (R3, ADR 0048).
if source_paths and _context_guidance_lines:
    catalog = _context_guidance_lines(LAZY, os.getcwd(), sorted(source_intents), stage='edit')
else:
    catalog = _catalog_lines(LAZY, os.getcwd()) if _catalog_lines else []

lines = list(MANDATE)
if records:
    lines.append('- Relevant records for the files you just touched (read/follow before acting):')
    lines.extend(records)
elif paths:
    lines.append('- No mapped record for the touched paths — run `.lazy-harness/bin/lazy map <path>` yourself, or create/converge the missing record (AGENTS §2.5).')
if catalog:
    lines.extend(catalog)

body = '\n'.join(lines).strip() + '\n'
print(json.dumps({'action': 'allow', 'inject': {'body': body, 'format': 'system_reminder'}}, ensure_ascii=False))
PY
