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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd())
sys.path.insert(0, str(ROOT / ".lazy-harness" / "hooks" / "lifecycle" / "helpers"))
try:
    from runtime_paths import runtime_log_path, worktree_git_dir
except Exception:  # pragma: no cover - summary falls back for transitional hosts
    runtime_log_path = None  # type: ignore[assignment]
    worktree_git_dir = None  # type: ignore[assignment]

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


def parse_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def read_rows(path: Path) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    invalid = 0
    if not path.exists():
        return rows, invalid
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            invalid += 1
            continue
        if isinstance(row, dict):
            row = dict(row)
            row.setdefault("sourceLog", str(path))
            rows.append(row)
        else:
            invalid += 1
    return rows, invalid


def filter_and_limit_rows(rows: list[dict[str, Any]], since: datetime | None, limit: int | None) -> tuple[list[dict[str, Any]], int]:
    filtered: list[dict[str, Any]] = []
    skipped = 0
    for row in rows:
        if since is None:
            filtered.append(row)
            continue
        ts = parse_timestamp(row.get("ts") or row.get("timestamp"))
        if ts is not None and ts >= since:
            filtered.append(row)
        else:
            skipped += 1
    filtered.sort(key=lambda row: (parse_timestamp(row.get("ts") or row.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc), str(row.get("sourceLog") or "")))
    if limit and limit > 0:
        filtered = filtered[-limit:]
    return filtered, skipped


def unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for path in paths:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def session_timing_logs(root: Path, explicit_log: Path) -> list[Path]:
    paths = [explicit_log]
    legacy = root / ".lazy-harness" / "logs" / "hook-timings.jsonl"
    paths.append(legacy)
    runtime_base = None
    if worktree_git_dir is not None:
        try:
            runtime_base = worktree_git_dir(root) / "lazy-harness" / "runtime"
        except Exception:
            runtime_base = None
    if runtime_base is None:
        runtime_base = root / ".git" / "lazy-harness" / "runtime"
    if runtime_base.exists():
        paths.extend(sorted(runtime_base.glob("*/logs/hook-timings.jsonl")))
    if os.environ.get("LAZY_RUNTIME_ROOT"):
        paths.append(Path(os.environ["LAZY_RUNTIME_ROOT"]) / "logs" / "hook-timings.jsonl")
    return unique_paths(paths)


def read_rows_many(paths: list[Path]) -> tuple[list[dict[str, Any]], int, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    invalid = 0
    sources: list[dict[str, Any]] = []
    for path in paths:
        path_rows, path_invalid = read_rows(path)
        rows.extend(path_rows)
        invalid += path_invalid
        sources.append({"path": str(path), "exists": path.exists(), "rows": len(path_rows), "invalidRows": path_invalid})
    return rows, invalid, sources


def summarize(rows: list[dict[str, Any]], invalid: int, *, sources: list[dict[str, Any]] | None = None, since: str | None = None, filtered_rows: int = 0, source_rows: int | None = None, all_sessions: bool = False) -> dict[str, Any]:
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
    timestamps = [str(row.get("ts") or row.get("timestamp")) for row in rows if row.get("ts") or row.get("timestamp")]
    return {
        "ok": True,
        "mode": "hook-timing-summary",
        "schemaVersion": "1.1",
        "rows": len(rows),
        "sourceRows": source_rows if source_rows is not None else len(rows),
        "filteredRows": filtered_rows,
        "since": since,
        "allSessions": all_sessions,
        "logCount": len(sources or []),
        "logs": sources or [],
        "firstTimestamp": min(timestamps) if timestamps else None,
        "lastTimestamp": max(timestamps) if timestamps else None,
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
    if summary.get("allSessions"):
        lines.append(f"- Logs aggregated: {summary.get('logCount', 0)}")
    else:
        lines.append(f"- Log: `{path}`")
    lines.append(f"- Rows: {summary['rows']}")
    if summary.get("since"):
        lines.append(f"- Since: `{summary['since']}`")
        lines.append(f"- Source rows before filter: {summary.get('sourceRows')}")
        lines.append(f"- Filtered out rows: {summary.get('filteredRows')}")
    if summary.get("firstTimestamp") or summary.get("lastTimestamp"):
        lines.append(f"- First: {summary.get('firstTimestamp')}")
        lines.append(f"- Last: {summary.get('lastTimestamp')}")
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
    parser.add_argument("--limit", type=int, default=0, help="only summarize the last N rows after filtering")
    parser.add_argument("--since", default="", help="only summarize rows whose ts/timestamp is at or after this ISO-8601 instant")
    parser.add_argument("--all-sessions", action="store_true", help="aggregate hook-timings.jsonl from all session runtime roots plus the selected log")
    args = parser.parse_args()
    path = Path(args.log)
    since_dt = parse_timestamp(args.since) if args.since else None
    if args.since and since_dt is None:
        parser.error("--since must be an ISO-8601 timestamp, e.g. 2026-06-04T10:06:00Z")
    paths = session_timing_logs(ROOT, path) if args.all_sessions else [path]
    rows, invalid, sources = read_rows_many(paths)
    source_rows = len(rows)
    rows, filtered_rows = filter_and_limit_rows(rows, since_dt, args.limit if args.limit > 0 else None)
    summary = summarize(rows, invalid, sources=sources, since=args.since or None, filtered_rows=filtered_rows, source_rows=source_rows, all_sessions=args.all_sessions)
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(render_md(summary, path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
