#!/usr/bin/env bash
# Capture transport only: the Pi adapter owns structural receipts; the LLM owns
# necessity/relevance. Never scan raw user/assistant/tool prose for semantic STOP.
set -euo pipefail
PAYLOAD_JSON="${1:-}" python3 <<'PY'
import json
import os

unverified = {
    "status": "unverified",
    "reason": "capture judgement/evidence unavailable; missing packet is not no-record",
    "semanticStatus": "llm-judgement-not-verified",
    "approvalStatus": "not-evaluated",
}
try:
    payload = json.loads(os.environ["PAYLOAD_JSON"] or "{}")
    capture = payload.get("capture_validation") if isinstance(payload, dict) else None
    valid = (
        isinstance(capture, dict)
        and payload.get("source") == "lazy-harness"
        and capture.get("schemaVersion") == "1.0"
        and isinstance(payload.get("working_dir"), str)
        and capture.get("root") == payload["working_dir"]
        and isinstance(capture.get("epoch"), int)
        and capture.get("status") in {"unverified", "pending", "no-record-asserted", "evidence-linked"}
        and isinstance(capture.get("reason"), str)
        and capture.get("semanticStatus") == "llm-judgement-not-verified"
        and capture.get("approvalStatus") == "not-evaluated"
    )
    print(json.dumps(capture if valid else unverified, ensure_ascii=False))
except (ValueError, TypeError):
    print(json.dumps(unverified))
PY
