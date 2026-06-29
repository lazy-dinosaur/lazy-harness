#!/usr/bin/env bash
# check-affected-tests.sh — run matching affected tests when TDD cross-verify found coverage.
#
# Input: response.completed payload as argv[1]
# Output: deny reason for failed affected tests or ambiguous test strategy.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

SCRIPT=".lazy-harness/scripts/affected-test-runner.ts"
QUEUE="${LAZY_HARNESS_QUESTION_QUEUE:-.lazy-harness/questions/open.xml}"
[ ! -f "$SCRIPT" ] && exit 0

FILES_FILE=$(mktemp -t lazy-affected-files.XXXXXX)
PAYLOAD_JSON="$PAYLOAD" FILES_FILE="$FILES_FILE" python3 <<'PY' 2>/dev/null || true
import json
import os
import re
from pathlib import Path
try:
    payload = json.loads(os.environ.get("PAYLOAD_JSON", "{}"))
except Exception:
    raise SystemExit(0)
allowed = {"Write", "Edit", "MultiEdit", "write", "edit", "multiedit", "mcp__filesystem__write_file", "mcp__filesystem__edit_file"}
pattern = re.compile(r"""(?:src|app|packages|tests/lazy-harness/affected|\.lazy-harness/triggers/fixtures|\.lazy-harness/triggers/walkthrough-fixtures)/[^\s"',)}]+\.(?:tsx|ts|jsx|js)""")
paths = []
for call in payload.get("recent_tool_calls", []):
    if str(call.get("name", "")) not in allowed:
        continue
    for match in pattern.finditer(str(call.get("edit_target", ""))):
        paths.append(match.group(0))
Path(os.environ["FILES_FILE"]).write_text(",".join(dict.fromkeys(paths)), encoding="utf-8")
PY
FILES=""
[ -f "$FILES_FILE" ] && FILES=$(<"$FILES_FILE")
rm -f "$FILES_FILE"

[ -z "$FILES" ] && exit 0

RESULT=$(bun "$SCRIPT" --files "$FILES" --queue "$QUEUE" --format json 2>/dev/null || true)
[ -z "$RESULT" ] && exit 0
FORCE=$(printf '%s' "$RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("forceGate", False))' 2>/dev/null || true)
[ "$FORCE" != "True" ] && [ "$FORCE" != "true" ] && exit 0
SUMMARY=$(RESULT_JSON="$RESULT" python3 <<'PY' 2>/dev/null || true
import json, os
try:
    data=json.loads(os.environ.get('RESULT_JSON', '{}'))
except Exception:
    raise SystemExit(0)
run=data.get('run') or {}
if run:
    print(f"command: {' '.join(run.get('command', []))}")
    print(f"exitCode: {run.get('exitCode')}")
    stdout=(run.get('stdout') or '').strip().splitlines()[-8:]
    stderr=(run.get('stderr') or '').strip().splitlines()[-8:]
    if stdout:
        print('stdout:')
        print('\n'.join(stdout))
    if stderr:
        print('stderr:')
        print('\n'.join(stderr))
questions=data.get('questions') or [f.get('question') for f in data.get('files', []) if f.get('question')]
for q in questions:
    print(f"- {q.get('id')}: {q.get('question')}")
    for opt in q.get('options', []):
        print(f"  {opt.get('id')}. {opt.get('label')}")
PY
)

cat <<EOF_DENY
STOP. 5d-3 Affected Test Gate: 변경 파일에 대응하는 테스트 실행/전략 확인이 필요합니다.

$SUMMARY

규칙: matching test 가 있으면 해당 vitest 를 통과시켜야 합니다. test/framework 가 없거나 비어 있으면 A/B/C/D 중 하나를 사용자에게 확인하고 decision 으로 기록하세요.
EOF_DENY

exit 0
