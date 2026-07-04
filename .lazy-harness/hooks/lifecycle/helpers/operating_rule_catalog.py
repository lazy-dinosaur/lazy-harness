"""Deterministic operating-rule/capability catalog for lifecycle re-grounding hooks.

R3 (ADR 0048, 2026-06-28 amendment): the turn-start hook (on-message-received.sh)
and the mid-turn re-grounding hook (on-context.sh) both surface the registered
operating rules/capabilities so stored project rules are visible before action
(jcode full-grammar parity).

This is a deterministic enumeration of the registry (`lazy capability list` +
`lazy policy list`). It does NOT classify user text and is NOT a `lazy find
--purpose` query backend (ADR 0041 / ADR 0048 Must-not); the agent matches the
intent itself. Single source of the catalog format for both hooks.
"""
from __future__ import annotations

import json
import os
import subprocess

MAX_ENTRIES = 14
MAX_INTENT_CHARS = 140
CATALOG_COMMAND_TIMEOUT_SECONDS = float(os.environ.get("LAZY_HARNESS_CATALOG_TIMEOUT_SECONDS", "3"))

HEADER = (
    "- Operating rules/capabilities registered for THIS project (deterministic catalog). "
    "If your task matches an intent below, resolve it FIRST "
    "(`.lazy-harness/bin/lazy capability resolve --intent <intent>` / `lazy rules resolve`) "
    "and follow the stored convention BEFORE acting \u2014 do not improvise "
    "(jcode parity: stored project rules surface before action; AGENTS \u00a72.4/\u00a72.5):"
)


def _run_json(lazy_bin: str, args: list, cwd: str) -> dict:
    try:
        result = subprocess.run(
            [lazy_bin] + list(args),
            capture_output=True,
            text=True,
            timeout=CATALOG_COMMAND_TIMEOUT_SECONDS,
            cwd=cwd,
        )
        data = json.loads(result.stdout or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def catalog_entries(lazy_bin: str, cwd: str) -> list:
    """Return [(id, level, [intents])] for registered capabilities then policies, deduped by id."""
    entries: list = []
    seen: set = set()
    cap = _run_json(lazy_bin, ["capability", "list", "--format=json"], cwd)
    for item in (cap.get("capabilities") or []):
        cid = str(item.get("id") or "").strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)
        level = str(item.get("level") or "").strip() or "discover"
        intents = [str(x).strip() for x in (item.get("appliesWhen") or []) if str(x).strip()]
        entries.append((cid, level, intents))
    pol = _run_json(lazy_bin, ["policy", "list", "--format=json"], cwd)
    for item in (pol.get("policies") or []):
        pid = str(item.get("id") or "").strip()
        if not pid or pid in seen:
            continue
        seen.add(pid)
        level = str(item.get("level") or "").strip() or "discover"
        intents = [str(x).strip() for x in (item.get("appliesTo") or []) if str(x).strip()]
        entries.append((pid, level, intents))
    return entries


def catalog_lines(lazy_bin: str, cwd: str) -> list:
    """Return the catalog block (header + entry lines), or [] when nothing is registered."""
    entries = catalog_entries(lazy_bin, cwd)
    if not entries:
        return []
    lines = [HEADER]
    for cid, level, intents in entries[:MAX_ENTRIES]:
        intent_text = ", ".join(intents)
        if len(intent_text) > MAX_INTENT_CHARS:
            intent_text = intent_text[: MAX_INTENT_CHARS - 3] + "..."
        suffix = (": " + intent_text) if intent_text else ""
        lines.append("  - `%s` (%s)%s" % (cid, level, suffix))
    return lines
