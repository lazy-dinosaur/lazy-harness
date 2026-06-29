#!/usr/bin/env bash
# check-lazy-cli-entrypoint.sh — prevent stale package-script lazy:test/lazy:doctor usage

set -euo pipefail
PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json, os, re, sys

try:
    payload = json.loads(os.environ.get('PAYLOAD_JSON', '{}'))
except Exception:
    sys.exit(0)

# Scope: only the agent's own actions — assistant prose + command-tool args.
# NOT file READ result_previews (reading a file that contains `lazy:test`, e.g. this
# gate's own parity fixture, must not false-fire) nor edit bodies.
strings = []
ar = payload.get('assistant_response')
if isinstance(ar, str):
    strings.append(ar)
command_tools = {'bash', 'cmd', 'command', 'shell', 'terminal'}
for call in (payload.get('recent_tool_calls') or []):
    if isinstance(call, dict) and str(call.get('name', '')).lower() in command_tools:
        ap = call.get('args_preview')
        if isinstance(ap, str):
            strings.append(ap)
blob = '\n'.join(strings)
lower=blob.lower()

stale_patterns = [
    'bun run lazy:test',
    'bun run lazy:doctor',
    'lazy:test',
    'lazy:doctor',
    'package.json에 lazy:test',
    'package.json has no lazy:test',
]
if not any(p in lower for p in stale_patterns):
    sys.exit(0)

# Historical text may appear inside a read result. Only stop when the assistant is
# executing, recommending, or diagnosing with stale CLI, not when merely editing
# an old ADR quote. Strong cues reduce false positives.
action_cues = [
    '실행', '돌리', '재현', '검증', 'command', 'run', 'test failed', '실패',
    '스크립트가 없어', 'no script', 'package.json', 'lazy test',
]
if not any(cue in lower for cue in action_cues):
    sys.exit(0)

# If the same payload already states the canonical replacement, allow purely
# corrective explanations that name the stale form as something to avoid.
avoid_cues = ['낡은', 'stale', 'deprecated', '쓰지 말', 'avoid', '대신 .lazy-harness/bin/lazy']
if any(cue in lower for cue in avoid_cues):
    sys.exit(0)

print('STOP. Lazy CLI entrypoint gate: `bun run lazy:test` / `lazy:test` 는 낡은 호출입니다.\n')
print('현재 canonical CLI:')
print('  - .lazy-harness/bin/lazy test')
print('  - .lazy-harness/bin/lazy doctor --profile smoke')
print('\n해야 할 일:')
print('  A. package.json script 존재 여부를 기준으로 판단하지 말고 `.lazy-harness/bin/lazy version` 으로 root 확인')
print('  B. `.lazy-harness/bin/lazy test` 로 재현')
print('  C. 오래된 handoff/ADR 에서 `lazy:test` 를 봤다면 current SDD/README/CLI record 를 우선')
print('\n규칙: SDD lazy-cli-entrypoint.')
PY
