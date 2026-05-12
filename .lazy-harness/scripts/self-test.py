#!/usr/bin/env python3
"""Lazy-Harness reproducible self-test.

Checks the framework-owned operational invariants defined by ADR 0022:
- every .lazy-harness XML file parses
- permanent JSONL logs parse line-by-line
- trigger fixtures produce DDD/SDD/BDD/SSOT candidates
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[2]
LAZY = ROOT / ".lazy-harness"


def fail(message: str) -> None:
    print(f"✗ {message}")
    raise SystemExit(1)


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
    expected_counts = {"ddd": 5, "sdd": 1, "bdd": 1, "ssot": 4}
    if by_layer != expected_counts:
        fail(f"trigger fixture counts changed: expected {expected_counts}, got {by_layer}")

    expected_all = {
        ("ddd", "EMR"),
        ("ddd", "Emr"),
        ("ddd", "PatientDto"),
        ("ddd", "PatientRiskProfile"),
        ("sdd", "orderItemSchema"),
        ("bdd", "PatientSearchAutocomplete"),
        ("ssot", "mapPatientToDto"),
        ("ssot", "calculateChecksum"),
        ("ssot", "validatePatientRiskProfile"),
        ("ssot", "normalizeAppointmentStatus"),
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
    for expected in ["mapPatientToDto", "calculateChecksum", "validatePatientRiskProfile", "normalizeAppointmentStatus"]:
        if expected not in ssot_names:
            fail(f"missing SSOT fixture candidate: {expected}")
    ssot_confidence = {candidate.get("name"): candidate.get("confidence") for candidate in ssot_candidates}
    expected_confidence = {
        "mapPatientToDto": "high",
        "validatePatientRiskProfile": "high",
        "normalizeAppointmentStatus": "high",
        "calculateChecksum": "medium",
    }
    if ssot_confidence != expected_confidence:
        fail(f"SSOT confidence changed: expected {expected_confidence}, got {ssot_confidence}")
    print(f"✓ trigger fixtures ok {by_layer}")


def main() -> None:
    check_xml()
    check_jsonl()
    check_triggers()
    print("lazy-harness self-test ok")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.stdout.write(exc.stdout)
        sys.stderr.write(exc.stderr)
        fail(f"command failed: {' '.join(exc.cmd)}")
