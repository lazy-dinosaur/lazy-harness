#!/usr/bin/env bash
# check-context-first.sh — prevent premature source digging before lazy-harness record/context lookup.
#
# Input: Jcode tool.execute.before payload as argv[1] or stdin.
# Output: plain deny reason when a source search should first consult records, else silent.
# Wrapper is responsible for converting output to Jcode hook decision JSON.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && PAYLOAD=$(cat 2>/dev/null || true)
[ -z "$PAYLOAD" ] && exit 0

python3 - "$PAYLOAD" <<'PY'
import json
import re
import sys
from datetime import datetime
from pathlib import Path

raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    payload = json.loads(raw) if raw.strip() else {}
except Exception:
    sys.exit(0)

tool = payload.get("tool", {}) or {}
root_name = str(tool.get("name", "")).lower()
root_args = tool.get("args", {}) or {}
session_id = str(payload.get("session_id") or "")

record_paths = [
    ".lazy-harness/domain",
    ".lazy-harness/spec",
    ".lazy-harness/behavior",
    ".lazy-harness/tests",
    ".lazy-harness/decisions",
    ".lazy-harness/ssot",
    ".lazy-harness/regression",
    ".lazy-harness/logs/decisions",
    ".lazy-harness/scripts/reference-resolver",
]
source_roots = ["src/", "app/", "packages/", "prisma/", "tests/"]
knowledge_keywords = [
    "chat", "chatwindow", "message", "notification", "toast", "overlay", "patient",
    "referral", "appointment", "emr", "auth", "hospital", "queue", "coordinator",
    "pc", "person", "sender", "author", "device", "deviceid", "ismine", "participant",
    "채팅", "메시지", "알림", "토스트", "오버레이", "환자", "예약", "병원", "인증",
]


def lower_blob(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.lower()
    try:
        return json.dumps(value, ensure_ascii=False).lower()
    except Exception:
        return str(value).lower()


def is_record_lookup(blob: str) -> bool:
    return any(path in blob for path in record_paths)


def has_source_target(blob: str, *, default_source: bool = False) -> bool:
    if is_record_lookup(blob):
        return False
    if any(root in blob for root in source_roots):
        return True
    if re.search(r"\.(ts|tsx|js|jsx|vue|svelte|prisma|sql|md)\b", blob):
        return True
    return default_source


def keyword(blob: str) -> str | None:
    return next((entry for entry in knowledge_keywords if entry in blob), None)


def cache_path() -> Path | None:
    if not session_id:
        return None
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)[:120]
    return Path(".lazy-harness/.cache/session") / f"context-first-{safe}.json"


def cache_is_set() -> bool:
    path = cache_path()
    if not path or not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return bool(data.get("record_context_seen"))


def set_cache(topic: str) -> None:
    path = cache_path()
    if not path:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "record_context_seen": True,
            "topic": topic,
            "first_seen_at": datetime.utcnow().isoformat() + "Z",
        }, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def operation_blobs(name: str, args) -> list[tuple[str, str, bool]]:
    """Return (tool_name, searchable blob, default_source) entries."""
    name = name.lower()
    if name == "batch" and isinstance(args, dict):
        out: list[tuple[str, str, bool]] = []
        for call in args.get("tool_calls", []) or []:
            if not isinstance(call, dict):
                continue
            call_name = str(call.get("tool") or call.get("name") or "").lower()
            call_args = {k: v for k, v in call.items() if k not in {"tool", "name"}}
            out.extend(operation_blobs(call_name, call_args))
        return out
    if name in {"bash", "shell", "functions.bash"}:
        command = ""
        if isinstance(args, dict):
            command = str(args.get("command") or args.get("cmd") or args.get("script") or "")
        elif isinstance(args, str):
            command = args
        blob = command.lower()
        if not re.search(r"(^|[;&|()\s])(rg|grep|ag|fd|find|sed|awk|cat|less|bat|nl)\b", blob):
            return []
        # Build/test/git/status commands should stay unblocked.
        allow_patterns = [
            r"\bgit\s+(status|diff|log|show|branch|rev-parse)\b",
            r"\b(jcode|lazy|bun|npm|pnpm|yarn|python3?)\s+.*\b(test|doctor|lint|build|typecheck)\b",
            r"\b(ls|pwd|wc)\b",
        ]
        if any(re.search(pattern, blob) for pattern in allow_patterns):
            return []
        return [(name, blob, False)]
    if name in {"agentgrep", "grep", "glob"}:
        return [(name, lower_blob(args), True)]
    if name in {"read"}:
        return [(name, lower_blob(args), False)]
    return []

ops = operation_blobs(root_name, root_args)
if not ops:
    sys.exit(0)

for _name, blob, _default_source in ops:
    topic = keyword(blob) or "record-context"
    if is_record_lookup(blob):
        set_cache(topic)
        sys.exit(0)

if cache_is_set():
    sys.exit(0)

for op_name, blob, default_source in ops:
    topic = keyword(blob)
    if not topic:
        continue
    if not has_source_target(blob, default_source=default_source):
        continue
    blocked = blob[:500]
    print(f"""[lazy-harness context-first gate] 바로 source를 뒤지기 전에 기존 기록/지식 그래프를 먼저 확인하세요.
감지된 주제: {topic}
차단된 도구: {op_name}
차단된 내용: {blocked}

먼저 아래 중 하나를 실행한 뒤 다시 source 검색/읽기를 하세요:

  1) rg -n "{topic}" .lazy-harness/domain .lazy-harness/spec .lazy-harness/behavior .lazy-harness/decisions .lazy-harness/ssot .lazy-harness/regression
  2) bun .lazy-harness/scripts/reference-resolver.ts --query "{topic}" --format ask
  3) 기록이 없으면: knowledge-intake 후보로 등록/질문하고 그 다음 source 확인

목적: 대화/구현 전에 DDD/SDD/BDD/TDD/ADR/SSOT 자료를 먼저 참고하게 강제.""")
    sys.exit(0)

sys.exit(0)
PY
