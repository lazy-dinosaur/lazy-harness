"""Structure backfill for fragments made before 0009/0010: form, subject and leaves at the same revision, no history."""
import json

import backfill_structure as bf
import knowledge_cli
import store_pg as pg
from test_store_pg import host  # noqa: F401 (fixture)


def seed(dsn, host, alias, text, subject=None):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                       values (%s,%s,'bf',(select coalesce(max(seq),0)+1 from knowledge.fragment where host_id=%s and domain='bf'),
                       %s,'fact','bf:g',%s::jsonb) returning id::text""",
                    (host, alias, host, text, json.dumps({"evidence_refs": [], **({"subject": subject} if subject else {})})))
        return cur.fetchone()[0]


def test_backfill_structures_old_fragments_without_new_revisions(dsn, host):
    a = seed(dsn, host, "bf-1", "도메인 설명 길이는 생성·수정 모두 300자", "도메인 설명 길이")
    b = seed(dsn, host, "bf-2", "domain_router.py의 ensure는 생성 설명을 최대 300자로 자른다.")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select count(*) from knowledge.fragment_history where fragment_id = any(%s::uuid[])", ([a, b],))
        hist = cur.fetchone()[0]
        rows = bf.plan(cur, host)
        assert {r["alias"]: (r["subject"], r["subject_from"]) for r in rows} == {
            "bf-1": ("도메인 설명 길이", "source"), "bf-2": ("domain_router.py", "head")}
        assert bf.apply(cur, host, rows) == 2
        assert bf.apply(cur, host, rows) == 0  # idempotent
    frags = {r["alias"]: r for r in pg.rows(dsn, "fragment") if r["host_id"] == host}
    assert all(frags[k]["revision"] == 1 and frags[k]["form"] and frags[k]["subject_id"] for k in ("bf-1", "bf-2"))
    leaves = [r for r in pg.rows(dsn, "fragment_leaf") if r["fragment_id"] in (a, b)]
    assert len(leaves) == 2 and {r["revision"] for r in leaves} == {1}
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select count(*) from knowledge.fragment_history where fragment_id = any(%s::uuid[])", ([a, b],))
        assert cur.fetchone()[0] == hist  # no history for metadata
        # a content change still needs the revision bump
        import pytest
        with pytest.raises(pg.driver.Error):
            cur.execute("update knowledge.fragment set text='x' where id=%s", (a,))
    # 0011: structure is filled once without a revision; changing it afterwards is a meaning change with history
    for sql in ("update knowledge.fragment set form='{\"kind\":\"plain\",\"then\":[\"x\"]}'::jsonb where id=%s",
                "update knowledge.fragment set subject_id=null where id=%s"):
        with pg.connect(dsn) as conn, conn.cursor() as cur, pytest.raises(pg.driver.Error):
            cur.execute(sql, (a,))


def test_grouped_contradiction_question(dsn, host):
    """flow3 r4: one question per fragment listing every fragment it contradicts; one answer closes them all."""
    import digest_driver
    from test_store_pg import fixture, judgement

    def absorb(text):
        body = judgement(host, text=text)
        body["facts"][0]["subject"] = "그룹 설명"
        e = pg.register(dsn, body)
        pg.batch(dsn, 1, {e["entry_id"]: [fixture(text=text)]}, entry_ids=[e["entry_id"]])
        pg.complete(dsn, body["work_unit_id"])
        digest_driver.run_digestion(dsn, body["work_unit_id"], lambda p: {"answers": fixture(text=p["state"]["candidate_fact"])["answers"]})
        return body["work_unit_id"]
    absorb("그룹 설명은 300자다")
    absorb("그룹 설명은 500자다")
    unit = absorb("그룹 설명은 1000자다")
    contra = lambda state, texts, q: [{"noul": 0.9 if ("300" in t or "500" in t) and "1000" in state["fact"] else 0.0} for t in texts]
    assert pg.scan_contradictions(dsn, unit, contra)["contradictions"] == 2
    items = [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "contradiction"
             and "1000" in i["fact"]]
    assert len(items) == 1 and len(items[0]["review_reasons"]) == 2, items
    pg.review_resolve(dsn, host, items[0]["entry_id"], items[0]["fact_index"], "approve", "1000이 맞아", "t", items[0]["question_ids"])
    assert not [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "contradiction"
                and "1000" in i["fact"]]
