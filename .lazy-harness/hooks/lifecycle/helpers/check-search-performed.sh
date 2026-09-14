#!/usr/bin/env bash
# check-search-performed.sh — Layer 2 force-gate (ADR 0024)
#
# Edit/Write/MultiEdit 호출 시 본 session 내 AGENTS.md §1 따라 검색 활동
# (grep/reference-resolver/Bash) 이 한 번이라도 있었는지 확인.
#
# 검색 감지 정책 (보수적: false-deny 보다 false-allow 우선):
#   - tool_calls 에 Grep / AgentGrep / Bash:grep / Bash:rg / Bash:find /
#     Bash:reference-resolver 중 .lazy-harness record scope 를 query 한 흔적 → SEARCH_OK
#   - tool_calls 에 Read/List/Glob 이 .lazy-harness/ 하위 record 를 읽었으면 → SEARCH_OK
#   - batch/multi_tool_use 안의 nested read/search 도 이전 evidence 로 flatten 해서 인정
#   - 위 둘 다 없고, 이번 호출이 src/ 또는 .lazy-harness/triggers/fixtures/
#     하위 ts/tsx/js/jsx 를 수정하려는 Edit/Write/MultiEdit/Patch/ApplyPatch 일 때만 deny.
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
python3 - "$PAYLOAD" <<'PY'
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    payload = json.loads(sys.argv[1] if len(sys.argv) > 1 else "{}")
except Exception:
    sys.exit(0)

tool = payload.get("tool", {}) or {}
tool_name = str(tool.get("name", ""))
tool_name_l = tool_name.lower()
tool_args = tool.get("args", {}) or {}

# 본 hook 이 관여하는 tool 만 처리
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "edit", "write", "multiedit",
               "patch", "apply_patch", "Patch", "ApplyPatch",
               "mcp__filesystem__write_file", "mcp__filesystem__edit_file"}
WRAPPER_TOOLS = {"batch", "multi_tool_use.parallel"}

def is_write_name(name: str) -> bool:
    lower = str(name or "").lower()
    return name in WRITE_TOOLS or bool(re.search(r"(?:^|[.:_\-])(write|edit|patch|apply_patch)$", lower))

if not is_write_name(tool_name) and tool_name_l not in WRAPPER_TOOLS:
    sys.exit(0)

CODE_PATTERN = re.compile(r"(?:^src/|^\.lazy-harness/triggers/fixtures/).+\.(?:ts|tsx|js|jsx)$")

def normalize_path(path: str) -> str:
    path = str(path or "").strip().replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]
    if path.startswith("a/") or path.startswith("b/"):
        path = path[2:]
    return path

def patch_paths(text: str) -> list[str]:
    paths: list[str] = []
    for line in str(text or "").splitlines():
        m = re.match(r"\*\*\*\s+(?:Update|Add|Delete) File:\s+(.+)$", line)
        if m:
            paths.append(normalize_path(m.group(1)))
            continue
        m = re.match(r"(?:---|\+\+\+)\s+(?:[ab]/)?(.+)$", line)
        if m and m.group(1) != "/dev/null":
            paths.append(normalize_path(m.group(1)))
    return paths

def target_paths(args: dict) -> list[str]:
    paths: list[str] = []
    for key in ("file_path", "path", "target_file"):
        val = args.get(key)
        if isinstance(val, str) and val:
            paths.append(normalize_path(val))
    for key in ("patch_text", "patch", "diff"):
        val = args.get(key)
        if isinstance(val, str) and val:
            paths.extend(patch_paths(val))
    nested = args.get("tool_calls") or args.get("toolCalls") or args.get("tool_uses") or []
    if isinstance(nested, list):
        for call in nested:
            if not isinstance(call, dict):
                continue
            name = str(call.get("recipient_name") or call.get("tool") or call.get("name") or call.get("toolName") or "")
            child_args = {}
            for child_key in ("parameters", "input", "args"):
                if isinstance(call.get(child_key), dict):
                    child_args = call[child_key]
                    break
            if is_write_name(name) or name.lower() in WRAPPER_TOOLS:
                paths.extend(target_paths(child_args))
    return [p for p in paths if p]

# 대상 파일이 source code 인지 확인 (record 자체 편집은 면제 — record 누적이 의도된 작업)
targets = target_paths(tool_args)
code_targets = []
for candidate in targets:
    if candidate.startswith(".lazy-harness/") and not candidate.startswith(".lazy-harness/triggers/fixtures"):
        continue
    if CODE_PATTERN.match(candidate):
        code_targets.append(candidate)

if not code_targets:
    sys.exit(0)

# Session-cache 확인
session_id = payload.get("session_id") or "default"
cache_dir = Path(".lazy-harness/.cache/session")
cache_dir.mkdir(parents=True, exist_ok=True)
cache_path = cache_dir / f"{session_id}.json"

# A non-complete or errored-complete Reader join starts a fresh direct-fallback
# evidence boundary. Invalidate both prior calls and legacy session cache before
# applying the cache fast path.
recent = payload.get("recent_tool_calls", []) or []
reader_terminal_boundary = False
for index in range(len(recent) - 1, -1, -1):
    call = recent[index] if isinstance(recent[index], dict) else {}
    name = str(call.get("name") or call.get("tool") or "")
    if name != "lazy_reader_join":
        continue
    join_args = call.get("args") if isinstance(call.get("args"), dict) else {}
    if bool(call.get("is_error")) or str(join_args.get("status") or "") != "complete":
        recent = recent[index + 1:]
        reader_terminal_boundary = True
    break
if reader_terminal_boundary:
    try:
        cache_path.unlink(missing_ok=True)
    except Exception:
        pass
elif cache_path.exists():
    try:
        cache = json.loads(cache_path.read_text())
        if cache.get("search_performed"):
            sys.exit(0)
    except Exception:
        pass

# Tool-call 이력에서 검색 흔적 탐지
search_record_dirs = ("domain", "spec", "behavior", "tests", "decisions", "ssot", "planning", "plans", "project", "knowledge")

def walk_values(value):
    if value is None:
        return
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_values(child)
        return
    if isinstance(value, list):
        for child in value:
            yield from walk_values(child)
        return
    yield str(value)

def args_blob(call):
    parts = []
    for key in ("name", "tool", "recipient_name", "args_preview", "args", "parameters", "arguments", "command", "path", "file_path"):
        parts.extend(walk_values(call.get(key)) or [])
    return "\n".join(parts).replace("\\", "/")

def call_name(call):
    return str(call.get("name") or call.get("tool") or call.get("recipient_name") or "").lower()

def flatten_calls(calls):
    for call in calls:
        if not isinstance(call, dict):
            continue
        yield call
        for key in ("args", "parameters", "input", "arguments"):
            value = call.get(key)
            if isinstance(value, dict):
                nested = value.get("tool_calls") or value.get("toolCalls") or value.get("tool_uses") or []
                if isinstance(nested, list):
                    yield from flatten_calls(nested)

def hit_record_dir(blob: str) -> bool:
    blob = str(blob or "").replace("\\", "/")
    if ".lazy-harness" not in blob:
        return False
    if any(f".lazy-harness/{d}" in blob for d in search_record_dirs):
        return True
    for m in re.finditer(r"\.lazy-harness/\{([^}]*)\}", blob):
        tokens = {part.strip().strip("/") for part in m.group(1).split(",")}
        if tokens.intersection(search_record_dirs):
            return True
    # Root inventory over `.lazy-harness` is valid harness-first evidence.
    return bool(re.search(r"\.lazy-harness(?:/|\b)", blob))

def is_read_or_search(name: str, blob: str) -> bool:
    if any(token in name for token in ("read", "grep", "agentgrep", "glob", "search", "list", "directory", "tree", "find", "ls")):
        return True
    if name in ("bash", "functions.bash"):
        return bool(re.search(r"\b(grep|rg|find|tree|ls|git\s+grep|git\s+ls-files)\b|reference-resolver|(?:\.lazy-harness/bin/lazy|\blazy)\s+map\b", blob, re.IGNORECASE))
    return False

search_seen = False
for call in flatten_calls(recent):
    name = call_name(call)
    blob = args_blob(call)
    if name == "lazy_reader_join":
        join_args = call.get("args") if isinstance(call.get("args"), dict) else call.get("parameters") if isinstance(call.get("parameters"), dict) else {}
        if (
            not bool(call.get("is_error"))
            and str(join_args.get("status") or "") == "complete"
            and str(join_args.get("resultMarker") or "") == "LAZY_HARNESS_READER_RESULT: complete"
        ):
            search_seen = True; break
        continue
    if hit_record_dir(blob) and is_read_or_search(name, blob):
        search_seen = True; break

if search_seen:
    cache_path.write_text(json.dumps({
        "search_performed": True,
        "first_seen_at": datetime.utcnow().isoformat() + "Z",
    }))
    sys.exit(0)

# === DENY ===
target_path = code_targets[0] if code_targets else "<token>"
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
