#!/usr/bin/env python3
"""Framework-owned Lazy-Harness doctor.

ADR 0022 boundary:
- Jcode may wrap this command, but operational checks live in .lazy-harness.
- `lazy:test` remains the primary reproducible gate and calls the smoke profile.

ADR 0026 scope separation:
- Same script runs both in framework dev repo and on hosts after lazy-init.
- `detect_scope()` auto-detects via framework-own markers; `--scope` overrides.
- Checks are tagged BOTH | FRAMEWORK_ONLY | HOST_ONLY. Scope-irrelevant checks
  are silently skipped with a [skipped] note in text output.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Callable, Literal

ROOT = pathlib.Path(os.environ.get("LAZY_HOST_ROOT", pathlib.Path(__file__).resolve().parents[2])).resolve()
LAZY = ROOT / ".lazy-harness"

Scope = Literal["framework", "host"]
CheckTag = Literal["BOTH", "FRAMEWORK_ONLY", "HOST_ONLY"]


def detect_scope() -> Scope:
    """ADR 0026: framework dev repo has both markers; hosts have neither."""
    return (
        "framework"
        if (LAZY / "framework" / "framework-contract.md").exists()
        and (LAZY / "planning" / "phase-5-plan.xml").exists()
        else "host"
    )


@dataclass
class CheckResult:
    check_id: str
    status: str
    message: str
    details: list[str]
    scope: str = "both"  # ADR 0026: which scope this check applies to


Check = Callable[[], CheckResult]


def rel(path: pathlib.Path) -> str:
    return str(path.relative_to(ROOT))


def ok(check_id: str, message: str, details: list[str] | None = None) -> CheckResult:
    return CheckResult(check_id, "ok", message, details or [])


def fail(check_id: str, message: str, details: list[str] | None = None) -> CheckResult:
    return CheckResult(check_id, "fail", message, details or [])


def warn(check_id: str, message: str, details: list[str] | None = None) -> CheckResult:
    return CheckResult(check_id, "warn", message, details or [])


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def check_xml_parse() -> CheckResult:
    errors: list[str] = []
    for path in sorted(LAZY.rglob("*.xml")):
        try:
            ET.parse(path)
        except Exception as exc:  # noqa: BLE001 - doctor must surface parser detail
            errors.append(f"{rel(path)}: {exc}")
    if errors:
        return fail("D01", "XML parse failed", errors)
    return ok("D01", "XML parse ok")


def check_jsonl_parse() -> CheckResult:
    errors: list[str] = []
    for path in [LAZY / "logs" / "actions.jsonl", LAZY / "logs" / "decisions.jsonl", LAZY / "logs" / "validations.jsonl"]:
        if not path.exists():
            errors.append(f"missing {rel(path)}")
            continue
        for index, line in enumerate(read_text(path).splitlines(), start=1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{rel(path)}:{index}: {exc}")
    if errors:
        return fail("D02", "JSONL parse failed", errors)
    return ok("D02", "JSONL parse ok")


def decision_files() -> list[pathlib.Path]:
    """ADR files follow strict `NNNN-slug.md` convention where NNNN is 0001~9999.
    The leading-zero glob `0[0-9][0-9][0-9]-*.md` deliberately excludes date-based
    decision notes (e.g. `2026-05-13-foo.md`) which hosts may also keep alongside
    ADRs but are not part of the ADR sequence."""
    return sorted((LAZY / "decisions").glob("0[0-9][0-9][0-9]-*.md"))


def check_adr_sequence() -> CheckResult:
    """BOTH scope (ADR 0026): pure ADR number contiguity. Host ADRs also need this.

    Framework philosophy: a host that has not started its institutional memory yet
    (zero ADRs) should not be punished. The sequence check only kicks in once the
    host has at least one ADR — at that point contiguity actually means something."""
    files = decision_files()
    if not files:
        # Host hasn't started accumulating ADRs yet — sequence check is meaningless.
        # This is the expected state for early-stage hosts; they fill ADRs as they
        # make architectural decisions.
        return ok("D03", "no ADRs yet — sequence check skipped (host pre-decision phase)")

    numbers = [int(path.name[:4]) for path in files]
    expected = list(range(1, max(numbers) + 1))
    details: list[str] = []
    if numbers != expected:
        missing = sorted(set(expected) - set(numbers))
        duplicate = sorted({number for number in numbers if numbers.count(number) > 1})
        if missing:
            details.append(f"missing ADR numbers: {missing}")
        if duplicate:
            details.append(f"duplicate ADR numbers: {duplicate}")
        return fail("D03", "ADR sequence is not contiguous", details)

    count = len(files)
    max_id = numbers[-1]
    return ok("D03", f"ADR sequence ok ({count}, 0001~{max_id:04d})")


def check_framework_adr_freshness() -> CheckResult:
    """FRAMEWORK_ONLY scope (ADR 0026): README / handoff must reflect ADR count.
    Host doesn't need this — host's README/handoff drift policy is its own concern."""
    files = decision_files()
    numbers = [int(path.name[:4]) for path in files]
    count = len(files)
    max_id = numbers[-1] if numbers else 0
    details: list[str] = []
    readme = read_text(LAZY / "README.md")
    handoff = read_text(LAZY / "handoff" / "00-current-state.md")
    if f"# {count} ADRs" not in readme and f"# {count} ADR" not in readme and f"# {count}" not in readme:
        if f"decisions/          # {count} ADRs" not in readme:
            details.append(f"README ADR count does not mention {count}")
    if f"**{count}**" not in handoff or f"0001~{max_id:04d}" not in handoff:
        details.append(f"handoff ADR line should mention **{count}** and 0001~{max_id:04d}")
    if details:
        return fail("D03F", "ADR docs are stale", details)
    return ok("D03F", f"framework ADR docs fresh ({count}, 0001~{max_id:04d})")


def check_plan_freshness() -> CheckResult:
    phase_plan = read_text(LAZY / "planning" / "phase-5-plan.xml")
    readme = read_text(LAZY / "README.md")
    handoff = read_text(LAZY / "handoff" / "00-current-state.md")
    required_done = ["5c-1", "5c-2", "5c-3", "5c-4", "5c-5", "5c-6", "5c-7", "5c-8", "5c-9"]
    details: list[str] = []
    for criterion in required_done:
        pattern = rf'<criterion id="{re.escape(criterion)}" status="done"'
        if not re.search(pattern, phase_plan):
            details.append(f"phase-5-plan.xml: {criterion} must be status=done")
    for marker in ["5c-5 Cross-layer", "5c-6 Lint/typecheck", "5c-7 Structured ask", "5c-9 Doctor C17", "5c-8"]:
        if marker not in handoff:
            details.append(f"handoff missing marker: {marker}")
    for marker in ["**5c-5**", "**5c-7**", "5c-6", "5c-8", "5c-9"]:
        if marker not in readme:
            details.append(f"README missing phase marker: {marker}")
    if details:
        return fail("D04", "phase README/handoff freshness failed", details)
    return ok("D04", "phase README/handoff freshness ok")


def current_branch() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001
        return ""


def check_branch_policy() -> CheckResult:
    branch = current_branch()
    details: list[str] = []
    if not (LAZY / "decisions" / "0021-experimental-branch-and-extract-strategy.md").exists():
        details.append("missing ADR 0021 branch/extract strategy")
    if branch != "experimental/lazy-harness":
        status = subprocess.check_output(["git", "status", "--short", "--", ".lazy-harness", ".jcode"], cwd=ROOT, text=True)
        if status.strip():
            details.append(f"private harness files modified on non-framework branch {branch}: {status.strip()}")
    for path in [LAZY / "hooks" / "pre-commit-guard.sh", LAZY / "hooks" / "pre-push.sh"]:
        if not path.exists():
            details.append(f"missing hook: {rel(path)}")
        elif not path.stat().st_mode & 0o111:
            details.append(f"hook is not executable: {rel(path)}")
    if details:
        return fail("D05", "branch/hook policy failed", details)
    return ok("D05", f"branch/hook policy ok ({branch})")


def external_pattern_terms() -> list[str]:
    # Split SaaS names so the C17 doctor does not flag its own forbidden-term list.
    return [
        r"\bfetch\s*\(",
        r"\baxios\b",
        r"\bnode-fetch\b",
        r"\bgot\s*\(",
        r"https?://",
        "api." + "figma" + ".com",
        "slack" + ".com/api",
        "api." + "linear" + ".app",
        "api." + "github" + ".com",
        "open" + "ai",
        "anth" + "ropic",
        "supa" + "base",
    ]


EXTERNAL_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in external_pattern_terms()]


def check_external_dependency_invariant() -> CheckResult:
    # C17 executable/code scope. Documentation files intentionally excluded to avoid
    # failing on ADR examples that describe forbidden integrations.
    code_suffixes = {".ts", ".tsx", ".js", ".mjs", ".cjs", ".py", ".sh"}
    scan_roots = [LAZY / "triggers", LAZY / "hooks", LAZY / "scripts", LAZY / "framework"]
    include_negative_fixture = os.environ.get("LAZY_HARNESS_DOCTOR_INCLUDE_NEGATIVE") == "1"
    hits: list[str] = []
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for path in sorted(scan_root.rglob("*")):
            if not path.is_file() or path.suffix not in code_suffixes:
                continue
            # Skip legacy-* directories (archived/retired tooling, not active code).
            if any(part.startswith("legacy-") for part in path.relative_to(LAZY).parts):
                continue
            if path.name.startswith("__doctor_c17_negative_tmp") and not include_negative_fixture:
                continue
            text = read_text(path)
            for index, line in enumerate(text.splitlines(), start=1):
                if any(pattern.search(line) for pattern in EXTERNAL_PATTERNS):
                    hits.append(f"{rel(path)}:{index}: {line.strip()[:160]}")
    if hits:
        return fail("D06", "C17 external dependency invariant failed", hits)
    return ok("D06", "C17 external dependency invariant ok")


TYPECHECK_ENV_PATTERNS = [
    re.compile(r"Cannot find type definition file for", re.IGNORECASE),
    re.compile(r"File .+ not found", re.IGNORECASE),
    re.compile(r"Cannot read file", re.IGNORECASE),
    re.compile(r"Cannot find module .+ or its corresponding type declarations", re.IGNORECASE),
]

TYPECHECK_CODE_PATTERNS = [
    re.compile(r"Type .+ is not assignable to type", re.IGNORECASE),
    re.compile(r"Property .+ does not exist on type", re.IGNORECASE),
    re.compile(r"';' expected|Declaration or statement expected|Expression expected", re.IGNORECASE),
]


def classify_typecheck_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("$"):
        return None
    if any(pattern.search(stripped) for pattern in TYPECHECK_ENV_PATTERNS):
        return "environment"
    if any(pattern.search(stripped) for pattern in TYPECHECK_CODE_PATTERNS):
        return "code-drift"
    if re.search(r"\berror\s+TS\d+:", stripped):
        return "unknown"
    if re.search(r"^.+\(\d+,\d+\):\s+error\s+TS\d+:", stripped):
        return "unknown"
    return None


def check_package_health() -> CheckResult:
    if not (ROOT / "package.json").exists():
        return warn("D07", "package health skipped: environment without package.json")

    try:
        completed = subprocess.run(
            ["bun", "run", "typecheck:node"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError:
        return warn("D07", "package health environment warning", ["bun executable not found"])
    except subprocess.TimeoutExpired:
        return warn("D07", "package health environment warning", ["typecheck:node timed out after 120s"])

    combined = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    diagnostics = [line.strip() for line in combined.splitlines() if classify_typecheck_line(line)]
    categories = {classify_typecheck_line(line) for line in diagnostics}
    categories.discard(None)

    if completed.returncode == 0:
        return ok("D07", "package health ok")
    if categories and categories <= {"environment"}:
        return warn("D07", "package health environment warning", diagnostics[:20])
    if "code-drift" in categories or "unknown" in categories:
        return fail("D07", "package health typecheck failed", diagnostics[:20] or combined.splitlines()[:20])
    return warn("D07", "package health environment warning", combined.splitlines()[:20])


def check_unicode_replacement_chars() -> CheckResult:
    scan_suffixes = {".md", ".xml", ".json", ".jsonl", ".txt"}
    hits: list[str] = []
    for root in [LAZY, ROOT / "docs"]:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in scan_suffixes:
                continue
            text = read_text(path)
            for index, line in enumerate(text.splitlines(), start=1):
                if "�" in line:
                    hits.append(f"{rel(path)}:{index}: {line.strip()[:160]}")
                    if len(hits) >= 40:
                        return warn("D08", "Unicode replacement characters found", hits)
    if hits:
        return warn("D08", "Unicode replacement characters found", hits)
    return ok("D08", "Unicode replacement characters absent")


SMOKE_CHECKS: list[tuple[Check, CheckTag]] = [
    (check_xml_parse, "BOTH"),
    (check_jsonl_parse, "BOTH"),
    (check_adr_sequence, "BOTH"),
    (check_framework_adr_freshness, "FRAMEWORK_ONLY"),
    (check_plan_freshness, "FRAMEWORK_ONLY"),
    (check_branch_policy, "FRAMEWORK_ONLY"),
]

FULL_CHECKS: list[tuple[Check, CheckTag]] = [
    *SMOKE_CHECKS,
    (check_external_dependency_invariant, "BOTH"),
    (check_package_health, "BOTH"),
    (check_unicode_replacement_chars, "BOTH"),
]


def run_checks(profile: str, scope: Scope) -> list[CheckResult]:
    """ADR 0026: filter checks by scope. BOTH always runs; FRAMEWORK_ONLY only on
    framework scope; HOST_ONLY only on host scope. Skipped checks are not in the result list."""
    checks = SMOKE_CHECKS if profile == "smoke" else FULL_CHECKS
    results: list[CheckResult] = []
    for check, tag in checks:
        if tag == "BOTH":
            applies = True
        elif tag == "FRAMEWORK_ONLY":
            applies = scope == "framework"
        elif tag == "HOST_ONLY":
            applies = scope == "host"
        else:
            applies = True
        if applies:
            result = check()
            # Annotate scope for result schema (ADR 0026)
            result.scope = "both" if tag == "BOTH" else tag.lower().replace("_only", "")
            results.append(result)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Lazy-Harness framework-owned doctor")
    parser.add_argument("--profile", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument(
        "--scope",
        choices=["auto", "framework", "host"],
        default="auto",
        help="ADR 0026: which scope to validate. 'auto' detects via framework-own markers.",
    )
    args = parser.parse_args()

    scope: Scope = detect_scope() if args.scope == "auto" else args.scope  # type: ignore[assignment]

    results = run_checks(args.profile, scope)
    failed = [result for result in results if result.status == "fail"]

    if args.format == "json":
        print(
            json.dumps(
                {
                    "ok": not failed,
                    "profile": args.profile,
                    "scope": scope,
                    "results": [result.__dict__ for result in results],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for result in results:
            icon = "✓" if result.status == "ok" else "⚠" if result.status == "warn" else "✗"
            print(f"{icon} {result.check_id} {result.message}")
            for detail in result.details:
                print(f"  - {detail}")
        if failed:
            print(f"lazy-harness doctor failed (scope={scope})")
        else:
            print(f"lazy-harness doctor ok ({args.profile}, scope={scope})")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
