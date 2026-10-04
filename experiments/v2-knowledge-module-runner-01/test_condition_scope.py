"""real01 r07/r19 (2026-10-03, user 'a'): a wider fact that names the narrower fact's case and says something else
there is a contradiction (SCOPE3_Q, one choice), not a default + exception; conditions written differently are compared when one
contains the other (COND_Q). A wider fact that speaks generally stays a default + exception (2026-10-02 rule)."""
import store_pg as pg
from test_declared_alias import _absorb
from test_store_pg import host  # noqa: F401 (fixture)


def _judge(scope=0.0, exc=0.0, cond=0.0, canon=0.0, seen=None):
    def judge(state, texts, q, criteria=None):
        if seen is not None:
            seen.append(q[:12])
        if criteria:  # the merged wider/narrower question (SCOPE3_Q): one option wins (a valid distribution)
            top = "contradiction" if scope >= 0.5 else "exception" if exc >= 0.5 else "neither"
            return [{"type": "choice", "probabilities": {k: (0.9 if k == top else 0.05)
                                                         for k in ("contradiction", "exception", "neither")}}
                    for _ in texts]
        score = cond if q.startswith(pg.COND_Q[:20]) else canon
        return [{"noul": score} for _ in texts]
    return judge


def _exceptions(dsn, host):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select count(*) from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
                       where e.host_id=%s and q.rule_id='canon_exception'""", (host,))
        return cur.fetchone()[0]


def test_a_default_that_names_the_case_contradicts_the_rule(dsn, host):
    _absorb(dsn, host, "검토화면은 WRITING 행을 열 수 없다", "검토화면")
    later = _absorb(dsn, host, "IF 행은 WRITING이다 THEN 검토화면은 행을 열 수 있다", "검토화면")
    out = pg.scan_contradictions(dsn, later, _judge(scope=0.9, exc=0.9))
    assert out["contradictions"] >= 1 and _exceptions(dsn, host) == 0


def test_a_general_default_and_a_conditional_rule_both_stand(dsn, host):
    _absorb(dsn, host, "수수료는 0원이다", "수수료")
    later = _absorb(dsn, host, "IF 해외 주문이다 THEN 수수료는 3%다", "수수료")
    out = pg.scan_contradictions(dsn, later, _judge(scope=0.1, exc=0.9))
    assert out["contradictions"] == 0 and _exceptions(dsn, host) == 1


def test_conditions_written_differently_are_compared_when_one_contains_the_other(dsn, host):
    _absorb(dsn, host, "IF 배열은 존재한다 EVEN IF 배열은 비어 있다 THEN 파서는 배열을 권위 있는 값으로 취급한다", "파서")
    later = _absorb(dsn, host, "IF 배열은 존재하지만 비어 있다 THEN 파서는 배열을 권위 있는 값으로 취급하지 않는다", "파서")
    seen = []
    out = pg.scan_contradictions(dsn, later, _judge(scope=0.9, cond=0.9, seen=seen))
    assert out["contradictions"] >= 1
    assert any(s == pg.COND_Q[:12] for s in seen)


def test_different_situations_are_not_compared(dsn, host):
    _absorb(dsn, host, "IF 해외 주문이다 THEN 배송비는 3%다", "배송비")
    later = _absorb(dsn, host, "IF 급송 주문이다 THEN 배송비는 5%다", "배송비")
    seen = []
    out = pg.scan_contradictions(dsn, later, _judge(scope=0.9, exc=0.9, cond=0.1, canon=0.9, seen=seen))
    assert out["contradictions"] == 0  # COND_Q said different situations: never asked as a contradiction
    assert pg.SCOPE3_Q[:12] not in seen


def test_the_recheck_keeps_a_scoped_contradiction_open(dsn, host):
    _absorb(dsn, host, "검토화면은 WRITING 행을 열 수 없다", "검토화면")
    later = _absorb(dsn, host, "IF 행은 WRITING이다 THEN 검토화면은 행을 열 수 있다", "검토화면")
    judge = _judge(scope=0.9, exc=0.9)
    assert pg.scan_contradictions(dsn, later, judge)["contradictions"] >= 1
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""update knowledge.confirmation_queue set resolution='recheck' where rule_id='canon_contradiction'
                       and entry_id in (select entry_id from knowledge.ledger_entry where host_id=%s)""", (host,))
    out = pg.recheck_contradictions(dsn, judge, limit=50)
    assert out["rechecked"] > 0 and out["resolved"] == 0 and out["failed"] == 0, out


def test_a_missing_score_fails_instead_of_meaning_no(dsn, host):
    """astra scope review P1: an empty or NaN answer never closes or skips a pair."""
    import pytest
    _absorb(dsn, host, "검토화면은 WRITING 행을 열 수 없다", "검토화면")
    later = _absorb(dsn, host, "IF 행은 WRITING이다 THEN 검토화면은 행을 열 수 있다", "검토화면")
    with pytest.raises(ValueError, match="judge (score|choice|probability)"):
        pg.scan_contradictions(dsn, later, lambda state, texts, q, criteria=None: [{} for _ in texts])


def test_condition_questions_share_one_budget_and_ask_each_pair_once(dsn, host):
    """astra scope review P2: COND_Q is asked once per distinct condition pair within COND_MAX for the fragment."""
    for k in range(3):
        _absorb(dsn, host, f"IF 배열은 존재한다 EVEN IF 배열은 비어 있다 THEN 파서는 값{k}을 권위 있게 본다", "파서")
    later = _absorb(dsn, host, "IF 배열은 존재하지만 비어 있다 THEN 파서는 값0을 권위 있게 보지 않는다", "파서")
    seen = []
    pg.scan_contradictions(dsn, later, _judge(scope=0.0, exc=0.0, cond=0.9, seen=seen))
    assert seen.count(pg.COND_Q[:12]) == 1  # one call ...


def test_every_vector_candidate_with_a_contained_condition_gets_the_scope_question(dsn, host, monkeypatch):
    """astra scope r2 P1 / r3 P2: two vector candidates under the same condition; COND_Q asks one item, SCOPE3_Q gets
    both, and only the one that contradicts (B) is returned."""
    _absorb(dsn, host, "IF 배열은 존재한다 EVEN IF 배열은 비어 있다 THEN 파서A는 로그를 남긴다", "파서A")
    _absorb(dsn, host, "IF 배열은 존재한다 EVEN IF 배열은 비어 있다 THEN 파서B는 배열을 권위 있게 본다", "파서B")
    _absorb(dsn, host, "IF 배열은 존재하지만 비어 있다 THEN 파서C는 배열을 권위 있게 보지 않는다", "파서C")
    frags = {r["text"]: r for r in pg.rows(dsn, "fragment") if r["host_id"] == host}
    own = next(r for t, r in frags.items() if "파서C" in t)
    others = [r for t, r in frags.items() if "파서A" in t or "파서B" in t]
    monkeypatch.setattr(pg, "search", lambda *a, **k: [{"id": r["id"], "alias": r["alias"], "text": r["text"]} for r in others])
    calls = []

    def judge(state, texts, q, criteria=None):
        calls.append((q[:12], list(texts)))
        if criteria:
            return [{"probabilities": {"contradiction": 0.9 if "파서B" in t else 0.0, "exception": 0.0,
                                       "neither": 0.1 if "파서B" in t else 1.0}} for t in texts]
        if q.startswith(pg.COND_Q[:20]):
            return [{"noul": 0.9} for _ in texts]
        return [{"noul": 0.0} for _ in texts]
    found = pg._vector_contradictions(dsn, host, str(own["id"]), own["text"], set(), judge)
    cond_items = sum(len(ts) for q, ts in calls if q == pg.COND_Q[:12])
    scope_items = sum(len(ts) for q, ts in calls if q == pg.SCOPE3_Q[:12])
    assert cond_items == 1 and scope_items == 2
    assert [f["alias"] for f in found if f["kind"] == "compare"] == [next(r["alias"] for r in others if "파서B" in r["text"])]


def test_even_if_is_spelled_out_for_the_condition_question():
    """real01 r19: EVEN IF read as one more condition; the condition question shows 'regardless of'."""
    import fact_form
    f = fact_form.parse("IF 배열은 존재한다 EVEN IF 배열은 비어 있다 THEN 파서는 값을 권위 있게 본다")
    assert fact_form.condition_text(f, explain=True) == "IF 배열은 존재한다 (배열은 비어 있다 인지와 관계없이)"
    assert "EVEN IF" in fact_form.condition_text(f)


def test_a_broken_distribution_fails_and_an_unsure_recheck_keeps_the_pair():
    """astra choice review P1/P2: probabilities must cover the options and sum to 1; below CHOICE_KEEP a recheck keeps."""
    import pytest
    for bad in ({"contradiction": 0.9, "exception": 0.9, "neither": 0.0}, {"contradiction": 1.0},
                {"contradiction": 0.0, "exception": 0.0, "neither": 0.0}):
        with pytest.raises(ValueError, match="judge (choice|probabilit)"):
            pg._strict_choice({"probabilities": bad}, pg.SCOPE_CHOICES)
    unsure = lambda state, texts, q, criteria=None: [
        {"probabilities": {"contradiction": 0.4, "exception": 0.3, "neither": 0.3}} for _ in texts]
    contra, exc, left = pg._scoped(unsure, "a", [{"shown": "b"}], return_unsure=True)
    assert contra == [] and exc == [] and len(left) == 1
