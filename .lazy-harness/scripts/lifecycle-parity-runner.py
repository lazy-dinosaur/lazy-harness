#!/usr/bin/env python3
"""Batch parity runner for response.completed legacy hook vs lifecycle-check shadow.

Phase 2 safety tool. It creates fresh temporary host copies per fixture, runs
production `on-response-completed.sh` and shadow `lifecycle-check.py`, and
compares first-output behavior. It does not replace production hook behavior.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
AFTERSHOCK_DECISIONS_FALLBACK = '{"id":"D-2026-05-12-aftershock","source":"interview-loop","questionId":"Q-fixture","selectedOption":"A","summary":"Register patient intake term","effects":[{"kind":"ddd-register-term","term":"ReferralIntake","reason":"fixture cascade"},{"kind":"defer","reason":"fixture no follow-up"}],"aftershockDepth":0,"createdAt":"2026-05-12T00:00:00.000Z"}\n'


def fixture_payloads(root: Path) -> list[dict[str, Any]]:
    aftershock_decisions = root / ".lazy-harness" / "triggers" / "fixtures" / "aftershock" / "decisions.jsonl"
    return [
        {
            "name": "read-only-no-output",
            "payload": {"message_id": "parity-read-only", "recent_tool_calls": [{"name": "read", "args_preview": ".lazy-harness/spec/platform/hook-performance-measurement.md"}]},
            "expectOutput": False,
        },
        {
            "name": "real-sample-record-audit-read-only-no-output",
            "payload": {
                "message_id": "parity-real-sample-record-audit",
                "last_user_message": "지금 기록이 얼마나 쌓였는지 볼까?",
                "recent_tool_calls": [
                    {"name": "read", "args_preview": ".lazy-harness/planning/performance-optimization-plan.md"},
                    {"name": "agentgrep", "args_preview": "query=record-audit path=.lazy-harness"},
                ],
            },
            "expectOutput": False,
        },
        {
            "name": "bdd-natural-language-candidate-capture",
            "payload": {"message_id": "parity-bdd", "last_user_message": "사용자가 환자 목록 버튼을 클릭하면 환자 목록 화면으로 이동해야 합니다.", "recent_tool_calls": []},
            "expectOutput": False,
        },
        {
            "name": "option-gate-discipline-stop",
            "payload": {
                "assistant_response": "## Rule placement\n- Rule: release execution policy.\n- Scope: ambiguous\n- Confirmation: needs-option-gate\n\n선택해주세요:\nA. SSOT 기록 후 test release dispatch (Recommended)\n",
                "recent_tool_calls": [{"name": "Write", "args_preview": ".lazy-harness/ssot/release-sources.md"}],
            },
            "expectOutput": True,
            "expectHelperSuffix": "check-option-gate-discipline.sh",
            "expectContains": "Option gate discipline",
        },
        {
            "name": "record-before-session-history-stop",
            "payload": {"assistant_response": "기록된 계획을 찾아보겠습니다.", "recent_tool_calls": [{"name": "session_search", "args_preview": "계획"}]},
            "expectOutput": True,
            "expectHelperSuffix": "check-record-before-session-history.sh",
            "expectContains": "Record-before-session-history",
        },
        {
            "name": "analysis-discovery-capture-stop",
            "payload": {
                "assistant_response": "Analysis plan:\n1. DDD domain finding\n2. SDD contract finding\n3. BDD user flow finding\nBacklog: capture this later.",
                "recent_tool_calls": [{"name": "read", "args_preview": ".lazy-harness/spec/platform/hook-performance-measurement.md"}],
            },
            "expectOutput": True,
            "expectHelperSuffix": "check-analysis-discovery-capture.sh",
            "expectContains": "Analysis discovery capture gate",
        },
        {
            "name": "project-rule-placement-stop",
            "payload": {
                "assistant_response": "프로젝트 규칙을 .jcode/harness/20-project-rules.md에 추가하겠습니다.",
                "recent_tool_calls": [{"name": "Write", "args_preview": ".jcode/harness/20-project-rules.md"}],
            },
            "expectOutput": True,
            "expectHelperSuffix": "check-project-rule-placement.sh",
            "expectContains": "Project rule placement gate",
        },
        {
            "name": "lazy-cli-entrypoint-stop",
            "payload": {
                "assistant_response": "검증은 bun run lazy:test 명령으로 실행하겠습니다.",
                "recent_tool_calls": [],
            },
            "expectOutput": True,
            "expectHelperSuffix": "check-lazy-cli-entrypoint.sh",
            "expectContains": "Lazy CLI entrypoint gate",
        },
        {
            "name": "tdd-cross-verify-stop",
            "payload": {"recent_tool_calls": [{"name": "Edit", "args_preview": ".lazy-harness/triggers/fixtures/tdd-cross-verify/missing-test.ts"}]},
            "expectOutput": True,
            "expectHelperSuffix": "check-tdd-cross-verify.sh",
            "expectContains": "5d-3 TDD Cross-Verify Gate",
        },
        {
            "name": "layer-impact-observation-side-effect",
            "payload": {"recent_tool_calls": [{"name": "Edit", "args_preview": "src/patient/example.ts"}]},
            "expectValidationRows": 1,
        },
        {
            "name": "aftershock-stop",
            "payload": {"recent_tool_calls": [{"name": "Edit", "args_preview": ".lazy-harness/logs/decisions.jsonl"}]},
            "expectOutput": True,
            "expectHelperSuffix": "check-aftershock-reanalysis.sh",
            "expectContains": "5d-4 Aftershock Re-analysis",
            "decisionsFixture": str(aftershock_decisions),
            "decisionsFallback": AFTERSHOCK_DECISIONS_FALLBACK,
        },
        {
            "name": "unknown-full-fallback-no-output",
            "payload": {"message_id": "parity-unknown-no-output", "recent_tool_calls": [{"name": "bash", "args_preview": "pwd"}]},
            "expectOutput": False,
        },
    ]


def copy_host(root: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="lazy_lifecycle_parity_"))
    shutil.copytree(root / ".lazy-harness", tmp / ".lazy-harness", ignore=shutil.ignore_patterns(".cache", "state", "logs/hook-timings.jsonl"))
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=False)
    return tmp


def hook_body(stdout: str) -> str:
    if not stdout.strip():
        return ""
    try:
        return str(json.loads(stdout).get("inject", {}).get("body", ""))
    except Exception:
        return "__INVALID_INJECT_JSON__" + stdout


def prepare_env(host: Path, fixture: dict[str, Any], queue_name: str) -> dict[str, str]:
    queue = host / ".lazy-harness" / "questions" / queue_name
    validations = host / ".lazy-harness" / "logs" / f"{queue_name}.validations.jsonl"
    queue.unlink(missing_ok=True)
    validations.unlink(missing_ok=True)
    env = {
        **os.environ,
        "LAZY_HOST_ROOT": str(host),
        "LAZY_HARNESS_QUESTION_QUEUE": str(queue.relative_to(host)),
        "LAZY_HARNESS_VALIDATIONS_FILE": str(validations.relative_to(host)),
        "LAZY_HOOK_TIMING_LOG": str(host / ".lazy-harness" / "logs" / f"{queue_name}.timings.jsonl"),
    }
    if fixture.get("decisionsFixture"):
        source = Path(str(fixture["decisionsFixture"]))
        decisions = host / ".lazy-harness" / "logs" / f"{queue_name}.decisions.jsonl"
        decisions.parent.mkdir(parents=True, exist_ok=True)
        # Source path belongs to the original root. Re-map into the copied host.
        if source.is_absolute() and ".lazy-harness" in source.parts:
            rel_parts = source.parts[source.parts.index(".lazy-harness") + 1:]
            copied_source = host / ".lazy-harness" / Path(*rel_parts)
        else:
            copied_source = source
        if copied_source.exists():
            decisions_text = copied_source.read_text(encoding="utf-8")
        else:
            decisions_text = str(fixture.get("decisionsFallback") or "")
        decisions.write_text(decisions_text, encoding="utf-8")
        env["LAZY_HARNESS_DECISIONS_FILE"] = str(decisions.relative_to(host))
    return env


def read_validation_rows(host: Path, env: dict[str, str]) -> list[dict[str, Any]]:
    rel = env.get("LAZY_HARNESS_VALIDATIONS_FILE")
    if not rel:
        return []
    path = host / rel
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            row = {"__invalid__": line}
        if isinstance(row, dict):
            row.pop("id", None)
            row.pop("createdAt", None)
            row.pop("timestamp", None)
            row.pop("ts", None)
        rows.append(row)
    return rows


def run_fixture(root: Path, fixture: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(fixture["payload"], ensure_ascii=False)
    legacy_host = copy_host(root)
    shadow_host = copy_host(root)
    try:
        legacy_env = prepare_env(legacy_host, fixture, f"legacy-{fixture['name']}.xml")
        shadow_env = prepare_env(shadow_host, fixture, f"shadow-{fixture['name']}.xml")
        legacy = subprocess.run(
            [str(legacy_host / ".lazy-harness" / "hooks" / "lifecycle" / "on-response-completed.sh")],
            cwd=legacy_host,
            input=payload,
            text=True,
            capture_output=True,
            env=legacy_env,
            check=False,
        )
        shadow = subprocess.run(
            [str(shadow_host / ".lazy-harness" / "bin" / "lazy"), "lifecycle-check", "--format=json"],
            cwd=shadow_host,
            input=payload,
            text=True,
            capture_output=True,
            env=shadow_env,
            check=False,
        )
        legacy_validations = read_validation_rows(legacy_host, legacy_env)
        shadow_validations = read_validation_rows(shadow_host, shadow_env)
        legacy_body = hook_body(legacy.stdout).rstrip()
        shadow_json: dict[str, Any]
        try:
            shadow_json = json.loads(shadow.stdout)
        except Exception as exc:
            shadow_json = {"ok": False, "parseError": str(exc), "raw": shadow.stdout}
        shadow_body = str(shadow_json.get("firstOutput") or "").rstrip()
        issues: list[str] = []
        if legacy.returncode != 0:
            issues.append(f"legacy-exit-{legacy.returncode}")
        if shadow.returncode != 0:
            issues.append(f"shadow-exit-{shadow.returncode}")
        if bool(legacy_body) != bool(shadow_body):
            issues.append("output-presence-mismatch")
        if legacy_body != shadow_body:
            issues.append("output-body-mismatch")
        if legacy_validations != shadow_validations:
            issues.append("validation-side-effect-mismatch")
        if fixture.get("expectOutput") is not None and bool(shadow_body) != bool(fixture["expectOutput"]):
            issues.append("expected-output-mismatch")
        if fixture.get("expectValidationRows") is not None and len(shadow_validations) != int(fixture["expectValidationRows"]):
            issues.append("expected-validation-rows-mismatch")
        suffix = fixture.get("expectHelperSuffix")
        if suffix and not str(shadow_json.get("firstOutputHelper") or "").endswith(str(suffix)):
            issues.append("expected-helper-mismatch")
        contains = fixture.get("expectContains")
        if contains and str(contains) not in shadow_body:
            issues.append("expected-text-missing")
        return {
            "name": fixture["name"],
            "ok": not issues,
            "issues": issues,
            "legacyOutputEmitted": bool(legacy_body),
            "shadowOutputEmitted": bool(shadow_body),
            "firstOutputHelper": shadow_json.get("firstOutputHelper"),
            "fastPathReason": shadow_json.get("fastPathReason"),
            "selectedHelpers": len(shadow_json.get("selectedHelpers") or []),
            "skippedHelpers": len(shadow_json.get("skippedHelpers") or []),
            "legacyValidationRows": len(legacy_validations),
            "shadowValidationRows": len(shadow_validations),
        }
    finally:
        shutil.rmtree(legacy_host, ignore_errors=True)
        shutil.rmtree(shadow_host, ignore_errors=True)


def run(root: Path) -> dict[str, Any]:
    fixtures = fixture_payloads(root)
    results = [run_fixture(root, fixture) for fixture in fixtures]
    failures = [result for result in results if not result["ok"]]
    return {
        "ok": not failures,
        "mode": "lifecycle-parity-runner",
        "schemaVersion": "1.0",
        "root": str(root),
        "fixtures": len(results),
        "passed": len(results) - len(failures),
        "failed": len(failures),
        "results": results,
        "notes": [
            "Compares production response.completed hook output with lifecycle-check shadow output in fresh temp hosts.",
            "Compares validation side-effect rows after normalizing volatile IDs.",
            "This is Phase 2 safety coverage only; production hook replacement remains forbidden until parity is broad enough.",
        ],
    }


def render_md(result: dict[str, Any]) -> str:
    lines = ["# Lifecycle parity runner", ""]
    lines.append(f"- Root: `{result['root']}`")
    lines.append(f"- OK: {result['ok']}")
    lines.append(f"- Fixtures: {result['fixtures']}")
    lines.append(f"- Passed: {result['passed']}")
    lines.append(f"- Failed: {result['failed']}")
    lines.append("")
    lines.append("## Results")
    for item in result["results"]:
        lines.append(f"- {item['name']}: ok={item['ok']} helper={item.get('firstOutputHelper')} issues={item.get('issues')}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch compare legacy response hook with lifecycle-check shadow")
    parser.add_argument("--root", default=str(ROOT), help="source/host root")
    parser.add_argument("--format", choices=["json", "md", "markdown"], default="json")
    parser.add_argument("--fail-on-mismatch", action="store_true", help="exit 2 when any fixture mismatches")
    args = parser.parse_args()
    result = run(Path(args.root).resolve())
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_md(result))
    if args.fail_on_mismatch and not result["ok"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
