#!/usr/bin/env bash
# check-context-first.sh — prevent premature source digging before lazy-harness record/context lookup.
#
# Input: Jcode tool.execute.before payload for bash as argv[1] or stdin.
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

raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    payload = json.loads(raw) if raw.strip() else {}
except Exception:
    sys.exit(0)

tool = payload.get("tool", {}) or {}
name = str(tool.get("name", "")).lower()
if name not in {"bash", "shell", "functions.bash"}:
    sys.exit(0)

args = tool.get("args", {}) or {}
command = ""
if isinstance(args, dict):
    command = str(args.get("command") or args.get("cmd") or args.get("script") or "")
elif isinstance(args, str):
    command = args

if not command.strip():
    sys.exit(0)

cmd = command.lower()

# Only gate source-inspection commands. Build/test/git/status commands should stay unblocked.
search_like = re.search(r"(^|[;&|()\s])(rg|grep|ag|fd|find|sed|awk|cat|less|bat|nl)\b", cmd)
if not search_like:
    sys.exit(0)

# Explicit record/context lookups are allowed and count as the correct first move.
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
if any(path in cmd for path in record_paths):
    sys.exit(0)

# Allow broad repo hygiene that is not knowledge/domain investigation.
allow_patterns = [
    r"\bgit\s+(status|diff|log|show|branch|rev-parse)\b",
    r"\b(jcode|lazy|bun|npm|pnpm|yarn|python3?)\s+.*\b(test|doctor|lint|build|typecheck)\b",
    r"\b(ls|pwd|wc)\b",
]
if any(re.search(pattern, cmd) for pattern in allow_patterns):
    sys.exit(0)

# Keywords that usually mean the user asked for existing project knowledge/feature behavior.
knowledge_keywords = [
    "chat", "chatwindow", "message", "notification", "toast", "overlay", "patient",
    "referral", "appointment", "emr", "auth", "hospital", "queue", "coordinator",
    "채팅", "메시지", "알림", "토스트", "오버레이", "환자", "예약", "병원", "인증",
]
mentions_knowledge = any(keyword in cmd for keyword in knowledge_keywords)

# If the command searches source/application files and has a knowledge keyword, force record-first.
source_paths = [" src/", "src/", " app/", "app/", " packages/", "packages/", " prisma/", "prisma/"]
searches_source = any(path in f" {cmd}" for path in source_paths) or re.search(r"\.(ts|tsx|js|jsx|vue|svelte|prisma|sql|md)\b", cmd)

if not (mentions_knowledge and searches_source):
    sys.exit(0)

keyword_hint = next((keyword for keyword in knowledge_keywords if keyword in cmd), "<topic>")
print(f"""[lazy-harness context-first gate] 바로 source를 뒤지기 전에 기존 기록/지식 그래프를 먼저 확인하세요.
감지된 주제: {keyword_hint}
차단된 명령: {command}

먼저 아래 중 하나를 실행한 뒤 다시 source 검색하세요:

  1) rg -n "{keyword_hint}" .lazy-harness/domain .lazy-harness/spec .lazy-harness/behavior .lazy-harness/decisions .lazy-harness/ssot .lazy-harness/regression
  2) bun .lazy-harness/scripts/reference-resolver.ts --query "{keyword_hint}" --format ask
  3) 기록이 없으면: knowledge-intake 후보로 등록/질문하고 그 다음 source 확인

목적: 대화/구현 전에 DDD/SDD/BDD/TDD/ADR/SSOT 자료를 먼저 참고하게 강제.""")
PY
