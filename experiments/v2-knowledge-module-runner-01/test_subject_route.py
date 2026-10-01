"""Domain by subject (a known subject's domain is decided in code) and embeddings from the Korean view."""
import digest_driver
import domain_router as dr
import store_pg as pg
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixtures)


def judge(packet):
    return {"answers": fixture(text=packet["state"]["candidate_fact"])["answers"]}


def absorb(dsn, host, text, subject, partition, choose, stored=None):
    body = judgement(host, text=text)
    body["partition_key"] = partition
    body["facts"][0]["subject"] = subject
    entry = pg.register(dsn, body)
    pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text=text)]}, entry_ids=[entry["entry_id"]])
    pg.complete(dsn, body["work_unit_id"])
    out = digest_driver.run_digestion(dsn, body["work_unit_id"], judge, choose=choose)
    want = stored or text  # digestion rewrites a matched subject to the dictionary name
    return out, [r["domain"] for r in pg.rows(dsn, "fragment") if r["host_id"] == host and r["text"] == want][0]


def test_known_subject_routes_in_code(dsn, host):
    none = lambda text, options: {k: 0.0 for k in options}
    absorb(dsn, host, "첨부 파일은 30일 보관된다", "첨부 파일", "예약", none)
    absorb(dsn, host, "채팅방 이름은 부서명이다", "채팅방", "채팅", none)
    calls = []

    def to_chat(text, options):
        calls.append(text)
        return {k: (.9 if options[k].startswith("채팅") else .05) for k in options}
    # the worker proposes '체팅' (not an existing domain) and Jev would say 채팅; the subject already lives in 예약
    out, d = absorb(dsn, host, "IF 보관 위치가 없다 THEN 첨부 파일 화면은 7일 보관된다", "첨부 파일 화면", "체팅", to_chat,
                    stored="IF 보관 위치가 없다 THEN 첨부 파일은 7일 보관된다")
    assert d == "예약" and calls == [], (out, d, calls)
    # an unknown subject still goes to Jev
    out, d = absorb(dsn, host, "알림음은 끄지 않는다", "알림음", "체팅", to_chat)
    assert d == "채팅" and len(calls) == 1, (out, d, calls)


def test_embedding_input_is_the_korean_view():
    assert pg._embedding_input("fact", "d", [], "IF A가 없다 THEN B는 닫힌다", "plain") == "A가 없으면 B는 닫힌다."
    assert pg._embedding_input("fact", "d", [], "화면은 목록을 보여 준다", "plain") == "화면은 목록을 보여 준다"
    assert pg._embedding_input("fact", "d", ["x"], "IF A가 없다 THEN B는 닫힌다", "ctx-v1").endswith("] A가 없으면 B는 닫힌다.")
