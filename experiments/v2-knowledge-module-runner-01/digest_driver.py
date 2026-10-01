"""One-shot completion-gated digestion; judgement is injected, never inferred here."""
import argparse
import copy
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

import runner
import store_pg


def run_digestion(dsn, unit_id, judge, *, apply=True, choose=None, confirm=None, same=None, embed_fn=None):
    """choose(fact_text, options) -> {key: prob} routes adds to a domain (domain_router); None = exact/new only."""
    preview = store_pg.digest(dsn, unit_id, False)
    if preview["status"] != "needs_recheck":
        return preview
    receipt_ids = preview["receipt_ids"]
    if not receipt_ids:
        return {"status": "noop"}
    fixtures, judgments, packets = {}, {}, []
    import worktime_driver
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select judgement_body from knowledge.ledger_entry where work_unit_id=%s
                    and state not in ('rejected_input','expired','closed') order by created_at""", (unit_id,))
        pending = worktime_driver.pending_rewrites([f for (body,) in cur.fetchall() for f in body.get("facts", [])])
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
            packet = copy.deepcopy(receipt["packet"])
            cur.execute("""select coalesce(max(h.history_id),0) from knowledge.fragment_history h
                        join knowledge.fragment f on f.id=h.fragment_id where f.host_id=%s""", (receipt["host_id"],))
            history_seen = cur.fetchone()[0]
            if fact.get("operation", "add") == "add":
                packet["state"]["existing_records_excerpt"] = worktime_driver.existing_excerpt(
                    dsn, receipt["host_id"], fact, pending)
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
        subjects = [rc["judgement_body"]["facts"][rc["fact_index"]].get("subject") for _, rc in items]
        name, how = _subject_domain(dsn, items[0][1]["host_id"], subjects, domains)
        if name is None:
            name, how = domain_router.route_unit(domains, key, facts, choose or (lambda text, options: {}), confirm=confirm)
        if name not in domains:
            domains[name] = {"description": (facts[0] if facts else "")[:300], "status": "active", "merged_into": None}
        for receipt_id, _ in items:
            routed[receipt_id] = {"domain": name, "how": how}
    # Subjects: a name not in the dictionary is compared with subjects registered after its record (the record-time
    # check could not see them); store_pg.digest registers or reuses inside its transaction (single writer).
    import embed
    import subject_dict
    efn = embed_fn or embed.encode_queries
    subject_routed = {}
    for receipt_id, receipt, packet, revision, history_seen in packets:
        fact = receipt["judgement_body"]["facts"][receipt["fact_index"]]
        name = fact.get("subject")
        if fact.get("operation", "add") == "deprecate" or not isinstance(name, str) or not name.strip():
            continue
        with store_pg.connect(dsn) as conn, conn.cursor() as cur:
            if subject_dict.lookup(cur, receipt["host_id"], name):
                continue
            cur.execute("""select e.created_at from knowledge.check_receipt r join knowledge.ledger_entry e
                           on e.entry_id=r.entry_id where r.receipt_id=%s""", (receipt_id,))
            after = cur.fetchone()[0]
            try:
                vector = efn([subject_dict.core(name)])[0]
            except embed.EmbeddingUnavailable:
                continue
            cands = subject_dict.nearest(cur, receipt["host_id"], vector, after=after)
        best = subject_dict.decide(name, cands, same, fact.get("fact"))
        subject_routed[receipt_id] = ({"subject_id": best["subject_id"], "name": best["name"]} if best
                                      else {"vector": list(vector)})
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
        if receipt_id in subject_routed:
            fixture["subject_routed"] = subject_routed[receipt_id]
        fixtures[receipt_id] = fixture
        judgments[receipt_id] = judged
    result = store_pg.digest(dsn, unit_id, apply, fixtures)
    return {**result, "judgments": judgments}


def _subject_domain(dsn, host, subjects, domains):
    """schema-delta '도메인 라우팅은 주어 기준': when the unit's known subjects already live in exactly one active domain
    (following merges), that domain is the answer in code -> (domain, 'subject'); otherwise (None, None) and Jev routes."""
    import domain_router
    import subject_dict
    found = set()
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        ids = {hit["subject_id"] for s in subjects if isinstance(s, str) and s.strip()
               for hit in [subject_dict.lookup(cur, host, s)] if hit}
        if not ids:
            return None, None
        cur.execute("""select distinct domain from knowledge.fragment where host_id=%s and active
                       and subject_id = any(%s::uuid[])""", (host, sorted(ids)))
        for (d,) in cur.fetchall():
            found.add(domain_router.resolve(domains, d))
    active = {d for d in found if d in domains and domains[d]["status"] == "active"}
    return (active.pop(), "subject") if len(active) == 1 else (None, None)


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
