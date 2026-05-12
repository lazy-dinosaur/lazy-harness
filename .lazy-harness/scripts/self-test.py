#!/usr/bin/env python3
"""Lazy-Harness reproducible self-test.

Checks the framework-owned operational invariants defined by ADR 0022:
- every .lazy-harness XML file parses
- permanent JSONL logs parse line-by-line
- trigger fixtures produce DDD/SDD/BDD/SSOT candidates
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
LAZY = ROOT / ".lazy-harness"


def fail(message: str) -> None:
    print(f"✗ {message}")
    raise SystemExit(1)


def check_doctor_smoke() -> None:
    command = ["python3", ".lazy-harness/scripts/doctor.py", "--profile", "smoke"]
    completed = subprocess.run(command, cwd=ROOT, check=True, text=True, capture_output=True)
    if "lazy-harness doctor ok (smoke)" not in completed.stdout:
        fail("doctor smoke did not report ok:\n" + completed.stdout)
    print("✓ doctor smoke ok")


def check_doctor_c17_negative() -> None:
    fixture = LAZY / "scripts" / f"__doctor_c17_negative_tmp_{os.getpid()}.py"
    forbidden_call = 'fe' + 'tch' + '("' + 'https' + '://api.' + 'figma' + '.com/v1/files/example")\n'
    fixture.write_text(forbidden_call, encoding="utf-8")
    try:
        env = {**os.environ, "LAZY_HARNESS_DOCTOR_INCLUDE_NEGATIVE": "1"}
        completed = subprocess.run(
            ["python3", ".lazy-harness/scripts/doctor.py", "--profile", "full"],
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

    subprocess.run(["python3", ".lazy-harness/scripts/doctor.py", "--profile", "full"], cwd=ROOT, check=True, text=True, capture_output=True)
    print("✓ doctor C17 negative fixture ok")


def check_doctor_package_health() -> None:
    completed = subprocess.run(
        ["python3", ".lazy-harness/scripts/doctor.py", "--profile", "full", "--format", "json"],
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


def run_response_completed_hook(payload: dict, queue: pathlib.Path, decisions: pathlib.Path | None = None) -> str:
    env = {**os.environ, "LAZY_HARNESS_QUESTION_QUEUE": str(queue.relative_to(ROOT))}
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
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        fail(f"response.completed hook exit changed: {completed.returncode}")
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
        ], queue=queue, expect_code=2)
        if deduped.get("questions") != []:
            fail("tdd-cross-verify queue dedupe changed: " + json.dumps(deduped, ensure_ascii=False))
        covered = run_tdd_cross_verify([
            ".lazy-harness/triggers/fixtures/tdd-cross-verify/covered-feature.ts",
        ])
        if covered.get("ok") is not True or covered.get("forceGate") is not False or covered.get("passed") != 1:
            fail("tdd-cross-verify covered fixture changed: " + json.dumps(covered, ensure_ascii=False))
    finally:
        queue.unlink(missing_ok=True)
    print("✓ 5d-3 TDD cross-verify ok")



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
        if "5d-3 Affected Test Gate" not in fail_out or "Q-8e866d44709ff49c" not in fail_out:
            fail("affected test hook did not surface interview gate:\n" + fail_out)
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
        tdd = run_tdd_cross_verify([".lazy-harness/triggers/walkthrough-fixtures/referral-priority-feature.ts"], queue=queue, expect_code=2)
        if tdd.get("forceGate") is not True or tdd.get("failed") != 1:
            fail("5d-6 walkthrough TDD force gate changed: " + json.dumps(tdd, ensure_ascii=False))
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
    expected_counts = {"ddd": 6, "sdd": 2, "bdd": 3, "ssot": 7}
    if by_layer != expected_counts:
        fail(f"trigger fixture counts changed: expected {expected_counts}, got {by_layer}")

    expected_all = {
        ("ddd", "EMR"),
        ("ddd", "Emr"),
        ("ddd", "PatientDto"),
        ("ddd", "PatientRiskProfile"),
        ("sdd", "orderItemSchema"),
        ("sdd", "referralIntakeSchema"),
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
        "sdd->ddd:gap": 2,
        "bdd->ddd:gap": 3,
        "bdd->sdd:gap": 3,
        "ssot->ddd:gap": 2,
    }
    if cross_layer.get("summary") != expected_summary:
        fail(f"cross-layer summary changed: expected {expected_summary}, got {cross_layer.get('summary')}")
    expected_gaps = {
        ("sdd", "ddd", "OrderItem", "orderItemSchema"),
        ("sdd", "ddd", "ReferralIntake", "referralIntakeSchema"),
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


def main() -> None:
    check_doctor_smoke()
    check_doctor_c17_negative()
    check_doctor_package_health()
    check_xml()
    check_jsonl()
    check_lint_output()
    check_interview_loop_collect()
    check_interview_loop_answer()
    check_tdd_cross_verify()
    check_affected_test_runner()
    check_aftershock_reanalysis()
    check_lifecycle_hook_integration()
    check_real_feature_walkthrough()
    check_e2e_demo()
    check_triggers()
    print("lazy-harness self-test ok")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.stdout.write(exc.stdout)
        sys.stderr.write(exc.stderr)
        fail(f"command failed: {' '.join(exc.cmd)}")
