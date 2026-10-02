"""contra07 (2026-10-02): facts about the same thing under another name were never compared. A canon fact that names the
other subject ('출고API는 식별자가 POST /v3/shipments다') links the two subjects; the judge still decides each pair."""
import digest_driver
import store_pg as pg
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixture)


def _absorb(dsn, host, text, subject):
    body = judgement(host, text=text)
    body["facts"][0]["subject"] = subject
    e = pg.register(dsn, body)
    pg.batch(dsn, 1, {e["entry_id"]: [fixture(text=text)]}, entry_ids=[e["entry_id"]])
    pg.complete(dsn, body["work_unit_id"])
    digest_driver.run_digestion(dsn, body["work_unit_id"], lambda p: {"answers": fixture(text=p["state"]["candidate_fact"])["answers"]})
    return body["work_unit_id"]


import pytest


@pytest.fixture(autouse=True)
def no_vector(monkeypatch):  # astra link review: prove the leaf path, not the vector neighbours
    monkeypatch.setattr(pg, "_vector_contradictions", lambda *a, **k: [])


def _judge(state, texts, q):
    return [{"noul": 0.9 if ("202" in t and "200" in state["fact"]) or ("필수" in t and "선택" in state["fact"]) else 0.0}
            for t in texts]


def test_identifier_named_in_a_canon_fact_links_the_subjects(dsn, host):
    _absorb(dsn, host, "출고API는 식별자가 POST /v3/shipments다", "출고API")
    _absorb(dsn, host, "출고API는 정상 접수 응답 코드가 202다", "출고API")
    unit = _absorb(dsn, host, "POST /v3/shipments는 정상 접수 응답 코드가 200이다", "POST /v3/shipments")
    assert pg.scan_contradictions(dsn, unit, _judge)["contradictions"] >= 1


def test_feature_name_fact_links_the_subjects(dsn, host):
    _absorb(dsn, host, "회수접수는 반품API의 기능명이다", "회수접수")
    _absorb(dsn, host, "반품API는 회수지 우편번호를 필수로 요구한다", "반품API")
    unit = _absorb(dsn, host, "회수접수는 회수지 우편번호를 선택 항목으로 지정한다", "회수접수")
    assert pg.scan_contradictions(dsn, unit, _judge)["contradictions"] >= 1


def test_unrelated_subjects_are_not_linked(dsn, host):
    _absorb(dsn, host, "기사앱은 오프라인 서명을 지원한다", "기사앱")
    unit = _absorb(dsn, host, "창고맵은 구역 색상을 표시한다", "창고맵")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select subject_id::text from knowledge.fragment where host_id=%s and text like '창고맵%%'", (host,))
        sid = cur.fetchone()[0]
        assert pg._linked_subjects(cur, host, [sid]) == []
    pg.scan_contradictions(dsn, unit, _judge)


def test_linked_in_the_other_direction(dsn, host):
    _absorb(dsn, host, "회수접수는 반품API의 기능명이다", "회수접수")
    _absorb(dsn, host, "회수접수는 회수지 우편번호를 선택 항목으로 지정한다", "회수접수")
    unit = _absorb(dsn, host, "반품API는 회수지 우편번호를 필수로 요구한다", "반품API")
    judge = lambda state, texts, q: [{"noul": 0.9 if ("선택" in t and "필수" in state["fact"]) else 0.0} for t in texts]
    assert pg.scan_contradictions(dsn, unit, judge)["contradictions"] >= 1


def test_a_name_inside_a_longer_word_is_not_a_link(dsn, host):
    assert pg._names_in("반품API", "반품API는 정보를 준다") and pg._names_in("반품API", "회수접수는 반품API의 기능명이다")
    assert not pg._names_in("API", "GraphAPI는 빠르다") and not pg._names_in("반품API", "물류반품API는 없다")
