"""astra direction review (2026-10-01): a duplicate is not a contradiction, so the user is never asked about it.
A user-confirmed add judged duplicate only by Jev is added; the code's exact match keeps it as evidence and the
absorption points at the surviving fragment ('already in canon as [alias@revision]'). Other evidence is still skipped."""
import copy

import dedup
import digest_driver
import fact_form
import knowledge_cli
import store_pg as pg
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixture)


def _dup(packet):
    answers = copy.deepcopy(fixture(text=packet["state"]["candidate_fact"])["answers"])
    answers["is_new"] = {"type": "noul", "noul": 0.02}
    return {"answers": answers}


def _new(packet):
    return {"answers": fixture(text=packet["state"]["candidate_fact"])["answers"]}


def _absorb(dsn, host, text, judge, source="user_confirmed", subject="중복 시험"):
    body = judgement(host, text=text, source=source)
    body["facts"][0]["subject"] = subject
    e = pg.register(dsn, body)
    pg.batch(dsn, 1, {e["entry_id"]: [fixture(text=text)]}, entry_ids=[e["entry_id"]])
    pg.complete(dsn, body["work_unit_id"])
    digest_driver.run_digestion(dsn, body["work_unit_id"], judge)
    return body["work_unit_id"]


def _active(dsn, host):
    return sorted(r["text"] for r in pg.rows(dsn, "fragment") if r["host_id"] == host and r["active"])


def _absorptions(dsn, unit):
    return [r for r in pg.rows(dsn, "absorption") if r["work_unit_id"] == unit]


def _no_review(dsn, host):
    return not knowledge_cli.review_cmd(dsn, {"host_id": host})["items"]


def test_user_confirmed_add_judged_duplicate_only_by_jev_is_added(dsn, host):
    _absorb(dsn, host, "중복 시험 사실은 하나다", _new)
    _absorb(dsn, host, "중복 시험 사실은 둘이다", _dup)
    assert _active(dsn, host) == ["중복 시험 사실은 둘이다", "중복 시험 사실은 하나다"]
    assert _no_review(dsn, host)


def test_exact_same_fact_is_kept_as_evidence_pointing_at_the_fragment(dsn, host):
    _absorb(dsn, host, "중복 시험 사실은 하나다", _new)
    unit = _absorb(dsn, host, "중복 시험 사실은 하나다.", _dup)
    assert _active(dsn, host) == ["중복 시험 사실은 하나다"]
    [a] = _absorptions(dsn, unit)
    frag = [r for r in pg.rows(dsn, "fragment") if r["host_id"] == host][0]
    assert a["decision"] == "retained_as_evidence" and str(a["fragment_ref"]) == str(frag["id"])
    assert a["fragment_revision_after"] == frag["revision"]
    assert _no_review(dsn, host)


def test_any_evidence_judged_duplicate_is_added_and_marked(dsn, host):
    """contra06 (2026-10-02, user 'a'): a judge's duplicate alone never drops an add, whatever the evidence; the
    fragment is marked possible_duplicate for cleanup. v1/v2 facts the worktime check closed silently are kept."""
    _absorb(dsn, host, "v1 리마인더 API는 재시도 횟수를 최대 1회로 제한한다", _new, source="code_test", subject="v1 리마인더 API")
    _absorb(dsn, host, "v2 리마인더 API는 재시도 횟수를 최대 3회로 제한한다", _dup, source="code_test", subject="v2 리마인더 API")
    assert "v2 리마인더 API는 재시도 횟수를 최대 3회로 제한한다" in _active(dsn, host)
    frag = [r for r in pg.rows(dsn, "fragment") if r["host_id"] == host and "v2" in r["text"]][0]
    assert frag["source"].get("possible_duplicate") is True
    assert _no_review(dsn, host)  # a duplicate is never a question to the user


def test_dedup_keeps_identifier_punctuation():
    assert not dedup.same_fact("`a.b`는 켜진다", "`ab`는 켜진다")
    assert not dedup.same_fact("domain_router.py는 자른다", "domain_routerpy는 자른다")
    assert not dedup.same_fact("값은 1.5다", "값은 15다")
    assert dedup.same_fact("`a.b`는 켜진다.", "`a.b` 는 켜진다")
    assert dedup.same_fact("생성·수정 모두 300자다", "생성 수정 모두 300자다.")


def test_conditional_or_result_is_rejected_and_never_flattened():
    t = "IF A가 있다 THEN B는 된다 OR C는 된다 EXCEPT WHEN D가 있다"
    assert fact_form.check(t)
    assert fact_form.parse(t)["then"] == ["B는 된다 OR C는 된다"] or len(fact_form.parse(t)["then"]) == 1
    ok = "IF A가 있다 THEN B는 된다 EXCEPT WHEN D가 있다 OR E가 있다"
    assert not fact_form.check(ok)  # OR inside the exception condition stays allowed


def test_worktime_duplicate_is_eligible_absorbed_and_marked(dsn, host):
    """astra dupA review: the worktime check saying duplicate no longer closes an add."""
    body = judgement(host, text="작업 중 중복 시험은 하나다", source="code_test")
    body["facts"][0]["subject"] = "작업 중 중복 시험"
    e = pg.register(dsn, body)
    dup = copy.deepcopy(fixture(text="작업 중 중복 시험은 하나다"))
    dup["answers"]["is_new"] = {"type": "noul", "noul": 0.02}
    pg.batch(dsn, 1, {e["entry_id"]: [dup]}, entry_ids=[e["entry_id"]])
    assert [r["state"] for r in pg.rows(dsn, "ledger_entry") if r["entry_id"] == e["entry_id"]] in (["eligible"], ["provisional"])
    pg.complete(dsn, body["work_unit_id"])
    digest_driver.run_digestion(dsn, body["work_unit_id"], _new)  # digestion says new; the worktime duplicate still marks
    frag = [r for r in pg.rows(dsn, "fragment") if r["host_id"] == host and r["text"] == "작업 중 중복 시험은 하나다"]
    assert frag and frag[0]["source"].get("possible_duplicate") is True


def test_reopen_skips_what_the_code_finds_in_canon():
    import reopen_duplicates
    rows = [("e1", 0, {"fact": "재처리 시험은 둘이다"}, "digestion P03"),
            ("e2", 0, {"fact": "재처리 시험은 하나다."}, "worktime duplicate")]
    got = {c["fact"]: c["in_canon_as"] for c in reopen_duplicates.classify(rows, [("k-1", "재처리 시험은 하나다")])}
    assert got == {"재처리 시험은 둘이다": None, "재처리 시험은 하나다.": "k-1"}


def test_reopen_query_runs(dsn, host):
    import reopen_duplicates
    assert reopen_duplicates.candidates(dsn, host) == []
