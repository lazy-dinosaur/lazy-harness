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


def run_lifecycle_check_shadow(payload: dict, queue: pathlib.Path, decisions: pathlib.Path | None = None) -> dict:
    validations = LAZY / "logs" / f"__tmp_lifecycle_shadow_validations_{os.getpid()}.jsonl"
    validations.unlink(missing_ok=True)
    env = {
        **os.environ,
        "LAZY_HARNESS_QUESTION_QUEUE": str(queue.relative_to(ROOT)),
        "LAZY_HARNESS_VALIDATIONS_FILE": str(validations.relative_to(ROOT)),
    }
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
    """BDD helper captures pending candidates silently and never repeats asks.

    BDD scenario detection is record/candidate intake, not implementation approval.
    The helper must not inject A/B/C/D prompts for the same pending scenario across
    turns. Instead it appends one deduped row to
    `.lazy-harness/knowledge/candidates.jsonl` for later user-confirmed promotion.
    """
    candidates_file = ROOT / ".lazy-harness" / "knowledge" / "candidates.jsonl"
    state_file = ROOT / ".lazy-harness" / "state" / "open-gates.json"
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
            "medivance.experimental-lazy-harness /harness-doctor Phase 5 ADR 0007 C1~C16\n",
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
            if os.readlink(instruction) != "../../.lazy-harness/AGENTS.md":
                fail("05-lazy-harness symlink target is wrong: " + os.readlink(instruction))
        else:
            content = instruction.read_text(encoding="utf-8")
            if "4 단계 흐름" in content or "Default = 모름" not in content:
                fail("05-lazy-harness fallback did not refresh stale instruction copy")

        archive = temp / ".jcode" / "archive"
        archived_names = {p.name for p in archive.iterdir()} if archive.exists() else set()
        required_archives = {
            "AGENTS.md.pre-generated-marker",
            "config.toml.pre-generated-marker",
            "05-lazy-harness.md.pre-symlink",
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


def check_jcode_wiring_message_received_hook() -> None:
    """Generated and user-owned Jcode configs must wire message.received context hook."""
    source = (LAZY / "scripts" / "jcode-wiring.ts").read_text(encoding="utf-8")
    required = [
        'event = \\"message.received\\"',
        'command = \\".lazy-harness/hooks/lifecycle/on-message-received.sh\\"',
        'blocking = true',
        'timeout_ms = 800',
        'ensureMessageReceivedHook',
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("jcode wiring missing message.received hook contract: " + json.dumps(missing, ensure_ascii=False))

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
        for phrase in ['event = "message.received"', 'on-message-received.sh', 'blocking = true', 'timeout_ms = 800']:
            if phrase not in updated:
                fail("message.received hook patch missing phrase " + phrase + ":\n" + updated)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ jcode message.received hook wiring ok")


def check_manifest_syncs_python_lifecycle_helpers() -> None:
    """Hosts need Python lifecycle helpers copied by lazy-sync/lazy-init."""
    manifest = json.loads((LAZY / "manifests" / "init-categories.json").read_text(encoding="utf-8"))
    hooks_item = None
    for item in manifest["categories"]["A"]["items"]:
        if item.get("path") == "hooks/":
            hooks_item = item
            break
    if not hooks_item or "lifecycle/helpers/*.py" not in hooks_item.get("glob", []):
        fail("init-categories manifest must sync Python lifecycle helpers for host guard support")
    print("✓ manifest Python lifecycle helper sync ok")


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
        env={**os.environ, "LAZY_HOST_ROOT": str(root or ROOT)},
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


def _run_task_router(message: str, changed_files: list[str] | None = None, extra_args: list[str] | None = None, env: dict | None = None) -> dict:
    command = ["bun", ".lazy-harness/scripts/task-router.ts", "--message", message, "--format=json"]
    if changed_files:
        command.extend(["--changed-files", ",".join(changed_files)])
    if extra_args:
        command.extend(extra_args)
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        fail("task-router command failed:\nSTDOUT:\n" + completed.stdout + "\nSTDERR:\n" + completed.stderr)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        fail(f"task-router did not emit JSON: {exc}\n{completed.stdout}")


def check_task_router_read_only_contract() -> None:
    """ADR 0037: route is read-only by default; --log is append-only telemetry."""
    source = (LAZY / "scripts" / "task-router.ts").read_text(encoding="utf-8")
    forbidden = [
        "rmSync",
        "unlinkSync",
        "interview-loop",
        "--apply",
    ]
    leaked = [phrase for phrase in forbidden if phrase in source]
    if leaked:
        fail("task-router must stay read-only/advisory; forbidden phrase(s): " + json.dumps(leaked, ensure_ascii=False))

    required = [
        "router-read-only",
        "no-recommended-auto-select",
        "candidate-is-not-canonical",
        "workflow-route",
        "route-decisions.jsonl",
        "messageHash",
    ]
    missing = [phrase for phrase in required if phrase not in source]
    if missing:
        fail("task-router missing invariant phrase(s): " + json.dumps(missing, ensure_ascii=False))

    temp = pathlib.Path(tempfile.mkdtemp(prefix="route_read_only_"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=temp, check=True)
        (temp / ".lazy-harness").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "logs").mkdir(parents=True, exist_ok=True)
        env = {**os.environ, "LAZY_HOST_ROOT": str(temp)}
        _run_task_router("typo in README", env=env)
        telemetry = temp / ".lazy-harness" / "logs" / "route-decisions.jsonl"
        if telemetry.exists():
            fail("task-router default mode must not create route telemetry")
        _run_task_router("typo in README", extra_args=["--log"], env=env)
        if not telemetry.exists():
            fail("task-router --log should append route telemetry")
        entry = json.loads(telemetry.read_text(encoding="utf-8").strip())
        if "message" in entry or "messagePreview" in entry:
            fail("route telemetry must not store raw message: " + json.dumps(entry, ensure_ascii=False))
        required_keys = ["messageHash", "scope", "risk", "gateMode", "recordCaptureMode", "routeVersion", "matchedSignals", "riskEvidence", "scopeEvidence", "pathEvidence", "gateReasonCode", "truncatedLikely", "changedFileKinds"]
        missing_keys = [key for key in required_keys if key not in entry]
        if missing_keys:
            fail("route telemetry missing key(s): " + json.dumps(missing_keys, ensure_ascii=False))

        completed = subprocess.run(
            ["bun", ".lazy-harness/scripts/task-router.ts", "--summary", "--format=json"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            fail("task-router summary failed:\n" + completed.stdout + completed.stderr)
        summary = json.loads(completed.stdout)
        if summary.get("totalRoutes") != 1:
            fail("route summary should count logged route: " + json.dumps(summary, ensure_ascii=False))
    finally:
        shutil.rmtree(temp, ignore_errors=True)

    print("✓ task-router read-only/log telemetry contract ok")


def check_task_router_fixtures() -> None:
    """Route fixtures protect workflow compression without safety reduction."""
    fixtures_path = LAZY / "fixtures" / "task-router" / "cases.json"
    if not fixtures_path.exists():
        fail("task-router fixtures missing: " + str(fixtures_path))
    cases = json.loads(fixtures_path.read_text(encoding="utf-8"))
    if len(cases) < 8:
        fail("task-router fixtures should cover critical route cases")

    for case in cases:
        result = _run_task_router(case["message"], case.get("changedFiles"))
        route = result.get("route", {})
        expect = case.get("expect", {})
        checks = {
            "intent": route.get("intent"),
            "scope": route.get("scope"),
            "risk": route.get("risk"),
            "confidence": route.get("confidence"),
            "recordSearchMode": route.get("recordSearch", {}).get("mode"),
            "recordCaptureMode": route.get("recordCapture", {}).get("mode"),
            "implMapTier": route.get("implementationMap", {}).get("tier"),
            "gateMode": route.get("gate", {}).get("mode"),
        }
        for key, expected in expect.items():
            if key == "layersInclude":
                missing_layers = [layer for layer in expected if layer not in route.get("affectedLayers", [])]
                if missing_layers:
                    fail(f"task-router fixture {case['name']} missing layers {missing_layers}: " + json.dumps(result, ensure_ascii=False))
            elif key == "nonNegotiablesInclude":
                missing_items = [item for item in expected if item not in route.get("nonNegotiables", [])]
                if missing_items:
                    fail(f"task-router fixture {case['name']} missing non-negotiables {missing_items}: " + json.dumps(result, ensure_ascii=False))
            elif key in checks and checks[key] != expected:
                fail(f"task-router fixture {case['name']} expected {key}={expected}, got {checks[key]}: " + json.dumps(result, ensure_ascii=False))

        if route.get("recordCapture", {}).get("mode") == "candidate" and "candidate-is-not-canonical" not in route.get("nonNegotiables", []):
            fail("task-router candidate route must include candidate-is-not-canonical: " + json.dumps(result, ensure_ascii=False))
        if route.get("gate", {}).get("mode") != "none" and "unresolved-gate-blocks-progress" not in route.get("nonNegotiables", []):
            fail("task-router gated route must preserve unresolved-gate-blocks-progress: " + json.dumps(result, ensure_ascii=False))

    print(f"✓ task-router fixtures ok ({len(cases)} cases)")


def check_lazy_route_cli_help() -> None:
    """lazy help must truthfully advertise self-test scope and route command."""
    completed = subprocess.run([".lazy-harness/bin/lazy", "--help"], cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        fail("lazy --help failed:\n" + completed.stdout + completed.stderr)
    help_text = completed.stdout
    required = ["test [--scope=auto|framework|host]", "capability add|list|resolve|candidates|audit", "gate-state list|clear-stale", "route --message", "route-summary", "route-audit", "hook-timings", "lifecycle-check", "lifecycle-parity", "lifecycle-fixture inspect|append|list", "Read-only workflow compression route"]
    missing = [phrase for phrase in required if phrase not in help_text]
    if missing:
        fail("lazy help missing route/scope phrase(s): " + json.dumps(missing, ensure_ascii=False) + "\n" + help_text)
    if "test [--profile=smoke|full]" in help_text:
        fail("lazy help still advertises unsupported self-test --profile")

    result = _run_task_router("typo in README")
    if result.get("route", {}).get("implementationMap", {}).get("tier") != "none":
        fail("lazy route trivial fixture should not require implementation map: " + json.dumps(result, ensure_ascii=False))
    risky = _run_task_router("Feat: 치료 기록 삭제 버튼 추가", ["src/main/trpc/routers/appointment.ts", "src/renderer/src/screens/Appointment/modal/TreatmentPatientDetailModal/index.tsx"])
    route = risky["route"]
    if route["risk"] != "high" or route["gate"]["mode"] != "option-gate" or "destructive-word" not in route["evidence"]["riskEvidence"] or "trpc-router" not in route["evidence"]["pathEvidence"]:
        fail("lazy route should flag destructive TRPC/UI commit evidence: " + json.dumps(risky, ensure_ascii=False))
    audit = subprocess.run([".lazy-harness/bin/lazy", "route-audit", "--commits=1", "--format=json"], cwd=ROOT, text=True, capture_output=True, check=False)
    if audit.returncode != 0 or json.loads(audit.stdout).get("mode") != "route-audit":
        fail("lazy route-audit should emit route-audit JSON:\n" + audit.stdout + audit.stderr)
    print("✓ lazy route CLI help ok")


def check_gate_state_cli_and_record_audit_source_guard() -> None:
    """Phase 3 readiness helpers protect runtime gate cleanup and source-arg mistakes."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-gate-state-"))
    try:
        state_dir = temp / ".lazy-harness" / "state"
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
        env = {**os.environ, "LAZY_HOST_ROOT": str(temp)}
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
        env = {**os.environ, "LAZY_HOST_ROOT": str(temp)}
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
        fixture_env = {**os.environ, "LAZY_HOST_ROOT": str(temp)}
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


def check_response_completed_auto_route_telemetry() -> None:
    """response.completed should automatically log route telemetry once per message_id."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="route_auto_"))
    try:
        shutil.copytree(ROOT / ".lazy-harness", temp / ".lazy-harness", ignore=shutil.ignore_patterns(".cache", "state"))
        subprocess.run(["git", "init", "-q"], cwd=temp, check=True)
        telemetry = temp / ".lazy-harness" / "logs" / "route-decisions.jsonl"
        if telemetry.exists():
            telemetry.unlink()
        timings = temp / ".lazy-harness" / "logs" / "hook-timings.jsonl"
        if timings.exists():
            timings.unlink()
        payload = {
            "last_user_message": "fix a button click behavior bug",
            "message_id": "auto-route-msg-1",
            "recent_tool_calls": [],
        }
        large_payload = {
            "last_user_message": "fix route telemetry for large response payloads",
            "message_id": "auto-route-msg-large",
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
                env={**os.environ, "LAZY_HOST_ROOT": str(temp), "LAZY_HOOK_TIMING_LOG": str(timings)},
            )
            if completed.returncode != 0:
                fail("response.completed hook should stay best-effort for auto route telemetry:\n" + completed.stdout + completed.stderr)
        large_completed = subprocess.run(
            [str(hook)],
            cwd=temp,
            input=json.dumps(large_payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "LAZY_HOST_ROOT": str(temp), "LAZY_HOOK_TIMING_LOG": str(timings)},
        )
        if large_completed.returncode != 0:
            fail("response.completed hook should tolerate live-sized payloads for auto route telemetry:\n" + large_completed.stdout + large_completed.stderr)
        if not telemetry.exists():
            fail("response.completed hook should auto-create route telemetry")
        lines = [line for line in telemetry.read_text(encoding="utf-8").splitlines() if line.strip()]
        entries = [json.loads(line) for line in lines]
        matching = [entry for entry in entries if entry.get("messageIdHash")]
        if len(matching) != 2:
            fail("response.completed auto telemetry should dedupe by message_id and tolerate live-sized payloads; got matching lines=" + str(len(matching)))
        entry = matching[0]
        if "message" in entry or "messagePreview" in entry:
            fail("auto route telemetry must not store raw user message: " + json.dumps(entry, ensure_ascii=False))
        if not entry.get("messageIdHash"):
            fail("auto route telemetry should include messageIdHash for dedupe: " + json.dumps(entry, ensure_ascii=False))
        if not timings.exists():
            fail("response.completed hook should create timing telemetry in measure-only mode")
        timing_entries = [json.loads(line) for line in timings.read_text(encoding="utf-8").splitlines() if line.strip()]
        components = {entry.get("component") for entry in timing_entries}
        if "route-telemetry" not in components or "hook-total" not in components:
            fail("hook timings should include route-telemetry and hook-total components: " + json.dumps(sorted(components), ensure_ascii=False))
        if not any(str(component).endswith("check-bdd-trigger.sh") for component in components):
            fail("hook timings should include lifecycle helper components that are not write-only fast-pathed")
        if any("durationMs" not in entry or "outputEmitted" not in entry or "exitCode" not in entry for entry in timing_entries):
            fail("hook timing entries missing required fields")
        summary_completed = subprocess.run(
            [str(temp / ".lazy-harness" / "bin" / "lazy"), "hook-timings", "--format=json", "--limit=100"],
            cwd=temp,
            env={**os.environ, "LAZY_HOST_ROOT": str(temp)},
            text=True,
            capture_output=True,
            check=False,
        )
        if summary_completed.returncode != 0:
            fail("lazy hook-timings summary failed:\n" + summary_completed.stdout + summary_completed.stderr)
        summary = json.loads(summary_completed.stdout)
        if summary.get("mode") != "hook-timing-summary" or summary.get("rows", 0) < len(timing_entries):
            fail("hook timing summary should report timing rows: " + summary_completed.stdout[:500])

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
            env = {**os.environ, "LAZY_HOST_ROOT": str(temp), "LAZY_HOOK_TIMING_LOG": str(log_path)}
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
            env={**os.environ, "LAZY_HOST_ROOT": str(temp), "LAZY_HOOK_TIMING_LOG": str(temp / ".lazy-harness" / "logs" / "hook-timings-correction.jsonl")},
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
            env={**os.environ, "LAZY_HOST_ROOT": str(temp), "LAZY_HOOK_TIMING_LOG": str(temp / ".lazy-harness" / "logs" / "hook-timings-correction-captured.jsonl")},
        )
        if captured_completed.returncode != 0:
            fail("captured user correction fixture hook failed:\n" + captured_completed.stdout + captured_completed.stderr)
        if "User correction capture gate" in captured_completed.stdout:
            fail("user correction with durable capture should not trigger correction gate:\n" + captured_completed.stdout + captured_completed.stderr)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ response.completed auto route telemetry ok")


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
    tdd_shadow_queue = LAZY / "questions" / f"__tmp_shadow_tdd_{os.getpid()}.xml"
    aftershock_queue = LAZY / "questions" / f"__tmp_hook_aftershock_{os.getpid()}.xml"
    aftershock_shadow_queue = LAZY / "questions" / f"__tmp_shadow_aftershock_{os.getpid()}.xml"
    bdd_queue = LAZY / "questions" / f"__tmp_hook_bdd_{os.getpid()}.xml"
    bdd_shadow_queue = LAZY / "questions" / f"__tmp_shadow_bdd_{os.getpid()}.xml"
    generic_queue = LAZY / "questions" / f"__tmp_hook_generic_{os.getpid()}.xml"
    decisions = LAZY / "logs" / f"__tmp_hook_decisions_{os.getpid()}.jsonl"
    shadow_decisions = LAZY / "logs" / f"__tmp_shadow_decisions_{os.getpid()}.jsonl"
    bdd_state = ROOT / ".lazy-harness" / "state" / "open-gates.json"
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


def check_record_audit_cli() -> None:
    """Record audit must summarize host-owned records, markers, JSONL, Project Profile, and graph hygiene."""
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        host = base / "host"
        source = base / "source"
        for path in [
            host / ".lazy-harness" / "domain",
            host / ".lazy-harness" / "project",
            host / ".lazy-harness" / "knowledge",
            host / ".lazy-harness" / "logs",
            source / ".lazy-harness" / "domain",
            source / ".lazy-harness" / "project",
            source / ".lazy-harness" / "knowledge",
            source / ".lazy-harness" / "logs",
        ]:
            path.mkdir(parents=True)
        (source / ".lazy-harness" / "domain" / "base.md").write_text("base\n", encoding="utf-8")
        (source / ".lazy-harness" / "domain" / "framework-only.md").write_text("framework source only\n", encoding="utf-8")
        (host / ".lazy-harness" / "domain" / "base.md").write_text("base changed\n", encoding="utf-8")
        (host / ".lazy-harness" / "domain" / "host.md").write_text("host only TODO\n", encoding="utf-8")
        (host / ".lazy-harness" / "project" / "profile.xml").write_text(
            '<projectProfile><purpose status="needs-interview"/><owner status="confirmed">x</owner></projectProfile>\n',
            encoding="utf-8",
        )
        (host / ".lazy-harness" / "knowledge" / "graph.jsonl").write_text(
            '{"id":"a","path":".lazy-harness/domain/host.md"}\n'
            '{"id":"b","path":".lazy-harness/domain/missing.md"}\n'
            '{"id":"c","path":".lazy-harness/domain/a.md,.lazy-harness/domain/b.md"}\n'
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
        if totals.get("hostUnique") != 3 or totals.get("hostChanged") != 1 or totals.get("hostOwnedOrChanged") != 4:
            fail("record-audit should compare host-owned/changed records: " + json.dumps(totals, ensure_ascii=False))
        profile = result.get("projectProfile", {})
        if profile.get("artifactsComplete") is not False or profile.get("answersComplete") is not False or profile.get("needsInterviewFields") != 1 or profile.get("confirmedFields") != 1:
            fail("record-audit should split Project Profile artifact and answer completeness")
        graph = result.get("graph", {})
        if graph.get("rows") != 4 or graph.get("missingPaths") != 2 or graph.get("sourceOnlyPaths") != 1 or graph.get("commaJoinedPaths") != 1:
            fail("record-audit should report actionable graph hygiene and source-only paths")
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


def check_relevant_record_query_cli() -> None:
    """Relevant-record query should emit compact digest entries without tool keys."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-relevant-query-"))
    try:
        write_digest_fixture(temp)
        script = LAZY / "scripts" / "relevant-record-query.ts"
        completed = subprocess.run(
            [
                "bun",
                str(script),
                "--root",
                str(temp),
                "--message",
                "PR description 작성해줘",
                "--format",
                "json",
                "--require-digest",
                "--token-budget",
                "300",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            fail("relevant-record-query CLI failed:\n" + completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        entries = result.get("digest", {}).get("entries", [])
        if not entries:
            fail("relevant-record-query did not return digest entries:\n" + completed.stdout)
        first = entries[0]
        if first.get("recordPath") != ".lazy-harness/ssot/pr-description-format.md":
            fail("relevant-record-query returned wrong record:\n" + completed.stdout)
        body = json.dumps(first, ensure_ascii=False)
        if "Why, What, and Task" not in body or "gh or bash" not in body:
            fail("relevant-record-query missed digest bullets:\n" + completed.stdout)
        if result.get("digest", {}).get("estimatedTokens", 9999) > 300:
            fail("relevant-record-query exceeded token budget:\n" + completed.stdout)

        equals_completed = subprocess.run(
            [
                "bun",
                str(script),
                f"--root={temp}",
                "--message=PR description 작성해줘",
                "--format=json",
                "--require-digest",
                "--token-budget=300",
                "--layer=SSOT",
                "--status=active",
                "--limit=1",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if equals_completed.returncode != 0:
            fail("relevant-record-query --flag=value syntax failed:\n" + equals_completed.stdout + equals_completed.stderr)
        equals_result = json.loads(equals_completed.stdout)
        equals_entries = equals_result.get("digest", {}).get("entries", [])
        if len(equals_entries) != 1 or equals_entries[0].get("recordPath") != ".lazy-harness/ssot/pr-description-format.md":
            fail("relevant-record-query --flag=value syntax returned wrong entries:\n" + equals_completed.stdout)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ relevant-record-query CLI digest ok")


def check_context_delivery_contract_sdd() -> None:
    """Native Context Broker Phase 1 must have a stable packet contract."""
    sdd_path = LAZY / "spec" / "platform" / "context-delivery-contract.md"
    schema_path = LAZY / "schemas" / "context-delivery-packet.schema.json"
    if not sdd_path.exists():
        fail("Context Delivery Contract SDD missing: " + str(sdd_path))
    if not schema_path.exists():
        fail("Context Delivery Packet schema missing: " + str(schema_path))

    text = sdd_path.read_text(encoding="utf-8")
    required_phrases = [
        "## Rule digest",
        "raw hit",
        "Normalized evidence",
        "Context Delivery Packet",
        "digest-only",
        "self-resolve-before-answer",
        "self-resolve-before-change",
        "delegate-search",
        "requiredRead",
        "optionalRead",
        "candidateMeanings",
        "fallbackSearches",
        "system_reminder",
        "예약시트",
        "ReservationTable",
        "privacy",
        "fail-open",
        "Searcher subagent handoff",
        "Implementation map",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in text]
    if missing:
        fail("Context Delivery Contract SDD missing required content: " + json.dumps(missing, ensure_ascii=False))

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("title") != "ContextDeliveryPacket":
        fail("Context Delivery Packet schema title mismatch")
    required = set(schema.get("required", []))
    expected_required = {
        "schemaVersion",
        "generatedAt",
        "instructionLevel",
        "candidateMeanings",
        "queries",
        "requiredRead",
        "optionalRead",
        "confidence",
        "fallbackSearches",
        "instruction",
    }
    if not expected_required.issubset(required):
        fail("Context Delivery Packet schema missing required fields: " + json.dumps(sorted(expected_required - required)))
    levels = set(schema.get("definitions", {}).get("instructionLevel", {}).get("enum", []))
    expected_levels = {"digest-only", "self-resolve-before-answer", "self-resolve-before-change", "delegate-search"}
    if levels != expected_levels:
        fail("Context Delivery Packet instruction levels mismatch: " + json.dumps(sorted(levels)))
    read_kinds = set(schema.get("definitions", {}).get("readKind", {}).get("enum", []))
    for expected in ["record", "project-profile", "graph-edge", "source-file", "symbol", "test", "plan", "schema", "generated-index"]:
        if expected not in read_kinds:
            fail("Context Delivery Packet schema missing read kind: " + expected)

    sample_packet = {
        "schemaVersion": "1.0",
        "generatedAt": "2026-06-01T00:00:00.000Z",
        "instructionLevel": "self-resolve-before-change",
        "resolvedPhrase": "예약시트",
        "candidateMeanings": [
            {"label": "ReservationTable / reservation sheet", "confidence": 0.76, "why": "multilingual surface candidate"}
        ],
        "queries": [
            {"query": "예약시트 예약표 예약관리", "source": "llm-expansion", "purpose": "Korean aliases"},
            {"query": "reservation sheet booking table ReservationTable", "source": "llm-expansion", "purpose": "English and code aliases"},
        ],
        "requiredRead": [
            {
                "path": ".lazy-harness/behavior/reservation-management.md",
                "kind": "record",
                "reason": "Confirm UI behavior before editing.",
                "confidence": 0.82,
                "whyMatched": "Matched Korean and English reservation aliases.",
                "matchedQueries": ["예약시트", "reservation sheet"],
            }
        ],
        "optionalRead": [],
        "confidence": 0.76,
        "fallbackSearches": ["rg -n \"예약|reservation|booking|appointment|schedule\" .lazy-harness src tests"],
        "instruction": "Read requiredRead before answering or editing.",
    }
    for field in expected_required:
        if field not in sample_packet:
            fail("sample Context Delivery Packet missing field: " + field)
    if sample_packet["instructionLevel"] not in expected_levels:
        fail("sample Context Delivery Packet uses invalid instructionLevel")
    if not 0 <= sample_packet["confidence"] <= 1:
        fail("sample Context Delivery Packet confidence must be 0..1")
    print("✓ context delivery contract SDD ok")


def check_context_delivery_metadata_phase2() -> None:
    """Phase 2 metadata should bridge aliases/profile navigation into retrieval evidence."""
    digest_path = LAZY / "spec" / "platform" / "record-digest-format.md"
    query_path = LAZY / "spec" / "platform" / "relevant-record-query.md"
    profile_path = LAZY / "spec" / "platform" / "project-profile.md"
    schema_path = LAZY / "schemas" / "relevant-record-index.schema.json"
    fixture_path = LAZY / "fixtures" / "context-delivery" / "feature-navigation-reservation-surface.xml"
    for path in [digest_path, query_path, profile_path, schema_path, fixture_path]:
        if not path.exists():
            fail("Context Delivery Phase 2 expected artifact missing: " + str(path))

    digest_text = digest_path.read_text(encoding="utf-8")
    for phrase in [
        "## Optional retrieval metadata",
        "Aliases",
        "Surface terms",
        "Implementation hints",
        "예약시트",
        "ReservationTable",
        "aliases[]",
        "implementationHints.routeHints[]",
    ]:
        if phrase not in digest_text:
            fail("record-digest-format missing Phase 2 retrieval metadata phrase: " + phrase)

    query_text = query_path.read_text(encoding="utf-8")
    for phrase in [
        "digest aliases/surface terms",
        "Project Profile feature navigation",
        "feature-navigation.xml",
        "예약시트",
        "self-resolve-before-change",
    ]:
        if phrase not in query_text:
            fail("relevant-record-query missing Phase 2 retrieval phrase: " + phrase)

    profile_text = profile_path.read_text(encoding="utf-8")
    for phrase in [
        "## Rule digest",
        "## Feature navigation as retrieval source",
        "feature-navigation.xml",
        "예약시트",
        "reservation sheet",
        "ReservationTable",
        "requiredRead",
    ]:
        if phrase not in profile_text:
            fail("project-profile missing Context Delivery feature navigation phrase: " + phrase)

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    record_props = schema.get("definitions", {}).get("recordEntry", {}).get("properties", {})
    for prop in ["aliases", "surfaceTerms", "implementationHints"]:
        if prop not in record_props:
            fail("relevant-record-index schema missing Phase 2 property: " + prop)
    hint_props = record_props.get("implementationHints", {}).get("properties", {})
    for prop in ["routeHints", "componentHints", "fileHints", "symbolHints", "testHints"]:
        if prop not in hint_props:
            fail("relevant-record-index implementationHints missing property: " + prop)

    root = ET.parse(fixture_path).getroot()
    feature = root.find("feature")
    if feature is None or feature.attrib.get("id") != "reservations":
        fail("context delivery feature-navigation fixture missing reservations feature")
    aliases = [node.text for node in feature.findall("./aliases/alias")]
    for expected in ["예약시트", "예약표", "reservation sheet", "ReservationTable"]:
        if expected not in aliases:
            fail("context delivery feature-navigation fixture missing alias: " + expected)
    paths = [node.text for node in feature.findall(".//path")]
    if "src/features/reservations/ReservationTable.tsx" not in paths:
        fail("context delivery feature-navigation fixture missing source path")
    if "tests/reservations/reservation-table.test.tsx" not in paths:
        fail("context delivery feature-navigation fixture missing test path")
    records = [node.text for node in feature.findall("./records/record")]
    if ".lazy-harness/behavior/reservation-management.md" not in records:
        fail("context delivery feature-navigation fixture missing BDD record path")

    manifest = json.loads((LAZY / "manifests" / "init-categories.json").read_text(encoding="utf-8"))
    category_a_items = manifest.get("categories", {}).get("A", {}).get("items", [])
    category_a_paths = {item.get("path") for item in category_a_items}
    if "spec/platform/project-profile.md" not in category_a_paths:
        fail("Context Delivery Phase 2 requires project-profile SDD to sync to hosts")
    fixture_item = next((item for item in category_a_items if item.get("path") == "fixtures/"), {})
    if "context-delivery/*.xml" not in fixture_item.get("glob", []):
        fail("Context Delivery Phase 2 fixture glob missing from manifest")
    print("✓ context delivery metadata Phase 2 ok")


def check_context_index_generator_phase3() -> None:
    """Phase 3 context-index generator should produce deterministic derived cache output."""
    schema_path = LAZY / "schemas" / "context-index.schema.json"
    script_path = LAZY / "scripts" / "context-index.ts"
    if not schema_path.exists():
        fail("Context index schema missing: " + str(schema_path))
    if not script_path.exists():
        fail("Context index generator missing: " + str(script_path))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("title") != "ContextIndex":
        fail("Context index schema title mismatch")
    record_props = schema.get("definitions", {}).get("recordEntry", {}).get("properties", {})
    for prop in ["recordPath", "digest", "aliases", "surfaceTerms", "implementationHints", "graphIds", "projectProfileFeatureIds"]:
        if prop not in record_props:
            fail("Context index schema missing record property: " + prop)

    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-context-index-"))
    try:
        (temp / ".lazy-harness" / "behavior").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "project").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "knowledge").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "generated").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "behavior" / "reservation-management.md").write_text(
            "# Reservation Management\n\n"
            "## Rule digest\n\n"
            "- Status: active\n"
            "- Layer: BDD\n"
            "- Scope: host-project\n"
            "- Applies when:\n"
            "  - user asks about reservation management UI\n"
            "- Must:\n"
            "  - confirm reservation table behavior before editing\n"
            "- Aliases:\n"
            "  - 예약시트\n"
            "  - reservation sheet\n"
            "- Surface terms:\n"
            "  - 예약표\n"
            "- Implementation hints:\n"
            "  - Routes: `/reservations`\n"
            "  - Components: `ReservationTable`\n"
            "  - Files: `src/features/reservations/ReservationTable.tsx`\n"
            "  - Tests: `tests/reservations/reservation-table.test.tsx`\n"
            "- Related records:\n"
            "  - `.lazy-harness/spec/reservation-management.md`\n\n"
            "## Implementation map\n\n"
            "- Component: `ReservationManagementPage`\n"
            "- Source: `src/features/reservations/ReservationManagementPage.tsx`\n",
            encoding="utf-8",
        )
        fixture = LAZY / "fixtures" / "context-delivery" / "feature-navigation-reservation-surface.xml"
        shutil.copy2(fixture, temp / ".lazy-harness" / "project" / "feature-navigation.xml")
        (temp / ".lazy-harness" / "knowledge" / "graph.jsonl").write_text(
            json.dumps({
                "id": "kg_reservation_behavior_impl",
                "source": ".lazy-harness/behavior/reservation-management.md",
                "relation": "implemented_by",
                "target": "src/features/reservations/ReservationTable.tsx",
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
            fail("context-index generator failed:\n" + first.stdout + first.stderr)
        if first.stdout != second.stdout:
            fail("context-index generator output is not deterministic")
        index = json.loads(first.stdout)
        if index.get("schemaVersion") != "1.0" or index.get("source", {}).get("method") != "context-index-v1":
            fail("context-index output missing schema/method")
        records = index.get("records", [])
        if len(records) != 1:
            fail("context-index fixture should produce exactly one record")
        record = records[0]
        for expected in ["예약시트", "예약표", "reservation sheet", "ReservationTable"]:
            if expected not in record.get("aliases", []) and expected not in record.get("surfaceTerms", []):
                fail("context-index record missing retrieval term: " + expected)
        hints = record.get("implementationHints", {})
        if "ReservationTable" not in hints.get("componentHints", []):
            fail("context-index missing component hint")
        if "src/features/reservations/ReservationTable.tsx" not in hints.get("fileHints", []):
            fail("context-index missing file hint")
        if "tests/reservations/reservation-table.test.tsx" not in hints.get("testHints", []):
            fail("context-index missing test hint")
        if "kg_reservation_behavior_impl" not in record.get("graphIds", []):
            fail("context-index missing graph edge id")
        if "reservations" not in record.get("projectProfileFeatureIds", []):
            fail("context-index missing project profile feature id")
        if index.get("projectProfile", {}).get("featureNavigationPath") != ".lazy-harness/project/feature-navigation.xml":
            fail("context-index missing feature navigation path")

        written = run_index("--write", "--output", str(temp / ".lazy-harness" / "generated" / "context-index.json"), "--format=md")
        if written.returncode != 0 or "Context index" not in written.stdout:
            fail("context-index --write markdown output failed:\n" + written.stdout + written.stderr)
        if not (temp / ".lazy-harness" / "generated" / "context-index.json").exists():
            fail("context-index --write did not create generated cache")
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ context-index generator Phase 3 ok")


def check_context_delivery_dual_mode_phase4() -> None:
    """Phase 4 should produce packet-shaped dual-mode required-read context."""
    delivery_script = LAZY / "scripts" / "context-delivery.ts"
    index_script = LAZY / "scripts" / "context-index.ts"
    packet_schema = LAZY / "schemas" / "context-delivery-packet.schema.json"
    if not delivery_script.exists():
        fail("Context Delivery packet generator missing: " + str(delivery_script))
    schema = json.loads(packet_schema.read_text(encoding="utf-8"))
    levels = set(schema.get("definitions", {}).get("instructionLevel", {}).get("enum", []))
    if "self-resolve-before-change" not in levels:
        fail("Context Delivery packet schema missing self-resolve-before-change")

    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-context-delivery-"))
    try:
        (temp / ".lazy-harness" / "behavior").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "project").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "knowledge").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "generated").mkdir(parents=True, exist_ok=True)
        (temp / "src" / "features" / "reservations").mkdir(parents=True, exist_ok=True)
        (temp / "tests" / "reservations").mkdir(parents=True, exist_ok=True)
        (temp / "src" / "features" / "reservations" / "ReservationTable.tsx").write_text("export function ReservationTable() { return null }\n", encoding="utf-8")
        (temp / "tests" / "reservations" / "reservation-table.test.tsx").write_text("test('reservation table', () => {})\n", encoding="utf-8")
        (temp / ".lazy-harness" / "behavior" / "reservation-management.md").write_text(
            "# Reservation Management\n\n"
            "## Rule digest\n\n"
            "- Status: active\n"
            "- Layer: BDD\n"
            "- Scope: host-project\n"
            "- Applies when:\n"
            "  - user asks about reservation management UI\n"
            "- Must:\n"
            "  - confirm reservation table behavior before editing\n"
            "- Aliases:\n"
            "  - 예약시트\n"
            "  - reservation sheet\n"
            "- Surface terms:\n"
            "  - 예약표\n"
            "- Implementation hints:\n"
            "  - Routes: `/reservations`\n"
            "  - Components: `ReservationTable`\n"
            "  - Files: `src/features/reservations/ReservationTable.tsx`\n"
            "  - Tests: `tests/reservations/reservation-table.test.tsx`\n"
            "- Related records:\n"
            "  - `.lazy-harness/spec/reservation-management.md`\n",
            encoding="utf-8",
        )
        fixture = LAZY / "fixtures" / "context-delivery" / "feature-navigation-reservation-surface.xml"
        shutil.copy2(fixture, temp / ".lazy-harness" / "project" / "feature-navigation.xml")
        (temp / ".lazy-harness" / "knowledge" / "graph.jsonl").write_text(
            json.dumps({
                "id": "kg_reservation_behavior_impl",
                "source": ".lazy-harness/behavior/reservation-management.md",
                "relation": "implemented_by",
                "target": "src/features/reservations/ReservationTable.tsx",
            }, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        def run_delivery(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["bun", str(delivery_script), "--root", str(temp), *args],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        first = run_delivery("--message", "예약시트 고쳐줘", "--format", "json")
        if first.returncode != 0:
            fail("context-delivery source-scan fallback failed:\n" + first.stdout + first.stderr)
        packet = json.loads(first.stdout)
        if packet.get("instructionLevel") != "self-resolve-before-change":
            fail("context-delivery should require self-resolve-before-change for 예약시트 change request")
        queries_text = json.dumps(packet.get("queries", []), ensure_ascii=False)
        for expected in ["예약시트", "예약표", "reservation sheet", "ReservationTable"]:
            if expected not in queries_text:
                fail("context-delivery missing expanded query term: " + expected)
        required = packet.get("requiredRead", [])
        required_pairs = {(item.get("kind"), item.get("path")) for item in required}
        for expected in [
            ("record", ".lazy-harness/behavior/reservation-management.md"),
            ("project-profile", ".lazy-harness/project/feature-navigation.xml"),
            ("source-file", "src/features/reservations/ReservationTable.tsx"),
            ("test", "tests/reservations/reservation-table.test.tsx"),
        ]:
            if expected not in required_pairs:
                fail("context-delivery requiredRead missing " + repr(expected) + ":\n" + json.dumps(required, ensure_ascii=False, indent=2))
        if not all(item.get("whyMatched") and item.get("matchedQueries") for item in required):
            fail("context-delivery requiredRead items must include whyMatched and matchedQueries")
        if not any("contextIndexSource=source-scan" == note for note in packet.get("notes", [])):
            fail("context-delivery should note source-scan fallback when generated index is absent")

        index_write = subprocess.run(
            ["bun", str(index_script), "--root", str(temp), "--write", "--format=json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if index_write.returncode != 0:
            fail("context-index write for context-delivery fixture failed:\n" + index_write.stdout + index_write.stderr)
        second = run_delivery("--message=예약시트 고쳐줘", "--format=json")
        packet_from_index = json.loads(second.stdout)
        if not any("contextIndexSource=generated-index" == note for note in packet_from_index.get("notes", [])):
            fail("context-delivery should consume generated context index when present")
        markdown = run_delivery("--message", "예약시트 고쳐줘", "--format", "md")
        if markdown.returncode != 0 or "Context Delivery Packet" not in markdown.stdout or "Required read before answer/change" not in markdown.stdout:
            fail("context-delivery markdown rendering missing required sections:\n" + markdown.stdout + markdown.stderr)

        framework_only = pathlib.Path(tempfile.mkdtemp(prefix="lazy-context-delivery-framework-only-"))
        try:
            (framework_only / ".lazy-harness" / "spec" / "platform").mkdir(parents=True, exist_ok=True)
            (framework_only / ".lazy-harness" / "knowledge").mkdir(parents=True, exist_ok=True)
            (framework_only / ".lazy-harness" / "spec" / "platform" / "context-delivery-contract.md").write_text(
                "# SDD - Context Delivery Contract\n\n"
                "## Rule digest\n\n"
                "- Status: active\n"
                "- Layer: SDD\n"
                "- Scope: framework-global\n"
                "- Applies when:\n"
                "  - implementing Context Delivery Packet retrieval\n"
                "- Must:\n"
                "  - use `예약시트` only as an example ambiguous surface term\n\n"
                "## `예약시트` example\n\n예약시트 고쳐줘\n",
                encoding="utf-8",
            )
            no_host = subprocess.run(
                ["bun", str(delivery_script), "--root", str(framework_only), "--message", "예약시트 고쳐줘", "--format=json"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if no_host.returncode != 0:
                fail("context-delivery framework-only negative fixture failed:\n" + no_host.stdout + no_host.stderr)
            no_host_packet = json.loads(no_host.stdout)
            if any(item.get("path") == ".lazy-harness/spec/platform/context-delivery-contract.md" for item in no_host_packet.get("requiredRead", [])):
                fail("framework-global example record must not become requiredRead for host product-surface request")
            if not no_host_packet.get("fallbackSearches"):
                fail("framework-only product-surface request should retain fallback searches")
        finally:
            shutil.rmtree(framework_only, ignore_errors=True)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ context-delivery dual-mode Phase 4 ok")


def check_message_received_hook_context_injection() -> None:
    """message.received hook should emit same-turn system reminder inject JSON from digests."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-message-received-"))
    try:
        write_digest_fixture(temp)
        (temp / ".lazy-harness" / "scripts").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "hooks" / "lifecycle").mkdir(parents=True, exist_ok=True)
        shutil.copy2(LAZY / "scripts" / "relevant-record-query.ts", temp / ".lazy-harness" / "scripts" / "relevant-record-query.ts")
        hook = temp / ".lazy-harness" / "hooks" / "lifecycle" / "on-message-received.sh"
        shutil.copy2(LAZY / "hooks" / "lifecycle" / "on-message-received.sh", hook)
        hook.chmod(0o755)
        payload = {
            "event": "message.received",
            "session_id": "s-test",
            "message_id": "m-test",
            "working_dir": str(temp),
            "last_user_message": "PR description 작성해줘",
            "recent_tool_calls": [],
            "turn_count": 1,
        }
        completed = subprocess.run(
            [str(hook)],
            cwd=temp,
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "LAZY_HOST_ROOT": str(temp)},
        )
        if completed.returncode != 0:
            fail("message.received hook should fail-open with exit 0:\n" + completed.stdout + completed.stderr)
        output = completed.stdout.strip()
        if not output:
            fail("message.received hook did not emit inject JSON")
        data = json.loads(output)
        body = data.get("inject", {}).get("body", "")
        if data.get("inject", {}).get("format") != "system_reminder" or "Why, What, and Task" not in body:
            fail("message.received hook output missing digest body:\n" + output)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ message.received hook context injection ok")


def check_response_rule_audit_from_surfaced_digest() -> None:
    """Phase 4: response.completed should audit surfaced digest misses and stay silent on clean turns."""
    temp = pathlib.Path(tempfile.mkdtemp(prefix="lazy-response-rule-audit-"))
    try:
        write_digest_fixture(temp)
        (temp / ".lazy-harness" / "scripts").mkdir(parents=True, exist_ok=True)
        (temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers").mkdir(parents=True, exist_ok=True)
        shutil.copy2(LAZY / "scripts" / "relevant-record-query.ts", temp / ".lazy-harness" / "scripts" / "relevant-record-query.ts")
        hook = temp / ".lazy-harness" / "hooks" / "lifecycle" / "on-message-received.sh"
        shutil.copy2(LAZY / "hooks" / "lifecycle" / "on-message-received.sh", hook)
        hook.chmod(0o755)
        helper = temp / ".lazy-harness" / "hooks" / "lifecycle" / "helpers" / "check-response-rule-audit.py"
        shutil.copy2(LAZY / "hooks" / "lifecycle" / "helpers" / "check-response-rule-audit.py", helper)
        helper.chmod(0o755)

        message_payload = {
            "event": "message.received",
            "session_id": "phase4-session",
            "message_id": "phase4-pr-message",
            "working_dir": str(temp),
            "last_user_message": "PR description 작성해줘",
        }
        injected = subprocess.run(
            [str(hook)],
            cwd=temp,
            input=json.dumps(message_payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "LAZY_HOST_ROOT": str(temp)},
        )
        if injected.returncode != 0 or not injected.stdout.strip():
            fail("message.received hook should emit digest before response-rule audit:\n" + injected.stdout + injected.stderr)
        inject_body = json.loads(injected.stdout).get("inject", {}).get("body", "")
        if "Why, What, and Task" not in inject_body:
            fail("message.received hook did not surface PR digest needed by audit:\n" + injected.stdout)

        journal = temp / ".lazy-harness" / "state" / "surfaced-rule-digests.jsonl"
        if not journal.exists():
            fail("message.received hook should write surfaced digest journal")
        journal_text = journal.read_text(encoding="utf-8")
        if "PR description 작성해줘" in journal_text:
            fail("surfaced digest journal must not store raw user message")
        journal_rows = [json.loads(line) for line in journal_text.splitlines() if line.strip()]
        if not journal_rows or journal_rows[-1].get("messageIdHash") is None:
            fail("surfaced digest journal should include safe message id hash")

        def run_helper(payload: dict) -> str:
            completed = subprocess.run(
                [str(helper), json.dumps(payload, ensure_ascii=False)],
                cwd=temp,
                text=True,
                capture_output=True,
                check=False,
                env={**os.environ, "LAZY_HOST_ROOT": str(temp)},
            )
            if completed.returncode != 0:
                fail("response rule audit helper exit changed:\n" + completed.stdout + completed.stderr)
            return completed.stdout

        ignored_pr = run_helper({
            "message_id": "phase4-pr-message",
            "recent_tool_calls": [
                {"name": "mcp__github__create_pull_request", "arguments": {"title": "Fixture", "body": "No structured body"}},
            ],
        })
        if "Response rule audit" not in ignored_pr or "Why / What / Task" not in ignored_pr:
            fail("response rule audit should catch surfaced PR rule miss:\n" + ignored_pr)

        clean_pr = run_helper({
            "message_id": "phase4-pr-message",
            "recent_tool_calls": [
                {"name": "mcp__github__create_pull_request", "arguments": {"title": "Fixture", "body": "Why:\n- because\n\nWhat:\n- changed\n\nTask:\n- done"}},
            ],
        })
        if clean_pr.strip():
            fail("response rule audit should stay silent when surfaced PR rule is satisfied:\n" + clean_pr)

        # Manual journal row for a record-completion obligation not tied to PR.
        missing_capture_id = "phase4-record-missing"
        import hashlib
        journal.write_text(journal.read_text(encoding="utf-8") + json.dumps({
            "schemaVersion": "1.0",
            "event": "message.received.digest",
            "epochSeconds": 9999999999,
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
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    print("✓ response rule audit from surfaced digest ok")


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
        (check_jcode_wiring_repairs_stale_defaults, "BOTH"),
        (check_jcode_wiring_repairs_markerless_bash_hook_default, "BOTH"),
        (check_jcode_wiring_removes_rejected_layer2_block, "BOTH"),
        (check_jcode_wiring_message_received_hook, "BOTH"),
        (check_manifest_syncs_python_lifecycle_helpers, "BOTH"),
        (check_jcode_dev_hooks_are_nonblocking, "BOTH"),
        (check_rule_action_boundary_legacy_no_project_policy, "BOTH"),
        (check_jcode_wiring_bash_safety_only_hook, "BOTH"),
        (check_guidance_ladder_hard_stop_promotion, "BOTH"),
        (check_jcode_project_profile_skill_wrapper, "BOTH"),
        (check_jcode_doc_ingest_skill_wrapper, "BOTH"),
        (check_pre_commit_runs_lazy_test, "BOTH"),
        (check_task_router_read_only_contract, "BOTH"),
        (check_task_router_fixtures, "BOTH"),
        (check_lazy_route_cli_help, "BOTH"),
        (check_gate_state_cli_and_record_audit_source_guard, "BOTH"),
        (check_lifecycle_fixture_intake_cli, "BOTH"),
        (check_capability_registry_cli_phase1, "BOTH"),
        (check_response_completed_auto_route_telemetry, "BOTH"),
        (check_standalone_source_detection_uses_markers, "BOTH"),
        (check_lazy_host_root_resolution, "BOTH"),
        (check_skill_create_cli, "BOTH"),
        (check_tdd_cross_verify, "FRAMEWORK_ONLY"),
        (check_affected_test_runner, "FRAMEWORK_ONLY"),
        (check_aftershock_reanalysis, "FRAMEWORK_ONLY"),
        (check_lifecycle_hook_integration, "FRAMEWORK_ONLY"),
        (check_lifecycle_parity_runner, "FRAMEWORK_ONLY"),
        (check_knowledge_intake, "FRAMEWORK_ONLY"),
        (check_document_resource_ingestion_inspect, "FRAMEWORK_ONLY"),
        (check_project_profile_inspect, "FRAMEWORK_ONLY"),
        (check_record_audit_cli, "FRAMEWORK_ONLY"),
        (check_graph_hygiene_cli, "FRAMEWORK_ONLY"),
        (check_real_feature_walkthrough, "FRAMEWORK_ONLY"),
        (check_e2e_demo, "FRAMEWORK_ONLY"),
        (check_triggers, "FRAMEWORK_ONLY"),
        (check_layer_impact_gate, "FRAMEWORK_ONLY"),
        (check_reference_resolver, "FRAMEWORK_ONLY"),
        (check_search_provider_canonical_record_dirs, "FRAMEWORK_ONLY"),
        (check_relevant_record_query_cli, "FRAMEWORK_ONLY"),
        (check_context_delivery_contract_sdd, "BOTH"),
        (check_context_delivery_metadata_phase2, "BOTH"),
        (check_context_index_generator_phase3, "BOTH"),
        (check_context_delivery_dual_mode_phase4, "BOTH"),
        (check_message_received_hook_context_injection, "FRAMEWORK_ONLY"),
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
