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
from pathlib import Path
from typing import Any

PAYLOAD_RAW = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    PAYLOAD = json.loads(PAYLOAD_RAW or "{}")
except Exception:
    PAYLOAD = {}
if not isinstance(PAYLOAD, dict):
    raise SystemExit(0)

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
DIGEST_JOURNAL = ROOT / ".lazy-harness" / "state" / "surfaced-rule-digests.jsonl"
PACKET_JOURNAL = ROOT / ".lazy-harness" / "state" / "context-delivery-packets.jsonl"
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
CAPTURE_RE = re.compile(
    r"\.lazy-harness/(?:(?:domain|spec|behavior|tests|decisions|ssot|planning|plans)/[^\s\"'`,)}]+|knowledge/(?:candidates|graph|graph-drafts|corrections)\.jsonl|logs/corrections\.jsonl)"
)
FRAMEWORK_SOURCE_RE = re.compile(r"\.lazy-harness/(?:hooks|scripts|bin|schemas|manifests|AGENTS\.md|spec/platform/)\S*")
PR_ARTIFACT_RE = re.compile(r"\b(?:pull request|PR|gh\s+pr\s+(?:create|edit)|create_pull_request|update_pull_request)\b", re.IGNORECASE)
PR_HEADINGS = [re.compile(r"(?im)^\s*(?:#+\s*)?%s\s*:" % h) for h in ("Why", "What", "Task")]


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


def recent_calls() -> list[dict[str, Any]]:
    calls = PAYLOAD.get("recent_tool_calls") or PAYLOAD.get("recentToolCalls") or []
    return [c for c in calls if isinstance(c, dict)] if isinstance(calls, list) else []


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

    if msg_hash:
        for row in reversed(rows):
            if fresh(row) and row.get("messageIdHash") == msg_hash:
                return row
    if session_hash:
        for row in reversed(rows):
            if fresh(row) and row.get("sessionIdHash") == session_hash:
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


def has_mutation_tool_call() -> bool:
    for call in recent_calls():
        if str(call.get("name") or "") in WRITE_TOOLS:
            return True
    return False


def has_required_read_evidence(required_paths: list[str]) -> bool:
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
    for call in recent_calls():
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
        if required_paths and confidence >= 0.6 and has_mutation_tool_call() and not has_required_read_evidence(required_paths):
            print("ADVISORY. Context Delivery audit: required-read evidence may be missing.\n")
            print("문제: 이번 turn에 Context Delivery Packet requiredRead가 기록되었고 파일 변경 도구가 사용되었지만, 변경 전 requiredRead 경로를 읽은 증거를 찾지 못했습니다.")
            print("\n해야 할 일:")
            print("  A. 아래 requiredRead 경로를 읽고 변경 근거를 확인 (Recommended)")
            print("  B. 이미 읽었지만 payload evidence가 누락됐다면 응답에 읽은 경로를 명시")
            print("  C. packet이 부정확했다면 Context Delivery index/query 기록을 보강")
            print("\nRequired reads:")
            for path in required_paths[:5]:
                print(f"  - {path}")
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
