#!/usr/bin/env python3
"""response.completed advisory for Implementation-map STATUS drift.

Turn-scoped backstop (ADR 0041 / 0048 / guidance-ladder L3): when this turn wrote
to a `.lazy-harness/**/*.md` record or touched/removed a source file, check whether
any record's `## Implementation map` `Status:` now disagrees with reality:

- planned-status-files-present  — Status planned/none but a referenced impl file exists.
- verified-status-files-missing — Status verified but a referenced file is gone.

Only records this turn touched (record path or a drifted file path appears in the
turn's tool-call evidence) are surfaced, so unrelated accumulated drift is not re-nagged
every turn; `lazy impl-map` remains the full-corpus manual review.

Deterministic, advisory, fail-open (exit 0), one advisory/turn, no user-text
classification (reads recent_tool_calls tool-arg paths only). Detection logic is reused
from .lazy-harness/scripts/implementation-map-audit.ts (single source).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

sys_path_helper = str(Path(".lazy-harness/hooks/lifecycle/helpers").resolve())
import sys

sys.path.insert(0, sys_path_helper)
try:
    from runtime_paths import runtime_state_path
except Exception:  # pragma: no cover - lifecycle helper must fail open
    runtime_state_path = None  # type: ignore[assignment]

PAYLOAD_RAW = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    PAYLOAD = json.loads(PAYLOAD_RAW or "{}")
except Exception:
    raise SystemExit(0)
if not isinstance(PAYLOAD, dict):
    raise SystemExit(0)

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
ADVISORY_PREFIX = "advisory. implementation-map status drift"

WRITE_TOOLS = {
    "Write", "Edit", "MultiEdit", "write", "edit", "multiedit",
    "Bash", "bash", "shell",
    "mcp__filesystem__write_file", "mcp__filesystem__edit_file", "mcp__filesystem__move_file",
}
CODE_TOKEN_RE = re.compile(r"[\w./@-]+\.(?:ts|tsx|js|jsx|mjs|cjs|py|sh|bash|sql|prisma|rs|go|rb|java|kt|swift|md)\b")


def recent_calls() -> list[dict[str, Any]]:
    calls = PAYLOAD.get("recent_tool_calls") or PAYLOAD.get("recentToolCalls") or []
    return [c for c in calls if isinstance(c, dict)] if isinstance(calls, list) else []


def call_blob(call: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("args_preview", "args", "input", "arguments", "command"):
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


def write_blob() -> str:
    parts: list[str] = []
    for call in recent_calls():
        if str(call.get("name") or "") in WRITE_TOOLS:
            parts.append(call_blob(call))
    return "\n".join(parts)


def echo_guard() -> bool:
    last = str(PAYLOAD.get("last_user_message") or "").lower()
    return last.startswith(ADVISORY_PREFIX)


def run_scan() -> list[dict[str, Any]]:
    script = ROOT / ".lazy-harness" / "scripts" / "implementation-map-audit.ts"
    if not script.exists() or shutil.which("bun") is None:
        return []
    try:
        res = subprocess.run(
            ["bun", str(script), "--root", str(ROOT), "--format=json"],
            cwd=str(ROOT), text=True, capture_output=True, check=False, timeout=20,
        )
        if res.returncode != 0:
            return []
        data = json.loads(res.stdout)
    except Exception:
        return []
    candidates = data.get("driftCandidates") if isinstance(data, dict) else None
    return [c for c in candidates if isinstance(c, dict)] if isinstance(candidates, list) else []


def touched(candidate: dict[str, Any], blob: str) -> bool:
    path = str(candidate.get("path") or "")
    if path and path in blob:
        return True
    for ref in candidate.get("driftFiles") or []:
        ref = str(ref)
        if ref and (ref in blob or os.path.basename(ref) in blob):
            return True
    return False


def gate_already_open_this_turn(fingerprint_seed: str) -> bool:
    message_id = str(PAYLOAD.get("message_id") or "unknown")
    fingerprint = hashlib.sha1(fingerprint_seed.encode("utf-8")).hexdigest()[:16]
    key = f"impl-map-status-drift:{fingerprint}"
    if runtime_state_path is not None:
        state_path = runtime_state_path(ROOT, "open-gates.json", PAYLOAD)
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
    opens[key] = {"first_seen_message_id": message_id,
                  "first_seen_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    state["open_fingerprints"] = opens
    state["last_message_id"] = message_id
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass
    return False


def emit(relevant: list[dict[str, Any]]) -> None:
    print("ADVISORY. Implementation-map status drift: 방금 건드린 record 의 Status 가 현실과 어긋났을 수 있습니다.\n")
    print("문제: 이번 turn 이 건드린 record 의 `## Implementation map` `Status:` 가 파일 존재 현실과 맞지 않습니다.")
    for c in relevant:
        codes = ", ".join(c.get("drift") or [])
        detail = "; ".join(c.get("driftDetail") or [])
        print(f"  - {c.get('path')} [{codes}] — {detail}")
    print("\n해야 할 일:")
    print("  A. 구현이 실제로 됐으면 Status 를 `verified` 로, 파일이 사라졌으면 참조를 정정/`Status` 강등 (Recommended)")
    print("  B. 파일 존재는 heuristic 일 뿐 — 확인 가능한 source 없이는 `verified` 로 올리지 말 것")
    print("  C. 전체 corpus 점검은 `lazy impl-map` 로 (이건 turn-scoped advisory)")
    print("\n규칙: .lazy-harness/spec/platform/implementation-map-standard.md §8.")


def main() -> int:
    if echo_guard():
        return 0
    blob = write_blob()
    if not blob:
        return 0
    if ".lazy-harness/" not in blob and not CODE_TOKEN_RE.search(blob):
        return 0
    relevant = [c for c in run_scan() if touched(c, blob)]
    if not relevant:
        return 0
    seed = json.dumps([c.get("path") for c in relevant], ensure_ascii=False, sort_keys=True)
    if gate_already_open_this_turn(seed):
        return 0
    emit(relevant)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
