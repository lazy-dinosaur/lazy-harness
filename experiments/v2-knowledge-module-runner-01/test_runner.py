import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import runner

FIXTURES = Path(__file__).parent / "fixtures"
PLAN = runner.load(FIXTURES / "jev-p1-expand-08-plan.json")


class PacketLintTests(unittest.TestCase):
    def test_p1_plan_detects_both_anonymization_mismatches(self):
        errors = runner.lint(PLAN)["errors"]
        self.assertEqual({"T1", "T2"}, {error["where"].split(".")[0] for error in errors})
        self.assertEqual({"E_CLAIM_QUOTE"}, {error["code"] for error in errors})
        self.assertTrue(runner.lint({"cases": [case for case in PLAN["cases"] if case["id"] not in ("T1", "T2")]})["ok"])

    def test_e2e_bad_packets(self):
        for name, code in (("schema-fields", "E_SCHEMA"), ("schema-noul", "E_SCHEMA"),
                           ("escape", "E_ESCAPE"), ("conditional", "E_CONDITIONAL"),
                           ("prescriptive", "E_PRESCRIPTIVE"), ("leak", "E_LEAK")):
            with self.subTest(name=name):
                denylist = ["SUPERSECRET"] if name == "leak" else []
                result = runner.lint(runner.load(FIXTURES / f"bad-{name}.json"), denylist)
                self.assertIn(code, {error["code"] for error in result["errors"]})

    def test_backtick_and_identifier_quote(self):
        packet = {"state": {"candidate_fact": "`flagA` and E5 and SCEN-1", "evidence_quote": "flagA E5 SCEN-1"}}
        self.assertTrue(runner.lint(packet)["ok"])
        packet["state"]["evidence_quote"] = "flagB E5"
        self.assertEqual(2, len(runner.lint(packet)["errors"]))

    def test_evaluative_narrative_only(self):
        packet = {"cases": [{"id": "N5", "state": {"narrative": "매우 중요한 발견이다",
                    "candidate_fact": "핵심", "evidence_quote": "핵심"}}]}
        self.assertEqual([{"code": "E_EVALUATIVE", "where": "N5.state.narrative",
                           "detail": "evaluative narrative"}], runner.lint(packet)["errors"])
        packet["cases"][0]["state"]["narrative"] = "새 사실이 발견됐다"
        self.assertTrue(runner.lint(packet)["ok"])


class RoutingTests(unittest.TestCase):
    def test_p1_reported_values_and_review_precedence(self):
        # Unreported axes in these fixtures are synthetic; reported P1 values are retained verbatim.
        expected = {"D4": "needs_review", "D2": "needs_review", "D3": "needs_review",
                    # X2 (is_new .11) is no longer dropped as duplicate: DUP_SKIP_MAX = 0.1 keeps near-duplicates
                    # that may carry one new detail (write-01 round_dedup); later clean-up handles true duplicates.
                    "T2": "no_record", "X1": "duplicate_skip", "X2": "needs_review"}
        for case, combined in expected.items():
            with self.subTest(case=case):
                result = runner.decide(PLAN, runner.load(FIXTURES / f"responses-{case}.json"))
                self.assertEqual(combined, result["combined"])
        self.assertEqual("route_review", runner.decide(PLAN, runner.load(FIXTURES / "responses-D3.json"))["per_question"]["is_supported"]["route"])

    def test_unambiguous_record_and_no_record(self):
        responses = runner.load(FIXTURES / "responses-D4.json")
        responses["should_record"]["noul"] = .7
        self.assertEqual("record", runner.decide(PLAN, responses)["combined"])
        responses["durability"]["choice"] = "transient_progress"
        responses["durability"]["probabilities"] = {"transient_progress": .95, "none_or_uncertain": .05}
        self.assertEqual("no_record", runner.decide(PLAN, responses)["combined"])

    def test_impact_combination_and_legacy_should_record(self):
        responses = {
            "is_new": {"type": "noul", "noul": .89},
            "durability": {"type": "choice", "probabilities": {"durable_fact": .95, "transient_progress": .03,
                           "explanation_only": .01, "none_or_uncertain": .01}},
            "impact": {"type": "choice", "probabilities": {"changes_decisions": .99,
                       "reference_only": .005, "no_future_use": .003, "none_or_uncertain": .002}},
        }
        self.assertEqual("record", runner.decide({}, responses)["combined"])
        responses["impact"]["probabilities"] = {"no_future_use": .81, "reference_only": .16,
                                                    "changes_decisions": .02, "none_or_uncertain": .01}
        self.assertEqual("no_record", runner.decide({}, responses)["combined"])
        responses["impact"]["probabilities"] = {"reference_only": .90, "changes_decisions": .05,
                                                    "no_future_use": .03, "none_or_uncertain": .02}
        result = runner.decide({}, responses)
        self.assertEqual("needs_review", result["combined"])
        self.assertIn("impact: reference_only (policy pending)", result["review_reasons"])
        responses["impact"]["probabilities"] = {"none_or_uncertain": .85, "changes_decisions": .08,
                                                    "reference_only": .05, "no_future_use": .02}
        self.assertEqual("needs_review", runner.decide({}, responses)["combined"])
        responses["impact"]["probabilities"] = {"changes_decisions": .99,
                        "reference_only": .005, "no_future_use": .003, "none_or_uncertain": .002}
        responses["is_new"]["noul"] = .05  # below DUP_SKIP_MAX (0.1): near-certain duplicate
        self.assertEqual("duplicate_skip", runner.decide({}, responses)["combined"])
        legacy = runner.load(FIXTURES / "responses-D4.json")
        legacy["should_record"]["noul"] = .7
        self.assertNotIn("impact", legacy)
        self.assertEqual("record", runner.decide(PLAN, legacy)["combined"])

    def test_impact_stability_n5_review(self):
        evidence = Path("/home/lazydino/dev/lazy-harness/.lazy-harness/evidence/jev-impact-stability-14-result.json")
        probabilities = runner.load(evidence)["breadth"]["probabilities"]["N5"]
        responses = {
            "is_new": {"type": "noul", "noul": .9},
            "durability": {"type": "choice", "probabilities": {"durable_fact": .95, "transient_progress": .03,
                           "explanation_only": .01, "none_or_uncertain": .01}},
            "impact": {"type": "choice", "probabilities": probabilities},
        }
        result = runner.decide({}, responses)
        self.assertEqual("route_review", result["per_question"]["impact"]["route"])
        self.assertEqual("needs_review", result["combined"])

    def test_escape_and_noul_endpoints(self):
        # 비중복 사례 기반: 중복(duplicate_skip) 우선순위가 escape 회부를 덮는 것은 의도된 동작이므로 D4 사용
        responses = runner.load(FIXTURES / "responses-D4.json")
        responses["is_supported"]["choice"] = "none_or_uncertain"
        self.assertEqual("needs_review", runner.decide(PLAN, responses)["combined"])
        for probability in (.35, .65):
            responses["is_supported"]["choice"] = "supported"
            responses["is_new"]["noul"] = probability
            self.assertEqual("route_review", runner.decide(PLAN, responses)["per_question"]["is_new"]["route"])


class CallTests(unittest.TestCase):
    def test_dry_run_never_opens_network(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network attempted")):
            result = subprocess.run([sys.executable, str(Path(__file__).parent / "runner.py"), "call",
                                     str(FIXTURES / "call-packet.json"), "demo"],
                                    text=True, capture_output=True, check=True)
        body = json.loads(result.stdout)
        self.assertEqual({"state", "questions", "model"}, set(body))
        self.assertEqual("typesafe/jev-1.13", body["model"])
        self.assertNotIn("SUPERSECRET", result.stdout)

    def test_call_missing_model_rejected(self):
        packet = runner.load(FIXTURES / "call-packet.json")
        packet.pop("model")
        with self.assertRaisesRegex(ValueError, "model"):
            runner.build_request(packet, "demo")

    def test_decide_cli_operation(self):
        responses = FIXTURES / "c1-offline-responses.json"
        # Fixture contains operation-specific response maps; use a temporary file for one case.
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "responses.json"
            for case, operation, expected in (("U1", "update", "update_record"), ("D1", "deprecate", "deprecate_record")):
                path.write_text(json.dumps(runner.load(responses)[case]), encoding="utf-8")
                result = subprocess.run([sys.executable, str(Path(__file__).parent / "runner.py"), "decide",
                                         str(FIXTURES / "call-packet.json"), str(path), "--operation", operation],
                                        text=True, capture_output=True, check=True)
                self.assertEqual(expected, json.loads(result.stdout)["combined"])

    def test_missing_wire_questions_rejected(self):
        with self.assertRaisesRegex(ValueError, "explicit questions"):
            runner.build_request(PLAN, "D4")



class DupSkipThresholdTests(unittest.TestCase):
    """DUP_SKIP_MAX (write-01 round_dedup): only near-certain duplicates are dropped at digestion."""
    def responses(self, is_new):
        return {"is_new": {"type": "noul", "noul": is_new},
                "durability": {"type": "choice", "probabilities": {"durable_fact": .95, "transient_progress": .03, "explanation_only": .01, "none_or_uncertain": .01}},
                "impact": {"type": "choice", "probabilities": {"changes_decisions": .99, "reference_only": .005, "no_future_use": .003, "none_or_uncertain": .002}}}

    def test_threshold(self):
        self.assertEqual(0.1, runner.DUP_SKIP_MAX)
        self.assertEqual("duplicate_skip", runner.decide({}, self.responses(.09))["combined"])
        self.assertNotEqual("duplicate_skip", runner.decide({}, self.responses(.2))["combined"])
        self.assertEqual("record", runner.decide({}, self.responses(.9))["combined"])

if __name__ == "__main__":
    unittest.main()

# All ledger and fragment files below are synthetic and confined to a temporary directory.
import tempfile
import store


class ModuleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.c1 = runner.load(FIXTURES / "c1-offline-responses.json")
        store.write(self.root / "fragments" / "target.json", {"revision": 1, "active": True, "text": "old"})

    def register(self, operation="update", target="target", unit="unit", fact="new"):
        return store.register(self.root, {"judgement_id": f"j{len(store.rows(self.root, 'ledger_entry'))}",
            "version": 1, "work_unit_id": unit, "host_id": "synthetic-host", "partition_key": "worker",
            "disposition_candidate": "required", "evidence_refs": ["synthetic quote"],
            "facts": [{"operation": operation, "target_ref": target, "fact": fact, "subject": fact,
                       "reason": "synthetic reason", "evidence_refs": ["synthetic quote"]}]})

    def fixture(self, operation, case="U1"):
        questions = {key: {"type": value["type"], "instructions": "Select a literal value",
                   "criteria": ({"true": None, "false": None} if value["type"] == "noul" else
                                {name: None for name in value["probabilities"]})}
                     for key, value in self.c1[case].items()}
        return {"target_revision_seen": 1, "packet": {"template_id": "intent", "template_version": "v0.3",
                "state": {"narrative": "synthetic narrative", "candidate_fact": "new", "evidence_quote": "new", "target_excerpt": "old"},
                "questions": questions}, "answers": self.c1[case]}

    def test_register_immediately_proposed(self):
        entry = self.register()
        self.assertEqual("proposed", store.read(self.root / "ledger_entry" / (entry["entry_id"] + ".json"))["state"])
        self.assertEqual(1, len((self.root / "ledger_entry" / "events.jsonl").read_text().splitlines()))

    def test_batch_window_and_receipts(self):
        entries = [self.register() for _ in range(3)]
        fixtures = {e["entry_id"]: [self.fixture("update")] for e in entries}
        result = store.batch(self.root, 2, fixtures)
        self.assertEqual(2, len(result))
        self.assertEqual("proposed", store.rows(self.root, "ledger_entry")[-1]["state"])
        self.assertEqual(2, len(store.rows(self.root, "check_receipt")))
        receipt = store.rows(self.root, "check_receipt")[0]
        self.assertEqual(("worktime", 1, "v0.3"), (receipt["stage"], receipt["target_revision_seen"], receipt["template_version"]))

    def test_target_lint(self):
        entry = self.register(target=None)
        result = store.batch(self.root, 1, {})
        self.assertEqual("E_TARGET", result[0]["facts"][0]["errors"][0]["code"])
        self.assertEqual("rejected_input", result[0]["state"])

    def test_update_combination_c1(self):
        self.assertEqual("update_record", runner.decide({}, self.c1["U1"], "update")["combined"])
        self.assertEqual("duplicate_skip", runner.decide({}, self.c1["A1"], "update")["combined"])
        consistent = dict(self.c1["A1"])
        consistent["differs_from_target"] = {"type": "noul", "noul": .82}
        self.assertEqual("needs_review", runner.decide({}, consistent, "update")["combined"])

    def test_deprecate_combination_c1(self):
        self.assertEqual("deprecate_record", runner.decide({}, self.c1["D1"], "deprecate")["combined"])
        answers = dict(self.c1["D1"])
        answers["invalidation_evidence"] = {"type":"choice", "choice":"still_valid",
            "probabilities":{"still_valid": .95,"invalidates": .02,"none_or_uncertain": .03}}
        self.assertEqual("needs_review", runner.decide({}, answers, "deprecate")["combined"])

    def test_stale_revision_blocks_absorption(self):
        entry = self.register()
        fixture = self.fixture("update")
        store.batch(self.root, 1, {entry["entry_id"]: [fixture]})
        store.complete(self.root, "unit")
        fragment = store.read(self.root / "fragments" / "target.json")
        fragment["revision"] = 2
        store.write(self.root / "fragments" / "target.json", fragment)
        self.assertEqual("needs_recheck", store.digest(self.root, "unit", apply=True)["status"])
        self.assertEqual([], store.rows(self.root, "absorption"))

    def test_deprecate_absorption_and_history(self):
        entry = self.register("deprecate")
        fixture = self.fixture("deprecate", "D1")
        store.batch(self.root, 1, {entry["entry_id"]: [fixture]})
        store.complete(self.root, "unit")
        receipt = store.rows(self.root, "check_receipt")[0]
        self.assertEqual("absorbed", store.digest(self.root, "unit", True, {receipt["receipt_id"]: fixture})["status"])
        self.assertFalse(store.read(self.root / "fragments" / "target.json")["active"])
        self.assertEqual(1, len((self.root / "fragment_history" / "events.jsonl").read_text().splitlines()))

    def test_update_cas_mismatch_rejected(self):
        entry = self.register()
        fixture = self.fixture("update")
        store.batch(self.root, 1, {entry["entry_id"]: [fixture]})
        store.complete(self.root, "unit")
        receipt = store.rows(self.root, "check_receipt")[0]
        fragment = store.read(self.root / "fragments" / "target.json")
        fragment["revision"] = 2
        store.write(self.root / "fragments" / "target.json", fragment)
        self.assertEqual("needs_recheck", store.digest(self.root, "unit", True)["status"])
        self.assertEqual("needs_recheck", store.digest(self.root, "unit", True, {receipt["receipt_id"]: fixture})["status"])

    def test_consistency_flag(self):
        update, deprecate = self.register(), self.register("deprecate")
        fixtures = {update["entry_id"]: [self.fixture("update")],
                    deprecate["entry_id"]: [self.fixture("deprecate", "D1")]}
        store.batch(self.root, 2, fixtures)
        store.complete(self.root, "unit")
        self.assertEqual([{"target_ref": "target", "operations": ["deprecate", "update"]}],
                         store.digest(self.root, "unit")["consistency_flags"])

    def test_dedup_key_separates_fact_index_and_stage(self):
        # schema-delta §3: 같은 evidence_refs 의 다중 fact / worktime·digestion 영수증이 충돌하면 안 된다
        entry = self.register()
        fact = entry["judgement_body"]["facts"][0]
        packet = self.fixture("update")["packet"]
        keys = {store.dedup_key(entry, fact, packet, "m", 0, "worktime"),
                store.dedup_key(entry, fact, packet, "m", 1, "worktime"),
                store.dedup_key(entry, fact, packet, "m", 0, "digestion")}
        self.assertEqual(3, len(keys))
        self.assertEqual(store.dedup_key(entry, fact, packet, "m", 0, "worktime"),
                         store.dedup_key(entry, fact, packet, "m", 0, "worktime"))

    def test_resubmit_reenters_and_escalates(self):
        # event-contract §3: review_queue -> 보충 -> proposed 재진입, 상한 2회 초과 시 에스컬레이션
        entry = self.register()
        with self.assertRaises(ValueError):  # proposed 상태는 재제출 대상 아님
            store.resubmit(self.root, entry["entry_id"])
        e = store.read(self.root / "ledger_entry" / (entry["entry_id"] + ".json"))
        store.transition(self.root, e, "review_queue", "runner")
        for n in (1, 2):
            self.assertEqual({"status": "proposed", "supplement_count": n}, store.resubmit(self.root, entry["entry_id"]))
            e = store.read(self.root / "ledger_entry" / (entry["entry_id"] + ".json"))
            store.transition(self.root, e, "review_queue", "runner")
        self.assertEqual("escalated", store.resubmit(self.root, entry["entry_id"])["status"])

    def test_dedup_key_changes_with_packet(self):
        # C4 발견: 보충으로 패킷만 바뀜 때 옛 회부 캐시에 걸리면 안 된다
        entry = self.register()
        fact = entry["judgement_body"]["facts"][0]
        packet = self.fixture("update")["packet"]
        revised = {**packet, "state": {**packet["state"], "narrative": "supplemented"}}
        self.assertNotEqual(store.dedup_key(entry, fact, packet, "m", 0, "worktime"),
                            store.dedup_key(entry, fact, revised, "m", 0, "worktime"))

    def test_lint_rejects_list_questions_missing_state_and_wrong_excerpt(self):
        # C4 발견: questions 배열·narrative 누락은 크래시 없이 거절, target_excerpt 는 조각 현재 text 와 일치해야 함
        bad = {"template_id": "intent", "template_version": "v0.3.1",
               "state": {"candidate_fact": "new", "evidence_quote": "new", "target_excerpt": "old"},
               "questions": [{"type": "noul", "instructions": "x", "criteria": {"true": None, "false": None}}]}
        codes = {e["code"] for e in runner.lint(bad)["errors"]}
        self.assertEqual({"E_SCHEMA", "E_STATE"}, codes)
        entry = self.register()
        fixture = self.fixture("update")
        fixture["packet"]["state"]["target_excerpt"] = '{"text": "old"}'
        result = store.batch(self.root, 1, {entry["entry_id"]: [fixture]})
        self.assertEqual("rejected_input", result[0]["state"])
        self.assertIn("E_TARGET", {e["code"] for e in result[0]["facts"][0]["errors"]})

    def test_scope_expanded_blocks_record(self):
        # C4 발견: scope expanded(확실)가 기록을 통과하면 안 된다
        answers = dict(self.c1["U1"])
        answers["scope"] = {"type": "choice", "choice": "expanded",
                            "probabilities": {"expanded": 0.92, "preserved": 0.05, "narrowed": 0.02, "none_or_uncertain": 0.01}}
        packet = self.fixture("update")["packet"]
        self.assertEqual("needs_review", runner.decide(packet, answers, operation="update")["combined"])
        answers["scope"] = {"type": "choice", "choice": "preserved",
                            "probabilities": {"preserved": 0.9, "expanded": 0.05, "narrowed": 0.04, "none_or_uncertain": 0.01}}
        self.assertEqual("update_record", runner.decide(packet, answers, operation="update")["combined"])

    def test_build_fragment_group_id_uses_judgement_and_group_or_index(self):
        entry = self.register(operation="add", target=None)
        import store as module
        facts = entry["judgement_body"]["facts"]
        facts[0]["group"] = "group"
        facts.append({"fact": "another fact", "subject": "another fact"})
        first = module.build_fragment(entry, 0, [], [], module.now(), 1)
        second = module.build_fragment(entry, 1, [], [], module.now(), 2)
        self.assertEqual(entry["judgement_id"] + ":group", first["group_id"])
        self.assertEqual(entry["judgement_id"] + ":1", second["group_id"])

    def test_stats(self):
        entry = self.register()
        store.batch(self.root, 1, {entry["entry_id"]: [self.fixture("update")]})
        stats = store.stats(self.root)
        self.assertEqual(2, len(stats))
        self.assertTrue(all(x["template_version"] == "v0.3" and x["total"] == 1 for x in stats))
