#!/usr/bin/env bash
# check-analysis-discovery-capture.sh — ADR 0034 analysis/planning capture gate
#
# Prevent high-confidence analysis/planning turns from ending with discovered
# DDD/SDD/BDD/TDD/ADR/SSOT/Planning facts or backlog only in chat.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json
import re
import sys
import os

try:
    payload = json.loads(os.environ.get("PAYLOAD_JSON", "{}"))
except Exception:
    sys.exit(0)

WRITE_TOOLS = {
    "Write", "Edit", "MultiEdit", "write", "edit", "multiedit",
    "mcp__filesystem__write_file", "mcp__filesystem__edit_file",
}
CAPTURE_RE = re.compile(
    r"\.lazy-harness/(?:(?:domain|spec|behavior|tests|decisions|ssot|planning)/[^\s\"'`,)}]+|knowledge/(?:candidates|graph-drafts)\.jsonl)"
)

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
if not blob.strip():
    sys.exit(0)

# Same-turn capture via write/edit paths satisfies the gate.
for call in payload.get("recent_tool_calls", []) or []:
    if str(call.get("name", "")) not in WRITE_TOOLS:
        continue
    args_blob = str(call.get("args_preview", ""))
    if CAPTURE_RE.search(args_blob):
        sys.exit(0)

# Explicit local judgement satisfies the gate if all required buckets are named.
required = ["DDD", "SDD", "BDD", "TDD", "ADR", "SSOT", "Planning"]
if "Discovery capture" in blob and all(term in blob for term in required):
    sys.exit(0)

upper_blob = blob.upper()
layer_terms = {
    "DDD": ["DDD", ".LAZY-HARNESS/DOMAIN"],
    "SDD": ["SDD", ".LAZY-HARNESS/SPEC"],
    "BDD": ["BDD", ".LAZY-HARNESS/BEHAVIOR"],
    "TDD": ["TDD", ".LAZY-HARNESS/TESTS"],
    "ADR": ["ADR", ".LAZY-HARNESS/DECISIONS"],
    "SSOT": ["SSOT", ".LAZY-HARNESS/SSOT"],
    "PLANNING": ["PLANNING", ".LAZY-HARNESS/PLANNING"],
}
matched_layers = [name for name, needles in layer_terms.items() if any(needle in upper_blob for needle in needles)]

plan_cues = [
    "analysis", "analyzed", "discovered", "implementation plan", "plan", "planning", "backlog",
    "계획", "분석", "목차", "코드분석", "발견", "백로그",
]
lower_blob = blob.lower()
has_plan_cue = any(cue.lower() in lower_blob for cue in plan_cues)
has_numbered_steps = bool(re.search(r"(?m)^\s*(?:\d+[.)]|[-*]\s+(?:phase|step|todo|backlog))\b", blob, re.IGNORECASE))

# High-confidence only: multiple layer concepts plus planning/analysis cues.
if len(matched_layers) < 3 or not (has_plan_cue or has_numbered_steps):
    sys.exit(0)

print("STOP. Analysis discovery capture gate: 분석/계획 중 발견한 layer 지식이나 backlog 를 chat 에만 남기면 안 됩니다.\n")
print("감지된 layer 후보: " + ", ".join(matched_layers))
print("\n해야 할 일:")
print("  A. 관련 DDD/SDD/BDD/TDD/ADR/SSOT record 를 추가/갱신 (Recommended)")
print("  B. 확정 전 지식은 .lazy-harness/knowledge/candidates.jsonl 또는 graph-drafts.jsonl 에 후보로 기록")
print("  C. 다단계 계획/backlog 는 .lazy-harness/planning/ 에 기록")
print("  D. 응답/record 에 `Discovery capture` 섹션을 추가하고 DDD/SDD/BDD/TDD/ADR/SSOT/Planning 각각 updated/candidate/none 판단 기록")
print("  E. layer/plan 범위가 애매하면 사용자에게 옵션 게이트로 확인")
print("  F. 의식적 skip 이면 .lazy-harness/logs/skipped.jsonl 에 사유 기록")
print("\n규칙: AGENTS §2.4 Analysis discovery capture (ADR 0034).")
PY
