"""User 2026-10-02: a plain fact is a default; a conditional opposite is an exception, both stand (not a user question).
Only a plain fact that says 'always' (무조건·항상·예외 없이·어떤 경우에도 …) contradicts it. An exception found by the scan is a
parent hint: write the default as 'X EXCEPT WHEN c'."""
import fact_form
import knowledge_cli
import store_pg as pg
from test_p13_answer_scope import _absorb
from test_store_pg import host  # noqa: F401 (fixture)


def test_relation():
    plain = fact_form.parse("수수료는 0원이다")
    always = fact_form.parse("무조건 수수료는 0원이다")
    rule = fact_form.parse("IF 당일 취소이다 THEN 수수료는 3000원이다")
    other_rule = fact_form.parse("IF 전날 취소이다 THEN 수수료는 1000원이다")
    assert fact_form.relation(plain, rule) == "exception" and fact_form.relation(rule, plain) == "exception"
    assert fact_form.relation(always, rule) == "compare"
    assert fact_form.relation(plain, fact_form.parse("수수료는 500원이다")) == "compare"
    assert fact_form.relation(rule, other_rule) is None
    for w in ("항상", "예외 없이", "어떤 경우에도", "언제나", "절대"):
        assert fact_form.explicit_always(fact_form.parse(f"수수료는 {w} 0원이다")), w
    assert not fact_form.explicit_always(fact_form.parse("관리자는 한도를 늘린다"))


def _judge(state, texts, q):
    if q.startswith("items[{i}] 와 state.fact 는 같은 대상"):  # EXC_Q
        return [{"noul": 0.9} for _ in texts]
    if q.startswith(pg.SCOPE_Q[:20]):  # a general default does not name the exception's case (real01 scope check)
        return [{"noul": 0.0} for _ in texts]
    return [{"noul": 0.9 if ("3000" in t) != ("3000" in state["fact"]) else 0.0} for t in texts]


def _kinds(dsn, host):
    return sorted(i.get("kind") for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"])


def test_default_and_exception_both_stand_with_a_parent_hint(dsn, host):
    _absorb(dsn, host, "범위 설명은 0자다")
    unit = _absorb(dsn, host, "IF 당일 취소이다 THEN 범위 설명은 3000자다")
    out = pg.scan_contradictions(dsn, unit, _judge)
    assert out["contradictions"] == 0
    assert _kinds(dsn, host) == ["exception_link"]
    [it] = knowledge_cli.review_cmd(dsn, {"host_id": host})["items"]
    assert it["for"] == "parent" and "EXCEPT WHEN" in it["review_reasons"][0]
    # the parent rewrites the default: the hint is withdrawn
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""update knowledge.fragment set revision=revision+1, text='범위 설명은 0자다 EXCEPT WHEN 당일 취소이다'
                       where host_id=%s and text='범위 설명은 0자다'""", (host,))
    assert _kinds(dsn, host) == []


def test_explicit_always_against_a_rule_is_a_contradiction(dsn, host):
    _absorb(dsn, host, "범위 설명은 무조건 0자다")
    unit = _absorb(dsn, host, "IF 당일 취소이다 THEN 범위 설명은 3000자다")
    assert pg.scan_contradictions(dsn, unit, _judge)["contradictions"] == 1
    [it] = [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "contradiction"]
    pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "reject", "아니야", "t", it["question_ids"])


def test_always_words_are_whole_words_and_not_denied():
    no = ["절대경로는 /tmp 이다", "관리자는 한도를 늘린다", "수수료가 항상 무료인 것은 아니다", "수수료는 반드시 0원인 건 아니다"]
    yes = ["수수료는 항시 0원이다", "수수료는 어떤 경우에나 0원이다", "수수료는 절대 환불되지 않는다"]
    for t in no:
        assert not fact_form.explicit_always(fact_form.parse(t)), t
    for t in yes:
        assert fact_form.explicit_always(fact_form.parse(t)), t


def test_exception_hint_is_one_per_pair_either_direction(dsn, host):
    _absorb(dsn, host, "범위 설명은 0자다")
    unit = _absorb(dsn, host, "IF 당일 취소이다 THEN 범위 설명은 3000자다")
    pg.scan_contradictions(dsn, unit, _judge)
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select q.entry_id, q.fact_index, q.reason from knowledge.confirmation_queue q join knowledge.ledger_entry e
                       on e.entry_id=q.entry_id where e.host_id=%s and q.rule_id='canon_exception' and q.status='pending'""", (host,))
        eid, idx, reason = cur.fetchone()
        r = __import__("json").loads(reason)
        assert not pg._add_exception(cur, host, eid, idx, r["with"], r["with_text"], r["alias"], r["text"])  # reverse direction
        assert not pg._add_exception(cur, host, eid, idx, r["alias"], r["text"], r["with"], r["with_text"])
    assert _kinds(dsn, host) == ["exception_link"]


def test_recheck_turns_an_always_contradiction_into_an_exception_when_always_is_removed(dsn, host):
    _absorb(dsn, host, "범위 설명은 무조건 0자다")
    unit = _absorb(dsn, host, "IF 당일 취소이다 THEN 범위 설명은 3000자다")
    pg.scan_contradictions(dsn, unit, _judge)
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # the 'always' is dropped: now a plain default
        cur.execute("""update knowledge.fragment set revision=revision+1, text='범위 설명은 0자다',
                       form='{"kind":"plain","then":["범위 설명은 0자다"]}'::jsonb
                       where host_id=%s and text='범위 설명은 무조건 0자다'""", (host,))
    out = pg.recheck_contradictions(dsn, _judge)
    assert out["resolved"] == 1
    assert _kinds(dsn, host) == ["exception_link"]


def test_old_exception_hint_is_replaced_for_new_texts(dsn, host):
    """astra exc review r2: a pending hint for older texts must not block the hint for the current texts."""
    _absorb(dsn, host, "범위 설명은 0자다")
    unit = _absorb(dsn, host, "IF 당일 취소이다 THEN 범위 설명은 3000자다")
    pg.scan_contradictions(dsn, unit, _judge)
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select q.entry_id, q.fact_index, q.reason from knowledge.confirmation_queue q join knowledge.ledger_entry e
                       on e.entry_id=q.entry_id where e.host_id=%s and q.rule_id='canon_exception' and q.status='pending'""", (host,))
        eid, idx, reason = cur.fetchone()
        r = __import__("json").loads(reason)
        assert pg._add_exception(cur, host, eid, idx, r["alias"], r["text"] + " 변경", r["with"], r["with_text"])
        cur.execute("""select count(*) from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
                       where e.host_id=%s and q.rule_id='canon_exception' and q.status='pending'""", (host,))
        assert cur.fetchone()[0] == 1


def test_recheck_gives_no_hint_when_the_values_now_agree(dsn, host):
    """astra exc review r2: 'always 0' rewritten as plain '3000' agrees with the rule: resolved, no EXCEPT WHEN hint."""
    _absorb(dsn, host, "범위 설명은 무조건 0자다")
    unit = _absorb(dsn, host, "IF 당일 취소이다 THEN 범위 설명은 3000자다")
    pg.scan_contradictions(dsn, unit, _judge)
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""update knowledge.fragment set revision=revision+1, text='범위 설명은 3000자다',
                       form='{"kind":"plain","then":["범위 설명은 3000자다"]}'::jsonb
                       where host_id=%s and text='범위 설명은 무조건 0자다'""", (host,))
    same_value = lambda state, texts, q: [{"noul": 0.0} for _ in texts]
    assert pg.recheck_contradictions(dsn, same_value)["resolved"] == 1
    assert _kinds(dsn, host) == []


def test_a_warned_leaf_is_compared_across_subjects(dsn, host):
    """astra warn review: '편집 창은 닫히지 않고 입력은 비워진다' (kept with a W_FORM warning) must still be compared with
    a fact about '입력', not only with facts of its own subject."""
    import digest_driver
    from test_store_pg import fixture, judgement

    def absorb(text, subject):
        body = judgement(host, text=text)
        body["facts"][0]["subject"] = subject
        e = pg.register(dsn, body)
        pg.batch(dsn, 1, {e["entry_id"]: [fixture(text=text)]}, entry_ids=[e["entry_id"]])
        pg.complete(dsn, body["work_unit_id"])
        digest_driver.run_digestion(dsn, body["work_unit_id"], lambda p: {"answers": fixture(text=p["state"]["candidate_fact"])["answers"]})
        return body["work_unit_id"]
    absorb("입력 칸은 비워지지 않는다", "입력 칸")
    unit = absorb("범위 설명은 닫히지 않고 입력 칸은 비워진다", "범위 설명")
    seen = []

    def judge(state, texts, q):
        seen.extend(texts)
        pair = state["fact"] + " | " + " ".join(texts)
        return [{"noul": 0.9 if ("비워지지" in t) != ("비워지지" in state["fact"]) else 0.0} for t in texts]
    assert pg.scan_contradictions(dsn, unit, judge)["contradictions"] == 1, seen
    # reverse order (astra warn review r2): the warned leaf is already canon, the plain fact comes later
    absorb("알림 창은 닫히지 않고 입력 상자는 비워지지 않는다", "알림 창")
    later = absorb("입력 상자는 비워진다", "입력 상자")
    seen.clear()
    assert pg.scan_contradictions(dsn, later, judge)["contradictions"] >= 1, seen
