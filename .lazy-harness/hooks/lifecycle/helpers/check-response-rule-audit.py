#!/usr/bin/env python3
"""response.completed audit for surfaced relevant-record digests.

Phase 4 of the organic memory loop:
- message.received stores a sanitized journal of digests surfaced before a turn.
- response.completed reads that journal and emits concise feedback only when
  evidence shows a surfaced rule or record-completion obligation was missed.

The helper is deliberately conservative. It never stores raw user/assistant text
and stays silent unless there is a strong artifact/capture signal.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from runtime_paths import runtime_state_path
except Exception:  # pragma: no cover - lifecycle helper must fail open
    runtime_state_path = None  # type: ignore[assignment]

PAYLOAD_RAW = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    PAYLOAD = json.loads(PAYLOAD_RAW or "{}")
except Exception:
    PAYLOAD = {}
if not isinstance(PAYLOAD, dict):
    raise SystemExit(0)

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
if runtime_state_path is not None:
    DIGEST_JOURNAL = runtime_state_path(ROOT, "surfaced-rule-digests.jsonl", PAYLOAD)
    PACKET_JOURNAL = runtime_state_path(ROOT, "search-read-debt.jsonl", PAYLOAD)
else:
    _runtime_root = Path(os.environ.get("LAZY_RUNTIME_ROOT") or (ROOT / ".lazy-harness" / ".runtime"))
    DIGEST_JOURNAL = _runtime_root / "state" / "surfaced-rule-digests.jsonl"
    PACKET_JOURNAL = _runtime_root / "state" / "search-read-debt.jsonl"
TOOL_EVENTS_JOURNAL = ROOT / ".jcode" / "hooks" / "tool-events.jsonl"
TTL_SECONDS = int(os.environ.get("LAZY_RESPONSE_RULE_AUDIT_TTL_SECONDS", "7200") or "7200")

WRITE_TOOLS = {
    "Write", "Edit", "MultiEdit", "write", "edit", "multiedit",
    "mcp__filesystem__write_file", "mcp__filesystem__edit_file",
}
PR_TOOLS = {
    "mcp__github__create_pull_request",
    "mcp__github__update_pull_request",
    "create_pull_request",
    "update_pull_request",
}
READ_EVIDENCE_TOOLS = {
    "Read", "read", "mcp__filesystem__read_text_file", "mcp__filesystem__read_file",
    "mcp__filesystem__read_multiple_files", "agentgrep", "grep", "bash",
    "glob", "ls", "lsp", "mcp__github__get_file_contents",
}
SEARCH_DEBT_LEVELS = {"self-resolve-before-answer", "self-resolve-before-change", "delegate-search"}
SEARCH_EVIDENCE_TOOLS = set()
CAPTURE_RE = re.compile(
    r"\.lazy-harness/(?:(?:domain|spec|behavior|tests|decisions|ssot|planning|plans)/[^\s\"'`,)}]+|knowledge/(?:candidates|graph|graph-drafts|corrections)\.jsonl|logs/corrections\.jsonl)"
)
FRAMEWORK_SOURCE_RE = re.compile(r"\.lazy-harness/(?:hooks|scripts|bin|schemas|manifests|AGENTS\.md|spec/platform/)\S*")
PR_ARTIFACT_RE = re.compile(r"\b(?:pull request|PR|gh\s+pr\s+(?:create|edit)|create_pull_request|update_pull_request)\b", re.IGNORECASE)
PR_HEADINGS = [re.compile(r"(?im)^\s*(?:#+\s*)?%s\s*:" % h) for h in ("Why", "What", "Task")]

LAZY_FIND_COMMAND_RE = re.compile(
    r"(?:^|\s)(?:\.lazy-harness/bin/lazy|(?:^|\s)lazy)\s+find(?:\s|$)",
    re.IGNORECASE,
)



def stable_hash(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def walk_strings(value: Any, out: list[str]) -> None:
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            walk_strings(child, out)
    elif isinstance(value, list):
        for child in value:
            walk_strings(child, out)


def call_blob(call: dict[str, Any]) -> str:
    parts: list[str] = []

    def append_value(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            for child in value.values():
                append_value(child)
            try:
                parts.append(json.dumps(value, ensure_ascii=False))
            except Exception:
                pass
        elif isinstance(value, list):
            for child in value:
                append_value(child)
            try:
                parts.append(json.dumps(value, ensure_ascii=False))
            except Exception:
                pass
        else:
            parts.append(str(value))

    for key in ("name", "args_preview", "args", "input", "arguments", "command", "body", "title", "path", "file_path"):
        append_value(call.get(key))
    return "\n".join(parts)


def payload_recent_calls() -> list[dict[str, Any]]:
    calls = PAYLOAD.get("recent_tool_calls") or PAYLOAD.get("recentToolCalls") or []
    return [c for c in calls if isinstance(c, dict)] if isinstance(calls, list) else []


def parse_event_epoch(value: str) -> float:
    text = str(value or "").strip()
    if not text:
        return 0
    try:
        return float(text)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0


def extract_logged_payload(line: str) -> tuple[float, dict[str, Any] | None]:
    text = line.strip()
    if not text:
        return 0, None
    prefix, sep, rest = text.partition(" ")
    if not sep:
        return 0, None
    try:
        payload = json.loads(rest)
    except Exception:
        return 0, None
    if not isinstance(payload, dict):
        return 0, None
    return parse_event_epoch(prefix), payload


def logged_tool_event_calls(packet_row: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not TOOL_EVENTS_JOURNAL.exists():
        return []
    current_message_id = str(PAYLOAD.get("message_id") or PAYLOAD.get("messageId") or "")
    current_session_id = str(PAYLOAD.get("session_id") or PAYLOAD.get("sessionId") or "")
    try:
        packet_epoch = float((packet_row or {}).get("epochSeconds") or 0)
    except Exception:
        packet_epoch = 0
    now = time.time()
    rows: list[dict[str, Any]] = []
    try:
        lines = TOOL_EVENTS_JOURNAL.read_text(encoding="utf-8", errors="ignore").splitlines()[-400:]
    except Exception:
        return []
    for line in lines:
        event_epoch, event = extract_logged_payload(line)
        if not event or event.get("event") != "tool.execute.after":
            continue
        if event_epoch and now - event_epoch > TTL_SECONDS:
            continue
        if packet_epoch and event_epoch and event_epoch < packet_epoch - 5:
            continue
        event_message_id = str(event.get("message_id") or event.get("messageId") or "")
        event_session_id = str(event.get("session_id") or event.get("sessionId") or "")
        same_message = bool(current_message_id and event_message_id == current_message_id)
        same_session = bool(current_session_id and event_session_id == current_session_id)
        if current_message_id:
            if not same_message:
                continue
        elif current_session_id:
            if not same_session:
                continue
        else:
            continue
        tool = event.get("tool") if isinstance(event.get("tool"), dict) else {}
        name = str(tool.get("name") or event.get("tool_name") or event.get("name") or "")
        args = tool.get("args") if isinstance(tool.get("args"), dict) else {}
        rows.append({
            "name": name,
            "args": args or {},
            "args_preview": json.dumps(args or {}, ensure_ascii=False)[:4000],
            "source": "tool-events-journal",
        })
    return rows


def recent_calls() -> list[dict[str, Any]]:
    return payload_recent_calls()


def evidence_calls(packet_row: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    calls = payload_recent_calls()
    logged = logged_tool_event_calls(packet_row)
    if not logged:
        return calls
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for call in [*calls, *logged]:
        key = json.dumps(call, ensure_ascii=False, sort_keys=True, default=str)
        if key in seen:
            continue
        seen.add(key)
        out.append(call)
    return out


def has_lazy_capture() -> bool:
    for call in recent_calls():
        if str(call.get("name") or "") not in WRITE_TOOLS:
            continue
        if CAPTURE_RE.search(call_blob(call)):
            return True
    return False


def changed_framework_source_without_record() -> bool:
    for call in recent_calls():
        if str(call.get("name") or "") not in WRITE_TOOLS:
            continue
        blob = call_blob(call)
        if FRAMEWORK_SOURCE_RE.search(blob) and not CAPTURE_RE.search(blob):
            return True
    return False


def load_journal_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                rows.append(row)
    except Exception:
        return []
    return rows[-200:]


def matching_journal(path: Path) -> dict[str, Any] | None:
    rows = load_journal_rows(path)
    if not rows:
        return None
    now = time.time()
    msg_hash = stable_hash(PAYLOAD.get("message_id") or PAYLOAD.get("messageId"))
    session_hash = stable_hash(PAYLOAD.get("session_id") or PAYLOAD.get("sessionId"))

    # Conservative correlation: do not use the latest journal row for payloads
    # without an identifier. Older lifecycle fixtures and some read-only payloads
    # omit message/session ids; matching those to an unrelated fresh digest causes
    # noisy false positives.
    if not msg_hash and not session_hash:
        return None

    def fresh(row: dict[str, Any]) -> bool:
        try:
            ts = float(row.get("epochSeconds") or 0)
        except Exception:
            ts = 0
        return ts <= 0 or now - ts <= TTL_SECONDS

    for row in reversed(rows):
        if not fresh(row):
            continue
        row_msg = row.get("messageIdHash")
        row_session = row.get("sessionIdHash")
        if msg_hash:
            if row_msg != msg_hash:
                continue
            if session_hash and row_session != session_hash:
                continue
            return row
        if session_hash and row_session == session_hash:
            return row
    return None


def entry_paths(entries: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for entry in entries:
        path = str(entry.get("recordPath") or "")
        if path:
            paths.append(path)
    return paths


def packet_required_paths(row: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    for item in row.get("requiredRead") or []:
        if isinstance(item, dict):
            path = str(item.get("path") or "").strip()
            if path:
                paths.append(path)
    return paths


def packet_has_search_debt(row: dict[str, Any]) -> bool:
    if packet_required_paths(row):
        return False
    level = str(row.get("instructionLevel") or "")
    try:
        fallback_count = int(row.get("fallbackSearchCount") or 0)
    except Exception:
        fallback_count = 0
    return level in SEARCH_DEBT_LEVELS and (fallback_count > 0 or level == "delegate-search")


def has_mutation_tool_call(packet_row: dict[str, Any] | None = None) -> bool:
    for call in evidence_calls(packet_row):
        if str(call.get("name") or "") in WRITE_TOOLS:
            return True
    return False


def has_required_read_evidence(required_paths: list[str], packet_row: dict[str, Any] | None = None) -> bool:
    if not required_paths:
        return True
    normalized = []
    for path in required_paths:
        value = path.strip()
        if value.startswith("./"):
            value = value[2:]
        if value:
            normalized.append(value)
    if not normalized:
        return True
    seen = {path: False for path in normalized}
    for call in evidence_calls(packet_row):
        name = str(call.get("name") or "")
        if name in WRITE_TOOLS:
            continue
        if name not in READ_EVIDENCE_TOOLS:
            continue
        blob = call_blob(call).replace("\\", "/")
        for path in normalized:
            if path and (path in blob or f"./{path}" in blob):
                seen[path] = True
    return all(seen.values())


def shell_has_search_evidence(command: str) -> bool:
    if LAZY_FIND_COMMAND_RE.search(command):
        return False
    return bool(re.search(
        r"(?:^|\s)(?:\.lazy-harness/bin/lazy|lazy)\s+map\b",
        command,
        re.IGNORECASE,
    ))


def call_has_search_evidence(call: dict[str, Any]) -> bool:
    name = str(call.get("name") or call.get("tool") or "")
    blob = call_blob(call)
    lower = blob.lower()
    if LAZY_FIND_COMMAND_RE.search(blob):
        return False
    if name in SEARCH_EVIDENCE_TOOLS:
        return True
    if name in {"bash", "Bash"} and shell_has_search_evidence(blob):
        return True
    if name in {"subagent", "swarm"} and any(marker in lower for marker in ("searcher", "root-bound search", "do not mutate", "read-only", "search-debt")):
        return True
    return False


def has_search_evidence(packet_row: dict[str, Any] | None = None) -> bool:
    return any(call_has_search_evidence(call) for call in evidence_calls(packet_row))



def load_capabilities() -> list[dict[str, Any]]:
    path = ROOT / ".lazy-harness" / "ssot" / "capabilities.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    capabilities = data.get("capabilities") if isinstance(data, dict) else []
    return [cap for cap in capabilities if isinstance(cap, dict)] if isinstance(capabilities, list) else []


def action_label_matches(label: str, blob: str) -> bool:
    needle = str(label or "").strip().lower()
    haystack = str(blob or "").lower()
    return bool(needle and needle in haystack)


def capability_action_labels(cap: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for key in ("discouragedActions", "preferredActions", "actions"):
        values = cap.get(key)
        if isinstance(values, list):
            labels.extend(str(value) for value in values if str(value or "").strip())
    entrypoint = cap.get("entrypoint")
    if isinstance(entrypoint, str) and entrypoint.strip():
        labels.append(entrypoint.strip())
    return labels


def is_resolve_evidence_for_capability(cap: dict[str, Any], matched_action: str, packet_row: dict[str, Any] | None = None) -> bool:
    cap_id = str(cap.get("id") or "")
    labels = [matched_action, *capability_action_labels(cap)]
    for call in evidence_calls(packet_row):
        blob = call_blob(call).lower()
        if "lazy rules resolve" not in blob and "lazy capability resolve" not in blob:
            continue
        if cap_id and cap_id.lower() in blob:
            return True
        if any(action_label_matches(label, blob) for label in labels):
            return True
    return False


def missed_discouraged_action(packet_row: dict[str, Any] | None = None) -> dict[str, Any] | None:
    capabilities = load_capabilities()
    if not capabilities:
        return None
    calls = evidence_calls(packet_row)
    for cap in capabilities:
        level = str(cap.get("level") or "").strip().lower()
        if level not in {"warn", "block"}:
            continue
        discouraged = cap.get("discouragedActions")
        if not isinstance(discouraged, list) or not discouraged:
            continue
        for call in calls:
            blob = call_blob(call)
            lower = blob.lower()
            # Resolver calls are evidence, not missed actions.
            if "lazy rules resolve" in lower or "lazy capability resolve" in lower:
                continue
            for action in discouraged:
                action_text = str(action or "").strip()
                if not action_label_matches(action_text, blob):
                    continue
                if is_resolve_evidence_for_capability(cap, action_text, packet_row):
                    continue
                return {"capability": cap, "action": action_text, "toolBlob": blob}
    return None


def has_pr_description_rule(entries: list[dict[str, Any]]) -> bool:
    for entry in entries:
        text = f"{entry.get('recordPath','')} {entry.get('title','')}".lower()
        if "pr-description" in text or "pull request description" in text or "pr workflow" in text:
            return True
    return False


def pr_artifact_missing_headings() -> bool:
    for call in recent_calls():
        name = str(call.get("name") or "")
        blob = call_blob(call)
        if name in PR_TOOLS or PR_ARTIFACT_RE.search(blob):
            if not all(pattern.search(blob) for pattern in PR_HEADINGS):
                return True
    return False


def completion_cues_present(blob: str) -> bool:
    lower = blob.lower()
    cues = [
        "user-confirmed", "confirmed", "confirmation:", "record completion",
        "source-of-truth", "source of truth", "ownership", "project rule", "rule placement",
        "regression", "tdd", "contract", "sdd", "bdd", "ssot", "adr",
        "확정", "정정", "소스오브트루스", "규칙", "룰", "결정", "회귀", "계약", "기록",
    ]
    return any(cue in lower for cue in cues)

def mandatory_record_completion_missing(entries: list[dict[str, Any]], blob: str) -> bool:
    if has_lazy_capture():
        return False
    completion_entries = [e for e in entries if str(e.get("recordCompletion") or "").strip()]
    if not completion_entries:
        return False
    if changed_framework_source_without_record():
        return True
    return completion_cues_present(blob) and any(
        marker in " ".join(entry_paths(completion_entries)).lower()
        for marker in ("harness-enforcement-policy", "record-write-update-policy", "project-rule-router", "pre-response-rule-context", "relevant-record-query")
    )


def main() -> int:
    strings: list[str] = []
    walk_strings(PAYLOAD, strings)
    blob = "\n".join(strings)

    row = matching_journal(DIGEST_JOURNAL)
    entries = [e for e in (row or {}).get("entries") or [] if isinstance(e, dict)]
    if entries:
        if has_pr_description_rule(entries) and pr_artifact_missing_headings():
            print("STOP. Response rule audit: surfaced PR description guidance appears to be ignored.\n")
            print("문제: 이번 turn 전에 PR description 관련 record가 surfaced 되었지만, 생성/수정된 PR artifact에서 Why / What / Task 구조를 확인하지 못했습니다.")
            print("\n해야 할 일:")
            print("  A. PR body를 Why / What / Task 구조로 수정하고 다시 실행 (Recommended)")
            print("  B. 이 PR이 예외라면 관련 SSOT/ADR에 예외 사유를 기록")
            print("\nSurfaced records:")
            for path in entry_paths(entries)[:5]:
                print(f"  - {path}")
            return 0

        if mandatory_record_completion_missing(entries, blob):
            print("STOP. Response rule audit: surfaced record-completion guidance may be missing.\n")
            print("문제: 이번 turn 전에 record-completion 의무가 있는 lazy-harness record가 surfaced 되었고, 현재 응답/도구 증거는 새 규칙/정정/계약/하네스 변경을 암시하지만 durable `.lazy-harness` capture가 보이지 않습니다.")
            print("\n해야 할 일:")
            print("  A. 같은 turn에서 적절한 .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning}/ record 또는 knowledge graph를 갱신 (Recommended)")
            print("  B. 이미 기록했다면 recent tool evidence가 누락된 것이므로 해당 record path를 명시")
            print("  C. 기록 대상이 아니면 Rule placement/Discovery capture에서 non-applicable 판단을 명시")
            print("\nSurfaced records:")
            for path in entry_paths(entries)[:5]:
                print(f"  - {path}")
            return 0

    packet_row = matching_journal(PACKET_JOURNAL)
    if packet_row:
        required_paths = packet_required_paths(packet_row)
        try:
            confidence = float(packet_row.get("confidence") or 0)
        except Exception:
            confidence = 0
        if required_paths and confidence >= 0.6 and has_mutation_tool_call(packet_row) and not has_required_read_evidence(required_paths, packet_row):
            print("ADVISORY. Search/read debt audit: required-read evidence may be missing.\n")
            print("문제: 이번 turn에 requiredRead debt가 기록되었고 파일 변경 도구가 사용되었지만, 변경 전 requiredRead 경로를 읽은 증거를 찾지 못했습니다.")
            print("\n해야 할 일:")
            print("  A. 아래 requiredRead 경로를 읽고 변경 근거를 확인 (Recommended)")
            print("  B. 이미 읽었지만 payload evidence가 누락됐다면 응답에 읽은 경로를 명시")
            print("  C. debt row가 부정확했다면 search/read-debt contract와 evidence 기록을 보강")
            print("\nRequired reads:")
            for path in required_paths[:5]:
                print(f"  - {path}")
            return 0
        if packet_has_search_debt(packet_row) and not has_search_evidence(packet_row):
            print("ADVISORY. Search/read debt audit: search evidence may be missing.\n")
            print("문제: 이번 turn에 direct-search debt가 기록되었지만, root-bound search evidence를 찾지 못했습니다.")
            print("\n해야 할 일:")
            print("  A. agentgrep/grep/rg 등으로 .lazy-harness/source/test 검색을 먼저 수행 (Recommended)")
            print("  B. 검색을 이미 했지만 payload evidence가 누락됐다면 검색 쿼리/경로를 명시")
            print("  C. 검색 결과가 모호하면 option gate 또는 searcher subagent handoff로 수렴")
            return 0

    missed = missed_discouraged_action(packet_row)
    if missed:
        cap = missed.get("capability") or {}
        preferred = cap.get("preferredActions") if isinstance(cap, dict) else []
        preferred_list = [str(value) for value in preferred if str(value or "").strip()] if isinstance(preferred, list) else []
        print("ADVISORY. Operating rule audit: discouraged action may have missed project rulebook guidance.\n")
        print("문제: 최근 tool evidence에서 project operating rulebook capability가 discourages 하는 action이 보였지만, 사전 `lazy rules resolve` / `lazy capability resolve` 증거를 찾지 못했습니다.")
        print("\nMatched capability:")
        print(f"  - id: {cap.get('id', '(unknown)')}")
        print(f"  - level: {cap.get('level', '(unknown)')}")
        print(f"  - discouraged action: {missed.get('action')}")
        if preferred_list:
            print("  - preferred actions: " + ", ".join(preferred_list[:5]))
        if cap.get("sourceRecord"):
            print(f"  - sourceRecord: {cap.get('sourceRecord')}")
        if cap.get("rulebookRecord"):
            print(f"  - rulebookRecord: {cap.get('rulebookRecord')}")
        print("\n해야 할 일:")
        print("  A. `lazy rules resolve --action <action>` 또는 `lazy capability resolve --action <action>`로 project rulebook guidance를 확인 (Recommended)")
        print("  B. 예외가 맞다면 관련 rulebook/SSOT/ADR에 bypass 사유를 기록")
        print("  C. capability가 부정확하면 preferredActions/discouragedActions를 수정")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
