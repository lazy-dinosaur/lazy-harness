"""Structure used beyond the canon scan (schema-delta '스키마 저장·활용 순서'): in-unit contradictions at record time
compare result leaves of one subject under the same condition (or one side unconditional); digestion keeps an add that
repeats a canonical fact of the same subject (same condition, same result sentences in any order) as evidence."""
import dedup
import digest_driver
import knowledge_cli
import store_pg as pg
from test_store_pg import fixture, host, judgement  # noqa: F401 (fixtures)


def test_same_fact_by_structure():
    assert dedup.same_fact("IF A가 없다 THEN B는 닫힌다 AND C는 비워진다", "IF A가 없다 THEN C는 비워진다 AND B는 닫힌다")
    assert not dedup.same_fact("IF A가 없다 THEN B는 닫힌다", "IF A가 있다 THEN B는 닫힌다")
    assert not dedup.same_fact("첨부 파일은 7일 보관된다", "첨부 파일은 30일 보관된다")
    assert not dedup.same_fact("B는 닫힌다 AND C는 비워진다", "B는 닫힌다")
    assert dedup.same_fact("화면은 목록을 보여 준다.", "화면은 목록을 보여 준다")
    assert dedup.find_duplicate("IF A가 없다 THEN C는 비워진다 AND B는 닫힌다", ["x", "IF A가 없다 THEN B는 닫힌다 AND C는 비워진다"]) == 1


def fact(text, subject="첨부 파일"):
    return {"operation": "add", "kind": "fact", "subject": subject, "fact": text, "reason": "r",
            "evidence_source": "user_confirmed", "keywords": [subject],
            "evidence_refs": [{"type": "user_utterance", "locator": "test/local", "quote": text}]}


def settle(dsn, entry_id, text):
    pg.batch(dsn, 1, {entry_id: [fixture(text=text)]}, entry_ids=[entry_id])  # leave nothing 'proposed'


def test_in_unit_contradiction_compares_leaves_under_the_same_condition(dsn, host):
    first = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [fact("첨부 파일은 30일 보관된다")]})
    uid = first["work_unit_id"]
    rule = "IF 보관 위치가 없다 THEN 첨부 파일은 7일 보관된다"
    second = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "work_unit_id": uid, "facts": [fact(rule)]})
    other = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "work_unit_id": uid,
                                       "facts": [fact("알림 설정은 30일 보관된다", "알림 설정")]})
    asked = []

    def judge(state, texts, q):
        asked.append((state["change"]["fact"], list(texts)))
        return [{"noul": 0.9 if "30일" in t else 0.1} for t in texts]
    new = fact("IF 사용자가 고정한다 THEN 첨부 파일은 영구 보관된다")
    import fact_form
    new["form"] = fact_form.parse(new["fact"])
    out = knowledge_cli.contradictions(dsn, host, uid, [new], {}, judge=judge)
    # compared with the unconditional 30-day fact of the same subject only: not the 7-day rule (other condition),
    # not the notification setting (other subject)
    assert asked == [("IF 사용자가 고정한다 THEN 첨부 파일은 영구 보관된다", ["첨부 파일은 30일 보관된다"])], asked
    assert out == [{"fact_index": 0, "with": "이 작업의 앞 기록", "text": "첨부 파일은 30일 보관된다"}], out
    for r, t in ((first, "첨부 파일은 30일 보관된다"), (second, rule), (other, "알림 설정은 30일 보관된다")):
        settle(dsn, r["entry_id"], t)


def test_digestion_keeps_a_structural_repeat_of_the_canon_as_evidence(dsn, host):
    judge = lambda packet: {"answers": fixture(text=packet["state"]["candidate_fact"])["answers"]}  # Jev says 'new'

    def absorb(text):
        body = judgement(host, text=text)
        body["facts"][0]["subject"] = "첨부 파일"
        entry = pg.register(dsn, body)
        settle(dsn, entry["entry_id"], text)
        pg.complete(dsn, body["work_unit_id"])
        return digest_driver.run_digestion(dsn, body["work_unit_id"], judge)
    a = "IF 보관 위치가 없다 THEN 첨부 파일은 7일 보관된다 AND 첨부 파일은 숨겨진다"
    b = "IF 보관 위치가 없다 THEN 첨부 파일은 숨겨진다 AND 첨부 파일은 7일 보관된다"
    assert absorb(a)["status"] == "absorbed"
    out = absorb(b)
    assert out["status"] == "processed", out
    texts = [r["text"] for r in pg.rows(dsn, "fragment") if r["host_id"] == host and r["active"]]
    assert texts == [a], texts
    assert [x["rule_id"] for x in pg.rows(dsn, "absorption") if x["rule_id"] == pg.CANON_DUP_RULE]
    # a different condition is a different fact
    assert absorb("IF 보관 위치가 있다 THEN 첨부 파일은 숨겨진다 AND 첨부 파일은 7일 보관된다")["status"] == "absorbed"
