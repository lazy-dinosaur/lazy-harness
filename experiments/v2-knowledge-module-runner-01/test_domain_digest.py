"""End-to-end: digestion routes an add to an existing domain and creates new ones only when Jev is confident."""
import json

import digest_driver
import domain_router as dr
import store_pg as pg
from test_store_pg import host, judgement  # fixtures / helper


def absorb(dsn, host, text, partition_key, choose):
    body = judgement(host, text=text)
    body["partition_key"] = partition_key
    entry = pg.register(dsn, body)
    uid = body["work_unit_id"]
    answers = {"is_new": {"type": "noul", "noul": .96},
               "durability": {"type": "choice", "probabilities": {"durable_fact": .96, "transient_progress": .02, "explanation_only": .01, "none_or_uncertain": .01}},
               "impact": {"type": "choice", "probabilities": {"changes_decisions": .97, "reference_only": .01, "no_future_use": .01, "none_or_uncertain": .01}},
               "is_supported": {"type": "choice", "probabilities": {"direct": .96, "partial": .02, "none": .01, "none_or_uncertain": .01}}}
    import worktime_driver
    worktime_driver.run_worktime(dsn, 1, lambda packet: {"answers": {k: answers[k] for k in packet["questions"]}}, entry_ids=[entry["entry_id"]])
    pg.register_completion_sources(dsn, uid, ["user_confirm"])
    pg.signal_completion(dsn, uid, "user_confirm", evidence={"quote": "좋아", "locator": None})
    out = digest_driver.run_digestion(dsn, uid, lambda packet: {"answers": {k: answers[k] for k in packet["questions"]}}, choose=choose)
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select domain from knowledge.fragment where host_id=%s and text=%s and active", (host, text))
        row = cur.fetchone()
    return out, (row[0] if row else None)


def test_digestion_routes_domain(dsn, host):
    none = lambda text, options: {k: 0.0 for k in options}
    out, d1 = absorb(dsn, host, "예약 기본 길이는 30분이다", "예약", none)
    assert d1 == "예약", out  # first domain created from the worker's name
    to_existing = lambda text, options: {k: (.9 if options[k].startswith("예약") else .05) for k in options}
    out, d2 = absorb(dsn, host, "예약 시간 단위는 10분이다", "reservation", to_existing)
    assert d2 == "예약", out  # 'reservation' routed to the existing domain, no new name
    new = lambda text, options: {k: (.9 if k == "none" else .05) for k in options}
    out, d3 = absorb(dsn, host, "채팅방 이름은 부서명이다", "채팅", new)
    assert d3 == "채팅", out
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        names = sorted(r["domain"] for r in dr.list_domains(cur, host))
    assert names == ["예약", "채팅"]


def test_domain_show_follows_merge(dsn, host):
    none = lambda text, options: {k: 0.0 for k in options}
    absorb(dsn, host, "배포는 main 에서만 한다", "배포", none)
    new = lambda text, options: {k: (.9 if k == "none" else .05) for k in options}
    out, d = absorb(dsn, host, "CI runner 메모리는 16GiB 이다", "CI 배포", new)
    assert d == "CI 배포", out
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        assert [r["text"] for r in dr.fragments(cur, host, "배포")] == ["배포는 main 에서만 한다"]
        # knowledge shared by two domains is handled by merge: the survivor shows both
        dr.merge(cur, host, "CI 배포", "배포")
        assert sorted(r["text"] for r in dr.fragments(cur, host, "배포")) == ["CI runner 메모리는 16GiB 이다", "배포는 main 에서만 한다"]
