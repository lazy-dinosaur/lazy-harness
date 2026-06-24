#!/usr/bin/env python3
"""response.completed advisory for operating-rule STORAGE correctness.

This helper closes a gap that check-project-rule-placement.sh does not cover:
that gate only guards `.jcode`/Jcode-memory over-routing and treats ANY write to
`.lazy-harness/<layer>` as satisfying placement. It cannot tell that operating-rule
semantics were written to a wrong/non-canonical surface inside `.lazy-harness`, nor
that an existing rule was duplicated because the agent did not resolve first.

Canonical store for operating-rule behavior semantics is
`.lazy-harness/ssot/policies.json` (+ `.lazy-harness/ssot/capabilities.json` for
action binding). `.lazy-harness/rules/**` is a compatibility/explain surface
(ADR 0046). See `.lazy-harness/ssot/rule-sources.md` and
`.lazy-harness/planning/operating-rule-storage-apply-repair-20260624.md`.

Posture (ADR 0041): advisory only, exit 0, fail-open, deterministic cue/label
matching of ASSISTANT/tool-arg evidence (not raw user-text semantic classification).
No hard gate. One advisory per turn, deduped via open-gates.json.
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

sys.path.insert(0, str(Path(".lazy-harness/hooks/lifecycle/helpers").resolve()))
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

WRITE_TOOLS = {
    "Write", "Edit", "MultiEdit", "write", "edit", "multiedit",
    "mcp__filesystem__write_file", "mcp__filesystem__edit_file",
}

# Operating-rule stores: writing here without resolving first risks duplication.
RULE_STORE_RE = re.compile(
    r"\.lazy-harness/(?:ssot/(?:capabilities|policies)\.json|rules/[^\s\"'`,)}]+\.md)"
)
# Non-canonical SSOT markdown target (filename captured for the meta allowlist).
SSOT_MD_RE = re.compile(r"\.lazy-harness/ssot/([^\s\"'`,)}/]+\.md)")

# SSOT markdown records that legitimately describe/route rules (not a wrong surface).
META_SSOT = {
    "rule-sources.md", "rule-lifecycle.md", "capability-registry.md",
    "policy-registry.md", "project-identity.md", "harness-enforcement-policy.md",
    "cli-tool-boundary.md", "implementation-map-storage.md", "gate-fingerprint-state.md",
}

# Strong operating-rule AUTHORING cues: command steering / level / bypass / PR body.
AUTHORING_CUES = [
    "preferredactions", "discouragedactions", "requiresreasonforbypass",
    "preferred command", "discouraged command", "canonical command",
    "preferred action", "discouraged action", "discouraged raw",
    "level: warn", "level: block", "level:warn", "level:block",
    "mandatory section", "pr body", "pr description", "pull request body",
    "운영 규칙", "운영규칙", "canonical worktree", "raw dev-server", "bypass rule",
]
WORKFLOW_GATE_RE = re.compile(
    r"(?:must|always|반드시|항상).{0,40}(?:before|전에).{0,40}"
    r"(?:commit|push|merge|yield|pr|pull request|mutation|release|배포)",
    re.IGNORECASE | re.DOTALL,
)
RESOLVE_EVIDENCE = ("lazy policy resolve", "lazy capability resolve", "lazy rules resolve")


def recent_calls() -> list[dict[str, Any]]:
    calls = PAYLOAD.get("recent_tool_calls") or PAYLOAD.get("recentToolCalls") or []
    return [c for c in calls if isinstance(c, dict)] if isinstance(calls, list) else []


def call_blob(call: dict[str, Any]) -> str:
    parts: list[str] = []
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


def has_resolve_evidence() -> bool:
    for call in recent_calls():
        blob = call_blob(call).lower()
        if any(marker in blob for marker in RESOLVE_EVIDENCE):
            return True
    return False


def rule_store_write() -> str | None:
    for call in recent_calls():
        if str(call.get("name") or "") not in WRITE_TOOLS:
            continue
        match = RULE_STORE_RE.search(call_blob(call))
        if match:
            return match.group(0)
    return None


def wrong_surface_write() -> str | None:
    for call in recent_calls():
        if str(call.get("name") or "") not in WRITE_TOOLS:
            continue
        blob = call_blob(call)
        match = SSOT_MD_RE.search(blob)
        if not match or match.group(1) in META_SSOT:
            continue
        lower = blob.lower()
        if any(cue in lower for cue in AUTHORING_CUES) or WORKFLOW_GATE_RE.search(blob):
            return match.group(0)
    return None


def echo_guard() -> bool:
    last = str(PAYLOAD.get("last_user_message") or "").lower()
    return last.startswith("advisory. operating rule storage")


def gate_already_open_this_turn(branch: str) -> bool:
    message_id = str(PAYLOAD.get("message_id") or "unknown")
    recent = [{"name": str(c.get("name", "")), "blob": call_blob(c)} for c in recent_calls()]
    fp_input = json.dumps(
        {"branch": branch, "recent_tool_calls": recent,
         "last_user_message": PAYLOAD.get("last_user_message") or ""},
        ensure_ascii=False, sort_keys=True,
    )
    fingerprint = hashlib.sha1(fp_input.encode("utf-8")).hexdigest()[:16]
    key = f"operating-rule-storage:{fingerprint}"
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


def emit_dedup(target: str) -> None:
    print("ADVISORY. Operating rule storage: 기존 규칙 확인 없이 운영 규칙을 추가했을 수 있습니다.\n")
    print("문제: 이번 turn에서 operating-rule store에 쓰기가 보였지만, 사전 `lazy policy resolve` / "
          "`lazy capability resolve` / `lazy rules resolve` 증거를 찾지 못했습니다. 기존 규칙을 먼저 "
          "찾지 않으면 중복 규칙이 생깁니다.")
    print(f"\nWrite target: {target}")
    print("\n해야 할 일:")
    print("  A. `lazy policy resolve` / `lazy capability resolve`로 같은 intent/action의 기존 규칙을 먼저 확인 (Recommended)")
    print("  B. 신규 규칙이 맞다면 canonical store에 기록: 의미는 .lazy-harness/ssot/policies.json, "
          "action 바인딩은 .lazy-harness/ssot/capabilities.json (rules/**는 compat/explain)")
    print("  C. 이미 resolve했지만 evidence가 누락됐다면 응답에 resolve 명령을 명시")


def emit_wrong_surface(target: str) -> None:
    print("ADVISORY. Operating rule storage: 운영 규칙을 non-canonical surface에 기록했을 수 있습니다.\n")
    print("문제: 운영 규칙(명령 선호/지양, warn/block, 'mutation/PR 전 필수 단계' 등) 의미가 "
          f"`{target}` 같은 일반 SSOT markdown에 prose로 보입니다. 운영 규칙의 canonical store는 "
          "typed policy입니다.")
    print("\n해야 할 일:")
    print("  A. 규칙 의미는 .lazy-harness/ssot/policies.json (typed policy), action 바인딩은 "
          ".lazy-harness/ssot/capabilities.json에 기록 (Recommended)")
    print("  B. 사람이 읽는 설명은 .lazy-harness/rules/**(compatibility/explain surface)에 둠")
    print("  C. 이게 운영 규칙이 아니라 프로젝트 사실이면 적절한 DDD/SDD/BDD/TDD/SSOT record로 두고 무시")
    print("\n규칙: .lazy-harness/ssot/rule-sources.md + ADR 0046 (policies.json canonical).")


def main() -> int:
    if echo_guard():
        return 0
    if not recent_calls():
        return 0

    store_target = rule_store_write()
    if store_target and not has_resolve_evidence():
        if gate_already_open_this_turn("dedup"):
            return 0
        emit_dedup(store_target)
        return 0

    surface_target = wrong_surface_write()
    if surface_target:
        if gate_already_open_this_turn("wrong-surface"):
            return 0
        emit_wrong_surface(surface_target)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
