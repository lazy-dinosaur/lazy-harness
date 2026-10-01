"""astra review P1 (2026-10-01), reproduced: Korean view keeps every result conditional; delete vs rewrite is a merge
conflict; canon duplicate is judged on the canon after the pass; an update Jev calls a duplicate still applies; a
failed canon scan is retried; the DB rejects an empty form."""
import json

import pytest

import digest_driver
import fact_form
import fact_text
import merge_form
import store_pg as pg
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixtures)


def test_korean_view_repeats_the_condition_for_each_result():
    t, how = fact_text.to_korean(fact_form.parse("IF C가 없다 THEN A는 닫힌다 AND B는 숨겨진다"))
    assert (t, how) == ("C가 없으면 A는 닫힌다. C가 없으면 B는 숨겨진다.", "natural"), t


def test_delete_versus_rewrite_is_a_conflict():
    base = "창은 닫힌다 AND 입력은 비워진다"
    assert merge_form.merge(base, "입력은 비워진다", "창은 숨겨진다 AND 입력은 비워진다") == (None, "conflict")


def test_db_rejects_an_empty_form(dsn):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        for bad in ({}, {"kind": "plain"}, {"then": ["x"]}, {"kind": "if", "if": {}, "then": ["x"]}, {"kind": "before", "then": ["x"]}):
            cur.execute("select knowledge.valid_fact_form(%s::jsonb)", (json.dumps(bad),))
            assert cur.fetchone()[0] is False, bad
        cur.execute("select knowledge.valid_fact_form(%s::jsonb)", (json.dumps(fact_form.parse("IF A가 있다 THEN B는 된다")),))
        assert cur.fetchone()[0] is True


def seed(dsn, host, alias, text):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                       values (%s,%s,'p1',(select coalesce(max(seq),0)+1 from knowledge.fragment where host_id=%s and domain='p1'),
                       %s,'fact','p1:g',%s::jsonb) returning id::text""", (host, alias, host, text, json.dumps({"evidence_refs": []})))
        return cur.fetchone()[0]


def test_update_called_duplicate_by_jev_still_applies(dsn, host):
    f = seed(dsn, host, "p1a-1", "길이는 300자다")
    body = judgement(host, operation="update", target=f, text="길이는 1000자다")
    body["facts"][0]["expected_revision"] = 1
    e = pg.register(dsn, body)
    pg.batch(dsn, 1, {e["entry_id"]: [fixture(operation="update", text="길이는 1000자다", excerpt="길이는 300자다")]},
             entry_ids=[e["entry_id"]])
    pg.complete(dsn, body["work_unit_id"])

    def dup_judge(packet):  # Jev: 'no difference from the target'
        st = packet["state"]
        f_ = fixture(operation="update", text=st["candidate_fact"], excerpt=st.get("target_excerpt"))
        answers = {k: f_["answers"][k] for k in packet["questions"]}
        if "differs_from_target" in answers:
            answers["differs_from_target"] = {"type": "noul", "noul": 0.02}
        return {"answers": answers}
    digest_driver.run_digestion(dsn, body["work_unit_id"], dup_judge)
    assert [r["text"] for r in pg.rows(dsn, "fragment") if r["id"] == f] == ["길이는 1000자다"]


def test_canon_duplicate_ignores_a_fragment_deprecated_in_the_same_pass(dsn, host):
    def judge(packet):
        q = packet["questions"]
        op = "deprecate" if "replacement_exists" in q else ("update" if "target_excerpt" in packet["state"] else "add")
        f_ = fixture(operation=op, text=packet["state"]["candidate_fact"], excerpt=packet["state"].get("target_excerpt"))
        return {"answers": {k: f_["answers"][k] for k in q}}
    # first unit makes the canon fragment with a subject
    b0 = judgement(host, text="캐시는 7일 보관된다")
    b0["facts"][0]["subject"] = "캐시"
    e0 = pg.register(dsn, b0)
    pg.batch(dsn, 1, {e0["entry_id"]: [fixture(text="캐시는 7일 보관된다")]}, entry_ids=[e0["entry_id"]])
    pg.complete(dsn, b0["work_unit_id"])
    digest_driver.run_digestion(dsn, b0["work_unit_id"], judge)
    old = [r for r in pg.rows(dsn, "fragment") if r["host_id"] == host and r["text"] == "캐시는 7일 보관된다"][0]
    # second unit: deprecate it and add the same sentence as a new fragment (e.g. moved to another domain)
    dep = judgement(host, operation="deprecate", target=str(old["id"]), text="캐시 보관 규칙을 옮긴다")
    dep["facts"][0]["expected_revision"] = old["revision"]
    uid = dep["work_unit_id"]
    e1 = pg.register(dsn, dep)
    pg.batch(dsn, 1, {e1["entry_id"]: [fixture(operation="deprecate", text="캐시 보관 규칙을 옮긴다", excerpt=old["text"])]},
             entry_ids=[e1["entry_id"]])
    add = judgement(host, text="캐시는 7일 보관된다")
    add["facts"][0]["subject"] = "캐시"
    add["work_unit_id"] = uid
    e2 = pg.register(dsn, add)
    pg.batch(dsn, 1, {e2["entry_id"]: [fixture(text="캐시는 7일 보관된다")]}, entry_ids=[e2["entry_id"]])
    pg.complete(dsn, uid)
    digest_driver.run_digestion(dsn, uid, judge)
    live = [r for r in pg.rows(dsn, "fragment") if r["host_id"] == host and r["active"] and r["text"] == "캐시는 7일 보관된다"]
    assert len(live) == 1 and live[0]["id"] != old["id"], live  # the fact survives as the new fragment


def test_failed_canon_scan_is_listed_for_a_retry(dsn, host):
    def absorb(text):
        b_ = judgement(host, text=text)
        b_["facts"][0]["subject"] = "재시도 대상"
        e_ = pg.register(dsn, b_)
        pg.batch(dsn, 1, {e_["entry_id"]: [fixture(text=text)]}, entry_ids=[e_["entry_id"]])
        pg.complete(dsn, b_["work_unit_id"])
        digest_driver.run_digestion(dsn, b_["work_unit_id"], lambda p: {"answers": fixture(text=p["state"]["candidate_fact"])["answers"]})
        return b_
    first = absorb("재시도 대상은 3회다")
    pg.scan_contradictions(dsn, first["work_unit_id"], lambda state, texts, q: [{"noul": 0.0} for _ in texts])
    b = absorb("재시도 대상은 5회다")  # a neighbour exists, so the judge is called
    assert b["work_unit_id"] in pg.units_to_scan(dsn, limit=1000)  # never scanned yet
    boom = lambda state, texts, q: (_ for _ in ()).throw(RuntimeError("Jev down"))
    with pytest.raises(RuntimeError):
        pg.scan_contradictions(dsn, b["work_unit_id"], boom)
    assert b["work_unit_id"] in pg.units_to_scan(dsn, limit=1000)  # still waiting for a scan
    pg.scan_contradictions(dsn, b["work_unit_id"], lambda state, texts, q: [{"noul": 0.0} for _ in texts])
    assert b["work_unit_id"] not in pg.units_to_scan(dsn, limit=1000)
