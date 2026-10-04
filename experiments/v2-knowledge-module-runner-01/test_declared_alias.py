"""Stage 1 of resolving aliases in the subject dictionary (2026-10-03): a parent declares other names of the same thing
(aliases); digestion registers them as declared aliases of the fact's subject; a later fact written under an alias keeps
its text but gets the same subject id, so the same-subject scan compares them. A name already mapped to another subject is
a conflict for approval (never merged in stage 1)."""
import pytest

import digest_driver
import knowledge_cli
import store_pg as pg
import subject_dict
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixture)


def _absorb(dsn, host, text, subject, aliases=None):
    body = judgement(host, text=text)
    body["facts"][0]["subject"] = subject
    if aliases is not None:
        body["facts"][0]["aliases"] = aliases
    e = pg.register(dsn, body)
    pg.batch(dsn, 1, {e["entry_id"]: [fixture(text=text)]}, entry_ids=[e["entry_id"]])
    pg.complete(dsn, body["work_unit_id"])
    digest_driver.run_digestion(dsn, body["work_unit_id"], lambda p: {"answers": fixture(text=p["state"]["candidate_fact"])["answers"]})
    return body["work_unit_id"]


def _frag(dsn, host, text):
    return [r for r in pg.rows(dsn, "fragment") if r["host_id"] == host and r["text"] == text][0]


def test_declared_alias_gives_the_same_subject_and_keeps_the_text(dsn, host):
    _absorb(dsn, host, "출고API는 정상 접수 응답 코드가 202다", "출고API", aliases=["POST /v3/shipments"])
    later = _absorb(dsn, host, "POST /v3/shipments는 정상 접수 응답 코드가 200이다", "POST /v3/shipments")
    a = _frag(dsn, host, "출고API는 정상 접수 응답 코드가 202다")
    b = _frag(dsn, host, "POST /v3/shipments는 정상 접수 응답 코드가 200이다")  # text not rewritten
    assert a["subject_id"] == b["subject_id"]
    judge = lambda state, texts, q: [{"noul": 0.9 if ("202" in t) != ("202" in state["fact"]) else 0.0} for t in texts]
    assert pg.scan_contradictions(dsn, later, judge)["contradictions"] >= 1  # the plain same-subject scan finds it


def test_alias_already_another_subject_is_a_conflict_not_a_merge(dsn, host):
    _absorb(dsn, host, "회수접수는 우편번호를 선택 항목으로 둔다", "회수접수")
    _absorb(dsn, host, "반품API는 우편번호를 필수로 요구한다", "반품API", aliases=["회수접수"])
    a = _frag(dsn, host, "회수접수는 우편번호를 선택 항목으로 둔다")
    b = _frag(dsn, host, "반품API는 우편번호를 필수로 요구한다")
    assert a["subject_id"] != b["subject_id"]  # never merged in stage 1
    items = [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "alias_conflict"]
    # stage 2: the user is asked (no longer a parent-only hint); the question names both subjects
    assert len(items) == 1 and items[0].get("for") != "parent" and "회수접수" in items[0]["fact"]


def test_record_validates_aliases(dsn, host):
    def rec(aliases):
        body = judgement(host, text="검사 API는 켜진다")
        body["facts"][0]["subject"] = "검사 API"
        body["facts"][0]["aliases"] = aliases
        return knowledge_cli.record(dsn, {k: v for k, v in body.items() if k != "judgement_id"})
    for bad in ("x", [""], ["검사 API"], ["a", "A"], [1]):
        out = rec(bad)
        assert out.get("ok") is False and "E_ALIASES" in [e["code"] for e in out["errors"]], (bad, out)


def test_declared_alias_keeps_its_source(dsn, host):
    _absorb(dsn, host, "주문API는 요청 본문 형식이 JSON이다", "주문API", aliases=["POST /v3/orders"])
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select kind, source_fragment_id is not null, source_revision from knowledge.subject_alias
                       where host_id=%s and alias=%s""", (host, subject_dict.norm("POST /v3/orders")))
        assert cur.fetchone() == ("declared", True, 1)


def test_declared_alias_matches_its_exact_spelling_only(dsn, host):
    """astra alias r1: declaring 'X' must not make 'X 화면' the same subject."""
    _absorb(dsn, host, "재고API는 수량을 정수로 반환한다", "재고API", aliases=["재고조회"])
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        assert subject_dict.lookup(cur, host, "재고조회")["kind"] == "declared"
        assert subject_dict.lookup(cur, host, "재고조회 화면") is None


def test_a_leaf_written_under_the_alias_in_the_same_fact_gets_the_subject(dsn, host):
    """astra alias r1: aliases are registered before the leaves, so an alias leaf is not a separate new subject."""
    _absorb(dsn, host, "배송API는 인증을 요구한다 AND POST /v3/deliveries는 JSON을 받는다", "배송API",
            aliases=["POST /v3/deliveries"])
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select distinct l.subject_id::text from knowledge.fragment_leaf l join knowledge.fragment f
                       on f.id=l.fragment_id where f.host_id=%s and f.text like '배송API%%'""", (host,))
        assert len(cur.fetchall()) == 1
    assert not [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "alias_conflict"]


def test_changed_evidence_asks_to_recheck_the_alias(dsn, host):
    _absorb(dsn, host, "결제API는 카드 결제를 지원한다", "결제API", aliases=["POST /v3/payments"])
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""update knowledge.fragment set revision=revision+1, active=false
                       where host_id=%s and text='결제API는 카드 결제를 지원한다'""", (host,))
    items = [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "alias_recheck"]
    assert len(items) == 1 and "폐기" in items[0]["review_reasons"][0]


def test_record_time_contradiction_sees_the_alias(dsn, host):
    """astra alias r1: within one work unit, a fact under the alias is compared with a fact under the subject."""
    _absorb(dsn, host, "요금API는 통화가 원화다", "요금API", aliases=["GET /v3/fees"])
    import fact_form
    unit = __import__("uuid").uuid4().hex
    first = {"fact": "요금API는 반올림 단위가 10원이다", "subject": "요금API"}
    first["form"] = fact_form.parse(first["fact"])
    body = judgement(host, text=first["fact"])
    body["facts"][0].update(first)
    body["work_unit_id"] = str(__import__("uuid").UUID(unit))
    entry = pg.register(dsn, body)
    new = {"fact": "GET /v3/fees는 반올림 단위가 100원이다", "subject": "GET /v3/fees"}
    new["form"] = fact_form.parse(new["fact"])
    judge = lambda state, texts, q: [{"noul": 0.9 if "10원" in t else 0.0} for t in texts]
    out = knowledge_cli.contradictions(dsn, host, body["work_unit_id"], [new], {}, judge=judge)
    # leave nothing proposed in the shared test DB (other tests batch the oldest proposed entries)
    pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text=first["fact"])]}, entry_ids=[entry["entry_id"]])
    assert out, out


def test_routed_subject_yields_to_a_declared_alias_made_meanwhile(dsn, host):
    """astra alias r2: a routing decided before the commit (name -> C) must not win over 'name' declared an alias of A."""
    _absorb(dsn, host, "출고API는 응답 코드가 202다", "출고API", aliases=["POST /v3/out"])
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        a = subject_dict.lookup(cur, host, "출고API")["subject_id"]
        c = subject_dict.register(cur, host, "다른 대상", allow_embed=False)
        fact = {"fact": "POST /v3/out는 응답 코드가 200이다", "subject": "POST /v3/out"}
        sid, out = pg._assign_subject(cur, host, fact, {"subject_routed": {"subject_id": c, "name": "다른 대상"}})
        assert sid == a and out["fact"] == fact["fact"]  # the dictionary wins; the text is not rewritten to C


def test_spelling_and_tail_variant_share_one_subject_under_concurrency(dsn, host):
    """astra alias r3: 'X' and 'X 화면' write the same core key 'x'; registered concurrently they must end as one subject."""
    import threading
    out = {}

    def reg(name):
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            out[name] = subject_dict.register(cur, host, name, allow_embed=False)
    ts = [threading.Thread(target=reg, args=(n,)) for n in ("동시 대상", "동시 대상 화면")]
    [t.start() for t in ts]; [t.join() for t in ts]
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        a = subject_dict.lookup(cur, host, "동시 대상")["subject_id"]
        b = subject_dict.lookup(cur, host, "동시 대상 화면")["subject_id"]
    assert a == b == out["동시 대상"] == out["동시 대상 화면"]


def test_the_judge_is_told_the_names_of_one_subject(dsn, host):
    """real01: 'printer.ts' vs 'src/main/ipc/printer.ts' were one subject but judged as different things (0.14)."""
    _absorb(dsn, host, "printer.ts는 여백 상수를 0으로 유지한다", "printer.ts", aliases=["src/main/ipc/printer.ts"])
    later = _absorb(dsn, host, "src/main/ipc/printer.ts는 여백 상수를 5로 사용한다", "src/main/ipc/printer.ts")
    seen = []

    def judge(state, texts, q):
        seen.append((state, q))
        return [{"noul": 0.0} for _ in texts]
    pg.scan_contradictions(dsn, later, judge)
    names = [s.get("same_subject_names") for s, _ in seen if s.get("same_subject_names")]
    assert names and "printer.ts" in names[0] and subject_dict.norm("src/main/ipc/printer.ts") in names[0]
    assert all("same_subject_names" in q for s, q in seen if s.get("same_subject_names"))


def test_the_recheck_keeps_the_alias_context(dsn, host):
    """astra names review P1: a contradiction found with the names must not be resolved by a recheck without them."""
    _absorb(dsn, host, "printer.ts는 여백 상수를 0으로 유지한다", "printer.ts", aliases=["src/main/ipc/printer.ts"])
    later = _absorb(dsn, host, "src/main/ipc/printer.ts는 여백 상수를 5로 사용한다", "src/main/ipc/printer.ts")
    # a judge that sees a contradiction only when told the names are one thing
    judge = lambda state, texts, q: [{"noul": 0.9 if state.get("same_subject_names") else 0.1} for _ in texts]
    assert pg.scan_contradictions(dsn, later, judge)["contradictions"] >= 1
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""update knowledge.confirmation_queue set resolution='recheck' where rule_id='canon_contradiction'
                       and entry_id in (select entry_id from knowledge.ledger_entry where host_id=%s)""", (host,))
    out = pg.recheck_contradictions(dsn, judge, limit=50)
    assert out["rechecked"] > 0 and out["resolved"] == 0 and out["failed"] == 0 and out["retried"] == 0, out
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select count(*) from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
                       where e.host_id=%s and q.rule_id='canon_contradiction' and q.resolution='open'""", (host,))
        assert cur.fetchone()[0] >= 1  # still an open contradiction


def test_names_are_picked_per_call_within_the_bounds():
    """astra names review r2 P2: the names written in this call's texts survive a long alias list."""
    names = ["printer.ts"] + [f"alias-{k:02d}-" + "x" * 40 for k in range(20)] + ["src/main/ipc/printer.ts"]
    picked = pg._pick_names(names, ["src/main/ipc/printer.ts는 여백 상수를 5로 사용한다"])
    assert "printer.ts" in picked and "src/main/ipc/printer.ts" in picked
    assert len(picked) <= pg.SAME_NAMES_MAX and sum(map(len, picked)) <= pg.SAME_NAMES_CHARS
    long_head = ["가" * 500, "printer.ts"]  # an over-long subject name never breaks the bound
    assert pg._pick_names(long_head, ["printer.ts는 켜진다"]) == ["printer.ts"]
    assert pg._written(["late.ts"], ["가" * 700 + " late.ts는 켜진다"]) == []  # past the judge's cut: not counted
    many = ["p.ts"] + [f"n{k}" for k in range(12)]  # names written in the text are never dropped, even past the bound
    text = " ".join(f"n{k}는 켜진다" for k in range(12))
    assert set(pg._written(many, [text])) <= set(pg._pick_names(many, [text]))


def test_the_wrapper_splits_a_call_so_every_text_keeps_its_names():
    """astra names review r3 P2: eight texts each written under a different alias -> every call carries its names."""
    names = ["printer.ts"] + [f"src/p{k}/printer-{k:02d}.ts" for k in range(12)]
    texts = [f"src/p{k}/printer-{k:02d}.ts는 여백 상수를 {k}로 쓴다" for k in range(12)]
    calls = []

    def judge(state, ts, q):
        calls.append((state.get("same_subject_names") or [], ts))
        return [{"noul": 0.0} for _ in ts]
    out = pg._names_judge(judge, names)({"fact": "printer.ts는 여백 상수를 0으로 쓴다"}, texts, pg.CANON_Q)
    assert len(out) == len(texts)
    # answers stay with their texts across the split (each answer names its text)
    tagged = pg._names_judge(lambda st, ts, q: [{"noul": 0.0, "t": t} for t in ts], names)(
        {"fact": "printer.ts는 여백 상수를 0으로 쓴다"}, texts, pg.CANON_Q)
    assert [a["t"] for a in tagged] == texts
    # a call that answers the wrong number of texts is refused, never offset by another call
    bad = iter([1, 3, 1, 3, 1, 3, 1, 3])
    with pytest.raises(ValueError, match="number of answers"):
        pg._names_judge(lambda st, ts, q: [{"noul": 0.0}] * next(bad), names)(
            {"fact": "printer.ts는 여백 상수를 0으로 쓴다"}, texts, pg.CANON_Q)
    for picked, ts in calls:
        assert all(n in picked for n in pg._written(names, ts))
        assert len(picked) <= pg.SAME_NAMES_MAX and sum(map(len, picked)) <= pg.SAME_NAMES_CHARS
