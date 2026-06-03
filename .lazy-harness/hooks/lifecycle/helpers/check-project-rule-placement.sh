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
import hashlib
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path('.lazy-harness/hooks/lifecycle/helpers').resolve()))
try:
    from runtime_paths import runtime_state_path
except Exception:
    runtime_state_path = None

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

# Jcode can surface blocking hook output back into the next turn as
# last_user_message. Only this structural field is allowed to trigger the echo
# guard; do not scan the whole payload/blob, because assistant discussion of a
# STOP text should not weaken normal project-rule detection.
last_user_message = str(payload.get("last_user_message") or "")
last_lower = last_user_message.lower()
if (
    (
        last_lower.startswith("stop. project rule placement gate")
        or last_lower.startswith("stop. rule placement duplication")
    )
    and ("해야 할 일:" in last_user_message or "중복 key:" in last_user_message)
    and ("rule placement" in last_lower)
):
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
    # Non-applicable judgement: the assistant explicitly concluded there is no
    # project rule to place. This is a completed no-op judgement and must not
    # be reinterpreted as a new "record this rule" action just because Korean
    # text includes "기록" inside "기록하지 않음".
    has_noop_scope = re.search(r"scope\s*:\s*(?:non-applicable|not-applicable|none|n/a)", normalized)
    has_noop_rule = re.search(r"rule\s*:\s*(?:없음|none|n/a|not applicable|non-applicable)", normalized)
    has_noop_record = re.search(r"primary\s+record\s*:\s*(?:none|없음|n/a|not applicable|non-applicable)", normalized)
    has_confirmation = re.search(r"confirmation\s*:\s*(?:user-confirmed|inferred-from-record)", normalized)
    if has_noop_scope and has_noop_rule and has_noop_record and has_confirmation:
        return True

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


def duplicate_rule_placement_keys(text: str) -> list[str]:
    """Return duplicate (rule, primary-record) keys across placement-like blocks.

    This catches assistant amplification where the same product rule is emitted as
    both "Product rule placement" and "Related product rule placement" in one
    response. A complete placement judgement is useful once; repeated copies are
    noise and can look like an infinite loop to the user.
    """
    normalized = text.replace("`", "")
    # Split loosely on placement headings while preserving bullet bodies.
    chunks = re.split(r"(?im)^\s*(?:#+\s*)?(?:related\s+)?(?:product\s+)?rule\s+placement\s*$", normalized)
    keys = []
    for chunk in chunks:
        rule_match = re.search(r"(?im)^\s*(?:[-*•]\s*)?rule\s*:\s*(.+?)\s*$", chunk)
        record_match = re.search(r"(?im)^\s*(?:[-*•]\s*)?primary\s+record\s*:\s*(.+?)\s*$", chunk)
        if not rule_match or not record_match:
            continue
        rule = re.sub(r"\s+", " ", rule_match.group(1).strip().lower())
        record = re.sub(r"\s+", " ", record_match.group(1).strip().lower())
        if rule and record:
            keys.append(f"{rule} -> {record}")
    seen = set()
    duplicates = []
    for key in keys:
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    return duplicates

# Complete Rule placement judgement satisfies the gate. Accept bullets, missing
# Markdown heading markers, and `.jcode` with or without backticks.
duplicate_keys = duplicate_rule_placement_keys(blob)
if duplicate_keys:
    print("STOP. Rule placement duplication: 같은 Rule placement 판단을 한 응답에서 반복 출력했습니다.\n")
    print("해야 할 일: 같은 rule/primary record 조합은 한 번만 남기고, 관련 판단은 중복 블록이 아니라 한 줄 cross-reference 로 압축하세요.")
    print("중복 key:")
    for key in duplicate_keys[:5]:
        print(f"  - {key}")
    sys.exit(0)

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
negative_noop_cues = [
    "기록하지 않음", "기록 안 함", "기록하지 않았다", "기록하지 않아도", "기록할 필요 없음",
    "not recording", "do not record", "no record", "no recording", "non-applicable", "not applicable",
]

has_rule = any(cue in lower for cue in [c.lower() for c in rule_cues])
has_placement = any(cue in lower for cue in [c.lower() for c in placement_cues])
has_workflow = any(cue in lower for cue in [c.lower() for c in workflow_cues])
has_action = any(cue in lower for cue in [c.lower() for c in action_cues])
has_status_only = any(cue in lower for cue in [c.lower() for c in status_only_cues])
has_negative_noop = any(cue in lower for cue in [c.lower() for c in negative_noop_cues])
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
if has_negative_noop and not write_touched and not jcode_touched and not memory_rule_touched:
    sys.exit(0)
if not (jcode_touched or memory_rule_touched or (has_rule and has_action and (has_placement or has_workflow))):
    sys.exit(0)


def gate_already_open_this_turn() -> bool:
    """Suppress duplicate project-rule placement gates for one response turn.

    Production jcode response.completed payloads may omit assistant_response, so a
    STOP reminder can be re-derived from the same stable inputs. The BDD helper
    already protects this class with `$LAZY_RUNTIME_ROOT/state/open-gates.json`; use
    the same runtime state contract here to prevent visible Rule placement loops.
    """
    message_id = str(payload.get("message_id") or "unknown")
    recent = []
    for call in payload.get("recent_tool_calls", []) or []:
        recent.append({
            "name": str(call.get("name", "")),
            "blob": call_blob(call),
        })
    fp_input = json.dumps({
        "last_user_message": payload.get("last_user_message") or "",
        "recent_tool_calls": recent,
        "jcode_touched": jcode_touched,
        "memory_rule_touched": memory_rule_touched,
        "has_rule": has_rule,
        "has_action": has_action,
        "has_placement": has_placement,
        "has_workflow": has_workflow,
    }, ensure_ascii=False, sort_keys=True)
    fingerprint = hashlib.sha1(fp_input.encode("utf-8")).hexdigest()[:16]
    key = f"project-rule-placement:{fingerprint}"
    if runtime_state_path is not None:
        state_path = runtime_state_path(Path.cwd(), "open-gates.json", payload)
    else:
        state_path = Path(os.environ.get("LAZY_RUNTIME_ROOT") or ".lazy-harness/.runtime") / "state" / "open-gates.json"
    state = {"last_message_id": "", "open_fingerprints": {}}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            state = {"last_message_id": "", "open_fingerprints": {}}
    if state.get("last_message_id") != message_id:
        state = {"last_message_id": message_id, "open_fingerprints": {}}
    opens = state.setdefault("open_fingerprints", {})
    if key in opens:
        return True
    opens[key] = {
        "first_seen_message_id": message_id,
        "first_seen_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    state["open_fingerprints"] = opens
    state["last_message_id"] = message_id
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass
    return False


if gate_already_open_this_turn():
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
