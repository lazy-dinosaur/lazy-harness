#!/usr/bin/env python3
"""Lazy-Harness reproducible self-test.

Checks the framework-owned operational invariants defined by ADR 0022:
- every .lazy-harness XML file parses
- permanent JSONL logs parse line-by-line
- trigger fixtures produce DDD/SDD/BDD/SSOT candidates
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import runpy
import subprocess
import sys
import tempfile
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
        env = {**os.environ, "LAZY_HARNESS_DOCTOR_INCLUDE_NEGATIVE": "1"}
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
    env = {
        **os.environ,
        "LAZY_HARNESS_QUESTION_QUEUE": str(queue.relative_to(ROOT)),
        "LAZY_HARNESS_VALIDATIONS_FILE": str(validations.relative_to(ROOT)),
    }
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
    state_file = ROOT / ".lazy-harness" / "state" / "open-gates.json"
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
                "content": "Medivance worktree workflow: after creating a worktree with bun wt new, immediately switch Jcode cwd to the new worktree.",
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
            "• Rule: Medivance PR descriptions must use Why, What, Task, Validation, then User-note-type / User-note when applicable.\n"
            "• Scope: team-policy\n"
            "• Primary record: .lazy-harness/ssot/pr-description-format.md\n"
            "• Why not AGENTS.md: This is a Medivance team PR workflow policy, not framework-global guidance.\n"
            "• Why not .jcode: .jcode is local/private Jcode memory only; canonical shared team policy belongs in .lazy-harness/ssot.\n"
            "• Confirmation: user-confirmed\n"
        ),
        "recent_tool_calls": [],
    }
    real_world_judgement = run_project_rule_placement_helper(real_world_judgement_payload)
    if real_world_judgement.strip():
        fail("project rule placement helper should pass real-world bullet/no-backtick judgement:\n" + real_world_judgement)

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
            "framework gate는 두 프로젝트에 적용됨. Medivance release dispatch 정책은 "
            ".lazy-harness/ssot/release-branch-policy.md record에 이미 있음. "
            "medivance-pwa는 release script가 없어 적용 대상이 아님."
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
    """BDD helper must ask once per turn (same message_id) via fingerprint state.

    Note: jcode `response.completed` payload does NOT include `assistant_response`,
    so the older suppression strategy that string-matched assistant text was a
    no-op in production. The new contract uses
    `.lazy-harness/state/open-gates.json` keyed by (helper, fingerprint,
    message_id) so a given (files+last_user_message) signature fires at most
    once per turn. See `.lazy-harness/tests/bdd-trigger-option-gate-loop-bypass.md`.
    """
    state_file = ROOT / ".lazy-harness" / "state" / "open-gates.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    backup = state_file.read_text(encoding="utf-8") if state_file.exists() else None
    if state_file.exists():
        state_file.unlink()
    try:
        first_payload = {
            "last_user_message": "사용자가 환자 목록 버튼을 클릭하면 환자 목록 화면으로 이동해야 합니다.",
            "message_id": "test-msg-turn-A",
            "recent_tool_calls": [],
        }
        first = run_bdd_trigger_helper(first_payload)
        if "BDD scenario 후보" not in first or "BDD scenario 등록" not in first:
            fail("BDD trigger helper should surface first natural-language scenario gate:\n" + first)

        # Same message_id (= same turn) + same fingerprint inputs → must be suppressed.
        repeated_same_turn = run_bdd_trigger_helper(first_payload)
        if repeated_same_turn.strip():
            fail("BDD trigger helper should suppress duplicate fire in same turn (same message_id):\n" + repeated_same_turn)

        # New message_id (= new turn) → fingerprint cleared, must fire again.
        new_turn_payload = dict(first_payload)
        new_turn_payload["message_id"] = "test-msg-turn-B"
        repeated_new_turn = run_bdd_trigger_helper(new_turn_payload)
        if "BDD scenario 후보" not in repeated_new_turn:
            fail("BDD trigger helper should fire again on a new turn (different message_id):\n" + repeated_new_turn)
    finally:
        # Restore prior state so tests do not pollute host state file.
        if backup is not None:
            state_file.write_text(backup, encoding="utf-8")
        elif state_file.exists():
            state_file.unlink()
    print("✓ BDD trigger loop suppression ok")


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
        "assistant_response": "기록해둔 예약시트 계획을 찾아보겠습니다.",
        "recent_tool_calls": [{
            "name": "session_search",
            "query": "reservation sheet plan",
        }],
    }
    blocked = run_record_before_session_history_helper(blocked_payload)
    if "Record-before-session-history gate" not in blocked:
        fail("record-before-session-history helper should block session_search-first lookup:\n" + blocked)

    record_first_payload = {
        "assistant_response": "기록해둔 예약시트 계획을 찾아보겠습니다.",
        "recent_tool_calls": [
            {
                "name": "agentgrep",
                "args_preview": "Search .lazy-harness/planning for reservation sheet notes",
            },
            {
                "name": "session_search",
                "query": "reservation sheet plan",
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


def check_pre_commit_runs_lazy_test() -> None:
    """pre-commit guard must move framework validation to the commit boundary."""
    source = (LAZY / "hooks" / "pre-commit-guard.sh").read_text(encoding="utf-8")
    required = [
        "run_commit_gate()",
        '"$LAZY/bin/lazy" test',
        '"$LAZY/scripts/self-test.py"',
        "pre-commit blocked: .lazy-harness/bin/lazy test 실패",
        "IS_FRAMEWORK_REPO",
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("pre-commit guard missing commit-time lazy test gate: " + json.dumps(missing, ensure_ascii=False))
    print("✓ pre-commit lazy test gate ok")


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
        subprocess.run(["git", "init", "-q"], cwd=temp, check=True)
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
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ LAZY_HOST_ROOT worktree root resolution ok")


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
    aftershock_queue = LAZY / "questions" / f"__tmp_hook_aftershock_{os.getpid()}.xml"
    decisions = LAZY / "logs" / f"__tmp_hook_decisions_{os.getpid()}.jsonl"
    for path in [tdd_queue, aftershock_queue, decisions]:
        path.unlink(missing_ok=True)
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

        decisions.write_text((LAZY / "triggers" / "fixtures" / "aftershock" / "decisions.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
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
    finally:
        for path in [tdd_queue, aftershock_queue, decisions]:
            path.unlink(missing_ok=True)
    print("✓ 5d-5 lifecycle hook integration ok")


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


def check_tool_execute_before_hook() -> None:
    """N2.5 — Layer 2 force-gate hook (ADR 0024).

    Run on-tool-execute-before.sh through 5 canonical scenarios and assert
    deny / allow + session-cache behavior matches design.
    """
    hook = LAZY / "hooks" / "lifecycle" / "on-tool-execute-before.sh"
    if not hook.exists() or not os.access(hook, os.X_OK):
        fail("N2.5 hook missing or not executable: on-tool-execute-before.sh")

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
            env={**os.environ, "LAZY_HOST_ROOT": str(ROOT)},
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
        (check_jcode_wiring_pointer_only, "BOTH"),
        (check_jcode_dev_hooks_are_nonblocking, "BOTH"),
        (check_pre_commit_runs_lazy_test, "BOTH"),
        (check_standalone_source_detection_uses_markers, "BOTH"),
        (check_lazy_host_root_resolution, "BOTH"),
        (check_skill_create_cli, "BOTH"),
        (check_tdd_cross_verify, "FRAMEWORK_ONLY"),
        (check_affected_test_runner, "FRAMEWORK_ONLY"),
        (check_aftershock_reanalysis, "FRAMEWORK_ONLY"),
        (check_lifecycle_hook_integration, "FRAMEWORK_ONLY"),
        (check_knowledge_intake, "FRAMEWORK_ONLY"),
        (check_real_feature_walkthrough, "FRAMEWORK_ONLY"),
        (check_e2e_demo, "FRAMEWORK_ONLY"),
        (check_triggers, "FRAMEWORK_ONLY"),
        (check_layer_impact_gate, "FRAMEWORK_ONLY"),
        (check_reference_resolver, "FRAMEWORK_ONLY"),
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
