"""Fact form: English operators between Korean leaf sentences; connectives inside a leaf are rejected."""
import fact_form


def ok(text):
    assert fact_form.check(text) == [], (text, fact_form.check(text))


def bad(text, needle):
    errs = fact_form.check(text)
    assert errs and any(needle in e for e in errs), (text, errs)


def test_operator_forms_pass():
    ok("화면은 목록을 보여 준다.")
    ok("IF 보관 위치가 없다 OR 보관 위치가 비활성 상태다 THEN 첨부 파일은 고아 첨부로 분류된다")
    ok("IF 사용자가 저장 안 함을 고른다 THEN 편집 창은 닫히지 않는다 AND 편집 창은 입력만 비운다")
    ok("IF MCP가 노드 정보를 제공할 수 있다 EVEN IF REST PAT가 실패한다 THEN 에이전트는 MCP를 활성 경로로 쓴다")
    ok("AFTER 캐시 크기를 2 GiB로 올렸다 THEN 빌드 시간이 약 40% 줄었다")
    ok("ADR 0054는 개정된다 BECAUSE 로컬 코드 정돈과 시스템 아키텍처를 분리하고 있어서 독립 경계다")
    ok("IF (방이 열린다 OR 방이 포커스된다) THEN `chat.markAsRead`는 읽음 처리를 보낸다")
    ok("자동완성은 필터링할 때 쓰는 키를 보여 준다")  # noun-modifying '~할 때'
    ok("limit is 300 chars")


def test_connectives_and_bad_structure_are_rejected():
    bad("편집 창은 닫히지 않고 입력만 비운다.", "않고")
    bad("보관 위치가 없으면 첨부 파일은 고아로 분류된다", "없으면")
    bad("IF 사용자가 누른다 THEN 창은 닫히거나 숨는다", "닫히거나")
    bad("IF 사용자가 누른다", "THEN")
    bad("창은 닫힌다 THEN 입력은 비워진다", "THEN 은")
    bad("IF 사용자가 누른다 THEN 창은 닫힌다 OR 창은 숨는다", "AND 로만")
    bad("창은 닫힌다 BECAUSE 사용자가 원했다 AND 입력은 비워진다", "BECAUSE")
    bad("IF (방이 열린다 THEN 창은 닫힌다", "괄호")


def test_record_rejects_a_fact_that_is_not_in_the_form(dsn, host):
    import knowledge_cli
    fact = {"operation": "add", "kind": "fact", "subject": "편집 창", "fact": "편집 창은 닫히지 않고 입력만 비운다",
            "reason": "r", "evidence_source": "user_confirmed", "keywords": ["편집 창"],
            "evidence_refs": [{"type": "user_utterance", "locator": "test/local", "quote": "편집 창은 닫히지 않고 입력만 비운다"}]}
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [fact]})
    assert out["ok"] is False and [e["code"] for e in out["errors"]] == ["E_FORM"], out
    good = {**fact, "fact": "편집 창은 닫히지 않는다 AND 편집 창은 입력만 비운다",
            "evidence_refs": [{"type": "user_utterance", "locator": "test/local", "quote": "편집 창은 닫히지 않는다 AND 편집 창은 입력만 비운다"}]}
    out = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [good]})
    assert out.get("entry_id") and not out.get("errors"), out
    import store_pg as pg
    from test_store_pg import fixture
    pg.batch(dsn, 1, {out["entry_id"]: [fixture(text=good["fact"])]}, entry_ids=[out["entry_id"]])  # leave nothing proposed


from test_store_pg import host  # noqa: E402,F401 (fixture)
