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

python3 <<'PY'
import json

body = '\n'.join([
    'REMINDER (mid-turn re-grounding — you just read/searched/edited files this turn). Re-apply the harness grammar before the next step:',
    '- Ground in the RELEVANT records for what you just touched: reading code/tests is NOT record-grounding. Before any action, run `.lazy-harness/bin/lazy map` for the feature/path you touched and read the governing `.lazy-harness/<layer>` record (ssot/spec/decisions/...) — host rules (config/runtime/ownership/DB/workflow) live in records, not in the code you just read (AGENTS §2.1/§2.5).',
    '- record↔code conflict: record=intent, code=reality → ask the user which is the truth; never silently pick (AGENTS §0).',
    '- ambiguous / new design decision: stop and ask a 3-5 option gate + Recommended, RENDERED via the runtime interactive `ask` tool (native choices, not plain A/B/C text); never self-select or jump to implementation before approval (AGENTS §2.3, ADR 0019/0038).',
    '- Capture before you finish the turn: new decisions, user corrections, repeated-mistake fixes, or host learnings (policy/workflow/ownership/runtime/DB) → record them in the right `.lazy-harness/<layer>` record NOW, not just in chat. The keyword-gated capture advisories will NOT catch natural-language learnings, so this is on you (AGENTS §2.4, ADR 0032/0034).',
    '- stay read-only until search/read evidence covers the RELEVANT records (not just any file read) this work touches; mutation is guarded.',
]).strip() + '\n'

print(json.dumps({'action': 'allow', 'inject': {'body': body, 'format': 'system_reminder'}}, ensure_ascii=False))
PY
