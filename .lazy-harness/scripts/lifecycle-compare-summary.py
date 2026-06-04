#!/usr/bin/env python3
"""Summarize response.completed lifecycle compare logs.

Read-only Phase 3 dogfood tool. It reports parity/mismatch classes without
storing raw payloads, user messages, or hook bodies.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
sys.path.insert(0, str(ROOT / ".lazy-harness" / "hooks" / "lifecycle" / "helpers"))
try:
    from runtime_paths import runtime_log_path
except Exception:  # pragma: no cover - transitional hosts can still summarize explicit logs
    runtime_log_path = None  # type: ignore[assignment]

if os.environ.get("LAZY_RESPONSE_COMPLETED_COMPARE_LOG"):
    DEFAULT_LOG = Path(os.environ["LAZY_RESPONSE_COMPLETED_COMPARE_LOG"])
elif runtime_log_path is not None:
    DEFAULT_LOG = runtime_log_path(ROOT, "lifecycle-compare.jsonl")
else:
    DEFAULT_LOG = Path(os.environ.get("LAZY_RUNTIME_ROOT") or (ROOT / ".lazy-harness" / ".runtime")) / "logs" / "lifecycle-compare.jsonl"


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


def read_rows(path: Path, limit: int | None = None) -> tuple[list[dict[str, Any]], int]:
    if not path.exists():
        return [], 0
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if limit and limit > 0:
        lines = lines[-limit:]
    rows: list[dict[str, Any]] = []
    invalid = 0
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


def filter_since(rows: list[dict[str, Any]], since: datetime | None) -> tuple[list[dict[str, Any]], int]:
    if since is None:
        return rows, 0
    filtered: list[dict[str, Any]] = []
    skipped = 0
    for row in rows:
        ts = parse_timestamp(row.get("timestamp"))
        if ts is not None and ts >= since:
            filtered.append(row)
        else:
            skipped += 1
    return filtered, skipped


def mismatch_fields(row: dict[str, Any]) -> list[str]:
    bad: list[str] = []
    if row.get("bodyHashMatch") is not True:
        bad.append("bodyHashMatch")
    if row.get("helperMatch") is not True:
        bad.append("helperMatch")
    if row.get("legacyOutputEmitted") != row.get("orchestratorOutputEmitted"):
        bad.append("outputEmitted")
    if row.get("orchestratorExitCode") not in (0, None):
        bad.append("orchestratorExitCode")
    if row.get("orchestratorSandbox") is not True:
        bad.append("orchestratorSandbox")
    return bad


def _helper(row: dict[str, Any], key: str) -> str:
    return str(row.get(key) or "<none>")


def _num(row: dict[str, Any], key: str) -> int:
    try:
        return int(row.get(key) or 0)
    except Exception:
        return 0


def classify(row: dict[str, Any]) -> str:
    bad = mismatch_fields(row)
    if not bad:
        if row.get("bodyHashMatch") is True and _num(row, "legacyBodyBytes") != _num(row, "orchestratorBodyBytes"):
            if _num(row, "legacyCompareBytes") == _num(row, "orchestratorCompareBytes"):
                return "match-after-normalization:trailing-newline"
        return "match"
    legacy_helper = _helper(row, "legacyHelper")
    orchestrator_helper = _helper(row, "orchestratorHelper")
    legacy_emitted = bool(row.get("legacyOutputEmitted"))
    orchestrator_emitted = bool(row.get("orchestratorOutputEmitted"))
    legacy_bytes = _num(row, "legacyBodyBytes")
    orchestrator_bytes = _num(row, "orchestratorBodyBytes")
    if legacy_emitted and orchestrator_emitted and legacy_helper == orchestrator_helper and abs(legacy_bytes - orchestrator_bytes) == 1:
        return "output-normalization:trailing-newline"
    if legacy_emitted and not orchestrator_emitted and legacy_helper.endswith("check-fix-regression.sh"):
        return "sandbox-fidelity:missing-git-commit-context"
    if legacy_emitted and not orchestrator_emitted and legacy_helper.endswith("check-response-rule-audit.py"):
        return "sandbox-fidelity:missing-runtime-jcode-journals"
    if (not legacy_emitted) and orchestrator_emitted and orchestrator_helper.endswith("check-project-rule-placement.sh"):
        return "sandbox-fidelity:missing-open-gates-state"
    if legacy_emitted != orchestrator_emitted:
        return "presence-mismatch:unclassified"
    if legacy_helper != orchestrator_helper:
        return "helper-mismatch:unclassified"
    return "body-mismatch:unclassified"


def summarize(rows: list[dict[str, Any]], invalid: int, path: Path, *, since: str | None = None, filtered_rows: int = 0, source_rows: int | None = None) -> dict[str, Any]:
    mismatches = [row for row in rows if mismatch_fields(row)]
    field_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    helper_pairs: Counter[str] = Counter()
    failures = 0
    sensitive_like_keys: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, 1):
        cls = classify(row)
        class_counts[cls] += 1
        for field in mismatch_fields(row):
            field_counts[field] += 1
        helper_pairs[f"{_helper(row, 'legacyHelper')} -> {_helper(row, 'orchestratorHelper')}"] += 1
        if row.get("orchestratorExitCode") not in (0, None):
            failures += 1
        for key in row:
            if str(key).lower() in {"body", "payload", "message", "content", "raw", "legacybody", "orchestratorbody"}:
                sensitive_like_keys.append({"row": idx, "key": key})
        if mismatch_fields(row) and len(samples) < 10:
            samples.append({
                "row": idx,
                "timestamp": row.get("timestamp"),
                "bad": mismatch_fields(row),
                "class": cls,
                "legacyHelper": row.get("legacyHelper"),
                "orchestratorHelper": row.get("orchestratorHelper"),
                "legacyOutputEmitted": row.get("legacyOutputEmitted"),
                "orchestratorOutputEmitted": row.get("orchestratorOutputEmitted"),
                "legacyBodyBytes": row.get("legacyBodyBytes"),
                "orchestratorBodyBytes": row.get("orchestratorBodyBytes"),
                "legacyCompareBytes": row.get("legacyCompareBytes"),
                "orchestratorCompareBytes": row.get("orchestratorCompareBytes"),
            })
    return {
        "ok": invalid == 0 and len(mismatches) == 0 and not sensitive_like_keys,
        "mode": "lifecycle-compare-summary",
        "schemaVersion": "1.0",
        "log": str(path),
        "rows": len(rows),
        "sourceRows": source_rows if source_rows is not None else len(rows),
        "filteredRows": filtered_rows,
        "since": since,
        "invalidRows": invalid,
        "mismatches": len(mismatches),
        "failures": failures,
        "firstTimestamp": rows[0].get("timestamp") if rows else None,
        "lastTimestamp": rows[-1].get("timestamp") if rows else None,
        "fieldCounts": dict(field_counts),
        "classCounts": dict(class_counts),
        "helperPairs": dict(helper_pairs.most_common(20)),
        "sensitiveLikeKeys": sensitive_like_keys[:20],
        "samples": samples,
        "notes": [
            "Read-only summary for response.completed compare-mode dogfood.",
            "Rows contain hashes/lengths/helper names only; raw hook bodies must not appear.",
            "Production orchestrator replacement still requires explicit approval and zero mismatch readiness.",
        ],
    }


def render_md(summary: dict[str, Any]) -> str:
    lines = ["# Lifecycle compare summary", ""]
    lines.append(f"- Log: `{summary['log']}`")
    lines.append(f"- Rows: {summary['rows']}")
    if summary.get("since"):
        lines.append(f"- Since: `{summary['since']}`")
        lines.append(f"- Source rows before filter: {summary.get('sourceRows')}")
        lines.append(f"- Filtered out rows: {summary.get('filteredRows')}")
    lines.append(f"- Invalid rows: {summary['invalidRows']}")
    lines.append(f"- Mismatches: {summary['mismatches']}")
    lines.append(f"- Failures: {summary['failures']}")
    lines.append(f"- First: {summary.get('firstTimestamp')}")
    lines.append(f"- Last: {summary.get('lastTimestamp')}")
    lines.append(f"- Sensitive-like raw keys: {len(summary.get('sensitiveLikeKeys') or [])}")
    lines.append("")
    lines.append("## Mismatch fields")
    if summary["fieldCounts"]:
        for key, value in summary["fieldCounts"].items():
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Classes")
    for key, value in summary["classCounts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    lines.append("## Top helper pairs")
    for key, value in summary["helperPairs"].items():
        lines.append(f"- `{key}`: {value}")
    if summary["samples"]:
        lines.append("")
        lines.append("## Mismatch samples")
        for sample in summary["samples"]:
            lines.append(f"- row={sample['row']} class=`{sample['class']}` bad={sample['bad']} legacy=`{sample.get('legacyHelper')}` orchestrator=`{sample.get('orchestratorHelper')}` bytes={sample.get('legacyBodyBytes')}->{sample.get('orchestratorBodyBytes')}")
    lines.append("")
    lines.append("## Notes")
    for note in summary["notes"]:
        lines.append(f"- {note}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize lazy-harness response.completed lifecycle compare logs")
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="lifecycle compare JSONL path")
    parser.add_argument("--format", choices=["json", "md", "markdown"], default="md")
    parser.add_argument("--limit", type=int, default=0, help="only summarize the last N log lines")
    parser.add_argument("--since", default="", help="only summarize rows whose timestamp is at or after this ISO-8601 instant")
    parser.add_argument("--fail-on-mismatch", action="store_true", help="exit 2 when invalid rows, mismatches, failures, or raw-key privacy issues exist")
    args = parser.parse_args()
    path = Path(args.log)
    since_dt = parse_timestamp(args.since) if args.since else None
    if args.since and since_dt is None:
        parser.error("--since must be an ISO-8601 timestamp, e.g. 2026-06-04T10:06:00Z")
    rows, invalid = read_rows(path, args.limit if args.limit > 0 else None)
    source_rows = len(rows)
    rows, filtered_rows = filter_since(rows, since_dt)
    summary = summarize(rows, invalid, path, since=args.since or None, filtered_rows=filtered_rows, source_rows=source_rows)
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(render_md(summary))
    if args.fail_on_mismatch and not summary["ok"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
