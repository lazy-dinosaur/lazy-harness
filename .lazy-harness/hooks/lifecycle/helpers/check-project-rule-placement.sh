#!/usr/bin/env bash
# check-project-rule-placement.sh — project-specific rule routing gate
#
# Prevent project/team rules from being routed to .jcode by default without
# a Rule placement judgement.

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
MEMORY_TOOLS = {"memory", "functions.memory"}
LAZY_CAPTURE_RE = re.compile(
    r"\.lazy-harness/(?:(?:domain|spec|behavior|tests|decisions|ssot|planning)/[^\s\"'`,)}]+|knowledge/(?:candidates|graph-drafts)\.jsonl)"
)
JCODE_RULES = ".jcode/harness/20-project-rules.md"

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
lower = blob.lower()
if not blob.strip():
    sys.exit(0)


def call_blob(call):
    parts = []
    for key in ("args_preview", "args", "input", "arguments"):
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
    return "\n".join(parts)


def has_rule_placement_judgement(text: str) -> bool:
    normalized = text.lower().replace("`", "")
    required_patterns = [
        r"rule\s*placement",
        r"rule\s*:",
        r"scope\s*:",
        r"primary\s+record\s*:",
        r"why\s+not\s+agents\.md\s*:",
        r"why\s+not\s+\.?jcode\s*:",
        r"confirmation\s*:",
    ]
    return all(re.search(pattern, normalized, re.IGNORECASE) for pattern in required_patterns)

# Complete Rule placement judgement satisfies the gate. Accept bullets, missing
# Markdown heading markers, and `.jcode` with or without backticks.
if has_rule_placement_judgement(blob):
    sys.exit(0)

MEMORY_RULE_CUES = [
    "프로젝트 규칙", "프로젝트마다 규칙", "규칙", "룰", "team policy", "project policy",
    "project-specific", "workflow", "ownership", "source-of-truth", "forbidden",
    "운영", "정책", "소유권", "수정 금지", "worktree", "cwd", "bun wt",
]
memory_rule_touched = False
for call in payload.get("recent_tool_calls", []) or []:
    if str(call.get("name", "")) not in MEMORY_TOOLS:
        continue
    args_blob = call_blob(call)
    args_lower = args_blob.lower()
    is_remember = "remember" in args_lower or ('"action"' in args_lower and '"remember"' in args_lower)
    if is_remember and any(cue.lower() in args_lower for cue in MEMORY_RULE_CUES):
        memory_rule_touched = True

# Same-turn .lazy-harness record/planning capture satisfies the gate.
if not memory_rule_touched:
    for call in payload.get("recent_tool_calls", []) or []:
        if str(call.get("name", "")) not in WRITE_TOOLS:
            continue
        args_blob = call_blob(call)
        if LAZY_CAPTURE_RE.search(args_blob):
            sys.exit(0)

# .jcode write is allowed only with explicit local-only judgement.
jcode_touched = False
for call in payload.get("recent_tool_calls", []) or []:
    if str(call.get("name", "")) not in WRITE_TOOLS:
        continue
    args_blob = call_blob(call)
    if JCODE_RULES in args_blob:
        jcode_touched = True
        if "jcode-local" in lower or "local-only" in lower or "local only" in lower:
            sys.exit(0)

rule_cues = [
    "프로젝트 규칙", "프로젝트마다 규칙", "규칙 추가", "룰 추가", "rule", "rules differ", "project-specific",
    "어디에 기록", "어디에 저장", "문서화", "source of truth", "ssot",
]
placement_cues = [".jcode", "20-project-rules", "agents.md", "agENTS.md".lower(), ".lazy-harness", "rule-sources"]
workflow_cues = ["workflow", "ownership", "source-of-truth", "forbidden", "운영", "정책", "소유권", "수정 금지"]
action_cues = [
    "추가", "기록", "저장", "옮", "이동", "마이그레이션", "바꾸", "변경", "정정", "고정",
    "add", "record", "store", "move", "migrate", "change", "correct", "route", "place",
]
status_only_cues = [
    "적용됨", "적용됐", "있음", "이미", "확인", "status", "applied", "synced", "exists",
]

has_rule = any(cue in lower for cue in [c.lower() for c in rule_cues])
has_placement = any(cue in lower for cue in [c.lower() for c in placement_cues])
has_workflow = any(cue in lower for cue in [c.lower() for c in workflow_cues])
has_action = any(cue in lower for cue in [c.lower() for c in action_cues])
has_status_only = any(cue in lower for cue in [c.lower() for c in status_only_cues])
has_forward_action = any(cue in lower for cue in [
    "해야", "하겠", "할게", "하자", "필요", "빠져", "누락", "추가해야", "기록해야",
    "will", "need", "needs", "missing", "should", "must",
])
write_touched = any(str(call.get("name", "")) in WRITE_TOOLS for call in payload.get("recent_tool_calls", []) or [])

# High-confidence only. Casual/status reporting about existing records should stay silent.
# The gate is for newly discovered/corrected/routed project rules, not for answers
# that merely report whether a known policy is already recorded or synced.
if has_status_only and not has_forward_action and not write_touched and not jcode_touched and not memory_rule_touched:
    sys.exit(0)
if not (jcode_touched or memory_rule_touched or (has_rule and has_action and (has_placement or has_workflow))):
    sys.exit(0)

print("STOP. Project rule placement gate: 프로젝트별 rule/correction 을 어디에 둘지 판정 없이 진행하면 안 됩니다.\n")
print("해야 할 일:")
print("  A. .lazy-harness/ssot/... shared project rule 로 기록 (Recommended for team/project policy)")
print("  B. .lazy-harness/decisions/... trade-off/why decision 으로 기록")
print("  C. .lazy-harness/planning/... transient plan/backlog 로 기록")
print("  D. .jcode/harness/20-project-rules.md local/private Jcode-only 로 기록하고 `Rule placement` 에 jcode-local 명시")
print("  E. Jcode memory 에 잘못 저장했다면 memory forget 후 canonical .lazy-harness record 로 재기록")
print("  F. 직접 입력 / ambiguous 면 옵션 게이트로 사용자 확인")
print("\n필수 판단:")
print("  ## Rule placement")
print("  - Rule: ...")
print("  - Scope: framework-global | host-project | team-policy | layer-fact | jcode-local | transient-plan | ambiguous")
print("  - Primary record: ...")
print("  - Why not AGENTS.md: ...")
print("  - Why not `.jcode`: ...")
print("  - Confirmation: user-confirmed | inferred-from-record | needs-option-gate")
print("\n규칙: .lazy-harness/ssot/rule-sources.md + SDD project-rule-router.")
PY
