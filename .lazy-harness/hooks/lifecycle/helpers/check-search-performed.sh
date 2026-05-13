#!/usr/bin/env bash
# check-search-performed.sh — Layer 2 force-gate (ADR 0024)
#
# Edit/Write/MultiEdit 호출 시 본 session 내 AGENTS.md §1 따라 검색 활동
# (grep/reference-resolver/Bash) 이 한 번이라도 있었는지 확인.
#
# 검색 감지 정책 (보수적: false-deny 보다 false-allow 우선):
#   - tool_calls 에 Grep / AgentGrep / Bash:grep / Bash:rg / Bash:reference-resolver
#     중 .lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/ 를
#     query 한 흔적 → SEARCH_OK
#   - tool_calls 에 Read 가 .lazy-harness/ 하위 record 를 읽었으면 → SEARCH_OK
#   - 위 둘 다 없고, 이번 호출이 src/ 또는 .lazy-harness/triggers/fixtures/
#     하위 ts/tsx 를 수정하려는 Edit/Write/MultiEdit 일 때만 deny.
#
# Session-cache:
#   .lazy-harness/.cache/session/<session_id>.json
#   { "search_performed": true, "first_seen_at": "<iso8601>" }
#   한 번 OK 면 본 세션 동안 재검사 면제.
#
# Input: tool.execute.before payload as argv[1]
# Output: deny 메시지 (silent skip 차단), 또는 빈 출력.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

# Python helper — 본 hook 의 복잡한 정책 로직만 격리
python3 <<PY
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    payload = json.loads(${PAYLOAD@Q})
except Exception:
    sys.exit(0)

tool = payload.get("tool", {}) or {}
tool_name = str(tool.get("name", ""))
tool_args = tool.get("args", {}) or {}

# 본 hook 이 관여하는 tool 만 처리
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "edit", "write", "multiedit",
               "mcp__filesystem__write_file", "mcp__filesystem__edit_file"}
if tool_name not in WRITE_TOOLS:
    sys.exit(0)

# 대상 파일이 source code 인지 확인 (record 자체 편집은 면제 — record 누적이 의도된 작업)
target_path = ""
for key in ("file_path", "path", "target_file"):
    val = tool_args.get(key)
    if isinstance(val, str) and val:
        target_path = val
        break

# record 편집 본인은 면제
if target_path.startswith(".lazy-harness/") and not target_path.startswith(".lazy-harness/triggers/fixtures"):
    sys.exit(0)

# 코드 파일만 게이트 대상
CODE_PATTERN = re.compile(r"(?:^src/|^\.lazy-harness/triggers/fixtures/).+\.(?:ts|tsx|js|jsx)$")
if not CODE_PATTERN.match(target_path):
    sys.exit(0)

# Session-cache 확인
session_id = payload.get("session_id") or "default"
cache_dir = Path(".lazy-harness/.cache/session")
cache_dir.mkdir(parents=True, exist_ok=True)
cache_path = cache_dir / f"{session_id}.json"

if cache_path.exists():
    try:
        cache = json.loads(cache_path.read_text())
        if cache.get("search_performed"):
            sys.exit(0)
    except Exception:
        pass

# Tool-call 이력에서 검색 흔적 탐지
recent = payload.get("recent_tool_calls", []) or []
search_record_dirs = ("domain", "spec", "behavior", "tests", "decisions", "ssot")

def args_blob(call):
    a = call.get("args_preview") or call.get("args") or ""
    return a if isinstance(a, str) else json.dumps(a)

def hit_record_dir(blob: str) -> bool:
    return any(f".lazy-harness/{d}" in blob for d in search_record_dirs)

search_seen = False
for call in recent:
    name = str(call.get("name", "")).lower()
    blob = args_blob(call)
    if name in ("grep", "agentgrep") or name.endswith(".agentgrep"):
        if hit_record_dir(blob):
            search_seen = True; break
    if name in ("grep",) and hit_record_dir(blob):
        search_seen = True; break
    if name in ("bash",) and (("grep" in blob or "rg " in blob or "reference-resolver" in blob) and hit_record_dir(blob)):
        search_seen = True; break
    if name in ("read",) and hit_record_dir(blob):
        search_seen = True; break
    if name in ("glob",) and hit_record_dir(blob):
        search_seen = True; break

if search_seen:
    cache_path.write_text(json.dumps({
        "search_performed": True,
        "first_seen_at": datetime.utcnow().isoformat() + "Z",
    }))
    sys.exit(0)

# === DENY ===
target_basename = Path(target_path).stem if target_path else "<token>"
deny = f"""[lazy-harness gate] AGENTS.md §1 검사: 본 세션에서 record 검색이 아직 없음.
대상: {target_path}

수정 시작 전에 1 회만 다음 중 하나를 실행:

  1) grep -rli '{target_basename}' .lazy-harness/{{domain,spec,behavior,tests,decisions,ssot}}/
  2) bun .lazy-harness/scripts/reference-resolver.ts --file '{target_path}' --format ask
  3) 명확히 신규/no-context 작업이면 .lazy-harness/AGENTS.md 의 §3 절차로 skip 사유 기록.

본 hook 은 silent skip 방지 (ADR 0024 §5 Layer 2). 한 번 검색하면 본 세션 동안 재가동되지 않음."""

print(deny)
sys.exit(0)
PY
