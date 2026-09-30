"""Fragment token [alias@revision]: shown when reading, resolved mechanically when recording (no guessing)."""
import json

import knowledge_cli
import store_pg as pg
import worker_tools as wt
from test_store_pg import host  # fixture


def seed(dsn, host):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                    values (%s,'tr-1','tr',1,'설명은 300자','fact','tr:g',%s::jsonb) returning id::text,revision""",
                    (host, json.dumps({"evidence_refs": []})))
        return cur.fetchone()


def fact(target):
    return {"operation": "update", "kind": "fact", "subject": "설명은", "fact": "설명은 1000자", "evidence_source": "user_confirmed",
            "reason": "test", "target_ref": target, "evidence_refs": [{"type": "user_utterance", "locator": "t", "quote": "설명은 1000자"}]}


def test_render_shows_token():
    lines = wt._render([{"id": "x", "alias": "tr-1", "revision": 3, "text": "t", "kind": "fact", "domain": "tr", "seq": 1}])
    assert any("[tr-1@3] t" in l for l in lines)


def test_record_resolves_token(dsn, host):
    fid, rev = seed(dsn, host)
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "tr", "facts": [fact(f"[tr-1@{rev}]")]})
    assert out.get("state") == "proposed", out
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select judgement_body from knowledge.ledger_entry where entry_id=%s", (out["entry_id"],))
        f = cur.fetchone()[0]["facts"][0]
    assert f["target_ref"] == fid and f["expected_revision"] == rev
    bad = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "tr", "facts": [fact("tr-404@1")]})
    assert bad["errors"][0]["code"] == "E_TARGET"
    pg.abandon(dsn, out["work_unit_id"], "test cleanup")
