#!/usr/bin/env python3
"""Enforce promoted typed-agent routes from the host policy registry.

Only structured spawn metadata is inspected. The helper stays silent unless the
host has an active ``level=block`` policy with ``runtime.mode`` set to
``typed-agent-routing`` and ``runtime.blocks=true``. Demoting or disabling the
policy therefore rolls the runtime block back without changing this helper.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any


def parse_payload() -> dict[str, Any]:
    raw = sys.argv[1] if len(sys.argv) > 1 else ""
    if not raw.strip():
        try:
            raw = sys.stdin.read()
        except Exception:
            raw = ""
    try:
        value = json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def host_root(payload: dict[str, Any]) -> Path | None:
    for candidate in (
        payload.get("working_dir"),
        payload.get("cwd"),
        os.environ.get("LAZY_HOST_ROOT"),
        os.getcwd(),
    ):
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        root = Path(candidate).expanduser().resolve()
        if (root / ".lazy-harness" / "ssot" / "policies.json").is_file():
            return root
    return None


def load_routes(root: Path) -> tuple[str, dict[str, dict[str, str]]] | None:
    try:
        registry = json.loads((root / ".lazy-harness" / "ssot" / "policies.json").read_text(encoding="utf-8"))
    except Exception:
        return None
    policies = registry.get("policies") if isinstance(registry, dict) else None
    if not isinstance(policies, list):
        return None
    for policy in policies:
        if not isinstance(policy, dict) or policy.get("level") != "block":
            continue
        runtime = policy.get("runtime")
        if not isinstance(runtime, dict) or runtime.get("blocks") is not True or runtime.get("mode") != "typed-agent-routing":
            continue
        configured = runtime.get("typedAgentRouting")
        if not isinstance(configured, dict):
            continue
        routes: dict[str, dict[str, str]] = {}
        for role, value in configured.items():
            if not isinstance(role, str) or not isinstance(value, dict):
                continue
            label = str(value.get("labelPrefix") or "").strip().lower()
            model = normalized_model(value.get("model"))
            effort = str(value.get("effort") or "").strip().lower()
            if label and model and effort:
                routes[role] = {"label": label, "model": model, "effort": effort}
        if routes:
            return str(policy.get("id") or "typed-agent-routing"), routes
    return None


def normalized_model(value: object) -> str:
    raw = str(value or "").strip().lower()
    if ":" in raw:
        raw = raw.rsplit(":", 1)[-1]
    if "/" in raw:
        raw = raw.rsplit("/", 1)[-1]
    return raw


def main() -> None:
    payload = parse_payload()
    tool = payload.get("tool")
    if not isinstance(tool, dict):
        return
    tool_name = str(tool.get("name") or "").strip().lower().rsplit(".", 1)[-1]
    if tool_name != "swarm":
        return
    args = tool.get("args")
    if not isinstance(args, dict) or str(args.get("action") or "").lower() != "spawn":
        return

    root = host_root(payload)
    configured = load_routes(root) if root is not None else None
    if configured is None:
        return
    policy_id, routes = configured
    label = str(args.get("label") or "").strip().lower()
    selected: tuple[str, dict[str, str]] | None = None
    for role, route in routes.items():
        if label.startswith(route["label"]):
            selected = role, route
            break
    if selected is None:
        return

    role, route = selected
    model = normalized_model(args.get("model"))
    effort = str(args.get("effort") or "").strip().lower()
    if model == route["model"] and effort == route["effort"]:
        return
    print(
        f"[{policy_id}] Typed {role} routing requires model={route['model']} and effort={route['effort']}. "
        f"Received model={model or 'unset'}, effort={effort or 'unset'}."
    )


if __name__ == "__main__":
    main()
