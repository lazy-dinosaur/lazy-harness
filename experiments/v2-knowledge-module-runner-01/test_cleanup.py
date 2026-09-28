"""G4 clean-up by merge-update: both guards must pass; otherwise both fragments stay. Preview changes nothing."""
import json

import cleanup
import store_pg as pg
from test_store_pg import host  # fixture

A = "예약 기본 길이는 30분이다."
B = "예약 기본 길이는 30분이며 `slotMinutes` 로 설정한다."
MERGED = "예약 기본 길이는 30분이며 `slotMinutes` 로 설정한다."


def _seed(dsn, host, texts):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        for i, t in enumerate(texts, 1):
            cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                        values (%s,%s,'D',%s,%s,'fact','D:g',%s::jsonb)""",
                        (host, f"D-{i}", i, t, json.dumps({"record_id": "D", "origin": "test", "evidence_refs": []})))
    pg.backfill_embeddings(dsn, host, "plain")


def judge_for(rel):
    return lambda packet: {"answers": {"relation": {"type": "choice", "probabilities": {k: (.95 if k == rel else .01) for k in cleanup.RELATION["criteria"]}}}}


def merger_text(text):
    calls = []
    def m(items):
        calls.append(items)
        return {x["id"]: {"id": x["id"], "action": "merge", "text": text} for x in items}
    m.calls = calls
    return m


all_ok = lambda state, texts, q: [1.0] * len(texts)


def _active(dsn, host):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select alias, text from knowledge.fragment where host_id=%s and active order by alias", (host,))
        return cur.fetchall()


def test_merge_updates_first_and_retires_second(dsn, host, tmp_path):
    _seed(dsn, host, [A, B])
    prev = cleanup.run(dsn, host, judge_for("b_contains_a"), all_ok, merger_text(MERGED), min_sim=0.8, state_dir=tmp_path)
    assert prev["merged"] == 1 and _active(dsn, host) == [("D-1", A), ("D-2", B)]  # preview changes nothing
    out = cleanup.run(dsn, host, judge_for("b_contains_a"), all_ok, merger_text(MERGED), apply=True, min_sim=0.8, state_dir=tmp_path)
    assert out["rows"][0]["applied"] and _active(dsn, host) == [("D-1", MERGED)]
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select f.alias, h.op, h.actor from knowledge.fragment f join knowledge.fragment_history h
                       on h.fragment_id=f.id and h.revision=f.revision where f.host_id=%s order by f.alias""", (host,))
        rows = cur.fetchall()
    assert [(a, op) for a, op, _ in rows] == [("D-1", "update"), ("D-2", "deprecate")] and all(x.startswith("cleanup:") for *_, x in rows)
    back = cleanup.revert(dsn, host, out["run_id"], state_dir=tmp_path)
    assert back["reverted"] == ["D-1"] and _active(dsn, host) == [("D-1", A), ("D-2", B)]


def test_code_guard_keeps_both_after_one_retry(dsn, host, tmp_path):
    _seed(dsn, host, [A, B])
    m = merger_text("예약 기본 길이는 30분이다.")  # drops `slotMinutes` both times
    out = cleanup.run(dsn, host, judge_for("b_contains_a"), all_ok, m, apply=True, min_sim=0.8, state_dir=tmp_path)
    assert out["counts"] == {"kept_code": 1} and len(m.calls) == 2 and "`slotMinutes`" in m.calls[1][0]["missing"]
    assert len(_active(dsn, host)) == 2


def test_clause_guard_and_skips(dsn, host, tmp_path):
    _seed(dsn, host, [A, B])
    none = lambda state, texts, q: [0.0] * len(texts)
    out = cleanup.run(dsn, host, judge_for("same"), none, merger_text(MERGED), apply=True, min_sim=0.8, state_dir=tmp_path)
    assert out["counts"] == {"kept_clause": 1} and len(_active(dsn, host)) == 2
    out = cleanup.run(dsn, host, judge_for("different"), all_ok, merger_text(MERGED), apply=True, min_sim=0.8, state_dir=tmp_path)
    assert out["counts"] == {"skipped": 1} and len(_active(dsn, host)) == 2
    out = cleanup.run(dsn, host, judge_for("partial_overlap"), all_ok, merger_text(MERGED), apply=True, min_sim=0.8, state_dir=tmp_path)
    assert out["counts"] == {"skipped": 1} and len(_active(dsn, host)) == 2  # partial overlap is never merged
    conflict = lambda items: {x["id"]: {"id": x["id"], "action": "conflict", "why": "값 충돌"} for x in items}
    out = cleanup.run(dsn, host, judge_for("same"), all_ok, conflict, apply=True, min_sim=0.8, state_dir=tmp_path)
    assert out["counts"] == {"conflict": 1} and len(_active(dsn, host)) == 2
