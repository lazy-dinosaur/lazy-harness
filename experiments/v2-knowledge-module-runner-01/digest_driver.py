"""One-shot completion-gated digestion; judgement is injected, never inferred here."""
import argparse
import copy
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import runner
import store_pg


def run_digestion(dsn, unit_id, judge, *, apply=True, choose=None, confirm=None):
    """choose(fact_text, options) -> {key: prob} routes adds to a domain (domain_router); None = exact/new only."""
    preview = store_pg.digest(dsn, unit_id, False)
    if preview["status"] != "needs_recheck":
        return preview
    receipt_ids = preview["receipt_ids"]
    if not receipt_ids:
        return {"status": "noop"}
    fixtures, judgments, packets = {}, {}, []
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        for receipt_id in receipt_ids:
            cur.execute("""select r.packet, r.jev_model_requested, r.jev_model_actual,
                        e.judgement_body, r.fact_index, e.host_id, e.partition_key, w.baseline_code_ref, h.repo_locator
                        from knowledge.check_receipt r join knowledge.ledger_entry e on e.entry_id=r.entry_id
                        join knowledge.work_unit w on w.work_unit_id=e.work_unit_id
                        join knowledge.host h on h.host_id=e.host_id
                        where r.receipt_id=%s and r.stage='worktime' and e.work_unit_id=%s""", (receipt_id, unit_id))
            receipt = store_pg._row(cur)
            if receipt is None:
                return {"status": "needs_recheck", "receipt_ids": [receipt_id]}
            fact = receipt["judgement_body"]["facts"][receipt["fact_index"]]
            if any(ref.get("type") == "code_test" and store_pg.code_changed_since(
                    receipt["repo_locator"], receipt["baseline_code_ref"], ref.get("locator")) is True
                    for ref in fact.get("evidence_refs", []) if isinstance(ref, dict)):
                return {"status": "needs_recheck", "receipt_ids": [receipt_id]}
            packet = copy.deepcopy(receipt["packet"])
            cur.execute("""select coalesce(max(h.history_id),0) from knowledge.fragment_history h
                        join knowledge.fragment f on f.id=h.fragment_id where f.host_id=%s""", (receipt["host_id"],))
            history_seen = cur.fetchone()[0]
            if fact.get("operation", "add") == "add":
                import worktime_driver
                packet["state"]["existing_records_excerpt"] = worktime_driver.existing_excerpt(
                    dsn, receipt["host_id"], fact)
            revision = None
            if fact.get("operation", "add") in ("update", "deprecate"):
                cur.execute("select text,revision from knowledge.fragment where id=%s and host_id=%s",
                            (fact.get("target_ref"), receipt["host_id"]))
                target = store_pg._row(cur)
                if not target:
                    return {"status": "needs_recheck", "receipt_ids": [receipt_id]}
                packet["state"]["target_excerpt"] = target["text"]
                revision = target["revision"]
            packets.append((receipt_id, receipt, packet, revision, history_seen))
    # Domain routing (read the list, then call Jev outside any transaction).
    import domain_router
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        domains = domain_router.load(cur, packets[0][1]["host_id"]) if packets else {}
    routed = {}
    adds = [(rid, rc) for rid, rc, *_ in packets if rc["judgement_body"]["facts"][rc["fact_index"]].get("operation", "add") == "add"]
    by_key = {}
    for receipt_id, receipt in adds:
        by_key.setdefault(receipt["partition_key"], []).append((receipt_id, receipt))
    for key, items in by_key.items():  # one routing decision per work unit and proposed name
        facts = [rc["judgement_body"]["facts"][rc["fact_index"]].get("fact", "") for _, rc in items]
        name, how = domain_router.route_unit(domains, key, facts, choose or (lambda text, options: {}), confirm=confirm)
        if name not in domains:
            domains[name] = {"description": (facts[0] if facts else "")[:300], "status": "active", "merged_into": None}
        for receipt_id, _ in items:
            routed[receipt_id] = {"domain": name, "how": how}
    # Jev/network calls must not hold a DB transaction open. Digest's final
    # transaction rechecks the target revision before committing any writes.
    for receipt_id, receipt, packet, revision, history_seen in packets:
        judged = judge(packet)
        if not isinstance(judged, dict) or not isinstance(judged.get("answers"), dict):
            raise ValueError("judge must return {'answers': <typed answer map>, ...}")
        fixture = {"packet": packet, "answers": judged["answers"],
                   "jev_model_requested": judged.get("jev_model_requested", receipt["jev_model_requested"]),
                   "jev_model_actual": judged.get("jev_model_actual", receipt["jev_model_actual"]),
                   "target_revision_seen": revision, "baseline_history_seen": history_seen,
                   "fresh_excerpt": packet["template_id"] == "record-need"}
        for key in ("input_tokens", "output_tokens", "cost_usd", "usage_source"):
            if key in judged:  # keep provider-reported usage on the digestion receipt too
                fixture[key] = judged[key]
        if "utterance_status" in judged:
            fixture["utterance_status"] = judged["utterance_status"]
        if receipt_id in routed:
            fixture["domain_routed"] = routed[receipt_id]
        fixtures[receipt_id] = fixture
        judgments[receipt_id] = judged
    result = store_pg.digest(dsn, unit_id, apply, fixtures)
    return {**result, "judgments": judgments}


def _jev_judge(packet):
    import config
    cfg = config.require("jev_api_key", "jev_base_url", "jev_model")
    key, base, model = cfg["jev_api_key"], cfg["jev_base_url"], cfg["jev_model"]
    request_body = runner.build_request({**packet, "model": model}, "state")
    request = Request(base.rstrip("/") + "/v1/systemone",
                      data=json.dumps(request_body, ensure_ascii=False).encode(),
                      headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=60) as response:
        body = json.load(response)
    answers = body["answers"]
    if not isinstance(answers, dict) or set(answers) != set(packet["questions"]):
        raise ValueError("Jev answer keys mismatch")
    usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
    out = {"answers": answers, "jev_model_requested": model,
           "jev_model_actual": body.get("model") or "unreported-by-tool"}
    if usage:  # OpenRouter reports tokens and cost in the response body
        out.update(input_tokens=usage.get("input_tokens"), output_tokens=usage.get("output_tokens"),
                   cost_usd=usage.get("cost"), usage_source="provider-response")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--judge", choices=("jev", "fixture"), default="fixture")
    parser.add_argument("--fixture")
    parser.add_argument("--test-dsn", action="store_true", help="use LH_KNOWLEDGE_TEST_DSN instead of knowledge.json db_url")
    args = parser.parse_args()
    import config
    dsn = os.environ.get("LH_KNOWLEDGE_TEST_DSN") if args.test_dsn else config.load()["db_url"]
    if not dsn:
        parser.error("database not configured (knowledge.json db_url, or --test-dsn with LH_KNOWLEDGE_TEST_DSN)")
    if args.judge == "fixture":
        if not args.fixture:
            parser.error("fixture judge requires --fixture")
        answers = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        judge = lambda packet: answers
    else:
        if args.fixture:
            parser.error("--fixture only applies to fixture judge")
        judge = _jev_judge
    print(json.dumps(run_digestion(dsn, args.unit, judge, apply=not args.dry_run), ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
