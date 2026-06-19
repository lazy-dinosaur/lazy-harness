#!/usr/bin/env python3
"""Lazy-Harness reproducible self-test.

Checks the framework-owned operational invariants defined by ADR 0022:
- every .lazy-harness XML file parses
- permanent JSONL logs parse line-by-line
- trigger fixtures produce DDD/SDD/BDD/SSOT candidates
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import py_compile
import re
import runpy
import subprocess
import sys
import tempfile
import time
import shutil
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(os.environ.get("LAZY_HOST_ROOT", pathlib.Path(__file__).resolve().parents[2])).resolve()
LAZY = ROOT / ".lazy-harness"
ACTIVE_SCOPE = "auto"


def doctor_scope_args() -> list[str]:
    return ["--scope", ACTIVE_SCOPE] if ACTIVE_SCOPE in {"framework", "host"} else []


def fail(message: str) -> None:
    print(f"✗ {message}")
    raise SystemExit(1)


INHERITED_ENV_KEYS_TO_CLEAR = (
    "LAZY_RUNTIME_ROOT",
    "LAZY_SHARED_ROOT",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_PREFIX",
    "GIT_QUARANTINE_PATH",
)


def env_without_lazy_runtime(**overrides: str) -> dict[str, str]:
    """Return a child-process env isolated from outer lazy/git hook context.

    Git hooks can export GIT_* variables that override cwd/-C in nested temp
    repositories. Strip inherited lazy runtime and git hook state first, then
    apply explicit fixture overrides so intentional sandbox roots still work.
    """
    env = dict(os.environ)
    for key in INHERITED_ENV_KEYS_TO_CLEAR:
        env.pop(key, None)
    env.update(overrides)
    return env


for _inherited_key in INHERITED_ENV_KEYS_TO_CLEAR:
    os.environ.pop(_inherited_key, None)


def runtime_open_gates_file(root: pathlib.Path) -> pathlib.Path:
    try:
        git_dir = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--absolute-git-dir"], env=env_without_lazy_runtime(), text=True, stderr=subprocess.DEVNULL).strip()
        base = pathlib.Path(git_dir)
    except Exception:  # noqa: BLE001
        base = root / ".lazy-harness" / ".gitless"
    return base / "lazy-harness" / "runtime" / "default" / "state" / "open-gates.json"


def check_doctor_smoke() -> None:
    command = ["python3", ".lazy-harness/scripts/doctor.py", "--profile", "smoke", *doctor_scope_args()]
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    # ADR 0026: doctor now prints "lazy-harness doctor ok (smoke, scope=<scope>)".
    if "lazy-harness doctor ok (smoke" not in completed.stdout:
        fail("doctor smoke did not report ok:\n" + completed.stdout)
    print("✓ doctor smoke ok")


def check_doctor_c17_negative() -> None:
    fixture = LAZY / "scripts" / f"__doctor_c17_negative_tmp_{os.getpid()}.py"
    forbidden_call = 'fe' + 'tch' + '("' + 'https' + '://api.' + 'figma' + '.com/v1/files/example")\n'
    fixture.write_text(forbidden_call, encoding="utf-8")
    try:
        env = env_without_lazy_runtime(LAZY_HARNESS_DOCTOR_INCLUDE_NEGATIVE="1")
        completed = subprocess.run(
            ["python3", ".lazy-harness/scripts/doctor.py", "--profile", "full", *doctor_scope_args()],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
        )
        combined = completed.stdout + completed.stderr
        if completed.returncode == 0:
            fail("doctor full should fail on C17 negative fixture")
        if "D06 C17 external dependency invariant failed" not in combined:
            fail("doctor full failed for the wrong reason:\n" + combined)
    finally:
        fixture.unlink(missing_ok=True)

    subprocess.run(["python3", ".lazy-harness/scripts/doctor.py", "--profile", "full", *doctor_scope_args()], cwd=ROOT, check=True, text=True, capture_output=True)
    print("✓ doctor C17 negative fixture ok")


def check_doctor_package_health() -> None:
    completed = subprocess.run(
        ["python3", ".lazy-harness/scripts/doctor.py", "--profile", "full", "--format", "json", *doctor_scope_args()],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(completed.stdout)
    results = {result.get("check_id"): result for result in payload.get("results", [])}
    d07 = results.get("D07")
    if not d07:
        fail("doctor full missing D07 package health result")
    if d07.get("status") not in {"ok", "warn"}:
        fail("doctor D07 should be ok or warn, got: " + json.dumps(d07, ensure_ascii=False))
    if d07.get("status") == "warn" and "environment" not in d07.get("message", ""):
        fail("doctor D07 warning should classify environment/package health: " + json.dumps(d07, ensure_ascii=False))
    d08 = results.get("D08")
    if not d08:
        fail("doctor full missing D08 unicode replacement result")
    if d08.get("status") not in {"ok", "warn"}:
        fail("doctor D08 should be ok or warn, got: " + json.dumps(d08, ensure_ascii=False))
    print(f"✓ doctor D07 package health {d07.get('status')}")


def check_package_health_generate_remediation_heuristic() -> None:
    """D07 should detect safe generated-artifact remediation commands before stopping."""
    ns = runpy.run_path(str(LAZY / "scripts" / "doctor.py"))
    find_generate_command = ns["find_generate_command"]
    should_try_generate = ns["should_try_generate"]

    pkg = {"scripts": {"db:generate": "prisma generate"}}
    command = find_generate_command(pkg, "")
    if command != ["bun", "run", "db:generate"]:
        fail(f"doctor generate command precedence changed: {command}")

    prisma_pkg = {"dependencies": {"@prisma/client": "latest", "prisma": "latest"}}
    fallback = find_generate_command(prisma_pkg, "error TS2305: @prisma/client has no exported member ActionVisibility")
    if fallback != ["bun", "x", "prisma", "generate"]:
        fail(f"doctor Prisma fallback generate command changed: {fallback}")

    if not should_try_generate('error TS2305: Module "@prisma/client" has no exported member ActionVisibility', [], prisma_pkg):
        fail("doctor should try generate for Prisma generated-client drift")
    if should_try_generate("error TS2322: Type string is not assignable to number", [], {}):
        fail("doctor should not try generate for unrelated app code drift")

    print("✓ package health generate remediation heuristic ok")


def check_xml() -> None:
    errors: list[str] = []
    for path in sorted(LAZY.rglob("*.xml")):
        try:
            ET.parse(path)
        except Exception as exc:  # noqa: BLE001 - surface parser detail
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    if errors:
        fail("XML parse errors:\n" + "\n".join(errors))
    print("✓ XML parse ok")


def check_jsonl() -> None:
    errors: list[str] = []
    for path in [LAZY / "logs" / "actions.jsonl", LAZY / "logs" / "decisions.jsonl", LAZY / "logs" / "validations.jsonl"]:
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}")
            continue
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path.relative_to(ROOT)}:{index}: {exc}")
    if errors:
        fail("JSONL parse errors:\n" + "\n".join(errors))
    print("✓ JSONL parse ok")


def check_schemas() -> None:
    """All *.schema.json under .lazy-harness/schemas/ must be valid JSON Schema draft-07
    headers with $schema / $id / title set. Prevents silent skip when a new schema is
    added without minimum metadata (Principle 9 Unified Result Schema discipline)."""
    schemas_dir = LAZY / "schemas"
    if not schemas_dir.exists():
        print("✓ schema metadata ok (no schemas dir)")
        return
    errors: list[str] = []
    count = 0
    for path in sorted(schemas_dir.rglob("*.schema.json")):
        count += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
            continue
        for key in ("$schema", "$id", "title"):
            if not data.get(key):
                errors.append(f"{path.relative_to(ROOT)}: missing required key {key!r}")
        schema_url = data.get("$schema") or ""
        if "json-schema.org" not in schema_url:
            errors.append(f"{path.relative_to(ROOT)}: $schema must point to json-schema.org, got {schema_url!r}")
    if errors:
        fail("schema metadata errors:\n" + "\n".join(errors))
    print(f"✓ schema metadata ok ({count} files)")


def run_trigger(layer: str) -> dict:
    command = [
        "bun",
        ".lazy-harness/triggers/code-change.ts",
        "--scope",
        ".lazy-harness/triggers/fixtures",
        "--layer",
        layer,
        "--format",
        "json",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


def run_trigger_scope(scope: str, layer: str = "all") -> dict:
    command = [
        "bun",
        ".lazy-harness/triggers/code-change.ts",
        "--scope",
        scope,
        "--layer",
        layer,
        "--format",
        "json",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


def run_lint_output_fixture(name: str) -> dict:
    command = [
        "bun",
        ".lazy-harness/triggers/lint-output.ts",
        "--input",
        f".lazy-harness/triggers/fixtures/lint-output/{name}.txt",
        "--format",
        "json",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


def run_interview_collect(queue: pathlib.Path, input_path: str = ".lazy-harness/triggers/fixtures/interview-loop/cross-layer-gap.json") -> dict:
    command = [
        "bun",
        ".lazy-harness/scripts/interview-loop.ts",
        "--mode",
        "collect",
        "--input",
        input_path,
        "--queue",
        str(queue.relative_to(ROOT)),
        "--format",
        "json",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


def run_interview_answer(queue: pathlib.Path, decisions: pathlib.Path, question_id: str, answer: str, apply: bool = False) -> dict:
    command = [
        "bun",
        ".lazy-harness/scripts/interview-loop.ts",
        "--mode",
        "answer",
        "--queue",
        str(queue.relative_to(ROOT)),
        "--decisions",
        str(decisions.relative_to(ROOT)),
        "--question-id",
        question_id,
        "--answer",
        answer,
        "--format",
        "json",
    ]
    if apply:
        command.append("--apply")
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


def run_tdd_cross_verify(files: list[str], queue: pathlib.Path | None = None, expect_code: int = 0) -> dict:
    command = [
        "bun",
        ".lazy-harness/scripts/tdd-cross-verify.ts",
        "--files",
        ",".join(files),
        "--format",
        "json",
    ]
    if queue is not None:
        command.extend(["--queue", str(queue.relative_to(ROOT))])
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != expect_code:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"tdd-cross-verify exit changed: expected {expect_code}, got {completed.returncode}")
    return json.loads(completed.stdout)



def run_affected_tests(files: list[str], queue: pathlib.Path | None = None, expect_code: int = 0) -> dict:
    command = [
        "bun",
        ".lazy-harness/scripts/affected-test-runner.ts",
        "--files",
        ",".join(files),
        "--format",
        "json",
    ]
    if queue is not None:
        command.extend(["--queue", str(queue.relative_to(ROOT))])
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != expect_code:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"affected-test-runner exit changed: expected {expect_code}, got {completed.returncode}")
    return json.loads(completed.stdout)

def run_aftershock_reanalysis(queue: pathlib.Path, decisions_path: str = ".lazy-harness/triggers/fixtures/aftershock/decisions.jsonl") -> dict:
    command = [
        "bun",
        ".lazy-harness/scripts/aftershock-reanalysis.ts",
        "--decisions",
        decisions_path,
        "--queue",
        str(queue.relative_to(ROOT)),
        "--format",
        "json",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


def run_knowledge_intake_fixture() -> dict:
    command = [
        "bun",
        ".lazy-harness/scripts/knowledge-intake.ts",
        "--fixture",
        "all",
        "--plan",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    return json.loads(completed.stdout)


def run_response_completed_hook(payload: dict, queue: pathlib.Path, decisions: pathlib.Path | None = None) -> str:
    validations = LAZY / "logs" / f"__tmp_hook_validations_{os.getpid()}.jsonl"
    validations.unlink(missing_ok=True)
    env = env_without_lazy_runtime(
        LAZY_HARNESS_QUESTION_QUEUE=str(queue.relative_to(ROOT)),
        LAZY_HARNESS_VALIDATIONS_FILE=str(validations.relative_to(ROOT)),
    )
    if decisions is not None:
        env["LAZY_HARNESS_DECISIONS_FILE"] = str(decisions.relative_to(ROOT))
    completed = subprocess.run(
        [".lazy-harness/hooks/lifecycle/on-response-completed.sh"],
        cwd=ROOT,
        env=env,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        if completed.returncode != 0:
            sys.stdout.write(completed.stdout)
            sys.stderr.write(completed.stderr)
            fail(f"response.completed hook exit changed: {completed.returncode}")
        return completed.stdout
    finally:
        validations.unlink(missing_ok=True)


def run_lifecycle_check_shadow(payload: dict, queue: pathlib.Path, decisions: pathlib.Path | None = None) -> dict:
    validations = LAZY / "logs" / f"__tmp_lifecycle_shadow_validations_{os.getpid()}.jsonl"
    validations.unlink(missing_ok=True)
    env = env_without_lazy_runtime(
        LAZY_HARNESS_QUESTION_QUEUE=str(queue.relative_to(ROOT)),
        LAZY_HARNESS_VALIDATIONS_FILE=str(validations.relative_to(ROOT)),
    )
    if decisions is not None:
        env["LAZY_HARNESS_DECISIONS_FILE"] = str(decisions.relative_to(ROOT))
    completed = subprocess.run(
        [".lazy-harness/scripts/lifecycle-check.py", "--format=json"],
        cwd=ROOT,
        env=env,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        if completed.returncode != 0:
            sys.stdout.write(completed.stdout)
            sys.stderr.write(completed.stderr)
            fail(f"lifecycle-check shadow exit changed: {completed.returncode}")
        return json.loads(completed.stdout)
    finally:
        validations.unlink(missing_ok=True)


def hook_inject_body(stdout: str) -> str:
    if not stdout.strip():
        return ""
    try:
        return json.loads(stdout).get("inject", {}).get("body", "")
    except json.JSONDecodeError:
        fail("response.completed hook did not emit inject JSON:\n" + stdout)
    return ""


def run_layer_completeness_helper(payload: dict) -> str:
    completed = subprocess.run(
        [".lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh", json.dumps(payload)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"layer completeness helper exit changed: {completed.returncode}")
    return completed.stdout


def run_analysis_discovery_capture_helper(payload: dict) -> str:
    completed = subprocess.run(
        [".lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh", json.dumps(payload)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"analysis discovery capture helper exit changed: {completed.returncode}")
    return completed.stdout


def run_project_rule_placement_helper(payload: dict) -> str:
    completed = subprocess.run(
        [".lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh", json.dumps(payload)],
        cwd=ROOT,
        env=env_without_lazy_runtime(),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"project rule placement helper exit changed: {completed.returncode}")
    return completed.stdout


def run_option_gate_discipline_helper(payload: dict) -> str:
    completed = subprocess.run(
        [".lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh", json.dumps(payload)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"option gate discipline helper exit changed: {completed.returncode}")
    return completed.stdout


def run_record_before_session_history_helper(payload: dict) -> str:
    completed = subprocess.run(
        [".lazy-harness/hooks/lifecycle/helpers/check-record-before-session-history.sh", json.dumps(payload)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"record-before-session-history helper exit changed: {completed.returncode}")
    return completed.stdout


def run_lazy_cli_entrypoint_helper(payload: dict) -> str:
    completed = subprocess.run(
        [".lazy-harness/hooks/lifecycle/helpers/check-lazy-cli-entrypoint.sh", json.dumps(payload)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"lazy CLI entrypoint helper exit changed: {completed.returncode}")
    return completed.stdout


def run_bdd_trigger_helper(payload: dict) -> str:
    completed = subprocess.run(
        [".lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh", json.dumps(payload)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"BDD trigger helper exit changed: {completed.returncode}")
    return completed.stdout


def check_interview_loop_collect() -> None:
    queue = LAZY / "questions" / f"__tmp_interview_open_{os.getpid()}.xml"
    queue.unlink(missing_ok=True)
    try:
        first = run_interview_collect(queue)
        if first.get("created") != 3 or first.get("existing") != 0 or first.get("totalOpen") != 3:
            fail("interview-loop first collect changed: " + json.dumps(first, ensure_ascii=False))
        ids = [question.get("id") for question in first.get("questions", [])]
        expected_ids = ["Q-ec56f39bb7555484", "Q-3e77e39bd09c434f", "Q-17029903de55218f"]
        if ids != expected_ids:
            fail(f"interview-loop question ids changed: expected {expected_ids}, got {ids}")
        ET.parse(queue)
        second = run_interview_collect(queue)
        if second.get("created") != 0 or second.get("existing") != 3 or second.get("totalOpen") != 3:
            fail("interview-loop dedupe changed: " + json.dumps(second, ensure_ascii=False))
    finally:
        queue.unlink(missing_ok=True)
    print("✓ 5d-1 interview-loop collect ok")


def check_interview_loop_answer() -> None:
    queue = LAZY / "questions" / f"__tmp_interview_answer_open_{os.getpid()}.xml"
    decisions = LAZY / "logs" / f"__tmp_interview_decisions_{os.getpid()}.jsonl"
    queue.unlink(missing_ok=True)
    decisions.unlink(missing_ok=True)
    try:
        collect = run_interview_collect(queue)
        question_id = collect["questions"][2]["id"]
        preview = run_interview_answer(queue, decisions, question_id, "A", apply=False)
        if preview.get("applied") is not False or not preview.get("warnings"):
            fail("interview-loop answer preview changed: " + json.dumps(preview, ensure_ascii=False))
        if decisions.exists():
            fail("interview-loop preview must not create decisions file")
        applied = run_interview_answer(queue, decisions, question_id, "A", apply=True)
        if applied.get("applied") is not True or not applied.get("decision"):
            fail("interview-loop answer apply changed: " + json.dumps(applied, ensure_ascii=False))
        root = ET.parse(queue).getroot()
        matched = [question for question in root.findall("question") if question.attrib.get("id") == question_id]
        if not matched or matched[0].attrib.get("status") != "answered" or not matched[0].attrib.get("decisionId"):
            fail("interview-loop answered status not persisted")
        decision_lines = [json.loads(line) for line in decisions.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(decision_lines) != 1 or decision_lines[0].get("source") != "interview-loop" or decision_lines[0].get("questionId") != question_id:
            fail("interview-loop decision log changed: " + json.dumps(decision_lines, ensure_ascii=False))
    finally:
        queue.unlink(missing_ok=True)
        decisions.unlink(missing_ok=True)
    print("✓ 5d-2 interview-loop answer ok")


def check_tdd_cross_verify() -> None:
    queue = LAZY / "questions" / f"__tmp_tdd_cross_verify_{os.getpid()}.xml"
    queue.unlink(missing_ok=True)
    try:
        missing = run_tdd_cross_verify([
            ".lazy-harness/triggers/fixtures/tdd-cross-verify/missing-test.ts",
        ], queue=queue, expect_code=2)
        if missing.get("ok") is not False or missing.get("forceGate") is not True or missing.get("failed") != 1:
            fail("tdd-cross-verify missing-test gate changed: " + json.dumps(missing, ensure_ascii=False))
        question = (missing.get("questions") or [{}])[0]
        if question.get("id") != "Q-22c6c7cf5a7620f1" or question.get("criterionId") != "5d-3" or question.get("source") != "tdd-cross-verify":
            fail("tdd-cross-verify question identity changed: " + json.dumps(question, ensure_ascii=False))
        root = ET.parse(queue).getroot()
        persisted = [entry for entry in root.findall("question") if entry.attrib.get("id") == "Q-22c6c7cf5a7620f1"]
        if not persisted or persisted[0].attrib.get("criterionId") != "5d-3":
            fail("tdd-cross-verify question was not persisted to queue")
        deduped = run_tdd_cross_verify([
            ".lazy-harness/triggers/fixtures/tdd-cross-verify/missing-test.ts",
        ], queue=queue, expect_code=0)
        if deduped.get("questions") != []:
            fail("tdd-cross-verify queue dedupe changed: " + json.dumps(deduped, ensure_ascii=False))
        if deduped.get("forceGate") is not False:
            fail("tdd-cross-verify dedup forceGate must be false to break ask-loop: " + json.dumps(deduped, ensure_ascii=False))
        covered = run_tdd_cross_verify([
            ".lazy-harness/triggers/fixtures/tdd-cross-verify/covered-feature.ts",
        ])
        if covered.get("ok") is not True or covered.get("forceGate") is not False or covered.get("passed") != 1:
            fail("tdd-cross-verify covered fixture changed: " + json.dumps(covered, ensure_ascii=False))
    finally:
        queue.unlink(missing_ok=True)
    print("✓ 5d-3 TDD cross-verify ok")


def check_layer_completeness_helper() -> None:
    """AGENTS §2.4 — TDD/regression records must not complete without layer judgement."""
    tdd = LAZY / "tests" / f"__tmp_layer_completeness_{os.getpid()}.md"
    try:
        tdd.write_text("# Regression only\n\nNo cross-layer judgement yet.\n", encoding="utf-8")
        payload = {"recent_tool_calls": [{"name": "Edit", "args_preview": str(tdd.relative_to(ROOT))}]}
        blocked = run_layer_completeness_helper(payload)
        if "Layer completeness gate" not in blocked or "SDD/BDD/SSOT/DDD" not in blocked:
            fail("layer completeness helper did not block TDD-only record:\n" + blocked)

        tdd.write_text(
            "# Regression with judgement\n\n"
            "## Layer completeness\n\n"
            "- SDD: 영향 없음\n- BDD: 영향 없음\n- SSOT: 영향 없음\n- DDD: 영향 없음\n",
            encoding="utf-8",
        )
        passed = run_layer_completeness_helper(payload)
        if passed.strip():
            fail("layer completeness helper should pass with explicit judgement:\n" + passed)

        paired = {
            "recent_tool_calls": [{
                "name": "Edit",
                "args_preview": f"{tdd.relative_to(ROOT)} .lazy-harness/spec/example.md",
            }]
        }
        paired_out = run_layer_completeness_helper(paired)
        if paired_out.strip():
            fail("layer completeness helper should pass when SDD is updated in same turn:\n" + paired_out)
    finally:
        tdd.unlink(missing_ok=True)
    print("✓ layer completeness helper ok")



def check_analysis_discovery_capture_helper() -> None:
    """ADR 0034 — non-trivial analysis/planning discoveries must be captured."""
    blocked_payload = {
        "assistant_response": (
            "I analyzed the redesign and found DDD, SDD, BDD, TDD, ADR, SSOT, and Planning impacts.\n"
            "Implementation plan:\n"
            "1. Update contracts.\n"
            "2. Add regression tests.\n"
            "3. Record backlog.\n"
        ),
        "recent_tool_calls": [],
    }
    blocked = run_analysis_discovery_capture_helper(blocked_payload)
    if "Analysis discovery capture gate" not in blocked or "DDD" not in blocked or "SSOT" not in blocked:
        fail("analysis discovery capture helper did not block uncaptured analysis:\n" + blocked)

    judgement_payload = {
        "assistant_response": (
            "## Discovery capture\n"
            "- DDD: none because no domain fact changed.\n"
            "- SDD: none because no contract changed.\n"
            "- BDD: none because no behavior changed.\n"
            "- TDD: none because no regression changed.\n"
            "- ADR: none because no decision changed.\n"
            "- SSOT: none because no source of truth changed.\n"
            "- Planning: none because no backlog remains.\n"
        ),
        "recent_tool_calls": [],
    }
    judgement = run_analysis_discovery_capture_helper(judgement_payload)
    if judgement.strip():
        fail("analysis discovery capture helper should pass with explicit judgement:\n" + judgement)

    planning_payload = {
        "assistant_response": blocked_payload["assistant_response"],
        "recent_tool_calls": [{
            "name": "Write",
            "args_preview": ".lazy-harness/planning/example-backlog.md",
        }],
    }
    planning = run_analysis_discovery_capture_helper(planning_payload)
    if planning.strip():
        fail("analysis discovery capture helper should pass when planning is updated:\n" + planning)

    candidate_payload = {
        "assistant_response": blocked_payload["assistant_response"],
        "recent_tool_calls": [{
            "name": "Edit",
            "args_preview": ".lazy-harness/knowledge/candidates.jsonl",
        }],
    }
    candidate = run_analysis_discovery_capture_helper(candidate_payload)
    if candidate.strip():
        fail("analysis discovery capture helper should pass when candidates are updated:\n" + candidate)

    print("✓ analysis discovery capture helper ok")


def check_project_rule_placement_helper() -> None:
    """Project-specific rules must route to .lazy-harness or explicit jcode-local judgement."""
    state_file = runtime_open_gates_file(ROOT)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    backup = state_file.read_text(encoding="utf-8") if state_file.exists() else None
    if state_file.exists():
        state_file.unlink()
    try:
        _check_project_rule_placement_helper_cases()
    finally:
        if backup is not None:
            state_file.write_text(backup, encoding="utf-8")
        elif state_file.exists():
            state_file.unlink()

    print("✓ project rule placement helper ok")


def _check_project_rule_placement_helper_cases() -> None:
    blocked_payload = {
        "assistant_response": (
            "프로젝트마다 규칙이 다르니까 이 프로젝트 규칙은 .jcode/harness/20-project-rules.md 에 추가하겠습니다."
        ),
        "message_id": "project-rule-test-blocked",
        "recent_tool_calls": [{
            "name": "Edit",
            "args_preview": ".jcode/harness/20-project-rules.md",
        }],
    }
    blocked = run_project_rule_placement_helper(blocked_payload)
    if "Project rule placement gate" not in blocked or "Rule placement" not in blocked:
        fail("project rule placement helper did not block uncategorized .jcode project rule:\n" + blocked)

    memory_blocked_payload = {
        "assistant_response": (
            "알겠어. 프로젝트 메모리에 저장해뒀어. 앞으로 bun wt new 후 Jcode cwd 를 새 worktree 로 옮길게."
        ),
        "message_id": "project-rule-test-memory",
        "recent_tool_calls": [{
            "name": "memory",
            "args": {
                "action": "remember",
                "category": "preference",
                "content": "HostApp worktree workflow: after creating a worktree with bun wt new, immediately switch Jcode cwd to the new worktree.",
                "scope": "project",
            },
        }],
    }
    memory_blocked = run_project_rule_placement_helper(memory_blocked_payload)
    if "Project rule placement gate" not in memory_blocked or "memory forget" not in memory_blocked:
        fail("project rule placement helper did not block project rule stored in Jcode memory:\n" + memory_blocked)

    loop_payload = {
        "last_user_message": "이 프로젝트 규칙은 .jcode가 아니라 SSOT에 기록해야 해.",
        "message_id": "project-rule-test-loop",
        "recent_tool_calls": [{
            "name": "Edit",
            "args_preview": ".jcode/harness/20-project-rules.md",
        }],
    }
    first_loop = run_project_rule_placement_helper(loop_payload)
    if "Project rule placement gate" not in first_loop:
        fail("project rule placement helper should emit first derived gate without assistant_response:\n" + first_loop)
    repeated_loop = run_project_rule_placement_helper(loop_payload)
    if repeated_loop.strip():
        fail("project rule placement helper should suppress duplicate same-turn derived gate:\n" + repeated_loop)
    self_reminder_echo_payload = {
        "last_user_message": (
            "STOP. Project rule placement gate: 프로젝트별 rule/correction 을 어디에 둘지 판정 없이 진행하면 안 됩니다.\n"
            "해야 할 일:\n"
            "  A. .lazy-harness/ssot/... shared project rule 로 기록\n"
            "필수 판단:\n"
            "  ## Rule placement\n"
        ),
        "message_id": "project-rule-self-reminder-echo",
        "recent_tool_calls": [],
    }
    self_reminder_echo = run_project_rule_placement_helper(self_reminder_echo_payload)
    if self_reminder_echo.strip():
        fail("project rule placement helper should ignore its own STOP reminder echoed as user input:\n" + self_reminder_echo)
    assistant_discussion_payload = {
        "assistant_response": (
            "STOP. Project rule placement gate 문구를 분석했지만, 실제로는 .jcode에 프로젝트 규칙을 기록하려고 합니다."
        ),
        "message_id": "project-rule-assistant-discussion-not-echo",
        "recent_tool_calls": [{"name": "Edit", "args_preview": ".jcode/harness/20-project-rules.md"}],
    }
    assistant_discussion = run_project_rule_placement_helper(assistant_discussion_payload)
    if "Project rule placement gate" not in assistant_discussion:
        fail("project rule placement helper should not suppress assistant discussion of STOP text outside last_user_message:\n" + assistant_discussion)
    new_turn_payload = dict(loop_payload)
    new_turn_payload["message_id"] = "project-rule-test-loop-new-turn"
    new_turn = run_project_rule_placement_helper(new_turn_payload)
    if "Project rule placement gate" not in new_turn:
        fail("project rule placement helper should re-fire on a new message_id:\n" + new_turn)

    shared_payload = {
        "assistant_response": "프로젝트 규칙을 shared SSOT 로 기록했습니다.",
        "recent_tool_calls": [{
            "name": "Write",
            "args_preview": ".lazy-harness/ssot/rule-sources.md",
        }],
    }
    shared = run_project_rule_placement_helper(shared_payload)
    if shared.strip():
        fail("project rule placement helper should pass when SSOT is updated:\n" + shared)

    local_payload = {
        "assistant_response": (
            "## Rule placement\n"
            "- Rule: local Jcode workflow preference.\n"
            "- Scope: jcode-local\n"
            "- Primary record: .jcode/harness/20-project-rules.md\n"
            "- Why not AGENTS.md: not framework-global.\n"
            "- Why not `.jcode`: it is intentionally local-only.\n"
            "- Confirmation: user-confirmed\n"
        ),
        "recent_tool_calls": [{
            "name": "Edit",
            "args_preview": ".jcode/harness/20-project-rules.md",
        }],
    }
    local = run_project_rule_placement_helper(local_payload)
    if local.strip():
        fail("project rule placement helper should pass with jcode-local judgement:\n" + local)

    planning_payload = {
        "assistant_response": "이 프로젝트 규칙 개선은 backlog 로 남겼습니다.",
        "recent_tool_calls": [{
            "name": "Write",
            "args_preview": ".lazy-harness/planning/project-rule-router.md",
        }],
    }
    planning = run_project_rule_placement_helper(planning_payload)
    if planning.strip():
        fail("project rule placement helper should pass when planning artifact is updated:\n" + planning)

    real_world_judgement_payload = {
        "assistant_response": (
            "Rule placement\n"
            "• Rule: HostApp PR descriptions must use Why, What, Task, Validation, then User-note-type / User-note when applicable.\n"
            "• Scope: team-policy\n"
            "• Primary record: .lazy-harness/ssot/pr-description-format.md\n"
            "• Why not AGENTS.md: This is a HostApp team PR workflow policy, not framework-global guidance.\n"
            "• Why not .jcode: .jcode is local/private Jcode memory only; canonical shared team policy belongs in .lazy-harness/ssot.\n"
            "• Confirmation: user-confirmed\n"
        ),
        "recent_tool_calls": [],
    }
    real_world_judgement = run_project_rule_placement_helper(real_world_judgement_payload)
    if real_world_judgement.strip():
        fail("project rule placement helper should pass real-world bullet/no-backtick judgement:\n" + real_world_judgement)

    non_applicable_judgement_payload = {
        "assistant_response": (
            "## Rule placement\n"
            "- Rule: 없음\n"
            "- Scope: non-applicable\n"
            "- Primary record: none\n"
            "- Confirmation: user-confirmed\n"
            "- Disposition: 기록하지 않음\n"
        ),
        "recent_tool_calls": [],
    }
    non_applicable_judgement = run_project_rule_placement_helper(non_applicable_judgement_payload)
    if non_applicable_judgement.strip():
        fail("project rule placement helper should pass non-applicable/no-record judgement:\n" + non_applicable_judgement)

    korean_noop_payload = {
        "assistant_response": "처리: 기록하지 않음. 확정된 프로젝트 규칙이 없어서 primary record 없음.",
        "recent_tool_calls": [],
    }
    korean_noop = run_project_rule_placement_helper(korean_noop_payload)
    if korean_noop.strip():
        fail("project rule placement helper false-positive on Korean no-record disposition:\n" + korean_noop)

    duplicate_product_rule_payload = {
        "assistant_response": (
            "Product rule placement\n"
            "• Rule: 치료기록지 배정/재배정 알림은 { actionKind: 'treatmentDocument' } metadata를 보존해야 하며 클릭 시 TreatmentDocumentModal이 바로 열려야 한다.\n"
            "• Scope: host-project\n"
            "• Primary record: .lazy-harness/ssot/patient-treatment-surfaces.md\n"
            "• Why not AGENTS.md: 제품 동작/도메인 규칙이지 agent 운영 규칙이 아니다.\n"
            "• Why not .jcode: 개인 로컬 규칙이 아니라 팀/프로젝트 공유 product behavior다.\n"
            "• Confirmation: user-observed regression, user-confirmed\n\n"
            "Related product rule placement\n"
            "• Rule: 치료기록지 배정/재배정 알림은 { actionKind: 'treatmentDocument' } metadata를 보존해야 하며 클릭 시 TreatmentDocumentModal이 바로 열려야 한다.\n"
            "• Scope: host-project\n"
            "• Primary record: .lazy-harness/ssot/patient-treatment-surfaces.md\n"
            "• Why not AGENTS.md: 제품 동작/도메인 규칙이지 agent 운영 규칙이 아니다.\n"
            "• Why not .jcode: 개인 로컬 규칙이 아니라 팀/프로젝트 공유 product behavior다.\n"
            "• Confirmation: user-observed regression, user-confirmed\n"
        ),
        "recent_tool_calls": [],
    }
    duplicate_product_rule = run_project_rule_placement_helper(duplicate_product_rule_payload)
    if "Rule placement duplication" not in duplicate_product_rule:
        fail("project rule placement helper should flag duplicate product rule placement blocks:\n" + duplicate_product_rule)

    args_payload = {
        "assistant_response": "PR 규격 SSOT를 recognized edit로 갱신했습니다.",
        "recent_tool_calls": [{
            "name": "edit",
            "args": {"file_path": ".lazy-harness/ssot/pr-description-format.md"},
        }],
    }
    args_out = run_project_rule_placement_helper(args_payload)
    if args_out.strip():
        fail("project rule placement helper should pass .lazy-harness path from structured args:\n" + args_out)

    casual_payload = {
        "assistant_response": "AGENTS.md and .jcode exist in the project.",
        "recent_tool_calls": [],
    }
    casual = run_project_rule_placement_helper(casual_payload)
    if casual.strip():
        fail("project rule placement helper false-positive on casual mention:\n" + casual)

    status_report_payload = {
        "assistant_response": (
            "framework gate는 두 프로젝트에 적용됨. HostApp release dispatch 정책은 "
            ".lazy-harness/ssot/release-branch-policy.md record에 이미 있음. "
            "host-app-b는 release script가 없어 적용 대상이 아님."
        ),
        "recent_tool_calls": [],
    }
    status_report = run_project_rule_placement_helper(status_report_payload)
    if status_report.strip():
        fail("project rule placement helper false-positive on existing-record status report:\n" + status_report)

def check_option_gate_discipline_helper() -> None:
    """Option gates must stop for the user and must not self-select Recommended."""
    plain_gate_payload = {
        "assistant_response": (
            "## Rule placement\n"
            "- Rule: release execution policy.\n"
            "- Scope: ambiguous\n"
            "- Confirmation: needs-option-gate\n\n"
            "선택해주세요:\n"
            "A. SSOT 기록 후 test release dispatch (Recommended)\n"
            "B. SSOT 기록 후 --watch 포함 dispatch\n"
            "C. dry-run first\n"
            "D. cancel\n"
        ),
        "recent_tool_calls": [],
    }
    plain_gate = run_option_gate_discipline_helper(plain_gate_payload)
    if plain_gate.strip():
        fail("option gate discipline helper should allow a plain ask-once gate:\n" + plain_gate)

    write_after_gate_payload = {
        "assistant_response": plain_gate_payload["assistant_response"],
        "recent_tool_calls": [{
            "name": "Write",
            "args_preview": ".lazy-harness/ssot/release-sources.md",
        }],
    }
    write_after_gate = run_option_gate_discipline_helper(write_after_gate_payload)
    if "Option gate discipline" not in write_after_gate:
        fail("option gate discipline helper should block write after unresolved gate:\n" + write_after_gate)

    exec_after_gate_payload = {
        "assistant_response": plain_gate_payload["assistant_response"],
        "recent_tool_calls": [{
            "name": "bash",
            "args_preview": "bun release test --force --with-notes",
        }],
    }
    exec_after_gate = run_option_gate_discipline_helper(exec_after_gate_payload)
    if "Option gate discipline" not in exec_after_gate:
        fail("option gate discipline helper should block command execution after unresolved gate:\n" + exec_after_gate)

    self_select_payload = {
        "assistant_response": (
            "## Rule placement\n"
            "- Rule: release execution policy.\n"
            "- Confirmation: needs-option-gate\n\n"
            "진행 선택: A. SSOT 기록 후 test release dispatch (Recommended)\n"
            "SSOT 기록 완료했습니다. 이제 dispatch 하겠습니다. Confirmation: user-confirmed"
        ),
        "recent_tool_calls": [],
    }
    self_select = run_option_gate_discipline_helper(self_select_payload)
    if "Option gate discipline" not in self_select:
        fail("option gate discipline helper should block self-selected Recommended path:\n" + self_select)

    inferred_payload = {
        "assistant_response": (
            "## Rule placement\n"
            "- Rule: existing release policy.\n"
            "- Confirmation: inferred-from-record\n"
            "기존 SSOT 근거로 게이트 없이 진행합니다."
        ),
        "recent_tool_calls": [],
    }
    inferred = run_option_gate_discipline_helper(inferred_payload)
    if inferred.strip():
        fail("option gate discipline helper should pass non-gated inferred judgement:\n" + inferred)

    print("✓ option gate discipline helper ok")


def check_bdd_trigger_loop_suppression() -> None:
    """BDD helper captures pending candidates silently and never repeats asks.

    BDD scenario detection is record/candidate intake, not implementation approval.
    The helper must not inject A/B/C/D prompts for the same pending scenario across
    turns. Instead it appends one deduped row to
    `.lazy-harness/knowledge/candidates.jsonl` for later user-confirmed promotion.
    """
    candidates_file = ROOT / ".lazy-harness" / "knowledge" / "candidates.jsonl"
    state_file = runtime_open_gates_file(ROOT)
    candidates_file.parent.mkdir(parents=True, exist_ok=True)
    candidates_backup = candidates_file.read_text(encoding="utf-8") if candidates_file.exists() else None
    state_backup = state_file.read_text(encoding="utf-8") if state_file.exists() else None
    if candidates_file.exists():
        candidates_file.unlink()
    if state_file.exists():
        state_file.unlink()
    try:
        first_payload = {
            "last_user_message": "사용자가 환자 목록 버튼을 클릭하면 환자 목록 화면으로 이동해야 합니다.",
            "message_id": "test-msg-turn-A",
            "recent_tool_calls": [],
        }
        first = run_bdd_trigger_helper(first_payload)
        if first.strip():
            fail("BDD trigger helper should silently capture candidate, not inject gate:\n" + first)

        if not candidates_file.exists():
            fail("BDD trigger helper should append candidates.jsonl row")
        rows = [json.loads(line) for line in candidates_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        bdd_rows = [row for row in rows if row.get("source") == "lifecycle-bdd-trigger" and row.get("candidateType") == "bdd-scenario"]
        if len(bdd_rows) != 1:
            fail("BDD trigger helper should append exactly one BDD candidate row, got " + str(len(bdd_rows)))
        if bdd_rows[0].get("promotionPolicy", "").find("explicit user confirmation") < 0:
            fail("BDD candidate row should preserve user-confirmed promotion policy")

        repeated_same_turn = run_bdd_trigger_helper(first_payload)
        if repeated_same_turn.strip():
            fail("BDD trigger helper should stay silent for duplicate same-turn candidate:\n" + repeated_same_turn)

        new_turn_payload = dict(first_payload)
        new_turn_payload["message_id"] = "test-msg-turn-B"
        repeated_new_turn = run_bdd_trigger_helper(new_turn_payload)
        if repeated_new_turn.strip():
            fail("BDD trigger helper should stay silent for same pending candidate in a new turn:\n" + repeated_new_turn)

        rows_after = [json.loads(line) for line in candidates_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        bdd_after = [row for row in rows_after if row.get("source") == "lifecycle-bdd-trigger" and row.get("candidateType") == "bdd-scenario"]
        if len(bdd_after) != 1:
            fail("BDD trigger helper should dedupe pending candidate across turns, got " + str(len(bdd_after)))
    finally:
        if candidates_backup is not None:
            candidates_file.write_text(candidates_backup, encoding="utf-8")
        elif candidates_file.exists():
            candidates_file.unlink()
        if state_backup is not None:
            state_file.write_text(state_backup, encoding="utf-8")
        elif state_file.exists():
            state_file.unlink()
    print("✓ BDD trigger silent candidate capture ok")


def check_bdd_trigger_avoids_runtime_tsmorph() -> None:
    """BDD last-message trigger must not require ts-morph in installed hosts."""
    source = (LAZY / "triggers" / "code-change.ts").read_text(encoding="utf-8")
    runtime_imports = [line for line in source.splitlines() if "from 'ts-morph'" in line and not line.strip().startswith("import type")]
    if runtime_imports:
        fail("code-change.ts must not runtime-import ts-morph; BDD host trigger must work without host ts-morph")
    detector_runtime_imports = [
        line for line in source.splitlines()
        if "from './detectors/" in line and not line.strip().startswith("import type") and "./detectors/bdd" not in line
    ]
    if detector_runtime_imports:
        fail("code-change.ts must not runtime-import non-BDD detectors on the BDD path")
    if "if (opts.layer !== 'bdd')" not in source or "loadTsMorph()" not in source:
        fail("code-change.ts should lazy-load ts-morph only for non-BDD layers")
    if "loadNonBddDetectors()" not in source:
        fail("code-change.ts should lazy-load non-BDD detectors only for non-BDD layers")
    print("✓ BDD trigger ts-morph isolation ok")


def check_record_before_session_history_helper() -> None:
    """Recorded plans/rules must search .lazy-harness before session history."""
    blocked_payload = {
        "assistant_response": "기록해둔 기능패널 계획을 찾아보겠습니다.",
        "recent_tool_calls": [{
            "name": "session_search",
            "query": "feature panel plan",
        }],
    }
    blocked = run_record_before_session_history_helper(blocked_payload)
    if "Record-before-session-history gate" not in blocked:
        fail("record-before-session-history helper should block session_search-first lookup:\n" + blocked)

    record_first_payload = {
        "assistant_response": "기록해둔 기능패널 계획을 찾아보겠습니다.",
        "recent_tool_calls": [
            {
                "name": "agentgrep",
                "args_preview": "Search .lazy-harness/planning for feature panel notes",
            },
            {
                "name": "session_search",
                "query": "feature panel plan",
            },
        ],
    }
    record_first = run_record_before_session_history_helper(record_first_payload)
    if record_first.strip():
        fail("record-before-session-history helper should pass record-first lookup:\n" + record_first)

    chat_only_payload = {
        "assistant_response": "사용자가 대화 로그만 요청했으므로 이전 세션 대화만 찾겠습니다.",
        "recent_tool_calls": [{
            "name": "session_search",
            "query": "exact transcript phrase",
        }],
    }
    chat_only = run_record_before_session_history_helper(chat_only_payload)
    if chat_only.strip():
        fail("record-before-session-history helper should pass explicit chat-only lookup:\n" + chat_only)

    unrelated_payload = {
        "assistant_response": "이전 대화에서 정확한 표현을 찾아보겠습니다.",
        "recent_tool_calls": [{"name": "session_search", "query": "exact words"}],
    }
    unrelated = run_record_before_session_history_helper(unrelated_payload)
    if unrelated.strip():
        fail("record-before-session-history helper should not block non-record chat recall:\n" + unrelated)

    print("✓ record-before-session-history helper ok")




def check_pre_push_uses_canonical_lazy_cli() -> None:
    """Git pre-push must not call stale package-script lazy:test."""
    hook = (LAZY / "hooks" / "pre-push.sh").read_text(encoding="utf-8")
    forbidden = ["bun run lazy:test", "bun run lazy:doctor", "HAS_NPM_SCRIPT", "suggestedFix: run bun run lazy:test"]
    leaked = [token for token in forbidden if token in hook]
    if leaked:
        fail("pre-push hook still references stale lazy package-script path: " + ", ".join(leaked))
    required = [
        'env -u GIT_DIR -u GIT_WORK_TREE "$LAZY/bin/lazy" test',
        'env -u GIT_DIR -u GIT_WORK_TREE "$LAZY/scripts/self-test.py"',
        'LAZY_HOST_ROOT="$REPO_ROOT"',
        "git-action.lockdir",
        "same worktree already has a lazy-harness git action running",
        "IS_FRAMEWORK_REPO",
        "framework/framework-contract.md",
        "planning/phase-5-plan.xml",
        "standalone lazy-harness source repo",
    ]
    missing = [token for token in required if token not in hook]
    if missing:
        fail("pre-push hook missing canonical lazy CLI/fallback path: " + ", ".join(missing))
    print("✓ pre-push canonical lazy CLI ok")


def check_lazy_cli_entrypoint_helper() -> None:
    """Current lazy CLI is .lazy-harness/bin/lazy, not stale package scripts."""
    blocked_payload = {
        "assistant_response": "lazy test 실패를 재현하려고 bun run lazy:test 를 실행했는데 package.json에 스크립트가 없어 실패했습니다.",
        "recent_tool_calls": [{"name": "bash", "args_preview": "bun run lazy:test"}],
    }
    blocked = run_lazy_cli_entrypoint_helper(blocked_payload)
    if "Lazy CLI entrypoint gate" not in blocked or ".lazy-harness/bin/lazy test" not in blocked:
        fail("lazy CLI entrypoint helper should block stale package-script usage:\n" + blocked)

    canonical_payload = {
        "assistant_response": ".lazy-harness/bin/lazy version 후 .lazy-harness/bin/lazy test 로 재현합니다.",
        "recent_tool_calls": [{"name": "bash", "args_preview": ".lazy-harness/bin/lazy test"}],
    }
    canonical = run_lazy_cli_entrypoint_helper(canonical_payload)
    if canonical.strip():
        fail("lazy CLI entrypoint helper should pass canonical CLI usage:\n" + canonical)

    corrective_payload = {
        "assistant_response": "`bun run lazy:test` 는 낡은 호출이라 쓰지 말고 대신 .lazy-harness/bin/lazy test 를 사용합니다.",
        "recent_tool_calls": [],
    }
    corrective = run_lazy_cli_entrypoint_helper(corrective_payload)
    if corrective.strip():
        fail("lazy CLI entrypoint helper should pass corrective stale-command explanation:\n" + corrective)

    print("✓ lazy CLI entrypoint helper ok")


def check_fast_validation_tier_cli() -> None:
    """`lazy check` is a fast static tier and must not replace full regression."""
    sdd = LAZY / "spec" / "platform" / "fast-validation-tier.md"
    tdd = LAZY / "tests" / "fast-validation-tier.md"
    script = LAZY / "scripts" / "lazy-check.py"
    for path in (sdd, tdd, script):
        if not path.exists():
            fail(f"fast validation tier missing file: {path.relative_to(ROOT)}")
    sdd_text = sdd.read_text(encoding="utf-8")
    tdd_text = tdd.read_text(encoding="utf-8")
    lazy_cli = (LAZY / "bin" / "lazy").read_text(encoding="utf-8")
    for expected in (
        "lazy check",
        "not full regression",
        "does not replace `.lazy-harness/bin/lazy test`",
        "fullRegression: false",
    ):
        if expected not in sdd_text and expected not in tdd_text:
            fail("fast validation tier records missing invariant: " + expected)
    if 'check)' not in lazy_cli or 'lazy-check.py' not in lazy_cli or 'check [--files F1,F2,...]' not in lazy_cli:
        fail("lazy CLI missing check dispatcher/help contract")
    manifest_text = (LAZY / "manifests" / "init-categories.json").read_text(encoding="utf-8")
    for expected in ("spec/platform/fast-validation-tier.md", "tests/fast-validation-tier.md"):
        if expected not in manifest_text:
            fail("init categories missing fast validation tier sync record: " + expected)
    py_compile.compile(str(script), doraise=True)

    positive = subprocess.run(
        [
            str(LAZY / "bin" / "lazy"),
            "check",
            "--files",
            ".lazy-harness/fixtures/project-map-v2/example-node.json",
            "--format=json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(ROOT)),
    )
    if positive.returncode != 0:
        fail("lazy check positive fixture failed:\n" + positive.stdout + positive.stderr)
    positive_result = json.loads(positive.stdout)
    if not positive_result.get("ok") or positive_result.get("fullRegression") is not False:
        fail("lazy check positive fixture must report ok and fullRegression=false: " + positive.stdout)
    if ".lazy-harness/fixtures/project-map-v2/example-node.json" not in positive_result.get("files", []):
        fail("lazy check positive fixture did not include explicit file: " + positive.stdout)

    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-check-fixture-", dir=ROOT))
    try:
        bad_json = temp / "bad.json"
        bad_json.write_text("{ bad json\n", encoding="utf-8")
        negative = subprocess.run(
            [
                str(LAZY / "bin" / "lazy"),
                "check",
                "--files",
                str(bad_json.relative_to(ROOT)),
                "--format=json",
                "--no-diff-check",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(ROOT)),
        )
        if negative.returncode == 0:
            fail("lazy check malformed JSON should fail")
        negative_result = json.loads(negative.stdout)
        if negative_result.get("ok") is not False or not any(item.get("check") == "json-parse" for item in negative_result.get("errors", [])):
            fail("lazy check malformed JSON should report json-parse: " + negative.stdout)
    finally:
        shutil.rmtree(temp, ignore_errors=True)

    outside = subprocess.run(
        [
            str(LAZY / "bin" / "lazy"),
            "check",
            "--files",
            "/tmp/lazy-check-outside.json",
            "--format=json",
            "--no-diff-check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(ROOT)),
    )
    if outside.returncode == 0:
        fail("lazy check outside-root file should fail")
    outside_result = json.loads(outside.stdout)
    if not any(item.get("check") == "root-bound" for item in outside_result.get("errors", [])):
        fail("lazy check outside-root file should report root-bound: " + outside.stdout)

    print("✓ fast validation tier CLI ok")


def check_bounded_validation_governor_cli() -> None:
    """`lazy validate` keeps validation explicit, bounded, and release-gated."""
    sdd = LAZY / "spec" / "platform" / "bounded-validation-governor.md"
    tdd = LAZY / "tests" / "bounded-validation-governor.md"
    script = LAZY / "scripts" / "validation-governor.py"
    for path in (sdd, tdd, script):
        if not path.exists():
            fail(f"bounded validation governor missing file: {path.relative_to(ROOT)}")
    py_compile.compile(str(script), doraise=True)

    lazy_cli = (LAZY / "bin" / "lazy").read_text(encoding="utf-8")
    if "validate [--plan=fast|standard|release]" not in lazy_cli or "validation-governor.py" not in lazy_cli:
        fail("lazy CLI missing validate dispatcher/help contract")

    manifest_text = (LAZY / "manifests" / "init-categories.json").read_text(encoding="utf-8")
    for expected in ("spec/platform/bounded-validation-governor.md", "tests/bounded-validation-governor.md"):
        if expected not in manifest_text:
            fail("init categories missing bounded validation sync record: " + expected)

    help_text = subprocess.check_output([str(LAZY / "bin" / "lazy"), "help"], cwd=ROOT, text=True)
    if "validate [--plan=fast|standard|release]" not in help_text:
        fail("lazy help should list validate command")

    env = env_without_lazy_runtime(
        LAZY_HOST_ROOT=str(ROOT),
        LAZY_VALIDATE_PROGRESS="1",
        LAZY_VALIDATE_EVIDENCE_CACHE="0",
    )
    fast = subprocess.run(
        [
            str(LAZY / "bin" / "lazy"),
            "validate",
            "--plan",
            "fast",
            "--files",
            ".lazy-harness/fixtures/project-map-v2/example-node.json",
            "--format=json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if fast.returncode != 0:
        fail("lazy validate fast plan failed:\n" + fast.stdout + fast.stderr)
    fast_result = json.loads(fast.stdout)
    if fast_result.get("plan") != "fast" or fast_result.get("bounded") is not True or fast_result.get("fullRegression") is not False:
        fail("lazy validate fast output changed: " + fast.stdout)
    fast_steps = fast_result.get("steps", [])
    if len(fast_steps) != 1 or fast_steps[0].get("status") != "passed" or fast_steps[0].get("kind") != "fast-static":
        fail("lazy validate fast should run exactly one fast-static step: " + fast.stdout)
    progress_lines = [line for line in fast.stderr.splitlines() if line.startswith("JCODE_PROGRESS ")]
    if len(progress_lines) < 3:
        fail("lazy validate fast should emit progress rows to stderr without corrupting stdout JSON: " + fast.stderr)
    try:
        progress_payloads = [json.loads(line.removeprefix("JCODE_PROGRESS ")) for line in progress_lines]
    except json.JSONDecodeError as exc:
        fail("lazy validate progress row is not JSON: " + str(exc) + "\n" + fast.stderr)
    if not any(payload.get("message") == "Running fast-static-check" for payload in progress_payloads):
        fail("lazy validate progress should include step start message: " + fast.stderr)
    if not any(payload.get("message") == "passed: fast-static-check" for payload in progress_payloads):
        fail("lazy validate progress should include step completion message: " + fast.stderr)

    fast_no_progress = subprocess.run(
        [
            str(LAZY / "bin" / "lazy"),
            "validate",
            "--plan",
            "fast",
            "--progress=off",
            "--files",
            ".lazy-harness/fixtures/project-map-v2/example-node.json",
            "--format=json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if fast_no_progress.returncode != 0:
        fail("lazy validate fast --progress=off failed:\n" + fast_no_progress.stdout + fast_no_progress.stderr)
    json.loads(fast_no_progress.stdout)
    if "JCODE_PROGRESS" in fast_no_progress.stderr:
        fail("lazy validate --progress=off should suppress progress stderr: " + fast_no_progress.stderr)

    release_blocked = subprocess.run(
        [str(LAZY / "bin" / "lazy"), "validate", "--plan", "release", "--format=json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if release_blocked.returncode == 0:
        fail("lazy validate release should require --allow-release")
    release_blocked_result = json.loads(release_blocked.stdout)
    if not any("release plan requires --allow-release" in error for error in release_blocked_result.get("errors", [])):
        fail("lazy validate release block missing opt-in error: " + release_blocked.stdout)

    release_dry = subprocess.run(
        [str(LAZY / "bin" / "lazy"), "validate", "--plan", "release", "--dry-run", "--format=json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if release_dry.returncode != 0:
        fail("lazy validate release dry-run failed:\n" + release_dry.stdout + release_dry.stderr)
    release_dry_result = json.loads(release_dry.stdout)
    if release_dry_result.get("dryRun") is not True or release_dry_result.get("fullRegression") is not True:
        fail("lazy validate release dry-run should plan full regression without executing: " + release_dry.stdout)
    if not any(step.get("status") == "planned" and step.get("kind") == "full-regression" for step in release_dry_result.get("steps", [])):
        fail("lazy validate release dry-run missing planned full-regression step: " + release_dry.stdout)

    standard_dry = subprocess.run(
        [str(LAZY / "bin" / "lazy"), "validate", "--plan", "standard", "--dry-run", "--format=json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if standard_dry.returncode != 0:
        fail("lazy validate standard dry-run failed:\n" + standard_dry.stdout + standard_dry.stderr)
    standard_dry_result = json.loads(standard_dry.stdout)
    standard_full_steps = [step for step in standard_dry_result.get("steps", []) if step.get("kind") == "full-regression"]
    if len(standard_full_steps) != 1 or standard_dry_result.get("fullRegression") is not True:
        fail("lazy validate standard dry-run should contain exactly one full-regression step: " + standard_dry.stdout)

    too_long = subprocess.run(
        [str(LAZY / "bin" / "lazy"), "validate", "--plan", "fast", "--max-seconds=3601", "--format=json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if too_long.returncode == 0:
        fail("lazy validate should reject over-hour budgets")
    too_long_result = json.loads(too_long.stdout)
    if not any("cannot exceed 3600" in error for error in too_long_result.get("errors", [])):
        fail("lazy validate over-hour budget error changed: " + too_long.stdout)

    exhausted = subprocess.run(
        [str(LAZY / "bin" / "lazy"), "validate", "--plan", "fast", "--max-seconds=0", "--format=json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if exhausted.returncode == 0:
        fail("lazy validate zero budget should fail without running steps")
    exhausted_result = json.loads(exhausted.stdout)
    if not any(step.get("status") == "skipped" and step.get("reason") == "deadline-exhausted" for step in exhausted_result.get("steps", [])):
        fail("lazy validate zero budget should skip with deadline-exhausted: " + exhausted.stdout)

    governor = runpy.run_path(str(script), run_name="lazy_validation_governor_import")
    old_cache_env = os.environ.get("LAZY_VALIDATE_EVIDENCE_CACHE")
    try:
        os.environ.pop("LAZY_VALIDATE_EVIDENCE_CACHE", None)
        if not governor["evidence_cache_enabled"]("auto"):
            fail("validation evidence cache should be enabled by default")
        if governor["evidence_cache_enabled"]("off"):
            fail("validation evidence cache should be disabled by --evidence-cache=off")
        os.environ["LAZY_VALIDATE_EVIDENCE_CACHE"] = "0"
        if governor["evidence_cache_enabled"]("auto"):
            fail("validation evidence cache should be disabled by LAZY_VALIDATE_EVIDENCE_CACHE=0")
    finally:
        if old_cache_env is None:
            os.environ.pop("LAZY_VALIDATE_EVIDENCE_CACHE", None)
        else:
            os.environ["LAZY_VALIDATE_EVIDENCE_CACHE"] = old_cache_env
    fake_step = governor["ValidationStep"]("full-self-test", "full-regression", ["fake-lazy", "test"])
    fake_result = governor["StepResult"]("full-self-test", "full-regression", ["fake-lazy", "test"], "passed", exitCode=0, elapsedSeconds=1.25)
    fingerprint_a = {
        "head": "HEAD-A",
        "diffHash": "diff-A",
        "statusHash": "status-A",
        "untrackedHash": "untracked-A",
        "harnessHash": "harness-A",
    }
    fingerprint_b = {**fingerprint_a, "harnessHash": "harness-B"}
    cache_runtime = pathlib.Path(tempfile.mkdtemp(prefix="validate-cache-"))
    old_runtime = os.environ.get("LAZY_RUNTIME_ROOT")
    try:
        os.environ["LAZY_RUNTIME_ROOT"] = str(cache_runtime)
        for volatile in (
            ".lazy-harness/state/validation-evidence-cache.json",
            ".lazy-harness/logs/validations.jsonl",
            ".lazy-harness/generated/implementation-index.json",
            ".lazy-harness/scripts/__pycache__/validation-governor.pyc",
        ):
            if not governor["is_volatile_harness_path"](volatile):
                fail("validation evidence fingerprint should ignore volatile harness path: " + volatile)
        for canonical in (
            ".lazy-harness/scripts/validation-governor.py",
            ".lazy-harness/spec/platform/bounded-validation-governor.md",
        ):
            if governor["is_volatile_harness_path"](canonical):
                fail("validation evidence fingerprint should keep canonical harness path: " + canonical)
        key_a = governor["evidence_key"](fake_step, "auto", fingerprint_a)
        key_b = governor["evidence_key"](fake_step, "auto", fingerprint_b)
        if key_a == key_b:
            fail("validation evidence key should change when conservative fingerprint changes")
        if governor["cached_step_result"](fake_step, key_a, governor["load_cache"]()) is not None:
            fail("validation evidence cache should miss before store")
        governor["store_step_result"](fake_step, key_a, fingerprint_a, fake_result)
        cache_file = cache_runtime / "state" / "validation-evidence-cache.json"
        if not cache_file.exists():
            fail("validation evidence cache should be written under LAZY_RUNTIME_ROOT/state")
        reused = governor["cached_step_result"](fake_step, key_a, governor["load_cache"]())
        if reused is None or reused.status != "reused" or reused.reason != "valid cached full-regression evidence" or not reused.evidenceKey:
            fail("validation evidence cache should return reused full-regression evidence")
        if governor["cached_step_result"](fake_step, key_b, governor["load_cache"]()) is not None:
            fail("validation evidence cache should not reuse across different conservative fingerprints")
    finally:
        if old_runtime is None:
            os.environ.pop("LAZY_RUNTIME_ROOT", None)
        else:
            os.environ["LAZY_RUNTIME_ROOT"] = old_runtime
        shutil.rmtree(cache_runtime, ignore_errors=True)

    ignored = subprocess.run(
        ["git", "check-ignore", "-q", ".lazy-harness/state/validation-evidence-cache.json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if ignored.returncode != 0:
        fail("default validation evidence cache path should be ignored by active git ignore rules")

    print("✓ bounded validation governor CLI ok")


def check_skill_create_cli() -> None:
    """Custom project skill generator creates wrappers, optional scripts, and metadata."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy_skill_create_"))
    try:
        (temp / ".lazy-harness" / "knowledge").mkdir(parents=True)
        command = [
            "bun",
            ".lazy-harness/scripts/skill-create.ts",
            "create",
            "release-workflow",
            "--target",
            str(temp),
            "--description",
            "Release workflow helper",
            "--usage",
            "bun release test",
            "--script",
            "run.sh",
        ]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            fail("skill-create command failed:\nSTDOUT:\n" + completed.stdout + "\nSTDERR:\n" + completed.stderr)

        skill = temp / ".jcode" / "skills" / "release-workflow" / "SKILL.md"
        script = temp / ".jcode" / "skills" / "release-workflow" / "scripts" / "run.sh"
        log = temp / ".lazy-harness" / "knowledge" / "skills.jsonl"
        if not skill.exists() or not script.exists() or not log.exists():
            fail("skill-create did not create expected files")
        skill_text = skill.read_text(encoding="utf-8")
        if not skill_text.startswith("---\nname: release-workflow") or "Generated by lazy-harness" not in skill_text:
            fail("generated SKILL.md frontmatter/marker changed:\n" + skill_text)
        script_text = script.read_text(encoding="utf-8")
        if not script_text.startswith("#!/usr/bin/env bash") or "Generated by lazy-harness" not in script_text:
            fail("generated script shebang/marker changed:\n" + script_text)
        entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(entries) != 1 or entries[0].get("skillName") != "release-workflow" or entries[0].get("scriptPath") != ".jcode/skills/release-workflow/scripts/run.sh":
            fail("skills.jsonl metadata changed: " + json.dumps(entries, ensure_ascii=False))

        user_owned = temp / ".jcode" / "skills" / "manual-skill" / "SKILL.md"
        user_owned.parent.mkdir(parents=True)
        user_owned.write_text("# user owned\n", encoding="utf-8")
        blocked = subprocess.run(
            ["bun", ".lazy-harness/scripts/skill-create.ts", "create", "manual-skill", "--target", str(temp)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if blocked.returncode != 3 or "Refusing to overwrite user-owned file" not in blocked.stderr:
            fail("skill-create should refuse user-owned skill overwrite:\n" + blocked.stdout + blocked.stderr)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ custom skill create CLI ok")

def check_jcode_wiring_pointer_only() -> None:
    """Generated .jcode project-rules file must not invite host-rule bodies."""
    source = (LAZY / "scripts" / "jcode-wiring.ts").read_text(encoding="utf-8")
    required = [
        "pointer-only by default",
        "Do not store host/team rule bodies here",
        ".lazy-harness/ssot/rule-sources.md",
        "Scope: jcode-local",
        "migrateProjectRulesPointerOnly",
        "20-project-rules.pre-pointer-only-migration.md",
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("jcode wiring template missing pointer-only guard phrases: " + json.dumps(missing, ensure_ascii=False))
    forbidden = [
        "Add project-specific workflow notes here",
        "Add project-specific discoveries in `.jcode/harness/20-project-rules.md`",
    ]
    leaked = [phrase for phrase in forbidden if phrase in source]
    if leaked:
        fail("jcode wiring template still invites rule-body pollution: " + json.dumps(leaked, ensure_ascii=False))
    print("✓ jcode wiring pointer-only template ok")


def check_jcode_wiring_repairs_stale_defaults() -> None:
    """Markerless old generated .jcode defaults must be archived and refreshed."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-jcode-wiring-"))
    try:
        (temp / ".lazy-harness").mkdir(parents=True)
        shutil.copy2(LAZY / "AGENTS.md", temp / ".lazy-harness" / "AGENTS.md")
        (temp / ".jcode" / "harness").mkdir(parents=True)
        (temp / ".jcode" / "hooks").mkdir(parents=True)

        (temp / ".jcode" / "AGENTS.md").write_text(
            "# Private Jcode Harness\n\n"
            "This directory is Lazydino's private project-local harness for Jcode.\n"
            "experimental-lazy-harness /harness-doctor Phase 5 ADR 0007 C1~C16\n",
            encoding="utf-8",
        )
        (temp / ".jcode" / "config.toml").write_text(
            "# Project-local Jcode harness config.\n"
            "[prompt]\nignore_project_agents = true\n"
            "private_instructions = [\"rules/*.md\", \"monorepo/*/AGENTS.md\", \"missing/*.md\",\"AGENTS.md\"]\n"
            "[[hooks.commands]]\nevent = \"session.stop\"\ncommand = \".jcode/hooks/test-session-stop.sh\"\n",
            encoding="utf-8",
        )
        (temp / ".jcode" / "harness" / "05-lazy-harness.md").write_text(
            "# Lazy-Harness AI 행동 양식\n\n## 2. 4 단계 흐름 (작업 시작 ~ 종료)\n",
            encoding="utf-8",
        )
        (temp / ".jcode" / "harness" / "10-routing-policy.md").write_text(
            "# Jcode Agent Routing Policy\n\nUse the configured Jcode agent profiles intentionally.\n"
            "## Model/persona guidance\nConcrete implementation, backend edits, command execution, and validation loops\n",
            encoding="utf-8",
        )
        (temp / ".jcode" / "hooks" / "check-bash.sh").write_text(
            "#!/usr/bin/env bash\necho custom-user-owned-hook\n",
            encoding="utf-8",
        )
        for skill_name in ["lazy-init", "lazy-sync"]:
            skill_dir = temp / ".jcode" / "skills" / skill_name
            skill_dir.mkdir(parents=True)
            skill_dir.joinpath("SKILL.md").write_text(
                f"---\nname: {skill_name}\n---\n\n# {skill_name}\n\n"
                "Do not edit generated framework files directly in the host; use lazy update/sync.\n"
                "See framework-contract.md and /harness-update.\n",
                encoding="utf-8",
            )

        code = (
            "import { installJcodeWiring } from './.lazy-harness/scripts/jcode-wiring.ts';"
            f"installJcodeWiring({{ targetRoot: {json.dumps(str(temp))}, quiet: true }});"
        )
        completed = subprocess.run(["bun", "-e", code], cwd=ROOT, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            fail("jcode wiring repair import/run failed:\n" + completed.stdout + completed.stderr)

        generated_marker = "Generated by lazy-harness. Local edits below this line make the file user-owned."
        refreshed = [
            temp / ".jcode" / "AGENTS.md",
            temp / ".jcode" / "config.toml",
            temp / ".jcode" / "harness" / "10-routing-policy.md",
        ]
        for path in refreshed:
            content = path.read_text(encoding="utf-8")
            if generated_marker not in content:
                fail(f"stale markerless generated default was not refreshed with marker: {path}")

        instruction = temp / ".jcode" / "harness" / "05-lazy-harness.md"
        if instruction.is_symlink():
            fail("05-lazy-harness should be pointer-only regular file, not symlink")
        content = instruction.read_text(encoding="utf-8")
        if generated_marker not in content:
            fail("05-lazy-harness pointer-only file missing generated marker")
        if "Lazy-Harness Pointer" not in content or "pointer-only" not in content:
            fail("05-lazy-harness did not refresh to pointer-only instruction")
        if "4 단계 흐름" in content or "Default = 모름" in content:
            fail("05-lazy-harness pointer-only file duplicated full lazy-harness grammar")

        archive = temp / ".jcode" / "archive"
        archived_names = {p.name for p in archive.iterdir()} if archive.exists() else set()
        required_archives = {
            "AGENTS.md.pre-generated-marker",
            "config.toml.pre-generated-marker",
            "05-lazy-harness.md.pre-pointer-only",
            "10-routing-policy.md.pre-generated-marker",
        }
        missing_archives = sorted(required_archives - archived_names)
        if missing_archives:
            fail("jcode stale repair did not archive old defaults: " + json.dumps(missing_archives, ensure_ascii=False))
        skill_archives = sorted(p.name for p in archive.iterdir() if p.name.startswith("SKILL.md.pre-generated-marker"))
        if len(skill_archives) < 2:
            fail("jcode stale repair overwrote colliding SKILL.md archives: " + json.dumps(skill_archives, ensure_ascii=False))

        custom_hook = (temp / ".jcode" / "hooks" / "check-bash.sh").read_text(encoding="utf-8")
        if "custom-user-owned-hook" not in custom_hook:
            fail("jcode repair overwrote a markerless custom user-owned hook")
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ jcode stale default repair ok")


def check_jcode_wiring_repairs_markerless_bash_hook_default() -> None:
    """Markerless generated bash hook defaults must be refreshed, not treated as user-owned."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-jcode-bash-hook-"))
    try:
        (temp / ".lazy-harness").mkdir(parents=True)
        shutil.copy2(LAZY / "AGENTS.md", temp / ".lazy-harness" / "AGENTS.md")
        (temp / ".jcode" / "hooks").mkdir(parents=True)
        (temp / ".jcode" / "hooks" / "check-bash.sh").write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "payload=$(cat || true)\n"
            "python3 - <<'PY'\n"
            "print('Refusing rm -rf /')\n"
            "print('Refusing filesystem creation on block device')\n"
            "PY\n",
            encoding="utf-8",
        )

        code = (
            "import { installJcodeWiring } from './.lazy-harness/scripts/jcode-wiring.ts';"
            f"installJcodeWiring({{ targetRoot: {json.dumps(str(temp))}, quiet: true }});"
        )
        completed = subprocess.run(["bun", "-e", code], cwd=ROOT, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            fail("jcode wiring bash hook repair import/run failed:\n" + completed.stdout + completed.stderr)

        hook = (temp / ".jcode" / "hooks" / "check-bash.sh").read_text(encoding="utf-8")
        if "Generated by lazy-harness" not in hook or "Refusing raw disk overwrite" not in hook or "check-rule-action-boundary.py" in hook:
            fail("markerless generated bash hook was not refreshed with safety-only wiring:\n" + hook)
        archive = temp / ".jcode" / "archive"
        archived_names = {p.name for p in archive.iterdir()} if archive.exists() else set()
        if "check-bash.sh.pre-generated-marker" not in archived_names:
            fail("markerless generated bash hook repair did not archive previous hook: " + json.dumps(sorted(archived_names), ensure_ascii=False))
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ jcode markerless bash hook repair ok")


def check_jcode_wiring_removes_rejected_layer2_block() -> None:
    """Rejected hard-gate experiment block must be removed from user-owned configs."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-jcode-rejected-layer2-"))
    try:
        (temp / ".lazy-harness").mkdir(parents=True)
        shutil.copy2(LAZY / "AGENTS.md", temp / ".lazy-harness" / "AGENTS.md")
        (temp / ".jcode").mkdir(parents=True)
        config = temp / ".jcode" / "config.toml"
        config.write_text(
            "# user-owned config\n"
            "[prompt]\n"
            "custom_local_flag = true\n\n"
            "# BEGIN lazy-harness mandatory Layer 2 force-gates\n"
            "[[hooks.commands]]\n"
            "event = \"tool.execute.before\"\n"
            "tool = \"edit\"\n"
            "command = \".lazy-harness/hooks/lifecycle/on-tool-execute-before.sh\"\n"
            "blocking = true\n"
            "timeout_ms = 3000\n"
            "# END lazy-harness mandatory Layer 2 force-gates\n\n"
            "[hooks]\n"
            "enabled = true\n",
            encoding="utf-8",
        )
        code = (
            "import { installJcodeWiring } from './.lazy-harness/scripts/jcode-wiring.ts';"
            f"installJcodeWiring({{ targetRoot: {json.dumps(str(temp))}, quiet: true }});"
        )
        completed = subprocess.run(["bun", "-e", code], cwd=ROOT, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            fail("jcode rejected Layer 2 cleanup import/run failed:\n" + completed.stdout + completed.stderr)
        updated = config.read_text(encoding="utf-8")
        if "custom_local_flag = true" not in updated:
            fail("rejected Layer 2 cleanup overwrote user-owned config content:\n" + updated)
        if "mandatory Layer 2 force-gates" in updated or 'tool = "edit"' in updated:
            fail("rejected Layer 2 cleanup left hard-gate block behind:\n" + updated)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ jcode rejected Layer 2 block cleanup ok")


def check_pi_package_layout_and_contract() -> None:
    """Pi package must expose native package resources and bridge lazy lifecycle hooks."""
    pkg_root = ROOT / "packages" / "lazy-harness-pi"
    manifest = pkg_root / "package.json"
    extension = pkg_root / "extensions" / "lazy-harness" / "index.ts"
    prompt = pkg_root / "prompts" / "lazy-harness.md"
    readme = pkg_root / "README.md"
    wrapper = LAZY / "scripts" / "pi-package.ts"
    lazy_entrypoint = LAZY / "bin" / "lazy"
    for path in [manifest, extension, prompt, readme, wrapper, lazy_entrypoint]:
        if not path.exists():
            fail(f"Pi package missing required file: {path.relative_to(ROOT)}")

    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("name") != "@lazy-dinosaur/lazy-harness-pi":
        fail("Pi package manifest has unexpected name")
    if "pi-package" not in data.get("keywords", []):
        fail("Pi package manifest missing pi-package keyword")
    pi_manifest = data.get("pi") if isinstance(data.get("pi"), dict) else {}
    for key, expected in {"extensions": "./extensions", "skills": "./skills", "prompts": "./prompts"}.items():
        values = pi_manifest.get(key)
        if not isinstance(values, list) or expected not in values:
            fail(f"Pi package manifest missing pi.{key} entry {expected!r}")

    pi_settings = ROOT / ".pi" / "settings.json"
    if pi_settings.exists():
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", ".pi/settings.json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if tracked.returncode == 0:
            fail("Pi project-local settings must never be committed; .pi/settings.json is tracked")
        settings_text = pi_settings.read_text(encoding="utf-8")
        if "../packages/lazy-harness-pi" not in settings_text:
            fail("Existing untracked .pi/settings.json must only attach the source-local lazy-harness-pi package")
        exclude = ROOT / ".git" / "info" / "exclude"
        if exclude.exists() and ".pi/" not in exclude.read_text(encoding="utf-8"):
            fail("Existing untracked .pi/settings.json requires .pi/ in .git/info/exclude to avoid teammate contamination")

    extension_text = extension.read_text(encoding="utf-8")
    required_phrases = [
        "before_agent_start",
        "tool_call",
        "tool_result",
        "on-message-received.sh",
        "on-tool-execute-before.sh",
        "recent_tool_calls",
        "rememberToolCall",
        "block: true",
        "REMINDER. Harness-first search/read debt before response.",
        "LAZY_HARNESS_INVOKER",
        "pi.registerCommand(\"lazy-map\"",
        "pi.registerCommand(\"lazy-doctor\"",
        "pi.registerCommand(\"lazy-test\"",
        "pi.registerCommand(\"lazy-import-antigravity-mcp\"",
        "import-antigravity-mcp.ts",
        "normalizePiTool",
        "cmd",
        "terminal",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in extension_text]
    if missing:
        fail("Pi package extension missing bridge contract phrases: " + json.dumps(missing, ensure_ascii=False))
    readme_text = readme.read_text(encoding="utf-8")
    for phrase in [
        "Global install for all projects",
        "Project-local install for this repo only",
        "Recommended wrapper commands",
        ".lazy-harness/bin/lazy pi install --local",
        ".lazy-harness/bin/lazy pi install --global",
        ".lazy-harness/bin/lazy pi smoke",
        "The package is not installed by default after a clean reset",
        "pi install /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --no-approve",
        "pi install -l /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --approve",
    ]:
        if phrase not in readme_text:
            fail("Pi package README missing clean install guidance: " + phrase)

    lazy_text = lazy_entrypoint.read_text(encoding="utf-8")
    for phrase in [
        "pi install|remove|list|smoke|doctor",
        "pi-package.ts",
    ]:
        if phrase not in lazy_text:
            fail("lazy CLI entrypoint missing Pi wrapper dispatch phrase: " + phrase)

    wrapper_text = wrapper.read_text(encoding="utf-8")
    for phrase in [
        "Usage: lazy pi <command>",
        "install --local|--global",
        "remove --local|--global",
        "smoke [--dry-run]",
        "doctor [--no-smoke]",
        "npm/standalone publishing is intentionally out of scope",
        "The source package path and target repo are intentionally separate",
        "LAZY_PI_TARGET_REPO",
        "LAZY_PI_SOURCE_ROOT",
        "--target-repo",
        "sourceRoot",
        "targetRepo",
        "ensureLocalPiIgnored",
        "localPiGitExclude",
        "pi install",
        "pi remove",
        "pi list",
        "pi -e",
        "--no-approve",
        "--approve",
        "packages/lazy-harness-pi",
    ]:
        if phrase not in wrapper_text:
            fail("Pi wrapper script missing contract phrase: " + phrase)

    for args, expected_command in [
        (["install", "--local", "--dry-run", "--format=json"], ["pi", "install", str(pkg_root), "-l", "--approve"]),
        (["install", "--global", "--dry-run", "--format=json"], ["pi", "install", str(pkg_root), "--no-approve"]),
        (["remove", "--local", "--dry-run", "--format=json"], ["pi", "remove", str(pkg_root), "-l", "--approve"]),
        (["smoke", "--dry-run", "--format=json"], ["pi", "-e", str(pkg_root), "--help"]),
    ]:
        completed = subprocess.run(
            ["bun", ".lazy-harness/scripts/pi-package.ts", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=env_without_lazy_runtime(),
        )
        if completed.returncode != 0:
            fail("Pi wrapper dry-run command failed: " + " ".join(args) + "\n" + completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        if payload.get("result", {}).get("command") != expected_command:
            fail("Pi wrapper dry-run command mismatch: " + completed.stdout)
        if payload.get("sourceRoot") != str(ROOT) or payload.get("packagePath") != str(pkg_root):
            fail("Pi wrapper source/package path mismatch: " + completed.stdout)
        if args[0] == "install" and "targetRepo" not in payload:
            fail("Pi wrapper install dry-run must report targetRepo: " + completed.stdout)

    doctor_completed = subprocess.run(
        ["bun", ".lazy-harness/scripts/pi-package.ts", "doctor", "--no-smoke", "--format=json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env_without_lazy_runtime(),
    )
    if doctor_completed.returncode != 0:
        fail("Pi wrapper doctor --no-smoke should not fail in environments without Pi:\n" + doctor_completed.stdout + doctor_completed.stderr)
    doctor_payload = json.loads(doctor_completed.stdout)
    if doctor_payload.get("smoke") is not None or "doctor/smoke never mutate Pi settings" not in doctor_payload.get("note", ""):
        fail("Pi wrapper doctor --no-smoke contract changed: " + doctor_completed.stdout)

    temp_cwd = pathlib.Path(tempfile.mkdtemp(prefix="lazy-pi-wrapper-cwd-"))
    try:
        for command in [
            [str(ROOT / ".lazy-harness" / "bin" / "lazy"), "pi", "install", "--local", "--dry-run", "--format=json"],
            ["bun", str(wrapper), "install", "--local", "--dry-run", "--format=json"],
        ]:
            env = env_without_lazy_runtime()
            # Pre-commit runs lazy test from an already-lazy environment. A
            # nested absolute lazy invocation and a direct pi-package.ts run must
            # still target their own cwd, not a stale parent invocation cwd.
            env["LAZY_INVOCATION_CWD"] = str(ROOT)
            env.pop("LAZY_PI_TARGET_REPO", None)
            completed = subprocess.run(
                command,
                cwd=temp_cwd,
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            if completed.returncode != 0:
                fail("Pi wrapper cwd-independent dry-run failed: " + " ".join(command) + "\n" + completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            if payload.get("sourceRoot") != str(ROOT) or payload.get("packagePath") != str(pkg_root) or payload.get("targetRepo") != str(temp_cwd) or payload.get("result", {}).get("command") != ["pi", "install", str(pkg_root), "-l", "--approve"]:
                fail("Pi wrapper cwd-independent package path mismatch: " + completed.stdout)
    finally:
        shutil.rmtree(temp_cwd, ignore_errors=True)

    target_repo = pathlib.Path(tempfile.mkdtemp(prefix="lazy-pi-target-repo-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=target_repo, text=True, capture_output=True, check=True)
        completed = subprocess.run(
            [str(ROOT / ".lazy-harness" / "bin" / "lazy"), "pi", "install", "--local", "--dry-run", "--target-repo", str(target_repo), "--format=json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=env_without_lazy_runtime(),
        )
        if completed.returncode != 0:
            fail("Pi wrapper explicit target-repo dry-run failed:\n" + completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        exclude_path = subprocess.run(["git", "-C", str(target_repo), "rev-parse", "--git-path", "info/exclude"], text=True, capture_output=True, check=True).stdout.strip()
        expected_exclude = str((target_repo / exclude_path).resolve())
        if payload.get("sourceRoot") != str(ROOT) or payload.get("targetRepo") != str(target_repo.resolve()) or payload.get("localPiGitExclude", {}).get("path") != expected_exclude:
            fail("Pi wrapper explicit target-repo/source-root isolation mismatch: " + completed.stdout)
    finally:
        shutil.rmtree(target_repo, ignore_errors=True)

    expected_skills = ["lazy-init", "lazy-doctor", "lazy-sync", "lazy-update", "lazy-test", "lazy-impl-map-migrate"]
    for skill in expected_skills:
        skill_file = pkg_root / "skills" / skill / "SKILL.md"
        if not skill_file.exists():
            fail(f"Pi package missing skill wrapper: {skill_file.relative_to(ROOT)}")
        content = skill_file.read_text(encoding="utf-8")
        if "name:" not in content or skill not in content:
            fail(f"Pi package skill wrapper lacks expected frontmatter/content: {skill}")
        if skill == "lazy-impl-map-migrate":
            for phrase in [
                "Guided LLM-assisted implementation-map migration",
                ".lazy-harness/bin/lazy impl-map --format=json",
                ".lazy-harness/bin/lazy graph-hygiene --format=json",
                "Do not bulk rewrite host records blindly",
                "Do not rewrite `knowledge/graph.jsonl` wholesale",
                "Default mode is bounded autopilot mode",
                "choose the next clear Recommended batch automatically",
                "Manual option-gate mode remains available",
                "present a 3-5 option gate and stop",
                "automatically continue with the next clear Recommended batch",
                "no default numeric batch limit",
                "until needs-map is complete",
                "Stop on validation failure, needs-review, ignored/tracked file uncertainty, missing source/test evidence",
                "graph wholesale cleanup pressure",
                "user-specified max batch limit reached",
                "exact stop reason",
                "OMP compatibility work is intentionally after this guided migration skill exists",
            ]:
                if phrase not in content:
                    fail("Pi package lazy-impl-map-migrate skill missing phrase: " + phrase)

    importer = pkg_root / "scripts" / "import-antigravity-mcp.ts"
    fixture = pkg_root / "fixtures" / "antigravity-mcp-config.jsonc"
    for path in [importer, fixture]:
        if not path.exists():
            fail(f"Pi package missing Antigravity MCP importer artifact: {path.relative_to(ROOT)}")
    importer_text = importer.read_text(encoding="utf-8")
    for phrase in ["serverUrl", "authProviderType", "google_credentials", "bearerTokenEnv", "disabledTools", "excludeTools", "mcp_oauth_tokens", "--apply", "--dry-run"]:
        if phrase not in importer_text:
            fail("Pi Antigravity MCP importer missing phrase: " + phrase)
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-pi-antigravity-mcp-"))
    try:
        target = temp / "pi-mcp.json"
        target.write_text(json.dumps({"mcpServers": {"existing": {"command": "node"}}, "imports": ["claude-code"]}), encoding="utf-8")
        completed = subprocess.run(
            ["bun", str(importer), "--source", str(fixture), "--target", str(target), "--prefix", "ag-", "--apply"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=env_without_lazy_runtime(),
        )
        if completed.returncode != 0:
            fail("Pi Antigravity MCP importer fixture command failed:\n" + completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        if sorted(report.get("imported", [])) != ["ag-gcp-adc", "ag-local-db", "ag-remote-oauth"]:
            fail("Pi Antigravity MCP importer imported unexpected servers: " + completed.stdout)
        if not any("google_credentials converted" in item.get("warning", "") for item in report.get("warnings", [])):
            fail("Pi Antigravity MCP importer did not report google_credentials bridge warning: " + completed.stdout)
        written = json.loads(target.read_text(encoding="utf-8"))
        servers = written.get("mcpServers", {})
        expected_remote_url = "http" + "://127.0.0.1:39391/mcp/"
        if servers.get("ag-remote-oauth", {}).get("url") != expected_remote_url:
            fail("Pi Antigravity MCP importer failed serverUrl->url conversion: " + json.dumps(servers.get("ag-remote-oauth"), ensure_ascii=False))
        if servers.get("ag-remote-oauth", {}).get("excludeTools") != ["dangerous_tool"]:
            fail("Pi Antigravity MCP importer failed disabledTools->excludeTools conversion")
        if servers.get("ag-gcp-adc", {}).get("auth") != "bearer" or servers.get("ag-gcp-adc", {}).get("bearerTokenEnv") != "ANTIGRAVITY_MCP_AG_GCP_ADC_ACCESS_TOKEN":
            fail("Pi Antigravity MCP importer failed google_credentials bearerTokenEnv conversion: " + json.dumps(servers.get("ag-gcp-adc"), ensure_ascii=False))
        if "ag-disabled-one" in servers:
            fail("Pi Antigravity MCP importer should skip disabled servers by default")
    finally:
        shutil.rmtree(temp, ignore_errors=True)

    runtime_smoke = pathlib.Path(tempfile.mkdtemp(prefix="lazy-pi-read-debt-smoke-"))
    try:
        smoke = runtime_smoke / "pi-read-debt-smoke.ts"
        smoke.write_text(
            "import lazyHarnessPi from " + json.dumps(str(extension)) + ";\n"
            "const handlers = new Map();\n"
            "const commands = new Map();\n"
            "const pi = { on(e,h){handlers.set(e,h)}, registerCommand(n,o){commands.set(n,o)}, async exec(){return {stdout:'',stderr:'',exitCode:0}} };\n"
            "lazyHarnessPi(pi);\n"
            "const ctx={cwd:" + json.dumps(str(ROOT)) + ", signal:undefined, ui:{notify(){}}};\n"
            "const before=await handlers.get('before_agent_start')({prompt:'testdb instance start', systemPrompt:'base'},ctx);\n"
            "if(!before?.systemPrompt?.includes('REMINDER. Harness-first')) throw new Error('no reminder');\n"
            "const cases=[\n"
            " ['write',{toolName:'write', input:{file_path:'tmp.txt',content:'x'}}],\n"
            " ['bash',{toolName:'bash', input:{command:'nohup bun scripts/dev-cli.ts --test --instance x &'}}],\n"
            " ['cmd',{toolName:'cmd', input:{command:'nohup bun scripts/dev-cli.ts --test --instance x &'}}],\n"
            " ['terminal',{toolName:'terminal', input:{text:'nohup bun scripts/dev-cli.ts --test --instance x &'}}],\n"
            " ['batch-bash',{toolName:'batch', input:{tool_calls:[{tool:'bash',parameters:{command:'nohup bun scripts/dev-cli.ts --test --instance x &'}}]}}],\n"
            "];\n"
            "for (const [name, ev] of cases) { const r=await handlers.get('tool_call')({toolCallId:name,...ev},ctx); if(!r?.block) throw new Error(name+' not blocked'); }\n"
            "console.log('pi shell alias read-debt smoke ok');\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            ["bun", str(smoke)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=env_without_lazy_runtime(),
        )
        if completed.returncode != 0:
            fail("Pi shell alias read-debt smoke failed:\n" + completed.stdout + completed.stderr)
    finally:
        shutil.rmtree(runtime_smoke, ignore_errors=True)

    isolation_smoke = pathlib.Path(tempfile.mkdtemp(prefix="lazy-pi-root-isolation-"))
    try:
        root_a = isolation_smoke / "repo-a"
        root_b = isolation_smoke / "repo-b"
        for root in [root_a, root_b]:
            (root / ".lazy-harness" / "bin").mkdir(parents=True)
            (root / ".lazy-harness" / "hooks" / "lifecycle").mkdir(parents=True)
            (root / ".lazy-harness" / "bin" / "lazy").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            hook = root / ".lazy-harness" / "hooks" / "lifecycle" / "on-tool-execute-before.sh"
            hook.write_text("#!/usr/bin/env bash\ncat > .lazy-harness/last-tool-payload.json\n", encoding="utf-8")
            hook.chmod(0o755)
        smoke = isolation_smoke / "root-isolation.ts"
        smoke.write_text(
            "import { readFileSync } from 'node:fs';\n"
            "import lazyHarnessPi from " + json.dumps(str(extension)) + ";\n"
            "const handlers = new Map();\n"
            "const pi = { on(e,h){handlers.set(e,h)}, registerCommand(){}, async exec(){return {stdout:'',stderr:'',exitCode:0}} };\n"
            "lazyHarnessPi(pi);\n"
            "const rootA=" + json.dumps(str(root_a)) + ";\n"
            "const rootB=" + json.dumps(str(root_b)) + ";\n"
            "await handlers.get('tool_result')({toolName:'read', input:{file_path:'a.txt'}, toolCallId:'a-read', content:'aaa'}, {cwd:rootA});\n"
            "await handlers.get('tool_call')({toolName:'write', input:{file_path:'b.txt', content:'b'}}, {cwd:rootB});\n"
            "const b=JSON.parse(readFileSync(rootB+'/.lazy-harness/last-tool-payload.json','utf8'));\n"
            "if (b.recent_tool_calls.length !== 0) throw new Error('repo B saw repo A tool calls');\n"
            "await handlers.get('tool_call')({toolName:'write', input:{file_path:'a2.txt', content:'a'}}, {cwd:rootA});\n"
            "const a=JSON.parse(readFileSync(rootA+'/.lazy-harness/last-tool-payload.json','utf8'));\n"
            "if (a.recent_tool_calls.length !== 1 || a.recent_tool_calls[0].toolCallId !== 'a-read') throw new Error('repo A lost own tool call evidence');\n"
            "console.log('pi root-scoped recent tool isolation ok');\n",
            encoding="utf-8",
        )
        completed = subprocess.run(["bun", str(smoke)], cwd=ROOT, text=True, capture_output=True, check=False, env=env_without_lazy_runtime())
        if completed.returncode != 0:
            fail("Pi root-scoped recent tool isolation smoke failed:\n" + completed.stdout + completed.stderr)
    finally:
        shutil.rmtree(isolation_smoke, ignore_errors=True)

    print("✓ Pi package layout and extension contract ok")


def check_jcode_wiring_message_received_hook() -> None:
    """Generated and user-owned Jcode configs must wire static harness prompt plus generic search/read evidence guard."""
    source = (LAZY / "scripts" / "jcode-wiring.ts").read_text(encoding="utf-8")
    required = [
        'event = \\"message.received\\"',
        'command = \\".lazy-harness/hooks/lifecycle/on-message-received.sh\\"',
        'blocking = true',
        'timeout_ms = 800',
        'ensureMessageReceivedHook',
        'ensureReadDebtPermitHook',
        'not a user-text classifier',
        'Generic pre-action search/read evidence guard',
        'It does not perform semantic',
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("jcode wiring missing message.received hook contract: " + json.dumps(missing, ensure_ascii=False))
    forbidden = [
        'cleanupReadDebt' + 'PermitHook',
        'tool-specific policy adapter',
        'Aliases and implementation ' + 'hints from',
    ]
    leaked = [phrase for phrase in forbidden if phrase in source]
    if leaked:
        fail("jcode wiring must not install tool-specific adapters or framework search implementation: " + json.dumps(leaked, ensure_ascii=False))

    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-jcode-message-received-"))
    try:
        (temp / ".lazy-harness").mkdir(parents=True)
        shutil.copy2(LAZY / "AGENTS.md", temp / ".lazy-harness" / "AGENTS.md")
        (temp / ".jcode").mkdir(parents=True)
        config = temp / ".jcode" / "config.toml"
        config.write_text(
            "# user-owned config\n"
            "[prompt]\n"
            "custom_local_flag = true\n\n"
            "[hooks]\n"
            "enabled = true\n",
            encoding="utf-8",
        )
        code = (
            "import { installJcodeWiring } from './.lazy-harness/scripts/jcode-wiring.ts';"
            f"installJcodeWiring({{ targetRoot: {json.dumps(str(temp))}, quiet: true }});"
        )
        completed = subprocess.run(["bun", "-e", code], cwd=ROOT, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            fail("jcode message.received wiring import/run failed:\n" + completed.stdout + completed.stderr)
        updated = config.read_text(encoding="utf-8")
        if "custom_local_flag = true" not in updated:
            fail("message.received hook patch overwrote user-owned config content:\n" + updated)
        for phrase in [
            'event = "message.received"', 'on-message-received.sh', 'blocking = true', 'timeout_ms = 800',
            'event = "tool.execute.before"', 'tool = "*"', 'on-tool-execute-before.sh', 'timeout_ms = 1200',
        ]:
            if phrase not in updated:
                fail("jcode direct-search/read guard patch missing phrase " + phrase + ":\n" + updated)

        legacy_message = temp / ".jcode" / "config.toml"
        legacy_message.write_text(updated.replace(
            "# BEGIN lazy-harness message.received static-harness hook\n"
            "# Bounded pre-turn static harness inventory/search prompt and search-debt journal.\n"
            "# This is not a semantic search backend, not a user-text classifier, not a tool\n"
            "# allowlist, and not a broad edit gate; timeout/failure is fail-open.\n",
            "# BEGIN lazy-harness message.received context hook\n"
            "# Bounded pre-turn relevant-record context injection. This is not a broad edit\n"
            "# gate; timeout/failure is handled fail-open by Jcode and the hook.\n",
        ).replace(
            "# END lazy-harness message.received static-harness hook",
            "# END lazy-harness message.received context hook",
        ), encoding="utf-8")
        completed = subprocess.run(["bun", "-e", code], cwd=ROOT, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            fail("jcode legacy message.received refresh import/run failed:\n" + completed.stdout + completed.stderr)
        refreshed_message = legacy_message.read_text(encoding="utf-8")
        if "message.received context hook" in refreshed_message or "relevant-record context injection" in refreshed_message:
            fail("jcode wiring failed to refresh stale message.received context hook marker:\n" + refreshed_message)
        if refreshed_message.count("on-message-received.sh") != 1 or "message.received static-harness hook" not in refreshed_message:
            fail("jcode legacy message.received refresh duplicated or lost hook:\n" + refreshed_message)

        legacy = temp / ".jcode" / "config.toml"
        legacy.write_text(
            updated,
            encoding="utf-8",
        )
        completed = subprocess.run(["bun", "-e", code], cwd=ROOT, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            fail("jcode read-debt idempotence import/run failed:\n" + completed.stdout + completed.stderr)
        cleaned = legacy.read_text(encoding="utf-8")
        if cleaned.count("on-tool-execute-before.sh") != 1:
            fail("jcode wiring duplicated generic search/read evidence guard:\n" + cleaned)
        stale = cleaned.replace(
            "# Generic pre-action search/read evidence guard. It does not perform semantic\n"
            "# search and it is not a concrete-tool policy adapter or allowlist. It only checks\n"
            "# whether message.received produced direct-search/read-debt and whether\n"
            "# the LLM/searcher already left root-bound harness-following search/read evidence\n"
            "# before action.\n",
            "# Narrow pre-action permit gate. It is silent unless a deterministic producer\n"
            "# created concrete requiredRead debt for this turn and the next action would run\n"
            "# before read/search evidence exists. This is not a broad edit/write hard stop.\n",
        )
        legacy.write_text(stale, encoding="utf-8")
        completed = subprocess.run(["bun", "-e", code], cwd=ROOT, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            fail("jcode read-debt refresh import/run failed:\n" + completed.stdout + completed.stderr)
        refreshed = legacy.read_text(encoding="utf-8")
        if "Narrow pre-action permit gate" in refreshed or "Generic pre-action search/read evidence guard" not in refreshed:
            fail("jcode wiring failed to refresh stale managed search/read guard block:\n" + refreshed)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ jcode message.received hook wiring/static harness guard ok")


def check_prompt_budget_measurement() -> None:
    """Phase 1 prompt/runtime compression should measure prompt budget without runtime behavior changes."""
    spec_path = LAZY / "spec" / "platform" / "prompt-budget.md"
    tdd_path = LAZY / "tests" / "prompt-budget.md"
    script_path = LAZY / "scripts" / "prompt-budget.py"
    for path in [spec_path, tdd_path, script_path]:
        if not path.exists():
            fail("prompt budget artifact missing: " + str(path))

    script_text = script_path.read_text(encoding="utf-8")
    for phrase in ["SYNTHETIC_MESSAGE", "LAZY_RUNTIME_ROOT", "fixtureMessageLeaked", "transitionHardMaxTokens", "enforcement", "advisory"]:
        if phrase not in script_text:
            fail("prompt-budget.py missing privacy/budget phrase: " + phrase)

    completed = subprocess.run(
        ["python3", str(script_path), "--root", str(ROOT), "--format=json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env_without_lazy_runtime(),
    )
    if completed.returncode != 0:
        fail("prompt-budget json command failed:\n" + completed.stdout + completed.stderr)
    if "__lazy_prompt_budget_fixture_message__" in completed.stdout:
        fail("prompt-budget output leaked synthetic fixture message")
    try:
        report = json.loads(completed.stdout)
    except Exception as exc:  # noqa: BLE001
        fail("prompt-budget json output did not parse: " + str(exc) + "\n" + completed.stdout)

    for key in ["schemaVersion", "status", "budgets", "surfaces", "duplicates", "renderedMessageReceived", "notes"]:
        if key not in report:
            fail("prompt-budget json missing key: " + key)
    if report.get("schemaVersion") != "1.0":
        fail("prompt-budget schemaVersion mismatch: " + json.dumps(report, ensure_ascii=False)[:500])
    if report.get("status") == "fail":
        fail("prompt-budget should not fail during Phase 1 transition:\n" + completed.stdout)

    rendered = report.get("renderedMessageReceived") or {}
    for key in ["lineCount", "tokenEstimate", "status", "journalRows", "bodyHash", "transitionHardMaxTokens"]:
        if key not in rendered:
            fail("prompt-budget renderedMessageReceived missing key: " + key)
    if int(rendered.get("lineCount") or 0) <= 0 or int(rendered.get("tokenEstimate") or 0) <= 0:
        fail("prompt-budget rendered message should include positive line/token estimates: " + json.dumps(rendered, ensure_ascii=False))
    if int(rendered.get("journalRows") or 0) < 1:
        fail("prompt-budget should render hook in isolated runtime and observe journal row: " + json.dumps(rendered, ensure_ascii=False))
    if rendered.get("fixtureMessageLeaked"):
        fail("prompt-budget rendered output reports fixture message leak")
    if int(rendered.get("tokenEstimate") or 0) > int(rendered.get("transitionHardMaxTokens") or 0):
        fail("prompt-budget rendered prompt exceeded transition hard max: " + json.dumps(rendered, ensure_ascii=False))

    surface_paths = {surface.get("path") for surface in report.get("surfaces", [])}
    if ".lazy-harness/AGENTS.md" not in surface_paths:
        fail("prompt-budget surfaces missing .lazy-harness/AGENTS.md: " + json.dumps(report.get("surfaces", []), ensure_ascii=False))

    md = subprocess.run(
        [str(LAZY / "bin" / "lazy"), "prompt-budget", "--format=md"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(ROOT)),
    )
    if md.returncode != 0:
        fail("lazy prompt-budget markdown command failed:\n" + md.stdout + md.stderr)
    for phrase in ["# Prompt budget", "Rendered message.received", "Estimated tokens", "Prompt surfaces", "Duplicate grammar hints"]:
        if phrase not in md.stdout:
            fail("lazy prompt-budget markdown output missing phrase: " + phrase + "\n" + md.stdout)
    if "__lazy_prompt_budget_fixture_message__" in md.stdout:
        fail("lazy prompt-budget markdown leaked synthetic fixture message")

    temp = pathlib.Path(tempfile.mkdtemp(prefix="prompt-budget-huge-skill-"))
    try:
        (temp / ".lazy-harness").mkdir(parents=True)
        skill = temp / ".jcode" / "skills" / "huge-host-skill" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("# Huge host-local skill\n\n" + "\n".join(f"Detailed on-demand instruction line {i}" for i in range(1, 521)) + "\n", encoding="utf-8")
        huge = subprocess.run(
            ["python3", str(script_path), "--root", str(temp), "--format=json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=env_without_lazy_runtime(),
        )
        if huge.returncode != 0:
            fail("prompt-budget should not fail solely due to oversized host-local skill:\n" + huge.stdout + huge.stderr)
        huge_report = json.loads(huge.stdout)
        if huge_report.get("status") == "fail":
            fail("oversized host-local skill should not make top-level prompt-budget fail:\n" + huge.stdout)
        skill_surfaces = [surface for surface in huge_report.get("surfaces", []) if surface.get("kind") == "skill-prompt"]
        if len(skill_surfaces) != 1:
            fail("oversized skill fixture should produce one skill-prompt surface: " + json.dumps(huge_report.get("surfaces", []), ensure_ascii=False))
        surface = skill_surfaces[0]
        if surface.get("enforcement") != "advisory" or surface.get("rawStatus") != "fail" or surface.get("status") != "warn":
            fail("oversized skill fixture should be advisory warn with raw fail: " + json.dumps(surface, ensure_ascii=False))
    finally:
        shutil.rmtree(temp, ignore_errors=True)

    print("✓ prompt budget measurement ok")


def check_framework_runtime_no_host_product_hardcoding() -> None:
    """Framework runtime/generator/fixture surfaces must stay host-agnostic."""
    roots = [
        LAZY / "scripts",
        LAZY / "hooks",
        LAZY / "bin",
        LAZY / "manifests",
        LAZY / "schemas",
        LAZY / "fixtures",
    ]
    suffixes = {".md", ".ts", ".tsx", ".js", ".py", ".sh", ".json", ".jsonl", ".xml", ".toml", ".yaml", ".yml", ".txt"}
    forbidden = [
        "medi" + "vance",
        "MEDI" + "VANCE",
        "메디" + "밴스",
        "예" + "약" + "시트",
        "예" + "약" + "표",
        "예" + "약" + "관리",
        "reserv" + "ation " + "sheet",
        "Reservation" + "Table",
        "Reservation" + "ManagementPage",
        "Reservation" + "Sheet",
        "book" + "ing " + "sheet",
        "book" + "ing " + "table",
        "Calendar master " + "header design",
        "vacationList" + "Airplane",
        "/home/lazydino/dev/" + "medi" + "vance",
        "src/" + "renderer" + "/src",
        "src/" + "main" + "/trpc",
    ]
    allowed_files = {str(LAZY / "scripts" / "self-test.py")}
    leaks: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            rel = str(path)
            if rel in allowed_files:
                # This test intentionally constructs forbidden tokens from pieces.
                # Whole-token leaks in self-test still fail, but split literals do not.
                pass
            for token in forbidden:
                if token in text:
                    leaks.append(f"{rel}: {token!r}")
    if leaks:
        fail("framework runtime/generator/fixtures leaked host/product-specific hardcoding:\n" + "\n".join(leaks[:80]))
    print("✓ framework runtime host/product hardcoding guard ok")


def check_manifest_syncs_python_lifecycle_helpers() -> None:
    """Hosts need Python lifecycle helpers copied by lazy-sync/lazy-init."""
    manifest = json.loads((LAZY / "manifests" / "init-categories.json").read_text(encoding="utf-8"))
    item_paths = {item.get("path") for item in manifest["categories"]["A"]["items"]}
    hooks_item = None
    for item in manifest["categories"]["A"]["items"]:
        if item.get("path") == "hooks/":
            hooks_item = item
            break
    if not hooks_item or "lifecycle/helpers/*.py" not in hooks_item.get("glob", []):
        fail("init-categories manifest must sync Python lifecycle helpers for host guard support")
    for required_record in [
        "domain/searchable-record-memory.md",
        "behavior/llm-owned-record-retrieval.md",
        "spec/platform/record-index-header.md",
        "tests/record-index-header.md",
        "spec/platform/pre-response-rule-context.md",
        "tests/pre-response-rule-context.md",
    ]:
        if required_record not in item_paths:
            fail("init-categories manifest must sync retrieval/index foundation record: " + required_record)
    print("✓ manifest Python lifecycle helper sync ok")


def check_lazy_sync_prunes_stale_managed_files() -> None:
    """lazy-sync must remove stale files from managed Category A directories."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-sync-prune-"))
    try:
        state = temp / ".lazy-harness" / "state"
        stale = temp / ".lazy-harness" / "fixtures" / "context-delivery" / "obsolete-managed-fixture.xml"
        removed_managed = [
            temp / ".lazy-harness" / "spec" / "platform" / "operational-state-packet.md",
            temp / ".lazy-harness" / "tests" / "operational-state-packet.md",
            temp / ".lazy-harness" / "scripts" / "task-router.ts",
            temp / ".lazy-harness" / "fixtures" / "task-router" / "cases.json",
        ]
        graph = temp / ".lazy-harness" / "knowledge" / "graph.jsonl"
        state.mkdir(parents=True)
        stale.parent.mkdir(parents=True)
        for removed in removed_managed:
            removed.parent.mkdir(parents=True, exist_ok=True)
            removed.write_text("legacy managed file\n", encoding="utf-8")
        graph.parent.mkdir(parents=True)
        stale.write_text("<legacy-fixture />\n", encoding="utf-8")
        host_graph_row = {"id": "host_local_graph_fact", "source": "host-local fact must survive lazy-sync"}
        graph.write_text(json.dumps(host_graph_row, ensure_ascii=False) + "\n", encoding="utf-8")
        capabilities = temp / ".lazy-harness" / "ssot" / "capabilities.json"
        capabilities.parent.mkdir(parents=True, exist_ok=True)
        capabilities.write_text(
            json.dumps(
                {
                    "version": 1,
                    "capabilities": [
                        {
                            "id": "host-local-capability",
                            "kind": "command",
                            "level": "discover",
                            "sourceRecord": ".lazy-harness/ssot/host-local.md",
                            "appliesWhen": ["host_local_only"],
                            "actions": ["host-local action"],
                        }
                    ],
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, env=env_without_lazy_runtime(), text=True).strip()
        (state / "synced-from-commit").write_text(
            json.dumps({"syncedFromCommit": head, "sourceRoot": str(ROOT)}, ensure_ascii=False),
            encoding="utf-8",
        )
        completed = subprocess.run(
            ["bun", ".lazy-harness/scripts/lazy-sync.ts", "--from", str(ROOT), "--target", str(temp), "--force", "--quiet"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            fail("lazy-sync prune fixture failed:\n" + completed.stdout + completed.stderr)
        current = temp / ".lazy-harness" / "fixtures" / "context-tier" / "context-tier-manifest.sample.json"
        if stale.exists() or not current.exists():
            fail("lazy-sync must prune stale managed fixture and copy current context-tier fixture")
        for required_record in [
            "domain/searchable-record-memory.md",
            "behavior/llm-owned-record-retrieval.md",
            "spec/platform/record-index-header.md",
            "tests/record-index-header.md",
            "spec/platform/pre-response-rule-context.md",
            "tests/pre-response-rule-context.md",
        ]:
            if not (temp / ".lazy-harness" / required_record).exists():
                fail("lazy-sync must copy retrieval/index foundation record: " + required_record)
        still_present = [str(p.relative_to(temp)) for p in removed_managed if p.exists()]
        if still_present:
            fail("lazy-sync must prune known removed managed files: " + json.dumps(still_present, ensure_ascii=False))
        graph_text = graph.read_text(encoding="utf-8")
        if "host_local_graph_fact" not in graph_text or "kg_" not in graph_text:
            fail("lazy-sync must merge source knowledge seeds while preserving host-local graph rows")
        if not (temp / ".lazy-harness" / "rules" / "README.md").exists():
            fail("lazy-sync must copy the framework rulebook README seed")
        capability_ids = [
            cap.get("id")
            for cap in json.loads(capabilities.read_text(encoding="utf-8")).get("capabilities", [])
        ]
        for required_capability in [
            "host-local-capability",
            "project-operating-rulebook",
            "retrieval-purpose-test",
        ]:
            if required_capability not in capability_ids:
                fail("lazy-sync must preserve host capabilities and merge framework seeds: " + required_capability)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ lazy-sync stale managed file prune ok")


def check_jcode_dev_hooks_are_nonblocking() -> None:
    """Generated Jcode wiring must keep edit/write/multiedit fast and non-blocking."""
    source = (LAZY / "scripts" / "jcode-wiring.ts").read_text(encoding="utf-8")
    forbidden = [
        'tool = "edit"',
        'tool = "write"',
        'tool = "multiedit"',
    ]
    leaked = [phrase for phrase in forbidden if phrase in source]
    if leaked:
        fail("jcode wiring must not register blocking edit/write hooks: " + json.dumps(leaked, ensure_ascii=False))
    required = [
        "development fast",
        "pre-commit/pre-push",
        "commit-time gates",
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("jcode wiring missing commit-time gate explanation: " + json.dumps(missing, ensure_ascii=False))
    print("✓ jcode development hooks non-blocking policy ok")


def run_rule_action_boundary_helper(payload: dict, root: pathlib.Path | None = None) -> str:
    completed = subprocess.run(
        [".lazy-harness/hooks/lifecycle/helpers/check-rule-action-boundary.py", json.dumps(payload)],
        cwd=root or ROOT,
        env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(root or ROOT)),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"rule action boundary helper exit changed: {completed.returncode}")
    return completed.stdout


def check_rule_action_boundary_legacy_no_project_policy() -> None:
    """Phase 5: legacy action-boundary helper must no longer block project policy."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-rule-boundary-"))
    try:
        (temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers").mkdir(parents=True)
        (temp / ".lazy-harness" / "ssot").mkdir(parents=True)
        shutil.copy2(
            LAZY / "hooks" / "lifecycle" / "helpers" / "check-rule-action-boundary.py",
            temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers" / "check-rule-action-boundary.py",
        )

        payload = {"tool": {"name": "bash", "args": {"command": "gh pr create --body '## Summary\ntext'"}}}
        without_record = run_rule_action_boundary_helper(payload, temp)
        if without_record.strip():
            fail("legacy action-boundary shim should stay silent without host PR format record:\n" + without_record)

        (temp / ".lazy-harness" / "ssot" / "pr-description-format.md").write_text(
            "# PR Description Format\n\nRequired: Why / What / Task\n",
            encoding="utf-8",
        )
        malformed = run_rule_action_boundary_helper(payload, temp)
        if malformed.strip():
            fail("Phase 5 migrated PR policy out of tool-attached guard; malformed PR body should not be denied here:\n" + malformed)

        valid_body = "## Why\nneeded\n\n## What\nchanged\n\n## Task\n- [x] work\n"
        valid = run_rule_action_boundary_helper(
            {"tool": {"name": "bash", "args": {"command": "gh pr create --body " + json.dumps(valid_body)}}},
            temp,
        )
        if valid.strip():
            fail("legacy action-boundary shim should allow valid body:\n" + valid)

        body_file = temp / "body.md"
        body_file.write_text(valid_body, encoding="utf-8")
        valid_file = run_rule_action_boundary_helper(
            {"tool": {"name": "bash", "args": {"command": f"gh pr edit 41 --body-file {body_file}"}}},
            temp,
        )
        if valid_file.strip():
            fail("legacy action-boundary shim should allow valid --body-file:\n" + valid_file)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ rule action boundary legacy no project policy ok")


def check_jcode_wiring_bash_safety_only_hook() -> None:
    """Generated bash hook must keep only destructive shell safety, not project policy adapters."""
    source = (LAZY / "scripts" / "jcode-wiring.ts").read_text(encoding="utf-8")
    required = [
        '\\"action\\": \\"deny\\"',
        'tool = \\"bash\\"',
        "Refusing raw disk overwrite",
        "Refusing filesystem creation on block device",
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("jcode wiring missing bash safety-only hook phrases: " + json.dumps(missing, ensure_ascii=False))
    forbidden = ["check-rule-action-boundary.py", "BOUNDARY_OUT", "gh pr create", "gh pr edit"]
    leaked = [phrase for phrase in forbidden if phrase in source]
    if leaked:
        fail("jcode bash hook template must not include project-policy boundary adapters: " + json.dumps(leaked, ensure_ascii=False))
    print("✓ jcode wiring bash safety-only hook ok")


def run_hard_stop_promotion_audit(root: pathlib.Path, strict: bool = True) -> subprocess.CompletedProcess:
    command = [
        "python3",
        str(LAZY / "scripts" / "hard-stop-promotion-audit.py"),
        "--root",
        str(root),
        "--format",
        "json",
    ]
    if strict:
        command.append("--strict")
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def check_guidance_ladder_hard_stop_promotion() -> None:
    """Phase 6: hard stops require explicit promotion evidence before implementation."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-hard-stop-promotion-"))
    try:
        spec_dir = temp / ".lazy-harness" / "spec" / "platform"
        fixture_dir = temp / ".lazy-harness" / "tests" / "fixtures" / "hard-stop"
        spec_dir.mkdir(parents=True)
        fixture_dir.mkdir(parents=True)

        invalid = spec_dir / "invalid-hard-stop.md"
        invalid.write_text(
            "# Invalid hard stop\n\n"
            "## Hard-stop promotion\n\n"
            "- Status: active\n"
            "- Boundary: block a broad project policy action\n"
            "- Scope: framework-global\n"
            "- User confirmation: user-confirmed fixture\n",
            encoding="utf-8",
        )
        invalid_run = run_hard_stop_promotion_audit(temp, strict=True)
        if invalid_run.returncode == 0:
            fail("invalid hard-stop promotion should fail strict audit:\n" + invalid_run.stdout)
        invalid_result = json.loads(invalid_run.stdout)
        problems = "\n".join(invalid_result.get("violations", [{}])[0].get("problems", []))
        for expected in ["missing Evidence", "missing Fixture", "missing Rollback"]:
            if expected not in problems:
                fail("invalid hard-stop promotion audit missed expected problem " + expected + ":\n" + invalid_run.stdout)

        invalid.unlink()
        fixture = fixture_dir / "irreversible-action.json"
        fixture.write_text('{"block":"irreversible","allow":"safe"}\n', encoding="utf-8")
        valid = spec_dir / "valid-hard-stop.md"
        valid.write_text(
            "# Valid hard stop\n\n"
            "## Hard-stop promotion\n\n"
            "- Status: active\n"
            "- Boundary: block fixture irreversible action before execution\n"
            "- Scope: framework-global\n"
            "- User confirmation: user-confirmed 2026-06-01 fixture boundary\n"
            "- Evidence: irreversible action risk; softer audit would run after the damage\n"
            "- Existing softer coverage: response audit exists but cannot prevent pre-execution data loss\n"
            "- Fixture: .lazy-harness/tests/fixtures/hard-stop/irreversible-action.json\n"
            "- Narrowness: exact fixture boundary only, no bash/gh/project-policy adapter sprawl\n"
            "- Rollback: set Status to retired and remove the blocking branch\n",
            encoding="utf-8",
        )
        valid_run = run_hard_stop_promotion_audit(temp, strict=True)
        if valid_run.returncode != 0:
            fail("valid hard-stop promotion should pass strict audit:\n" + valid_run.stdout + valid_run.stderr)
        valid_result = json.loads(valid_run.stdout)
        if valid_result.get("summary", {}).get("promotions") != 1 or valid_result.get("violations"):
            fail("valid hard-stop promotion audit returned wrong summary:\n" + valid_run.stdout)

        source_run = run_hard_stop_promotion_audit(ROOT, strict=True)
        if source_run.returncode != 0:
            fail("source hard-stop promotion audit should pass:\n" + source_run.stdout + source_run.stderr)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ guidance ladder hard-stop promotion ok")


def check_jcode_project_profile_skill_wrapper() -> None:
    """Generated Jcode wiring must install the framework-owned Project Profile skill."""
    source = (LAZY / "scripts" / "jcode-wiring.ts").read_text(encoding="utf-8")
    required = [
        "lazy-project-profile",
        "project-profile.ts --mode inspect",
        "project-profile.ts --mode plan",
        "project-profile.ts --mode apply --confirm",
        "interview-first architecture flow",
        ".lazy-harness/spec/platform/project-profile.md",
        ".lazy-harness/plans/project-init-interview-spec.md",
        "Do not silently invent architecture defaults",
        "Document Resource Ingestion",
        "separate ingestion flow",
        "Ask 3-5 option gates",
        "project-profile.ts --mode interview --dry-run",
        "project-profile.ts --mode interview --confirm",
        "profile-interview.xml",
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("jcode wiring missing lazy-project-profile wrapper contract: " + json.dumps(missing, ensure_ascii=False))
    manifest = (LAZY / "manifests" / "skills.xml").read_text(encoding="utf-8")
    if '<skill id="lazy-project-profile" status="beta"' not in manifest or ".jcode/skills/lazy-project-profile/" not in manifest:
        fail("skills manifest must promote lazy-project-profile to beta framework-owned wrapper")
    print("✓ jcode project profile skill wrapper ok")


def check_jcode_doc_ingest_skill_wrapper() -> None:
    """Generated Jcode wiring must install the document ingestion skill separately from Project Profile."""
    source = (LAZY / "scripts" / "jcode-wiring.ts").read_text(encoding="utf-8")
    required = [
        "lazy-doc-ingest",
        "document-resource-ingestion.ts --mode inspect",
        "document-resource-ingestion.ts --mode plan",
        "document-resource-ingestion.ts --mode apply --dry-run",
        "document-resource-ingestion.ts --mode apply --confirm",
        ".lazy-harness/spec/platform/document-resource-ingestion.md",
        "separate capability from /lazy-project-profile",
        "Never auto-promote external facts",
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("jcode wiring missing lazy-doc-ingest wrapper contract: " + json.dumps(missing, ensure_ascii=False))
    manifest = (LAZY / "manifests" / "skills.xml").read_text(encoding="utf-8")
    if '<skill id="lazy-doc-ingest" status="beta"' not in manifest or ".jcode/skills/lazy-doc-ingest/" not in manifest:
        fail("skills manifest must declare lazy-doc-ingest beta framework-owned wrapper")
    import_check = subprocess.run(
        ["bun", "-e", "import('./.lazy-harness/scripts/jcode-wiring.ts').then(m => { if (typeof m.installJcodeWiring !== 'function') process.exit(2) })"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if import_check.returncode != 0:
        fail("jcode wiring must import cleanly after skill wrapper edits:\n" + import_check.stdout + import_check.stderr)
    print("✓ jcode document ingestion skill wrapper ok")


def check_jcode_impl_map_migrate_skill_wrapper() -> None:
    """Generated Jcode/Pi wiring must expose the guided implementation-map migration skill."""
    source = (LAZY / "scripts" / "jcode-wiring.ts").read_text(encoding="utf-8")
    required = [
        "lazy-impl-map-migrate",
        "Guided LLM-assisted implementation-map migration",
        "implementation-map-migration.md",
        "implementation-map-standard.md",
        "implementation-map-storage.md",
        "graph-hygiene.md",
        "lazy impl-map --format=json",
        "lazy graph-hygiene --format=json",
        "3-5 option gate",
        "Do not rewrite graph.jsonl wholesale",
        "choose the next clear Recommended batch automatically",
        "present a 3-5 option gate and stop",
        "After each selected batch is completed and validated",
        "Default mode is bounded autopilot mode",
        "Manual option-gate mode remains available",
        "automatically continue with the next clear Recommended batch",
        "no default numeric batch limit",
        "until needs-map is complete",
        "Stop on validation failure, needs-review, ignored/tracked file uncertainty, missing source/test evidence",
        "graph wholesale cleanup pressure",
        "user-specified max batch limit reached",
        "exact stop reason",
        "OMP compatibility work is intentionally after this guided migration skill exists",
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("jcode wiring missing lazy-impl-map-migrate wrapper contract: " + json.dumps(missing, ensure_ascii=False))
    manifest = (LAZY / "manifests" / "skills.xml").read_text(encoding="utf-8")
    if '<skill id="lazy-impl-map-migrate" status="beta"' not in manifest or ".jcode/skills/lazy-impl-map-migrate/" not in manifest or "packages/lazy-harness-pi/skills/lazy-impl-map-migrate/SKILL.md" not in manifest:
        fail("skills manifest must declare lazy-impl-map-migrate beta framework-owned wrapper")
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-jcode-impl-map-skill-"))
    try:
        install_check = subprocess.run(
            [
                "bun",
                "-e",
                "import('./.lazy-harness/scripts/jcode-wiring.ts').then(m => m.installJcodeWiring({ targetRoot: " + json.dumps(str(temp)) + ", quiet: true }))",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if install_check.returncode != 0:
            fail("jcode wiring must generate lazy-impl-map-migrate skill wrapper in temp target:\n" + install_check.stdout + install_check.stderr)
        paths = [
            temp / ".jcode" / "skills" / "lazy-impl-map-migrate" / "SKILL.md",
            ROOT / "packages" / "lazy-harness-pi" / "skills" / "lazy-impl-map-migrate" / "SKILL.md",
        ]
        for path in paths:
            if not path.exists():
                label = str(path) if temp in path.parents else str(path.relative_to(ROOT))
                fail(f"lazy-impl-map-migrate skill wrapper missing: {label}")
            content = path.read_text(encoding="utf-8")
            for phrase in required:
                if phrase not in content and phrase not in {"3-5 option gate"}:
                    label = str(path) if temp in path.parents else str(path.relative_to(ROOT))
                    fail(f"lazy-impl-map-migrate skill wrapper {label} missing phrase: {phrase}")
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ jcode implementation-map migration skill wrapper ok")


def check_pre_commit_runs_lazy_test() -> None:
    """pre-commit guard must move framework validation to the commit boundary."""
    source = (LAZY / "hooks" / "pre-commit-guard.sh").read_text(encoding="utf-8")
    required = [
        "run_commit_gate()",
        '"$LAZY/bin/lazy" test',
        '"$LAZY/scripts/self-test.py"',
        "pre-commit blocked: .lazy-harness/bin/lazy test 실패",
        "git-action.lockdir",
        "same worktree already has a lazy-harness git action running",
        "IS_FRAMEWORK_REPO",
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("pre-commit guard missing commit-time lazy test gate: " + json.dumps(missing, ensure_ascii=False))
    print("✓ pre-commit lazy test gate ok")


def check_gate_state_cli_and_record_audit_source_guard() -> None:
    """Phase 3 readiness helpers protect runtime gate cleanup and source-arg mistakes."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-gate-state-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        state_dir = runtime_open_gates_file(temp).parent
        state_dir.mkdir(parents=True)
        (temp / ".lazy-harness" / "knowledge").mkdir(parents=True)
        (state_dir / "open-gates.json").write_text(
            json.dumps({
                "last_message_id": "fixture-message",
                "open_fingerprints": {
                    "bdd:old": {"first_seen_message_id": "old", "first_seen_ts": "2020-01-01T00:00:00Z"},
                    "project-rule-placement:new": {"first_seen_message_id": "new", "first_seen_ts": "2999-01-01T00:00:00Z"},
                },
            }),
            encoding="utf-8",
        )
        env = env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp))
        listed = subprocess.run([str(LAZY / "bin" / "lazy"), "gate-state", "list", "--format=json"], cwd=temp, env=env, text=True, capture_output=True, check=False)
        if listed.returncode != 0:
            fail("gate-state list failed:\n" + listed.stdout + listed.stderr)
        listed_json = json.loads(listed.stdout)
        if listed_json.get("count") != 2:
            fail("gate-state list should show two fixture gates: " + listed.stdout)

        dry = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "gate-state", "clear-stale", "--older-than-hours", "1", "--prefix", "bdd:", "--dry-run", "--format=json"],
            cwd=temp,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if dry.returncode != 0 or "bdd:old" not in json.loads(dry.stdout).get("removed", []):
            fail("gate-state dry-run should report old bdd gate removal:\n" + dry.stdout + dry.stderr)
        still_two = json.loads((state_dir / "open-gates.json").read_text(encoding="utf-8"))
        if len(still_two.get("open_fingerprints", {})) != 2:
            fail("gate-state dry-run must not mutate state")

        cleared = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "gate-state", "clear-stale", "--older-than-hours", "1", "--prefix", "bdd:", "--format=json"],
            cwd=temp,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if cleared.returncode != 0:
            fail("gate-state clear-stale failed:\n" + cleared.stdout + cleared.stderr)
        state = json.loads((state_dir / "open-gates.json").read_text(encoding="utf-8"))
        keys = set(state.get("open_fingerprints", {}).keys())
        if keys != {"project-rule-placement:new"}:
            fail("gate-state clear-stale should remove only stale matching prefix: " + json.dumps(sorted(keys), ensure_ascii=False))

        audit = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "record-audit", "--format=json", "--source", str(temp)],
            cwd=temp,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if audit.returncode != 0:
            fail("record-audit self-source fixture failed:\n" + audit.stdout + audit.stderr)
        warnings = json.loads(audit.stdout).get("warnings", [])
        if not any("--source argument points at this host" in warning for warning in warnings):
            fail("record-audit should warn when --source points at same host: " + audit.stdout)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ gate-state CLI and record-audit source guard ok")


def check_lifecycle_fixture_intake_cli() -> None:
    """Real payload intake must store safe metadata only and feed parity fixtures."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-lifecycle-intake-"))
    try:
        shutil.copytree(ROOT / ".lazy-harness", temp / ".lazy-harness", ignore=shutil.ignore_patterns(".cache", "logs", "state", "node_modules"))
        env = env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp))
        raw_payload = {
            "message_id": "raw-message-id",
            "last_user_message": "비밀 사용자 문장 patient ABC 123",
            "assistant_response": "민감한 답변입니다. .lazy-harness/bin/lazy test 를 실행하겠습니다.",
            "recent_tool_calls": [
                {"name": "read", "args_preview": ".lazy-harness/planning/performance-optimization-plan.md"},
                {"name": "bash", "args_preview": "echo secret-token-123 && git status"},
            ],
        }
        raw = json.dumps(raw_payload, ensure_ascii=False)
        inspected = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "lifecycle-fixture", "inspect", "--payload", raw, "--format=json", "--name", "fixture-intake-smoke"],
            cwd=temp,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if inspected.returncode != 0:
            fail("lifecycle-fixture inspect failed:\n" + inspected.stdout + inspected.stderr)
        inspected_text = inspected.stdout
        for forbidden in ["비밀 사용자", "patient ABC", "민감한 답변", "secret-token-123"]:
            if forbidden in inspected_text:
                fail("lifecycle-fixture inspect leaked raw content: " + forbidden + "\n" + inspected_text)
        candidate = json.loads(inspected_text)["candidate"]
        if candidate.get("category") != "mutating-or-shell" or candidate.get("lastUserMessage", {}).get("present") is not True:
            fail("lifecycle-fixture inspect missing safe metadata: " + inspected_text)
        previews = [call.get("args_preview", "") for call in candidate.get("sanitizedPayload", {}).get("recent_tool_calls", [])]
        if not any(str(preview).startswith("paths:") for preview in previews) or not any(preview == "command:git" for preview in previews):
            fail("lifecycle-fixture inspect did not sanitize previews as expected: " + json.dumps(previews, ensure_ascii=False))

        appended = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "lifecycle-fixture", "append", "--payload", raw, "--format=json", "--name", "fixture-intake-smoke", "--source", "self-test"],
            cwd=temp,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if appended.returncode != 0:
            fail("lifecycle-fixture append failed:\n" + appended.stdout + appended.stderr)
        candidate_file = temp / ".lazy-harness" / "fixtures" / "lifecycle" / "real-payload-candidates.jsonl"
        text = candidate_file.read_text(encoding="utf-8")
        for forbidden in ["비밀 사용자", "patient ABC", "민감한 답변", "secret-token-123"]:
            if forbidden in text:
                fail("lifecycle-fixture append leaked raw content: " + forbidden)
        listed = subprocess.run([str(LAZY / "bin" / "lazy"), "lifecycle-fixture", "list", "--format=json"], cwd=temp, env=env, text=True, capture_output=True, check=False)
        listed_json = json.loads(listed.stdout) if listed.stdout.strip() else {}
        listed_names = [candidate.get("name") for candidate in listed_json.get("candidates", [])]
        if listed.returncode != 0 or "fixture-intake-smoke" not in listed_names:
            fail("lifecycle-fixture list should include appended fixture even when host already has candidates:\n" + listed.stdout + listed.stderr)
        parity = subprocess.run([str(LAZY / "bin" / "lazy"), "lifecycle-parity", "--format=json", "--fail-on-mismatch"], cwd=temp, env=env, text=True, capture_output=True, check=False)
        if parity.returncode != 0:
            fail("lifecycle parity with intake candidate failed:\n" + parity.stdout + parity.stderr)
        parity_json = json.loads(parity.stdout)
        if parity_json.get("passed", 0) < 13:
            fail("lifecycle parity should include the appended candidate fixture: " + parity.stdout)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ lifecycle fixture intake CLI ok")


def check_capability_registry_cli_phase1() -> None:
    """Capability Registry Phase 1/2 stays non-blocking and supports add/list/resolve/audit."""
    script = LAZY / "scripts" / "capability.ts"
    if not script.exists():
        fail("capability CLI script missing")
    source = script.read_text(encoding="utf-8")
    forbidden = ["check-capability-boundary", "action-boundary", "block unless"]
    leaked = [phrase for phrase in forbidden if phrase in source]
    if leaked:
        fail("capability Phase 1 CLI must remain list/resolve/audit only; forbidden phrase(s): " + json.dumps(leaked, ensure_ascii=False))

    completed = subprocess.run([".lazy-harness/bin/lazy", "capability", "audit", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        fail("lazy capability audit failed:\n" + completed.stdout + completed.stderr)
    audit = json.loads(completed.stdout)
    if audit.get("ok") is not True:
        fail("capability audit should pass for current host registry, including empty host-owned registries: " + json.dumps(audit, ensure_ascii=False))

    manifest = json.loads((LAZY / "manifests" / "init-categories.json").read_text(encoding="utf-8"))
    manifest_paths = set()
    manifest_target_paths = set()
    for category in manifest.get("categories", {}).values():
        if not isinstance(category, dict):
            continue
        for item in category.get("items", []):
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("path"), str):
                manifest_paths.add(f".lazy-harness/{item['path']}")
            if isinstance(item.get("targetPath"), str):
                manifest_target_paths.add(f".lazy-harness/{item['targetPath']}")
    registry = json.loads((LAZY / "ssot" / "capabilities.json").read_text(encoding="utf-8"))
    missing_manifest_source_records = []
    for capability in registry.get("capabilities", []):
        if capability.get("owner") != "framework-global":
            continue
        source_record = capability.get("sourceRecord")
        if not isinstance(source_record, str) or not source_record.startswith(".lazy-harness/"):
            continue
        if not (ROOT / source_record).exists():
            fail("framework capability sourceRecord missing in source: " + source_record)
        if source_record not in manifest_paths and source_record not in manifest_target_paths:
            missing_manifest_source_records.append({"id": capability.get("id"), "sourceRecord": source_record})
    if missing_manifest_source_records:
        fail("framework capability sourceRecords missing from Category A sync manifest: " + json.dumps(missing_manifest_source_records, ensure_ascii=False))

    listed = subprocess.run([".lazy-harness/bin/lazy", "capability", "list", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if listed.returncode != 0:
        fail("lazy capability list failed:\n" + listed.stdout + listed.stderr)
    json.loads(listed.stdout)

    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-capability-audit-"))
    try:
        (temp / ".lazy-harness" / "ssot").mkdir(parents=True)
        (temp / ".lazy-harness" / "ssot" / "capability-registry.md").write_text("# Capability Registry\n", encoding="utf-8")
        (temp / ".lazy-harness" / "ssot" / "capabilities.json").write_text(
            json.dumps({
                "version": 1,
                "capabilities": [{
                    "id": "capability-registry-phase1",
                    "kind": "command",
                    "level": "discover",
                    "sourceRecord": ".lazy-harness/ssot/capability-registry.md",
                    "appliesWhen": ["finding_project_capabilities"],
                    "actions": ["lazy capability list"],
                    "description": "fixture capability",
                    "owner": "framework-global",
                }],
            }),
            encoding="utf-8",
        )
        fixture_env = env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp))
        fixture_list = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "capability", "list", "--format=json"],
            cwd=temp,
            env=fixture_env,
            text=True,
            capture_output=True,
            check=False,
        )
        if fixture_list.returncode != 0:
            fail("fixture lazy capability list failed:\n" + fixture_list.stdout + fixture_list.stderr)
        fixture_ids = [cap.get("id") for cap in json.loads(fixture_list.stdout).get("capabilities", [])]
        if "capability-registry-phase1" not in fixture_ids:
            fail("fixture capability list missing seed capability: " + fixture_list.stdout)
        resolved = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "capability", "resolve", "--intent", "finding_project_capabilities", "--format=json"],
            cwd=temp,
            env=fixture_env,
            text=True,
            capture_output=True,
            check=False,
        )
        if resolved.returncode != 0:
            fail("fixture lazy capability resolve failed:\n" + resolved.stdout + resolved.stderr)
        resolve_json = json.loads(resolved.stdout)
        matches = [cap.get("id") for cap in resolve_json.get("matches", [])]
        if matches[:1] != ["capability-registry-phase1"]:
            fail("fixture capability resolve did not return seed capability first: " + json.dumps(resolve_json, ensure_ascii=False))

        for record_name in ["script.md", "skill.md", "prompt.md", "validation.md"]:
            (temp / ".lazy-harness" / "ssot" / record_name).write_text(f"# {record_name}\n", encoding="utf-8")
        add_cases = [
            ["--id", "fixture-script", "--kind", "script", "--level", "default", "--source-record", ".lazy-harness/ssot/script.md", "--applies-when", "starting_work", "--entrypoint", "scripts/start.sh", "--description", "Fixture script", "--owner", "host-project", "--tag", "fixture,script"],
            ["--id", "fixture-skill", "--kind", "skill", "--level", "recommend", "--source-record", ".lazy-harness/ssot/skill.md", "--applies-when", "creating_release", "--skill-name", "/release-workflow", "--description", "Fixture skill", "--owner", "host-project"],
            ["--id", "fixture-prompt", "--kind", "prompt", "--level", "discover", "--source-record", ".lazy-harness/ssot/prompt.md", "--applies-when", "writing_pr_body", "--template-path", ".lazy-harness/prompts/pr.md", "--description", "Fixture prompt", "--owner", "team-policy"],
            ["--id", "fixture-validation", "--kind", "validation", "--level", "default", "--source-record", ".lazy-harness/ssot/validation.md", "--applies-when", "validating_changes", "--entrypoint", "bun lint", "--action", "bun lint", "--description", "Fixture validation", "--owner", "host-project"],
        ]
        for add_args in add_cases:
            added = subprocess.run(
                [str(LAZY / "bin" / "lazy"), "capability", "add", *add_args, "--format=json"],
                cwd=temp,
                env=fixture_env,
                text=True,
                capture_output=True,
                check=False,
            )
            if added.returncode != 0:
                fail("capability add fixture failed:\n" + added.stdout + added.stderr)
            added_json = json.loads(added.stdout)
            if added_json.get("ok") is not True or added_json.get("status") not in {"created", "updated", "unchanged"}:
                fail("capability add fixture emitted unexpected JSON: " + added.stdout)
        again = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "capability", "add", *add_cases[0], "--format=json"],
            cwd=temp,
            env=fixture_env,
            text=True,
            capture_output=True,
            check=False,
        )
        if again.returncode != 0 or json.loads(again.stdout).get("status") != "unchanged":
            fail("capability add should be idempotent unchanged on repeated same input:\n" + again.stdout + again.stderr)
        registry = json.loads((temp / ".lazy-harness" / "ssot" / "capabilities.json").read_text(encoding="utf-8"))
        fixture_ids_after_add = [cap.get("id") for cap in registry.get("capabilities", [])]
        if fixture_ids_after_add != sorted(fixture_ids_after_add):
            fail("capability add should write deterministic id-sorted registry: " + json.dumps(fixture_ids_after_add, ensure_ascii=False))
        for expected in ["fixture-script", "fixture-skill", "fixture-prompt", "fixture-validation"]:
            if expected not in fixture_ids_after_add:
                fail("capability add missing expected id " + expected + ": " + json.dumps(registry, ensure_ascii=False))
        repeated = subprocess.run(
            [
                str(LAZY / "bin" / "lazy"), "capability", "add",
                "--id", "fixture-repeated",
                "--kind", "validation",
                "--level", "recommend",
                "--source-record", ".lazy-harness/ssot/validation.md",
                "--applies-when", "validating_changes",
                "--applies-when", "before_commit",
                "--entrypoint", "bun lint && bun test",
                "--action", "bun lint",
                "--action", "bun test",
                "--description", "Fixture repeated flags",
                "--owner", "host-project",
                "--tag", "fixture",
                "--tag", "repeat",
                "--format=json",
            ],
            cwd=temp,
            env=fixture_env,
            text=True,
            capture_output=True,
            check=False,
        )
        if repeated.returncode != 0:
            fail("capability add should accept repeated multi-value flags:\n" + repeated.stdout + repeated.stderr)
        repeated_cap = json.loads(repeated.stdout).get("capability", {})
        if repeated_cap.get("appliesWhen") != ["validating_changes", "before_commit"] or repeated_cap.get("actions") != ["bun lint", "bun test"] or repeated_cap.get("tags") != ["fixture", "repeat"]:
            fail("capability add repeated flags should preserve all values: " + repeated.stdout)
        resolved_validation = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "capability", "resolve", "--intent", "validating_changes", "--format=json"],
            cwd=temp,
            env=fixture_env,
            text=True,
            capture_output=True,
            check=False,
        )
        if resolved_validation.returncode != 0 or "fixture-validation" not in [cap.get("id") for cap in json.loads(resolved_validation.stdout).get("matches", [])]:
            fail("capability resolve should find added validation capability:\n" + resolved_validation.stdout + resolved_validation.stderr)
        graph_text = (temp / ".lazy-harness" / "knowledge" / "graph.jsonl").read_text(encoding="utf-8")
        if "capability_fixture-validation" not in graph_text:
            fail("capability add should upsert graph entry for added capabilities")

        (temp / "package.json").write_text(
            json.dumps({
                "name": "fixture-app",
                "packageManager": "bun@1.2.0",
                "scripts": {
                    "lint": "eslint .",
                    "typecheck": "tsc --noEmit",
                    "test:run": "vitest run",
                },
            }),
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "tests").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "tests" / "test-strategy.xml").write_text("<test-strategy />\n", encoding="utf-8")
        (temp / ".lazy-harness" / "ssot" / "release-branch-policy.md").write_text("# Release branch policy\n", encoding="utf-8")
        candidates = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "capability", "candidates", "--format=json"],
            cwd=temp,
            env=fixture_env,
            text=True,
            capture_output=True,
            check=False,
        )
        if candidates.returncode != 0:
            fail("capability candidates should be read-only and successful:\n" + candidates.stdout + candidates.stderr)
        candidate_json = json.loads(candidates.stdout)
        candidate_ids = {entry.get("id") for entry in candidate_json.get("candidates", [])}
        if "fixture-app-baseline-app-validation" not in candidate_ids:
            fail("capability candidates should detect missing package-script app validation: " + candidates.stdout)
        if "fixture-skill-action-coverage" not in candidate_ids:
            fail("capability candidates should detect release action coverage gaps: " + candidates.stdout)

        (temp / ".lazy-harness" / "ssot" / "capabilities.json").write_text(
            json.dumps({
                "version": 1,
                "capabilities": [{
                    "id": "broken",
                    "kind": "script",
                    "level": "recommend",
                    "sourceRecord": ".lazy-harness/ssot/missing.md",
                    "appliesWhen": ["x"],
                    "description": "missing source record",
                    "owner": "host-project",
                }],
            }),
            encoding="utf-8",
        )
        bad = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "capability", "audit", "--format=json"],
            cwd=temp,
            env=fixture_env,
            text=True,
            capture_output=True,
            check=False,
        )
        if bad.returncode == 0:
            fail("capability audit should fail missing sourceRecord")
        bad_json = json.loads(bad.stdout)
        if not any("missing sourceRecord" in issue.get("message", "") for issue in bad_json.get("issues", [])):
            fail("capability audit missing-source error not reported: " + json.dumps(bad_json, ensure_ascii=False))
    finally:
        shutil.rmtree(temp, ignore_errors=True)

    print("✓ capability registry Phase 1/2 CLI ok")


def check_project_operating_rulebook_cli() -> None:
    """Project operating rulebook stays separate from fact records and resolves rule-backed actions."""
    script = LAZY / "scripts" / "rulebook.ts"
    if not script.exists():
        fail("rulebook CLI script missing")

    root_audit = subprocess.run([".lazy-harness/bin/lazy", "rules", "audit", "--strict", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if root_audit.returncode != 0:
        fail("source lazy rules audit --strict failed:\n" + root_audit.stdout + root_audit.stderr)
    root_audit_json = json.loads(root_audit.stdout)
    if root_audit_json.get("ok") is not True or root_audit_json.get("count", 0) < 1:
        fail("source rulebook audit should pass and see at least README: " + root_audit.stdout)

    def assert_rulebook_compat_boundary(payload: dict, label: str) -> None:
        if payload.get("schemaVersion") != "rulebook-compatibility/v1":
            fail(f"{label} must expose rulebook compatibility schema boundary: " + json.dumps(payload, ensure_ascii=False))
        if payload.get("retiredCanonicalSemantics") is not True:
            fail(f"{label} must mark rulebook canonical semantics retired: " + json.dumps(payload, ensure_ascii=False))
        if payload.get("canonicalPolicySource") != ".lazy-harness/ssot/policies.json":
            fail(f"{label} must point to typed policy canonical source: " + json.dumps(payload, ensure_ascii=False))
        if payload.get("semanticAuthority") != "typed-policy-registry":
            fail(f"{label} must keep semantic authority on typed policy registry: " + json.dumps(payload, ensure_ascii=False))

    assert_rulebook_compat_boundary(root_audit_json, "source lazy rules audit")
    root_list = subprocess.run([".lazy-harness/bin/lazy", "rules", "list", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if root_list.returncode != 0:
        fail("source lazy rules list failed:\n" + root_list.stdout + root_list.stderr)
    root_list_json = json.loads(root_list.stdout)
    assert_rulebook_compat_boundary(root_list_json, "source lazy rules list")
    source_rules = {rule.get("path"): rule for rule in root_list_json.get("rules", [])}
    if source_rules.get(".lazy-harness/rules/README.md", {}).get("relatedPolicy") != "project-operating-rulebook-policy":
        fail("source rulebook README must surface related typed policy in list output: " + root_list.stdout)
    source_capabilities = json.loads((ROOT / ".lazy-harness" / "ssot" / "capabilities.json").read_text(encoding="utf-8"))
    project_rulebook_capability = next((cap for cap in source_capabilities.get("capabilities", []) if cap.get("id") == "project-operating-rulebook"), None)
    if not project_rulebook_capability or "project-operating-rulebook-policy" not in project_rulebook_capability.get("policyIds", []):
        fail("source project-operating-rulebook capability must link typed policy coverage")

    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-rulebook-cli-"))
    try:
        (temp / ".lazy-harness" / "rules").mkdir(parents=True)
        (temp / ".lazy-harness" / "ssot").mkdir(parents=True)
        (temp / ".lazy-harness" / "rules" / "dev-worktree.md").write_text(
            """# Dev Worktree Operating Rule

Status: active
Layer: Rulebook
Scope: host-project
Owner: fixture
Level: warn
Related capability: dev-worktree-standard-command
Related records:
- `.lazy-harness/spec/infra/dev-worktree-instances.md`

## Rule digest

- Applies when:
  - creating_worktree
  - starting_dev_instance
- Prefer:
  - `bun run wt new`
  - `bun run dev:instance`
- Avoid:
  - raw `git worktree add`
  - raw `bun run dev`
- Requires:
  - inspect project operating rule before creating worktrees or starting dev servers
- Bypass:
  - allowed only with explicit user confirmation and reason
- Record completion:
  - update capability binding when command wrappers change

## Operating rule

Use the host worktree and dev-instance wrappers instead of raw git worktree or raw dev-server commands.

## Examples

- Good: `bun run wt new feature/foo --base develop`
- Good: `bun run dev:instance -- --instance feature-foo`
- Avoid: `git worktree add ../foo feature/foo`
- Avoid: `bun run dev`

## Capability binding

- Capability id: dev-worktree-standard-command
- Preferred actions: `bun run wt new`, `bun run dev:instance`
- Discouraged actions: `git worktree add`, `bun run dev`
- Intent labels: creating_worktree, starting_dev_instance
- Enforcement level: warn

## Implementation map

- Source records: `.lazy-harness/spec/infra/dev-worktree-instances.md`
- Capabilities: `dev-worktree-standard-command`
- Validation: `lazy rules audit --strict`
- Tests: `.lazy-harness/tests/project-operating-rulebook.md`
""",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "ssot" / "capabilities.json").write_text(
            json.dumps({
                "version": 1,
                "capabilities": [{
                    "id": "dev-worktree-standard-command",
                    "kind": "command",
                    "level": "warn",
                    "sourceRecord": ".lazy-harness/rules/dev-worktree.md",
                    "rulebookRecord": ".lazy-harness/rules/dev-worktree.md",
                    "appliesWhen": ["creating_worktree", "starting_dev_instance"],
                    "preferredActions": ["bun run wt new", "bun run dev:instance"],
                    "discouragedActions": ["git worktree add", "bun run dev"],
                    "entrypoint": "bun run wt new / bun run dev:instance",
                    "requiresReasonForBypass": True,
                    "description": "Use host worktree/dev-instance wrappers instead of raw commands.",
                    "owner": "host-project",
                    "tags": ["rulebook", "worktree", "dev-instance"],
                }],
            }),
            encoding="utf-8",
        )
        env = env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp))
        listed = subprocess.run([str(LAZY / "bin" / "lazy"), "rules", "list", "--format=json"], cwd=temp, env=env, text=True, capture_output=True, check=False)
        if listed.returncode != 0:
            fail("lazy rules list fixture failed:\n" + listed.stdout + listed.stderr)
        listed_json = json.loads(listed.stdout)
        assert_rulebook_compat_boundary(listed_json, "fixture lazy rules list")
        if [rule.get("path") for rule in listed_json.get("rules", [])] != [".lazy-harness/rules/dev-worktree.md"]:
            fail("lazy rules list should parse fixture rulebook entry: " + listed.stdout)

        audit = subprocess.run([str(LAZY / "bin" / "lazy"), "rules", "audit", "--strict", "--format=json"], cwd=temp, env=env, text=True, capture_output=True, check=False)
        if audit.returncode != 0:
            fail("lazy rules audit --strict fixture failed:\n" + audit.stdout + audit.stderr)
        audit_json = json.loads(audit.stdout)
        assert_rulebook_compat_boundary(audit_json, "fixture lazy rules audit")
        if audit_json.get("ok") is not True or audit_json.get("count") != 1:
            fail("lazy rules audit fixture should pass exactly one rule: " + audit.stdout)

        resolved_rule = subprocess.run([str(LAZY / "bin" / "lazy"), "rules", "resolve", "--action", "git worktree add feature/foo", "--format=json"], cwd=temp, env=env, text=True, capture_output=True, check=False)
        if resolved_rule.returncode != 0:
            fail("lazy rules resolve discouraged action failed:\n" + resolved_rule.stdout + resolved_rule.stderr)
        rule_json = json.loads(resolved_rule.stdout)
        assert_rulebook_compat_boundary(rule_json, "fixture lazy rules resolve")
        if rule_json.get("enforcement") != "compatibility-advisory":
            fail("lazy rules resolve should be compatibility-advisory after semantic retirement: " + resolved_rule.stdout)
        matches = rule_json.get("matches", [])
        if not matches or matches[0].get("matchType") != "discouraged-action":
            fail("lazy rules resolve should match discouraged raw worktree command: " + resolved_rule.stdout)
        cap = matches[0].get("capability", {})
        if "bun run wt new" not in cap.get("preferredActions", []):
            fail("lazy rules resolve should show preferred worktree command: " + resolved_rule.stdout)

        resolved_cap = subprocess.run([str(LAZY / "bin" / "lazy"), "capability", "resolve", "--action", "git worktree add feature/foo", "--format=json"], cwd=temp, env=env, text=True, capture_output=True, check=False)
        if resolved_cap.returncode != 0:
            fail("lazy capability resolve discouraged action failed:\n" + resolved_cap.stdout + resolved_cap.stderr)
        cap_matches = [cap.get("id") for cap in json.loads(resolved_cap.stdout).get("matches", [])]
        if cap_matches[:1] != ["dev-worktree-standard-command"]:
            fail("capability resolve should match discouragedActions-backed capability: " + resolved_cap.stdout)

        broken = json.loads((temp / ".lazy-harness" / "ssot" / "capabilities.json").read_text(encoding="utf-8"))
        broken["capabilities"][0]["rulebookRecord"] = ".lazy-harness/rules/missing.md"
        (temp / ".lazy-harness" / "ssot" / "capabilities.json").write_text(json.dumps(broken), encoding="utf-8")
        bad = subprocess.run([str(LAZY / "bin" / "lazy"), "rules", "audit", "--strict", "--format=json"], cwd=temp, env=env, text=True, capture_output=True, check=False)
        if bad.returncode == 0:
            fail("lazy rules audit should fail missing rulebookRecord")
        bad_json = json.loads(bad.stdout)
        assert_rulebook_compat_boundary(bad_json, "fixture broken lazy rules audit")
        if not any("missing rulebookRecord" in issue.get("message", "") for issue in bad_json.get("issues", [])):
            fail("lazy rules audit missing rulebookRecord error not reported: " + bad.stdout)
    finally:
        shutil.rmtree(temp, ignore_errors=True)

    print("✓ project operating rulebook CLI ok")


def check_purpose_scoped_retrieval_cli() -> None:
    """lazy find keeps retrieval spaces purpose-scoped and cue-only."""
    script = LAZY / "scripts" / "purpose-find.ts"
    if not script.exists():
        fail("purpose-scoped retrieval CLI script missing")
    source = script.read_text(encoding="utf-8")
    forbidden = ["lazy route", "route-summary", "raw prompt classifier", "requiredRead", "next-action"]
    leaked = [phrase for phrase in forbidden if phrase in source]
    if leaked:
        fail("purpose-find must not reintroduce route/raw-prompt/required-read semantics: " + json.dumps(leaked, ensure_ascii=False))

    core = pathlib.Path(tempfile.mkdtemp(prefix="lazy-purpose-core-"))
    try:
        (core / ".lazy-harness" / "rules").mkdir(parents=True)
        (core / ".lazy-harness" / "tests").mkdir(parents=True)
        (core / ".lazy-harness" / "spec" / "platform").mkdir(parents=True)
        (core / ".lazy-harness" / "decisions").mkdir(parents=True)
        (core / ".lazy-harness" / "ssot").mkdir(parents=True)
        (core / ".lazy-harness" / "rules" / "project-policy-storage.md").write_text(
            """# Project Policy Storage Rule

Status: active
Layer: Rulebook

## Rule digest

- Applies when: project policy storage
- Prefer: `.lazy-harness/rules/**` for operating policies

## Operating rule

Project policy storage belongs in the rulebook surface for purpose-scoped retrieval tests.
""",
            encoding="utf-8",
        )
        (core / ".lazy-harness" / "tests" / "purpose-scoped-retrieval.md").write_text(
            """# Purpose-Scoped Retrieval Regression

Status: accepted
Layer: TDD

## Regression

Purpose scoped retrieval must find TDD records for test purpose before widening to fact or decision records.
""",
            encoding="utf-8",
        )
        (core / ".lazy-harness" / "decisions" / "purpose-scoped-retrieval.md").write_text(
            """# Purpose Scoped Retrieval Decision

Status: accepted
Layer: ADR

This broad decision intentionally mentions purpose scoped retrieval but must not appear in test-purpose records.
""",
            encoding="utf-8",
        )
        (core / ".lazy-harness" / "spec" / "platform" / "capability-resolution.md").write_text(
            """# Capability Resolution

Status: accepted
Layer: SDD

Capability resolution fact records are returned for fact purpose retrieval.
""",
            encoding="utf-8",
        )
        (core / ".lazy-harness" / "ssot" / "capabilities.json").write_text(
            json.dumps({
                "version": 1,
                "capabilities": [{
                    "id": "retrieval-purpose-test",
                    "kind": "command",
                    "level": "recommend",
                    "sourceRecord": ".lazy-harness/spec/platform/purpose-scoped-retrieval.md",
                    "appliesWhen": ["retrieval_test"],
                    "preferredActions": ["lazy find --purpose test"],
                    "description": "Use test purpose retrieval for validation and TDD surfaces.",
                    "owner": "framework-fixture",
                    "tags": ["purpose", "retrieval", "test", "validation"],
                }],
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        env = env_without_lazy_runtime(LAZY_HOST_ROOT=str(core))
        lazy_cmd = str(LAZY / "bin" / "lazy")

        missing = subprocess.run([lazy_cmd, "find", "project policy", "--format=json"], cwd=core, env=env, text=True, capture_output=True, check=False)
        if missing.returncode == 0 or "requires --purpose" not in (missing.stderr + missing.stdout):
            fail("lazy find should require explicit --purpose")

        rulebook = subprocess.run([lazy_cmd, "find", "--purpose", "rulebook", "project policy storage", "--format=json"], cwd=core, env=env, text=True, capture_output=True, check=False)
        if rulebook.returncode != 0:
            fail("lazy find --purpose rulebook failed:\n" + rulebook.stdout + rulebook.stderr)
        rulebook_json = json.loads(rulebook.stdout)
        if rulebook_json.get("purpose") != "rulebook" or "rules" not in rulebook_json.get("searchSpaces", []):
            fail("rulebook purpose should report rules search space: " + rulebook.stdout)
        if rulebook_json.get("candidates", {}).get("records"):
            fail("rulebook purpose should not default to broad record candidates: " + rulebook.stdout)
        if not rulebook_json.get("candidates", {}).get("rules"):
            fail("rulebook purpose should return rule candidates: " + rulebook.stdout)

        test = subprocess.run([lazy_cmd, "find", "--purpose", "test", "purpose scoped retrieval", "--format=json"], cwd=core, env=env, text=True, capture_output=True, check=False)
        if test.returncode != 0:
            fail("lazy find --purpose test failed:\n" + test.stdout + test.stderr)
        test_json = json.loads(test.stdout)
        test_records = [entry.get("path") for entry in test_json.get("candidates", {}).get("records", [])]
        if ".lazy-harness/tests/purpose-scoped-retrieval.md" not in test_records:
            fail("test purpose should surface purpose-scoped TDD record: " + test.stdout)
        if any(str(path).startswith(".lazy-harness/decisions/") for path in test_records):
            fail("test purpose should not default to ADR/fact record sweep: " + test.stdout)

        fact = subprocess.run([lazy_cmd, "find", "--purpose", "fact", "capability resolution", "--format=json"], cwd=core, env=env, text=True, capture_output=True, check=False)
        if fact.returncode != 0:
            fail("lazy find --purpose fact failed:\n" + fact.stdout + fact.stderr)
        fact_records = [entry.get("path") for entry in json.loads(fact.stdout).get("candidates", {}).get("records", [])]
        if ".lazy-harness/spec/platform/capability-resolution.md" not in fact_records:
            fail("fact purpose should surface capability resolution record: " + fact.stdout)

        arch = subprocess.run([lazy_cmd, "find", "--purpose", "architecture", "purpose scoped retrieval", "--format=json"], cwd=core, env=env, text=True, capture_output=True, check=False)
        if arch.returncode != 0:
            fail("lazy find --purpose architecture failed:\n" + arch.stdout + arch.stderr)
        spaces = set(json.loads(arch.stdout).get("searchSpaces", []))
        if not {"overview", "records", "rules", "capabilities", "source", "tests", "graph"}.issubset(spaces):
            fail("architecture purpose should include broad search spaces: " + arch.stdout)

        cap = subprocess.run([lazy_cmd, "capability", "resolve", "--intent", "retrieval_test", "--format=json"], cwd=core, env=env, text=True, capture_output=True, check=False)
        if cap.returncode != 0:
            fail("retrieval purpose capability resolve failed:\n" + cap.stdout + cap.stderr)
    finally:
        shutil.rmtree(core, ignore_errors=True)


    dogfood = pathlib.Path(tempfile.mkdtemp(prefix="lazy-purpose-dogfood-"))
    try:
        (dogfood / ".lazy-harness" / "rules").mkdir(parents=True)
        (dogfood / ".lazy-harness" / "ssot").mkdir(parents=True)
        (dogfood / ".lazy-harness" / "spec" / "infra").mkdir(parents=True)
        (dogfood / ".lazy-harness" / "tests").mkdir(parents=True)
        (dogfood / "tests").mkdir(parents=True)
        (dogfood / ".lazy-harness" / "rules" / "dev-worktree.md").write_text(
            """# Dev Worktree Operating Rule

Status: active
Layer: Rulebook
Scope: host-project
Owner: fixture
Level: warn
Related capability: dev-worktree-standard-command
Related records:
- `.lazy-harness/spec/infra/dev-worktree-instances.md`

## Rule digest

- Applies when:
  - creating_worktree
  - starting_dev_instance
- Prefer:
  - `bun run wt new`
  - `bun run dev:instance`
- Avoid:
  - raw `git worktree add`
  - raw `bun run dev`
- Requires:
  - use project wrappers for dogfood worktree/dev-instance sessions
- Bypass:
  - explicit user confirmation and reason required
- Record completion:
  - update capability binding when wrappers change

## Operating rule

Use the host worktree and dev-instance wrappers instead of raw git worktree or raw dev-server commands.

## Capability binding

- Capability id: dev-worktree-standard-command
- Preferred actions: `bun run wt new`, `bun run dev:instance`
- Discouraged actions: `git worktree add`, `bun run dev`
- Intent labels: creating_worktree, starting_dev_instance
- Enforcement level: warn

## Implementation map

- Source records: `.lazy-harness/spec/infra/dev-worktree-instances.md`
- Capabilities: `dev-worktree-standard-command`
- Tests: `.lazy-harness/tests/dev-worktree-instances.md`
""",
            encoding="utf-8",
        )
        (dogfood / ".lazy-harness" / "spec" / "infra" / "dev-worktree-instances.md").write_text(
            """# Dev Worktree Instances

Status: accepted
Layer: SDD

## Rule digest

- Worktree wrapper: `bun run wt new <branch> --base develop`
- Dev instance wrapper: `bun run dev:instance -- --instance <name|auto>`
- Inspect URL: `bun run dev:inspect <name>`

## Implementation map

- Commands: `bun run wt new`, `bun run dev:instance`, `bun run dev:inspect`
""",
            encoding="utf-8",
        )
        (dogfood / ".lazy-harness" / "tests" / "dev-worktree-instances.md").write_text(
            """# Dev Worktree Instance Regression

Status: accepted
Layer: TDD

## Regression

Purpose-scoped retrieval must find worktree/dev-instance validation surfaces without broad fact record sweeps.

## Implementation map

- Protected command wrapper: `bun run wt new`
- Protected dev instance wrapper: `bun run dev:instance`
""",
            encoding="utf-8",
        )
        (dogfood / "tests" / "dev-worktree.spec.ts").write_text(
            """describe('dev worktree instance wrappers', () => {
  it('documents bun run wt new and bun run dev:instance dogfood validation', () => {})
})
""",
            encoding="utf-8",
        )
        (dogfood / ".lazy-harness" / "ssot" / "capabilities.json").write_text(
            json.dumps({
                "version": 1,
                "capabilities": [{
                    "id": "dev-worktree-standard-command",
                    "kind": "command",
                    "level": "warn",
                    "sourceRecord": ".lazy-harness/rules/dev-worktree.md",
                    "rulebookRecord": ".lazy-harness/rules/dev-worktree.md",
                    "appliesWhen": ["creating_worktree", "starting_dev_instance"],
                    "preferredActions": ["bun run wt new", "bun run dev:instance", "bun run dev:inspect"],
                    "discouragedActions": ["git worktree add", "bun run dev"],
                    "entrypoint": "bun run wt new / bun run dev:instance",
                    "requiresReasonForBypass": True,
                    "description": "Dogfood fixture for project worktree/dev-instance wrapper retrieval.",
                    "owner": "host-project",
                    "tags": ["rulebook", "worktree", "dev-instance"],
                }],
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        env = env_without_lazy_runtime(LAZY_HOST_ROOT=str(dogfood))
        dog_rulebook = subprocess.run([str(LAZY / "bin" / "lazy"), "find", "--purpose", "rulebook", "git worktree add", "--format=json"], cwd=dogfood, env=env, text=True, capture_output=True, check=False)
        if dog_rulebook.returncode != 0:
            fail("dogfood rulebook purpose search failed:\n" + dog_rulebook.stdout + dog_rulebook.stderr)
        dog_rulebook_json = json.loads(dog_rulebook.stdout)
        if dog_rulebook_json.get("candidates", {}).get("records"):
            fail("dogfood rulebook purpose must not default to fact records: " + dog_rulebook.stdout)
        if ".lazy-harness/rules/dev-worktree.md" not in [entry.get("path") for entry in dog_rulebook_json.get("candidates", {}).get("rules", [])]:
            fail("dogfood rulebook purpose should find worktree operating rule: " + dog_rulebook.stdout)
        if "dev-worktree-standard-command" not in [entry.get("id") for entry in dog_rulebook_json.get("candidates", {}).get("capabilities", [])]:
            fail("dogfood rulebook purpose should find worktree capability: " + dog_rulebook.stdout)

        dog_test = subprocess.run([str(LAZY / "bin" / "lazy"), "find", "--purpose", "test", "worktree dev instance", "--format=json"], cwd=dogfood, env=env, text=True, capture_output=True, check=False)
        if dog_test.returncode != 0:
            fail("dogfood test purpose search failed:\n" + dog_test.stdout + dog_test.stderr)
        dog_test_json = json.loads(dog_test.stdout)
        dog_test_records = [entry.get("path") for entry in dog_test_json.get("candidates", {}).get("records", [])]
        dog_test_files = [entry.get("path") for entry in dog_test_json.get("candidates", {}).get("testFiles", [])]
        if ".lazy-harness/tests/dev-worktree-instances.md" not in dog_test_records:
            fail("dogfood test purpose should find TDD worktree record: " + dog_test.stdout)
        if "tests/dev-worktree.spec.ts" not in dog_test_files:
            fail("dogfood test purpose should find source test file: " + dog_test.stdout)
        if any(str(path).startswith(".lazy-harness/spec/") for path in dog_test_records):
            fail("dogfood test purpose should not default to SDD fact records: " + dog_test.stdout)

        dog_fact = subprocess.run([str(LAZY / "bin" / "lazy"), "find", "--purpose", "fact", "dev worktree instances", "--format=json"], cwd=dogfood, env=env, text=True, capture_output=True, check=False)
        if dog_fact.returncode != 0:
            fail("dogfood fact purpose search failed:\n" + dog_fact.stdout + dog_fact.stderr)
        dog_fact_records = [entry.get("path") for entry in json.loads(dog_fact.stdout).get("candidates", {}).get("records", [])]
        if ".lazy-harness/spec/infra/dev-worktree-instances.md" not in dog_fact_records:
            fail("dogfood fact purpose should find dev-worktree SDD fact record: " + dog_fact.stdout)

        dog_capability = subprocess.run([str(LAZY / "bin" / "lazy"), "find", "--purpose", "capability", "git worktree add", "--format=json"], cwd=dogfood, env=env, text=True, capture_output=True, check=False)
        if dog_capability.returncode != 0:
            fail("dogfood capability purpose search failed:\n" + dog_capability.stdout + dog_capability.stderr)
        if "dev-worktree-standard-command" not in [entry.get("id") for entry in json.loads(dog_capability.stdout).get("candidates", {}).get("capabilities", [])]:
            fail("dogfood capability purpose should find discouraged raw worktree capability: " + dog_capability.stdout)
    finally:
        shutil.rmtree(dogfood, ignore_errors=True)

    cap_ids = [entry.get("id") for entry in json.loads(cap.stdout).get("matches", [])]
    if "retrieval-purpose-test" not in cap_ids:
        fail("retrieval_test capability should resolve to retrieval-purpose-test: " + cap.stdout)

    print("✓ purpose-scoped retrieval CLI ok")


def check_response_completed_no_auto_route_telemetry() -> None:
    """response.completed must not automatically run route/user-text classifiers; hook timing still works."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="no_route_auto_"))
    try:
        shutil.copytree(ROOT / ".lazy-harness", temp / ".lazy-harness", ignore=shutil.ignore_patterns(".cache", "state"))
        subprocess.run(["git", "init", "-q"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        telemetry = temp / ".git" / "lazy-harness" / "shared" / "logs" / "route-decisions.jsonl"
        if telemetry.exists():
            telemetry.unlink()
        timings = temp / ".lazy-harness" / "logs" / "hook-timings.jsonl"
        if timings.exists():
            timings.unlink()
        payload = {
            "last_user_message": "fix a button click behavior bug",
            "message_id": "no-route-msg-1",
            "recent_tool_calls": [],
        }
        large_payload = {
            "last_user_message": "fix route telemetry for large response payloads",
            "message_id": "no-route-msg-large",
            "recent_tool_calls": [{"name": "read", "args_preview": "x" * 160000}],
        }
        hook = temp / ".lazy-harness" / "hooks" / "lifecycle" / "on-response-completed.sh"
        for _ in range(2):
            completed = subprocess.run(
                [str(hook)],
                cwd=temp,
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                check=False,
                env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp), LAZY_HOOK_TIMING_LOG=str(timings)),
            )
            if completed.returncode != 0:
                fail("response.completed hook should stay best-effort without auto route telemetry:\n" + completed.stdout + completed.stderr)
        large_completed = subprocess.run(
            [str(hook)],
            cwd=temp,
            input=json.dumps(large_payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp), LAZY_HOOK_TIMING_LOG=str(timings)),
        )
        if large_completed.returncode != 0:
            fail("response.completed hook should tolerate live-sized payloads without auto route telemetry:\n" + large_completed.stdout + large_completed.stderr)
        if telemetry.exists():
            fail("response.completed must not auto-create route telemetry from raw user text")
        if not timings.exists():
            fail("response.completed hook should create timing telemetry in measure-only mode")
        timing_entries = [json.loads(line) for line in timings.read_text(encoding="utf-8").splitlines() if line.strip()]
        components = {entry.get("component") for entry in timing_entries}
        if "route-telemetry" in components:
            fail("hook timings must not include route-telemetry after task-router removal: " + json.dumps(sorted(components), ensure_ascii=False))
        if "hook-total" not in components:
            fail("hook timings should include hook-total component: " + json.dumps(sorted(components), ensure_ascii=False))
        if not any(str(component).endswith("check-bdd-trigger.sh") for component in components):
            fail("hook timings should include lifecycle helper components that are not write-only fast-pathed")
        if any("durationMs" not in entry or "outputEmitted" not in entry or "exitCode" not in entry for entry in timing_entries):
            fail("hook timing entries missing required fields")
        summary_completed = subprocess.run(
            [str(temp / ".lazy-harness" / "bin" / "lazy"), "hook-timings", "--format=json", "--limit=100"],
            cwd=temp,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp), LAZY_HOOK_TIMING_LOG=str(timings)),
            text=True,
            capture_output=True,
            check=False,
        )
        if summary_completed.returncode != 0:
            fail("lazy hook-timings summary failed:\n" + summary_completed.stdout + summary_completed.stderr)
        summary = json.loads(summary_completed.stdout)
        if summary.get("mode") != "hook-timing-summary" or summary.get("rows", 0) < len(timing_entries):
            fail("hook timing summary should report timing rows: " + summary_completed.stdout[:500])

        manual_session_log = temp / ".git" / "lazy-harness" / "runtime" / "session-manual" / "logs" / "hook-timings.jsonl"
        manual_session_log.parent.mkdir(parents=True, exist_ok=True)
        manual_session_log.write_text(
            json.dumps({"ts": "2000-01-01T00:00:00Z", "component": "manual-old", "durationMs": 1, "exitCode": 0, "outputEmitted": False})
            + "\n"
            + json.dumps({"ts": "2099-01-01T00:00:00Z", "component": "manual-new", "durationMs": 7, "exitCode": 0, "outputEmitted": False})
            + "\n",
            encoding="utf-8",
        )
        all_sessions_completed = subprocess.run(
            [str(temp / ".lazy-harness" / "bin" / "lazy"), "hook-timings", "--format=json", "--all-sessions", "--since", "2099-01-01T00:00:00Z"],
            cwd=temp,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            text=True,
            capture_output=True,
            check=False,
        )
        if all_sessions_completed.returncode != 0:
            fail("lazy hook-timings --all-sessions --since failed:\n" + all_sessions_completed.stdout + all_sessions_completed.stderr)
        all_sessions_summary = json.loads(all_sessions_completed.stdout)
        all_session_components = {item.get("component"): item for item in all_sessions_summary.get("components", [])}
        if all_sessions_summary.get("mode") != "hook-timing-summary" or all_sessions_summary.get("allSessions") is not True:
            fail("hook timing all-sessions summary should report aggregation mode: " + all_sessions_completed.stdout[:500])
        if all_sessions_summary.get("rows") != 1 or "manual-new" not in all_session_components or "manual-old" in all_session_components:
            fail("hook timing --since should aggregate session logs and filter old rows: " + all_sessions_completed.stdout[:800])
        if all_sessions_summary.get("logCount", 0) < 2:
            fail("hook timing --all-sessions should report multiple log sources: " + all_sessions_completed.stdout[:800])

        write_only_helpers = {
            ".lazy-harness/hooks/lifecycle/helpers/check-layer-impact.sh",
            ".lazy-harness/hooks/lifecycle/helpers/check-ddd-trigger.sh",
            ".lazy-harness/hooks/lifecycle/helpers/check-ssot-trigger.sh",
            ".lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh",
            ".lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh",
            ".lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh",
        }

        def run_hook_with_timing(payload_obj: dict, log_name: str, extra_env: dict[str, str] | None = None) -> set[str]:
            log_path = temp / ".lazy-harness" / "logs" / log_name
            log_path.unlink(missing_ok=True)
            env = env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp), LAZY_HOOK_TIMING_LOG=str(log_path))
            if extra_env:
                env.update(extra_env)
            completed = subprocess.run(
                [str(hook)],
                cwd=temp,
                input=json.dumps(payload_obj, ensure_ascii=False),
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            if completed.returncode != 0:
                fail("response.completed hook fast-path fixture failed:\n" + completed.stdout + completed.stderr)
            entries = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            return {str(entry.get("component")) for entry in entries}

        read_only_components = run_hook_with_timing(
            {"message_id": "fastpath-readonly", "recent_tool_calls": [{"name": "read", "args_preview": ".lazy-harness/spec/platform/hook-performance-measurement.md"}]},
            "hook-timings-readonly.jsonl",
        )
        if write_only_helpers & read_only_components:
            fail("read-only fast-path must skip only write-only helpers: " + json.dumps(sorted(write_only_helpers & read_only_components), ensure_ascii=False))
        if ".lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh" not in read_only_components:
            fail("read-only fast-path must keep non-write-only helpers on the full path")

        unknown_components = run_hook_with_timing(
            {"message_id": "fastpath-unknown", "recent_tool_calls": [{"name": "bash", "args_preview": "echo maybe writes"}]},
            "hook-timings-unknown.jsonl",
        )
        if not write_only_helpers.issubset(unknown_components):
            fail("unknown/non-read-only tools must fall back to all write-only helpers")

        missing_field_components = run_hook_with_timing(
            {"message_id": "fastpath-missing-field"},
            "hook-timings-missing-field.jsonl",
        )
        if not write_only_helpers.issubset(missing_field_components):
            fail("payloads without recent_tool_calls must fall back to all write-only helpers")

        orchestrator_components = run_hook_with_timing(
            {"message_id": "engine-orchestrator", "recent_tool_calls": [{"name": "read", "args_preview": ".lazy-harness/spec/platform/hook-performance-measurement.md"}]},
            "hook-timings-orchestrator.jsonl",
            {"LAZY_RESPONSE_COMPLETED_ENGINE": "orchestrator"},
        )
        if "lifecycle-orchestrator" not in orchestrator_components or "hook-total" not in orchestrator_components:
            fail("orchestrator opt-in engine should emit lifecycle-orchestrator and hook-total timing rows")

        compare_log = temp / ".lazy-harness" / "logs" / "lifecycle-compare-test.jsonl"
        compare_components = run_hook_with_timing(
            {"message_id": "engine-compare", "recent_tool_calls": [{"name": "read", "args_preview": ".lazy-harness/spec/platform/hook-performance-measurement.md"}]},
            "hook-timings-compare.jsonl",
            {"LAZY_RESPONSE_COMPLETED_ENGINE": "compare", "LAZY_RESPONSE_COMPLETED_COMPARE_LOG": str(compare_log)},
        )
        if "lifecycle-orchestrator" not in compare_components:
            fail("compare engine should run sandboxed orchestrator for debug comparison")
        if not compare_log.exists():
            fail("compare engine should write lifecycle comparison log")
        compare_rows = [json.loads(line) for line in compare_log.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not compare_rows or compare_rows[-1].get("event") != "response.completed.compare" or compare_rows[-1].get("orchestratorSandbox") is not True:
            fail("compare engine should log sanitized sandbox comparison rows: " + compare_log.read_text(encoding="utf-8"))
        if "legacyBody" in compare_rows[-1] or "orchestratorBody" in compare_rows[-1]:
            fail("compare log must store hashes/lengths, not raw hook bodies")

        summary_completed = subprocess.run(
            [str(temp / ".lazy-harness" / "bin" / "lazy"), "lifecycle-compare-summary", "--format=json", "--log", str(compare_log)],
            cwd=temp,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            text=True,
            capture_output=True,
            check=False,
        )
        if summary_completed.returncode != 0:
            fail("lazy lifecycle-compare-summary failed:\n" + summary_completed.stdout + summary_completed.stderr)
        compare_summary = json.loads(summary_completed.stdout)
        if compare_summary.get("mode") != "lifecycle-compare-summary" or compare_summary.get("rows", 0) < 1:
            fail("lifecycle compare summary should report compare rows: " + summary_completed.stdout[:500])
        since_completed = subprocess.run(
            [str(temp / ".lazy-harness" / "bin" / "lazy"), "lifecycle-compare-summary", "--format=json", "--log", str(compare_log), "--since", "2999-01-01T00:00:00Z"],
            cwd=temp,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            text=True,
            capture_output=True,
            check=False,
        )
        if since_completed.returncode != 0:
            fail("lazy lifecycle-compare-summary --since failed:\n" + since_completed.stdout + since_completed.stderr)
        since_summary = json.loads(since_completed.stdout)
        if since_summary.get("rows") != 0 or since_summary.get("sourceRows", 0) < 1 or since_summary.get("filteredRows", 0) < 1:
            fail("lifecycle compare --since should filter older rows while reporting source/filtered counts: " + since_completed.stdout[:800])

        def run_compare_payload(payload_obj: dict, log_name: str, extra_env: dict[str, str] | None = None) -> dict:
            log_path = temp / ".lazy-harness" / "logs" / log_name
            env = env_without_lazy_runtime(
                LAZY_HOST_ROOT=str(temp),
                LAZY_HOOK_TIMING_LOG=str(temp / ".lazy-harness" / "logs" / f"{log_name}.timings.jsonl"),
                LAZY_RESPONSE_COMPLETED_ENGINE="compare",
                LAZY_RESPONSE_COMPLETED_COMPARE_LOG=str(log_path),
            )
            if extra_env:
                env.update(extra_env)
            completed = subprocess.run(
                [str(hook)],
                cwd=temp,
                input=json.dumps(payload_obj, ensure_ascii=False),
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            if completed.returncode != 0:
                fail("compare fixture hook failed:\n" + completed.stdout + completed.stderr)
            rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not rows:
                fail("compare fixture should append a compare row")
            return rows[-1]

        newline_row = run_compare_payload({
            "message_id": "compare-newline-normalization",
            "assistant_response": "Analysis plan:\n1. DDD domain finding\n2. SDD contract finding\n3. BDD user flow finding\nBacklog: capture this later.",
            "recent_tool_calls": [{"name": "read", "args_preview": ".lazy-harness/spec/platform/hook-performance-measurement.md"}],
        }, "lifecycle-compare-newline.jsonl")
        if newline_row.get("bodyHashMatch") is not True or newline_row.get("helperMatch") is not True:
            fail("compare log should normalize trailing-newline body differences to legacy semantics: " + json.dumps(newline_row, ensure_ascii=False))
        if newline_row.get("bodyHashNormalization") != "strip-trailing-newlines":
            fail("compare log should record body hash normalization policy: " + json.dumps(newline_row, ensure_ascii=False))

        project_rule_payload = {
            "message_id": "compare-open-gate-suppression",
            "assistant_response": "프로젝트 규칙을 .jcode/harness/20-project-rules.md에 추가하겠습니다.",
            "recent_tool_calls": [{"name": "Write", "args_preview": ".jcode/harness/20-project-rules.md"}],
        }
        first_gate = run_compare_payload(project_rule_payload, "lifecycle-compare-open-gates.jsonl")
        if first_gate.get("bodyHashMatch") is not True or first_gate.get("helperMatch") is not True:
            fail("first project-rule compare row should match before open-gate suppression: " + json.dumps(first_gate, ensure_ascii=False))
        second_gate = run_compare_payload(project_rule_payload, "lifecycle-compare-open-gates.jsonl")
        if second_gate.get("legacyOutputEmitted") is not False or second_gate.get("orchestratorOutputEmitted") is not False or second_gate.get("bodyHashMatch") is not True:
            fail("sandbox should mirror open-gates state so duplicate suppression matches legacy: " + json.dumps(second_gate, ensure_ascii=False))

        subprocess.run(["git", "config", "user.email", "lazy-harness@example.invalid"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        subprocess.run(["git", "config", "user.name", "Lazy Harness Test"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        (temp / "fix-compare-fixture.txt").write_text("fix fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "fix-compare-fixture.txt"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        subprocess.run(["git", "commit", "-q", "-m", "Fix: lifecycle compare sandbox fixture"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        fix_row = run_compare_payload({
            "message_id": "compare-fix-regression-git-context",
            "recent_tool_calls": [{"name": "read", "args_preview": ".lazy-harness/tests/pre-action-search-evidence-guard.md"}],
        }, "lifecycle-compare-fix-regression.jsonl")
        if fix_row.get("bodyHashMatch") is not True or fix_row.get("helperMatch") is not True or not str(fix_row.get("legacyHelper") or "").endswith("check-fix-regression.sh"):
            fail("sandbox should receive read-only git facts so fix-regression compare matches legacy: " + json.dumps(fix_row, ensure_ascii=False))

        mirror_runtime = temp / ".lazy-harness" / "original-runtime-for-sandbox"
        for name in ("open-gates.json", "surfaced-rule-digests.jsonl", "search-read-debt.jsonl"):
            target = mirror_runtime / "state" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"fixture": name}, ensure_ascii=False) + "\n", encoding="utf-8")
        tool_events = temp / ".jcode" / "hooks" / "tool-events.jsonl"
        tool_events.parent.mkdir(parents=True, exist_ok=True)
        tool_events.write_text('1700000000 {"event":"tool.execute.after","message_id":"sandbox-state-mirror","session_id":"sandbox-session","tool":{"name":"read","args":{"file_path":"README.md"}}}\n', encoding="utf-8")
        sandbox_check = subprocess.run(
            [str(temp / ".lazy-harness" / "bin" / "lazy"), "lifecycle-check", "--sandbox", "--format=json"],
            cwd=temp,
            input=json.dumps({"message_id": "sandbox-state-mirror", "session_id": "sandbox-session", "recent_tool_calls": []}, ensure_ascii=False),
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp), LAZY_RUNTIME_ROOT=str(mirror_runtime)),
            text=True,
            capture_output=True,
            check=False,
        )
        if sandbox_check.returncode != 0:
            fail("lifecycle-check sandbox state mirror fixture failed:\n" + sandbox_check.stdout + sandbox_check.stderr)
        sandbox_json = json.loads(sandbox_check.stdout)
        mirrored = ((sandbox_json.get("sandboxContext") or {}).get("mirroredState") or {})
        for name in ("open-gates.json", "surfaced-rule-digests.jsonl", "search-read-debt.jsonl", ".jcode/hooks/tool-events.jsonl"):
            if not (mirrored.get(name) or {}).get("copied"):
                fail("lifecycle-check sandbox should mirror bounded state/journal fixture for " + name + ": " + json.dumps(mirrored, ensure_ascii=False))

        correction_payload = {
            "message_id": "correction-capture-missing",
            "last_user_message": "너가 기록하는거 아닌거 알지? 하네스를 수정하는거야. 자꾸 실수하는건 기능으로 넣어야겠다.",
            "assistant_response": "맞습니다. 제가 또 방향을 잘못 잡았습니다. 죄송합니다.",
            "recent_tool_calls": [],
        }
        correction_completed = subprocess.run(
            [str(hook)],
            cwd=temp,
            input=json.dumps(correction_payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp), LAZY_HOOK_TIMING_LOG=str(temp / ".lazy-harness" / "logs" / "hook-timings-correction.jsonl")),
        )
        if correction_completed.returncode != 0:
            fail("user correction capture fixture hook failed:\n" + correction_completed.stdout + correction_completed.stderr)
        if "User correction capture gate" not in correction_completed.stdout:
            fail("user correction acknowledgement without durable capture must STOP:\n" + correction_completed.stdout + correction_completed.stderr)

        correction_captured_payload = {
            **correction_payload,
            "message_id": "correction-capture-recorded",
            "recent_tool_calls": [{
                "name": "write",
                "args_preview": ".lazy-harness/planning/current-framework-roadmap-snapshot.md Correction capture primary record",
            }],
        }
        captured_completed = subprocess.run(
            [str(hook)],
            cwd=temp,
            input=json.dumps(correction_captured_payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp), LAZY_HOOK_TIMING_LOG=str(temp / ".lazy-harness" / "logs" / "hook-timings-correction-captured.jsonl")),
        )
        if captured_completed.returncode != 0:
            fail("captured user correction fixture hook failed:\n" + captured_completed.stdout + captured_completed.stderr)
        if "User correction capture gate" in captured_completed.stdout:
            fail("user correction with durable capture should not trigger correction gate:\n" + captured_completed.stdout + captured_completed.stderr)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ response.completed no auto route telemetry ok")


def check_removed_query_helper_artifacts_absent() -> None:
    """Deleted query-helper artifacts and commands must stay removed."""
    deleted_paths = [
        LAZY / "scripts" / ("context" + "-delivery.ts"),
        LAZY / "scripts" / ("relevant" + "-record-query.ts"),
        LAZY / "scripts" / ("context" + "-broker-dogfood.ts"),
        LAZY / "schemas" / ("context" + "-delivery-packet.schema.json"),
        LAZY / "schemas" / ("relevant" + "-record-index.schema.json"),
        LAZY / "spec" / "platform" / ("context" + "-delivery-contract.md"),
        LAZY / "spec" / "platform" / ("relevant" + "-record-query.md"),
        LAZY / "spec" / "platform" / ("context" + "-broker-dogfood.md"),
        LAZY / "tests" / ("relevant" + "-record-query-cli-equals-flags.md"),
        LAZY / "tests" / ("context" + "-broker-dogfood.md"),
    ]
    present = [str(path.relative_to(ROOT)) for path in deleted_paths if path.exists()]
    if present:
        fail("deleted query-helper artifacts are present: " + json.dumps(present, ensure_ascii=False))

    help_text = subprocess.check_output([str(LAZY / "bin" / "lazy"), "help"], cwd=ROOT, text=True)
    forbidden_commands = ["context --message", "context-delivery", "context-dogfood"]
    leaked = [cmd for cmd in forbidden_commands if cmd in help_text]
    if leaked:
        fail("lazy help still advertises deleted query-helper commands: " + json.dumps(leaked, ensure_ascii=False))

    hook_text = (LAZY / "hooks" / "lifecycle" / "on-message-received.sh").read_text(encoding="utf-8")
    helper_text = (LAZY / "hooks" / "lifecycle" / "helpers" / "check-read-debt-permit.py").read_text(encoding="utf-8")
    literal_offenders = ["relevant" + "-record-query.ts", "context" + "-delivery.ts", "context" + "-broker-dogfood.ts"]
    leaked_literals = [token for token in literal_offenders if token in hook_text or token in helper_text]
    if leaked_literals:
        fail("lifecycle path still references deleted query-helper scripts: " + json.dumps(leaked_literals, ensure_ascii=False))
    print("✓ removed query-helper artifacts absent")


def check_standalone_source_detection_uses_markers() -> None:
    """Standalone source repo detection must not depend on synced-from-commit absence."""
    doctor_source = (LAZY / "scripts" / "doctor.py").read_text(encoding="utf-8")
    required = [
        '"framework" / "framework-contract.md"',
        '"planning" / "phase-5-plan.xml"',
        "Do not use state/synced-from-commit absence",
    ]
    missing = [phrase for phrase in required if phrase not in doctor_source]
    if missing:
        fail("doctor standalone source detection must use framework markers: " + json.dumps(missing, ensure_ascii=False))

    lazy_init_source = (LAZY / "scripts" / "lazy-init.ts").read_text(encoding="utf-8")
    required = [
        "self-target source repo",
        "resolve(sourceRoot) === resolve(targetRoot)",
        "Host institutional memory",
    ]
    missing = [phrase for phrase in required if phrase not in lazy_init_source]
    if missing:
        fail("lazy-init must skip version marker for self-target source repo: " + json.dumps(missing, ensure_ascii=False))
    print("✓ standalone source marker detection ok")


def check_lazy_host_root_resolution() -> None:
    """lazy CLI and Python validators must use the caller worktree as host root."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy_host_root_"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        (temp / ".lazy-harness").symlink_to(LAZY, target_is_directory=True)

        poisoned_git_env = {
            **os.environ,
            "LAZY_HOST_ROOT": str(temp.resolve()),
            "GIT_DIR": str((ROOT / ".git").resolve()),
            "GIT_WORK_TREE": str(ROOT),
        }
        completed = subprocess.run(
            [str(temp / ".lazy-harness" / "bin" / "lazy"), "version"],
            cwd=temp,
            env=poisoned_git_env,
            text=True,
            capture_output=True,
            check=True,
        )
        expected = f"host_root:  {temp.resolve()}"
        if expected not in completed.stdout:
            fail("lazy version should prefer LAZY_HOST_ROOT even when GIT_DIR/GIT_WORK_TREE are inherited:\n" + completed.stdout)

        snippet = f"import runpy; print(runpy.run_path({json.dumps(str(LAZY / 'scripts' / 'doctor.py'))})['ROOT'])"
        env = poisoned_git_env
        root_out = subprocess.run(
            ["python3", "-c", snippet],
            cwd=temp,
            env=env,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        if root_out != str(temp.resolve()):
            fail(f"doctor.py should prefer LAZY_HOST_ROOT; got {root_out}, expected {temp.resolve()}")

        snippet = f"import runpy; print(runpy.run_path({json.dumps(str(LAZY / 'scripts' / 'self-test.py'))})['ROOT'])"
        root_out = subprocess.run(
            ["python3", "-c", snippet],
            cwd=temp,
            env=env,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        if root_out != str(temp.resolve()):
            fail(f"self-test.py should prefer LAZY_HOST_ROOT; got {root_out}, expected {temp.resolve()}")

        snippet = (
            "import json, os, runpy; "
            f"ns=runpy.run_path({json.dumps(str(LAZY / 'scripts' / 'self-test.py'))}); "
            "clean=ns['env_without_lazy_runtime'](LAZY_RUNTIME_ROOT='explicit-runtime'); "
            "print(json.dumps({"
            "'processGitDir': os.environ.get('GIT_DIR'), "
            "'processGitWorkTree': os.environ.get('GIT_WORK_TREE'), "
            "'cleanGitDir': clean.get('GIT_DIR'), "
            "'cleanGitWorkTree': clean.get('GIT_WORK_TREE'), "
            "'explicitRuntime': clean.get('LAZY_RUNTIME_ROOT')"
            "}))"
        )
        env_report = subprocess.run(
            ["python3", "-c", snippet],
            cwd=temp,
            env=poisoned_git_env,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        env_json = json.loads(env_report)
        if env_json != {
            "processGitDir": None,
            "processGitWorkTree": None,
            "cleanGitDir": None,
            "cleanGitWorkTree": None,
            "explicitRuntime": "explicit-runtime",
        }:
            fail("self-test env helper should clear inherited git hook env and preserve explicit overrides: " + env_report)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ LAZY_HOST_ROOT worktree root resolution ok")


def check_parallel_runtime_state_isolation() -> None:
    """Symlinked worktrees must isolate runtime journals by caller worktree/session."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy_parallel_runtime_"))
    try:
        primary = temp / "primary"
        secondary = temp / "secondary"
        primary.mkdir()
        secondary.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=primary, env=env_without_lazy_runtime(), check=True)
        subprocess.run(["git", "init", "-q"], cwd=secondary, env=env_without_lazy_runtime(), check=True)
        (primary / ".lazy-harness").symlink_to(LAZY, target_is_directory=True)
        (secondary / ".lazy-harness").symlink_to(LAZY, target_is_directory=True)

        payload_a = json.dumps({"event": "message.received", "session_id": "session-a", "message_id": "m-a", "last_user_message": "A 작업", "working_dir": str(secondary)})
        payload_b = json.dumps({"event": "message.received", "session_id": "session-b", "message_id": "m-b", "last_user_message": "B 작업", "working_dir": str(secondary)})
        for payload in [payload_a, payload_b]:
            completed = subprocess.run(
                [str(secondary / ".lazy-harness" / "hooks" / "lifecycle" / "on-message-received.sh")],
                cwd=secondary,
                input=payload,
                text=True,
                capture_output=True,
                env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(secondary)),
                check=False,
            )
            if completed.returncode != 0:
                fail("message.received runtime isolation fixture failed:\n" + completed.stdout + completed.stderr)

        runtime_a = subprocess.check_output(
            ["python3", str(LAZY / "hooks" / "lifecycle" / "helpers" / "runtime_paths.py"), "runtime-root", payload_a],
            cwd=secondary,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(secondary)),
            text=True,
        ).strip()
        runtime_b = subprocess.check_output(
            ["python3", str(LAZY / "hooks" / "lifecycle" / "helpers" / "runtime_paths.py"), "runtime-root", payload_b],
            cwd=secondary,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(secondary)),
            text=True,
        ).strip()
        if runtime_a == runtime_b:
            fail("different session ids should map to different runtime roots")
        if not runtime_a.startswith(str((secondary / ".git" / "lazy-harness" / "runtime").resolve())):
            fail(f"runtime root should live under caller worktree git-dir, got {runtime_a}")
        for runtime in [pathlib.Path(runtime_a), pathlib.Path(runtime_b)]:
            journal = runtime / "state" / "search-read-debt.jsonl"
            if not journal.exists():
                fail(f"runtime journal missing: {journal}")
        symlink_target_journal = primary / ".lazy-harness" / "state" / "search-read-debt.jsonl"
        if symlink_target_journal.exists() and str(symlink_target_journal.resolve()).startswith(str(LAZY.resolve())):
            # The source repo may have historical rows, but this fixture must not create
            # a fresh primary/symlink-target journal in the temp worktrees.
            pass

        payload_tool_a = json.dumps({"event": "tool.execute.before", "session_id": "session-a", "tool": {"name": "bash", "args": {"command": "echo mutate"}}})
        denied = subprocess.run(
            [str(secondary / ".lazy-harness" / "hooks" / "lifecycle" / "on-tool-execute-before.sh")],
            cwd=secondary,
            input=payload_tool_a,
            text=True,
            capture_output=True,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(secondary)),
            check=False,
        )
        if denied.returncode == 0 or "search-debt" not in denied.stdout:
            fail("tool.execute.before should read the matching runtime debt journal and deny action:\n" + denied.stdout + denied.stderr)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ parallel runtime state isolation ok")


def check_shared_jsonl_conflict_visible() -> None:
    """Stable JSONL helper must dedupe identical rows and record conflicts."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy_jsonl_conflict_"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        (temp / ".lazy-harness" / "knowledge").mkdir(parents=True, exist_ok=True)
        runtime_paths = str((LAZY / "scripts" / "runtime-paths.ts").resolve())
        script = f"""
import {{ appendJsonlStable }} from {json.dumps(runtime_paths)}
	const path = './.lazy-harness/knowledge/test-conflict.jsonl'
	console.log(appendJsonlStable(path, {{ id: 'row-1', value: 1 }}, 'id', process.cwd()))
	console.log(appendJsonlStable(path, {{ id: 'row-1', value: 1 }}, 'id', process.cwd()))
	console.log(appendJsonlStable(path, {{ id: 'row-1', value: 2 }}, 'id', process.cwd()))
	console.log(appendJsonlStable(path, {{ topic: 'idless', nested: {{ b: 2, a: 1 }} }}, 'id', process.cwd()))
	console.log(appendJsonlStable(path, {{ nested: {{ a: 1, b: 2 }}, topic: 'idless' }}, 'id', process.cwd()))
	"""
        completed = subprocess.run(["bun", "-e", script], cwd=temp, env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)), text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            fail("appendJsonlStable fixture failed:\n" + completed.stdout + completed.stderr)
        statuses = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        if statuses != ["appended", "deduped-identical", "conflict-recorded", "appended", "deduped-identical"]:
            fail("appendJsonlStable statuses changed: " + json.dumps(statuses, ensure_ascii=False))
        target = temp / ".lazy-harness" / "knowledge" / "test-conflict.jsonl"
        conflicts = pathlib.Path(str(target) + ".conflicts.jsonl")
        if not target.exists() or not conflicts.exists():
            fail("appendJsonlStable should create target and conflict journals")
        rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
        conflict_rows = [json.loads(line) for line in conflicts.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) != 2 or rows[0].get("value") != 1 or rows[1].get("topic") != "idless":
            fail("appendJsonlStable should not overwrite existing row: " + json.dumps(rows, ensure_ascii=False))
        if len(conflict_rows) != 1 or conflict_rows[0].get("status") != "conflict-recorded":
            fail("appendJsonlStable conflict row missing: " + json.dumps(conflict_rows, ensure_ascii=False))
        py_helper = str((LAZY / "hooks" / "lifecycle" / "helpers" / "runtime_paths.py").resolve())
        py_script = f"""
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('runtime_paths', {json.dumps(py_helper)})
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
path = Path('./.lazy-harness/knowledge/test-python-idless.jsonl')
print(mod.append_jsonl_stable(Path.cwd(), path, {{'topic':'idless-python','nested':{{'b':2,'a':1}}}}))
print(mod.append_jsonl_stable(Path.cwd(), path, {{'nested':{{'a':1,'b':2}},'topic':'idless-python'}}))
"""
        py_completed = subprocess.run([sys.executable, "-c", py_script], cwd=temp, env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)), text=True, capture_output=True, check=False)
        if py_completed.returncode != 0:
            fail("python append_jsonl_stable idless fixture failed:\n" + py_completed.stdout + py_completed.stderr)
        py_statuses = [line.strip() for line in py_completed.stdout.splitlines() if line.strip()]
        if py_statuses != ["appended", "deduped-identical"]:
            fail("python append_jsonl_stable idless statuses changed: " + json.dumps(py_statuses, ensure_ascii=False))
        py_target = temp / ".lazy-harness" / "knowledge" / "test-python-idless.jsonl"
        py_rows = [json.loads(line) for line in py_target.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(py_rows) != 1 or py_rows[0].get("topic") != "idless-python":
            fail("python append_jsonl_stable should dedupe idless stable JSON rows: " + json.dumps(py_rows, ensure_ascii=False))
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ shared JSONL conflict visibility ok")


def check_affected_test_runner() -> None:
    queue = LAZY / "questions" / f"__tmp_affected_tests_{os.getpid()}.xml"
    queue.unlink(missing_ok=True)
    try:
        covered = run_affected_tests(["tests/lazy-harness/affected/covered.ts"], queue=queue)
        if covered.get("ok") is not True or covered.get("forceGate") is not False:
            fail("affected-test-runner covered fixture changed: " + json.dumps(covered, ensure_ascii=False))
        if covered.get("runnableTests") != ["tests/lazy-harness/affected/covered.test.ts"]:
            fail("affected-test-runner runnable tests changed: " + json.dumps(covered.get("runnableTests"), ensure_ascii=False))
        run = covered.get("run") or {}
        if run.get("exitCode") != 0 or "1 passed" not in (run.get("stdout") or ""):
            fail("affected-test-runner did not execute configured tests successfully: " + json.dumps(run, ensure_ascii=False))
        if run.get("command") != ["bun", "run", "test:run", "tests/lazy-harness/affected/covered.test.ts"]:
            fail("affected-test-runner should use repo-native test script, not hardcoded vitest: " + json.dumps(run, ensure_ascii=False))

        missing = run_affected_tests(["tests/lazy-harness/affected/missing.ts"], queue=queue, expect_code=2)
        if missing.get("ok") is not False or missing.get("forceGate") is not True or missing.get("questions") == []:
            fail("affected-test-runner missing fixture changed: " + json.dumps(missing, ensure_ascii=False))
        question = missing["questions"][0]
        if question.get("id") != "Q-8e866d44709ff49c" or question.get("source") != "affected-test-runner":
            fail("affected-test-runner question identity changed: " + json.dumps(question, ensure_ascii=False))
        labels = [option.get("label", "") for option in question.get("options", [])]
        if not any("프로젝트 테스트 전략" in label for label in labels) or not any("skip/defer" in label for label in labels):
            fail("affected-test-runner interview options changed: " + json.dumps(labels, ensure_ascii=False))

        pass_payload = {"recent_tool_calls": [{"name": "Edit", "args_preview": "tests/lazy-harness/affected/covered.ts"}]}
        pass_out = run_response_completed_hook(pass_payload, queue)
        if pass_out.strip():
            fail("affected test hook should stay silent when vitest passes:\n" + pass_out)

        fail_payload = {"recent_tool_calls": [{"name": "Edit", "args_preview": "tests/lazy-harness/affected/missing.ts"}]}
        fail_out = run_response_completed_hook(fail_payload, queue)
        # Ask-once policy: the missing-test question was already persisted by the
        # first run_affected_tests call above. The hook must NOT re-surface it on
        # subsequent response.completed events, otherwise the same question
        # ask-loops until `recent_tool_calls` drops the path. See
        # .lazy-harness/tests/tdd-cross-verify-forcegate-loop.md.
        if fail_out.strip():
            fail("affected test hook must stay silent when question fingerprint already queued:\n" + fail_out)

        # Sanity: a brand-new missing source path must still trigger the gate exactly once.
        fresh_payload = {"recent_tool_calls": [{"name": "Edit", "args_preview": "tests/lazy-harness/affected/missing-fresh.ts"}]}
        try:
            (ROOT / "tests/lazy-harness/affected").mkdir(parents=True, exist_ok=True)
            fresh_source = ROOT / "tests/lazy-harness/affected/missing-fresh.ts"
            fresh_source.write_text("export const sentinel = 1\n", encoding="utf-8")
            fresh_out = run_response_completed_hook(fresh_payload, queue)
            if "5d-3 Affected Test Gate" not in fresh_out:
                fail("affected test hook did not surface gate for a fresh missing-test fingerprint:\n" + fresh_out)
            fresh_again = run_response_completed_hook(fresh_payload, queue)
            if fresh_again.strip():
                fail("affected test hook re-surfaced gate for already-queued fresh fingerprint:\n" + fresh_again)
        finally:
            fresh_source.unlink(missing_ok=True)
    finally:
        queue.unlink(missing_ok=True)
    print("✓ 5d-3 affected test runner ok")

def check_aftershock_reanalysis() -> None:
    queue = LAZY / "questions" / f"__tmp_aftershock_{os.getpid()}.xml"
    queue.unlink(missing_ok=True)
    try:
        first = run_aftershock_reanalysis(queue)
        if first.get("created") != 1 or first.get("existing") != 0 or first.get("scannedDecisions") != 1:
            fail("aftershock first analysis changed: " + json.dumps(first, ensure_ascii=False))
        question = (first.get("questions") or [{}])[0]
        if question.get("id") != "Q-e69259ad4ca94b24" or question.get("criterionId") != "5d-4" or question.get("source") != "aftershock" or question.get("layer") != "sdd":
            fail("aftershock question identity changed: " + json.dumps(question, ensure_ascii=False))
        root = ET.parse(queue).getroot()
        persisted = [entry for entry in root.findall("question") if entry.attrib.get("id") == "Q-e69259ad4ca94b24"]
        if not persisted or persisted[0].attrib.get("criterionId") != "5d-4" or persisted[0].attrib.get("source") != "aftershock":
            fail("aftershock question was not persisted to queue")
        second = run_aftershock_reanalysis(queue)
        if second.get("created") != 0 or second.get("existing") != 1 or second.get("questions") != []:
            fail("aftershock dedupe changed: " + json.dumps(second, ensure_ascii=False))
    finally:
        queue.unlink(missing_ok=True)
    print("✓ 5d-4 aftershock re-analysis ok")


def check_lifecycle_hook_integration() -> None:
    tdd_queue = LAZY / "questions" / f"__tmp_hook_tdd_{os.getpid()}.xml"
    tdd_shadow_queue = LAZY / "questions" / f"__tmp_shadow_tdd_{os.getpid()}.xml"
    aftershock_queue = LAZY / "questions" / f"__tmp_hook_aftershock_{os.getpid()}.xml"
    aftershock_shadow_queue = LAZY / "questions" / f"__tmp_shadow_aftershock_{os.getpid()}.xml"
    bdd_queue = LAZY / "questions" / f"__tmp_hook_bdd_{os.getpid()}.xml"
    bdd_shadow_queue = LAZY / "questions" / f"__tmp_shadow_bdd_{os.getpid()}.xml"
    generic_queue = LAZY / "questions" / f"__tmp_hook_generic_{os.getpid()}.xml"
    decisions = LAZY / "logs" / f"__tmp_hook_decisions_{os.getpid()}.jsonl"
    shadow_decisions = LAZY / "logs" / f"__tmp_shadow_decisions_{os.getpid()}.jsonl"
    bdd_state = runtime_open_gates_file(ROOT)
    bdd_state_backup = bdd_state.read_text(encoding="utf-8") if bdd_state.exists() else None
    for path in [tdd_queue, tdd_shadow_queue, aftershock_queue, aftershock_shadow_queue, bdd_queue, bdd_shadow_queue, generic_queue, decisions, shadow_decisions]:
        path.unlink(missing_ok=True)
    bdd_state.unlink(missing_ok=True)
    try:
        tdd_payload = {
            "recent_tool_calls": [
                {"name": "Edit", "args_preview": ".lazy-harness/triggers/fixtures/tdd-cross-verify/missing-test.ts"},
            ],
        }
        tdd_out = run_response_completed_hook(tdd_payload, tdd_queue)
        if "5d-3 TDD Cross-Verify Gate" not in tdd_out or "Q-22c6c7cf5a7620f1" not in tdd_out:
            fail("response.completed did not surface TDD cross-verify gate:\n" + tdd_out)
        tdd_root = ET.parse(tdd_queue).getroot()
        if not any(question.attrib.get("criterionId") == "5d-3" for question in tdd_root.findall("question")):
            fail("response.completed TDD helper did not persist question")

        tdd_shadow = run_lifecycle_check_shadow(tdd_payload, tdd_shadow_queue)
        if tdd_shadow.get("firstOutputHelper") != ".lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh":
            fail("lifecycle-check shadow should match TDD first output helper: " + json.dumps(tdd_shadow, ensure_ascii=False)[:800])
        if "5d-3 TDD Cross-Verify Gate" not in tdd_shadow.get("firstOutput", "") or "Q-22c6c7cf5a7620f1" not in tdd_shadow.get("firstOutput", ""):
            fail("lifecycle-check shadow did not surface TDD gate output")
        if json.loads(tdd_shadow.get("injectJson") or "{}").get("inject", {}).get("body") != tdd_shadow.get("firstOutput"):
            fail("lifecycle-check shadow injectJson should match firstOutput body")

        decisions.write_text((LAZY / "triggers" / "fixtures" / "aftershock" / "decisions.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
        shadow_decisions.write_text((LAZY / "triggers" / "fixtures" / "aftershock" / "decisions.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
        aftershock_payload = {
            "recent_tool_calls": [
                {"name": "Edit", "args_preview": ".lazy-harness/logs/decisions.jsonl"},
            ],
        }
        aftershock_out = run_response_completed_hook(aftershock_payload, aftershock_queue, decisions=decisions)
        if "5d-4 Aftershock Re-analysis" not in aftershock_out or "Q-e69259ad4ca94b24" not in aftershock_out:
            fail("response.completed did not surface aftershock gate:\n" + aftershock_out)
        aftershock_root = ET.parse(aftershock_queue).getroot()
        if not any(question.attrib.get("criterionId") == "5d-4" for question in aftershock_root.findall("question")):
            fail("response.completed aftershock helper did not persist question")

        aftershock_shadow = run_lifecycle_check_shadow(aftershock_payload, aftershock_shadow_queue, decisions=shadow_decisions)
        if aftershock_shadow.get("firstOutputHelper") != ".lazy-harness/hooks/lifecycle/helpers/check-aftershock-reanalysis.sh":
            fail("lifecycle-check shadow should match aftershock first output helper: " + json.dumps(aftershock_shadow, ensure_ascii=False)[:800])
        if "5d-4 Aftershock Re-analysis" not in aftershock_shadow.get("firstOutput", "") or "Q-e69259ad4ca94b24" not in aftershock_shadow.get("firstOutput", ""):
            fail("lifecycle-check shadow did not surface aftershock gate output")

        bdd_payload = {
            "last_user_message": "사용자가 환자 목록 버튼을 클릭하면 환자 목록 화면으로 이동해야 합니다.",
            "message_id": "shadow-bdd-parity",
            "recent_tool_calls": [],
        }
        bdd_candidates = ROOT / ".lazy-harness" / "knowledge" / "candidates.jsonl"
        bdd_candidates_backup = bdd_candidates.read_text(encoding="utf-8") if bdd_candidates.exists() else None
        bdd_candidates.unlink(missing_ok=True)
        bdd_hook_body = hook_inject_body(run_response_completed_hook(bdd_payload, bdd_queue))
        if bdd_hook_body.strip():
            fail("response.completed should silently capture BDD candidate, not surface gate:\n" + bdd_hook_body)
        if not bdd_candidates.exists() or "lifecycle-bdd-trigger" not in bdd_candidates.read_text(encoding="utf-8"):
            fail("response.completed BDD helper should append candidate row")
        bdd_candidates.unlink(missing_ok=True)
        bdd_shadow = run_lifecycle_check_shadow(bdd_payload, bdd_shadow_queue)
        if bdd_shadow.get("outputEmitted") is not False or bdd_shadow.get("firstOutput"):
            fail("lifecycle-check shadow should silently capture BDD candidate: " + json.dumps(bdd_shadow, ensure_ascii=False)[:800])
        if not bdd_candidates.exists() or "lifecycle-bdd-trigger" not in bdd_candidates.read_text(encoding="utf-8"):
            fail("lifecycle-check shadow BDD helper should append candidate row")
        if bdd_candidates_backup is not None:
            bdd_candidates.write_text(bdd_candidates_backup, encoding="utf-8")
        else:
            bdd_candidates.unlink(missing_ok=True)

        option_payload = {
            "assistant_response": (
                "## Rule placement\n"
                "- Rule: release execution policy.\n"
                "- Scope: ambiguous\n"
                "- Confirmation: needs-option-gate\n\n"
                "선택해주세요:\n"
                "A. SSOT 기록 후 test release dispatch (Recommended)\n"
            ),
            "recent_tool_calls": [{"name": "Write", "args_preview": ".lazy-harness/ssot/release-sources.md"}],
        }
        option_hook_body = hook_inject_body(run_response_completed_hook(option_payload, generic_queue))
        option_shadow = run_lifecycle_check_shadow(option_payload, generic_queue)
        if "Option gate discipline" not in option_hook_body or "Option gate discipline" not in option_shadow.get("firstOutput", ""):
            fail("option-gate parity fixture did not surface expected STOP")
        if option_shadow.get("firstOutputHelper") != ".lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh":
            fail("lifecycle-check shadow should match option-gate first output helper")

        record_before_payload = {
            "assistant_response": "기록된 계획을 찾아보겠습니다.",
            "recent_tool_calls": [{"name": "session_search", "args_preview": "계획"}],
        }
        record_hook_body = hook_inject_body(run_response_completed_hook(record_before_payload, generic_queue))
        record_shadow = run_lifecycle_check_shadow(record_before_payload, generic_queue)
        if "Record-before-session-history" not in record_hook_body or "Record-before-session-history" not in record_shadow.get("firstOutput", ""):
            fail("record-before parity fixture did not surface expected STOP")
        if record_shadow.get("firstOutputHelper") != ".lazy-harness/hooks/lifecycle/helpers/check-record-before-session-history.sh":
            fail("lifecycle-check shadow should match record-before first output helper")

        read_only_payload = {
            "message_id": "shadow-no-output-read-only",
            "recent_tool_calls": [{"name": "read", "args_preview": ".lazy-harness/spec/platform/hook-performance-measurement.md"}],
        }
        read_only_hook_out = run_response_completed_hook(read_only_payload, generic_queue)
        read_only_shadow = run_lifecycle_check_shadow(read_only_payload, generic_queue)
        if read_only_hook_out.strip() or read_only_shadow.get("outputEmitted") is not False or read_only_shadow.get("firstOutput"):
            fail("read-only no-output parity fixture should stay silent")

        block_dry_payload = {
            "message_id": "shadow-policy-block-dry-run",
            "recent_tool_calls": [{"name": "read", "args_preview": ".lazy-harness/tests/policy-block-validation-evidence.md"}],
            "policy_context": {
                "blockRuntimeDryRun": True,
                "stage": "turn",
                "appliesTo": ["claiming_validation_complete_without_evidence"],
            },
        }
        block_hook_body = hook_inject_body(run_response_completed_hook(block_dry_payload, generic_queue))
        block_shadow = run_lifecycle_check_shadow(block_dry_payload, generic_queue)
        if "DRY-RUN STOP. Policy Machinery block runtime" not in block_hook_body or "validation-evidence-block" not in block_hook_body:
            fail("response.completed should surface dry-run block helper output for explicit structured dry-run context:\n" + block_hook_body)
        if "No lifecycle hard-stop is installed" not in block_hook_body:
            fail("response.completed dry-run block output must state no lifecycle hard-stop is installed")
        if block_shadow.get("firstOutputHelper") != ".lazy-harness/hooks/lifecycle/helpers/check-policy-block-runtime.py":
            fail("lifecycle-check shadow should match block dry-run first output helper: " + json.dumps(block_shadow, ensure_ascii=False)[:800])
        if "DRY-RUN STOP. Policy Machinery block runtime" not in block_shadow.get("firstOutput", ""):
            fail("lifecycle-check shadow should surface dry-run block helper output")

        block_raw_payload = {
            "message_id": "shadow-policy-block-raw-text",
            "recent_tool_calls": [{"name": "read", "args_preview": ".lazy-harness/tests/policy-block-validation-evidence.md"}],
            "last_user_message": "검증 완료",
            "assistant_response": "검증 완료",
        }
        block_raw_hook_out = run_response_completed_hook(block_raw_payload, generic_queue)
        block_raw_shadow = run_lifecycle_check_shadow(block_raw_payload, generic_queue)
        if block_raw_hook_out.strip() or "DRY-RUN STOP" in block_raw_shadow.get("firstOutput", ""):
            fail("dry-run block lifecycle integration must stay silent for raw text payloads")
    finally:
        for path in [tdd_queue, tdd_shadow_queue, aftershock_queue, aftershock_shadow_queue, bdd_queue, bdd_shadow_queue, generic_queue, decisions, shadow_decisions]:
            path.unlink(missing_ok=True)
        if bdd_state_backup is not None:
            bdd_state.write_text(bdd_state_backup, encoding="utf-8")
        else:
            bdd_state.unlink(missing_ok=True)
    print("✓ 5d-5 lifecycle hook integration ok")


def check_lifecycle_parity_runner() -> None:
    completed = subprocess.run(
        [".lazy-harness/bin/lazy", "lifecycle-parity", "--format=json", "--fail-on-mismatch"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail("lifecycle parity runner failed")
    result = json.loads(completed.stdout)
    if result.get("mode") != "lifecycle-parity-runner" or result.get("fixtures") != 12 or result.get("failed") != 0:
        fail("lifecycle parity runner summary changed: " + completed.stdout[:800])
    print("✓ lifecycle parity runner ok")


def check_knowledge_intake() -> None:
    before_status = subprocess.run(
        ["git", "status", "--short", ".lazy-harness"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    result = run_knowledge_intake_fixture()
    after_status = subprocess.run(
        ["git", "status", "--short", ".lazy-harness"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout

    if before_status != after_status:
        fail("knowledge-intake Stage 1 must not write files")
    if result.get("ok") is not True or result.get("mode") != "plan" or result.get("checkedTexts") != 7:
        fail("knowledge-intake fixture result changed: " + json.dumps(result, ensure_ascii=False))

    candidates = result.get("candidates", [])
    layers = {candidate.get("recommendedLayer") for candidate in candidates}
    required_layers = {"ddd", "sdd", "bdd", "tdd", "adr", "ssot"}
    missing_layers = sorted(required_layers - layers)
    if missing_layers:
        fail(f"knowledge-intake missing layers: {missing_layers}")

    candidate_types = {candidate.get("candidateType") for candidate in candidates}
    required_types = {
        "domain-term",
        "business-invariant",
        "contract-source",
        "user-behavior",
        "regression-fact",
        "decision-tradeoff",
        "source-of-truth",
    }
    missing_types = sorted(required_types - candidate_types)
    if missing_types:
        fail(f"knowledge-intake missing candidate types: {missing_types}")

    if not any(candidate.get("confidence") == "ambiguous" for candidate in candidates):
        fail("knowledge-intake should surface at least one ambiguous candidate")
    if not all(candidate.get("action") in {"ask", "record-candidate", "ignore"} for candidate in candidates):
        fail("knowledge-intake emitted invalid action")

    ask = subprocess.run(
        ["bun", ".lazy-harness/scripts/knowledge-intake.ts", "--fixture", "bdd-behavior", "--plan", "--format", "ask"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    if "[lazy-harness intake]" not in ask or "Recommended" not in ask:
        fail("knowledge-intake ask format changed:\n" + ask)

    print(f"✓ knowledge-intake detector ok ({len(candidates)} candidates)")


def check_document_resource_ingestion_inspect() -> None:
    """Document Resource Ingestion inspect mode must classify docs without writing records."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / "src").mkdir()
        (root / "src" / "current.ts").write_text("export const current = true\n", encoding="utf-8")
        (root / ".lazy-harness").mkdir()
        (root / ".lazy-harness" / "ignored.md").write_text("# Should not scan\n", encoding="utf-8")
        (root / "docs").mkdir()
        (root / "README.md").write_text("# Active Project\n\nArchitecture uses src/current.ts and tests/unit/app.test.ts.\n", encoding="utf-8")
        duplicate = "# Shared Architecture\n\nSystem design uses src/current.ts and backend API contracts.\n"
        (root / "docs" / "architecture-a.md").write_text(duplicate, encoding="utf-8")
        (root / "docs" / "architecture-b.md").write_text(duplicate, encoding="utf-8")
        (root / "docs" / "legacy-plan.md").write_text("# Legacy Plan\n\nDeprecated and outdated. See src/missing-one.ts.\n", encoding="utf-8")
        (root / "docs" / "polluted.md").write_text("# Polluted\n\nDo not use. Broken � text. See src/missing-a.ts src/missing-b.ts src/missing-c.ts.\n", encoding="utf-8")
        completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "document-resource-ingestion.ts"),
                "--mode",
                "inspect",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            fail("document-resource-ingestion inspect failed:\n" + completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        docs = {doc["path"]: doc for doc in result.get("documents", [])}
        if ".lazy-harness/ignored.md" in docs:
            fail("document-resource-ingestion must exclude .lazy-harness docs")
        expected = {"README.md", "docs/architecture-a.md", "docs/architecture-b.md", "docs/legacy-plan.md", "docs/polluted.md"}
        if set(docs) != expected:
            fail(f"document-resource-ingestion scanned unexpected docs: expected {sorted(expected)}, got {sorted(docs)}")
        if docs["README.md"].get("status") != "authoritative":
            fail("README.md should be suggested as authoritative in fixture: " + json.dumps(docs["README.md"], ensure_ascii=False))
        if docs["docs/architecture-a.md"].get("status") != "duplicate" or docs["docs/architecture-b.md"].get("status") != "duplicate":
            fail("duplicate architecture docs should be clustered as duplicate")
        if not result.get("duplicateGroups"):
            fail("document-resource-ingestion should report duplicateGroups")
        if docs["docs/legacy-plan.md"].get("status") != "historical":
            fail("legacy-plan should be classified as historical")
        if docs["docs/polluted.md"].get("status") != "rejected":
            fail("polluted doc should be rejected/quarantined")
        plan_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "document-resource-ingestion.ts"),
                "--mode",
                "plan",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if plan_completed.returncode != 0:
            fail("document-resource-ingestion plan failed:\n" + plan_completed.stdout + plan_completed.stderr)
        plan = json.loads(plan_completed.stdout)
        if plan.get("mode") != "document-resource-ingestion.plan":
            fail("document-resource-ingestion plan mode changed: " + json.dumps(plan, ensure_ascii=False)[:500])
        proposed_paths = {write.get("path") for write in plan.get("proposedWrites", [])}
        if ".lazy-harness/project/document-intake.xml" not in proposed_paths or ".lazy-harness/knowledge/candidates.jsonl" not in proposed_paths:
            fail("document-resource-ingestion plan must propose intake ledger and candidates jsonl: " + json.dumps(plan.get("proposedWrites"), ensure_ascii=False))
        if len(plan.get("candidateEntries", [])) != 4:
            fail("document-resource-ingestion plan should create candidates for non-authoritative docs only")
        if any(entry.get("promotion") != "requires-user-confirmation" for entry in plan.get("candidateEntries", [])):
            fail("document-resource-ingestion candidates must require user confirmation")
        if not any("No DDD/SDD/BDD/TDD/ADR/SSOT promotion" in warning for warning in plan.get("warnings", [])):
            fail("document-resource-ingestion plan must warn against canonical promotion")
        dry_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "document-resource-ingestion.ts"),
                "--mode",
                "apply",
                "--dry-run",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if dry_completed.returncode != 0:
            fail("document-resource-ingestion apply --dry-run failed:\n" + dry_completed.stdout + dry_completed.stderr)
        dry_plan = json.loads(dry_completed.stdout)
        if dry_plan.get("mode") != "document-resource-ingestion.apply-dry-run" or dry_plan.get("dryRun") is not True:
            fail("document-resource-ingestion apply --dry-run should be explicit dry-run")
        blocked_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "document-resource-ingestion.ts"),
                "--mode",
                "apply",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if blocked_completed.returncode == 0 or "requires --dry-run" not in blocked_completed.stderr:
            fail("document-resource-ingestion apply without --dry-run must be blocked")
        apply_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "document-resource-ingestion.ts"),
                "--mode",
                "apply",
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if apply_completed.returncode != 0:
            fail("document-resource-ingestion apply --confirm failed:\n" + apply_completed.stdout + apply_completed.stderr)
        applied = json.loads(apply_completed.stdout)
        if applied.get("mode") != "document-resource-ingestion.apply" or applied.get("dryRun") is not False:
            fail("document-resource-ingestion apply --confirm should report real apply mode")
        ledger_path = root / ".lazy-harness" / "project" / "document-intake.xml"
        candidates_path = root / ".lazy-harness" / "knowledge" / "candidates.jsonl"
        if not ledger_path.exists() or "<documentIntake" not in ledger_path.read_text(encoding="utf-8"):
            fail("document-resource-ingestion apply --confirm should write document-intake.xml")
        candidate_lines = [line for line in candidates_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(candidate_lines) != 4:
            fail("document-resource-ingestion apply --confirm should append four candidate entries, got " + str(len(candidate_lines)))
        second_apply = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "document-resource-ingestion.ts"),
                "--mode",
                "apply",
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if second_apply.returncode != 0:
            fail("document-resource-ingestion second apply --confirm failed:\n" + second_apply.stdout + second_apply.stderr)
        candidate_lines_after = [line for line in candidates_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(candidate_lines_after) != 4:
            fail("document-resource-ingestion apply --confirm should dedupe candidate entries")
    print("✓ document-resource-ingestion inspect/plan/apply ok")


def check_project_profile_inspect() -> None:
    """Project Profile inspect mode must report missing/present artifacts and document-ingestion handoff."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / ".lazy-harness" / "project").mkdir(parents=True)
        (root / ".lazy-harness" / "tests").mkdir(parents=True)
        (root / ".lazy-harness" / "knowledge").mkdir(parents=True)
        (root / ".lazy-harness" / "project" / "document-intake.xml").write_text("<documentIntake />\n", encoding="utf-8")
        (root / ".lazy-harness" / "knowledge" / "candidates.jsonl").write_text("{}\n", encoding="utf-8")
        completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "inspect",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            fail("project-profile inspect failed:\n" + completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        if result.get("mode") != "project-profile.inspect":
            fail("project-profile inspect mode changed: " + completed.stdout[:500])
        summary = result.get("summary", {})
        if summary.get("present") != 0 or summary.get("missing") != 5:
            fail("project-profile inspect should count required artifacts")
        if summary.get("artifactsComplete") is not False or summary.get("answersComplete") is not False or summary.get("complete") is not False:
            fail("project-profile inspect should split artifact and answer completeness for missing profile")
        if summary.get("needsInterviewFields") != 0 or summary.get("confirmedFields") != 0:
            fail("project-profile inspect should count zero open fields when artifacts are missing")
        ingestion = result.get("documentIngestion") or {}
        if ingestion.get("ledgerStatus") != "present" or ingestion.get("candidatesStatus") != "present" or ingestion.get("shouldOfferIngestion") is not False:
            fail("project-profile inspect should detect document ingestion handoff outputs: " + json.dumps(ingestion, ensure_ascii=False))
        if not any("needs-interview skeleton" in option for option in result.get("optionGate", {}).get("options", [])):
            fail("project-profile inspect should return an option gate")
        plan_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "plan",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if plan_completed.returncode != 0:
            fail("project-profile plan failed:\n" + plan_completed.stdout + plan_completed.stderr)
        plan = json.loads(plan_completed.stdout)
        if plan.get("mode") != "project-profile.plan" or len(plan.get("proposedWrites", [])) != 4:
            fail("project-profile plan should propose four missing project skeletons")
        if any('status="needs-interview"' not in write.get("content", "") for write in plan.get("proposedWrites", [])):
            fail("project-profile plan must only propose needs-interview skeletons")
        blocked_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "apply",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if blocked_completed.returncode == 0 or "requires --dry-run" not in blocked_completed.stderr:
            fail("project-profile apply without --dry-run/--confirm must be blocked")
        apply_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "apply",
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if apply_completed.returncode != 0:
            fail("project-profile apply --confirm failed:\n" + apply_completed.stdout + apply_completed.stderr)
        applied = json.loads(apply_completed.stdout)
        if applied.get("mode") != "project-profile.apply" or len(applied.get("appliedWrites", [])) != 4:
            fail("project-profile apply --confirm should write four skeletons")
        for name in ["profile.xml", "stack.xml", "filesystem.xml", "feature-navigation.xml"]:
            content = (root / ".lazy-harness" / "project" / name).read_text(encoding="utf-8")
            if 'status="needs-interview"' not in content:
                fail("project-profile skeleton must preserve needs-interview status: " + name)
        after_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "inspect",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        after = json.loads(after_completed.stdout)
        after_summary = after.get("summary", {})
        if after_summary.get("complete") is not False or after_summary.get("present") != 4:
            fail("project-profile inspect after skeleton apply should see four project records and missing test strategy")
        if after_summary.get("artifactsComplete") is not False or after_summary.get("answersComplete") is not False or after_summary.get("needsInterviewFields") != 26:
            fail("project-profile inspect should show incomplete answers after skeleton apply")
        (root / ".lazy-harness" / "tests" / "test-strategy.xml").write_text(
            '<testStrategy version="1" status="confirmed"><command>lazy test</command></testStrategy>\n',
            encoding="utf-8",
        )
        complete_artifacts_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "inspect",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if complete_artifacts_completed.returncode != 0:
            fail("project-profile inspect with complete artifacts failed:\n" + complete_artifacts_completed.stdout + complete_artifacts_completed.stderr)
        complete_artifacts = json.loads(complete_artifacts_completed.stdout)
        complete_summary = complete_artifacts.get("summary", {})
        if complete_summary.get("present") != 5 or complete_summary.get("missing") != 0:
            fail("project-profile inspect should see all five artifacts after test strategy exists")
        if complete_summary.get("artifactsComplete") is not True or complete_summary.get("answersComplete") is not False or complete_summary.get("complete") is not False:
            fail("project-profile inspect must not report complete=true while needs-interview answers remain")
        if complete_summary.get("needsInterviewFields") != 26 or complete_summary.get("confirmedFields") != 1:
            fail("project-profile inspect should count needs-interview and confirmed fields across artifacts")
        if not any("--mode fill" in action for action in complete_artifacts.get("nextActions", [])):
            fail("project-profile inspect should point incomplete profiles to fill/interview flow")
        interview_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "interview",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if interview_completed.returncode != 0:
            fail("project-profile interview failed:\n" + interview_completed.stdout + interview_completed.stderr)
        interview = json.loads(interview_completed.stdout)
        questions = interview.get("questions", [])
        if interview.get("mode") != "project-profile.interview" or len(questions) != 22:
            fail("project-profile interview should emit open questions for all needs-interview skeleton fields: " + interview_completed.stdout[:500])
        targets = {question.get("target") for question in questions}
        for target in ["profile.purpose", "stack.frontend", "filesystem.sourceRoots", "step[layer=DDD]", "featureNavigation.sideEffectPolicy"]:
            if target not in targets:
                fail("project-profile interview missing expected target: " + target)
        if any("Answer now with confirmed project truth" not in "\n".join(question.get("options", [])) for question in questions):
            fail("project-profile interview questions must preserve A/B/C/D option gate wording")
        interview_apply_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "interview",
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if interview_apply_completed.returncode != 0:
            fail("project-profile interview --confirm failed:\n" + interview_apply_completed.stdout + interview_apply_completed.stderr)
        interview_apply = json.loads(interview_apply_completed.stdout)
        if interview_apply.get("mode") != "project-profile.interview-apply" or interview_apply.get("appliedWrites", [{}])[0].get("path") != ".lazy-harness/project/profile-interview.xml":
            fail("project-profile interview --confirm should write open-question transcript")
        ET.parse(root / ".lazy-harness" / "project" / "profile-interview.xml")
        answers_path = root / "answers.json"
        answers_path.write_text(json.dumps({"answers": [
            {"target": "profile.purpose", "value": "Build a safe test host", "source": "user-confirmed"},
            {"target": "stack.frontend", "value": "React"},
            {"target": "step[layer=DDD]", "value": "Start from domain records"},
            {"target": "missing.field", "value": "ignored"},
        ]}), encoding="utf-8")
        fill_blocked = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "fill",
                "--answers",
                str(answers_path),
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if fill_blocked.returncode == 0 or "requires --dry-run" not in fill_blocked.stderr:
            fail("project-profile fill without --dry-run/--confirm must be blocked")
        fill_dry_run = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "fill",
                "--answers",
                str(answers_path),
                "--dry-run",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if fill_dry_run.returncode != 0:
            fail("project-profile fill --dry-run failed:\n" + fill_dry_run.stdout + fill_dry_run.stderr)
        fill_preview = json.loads(fill_dry_run.stdout)
        if fill_preview.get("mode") != "project-profile.fill-dry-run" or len(fill_preview.get("proposedWrites", [])) != 3 or len(fill_preview.get("unmatchedAnswers", [])) != 1:
            fail("project-profile fill --dry-run should preview matching explicit answers only")
        fill_apply = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "fill",
                "--answers",
                str(answers_path),
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if fill_apply.returncode != 0:
            fail("project-profile fill --confirm failed:\n" + fill_apply.stdout + fill_apply.stderr)
        fill = json.loads(fill_apply.stdout)
        if fill.get("mode") != "project-profile.fill" or len(fill.get("appliedWrites", [])) != 3 or len(fill.get("unmatchedAnswers", [])) != 1:
            fail("project-profile fill --confirm should update matched fields and preserve unmatched answers")
        profile_content = (root / ".lazy-harness" / "project" / "profile.xml").read_text(encoding="utf-8")
        stack_content = (root / ".lazy-harness" / "project" / "stack.xml").read_text(encoding="utf-8")
        nav_content = (root / ".lazy-harness" / "project" / "feature-navigation.xml").read_text(encoding="utf-8")
        if 'status="confirmed"' not in profile_content or "Build a safe test host" not in profile_content or 'source="user-confirmed"' not in profile_content:
            fail("project-profile fill should confirm profile purpose with source")
        if 'status="confirmed"' not in stack_content or "React" not in stack_content:
            fail("project-profile fill should confirm stack frontend")
        if 'layer="DDD" status="confirmed"' not in nav_content or "Start from domain records" not in nav_content:
            fail("project-profile fill should confirm layer-specific navigation step")
        for name in ["profile.xml", "stack.xml", "filesystem.xml", "feature-navigation.xml"]:
            ET.parse(root / ".lazy-harness" / "project" / name)
    print("✓ project-profile inspect/plan/apply ok")


def check_project_profile_v2_runtime() -> None:
    """Project Profile V2 should emit a read-only interview packet without breaking V1 modes."""
    fixture_path = LAZY / "fixtures" / "project-profile-v2" / "interview-output.json"
    if not fixture_path.exists():
        fail("Project Profile V2 fixture missing: " + str(fixture_path.relative_to(ROOT)))
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        before_paths = sorted(str(path.relative_to(root)) for path in root.rglob("*"))
        blocked = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "interview-v2",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if blocked.returncode == 0 or "requires --dry-run" not in blocked.stderr:
            fail("project-profile interview-v2 without --dry-run must be blocked")
        confirmed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "interview-v2",
                "--dry-run",
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if confirmed.returncode == 0 or "--confirm is intentionally unsupported" not in confirmed.stderr:
            fail("project-profile interview-v2 --confirm must be blocked")
        completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "interview-v2",
                "--dry-run",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            fail("project-profile interview-v2 --dry-run failed:\n" + completed.stdout + completed.stderr)
        packet = json.loads(completed.stdout)
        after_paths = sorted(str(path.relative_to(root)) for path in root.rglob("*"))
        if after_paths != before_paths:
            fail("project-profile interview-v2 --dry-run must not write files: " + json.dumps(after_paths, ensure_ascii=False))

    required_top = {
        "schemaVersion",
        "mode",
        "adapterBoundary",
        "writes",
        "questionGroups",
        "projectMapSeeds",
        "policyCandidates",
        "unresolvedAmbiguities",
        "proposedWrites",
    }
    missing = sorted(required_top - set(packet))
    if missing:
        fail("project-profile interview-v2 packet missing fields: " + json.dumps(missing, ensure_ascii=False))
    if packet.get("schemaVersion") != "project-profile-interview-v2/v1" or packet.get("mode") != "interview-v2":
        fail("project-profile interview-v2 packet schema/mode mismatch: " + completed.stdout[:500])
    boundary = packet.get("adapterBoundary", {})
    if boundary.get("primary") != "pi" or "jcode" not in boundary.get("compatibility", []):
        fail("project-profile interview-v2 must keep Pi primary/Jcode compatibility")
    writes = packet.get("writes", {})
    if writes.get("dryRun") is not True or writes.get("confirmedOnly") is not True or writes.get("noSilentDefaults") is not True:
        fail("project-profile interview-v2 writes declaration must remain dry-run/confirmed-only/no-silent-defaults")
    group_ids = {group.get("id") for group in packet.get("questionGroups", [])}
    for expected in ("source-ownership", "system-design", "domain-vocabulary", "dependency-policy", "security-privacy", "human-confirmation"):
        if expected not in group_ids:
            fail("project-profile interview-v2 missing non-test question group: " + expected)
    fixture_group_ids = {group.get("id") for group in fixture.get("questionGroups", [])}
    if not fixture_group_ids.issubset(group_ids):
        fail("project-profile interview-v2 runtime must cover fixture question groups: " + json.dumps(sorted(fixture_group_ids - group_ids), ensure_ascii=False))
    seeds = packet.get("projectMapSeeds", [])
    if not seeds or not seeds[0].get("cluster", {}).get("branches") or not seeds[0].get("cluster", {}).get("edges"):
        fail("project-profile interview-v2 must include Project Map cluster seed branches and edges")
    policies = packet.get("policyCandidates", [])
    if len(policies) < 2 or not any(policy.get("dimension") != "validation" for policy in policies):
        fail("project-profile interview-v2 must include validation and non-test policy candidates")
    for policy in policies:
        if policy.get("confirmed") is not False:
            fail("project-profile interview-v2 policy candidates must remain unconfirmed")
        for stage in policy.get("stages", []):
            if stage.get("level") not in {"discover", "recommend"}:
                fail("project-profile interview-v2 initial policy level must be discover/recommend: " + json.dumps(stage, ensure_ascii=False))
    if not packet.get("unresolvedAmbiguities") or not any(item.get("id") == "policy-storage-target" for item in packet.get("unresolvedAmbiguities", [])):
        fail("project-profile interview-v2 must preserve unresolved policy-storage-target ambiguity")
    if not all(write.get("requiresConfirmation") is True for write in packet.get("proposedWrites", [])):
        fail("project-profile interview-v2 proposed writes must require confirmation")
    update_loop = packet.get("updateLoop", {})
    if update_loop.get("eventType") != "project-profile-refresh" or update_loop.get("source") != "project-profile":
        fail("project-profile interview-v2 must include project-profile-refresh update-loop metadata")
    transition = update_loop.get("transition", {})
    if transition.get("to") != "candidate" or transition.get("requiresConfirmation") is not True or transition.get("canonicalRecords") != []:
        fail("project-profile interview-v2 update-loop metadata must stay candidate-only")
    _assert_no_project_map_forbidden_fields(packet, "projectProfileInterviewV2")
    print("✓ project-profile V2 runtime ok")


def check_project_profile_v2_queue_runtime() -> None:
    """Project Profile V2 queue mode must write only a typed profile queue."""
    fixture_path = LAZY / "fixtures" / "project-profile-v2" / "profile-queue.json"
    if not fixture_path.exists():
        fail("Project Profile V2 queue fixture missing: " + str(fixture_path.relative_to(ROOT)))
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture.get("schemaVersion") != "project-profile-queue/v1" or fixture.get("mode") != "project-profile.queue-v2":
        fail("Project Profile V2 queue fixture schema/mode mismatch")
    promote_fixture_path = LAZY / "fixtures" / "project-profile-v2" / "promote-preview.json"
    if not promote_fixture_path.exists():
        fail("Project Profile V2 promote preview fixture missing: " + str(promote_fixture_path.relative_to(ROOT)))
    promote_fixture = json.loads(promote_fixture_path.read_text(encoding="utf-8"))
    if promote_fixture.get("schemaVersion") != "project-profile-promote-preview/v1" or promote_fixture.get("mode") != "project-profile.promote-v2":
        fail("Project Profile V2 promote preview fixture schema/mode mismatch")
    promote_confirm_fixture_path = LAZY / "fixtures" / "project-profile-v2" / "promote-confirm.json"
    if not promote_confirm_fixture_path.exists():
        fail("Project Profile V2 promote confirm fixture missing: " + str(promote_confirm_fixture_path.relative_to(ROOT)))
    promote_confirm_fixture = json.loads(promote_confirm_fixture_path.read_text(encoding="utf-8"))
    if promote_confirm_fixture.get("schemaVersion") != "project-profile-promote-result/v1" or promote_confirm_fixture.get("mode") != "project-profile.promote-v2-apply":
        fail("Project Profile V2 promote confirm fixture schema/mode mismatch")
    promote_record_fixture_path = LAZY / "fixtures" / "project-profile-v2" / "promote-record.json"
    if not promote_record_fixture_path.exists():
        fail("Project Profile V2 promote record fixture missing: " + str(promote_record_fixture_path.relative_to(ROOT)))
    promote_record_fixture = json.loads(promote_record_fixture_path.read_text(encoding="utf-8"))
    if promote_record_fixture.get("schemaVersion") != "project-profile-promote-result/v1" or promote_record_fixture.get("mode") != "project-profile.promote-v2-apply":
        fail("Project Profile V2 promote record fixture schema/mode mismatch")
    promote_branch_fixture_path = LAZY / "fixtures" / "project-profile-v2" / "promote-project-map-branch.json"
    if not promote_branch_fixture_path.exists():
        fail("Project Profile V2 promote project-map-branch fixture missing: " + str(promote_branch_fixture_path.relative_to(ROOT)))
    promote_branch_fixture = json.loads(promote_branch_fixture_path.read_text(encoding="utf-8"))
    if promote_branch_fixture.get("schemaVersion") != "project-profile-promote-result/v1" or promote_branch_fixture.get("mode") != "project-profile.promote-v2-apply":
        fail("Project Profile V2 promote project-map-branch fixture schema/mode mismatch")
    promote_candidate_fixture_path = LAZY / "fixtures" / "project-profile-v2" / "promote-candidate-row.json"
    if not promote_candidate_fixture_path.exists():
        fail("Project Profile V2 promote candidate-row fixture missing: " + str(promote_candidate_fixture_path.relative_to(ROOT)))
    promote_candidate_fixture = json.loads(promote_candidate_fixture_path.read_text(encoding="utf-8"))
    if promote_candidate_fixture.get("schemaVersion") != "project-profile-promote-result/v1" or promote_candidate_fixture.get("mode") != "project-profile.promote-v2-apply":
        fail("Project Profile V2 promote candidate-row fixture schema/mode mismatch")
    promote_rulebook_fixture_path = LAZY / "fixtures" / "project-profile-v2" / "promote-rulebook.json"
    if not promote_rulebook_fixture_path.exists():
        fail("Project Profile V2 promote rulebook fixture missing: " + str(promote_rulebook_fixture_path.relative_to(ROOT)))
    promote_rulebook_fixture = json.loads(promote_rulebook_fixture_path.read_text(encoding="utf-8"))
    if promote_rulebook_fixture.get("schemaVersion") != "project-profile-promote-result/v1" or promote_rulebook_fixture.get("mode") != "project-profile.promote-v2-apply":
        fail("Project Profile V2 promote rulebook fixture schema/mode mismatch")
    promote_capability_fixture_path = LAZY / "fixtures" / "project-profile-v2" / "promote-capability-binding.json"
    if not promote_capability_fixture_path.exists():
        fail("Project Profile V2 promote capability-binding fixture missing: " + str(promote_capability_fixture_path.relative_to(ROOT)))
    promote_capability_fixture = json.loads(promote_capability_fixture_path.read_text(encoding="utf-8"))
    if promote_capability_fixture.get("schemaVersion") != "project-profile-promote-result/v1" or promote_capability_fixture.get("mode") != "project-profile.promote-v2-apply":
        fail("Project Profile V2 promote capability-binding fixture schema/mode mismatch")
    promote_update_loop_fixture_path = LAZY / "fixtures" / "project-profile-v2" / "promote-update-loop-event.json"
    if not promote_update_loop_fixture_path.exists():
        fail("Project Profile V2 promote update-loop-event fixture missing: " + str(promote_update_loop_fixture_path.relative_to(ROOT)))
    promote_update_loop_fixture = json.loads(promote_update_loop_fixture_path.read_text(encoding="utf-8"))
    if promote_update_loop_fixture.get("schemaVersion") != "project-profile-promote-result/v1" or promote_update_loop_fixture.get("mode") != "project-profile.promote-v2-apply":
        fail("Project Profile V2 promote update-loop-event fixture schema/mode mismatch")
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        blocked = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "queue-v2",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if blocked.returncode == 0 or "requires --dry-run or --confirm" not in blocked.stderr:
            fail("project-profile queue-v2 without --dry-run/--confirm must be blocked")
        before_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        dry_run = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "queue-v2",
                "--dry-run",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if dry_run.returncode != 0:
            fail("project-profile queue-v2 --dry-run failed:\n" + dry_run.stdout + dry_run.stderr)
        queue = json.loads(dry_run.stdout)
        after_dry_run_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        if after_dry_run_files != before_files:
            fail("project-profile queue-v2 --dry-run must not write files: " + json.dumps(after_dry_run_files, ensure_ascii=False))
        confirm = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "queue-v2",
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if confirm.returncode != 0:
            fail("project-profile queue-v2 --confirm failed:\n" + confirm.stdout + confirm.stderr)
        applied = json.loads(confirm.stdout)
        written_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        if written_files != [".lazy-harness/project/profile-queue.json"]:
            fail("project-profile queue-v2 --confirm must write only profile-queue.json: " + json.dumps(written_files, ensure_ascii=False))
        written_queue = json.loads((root / ".lazy-harness" / "project" / "profile-queue.json").read_text(encoding="utf-8"))
        if "appliedWrites" in written_queue:
            fail("written profile queue must not persist transient appliedWrites")
        if applied.get("mode") != "project-profile.queue-v2-apply" or applied.get("appliedWrites", [{}])[0].get("path") != ".lazy-harness/project/profile-queue.json":
            fail("project-profile queue-v2 --confirm should report only profile-queue.json write")
        pending_item_id = written_queue["items"][0]["id"]
        deferred_item_id = "PPQ-queue-only-deferred-boundary"
        pending_promote = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                pending_item_id,
                "--dry-run",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if pending_promote.returncode == 0 or "only promotes status=accepted" not in pending_promote.stderr:
            fail("project-profile promote-v2 must reject pending queue items")
        no_dry_run_promote = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                pending_item_id,
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if no_dry_run_promote.returncode == 0 or "requires --dry-run for preview or --confirm" not in no_dry_run_promote.stderr:
            fail("project-profile promote-v2 without --dry-run/--confirm must be blocked")
        written_queue["items"][0]["status"] = "accepted"
        queue_file = root / ".lazy-harness" / "project" / "profile-queue.json"
        queue_file.write_text(json.dumps(written_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before_promote_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        before_promote_queue = queue_file.read_text(encoding="utf-8")
        promote = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                pending_item_id,
                "--dry-run",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote.returncode != 0:
            fail("project-profile promote-v2 --dry-run failed:\n" + promote.stdout + promote.stderr)
        promote_preview = json.loads(promote.stdout)
        after_promote_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        after_promote_queue = queue_file.read_text(encoding="utf-8")
        if after_promote_files != before_promote_files or after_promote_queue != before_promote_queue:
            fail("project-profile promote-v2 --dry-run must not write files or mutate queue")
        if promote_preview.get("schemaVersion") != promote_fixture.get("schemaVersion") or promote_preview.get("mode") != promote_fixture.get("mode"):
            fail("project-profile promote-v2 preview schema/mode mismatch")
        if promote_preview.get("item", {}).get("id") != pending_item_id or promote_preview.get("item", {}).get("status") != "accepted":
            fail("project-profile promote-v2 preview must echo the accepted item")
        queue_update = promote_preview.get("queueUpdate", {})
        if queue_update.get("from") != "accepted" or queue_update.get("to") != "promoted" or queue_update.get("previewOnly") is not True:
            fail("project-profile promote-v2 preview must include accepted→promoted preview queue update")
        planned_writes = promote_preview.get("plannedWrites", [])
        if not planned_writes or planned_writes[0].get("requiresConfirmation") is not True or planned_writes[0].get("action") != promote_fixture.get("plannedWrites", [{}])[0].get("action"):
            fail("project-profile promote-v2 preview must expose confirmation-gated planned writes")
        before_record_confirm_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        promote_record = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                pending_item_id,
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_record.returncode != 0:
            fail("project-profile promote-v2 record target --confirm failed:\n" + promote_record.stdout + promote_record.stderr)
        promote_record_result = json.loads(promote_record.stdout)
        after_record_confirm_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        expected_record_files = sorted(before_record_confirm_files + [".lazy-harness/domain/project-purpose.md"])
        if after_record_confirm_files != expected_record_files:
            fail("project-profile promote-v2 record target must write only queue plus deterministic record: " + json.dumps(after_record_confirm_files, ensure_ascii=False))
        confirmed_queue = json.loads(queue_file.read_text(encoding="utf-8"))
        if "appliedWrites" in confirmed_queue:
            fail("promote-v2 --confirm must not persist transient appliedWrites in queue file")
        confirmed_item = confirmed_queue["items"][0]
        if confirmed_item.get("id") != pending_item_id or confirmed_item.get("status") != "promoted":
            fail("promote-v2 --confirm must mark exactly the selected accepted item as promoted")
        if not confirmed_item.get("promotedAt") or confirmed_item.get("promotedTo") != [promote_record_fixture.get("targetEffects", [{}])[0].get("path")]:
            fail("promote-v2 --confirm must persist promotedAt/promotedTo metadata")
        effects = confirmed_item.get("promotionEffects", [])
        if not effects or effects[0].get("status") != "applied" or effects[0].get("action") != "create-record":
            fail("promote-v2 --confirm must persist applied record target effects")
        if confirmed_queue.get("summary", {}).get("pending") != len(confirmed_queue.get("items", [])) - 1:
            fail("promote-v2 --confirm must update queue pending summary")
        record_file = root / ".lazy-harness" / "domain" / "project-purpose.md"
        record_text = record_file.read_text(encoding="utf-8")
        if "Status: needs-interview" not in record_text or "treat this generated skeleton as confirmed project truth" not in record_text:
            fail("project-profile promote-v2 record target must create a needs-interview skeleton with anti-truth warning")
        if promote_record_result.get("schemaVersion") != promote_record_fixture.get("schemaVersion") or promote_record_result.get("mode") != promote_record_fixture.get("mode"):
            fail("project-profile promote-v2 record schema/mode mismatch")
        if promote_record_result.get("item", {}).get("status") != "promoted" or promote_record_result.get("queueUpdate", {}).get("previewOnly") is not False:
            fail("project-profile promote-v2 record target must report a real queue status update")
        record_target_effects = promote_record_result.get("targetEffects", [])
        if not record_target_effects or record_target_effects[0].get("status") != promote_record_fixture.get("targetEffects", [{}])[0].get("status") or record_target_effects[0].get("action") != promote_record_fixture.get("targetEffects", [{}])[0].get("action"):
            fail("project-profile promote-v2 record target must expose applied record effects")
        record_applied_writes = promote_record_result.get("appliedWrites", [])
        if record_applied_writes != promote_record_fixture.get("appliedWrites"):
            fail("project-profile promote-v2 record target must report record and queue writes")
        promote_again = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                pending_item_id,
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_again.returncode == 0 or "status=promoted" not in promote_again.stderr:
            fail("project-profile promote-v2 --confirm must reject already-promoted items")
        deferred_item = {
            "id": deferred_item_id,
            "status": "accepted",
            "primaryRoute": "queue-only",
            "facets": ["Project"],
            "relatedRoutes": [],
            "source": {"kind": "proposed-write", "id": "queue-only-deferred-boundary"},
            "summary": "Synthetic queue-only deferred boundary fixture",
            "evidence": [{"kind": "self-test", "summary": "Protect deferred target writer boundary for queue-only items."}],
            "promotionTarget": {"kind": "queue-only", "requiresConfirmation": True},
        }
        confirmed_queue["items"].insert(0, deferred_item)
        queue_file.write_text(json.dumps(confirmed_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before_non_record_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        promote_non_record = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                deferred_item_id,
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_non_record.returncode != 0:
            fail("project-profile promote-v2 deferred-only target --confirm failed:\n" + promote_non_record.stdout + promote_non_record.stderr)
        non_record_result = json.loads(promote_non_record.stdout)
        after_non_record_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        if after_non_record_files != before_non_record_files:
            fail("project-profile promote-v2 deferred-only target must not write additional canonical files")
        non_record_effects = non_record_result.get("targetEffects", [])
        if not non_record_effects or non_record_effects[0].get("status") != promote_confirm_fixture.get("targetEffects", [{}])[0].get("status") or non_record_effects[0].get("action") != "defer-target-writer":
            fail("project-profile promote-v2 deferred-only target must remain deferred")
        non_record_writes = non_record_result.get("appliedWrites", [])
        if len(non_record_writes) != 1 or non_record_writes[0].get("path") != ".lazy-harness/project/profile-queue.json" or non_record_writes[0].get("action") != "written":
            fail("project-profile promote-v2 deferred-only target must report only queue-file applied write")
        branch_item = json.loads(json.dumps(promote_branch_fixture["item"]))
        branch_item["status"] = "accepted"
        branch_item.pop("promotedAt", None)
        branch_item.pop("promotedTo", None)
        branch_item.pop("promotionEffects", None)
        branch_queue = json.loads(queue_file.read_text(encoding="utf-8"))
        branch_queue["items"].insert(0, branch_item)
        queue_file.write_text(json.dumps(branch_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before_branch_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        promote_branch = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                branch_item["id"],
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_branch.returncode != 0:
            fail("project-profile promote-v2 project-map-branch target --confirm failed:\n" + promote_branch.stdout + promote_branch.stderr)
        branch_result = json.loads(promote_branch.stdout)
        after_branch_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        expected_branch_files = sorted(before_branch_files + [".lazy-harness/project/feature-navigation.xml"])
        if after_branch_files != expected_branch_files:
            fail("project-profile promote-v2 project-map-branch target must write only queue plus feature-navigation.xml: " + json.dumps(after_branch_files, ensure_ascii=False))
        feature_nav_path = root / ".lazy-harness" / "project" / "feature-navigation.xml"
        feature_root = ET.parse(feature_nav_path).getroot()
        feature_nodes = feature_root.findall("feature")
        matching_features = [node for node in feature_nodes if node.attrib.get("id") == promote_branch_fixture.get("projectMapBranch", {}).get("id")]
        if len(matching_features) != 1:
            fail("project-profile promote-v2 project-map-branch target must append exactly one matching feature entry")
        feature_node = matching_features[0]
        if feature_node.attrib.get("status") != "candidate" or (feature_node.findtext("label") or "").strip() != promote_branch_fixture.get("projectMapBranch", {}).get("label"):
            fail("project-profile promote-v2 project-map-branch feature entry must remain candidate with expected label")
        if branch_result.get("projectMapBranch") != promote_branch_fixture.get("projectMapBranch"):
            fail("project-profile promote-v2 project-map-branch target must return the appended feature metadata")
        branch_effects = branch_result.get("targetEffects", [])
        if not branch_effects or branch_effects[0].get("status") != "applied" or branch_effects[0].get("action") != "append-project-map-branch":
            fail("project-profile promote-v2 project-map-branch target must expose applied branch effect")
        if branch_result.get("appliedWrites") != promote_branch_fixture.get("appliedWrites"):
            fail("project-profile promote-v2 project-map-branch target must report feature navigation and queue writes")
        _assert_no_project_map_forbidden_fields(branch_result, "projectProfilePromoteV2ProjectMapBranch")
        record_index = subprocess.run(
            ["bun", str(LAZY / "scripts" / "record-index.ts"), "--root", str(root), "--format=json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if record_index.returncode != 0:
            fail("project-profile promote-v2 project-map-branch output must be parseable by record-index:\n" + record_index.stdout + record_index.stderr)
        profile_features = json.loads(record_index.stdout).get("projectProfile", {}).get("features", [])
        if promote_branch_fixture.get("projectMapBranch", {}).get("id") not in {feature.get("id") for feature in profile_features}:
            fail("record-index must include promoted project-map-branch feature id")
        branch_nav_before = feature_nav_path.read_text(encoding="utf-8")
        branch_dedupe_queue = json.loads(queue_file.read_text(encoding="utf-8"))
        branch_dedupe_queue["items"] = [
            {k: v for k, v in {**item, "status": "accepted"}.items() if k not in {"promotedAt", "promotedTo", "promotionEffects"}}
            if item.get("id") == branch_item["id"] else item
            for item in branch_dedupe_queue["items"]
        ]
        queue_file.write_text(json.dumps(branch_dedupe_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        promote_branch_again = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                branch_item["id"],
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_branch_again.returncode != 0:
            fail("project-profile promote-v2 project-map-branch idempotence run failed:\n" + promote_branch_again.stdout + promote_branch_again.stderr)
        branch_again_result = json.loads(promote_branch_again.stdout)
        if feature_nav_path.read_text(encoding="utf-8") != branch_nav_before:
            fail("project-profile promote-v2 project-map-branch duplicate run must not alter feature-navigation.xml")
        if branch_again_result.get("targetEffects", [{}])[0].get("action") != "skip-existing-project-map-branch" or branch_again_result.get("appliedWrites", [{}])[0].get("action") != "skipped":
            fail("project-profile promote-v2 project-map-branch duplicate run must report skip-existing")
        candidate_item = json.loads(json.dumps(promote_candidate_fixture["item"]))
        candidate_item["status"] = "accepted"
        candidate_item.pop("promotedAt", None)
        candidate_item.pop("promotedTo", None)
        candidate_item.pop("promotionEffects", None)
        latest_queue = json.loads(queue_file.read_text(encoding="utf-8"))
        latest_queue["items"].insert(0, candidate_item)
        queue_file.write_text(json.dumps(latest_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before_candidate_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        promote_candidate = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                candidate_item["id"],
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_candidate.returncode != 0:
            fail("project-profile promote-v2 candidate-row target --confirm failed:\n" + promote_candidate.stdout + promote_candidate.stderr)
        candidate_result = json.loads(promote_candidate.stdout)
        after_candidate_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        expected_candidate_files = sorted(before_candidate_files + [".lazy-harness/knowledge/candidates.jsonl"])
        if after_candidate_files != expected_candidate_files:
            fail("project-profile promote-v2 candidate-row target must write only queue plus candidates.jsonl: " + json.dumps(after_candidate_files, ensure_ascii=False))
        candidates_path = root / ".lazy-harness" / "knowledge" / "candidates.jsonl"
        candidate_rows = [json.loads(line) for line in candidates_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if candidate_rows != [promote_candidate_fixture.get("candidateRow")]:
            fail("project-profile promote-v2 candidate-row target must append the stable candidate row")
        candidate_effects = candidate_result.get("targetEffects", [])
        if not candidate_effects or candidate_effects[0].get("status") != "applied" or candidate_effects[0].get("action") != "append-candidate-row":
            fail("project-profile promote-v2 candidate-row target must expose applied candidate effect")
        if candidate_result.get("candidateRow") != promote_candidate_fixture.get("candidateRow"):
            fail("project-profile promote-v2 candidate-row target must return the appended candidate row")
        if candidate_result.get("appliedWrites") != promote_candidate_fixture.get("appliedWrites"):
            fail("project-profile promote-v2 candidate-row target must report candidate and queue writes")
        dedupe_queue = json.loads(queue_file.read_text(encoding="utf-8"))
        dedupe_queue["items"] = [
            {k: v for k, v in {**item, "status": "accepted"}.items() if k not in {"promotedAt", "promotedTo", "promotionEffects"}}
            if item.get("id") == candidate_item["id"] else item
            for item in dedupe_queue["items"]
        ]
        queue_file.write_text(json.dumps(dedupe_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        promote_candidate_again = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                candidate_item["id"],
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_candidate_again.returncode != 0:
            fail("project-profile promote-v2 candidate-row dedupe run failed:\n" + promote_candidate_again.stdout + promote_candidate_again.stderr)
        dedupe_result = json.loads(promote_candidate_again.stdout)
        candidate_rows_after = [json.loads(line) for line in candidates_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if candidate_rows_after != candidate_rows:
            fail("project-profile promote-v2 candidate-row duplicate run must not append another row")
        if dedupe_result.get("appliedWrites", [{}])[0].get("action") != "deduped-identical" or dedupe_result.get("targetEffects", [{}])[0].get("action") != "dedupe-candidate-row":
            fail("project-profile promote-v2 candidate-row duplicate run must report dedupe")
        rulebook_item = json.loads(json.dumps(promote_rulebook_fixture["item"]))
        rulebook_item["status"] = "accepted"
        rulebook_item.pop("promotedAt", None)
        rulebook_item.pop("promotedTo", None)
        rulebook_item.pop("promotionEffects", None)
        rulebook_queue = json.loads(queue_file.read_text(encoding="utf-8"))
        rulebook_queue["items"].insert(0, rulebook_item)
        queue_file.write_text(json.dumps(rulebook_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before_rulebook_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        promote_rulebook = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                rulebook_item["id"],
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_rulebook.returncode != 0:
            fail("project-profile promote-v2 rulebook target --confirm failed:\n" + promote_rulebook.stdout + promote_rulebook.stderr)
        rulebook_result = json.loads(promote_rulebook.stdout)
        after_rulebook_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        expected_rulebook_files = sorted(before_rulebook_files + [".lazy-harness/rules/workflow-policy.md"])
        if after_rulebook_files != expected_rulebook_files:
            fail("project-profile promote-v2 rulebook target must write only queue plus rulebook draft: " + json.dumps(after_rulebook_files, ensure_ascii=False))
        rulebook_path = root / ".lazy-harness" / "rules" / "workflow-policy.md"
        rulebook_text = rulebook_path.read_text(encoding="utf-8")
        required_rulebook_snippets = ["Status: draft", "Layer: Rulebook", "Level: discover", "Capability id: none yet", "must not be treated as active default/warn/block behavior"]
        missing_rulebook_snippets = [snippet for snippet in required_rulebook_snippets if snippet not in rulebook_text]
        if missing_rulebook_snippets:
            fail("project-profile promote-v2 rulebook target missing draft/discover safeguards: " + json.dumps(missing_rulebook_snippets, ensure_ascii=False))
        if (root / ".lazy-harness" / "ssot" / "capabilities.json").exists():
            fail("project-profile promote-v2 rulebook target must not create capabilities.json")
        rulebook_effects = rulebook_result.get("targetEffects", [])
        if not rulebook_effects or rulebook_effects[0].get("status") != "applied" or rulebook_effects[0].get("action") != "create-rulebook":
            fail("project-profile promote-v2 rulebook target must expose applied rulebook effect")
        if rulebook_result.get("appliedWrites") != promote_rulebook_fixture.get("appliedWrites"):
            fail("project-profile promote-v2 rulebook target must report rulebook and queue writes")
        audit_rulebook = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "rules", "audit", "--strict", "--format=json", "--target", str(root)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if audit_rulebook.returncode != 0:
            fail("project-profile promote-v2 generated rulebook entry must pass strict rule audit:\n" + audit_rulebook.stdout + audit_rulebook.stderr)
        audit_json = json.loads(audit_rulebook.stdout)
        if audit_json.get("ok") is not True or audit_json.get("count") != 1:
            fail("project-profile promote-v2 generated rulebook audit result unexpected: " + audit_rulebook.stdout)
        capability_item = json.loads(json.dumps(promote_capability_fixture["item"]))
        capability_item["status"] = "accepted"
        capability_item.pop("promotedAt", None)
        capability_item.pop("promotedTo", None)
        capability_item.pop("promotionEffects", None)
        capability_queue = json.loads(queue_file.read_text(encoding="utf-8"))
        capability_queue["items"].insert(0, capability_item)
        queue_file.write_text(json.dumps(capability_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before_capability_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        promote_capability = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                capability_item["id"],
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_capability.returncode != 0:
            fail("project-profile promote-v2 capability-binding target --confirm failed:\n" + promote_capability.stdout + promote_capability.stderr)
        capability_result = json.loads(promote_capability.stdout)
        after_capability_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        expected_capability_files = sorted(before_capability_files + [".lazy-harness/ssot/capabilities.json"])
        if after_capability_files != expected_capability_files:
            fail("project-profile promote-v2 capability-binding target must write only queue plus capabilities.json: " + json.dumps(after_capability_files, ensure_ascii=False))
        capabilities_path = root / ".lazy-harness" / "ssot" / "capabilities.json"
        registry = json.loads(capabilities_path.read_text(encoding="utf-8"))
        if registry.get("capabilities") != [promote_capability_fixture.get("capability")]:
            fail("project-profile promote-v2 capability-binding target must write the expected discover/checklist capability")
        cap = registry["capabilities"][0]
        if cap.get("level") != "discover" or cap.get("kind") != "checklist" or cap.get("sourceRecord") != ".lazy-harness/project/profile-queue.json":
            fail("project-profile promote-v2 capability-binding target must remain discover/checklist with queue sourceRecord")
        if cap.get("level") in {"default", "warn", "block"} or cap.get("kind") == "hook":
            fail("project-profile promote-v2 capability-binding target must not create enforcement capability")
        capability_effects = capability_result.get("targetEffects", [])
        if not capability_effects or capability_effects[0].get("status") != "applied" or capability_effects[0].get("action") != "upsert-capability":
            fail("project-profile promote-v2 capability-binding target must expose applied capability effect")
        if capability_result.get("capability") != promote_capability_fixture.get("capability"):
            fail("project-profile promote-v2 capability-binding target must return the upserted capability")
        if capability_result.get("appliedWrites") != promote_capability_fixture.get("appliedWrites"):
            fail("project-profile promote-v2 capability-binding target must report capability and queue writes")
        audit_capability = subprocess.run(
            ["bun", str(LAZY / "scripts" / "capability.ts"), "audit", "--format=json", "--target", str(root)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if audit_capability.returncode != 0:
            fail("project-profile promote-v2 generated capability registry must pass audit:\n" + audit_capability.stdout + audit_capability.stderr)
        audit_capability_json = json.loads(audit_capability.stdout)
        if audit_capability_json.get("ok") is not True or audit_capability_json.get("count") != 1:
            fail("project-profile promote-v2 generated capability audit result unexpected: " + audit_capability.stdout)
        capability_dedupe_queue = json.loads(queue_file.read_text(encoding="utf-8"))
        capability_dedupe_queue["items"] = [
            {k: v for k, v in {**item, "status": "accepted"}.items() if k not in {"promotedAt", "promotedTo", "promotionEffects"}}
            if item.get("id") == capability_item["id"] else item
            for item in capability_dedupe_queue["items"]
        ]
        queue_file.write_text(json.dumps(capability_dedupe_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        promote_capability_again = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                capability_item["id"],
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_capability_again.returncode != 0:
            fail("project-profile promote-v2 capability-binding unchanged run failed:\n" + promote_capability_again.stdout + promote_capability_again.stderr)
        capability_again_result = json.loads(promote_capability_again.stdout)
        registry_after = json.loads(capabilities_path.read_text(encoding="utf-8"))
        if registry_after != registry:
            fail("project-profile promote-v2 capability-binding unchanged run must not alter registry")
        if capability_again_result.get("appliedWrites", [{}])[0].get("action") != "unchanged":
            fail("project-profile promote-v2 capability-binding unchanged run must report unchanged upsert")
        update_item = json.loads(json.dumps(promote_update_loop_fixture["item"]))
        update_item["status"] = "accepted"
        update_item.pop("promotedAt", None)
        update_item.pop("promotedTo", None)
        update_item.pop("promotionEffects", None)
        update_queue = json.loads(queue_file.read_text(encoding="utf-8"))
        update_queue.setdefault("sourcePacket", {})["generatedAt"] = promote_update_loop_fixture.get("updateEvent", {}).get("occurredAt")
        update_queue["items"].insert(0, update_item)
        queue_file.write_text(json.dumps(update_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before_update_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        before_candidates_text = candidates_path.read_text(encoding="utf-8") if candidates_path.exists() else ""
        promote_update_loop = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                update_item["id"],
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_update_loop.returncode != 0:
            fail("project-profile promote-v2 update-loop-event target --confirm failed:\n" + promote_update_loop.stdout + promote_update_loop.stderr)
        update_result = json.loads(promote_update_loop.stdout)
        after_update_files = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
        expected_update_files = sorted(before_update_files + [".lazy-harness/knowledge/project-map-update-events.jsonl"])
        if after_update_files != expected_update_files:
            fail("project-profile promote-v2 update-loop-event target must write only queue plus update event log: " + json.dumps(after_update_files, ensure_ascii=False))
        if candidates_path.exists() and candidates_path.read_text(encoding="utf-8") != before_candidates_text:
            fail("project-profile promote-v2 update-loop-event target must not mutate candidates.jsonl")
        update_events_path = root / ".lazy-harness" / "knowledge" / "project-map-update-events.jsonl"
        update_rows = [json.loads(line) for line in update_events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if update_rows != [promote_update_loop_fixture.get("updateEvent")]:
            fail("project-profile promote-v2 update-loop-event target must append the expected non-canonical update event")
        update_effects = update_result.get("targetEffects", [])
        if not update_effects or update_effects[0].get("status") != "applied" or update_effects[0].get("action") != "append-update-loop-event":
            fail("project-profile promote-v2 update-loop-event target must expose applied update-loop effect")
        if update_result.get("updateEvent") != promote_update_loop_fixture.get("updateEvent"):
            fail("project-profile promote-v2 update-loop-event target must return the appended update event")
        if update_result.get("appliedWrites") != promote_update_loop_fixture.get("appliedWrites"):
            fail("project-profile promote-v2 update-loop-event target must report update event and queue writes")
        _assert_no_project_map_forbidden_fields(update_result, "projectProfilePromoteV2UpdateLoop")
        update_dedupe_queue = json.loads(queue_file.read_text(encoding="utf-8"))
        update_dedupe_queue["items"] = [
            {k: v for k, v in {**item, "status": "accepted"}.items() if k not in {"promotedAt", "promotedTo", "promotionEffects"}}
            if item.get("id") == update_item["id"] else item
            for item in update_dedupe_queue["items"]
        ]
        queue_file.write_text(json.dumps(update_dedupe_queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        promote_update_loop_again = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "project-profile.ts"),
                "--mode",
                "promote-v2",
                "--item",
                update_item["id"],
                "--confirm",
                "--format=json",
                "--root",
                str(root),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if promote_update_loop_again.returncode != 0:
            fail("project-profile promote-v2 update-loop-event dedupe run failed:\n" + promote_update_loop_again.stdout + promote_update_loop_again.stderr)
        update_again_result = json.loads(promote_update_loop_again.stdout)
        update_rows_after = [json.loads(line) for line in update_events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if update_rows_after != update_rows:
            fail("project-profile promote-v2 update-loop-event duplicate run must not append another event")
        if update_again_result.get("appliedWrites", [{}])[0].get("action") != "deduped-identical" or update_again_result.get("targetEffects", [{}])[0].get("action") != "dedupe-update-loop-event":
            fail("project-profile promote-v2 update-loop-event duplicate run must report dedupe")
        if (root / ".lazy-harness" / "knowledge" / "project-map-update-events.jsonl.conflicts.jsonl").exists():
            fail("project-profile promote-v2 update-loop-event duplicate run must not record a conflict for identical event")

    required_top = {"schemaVersion", "mode", "queuePath", "sourcePacket", "items", "summary", "dryRunSource"}
    missing = sorted(required_top - set(queue))
    if missing:
        fail("project-profile queue-v2 packet missing fields: " + json.dumps(missing, ensure_ascii=False))
    if queue.get("schemaVersion") != "project-profile-queue/v1" or queue.get("queuePath") != ".lazy-harness/project/profile-queue.json":
        fail("project-profile queue-v2 schema/path mismatch")
    if queue.get("sourcePacket", {}).get("schemaVersion") != "project-profile-interview-v2/v1":
        fail("project-profile queue-v2 must reference interview-v2 source packet")
    items = queue.get("items", [])
    if not isinstance(items, list) or not items:
        fail("project-profile queue-v2 must emit queue items")
    allowed_routes = {"facts", "expectations", "contracts", "validation", "decisions", "ownership", "source-links", "policies", "event-ready-metadata", "queue-only"}
    allowed_statuses = {"pending", "accepted", "rejected", "promoted", "superseded"}
    allowed_promotion_kinds = {"record", "project-map-branch", "rulebook", "capability-binding", "candidate-row", "update-loop-event", "queue-only"}
    seen_routes = set()
    has_multifacet = False
    has_non_policy = False
    has_policy = False
    has_event_ready = False
    for item in items:
        for key in ("id", "status", "primaryRoute", "facets", "relatedRoutes", "source", "summary", "evidence", "promotionTarget"):
            if key not in item:
                fail("project-profile queue-v2 item missing key: " + key)
        if item.get("status") not in allowed_statuses:
            fail("project-profile queue-v2 item status invalid: " + json.dumps(item, ensure_ascii=False))
        route = item.get("primaryRoute")
        if route not in allowed_routes:
            fail("project-profile queue-v2 item primaryRoute invalid: " + json.dumps(item, ensure_ascii=False))
        seen_routes.add(route)
        facets = item.get("facets")
        related_routes = item.get("relatedRoutes")
        if not isinstance(facets, list) or not facets:
            fail("project-profile queue-v2 item must include non-empty facets: " + json.dumps(item, ensure_ascii=False))
        if not isinstance(related_routes, list):
            fail("project-profile queue-v2 relatedRoutes must be a list")
        if len(facets) > 1 and related_routes:
            has_multifacet = True
        if item.get("source", {}).get("kind") != "policy-candidate":
            has_non_policy = True
        if item.get("source", {}).get("kind") == "policy-candidate":
            has_policy = True
            if route != "policies":
                fail("policy-candidate source items should use primaryRoute=policies: " + json.dumps(item, ensure_ascii=False))
            if item.get("promotionTarget", {}).get("kind") not in {"rulebook", "capability-binding"}:
                fail("policy-candidate queue items should promote to rulebook/capability targets: " + json.dumps(item, ensure_ascii=False))
        if route == "event-ready-metadata":
            has_event_ready = True
            if item.get("promotionTarget", {}).get("kind") != "update-loop-event":
                fail("event-ready metadata should promote only to update-loop-event target")
        promotion = item.get("promotionTarget", {})
        if promotion.get("kind") not in allowed_promotion_kinds or promotion.get("requiresConfirmation") is not True:
            fail("project-profile queue-v2 promotion target invalid: " + json.dumps(item, ensure_ascii=False))
        if not isinstance(item.get("evidence"), list) or not item.get("evidence"):
            fail("project-profile queue-v2 items must include evidence")
    if not has_multifacet:
        fail("project-profile queue-v2 must include at least one multi-facet item")
    if not has_non_policy or not has_policy or not has_event_ready:
        fail("project-profile queue-v2 must include non-policy, policy-candidate, and event-ready metadata routes")
    if not {"facts", "expectations", "contracts", "validation", "ownership", "source-links", "policies", "event-ready-metadata"}.issubset(seen_routes):
        fail("project-profile queue-v2 missing expected category route coverage: " + json.dumps(sorted(seen_routes), ensure_ascii=False))
    summary = queue.get("summary", {})
    if summary.get("total") != len(items) or summary.get("pending") != len(items):
        fail("project-profile queue-v2 summary totals must match pending items")
    if summary.get("pendingPolicyCandidates", 0) < 1 or summary.get("pendingEventReadyMetadata") != 1:
        fail("project-profile queue-v2 summary must expose pending policy/event-ready counts")
    _assert_no_project_map_forbidden_fields(queue, "projectProfileQueueV2")
    print("✓ project-profile V2 queue runtime ok")


def check_record_audit_cli() -> None:
    """Record audit must summarize host-owned records, markers, JSONL, Project Profile, and graph hygiene."""
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        host = base / "host"
        source = base / "source"
        for path in [
            host / ".lazy-harness" / "domain",
            host / ".lazy-harness" / "spec",
            host / ".lazy-harness" / "project",
            host / ".lazy-harness" / "knowledge",
            host / ".lazy-harness" / "logs",
            source / ".lazy-harness" / "domain",
            source / ".lazy-harness" / "spec",
            source / ".lazy-harness" / "project",
            source / ".lazy-harness" / "knowledge",
            source / ".lazy-harness" / "logs",
        ]:
            path.mkdir(parents=True)
        (source / ".lazy-harness" / "domain" / "base.md").write_text("base\n", encoding="utf-8")
        (source / ".lazy-harness" / "domain" / "framework-only.md").write_text("framework source only\n", encoding="utf-8")
        (host / ".lazy-harness" / "domain" / "base.md").write_text("base changed\n", encoding="utf-8")
        (host / ".lazy-harness" / "domain" / "host.md").write_text("host only TODO\n", encoding="utf-8")
        (host / ".lazy-harness" / "spec" / "complete.md").write_text(
            "# Complete Record\n\n"
            "## Index header\n\n"
            "- Record id: record_complete\n"
            "- Layer: SDD\n"
            "- Status: active\n"
            "- Scope: framework-global\n"
            "- Primary aliases:\n"
            "  - Complete record\n"
            "- Search keys:\n"
            "  - complete-record\n"
            "- Source files:\n"
            "  - `.lazy-harness/scripts/record-audit.ts`\n"
            "- Test files:\n"
            "  - `.lazy-harness/scripts/self-test.py`\n"
            "- Graph ids:\n"
            "  - `kg_complete_record`\n\n"
            "## Implementation map\n\n"
            "- `.lazy-harness/scripts/record-audit.ts` implements the fixture.\n"
            "- `.lazy-harness/scripts/self-test.py` protects the fixture.\n",
            encoding="utf-8",
        )
        (host / ".lazy-harness" / "spec" / "missing.md").write_text(
            "# Historical Missing Record\n\n"
            "Historical records without Index header metadata remain advisory only.\n",
            encoding="utf-8",
        )
        (host / ".lazy-harness" / "project" / "profile.xml").write_text(
            '<projectProfile><purpose status="needs-interview"/><owner status="confirmed">x</owner></projectProfile>\n',
            encoding="utf-8",
        )
        (host / ".lazy-harness" / "knowledge" / "graph.jsonl").write_text(
            '{"id":"a","path":".lazy-harness/domain/host.md"}\n'
            '{"id":"b","path":".lazy-harness/domain/missing.md"}\n'
            '{"id":"c","path":".lazy-harness/domain/a.md,.lazy-harness/domain/b.md"}\n'
            '{"id":"kg_complete_record","path":".lazy-harness/spec/complete.md"}\n'
            '{"id":"framework","path":".lazy-harness/domain/framework-only.md"}\n',
            encoding="utf-8",
        )
        (host / ".lazy-harness" / "logs" / "actions.jsonl").write_text('{"ok":true}\nnot-json\n', encoding="utf-8")
        completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "record-audit.ts"),
                "--root",
                str(host),
                "--source",
                str(source),
                "--format=json",
                "--recent=3",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            fail("record-audit failed:\n" + completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        if result.get("mode") != "record-audit.inspect":
            fail("record-audit mode changed")
        totals = result.get("totals", {})
        if totals.get("hostUnique") != 5 or totals.get("hostChanged") != 1 or totals.get("hostOwnedOrChanged") != 6:
            fail("record-audit should compare host-owned/changed records: " + json.dumps(totals, ensure_ascii=False))
        profile = result.get("projectProfile", {})
        if profile.get("artifactsComplete") is not False or profile.get("answersComplete") is not False or profile.get("needsInterviewFields") != 1 or profile.get("confirmedFields") != 1:
            fail("record-audit should split Project Profile artifact and answer completeness")
        graph = result.get("graph", {})
        if graph.get("rows") != 5 or graph.get("missingPaths") != 2 or graph.get("sourceOnlyPaths") != 1 or graph.get("commaJoinedPaths") != 1:
            fail("record-audit should report actionable graph hygiene and source-only paths")
        record_quality = result.get("recordQuality", {})
        counts = record_quality.get("counts", {})
        expected_counts = {
            "missing-index-header": 3,
            "missing-alias-or-search-key": 3,
            "missing-source-test-hints": 3,
            "missing-graph-link": 2,
        }
        if record_quality.get("advisoryOnly") is not True or record_quality.get("inspectedRecords") != 4 or record_quality.get("completeRecords") != 1:
            fail("record-audit should summarize advisory record quality counts: " + json.dumps(record_quality, ensure_ascii=False))
        if counts != expected_counts:
            fail("record-audit recordQuality counts changed: " + json.dumps(counts, ensure_ascii=False))
        issues = {issue.get("code"): issue for issue in record_quality.get("issues", [])}
        for code, count in expected_counts.items():
            if issues.get(code, {}).get("count") != count:
                fail("record-audit recordQuality issue missing count for " + code + ": " + json.dumps(record_quality, ensure_ascii=False))
        if ".lazy-harness/spec/missing.md" not in issues["missing-index-header"].get("samplePaths", []):
            fail("record-audit should sample historical missing record path")
        warnings = result.get("warnings", [])
        if not any("Record quality advisory missing-index-header" in warning for warning in warnings):
            fail("record-audit should keep recordQuality advisory warnings human-readable")
        if sum(item.get("invalid", 0) for item in result.get("jsonl", [])) != 1:
            fail("record-audit should count invalid JSONL lines")
        marker_map = {item.get("marker"): item.get("files") for item in result.get("markers", [])}
        if marker_map.get("TODO") != 1 or marker_map.get("needs-interview") != 1:
            fail("record-audit should count open markers")
        cli_completed = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "record-audit", "--root", str(host), "--source", str(source), "--format=json", "--recent=1"],
            cwd=host,
            text=True,
            capture_output=True,
            check=False,
        )
        if cli_completed.returncode != 0:
            fail("lazy record-audit dispatcher failed:\n" + cli_completed.stdout + cli_completed.stderr)
        cli_result = json.loads(cli_completed.stdout)
        if cli_result.get("mode") != "record-audit.inspect" or len(cli_result.get("recentFiles", [])) > 1:
            fail("lazy record-audit dispatcher should pass through args")
    print("✓ record-audit cli ok")


def check_graph_hygiene_cli() -> None:
    """Graph hygiene must report graph JSONL path/id issues without mutating the graph."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        (root / ".lazy-harness" / "domain").mkdir(parents=True)
        (root / ".lazy-harness" / "knowledge").mkdir(parents=True)
        source = root / "framework-source"
        (source / ".lazy-harness" / "domain").mkdir(parents=True)
        (root / ".lazy-harness" / "domain" / "existing.md").write_text("ok\n", encoding="utf-8")
        (source / ".lazy-harness" / "domain" / "framework-only.md").write_text("source only\n", encoding="utf-8")
        graph = root / ".lazy-harness" / "knowledge" / "graph.jsonl"
        graph.write_text(
            '{"id":"a","path":".lazy-harness/domain/existing.md"}\n'
            '{"id":"a","path":".lazy-harness/domain/missing.md"}\n'
            '{"path":".lazy-harness/domain/no-id.md"}\n'
            '{"id":"comma","path":".lazy-harness/domain/a.md,.lazy-harness/domain/b.md"}\n'
            '{"id":"evidence","evidence":[{"path":".lazy-harness/domain/evidence-missing.md"}],"links":[{"target":".lazy-harness/domain/link-missing.md"}]}\n'
            '{"id":"framework","path":".lazy-harness/domain/framework-only.md"}\n'
            'not-json\n',
            encoding="utf-8",
        )
        before = graph.read_text(encoding="utf-8")
        completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "graph-hygiene.ts"),
                "--root",
                str(root),
                "--source",
                str(source),
                "--format=json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            fail("graph-hygiene failed:\n" + completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        summary = result.get("summary", {})
        if result.get("mode") != "graph-hygiene.inspect" or result.get("ok") is not False:
            fail("graph-hygiene mode/ok changed")
        expected = {
            "rows": 7,
            "invalidRows": 1,
            "duplicateIds": 1,
            "missingIds": 1,
            "missingPaths": 5,
            "sourceOnlyPaths": 1,
            "commaJoinedPaths": 1,
        }
        for key, value in expected.items():
            if summary.get(key) != value:
                fail(f"graph-hygiene summary {key} expected {value}, got {summary.get(key)}: " + completed.stdout[:500])
        codes = {issue.get("code") for issue in result.get("issues", [])}
        for code in ["invalid-json", "duplicate-id", "missing-id", "comma-joined-path", "missing-path"]:
            if code not in codes:
                fail("graph-hygiene missing issue code: " + code)
        if graph.read_text(encoding="utf-8") != before:
            fail("graph-hygiene must be read-only")
        fail_completed = subprocess.run(
            [
                "bun",
                str(LAZY / "scripts" / "graph-hygiene.ts"),
                "--root",
                str(root),
                "--source",
                str(source),
                "--format=json",
                "--fail-on-issues",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if fail_completed.returncode != 2:
            fail("graph-hygiene --fail-on-issues should exit 2 when issues exist")
        cli_completed = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "graph-hygiene", "--root", str(root), "--source", str(source), "--format=json"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if cli_completed.returncode != 0:
            fail("lazy graph-hygiene dispatcher failed:\n" + cli_completed.stdout + cli_completed.stderr)
        if json.loads(cli_completed.stdout).get("summary", {}).get("rows") != 7:
            fail("lazy graph-hygiene dispatcher should pass args through")
    print("✓ graph-hygiene cli ok")


def check_real_feature_walkthrough() -> None:
    queue = LAZY / "questions" / f"__tmp_5d6_walkthrough_{os.getpid()}.xml"
    decisions = LAZY / "logs" / f"__tmp_5d6_walkthrough_{os.getpid()}.jsonl"
    for path in [queue, decisions]:
        path.unlink(missing_ok=True)
    try:
        collect = run_interview_collect(queue, ".lazy-harness/triggers/fixtures/walkthrough/referral-priority-feature.json")
        if collect.get("created") != 2 or collect.get("totalOpen") != 2:
            fail("5d-6 walkthrough collect changed: " + json.dumps(collect, ensure_ascii=False))
        first_question = collect["questions"][0]
        if first_question.get("id") != "Q-a13961244b7dcc40":
            fail("5d-6 walkthrough first question id changed: " + json.dumps(first_question, ensure_ascii=False))
        answer = run_interview_answer(queue, decisions, first_question["id"], "A", apply=True)
        if answer.get("applied") is not True or answer.get("effects", [{}])[0].get("kind") != "ddd-register-term":
            fail("5d-6 walkthrough answer did not persist DDD effect: " + json.dumps(answer, ensure_ascii=False))
        first_aftershock = run_aftershock_reanalysis(queue, str(decisions.relative_to(ROOT)))
        if first_aftershock.get("created") != 1 or first_aftershock["questions"][0].get("depth") != 1 or first_aftershock["questions"][0].get("layer") != "sdd":
            fail("5d-6 walkthrough first aftershock changed: " + json.dumps(first_aftershock, ensure_ascii=False))
        aftershock_question = first_aftershock["questions"][0]
        second_answer = run_interview_answer(queue, decisions, aftershock_question["id"], "A", apply=True)
        if second_answer.get("applied") is not True or second_answer.get("effects", [{}])[0].get("kind") != "sdd-register-contract":
            fail("5d-6 walkthrough aftershock answer did not carry SDD effect: " + json.dumps(second_answer, ensure_ascii=False))
        second_aftershock = run_aftershock_reanalysis(queue, str(decisions.relative_to(ROOT)))
        depth_two = [question for question in second_aftershock.get("questions", []) if question.get("depth") == 2]
        if not depth_two or depth_two[0].get("layer") != "bdd":
            fail("5d-6 walkthrough did not reach depth 2: " + json.dumps(second_aftershock, ensure_ascii=False))
        # Use a separate queue for the assertion-only cross-verify run so the
        # hook below can still detect a fresh fingerprint. After the regression
        # fix (tests/tdd-cross-verify-forcegate-loop.md) forceGate fires only on
        # NEW unanswered questions, so re-running cross-verify on the main queue
        # would silently consume the fingerprint and break the hook surface
        # below.
        tdd_probe_queue = LAZY / f"questions/__tmp_5d6_walkthrough_probe_{os.getpid()}.xml"
        tdd_probe_queue.unlink(missing_ok=True)
        try:
            tdd = run_tdd_cross_verify([".lazy-harness/triggers/walkthrough-fixtures/referral-priority-feature.ts"], queue=tdd_probe_queue, expect_code=2)
            if tdd.get("forceGate") is not True or tdd.get("failed") != 1:
                fail("5d-6 walkthrough TDD force gate changed: " + json.dumps(tdd, ensure_ascii=False))
        finally:
            tdd_probe_queue.unlink(missing_ok=True)
        hook_payload = {
            "recent_tool_calls": [
                {"name": "Edit", "args_preview": ".lazy-harness/triggers/walkthrough-fixtures/referral-priority-feature.ts"},
            ],
        }
        hook_out = run_response_completed_hook(hook_payload, queue)
        if "5d-3 TDD Cross-Verify Gate" not in hook_out:
            fail("5d-6 walkthrough hook did not surface TDD gate:\n" + hook_out)
    finally:
        for path in [queue, decisions]:
            path.unlink(missing_ok=True)
    print("✓ 5d-6 real feature walkthrough ok")

def check_lint_output() -> None:
    expected = {
        "typecheck-env": {
            "tsc:environment:missing-type-definition": 1,
            "tsc:environment:missing-config": 1,
            "tsc:environment:missing-module": 1,
        },
        "typecheck-code": {
            "tsc:code-drift:type-mismatch": 1,
            "tsc:code-drift:property-missing": 1,
        },
        "eslint-code": {
            "eslint:code-drift:eslint-rule": 1,
        },
    }
    for fixture, summary in expected.items():
        result = run_lint_output_fixture(fixture)
        if not result.get("ok"):
            fail(f"lint-output fixture {fixture} ok=false")
        if result.get("warnings"):
            fail(f"lint-output fixture {fixture} warnings must be empty: " + json.dumps(result.get("warnings"), ensure_ascii=False))
        if result.get("summary") != summary:
            fail(f"lint-output fixture {fixture} summary changed: expected {summary}, got {result.get('summary')}")
    print("✓ lint-output fixtures ok")


def check_e2e_demo() -> None:
    result = run_trigger_scope(".lazy-harness/triggers/fixtures/e2e")
    candidates = result.get("candidates", [])
    by_layer: dict[str, int] = {}
    for candidate in candidates:
        by_layer[candidate.get("layer", "unknown")] = by_layer.get(candidate.get("layer", "unknown"), 0) + 1
    expected_counts = {"ddd": 1, "sdd": 1, "bdd": 1, "ssot": 2}
    if by_layer != expected_counts:
        fail(f"5c-8 E2E layer counts changed: expected {expected_counts}, got {by_layer}")
    expected_names = {
        ("ddd", "ReferralIntakeRecord"),
        ("sdd", "referralIntakeSchema"),
        ("bdd", "ReferralIntakePatientSearch"),
        ("ssot", "calculateReferralChecksum"),
        ("ssot", "normalizeReferralStatus"),
    }
    actual_names = {(candidate.get("layer"), candidate.get("name")) for candidate in candidates}
    if actual_names != expected_names:
        fail(f"5c-8 E2E candidates changed: expected {sorted(expected_names)}, got {sorted(actual_names)}")
    expected_summary = {"sdd->ddd:gap": 1, "bdd->ddd:gap": 1, "bdd->sdd:gap": 1}
    if (result.get("crossLayer") or {}).get("summary") != expected_summary:
        fail(f"5c-8 E2E cross-layer summary changed: expected {expected_summary}, got {(result.get('crossLayer') or {}).get('summary')}")
    structured_ask = result.get("structuredAskValidation") or {}
    if not structured_ask.get("ok") or structured_ask.get("checkedCandidates") != 6:
        fail(f"5c-8 E2E structured ask validation changed: {structured_ask}")
    lint_result = run_lint_output_fixture("typecheck-env")
    if not all(key.startswith("tsc:environment:") for key in lint_result.get("summary", {})):
        fail(f"5c-8 E2E lint drift env classification changed: {lint_result.get('summary')}")
    print("✓ 5c-8 E2E demo ok")


def check_triggers() -> None:
    result = run_trigger("all")
    if not result.get("ok"):
        fail("trigger result ok=false")
    if result.get("warnings"):
        fail("trigger warnings must be empty: " + json.dumps(result.get("warnings"), ensure_ascii=False))
    candidates = result.get("candidates", [])
    by_layer: dict[str, int] = {}
    for candidate in candidates:
        by_layer[candidate.get("layer", "unknown")] = by_layer.get(candidate.get("layer", "unknown"), 0) + 1
    expected_counts = {"ddd": 6, "sdd": 3, "bdd": 3, "ssot": 7}
    if by_layer != expected_counts:
        fail(f"trigger fixture counts changed: expected {expected_counts}, got {by_layer}")

    expected_all = {
        ("ddd", "EMR"),
        ("ddd", "Emr"),
        ("ddd", "PatientDto"),
        ("ddd", "PatientRiskProfile"),
        ("sdd", "orderItemSchema"),
        ("sdd", "referralIntakeSchema"),
        ("sdd", "WindowControls"),
        ("bdd", "PatientSearchAutocomplete"),
        ("bdd", "CrossLayerPatientAutocomplete"),
        ("bdd", "ReferralIntakePatientSearch"),
        ("ssot", "mapPatientToDto"),
        ("ssot", "calculateChecksum"),
        ("ssot", "calculateInvoiceChecksum"),
        ("ssot", "validatePatientRiskProfile"),
        ("ssot", "normalizeAppointmentStatus"),
        ("ssot", "calculateReferralChecksum"),
        ("ssot", "normalizeReferralStatus"),
    }
    actual_all = {(candidate.get("layer"), candidate.get("name")) for candidate in candidates}
    missing_expected = sorted(expected_all - actual_all)
    if missing_expected:
        fail("missing expected fixture candidates: " + json.dumps(missing_expected, ensure_ascii=False))

    ssot = run_trigger("ssot")
    if ssot.get("warnings"):
        fail("SSOT trigger warnings must be empty: " + json.dumps(ssot.get("warnings"), ensure_ascii=False))
    ssot_candidates = ssot.get("candidates", [])
    ssot_names = {candidate.get("name") for candidate in ssot_candidates}
    if "formatPatientName" in ssot_names:
        fail("registered SSOT utility formatPatientName should be suppressed")
    for expected in ["mapPatientToDto", "calculateChecksum", "calculateInvoiceChecksum", "validatePatientRiskProfile", "normalizeAppointmentStatus", "calculateReferralChecksum", "normalizeReferralStatus"]:
        if expected not in ssot_names:
            fail(f"missing SSOT fixture candidate: {expected}")
    ssot_confidence = {candidate.get("name"): candidate.get("confidence") for candidate in ssot_candidates}
    expected_confidence = {
        "mapPatientToDto": "high",
        "validatePatientRiskProfile": "high",
        "normalizeAppointmentStatus": "high",
        "calculateReferralChecksum": "high",
        "normalizeReferralStatus": "high",
        "calculateChecksum": "medium",
        "calculateInvoiceChecksum": "medium",
    }
    if ssot_confidence != expected_confidence:
        fail(f"SSOT confidence changed: expected {expected_confidence}, got {ssot_confidence}")
    check_cross_layer(result)
    print(f"✓ trigger fixtures ok {by_layer}")


def check_cross_layer(result: dict) -> None:
    cross_layer = result.get("crossLayer") or {}
    if cross_layer.get("criterionId") != "5c-5":
        fail(f"missing 5c-5 crossLayer map: {cross_layer}")
    expected_summary = {
        "sdd->ddd:gap": 6,
        "bdd->ddd:gap": 3,
        "bdd->sdd:gap": 3,
        "ssot->ddd:gap": 2,
    }
    if cross_layer.get("summary") != expected_summary:
        fail(f"cross-layer summary changed: expected {expected_summary}, got {cross_layer.get('summary')}")
    expected_gaps = {
        ("sdd", "ddd", "OrderItem", "orderItemSchema"),
        ("sdd", "ddd", "ReferralIntake", "referralIntakeSchema"),
        ("sdd", "ddd", "Close", "WindowControls"),
        ("sdd", "ddd", "InitialScrollSettleMs", "WindowControls"),
        ("sdd", "ddd", "ScrollBehavior", "WindowControls"),
        ("sdd", "ddd", "WindowControls", "WindowControls"),
        ("bdd", "ddd", "자동완성", "PatientSearchAutocomplete"),
        ("bdd", "sdd", "autocomplete", "PatientSearchAutocomplete"),
        ("bdd", "ddd", "자동완성", "CrossLayerPatientAutocomplete"),
        ("bdd", "sdd", "autocomplete", "CrossLayerPatientAutocomplete"),
        ("bdd", "ddd", "자동완성", "ReferralIntakePatientSearch"),
        ("bdd", "sdd", "autocomplete", "ReferralIntakePatientSearch"),
        ("ssot", "ddd", "Checksum", "calculateChecksum"),
        ("ssot", "ddd", "Invoice", "calculateInvoiceChecksum"),
    }
    actual_gaps = {
        (gap.get("fromLayer"), gap.get("targetLayer"), gap.get("term"), gap.get("candidateName"))
        for gap in cross_layer.get("gaps", [])
    }
    if actual_gaps != expected_gaps:
        fail(f"cross-layer gaps changed: expected {sorted(expected_gaps)}, got {sorted(actual_gaps)}")

    structured_ask = result.get("structuredAskValidation") or {}
    if structured_ask.get("criterionId") != "5c-7":
        fail(f"missing 5c-7 structured ask validation report: {structured_ask}")
    if not structured_ask.get("ok"):
        fail("structured ask validation failed: " + json.dumps(structured_ask.get("issues"), ensure_ascii=False))
    expected_checked = len(result.get("candidates", [])) + 1  # + cross-layer integrated ask
    if structured_ask.get("checkedCandidates") != expected_checked:
        fail(f"structured ask checked count changed: expected {expected_checked}, got {structured_ask.get('checkedCandidates')}")
    if structured_ask.get("issues") != []:
        fail("structured ask validation issues must be empty: " + json.dumps(structured_ask.get("issues"), ensure_ascii=False))


def check_layer_impact_gate() -> None:
    """N1 — Layer Impact Completion Gate fixtures.

    Run each fixture under .lazy-harness/triggers/fixtures/layer-impact/*.json
    through scripts/layer-impact-gate.ts and assert the projection
    (status / humanRequired / missingLayers / layerImpactSummary) matches.
    """
    fixtures_dir = LAZY / "triggers" / "fixtures" / "layer-impact"
    if not fixtures_dir.exists():
        fail("N1 fixture dir missing: .lazy-harness/triggers/fixtures/layer-impact")
    fixtures = sorted(fixtures_dir.glob("*.json"))
    if len(fixtures) < 3:
        fail(f"N1 fixtures must have >=3 cases, got {len(fixtures)}")
    for fx_path in fixtures:
        fx = json.loads(fx_path.read_text(encoding="utf-8"))
        cli_args = [
            "bun",
            str(LAZY / "scripts" / "layer-impact-gate.ts"),
        ]
        for ff in fx["input"]["files"]:
            flag = "--added" if ff["changeKind"] == "added" else (
                "--deleted" if ff["changeKind"] == "deleted" else "--file"
            )
            cli_args.extend([flag, ff["path"]])
        completed = subprocess.run(
            cli_args,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode not in (0, 1):
            fail(
                f"N1 gate exit unexpected for {fx_path.name}: "
                f"code={completed.returncode} stderr={completed.stderr.strip()}"
            )
        try:
            got = json.loads(completed.stdout)
        except Exception as exc:  # noqa: BLE001
            fail(f"N1 gate output not valid JSON for {fx_path.name}: {exc}")
        expected = fx["expect"]
        if got.get("status") != expected["status"]:
            fail(
                f"N1 {fx_path.name}: status got={got.get('status')} expected={expected['status']}"
            )
        if got.get("humanRequired") != expected["humanRequired"]:
            fail(
                f"N1 {fx_path.name}: humanRequired got={got.get('humanRequired')} "
                f"expected={expected['humanRequired']}"
            )
        if got.get("missingLayers") != expected["missingLayers"]:
            fail(
                f"N1 {fx_path.name}: missingLayers got={got.get('missingLayers')} "
                f"expected={expected['missingLayers']}"
            )
        for layer, exp_entry in expected["layerImpactSummary"].items():
            got_entry = got.get("layerImpact", {}).get(layer, {})
            for k, v in exp_entry.items():
                if got_entry.get(k) != v:
                    fail(
                        f"N1 {fx_path.name}: layerImpact.{layer}.{k} "
                        f"got={got_entry.get(k)} expected={v}"
                    )
        if got.get("resolverVersion") != expected.get("resolverVersion"):
            # Allow fixtures to still declare `null` from the heuristic-only era;
            # accept that as "any non-empty string" once N2 wire-in is active.
            expected_rv = expected.get("resolverVersion")
            got_rv = got.get("resolverVersion")
            if expected_rv is None and isinstance(got_rv, str) and len(got_rv) > 0:
                pass  # acceptable: N2 wire-in populates a fingerprint
            else:
                fail(
                    f"N1 {fx_path.name}: resolverVersion got={got_rv} "
                    f"expected={expected_rv}"
                )
    print(f"✓ N1 layer-impact-gate ok ({len(fixtures)} fixtures)")


def check_reference_resolver() -> None:
    """N2 — Map-aware Reference Resolver fixtures.

    Run each fixture under .lazy-harness/triggers/fixtures/reference-resolver/*.json
    through scripts/reference-resolver.ts and assert the produced matches[]
    against expected count / linkKinds / top-score bounds. Fixtures may declare
    `input.sideEffect.createFiles` to materialize ephemeral files (needed for
    the sibling-test-stem case, since that strategy probes the real filesystem).
    Side-effect files are cleaned up afterwards regardless of outcome.
    """
    fixtures_dir = LAZY / "triggers" / "fixtures" / "reference-resolver"
    if not fixtures_dir.exists():
        fail("N2 fixture dir missing: .lazy-harness/triggers/fixtures/reference-resolver")
    fixtures = sorted(fixtures_dir.glob("*.json"))
    if len(fixtures) < 3:
        fail(f"N2 fixtures must have >=3 cases, got {len(fixtures)}")
    for fx_path in fixtures:
        fx = json.loads(fx_path.read_text(encoding="utf-8"))
        created = []
        try:
            for rel in (fx.get("input", {}).get("sideEffect", {}).get("createFiles") or []):
                target = ROOT / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"// fixture file for {fx_path.name}\n", encoding="utf-8")
                created.append(target)
            cli_args = ["bun", str(LAZY / "scripts" / "reference-resolver.ts")]
            for f in fx["input"]["files"]:
                cli_args.extend(["--file", f])
            completed = subprocess.run(
                cli_args,
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                fail(
                    f"N2 resolver exit non-zero for {fx_path.name}: "
                    f"code={completed.returncode} stderr={completed.stderr.strip()}"
                )
            try:
                got = json.loads(completed.stdout)
            except Exception as exc:  # noqa: BLE001
                fail(f"N2 resolver output not valid JSON for {fx_path.name}: {exc}")
            matches = got.get("matches", [])
            exp = fx["expect"]
            if "minMatchCount" in exp and len(matches) < exp["minMatchCount"]:
                fail(
                    f"N2 {fx_path.name}: match count {len(matches)} < min {exp['minMatchCount']}"
                )
            if "maxMatchCount" in exp and len(matches) > exp["maxMatchCount"]:
                fail(
                    f"N2 {fx_path.name}: match count {len(matches)} > max {exp['maxMatchCount']}"
                )
            if "expectedLinkKinds" in exp:
                got_kinds = {m["linkKind"] for m in matches}
                missing_kinds = [k for k in exp["expectedLinkKinds"] if k not in got_kinds]
                if missing_kinds:
                    fail(
                        f"N2 {fx_path.name}: expected linkKinds missing={missing_kinds} "
                        f"got_kinds={sorted(got_kinds)}"
                    )
            if matches:
                top_score = matches[0]["score"]
                if "topScoreAtLeast" in exp and top_score < exp["topScoreAtLeast"]:
                    fail(
                        f"N2 {fx_path.name}: top score {top_score} < min {exp['topScoreAtLeast']}"
                    )
                if "topScoreAtMost" in exp and top_score > exp["topScoreAtMost"]:
                    fail(
                        f"N2 {fx_path.name}: top score {top_score} > max {exp['topScoreAtMost']}"
                    )
                if "topMatch" in exp:
                    tm = exp["topMatch"]
                    for k, v in tm.items():
                        if matches[0].get(k) != v:
                            fail(
                                f"N2 {fx_path.name}: topMatch.{k} got={matches[0].get(k)} "
                                f"expected={v}"
                            )
        finally:
            for t in created:
                try:
                    t.unlink()
                except FileNotFoundError:
                    pass
    print(f"✓ N2 reference-resolver ok ({len(fixtures)} fixtures)")


def check_search_provider_canonical_record_dirs() -> None:
    """SearchProvider fallback must scan current canonical record paths."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-search-provider-"))
    try:
        (temp / ".lazy-harness" / "domain").mkdir(parents=True)
        (temp / ".lazy-harness" / "ddd").mkdir(parents=True)
        (temp / ".lazy-harness" / "planning").mkdir(parents=True)
        (temp / ".lazy-harness" / "domain" / "policy.md").write_text(
            "# Canonical Domain\n\nUnicornPolicy lives in the canonical domain path.\n",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "ddd" / "legacy.md").write_text(
            "# Legacy DDD\n\nLegacyOnlyToken should not be discovered through the ddd layer.\n",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "planning" / "plan.md").write_text(
            "# Planning\n\nRoadmapToken should be discoverable through the planning layer.\n",
            encoding="utf-8",
        )
        provider = (LAZY / "scripts" / "search-provider.ts").as_posix()
        code = f"""
import {{ DirectAISearch }} from {json.dumps(provider)};
const search = new DirectAISearch();
const canonical = await search.search({{ terms: ['UnicornPolicy'], layers: ['ddd'] }});
const legacy = await search.search({{ terms: ['LegacyOnlyToken'], layers: ['ddd'] }});
const planning = await search.search({{ terms: ['RoadmapToken'], layers: ['planning'] }});
console.log(JSON.stringify({{ canonical, legacy, planning }}));
"""
        completed = subprocess.run(["bun", "-e", code], cwd=temp, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            fail("SearchProvider canonical dir check failed to run:\n" + completed.stdout + completed.stderr)
        try:
            got = json.loads(completed.stdout)
        except Exception as exc:  # noqa: BLE001
            fail(f"SearchProvider canonical dir output invalid JSON: {exc}\n{completed.stdout}")
        if not got.get("canonical") or ".lazy-harness/domain/policy.md" not in got["canonical"][0].get("recordPath", ""):
            fail("SearchProvider did not find canonical domain path: " + json.dumps(got, ensure_ascii=False))
        if got.get("legacy"):
            fail("SearchProvider should not scan legacy .lazy-harness/ddd path: " + json.dumps(got, ensure_ascii=False))
        if not got.get("planning") or ".lazy-harness/planning/plan.md" not in got["planning"][0].get("recordPath", ""):
            fail("SearchProvider did not find planning path: " + json.dumps(got, ensure_ascii=False))
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ SearchProvider canonical record dirs ok")


def write_digest_fixture(root: pathlib.Path) -> pathlib.Path:
    record = root / ".lazy-harness" / "ssot" / "pr-description-format.md"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(
        "# PR Description Format\n\n"
        "Status: accepted\n"
        "\n"
        "## Rule digest\n\n"
        "- Status: active\n"
        "- Layer: SSOT\n"
        "- Scope: host-project\n"
        "- Applies when:\n"
        "  - user asks to draft or update a PR description\n"
        "  - pull request body or release note summary is being prepared\n"
        "- Must:\n"
        "  - include Why, What, and Task sections in PR descriptions\n"
        "  - use this artifact rule regardless of which tool creates the PR\n"
        "- Must not:\n"
        "  - encode PR policy as a gh or bash specific rule\n"
        "- Record completion:\n"
        "  - confirmed PR description changes update this SSOT\n",
        encoding="utf-8",
    )
    return record





def check_record_index_generator_phase3() -> None:
    """Phase 3 record-index generator should produce deterministic derived cache output."""
    schema_path = LAZY / "schemas" / "record-index.schema.json"
    script_path = LAZY / "scripts" / "record-index.ts"
    map_script_path = LAZY / "scripts" / "record-map.ts"
    if not schema_path.exists():
        fail("Record index schema missing: " + str(schema_path))
    if not script_path.exists():
        fail("Record index generator missing: " + str(script_path))
    if not map_script_path.exists():
        fail("Record map CLI missing: " + str(map_script_path))
    old_schema = LAZY / "schemas" / ("context" + "-index.schema.json")
    old_script = LAZY / "scripts" / ("context" + "-index.ts")
    if old_schema.exists() or old_script.exists():
        fail("Option A requires old context-index files to be absent")
    help_text = subprocess.check_output([str(LAZY / "bin" / "lazy"), "help"], cwd=ROOT, text=True)
    if "context" + "-index" in help_text:
        fail("lazy help must not advertise old context-index command after Option A")
    if "map --overview" not in help_text:
        fail("lazy help must advertise map overview command")
    if "map <term-or-file>" not in help_text:
        fail("lazy help must advertise map drill-down command")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("title") != "RecordIndex":
        fail("Record index schema title mismatch")
    record_props = schema.get("definitions", {}).get("recordEntry", {}).get("properties", {})
    for prop in ["recordPath", "digest", "aliases", "surfaceTerms", "implementationHints", "graphIds", "projectProfileFeatureIds"]:
        if prop not in record_props:
            fail("Record index schema missing record property: " + prop)

    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-record-index-"))
    try:
        (temp / ".lazy-harness" / "behavior").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "project").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "knowledge").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "generated").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "behavior" / "feature-surface.md").write_text(
            "# Feature Surface\n\n"
            "Related SDD: `.lazy-harness/spec/feature-surface.md`\n\n"
            "## Rule digest\n\n"
            "- Status: active\n"
            "- Layer: BDD\n"
            "- Scope: host-project\n"
            "- Applies when:\n"
            "  - user asks about feature surface UI\n"
            "- Must:\n"
            "  - confirm feature panel behavior before editing\n"
            "- Aliases:\n"
            "  - 기능패널\n"
            "  - feature panel\n"
            "- Surface terms:\n"
            "  - 기능화면\n"
            "- Implementation hints:\n"
            "  - Routes: `/example-feature`\n"
            "  - Components: `FeaturePanel`\n"
            "  - Files: `src/features/example-feature/FeaturePanel.tsx`\n"
            "  - Tests: `tests/example-feature/feature-panel.test.tsx`\n"
            "- Related records:\n"
            "  - `.lazy-harness/spec/feature-surface.md`\n\n"
            "## Implementation map\n\n"
            "- Component: `FeatureSurfacePage`\n"
            "- Source: `src/features/example-feature/FeatureSurfacePage.tsx`\n",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "project" / "feature-navigation.xml").write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<featureNavigation version="1.0">
  <feature id="example-feature" status="confirmed">
    <label>Feature Surface</label>
    <aliases>
      <alias lang="ko">기능패널</alias>
      <alias lang="ko">기능화면</alias>
      <alias lang="en">feature panel</alias>
    </aliases>
    <routes><route>/example-feature</route></routes>
    <components><component>FeaturePanel</component></components>
    <records>
      <record layer="BDD">.lazy-harness/behavior/feature-surface.md</record>
    </records>
    <sourceFiles><path>src/features/example-feature/FeaturePanel.tsx</path></sourceFiles>
    <tests><path>tests/example-feature/feature-panel.test.tsx</path></tests>
    <risk>Fixture risk note.</risk>
  </feature>
</featureNavigation>
""",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "knowledge" / "graph.jsonl").write_text(
            json.dumps({
                "id": "kg_feature_surface_behavior_impl",
                "source": ".lazy-harness/behavior/feature-surface.md",
                "relation": "implemented_by",
                "target": "src/features/example-feature/FeaturePanel.tsx",
            }, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        def run_index(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["bun", str(script_path), "--root", str(temp), *args],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        first = run_index("--format", "json")
        second = run_index("--format=json")
        if first.returncode != 0:
            fail("record-index generator failed:\n" + first.stdout + first.stderr)
        if first.stdout != second.stdout:
            fail("record-index generator output is not deterministic")
        index = json.loads(first.stdout)
        if index.get("schemaVersion") != "1.0" or index.get("source", {}).get("method") != "record-index-v1":
            fail("record-index output missing schema/method")
        records = index.get("records", [])
        if len(records) != 1:
            fail("record-index fixture should produce exactly one record")
        record = records[0]
        for expected in ["기능패널", "기능화면", "feature panel"]:
            if expected not in record.get("aliases", []) and expected not in record.get("surfaceTerms", []):
                fail("record-index record missing retrieval term: " + expected)
        hints = record.get("implementationHints", {})
        if "FeaturePanel" not in hints.get("componentHints", []):
            fail("record-index missing component hint")
        if "src/features/example-feature/FeaturePanel.tsx" not in hints.get("fileHints", []):
            fail("record-index missing file hint")
        if "tests/example-feature/feature-panel.test.tsx" not in hints.get("testHints", []):
            fail("record-index missing test hint")
        if "kg_feature_surface_behavior_impl" not in record.get("graphIds", []):
            fail("record-index missing graph edge id")
        if ".lazy-harness/spec/feature-surface.md" not in record.get("digest", {}).get("relatedRecords", []):
            fail("record-index missing top-level Related record path")
        if "example-feature" not in record.get("projectProfileFeatureIds", []):
            fail("record-index missing project profile feature id")
        if index.get("projectProfile", {}).get("featureNavigationPath") != ".lazy-harness/project/feature-navigation.xml":
            fail("record-index missing feature navigation path")

        map_cmd = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "map", "feature panel", "--format=json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "LAZY_HOST_ROOT": str(temp)},
        )
        if map_cmd.returncode != 0:
            fail("lazy map command failed:\n" + map_cmd.stdout + map_cmd.stderr)
        record_map = json.loads(map_cmd.stdout)
        if record_map.get("mode") != "record-map.inspect":
            fail("lazy map output missing inspect mode")
        if record_map.get("source", {}).get("method") != "record-map-v1":
            fail("lazy map output missing method")
        initial_cache = record_map.get("source", {}).get("recordIndexCache", {})
        if initial_cache.get("used") is not False or "missing" not in str(initial_cache.get("reason", "")):
            fail("lazy map should rebuild when generated record-index cache is missing in fixture")
        if not record_map.get("features") or record_map["features"][0].get("id") != "example-feature":
            fail("lazy map should match feature navigation aliases")
        drilldown = record_map.get("drilldown", {})
        if ".lazy-harness/behavior/feature-surface.md" not in drilldown.get("recordPaths", []):
            fail("lazy map drilldown missing record path")
        if "src/features/example-feature/FeaturePanel.tsx" not in drilldown.get("sourceFiles", []):
            fail("lazy map drilldown missing source file")
        if "tests/example-feature/feature-panel.test.tsx" not in drilldown.get("testFiles", []):
            fail("lazy map drilldown missing test file")
        if "kg_feature_surface_behavior_impl" not in drilldown.get("graphIds", []):
            fail("lazy map drilldown missing graph id")
        notes_text = "\n".join(str(note) for note in record_map.get("notes", []))
        if "Cues only" not in notes_text or "read real record" not in notes_text:
            fail("lazy map notes must state cue-only/read-real-evidence behavior")
        forbidden_map_fields = {"requiredRead", "optionalRead", "confidence", "intent", "risk", "gate", "nextAction", "candidateMeanings"}

        def assert_no_forbidden_map_fields(value: object, where: str = "$") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in forbidden_map_fields:
                        fail("lazy map must not emit semantic-authority field: " + where + "." + key)
                    assert_no_forbidden_map_fields(child, where + "." + str(key))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    assert_no_forbidden_map_fields(child, where + f"[{index}]")

        assert_no_forbidden_map_fields(record_map)

        aggregate_map_cmd = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "map", "기능화면 FeaturePanel tests", "--format=json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "LAZY_HOST_ROOT": str(temp)},
        )
        if aggregate_map_cmd.returncode != 0:
            fail("lazy map aggregate fallback command failed:\n" + aggregate_map_cmd.stdout + aggregate_map_cmd.stderr)
        aggregate_map = json.loads(aggregate_map_cmd.stdout)
        aggregate_records = aggregate_map.get("records", [])
        if not aggregate_records or aggregate_records[0].get("recordPath") != ".lazy-harness/behavior/feature-surface.md":
            fail("lazy map aggregate token fallback should return the feature-surface record")
        aggregate_matched = aggregate_records[0].get("matched", [])
        if not any(item.get("field") == "record.aggregateTokenFallback" for item in aggregate_matched):
            fail("lazy map aggregate token fallback should expose cue-only aggregate matched fields")
        aggregate_drilldown = aggregate_map.get("drilldown", {})
        if "tests/example-feature/feature-panel.test.tsx" not in aggregate_drilldown.get("testFiles", []):
            fail("lazy map aggregate fallback drilldown missing test file")
        assert_no_forbidden_map_fields(aggregate_map)

        overview_cmd = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "map", "--overview", "--format=json", "--limit=3"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "LAZY_HOST_ROOT": str(temp)},
        )
        if overview_cmd.returncode != 0:
            fail("lazy map --overview command failed:\n" + overview_cmd.stdout + overview_cmd.stderr)
        overview = json.loads(overview_cmd.stdout)
        if overview.get("mode") != "record-map.overview":
            fail("lazy map --overview output missing overview mode")
        overview_notes = "\n".join(str(note) for note in overview.get("notes", []))
        if "Overview first" not in overview_notes or "before choosing search terms" not in overview_notes:
            fail("lazy map overview notes must require overview-first search term selection")
        if "multiple candidate tokens/files/layers" not in overview_notes or "dispersed records/source/tests" not in overview_notes:
            fail("lazy map overview notes must require repeated query-map coverage across dispersed evidence")
        inventory = overview.get("inventory", {})
        if not inventory.get("totalRecords") or not inventory.get("layers"):
            fail("lazy map overview must include whole record/layer inventory")
        if not overview.get("features") or overview["features"][0].get("id") != "example-feature":
            fail("lazy map overview should include feature navigation structure")
        if "kg_feature_surface_behavior_impl" not in overview.get("drilldown", {}).get("graphIds", []):
            fail("lazy map overview drilldown missing graph id")
        assert_no_forbidden_map_fields(overview)

        written = run_index("--write", "--output", str(temp / ".lazy-harness" / "generated" / "record-index.json"), "--format=md")
        if written.returncode != 0 or "Record index" not in written.stdout:
            fail("record-index --write markdown output failed:\n" + written.stdout + written.stderr)
        if not (temp / ".lazy-harness" / "generated" / "record-index.json").exists():
            fail("record-index --write did not create generated cache")
        cached_map_cmd = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "map", "feature panel", "--format=json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "LAZY_HOST_ROOT": str(temp)},
        )
        if cached_map_cmd.returncode != 0:
            fail("lazy map cached command failed:\n" + cached_map_cmd.stdout + cached_map_cmd.stderr)
        cached_map = json.loads(cached_map_cmd.stdout)
        cached_info = cached_map.get("source", {}).get("recordIndexCache", {})
        if cached_info.get("used") is not True or cached_info.get("reason") != "fresh generated cache":
            fail("lazy map should use fresh generated record-index cache after record-index --write")
        fresh_map_cmd = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "map", "feature panel", "--format=json", "--fresh"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "LAZY_HOST_ROOT": str(temp)},
        )
        if fresh_map_cmd.returncode != 0:
            fail("lazy map --fresh command failed:\n" + fresh_map_cmd.stdout + fresh_map_cmd.stderr)
        fresh_map = json.loads(fresh_map_cmd.stdout)
        fresh_info = fresh_map.get("source", {}).get("recordIndexCache", {})
        if fresh_info.get("used") is not False or "--fresh" not in str(fresh_info.get("reason", "")):
            fail("lazy map --fresh should bypass generated record-index cache")
        old_cmd = subprocess.run(
            [str(LAZY / "bin" / "lazy"), "context" + "-index", "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if old_cmd.returncode == 0:
            fail("old context-index command must be absent after Option A migration")
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ record-index generator Phase 3 ok")


def check_retrieval_coverage_audit_cli() -> None:
    """Retrieval audit should expose structural coverage gaps without semantic authority."""
    script_path = LAZY / "scripts" / "retrieval-coverage-audit.ts"
    sdd_path = LAZY / "spec" / "platform" / "retrieval-coverage-audit.md"
    tdd_path = LAZY / "tests" / "retrieval-coverage-audit.md"
    for path in [script_path, sdd_path, tdd_path]:
        if not path.exists():
            fail("Retrieval coverage audit artifact missing: " + str(path))

    help_text = subprocess.check_output([str(LAZY / "bin" / "lazy"), "help"], cwd=ROOT, text=True)
    if "retrieval-audit <term-or-file>" not in help_text:
        fail("lazy help must advertise retrieval-audit command")

    sdd_text = sdd_path.read_text(encoding="utf-8")
    for phrase in [
        "mode: retrieval-coverage-audit",
        "coverage.state",
        "mapped | partial | gap",
        "no-map-matches",
        "LLM/searcher remains the semantic search engine",
        "Forbidden fields",
        "`.lazy-harness/scripts/retrieval-coverage-audit.ts`",
        "Implementation map",
    ]:
        if phrase not in sdd_text:
            fail("Retrieval coverage audit SDD missing phrase: " + phrase)

    tdd_text = tdd_path.read_text(encoding="utf-8")
    for phrase in [
        "retrieval_audit_mapped",
        "retrieval_audit_partial",
        "retrieval_audit_gap",
        "retrieval_audit_cross_layer_related_records",
        "retrieval_audit_no_semantic_fields",
        "check_retrieval_coverage_audit_cli",
    ]:
        if phrase not in tdd_text:
            fail("Retrieval coverage audit TDD missing phrase: " + phrase)

    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-retrieval-audit-"))
    try:
        for subdir in ["behavior", "domain", "spec", "ssot", "tests", "project", "knowledge", "generated"]:
            (temp / ".lazy-harness" / subdir).mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "domain" / "searchable-record-memory.md").write_text(
            "# Searchable Record Memory\n\n"
            "## Rule digest\n\n"
            "- Status: active\n"
            "- Layer: DDD\n"
            "- Scope: host-project\n"
            "- Applies when:\n"
            "  - defining retrieval coverage audit terminology\n"
            "- Must:\n"
            "  - keep record memory searchable without semantic authority\n",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "behavior" / "llm-owned-record-retrieval.md").write_text(
            "# LLM-Owned Record Retrieval\n\n"
            "## Rule digest\n\n"
            "- Status: active\n"
            "- Layer: BDD\n"
            "- Scope: host-project\n"
            "- Applies when:\n"
            "  - retrieval coverage audit surfaces cross-layer candidates\n"
            "- Must:\n"
            "  - read actual DDD BDD SDD TDD SSOT records before relying on candidates\n",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "ssot" / "cli-tool-boundary.md").write_text(
            "# CLI Tool Boundary\n\n"
            "## Rule digest\n\n"
            "- Status: active\n"
            "- Layer: SSOT\n"
            "- Scope: host-project\n"
            "- Applies when:\n"
            "  - retrieval coverage audit emits cue-only CLI output\n"
            "- Must:\n"
            "  - keep semantic authority with the LLM/searcher\n",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "tests" / "retrieval-coverage-audit.md").write_text(
            "# Retrieval Coverage Audit Regression\n\n"
            "## Rule digest\n\n"
            "- Status: active\n"
            "- Layer: TDD\n"
            "- Scope: host-project\n"
            "- Applies when:\n"
            "  - retrieval coverage audit must verify no cross-layer records are missing\n"
            "- Must:\n"
            "  - protect DDD BDD SDD TDD SSOT related-record retrieval\n",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "spec" / "retrieval-coverage-audit.md").write_text(
            "# Retrieval Coverage Audit\n\n"
            "Related DDD: `.lazy-harness/domain/searchable-record-memory.md`\n"
            "Related BDD: `.lazy-harness/behavior/llm-owned-record-retrieval.md`\n"
            "Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`\n"
            "Related TDD: `.lazy-harness/tests/retrieval-coverage-audit.md`\n\n"
            "## Rule digest\n\n"
            "- Status: active\n"
            "- Layer: SDD\n"
            "- Scope: host-project\n"
            "- Applies when:\n"
            "  - retrieval coverage audit checks missing cross-layer records\n"
            "- Must:\n"
            "  - include related DDD BDD SSOT and TDD records as retrieval candidates\n\n"
            "## Implementation map\n\n"
            "- Source: `.lazy-harness/scripts/retrieval-coverage-audit.ts`\n"
            "- Tests: `.lazy-harness/scripts/self-test.py`\n",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "behavior" / "feature-surface.md").write_text(
            "# Feature Surface\n\n"
            "## Rule digest\n\n"
            "- Status: active\n"
            "- Layer: BDD\n"
            "- Scope: host-project\n"
            "- Applies when:\n"
            "  - user asks about feature surface UI\n"
            "- Must:\n"
            "  - confirm feature panel behavior before editing\n"
            "- Aliases:\n"
            "  - feature panel\n"
            "- Surface terms:\n"
            "  - feature surface\n"
            "- Implementation hints:\n"
            "  - Components: `FeaturePanel`\n"
            "  - Files: `src/features/example-feature/FeaturePanel.tsx`\n"
            "  - Tests: `tests/example-feature/feature-panel.test.tsx`\n"
            "- Related records:\n"
            "  - `.lazy-harness/spec/feature-surface.md`\n\n"
            "## Implementation map\n\n"
            "- Source: `src/features/example-feature/FeaturePanel.tsx`\n"
            "- Tests: `tests/example-feature/feature-panel.test.tsx`\n",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "spec" / "partial-record.md").write_text(
            "# Orphan Audit\n\n"
            "## Rule digest\n\n"
            "- Status: active\n"
            "- Layer: SDD\n"
            "- Scope: host-project\n"
            "- Applies when:\n"
            "  - orphan audit fixture appears\n"
            "- Must:\n"
            "  - keep structural partial coverage visible\n"
            "- Aliases:\n"
            "  - orphan audit\n",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "project" / "feature-navigation.xml").write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<featureNavigation version="1.0">
  <feature id="example-feature" status="confirmed">
    <label>Feature Surface</label>
    <aliases><alias lang="en">feature panel</alias></aliases>
    <components><component>FeaturePanel</component></components>
    <records><record layer="BDD">.lazy-harness/behavior/feature-surface.md</record></records>
    <sourceFiles><path>src/features/example-feature/FeaturePanel.tsx</path></sourceFiles>
    <tests><path>tests/example-feature/feature-panel.test.tsx</path></tests>
  </feature>
</featureNavigation>
""",
            encoding="utf-8",
        )
        (temp / ".lazy-harness" / "knowledge" / "graph.jsonl").write_text(
            json.dumps({
                "id": "kg_feature_surface_behavior_impl",
                "source": ".lazy-harness/behavior/feature-surface.md",
                "relation": "implemented_by",
                "target": "src/features/example-feature/FeaturePanel.tsx",
            }, ensure_ascii=False) + "\n" +
            json.dumps({
                "id": "kg_retrieval_coverage_audit_fixture_impl",
                "path": ".lazy-harness/spec/retrieval-coverage-audit.md",
                "relation": "implemented_by",
                "target": ".lazy-harness/scripts/retrieval-coverage-audit.ts",
            }, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        def run_audit(query: str) -> dict:
            completed = subprocess.run(
                [str(LAZY / "bin" / "lazy"), "retrieval-audit", query, "--format=json", "--limit=12"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env={**os.environ, "LAZY_HOST_ROOT": str(temp)},
            )
            if completed.returncode != 0:
                fail(f"lazy retrieval-audit failed for {query!r}:\n" + completed.stdout + completed.stderr)
            try:
                return json.loads(completed.stdout)
            except Exception as exc:  # noqa: BLE001
                fail(f"retrieval-audit output was not JSON for {query!r}: {exc}\n{completed.stdout}")

        mapped = run_audit("feature panel")
        if mapped.get("mode") != "retrieval-coverage-audit":
            fail("retrieval-audit output mode mismatch")
        if mapped.get("coverage", {}).get("state") != "mapped" or mapped.get("coverage", {}).get("gaps"):
            fail("feature panel query should be fully mapped: " + json.dumps(mapped.get("coverage"), ensure_ascii=False))
        candidates = mapped.get("candidates", {})
        if ".lazy-harness/behavior/feature-surface.md" not in candidates.get("recordPaths", []):
            fail("mapped audit missing record candidate")
        if "src/features/example-feature/FeaturePanel.tsx" not in candidates.get("sourceFiles", []):
            fail("mapped audit missing source candidate")
        if "tests/example-feature/feature-panel.test.tsx" not in candidates.get("testFiles", []):
            fail("mapped audit missing test candidate")
        if "kg_feature_surface_behavior_impl" not in candidates.get("graphIds", []):
            fail("mapped audit missing graph candidate")

        cross_layer = run_audit("retrieval coverage audit")
        if cross_layer.get("coverage", {}).get("state") != "mapped":
            fail("retrieval coverage audit query should map cross-layer records: " + json.dumps(cross_layer.get("coverage"), ensure_ascii=False))
        cross_paths = set(cross_layer.get("candidates", {}).get("recordPaths", []))
        for required_path in [
            ".lazy-harness/domain/searchable-record-memory.md",
            ".lazy-harness/behavior/llm-owned-record-retrieval.md",
            ".lazy-harness/spec/retrieval-coverage-audit.md",
            ".lazy-harness/ssot/cli-tool-boundary.md",
            ".lazy-harness/tests/retrieval-coverage-audit.md",
        ]:
            if required_path not in cross_paths:
                fail("retrieval-audit missing cross-layer related record candidate: " + required_path)
        cross_candidates = cross_layer.get("candidates", {})
        if ".lazy-harness/scripts/retrieval-coverage-audit.ts" not in cross_candidates.get("sourceFiles", []):
            fail("retrieval-audit cross-layer fixture missing source candidate")
        if ".lazy-harness/scripts/self-test.py" not in cross_candidates.get("testFiles", []):
            fail("retrieval-audit cross-layer fixture missing test candidate")
        if "kg_retrieval_coverage_audit_fixture_impl" not in cross_candidates.get("graphIds", []):
            fail("retrieval-audit cross-layer fixture missing graph candidate")

        partial = run_audit("orphan audit")
        if partial.get("coverage", {}).get("state") != "partial":
            fail("orphan audit query should be partial: " + json.dumps(partial.get("coverage"), ensure_ascii=False))
        partial_gaps = set(partial.get("coverage", {}).get("gaps", []))
        for gap in ["no-source-candidates", "no-test-candidates", "no-graph-candidates"]:
            if gap not in partial_gaps:
                fail("partial audit missing gap label: " + gap)
        if "no-map-matches" in partial_gaps:
            fail("partial audit should have at least one structural map match")

        gap = run_audit("zzzz-missing-token")
        if gap.get("coverage", {}).get("state") != "gap":
            fail("missing query should be a retrieval gap")
        if "no-map-matches" not in gap.get("coverage", {}).get("gaps", []):
            fail("gap audit missing no-map-matches label")
        if "grep -Rli" not in gap.get("commands", {}).get("fallbackGrep", ""):
            fail("gap audit missing fallback grep command")

        forbidden = {"requiredRead", "optionalRead", "confidence", "intent", "risk", "gate", "nextAction", "candidateMeanings"}

        def assert_no_forbidden_keys(value: object, path: str = "$.") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in forbidden:
                        fail("retrieval-audit emitted forbidden semantic-authority key: " + path + key)
                    assert_no_forbidden_keys(child, path + key + ".")
            elif isinstance(value, list):
                for idx, child in enumerate(value):
                    assert_no_forbidden_keys(child, path + f"{idx}.")

        for result in [mapped, cross_layer, partial, gap]:
            assert_no_forbidden_keys(result)

        if (temp / ".lazy-harness" / "generated" / "record-index.json").exists():
            fail("retrieval-audit must not write generated record-index cache")
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ retrieval coverage audit CLI ok")


def check_retrieval_workflow_benchmark_cli() -> None:
    """Retrieval workflow benchmark should stay read-only and measurement-only."""
    script_path = LAZY / "scripts" / "retrieval-workflow-benchmark.ts"
    sdd_path = LAZY / "spec" / "platform" / "retrieval-workflow-benchmark.md"
    tdd_path = LAZY / "tests" / "retrieval-workflow-benchmark.md"
    for path in [script_path, sdd_path, tdd_path]:
        if not path.exists():
            fail("Retrieval workflow benchmark artifact missing: " + str(path))

    sdd_text = sdd_path.read_text(encoding="utf-8")
    for phrase in [
        "mode: \"retrieval-workflow-benchmark\"",
        "post-overview helper cost",
        "map_plus_retrieval_audit",
        "Follow-up read simulation",
        "Forbidden fields anywhere in output",
        "measurement-only",
        "Implementation map",
    ]:
        if phrase not in sdd_text:
            fail("Retrieval workflow benchmark SDD missing phrase: " + phrase)

    tdd_text = tdd_path.read_text(encoding="utf-8")
    for phrase in [
        "retrieval_workflow_benchmark_shape",
        "retrieval_workflow_benchmark_no_semantic_fields",
        "retrieval_workflow_benchmark_read_only",
        "map_plus_retrieval_audit.helperCalls == 2",
        "does not change lifecycle/prompt/overview policy",
    ]:
        if phrase not in tdd_text:
            fail("Retrieval workflow benchmark TDD missing phrase: " + phrase)

    help_text = subprocess.check_output([str(LAZY / "bin" / "lazy"), "help"], cwd=ROOT, text=True)
    if "retrieval-workflow-benchmark" not in help_text:
        fail("lazy help must advertise retrieval-workflow-benchmark command")

    graph_path = LAZY / "knowledge" / "graph.jsonl"
    record_index_path = LAZY / "generated" / "record-index.json"
    graph_before = graph_path.read_bytes() if graph_path.exists() else b""
    record_index_before = record_index_path.read_bytes() if record_index_path.exists() else b""

    completed = subprocess.run(
        [str(LAZY / "bin" / "lazy"), "retrieval-workflow-benchmark", "--format=json", "--limit=8"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        fail("retrieval-workflow-benchmark JSON command failed:\n" + completed.stdout + completed.stderr)
    try:
        payload = json.loads(completed.stdout)
    except Exception as exc:  # noqa: BLE001
        fail(f"retrieval-workflow-benchmark output was not JSON: {exc}\n{completed.stdout[:1000]}")

    if payload.get("schemaVersion") != "1.0" or payload.get("mode") != "retrieval-workflow-benchmark":
        fail("retrieval-workflow-benchmark schema/mode mismatch")
    queries = payload.get("querySet", [])
    for required_query in ["retrieval coverage audit", "workflow compression not safety reduction"]:
        if required_query not in queries:
            fail("retrieval-workflow-benchmark missing default query: " + required_query)
    if "measurement-only" not in payload.get("policyBoundary", ""):
        fail("retrieval-workflow-benchmark missing measurement-only policy boundary")

    forbidden = {"requiredRead", "optionalRead", "confidence", "intent", "risk", "gate", "nextAction", "candidateMeanings"}

    def assert_no_forbidden_keys(value: object, path: str = "$." ) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in forbidden:
                    fail("retrieval-workflow-benchmark emitted forbidden semantic-authority key: " + path + key)
                assert_no_forbidden_keys(child, path + key + ".")
        elif isinstance(value, list):
            for idx, child in enumerate(value):
                assert_no_forbidden_keys(child, path + f"{idx}.")

    assert_no_forbidden_keys(payload)

    surfaces = payload.get("surfaces", [])
    if not surfaces:
        fail("retrieval-workflow-benchmark missing per-query surfaces")
    for query_result in surfaces:
        per_surface = query_result.get("surfaces", {})
        for name in ["map", "map_plus_retrieval_audit"]:
            if name not in per_surface:
                fail("retrieval-workflow-benchmark missing surface " + name)
            item = per_surface[name]
            for numeric_path in [
                ["helperBytes"],
                ["helperEstimatedTokens"],
                ["elapsedMs"],
                ["totalEstimatedTokens"],
                ["candidateCounts", "records"],
                ["candidateCounts", "sources"],
                ["candidateCounts", "tests"],
                ["candidateCounts", "graphs"],
                ["followupRead", "readCount"],
                ["followupRead", "bytes"],
                ["followupRead", "estimatedTokens"],
            ]:
                cursor = item
                for key in numeric_path:
                    cursor = cursor[key]
                if not isinstance(cursor, (int, float)):
                    fail("retrieval-workflow-benchmark numeric field missing: " + name + "." + ".".join(numeric_path))
            covered_layers = item.get("followupRead", {}).get("coveredLayers", {})
            for layer in ["DDD", "BDD", "SDD", "TDD", "SSOT"]:
                if layer not in covered_layers:
                    fail("retrieval-workflow-benchmark missing covered layer: " + layer)
        if per_surface["map_plus_retrieval_audit"].get("helperCalls") != 2:
            fail("map_plus_retrieval_audit helperCalls should be 2")

    for surface_name in ["map", "map_plus_retrieval_audit"]:
        if surface_name not in payload.get("summary", {}).get("aggregate", {}):
            fail("retrieval-workflow-benchmark missing aggregate surface: " + surface_name)

    md = subprocess.run(
        [str(LAZY / "bin" / "lazy"), "retrieval-workflow-benchmark", "--format=md", "--limit=8"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if md.returncode != 0:
        fail("retrieval-workflow-benchmark markdown command failed:\n" + md.stdout + md.stderr)
    if "measurement-only" not in md.stdout or "does not change lifecycle/prompt/overview policy" not in md.stdout:
        fail("retrieval-workflow-benchmark markdown missing policy boundary warning")

    if graph_path.exists() and graph_path.read_bytes() != graph_before:
        fail("retrieval-workflow-benchmark must not mutate canonical graph.jsonl")
    if record_index_path.exists() and record_index_path.read_bytes() != record_index_before:
        fail("retrieval-workflow-benchmark must not mutate generated record-index cache")
    print("✓ retrieval workflow benchmark CLI ok")


def check_source_feature_navigation_phase3() -> None:
    """Source repo Phase 3 should expose a compact canonical project feature map."""
    feature_path = LAZY / "project" / "feature-navigation.xml"
    if not feature_path.exists():
        fail("source feature navigation missing: .lazy-harness/project/feature-navigation.xml")

    expected = {
        "prompt-runtime-lifecycle": {
            "aliases": {"message.received", "prompt budget", "search debt"},
            "paths": {
                ".lazy-harness/spec/platform/pre-response-rule-context.md",
                ".lazy-harness/spec/platform/prompt-budget.md",
                ".lazy-harness/hooks/lifecycle/on-message-received.sh",
                ".lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py",
                ".lazy-harness/scripts/prompt-budget.py",
                ".lazy-harness/scripts/self-test.py",
            },
        },
        "capability-registry": {
            "aliases": {"capability registry", "capability resolution", "capabilities.json"},
            "paths": {
                ".lazy-harness/ssot/capability-registry.md",
                ".lazy-harness/spec/platform/capability-resolution.md",
                ".lazy-harness/scripts/capability.ts",
                ".lazy-harness/ssot/capabilities.json",
            },
        },
        "record-source-indexing": {
            "aliases": {"record index", "record map", "feature-navigation.xml"},
            "paths": {
                ".lazy-harness/spec/platform/project-profile.md",
                ".lazy-harness/scripts/record-index.ts",
                ".lazy-harness/scripts/record-map.ts",
                ".lazy-harness/bin/lazy",
                ".lazy-harness/schemas/record-index.schema.json",
            },
        },
        "record-decision-broker": {
            "aliases": {"record decision", "RecordDecisionPacket", "record-decision-broker.ts"},
            "paths": {
                ".lazy-harness/spec/platform/record-decision-broker.md",
                ".lazy-harness/tests/record-decision-broker.md",
                ".lazy-harness/scripts/record-decision-broker.ts",
                ".lazy-harness/schemas/record-decision-packet.schema.json",
            },
        },
        "implementation-map-graph-hygiene": {
            "aliases": {"implementation map", "knowledge graph", "graph.jsonl"},
            "paths": {
                ".lazy-harness/spec/platform/implementation-map-standard.md",
                ".lazy-harness/ssot/implementation-map-storage.md",
                ".lazy-harness/scripts/implementation-map-audit.ts",
                ".lazy-harness/scripts/graph-hygiene.ts",
                ".lazy-harness/knowledge/graph.jsonl",
            },
        },
        "lifecycle-compare-parity": {
            "aliases": {"lifecycle check", "lifecycle parity", "lifecycle-check.py"},
            "paths": {
                ".lazy-harness/decisions/0016-lifecycle-hook-strategy.md",
                ".lazy-harness/tests/lifecycle-compare-fidelity.md",
                ".lazy-harness/scripts/lifecycle-check.py",
                ".lazy-harness/scripts/lifecycle-parity-runner.py",
            },
        },
        "sync-install-update": {
            "aliases": {"lazy init", "lazy sync", "jcode wiring"},
            "paths": {
                "install.sh",
                ".lazy-harness/spec/lazy-sync-drift-detection.md",
                ".lazy-harness/tests/lazy-sync-dirty-false-positive.md",
                ".lazy-harness/scripts/lazy-init.ts",
                ".lazy-harness/scripts/lazy-sync.ts",
                ".lazy-harness/scripts/jcode-wiring.ts",
            },
        },
        "project-operating-rulebook": {
            "aliases": {"project operating rulebook", "lazy rules", "행동규약"},
            "paths": {
                ".lazy-harness/decisions/0044-project-operating-rulebook.md",
                ".lazy-harness/spec/platform/project-operating-rulebook.md",
                ".lazy-harness/tests/project-operating-rulebook.md",
                ".lazy-harness/rules/README.md",
                ".lazy-harness/scripts/rulebook.ts",
                ".lazy-harness/scripts/capability.ts",
                ".lazy-harness/schemas/capabilities.schema.json",
                ".lazy-harness/bin/lazy",
            },
        },
        "purpose-scoped-retrieval": {
            "aliases": {"purpose scoped retrieval", "lazy find", "목적별 검색", "행동 규약 검색"},
            "paths": {
                ".lazy-harness/decisions/0045-purpose-scoped-retrieval.md",
                ".lazy-harness/domain/purpose-scoped-retrieval.md",
                ".lazy-harness/behavior/purpose-scoped-retrieval.md",
                ".lazy-harness/spec/platform/purpose-scoped-retrieval.md",
                ".lazy-harness/tests/purpose-scoped-retrieval.md",
                ".lazy-harness/scripts/purpose-find.ts",
                ".lazy-harness/bin/lazy",
            },
        },
        "test-doctor": {
            "aliases": {"lazy test", "lazy doctor", "self-test.py"},
            "paths": {
                ".lazy-harness/decisions/0022-framework-owned-doctor-and-lazy-test.md",
                ".lazy-harness/decisions/0026-doctor-self-test-scope-separation.md",
                ".lazy-harness/scripts/self-test.py",
                ".lazy-harness/scripts/doctor.py",
                ".lazy-harness/bin/lazy",
            },
        },
    }

    root = ET.parse(feature_path).getroot()
    features = {feature.attrib.get("id"): feature for feature in root.findall("feature")}
    missing_features = [feature_id for feature_id in expected if feature_id not in features]
    if missing_features:
        fail("source feature navigation missing critical features: " + json.dumps(missing_features, ensure_ascii=False))

    for feature_id, requirements in expected.items():
        feature = features[feature_id]
        if feature.attrib.get("status") != "confirmed":
            fail(f"source feature {feature_id} should be status=confirmed")
        if not (feature.findtext("label") or "").strip():
            fail(f"source feature {feature_id} missing label")
        if not (feature.findtext("risk") or "").strip():
            fail(f"source feature {feature_id} missing risk note")
        aliases = {node.text.strip() for node in feature.findall("./aliases/alias") if node.text and node.text.strip()}
        missing_aliases = sorted(requirements["aliases"] - aliases)
        if missing_aliases:
            fail(f"source feature {feature_id} missing aliases: {missing_aliases}")
        paths = {
            node.text.strip()
            for node in feature.findall(".//path")
            if node.text and node.text.strip()
        } | {
            node.text.strip()
            for node in feature.findall("./records/record")
            if node.text and node.text.strip()
        }
        missing_paths = sorted(requirements["paths"] - paths)
        if missing_paths:
            fail(f"source feature {feature_id} missing paths: {missing_paths}")
        nonexistent = sorted(path for path in paths if not (ROOT / path).exists())
        if nonexistent:
            fail(f"source feature {feature_id} references missing paths: {nonexistent}")

    record_index = subprocess.run(
        ["bun", str(LAZY / "scripts" / "record-index.ts"), "--root", str(ROOT), "--format=json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if record_index.returncode != 0:
        fail("source record-index generation failed:\n" + record_index.stdout + record_index.stderr)
    payload = json.loads(record_index.stdout)
    profile = payload.get("projectProfile", {})
    if profile.get("featureNavigationPath") != ".lazy-harness/project/feature-navigation.xml":
        fail("source record-index missing source feature-navigation path")
    indexed_ids = {feature.get("id") for feature in profile.get("features", [])}
    missing_indexed = sorted(set(expected) - indexed_ids)
    if missing_indexed:
        fail("source record-index missing projectProfile feature ids: " + json.dumps(missing_indexed, ensure_ascii=False))

    records = {record.get("recordPath"): record for record in payload.get("records", [])}
    prompt_record = records.get(".lazy-harness/spec/platform/pre-response-rule-context.md")
    if not prompt_record or "prompt-runtime-lifecycle" not in prompt_record.get("projectProfileFeatureIds", []):
        fail("source record-index did not attach prompt-runtime-lifecycle to pre-response SDD")
    prompt_hints = prompt_record.get("implementationHints", {})
    if ".lazy-harness/hooks/lifecycle/on-message-received.sh" not in prompt_hints.get("fileHints", []):
        fail("source record-index did not merge prompt runtime source file hint")

    print(f"✓ source feature navigation Phase 3 ok ({len(expected)} features)")


def _context_tier_entries(manifest: dict) -> list[dict]:
    tiers = manifest.get("tiers")
    if not isinstance(tiers, dict):
        fail("context tier manifest fixture missing tiers object")
    entries: list[dict] = []
    for tier in ("always", "optional"):
        bucket = tiers.get(tier)
        if not isinstance(bucket, list):
            fail(f"context tier manifest fixture tier {tier!r} must be a list")
        entries.extend(bucket)
    for tier in ("phase", "task"):
        groups = tiers.get(tier)
        if not isinstance(groups, list):
            fail(f"context tier manifest fixture tier {tier!r} must be a list")
        for group in groups:
            if not isinstance(group, dict):
                fail(f"context tier manifest fixture tier {tier!r} group must be an object")
            if not group.get("id"):
                fail(f"context tier manifest fixture tier {tier!r} group missing id")
            applies = group.get("appliesWhen")
            if not isinstance(applies, list) or not applies:
                fail(f"context tier manifest fixture tier {tier!r} group missing appliesWhen")
            group_entries = group.get("entries")
            if not isinstance(group_entries, list):
                fail(f"context tier manifest fixture tier {tier!r} group missing entries list")
            entries.extend(group_entries)
    return entries


def _assert_context_tier_entry(entry: dict, allowed_kinds: set[str], allowed_postures: set[str]) -> None:
    if not isinstance(entry, dict):
        fail("context tier manifest entry must be an object")
    required = {"path", "kind", "reason", "posture"}
    missing = sorted(required - set(entry))
    if missing:
        fail(f"context tier manifest entry missing keys: {missing}")
    extra = sorted(set(entry) - required)
    if extra:
        fail(f"context tier manifest entry has unexpected keys: {extra}")
    if entry["kind"] not in allowed_kinds:
        fail(f"context tier manifest entry has invalid kind: {entry['kind']}")
    if entry["posture"] not in allowed_postures:
        fail(f"context tier manifest entry has invalid posture: {entry['posture']}")
    for key in ("path", "reason"):
        if not isinstance(entry[key], str) or not entry[key].strip():
            fail(f"context tier manifest entry key {key!r} must be a non-empty string")
    path = entry["path"]
    if pathlib.Path(path).is_absolute() or ".." in pathlib.Path(path).parts:
        fail(f"context tier manifest entry path must stay root-relative: {path}")
    if not (ROOT / path).exists():
        fail(f"context tier manifest entry path does not exist: {path}")


def check_context_tier_manifest_phase4() -> None:
    """Phase 4 keeps context tier manifests optional, advisory, and pointer-audited."""
    sdd_path = LAZY / "spec" / "platform" / "context-tier-manifest.md"
    schema_path = LAZY / "schemas" / "context-tier-manifest.schema.json"
    fixture_path = LAZY / "fixtures" / "context-tier" / "context-tier-manifest.sample.json"
    source_manifest_path = LAZY / "project" / "context-tiers.yaml"

    for path in (sdd_path, schema_path, fixture_path):
        if not path.exists():
            fail(f"context tier manifest Phase 4 missing file: {path.relative_to(ROOT)}")

    sdd = sdd_path.read_text(encoding="utf-8")
    for expected in (
        "treat context tiers as advisory pointer hints, not canonical truth",
        "keep the default `message.received` hook static and unchanged",
        "no record-index ingestion",
        "absence of `.lazy-harness/project/context-tiers.yaml` is valid",
    ):
        if expected not in sdd:
            fail("context tier manifest SDD missing invariant: " + expected)

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("title") != "ContextTierManifest":
        fail("context tier manifest schema title mismatch")
    if schema.get("properties", {}).get("status", {}).get("enum") != ["advisory"]:
        fail("context tier manifest schema status must be advisory-only")
    tier_props = schema.get("properties", {}).get("tiers", {}).get("properties", {})
    expected_tiers = {"always", "phase", "task", "optional"}
    if set(tier_props) != expected_tiers:
        fail("context tier manifest schema tier keys mismatch")
    definitions = schema.get("definitions", {})
    allowed_kinds = set(definitions.get("kind", {}).get("enum", []))
    allowed_postures = set(definitions.get("readPosture", {}).get("enum", []))
    if not {"record", "plan", "project-profile", "source-file", "test", "schema", "fixture", "graph"}.issubset(allowed_kinds):
        fail("context tier manifest schema missing required kind enum values")
    if allowed_postures != {"required-hint", "optional-hint", "validation-hint"}:
        fail("context tier manifest schema posture enum mismatch")

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    expected_top = {
        "schemaVersion": "1.0",
        "status": "advisory",
        "scope": "framework-source",
        "manifestKind": "context-tier-manifest",
    }
    for key, value in expected_top.items():
        if fixture.get(key) != value:
            fail(f"context tier manifest sample fixture {key} mismatch")
    if set(fixture.get("tiers", {})) != expected_tiers:
        fail("context tier manifest sample fixture tier keys mismatch")
    for entry in _context_tier_entries(fixture):
        _assert_context_tier_entry(entry, allowed_kinds, allowed_postures)

    forbidden_key_fragments = ("rawmessage", "rawuser", "transcript", "assistantresponse", "rawassistant")
    fixture_text = fixture_path.read_text(encoding="utf-8").lower()
    if any(fragment in fixture_text for fragment in forbidden_key_fragments):
        fail("context tier manifest sample fixture contains forbidden raw transcript/message field")

    if source_manifest_path.exists():
        source_text = source_manifest_path.read_text(encoding="utf-8")
        for expected in ("status: advisory", "manifestKind: context-tier-manifest", "always:", "phase:", "task:", "optional:"):
            if expected not in source_text:
                fail("source context tier manifest missing expected marker: " + expected)
        if ".lazy-harness/hooks/lifecycle/on-message-received.sh" in source_text:
            fail("source context tier manifest must not reference message.received hook implementation")
        for line_number, line in enumerate(source_text.splitlines(), 1):
            match = re.match(r"^\s*-?\s*path:\s*(.+?)\s*$", line)
            if not match:
                continue
            value = match.group(1).split(" #", 1)[0].strip().strip('"\'')
            if not value:
                fail(f"source context tier manifest empty path at line {line_number}")
            path = pathlib.Path(value)
            if path.is_absolute() or ".." in path.parts:
                fail(f"source context tier manifest path must stay root-relative at line {line_number}: {value}")
            if not (ROOT / value).exists():
                fail(f"source context tier manifest path missing at line {line_number}: {value}")

    manifest = json.loads((LAZY / "manifests" / "init-categories.json").read_text(encoding="utf-8"))
    category_a = manifest.get("categories", {}).get("A", {}).get("items", [])
    serialized_a = json.dumps(category_a, ensure_ascii=False)
    if "spec/platform/context-tier-manifest.md" not in serialized_a:
        fail("init categories missing context tier SDD")
    if "context-tier/*.json" not in serialized_a:
        fail("init categories fixtures glob does not sync context-tier JSON fixtures")

    print("✓ context tier manifest Phase 4 ok")


def _assert_no_project_map_forbidden_fields(value, path_name="$") -> None:
    forbidden = {
        "confidence",
        "intent",
        "risk",
        "requiredRead",
        "optionalRead",
        "gate",
        "nextAction",
        "candidateMeaning",
        "candidateMeanings",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden:
                fail(f"project-map V2 fixture contains forbidden semantic-authority field: {path_name}.{key}")
            _assert_no_project_map_forbidden_fields(child, f"{path_name}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_project_map_forbidden_fields(child, f"{path_name}[{index}]")


def check_project_map_v2_schema() -> None:
    """Project Map V2 Phase 1 must define cue-only node schema, taxonomy, and fixture."""
    sdd_path = LAZY / "spec" / "platform" / "project-map-v2.md"
    ssot_path = LAZY / "ssot" / "project-map-taxonomy.md"
    storage_ssot_path = LAZY / "ssot" / "project-map-record-storage.md"
    tdd_path = LAZY / "tests" / "project-map-v2.md"
    storage_tdd_path = LAZY / "tests" / "project-map-record-storage.md"
    fixture_path = LAZY / "fixtures" / "project-map-v2" / "example-node.json"
    branch_fixture_path = LAZY / "fixtures" / "project-map-v2" / "record-branch-block.md"

    for path in (sdd_path, ssot_path, storage_ssot_path, tdd_path, storage_tdd_path, fixture_path, branch_fixture_path):
        if not path.exists():
            fail(f"Project Map V2 missing file: {path.relative_to(ROOT)}")

    sdd = sdd_path.read_text(encoding="utf-8")
    ssot = ssot_path.read_text(encoding="utf-8")
    storage_ssot = storage_ssot_path.read_text(encoding="utf-8")
    tdd = tdd_path.read_text(encoding="utf-8")
    storage_tdd = storage_tdd_path.read_text(encoding="utf-8")
    branch_fixture = branch_fixture_path.read_text(encoding="utf-8")
    for expected in (
        "one primary category and multiple facets",
        "Anchor / branch / edge model",
        "what project-map cluster does this information belong to",
        "Pi is the primary future adapter direction",
        "Jcode remains a compatibility adapter",
        "Phase 1 must not move them",
        "Canonical storage pattern",
        "Project Map branch blocks inside those records",
        "generated view is never the truth by itself",
    ):
        if expected not in sdd:
            fail("Project Map V2 SDD missing invariant: " + expected)
    for expected in (
        "A Project Map node has exactly one primary category in Phase 1.",
        "Cluster roles",
        "Edge relations",
        "chat-window-patient-sharing",
        "Record storage pattern",
        "generated views are never the source of truth",
        "Tests are one example.",
        "pi`: primary future adapter",
        "jcode`: compatibility adapter",
    ):
        if expected not in ssot:
            fail("Project Map V2 taxonomy missing invariant: " + expected)
    for expected in (
        "project_map_node_required_fields",
        "project_map_node_cluster",
        "project_map_node_edges",
        "project_map_node_policy_stages",
        "project_map_node_adapter_boundary",
        "Forbidden semantic-authority fields",
    ):
        if expected not in tdd:
            fail("Project Map V2 TDD missing regression case: " + expected)
    for expected in (
        "canonical layer records",
        "Project Map branch blocks",
        "generated Project Map view",
        "do not become the source of truth",
    ):
        if expected not in storage_ssot:
            fail("Project Map V2 storage SSOT missing invariant: " + expected)
    for expected in (
        "project_map_record_storage_ssot_exists",
        "project_map_branch_block_fixture",
        "project_map_generated_view_cue_only",
    ):
        if expected not in storage_tdd:
            fail("Project Map V2 storage TDD missing regression case: " + expected)
    for expected in (
        "## Project Map branch",
        "- Anchor:",
        "- Branch:",
        "- Node:",
        "- Primary:",
        "- Facets:",
        "- Edges:",
        "- Related records:",
    ):
        if expected not in branch_fixture:
            fail("Project Map V2 branch block fixture missing field: " + expected)
    record_write_policy = (LAZY / "spec" / "platform" / "record-write-update-policy.md").read_text(encoding="utf-8")
    for expected in (
        "maintain digest + Project Map branch + implementation map + graph links",
        "Project Map branch records",
        "generated views remain cue-only and non-canonical",
    ):
        if expected not in record_write_policy:
            fail("record-write-update-policy missing Project Map branch storage rule: " + expected)

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    required = {
        "schemaVersion",
        "id",
        "title",
        "primary",
        "facets",
        "status",
        "scope",
        "canonicalRecords",
        "cluster",
        "links",
        "evidence",
        "policies",
    }
    missing = sorted(required - set(fixture))
    if missing:
        fail("Project Map V2 fixture missing required fields: " + json.dumps(missing, ensure_ascii=False))
    if fixture.get("schemaVersion") != "project-map-node/v1":
        fail("Project Map V2 fixture schemaVersion mismatch")
    allowed_primary = {"facts", "expectations", "contracts", "decisions", "validation", "ownership", "source-links", "policies"}
    if fixture.get("primary") not in allowed_primary:
        fail("Project Map V2 fixture primary category invalid")
    allowed_facets = {"DDD", "BDD", "SDD", "TDD", "ADR", "SSOT", "Planning", "Policy", "Evidence", "Project", "Source"}
    facets = fixture.get("facets")
    if not isinstance(facets, list) or not facets or any(facet not in allowed_facets for facet in facets):
        fail("Project Map V2 fixture facets invalid: " + json.dumps(facets, ensure_ascii=False))
    if len(facets) < 2:
        fail("Project Map V2 fixture should demonstrate multi-facet nodes")
    cluster = fixture.get("cluster")
    if not isinstance(cluster, dict):
        fail("Project Map V2 fixture cluster must be an object")
    if cluster.get("role") not in {"anchor", "branch"}:
        fail("Project Map V2 fixture cluster role invalid")
    if cluster.get("role") == "anchor" and cluster.get("anchorId") != fixture.get("id"):
        fail("Project Map V2 anchor fixture must have cluster.anchorId == id")
    branches = cluster.get("branches")
    if not isinstance(branches, list) or not branches:
        fail("Project Map V2 fixture must include cluster branches")
    branch_ids = {fixture.get("id")}
    branch_primary = set()
    for branch in branches:
        if not isinstance(branch, dict):
            fail("Project Map V2 cluster branch must be an object")
        branch_id = branch.get("id")
        if not isinstance(branch_id, str) or not branch_id:
            fail("Project Map V2 cluster branch missing id")
        branch_ids.add(branch_id)
        primary = branch.get("primary")
        if primary not in allowed_primary:
            fail("Project Map V2 cluster branch primary invalid: " + json.dumps(branch, ensure_ascii=False))
        branch_primary.add(primary)
        branch_facets = branch.get("facets")
        if not isinstance(branch_facets, list) or not branch_facets or any(facet not in allowed_facets for facet in branch_facets):
            fail("Project Map V2 cluster branch facets invalid: " + json.dumps(branch, ensure_ascii=False))
    required_branch_primary = {"facts", "expectations", "contracts", "validation"}
    if not required_branch_primary.issubset(branch_primary):
        fail("Project Map V2 fixture cluster must demonstrate facts/expectations/contracts/validation branches")
    allowed_edge_relations = {
        "has-fact",
        "has-expectation",
        "has-contract",
        "has-validation",
        "has-decision",
        "has-ownership",
        "has-source-link",
        "has-policy",
        "related-to",
    }
    edges = cluster.get("edges")
    if not isinstance(edges, list) or not edges:
        fail("Project Map V2 fixture must include cluster edges")
    seen_relations = set()
    for edge in edges:
        if not isinstance(edge, dict):
            fail("Project Map V2 cluster edge must be an object")
        if edge.get("from") not in branch_ids or edge.get("to") not in branch_ids:
            fail("Project Map V2 cluster edge endpoint unknown: " + json.dumps(edge, ensure_ascii=False))
        relation = edge.get("relation")
        if relation not in allowed_edge_relations:
            fail("Project Map V2 cluster edge relation invalid: " + json.dumps(edge, ensure_ascii=False))
        seen_relations.add(relation)
    for relation in ("has-fact", "has-expectation", "has-contract", "has-validation"):
        if relation not in seen_relations:
            fail("Project Map V2 fixture missing required branch relation: " + relation)
    for record_path in fixture.get("canonicalRecords", []):
        if not isinstance(record_path, str) or not record_path.startswith(".lazy-harness/") or ".." in pathlib.Path(record_path).parts:
            fail("Project Map V2 fixture canonical record path must stay root-bound: " + repr(record_path))
        if not (ROOT / record_path).exists():
            fail("Project Map V2 fixture canonical record path missing: " + record_path)
    allowed_stages = {"turn", "read-only-analysis", "edit", "commit", "push", "release", "high-risk-mutation"}
    allowed_levels = {"discover", "recommend", "default", "warn", "block"}
    policies = fixture.get("policies")
    if not isinstance(policies, list) or not policies:
        fail("Project Map V2 fixture must include policy examples")
    has_non_test_policy = False
    for policy in policies:
        if policy.get("nonTestPolicy") is True:
            has_non_test_policy = True
        stages = policy.get("stages")
        if not isinstance(stages, list) or not stages:
            fail("Project Map V2 policy missing stages: " + json.dumps(policy, ensure_ascii=False))
        for stage in stages:
            if stage.get("stage") not in allowed_stages:
                fail("Project Map V2 policy stage invalid: " + json.dumps(stage, ensure_ascii=False))
            if stage.get("level") not in allowed_levels:
                fail("Project Map V2 policy level invalid: " + json.dumps(stage, ensure_ascii=False))
    if not has_non_test_policy:
        fail("Project Map V2 fixture must include at least one non-test policy example")
    adapter = fixture.get("adapterBoundary", {})
    if adapter.get("primary") != "pi" or "jcode" not in adapter.get("compatibility", []):
        fail("Project Map V2 adapter boundary must be Pi-primary with Jcode compatibility")
    _assert_no_project_map_forbidden_fields(fixture)

    manifest = json.loads((LAZY / "manifests" / "init-categories.json").read_text(encoding="utf-8"))
    category_a = json.dumps(manifest.get("categories", {}).get("A", {}).get("items", []), ensure_ascii=False)
    for expected in (
        "planning/lazy-harness-v2-direction-purpose.md",
        "planning/lazy-harness-v2-implementation-roadmap.md",
        "planning/lazy-harness-v2-evolution-context.md",
        "spec/platform/project-map-v2.md",
        "ssot/project-map-taxonomy.md",
        "tests/project-map-v2.md",
        "project-map-v2/*.json",
        "project-map-v2/*.md",
    ):
        if expected not in category_a:
            fail("init categories missing Project Map V2 sync asset: " + expected)

    print("✓ Project Map V2 schema ok")


def check_project_map_update_loop_v2() -> None:
    """Project Map Phase 1.5 must define adapter-neutral update events with a limited confirmed writer boundary."""
    sdd_path = LAZY / "spec" / "platform" / "project-map-update-loop-v2.md"
    ssot_path = LAZY / "ssot" / "project-map-ingestion-sources.md"
    tdd_path = LAZY / "tests" / "project-map-update-loop-v2.md"
    fixture_path = LAZY / "fixtures" / "project-map-update-loop-v2" / "events.json"
    storage_ssot_path = LAZY / "ssot" / "project-map-record-storage.md"
    hook_sdd_path = LAZY / "spec" / "platform" / "hook-performance-measurement.md"

    for path in (sdd_path, ssot_path, tdd_path, fixture_path, storage_ssot_path, hook_sdd_path):
        if not path.exists():
            fail(f"Project Map update-loop V2 missing file: {path.relative_to(ROOT)}")

    sdd = sdd_path.read_text(encoding="utf-8")
    ssot = ssot_path.read_text(encoding="utf-8")
    tdd = tdd_path.read_text(encoding="utf-8")
    storage_ssot = storage_ssot_path.read_text(encoding="utf-8")
    hook_sdd = hook_sdd_path.read_text(encoding="utf-8")
    for expected in (
        "Project Map update events are JSON-compatible and adapter-neutral.",
        "Candidate/canonical transition model",
        "Forbidden fields anywhere in update event output",
        "Core update-loop semantics decide candidate/canonical transitions.",
        "General adapter/runtime ingestion remains future work.",
        ".lazy-harness/knowledge/project-map-update-events.jsonl",
        "Hook-originated validation output may be represented as a Project Map update event packet",
        "Phase 1 this is contract-only",
    ):
        if expected not in sdd:
            fail("Project Map update-loop SDD missing invariant: " + expected)
    for expected in (
        "Controlled source vocabulary",
        "Controlled event vocabulary",
        "Event-to-branch mapping",
        "Canonical promotion requires all of these",
        "Neither may set canonical truth without the core record-write/update path.",
    ):
        if expected not in ssot:
            fail("Project Map ingestion SSOT missing invariant: " + expected)
    for expected in (
        "project_map_update_event_required_fields",
        "project_map_update_event_vocabulary",
        "project_map_update_sources",
        "project_map_update_transitions",
        "project_map_update_forbidden_fields",
        "project_map_update_limited_runtime_boundary",
        "project_map_update_hook_validation_events",
    ):
        if expected not in tdd:
            fail("Project Map update-loop TDD missing regression case: " + expected)
    for expected in (
        "Structured validation evidence forwarding",
        "source = jcode-adapter",
        "eventType = validation-success|validation-failure",
        "evidence.kind = validation-output",
        "Phase 1 is contract/fixture/static-test only",
    ):
        if expected not in hook_sdd:
            fail("hook performance SDD missing structured validation evidence forwarding invariant: " + expected)
    for expected in (
        "project-map-update-loop-v2.md",
        "project-map-ingestion-sources.md",
        "needs-confirmation",
        "adapters may submit events but do not become semantic authority",
    ):
        if expected not in storage_ssot:
            fail("Project Map record storage SSOT missing update-loop link: " + expected)

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture.get("schemaVersion") != "project-map-update-events/v1":
        fail("Project Map update-loop fixture schemaVersion mismatch")
    events = fixture.get("events")
    if not isinstance(events, list) or not events:
        fail("Project Map update-loop fixture must contain events")

    allowed_event_types = {
        "user-correction",
        "implementation-change",
        "source-discovery",
        "validation-failure",
        "validation-success",
        "adr-decision",
        "project-profile-refresh",
        "policy-promotion",
        "policy-demotion",
        "document-ingestion",
        "adapter-event",
    }
    allowed_sources = {
        "user",
        "agent",
        "source-inspection",
        "test-run",
        "record-write",
        "project-profile",
        "document-resource",
        "policy-machinery",
        "pi-adapter",
        "jcode-adapter",
    }
    allowed_primary = {"facts", "expectations", "contracts", "decisions", "validation", "ownership", "source-links", "policies"}
    allowed_facets = {"DDD", "BDD", "SDD", "TDD", "ADR", "SSOT", "Planning", "Policy", "Evidence", "Project", "Source"}
    allowed_states = {"observation", "candidate", "needs-confirmation", "canonical", "superseded", "rejected"}
    allowed_evidence_kinds = {
        "user-confirmation",
        "user-correction",
        "changed-source",
        "changed-record",
        "changed-test",
        "source-inspection",
        "document-resource",
        "validation-output",
        "adr-record",
        "project-profile",
        "policy-record",
        "adapter-observation",
    }
    allowed_effect_actions = {
        "append-candidate",
        "update-record",
        "create-record",
        "append-graph-edge",
        "attach-evidence",
        "supersede-record",
        "mark-candidate-rejected",
        "none",
    }
    manifest = json.loads((LAZY / "manifests" / "init-categories.json").read_text(encoding="utf-8"))
    manifest_target_paths = {}
    for category in manifest.get("categories", {}).values():
        if not isinstance(category, dict):
            continue
        for item in category.get("items", []):
            if isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("targetPath"), str):
                manifest_target_paths[f".lazy-harness/{item['path']}"] = f".lazy-harness/{item['targetPath']}"

    seen_event_types = set()
    seen_sources = set()
    seen_to_states = set()
    seen_adapter_sources = set()
    seen_hook_validation_events = set()
    required_fields = {"schemaVersion", "id", "eventType", "source", "occurredAt", "scope", "target", "transition", "evidence", "effects"}
    for event in events:
        if not isinstance(event, dict):
            fail("Project Map update-loop event must be object")
        missing = sorted(required_fields - set(event))
        if missing:
            fail("Project Map update-loop event missing fields: " + json.dumps({"id": event.get("id"), "missing": missing}, ensure_ascii=False))
        if event.get("schemaVersion") != "project-map-update-event/v1":
            fail("Project Map update-loop event schemaVersion mismatch: " + repr(event.get("id")))
        event_type = event.get("eventType")
        if event_type not in allowed_event_types:
            fail("Project Map update-loop eventType invalid: " + json.dumps(event, ensure_ascii=False))
        seen_event_types.add(event_type)
        source = event.get("source")
        if source not in allowed_sources:
            fail("Project Map update-loop source invalid: " + json.dumps(event, ensure_ascii=False))
        seen_sources.add(source)
        if source in {"pi-adapter", "jcode-adapter"}:
            seen_adapter_sources.add(source)
            transition_to = event.get("transition", {}).get("to")
            if transition_to == "canonical":
                fail("adapter event must not become canonical by itself: " + repr(event.get("id")))

        target = event.get("target")
        if not isinstance(target, dict):
            fail("Project Map update-loop target must be object: " + repr(event.get("id")))
        for key in ("anchorId", "branch", "nodeId", "primary", "facets"):
            if key not in target:
                fail("Project Map update-loop target missing " + key + ": " + repr(event.get("id")))
        if target.get("primary") not in allowed_primary:
            fail("Project Map update-loop target primary invalid: " + json.dumps(event, ensure_ascii=False))
        facets = target.get("facets")
        if not isinstance(facets, list) or not facets or any(facet not in allowed_facets for facet in facets):
            fail("Project Map update-loop target facets invalid: " + json.dumps(event, ensure_ascii=False))

        transition = event.get("transition")
        if not isinstance(transition, dict):
            fail("Project Map update-loop transition must be object: " + repr(event.get("id")))
        for key in ("from", "to", "requiresConfirmation", "canonicalRecords", "candidateStore"):
            if key not in transition:
                fail("Project Map update-loop transition missing " + key + ": " + repr(event.get("id")))
        if transition.get("from") not in allowed_states or transition.get("to") not in allowed_states:
            fail("Project Map update-loop transition state invalid: " + json.dumps(event, ensure_ascii=False))
        seen_to_states.add(transition.get("to"))
        if not isinstance(transition.get("requiresConfirmation"), bool):
            fail("Project Map update-loop requiresConfirmation must be boolean: " + repr(event.get("id")))
        canonical_records = transition.get("canonicalRecords")
        if not isinstance(canonical_records, list):
            fail("Project Map update-loop canonicalRecords must be list: " + repr(event.get("id")))
        if transition.get("to") in {"canonical", "superseded"} and not canonical_records:
            fail("canonical/superseded update-loop event must include canonicalRecords: " + repr(event.get("id")))
        for record_path in canonical_records:
            if not isinstance(record_path, str) or not record_path.startswith(".lazy-harness/") or ".." in pathlib.Path(record_path).parts:
                fail("Project Map update-loop canonical record path must stay root-bound: " + repr(record_path))
            mapped_record_path = manifest_target_paths.get(record_path)
            if not (ROOT / record_path).exists() and not (mapped_record_path and (ROOT / mapped_record_path).exists()):
                fail("Project Map update-loop canonical record path missing: " + record_path)
        candidate_store = transition.get("candidateStore")
        if candidate_store != ".lazy-harness/knowledge/candidates.jsonl":
            fail("Project Map update-loop candidateStore must be canonical candidates JSONL: " + repr(event.get("id")))

        evidence = event.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            fail("Project Map update-loop event must include compact evidence: " + repr(event.get("id")))
        for item in evidence:
            if item.get("kind") not in allowed_evidence_kinds:
                fail("Project Map update-loop evidence kind invalid: " + json.dumps(item, ensure_ascii=False))
            path_value = item.get("path")
            if path_value:
                path_obj = pathlib.Path(path_value)
                if path_obj.is_absolute() or ".." in path_obj.parts:
                    fail("Project Map update-loop evidence path must stay root-relative: " + path_value)
        if source == "jcode-adapter" and event_type in {"validation-success", "validation-failure"}:
            if event.get("adapter") != "jcode":
                fail("hook-originated validation event must identify jcode adapter: " + repr(event.get("id")))
            if transition.get("to") == "canonical" or canonical_records:
                fail("hook-originated validation event must stay non-canonical in Phase 1: " + repr(event.get("id")))
            if not any(item.get("kind") == "validation-output" for item in evidence):
                fail("hook-originated validation event must include validation-output evidence: " + repr(event.get("id")))
            if not any(item.get("path") == ".lazy-harness/spec/platform/hook-performance-measurement.md" for item in evidence):
                fail("hook-originated validation event must point to hook SDD evidence path: " + repr(event.get("id")))
            seen_hook_validation_events.add(event_type)
        effects = event.get("effects")
        if not isinstance(effects, list):
            fail("Project Map update-loop effects must be list: " + repr(event.get("id")))
        for effect in effects:
            if effect.get("action") not in allowed_effect_actions:
                fail("Project Map update-loop effect action invalid: " + json.dumps(effect, ensure_ascii=False))
            path_value = effect.get("path")
            if path_value:
                path_obj = pathlib.Path(path_value)
                if path_obj.is_absolute() or ".." in path_obj.parts:
                    fail("Project Map update-loop effect path must stay root-relative: " + path_value)
        _assert_no_project_map_forbidden_fields(event, f"event[{event.get('id')}]")

    missing_event_types = sorted(allowed_event_types - seen_event_types)
    if missing_event_types:
        fail("Project Map update-loop fixture missing event types: " + json.dumps(missing_event_types, ensure_ascii=False))
    required_sources = {"pi-adapter", "jcode-adapter", "project-profile", "document-resource", "policy-machinery"}
    if not required_sources.issubset(seen_sources):
        fail("Project Map update-loop fixture missing required sources: " + json.dumps(sorted(required_sources - seen_sources), ensure_ascii=False))
    required_states = {"candidate", "needs-confirmation", "canonical", "superseded", "rejected"}
    if not required_states.issubset(seen_to_states):
        fail("Project Map update-loop fixture missing transition states: " + json.dumps(sorted(required_states - seen_to_states), ensure_ascii=False))
    if seen_adapter_sources != {"pi-adapter", "jcode-adapter"}:
        fail("Project Map update-loop fixture must include Pi and Jcode adapter events")
    if seen_hook_validation_events != {"validation-success", "validation-failure"}:
        fail("Project Map update-loop fixture missing hook-originated validation events: " + json.dumps(sorted({"validation-success", "validation-failure"} - seen_hook_validation_events), ensure_ascii=False))

    category_a = json.dumps(manifest.get("categories", {}).get("A", {}).get("items", []), ensure_ascii=False)
    for expected in (
        "spec/platform/project-map-update-loop-v2.md",
        "ssot/project-map-ingestion-sources.md",
        "tests/project-map-update-loop-v2.md",
        "decisions/0041-organic-hybrid-rule-guidance.md",
        "spec/platform/hook-performance-measurement.md",
        "project-map-update-loop-v2/*.json",
    ):
        if expected not in category_a:
            fail("init categories missing Project Map update-loop sync asset: " + expected)

    print("✓ Project Map update-loop V2 ok")


def check_policy_machinery_v2() -> None:
    """Policy Machinery V2 Option B should use typed policy registry without runtime enforcement."""
    sdd_path = LAZY / "spec" / "platform" / "policy-machinery-v2.md"
    tdd_path = LAZY / "tests" / "policy-machinery-v2.md"
    audit_path = LAZY / "planning" / "policy-machinery-v2-baseline-gap-audit.md"
    source_adr_path = LAZY / "decisions" / "0046-policy-machinery-typed-policy-canonical.md"
    host_operational_adr_path = LAZY / "framework" / "operational-adrs" / "0046-policy-machinery-typed-policy-canonical.md"
    adr_path = source_adr_path if source_adr_path.exists() else host_operational_adr_path
    policy_ssot_path = LAZY / "ssot" / "policy-registry.md"
    policy_registry_path = LAZY / "ssot" / "policies.json"
    policy_schema_path = LAZY / "schemas" / "policies.schema.json"
    policy_cli_path = LAZY / "scripts" / "policy.ts"
    generated_readme_path = LAZY / "generated" / "README.md"
    generated_rulebook_path = LAZY / "generated" / "policy-rulebook.md"
    policy_warn_helper_path = LAZY / "hooks" / "lifecycle" / "helpers" / "check-policy-warn-runtime.py"
    policy_block_helper_path = LAZY / "hooks" / "lifecycle" / "helpers" / "check-policy-block-runtime.py"
    response_hook_path = LAZY / "hooks" / "lifecycle" / "on-response-completed.sh"
    lifecycle_check_path = LAZY / "scripts" / "lifecycle-check.py"
    fixture_path = LAZY / "fixtures" / "policy-machinery-v2" / "example-policy.json"
    manifest_path = LAZY / "manifests" / "init-categories.json"
    capability_ssot_path = LAZY / "ssot" / "capability-registry.md"
    rulebook_sdd_path = LAZY / "spec" / "platform" / "project-operating-rulebook.md"

    for path in (sdd_path, tdd_path, audit_path, adr_path, policy_ssot_path, policy_registry_path, policy_schema_path, policy_cli_path, policy_warn_helper_path, policy_block_helper_path, response_hook_path, lifecycle_check_path, fixture_path, manifest_path, capability_ssot_path, rulebook_sdd_path, generated_readme_path):
        if not path.exists():
            fail(f"Policy Machinery V2 missing file: {path.relative_to(ROOT)}")

    sdd = sdd_path.read_text(encoding="utf-8")
    tdd = tdd_path.read_text(encoding="utf-8")
    audit = audit_path.read_text(encoding="utf-8")
    adr = adr_path.read_text(encoding="utf-8")
    policy_ssot = policy_ssot_path.read_text(encoding="utf-8")
    policy_cli = policy_cli_path.read_text(encoding="utf-8")
    generated_readme = generated_readme_path.read_text(encoding="utf-8")
    policy_warn_helper = policy_warn_helper_path.read_text(encoding="utf-8")
    policy_block_helper = policy_block_helper_path.read_text(encoding="utf-8")
    response_hook = response_hook_path.read_text(encoding="utf-8")
    lifecycle_check = lifecycle_check_path.read_text(encoding="utf-8")
    capability_ssot = capability_ssot_path.read_text(encoding="utf-8")
    rulebook_sdd = rulebook_sdd_path.read_text(encoding="utf-8")

    for expected in (
        "Option B typed policy canonical slice",
        "treat `.lazy-harness/ssot/policies.json` as canonical typed behavior policy storage",
        "Rulebook markdown under `.lazy-harness/rules/**` is compatibility/generated/explain surface during migration.",
        "`lazy policy resolve` is the first resolver slice",
        "enforcement = advisory-only",
        "## Warn-only runtime slice",
        "explicit structured `policy_context`",
        "never emits `STOP`",
        "## Generated rulebook view slice",
        "GENERATED VIEW, NON-CANONICAL",
        "lazy policy render-rulebook --write --format=json",
        "## Rulebook retire-readiness preflight slice",
        "lazy policy retire-readiness --format=json",
        "canonicalByPacketAlone: false",
        "lazy policy audit --format=json",
        "lazy policy resolve --stage turn --applies-to making_validation_claims --format=json",
        "lazy policy resolve --runtime warn --stage turn --applies-to making_validation_claims --format=json",
        "self-test.py#check_policy_machinery_v2",
    ):
        if expected not in sdd:
            fail("Policy Machinery V2 SDD missing invariant: " + expected)

    for expected in (
        "policy_machinery_contract_files",
        "policy_machinery_fixture_shape",
        "policy_machinery_no_semantic_authority_fields",
        "policy_machinery_option_b_storage",
        "policy_machinery_policy_cli_read_only",
        "policy_machinery_policy_resolve_advisory_only",
        "policy_machinery_warn_runtime_explicit_context",
        "policy_machinery_no_block_hook_runtime",
        "policy_machinery_generated_rulebook_view",
        "policy_machinery_rulebook_retire_readiness_source_host_ready",
        "policy_machinery_rulebook_retire_readiness_positive_fixture",
        "policy_machinery_block_runtime_readiness_preflight",
        "policy_machinery_first_block_policy_readiness",
        "policy_machinery_block_runtime_dry_run_helper",
        "Layer completeness gate",
    ):
        if expected not in tdd:
            fail("Policy Machinery V2 TDD missing regression case: " + expected)

    for expected in (
        "Current baseline",
        "Gap matrix",
        "User-confirmed storage decision",
        "read-only `lazy policy list/audit/explain`",
        "explicit-context warn-only runtime",
        "deterministic generated/explain rulebook view",
        "rulebook retire-readiness preflight",
        "block runtime preparation",
        "first `level=block` policy promotion readiness",
        "Discovery capture",
    ):
        if expected not in audit:
            fail("Policy Machinery V2 audit missing planning section: " + expected)

    for expected in (
        "Select Policy Machinery V2 option B",
        ".lazy-harness/ssot/policies.json = canonical typed policy registry",
        "lazy policy explain <id>",
        "Confirmation: user-confirmed",
    ):
        if expected not in adr:
            fail("Policy Machinery V2 ADR missing decision invariant: " + expected)
    for expected in (
        "canonical typed policy registry",
        "`.lazy-harness/rules/**` is a compatibility/generated/explain surface",
        "lazy policy resolve --stage turn --applies-to making_validation_claims --format=json",
        "lazy policy resolve --runtime warn --stage turn --applies-to making_validation_claims --format=json",
        "Warn runtime is a separate explicit-context mode",
        "Generated policy rulebook view",
        "lazy policy render-rulebook --write --format=json",
        "lazy policy retire-readiness --format=json",
        "lazy policy block-readiness --format=json",
        "lazy policy block-readiness --strict --format=json",
        "check-policy-block-runtime.py",
        "lazy policy audit --format=json",
    ):
        if expected not in policy_ssot:
            fail("Policy Registry SSOT missing invariant: " + expected)
    for forbidden in ("execSync", "appendJsonlStable"):
        if forbidden in policy_cli:
            fail("policy CLI first slice must stay read-only and non-enforcing; forbidden phrase: " + forbidden)
    for expected in ("Policy Machinery Option B", "Warn runtime requires --runtime=warn and never blocks", "Block runtime requires block-readiness evidence first", "policy render-rulebook --output must be a root-relative .lazy-harness/generated/ path", "Generated/explain view only", "canonical policy semantics live in .lazy-harness/ssot/policies.json", "policy-rulebook-retire-readiness/v1", "policy-block-readiness/v1", "Readiness/preflight only", "does not install or enable lifecycle hard-stop hooks"):
        if expected not in policy_cli:
            fail("policy CLI missing Option B explain boundary: " + expected)
    for expected in ("writeFileSync(outputPath, content", "requested.startsWith('.lazy-harness/generated/')", "GENERATED VIEW, NON-CANONICAL"):
        if expected not in policy_cli:
            fail("policy CLI missing generated rulebook constrained-write invariant: " + expected)
    for expected in ("policy-rulebook.md", "Canonical behavior policy semantics live in", "lazy policy render-rulebook --write", "Do not edit `policy-rulebook.md` as a source of truth"):
        if expected not in generated_readme:
            fail("generated README missing policy rulebook guidance: " + expected)
    for expected in ("never classifies raw user/assistant text", "policy_context", "WARN. Policy Machinery warn-only runtime", "acknowledgedPolicyWarnings"):
        if expected not in policy_warn_helper:
            fail("policy warn helper missing safety invariant: " + expected)
    if "STOP" in policy_warn_helper:
        fail("policy warn helper must never contain STOP output")
    if "last_user_message" in policy_warn_helper or "assistant_response" in policy_warn_helper:
        fail("policy warn helper must not inspect raw user/assistant text")
    for expected in ("never classifies raw user/assistant text", "blockRuntimeDryRun", "DRY-RUN STOP", "DRY-RUN ALLOW", "DRY-RUN BYPASS", "hard-stop is installed; this is review-only"):
        if expected not in policy_block_helper:
            fail("policy block dry-run helper missing safety invariant: " + expected)
    if "sys.exit(1)" in policy_block_helper or "raise SystemExit(1)" in policy_block_helper:
        fail("policy block dry-run helper must fail open and never exit nonzero")
    if "last_user_message" in policy_block_helper or "assistant_response" in policy_block_helper:
        fail("policy block dry-run helper must not inspect raw user/assistant text")
    for text, label in ((response_hook, "response.completed hook"), (lifecycle_check, "lifecycle-check orchestrator")):
        if "check-policy-warn-runtime.py" not in text:
            fail(label + " must include policy warn runtime helper")
        if "check-policy-block-runtime.py" not in text:
            fail(label + " must include policy block dry-run helper after explicit lifecycle dry-run integration")

    if "Capability kind and enforcement level are independent." not in capability_ssot:
        fail("Policy Machinery V2 depends on capability kind/level SSOT invariant")
    if ".lazy-harness/rules/**/*.md" not in rulebook_sdd or ".lazy-harness/ssot/capabilities.json" not in rulebook_sdd:
        fail("Policy Machinery V2 depends on hybrid rulebook + capability storage")

    policy_registry = json.loads(policy_registry_path.read_text(encoding="utf-8"))
    if policy_registry.get("version") != 1 or not isinstance(policy_registry.get("policies"), list):
        fail("Policy Registry must contain version=1 and policies array")
    policy_ids = [policy.get("id") for policy in policy_registry.get("policies", [])]
    if "record-first-validation" not in policy_ids:
        fail("Policy Registry missing record-first-validation seed policy")
    if "validation-evidence-warning" not in policy_ids:
        fail("Policy Registry missing validation-evidence-warning warn policy")
    if policy_ids != sorted(policy_ids):
        fail("Policy Registry policies must be deterministic id-sorted")
    policy_schema = json.loads(policy_schema_path.read_text(encoding="utf-8"))
    if policy_schema.get("title") != "Lazy Harness Policy Registry" or "policies" not in json.dumps(policy_schema, ensure_ascii=False):
        fail("Policy Registry schema metadata changed")

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture.get("schemaVersion") != "policy-machinery-v2/v1":
        fail("Policy Machinery V2 fixture schema mismatch")
    if fixture.get("id") != "record-first-validation":
        fail("Policy Machinery V2 fixture should use canonical policy id")
    if fixture.get("stage") not in {"turn", "edit", "commit", "push", "release", "high-risk-mutation"}:
        fail("Policy Machinery V2 fixture stage invalid: " + repr(fixture.get("stage")))
    if fixture.get("level") not in {"discover", "recommend", "default", "warn", "block"}:
        fail("Policy Machinery V2 fixture level invalid: " + repr(fixture.get("level")))
    if fixture.get("level") == "block":
        fail("Policy Machinery V2 static fixture must not use block level")
    source_record = fixture.get("sourceRecord")
    if not isinstance(source_record, str) or not source_record.startswith(".lazy-harness/") or ".." in pathlib.PurePosixPath(source_record).parts:
        fail("Policy Machinery V2 fixture sourceRecord must be root-relative .lazy-harness path")
    if not fixture.get("capabilityIds"):
        fail("Policy Machinery V2 fixture must link capability store")
    promotion = fixture.get("promotion", {})
    if promotion.get("requiresConfirmation") is not True:
        fail("Policy Machinery V2 fixture promotion must require confirmation")
    update_loop = fixture.get("updateLoop", {})
    if update_loop.get("eventType") not in {"policy-candidate", "policy-promotion", "policy-demotion"}:
        fail("Policy Machinery V2 fixture updateLoop eventType invalid")
    if update_loop.get("canonicalByPacketAlone") is not False:
        fail("Policy Machinery V2 fixture must not become canonical by packet alone")
    storage_decision = fixture.get("storageDecision", {})
    if storage_decision.get("requiresOptionGateBeforeMigration") is not False or storage_decision.get("current") != "typed-policy-canonical-plus-capability-bindings":
        fail("Policy Machinery V2 fixture must record user-confirmed Option B storage decision")

    allowed_evidence_kinds = {"record", "validation-output", "user-confirmation", "update-event"}
    for evidence in fixture.get("evidence", []):
        if evidence.get("kind") not in allowed_evidence_kinds:
            fail("Policy Machinery V2 fixture evidence kind invalid: " + json.dumps(evidence, ensure_ascii=False))
        path_value = evidence.get("path")
        if path_value:
            path_obj = pathlib.PurePosixPath(path_value)
            if path_obj.is_absolute() or ".." in path_obj.parts or not path_value.startswith(".lazy-harness/"):
                fail("Policy Machinery V2 fixture evidence path must stay root-relative .lazy-harness path: " + path_value)

    forbidden_fields = {"confidence", "intent", "risk", "requiredRead", "optionalRead", "nextAction", "candidateMeaning"}

    def walk(value: object, path: str = "fixture") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in forbidden_fields:
                    fail("Policy Machinery V2 fixture contains forbidden semantic-authority field: " + path + "." + key)
                walk(child, path + "." + str(key))
        elif isinstance(value, list):
            for idx, child in enumerate(value):
                walk(child, f"{path}[{idx}]")

    walk(fixture)

    for policy in policy_registry.get("policies", []):
        walk(policy, f"policy[{policy.get('id')}]")
        if policy.get("updateLoop", {}).get("canonicalByPacketAlone") is not False:
            fail("Policy Registry policy must not canonicalize by packet alone: " + repr(policy.get("id")))
        if policy.get("level") == "block" and policy.get("id") != "validation-evidence-block":
            fail("Policy Registry may only include the first approved validation-evidence block policy in this slice: " + repr(policy.get("id")))
        if policy.get("id") == "validation-evidence-block":
            runtime = policy.get("runtime", {})
            if runtime.get("blocks") is not True or runtime.get("requiresExplicitContext") is not True or runtime.get("fixture") != ".lazy-harness/tests/policy-block-validation-evidence.md":
                fail("validation-evidence-block must carry explicit block-readiness runtime metadata")
            if "block" not in policy.get("promotion", {}).get("allowedTargetLevels", []):
                fail("validation-evidence-block must be explicitly allowed to target block")
            evidence_kinds = {evidence.get("kind") for evidence in policy.get("evidence", [])}
            if not {"user-confirmation", "validation-output"}.issubset(evidence_kinds):
                fail("validation-evidence-block must include user-confirmation and validation-output evidence")
        if policy.get("sourceRecord") and not (ROOT / policy.get("sourceRecord")).exists():
            fail("Policy Registry policy sourceRecord missing: " + repr(policy.get("sourceRecord")))
        for evidence in policy.get("evidence", []):
            path_value = evidence.get("path")
            if path_value and not (ROOT / path_value).exists():
                fail("Policy Registry policy evidence path missing: " + repr(path_value))

    graph_path = LAZY / "knowledge" / "graph.jsonl"
    generated_record_index_path = LAZY / "generated" / "record-index.json"
    graph_before = graph_path.read_bytes() if graph_path.exists() else b""
    generated_before = generated_record_index_path.read_bytes() if generated_record_index_path.exists() else b""
    audit_result = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "audit", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if audit_result.returncode != 0:
        fail("lazy policy audit failed:\n" + audit_result.stdout + audit_result.stderr)
    audit_json = json.loads(audit_result.stdout)
    if audit_json.get("ok") is not True or audit_json.get("policies", 0) < 1:
        fail("lazy policy audit should pass and include at least one policy: " + audit_result.stdout)
    list_result = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "list", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if list_result.returncode != 0 or "record-first-validation" not in [policy.get("id") for policy in json.loads(list_result.stdout).get("policies", [])]:
        fail("lazy policy list should include record-first-validation:\n" + list_result.stdout + list_result.stderr)
    explain_json_result = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "explain", "--id", "record-first-validation", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if explain_json_result.returncode != 0:
        fail("lazy policy explain json failed:\n" + explain_json_result.stdout + explain_json_result.stderr)
    explain_json = json.loads(explain_json_result.stdout)
    if explain_json.get("canonicalSource") != ".lazy-harness/ssot/policies.json" or "Generated/explain view only" not in explain_json.get("policyBoundary", ""):
        fail("lazy policy explain json must identify canonical source and generated boundary: " + explain_json_result.stdout)
    explain_md_result = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "explain", "--id", "record-first-validation", "--format=md"], cwd=ROOT, text=True, capture_output=True, check=False)
    if explain_md_result.returncode != 0 or "Canonical source" not in explain_md_result.stdout or "Generated/explain view only" not in explain_md_result.stdout:
        fail("lazy policy explain md must render canonical source and generated boundary:\n" + explain_md_result.stdout + explain_md_result.stderr)
    resolve_result = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "resolve", "--stage", "turn", "--applies-to", "making_validation_claims", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if resolve_result.returncode != 0:
        fail("lazy policy resolve failed:\n" + resolve_result.stdout + resolve_result.stderr)
    resolve_json = json.loads(resolve_result.stdout)
    if resolve_json.get("schemaVersion") != "policy-resolve/v1" or resolve_json.get("enforcement") != "advisory-only":
        fail("lazy policy resolve must be advisory-only policy-resolve/v1: " + resolve_result.stdout)
    resolve_matches = resolve_json.get("matches", [])
    if "record-first-validation" not in [match.get("id") for match in resolve_matches]:
        fail("lazy policy resolve should match record-first-validation for making_validation_claims: " + resolve_result.stdout)
    for match in resolve_matches:
        if match.get("level") in {"warn", "block"}:
            fail("lazy policy resolve must not surface warn/block levels in advisory slice: " + resolve_result.stdout)
        if match.get("enforcement") != "advisory-only" or match.get("recommendedAction") != "surface-guidance":
            fail("lazy policy resolve match must be advisory-only surface-guidance: " + resolve_result.stdout)
    invalid_max_level = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "resolve", "--max-level", "warn", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if invalid_max_level.returncode == 0:
        fail("lazy policy resolve must reject warn/block max-level in advisory slice")
    warn_resolve_result = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "resolve", "--runtime", "warn", "--stage", "turn", "--applies-to", "making_validation_claims", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if warn_resolve_result.returncode != 0:
        fail("lazy policy resolve --runtime warn failed:\n" + warn_resolve_result.stdout + warn_resolve_result.stderr)
    warn_resolve = json.loads(warn_resolve_result.stdout)
    if warn_resolve.get("enforcement") != "warn-only" or warn_resolve.get("runtime") != "warn":
        fail("warn runtime resolver must be warn-only: " + warn_resolve_result.stdout)
    warn_matches = warn_resolve.get("matches", [])
    if "validation-evidence-warning" not in [match.get("id") for match in warn_matches]:
        fail("warn runtime resolver should surface validation-evidence-warning: " + warn_resolve_result.stdout)
    for match in warn_matches:
        if match.get("level") == "block" or match.get("enforcement") == "block":
            fail("warn runtime resolver must not surface block enforcement: " + warn_resolve_result.stdout)
    warn_helper_payload = json.dumps({"message_id": "policy-warn-fixture", "policy_context": {"stage": "turn", "appliesTo": ["making_validation_claims"]}}, ensure_ascii=False)
    warn_helper_result = subprocess.run([str(policy_warn_helper_path), warn_helper_payload], cwd=ROOT, text=True, capture_output=True, check=False)
    if warn_helper_result.returncode != 0:
        fail("policy warn helper should fail open with exit 0:\n" + warn_helper_result.stdout + warn_helper_result.stderr)
    if "WARN. Policy Machinery warn-only runtime" not in warn_helper_result.stdout or "validation-evidence-warning" not in warn_helper_result.stdout:
        fail("policy warn helper should emit warn-only output for explicit context:\n" + warn_helper_result.stdout)
    if "STOP" in warn_helper_result.stdout or "block" in warn_helper_result.stdout.lower().replace("not a block", ""):
        fail("policy warn helper must not emit blocking output:\n" + warn_helper_result.stdout)
    ack_payload = json.dumps({"message_id": "policy-warn-ack", "policy_context": {"stage": "turn", "appliesTo": ["making_validation_claims"], "acknowledgedPolicyWarnings": ["validation-evidence-warning"]}}, ensure_ascii=False)
    ack_result = subprocess.run([str(policy_warn_helper_path), ack_payload], cwd=ROOT, text=True, capture_output=True, check=False)
    if ack_result.returncode != 0 or ack_result.stdout.strip():
        fail("policy warn helper should stay silent for acknowledged warnings:\n" + ack_result.stdout + ack_result.stderr)
    raw_text_payload = json.dumps({"message_id": "policy-warn-raw", "last_user_message": "검증 완료라고 해", "assistant_response": "검증 완료"}, ensure_ascii=False)
    raw_text_result = subprocess.run([str(policy_warn_helper_path), raw_text_payload], cwd=ROOT, text=True, capture_output=True, check=False)
    if raw_text_result.returncode != 0 or raw_text_result.stdout.strip():
        fail("policy warn helper should stay silent without explicit policy_context:\n" + raw_text_result.stdout + raw_text_result.stderr)
    block_dry_run_payload = json.dumps({"message_id": "policy-block-dry-run", "policy_context": {"blockRuntimeDryRun": True, "stage": "turn", "appliesTo": ["claiming_validation_complete_without_evidence"]}}, ensure_ascii=False)
    block_dry_run_result = subprocess.run([str(policy_block_helper_path), block_dry_run_payload], cwd=ROOT, text=True, capture_output=True, check=False)
    if block_dry_run_result.returncode != 0:
        fail("policy block dry-run helper should fail open with exit 0:\n" + block_dry_run_result.stdout + block_dry_run_result.stderr)
    if "DRY-RUN STOP. Policy Machinery block runtime" not in block_dry_run_result.stdout or "validation-evidence-block" not in block_dry_run_result.stdout:
        fail("policy block dry-run helper should emit DRY-RUN STOP for explicit no-evidence block context:\n" + block_dry_run_result.stdout)
    if "No lifecycle hard-stop is installed" not in block_dry_run_result.stdout:
        fail("policy block dry-run helper must state no lifecycle hard-stop is installed:\n" + block_dry_run_result.stdout)
    block_allow_payload = json.dumps({"message_id": "policy-block-dry-run-allow", "policy_context": {"blockRuntimeDryRun": True, "stage": "turn", "appliesTo": ["claiming_validation_complete_without_evidence"], "validationEvidence": [".lazy-harness/bin/lazy test green"]}}, ensure_ascii=False)
    block_allow_result = subprocess.run([str(policy_block_helper_path), block_allow_payload], cwd=ROOT, text=True, capture_output=True, check=False)
    if block_allow_result.returncode != 0 or "DRY-RUN ALLOW. Policy Machinery block runtime" not in block_allow_result.stdout or "validation-evidence-block" not in block_allow_result.stdout:
        fail("policy block dry-run helper should emit DRY-RUN ALLOW when validation evidence is attached:\n" + block_allow_result.stdout + block_allow_result.stderr)
    block_bypass_payload = json.dumps({"message_id": "policy-block-dry-run-bypass", "policy_context": {"blockRuntimeDryRun": True, "stage": "turn", "appliesTo": ["claiming_validation_complete_without_evidence"], "acknowledgedPolicyBlocks": ["validation-evidence-block"], "policyBlockBypassReason": "reviewed dry-run bypass"}}, ensure_ascii=False)
    block_bypass_result = subprocess.run([str(policy_block_helper_path), block_bypass_payload], cwd=ROOT, text=True, capture_output=True, check=False)
    if block_bypass_result.returncode != 0 or "DRY-RUN BYPASS. Policy Machinery block runtime" not in block_bypass_result.stdout or "validation-evidence-block" not in block_bypass_result.stdout:
        fail("policy block dry-run helper should emit DRY-RUN BYPASS for explicit acknowledgement with reason:\n" + block_bypass_result.stdout + block_bypass_result.stderr)
    block_raw_text_payload = json.dumps({"message_id": "policy-block-raw", "last_user_message": "검증 완료", "assistant_response": "검증 완료"}, ensure_ascii=False)
    block_raw_text_result = subprocess.run([str(policy_block_helper_path), block_raw_text_payload], cwd=ROOT, text=True, capture_output=True, check=False)
    if block_raw_text_result.returncode != 0 or block_raw_text_result.stdout.strip():
        fail("policy block dry-run helper should stay silent without explicit policy_context:\n" + block_raw_text_result.stdout + block_raw_text_result.stderr)
    block_no_dry_run_payload = json.dumps({"message_id": "policy-block-no-dry", "policy_context": {"stage": "turn", "appliesTo": ["claiming_validation_complete_without_evidence"]}}, ensure_ascii=False)
    block_no_dry_run_result = subprocess.run([str(policy_block_helper_path), block_no_dry_run_payload], cwd=ROOT, text=True, capture_output=True, check=False)
    if block_no_dry_run_result.returncode != 0 or block_no_dry_run_result.stdout.strip():
        fail("policy block dry-run helper should stay silent unless blockRuntimeDryRun is explicit:\n" + block_no_dry_run_result.stdout + block_no_dry_run_result.stderr)
    render_md_result = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "render-rulebook", "--format=md"], cwd=ROOT, text=True, capture_output=True, check=False)
    if render_md_result.returncode != 0:
        fail("lazy policy render-rulebook md failed:\n" + render_md_result.stdout + render_md_result.stderr)
    for expected in ("# Generated Policy Rulebook", "GENERATED VIEW, NON-CANONICAL", "Canonical behavior policy source: `.lazy-harness/ssot/policies.json`", "project-operating-rulebook-policy", "record-first-validation", "validation-evidence-warning", "validation-evidence-block"):
        if expected not in render_md_result.stdout:
            fail("lazy policy render-rulebook md missing expected text: " + expected)
    render_json_result = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "render-rulebook", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if render_json_result.returncode != 0:
        fail("lazy policy render-rulebook json failed:\n" + render_json_result.stdout + render_json_result.stderr)
    render_json = json.loads(render_json_result.stdout)
    if render_json.get("schemaVersion") != "policy-rulebook-render/v1" or render_json.get("nonCanonical") is not True or render_json.get("canonicalSource") != ".lazy-harness/ssot/policies.json":
        fail("lazy policy render-rulebook json must identify non-canonical generated view: " + render_json_result.stdout)
    render_write_result = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "render-rulebook", "--write", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if render_write_result.returncode != 0:
        fail("lazy policy render-rulebook --write failed:\n" + render_write_result.stdout + render_write_result.stderr)
    render_write_json = json.loads(render_write_result.stdout)
    if render_write_json.get("wrote") is not True or render_write_json.get("outputPath") != ".lazy-harness/generated/policy-rulebook.md":
        fail("lazy policy render-rulebook --write must write default generated path: " + render_write_result.stdout)
    if not generated_rulebook_path.exists():
        fail("generated policy rulebook was not written")
    generated_rulebook = generated_rulebook_path.read_text(encoding="utf-8")
    if generated_rulebook != render_write_json.get("content"):
        fail("generated policy rulebook content must match render JSON content")
    if generated_rulebook != render_md_result.stdout:
        fail("generated policy rulebook content must match markdown render output")
    unsafe_output = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "render-rulebook", "--write", "--output", "../bad.md"], cwd=ROOT, text=True, capture_output=True, check=False)
    if unsafe_output.returncode == 0 or ".lazy-harness/generated/" not in unsafe_output.stderr:
        fail("lazy policy render-rulebook must reject output outside generated directory")
    retire_readiness = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "retire-readiness", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if retire_readiness.returncode != 0:
        fail("lazy policy retire-readiness non-strict should report without failing:\n" + retire_readiness.stdout + retire_readiness.stderr)
    retire_readiness_json = json.loads(retire_readiness.stdout)
    if retire_readiness_json.get("schemaVersion") != "policy-rulebook-retire-readiness/v1" or retire_readiness_json.get("ready") is not True:
        fail("current source should be rulebook-retire ready after active rulebook entries have typed policy links: " + retire_readiness.stdout)
    if "Readiness/preflight only" not in retire_readiness_json.get("boundary", "") or retire_readiness_json.get("counts", {}).get("blockers", -1) != 0:
        fail("retire-readiness must expose non-destructive boundary and zero blockers after source link: " + retire_readiness.stdout)
    if retire_readiness_json.get("counts", {}).get("coveredRulebookEntries") != 1 or not any(finding.get("path") == ".lazy-harness/rules/README.md" and finding.get("capabilityId") == "project-operating-rulebook" and finding.get("severity") == "info" for finding in retire_readiness_json.get("findings", [])):
        fail("retire-readiness should cover source rulebook README via project-operating-rulebook typed policy link: " + retire_readiness.stdout)
    strict_retire_readiness = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "retire-readiness", "--strict", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if strict_retire_readiness.returncode != 0:
        fail("lazy policy retire-readiness --strict should pass after source host typed policy link:\n" + strict_retire_readiness.stdout + strict_retire_readiness.stderr)
    strict_retire_json = json.loads(strict_retire_readiness.stdout)
    if strict_retire_json.get("ready") is not True or strict_retire_json.get("counts", {}).get("blockers") != 0:
        fail("strict retire-readiness should report ready source host with zero blockers: " + strict_retire_readiness.stdout)
    block_readiness = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "block-readiness", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if block_readiness.returncode != 0:
        fail("lazy policy block-readiness non-strict should report without failing:\n" + block_readiness.stdout + block_readiness.stderr)
    block_readiness_json = json.loads(block_readiness.stdout)
    if block_readiness_json.get("schemaVersion") != "policy-block-readiness/v1" or block_readiness_json.get("ready") is not True:
        fail("current source should be block-runtime ready after validation-evidence-block promotion evidence exists: " + block_readiness.stdout)
    if block_readiness_json.get("hardStopHookInstalled") is not False or block_readiness_json.get("lifecycleMutation") is not False:
        fail("block-readiness must not install lifecycle hard-stop hooks: " + block_readiness.stdout)
    if block_readiness_json.get("counts", {}).get("blockPolicies") != 1 or block_readiness_json.get("counts", {}).get("readyBlockPolicies") != 1 or block_readiness_json.get("counts", {}).get("blockers") != 0:
        fail("block-readiness should report exactly one ready source block policy and zero blockers: " + block_readiness.stdout)
    if not any(finding.get("policyId") == "validation-evidence-block" and finding.get("severity") == "info" for finding in block_readiness_json.get("findings", [])):
        fail("block-readiness should identify validation-evidence-block as ready: " + block_readiness.stdout)
    strict_block_readiness = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "block-readiness", "--strict", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if strict_block_readiness.returncode != 0:
        fail("lazy policy block-readiness --strict should pass after validation-evidence-block promotion evidence exists:\n" + strict_block_readiness.stdout + strict_block_readiness.stderr)
    strict_block_json = json.loads(strict_block_readiness.stdout)
    if strict_block_json.get("ready") is not True or strict_block_json.get("counts", {}).get("blockers") != 0:
        fail("strict block-readiness should report source ready with zero blockers: " + strict_block_readiness.stdout)
    with tempfile.TemporaryDirectory(prefix="policy-block-readiness-") as tmp:
        temp_root = pathlib.Path(tmp)
        (temp_root / ".lazy-harness/ssot").mkdir(parents=True, exist_ok=True)
        (temp_root / ".lazy-harness/spec/platform").mkdir(parents=True, exist_ok=True)
        (temp_root / ".lazy-harness/tests").mkdir(parents=True, exist_ok=True)
        (temp_root / ".lazy-harness/tests/block-policy.md").write_text("# Block policy fixture\n\nProves block and allow cases.\n", encoding="utf-8")
        (temp_root / ".lazy-harness/spec/platform/block-policy.md").write_text(
            """# Block Policy Fixture

Status: active
Layer: SDD

## Rule digest

- Status: active
- Scope: framework-global

## Hard-stop promotion

- Status: proposed
- Boundary: block fixture boundary only
- Scope: framework-global
- User confirmation: fixture user confirmed block boundary
- Evidence: high-risk fixture boundary with explicit validation
- Existing softer coverage: warn/runtime coverage existed and is insufficient for fixture
- Fixture: .lazy-harness/tests/block-policy.md
- Narrowness: only fixture applies_to token is covered
- Rollback: demote policy to warn or recommend
""",
            encoding="utf-8",
        )
        block_policy = {
            "id": "fixture-block-policy",
            "title": "Fixture block policy",
            "scope": "framework-global",
            "stage": "turn",
            "level": "block",
            "appliesTo": ["fixture_block_boundary"],
            "sourceRecord": ".lazy-harness/spec/platform/block-policy.md",
            "capabilityIds": [],
            "evidence": [
                {"kind": "user-confirmation", "summary": "Fixture user explicitly confirmed block boundary."},
                {"kind": "validation-output", "path": ".lazy-harness/tests/block-policy.md", "summary": "Fixture protects block and allow cases."},
            ],
            "promotion": {"requiresConfirmation": True, "allowedTargetLevels": ["block"]},
            "rollback": {"criteria": ["Fixture block policy becomes noisy."], "demotionTarget": "recommend"},
            "updateLoop": {"eventType": "policy-promotion", "canonicalByPacketAlone": False},
            "runtime": {"blocks": True, "requiresExplicitContext": True, "bypass": "Bypass only with explicit fixture acknowledgement.", "fixture": ".lazy-harness/tests/block-policy.md"},
            "explain": {"summary": "Fixture proves block readiness without installing hooks."},
        }
        (temp_root / ".lazy-harness/ssot/policies.json").write_text(json.dumps({"version": 1, "policies": [block_policy]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ready_block = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "block-readiness", "--target", str(temp_root), "--strict", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if ready_block.returncode != 0:
            fail("block-readiness strict should pass for complete promoted block fixture:\n" + ready_block.stdout + ready_block.stderr)
        ready_block_json = json.loads(ready_block.stdout)
        if ready_block_json.get("ready") is not True or ready_block_json.get("counts", {}).get("readyBlockPolicies") != 1 or ready_block_json.get("hardStopHookInstalled") is not False:
            fail("block-readiness positive fixture should be ready but non-mutating: " + ready_block.stdout)
        broken_block_policy = json.loads(json.dumps(block_policy))
        del broken_block_policy["runtime"]["fixture"]
        (temp_root / ".lazy-harness/ssot/policies.json").write_text(json.dumps({"version": 1, "policies": [broken_block_policy]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        broken_block = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "block-readiness", "--target", str(temp_root), "--strict", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if broken_block.returncode == 0:
            fail("block-readiness strict should fail when block runtime fixture is missing")
        broken_block_json = json.loads(broken_block.stdout)
        if not any("runtime.fixture" in finding.get("message", "") for finding in broken_block_json.get("findings", [])):
            fail("block-readiness missing fixture case should report runtime.fixture blocker: " + broken_block.stdout)
    with tempfile.TemporaryDirectory(prefix="policy-retire-readiness-") as tmp:
        temp_root = pathlib.Path(tmp)
        (temp_root / ".lazy-harness/rules").mkdir(parents=True, exist_ok=True)
        (temp_root / ".lazy-harness/ssot").mkdir(parents=True, exist_ok=True)
        (temp_root / ".lazy-harness/rules/dev-worktree.md").write_text(
            """# Dev Worktree Rule

Status: active
Layer: Rulebook
Scope: host-project
Owner: fixture
Level: warn
Related capability: dev-worktree-standard-command

## Rule digest

- Applies when:
  - creating_worktree
- Prefer:
  - `bun run wt new`
- Avoid:
  - raw `git worktree add`
- Bypass:
  - fixture bypass

## Operating rule

Use wrapper commands.

## Capability binding

Capability id: dev-worktree-standard-command

## Implementation map

Fixture implementation map.
""",
            encoding="utf-8",
        )
        ready_capabilities = {
            "version": 1,
            "capabilities": [
                {
                    "id": "dev-worktree-standard-command",
                    "kind": "command",
                    "level": "warn",
                    "sourceRecord": ".lazy-harness/rules/dev-worktree.md",
                    "rulebookRecord": ".lazy-harness/rules/dev-worktree.md",
                    "policyIds": ["dev-worktree-policy"],
                    "appliesWhen": ["creating_worktree"],
                    "description": "Fixture capability with typed policy coverage.",
                    "owner": "host-project",
                }
            ],
        }
        ready_policy = {
            "id": "dev-worktree-policy",
            "title": "Dev worktree policy",
            "scope": "host-project",
            "stage": "turn",
            "level": "warn",
            "appliesTo": ["creating_worktree"],
            "sourceRecord": ".lazy-harness/spec/platform/policy-machinery-v2.md",
            "capabilityIds": ["dev-worktree-standard-command"],
            "evidence": [{"kind": "record", "path": ".lazy-harness/tests/policy-machinery-v2.md", "summary": "Fixture evidence."}],
            "promotion": {"requiresConfirmation": True, "allowedTargetLevels": ["warn"]},
            "rollback": {"criteria": ["Fixture fails."], "demotionTarget": "recommend"},
            "updateLoop": {"eventType": "policy-promotion", "canonicalByPacketAlone": False},
            "explain": {"summary": "Fixture typed policy coverage.", "nonCanonicalViews": [".lazy-harness/rules/dev-worktree.md"]},
        }
        (temp_root / ".lazy-harness/ssot/capabilities.json").write_text(json.dumps(ready_capabilities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (temp_root / ".lazy-harness/ssot/policies.json").write_text(json.dumps({"version": 1, "policies": [ready_policy]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        ready_retire = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "retire-readiness", "--target", str(temp_root), "--strict", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if ready_retire.returncode != 0:
            fail("retire-readiness strict should pass when active rulebook entries have typed policy links:\n" + ready_retire.stdout + ready_retire.stderr)
        ready_retire_json = json.loads(ready_retire.stdout)
        if ready_retire_json.get("ready") is not True or ready_retire_json.get("counts", {}).get("coveredRulebookEntries") != 1:
            fail("retire-readiness positive fixture should be ready and cover one rule: " + ready_retire.stdout)
        broken_capabilities = json.loads(json.dumps(ready_capabilities))
        broken_capabilities["capabilities"][0]["policyIds"] = ["missing-policy"]
        (temp_root / ".lazy-harness/ssot/capabilities.json").write_text(json.dumps(broken_capabilities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        broken_retire = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "retire-readiness", "--target", str(temp_root), "--strict", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if broken_retire.returncode == 0:
            fail("retire-readiness strict should fail when capability references missing typed policy id")
        broken_retire_json = json.loads(broken_retire.stdout)
        if not any("missing typed policy id" in finding.get("message", "") for finding in broken_retire_json.get("findings", [])):
            fail("retire-readiness missing policy fixture should report missing typed policy id: " + broken_retire.stdout)
    with tempfile.TemporaryDirectory(prefix="policy-write-roundtrip-") as tmp:
        temp_root = pathlib.Path(tmp)
        required_fixture_paths = {
            ".lazy-harness/ssot/policies.json",
            ".lazy-harness/ssot/capabilities.json",
            ".lazy-harness/rules/README.md",
            ".lazy-harness/spec/platform/policy-machinery-v2.md",
            ".lazy-harness/spec/platform/guidance-ladder.md",
            ".lazy-harness/spec/platform/project-operating-rulebook.md",
            ".lazy-harness/ssot/policy-registry.md",
            ".lazy-harness/tests/policy-machinery-v2.md",
            ".lazy-harness/tests/policy-block-validation-evidence.md",
            ".lazy-harness/tests/project-operating-rulebook.md",
            ".lazy-harness/spec/platform/evidence-capsule-standard.md",
            ".lazy-harness/spec/platform/project-map-update-loop-v2.md",
            ".lazy-harness/generated/README.md",
        }
        for rel in required_fixture_paths:
            src = ROOT / rel
            dst = temp_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        policy_payload = {
            "id": "temp-write-roundtrip-policy",
            "title": "Temp write roundtrip policy",
            "scope": "framework-global",
            "stage": "turn",
            "level": "warn",
            "appliesTo": ["policy_write_roundtrip_fixture"],
            "sourceRecord": ".lazy-harness/spec/platform/policy-machinery-v2.md",
            "capabilityIds": [],
            "evidence": [
                {
                    "kind": "record",
                    "path": ".lazy-harness/tests/policy-machinery-v2.md",
                    "summary": "Temp fixture validates policy write roundtrip.",
                }
            ],
            "promotion": {"requiresConfirmation": True, "allowedTargetLevels": ["warn"]},
            "rollback": {"criteria": ["Temp fixture fails."], "demotionTarget": "recommend"},
            "updateLoop": {"eventType": "policy-candidate", "canonicalByPacketAlone": False},
            "explain": {"summary": "Temp write roundtrip summary."},
        }
        policy_input = temp_root / "policy.json"
        policy_input.write_text(json.dumps(policy_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        dry_upsert = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "upsert", "--target", str(temp_root), "--from-json", str(policy_input), "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if dry_upsert.returncode != 0:
            fail("lazy policy upsert dry-run failed:\n" + dry_upsert.stdout + dry_upsert.stderr)
        dry_upsert_json = json.loads(dry_upsert.stdout)
        if dry_upsert_json.get("wrote") is not False or dry_upsert_json.get("dryRun") is not True or dry_upsert_json.get("confirmRequiredToWrite") is not True:
            fail("lazy policy upsert without --confirm must be dry-run only: " + dry_upsert.stdout)
        if "temp-write-roundtrip-policy" in (temp_root / ".lazy-harness/ssot/policies.json").read_text(encoding="utf-8"):
            fail("lazy policy upsert dry-run must not write policies.json")
        saved_upsert = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "upsert", "--target", str(temp_root), "--from-json", str(policy_input), "--confirm", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if saved_upsert.returncode != 0:
            fail("lazy policy upsert --confirm failed:\n" + saved_upsert.stdout + saved_upsert.stderr)
        saved_upsert_json = json.loads(saved_upsert.stdout)
        if saved_upsert_json.get("wrote") is not True or saved_upsert_json.get("action") != "insert" or saved_upsert_json.get("canonicalTarget") != ".lazy-harness/ssot/policies.json":
            fail("lazy policy upsert --confirm must insert and write canonical registry: " + saved_upsert.stdout)
        saved_registry = json.loads((temp_root / ".lazy-harness/ssot/policies.json").read_text(encoding="utf-8"))
        saved_ids = [policy.get("id") for policy in saved_registry.get("policies", [])]
        if "temp-write-roundtrip-policy" not in saved_ids or saved_ids != sorted(saved_ids):
            fail("lazy policy upsert must persist deterministic id-sorted policy registry")
        replaced_payload = {**policy_payload, "title": "Temp write roundtrip policy replaced"}
        policy_input.write_text(json.dumps(replaced_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        replaced_upsert = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "upsert", "--target", str(temp_root), "--from-json", str(policy_input), "--confirm", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if replaced_upsert.returncode != 0 or json.loads(replaced_upsert.stdout).get("action") != "replace":
            fail("lazy policy upsert should replace existing id on second confirmed save:\n" + replaced_upsert.stdout + replaced_upsert.stderr)
        audit_temp = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "audit", "--target", str(temp_root), "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if audit_temp.returncode != 0 or json.loads(audit_temp.stdout).get("ok") is not True:
            fail("saved policy registry should audit cleanly:\n" + audit_temp.stdout + audit_temp.stderr)
        resolve_temp = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "resolve", "--target", str(temp_root), "--runtime", "warn", "--stage", "turn", "--applies-to", "policy_write_roundtrip_fixture", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if resolve_temp.returncode != 0:
            fail("saved policy should resolve in warn runtime:\n" + resolve_temp.stdout + resolve_temp.stderr)
        resolve_temp_json = json.loads(resolve_temp.stdout)
        if "temp-write-roundtrip-policy" not in [match.get("id") for match in resolve_temp_json.get("matches", [])]:
            fail("saved policy was not returned by warn resolver: " + resolve_temp.stdout)
        render_temp = subprocess.run([str(LAZY / "bin" / "lazy"), "policy", "render-rulebook", "--target", str(temp_root), "--write", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if render_temp.returncode != 0:
            fail("saved policy should render into generated rulebook:\n" + render_temp.stdout + render_temp.stderr)
        render_temp_json = json.loads(render_temp.stdout)
        if "temp-write-roundtrip-policy" not in render_temp_json.get("content", "") or not (temp_root / ".lazy-harness/generated/policy-rulebook.md").exists():
            fail("rendered generated rulebook must include saved policy")

        sync_host = temp_root / "sync-host"
        (sync_host / ".lazy-harness/ssot").mkdir(parents=True, exist_ok=True)
        (sync_host / ".lazy-harness/ssot/policies.json").write_text(json.dumps({"version": 1, "policies": [policy_payload]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        sync_result = subprocess.run(["bun", ".lazy-harness/scripts/lazy-sync.ts", "--from", str(ROOT), "--target", str(sync_host), "--force", "--quiet"], cwd=ROOT, text=True, capture_output=True, check=False)
        if sync_result.returncode != 0:
            fail("lazy-sync policy seed merge roundtrip failed:\n" + sync_result.stdout + sync_result.stderr)
        merged_registry = json.loads((sync_host / ".lazy-harness/ssot/policies.json").read_text(encoding="utf-8"))
        merged_ids = {policy.get("id") for policy in merged_registry.get("policies", [])}
        for expected_id in ("temp-write-roundtrip-policy", "record-first-validation", "validation-evidence-warning"):
            if expected_id not in merged_ids:
                fail("lazy-sync policy seed merge must preserve host policy and merge framework seed: " + expected_id)
    help_text = subprocess.check_output([str(LAZY / "bin" / "lazy"), "help"], cwd=ROOT, text=True)
    if "policy list|audit|explain|resolve|render-rulebook|upsert|retire-readiness|block-readiness" not in help_text:
        fail("lazy help must advertise policy command")
    if graph_path.exists() and graph_path.read_bytes() != graph_before:
        fail("lazy policy CLI must not mutate graph.jsonl")
    if generated_record_index_path.exists() and generated_record_index_path.read_bytes() != generated_before:
        fail("lazy policy CLI must not mutate generated record-index cache")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    category_a = json.dumps(manifest.get("categories", {}).get("A", {}).get("items", []), ensure_ascii=False)
    for expected in (
        "spec/platform/policy-machinery-v2.md",
        ".gitignore",
        "framework/operational-adrs/0046-policy-machinery-typed-policy-canonical.md",
        "ssot/policy-registry.md",
        "ssot/policies.json",
        "schemas/",
        "*.schema.json",
        "scripts/",
        "*.ts",
        "tests/policy-machinery-v2.md",
        "planning/policy-machinery-v2-baseline-gap-audit.md",
        "spec/platform/project-operating-rulebook.md",
        "fixtures/policy-machinery-v2/",
        "*.json",
    ):
        if expected not in category_a:
            fail("init categories missing Policy Machinery V2 sync asset: " + expected)

    print("✓ Policy Machinery V2 static contract ok")


def check_evidence_capsule_standard_phase5() -> None:
    """Phase 5 should provide a manual evidence capsule checklist without auto-writing."""
    sdd_path = LAZY / "spec" / "platform" / "evidence-capsule-standard.md"
    tdd_path = LAZY / "tests" / "evidence-capsule-standard.md"
    readme_path = LAZY / "evidence" / "README.md"
    template_path = LAZY / "templates" / "evidence-capsule.md"
    registry_path = LAZY / "ssot" / "capabilities.json"

    for path in (sdd_path, tdd_path, readme_path, template_path, registry_path):
        if not path.exists():
            fail(f"evidence capsule Phase 5 missing file: {path.relative_to(ROOT)}")

    sdd = sdd_path.read_text(encoding="utf-8")
    for expected in (
        "keep evidence capsules optional and human-authored; do not auto-write them from hooks",
        "The checklist is recommend-level, not a hard gate.",
        "In the framework source checkout, `.lazy-harness/ssot/capabilities.json` registers `lazy-evidence-capsule`",
        "Downstream host capability registries are host-owned",
        "check_evidence_capsule_standard_phase5",
    ):
        if expected not in sdd:
            fail("evidence capsule SDD missing invariant: " + expected)

    tdd = tdd_path.read_text(encoding="utf-8")
    for expected in (
        "Missing heading",
        "downstream host scope, absence is allowed",
        "Auto-writing evidence capsules from lifecycle hooks fails self-test",
        "Layer completeness gate",
    ):
        if expected not in tdd:
            fail("evidence capsule TDD missing regression/impact note: " + expected)

    template = template_path.read_text(encoding="utf-8")
    required_headings = [
        "# Evidence: <topic>",
        "## Scope",
        "## Environment",
        "## Commands",
        "## Results",
        "## Interpretation",
        "## Reproduce",
        "## Related records",
        "## Retention / privacy",
    ]
    missing_headings = [heading for heading in required_headings if heading not in template]
    if missing_headings:
        fail("evidence capsule template missing headings: " + json.dumps(missing_headings, ensure_ascii=False))
    template_lower = template.lower()
    for expected in ("secrets", "credentials", "personal data", "raw transcripts", "raw assistant responses", "excessive raw logs"):
        if expected not in template_lower:
            fail("evidence capsule template missing privacy warning phrase: " + expected)

    readme = readme_path.read_text(encoding="utf-8")
    for expected in (
        "Capsules are manually authored",
        "supporting evidence, not canonical truth",
        "Redact secrets, credentials, personal data, raw transcripts",
    ):
        if expected not in readme:
            fail("evidence capsule README missing guidance: " + expected)

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    caps = {cap.get("id"): cap for cap in registry.get("capabilities", [])}
    cap = caps.get("lazy-evidence-capsule")
    if not cap and ACTIVE_SCOPE == "framework":
        fail("framework-source capabilities registry missing lazy-evidence-capsule")
    expected_cap = {
        "kind": "checklist",
        "level": "recommend",
        "sourceRecord": ".lazy-harness/spec/platform/evidence-capsule-standard.md",
        "checklistPath": ".lazy-harness/templates/evidence-capsule.md",
        "owner": "framework-global",
    }
    if cap:
        for key, value in expected_cap.items():
            if cap.get(key) != value:
                fail(f"lazy-evidence-capsule capability {key} mismatch: {cap.get(key)!r}")
        if cap.get("level") in {"warn", "block"}:
            fail("lazy-evidence-capsule must remain non-blocking recommend-level")
        if "making_validation_claims" not in cap.get("appliesWhen", []):
            fail("lazy-evidence-capsule missing making_validation_claims appliesWhen")

    audit = subprocess.run([".lazy-harness/bin/lazy", "capability", "audit", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if audit.returncode != 0:
        fail("capability audit failed for current host registry:\n" + audit.stdout + audit.stderr)
    audit_json = json.loads(audit.stdout)
    if audit_json.get("ok") is not True:
        fail("capability audit should pass for current host registry: " + json.dumps(audit_json, ensure_ascii=False))

    if cap:
        resolved = subprocess.run([".lazy-harness/bin/lazy", "capability", "resolve", "--intent", "making_validation_claims", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
        if resolved.returncode != 0:
            fail("capability resolve failed for evidence capsule intent:\n" + resolved.stdout + resolved.stderr)
        resolved_ids = [item.get("id") for item in json.loads(resolved.stdout).get("matches", [])]
        if "lazy-evidence-capsule" not in resolved_ids:
            fail("capability resolve should recommend lazy-evidence-capsule when registered: " + resolved.stdout)

    manifest = json.loads((LAZY / "manifests" / "init-categories.json").read_text(encoding="utf-8"))
    category_a = json.dumps(manifest.get("categories", {}).get("A", {}).get("items", []), ensure_ascii=False)
    for expected in (
        "spec/platform/evidence-capsule-standard.md",
        "tests/evidence-capsule-standard.md",
        "evidence-capsule.md",
        "evidence/",
    ):
        if expected not in category_a:
            fail("init categories missing evidence capsule sync asset: " + expected)

    forbidden_auto_write = ("evidence-capsule.md", ".lazy-harness/evidence/", "lazy-evidence-capsule")
    hook_files = list((LAZY / "hooks").rglob("*.sh")) + list((LAZY / "hooks").rglob("*.py"))
    offenders: list[str] = []
    for hook in hook_files:
        text = hook.read_text(encoding="utf-8")
        if any(phrase in text for phrase in forbidden_auto_write):
            offenders.append(str(hook.relative_to(ROOT)))
    if offenders:
        fail("hooks must not auto-write or invoke evidence capsules: " + json.dumps(offenders, ensure_ascii=False))

    print("✓ evidence capsule standard Phase 5 ok")




def check_record_decision_broker_phase8() -> None:
    """Phase 8 should define a safe post-turn Record Decision Packet contract before runtime escalation."""
    sdd_path = LAZY / "spec" / "platform" / "record-decision-broker.md"
    tdd_path = LAZY / "tests" / "record-decision-broker.md"
    schema_path = LAZY / "schemas" / "record-decision-packet.schema.json"
    generator_path = LAZY / "scripts" / "record-decision-broker.ts"
    manifest_path = LAZY / "manifests" / "init-categories.json"
    for path in [sdd_path, tdd_path, schema_path, generator_path]:
        if not path.exists():
            fail("Record Decision Broker Phase 8 artifact missing: " + str(path))

    sdd_text = sdd_path.read_text(encoding="utf-8")
    for phrase in [
        "## Rule digest",
        "Record Decision Packet",
        "record-updated",
        "candidate-needed",
        "no-record-needed",
        "option-gate-needed",
        "deferred",
        "no automatic blind record writes",
        "Response shadow bridge",
        "MultiCandidate Packet",
        "check-record-decision-shadow.py",
        "Search/read evidence is pre-turn read evidence",
        "recommendedRecords must preserve every distinct candidate",
        "`--message` display/summary-only",
        "Do not write automatically from this packet alone",
        "`.lazy-harness/scripts/record-decision-broker.ts`",
        "Implementation map",
    ]:
        if phrase not in sdd_text:
            fail("Record Decision Broker SDD missing phrase: " + phrase)

    generator_text = generator_path.read_text(encoding="utf-8")
    if "looksExplanationOnly" in generator_text or "status|summary|explain" in generator_text:
        fail("record-decision-broker must not classify raw --message text with semantic regex")

    tdd_text = tdd_path.read_text(encoding="utf-8")
    for phrase in [
        "Clean explanation turn",
        "Confirmed new alias",
        "Ambiguous layer placement",
        "Same-turn record update",
        "Multiple missing candidates",
        "Deferred by user",
        "generator and response shadow fixtures",
        "check_record_decision_shadow_response_completed",
        "check_record_decision_broker_phase8",
    ]:
        if phrase not in tdd_text:
            fail("Record Decision Broker TDD missing phrase: " + phrase)

    manifest = manifest_path.read_text(encoding="utf-8")
    if "spec/platform/record-decision-broker.md" not in manifest:
        fail("init-categories manifest must sync Record Decision Broker SDD")
    if "tests/record-decision-broker.md" not in manifest:
        fail("init-categories manifest must sync Record Decision Broker TDD fixture")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("title") != "RecordDecisionPacket":
        fail("Record Decision Packet schema title mismatch")
    required = set(schema.get("required", []))
    expected_top = {"schemaVersion", "generatedAt", "recordDecision"}
    if not expected_top.issubset(required):
        fail("Record Decision Packet schema missing top-level fields: " + json.dumps(sorted(expected_top - required)))
    definitions = schema.get("definitions", {})
    dispositions = set(definitions.get("disposition", {}).get("enum", []))
    expected_dispositions = {"record-updated", "candidate-needed", "no-record-needed", "option-gate-needed", "deferred"}
    if dispositions != expected_dispositions:
        fail("Record Decision Packet dispositions mismatch: " + json.dumps(sorted(dispositions)))
    evidence_kinds = set(definitions.get("evidenceKind", {}).get("enum", []))
    for expected in ["user-confirmation", "user-correction", "changed-file", "changed-record", "context-delivery-required-read", "response-audit-advisory", "validation", "no-op"]:
        if expected not in evidence_kinds:
            fail("Record Decision Packet missing evidence kind: " + expected)
    actions = set(definitions.get("recordAction", {}).get("enum", []))
    for expected in ["update", "create", "append", "candidate", "none", "ask-option-gate"]:
        if expected not in actions:
            fail("Record Decision Packet missing record action: " + expected)
    triggers = set(definitions.get("trigger", {}).get("enum", []))
    for expected in ["new-alias-found", "validation-only", "explanation-only", "ambiguous-placement", "user-deferred"]:
        if expected not in triggers:
            fail("Record Decision Packet missing trigger: " + expected)

    decision_required = set(definitions.get("recordDecision", {}).get("required", []))
    expected_decision_fields = {"disposition", "confidence", "trigger", "summary", "evidence", "recommendedRecords", "instructions"}
    if not expected_decision_fields.issubset(decision_required):
        fail("recordDecision schema missing fields: " + json.dumps(sorted(expected_decision_fields - decision_required)))
    if definitions.get("recordDecision", {}).get("properties", {}).get("recommendedRecords", {}).get("maxItems") != 20:
        fail("recordDecision recommendedRecords must cap multi-candidate packets at 20")

    samples = [
        {
            "schemaVersion": "1.0",
            "generatedAt": "2026-06-01T00:00:00.000Z",
            "recordDecision": {
                "disposition": "candidate-needed",
                "confidence": 0.74,
                "trigger": "new-alias-found",
                "summary": "User confirmed a new surface alias.",
                "evidence": [{"kind": "user-confirmation", "summary": "Alias confirmed.", "confidence": 0.9}],
                "recommendedRecords": [{"path": ".lazy-harness/behavior/feature-surface.md", "layer": "BDD", "action": "update", "reason": "Alias should be captured.", "confidence": 0.8}],
                "instructions": ["Do not write automatically from this packet alone."],
            },
        },
        {
            "schemaVersion": "1.0",
            "generatedAt": "2026-06-01T00:00:00.000Z",
            "recordDecision": {
                "disposition": "no-record-needed",
                "confidence": 0.86,
                "trigger": "explanation-only",
                "summary": "Read-only explanation produced no durable fact.",
                "evidence": [{"kind": "no-op", "summary": "No files or records changed.", "confidence": 0.9}],
                "recommendedRecords": [{"action": "none", "reason": "No durable record action needed.", "confidence": 0.86}],
                "instructions": ["Keep response.completed silent."],
            },
        },
        {
            "schemaVersion": "1.0",
            "generatedAt": "2026-06-01T00:00:00.000Z",
            "recordDecision": {
                "disposition": "option-gate-needed",
                "confidence": 0.61,
                "trigger": "ambiguous-placement",
                "summary": "Evidence suggests a record may be needed but layer is ambiguous.",
                "evidence": [{"kind": "tool-call", "summary": "Changed mapped files but layer is unclear.", "confidence": 0.62}],
                "recommendedRecords": [{"action": "ask-option-gate", "reason": "Choose DDD/SDD/BDD/TDD/ADR/SSOT before mutating records.", "confidence": 0.7}],
                "instructions": ["Ask 3-5 options before writing records."],
            },
        },
    ]
    for sample in samples:
        decision = sample.get("recordDecision", {})
        for field in expected_top:
            if field not in sample:
                fail("sample Record Decision Packet missing top-level field: " + field)
        for field in expected_decision_fields:
            if field not in decision:
                fail("sample recordDecision missing field: " + field)
        if decision.get("disposition") not in expected_dispositions:
            fail("sample recordDecision invalid disposition")
        if decision.get("trigger") not in triggers:
            fail("sample recordDecision invalid trigger")
        if not 0 <= float(decision.get("confidence", -1)) <= 1:
            fail("sample recordDecision confidence must be 0..1")
        for evidence in decision.get("evidence", []):
            if evidence.get("kind") not in evidence_kinds:
                fail("sample recordDecision invalid evidence kind")
        for recommendation in decision.get("recommendedRecords", []):
            if recommendation.get("action") not in actions:
                fail("sample recordDecision invalid action")

    def run_generator(*args: str) -> dict:
        completed = subprocess.run(
            ["bun", str(generator_path), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            fail("record-decision-broker generator failed:\n" + completed.stdout + completed.stderr)
        try:
            return json.loads(completed.stdout)
        except Exception as exc:
            fail("record-decision-broker generator output was not JSON: " + str(exc) + "\n" + completed.stdout)

    generated_cases = [
        (
            run_generator("--message", "상태 요약", "--read-only"),
            "no-record-needed",
            "explanation-only",
            "none",
        ),
        (
            run_generator("--message", "기능패널은 feature panel", "--user-confirmation", "기능패널 alias confirmed"),
            "candidate-needed",
            "new-alias-found",
            "candidate",
        ),
        (
            run_generator("--message", "layer unclear", "--changed-file", "src/app.ts", "--ambiguous"),
            "option-gate-needed",
            "ambiguous-placement",
            "ask-option-gate",
        ),
        (
            run_generator("--message", "record updated", "--changed-record", ".lazy-harness/spec/platform/record-decision-broker.md"),
            "record-updated",
            "contract-change",
            "update",
        ),
    ]
    for packet, expected_disposition, expected_trigger, expected_action in generated_cases:
        decision = packet.get("recordDecision", {})
        if decision.get("disposition") != expected_disposition:
            fail(f"generator disposition mismatch: expected {expected_disposition}, got {decision.get('disposition')}\n{json.dumps(packet, ensure_ascii=False, indent=2)}")
        if decision.get("trigger") != expected_trigger:
            fail(f"generator trigger mismatch: expected {expected_trigger}, got {decision.get('trigger')}")
        if not decision.get("evidence") or not decision.get("recommendedRecords") or not decision.get("instructions"):
            fail("generator packet missing evidence/recommendations/instructions")
        actions_seen = {item.get("action") for item in decision.get("recommendedRecords", []) if isinstance(item, dict)}
        if expected_action not in actions_seen:
            fail(f"generator recommended action mismatch: expected {expected_action}, got {sorted(actions_seen)}")
        notes = packet.get("notes", [])
        if "mutationAllowed=false" not in notes or "runtimeMutationIntegration=false" not in notes or "runtimeDefaultOutput=false" not in notes:
            fail("generator packet must state mutation/hook safety notes")

    multi_packet = run_generator(
        "--message", "multi candidate evidence",
        "--changed-file", "src/features/reservation/ReservationPanel.tsx",
        "--changed-file", "src/api/reservations/route.ts",
        "--changed-test", "tests/reservation.spec.ts",
        "--response-audit-advisory", "record gap repeated across dogfood turns",
    )
    multi_decision = multi_packet.get("recordDecision", {})
    multi_records = [item for item in multi_decision.get("recommendedRecords", []) if isinstance(item, dict)]
    multi_layers = {item.get("layer") for item in multi_records}
    for expected_layer in ["BDD", "SDD", "TDD", "Knowledge"]:
        if expected_layer not in multi_layers:
            fail("multi-candidate generator should preserve layer " + expected_layer + ": " + json.dumps(multi_records, ensure_ascii=False, indent=2))
    if len(multi_records) < 4 or len(multi_records) > 20:
        fail("multi-candidate generator should preserve all distinct candidates with max 20 cap: " + json.dumps(multi_records, ensure_ascii=False, indent=2))
    if any(item.get("action") == "update" for item in multi_records):
        fail("multi-candidate generator must not propose canonical update without record-updated evidence: " + json.dumps(multi_records, ensure_ascii=False, indent=2))

    message_only = run_generator("--message", "사용자가 신규 별칭을 확인했다고 쓰여 있어도 flag 없이는 의미판단 금지")
    if message_only.get("recordDecision", {}).get("disposition") != "no-record-needed":
        fail("message-only generator call should not infer candidate-needed from raw text: " + json.dumps(message_only, ensure_ascii=False, indent=2))
    if message_only.get("recordDecision", {}).get("evidence", [{}])[0].get("kind") != "no-op":
        fail("message-only generator call should remain no-op evidence without explicit flags: " + json.dumps(message_only, ensure_ascii=False, indent=2))

    md_completed = subprocess.run(
        ["bun", str(generator_path), "--message", "상태 요약", "--read-only", "--format", "md"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if md_completed.returncode != 0 or "# Record Decision Packet" not in md_completed.stdout or "Disposition: no-record-needed" not in md_completed.stdout:
        fail("record-decision-broker markdown output missing expected content:\n" + md_completed.stdout + md_completed.stderr)
    print("✓ record decision broker Phase 8 ok")



def check_record_decision_shadow_response_completed() -> None:
    """response.completed Record Decision shadow bridge should journal safely and stay silent by default."""
    helper_src = LAZY / "hooks" / "lifecycle" / "helpers" / "check-record-decision-shadow.py"
    generator_src = LAZY / "scripts" / "record-decision-broker.ts"
    if not helper_src.exists() or not generator_src.exists():
        fail("Record Decision shadow helper/generator missing")
    hook_text = (LAZY / "hooks" / "lifecycle" / "on-response-completed.sh").read_text(encoding="utf-8")
    orchestrator_text = (LAZY / "scripts" / "lifecycle-check.py").read_text(encoding="utf-8")
    if "check-record-decision-shadow.py" not in hook_text:
        fail("response.completed hook must include Record Decision shadow helper")
    if "check-record-decision-shadow.py" not in orchestrator_text:
        fail("lifecycle-check orchestrator must include Record Decision shadow helper")

    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-record-decision-shadow-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        (temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "scripts").mkdir(parents=True, exist_ok=True)
        helper = temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers" / "check-record-decision-shadow.py"
        runtime_helper = temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers" / "runtime_paths.py"
        generator = temp / ".lazy-harness" / "scripts" / "record-decision-broker.ts"
        shutil.copy2(helper_src, helper)
        shutil.copy2(LAZY / "hooks" / "lifecycle" / "helpers" / "runtime_paths.py", runtime_helper)
        shutil.copy2(generator_src, generator)
        helper.chmod(0o755)

        def run_helper(payload: dict, advisory: bool = False) -> str:
            env = env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp))
            if advisory:
                env["LAZY_RECORD_DECISION_SHADOW_ADVISORY"] = "1"
            result = subprocess.run(
                [str(helper), json.dumps(payload, ensure_ascii=False)],
                cwd=temp,
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            if result.returncode != 0:
                fail("Record Decision shadow helper must exit 0:\n" + result.stdout + result.stderr)
            return result.stdout

        def last_row() -> dict:
            journal = runtime_open_gates_file(temp).parent / "record-decision-packets.jsonl"
            if not journal.exists():
                fail("Record Decision shadow helper should write journal")
            rows = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not rows:
                fail("Record Decision shadow journal should contain rows")
            return rows[-1]

        clean = run_helper({"message_id": "clean", "recent_tool_calls": [{"name": "read", "args_preview": "README.md"}]})
        if clean.strip():
            fail("Record Decision shadow should stay silent for read-only clean turn:\n" + clean)
        row = last_row()
        if row.get("disposition") != "no-record-needed" or row.get("trigger") != "explanation-only":
            fail("read-only shadow row should be no-record-needed: " + json.dumps(row, ensure_ascii=False))
        if "README.md" not in json.dumps(row, ensure_ascii=False):
            fail("read-only row should preserve path/tool evidence where safe")

        candidate = run_helper({"message_id": "candidate", "recent_tool_calls": [{"name": "Edit", "args_preview": "src/features/example-feature/FeaturePanel.tsx"}]})
        if candidate.strip():
            fail("Record Decision shadow should stay silent by default even for candidate-needed:\n" + candidate)
        row = last_row()
        if row.get("disposition") != "candidate-needed" or row.get("trigger") not in {"behavior-change", "source-change"}:
            fail("source edit shadow row should be candidate-needed: " + json.dumps(row, ensure_ascii=False))

        multi_candidate = run_helper({"message_id": "multi-candidate", "recent_tool_calls": [{"name": "Edit", "args_preview": "src/features/reservation/ReservationPanel.tsx src/api/reservations/route.ts tests/reservation.spec.ts"}]})
        if multi_candidate.strip():
            fail("Record Decision shadow should stay silent by default for multi-candidate packets:\n" + multi_candidate)
        row = last_row()
        if row.get("disposition") != "candidate-needed":
            fail("multi-candidate shadow row should be candidate-needed: " + json.dumps(row, ensure_ascii=False))
        layers = set(row.get("candidateLayers") or [])
        for expected_layer in ["BDD", "SDD", "TDD", "Knowledge"]:
            if expected_layer not in layers:
                fail("multi-candidate shadow row should preserve layer " + expected_layer + ": " + json.dumps(row, ensure_ascii=False, indent=2))
        if int(row.get("recommendedRecordCount") or 0) < 4 or len(row.get("recommendedRecords") or []) < 4:
            fail("multi-candidate shadow row should preserve all recommendations, not just one: " + json.dumps(row, ensure_ascii=False, indent=2))

        advisory = run_helper({"message_id": "candidate-advisory", "recent_tool_calls": [{"name": "Edit", "args_preview": "src/features/example-feature/FeaturePanel.tsx"}]}, advisory=True)
        if "ADVISORY. Record Decision shadow" not in advisory or "STOP" in advisory:
            fail("Record Decision shadow advisory should be ADVISORY-only:\n" + advisory)

        option = run_helper({"message_id": "ambiguous", "last_user_message": "그거 고쳐줘", "recent_tool_calls": [{"name": "Edit", "args_preview": "src/features/example-feature/FeaturePanel.tsx"}]}, advisory=True)
        if "option gate" in option or "option-gate" in option:
            fail("Record Decision shadow must not infer option-gate from raw user text:\n" + option)
        row = last_row()
        serialized = json.dumps(row, ensure_ascii=False)
        if row.get("disposition") != "candidate-needed" or "그거 고쳐줘" in serialized:
            fail("ambiguous raw user text should not affect shadow disposition or be stored: " + serialized)

        helper_text = helper.read_text(encoding="utf-8")
        for forbidden_code in ["AMBIGUOUS_RE", "payload_text(", "--ambiguous"]:
            if forbidden_code in helper_text:
                fail("Record Decision shadow helper must not classify raw user text: " + forbidden_code)

        record_updated = run_helper({"message_id": "record", "recent_tool_calls": [{"name": "Edit", "args_preview": ".lazy-harness/spec/platform/record-decision-broker.md"}]}, advisory=True)
        if record_updated.strip():
            fail("Record Decision shadow should stay silent when record-updated evidence exists:\n" + record_updated)
        row = last_row()
        if row.get("disposition") != "record-updated":
            fail("record edit shadow row should be record-updated: " + json.dumps(row, ensure_ascii=False))
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ record decision shadow response.completed ok")


def check_message_received_hook_context_injection() -> None:
    """message.received hook should emit a static inventory/search packet and journal search-debt."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-message-received-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        (temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers").mkdir(parents=True, exist_ok=True)
        hook = temp / ".lazy-harness" / "hooks" / "lifecycle" / "on-message-received.sh"
        shutil.copy2(LAZY / "hooks" / "lifecycle" / "on-message-received.sh", hook)
        hook.chmod(0o755)
        shutil.copy2(LAZY / "hooks" / "lifecycle" / "helpers" / "runtime-paths.sh", temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers" / "runtime-paths.sh")
        shutil.copy2(LAZY / "hooks" / "lifecycle" / "helpers" / "runtime_paths.py", temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers" / "runtime_paths.py")

        static_payloads = [
            {
                "event": "message.received",
                "session_id": "s-test",
                "message_id": "m-smalltalk",
                "working_dir": str(temp),
                "last_user_message": "안녕",
                "recent_tool_calls": [],
                "turn_count": 1,
            },
            {
                "event": "message.received",
                "session_id": "s-test",
                "message_id": "m-surface",
                "working_dir": str(temp),
                "last_user_message": "기능패널 고쳐줘",
                "recent_tool_calls": [],
                "turn_count": 2,
            },
        ]
        rendered: list[tuple[dict, str, str]] = []
        for payload in static_payloads:
            completed = subprocess.run(
                [str(hook)],
                cwd=temp,
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                capture_output=True,
                check=False,
                env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            )
            if completed.returncode != 0:
                fail("message.received hook should fail-open with exit 0:\n" + completed.stdout + completed.stderr)
            output = completed.stdout.strip()
            if not output:
                fail("message.received hook should emit static harness inventory/search inject JSON for any user message")
            data = json.loads(output)
            rendered.append((payload, output, data.get("inject", {}).get("body", "")))

        smalltalk_payload, smalltalk_output, smalltalk_body = rendered[0]
        payload, output, body = rendered[1]
        if smalltalk_body != body:
            fail("message.received hook body must be static and not vary by user text:\n--- smalltalk ---\n" + smalltalk_output + "\n--- surface ---\n" + output)

        empty_payload = {
            "event": "message.received",
            "session_id": "s-test",
            "message_id": "m-empty",
            "working_dir": str(temp),
            "last_user_message": "",
            "recent_tool_calls": [],
            "turn_count": 3,
        }
        empty = subprocess.run(
            [str(hook)],
            cwd=temp,
            input=json.dumps(empty_payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
        )
        if empty.returncode != 0 or empty.stdout.strip():
            fail("message.received hook should stay silent only when no user message exists:\n" + empty.stdout + empty.stderr)

        non_space = re.sub(r"\s+", "", body)
        token_estimate = max(len(re.findall(r"\S+", body)), (len(non_space) + 5) // 6 if non_space else 0)
        if token_estimate > 600:
            fail(f"compact message.received prompt too large: {token_estimate} estimated tokens > 600\n" + output)

        for phrase in [
            "REMINDER. Harness-first search/read debt before response.",
            "harness-first-static",
            "static transport; no user-text classification; no CLI/index semantic authority",
            "choose an explicit retrieval purpose",
            "inspect real `.lazy-harness`/source/test evidence in this host root",
            "Inventory counts:",
            "DDD=",
            "SDD=",
            "BDD=",
            "TDD=",
            "ADR=",
            "SSOT=",
            "Project=",
            "Knowledge=",
            "Derived indexes:",
            "Pointers:",
            "feature-navigation.xml=",
            "Source/test/doc dirs:",
            "Purpose guide (LLM/user chooses; hook does not classify)",
            "fact/contract→`lazy find --purpose fact` or `lazy map`",
            "rule/action→`lazy find --purpose rulebook` + `lazy rules`/`lazy capability`",
            "validation/test→`lazy find --purpose test`",
            "implementation→`lazy find --purpose source`",
            "architecture/ambiguous/high-risk→`lazy find --purpose architecture` + overview/map",
            "Broad overview for architecture/ambiguous/high-risk or unclear purpose",
            "`.lazy-harness/bin/lazy map --overview --format=md --limit=20`",
            "then repeat `.lazy-harness/bin/lazy map '<핵심 토큰>' --format=md --limit=8`",
            "purpose-specific candidates",
            "fallback only if empty/ambiguous/incomplete",
            "Rule digest/full body/Implementation map/graph links",
            "3-5 option gate",
            "Missing record: search current host code/docs/package/config",
            "generic evidence guard",
        ]:
            if phrase not in body:
                fail("direct-search prompt missing framework search phrase: " + phrase + "\n" + output)
        for forbidden in [
            "Harness inventory (actual files first, compact)",
            "Actual record layers",
            "sample:",
            "Evidence examples (examples, not a required tool list)",
            "find .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning} -maxdepth 2 -type f",
            "tree .lazy-harness | head -200",
            "Relevant lazy-harness rules",
            "Search/read debt",
            "FeaturePanel.tsx",
            "Search protocol: (1) extract 2-5 candidate meanings",
            "grep -rli <token>",
            "agentgrep",
            "self-resolve-before-answer",
        ]:
            if forbidden in body:
                fail("direct-search prompt should not render deterministic digest/packet paths: " + forbidden + "\n" + output)

        session_key = "session-" + hashlib.sha256("s-test".encode("utf-8")).hexdigest()[:20]
        packet_journal = temp / ".git" / "lazy-harness" / "runtime" / session_key / "state" / "search-read-debt.jsonl"
        if not packet_journal.exists():
            fail("message.received direct-search prompt should journal search-debt")
        packet_text = packet_journal.read_text(encoding="utf-8")
        if "기능패널 고쳐줘" in packet_text or "안녕" in packet_text:
            fail("message.received search-debt journal must not store raw user message")
        rows = [json.loads(line) for line in packet_text.splitlines() if line.strip()]
        row = rows[-1]
        if row.get("event") != "message.received.search-read-debt" or row.get("fallbackSearchCount") != 1:
            fail("search/read-debt journal row should be static transport, not deterministic packet:\n" + json.dumps(row, ensure_ascii=False, indent=2))
        if row.get("instructionLevel") != "harness-first-static":
            fail("direct-search journal row should use static instruction level, not message-derived levels:\n" + json.dumps(row, ensure_ascii=False, indent=2))
        if "noSemanticBackend=true" not in row.get("notes", []):
            fail("direct-search journal should record that no semantic backend was used")
        for note in ["staticTransport=true", "noUserTextSemanticBranching=true"]:
            if note not in row.get("notes", []):
                fail("direct-search journal should record static/no-branching hook semantics: " + note)

        hook_text = hook.read_text(encoding="utf-8")
        for forbidden_code in ["CHANGE_RE", "HOST_DETAIL_RE", "AMBIGUOUS_RE", "PURE_SMALLTALK_RE", "search_needed(", "self-resolve-before-change' if", "re.compile"]:
            if forbidden_code in hook_text:
                fail("message.received shell hook must not contain user-text semantic classifier code: " + forbidden_code)

        permit = LAZY / "hooks" / "lifecycle" / "helpers" / "check-read-debt-permit.py"

        def run_permit(recent_tool_calls: list[dict]) -> str:
            result = subprocess.run(
                [str(permit), json.dumps({
                    "message_id": "m-surface",
                    "session_id": "s-test",
                    "tool": {"name": "Edit", "args": {"file_path": "src/features/example-feature/FeaturePanel.tsx"}},
                    "recent_tool_calls": recent_tool_calls,
                }, ensure_ascii=False)],
                cwd=temp,
                text=True,
                capture_output=True,
                check=False,
                env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            )
            if result.returncode != 0:
                fail("read-debt permit helper should remain fail-open exit 0:\n" + result.stdout + result.stderr)
            return result.stdout

        no_search = run_permit([])
        if (
            "search-debt gate" not in no_search
            or "inventory/search evidence" not in no_search
            or "actual stored structure" not in no_search
            or "not a project/tool allowlist" not in no_search
        ):
            fail("direct-search debt should block action before real search evidence:\n" + no_search)
        cache_only = run_permit([{"name": "bash", "args_preview": "bun .lazy-harness/scripts/record-index.ts --write"}])
        if "search-debt gate" not in cache_only:
            fail("deterministic cache generation alone must not satisfy direct-search debt:\n" + cache_only)
        listed = run_permit([{"name": "bash", "args_preview": "tree .lazy-harness | head -200"}])
        if listed.strip():
            fail("root-bound tree inventory evidence should satisfy direct-search debt:\n" + listed)
        directory_tree = run_permit([{"name": "mcp__filesystem__directory_tree", "arguments": {"path": ".lazy-harness"}}])
        if directory_tree.strip():
            fail("filesystem directory_tree inventory evidence should satisfy direct-search debt:\n" + directory_tree)
        future_query = run_permit([{"name": "future_code_query_tool", "arguments": {"query": "list actual .lazy-harness records", "path": ".lazy-harness/spec"}}])
        if future_query.strip():
            fail("generic root-bound read/search/query evidence should satisfy direct-search debt without a hardcoded tool allowlist:\n" + future_query)
        unrelated_read = run_permit([{"name": "read", "arguments": {"file_path": "/tmp/unrelated.txt"}}])
        if "search-debt gate" not in unrelated_read:
            fail("read tool name alone must not satisfy search-debt without root-bound harness/source evidence:\n" + unrelated_read)
        unrooted_future_query = run_permit([{"name": "future_code_query_tool", "arguments": {"query": "list something unrelated", "path": "/tmp"}}])
        if "search-debt gate" not in unrooted_future_query:
            fail("future query tool name alone must not satisfy search-debt without root-bound harness/source evidence:\n" + unrooted_future_query)
        searched = run_permit([{"name": "bash", "args_preview": "rg -n '기능패널|feature panel' .lazy-harness src tests"}])
        if searched.strip():
            fail("direct rg/grep search evidence should satisfy direct-search debt:\n" + searched)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ message.received hook inventory-first search-debt injection ok")


def check_response_rule_audit_from_surfaced_digest() -> None:
    """Phase 4: response.completed should audit surfaced digest rows and stay silent on clean turns."""
    tdd_path = LAZY / "tests" / "response-rule-audit.md"
    manifest_path = LAZY / "manifests" / "init-categories.json"
    if not tdd_path.exists():
        fail("Response Rule Audit TDD record missing: " + str(tdd_path))
    manifest_text = manifest_path.read_text(encoding="utf-8")
    if "tests/response-rule-audit.md" not in manifest_text:
        fail("init-categories manifest must sync Response Rule Audit TDD fixture")

    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-response-rule-audit-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        (temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers").mkdir(parents=True, exist_ok=True)
        helper = temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers" / "check-response-rule-audit.py"
        shutil.copy2(LAZY / "hooks" / "lifecycle" / "helpers" / "check-response-rule-audit.py", helper)
        helper.chmod(0o755)
        runtime_helper = temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers" / "runtime_paths.py"
        shutil.copy2(LAZY / "hooks" / "lifecycle" / "helpers" / "runtime_paths.py", runtime_helper)
        runtime_helper.chmod(0o755)

        import hashlib
        journal = temp / ".git" / "lazy-harness" / "runtime" / "default" / "state" / "surfaced-rule-digests.jsonl"
        journal.parent.mkdir(parents=True, exist_ok=True)
        pr_message_id = "phase4-pr-message"
        journal.write_text(json.dumps({
            "schemaVersion": "1.0",
            "event": "message.received.digest",
            "epochSeconds": int(time.time()),
            "messageIdHash": hashlib.sha256(pr_message_id.encode()).hexdigest()[:16],
            "entries": [{
                "recordPath": ".lazy-harness/ssot/pr-description-format.md",
                "title": "Pull Request Description Format",
                "layer": "SSOT",
                "status": "active",
                "recordCompletion": "",
                "bullets": ["PR bodies must include Why, What, and Task."],
            }],
        }, ensure_ascii=False) + "\n", encoding="utf-8")
        journal_text = journal.read_text(encoding="utf-8")
        if "PR description 작성해줘" in journal_text:
            fail("surfaced digest journal must not store raw user message")

        def run_helper(payload: dict) -> str:
            completed = subprocess.run(
                [str(helper), json.dumps(payload, ensure_ascii=False)],
                cwd=temp,
                text=True,
                capture_output=True,
                check=False,
                env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            )
            if completed.returncode != 0:
                fail("response rule audit helper exit changed:\n" + completed.stdout + completed.stderr)
            return completed.stdout

        cap_dir = temp / ".lazy-harness" / "ssot"
        cap_dir.mkdir(parents=True, exist_ok=True)
        (cap_dir / "capabilities.json").write_text(json.dumps({
            "version": 1,
            "capabilities": [{
                "id": "dev-worktree-standard-command",
                "kind": "command",
                "level": "warn",
                "sourceRecord": ".lazy-harness/rules/dev-worktree.md",
                "rulebookRecord": ".lazy-harness/rules/dev-worktree.md",
                "appliesWhen": ["creating_worktree", "starting_dev_instance"],
                "preferredActions": ["bun run wt new", "bun run dev:instance"],
                "discouragedActions": ["git worktree add", "bun run dev"],
                "entrypoint": "bun run wt new / bun run dev:instance",
                "requiresReasonForBypass": True,
                "description": "Fixture warns when raw worktree/dev server commands skip rulebook resolution.",
                "owner": "host-project",
                "tags": ["rulebook", "worktree", "dev-instance"],
            }],
        }, ensure_ascii=False), encoding="utf-8")

        ignored_pr = run_helper({
            "message_id": pr_message_id,
            "recent_tool_calls": [
                {"name": "mcp__github__create_pull_request", "arguments": {"title": "Fixture", "body": "No structured body"}},
            ],
        })
        if "Response rule audit" not in ignored_pr or "Why / What / Task" not in ignored_pr:
            fail("response rule audit should catch surfaced PR rule miss:\n" + ignored_pr)

        clean_pr = run_helper({
            "message_id": pr_message_id,
            "recent_tool_calls": [
                {"name": "mcp__github__create_pull_request", "arguments": {"title": "Fixture", "body": "Why:\n- because\n\nWhat:\n- changed\n\nTask:\n- done"}},
            ],
        })
        if clean_pr.strip():
            fail("response rule audit should stay silent when surfaced PR rule is satisfied:\n" + clean_pr)

        missed_action = run_helper({
            "message_id": "phase-missed-discouraged-action",
            "recent_tool_calls": [{"name": "bash", "args_preview": "git worktree add ../fixture feature/foo"}],
        })
        if "Operating rule audit" not in missed_action or "dev-worktree-standard-command" not in missed_action or "bun run wt new" not in missed_action:
            fail("response audit should advise for missed discouragedAction without resolve evidence:\n" + missed_action)

        resolved_action = run_helper({
            "message_id": "phase-resolved-discouraged-action",
            "recent_tool_calls": [
                {"name": "bash", "args_preview": ".lazy-harness/bin/lazy capability resolve --action 'git worktree add ../fixture feature/foo' --format=json"},
                {"name": "bash", "args_preview": "git worktree add ../fixture feature/foo"},
            ],
        })
        if resolved_action.strip():
            fail("response audit should stay silent when discouragedAction was resolved first:\n" + resolved_action)

        no_action_match = run_helper({
            "message_id": "phase-no-discouraged-action",
            "recent_tool_calls": [{"name": "bash", "args_preview": "git status --short"}],
        })
        if no_action_match.strip():
            fail("response audit should stay silent when no discouraged action matches:\n" + no_action_match)

        # Manual journal row for a record-completion obligation not tied to PR.
        missing_capture_id = "phase4-record-missing"
        journal.write_text(journal.read_text(encoding="utf-8") + json.dumps({
            "schemaVersion": "1.0",
            "event": "message.received.digest",
            "epochSeconds": int(time.time()),
            "messageIdHash": hashlib.sha256(missing_capture_id.encode()).hexdigest()[:16],
            "entries": [{
                "recordPath": ".lazy-harness/ssot/harness-enforcement-policy.md",
                "title": "Harness Enforcement Policy",
                "layer": "SSOT",
                "status": "active",
                "recordCompletion": "user-confirmed enforcement policy changes update this SSOT",
                "bullets": ["audit missed rules and missing records after response with response.completed"],
            }],
        }, ensure_ascii=False) + "\n", encoding="utf-8")

        missing_capture = run_helper({
            "message_id": missing_capture_id,
            "assistant_response": "Confirmed source-of-truth correction and SDD contract change.",
            "recent_tool_calls": [{"name": "Edit", "args_preview": ".lazy-harness/hooks/lifecycle/on-message-received.sh"}],
        })
        if "record-completion guidance" not in missing_capture:
            fail("response rule audit should catch surfaced record-completion miss:\n" + missing_capture)

        captured = run_helper({
            "message_id": missing_capture_id,
            "assistant_response": "Confirmed source-of-truth correction and SDD contract change.",
            "recent_tool_calls": [{"name": "Edit", "args_preview": ".lazy-harness/ssot/harness-enforcement-policy.md"}],
        })
        if captured.strip():
            fail("response rule audit should stay silent when durable record capture is present:\n" + captured)


        packet_journal = journal.parent / "search-read-debt.jsonl"
        safe_find_message_id = "phase4-safe-purpose-find"
        arch_find_message_id = "phase4-architecture-purpose-find"
        packet_journal.write_text("".join([
            json.dumps({
                "event": "context-delivery.packet",
                "epochSeconds": int(time.time()),
                "messageIdHash": hashlib.sha256(safe_find_message_id.encode()).hexdigest()[:16],
                "instructionLevel": "self-resolve-before-change",
                "confidence": 0.0,
                "requiredRead": [],
                "fallbackSearchCount": 2,
            }, ensure_ascii=False) + "\n",
            json.dumps({
                "event": "context-delivery.packet",
                "epochSeconds": int(time.time()),
                "messageIdHash": hashlib.sha256(arch_find_message_id.encode()).hexdigest()[:16],
                "instructionLevel": "self-resolve-before-change",
                "confidence": 0.0,
                "requiredRead": [],
                "fallbackSearchCount": 2,
            }, ensure_ascii=False) + "\n",
        ]), encoding="utf-8")
        safe_find_audit = run_helper({
            "message_id": safe_find_message_id,
            "recent_tool_calls": [{"name": "bash", "args_preview": ".lazy-harness/bin/lazy find --purpose test 'purpose scoped retrieval' --format=json"}],
        })
        if safe_find_audit.strip():
            fail("response audit should accept safe-purpose lazy find as search evidence:\n" + safe_find_audit)
        architecture_find_audit = run_helper({
            "message_id": arch_find_message_id,
            "recent_tool_calls": [{"name": "bash", "args_preview": ".lazy-harness/bin/lazy find --purpose architecture 'purpose scoped retrieval' --format=json"}],
        })
        if "Search/read debt audit" not in architecture_find_audit:
            fail("response audit should not accept architecture-purpose lazy find alone as search evidence:\n" + architecture_find_audit)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ response rule audit from surfaced digest ok")


def check_tool_execute_before_hook() -> None:
    """N2.5 — Layer 2 force-gate hook (ADR 0024).

    Run on-tool-execute-before.sh through canonical scenarios and assert
    deny / allow + session-cache behavior matches design.
    """
    hook = LAZY / "hooks" / "lifecycle" / "on-tool-execute-before.sh"
    if not hook.exists() or not os.access(hook, os.X_OK):
        fail("N2.5 hook missing or not executable: on-tool-execute-before.sh")
    overview_batch_helper = LAZY / "hooks" / "lifecycle" / "helpers" / "check-overview-batch-order.py"
    if not overview_batch_helper.exists() or not os.access(overview_batch_helper, os.X_OK):
        fail("overview batch helper missing or not executable: check-overview-batch-order.py")

    # Clean cache before run (deterministic)
    cache_dir = LAZY / ".cache" / "session"
    if cache_dir.exists():
        for p in cache_dir.glob("__n25_*.json"):
            try:
                p.unlink()
            except FileNotFoundError:
                pass

    session_prefix = f"__n25_{os.getpid()}_"
    cases = [
        # (name, payload_dict, expect_exit, expect_stdout_contains)
        ("no-search-src-edit-deny", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case1",
            "tool": {"name": "Edit", "args": {"file_path": "src/main/services/foo.ts"}},
            "recent_tool_calls": [],
        }, 1, "lazy-harness gate"),
        ("grep-record-then-edit-allow", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case2",
            "tool": {"name": "Edit", "args": {"file_path": "src/main/services/foo.ts"}},
            "recent_tool_calls": [
                {"name": "Grep", "args_preview": "pattern foo path .lazy-harness/domain/"}
            ],
        }, 0, ""),
        ("brace-grep-record-then-edit-allow", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case2_brace",
            "tool": {"name": "Edit", "args": {"file_path": "src/main/services/foo.ts"}},
            "recent_tool_calls": [
                {"name": "bash", "args_preview": "grep -rli 'foo' .lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/ | head"}
            ],
        }, 0, ""),
        ("batched-record-read-then-edit-allow", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case2_batch_read",
            "tool": {"name": "Edit", "args": {"file_path": "src/main/services/foo.ts"}},
            "recent_tool_calls": [
                {"name": "batch", "args": {"tool_calls": [
                    {"tool": "read", "parameters": {"file_path": ".lazy-harness/spec/platform/search-read-debt-contract.md"}},
                    {"tool": "read", "parameters": {"file_path": ".lazy-harness/ssot/harness-enforcement-policy.md"}},
                ]}}
            ],
        }, 0, ""),
        ("batch-overview-with-query-allow", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case2_batch_overview",
            "tool": {"name": "batch", "args": {"tool_calls": [
                {"tool": "bash", "parameters": {"command": ".lazy-harness/bin/lazy map --overview --format=md --limit=20"}},
                {"tool": "bash", "parameters": {"command": ".lazy-harness/bin/lazy map 'retrieval coverage audit' --format=md --limit=8"}},
            ]}},
            "recent_tool_calls": [],
        }, 0, ""),
        ("multi-tool-overview-parallel-allow", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case2_parallel_overview",
            "tool": {"name": "multi_tool_use.parallel", "args": {"tool_uses": [
                {"recipient_name": "functions.bash", "parameters": {"command": ".lazy-harness/bin/lazy map --overview --format=md --limit=20"}},
                {"recipient_name": "functions.read", "parameters": {"file_path": ".lazy-harness/behavior/llm-owned-record-retrieval.md"}},
            ]}},
            "recent_tool_calls": [],
        }, 0, ""),
        ("apply-patch-src-no-search-deny", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case2_apply_patch",
            "tool": {"name": "apply_patch", "args": {"patch_text": "*** Begin Patch\n*** Update File: src/main/services/foo.ts\n@@\n-old\n+new\n*** End Patch"}},
            "recent_tool_calls": [],
        }, 1, "lazy-harness gate"),
        ("namespaced-apply-patch-src-no-search-deny", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case2_functions_apply_patch",
            "tool": {"name": "functions.apply_patch", "args": {"patch_text": "*** Begin Patch\n*** Update File: src/main/services/foo.ts\n@@\n-old\n+new\n*** End Patch"}},
            "recent_tool_calls": [],
        }, 1, "lazy-harness gate"),
        ("record-edit-exempt", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case3",
            "tool": {"name": "Write", "args": {"file_path": ".lazy-harness/decisions/0099-foo.md"}},
            "recent_tool_calls": [],
        }, 0, ""),
        ("non-code-exempt", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case4",
            "tool": {"name": "Write", "args": {"file_path": "docs/readme.md"}},
            "recent_tool_calls": [],
        }, 0, ""),
        # Re-uses session_id of case2 → cache should still hold within this process only.
        ("session-cache-permanent-allow", {
            "event": "tool.execute.before",
            "session_id": session_prefix + "case2",
            "tool": {"name": "Edit", "args": {"file_path": "src/main/services/bar.ts"}},
            "recent_tool_calls": [],
        }, 0, ""),
    ]

    for name, payload, want_exit, want_substr in cases:
        completed = subprocess.run(
            [str(hook), json.dumps(payload)],
            cwd=ROOT,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(ROOT)),
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != want_exit:
            fail(
                f"N2.5 hook case '{name}': exit got={completed.returncode} "
                f"expected={want_exit}\nstdout={completed.stdout!r}\nstderr={completed.stderr!r}"
            )
        if want_substr and want_substr not in completed.stdout:
            fail(
                f"N2.5 hook case '{name}': stdout missing substring "
                f"'{want_substr}'\nstdout={completed.stdout!r}"
            )

    # Cleanup cache files we made
    for p in (cache_dir.glob("__n25_*.json") if cache_dir.exists() else []):
        try:
            p.unlink()
        except FileNotFoundError:
            pass

    print(f"✓ N2.5 tool-execute-before hook ok ({len(cases)} scenarios)")


def check_read_debt_permit_generic_external_action() -> None:
    """Search-debt guard must block unknown external MCP action until root-bound search evidence exists."""
    helper = LAZY / "hooks" / "lifecycle" / "helpers" / "check-read-debt-permit.py"
    if not helper.exists():
        fail("read-debt helper missing: " + str(helper))
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-read-debt-generic-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=temp, env=env_without_lazy_runtime(), check=True)
        state = temp / ".git" / "lazy-harness" / "runtime" / "default" / "state"
        state.mkdir(parents=True)
        message_id = "generic-message-1"
        row = {
            "event": "context-delivery.packet",
            "epochSeconds": time.time(),
            "messageIdHash": hashlib.sha256(message_id.encode()).hexdigest()[:16],
            "instructionLevel": "self-resolve-before-change",
            "confidence": 0.0,
            "requiredRead": [],
            "fallbackSearchCount": 2,
        }
        (state / "search-read-debt.jsonl").write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        base_payload = {
            "message_id": message_id,
            "tool": {"name": "mcp__external__get_context", "args": {"id": "fixture"}},
        }
        no_search = subprocess.run(
            ["python3", str(helper), json.dumps({**base_payload, "recent_tool_calls": []}, ensure_ascii=False)],
            cwd=ROOT,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            text=True,
            capture_output=True,
            check=False,
        )
        if "search-debt gate" not in no_search.stdout or "root-bound search" not in no_search.stdout:
            fail("generic external action should be guarded until root-bound search evidence exists:\n" + no_search.stdout + no_search.stderr)
        with_search = subprocess.run(
            ["python3", str(helper), json.dumps({**base_payload, "recent_tool_calls": [{"name": "agentgrep", "query": "feature"}]}, ensure_ascii=False)],
            cwd=ROOT,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            text=True,
            capture_output=True,
            check=False,
        )
        if with_search.stdout.strip():
            fail("root-bound search evidence should satisfy generic search-debt guard:\n" + with_search.stdout + with_search.stderr)


        with_purpose_find = subprocess.run(
            ["python3", str(helper), json.dumps({**base_payload, "recent_tool_calls": [{"name": "bash", "args_preview": ".lazy-harness/bin/lazy find --purpose rulebook 'project policy storage' --format=json"}]}, ensure_ascii=False)],
            cwd=ROOT,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            text=True,
            capture_output=True,
            check=False,
        )
        if with_purpose_find.stdout.strip():
            fail("safe-purpose lazy find evidence should satisfy search-debt guard:\n" + with_purpose_find.stdout + with_purpose_find.stderr)

        with_architecture_find = subprocess.run(
            ["python3", str(helper), json.dumps({**base_payload, "recent_tool_calls": [{"name": "bash", "args_preview": ".lazy-harness/bin/lazy find --purpose architecture 'project policy storage' --format=json"}]}, ensure_ascii=False)],
            cwd=ROOT,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            text=True,
            capture_output=True,
            check=False,
        )
        if "search-debt gate" not in with_architecture_find.stdout:
            fail("architecture-purpose lazy find alone must not satisfy search-debt guard:\n" + with_architecture_find.stdout + with_architecture_find.stderr)

        required_message_id = "generic-message-required-read"
        required_row = {
            "event": "context-delivery.packet",
            "epochSeconds": time.time(),
            "messageIdHash": hashlib.sha256(required_message_id.encode()).hexdigest()[:16],
            "instructionLevel": "self-resolve-before-change",
            "confidence": 0.8,
            "requiredRead": [{"path": ".lazy-harness/spec/platform/purpose-scoped-retrieval.md"}],
            "fallbackSearchCount": 0,
        }
        with (state / "search-read-debt.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(required_row, ensure_ascii=False) + "\n")
        required_payload = {
            "message_id": required_message_id,
            "tool": {"name": "Edit", "args": {"file_path": "src/main/services/foo.ts"}},
            "recent_tool_calls": [{"name": "bash", "args_preview": ".lazy-harness/bin/lazy find --purpose fact 'purpose scoped retrieval' --format=json"}],
        }
        required_result = subprocess.run(
            ["python3", str(helper), json.dumps(required_payload, ensure_ascii=False)],
            cwd=ROOT,
            env=env_without_lazy_runtime(LAZY_HOST_ROOT=str(temp)),
            text=True,
            capture_output=True,
            check=False,
        )
        if "read-debt gate" not in required_result.stdout:
            fail("purpose-scoped find is search evidence, not requiredRead evidence:\n" + required_result.stdout + required_result.stderr)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ read-debt generic external action guard ok")


def check_agents_md_invariants() -> None:
    """N2.5 — .lazy-harness/AGENTS.md invariants (ADR 0024).

    Framework grammar must stay thin and host-agnostic. Asserts:
      - file exists
      - line count <= 180 (Phase α governance expansion: §0 + §2.5; hard cap 180)
      - mentions all 6 layer dirs (domain/spec/behavior/tests/decisions/ssot)
      - does NOT contain known host-specific tokens (tRPC / Prisma / multi-tenant
        / hospitalId etc.) — those belong to records, not grammar
    """
    path = LAZY / "AGENTS.md"
    if not path.exists():
        fail("N2.5 AGENTS.md missing: .lazy-harness/AGENTS.md")

    text = path.read_text(encoding="utf-8")
    line_count = len(text.splitlines())
    if line_count > 180:
        fail(
            f"N2.5 AGENTS.md too thick: {line_count} lines > 180 cap. "
            "Host-specific rules belong in records (DDD/SDD/BDD/TDD/ADR/SSOT), not grammar."
        )

    required_layers = ["domain/", "spec/", "behavior/", "tests/", "decisions/", "ssot/"]
    missing = [layer for layer in required_layers if layer not in text]
    if missing:
        fail(f"N2.5 AGENTS.md missing layer references: {missing}")

    required_phrases = [
        "Layer completeness gate",
        "TDD/regression/bug",
        "SDD/BDD/SSOT/DDD",
        "Analysis discovery capture",
        "Discovery capture",
        "rule-sources",
        "Rule placement",
    ]
    missing_phrases = [phrase for phrase in required_phrases if phrase not in text]
    if missing_phrases:
        fail(f"N2.5 AGENTS.md missing layer-completeness guard phrases: {missing_phrases}")

    forbidden_host_tokens = [
        "tRPC", "Prisma", "hospitalId", "multi-tenant", "multi-tenancy",
        # Split SaaS-like names so the C17 doctor does not flag its own forbidden-term list.
        "Elec" + "tron", "Tail" + "wind", "Supa" + "base", "EM" + "R",
    ]
    leaked = [t for t in forbidden_host_tokens if t in text]
    if leaked:
        fail(
            f"N2.5 AGENTS.md leaked host-specific tokens: {leaked}. "
            "Move these to records (e.g., decisions/ or domain/)."
        )

    print(f"✓ N2.5 AGENTS.md invariants ok ({line_count} lines)")


def main() -> None:
    """ADR 0026 scope separation:
    - BOTH checks run in both framework dev repo and on hosts.
    - FRAMEWORK_ONLY checks are skipped on hosts (their fixtures are not copied by lazy-init).
    - --scope CLI flag (auto|framework|host) lets caller force a scope; default auto.
    """
    parser = argparse.ArgumentParser(description="Lazy-Harness self-test (ADR 0026 scope-aware)")
    parser.add_argument(
        "--scope",
        choices=["auto", "framework", "host"],
        default="auto",
        help="Validation scope. 'auto' detects via framework-own markers (planning/phase-5-plan.xml + framework/framework-contract.md).",
    )
    args = parser.parse_args()

    scope = _detect_scope() if args.scope == "auto" else args.scope
    global ACTIVE_SCOPE
    ACTIVE_SCOPE = scope

    # ADR 0026: (check_callable, tag) tuples. BOTH = runs everywhere. FRAMEWORK_ONLY
    # = skipped on hosts because its fixtures are framework-own and not copied by lazy-init.
    checks: list[tuple[callable, str]] = [
        (check_doctor_smoke, "BOTH"),
        (check_doctor_c17_negative, "BOTH"),
        (check_doctor_package_health, "BOTH"),
        (check_package_health_generate_remediation_heuristic, "BOTH"),
        (check_xml, "BOTH"),
        (check_jsonl, "BOTH"),
        (check_schemas, "BOTH"),
        (check_lint_output, "FRAMEWORK_ONLY"),
        (check_interview_loop_collect, "BOTH"),
        (check_interview_loop_answer, "BOTH"),
        (check_layer_completeness_helper, "BOTH"),
        (check_analysis_discovery_capture_helper, "BOTH"),
        (check_project_rule_placement_helper, "BOTH"),
        (check_option_gate_discipline_helper, "BOTH"),
        (check_bdd_trigger_loop_suppression, "BOTH"),
        (check_bdd_trigger_avoids_runtime_tsmorph, "BOTH"),
        (check_record_before_session_history_helper, "BOTH"),
        (check_pre_push_uses_canonical_lazy_cli, "BOTH"),
        (check_lazy_cli_entrypoint_helper, "BOTH"),
        (check_fast_validation_tier_cli, "BOTH"),
        (check_bounded_validation_governor_cli, "BOTH"),
        (check_jcode_wiring_pointer_only, "BOTH"),
        (check_jcode_wiring_repairs_stale_defaults, "BOTH"),
        (check_jcode_wiring_repairs_markerless_bash_hook_default, "BOTH"),
        (check_jcode_wiring_removes_rejected_layer2_block, "BOTH"),
        (check_pi_package_layout_and_contract, "FRAMEWORK_ONLY"),
        (check_jcode_wiring_message_received_hook, "BOTH"),
        (check_prompt_budget_measurement, "BOTH"),
        (check_framework_runtime_no_host_product_hardcoding, "BOTH"),
        (check_manifest_syncs_python_lifecycle_helpers, "BOTH"),
        (check_lazy_sync_prunes_stale_managed_files, "BOTH"),
        (check_jcode_dev_hooks_are_nonblocking, "BOTH"),
        (check_rule_action_boundary_legacy_no_project_policy, "BOTH"),
        (check_jcode_wiring_bash_safety_only_hook, "BOTH"),
        (check_guidance_ladder_hard_stop_promotion, "BOTH"),
        (check_jcode_project_profile_skill_wrapper, "BOTH"),
        (check_jcode_doc_ingest_skill_wrapper, "BOTH"),
        (check_jcode_impl_map_migrate_skill_wrapper, "BOTH"),
        (check_pre_commit_runs_lazy_test, "BOTH"),
        (check_gate_state_cli_and_record_audit_source_guard, "BOTH"),
        (check_lifecycle_fixture_intake_cli, "BOTH"),
        (check_capability_registry_cli_phase1, "BOTH"),
        (check_project_operating_rulebook_cli, "BOTH"),
        (check_purpose_scoped_retrieval_cli, "BOTH"),
        (check_response_completed_no_auto_route_telemetry, "BOTH"),
        (check_removed_query_helper_artifacts_absent, "BOTH"),
        (check_standalone_source_detection_uses_markers, "BOTH"),
        (check_lazy_host_root_resolution, "BOTH"),
        (check_parallel_runtime_state_isolation, "BOTH"),
        (check_shared_jsonl_conflict_visible, "BOTH"),
        (check_skill_create_cli, "BOTH"),
        (check_tdd_cross_verify, "FRAMEWORK_ONLY"),
        (check_affected_test_runner, "FRAMEWORK_ONLY"),
        (check_aftershock_reanalysis, "FRAMEWORK_ONLY"),
        (check_lifecycle_hook_integration, "FRAMEWORK_ONLY"),
        (check_lifecycle_parity_runner, "FRAMEWORK_ONLY"),
        (check_knowledge_intake, "FRAMEWORK_ONLY"),
        (check_document_resource_ingestion_inspect, "FRAMEWORK_ONLY"),
        (check_project_profile_inspect, "FRAMEWORK_ONLY"),
        (check_project_profile_v2_runtime, "FRAMEWORK_ONLY"),
        (check_project_profile_v2_queue_runtime, "FRAMEWORK_ONLY"),
        (check_record_audit_cli, "FRAMEWORK_ONLY"),
        (check_graph_hygiene_cli, "FRAMEWORK_ONLY"),
        (check_real_feature_walkthrough, "FRAMEWORK_ONLY"),
        (check_e2e_demo, "FRAMEWORK_ONLY"),
        (check_triggers, "FRAMEWORK_ONLY"),
        (check_layer_impact_gate, "FRAMEWORK_ONLY"),
        (check_reference_resolver, "FRAMEWORK_ONLY"),
        (check_search_provider_canonical_record_dirs, "FRAMEWORK_ONLY"),
        (check_record_index_generator_phase3, "BOTH"),
        (check_retrieval_coverage_audit_cli, "BOTH"),
        (check_retrieval_workflow_benchmark_cli, "BOTH"),
        (check_source_feature_navigation_phase3, "FRAMEWORK_ONLY"),
        (check_context_tier_manifest_phase4, "BOTH"),
        (check_project_map_v2_schema, "BOTH"),
        (check_project_map_update_loop_v2, "BOTH"),
        (check_policy_machinery_v2, "BOTH"),
        (check_evidence_capsule_standard_phase5, "BOTH"),
        (check_read_debt_permit_generic_external_action, "BOTH"),
        (check_record_decision_broker_phase8, "BOTH"),
        (check_record_decision_shadow_response_completed, "BOTH"),
        (check_message_received_hook_context_injection, "BOTH"),
        (check_response_rule_audit_from_surfaced_digest, "BOTH"),
        (check_tool_execute_before_hook, "BOTH"),
        (check_agents_md_invariants, "BOTH"),
    ]

    ran = 0
    skipped = 0
    for check, tag in checks:
        if tag == "BOTH":
            applies = True
        elif tag == "FRAMEWORK_ONLY":
            applies = scope == "framework"
        elif tag == "HOST_ONLY":
            applies = scope == "host"
        else:
            applies = True

        if not applies:
            print(f"[skipped] {check.__name__} (scope={scope}, tag={tag})")
            skipped += 1
            continue
        check()
        ran += 1

    print(f"lazy-harness self-test ok (scope={scope}, ran={ran}, skipped={skipped})")


def _detect_scope() -> str:
    """ADR 0026: framework dev repo has both markers; hosts have neither."""
    lazy = ROOT / ".lazy-harness"
    return (
        "framework"
        if (lazy / "framework" / "framework-contract.md").exists()
        and (lazy / "planning" / "phase-5-plan.xml").exists()
        else "host"
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.stdout.write(exc.stdout)
        sys.stderr.write(exc.stderr)
        fail(f"command failed: {' '.join(exc.cmd)}")
