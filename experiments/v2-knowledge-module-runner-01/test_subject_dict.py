"""Subject dictionary: record time matches existing subjects (read only); digestion registers (single writer);
canon contradictions are compared within one subject."""
import digest_driver
import knowledge_cli
import store_pg as pg
import subject_dict
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixtures)

# fake vectors keyed by subject_dict.core(name)
VEC = {"예약관리": [1.0, 0.0, 0.0], "예약 관리": [0.99, 0.14, 0.0], "예약관리 sdd": [0.95, 0.0, 0.31], "채팅": [0.0, 1.0, 0.0]}


def fake_embed(names):
    return [VEC.get(n, [0.0, 0.0, 1.0]) for n in names]


def same(state, texts, question):
    # Jev sees JSON {name, sentences}: '예약 관리 기능' is the same entity as '예약관리'; '예약관리 SDD' (a document) is not
    return [0.9 if state["new"]["name"] == "예약 관리 기능" and '"sentences"' in t else 0.1 for t in texts]


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


def stored(dsn, entry_id):
    return [e for e in pg.rows(dsn, "ledger_entry") if e["entry_id"] == entry_id][0]["judgement_body"]["facts"][0]


def test_core_strips_generic_tails_only():
    assert subject_dict.core("CALL 화면") == "call" and subject_dict.core("staging 채널 기능") == "staging 채널"
    assert subject_dict.core("`chat.markAsRead` 함수") == "chat.markasread" and subject_dict.core("채팅창") == "채팅"
    assert subject_dict.core("채팅 리액션 팝업 테스트") == "채팅 리액션 팝업 테스트"  # a test is another thing
    assert subject_dict.core("예약관리 SDD") == "예약관리 sdd" and subject_dict.core("화면") == "화면"


def test_record_time_reuses_existing_subject_and_keeps_documents_apart(dsn, host):
    assert absorb(dsn, body_of(host, "예약관리는 30분 단위로 예약을 받는다", "예약관리"),
                  same=same, embed_fn=fake_embed)["status"] == "absorbed"
    rec = lambda f: knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [f]}, same=same, embed_fn=fake_embed)
    recorded = []
    # generic tail: code match, no Jev
    out = rec(body_of(host, "예약관리 페이지는 10분 단위로 예약을 받는다", "예약관리 페이지")["facts"][0])
    recorded.append(out["entry_id"])
    assert out.get("subjects") == [{"fact_index": 0, "from": "예약관리 페이지", "to": "예약관리", "how": "alias"}], out
    f = stored(dsn, out["entry_id"])
    assert f["fact"] == "예약관리는 10분 단위로 예약을 받는다" and f["subject"] == "예약관리"
    assert f["subject_as_written"] == "예약관리 페이지" and not f.get("subject_new")
    # other spelling: vector candidate + Jev with sentences (JSON)
    out = rec(body_of(host, "예약 관리 기능에서 취소는 1시간 전까지다", "예약 관리 기능")["facts"][0])
    recorded.append(out["entry_id"])
    assert out.get("subjects") == [{"fact_index": 0, "from": "예약 관리 기능", "to": "예약관리", "how": "same_entity"}], out
    assert stored(dsn, out["entry_id"])["fact"] == "예약관리에서 취소는 1시간 전까지다"
    # a document about it stays a different subject and the record never writes the dictionary
    out = rec(body_of(host, "예약관리 SDD는 이번 작업에서 갱신되지 않는다", "예약관리 SDD")["facts"][0])
    recorded.append(out["entry_id"])
    assert "subjects" not in out, out
    f = stored(dsn, out["entry_id"])
    assert f["subject"] == "예약관리 SDD" and f["subject_new"] is True
    assert [r for r in pg.rows(dsn, "subject") if r["host_id"] == host and r["name"] == "예약관리 SDD"] == []
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


def test_flow3_r2_wrong_merges_and_broken_rewrites_are_blocked():
    always = lambda state, texts, q: [0.99 for _ in texts]
    assert subject_dict.decide("도메인 설명 길이", [{"name": "도메인 설명", "subject_id": "x"}], always) is None
    assert subject_dict.decide("domain describe", [{"name": "도메인 설명", "subject_id": "x"}], always) is None
    assert subject_dict.decide("예약 관리 기능", [{"name": "예약관리", "subject_id": "x"}], always)["name"] == "예약관리"
    r = subject_dict.rewrite
    assert r("도메인 설명 길이는 1000자다", "도메인 설명", "도메인 설명 길이") == "도메인 설명 길이는 1000자다"
    assert r("CALL 화면은 소리를 낸다", "CALL 화면", "CALL") == "CALL은 소리를 낸다"
    assert r("자동 생성 설명은 잘린다", "자동 생성 설명", "예약관리") == "예약관리는 잘린다"
    assert r("IF A가 없다 THEN 예약 관리 기능에서 취소된다 AND 예약 관리 기능은 닫힌다", "예약 관리 기능", "예약관리") == \
        "IF A가 없다 THEN 예약관리에서 취소된다 AND 예약관리는 닫힌다"
    assert r("x.py의 ensure는 자른다", "ensure", "domain_router.ensure") == "x.py의 domain_router.ensure는 자른다"
