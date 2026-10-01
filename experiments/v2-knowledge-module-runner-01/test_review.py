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


def test_mixed_entry_digests_both_facts(dsn, host):
    body = two_facts(host)
    entry = pg.register(dsn, body)
    assert pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text="alpha"), unsure("beta")]})[0]["state"] == "provisional"
    unit = body["work_unit_id"]
    pg.complete(dsn, unit)
    assert digest_driver.run_digestion(dsn, unit, judge_record)["status"] == "absorbed"
    assert texts(dsn, host) == ["alpha", "beta"]
    assert digest_driver.run_digestion(dsn, unit, judge_record) == {"status": "noop"}


def test_unsure_quality_no_longer_holds_a_command(dsn, host):
    """A ledger record is the user's command: an unsure quality answer does not send it to review."""
    body = two_facts(host, "gamma", "delta")
    entry = pg.register(dsn, body)
    assert pg.batch(dsn, 1, {entry["entry_id"]: [unsure("gamma"), unsure("delta")]})[0]["state"] == "provisional"
    pg.complete(dsn, body["work_unit_id"])
    assert digest_driver.run_digestion(dsn, body["work_unit_id"], judge_record)["status"] == "absorbed"
    assert texts(dsn, host) == ["delta", "gamma"]
    assert knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] == []


def test_digest_disagreement_does_not_park(dsn, host):
    """No second-opinion review: an unsure digestion recheck still applies the command."""
    body = two_facts(host, "eta", "theta")
    entry = pg.register(dsn, body)
    assert pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text="eta"), fixture(text="theta")]})[0]["state"] == "provisional"
    unit = body["work_unit_id"]
    pg.complete(dsn, unit)
    def flaky(packet):
        text = packet["state"]["candidate_fact"]
        return {"answers": (unsure(text) if text == "theta" else fixture(text=text))["answers"]}
    assert digest_driver.run_digestion(dsn, unit, flaky)["status"] == "absorbed"
    assert texts(dsn, host) == ["eta", "theta"]
    assert knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] == []


def test_canon_contradiction_is_logged_and_answered(dsn, host):
    """After digestion a contradiction with the canon is logged (canon untouched) and shown at the next session."""
    first = judgement(host, text="limit is 300 chars")
    first["facts"][0]["subject"] = "limit"  # same subject: the scan compares within one subject
    e1 = pg.register(dsn, first)
    pg.batch(dsn, 1, {e1["entry_id"]: [fixture(text="limit is 300 chars")]})
    pg.complete(dsn, first["work_unit_id"])
    assert digest_driver.run_digestion(dsn, first["work_unit_id"], judge_record)["status"] == "absorbed"
    second = judgement(host, text="limit is 1000 chars")
    second["facts"][0]["subject"] = "limit"
    e2 = pg.register(dsn, second)
    pg.batch(dsn, 1, {e2["entry_id"]: [fixture(text="limit is 1000 chars")]})
    pg.complete(dsn, second["work_unit_id"])
    assert digest_driver.run_digestion(dsn, second["work_unit_id"], judge_record)["status"] == "absorbed"
    contra = lambda state, texts_, q: [{"noul": 0.9 if "300" in t else 0.1} for t in texts_]
    out = pg.scan_contradictions(dsn, second["work_unit_id"], contra)
    assert out["scanned"] == 1 and out["contradictions"] >= 1
    assert pg.scan_contradictions(dsn, second["work_unit_id"], contra)["scanned"] == 0  # logged once
    assert set(texts(dsn, host)) >= {"limit is 300 chars", "limit is 1000 chars"}  # canon untouched
    items = [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "contradiction"]
    assert items and "정본에서 이 사실과 모순" in items[0]["why_waiting"][0]
    for it in items:
        assert pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "approve", "1000자가 맞아", None, it["question_ids"])["kind"] == "contradiction"
    assert [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "contradiction"] == []


def test_completion_quote_cannot_approve_review(dsn, host):
    body = two_facts(host, "kappa", "lambda")
    entry = pg.register(dsn, body)
    pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text="kappa"), fixture(text="lambda")]})
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # a fact that waits for the user (the guard is what is tested)
        cur.execute("update knowledge.check_receipt set combined='needs_review' where entry_id=%s and fact_index=1", (entry["entry_id"],))
    pg.register_completion_sources(dsn, body["work_unit_id"], ["user_confirm"])
    pg.signal_completion(dsn, body["work_unit_id"], "user_confirm", evidence={"quote": "좋아 이걸로 하자"})
    with pytest.raises(ValueError):
        pg.review_resolve(dsn, host, entry["entry_id"], 1, "approve", "좋아  이걸로 하자")
    assert pg.review_resolve(dsn, host, entry["entry_id"], 1, "reject", "좋아 이걸로 하자")["decision"] == "reject"
