#!/usr/bin/env python3
"""Bounded validation governor for lazy-harness.

`lazy validate` chooses an explicit validation plan, enforces a total wall-clock
budget, and refuses release-grade validation unless the caller opts in. It is a
thin governor over existing lazy commands, not a replacement for `lazy check` or
`lazy test`.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import time
from dataclasses import asdict, dataclass

ROOT = pathlib.Path(os.environ.get("LAZY_HOST_ROOT", pathlib.Path(__file__).resolve().parents[2])).resolve()
LAZY = ROOT / ".lazy-harness"
LAZY_BIN = LAZY / "bin" / "lazy"

DEFAULT_BUDGET_SECONDS = {
    "fast": 60.0,
    "standard": 300.0,
    "release": 900.0,
}
MAX_BUDGET_SECONDS = 3600.0
OUTPUT_TAIL_CHARS = 4000


@dataclass
class ValidationStep:
    name: str
    kind: str
    command: list[str]


@dataclass
class StepResult:
    name: str
    kind: str
    command: list[str]
    status: str
    exitCode: int | None = None
    elapsedSeconds: float = 0.0
    stdoutTail: str = ""
    stderrTail: str = ""
    reason: str = ""


@dataclass
class ValidationResult:
    ok: bool
    plan: str
    bounded: bool
    maxSeconds: float
    elapsedSeconds: float
    dryRun: bool
    releaseAllowed: bool
    fullRegression: bool
    steps: list[StepResult]
    errors: list[str]
    notes: list[str]


def parse_files_arg(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                out.append(part)
    return sorted(set(out))


def tail(text: str) -> str:
    if len(text) <= OUTPUT_TAIL_CHARS:
        return text
    return text[-OUTPUT_TAIL_CHARS:]


def lazy_command(*args: str) -> list[str]:
    return [str(LAZY_BIN), *args]


def check_step(files: list[str]) -> ValidationStep:
    command = lazy_command("check", "--format=json")
    if files:
        command.extend(["--files", ",".join(files)])
    return ValidationStep("fast-static-check", "fast-static", command)


def test_step(scope: str) -> ValidationStep:
    command = lazy_command("test")
    if scope != "auto":
        command.extend(["--scope", scope])
    return ValidationStep("full-self-test", "full-regression", command)


def plan_steps(plan: str, files: list[str], scope: str) -> list[ValidationStep]:
    if plan == "fast":
        return [check_step(files)]
    if plan == "standard":
        return [check_step(files), test_step(scope)]
    if plan == "release":
        return [
            check_step(files),
            test_step(scope),
            ValidationStep("doctor-smoke", "health", lazy_command("doctor", "--profile=smoke")),
            ValidationStep("record-audit", "record-quality", lazy_command("record-audit", "--format=json")),
            ValidationStep("graph-hygiene", "knowledge-graph", lazy_command("graph-hygiene", "--format=json")),
            ValidationStep("lifecycle-parity", "lifecycle-parity", lazy_command("lifecycle-parity", "--format=json")),
        ]
    raise ValueError(f"unknown plan: {plan}")


def dedupe_steps(steps: list[ValidationStep]) -> tuple[list[ValidationStep], list[StepResult]]:
    seen: set[tuple[str, ...]] = set()
    unique: list[ValidationStep] = []
    skipped: list[StepResult] = []
    for step in steps:
        signature = tuple(step.command)
        if signature in seen:
            skipped.append(
                StepResult(
                    name=step.name,
                    kind=step.kind,
                    command=step.command,
                    status="skipped",
                    reason="duplicate-command",
                )
            )
            continue
        seen.add(signature)
        unique.append(step)
    return unique, skipped


def run_step(step: ValidationStep, deadline: float) -> StepResult:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return StepResult(
            name=step.name,
            kind=step.kind,
            command=step.command,
            status="skipped",
            reason="deadline-exhausted",
        )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            step.command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=remaining,
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        return StepResult(
            name=step.name,
            kind=step.kind,
            command=step.command,
            status="timeout",
            elapsedSeconds=round(elapsed, 3),
            stdoutTail=tail(exc.stdout if isinstance(exc.stdout, str) else ""),
            stderrTail=tail(exc.stderr if isinstance(exc.stderr, str) else ""),
            reason="step exceeded remaining validation budget",
        )
    elapsed = time.monotonic() - started
    return StepResult(
        name=step.name,
        kind=step.kind,
        command=step.command,
        status="passed" if completed.returncode == 0 else "failed",
        exitCode=completed.returncode,
        elapsedSeconds=round(elapsed, 3),
        stdoutTail=tail(completed.stdout),
        stderrTail=tail(completed.stderr),
    )


def build_result(args: argparse.Namespace) -> tuple[ValidationResult, int]:
    max_seconds = DEFAULT_BUDGET_SECONDS[args.plan] if args.max_seconds is None else args.max_seconds
    errors: list[str] = []
    notes = [
        "bounded validation governor; use explicit --plan release --allow-release for release-grade matrices",
        "lazy check remains fast static validation; lazy test remains the full regression gate",
    ]
    if max_seconds < 0:
        errors.append("--max-seconds must be non-negative")
    if max_seconds > MAX_BUDGET_SECONDS:
        errors.append("--max-seconds cannot exceed 3600; split validation into bounded chunks")
    if args.plan == "release" and not args.dry_run and not args.allow_release:
        errors.append("release plan requires --allow-release or --dry-run")

    files = parse_files_arg(args.files)
    requested_steps = plan_steps(args.plan, files, args.scope)
    steps, skipped = dedupe_steps(requested_steps)

    start = time.monotonic()
    if errors:
        result = ValidationResult(
            ok=False,
            plan=args.plan,
            bounded=True,
            maxSeconds=max_seconds,
            elapsedSeconds=round(time.monotonic() - start, 3),
            dryRun=args.dry_run,
            releaseAllowed=args.allow_release,
            fullRegression=False,
            steps=[
                *[
                    StepResult(step.name, step.kind, step.command, "planned", reason="not executed due validation argument error")
                    for step in steps
                ],
                *skipped,
            ],
            errors=errors,
            notes=notes,
        )
        return result, 2

    if args.dry_run:
        result = ValidationResult(
            ok=True,
            plan=args.plan,
            bounded=True,
            maxSeconds=max_seconds,
            elapsedSeconds=round(time.monotonic() - start, 3),
            dryRun=True,
            releaseAllowed=args.allow_release,
            fullRegression=any(step.kind == "full-regression" for step in steps),
            steps=[*[StepResult(step.name, step.kind, step.command, "planned") for step in steps], *skipped],
            errors=[],
            notes=notes,
        )
        return result, 0

    deadline = start + max_seconds
    results: list[StepResult] = []
    ok = True
    full_regression = False
    for step in steps:
        step_result = run_step(step, deadline)
        results.append(step_result)
        if step_result.status == "passed" and step.kind == "full-regression":
            full_regression = True
        if step_result.status != "passed":
            ok = False
            break
    results.extend(skipped)
    result = ValidationResult(
        ok=ok,
        plan=args.plan,
        bounded=True,
        maxSeconds=max_seconds,
        elapsedSeconds=round(time.monotonic() - start, 3),
        dryRun=False,
        releaseAllowed=args.allow_release,
        fullRegression=full_regression,
        steps=results,
        errors=[] if ok else ["validation plan failed or exceeded budget"],
        notes=notes,
    )
    return result, 0 if ok else 1


def print_md(result: ValidationResult) -> None:
    status = "ok" if result.ok else "failed"
    print(f"lazy validate {status} (plan={result.plan}, bounded={str(result.bounded).lower()}, max={result.maxSeconds:g}s, elapsed={result.elapsedSeconds:g}s)")
    for note in result.notes:
        print(f"- note: {note}")
    for error in result.errors:
        print(f"- error: {error}")
    for step in result.steps:
        command = " ".join(step.command)
        detail = f"- {step.status}: {step.name} [{step.kind}] `{command}`"
        if step.elapsedSeconds:
            detail += f" ({step.elapsedSeconds:g}s)"
        if step.reason:
            detail += f" — {step.reason}"
        print(detail)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run bounded lazy-harness validation plans.")
    parser.add_argument("--plan", choices=["fast", "standard", "release"], default="fast", help="Validation plan to run. release requires --allow-release unless --dry-run is set.")
    parser.add_argument("--files", action="append", default=[], help="Comma-separated or repeatable root-relative files passed to lazy check.")
    parser.add_argument("--scope", choices=["auto", "framework", "host"], default="auto", help="Scope passed to lazy test in plans that include full regression.")
    parser.add_argument("--max-seconds", type=float, default=None, help="Total validation budget. Defaults: fast=60, standard=300, release=900. Maximum 3600.")
    parser.add_argument("--allow-release", action="store_true", help="Required to execute --plan release. Not required for --dry-run.")
    parser.add_argument("--dry-run", action="store_true", help="Print the bounded plan without executing steps.")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    args = parser.parse_args(argv)

    result, code = build_result(args)
    if args.format == "json":
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print_md(result)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
