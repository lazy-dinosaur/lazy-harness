#!/usr/bin/env python3
"""Conservative graph cleanup planner.

Default mode is dry-run. Apply mode rewrites graph.jsonl only after writing a
backup beside the graph. The cleanup preserves rows: it adds missing ids,
renames duplicate ids, and moves paths that exist in neither host nor canonical
source into `stalePaths` so graph-hygiene no longer points agents at dead files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
from dataclasses import asdict, dataclass, field
from typing import Any

ROOT = pathlib.Path(os.environ.get("LAZY_HOST_ROOT", pathlib.Path(__file__).resolve().parents[2])).resolve()
LAZY = ROOT / ".lazy-harness"
PATH_KEYS = ("path", "file", "sourcePath", "targetPath")


@dataclass
class Operation:
    code: str
    line: int
    before: dict[str, Any]
    after: dict[str, Any]
    reason: str


@dataclass
class CleanupResult:
    ok: bool
    mode: str
    root: str
    graphPath: str
    source: str | None
    dryRun: bool
    backupPath: str | None
    summary: dict[str, int]
    operations: list[Operation] = field(default_factory=list)
    unsupported: list[dict[str, Any]] = field(default_factory=list)


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_hash(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


def lazy_dir(path: pathlib.Path) -> pathlib.Path:
    return path if path.name == ".lazy-harness" else path / ".lazy-harness"


def default_source(root: pathlib.Path) -> pathlib.Path | None:
    for candidate in [os.environ.get("LAZY_FRAMEWORK_SOURCE"), os.environ.get("LAZY_SOURCE_ROOT"), str(pathlib.Path.home() / "dev" / "lazy-harness")]:
        if not candidate:
            continue
        lazy = lazy_dir(pathlib.Path(candidate).resolve())
        if lazy.exists() and lazy != root / ".lazy-harness":
            return lazy
    return None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or apply conservative graph.jsonl cleanup.")
    parser.add_argument("--root", "--host", dest="root", default=str(ROOT))
    parser.add_argument("--graph", default=None)
    parser.add_argument("--source", default=None, help="Canonical lazy-harness source root or .lazy-harness directory.")
    parser.add_argument("--apply", action="store_true", help="Rewrite graph.jsonl after creating a backup. Omit for dry-run.")
    parser.add_argument("--format", choices=["json", "md"], default="md")
    return parser.parse_args(argv)


def path_exists(root: pathlib.Path, source: pathlib.Path | None, rel: str) -> tuple[bool, bool]:
    host_exists = (root / rel).exists()
    source_exists = False
    if source and rel.startswith(".lazy-harness/"):
        source_exists = (source / rel[len(".lazy-harness/"):]).exists()
    return host_exists, source_exists


def stale_paths_for_value(root: pathlib.Path, source: pathlib.Path | None, field_name: str, value: Any) -> tuple[Any, list[dict[str, str]], bool]:
    stale: list[dict[str, str]] = []
    changed = False
    if isinstance(value, str):
        if value.startswith(".lazy-harness/"):
            host_exists, source_exists = path_exists(root, source, value)
            if not host_exists and not source_exists:
                stale.append({"field": field_name, "path": value, "reason": "missing-in-host-and-source"})
                return None, stale, True
        return value, stale, False
    if isinstance(value, list):
        kept = []
        for item in value:
            if isinstance(item, str) and item.startswith(".lazy-harness/"):
                host_exists, source_exists = path_exists(root, source, item)
                if not host_exists and not source_exists:
                    stale.append({"field": field_name, "path": item, "reason": "missing-in-host-and-source"})
                    changed = True
                    continue
            kept.append(item)
        return kept, stale, changed
    return value, stale, False


def mark_stale_path(row: dict[str, Any], stale: list[dict[str, str]]) -> None:
    if not stale:
        return
    existing = row.get("stalePaths")
    if not isinstance(existing, list):
        existing = []
    row["stalePaths"] = [*existing, *stale]
    cleanup = row.get("graphCleanup")
    if not isinstance(cleanup, dict):
        cleanup = {}
    actions = cleanup.get("actions")
    if not isinstance(actions, list):
        actions = []
    if "stale-path" not in actions:
        actions.append("stale-path")
    cleanup["actions"] = actions
    cleanup["updatedAt"] = utc_now()
    row["graphCleanup"] = cleanup


def repair_stale_paths(root: pathlib.Path, source: pathlib.Path | None, row: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    next_row = dict(row)
    all_stale: list[dict[str, str]] = []
    changed = False
    for key in PATH_KEYS:
        if key not in next_row:
            continue
        new_value, stale, did_change = stale_paths_for_value(root, source, key, next_row[key])
        all_stale.extend(stale)
        changed = changed or did_change
        if did_change:
            if new_value is None or new_value == []:
                next_row.pop(key, None)
            else:
                next_row[key] = new_value
    evidence = next_row.get("evidence")
    if isinstance(evidence, list):
        new_evidence = []
        for idx, item in enumerate(evidence):
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                new_item = dict(item)
                new_value, stale, did_change = stale_paths_for_value(root, source, f"evidence[{idx}].path", new_item.get("path"))
                all_stale.extend(stale)
                if did_change:
                    changed = True
                    new_item.pop("path", None)
                new_evidence.append(new_item)
            else:
                new_evidence.append(item)
        next_row["evidence"] = new_evidence
    links = next_row.get("links")
    if isinstance(links, list):
        new_links = []
        for idx, item in enumerate(links):
            if isinstance(item, dict) and isinstance(item.get("target"), str) and str(item.get("target")).startswith(".lazy-harness/"):
                new_item = dict(item)
                new_value, stale, did_change = stale_paths_for_value(root, source, f"links[{idx}].target", new_item.get("target"))
                all_stale.extend(stale)
                if did_change:
                    changed = True
                    new_item["staleTarget"] = new_item.pop("target")
                new_links.append(new_item)
            else:
                new_links.append(item)
        next_row["links"] = new_links
    if changed:
        mark_stale_path(next_row, all_stale)
    return next_row, changed


def load_rows(graph: pathlib.Path) -> tuple[list[tuple[int, dict[str, Any], str]], list[dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any], str]] = []
    unsupported: list[dict[str, Any]] = []
    if not graph.exists():
        return rows, unsupported
    for line_number, line in enumerate(graph.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            unsupported.append({"line": line_number, "code": "invalid-json", "message": str(exc), "raw": line[:300]})
            continue
        if not isinstance(row, dict):
            unsupported.append({"line": line_number, "code": "non-object-row", "message": "Graph row is not a JSON object."})
            continue
        rows.append((line_number, row, line))
    return rows, unsupported


def cleanup(root: pathlib.Path, graph: pathlib.Path, source: pathlib.Path | None, apply: bool) -> CleanupResult:
    rows, unsupported = load_rows(graph)
    seen: dict[str, int] = {}
    operations: list[Operation] = []
    output_rows: list[dict[str, Any]] = []
    for line_number, row, _raw in rows:
        current = dict(row)
        before = dict(current)
        rid = current.get("id")
        if not isinstance(rid, str) or not rid:
            current["id"] = "kg_auto_" + stable_hash({k: v for k, v in current.items() if k != "id"})
            operations.append(Operation("add-id", line_number, before, dict(current), "row missing string id"))
            before = dict(current)
            rid = current["id"]
        if isinstance(rid, str) and rid in seen:
            current["id"] = f"{rid}__dup_{line_number}_{stable_hash(current)}"
            current["duplicateOf"] = rid
            operations.append(Operation("rename-duplicate-id", line_number, before, dict(current), f"duplicate id first seen on line {seen[rid]}"))
            before = dict(current)
            rid = current["id"]
        if isinstance(rid, str):
            seen.setdefault(rid, line_number)
        repaired, changed = repair_stale_paths(root, source, current)
        if changed:
            operations.append(Operation("mark-stale-path", line_number, current, dict(repaired), "path exists in neither host nor canonical source"))
            current = repaired
        output_rows.append(current)

    backup_path: str | None = None
    if apply and operations and not unsupported:
        backup = graph.with_suffix(graph.suffix + f".bak-{dt.datetime.now(dt.UTC).strftime('%Y%m%dT%H%M%SZ')}")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(graph, backup)
        graph.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in output_rows) + "\n", encoding="utf-8")
        backup_path = str(backup)

    counts: dict[str, int] = {"rows": len(rows), "unsupported": len(unsupported), "operations": len(operations)}
    for op in operations:
        counts[op.code] = counts.get(op.code, 0) + 1
    return CleanupResult(
        ok=len(unsupported) == 0,
        mode="graph-cleanup.apply" if apply else "graph-cleanup.plan",
        root=str(root),
        graphPath=str(graph),
        source=str(source) if source else None,
        dryRun=not apply,
        backupPath=backup_path,
        summary=counts,
        operations=operations,
        unsupported=unsupported,
    )


def print_md(result: CleanupResult) -> None:
    print(f"# Graph Cleanup {'Apply' if not result.dryRun else 'Plan'}")
    print(f"- ok: {str(result.ok).lower()}")
    print(f"- dryRun: {str(result.dryRun).lower()}")
    print(f"- graph: `{result.graphPath}`")
    if result.backupPath:
        print(f"- backup: `{result.backupPath}`")
    print("- summary:")
    for key, value in result.summary.items():
        print(f"  - {key}: {value}")
    if result.operations:
        print("\n## Operations")
        for op in result.operations[:50]:
            print(f"- {op.code} line {op.line}: {op.reason}")
        if len(result.operations) > 50:
            print(f"- ... {len(result.operations) - 50} more")
    if result.unsupported:
        print("\n## Unsupported")
        for item in result.unsupported[:20]:
            print(f"- line {item.get('line')}: {item.get('code')} {item.get('message')}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = pathlib.Path(args.root).resolve()
    graph = pathlib.Path(args.graph).resolve() if args.graph else root / ".lazy-harness" / "knowledge" / "graph.jsonl"
    source = lazy_dir(pathlib.Path(args.source).resolve()) if args.source else default_source(root)
    result = cleanup(root, graph, source, args.apply)
    if args.format == "json":
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print_md(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
