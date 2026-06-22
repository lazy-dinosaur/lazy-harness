#!/usr/bin/env python3
"""Audit lazy-harness hard-stop promotion records.

Phase 6 guardrail: a concrete hard stop should not be introduced unless a
canonical record contains a complete `## Hard-stop promotion` section.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SCAN_DIRS = [
    ".lazy-harness/spec",
    ".lazy-harness/ssot",
    ".lazy-harness/decisions",
    ".lazy-harness/tests",
    ".lazy-harness/planning",
]
REQUIRED_FIELDS = [
    "Status",
    "Boundary",
    "Scope",
    "User confirmation",
    "Evidence",
    "Existing softer coverage",
    "Fixture",
    "Narrowness",
    "Rollback",
]
ACTIVE_STATUSES = {"active", "proposed"}
ALLOWED_SCOPES = {"framework-global", "host-project", "team-policy"}
FIELD_RE = re.compile(r"^-\s+([A-Za-z][A-Za-z\s]+):\s*(.*)$")


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for scan in SCAN_DIRS:
        base = root / scan
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            if path.is_file():
                files.append(path)
    return sorted(files)


def extract_sections(text: str) -> list[tuple[int, list[str]]]:
    """Return (start_line, section_lines) for hard-stop sections outside fences."""
    lines = text.splitlines()
    sections: list[tuple[int, list[str]]] = []
    in_fence = False
    current_start: int | None = None
    current: list[str] = []
    for index, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and re.match(r"^##\s+Hard-stop promotion\s*$", line.strip(), re.I):
            if current_start is not None:
                sections.append((current_start, current))
            current_start = index
            current = []
            continue
        if current_start is not None:
            if not in_fence and re.match(r"^##\s+", line.strip()):
                sections.append((current_start, current))
                current_start = None
                current = []
            else:
                current.append(line)
    if current_start is not None:
        sections.append((current_start, current))
    return sections


def parse_fields(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in lines:
        m = FIELD_RE.match(line.strip())
        if not m:
            continue
        key = " ".join(m.group(1).split())
        value = m.group(2).strip()
        fields[key] = value
    return fields


def root_bound_path(root: Path, value: str) -> tuple[Path | None, str | None]:
    """Resolve a fixture path while preserving symlinked host-root boundaries.

    `Path.resolve()` follows a symlinked `.lazy-harness` directory to the
    primary checkout. That is correct for existence checks, but wrong for the
    root-bound guard: a worktree-local `.lazy-harness/foo` path must remain
    valid even when `.lazy-harness` itself is a symlink.
    """
    raw = Path(value)
    if raw.is_absolute():
        return None, f"Fixture escapes root `{value}`"
    if any(part == ".." for part in raw.parts):
        return None, f"Fixture escapes root `{value}`"
    logical_path = root / raw
    try:
        logical_path.absolute().relative_to(root.absolute())
    except ValueError:
        return None, f"Fixture escapes root `{value}`"
    return logical_path, None


def validate_section(root: Path, record: Path, start_line: int, fields: dict[str, str]) -> list[str]:
    problems: list[str] = []
    status = fields.get("Status", "").strip().lower()
    if status and status not in {"active", "proposed", "retired"}:
        problems.append(f"invalid Status `{fields.get('Status')}`")
    if status == "retired":
        # Retired records keep history but do not need active fixture existence.
        return problems
    for field in REQUIRED_FIELDS:
        value = fields.get(field, "").strip()
        if not value or value in {"<todo>", "TODO", "todo", "n/a", "N/A"}:
            problems.append(f"missing {field}")
    scope = fields.get("Scope", "").strip()
    if scope and scope not in ALLOWED_SCOPES:
        problems.append(f"invalid Scope `{scope}`")
    fixture = fields.get("Fixture", "").strip().strip("`")
    if fixture:
        fixture_path, fixture_error = root_bound_path(root, fixture)
        if fixture_error:
            problems.append(fixture_error)
        elif fixture_path is not None and not fixture_path.exists():
            problems.append(f"Fixture does not exist `{fixture}`")
    return problems


def audit(root: Path) -> dict[str, Any]:
    promotions: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for path in iter_markdown_files(root):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for start_line, lines in extract_sections(text):
            fields = parse_fields(lines)
            record = rel(root, path)
            problems = validate_section(root, path, start_line, fields)
            entry = {"recordPath": record, "startLine": start_line, "fields": fields}
            promotions.append(entry)
            if problems:
                violations.append({"recordPath": record, "startLine": start_line, "problems": problems})
    return {
        "ok": not violations,
        "schemaVersion": "1.0",
        "promotions": promotions,
        "violations": violations,
        "summary": {"promotions": len(promotions), "violations": len(violations)},
    }


def render_md(result: dict[str, Any]) -> str:
    lines = ["# Hard-stop promotion audit", ""]
    summary = result["summary"]
    lines.append(f"- Promotions: {summary['promotions']}")
    lines.append(f"- Violations: {summary['violations']}")
    if result["violations"]:
        lines.append("")
        lines.append("## Violations")
        for violation in result["violations"]:
            lines.append(f"- `{violation['recordPath']}:{violation['startLine']}`")
            for problem in violation["problems"]:
                lines.append(f"  - {problem}")
    else:
        lines.append("")
        lines.append("No invalid hard-stop promotions found.")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit hard-stop promotion records")
    parser.add_argument("--root", default=os.environ.get("LAZY_HOST_ROOT") or os.getcwd())
    parser.add_argument("--format", choices=["md", "json"], default="md")
    parser.add_argument("--strict", action="store_true", help="exit nonzero when violations exist")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    result = audit(root)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_md(result), end="")
    if args.strict and result["violations"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
