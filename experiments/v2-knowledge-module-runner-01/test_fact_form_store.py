"""0010 fact form stored: record parses the operator string into form (DB checks the shape); digestion copies it to
the fragment and writes one leaf row per sentence with its subject and polarity."""
import json

import pytest

import digest_driver
import fact_form
import knowledge_cli
import store_pg as pg
from test_store_pg import fixture, host  # noqa: F401 (fixture)

RULE = "IF 보관 위치가 없다 OR 보관 위치가 비활성 상태다 THEN 첨부 파일은 고아 첨부로 분류된다 AND 첨부 파일은 목록에 보이지 않는다"


def test_parse_shapes():
    f = fact_form.parse(RULE)
    assert f == {"kind": "if", "if": {"op": "OR", "args": [{"leaf": "보관 위치가 없다"}, {"leaf": "보관 위치가 비활성 상태다"}]},
                 "then": ["첨부 파일은 고아 첨부로 분류된다", "첨부 파일은 목록에 보이지 않는다"]}
    assert [(x["role"], x["polarity"]) for x in fact_form.leaves(f)] == [("if", "neg"), ("if", "pos"), ("then", "pos"), ("then", "neg")]
    g = fact_form.parse("IF (방이 열린다 OR 방이 포커스된다) AND 사용자가 있다 EVEN IF 창이 숨겨져 있다 THEN A는 읽는다 "
                        "EXCEPT WHEN 관리자가 막는다 BECAUSE 규칙이다")
    assert g["if"] == {"op": "AND", "args": [{"op": "OR", "args": [{"leaf": "방이 열린다"}, {"leaf": "방이 포커스된다"}]},
                                          {"leaf": "사용자가 있다"}]}
    assert g["even_if"] == {"leaf": "창이 숨겨져 있다"} and g["then"] == ["A는 읽는다"]
    assert g["except"] == {"leaf": "관리자가 막는다"} and g["because"] == "규칙이다"
    assert fact_form.parse("AFTER 캐시를 올렸다 THEN 빌드가 줄었다") == {"kind": "after", "anchor": "캐시를 올렸다", "then": ["빌드가 줄었다"]}
    assert fact_form.parse("화면은 목록을 보여 준다.") == {"kind": "plain", "then": ["화면은 목록을 보여 준다"]}
    assert fact_form.parse("A는 된다 OR B는 된다")["join"] == "OR"
    assert fact_form.condition_key(f) != fact_form.condition_key(fact_form.parse("첨부 파일은 고아 첨부로 분류된다"))


def rule_fact(text):
    return {"operation": "add", "kind": "fact", "subject": "첨부 파일", "fact": text, "reason": "r",
            "evidence_source": "user_confirmed", "keywords": ["첨부 파일"],
            "evidence_refs": [{"type": "user_utterance", "locator": "test/local", "quote": text}]}


def test_record_stores_form_and_digestion_writes_leaves(dsn, host):
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [rule_fact(RULE)]})
    assert out.get("entry_id"), out
    entry = [e for e in pg.rows(dsn, "ledger_entry") if e["entry_id"] == out["entry_id"]][0]
    assert entry["judgement_body"]["facts"][0]["form"] == fact_form.parse(RULE)
    pg.batch(dsn, 1, {out["entry_id"]: [fixture(text=RULE)]}, entry_ids=[out["entry_id"]])
    pg.complete(dsn, out["work_unit_id"])
    judge = lambda packet: {"answers": fixture(text=packet["state"]["candidate_fact"])["answers"]}
    assert digest_driver.run_digestion(dsn, out["work_unit_id"], judge)["status"] == "absorbed"
    frag = [r for r in pg.rows(dsn, "fragment") if r["host_id"] == host and r["text"] == RULE][0]
    assert frag["form"] == fact_form.parse(RULE) and frag["subject_id"]
    leaves = sorted((r for r in pg.rows(dsn, "fragment_leaf") if r["fragment_id"] == frag["id"]), key=lambda r: r["ord"])
    assert [(r["role"], r["polarity"]) for r in leaves] == [("if", "neg"), ("if", "pos"), ("then", "pos"), ("then", "neg")]
    assert {r["subject_id"] for r in leaves if r["role"] == "then"} == {frag["subject_id"]}  # the fact subject
    names = {r["subject_id"]: r["name"] for r in pg.rows(dsn, "subject") if r["host_id"] == host}
    assert {names.get(r["subject_id"]) for r in leaves if r["role"] == "if"} == {"보관 위치"}  # the leaf's own head


def test_db_rejects_a_malformed_form(dsn, host):
    body = {"judgement_id": "form-bad", "version": 1, "host_id": host, "partition_key": "D",
            "work_unit_id": "00000000-0000-4000-8000-0000000000f1",
            "facts": [{**rule_fact("x"), "form": {"kind": "if", "then": ["y"]}}]}  # IF without a condition
    with pytest.raises(pg.driver.Error):
        pg.register(dsn, body)
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select knowledge.valid_fact_form(%s::jsonb)", (json.dumps(fact_form.parse(RULE), ensure_ascii=False),))
        assert cur.fetchone()[0] is True


def test_contradiction_scan_compares_leaves_under_the_same_condition(dsn, host):
    """contra05 + user 2026-10-02: same subject, same condition, or a plain fact that says always (항상); a plain default
    vs a rule is an exception (not asked as a contradiction); rules under other conditions are not asked."""
    from test_store_pg import judgement

    def absorb(text):
        body = judgement(host, text=text)
        body["facts"][0]["subject"] = "첨부 파일"
        entry = pg.register(dsn, body)
        pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text=text)]}, entry_ids=[entry["entry_id"]])
        pg.complete(dsn, body["work_unit_id"])
        judge = lambda packet: {"answers": fixture(text=packet["state"]["candidate_fact"])["answers"]}
        assert digest_driver.run_digestion(dsn, body["work_unit_id"], judge)["status"] == "absorbed"
        return body["work_unit_id"]

    absorb("첨부 파일은 항상 30일 보관된다")
    absorb("IF 보관 위치가 없다 THEN 첨부 파일은 7일 보관된다")
    unit = absorb("IF 사용자가 고정한다 THEN 첨부 파일은 영구 보관된다")
    asked = []

    def contra(state, texts, q):
        asked.append((state["fact"], list(texts)))
        return [{"noul": 0.9 if "30일" in t else 0.1} for t in texts]
    assert pg.scan_contradictions(dsn, unit, contra) == {"scanned": 1, "contradictions": 1}
    assert asked == [("IF 사용자가 고정한다 THEN 첨부 파일은 영구 보관된다", ["첨부 파일은 항상 30일 보관된다"])], asked
    logged = [q for q in pg.rows(dsn, "confirmation_queue") if q["rule_id"] == "canon_contradiction"
              and "영구 보관" in str(q["reason"])]
    assert len(logged) == 1 and "30일" in str(logged[0]["reason"])
    # the item stays open until one side really changes (it is not closed by comparing a leaf with the whole text)
    import knowledge_cli
    items = [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "contradiction"]
    assert len(items) == 1 and "영구 보관" in items[0]["fact"], items


def test_canon_scan_also_compares_vector_neighbours_under_another_subject(dsn, host):
    """flow3 r3: the same concept under another subject is caught through the vector neighbours."""
    from test_store_pg import judgement

    def absorb(text, subject):
        body = judgement(host, text=text)
        body["facts"][0]["subject"] = subject
        entry = pg.register(dsn, body)
        pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text=text)]}, entry_ids=[entry["entry_id"]])
        pg.complete(dsn, body["work_unit_id"])
        judge = lambda packet: {"answers": fixture(text=packet["state"]["candidate_fact"])["answers"]}
        assert digest_driver.run_digestion(dsn, body["work_unit_id"], judge)["status"] == "absorbed"
        return body["work_unit_id"]

    absorb("도메인 설명은 최대 300자까지 저장된다", "도메인 설명")
    unit = absorb("설명 길이 제한은 최대 1000자다", "설명 길이 제한")
    contra = lambda state, texts, q: [{"noul": 0.9 if "300자" in t else 0.1} for t in texts]
    assert pg.scan_contradictions(dsn, unit, contra)["contradictions"] == 1


def test_cut_subject_is_rejected(dsn, host):
    import knowledge_cli
    f = {"operation": "add", "kind": "fact", "subject": "도메인", "fact": "도메인 설명 길이는 1000자다", "reason": "r",
         "evidence_source": "user_confirmed", "keywords": ["도메인"],
         "evidence_refs": [{"type": "user_utterance", "locator": "t", "quote": "도메인 설명 길이는 1000자다"}]}
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [f]})
    assert [e["code"] for e in out["errors"]] == ["E_SUBJECT"], out
    t2 = "store_pg.py와 digest_driver.py의 자동 생성 설명은 1000자로 잘린다"
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [{
        **f, "subject": "store_pg.py와", "fact": t2, "keywords": ["store_pg.py"],
        "evidence_refs": [{"type": "user_utterance", "locator": "t", "quote": t2}]}]})
    assert "E_SUBJECT" in [e["code"] for e in out["errors"]], out
