"""G2: deprecate end to end — record (lint) -> worktime (intent-deprecate) -> completion -> digestion -> active=false."""
import json

import digest_driver
import knowledge_cli
import store_pg as pg
import worktime_driver
from test_store_pg import host  # fixture


def seed_one(dsn, host, text):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("insert into knowledge.domain_type(host_id,domain) values (%s,'D') on conflict do nothing", (host,))
        cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                    values (%s,'D-001','D',1,%s,'fact','D:g1',%s::jsonb) returning id::text""",
                    (host, text, json.dumps({"record_id": "D", "origin": "test", "evidence_refs": []})))
        return cur.fetchone()[0]


def dep_fact(ref, quote="좋아 그 규칙은 이제 없애자"):
    return {"operation": "deprecate", "kind": "fact", "subject": "병원 일정",
            "fact": "병원 일정 종류 구분은 더 이상 쓰이지 않는다", "target_ref": ref,
            "evidence_source": "user_confirmed", "reason": "사용자가 규칙 폐지를 확정했다.",
            "evidence_refs": [{"type": "user_utterance", "locator": "chat", "quote": quote},
                              {"type": "official_doc", "locator": "fragment/D-001", "quote": "병원 일정 종류는 HOSPITAL_SCHEDULE 이다."}]}


def run(dsn, host, fact, invalidation):
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [fact]})
    assert out.get("state") == "proposed", out
    ans = {"invalidation_evidence": {"type": "choice", "probabilities": {invalidation: .96, "consistent" if invalidation != "consistent" else "invalidates": .02, "insufficient": .01, "none_or_uncertain": .01}},
           "replacement_exists": {"type": "choice", "probabilities": {"no_replacement_needed": .96, "replacement_provided": .02, "replacement_missing": .01, "none_or_uncertain": .01}}}
    judge = lambda packet: {"answers": {k: ans[k] for k in packet["questions"]}}
    worktime_driver.run_worktime(dsn, 1, judge, entry_ids=[out["entry_id"]])
    uid = out["work_unit_id"]
    pg.register_completion_sources(dsn, uid, ["user_confirm"])
    pg.signal_completion(dsn, uid, "user_confirm", evidence={"quote": "좋아", "locator": None})
    return digest_driver.run_digestion(dsn, uid, judge, choose=lambda text, options: {})


def test_deprecate_absorbs_to_inactive_with_history(dsn, host):
    ref = seed_one(dsn, host, "병원 일정 종류는 HOSPITAL_SCHEDULE 이다.")
    run(dsn, host, dep_fact(ref), "invalidates")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select active, revision from knowledge.fragment where id=%s", (ref,))
        assert cur.fetchone() == (False, 2)
        cur.execute("select op from knowledge.fragment_history where fragment_id=%s order by history_id desc limit 1", (ref,))
        assert cur.fetchone()[0] == "deprecate"
        cur.execute("select template_id from knowledge.check_receipt r join knowledge.ledger_entry e on e.entry_id=r.entry_id where e.host_id=%s", (host,))
        assert {r[0] for r in cur.fetchall()} == {"intent-deprecate"}
    assert all(r["id"] != ref for r in pg.search(dsn, host, "병원 일정 종류", 8))


def test_deprecate_is_a_command_even_when_jev_thinks_still_valid(dsn, host):
    """schema-delta '사용자에게 묻는 것은 모순뿐': a user-confirmed deprecate applies; Jev does not second-guess it."""
    ref = seed_one(dsn, host, "병원 일정 종류는 HOSPITAL_SCHEDULE 이다.")
    run(dsn, host, dep_fact(ref), "consistent")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select active from knowledge.fragment where id=%s", (ref,))
        assert cur.fetchone()[0] is False


def test_deprecate_needs_user_confirmation(dsn, host):
    ref = seed_one(dsn, host, "병원 일정 종류는 HOSPITAL_SCHEDULE 이다.")
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [{**dep_fact(ref), "evidence_source": "ai_inference"}]})
    assert not out["ok"] and out["errors"][0]["code"] == "E_DEPRECATE_CONFIRM"
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [dep_fact(ref, quote="이거 없애도 되나?")]})
    assert not out["ok"] and any(e["code"] == "E_USER_REF" or e["code"].startswith("E_USER") for e in out["errors"]), out
