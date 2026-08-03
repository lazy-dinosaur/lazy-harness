#!/usr/bin/env python3
"""Bounded validation governor for lazy-harness.

`lazy validate` chooses an explicit validation plan, enforces a total wall-clock
budget, and refuses release-grade validation unless the caller opts in. It is a
thin governor over existing lazy commands, not a replacement for `lazy check` or
`lazy test`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
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
CACHE_VERSION = 3
CACHE_MAX_ENTRIES = 50
PROGRESS_PREFIX = "LAZY_PROGRESS "
PROGRESS_SUPPORT_ENV = "LAZY_PROGRESS_SUPPORTED"


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
    evidenceKey: str = ""
    cachedAt: str = ""


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
    evidenceReused: bool
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


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_git(args: list[str]) -> bytes:
    completed = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).decode("utf-8", errors="replace"))
    return completed.stdout


def command_signature(command: str) -> str:
    executable = shutil.which(command)
    if executable is None:
        return sha256_text(json.dumps({"command": command, "status": "missing"}, sort_keys=True))
    try:
        completed = subprocess.run([executable, "--version"], cwd=ROOT, capture_output=True, check=False, timeout=10)
        version = (completed.stdout or completed.stderr).decode("utf-8", errors="replace").strip()
        if completed.returncode != 0 or not version:
            version = f"exit={completed.returncode}"
    except Exception as exc:
        version = f"uncertain:{type(exc).__name__}"
    return sha256_text(json.dumps({"command": command, "path": str(pathlib.Path(executable).resolve()), "version": version}, sort_keys=True))


def dependency_fingerprint() -> str:
    h = hashlib.sha256()
    for name in ("package.json", "bun.lock", "bun.lockb", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock", "requirements.txt"):
        path = ROOT / name
        if not path.is_file():
            continue
        h.update(name.encode("utf-8") + b"\0")
        h.update(sha256_bytes(path.read_bytes()).encode("ascii") + b"\0")
    return h.hexdigest()


def toolchain_fingerprint() -> str:
    payload = {
        "pythonExecutable": str(pathlib.Path(sys.executable).resolve()),
        "pythonVersion": sys.version,
        "bun": command_signature("bun"),
        "git": command_signature("git"),
    }
    return sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def runtime_root() -> pathlib.Path:
    return pathlib.Path(os.environ.get("LAZY_RUNTIME_ROOT", str(LAZY))).resolve()


def cache_path() -> pathlib.Path:
    return runtime_root() / "state" / "validation-evidence-cache.json"


def evidence_cache_enabled(value: str) -> bool:
    if value == "off" or os.environ.get("LAZY_VALIDATE_EVIDENCE_CACHE") == "0":
        return False
    return True


def is_volatile_harness_path(name: str) -> bool:
    normalized = name.strip("/")
    volatile_prefixes = (
        ".lazy-harness/state/",
        ".lazy-harness/logs/",
        ".lazy-harness/generated/",
    )
    return normalized.startswith(volatile_prefixes) or "/__pycache__/" in f"/{normalized}/" or normalized.endswith(".pyc")


def is_full_regression_irrelevant_path(name: str) -> bool:
    """Paths whose content cannot change the executable/full-regression result.

    Evidence capsules are validation output. They are still checked by the fast
    tier, but editing a summarized command/result must not invalidate the full
    regression evidence that produced it.
    """
    normalized = name.strip("/")
    return is_volatile_harness_path(normalized) or normalized.startswith(".lazy-harness/evidence/")


def should_hash_harness_file(path: pathlib.Path) -> bool:
    try:
        rel = path.relative_to(LAZY)
    except ValueError:
        return False
    if not path.is_file():
        return False
    rel_name = f".lazy-harness/{rel.as_posix()}"
    if is_full_regression_irrelevant_path(rel_name):
        return False
    if path.suffix == ".pyc":
        return False
    return True


def harness_fingerprint() -> str:
    h = hashlib.sha256()
    for path in sorted(LAZY.rglob("*")):
        if not should_hash_harness_file(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        h.update(rel.encode("utf-8") + b"\0")
        h.update(sha256_bytes(path.read_bytes()).encode("ascii") + b"\0")
    return h.hexdigest()


def untracked_fingerprint() -> str:
    raw = run_git(["ls-files", "--others", "--exclude-standard", "-z"])
    h = hashlib.sha256()
    for name in sorted(item for item in raw.decode("utf-8", errors="surrogateescape").split("\0") if item):
        if is_full_regression_irrelevant_path(name):
            continue
        path = ROOT / name
        h.update(name.encode("utf-8", errors="surrogateescape") + b"\0")
        if path.is_file():
            h.update(sha256_bytes(path.read_bytes()).encode("ascii") + b"\0")
        else:
            h.update(b"missing-or-non-file\0")
    return h.hexdigest()


def workspace_fingerprint() -> dict[str, str]:
    """Return conservative content-address inputs for validation evidence reuse.

    The key intentionally includes both project git state and the installed
    `.lazy-harness` body. Dogfood hosts often keep `.lazy-harness` untracked, so
    HEAD alone is not enough to prove a prior `lazy test` still covers the
    current harness copy.
    """
    head = run_git(["rev-parse", "HEAD"]).decode("utf-8", errors="replace").strip()
    diff_hash = sha256_bytes(run_git([
        "diff",
        "--binary",
        "HEAD",
        "--",
        ".",
        ":(exclude).lazy-harness/state/**",
        ":(exclude).lazy-harness/logs/**",
        ":(exclude).lazy-harness/generated/**",
        ":(exclude).lazy-harness/evidence/**",
    ]))
    raw_status = run_git(["status", "--porcelain=v1", "-z"]).decode("utf-8", errors="surrogateescape")
    status_items = [item for item in raw_status.split("\0") if item]
    filtered_status = "\0".join(item for item in status_items if not is_full_regression_irrelevant_path(item[3:] if len(item) > 3 else item))
    status_hash = sha256_text(filtered_status)
    return {
        "hostRootHash": sha256_text(str(ROOT)),
        "head": head,
        "diffHash": diff_hash,
        "statusHash": status_hash,
        "untrackedHash": untracked_fingerprint(),
        "harnessHash": harness_fingerprint(),
        "dependencyHash": dependency_fingerprint(),
        "toolchainHash": toolchain_fingerprint(),
    }


def evidence_key(step: ValidationStep, scope: str, fingerprint: dict[str, str]) -> str:
    payload = {
        "version": CACHE_VERSION,
        "kind": step.kind,
        "name": step.name,
        "command": step.command,
        "scope": scope,
        "fingerprint": fingerprint,
    }
    return sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def load_cache() -> dict[str, object]:
    path = cache_path()
    if not path.exists():
        return {"version": CACHE_VERSION, "entries": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": CACHE_VERSION, "entries": {}}
    if data.get("version") != CACHE_VERSION or not isinstance(data.get("entries"), dict):
        return {"version": CACHE_VERSION, "entries": {}}
    return data


def save_cache(data: dict[str, object]) -> None:
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = data.get("entries")
    if isinstance(entries, dict) and len(entries) > CACHE_MAX_ENTRIES:
        ordered = sorted(entries.items(), key=lambda item: str(item[1].get("cachedAt", "")), reverse=True)
        data["entries"] = dict(ordered[:CACHE_MAX_ENTRIES])
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def cached_step_result(step: ValidationStep, key: str, cache: dict[str, object]) -> StepResult | None:
    entries = cache.get("entries")
    if not isinstance(entries, dict):
        return None
    entry = entries.get(key)
    if not isinstance(entry, dict) or entry.get("ok") is not True:
        return None
    return StepResult(
        name=step.name,
        kind=step.kind,
        command=step.command,
        status="reused",
        exitCode=0,
        elapsedSeconds=0.0,
        reason="valid cached full-regression evidence",
        evidenceKey=key,
        cachedAt=str(entry.get("cachedAt", "")),
    )


def store_step_result(step: ValidationStep, key: str, fingerprint: dict[str, str], result: StepResult) -> None:
    cache = load_cache()
    entries = cache.setdefault("entries", {})
    if not isinstance(entries, dict):
        cache["entries"] = entries = {}
    entries[key] = {
        "ok": True,
        "cachedAt": utc_now(),
        "step": step.name,
        "kind": step.kind,
        "command": step.command,
        "fingerprint": fingerprint,
        "exitCode": result.exitCode,
        "elapsedSeconds": result.elapsedSeconds,
    }
    save_cache(cache)


def progress_enabled(value: str, dry_run: bool) -> bool:
    if dry_run:
        return False
    legacy_override = os.environ.get("LAZY_VALIDATE_PROGRESS")
    if value == "off" or legacy_override == "0":
        return False
    if value == "on":
        return True
    return os.environ.get(PROGRESS_SUPPORT_ENV) == "1" or legacy_override == "1"


def emit_progress(enabled: bool, *, current: int, total: int, message: str) -> None:
    if not enabled:
        return
    percent = 100 if total <= 0 else min(100, max(0, round((current / total) * 100)))
    payload = {
        "current": current,
        "total": total,
        "unit": "steps",
        "percent": percent,
        "message": message,
    }
    print(PROGRESS_PREFIX + json.dumps(payload, ensure_ascii=False), file=sys.stderr, flush=True)


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
            evidenceReused=False,
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
            evidenceReused=False,
            steps=[*[StepResult(step.name, step.kind, step.command, "planned") for step in steps], *skipped],
            errors=[],
            notes=notes,
        )
        return result, 0

    deadline = start + max_seconds
    results: list[StepResult] = []
    ok = True
    full_regression = False
    evidence_reused = False
    fingerprint: dict[str, str] | None = None
    cache: dict[str, object] | None = None
    cache_enabled = evidence_cache_enabled(args.evidence_cache)
    if cache_enabled:
        notes.append("full-regression evidence cache enabled; cache miss or uncertainty falls back to lazy test")
    else:
        notes.append("full-regression evidence cache disabled")
    progress = progress_enabled(args.progress, args.dry_run)
    emit_progress(progress, current=0, total=len(steps), message=f"Starting lazy validate plan={args.plan}")
    for index, step in enumerate(steps, start=1):
        emit_progress(progress, current=index - 1, total=len(steps), message=f"Running {step.name}")
        cache_key = ""
        if cache_enabled and step.kind == "full-regression":
            try:
                if fingerprint is None:
                    fingerprint = workspace_fingerprint()
                if cache is None:
                    cache = load_cache()
                cache_key = evidence_key(step, args.scope, fingerprint)
                cached_result = cached_step_result(step, cache_key, cache)
            except Exception as exc:
                cached_result = None
                notes.append(f"evidence cache unavailable; running full-regression step: {exc}")
            if cached_result is not None:
                step_result = cached_result
                evidence_reused = True
            else:
                step_result = run_step(step, deadline)
                if step_result.status == "passed" and fingerprint is not None and cache_key:
                    try:
                        store_step_result(step, cache_key, fingerprint, step_result)
                        step_result.evidenceKey = cache_key
                    except Exception as exc:
                        notes.append(f"evidence cache store failed after passing full-regression: {exc}")
        else:
            step_result = run_step(step, deadline)
        results.append(step_result)
        emit_progress(progress, current=index, total=len(steps), message=f"{step_result.status}: {step.name}")
        if step_result.status in {"passed", "reused"} and step.kind == "full-regression":
            full_regression = True
        if step_result.status not in {"passed", "reused"}:
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
        evidenceReused=evidence_reused,
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
    parser.add_argument("--evidence-cache", choices=["auto", "on", "off"], default="auto", help="Reuse cached full-regression evidence when the conservative workspace fingerprint matches. Use --evidence-cache=off or LAZY_VALIDATE_EVIDENCE_CACHE=0 to disable.")
    parser.add_argument(
        "--progress",
        choices=["auto", "on", "off"],
        default="auto",
        help=(
            "Emit runtime-neutral LAZY_PROGRESS lines to stderr. auto requires "
            "LAZY_PROGRESS_SUPPORTED=1; on enables explicitly; off or "
            "LAZY_VALIDATE_PROGRESS=0 disables."
        ),
    )
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
