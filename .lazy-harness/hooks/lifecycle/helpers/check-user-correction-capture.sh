#!/usr/bin/env bash
# check-user-correction-capture.sh — user correction / repeated mistake convergence gate
#
# If the user corrects the agent and the assistant acknowledges a mistake, the
# turn must converge into durable harness/project records or a correction ledger.
# Otherwise the same mistake is likely to repeat in a later session.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json
import os
import re
import sys

try:
    payload = json.loads(os.environ.get("PAYLOAD_JSON", "{}"))
except Exception:
    sys.exit(0)

WRITE_TOOLS = {
    "Write", "Edit", "MultiEdit", "write", "edit", "multiedit",
    "mcp__filesystem__write_file", "mcp__filesystem__edit_file",
}
CAPTURE_RE = re.compile(
    r"\.lazy-harness/(?:(?:domain|spec|behavior|tests|decisions|ssot|planning|plans)/[^\s\"'`,)}]+|knowledge/(?:candidates|graph|graph-drafts|corrections)\.jsonl|logs/corrections\.jsonl)"
)
SOURCE_FIX_RE = re.compile(
    r"\.lazy-harness/(?:hooks|scripts|bin|schemas|manifests|AGENTS\.md|spec/platform/)[^\s\"'`,)}]*"
)

last_user = str(payload.get("last_user_message") or "")
assistant = str(payload.get("assistant_response") or "")

strings: list[str] = []

def walk(value):
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)

walk(payload)
blob = "\n".join(strings)
lower_user = last_user.lower()
lower_assistant = assistant.lower()
lower_blob = blob.lower()

# User correction / repeated mistake cues. These are intentionally concrete and
# tuned for the recurring failure modes observed in dogfood sessions.
user_correction_patterns = [
    r"\b아니\b",
    r"그게\s*아니",
    r"맞지\s*않",
    r"틀렸",
    r"잘못",
    r"정신\s*나갔",
    r"병신",
    r"자꾸\s*실수",
    r"반복\s*실수",
    r"계속\s*누락",
    r"누락하고",
    r"기록하지\s*않",
    r"기록하는\s*게\s*아니",
    r"하네스\s*수정",
    r"잊지마",
    r"제대로\s*(?:안|못)",
    r"not\s+what\s+i\s+meant",
    r"you\s+are\s+wrong",
    r"wrong\s+target",
]
assistant_ack_patterns = [
    r"맞습니다",
    r"죄송",
    r"제가\s*(?:또\s*)?(?:잘못|실수)",
    r"방향을\s*(?:잘못|틀)",
    r"정정",
    r"보정",
    r"누락",
    r"수정하겠습니다",
    r"고치겠습니다",
]

user_corrected = bool(last_user) and any(re.search(p, lower_user, re.IGNORECASE) for p in user_correction_patterns)
assistant_ack = bool(assistant) and any(re.search(p, lower_assistant, re.IGNORECASE) for p in assistant_ack_patterns)

if not (user_corrected and assistant_ack):
    sys.exit(0)

# Same-turn durable capture satisfies the gate.
for call in payload.get("recent_tool_calls", []) or []:
    if str(call.get("name", "")) not in WRITE_TOOLS:
        continue
    parts = []
    for key in ("args_preview", "args", "input", "arguments", "command", "file_path", "path"):
        value = call.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            parts.append(value)
        else:
            try:
                parts.append(json.dumps(value, ensure_ascii=False))
            except Exception:
                parts.append(str(value))
    args_blob = "\n".join(parts)
    if CAPTURE_RE.search(args_blob):
        sys.exit(0)

# Explicit response judgement can satisfy only when paired with a durable path.
if (
    "correction capture" in lower_blob
    and ("primary record" in lower_blob or "corrections.jsonl" in lower_blob)
    and CAPTURE_RE.search(blob)
):
    sys.exit(0)

# A harness-source edit alone is not enough, because the failure we are blocking
# is forgetting to converge the correction into a searchable durable record. But
# if the assistant both edited harness source and named a follow-up durable record
# path, allow the turn to continue so implementation can complete.
source_fix_touched = False
for call in payload.get("recent_tool_calls", []) or []:
    if str(call.get("name", "")) not in WRITE_TOOLS:
        continue
    args_blob = str(call.get("args_preview", "")) + "\n" + str(call.get("args", ""))
    if SOURCE_FIX_RE.search(args_blob):
        source_fix_touched = True
        break
if source_fix_touched and CAPTURE_RE.search(blob) and "primary record" in lower_blob:
    sys.exit(0)

print("STOP. User correction capture gate: 사용자가 에이전트 실수/방향 오류를 정정했고, assistant가 이를 인정했지만 durable capture가 없습니다.\n")
print("문제: '맞습니다/죄송/제가 잘못'만 말하고 끝내면 같은 실수가 반복됩니다.")
print("\n해야 할 일:")
print("  A. 적절한 .lazy-harness/{ssot,spec,behavior,tests,decisions,planning}/ record에 Correction capture 섹션 추가 (Recommended)")
print("  B. 확정 전이면 .lazy-harness/knowledge/corrections.jsonl 또는 .lazy-harness/logs/corrections.jsonl 에 한 줄 기록")
print("  C. 하네스 자체 문제면 source 코드 수정 + primary record/Implementation map 함께 갱신")
print("  D. 반복 실수 방지책이 애매하면 옵션 게이트로 사용자 확인")
print("\n규칙: ADR 0032 user correction convergence + Analysis discovery capture. 말로만 사과하지 말고 기록/기능으로 수렴하세요.")
PY
