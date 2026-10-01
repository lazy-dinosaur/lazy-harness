"""astra direction review P1 (2026-10-01): duplicate judging of an add and the commit share one final change plan."""
import digest_driver
import store_pg as pg
from test_p0_review import add_entry, judge, seed, settle_unit, text_of, update_entry
from test_store_pg import host  # noqa: F401 (fixture)


def _capturing():
    seen = []

    def j(packet):
        seen.append(packet["state"])
        return judge(packet)
    return j, seen


def test_add_is_judged_against_the_merged_update_not_the_last_record(dsn, host):
    base = "IF 플랜이 없다 THEN 플랜 로그는 3일 보관된다 AND 플랜 화면은 숨겨진다"
    f = seed(dsn, host, "fp-1", base)
    uid, _ = update_entry(dsn, host, None, f, "IF 플랜이 없다 THEN 플랜 로그는 7일 보관된다 AND 플랜 화면은 숨겨진다", base)
    update_entry(dsn, host, uid, f, "IF 플랜이 없다 THEN 플랜 로그는 3일 보관된다 AND 플랜 화면은 지워진다", base)
    add_entry(dsn, host, uid, "플랜 알림은 꺼진다")
    pg.complete(dsn, uid)
    plan = pg.digest(dsn, uid, apply=False)
    merged = "IF 플랜이 없다 THEN 플랜 로그는 7일 보관된다 AND 플랜 화면은 지워진다"
    assert plan["rewrites"] == {f: merged}  # the plan is the merge, not 'last wins'
    j, seen = _capturing()
    digest_driver.run_digestion(dsn, uid, j)
    excerpts = [s["existing_records_excerpt"] for s in seen if "existing_records_excerpt" in s]
    assert excerpts and all("3일 보관된다 AND 플랜 화면은 지워진다" not in e for e in excerpts)
    assert any(merged in e for e in excerpts), excerpts
    assert text_of(dsn, f) == merged


def test_deprecated_fragment_is_not_a_duplicate_reference(dsn, host):
    f = seed(dsn, host, "fp-2", "폐기 시험 설정은 켜진다")
    body_uid, _ = update_entry(dsn, host, None, f, "폐기 시험 설정은 켜진다", "폐기 시험 설정은 켜진다")
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # make that record a deprecate of the fragment
        cur.execute("""update knowledge.ledger_entry set judgement_body=jsonb_set(judgement_body,'{facts,0,operation}','"deprecate"')
                       where work_unit_id=%s""", (body_uid,))
    add_entry(dsn, host, body_uid, "폐기 시험 설정은 켜진다")
    pg.complete(dsn, body_uid)
    plan = pg.digest(dsn, body_uid, apply=False)
    assert plan.get("rewrites") == {f: None}
    settle_unit(dsn, host, body_uid)  # the poller tests read every completed unit of the shared DB
