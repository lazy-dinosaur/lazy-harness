"""astra review P0 (2026-10-01), reproduced before the fix:
P0-1 a unit with a waiting change must not commit its other entries on a later pass;
P0-2 the preview must not close records, and two updates of one fragment in one unit are merged, not 'last wins';
P0-3 a stale-base approval holds for the revision the user saw, not for later ones; update/deprecate need the read revision;
P0-4 duplicate test keeps numbers and qualifiers."""
import json

import dedup
import digest_driver
import knowledge_cli
import store_pg as pg
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixtures)


def seed(dsn, host, alias, text):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                       values (%s,%s,'p0',(select coalesce(max(seq),0)+1 from knowledge.fragment where host_id=%s and domain='p0'),
                       %s,'fact','p0:g',%s::jsonb) returning id::text""", (host, alias, host, text, json.dumps({"evidence_refs": []})))
        return cur.fetchone()[0]


def bump(dsn, fid, text):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.fragment set revision=revision+1, text=%s where id=%s", (text, fid))


def judge(packet):
    st = packet["state"]
    f = fixture(operation="update" if "target_excerpt" in st else "add", text=st["candidate_fact"], excerpt=st.get("target_excerpt"))
    return {"answers": {k: f["answers"][k] for k in packet["questions"]}}


def text_of(dsn, fid):
    return [r["text"] for r in pg.rows(dsn, "fragment") if r["id"] == fid][0]


def settle_unit(dsn, host, uid):
    """Leave nothing waiting in the shared DB (the poller tests read every completed unit): reject what is still asked."""
    for it in [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i["work_unit_id"] == uid]:
        pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], "reject", "아니 그건 아니야", "t")
    digest_driver.run_digestion(dsn, uid, judge)


def update_entry(dsn, host, uid, fid, new, now, exp=1):
    body = judgement(host, operation="update", target=fid, text=new)
    body["facts"][0]["expected_revision"] = exp
    if uid:
        body["work_unit_id"] = uid
    e = pg.register(dsn, body)
    pg.batch(dsn, 1, {e["entry_id"]: [fixture(operation="update", text=new, excerpt=now)]}, entry_ids=[e["entry_id"]])
    return body["work_unit_id"], e["entry_id"]


def add_entry(dsn, host, uid, text):
    body = judgement(host, text=text)
    body["work_unit_id"] = uid
    e = pg.register(dsn, body)
    pg.batch(dsn, 1, {e["entry_id"]: [fixture(text=text)]}, entry_ids=[e["entry_id"]])
    return e["entry_id"]


def test_p0_1_waiting_change_holds_the_whole_unit_on_every_pass(dsn, host):
    f = seed(dsn, host, "p0a-1", "길이는 300자다")
    bump(dsn, f, "길이는 800자다")
    uid, _ = update_entry(dsn, host, None, f, "길이는 1000자다", "길이는 800자다")
    add_entry(dsn, host, uid, "p0a 보조 사실은 함께 들어간다")
    pg.complete(dsn, uid)
    digest_driver.run_digestion(dsn, uid, judge)  # the change conflicts: the unit waits
    digest_driver.run_digestion(dsn, uid, judge)  # a later pass without an answer
    assert not [r for r in pg.rows(dsn, "fragment") if r["host_id"] == host and r["text"] == "p0a 보조 사실은 함께 들어간다"]
    settle_unit(dsn, host, uid)


def test_p0_2_preview_changes_nothing_and_two_updates_of_one_fragment_merge(dsn, host):
    base = "IF A가 없다 THEN B는 3일 보관된다 AND C는 숨겨진다"
    f = seed(dsn, host, "p0b-1", base)
    uid, _ = update_entry(dsn, host, None, f, "IF A가 없다 THEN B는 7일 보관된다 AND C는 숨겨진다", base)
    update_entry(dsn, host, uid, f, "IF A가 없다 THEN B는 3일 보관된다 AND C는 지워진다", base)
    pg.complete(dsn, uid)
    before = len(pg.rows(dsn, "confirmation_queue"))
    pg.digest(dsn, uid, apply=False)
    assert len(pg.rows(dsn, "confirmation_queue")) == before  # preview wrote nothing
    digest_driver.run_digestion(dsn, uid, judge)
    assert text_of(dsn, f) == "IF A가 없다 THEN B는 7일 보관된다 AND C는 지워진다"  # both changes kept


def test_p0_3_stale_approval_is_for_the_revision_seen(dsn, host):
    f = seed(dsn, host, "p0c-1", "캐시는 300자다")
    bump(dsn, f, "캐시는 800자다")
    uid, _ = update_entry(dsn, host, None, f, "캐시는 1000자다", "캐시는 800자다")
    pg.complete(dsn, uid)
    digest_driver.run_digestion(dsn, uid, judge)
    item = [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i["work_unit_id"] == uid][0]
    pg.review_resolve(dsn, host, item["entry_id"], item["fact_index"], "approve", "1000이 맞아", "t")
    bump(dsn, f, "캐시는 500자다")  # another unit changes it again before this one is digested
    digest_driver.run_digestion(dsn, uid, judge)
    assert text_of(dsn, f) == "캐시는 500자다"  # not silently overwritten
    again = [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i["work_unit_id"] == uid]
    assert again and "r3" in str(again[0]["review_reasons"]), again  # asked again about the new revision
    settle_unit(dsn, host, uid)


def test_p0_3_update_needs_the_read_revision(dsn, host):
    f = seed(dsn, host, "p0d-1", "제한은 300자다")
    fact = {"operation": "update", "kind": "fact", "subject": "제한", "fact": "제한은 1000자다", "reason": "r",
            "evidence_source": "user_confirmed", "target_ref": f,
            "evidence_refs": [{"type": "user_utterance", "locator": "t", "quote": "제한은 1000자다"}]}
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "p0", "facts": [fact]})
    assert "E_TARGET" in [e["code"] for e in out.get("errors", [])], out
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "p0", "facts": [{**fact, "target_ref": "[p0d-1]"}]})
    assert "E_TARGET" in [e["code"] for e in out.get("errors", [])], out


def test_p0_4_duplicate_keeps_numbers_and_qualifiers():
    assert not dedup.same_fact("값은 1.5다", "값은 15다")
    assert not dedup.same_fact("재시도는 최대 3회다", "재시도는 3회다")
    assert not dedup.same_fact("현재 허용한다", "허용한다")
    assert dedup.same_fact("`ensure` 는 1000자로 자른다.", "ensure는 1000자로 자른다")
