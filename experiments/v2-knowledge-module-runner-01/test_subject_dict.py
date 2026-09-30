"""Subject dictionary: record time matches existing subjects (read only); digestion registers (single writer);
canon contradictions are compared within one subject."""
import digest_driver
import knowledge_cli
import store_pg as pg
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixtures)

VEC = {"예약관리": [1.0, 0.0, 0.0], "예약관리 페이지": [0.99, 0.14, 0.0], "예약관리 sdd": [0.95, 0.0, 0.31], "채팅": [0.0, 1.0, 0.0]}


def fake_embed(names):
    return [VEC.get(n, [0.0, 0.0, 1.0]) for n in names]


def same(state, texts, question):
    # '예약관리 페이지' is the same entity as '예약관리'; a document about it ('예약관리 SDD') is not
    return [0.9 if t.split(" ||| ")[0] == "예약관리 페이지" else 0.1 for t in texts]


def judge_record(packet):
    return {"answers": fixture(text=packet["state"]["candidate_fact"])["answers"]}


def body_of(host_id, text, subject):
    body = judgement(host_id, text=text)
    body["facts"][0]["subject"] = subject
    return body


def absorb(dsn, body, **kw):
    entry = pg.register(dsn, body)
    pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text=body["facts"][0]["fact"])]}, entry_ids=[entry["entry_id"]])
    pg.complete(dsn, body["work_unit_id"])
    return digest_driver.run_digestion(dsn, body["work_unit_id"], judge_record, **kw)


def frag(dsn, host_id, start):
    return [r for r in pg.rows(dsn, "fragment") if r["host_id"] == host_id and r["text"].startswith(start) and r["active"]]


def test_record_time_reuses_existing_subject_and_keeps_documents_apart(dsn, host):
    assert absorb(dsn, body_of(host, "예약관리는 30분 단위로 예약을 받는다", "예약관리"),
                  same=same, embed_fn=fake_embed)["status"] == "absorbed"
    page = body_of(host, "예약관리 페이지는 10분 단위로 예약을 받는다", "예약관리 페이지")["facts"][0]
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [page]}, same=same, embed_fn=fake_embed)
    recorded = [out["entry_id"]]
    assert out.get("subjects") == [{"fact_index": 0, "from": "예약관리 페이지", "to": "예약관리", "how": "same_entity"}], out
    stored = [e for e in pg.rows(dsn, "ledger_entry") if e["entry_id"] == out["entry_id"]][0]["judgement_body"]["facts"][0]
    assert stored["fact"] == "예약관리는 10분 단위로 예약을 받는다" and stored["subject"] == "예약관리"
    assert stored["subject_as_written"] == "예약관리 페이지" and not stored.get("subject_new")
    doc = body_of(host, "예약관리 SDD는 이번 작업에서 갱신되지 않는다", "예약관리 SDD")["facts"][0]
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [doc]}, same=same, embed_fn=fake_embed)
    recorded.append(out["entry_id"])
    assert "subjects" not in out, out
    stored = [e for e in pg.rows(dsn, "ledger_entry") if e["entry_id"] == out["entry_id"]][0]["judgement_body"]["facts"][0]
    assert stored["subject"] == "예약관리 SDD" and stored["subject_new"] is True
    assert [r for r in pg.rows(dsn, "subject") if r["host_id"] == host and r["name"] == "예약관리 SDD"] == []  # record never writes
    for eid in recorded:  # leave no 'proposed' entry behind for other tests' batch(window=1)
        body = [e for e in pg.rows(dsn, "ledger_entry") if e["entry_id"] == eid][0]["judgement_body"]
        pg.batch(dsn, 1, {eid: [fixture(text=body["facts"][0]["fact"])]}, entry_ids=[eid])


def test_digestion_rechecks_names_registered_after_the_record(dsn, host):
    first = body_of(host, "예약관리는 30분 단위로 예약을 받는다", "예약관리")
    second = body_of(host, "예약관리 페이지는 10분 단위로 예약을 받는다", "예약관리 페이지")
    e2 = pg.register(dsn, second)  # recorded before the first unit registered '예약관리'
    assert absorb(dsn, first, same=same, embed_fn=fake_embed)["status"] == "absorbed"
    pg.batch(dsn, 1, {e2["entry_id"]: [fixture(text=second["facts"][0]["fact"])]}, entry_ids=[e2["entry_id"]])
    pg.complete(dsn, second["work_unit_id"])
    assert digest_driver.run_digestion(dsn, second["work_unit_id"], judge_record, same=same, embed_fn=fake_embed)["status"] == "absorbed"
    rows = frag(dsn, host, "예약관리")
    assert sorted(r["text"] for r in rows) == ["예약관리는 10분 단위로 예약을 받는다", "예약관리는 30분 단위로 예약을 받는다"]
    assert len({r["subject_id"] for r in rows}) == 1 and rows[0]["subject_id"]
    assert [r["name"] for r in pg.rows(dsn, "subject") if r["host_id"] == host] == ["예약관리"]

    # canon contradiction scan compares within the subject, not every similar sentence
    assert absorb(dsn, body_of(host, "채팅은 30분 뒤 닫힌다", "채팅"), same=same, embed_fn=fake_embed)["status"] == "absorbed"
    contra = lambda state, texts, q: [{"noul": 0.9 if "30분" in t else 0.1} for t in texts]
    out = pg.scan_contradictions(dsn, second["work_unit_id"], contra)
    assert out == {"scanned": 1, "contradictions": 1}, out
    logged = [q for q in pg.rows(dsn, "confirmation_queue") if q["rule_id"] == "canon_contradiction" and q["entry_id"] == e2["entry_id"]]
    assert len(logged) == 1 and "예약관리는 30분" in str(logged[0]["reason"])
