"""flow3 P2 bug (2026-10-01): a work unit whose changes sit in several ledger entries hit two stale-base conflicts; the
user answered the one question shown for the unit, the answer was copied to every stale question of the unit, but only
the answered entry was reopened -- the other entry stayed in review_queue and its changes never reached the canon."""
import json

import digest_driver
import knowledge_cli
import store_pg as pg
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixtures)


def seed(dsn, host, alias, text):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                       values (%s,%s,'su',(select coalesce(max(seq),0)+1 from knowledge.fragment where host_id=%s and domain='su'),
                       %s,'fact','su:g',%s::jsonb) returning id::text""", (host, alias, host, text, json.dumps({"evidence_refs": []})))
        return cur.fetchone()[0]


def bump(dsn, fid, text):  # another work unit already changed the fragment
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.fragment set revision=revision+1, text=%s where id=%s", (text, fid))


def judge(packet):
    st = packet["state"]
    f = fixture(operation="update" if "target_excerpt" in st else "add", text=st["candidate_fact"], excerpt=st.get("target_excerpt"))
    return {"answers": {k: f["answers"][k] for k in packet["questions"]}}


def text_of(dsn, fid):
    return [r["text"] for r in pg.rows(dsn, "fragment") if r["id"] == fid][0]


def test_one_answer_reopens_every_entry_of_the_unit(dsn, host):
    f1, f2 = seed(dsn, host, "su-1", "길이는 300자다"), seed(dsn, host, "su-2", "캐시는 300자다")
    bump(dsn, f1, "길이는 800자다")
    bump(dsn, f2, "캐시는 800자다")
    uid = None
    for fid, new, now in ((f1, "길이는 1000자다", "길이는 800자다"), (f2, "캐시는 1000자다", "캐시는 800자다")):
        body = judgement(host, operation="update", target=fid, text=new)
        body["facts"][0]["expected_revision"] = 1  # both were read at revision 1
        if uid:
            body["work_unit_id"] = uid
        uid = body["work_unit_id"]
        entry = pg.register(dsn, body)
        pg.batch(dsn, 1, {entry["entry_id"]: [fixture(operation="update", text=new, excerpt=now, revision=2)]},
                 entry_ids=[entry["entry_id"]])
    pg.complete(dsn, uid)
    digest_driver.run_digestion(dsn, uid, judge)
    assert text_of(dsn, f1) == "길이는 800자다" and text_of(dsn, f2) == "캐시는 800자다"  # the unit waits
    stale = [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i["work_unit_id"] == uid]
    assert len(stale) == 1, stale  # one question for the change
    pg.review_resolve(dsn, host, stale[0]["entry_id"], stale[0]["fact_index"], "approve", "1000이 맞아", "test/user")
    out = digest_driver.run_digestion(dsn, uid, judge)
    assert text_of(dsn, f1) == "길이는 1000자다" and text_of(dsn, f2) == "캐시는 1000자다", out
    assert [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i["work_unit_id"] == uid] == []
