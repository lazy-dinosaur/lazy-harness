#!/usr/bin/env python3
"""Summarize response.completed hook timing logs.

Read-only Phase 0 performance tool. It never changes hook behavior or logs.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd())
sys.path.insert(0, str(ROOT / ".lazy-harness" / "hooks" / "lifecycle" / "helpers"))
try:
    from runtime_paths import runtime_log_path
except Exception:  # pragma: no cover - summary falls back for transitional hosts
    runtime_log_path = None  # type: ignore[assignment]

if os.environ.get("LAZY_HOOK_TIMING_LOG"):
    DEFAULT_LOG = Path(os.environ["LAZY_HOOK_TIMING_LOG"])
elif runtime_log_path is not None:
    DEFAULT_LOG = runtime_log_path(ROOT, "hook-timings.jsonl")
else:
    DEFAULT_LOG = Path(os.environ.get("LAZY_RUNTIME_ROOT") or (ROOT / ".lazy-harness" / ".runtime")) / "logs" / "hook-timings.jsonl"


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[index]


def read_rows(path: Path, limit: int | None) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    invalid = 0
    if not path.exists():
        return rows, invalid
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if limit and limit > 0:
        lines = lines[-limit:]
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            invalid += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            invalid += 1
    return rows, invalid


def summarize(rows: list[dict[str, Any]], invalid: int) -> dict[str, Any]:
    by_component: dict[str, list[float]] = defaultdict(list)
    emitted: dict[str, int] = defaultdict(int)
    exit_nonzero: dict[str, int] = defaultdict(int)
    for row in rows:
        component = str(row.get("component") or "unknown")
        try:
            duration = float(row.get("durationMs") or 0)
        except Exception:
            duration = 0.0
        by_component[component].append(duration)
        if row.get("outputEmitted") is True:
            emitted[component] += 1
        try:
            if int(row.get("exitCode") or 0) != 0:
                exit_nonzero[component] += 1
        except Exception:
            exit_nonzero[component] += 1
    components = []
    for component, values in sorted(by_component.items(), key=lambda item: (-sum(item[1]), item[0])):
        components.append({
            "component": component,
            "count": len(values),
            "totalMs": round(sum(values), 3),
            "avgMs": round(statistics.mean(values), 3),
            "p50Ms": round(percentile(values, 50), 3),
            "p90Ms": round(percentile(values, 90), 3),
            "p99Ms": round(percentile(values, 99), 3),
            "maxMs": round(max(values), 3),
            "outputEmitted": emitted.get(component, 0),
            "nonZeroExit": exit_nonzero.get(component, 0),
        })
    return {
        "ok": True,
        "mode": "hook-timing-summary",
        "schemaVersion": "1.0",
        "rows": len(rows),
        "invalidRows": invalid,
        "components": components,
        "totalMs": round(sum(item["totalMs"] for item in components), 3),
        "slowest": components[:10],
        "notes": [
            "Read-only timing summary for Phase 0 performance work.",
            "Timing data must not be used to skip gates until conservative fast-path tests exist.",
        ],
    }


def render_md(summary: dict[str, Any], path: Path) -> str:
    lines = ["# Hook timing summary", ""]
    lines.append(f"- Log: `{path}`")
    lines.append(f"- Rows: {summary['rows']}")
    lines.append(f"- Invalid rows: {summary['invalidRows']}")
    lines.append(f"- Total measured ms: {summary['totalMs']}")
    lines.append("")
    lines.append("## Components")
    for item in summary["components"]:
        lines.append(
            f"- `{item['component']}` count={item['count']} totalMs={item['totalMs']} "
            f"avgMs={item['avgMs']} p50={item['p50Ms']} p90={item['p90Ms']} p99={item['p99Ms']} "
            f"max={item['maxMs']} emitted={item['outputEmitted']} nonZero={item['nonZeroExit']}"
        )
    lines.append("")
    lines.append("## Notes")
    for note in summary["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize lazy-harness response.completed hook timing logs")
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="hook timing JSONL path")
    parser.add_argument("--format", choices=["json", "md", "markdown"], default="md")
    parser.add_argument("--limit", type=int, default=0, help="only summarize the last N log lines")
    args = parser.parse_args()
    path = Path(args.log)
    rows, invalid = read_rows(path, args.limit if args.limit > 0 else None)
    summary = summarize(rows, invalid)
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(render_md(summary, path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
