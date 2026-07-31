#!/usr/bin/env bash
# check-affected-tests.sh — run matching affected tests when TDD cross-verify found coverage.
#
# Input: response.completed payload as argv[1]
# Output: deny reason for failed affected tests or ambiguous test strategy.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

HOST_ROOT="${LAZY_HOST_ROOT:-$(pwd)}"
SCRIPT="$HOST_ROOT/.lazy-harness/scripts/affected-test-runner.ts"
QUEUE="${LAZY_HARNESS_QUESTION_QUEUE:-.lazy-harness/questions/open.xml}"
case "$QUEUE" in
  /*) ;;
  *) QUEUE="$HOST_ROOT/$QUEUE" ;;
esac
[ ! -f "$SCRIPT" ] && exit 0

GROUPS_FILE=$(mktemp -t lazy-affected-groups.XXXXXX)
trap 'rm -f "$GROUPS_FILE"' EXIT
PAYLOAD_JSON="$PAYLOAD" GROUPS_FILE="$GROUPS_FILE" HOST_ROOT="$HOST_ROOT" python3 <<'PY' 2>/dev/null || true
import json
import os
import re
import subprocess
from collections import OrderedDict
from pathlib import Path

try:
    payload = json.loads(os.environ.get("PAYLOAD_JSON", "{}"))
except Exception:
    raise SystemExit(0)

host_root = Path(os.environ["HOST_ROOT"]).resolve()
allowed = {"Write", "Edit", "MultiEdit", "write", "edit", "multiedit", "mcp__filesystem__write_file", "mcp__filesystem__edit_file"}
source_prefixes = (
    "src/", "app/", "packages/", "tests/lazy-harness/affected/",
    ".lazy-harness/triggers/fixtures/", ".lazy-harness/triggers/walkthrough-fixtures/",
)
target_pattern = re.compile(r"""[^\s"',)}]+\.(?:tsx|ts|jsx|js)""")
source_extension_pattern = re.compile(r"""\.(?:tsx|ts|jsx|js)$""")
groups = OrderedDict()


def resolve_target(raw_target):
    normalized_target = raw_target.replace("\\", "/").strip()
    if not source_extension_pattern.search(normalized_target):
        return None
    candidate = Path(normalized_target)
    if not candidate.is_absolute():
        candidate = host_root / candidate
    candidate = candidate.resolve()
    probe = candidate if candidate.is_dir() else candidate.parent
    try:
        completed = subprocess.run(
            ["git", "-C", str(probe), "rev-parse", "--show-toplevel"],
            text=True,
            capture_output=True,
            check=False,
            timeout=3,
        )
    except Exception:
        return None
    if completed.returncode != 0 or not completed.stdout.strip():
        return None
    worktree = Path(completed.stdout.strip()).resolve()
    try:
        relative = candidate.relative_to(worktree).as_posix()
    except ValueError:
        return None
    if not relative.startswith(source_prefixes):
        return None
    return str(worktree), relative


for call in payload.get("recent_tool_calls", []):
    if str(call.get("name", "")) not in allowed:
        continue
    edit_target = str(call.get("edit_target", "")).strip()
    resolved_targets = []
    whole_target = resolve_target(edit_target)
    if whole_target:
        # A Pi edit normally has one target. Resolve the complete field first so
        # absolute worktree/file paths containing spaces retain their ownership.
        resolved_targets.append(whole_target)
    else:
        # Patch tools may project multiple space-delimited targets. Preserve the
        # existing fallback for those unambiguous, space-free path tokens.
        for match in target_pattern.finditer(edit_target):
            resolved_target = resolve_target(match.group(0))
            if resolved_target:
                resolved_targets.append(resolved_target)
    for worktree, relative in resolved_targets:
        group = groups.setdefault(worktree, [])
        if relative not in group:
            group.append(relative)

with Path(os.environ["GROUPS_FILE"]).open("w", encoding="utf-8") as output:
    for worktree, files in groups.items():
        output.write(f"{worktree}\t{','.join(files)}\n")
PY

[ ! -s "$GROUPS_FILE" ] && exit 0

FORCED=false
SUMMARIES=""
while IFS="$(printf '\t')" read -r WORKTREE FILES; do
  [ -z "$WORKTREE" ] && continue
  [ -z "$FILES" ] && continue
  RESULT=$(cd "$WORKTREE" && bun "$SCRIPT" --files "$FILES" --queue "$QUEUE" --format json 2>/dev/null || true)
  [ -z "$RESULT" ] && continue
  FORCE=$(printf '%s' "$RESULT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("forceGate", False))' 2>/dev/null || true)
  [ "$FORCE" != "True" ] && [ "$FORCE" != "true" ] && continue
  FORCED=true
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
  [ -n "$SUMMARIES" ] && SUMMARIES="$SUMMARIES

"
  SUMMARIES="${SUMMARIES}worktree: $WORKTREE
$SUMMARY"
done < "$GROUPS_FILE"

[ "$FORCED" != "true" ] && exit 0
SUMMARY="$SUMMARIES"

cat <<EOF_DENY
STOP. 5d-3 Affected Test Gate: 변경 파일에 대응하는 테스트 실행/전략 확인이 필요합니다.

$SUMMARY

규칙: matching test 가 있으면 해당 vitest 를 통과시켜야 합니다. test/framework 가 없거나 비어 있으면 A/B/C/D 중 하나를 사용자에게 확인하고 decision 으로 기록하세요.
EOF_DENY

exit 0
