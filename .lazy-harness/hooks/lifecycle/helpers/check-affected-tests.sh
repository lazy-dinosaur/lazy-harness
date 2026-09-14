#!/usr/bin/env bash
# Route only actual edit targets; never recover source paths from quoted prose.
# Runner source and interview queue belong to the session host; test config,
# matching and execution belong to each edited repository.
set -euo pipefail
[ -z "${1:-}" ] && exit 0
PAYLOAD_JSON="$1" python3 <<'PY'
import json
import os
from pathlib import Path
import re
import subprocess

host = Path(os.environ.get('LAZY_HOST_ROOT') or os.getcwd()).resolve()
script = host / '.lazy-harness/scripts/affected-test-runner.ts'
if not script.is_file():
    raise SystemExit(0)
queue = Path(os.environ.get('LAZY_HARNESS_QUESTION_QUEUE') or '.lazy-harness/questions/open.xml')
if not queue.is_absolute():
    queue = host / queue
# git -C and test commands must not inherit another worktree's Git context.
env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
allowed = {'Write', 'Edit', 'MultiEdit', 'write', 'edit', 'multiedit',
           'functions.write', 'functions.edit', 'functions.multiedit',
           'mcp__filesystem__write_file', 'mcp__filesystem__edit_file'}
prefixes = ('src/', 'app/', 'packages/', 'tests/lazy-harness/affected/',
            '.lazy-harness/triggers/fixtures/', '.lazy-harness/triggers/walkthrough-fixtures/')
groups = {}
problems = []
try:
    payload = json.loads(os.environ['PAYLOAD_JSON'])
    if not isinstance(payload, dict):
        raise ValueError('payload must be an object')
    calls = payload.get('recent_tool_calls', [])
    if not isinstance(calls, list):
        raise ValueError('recent_tool_calls must be an array')
    for call in calls:
        if not isinstance(call, dict) or call.get('name') not in allowed:
            continue
        raw = call.get('edit_target', '')
        if not isinstance(raw, str):
            raise ValueError('edit_target must be a string')
        # Complete identity first: spaces and commas are path bytes, not delimiters.
        # Legacy space-joined multi-target fields are ambiguous; never execute
        # a guessed suffix or probe a different repository on their behalf.
        target = Path(raw)
        if not target.is_absolute():
            target = host / target
        if not target.is_file():
            # Detection only, never extraction: a source followed by a record
            # in the legacy joined field must not become silent success.
            if re.search(r'\.(tsx?|jsx?)(?=$|[\s,\"\'])', raw):
                problems.append(f'unresolved edit target (missing or ambiguous): {raw}')
            continue
        if not re.search(r'\.(tsx?|jsx?)$', raw):
            continue
        if os.environ.get('LAZY_LIFECYCLE_SANDBOX_CONTEXT') == '1':
            # The lifecycle sandbox copies only framework files, not arbitrary
            # edited repositories. Do not discover owners or run their commands.
            problems.append(f'not-executed: lifecycle sandbox; affected tests require live validation: {raw}')
            continue
        target = target.resolve()
        probe = subprocess.run(['git', '-C', str(target.parent), 'rev-parse', '--show-toplevel'],
                               env=env, text=True, capture_output=True, timeout=3)
        if probe.returncode == 0 and probe.stdout.strip():
            owner = Path(probe.stdout.strip()).resolve()
        elif target.is_relative_to(host):
            # Initialized non-Git hosts retain the existing host-local behavior.
            owner = host
        else:
            problems.append(f'cannot establish edited repository: {raw}')
            continue
        if not target.is_relative_to(owner):
            problems.append(f'edit target outside resolved repository: {raw}')
            continue
        relative = target.relative_to(owner).as_posix()
        if not relative.startswith(prefixes):
            continue
        group = groups.setdefault(owner, [])
        if relative not in group:
            group.append(relative)
except (ValueError, OSError, subprocess.SubprocessError) as error:
    problems.append(f'affected target routing failed: {error}')

for owner, files in groups.items():
    command = ['bun', str(script), '--queue', str(queue), '--format', 'json']
    for file in files:
        command.extend(['--file', file])
    try:
        completed = subprocess.run(command, cwd=owner, env={**env, 'LAZY_HOST_ROOT': str(owner)},
                                   text=True, capture_output=True)
        try:
            result = json.loads(completed.stdout)
        except ValueError as error:
            raise ValueError(f'runner exit {completed.returncode}, invalid assessment: {completed.stderr[-2000:]}') from error
        if not isinstance(result, dict) or not isinstance(result.get('forceGate'), bool):
            raise ValueError('runner assessment missing forceGate')
        if completed.returncode not in (0, 2):
            raise ValueError(f'runner exit {completed.returncode}: {completed.stderr[-2000:]}')
        if completed.returncode == 2 or result['forceGate']:
            problems.append(f'worktree: {owner}\n' + json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        problems.append(f'worktree: {owner}\naffected runner unavailable: {error}')

if problems:
    print('STOP. 5d-3 Affected Test Gate: 변경 파일에 대응하는 테스트 실행/전략 확인이 필요합니다.\n')
    print('\n\n'.join(problems))
    print('\n규칙: matching test 를 통과시키거나 새로운 테스트 전략 질문을 사용자에게 확인하세요. 경로/runner 실패는 성공이 아닙니다.')
PY
