"""astra direction review P1 (2026-10-01): a contradiction answer closes only the questions shown; a short judge answer
fails the scan instead of marking the fragment scanned."""
import pytest

import digest_driver
import knowledge_cli
import store_pg as pg
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixture)


def _absorb(dsn, host, text):
    body = judgement(host, text=text)
    body["facts"][0]["subject"] = "범위 설명"
    e = pg.register(dsn, body)
    pg.batch(dsn, 1, {e["entry_id"]: [fixture(text=text)]}, entry_ids=[e["entry_id"]])
    pg.complete(dsn, body["work_unit_id"])
    digest_driver.run_digestion(dsn, body["work_unit_id"], lambda p: {"answers": fixture(text=p["state"]["candidate_fact"])["answers"]})
    return body["work_unit_id"]


def _contra(state, texts, q):
    return [{"noul": 0.9 if ("300" in t or "500" in t or "700" in t) and "1000" in state["fact"] else 0.0} for t in texts]


def _items(dsn, host):
    return [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "contradiction"]


def test_answer_closes_only_the_questions_shown(dsn, host):
    _absorb(dsn, host, "범위 설명은 300자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    pg.scan_contradictions(dsn, unit, _contra)
    [shown] = _items(dsn, host)
    assert len(shown["question_ids"]) == 1
    # a new contradiction of the same fragment is found after the user was asked
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason,resolution)
                       select entry_id,fact_index,rule_id, jsonb_set(reason::jsonb,'{with}','"late"')::text, 'open'
                       from knowledge.confirmation_queue where confirmation_id=%s""", (shown["question_ids"][0],))
    with pytest.raises(ValueError):  # no ids: the answer is not bound to what was shown
        pg.review_resolve(dsn, host, shown["entry_id"], shown["fact_index"], "approve", "1000이 맞아", "t")
    pg.review_resolve(dsn, host, shown["entry_id"], shown["fact_index"], "approve", "1000이 맞아", "t", shown["question_ids"])
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select count(*) from knowledge.confirmation_queue where entry_id=%s and fact_index=%s
                       and rule_id='canon_contradiction' and status='pending'""", (shown["entry_id"], shown["fact_index"]))
        assert cur.fetchone()[0] == 1  # the late one is still asked
        cur.execute("""update knowledge.confirmation_queue set status='answered', resolution='resolved', resolved_at=now(),
                       resolution_evidence='{"by":"test"}' where entry_id=%s and rule_id='canon_contradiction'""",
                    (shown["entry_id"],))  # leave the shared DB clean


def test_stale_question_ids_are_refused(dsn, host):
    _absorb(dsn, host, "범위 설명은 700자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    pg.scan_contradictions(dsn, unit, _contra)
    [shown] = _items(dsn, host)
    with pytest.raises(ValueError):
        pg.review_resolve(dsn, host, shown["entry_id"], shown["fact_index"], "approve", "1000이 맞아", "t",
                          shown["question_ids"] + [10 ** 9])
    pg.review_resolve(dsn, host, shown["entry_id"], shown["fact_index"], "reject", "아니야", "t", shown["question_ids"])


def test_short_judge_answer_fails_the_scan_and_leaves_it_unscanned(dsn, host):
    _absorb(dsn, host, "범위 설명은 500자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    with pytest.raises(ValueError):
        pg.scan_contradictions(dsn, unit, lambda state, texts, q: [])
    assert unit in pg.units_to_scan(dsn, limit=500)  # retried later, not marked scanned
    pg.scan_contradictions(dsn, unit, lambda state, texts, q: [{"noul": 0.0} for _ in texts])


def test_question_ids_never_fall_through_to_another_review(dsn, host):
    """astra P13 cross-review P1-1: ids whose questions were all auto-closed must be refused, not used as another answer."""
    _absorb(dsn, host, "범위 설명은 300자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    pg.scan_contradictions(dsn, unit, _contra)
    [shown] = _items(dsn, host)
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # closed after listing (e.g. one side changed)
        cur.execute("update knowledge.confirmation_queue set status='answered' where confirmation_id = any(%s)", (shown["question_ids"],))
    with pytest.raises(ValueError):
        pg.review_resolve(dsn, host, shown["entry_id"], shown["fact_index"], "approve", "1000이 맞아", "t", shown["question_ids"])
    with pytest.raises(ValueError):
        pg.review_resolve(dsn, host, shown["entry_id"], shown["fact_index"], "approve", "1000이 맞아", "t", [])


def test_one_question_per_other_fragment(dsn, host):
    """P2: several leaves naming the same other fragment insert one question."""
    _absorb(dsn, host, "범위 설명은 500자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다 AND 범위 설명은 1000자로 저장된다")
    pg.scan_contradictions(dsn, unit, _contra)
    [shown] = _items(dsn, host)
    assert len(shown["question_ids"]) == 1, shown
    pg.review_resolve(dsn, host, shown["entry_id"], shown["fact_index"], "reject", "아니야", "t", shown["question_ids"])


def test_units_to_scan_is_fifo_and_pages(dsn, host):
    a = _absorb(dsn, host, "범위 설명은 페이지 일다")
    b = _absorb(dsn, host, "범위 설명은 페이지 이다")
    rows = pg.units_to_scan(dsn, limit=500, with_key=True)
    order = [u for u, _ in rows]
    assert order.index(a) < order.index(b)  # older absorption first, whatever the uuids
    keys = [k for _, k in rows]
    assert keys == sorted(keys)
    assert pg.units_to_scan(dsn, limit=500, after=keys[0]) == order[1:]
    assert pg.unscanned(dsn, [a, b, "00000000-0000-0000-0000-000000000000"]) == {a, b}
    for u in (a, b):
        pg.scan_contradictions(dsn, u, lambda state, texts, q: [{"noul": 0.0} for _ in texts])
    assert pg.unscanned(dsn, [a, b]) == set()


def test_pending_in_entry_counts_every_question_of_the_entry(dsn, host):
    _absorb(dsn, host, "범위 설명은 300자다")
    unit = _absorb(dsn, host, "범위 설명은 1000자다")
    pg.scan_contradictions(dsn, unit, _contra)
    [shown] = _items(dsn, host)
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # another question on another fact of the same entry
        cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason)
                       values (%s, %s, 'digest_recheck', '{}')""", (shown["entry_id"], shown["fact_index"] + 7))
    out = pg.review_resolve(dsn, host, shown["entry_id"], shown["fact_index"], "reject", "아니야", "t", shown["question_ids"])
    assert out["pending_in_entry"] == 1
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.confirmation_queue set status='answered' where entry_id=%s", (shown["entry_id"],))
