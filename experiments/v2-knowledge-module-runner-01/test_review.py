"""Fact-level review: undecided facts wait for a human, the rest digest normally."""
import copy

import pytest

import digest_driver
import knowledge_cli
import store_pg as pg
from test_store_pg import fixture, host, judgement


def unsure(text):
    response = fixture(text=text)
    response["answers"]["durability"] = {"type": "choice", "choice": "durable_fact",
                                         "probabilities": {"durable_fact": .52, "none_or_uncertain": .48}}
    return response


def two_facts(host_id, first="alpha", second="beta"):
    body = judgement(host_id, text=first)
    extra = copy.deepcopy(body["facts"][0])
    extra.update({"fact": second, "subject": second, "evidence_quote": second, "keywords": [second]})
    extra["evidence_refs"][0]["quote"] = second
    body["facts"].append(extra)
    return body


def judge_record(packet):
    return {"answers": fixture(text=packet["state"]["candidate_fact"])["answers"]}


def texts(dsn, host_id):
    return sorted(r["text"] for r in pg.rows(dsn, "fragment") if r["host_id"] == host_id)


def test_mixed_entry_digests_clear_fact_then_approved_fact(dsn, host):
    body = two_facts(host)
    entry = pg.register(dsn, body)
    outcome = pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text="alpha"), unsure("beta")]})[0]
    assert outcome["state"] == "provisional"
    unit = body["work_unit_id"]
    pg.complete(dsn, unit)
    assert digest_driver.run_digestion(dsn, unit, judge_record)["status"] == "absorbed"
    assert texts(dsn, host) == ["alpha"]
    items = knowledge_cli.review_cmd(dsn, {"host_id": host})["items"]
    assert [(i["fact"], i["fact_index"]) for i in items] == [("beta", 1)]
    assert items[0]["why_waiting"] == ["오래 쓸 지식인지 애매"]
    asked = knowledge_cli.review_cmd(dsn, {"host_id": host, "action": "resolve", "entry_id": entry["entry_id"],
                                          "fact_index": 1, "decision": "approve", "user_quote": "이거 넣을까?"})
    assert asked["ok"] is False
    done = knowledge_cli.review_cmd(dsn, {"host_id": host, "action": "resolve", "entry_id": entry["entry_id"],
                                         "fact_index": 1, "decision": "approve", "user_quote": "응 넣어"})
    assert done["entry_state"] == "eligible" and done["pending_in_entry"] == 0
    with pytest.raises(ValueError):
        pg.review_resolve(dsn, host, entry["entry_id"], 1, "reject", "아니")
    assert digest_driver.run_digestion(dsn, unit, judge_record)["status"] == "absorbed"
    assert texts(dsn, host) == ["alpha", "beta"]
    deciders = sorted(r["decided_by"] for r in pg.rows(dsn, "absorption") if str(r["entry_id"]) == entry["entry_id"])
    assert deciders == ["acceptance_policy", "human"]
    assert digest_driver.run_digestion(dsn, unit, judge_record) == {"status": "noop"}
    assert knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] == []


def test_all_unsure_entry_rejected_closes_without_fragment(dsn, host):
    body = two_facts(host, "gamma", "delta")
    entry = pg.register(dsn, body)
    assert pg.batch(dsn, 1, {entry["entry_id"]: [unsure("gamma"), unsure("delta")]})[0]["state"] == "review_queue"
    pg.complete(dsn, body["work_unit_id"])
    first = pg.review_resolve(dsn, host, entry["entry_id"], 0, "reject", "빼")
    assert first["entry_state"] == "review_queue" and first["pending_in_entry"] == 1
    assert pg.review_resolve(dsn, host, entry["entry_id"], 1, "reject", "그것도 빼")["entry_state"] == "closed"
    assert texts(dsn, host) == []
    with pytest.raises(ValueError):
        pg.review_resolve(dsn, "other-host", entry["entry_id"], 0, "approve", "응")


def test_legacy_review_queue_entry_releases_clear_facts(dsn, host):
    body = two_facts(host, "eps", "zeta")
    entry = pg.register(dsn, body)
    pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text="eps"), unsure("zeta")]})
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # entry-level review_queue from before the split
        cur.execute("update knowledge.ledger_entry set state='review_queue' where entry_id=%s", (entry["entry_id"],))
    pg.complete(dsn, body["work_unit_id"])
    assert pg.review_resolve(dsn, host, entry["entry_id"], 1, "reject", "이건 빼")["entry_state"] == "eligible"
    assert digest_driver.run_digestion(dsn, body["work_unit_id"], judge_record)["status"] == "absorbed"
    assert texts(dsn, host) == ["eps"]
