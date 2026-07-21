"""Deterministic operating-rule guidance for lifecycle re-grounding hooks.

The turn-start path renders a bounded registry catalog. The source-context path
also renders canonical ``lazy capability resolve`` / ``lazy policy resolve``
matches for exact intents derived from file-tool labels. Neither path classifies
user text or owns policy semantics.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
import subprocess


MAX_ENTRIES = 14
MAX_RESOLVED_ENTRIES = 8
MAX_INTENT_CHARS = 140
MAX_GUIDANCE_CHARS = 260

def _command_timeout_seconds() -> float:
    try:
        return max(0.1, float(os.environ.get("LAZY_HARNESS_CATALOG_TIMEOUT_SECONDS", "3")))
    except (TypeError, ValueError):
        return 3.0


CATALOG_COMMAND_TIMEOUT_SECONDS = _command_timeout_seconds()

HEADER = (
    "- Operating rules/capabilities registered for THIS project (deterministic catalog). "
    "If your task matches an intent below, resolve it FIRST "
    "(`.lazy-harness/bin/lazy capability resolve --intent <intent>` / `lazy rules resolve`) "
    "and follow the stored convention BEFORE acting — do not improvise "
    "(jcode parity: stored project rules surface before action; AGENTS §2.4/§2.5):"
)
RESOLVED_HEADER = (
    "- Resolved source-work guidance for THIS project "
    "(canonical exact-intent policy/capability resolvers; advisory transport, no hook enforcement):"
)


def _run_json(lazy_bin: str, args: list[str], cwd: str) -> dict:
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


def _clean(value: object, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def _catalog_entries_from_payloads(cap: dict, pol: dict) -> list[tuple[str, str, list[str]]]:
    entries: list[tuple[str, str, list[str]]] = []
    seen: set[str] = set()
    for item in cap.get("capabilities") or []:
        cid = str(item.get("id") or "").strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)
        level = str(item.get("level") or "").strip() or "discover"
        intents = [str(x).strip() for x in (item.get("appliesWhen") or []) if str(x).strip()]
        entries.append((cid, level, intents))
    for item in pol.get("policies") or []:
        pid = str(item.get("id") or "").strip()
        if not pid or pid in seen:
            continue
        seen.add(pid)
        level = str(item.get("level") or "").strip() or "discover"
        intents = [str(x).strip() for x in (item.get("appliesTo") or []) if str(x).strip()]
        entries.append((pid, level, intents))
    return entries


def catalog_entries(lazy_bin: str, cwd: str) -> list[tuple[str, str, list[str]]]:
    """Return ``(id, level, intents)`` rows for capabilities then policies."""
    cap = _run_json(lazy_bin, ["capability", "list", "--format=json"], cwd)
    pol = _run_json(lazy_bin, ["policy", "list", "--format=json"], cwd)
    return _catalog_entries_from_payloads(cap, pol)


def _catalog_lines(entries: list[tuple[str, str, list[str]]]) -> list[str]:
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


def catalog_lines(lazy_bin: str, cwd: str) -> list[str]:
    """Return the bounded catalog block, or ``[]`` when registries are unavailable."""
    return _catalog_lines(catalog_entries(lazy_bin, cwd))


def _resolved_lines(intents: list[str], capability_payloads: list[dict], policy_payload: dict) -> list[str]:
    capabilities: dict[str, dict] = {}
    for payload in capability_payloads:
        for item in payload.get("matches") or []:
            cid = str(item.get("id") or "").strip()
            if cid and cid not in capabilities:
                capabilities[cid] = item

    policies: dict[str, dict] = {}
    for item in policy_payload.get("matches") or []:
        pid = str(item.get("id") or "").strip()
        if pid and pid not in policies:
            policies[pid] = item

    if not capabilities and not policies:
        return []

    lines = [RESOLVED_HEADER, "  - exact intents: " + ", ".join(intents)]
    for pid in sorted(policies)[:MAX_RESOLVED_ENTRIES]:
        item = policies[pid]
        level = str(item.get("level") or "discover")
        summary = _clean(item.get("summary") or item.get("title"), MAX_GUIDANCE_CHARS)
        source = _clean(item.get("sourceRecord"), MAX_GUIDANCE_CHARS)
        detail = (" — " + summary) if summary else ""
        source_suffix = ("; source: `" + source + "`") if source else ""
        lines.append(f"  - policy `{pid}` ({level}){detail}{source_suffix}")

    for cid in sorted(capabilities)[:MAX_RESOLVED_ENTRIES]:
        item = capabilities[cid]
        level = str(item.get("level") or "discover")
        actions_value = item.get("actions")
        actions = actions_value if isinstance(actions_value, list) else []
        action_parts = [_clean(action, MAX_GUIDANCE_CHARS) for action in actions]
        guidance = " | ".join(part for part in action_parts if part)
        if not guidance:
            guidance = _clean(item.get("description"), MAX_GUIDANCE_CHARS)
        guidance = _clean(guidance, MAX_GUIDANCE_CHARS)
        source = _clean(item.get("sourceRecord"), MAX_GUIDANCE_CHARS)
        detail = (" — " + guidance) if guidance else ""
        source_suffix = ("; source: `" + source + "`") if source else ""
        lines.append(f"  - capability `{cid}` ({level}){detail}{source_suffix}")
    return lines


def context_guidance_lines(lazy_bin: str, cwd: str, intents: list[str], stage: str = "edit") -> list[str]:
    """Render the catalog plus canonical resolver matches for exact mechanical intents.

    Resolver and catalog commands run concurrently so their shared timeout remains
    bounded by the slowest command rather than accumulating across registries.
    """
    normalized = sorted({str(intent).strip() for intent in intents if str(intent).strip()})
    if not normalized:
        return catalog_lines(lazy_bin, cwd)

    jobs: dict[str, list[str]] = {
        "cap-list": ["capability", "list", "--format=json"],
        "policy-list": ["policy", "list", "--format=json"],
        "policy-resolve": [
            "policy", "resolve", "--stage", stage,
            "--applies-to", ",".join(normalized), "--format=json",
        ],
    }
    for intent in normalized:
        jobs[f"cap-resolve:{intent}"] = ["capability", "resolve", "--intent", intent, "--format=json"]

    with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
        futures = {name: executor.submit(_run_json, lazy_bin, args, cwd) for name, args in jobs.items()}
        payloads = {name: future.result() for name, future in futures.items()}

    entries = _catalog_entries_from_payloads(payloads.get("cap-list", {}), payloads.get("policy-list", {}))
    capability_payloads = [payloads.get(f"cap-resolve:{intent}", {}) for intent in normalized]
    return _catalog_lines(entries) + _resolved_lines(normalized, capability_payloads, payloads.get("policy-resolve", {}))
