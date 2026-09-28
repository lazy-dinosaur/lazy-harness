"""Offline-injectable worktime review of proposed knowledge entries."""
import argparse
import copy
import json
import os
from pathlib import Path

import digest_driver
import runner
import store_pg


import templates  # single source: migration seeds (knowledge.question_template)


def _questions():
    return templates.record_need()


def _intent_questions():
    return templates.intent()


def build_packet(fact, existing_excerpt):
    operation = fact.get("operation", "add")
    refs = [r for r in fact.get("evidence_refs", []) if isinstance(r, dict) and r.get("quote")]
    # Jev sees every evidence ref (standard v1 criterion 5), not only the single summary quote.
    quote = ("\n".join(f"[{r.get('type')} {r.get('locator')}] {r['quote']}" for r in refs)
             if len(refs) > 1 else fact["evidence_quote"])
    narrative = fact["reason"] + (f" 이유: {fact['why']}" if fact.get("why") else "")
    state = {"narrative": narrative, "candidate_fact": fact["fact"], "evidence_quote": quote}
    if operation == "add":
        state["existing_records_excerpt"] = existing_excerpt
        return {"template_id": "record-need", "template_version": "v0.2.2",
                "questions": _questions(), "state": state}
    if operation == "update":
        state["target_excerpt"] = existing_excerpt
        return {"template_id": "intent", "template_version": "v0.3.1",
                "questions": _intent_questions(), "state": state}
    if operation == "deprecate":
        state["target_excerpt"] = existing_excerpt
        state["deprecate_reason"] = state.pop("candidate_fact")
        return {"template_id": templates.DEPRECATE[0], "template_version": templates.DEPRECATE[1],
                "questions": templates.deprecate(), "state": state}
    raise NotImplementedError(f"worktime operation {operation} has no supported wire template")


def existing_excerpt(dsn, host, fact):
    hits = store_pg.search(dsn, host, fact["fact"], limit=5, mode="hybrid", expand=False)
    fallback = any(hit.get("warning") for hit in hits)
    if not hits:
        # search returns no metadata on an empty result set; check the local encoder
        # so the caller still sees that a hybrid search fell back to text.
        import embed
        try:
            embed.encode_query(fact["fact"])
        except embed.EmbeddingUnavailable:
            fallback = True
    prefix = "[text fallback: embedding service unavailable] " if fallback else ""
    if not hits:
        return prefix + "이 host 의 정본에 관련 조각이 없다."
    return prefix + "\n".join(hit["text"][:240] for hit in hits)


def _proposed(dsn, window, entry_ids=None):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select entry_id::text,host_id,judgement_body from knowledge.ledger_entry
                    where state='proposed' and (%s::uuid[] is null or entry_id=any(%s::uuid[]))
                    order by created_at,entry_id limit %s""", (entry_ids, entry_ids, window))
        return store_pg._rows(cur)


def _target_excerpt(dsn, host, fact):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select text from knowledge.fragment where id=%s and host_id=%s and active",
                    (fact["target_ref"], host))
        row = store_pg._row(cur)
    if row is None:
        raise ValueError("target fragment missing in host")
    return row["text"]


def run_worktime(dsn, window, judge, *, utterance_judge=None, entry_ids=None):
    if window < 1:
        raise ValueError("window must be positive")
    fixtures, failures, utterances = {}, [], {}
    for entry in _proposed(dsn, window, entry_ids):
        prepared = []
        for index, fact in enumerate(entry["judgement_body"].get("facts", [])):
            try:
                excerpt = (_target_excerpt(dsn, entry["host_id"], fact)
                           if fact.get("operation") == "update" else
                           existing_excerpt(dsn, entry["host_id"], fact))
                packet = build_packet(fact, excerpt)
                # Lint before any paid call: batch rejects the whole entry on a packet lint error,
                # so judging the other facts first would only waste Jev calls (cycle-02 finding).
                packet_errors = runner.lint(packet)["errors"]
                if packet_errors:
                    raise ValueError("packet lint: " + ", ".join(sorted({e["code"] for e in packet_errors})))
                judged = judge(copy.deepcopy(packet))
                if not isinstance(judged, dict) or not isinstance(judged.get("answers"), dict):
                    raise ValueError("judge must return {'answers': <typed answer map>, ...}")
                fixture = {"packet": packet, "answers": judged["answers"]}
                for key in ("jev_model_requested", "jev_model_actual", "input_tokens", "output_tokens",
                            "cost_usd", "usage_source"):
                    if key in judged:
                        fixture[key] = judged[key]
                if fact.get("evidence_source") == "user_confirmed" and utterance_judge:
                    status = utterance_judge(fact)
                    fixture["utterance_status"] = status
                    utterances.setdefault(entry["entry_id"], {})[index] = status
                prepared.append(fixture)
            except Exception as exc:
                # Never turn a failed review into no_record or submit a partial entry.
                failures.append({"entry_id": entry["entry_id"], "fact_index": index,
                                 "error": f"{type(exc).__name__}: {exc}"})
                prepared = None
                break
        if prepared is not None:
            fixtures[entry["entry_id"]] = prepared
    # batch only sees fully judged entries; missing fixtures remain proposed.
    results = store_pg.batch(dsn, window, fixtures, entry_ids=entry_ids)
    for result in results:
        if result["entry_id"] in utterances and result["entry_id"] in fixtures:
            result["utterance_status"] = utterances[result["entry_id"]]
    return {"results": results, "failures": failures}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, required=True)
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
        response = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        judge = lambda packet: response
    else:
        if args.fixture:
            parser.error("--fixture only applies to fixture judge")
        judge = digest_driver._jev_judge
    print(json.dumps(run_worktime(dsn, args.window, judge), ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
