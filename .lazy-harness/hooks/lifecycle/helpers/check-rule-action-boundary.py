#!/usr/bin/env python3
"""Legacy action-boundary compatibility shim (no-op).

Phase 5 migrated project/team policy away from concrete tool branches, and ADR 0050
removed the jcode runtime. This helper intentionally emits no policy output; it is
kept as a no-op so the response.completed helper chain and historical references
stay valid. PR/runtime/release guidance is handled by:

    message.received direct-search prompt/debt journal
    + response.completed response-rule-audit backstop

Destructive shell safety is now runtime-agnostic in check-destructive-command.py
(chained first in on-tool-execute-before.sh for Pi/OMP tool_call).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()


def parse_payload(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw or "{}")
    except Exception:
        return {"raw": raw}
    return data if isinstance(data, dict) else {"raw": raw}


def main() -> int:
    # Compatibility only. Parse enough to prove the helper tolerates existing
    # Jcode payloads, but do not enforce project policy on a tool-specific path.
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    _payload = parse_payload(raw)
    _ = ROOT
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
