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
    if q == pg.SAME_Q:  # the linked subjects of these tests are the same thing (identifier / feature name)
        return [{"noul": 0.9} for _ in texts]
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
    judge = lambda state, texts, q: [{"noul": 0.9 if q == pg.SAME_Q or ("선택" in t and "필수" in state["fact"]) else 0.0}
                                     for t in texts]
    assert pg.scan_contradictions(dsn, unit, judge)["contradictions"] >= 1


def test_a_name_inside_a_longer_word_is_not_a_link(dsn, host):
    assert pg._names_in("반품API", "반품API는 정보를 준다") and pg._names_in("반품API", "회수접수는 반품API의 기능명이다")
    assert not pg._names_in("API", "GraphAPI는 빠르다") and not pg._names_in("반품API", "물류반품API는 없다")


def test_related_but_different_subjects_are_not_compared_and_the_verdict_is_cached(dsn, host):
    """contra07 r4-6: '서울센터는 포장정책의 적용 센터다' links the names but they are not the same thing; their different
    values must not be asked as a contradiction. The 'not the same' verdict is asked once."""
    asked = []

    def judge(state, texts, q):
        if q == pg.SAME_Q:
            asked.append(texts[0])
            return [{"noul": 0.05} for _ in texts]
        return [{"noul": 0.9 if ("2겹" in t and "4겹" in state["fact"]) or ("4겹" in t and "2겹" in state["fact"]) else 0.0}
                for t in texts]
    _absorb(dsn, host, "서울센터는 포장정책의 적용 센터다", "서울센터")
    _absorb(dsn, host, "포장정책은 완충재 겹수가 2겹이다", "포장정책")
    unit = _absorb(dsn, host, "서울센터는 완충재 겹수가 4겹이다", "서울센터")
    assert pg.scan_contradictions(dsn, unit, judge)["contradictions"] == 0
    assert len(asked) == 1
    later = _absorb(dsn, host, "서울센터는 완충재 종류가 에어커튼이다", "서울센터")
    pg.scan_contradictions(dsn, later, judge)
    assert len(asked) == 1  # cached per subject pair


def test_link_verdict_is_reasked_when_its_evidence_changes(dsn, host):
    """astra same review: a stored 'same/not same' verdict holds only while its naming sentence is unchanged."""
    asked = []

    def judge(state, texts, q):
        if q == pg.SAME_Q:
            asked.append(state["fact"])
            return [{"noul": 0.05} for _ in texts]
        return [{"noul": 0.0} for _ in texts]
    _absorb(dsn, host, "부산센터는 피킹정책의 적용 센터다", "부산센터")
    _absorb(dsn, host, "피킹정책은 배치 크기가 24개다", "피킹정책")
    pg.scan_contradictions(dsn, _absorb(dsn, host, "부산센터는 배치 크기가 48개다", "부산센터"), judge)
    assert len(asked) == 1
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # the naming sentence is rewritten
        cur.execute("""update knowledge.fragment set revision=revision+1, text='부산센터는 피킹정책의 별칭이다'
                       where host_id=%s and text='부산센터는 피킹정책의 적용 센터다'""", (host,))
    pg.scan_contradictions(dsn, _absorb(dsn, host, "부산센터는 배치 단위가 상자다", "부산센터"), judge)
    assert len(asked) == 2  # re-asked for the new evidence


def test_rejected_link_does_not_come_back_through_the_vector_path(dsn, host, monkeypatch):
    """astra same review: a pair rejected by SAME_Q must not be judged again as a vector neighbour."""
    seen = {}

    def fake_vec(dsn_, host_, fid, text, asked, judge):
        seen["asked"] = set(asked)
        return []
    monkeypatch.setattr(pg, "_vector_contradictions", fake_vec)
    judge = lambda state, texts, q: [{"noul": 0.05 if q == pg.SAME_Q else 0.0} for _ in texts]
    _absorb(dsn, host, "대구센터는 포장정책의 적용 센터다", "대구센터")
    _absorb(dsn, host, "포장정책은 완충재가 2겹이다", "포장정책")
    pg.scan_contradictions(dsn, _absorb(dsn, host, "대구센터는 완충재가 4겹이다", "대구센터"), judge)
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select alias from knowledge.fragment where host_id=%s and text='포장정책은 완충재가 2겹이다'", (host,))
        other = cur.fetchone()[0]
    assert other in seen["asked"]


def test_rejected_link_does_not_come_back_through_the_warned_leaf_path(dsn, host):
    """astra same review r2: a linked leaf with a W_FORM warning was also added as a 'warned' leaf without the link."""
    judged = []

    def judge(state, texts, q):
        if q == pg.SAME_Q:
            return [{"noul": 0.05} for _ in texts]
        judged.extend(texts)
        return [{"noul": 0.9 if "2겹" in t else 0.0} for t in texts]
    _absorb(dsn, host, "광주센터는 묶음정책의 적용 센터다", "광주센터")
    _absorb(dsn, host, "묶음정책은 완충재가 2겹이고 포장재는 종이다", "묶음정책")  # a warned leaf (connective)
    unit = _absorb(dsn, host, "광주센터는 완충재가 4겹이다", "광주센터")
    assert pg.scan_contradictions(dsn, unit, judge)["contradictions"] == 0, judged


def test_rejected_link_holds_when_the_scanned_fact_is_warned(dsn, host):
    """astra same review r3: a scanned fragment with a warned leaf (wide query) must still respect 'not the same'."""
    judge_calls = []

    def judge(state, texts, q):
        if q == pg.SAME_Q:
            return [{"noul": 0.05} for _ in texts]
        judge_calls.extend(texts)
        return [{"noul": 0.9 if "2겹" in t else 0.0} for t in texts]
    _absorb(dsn, host, "울산센터는 덮개정책의 적용 센터다", "울산센터")
    _absorb(dsn, host, "덮개정책은 완충재가 2겹이다", "덮개정책")
    unit = _absorb(dsn, host, "울산센터는 완충재가 4겹이고 포장재는 종이다", "울산센터")  # warned: wide query
    assert pg.scan_contradictions(dsn, unit, judge)["contradictions"] == 0, judge_calls


def test_a_canon_leaf_that_states_this_subject_is_compared_without_the_same_check(dsn, host):
    """astra same review r4: '알림 창은 닫히지 않고 입력 상자는 비워지지 않는다' (canon) states '입력 상자'; a later
    '입력 상자는 비워진다' must be compared even though '알림 창' and '입력 상자' are not the same thing."""
    def judge(state, texts, q):
        if q == pg.SAME_Q:
            return [{"noul": 0.05} for _ in texts]  # not the same thing
        return [{"noul": 0.9 if ("비워지지" in t) != ("비워지지" in state["fact"]) else 0.0} for t in texts]
    _absorb(dsn, host, "알림 창은 닫히지 않고 입력 상자는 비워지지 않는다", "알림 창")
    unit = _absorb(dsn, host, "입력 상자는 비워진다", "입력 상자")
    assert pg.scan_contradictions(dsn, unit, judge)["contradictions"] >= 1
