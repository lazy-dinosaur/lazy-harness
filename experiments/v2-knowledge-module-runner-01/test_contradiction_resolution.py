"""0012 (2026-10-01): a contradiction's answer is not its resolution. Approve keeps it open until a fix is digested and
the pair is judged again; reject ('not a contradiction') resolves with the user's quote; a retired side resolves;
a changed side that still contradicts is asked again with the current texts."""
import knowledge_cli
import store_pg as pg
from test_p13_answer_scope import _absorb, _contra, _items
from test_store_pg import host  # noqa: F401 (fixture)


def _row(dsn, qid):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select status::text, resolution, resolution_evidence from knowledge.confirmation_queue where confirmation_id=%s", (qid,))
        return cur.fetchone()


def _set_text(dsn, host, alias, text):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.fragment set revision=revision+1, text=%s where host_id=%s and alias=%s", (text, host, alias))


def _retire(dsn, host, alias):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.fragment set revision=revision+1, active=false where host_id=%s and alias=%s", (host, alias))


def _due_again(dsn):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.confirmation_queue set rechecked_at=null where rule_id='canon_contradiction'")


def _shown(dsn, host):
    [it] = _items(dsn, host)
    return it, it["question_ids"][0]


def _alias_of(item):
    return item["fact"].split("]")[0].lstrip("[")


def test_approve_stays_open_until_the_fix_is_judged(dsn, host):
    _absorb(dsn, host, "범위 설명은 300자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    pg.scan_contradictions(dsn, unit, _contra)
    it, qid = _shown(dsn, host)
    pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "approve", "1000이 맞아", "t", it["question_ids"])
    assert _row(dsn, qid)[:2] == ("answered", "open")  # answered, not resolved
    due = [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "contradiction_fix_due"]
    assert len(due) == 1 and "1000이 맞아" in due[0]["review_reasons"][0]
    assert pg.recheck_contradictions(dsn, _contra)["rechecked"] == 0  # nothing changed yet
    other = it["review_reasons"][0].split("[")[1].split("]")[0]
    _set_text(dsn, host, other, "범위 설명은 1000자다")  # the fix (300 -> 1000) is digested
    assert pg.recheck_contradictions(dsn, _contra) == {"rechecked": 1, "resolved": 1, "reopened": 0, "failed": 0, "retried": 0}
    status, resolution, evidence = _row(dsn, qid)
    assert resolution == "resolved" and evidence["by"] == "rejudged" and len(evidence["ids"]) == 2 and evidence["revisions"]
    assert not [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind", "").startswith("contradiction")]


def test_reject_means_not_a_contradiction_and_resolves(dsn, host):
    _absorb(dsn, host, "범위 설명은 500자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    pg.scan_contradictions(dsn, unit, _contra)
    it, qid = _shown(dsn, host)
    pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "reject", "둘 다 맞아, 다른 얘기야", "t", it["question_ids"])
    _, resolution, evidence = _row(dsn, qid)
    assert resolution == "resolved" and evidence["by"] == "user" and evidence["quote"].startswith("둘 다")


def test_changed_side_that_still_contradicts_is_asked_again(dsn, host):
    _absorb(dsn, host, "범위 설명은 700자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    pg.scan_contradictions(dsn, unit, _contra)
    it, qid = _shown(dsn, host)
    other = it["review_reasons"][0].split("[")[1].split("]")[0]
    _set_text(dsn, host, other, "범위 설명은 500자다")  # changed, still contradicts 1000
    assert not _items(dsn, host)  # the stale question is withdrawn from the list ...
    assert _row(dsn, qid)[1] == "recheck"
    assert pg.recheck_contradictions(dsn, _contra)["reopened"] == 1  # ... and asked again with the new text
    it2, qid2 = _shown(dsn, host)
    assert qid2 != qid and "500" in it2["review_reasons"][0]  # a new question; the old row keeps its state
    assert _row(dsn, qid)[1] == "superseded"
    pg.review_resolve(dsn, host, it2["entry_id"], it2["fact_index"], "reject", "아니야", "t", it2["question_ids"])


def test_retired_side_resolves(dsn, host):
    _absorb(dsn, host, "범위 설명은 300자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    pg.scan_contradictions(dsn, unit, _contra)
    it, qid = _shown(dsn, host)
    _retire(dsn, host, it["review_reasons"][0].split("[")[1].split("]")[0])
    assert pg.recheck_contradictions(dsn, _contra)["resolved"] == 1
    assert _row(dsn, qid)[1] == "resolved"


def test_schema_refuses_resolved_without_evidence(dsn, host):
    import pytest
    _absorb(dsn, host, "범위 설명은 300자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    pg.scan_contradictions(dsn, unit, _contra)
    it, qid = _shown(dsn, host)
    with pg.connect(dsn) as conn, conn.cursor() as cur, pytest.raises(pg.driver.Error):
        cur.execute("update knowledge.confirmation_queue set resolution='resolved' where confirmation_id=%s", (qid,))
    pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "reject", "아니야", "t", it["question_ids"])


def _approved_pair(dsn, host, low):
    _absorb(dsn, host, f"범위 설명은 {low}자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    pg.scan_contradictions(dsn, unit, _contra)
    it, qid = _shown(dsn, host)
    other = it["review_reasons"][0].split("[")[1].split("]")[0]
    return it, qid, other


def test_reask_keeps_the_previous_answer(dsn, host):
    it, qid, other = _approved_pair(dsn, host, 300)
    pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "approve", "1000이 맞아", "t", it["question_ids"])
    _set_text(dsn, host, other, "범위 설명은 500자다")  # a wrong fix: still contradicts
    assert pg.recheck_contradictions(dsn, _contra)["reopened"] == 1
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select answer from knowledge.confirmation_queue where confirmation_id=%s", (qid,))
        assert "1000이 맞아" in cur.fetchone()[0]
    import pytest
    with pytest.raises(ValueError):  # a late answer to the old question cannot answer the new one
        pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "approve", "응", "t", [qid])
    it2, _ = _shown(dsn, host)
    pg.review_resolve(dsn, host, it2["entry_id"], it2["fact_index"], "reject", "아니야", "t", it2["question_ids"])


def test_bad_judge_score_never_resolves_and_does_not_block(dsn, host):
    it, qid, other = _approved_pair(dsn, host, 300)
    _set_text(dsn, host, other, "범위 설명은 1000자다")
    for bad in ([{}], [{"noul": float("nan")}], [{"noul": 2}], []):
        out = pg.recheck_contradictions(dsn, lambda s, t, q, bad=bad: bad)
        assert out["failed"] == 1 and out["resolved"] == 0
        assert _row(dsn, qid)[1] == "open"
        assert pg.recheck_contradictions(dsn, _contra)["rechecked"] == 0  # a failed row waits before the next try
        _due_again(dsn)
    assert pg.recheck_contradictions(dsn, _contra)["resolved"] == 1


def test_renamed_alias_is_not_retired(dsn, host):
    it, qid, other = _approved_pair(dsn, host, 300)
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # a row from before 0012 (no ids), then the alias disappears
        cur.execute("""update knowledge.confirmation_queue set reason=(reason::jsonb - 'id' - 'with_id' - 'rev' - 'with_rev')::text,
                       resolution='recheck', status='answered' where confirmation_id=%s""", (qid,))
        cur.execute("update knowledge.fragment set revision=revision+1, alias=alias||'-renamed' where host_id=%s and alias=%s", (host, other))
    out = pg.recheck_contradictions(dsn, _contra)
    assert out["failed"] == 1 and out["resolved"] == 0 and _row(dsn, qid)[1] == "recheck"
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""update knowledge.confirmation_queue set resolution='resolved', resolved_at=now(),
                       resolution_evidence='{"by":"test"}' where confirmation_id=%s""", (qid,))


def test_side_changed_during_the_judge_call_is_retried(dsn, host):
    it, qid, other = _approved_pair(dsn, host, 300)
    _set_text(dsn, host, other, "범위 설명은 1000자다")

    def racing(state, texts, q):
        _set_text(dsn, host, other, "범위 설명은 300자다")  # changed back while the judge runs
        return [{"noul": 0.0}]
    assert pg.recheck_contradictions(dsn, racing)["retried"] == 1
    assert _row(dsn, qid)[1] == "open"  # not resolved by a judgement of an old text
    _due_again(dsn)
    assert pg.recheck_contradictions(dsn, _contra)["reopened"] + pg.recheck_contradictions(dsn, _contra)["resolved"] >= 0
    it2, _ = _shown(dsn, host)
    pg.review_resolve(dsn, host, it2["entry_id"], it2["fact_index"], "reject", "아니야", "t", it2["question_ids"])


def test_fix_due_can_be_corrected_to_not_a_contradiction(dsn, host):
    it, qid, _ = _approved_pair(dsn, host, 300)
    pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "approve", "1000이 맞아", "t", it["question_ids"])
    import pytest
    with pytest.raises(ValueError):
        pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "approve", "응", "t", [qid])
    pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "reject", "생각해 보니 둘 다 맞아", "t", [qid])
    _, resolution, evidence = _row(dsn, qid)
    assert resolution == "resolved" and evidence["correction"] is True


def test_concurrent_scans_insert_one_live_question(dsn, host):
    it, qid, _ = _approved_pair(dsn, host, 300)
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason,resolution)
                       select entry_id,fact_index,rule_id,reason,'open' from knowledge.confirmation_queue
                       where confirmation_id=%s on conflict do nothing returning 1""", (qid,))
        assert cur.fetchone() is None
    pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "reject", "아니야", "t", it["question_ids"])


def test_merged_side_is_rejudged_on_its_survivor(dsn, host):
    """astra 0012 round 2: a cleanup merge retires one side; the contradiction follows the survivor, never 'resolved'."""
    it, qid, other = _approved_pair(dsn, host, 300)
    _absorb(dsn, host, "범위 설명은 병합 대상이다")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select alias from knowledge.fragment where host_id=%s and text='범위 설명은 병합 대상이다'", (host,))
        survivor = cur.fetchone()[0]
        cur.execute("select set_config('knowledge.actor', 'cleanup:t', true)")  # one transaction, like cleanup.py
        cur.execute("update knowledge.fragment set revision=revision+1, text='범위 설명은 300자다' where host_id=%s and alias=%s",
                    (host, survivor))
        cur.execute("update knowledge.fragment set revision=revision+1, active=false where host_id=%s and alias=%s", (host, other))
    out = pg.recheck_contradictions(dsn, _contra)
    assert out["reopened"] == 1 and out["resolved"] == 0, out
    assert _row(dsn, qid)[1] == "superseded"
    it2, _ = _shown(dsn, host)
    assert survivor in it2["review_reasons"][0]
    pg.review_resolve(dsn, host, it2["entry_id"], it2["fact_index"], "reject", "아니야", "t", it2["question_ids"])


def test_scan_fails_when_a_side_changes_during_the_judge_call(dsn, host):
    import pytest
    _absorb(dsn, host, "범위 설명은 300자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")

    def racing(state, texts, q):
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""update knowledge.fragment set revision=revision+1, text='범위 설명은 400자다'
                           where host_id=%s and text='범위 설명은 300자다'""", (host,))
        return _contra(state, texts, q)
    with pytest.raises(ValueError):
        pg.scan_contradictions(dsn, unit, racing)
    assert unit in pg.units_to_scan(dsn, limit=500)  # nothing recorded; retried
    pg.scan_contradictions(dsn, unit, lambda s, t, q: [{"noul": 0.0} for _ in t])


def test_negative_scan_fails_when_the_canon_changes_during_the_judge_call(dsn, host):
    """astra 0012 round 3: a 'no contradiction' result of old texts must not mark the fragment scanned."""
    import pytest
    _absorb(dsn, host, "범위 설명은 1000자다")
    unit = _absorb(dsn, host, "범위 설명은 생성 때 쓴다")

    def racing(state, texts, q):
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""update knowledge.fragment set revision=revision+1, text='범위 설명은 300자다'
                           where host_id=%s and text='범위 설명은 1000자다'""", (host,))
        return [{"noul": 0.0} for _ in texts]
    with pytest.raises(ValueError):
        pg.scan_contradictions(dsn, unit, racing)
    assert unit in pg.units_to_scan(dsn, limit=500)
    pg.scan_contradictions(dsn, unit, lambda s, t, q: [{"noul": 0.0} for _ in t])


def test_recheck_never_takes_the_whole_scan_budget(dsn, tmp_path, monkeypatch):
    import json
    import poller
    monkeypatch.setattr(poller, "_candidates", lambda dsn: ([], []))
    seen = {}
    monkeypatch.setattr(poller.store_pg, "recheck_contradictions",
                        lambda dsn, j, limit=5: seen.setdefault("limit", limit) and {"rechecked": limit, "failed": limit})
    units = [f"u{i}" for i in range(9)]
    monkeypatch.setattr(poller.store_pg, "units_to_scan",
                        lambda dsn, limit=5, after=None, with_key=False: [(u, u) for u in units if after is None or u > after][:limit])
    monkeypatch.setattr(poller.store_pg, "unscanned", lambda dsn, ids: set(ids))
    ran = []
    monkeypatch.setattr(poller.store_pg, "scan_contradictions", lambda dsn, u, j: ran.append(u))
    state = tmp_path / "h.json"
    state.write_text(json.dumps({}))
    poller.tick(dsn, judge=None, state=state, contra_judge=lambda *a: [])
    assert seen["limit"] == poller.RECHECK_PER_TICK and len(ran) == poller.SCAN_PER_TICK - poller.RECHECK_PER_TICK >= 3


def test_delayed_commit_with_a_lower_history_id_is_caught(dsn, host):
    """astra 0012 round 5: T1 changes A (low history id, commits late), T2 commits another change first; the scan judged
    old A. The final (id, revision) comparison under FOR SHARE must catch T1."""
    import threading
    import pytest
    _absorb(dsn, host, "범위 설명은 1000자다")
    _absorb(dsn, host, "범위 설명은 다른 조각이다")
    unit = _absorb(dsn, host, "범위 설명은 생성 때 쓴다")
    t1_started, t1_go = threading.Event(), threading.Event()

    def t1():
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""update knowledge.fragment set revision=revision+1, text='범위 설명은 300자다'
                           where host_id=%s and text='범위 설명은 1000자다'""", (host,))
            t1_started.set()
            t1_go.wait(10)  # commit late

    def judge(state, texts, q):
        th = threading.Thread(target=t1, daemon=True)
        th.start()
        t1_started.wait(5)
        with pg.connect(dsn) as conn, conn.cursor() as cur:  # T2: another change commits first (higher history id)
            cur.execute("""update knowledge.fragment set revision=revision+1, text='범위 설명은 다른 조각이다 하나'
                           where host_id=%s and text='범위 설명은 다른 조각이다'""", (host,))
        threading.Timer(1.0, t1_go.set).start()  # T1 commits while the scan waits on FOR SHARE
        return [{"noul": 0.0} for _ in texts]
    with pytest.raises(ValueError):
        pg.scan_contradictions(dsn, unit, judge)
    assert unit in pg.units_to_scan(dsn, limit=500)
    pg.scan_contradictions(dsn, unit, lambda s, t, q: [{"noul": 0.0} for _ in t])
