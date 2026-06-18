#!/usr/bin/env python3
"""Fast static validation tier for lazy-harness.

`lazy check` is intentionally not a full regression suite. It validates changed
files and lightweight repository invariants so agents can iterate quickly before
running `.lazy-harness/bin/lazy test` at commit/sync/release boundaries.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import py_compile
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from typing import Any

ROOT = pathlib.Path(os.environ.get("LAZY_HOST_ROOT", pathlib.Path(__file__).resolve().parents[2])).resolve()
LAZY = ROOT / ".lazy-harness"


@dataclass
class CheckIssue:
    path: str
    check: str
    message: str


@dataclass
class CheckResult:
    ok: bool
    mode: str
    files: list[str]
    checkedFiles: int
    errors: list[CheckIssue]
    warnings: list[CheckIssue]
    notes: list[str]
    fullRegression: bool = False


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def run(cmd: list[str], *, cwd: pathlib.Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def git_paths(args: list[str]) -> list[str]:
    completed = run(["git", *args])
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def default_changed_files() -> list[str]:
    paths: list[str] = []
    paths.extend(git_paths(["diff", "--name-only", "--cached"]))
    paths.extend(git_paths(["diff", "--name-only"]))
    paths.extend(git_paths(["ls-files", "--others", "--exclude-standard"]))
    return sorted(set(paths))


def all_harness_files() -> list[str]:
    if not LAZY.exists():
        return []
    return sorted(
        rel(path)
        for path in LAZY.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and not path.name.endswith(".pyc")
    )


def parse_files_arg(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                out.append(part)
    return sorted(set(out))


def resolve_root_path(path_str: str) -> pathlib.Path | None:
    path = (ROOT / path_str).resolve() if not pathlib.Path(path_str).is_absolute() else pathlib.Path(path_str).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        return None
    return path


def load_json_file(path: pathlib.Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def check_json(path: pathlib.Path, errors: list[CheckIssue]) -> None:
    try:
        load_json_file(path)
    except Exception as exc:  # noqa: BLE001 - validation reports parser details
        errors.append(CheckIssue(rel(path), "json-parse", str(exc)))


def check_jsonl(path: pathlib.Path, errors: list[CheckIssue]) -> None:
    try:
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            json.loads(line)
    except Exception as exc:  # noqa: BLE001
        errors.append(CheckIssue(rel(path), "jsonl-parse", str(exc)))


def check_xml(path: pathlib.Path, errors: list[CheckIssue]) -> None:
    try:
        ET.parse(path)
    except Exception as exc:  # noqa: BLE001
        errors.append(CheckIssue(rel(path), "xml-parse", str(exc)))


def check_py_compile(path: pathlib.Path, errors: list[CheckIssue]) -> None:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:  # noqa: BLE001
        errors.append(CheckIssue(rel(path), "python-compile", str(exc)))


def check_bash_syntax(path: pathlib.Path, errors: list[CheckIssue]) -> None:
    completed = run(["bash", "-n", str(path)])
    if completed.returncode != 0:
        errors.append(CheckIssue(rel(path), "bash-syntax", (completed.stderr or completed.stdout).strip()))


def check_no_nul(path: pathlib.Path, errors: list[CheckIssue]) -> None:
    try:
        data = path.read_bytes()
    except Exception as exc:  # noqa: BLE001
        errors.append(CheckIssue(rel(path), "read", str(exc)))
        return
    if b"\x00" in data:
        errors.append(CheckIssue(rel(path), "binary-nul", "text validation file contains NUL byte"))


def check_graph_ids(errors: list[CheckIssue]) -> None:
    graph = LAZY / "knowledge" / "graph.jsonl"
    if not graph.exists():
        return
    ids: dict[str, int] = {}
    try:
        for index, line in enumerate(graph.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row_id = row.get("id")
            if not isinstance(row_id, str) or not row_id:
                errors.append(CheckIssue(rel(graph), "graph-id", f"line {index}: missing id"))
                continue
            ids[row_id] = ids.get(row_id, 0) + 1
    except Exception as exc:  # noqa: BLE001
        errors.append(CheckIssue(rel(graph), "graph-jsonl", str(exc)))
        return
    duplicates = sorted(row_id for row_id, count in ids.items() if count > 1)
    if duplicates:
        errors.append(CheckIssue(rel(graph), "graph-duplicate-id", ", ".join(duplicates[:20])))


def check_manifest_paths(errors: list[CheckIssue], warnings: list[CheckIssue]) -> None:
    manifest = LAZY / "manifests" / "init-categories.json"
    if not manifest.exists():
        return
    try:
        data = load_json_file(manifest)
    except Exception as exc:  # noqa: BLE001
        errors.append(CheckIssue(rel(manifest), "manifest-json", str(exc)))
        return
    categories = data.get("categories", {}) if isinstance(data, dict) else {}
    if not isinstance(categories, dict):
        errors.append(CheckIssue(rel(manifest), "manifest-shape", "categories must be an object"))
        return
    for category_name, category in categories.items():
        items = category.get("items", []) if isinstance(category, dict) else []
        for item in items:
            item_path = item.get("path") if isinstance(item, dict) else None
            if not isinstance(item_path, str) or not item_path:
                errors.append(CheckIssue(rel(manifest), "manifest-path", f"category {category_name}: item missing path"))
                continue
            target = LAZY / item_path
            kind = item.get("kind")
            if kind == "file" and not target.is_file():
                errors.append(CheckIssue(rel(manifest), "manifest-file", f"missing file: {item_path}"))
            elif kind == "directory" and not target.is_dir():
                errors.append(CheckIssue(rel(manifest), "manifest-directory", f"missing directory: {item_path}"))
            globs = item.get("glob", [])
            if target.exists() and isinstance(globs, list):
                for pattern in globs:
                    if not isinstance(pattern, str):
                        continue
                    matches = list(target.glob(pattern)) if target.is_dir() else []
                    if not matches:
                        warnings.append(CheckIssue(rel(manifest), "manifest-glob", f"no matches for {item_path}/{pattern}"))


def manifest_target_path_for(root_bound_path: str) -> pathlib.Path | None:
    manifest = LAZY / "manifests" / "init-categories.json"
    if not manifest.exists() or not root_bound_path.startswith(".lazy-harness/"):
        return None
    try:
        data = load_json_file(manifest)
    except Exception:
        return None
    source_rel = root_bound_path.removeprefix(".lazy-harness/")
    for category in data.get("categories", {}).values():
        if not isinstance(category, dict):
            continue
        for item in category.get("items", []):
            if not isinstance(item, dict):
                continue
            if item.get("path") == source_rel and isinstance(item.get("targetPath"), str):
                return LAZY / item["targetPath"]
    return None


def check_fixture_canonical_records(path: pathlib.Path, errors: list[CheckIssue]) -> None:
    if ".lazy-harness/fixtures" not in rel(path).replace("\\", "/") or path.suffix != ".json":
        return
    try:
        data = load_json_file(path)
    except Exception:
        return
    records = data.get("canonicalRecords") if isinstance(data, dict) else None
    if not isinstance(records, list):
        return
    for value in records:
        if not isinstance(value, str) or not value.startswith(".lazy-harness/"):
            errors.append(CheckIssue(rel(path), "fixture-canonical-record", f"invalid root-bound path: {value!r}"))
            continue
        record_path = ROOT / value
        target_path = manifest_target_path_for(value)
        if not record_path.exists() and not (target_path and target_path.exists()):
            errors.append(CheckIssue(rel(path), "fixture-canonical-record", f"missing canonical record: {value}"))


def run_diff_check(errors: list[CheckIssue]) -> None:
    completed = run(["git", "diff", "--check"])
    if completed.returncode != 0:
        errors.append(CheckIssue("git diff --check", "whitespace", (completed.stdout + completed.stderr).strip()))


def should_check_graph(files: list[str], all_mode: bool) -> bool:
    return all_mode or any(path == ".lazy-harness/knowledge/graph.jsonl" for path in files)


def should_check_manifest(files: list[str], all_mode: bool) -> bool:
    return all_mode or any(path == ".lazy-harness/manifests/init-categories.json" for path in files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast changed-file static validation. Not a replacement for `lazy test`.")
    parser.add_argument("--files", action="append", default=[], help="Comma-separated or repeatable root-relative files to check. Defaults to git changed files.")
    parser.add_argument("--all", action="store_true", help="Check all .lazy-harness files, still using fast static checks only.")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    parser.add_argument("--no-diff-check", action="store_true", help="Skip `git diff --check`.")
    args = parser.parse_args()

    explicit_files = parse_files_arg(args.files)
    mode = "all" if args.all else "explicit" if explicit_files else "changed"
    files = all_harness_files() if args.all else explicit_files if explicit_files else default_changed_files()
    files = [path for path in files if path and not path.endswith("/")]

    errors: list[CheckIssue] = []
    warnings: list[CheckIssue] = []
    notes = ["fast static tier only; run `.lazy-harness/bin/lazy test` for full regression coverage"]

    if not args.no_diff_check:
        run_diff_check(errors)

    checked = 0
    normalized_files: list[str] = []
    for path_str in files:
        path = resolve_root_path(path_str)
        if path is None:
            errors.append(CheckIssue(path_str, "root-bound", "path is outside host root"))
            continue
        path_rel = rel(path)
        normalized_files.append(path_rel)
        if not path.exists():
            warnings.append(CheckIssue(path_rel, "missing", "file does not exist; assuming deleted/renamed"))
            continue
        if path.is_dir():
            continue
        checked += 1
        check_no_nul(path, errors)
        if path.suffix == ".json":
            check_json(path, errors)
            check_fixture_canonical_records(path, errors)
        elif path.suffix == ".jsonl":
            check_jsonl(path, errors)
        elif path.suffix == ".xml":
            check_xml(path, errors)
        elif path.suffix == ".py":
            check_py_compile(path, errors)
        elif path.suffix in {".sh", ".bash"} or path_rel == ".lazy-harness/bin/lazy":
            check_bash_syntax(path, errors)

    normalized_files = sorted(set(normalized_files))
    if should_check_graph(normalized_files, args.all):
        check_graph_ids(errors)
    if should_check_manifest(normalized_files, args.all):
        check_manifest_paths(errors, warnings)

    if not normalized_files:
        notes.append("no changed files detected")

    result = CheckResult(
        ok=not errors,
        mode=mode,
        files=normalized_files,
        checkedFiles=checked,
        errors=errors,
        warnings=warnings,
        notes=notes,
    )

    if args.format == "json":
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        status = "ok" if result.ok else "failed"
        print(f"lazy check {status} ({result.mode}, files={len(result.files)}, checked={result.checkedFiles})")
        for note in result.notes:
            print(f"- note: {note}")
        for warning in result.warnings:
            print(f"- warn [{warning.check}] {warning.path}: {warning.message}")
        for error in result.errors:
            print(f"- error [{error.check}] {error.path}: {error.message}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
