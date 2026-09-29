"""rules_store (migrations/0006) on the conftest-owned disposable PostgreSQL."""
import pytest

import rules_store as rs
import store_pg as pg
from test_store_pg import host  # fixture

RULE = {"when": "코드 파일을 수정했을 때", "must": "관련 테스트를 실행해 통과시킨다", "level": "must",
        "unless": "문서만 바꾼 경우", "why": "배포 사고"}


def test_create_update_delete_with_history(dsn, host):
    out = rs.create(dsn, host, RULE, "앞으로 코드 고치면 무조건 테스트 돌려")
    assert out["ok"] and out["id"].startswith("p-")
    rid = out["id"]
    assert [r["id"] for r in rs.list_rules(dsn, host)] == [rid]
    up = rs.update(dsn, host, rid, {"must": "pnpm test 를 통과시킨다", "unless": None}, "pnpm test 로 바꿔")
    assert up["version"] == 2
    now = rs.list_rules(dsn, host)[0]
    assert now["must"] == "pnpm test 를 통과시킨다" and "unless" not in now and now["why"] == "배포 사고"
    assert rs.delete(dsn, host, rid, "이 규칙 없애")["status"] == "deleted"
    assert rs.list_rules(dsn, host) == []
    assert [h["op"] for h in rs.history(dsn, rid)] == ["create", "update", "delete"]
    assert rs.history(dsn, rid)[1]["source"]["quote"] == "pnpm test 로 바꿔"


def test_schema_and_source_guards(dsn, host):
    assert rs.create(dsn, host, {**RULE, "level": "block"}, "해")["ok"] is False
    assert rs.create(dsn, host, {**RULE, "id": "h-1"}, "해")["ok"] is False
    assert rs.create(dsn, host, {**RULE, "code_check": {"type": "magic"}}, "해")["ok"] is False
    with pytest.raises(ValueError):
        rs.create(dsn, host, RULE, "이렇게 할까?")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into rules.rule(rule_id,host_id,when_text,must_text,level,source)
                       values ('h-900',null,'항상','폴더 밖 금지','must','{"quote":"harness"}')""")
    with pytest.raises(ValueError):
        rs.update(dsn, host, "h-900", {"must": "밖도 읽음"}, "바꿔")
    with pytest.raises(ValueError):
        rs.delete(dsn, host, "h-900", "지워")
    assert "h-900" not in [r["id"] for r in rs.list_rules(dsn, host)]  # DB base rows are never project rules
    with pg.connect(dsn) as conn, conn.cursor() as cur, pytest.raises(pg.driver.Error):
        cur.execute("""insert into rules.rule(rule_id,host_id,when_text,must_text,level,source)
                       values ('h-901',%s,'항상','x','must','{}')""", (host,))


def test_review_flags_need_user_confirmation(dsn, host):
    review = lambda rule, existing: ["conflict with p-1"]
    held = rs.create(dsn, host, RULE, "테스트 돌려", review=review)
    assert held["needs_user"] and rs.list_rules(dsn, host) == []
    done = rs.create(dsn, host, RULE, "테스트 돌려", review=review, confirm_quote="그래도 넣어")
    assert done["ok"] and rs.history(dsn, done["id"])[0]["source"]["confirm"] == "그래도 넣어"


def test_injection_and_receipts(dsn, host):
    rid = rs.create(dsn, host, RULE, "테스트 돌려")["id"]
    rs.record_injection(dsn, host, "turn-1", [rid], ["design-1"], 420)
    rs.record_injection(dsn, host, "turn-1", [rid], ["design-2"], 30)
    got = rs.injected(dsn, host, "turn-1")
    assert got["rules"] == [rid] and sorted(got["knowledge"]) == ["design-1", "design-2"]
    assert rs.injected(dsn, host, "turn-2") == {"rules": [], "knowledge": []}
    rule = rs.list_rules(dsn, host)[0]
    v = {"label": "violated", "confident": True, "cond": ["met", 0.9], "done": ["not_done", 0.9],
         "items": [{"alias": "design-1", "text": "t", "p": 0.9}], "rule_delivered": True}
    [receipt] = rs.save_receipts(dsn, host, "turn-1", [rule], [v], {"files": ["a.tsx"]})
    assert rs.dispute(dsn, receipt, "이 파일은 문서라 예외")["ok"]
    with pytest.raises(ValueError):
        rs.dispute(dsn, receipt, "두 번째")


def test_harness_receipts_need_no_rule_row(dsn, host):
    import harness_rules
    v = {"label": "violated", "confident": True, "cond": ["met", 0.9], "done": ["not_done", 0.9], "items": []}
    [rid] = rs.save_receipts(dsn, host, "turn-h", harness_rules.rules(), [v], {"user": "x"})
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select origin, rule_id from rules.judgement_receipt where receipt_id=%s", (rid,))
        assert cur.fetchone() == ("harness", "H-1")
        with pytest.raises(pg.driver.Error):
            cur.execute("""insert into rules.judgement_receipt(receipt_id,host_id,turn_ref,rule_id,rule_version,label,confident,cond,done,evidence,origin)
                           values (gen_random_uuid(),%s,'t','p-1',1,'followed',true,'[]','[]','{}','harness')""", (host,))
