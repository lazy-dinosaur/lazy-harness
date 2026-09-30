"""0009 ledger protocol lines: lint, key registry nudges, storage, append-only, D2 relation rules."""
import pytest

import knowledge_cli
import ledger_lines as ll
import store_pg as pg
from test_store_pg import host  # fixture


def L(key, new, kind="change", source="user", old="", **kw):
    return {"key": key, "old": old, "new": new, "kind": kind, "source": source, **kw}


def test_lint():
    assert ll.lint([L("도메인설명/길이제한", "1000자")]) == []
    codes = lambda lines: [e["code"] for e in ll.lint(lines)]
    assert codes([]) == ["E_LINES"]
    assert codes([L("도메인 설명", "1000자")]) == ["E_KEY"]
    assert codes([L("a/b", "")]) == ["E_NEW"]
    assert codes([L("a/b", "1000자, 50자")]) == ["E_ONE_VALUE"]
    assert codes([L("a/b", "1,000자")]) == []
    assert codes([L("a/b", "x", kind="guess", source="ai")]) == ["E_LINE_KIND", "E_LINE_SOURCE"]
    assert codes([L("a/b", "x"), L("a/b", "y")]) == ["E_KEY_TWICE"]


def test_similar_keys():
    known = ["도메인설명/길이제한", "도메인설명/공백처리", "검색결과/페이지크기"]
    assert ll.similar_keys("도메인설명/길이제한값", known)[0] == "도메인설명/길이제한"
    assert "검색결과/페이지크기" not in ll.similar_keys("도메인설명/최대길이", known)


def test_relation_rules():
    frag = {"도메인설명/초과처리": "F9", "도메인설명/공백처리": "F9"}.get
    K = "도메인설명/길이제한"
    assert ll.relation([L(K, "1000자")], [L(K, "1,000자")]) == "merge"
    assert ll.relation([L(K, "1000자")], [L(K, "800자")]) == "replace"
    assert ll.relation([L(K, "1000자", source="user")], [L(K, "800자", kind="observation", source="code")]) == "conflict"
    assert ll.relation([L(K, "1000자"), L("도메인이름/길이제한", "50자")], [L(K, "1000자")]) == "separate"
    assert ll.relation([L("도메인설명/초과처리", "1000자 거부")], [L("도메인설명/공백처리", "줄바꿈 제거")], frag) == "combine"
    assert ll.relation([L(K, "1000자")], [L("검색결과/페이지크기", "50개")]) == "separate"
    assert ll.relation([L(K, "5자", temporary=True)], [L(K, "1000자")]) == "replace"


def fact(text, lines):
    return {"operation": "add", "kind": "fact", "subject": text.split()[0], "fact": text, "evidence_source": "user_confirmed",
            "reason": "test", "evidence_refs": [{"type": "user_utterance", "locator": "test", "quote": text}], "lines": lines}


def test_record_stores_lines_and_nudges_keys(dsn, host):
    rec = lambda f, **kw: knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "facts": [f], **kw})
    missing = knowledge_cli.record(dsn, {"host_id": host, "partition_key": "D", "require_lines": True,
                                          "facts": [{k: v for k, v in fact("설명 제한은 1000자", []).items() if k != "lines"}]})
    assert [e["code"] for e in missing["errors"]] == ["E_LINES"]
    first = rec(fact("설명 제한은 1000자", [L("설명/길이제한", "1000자")]))
    assert first["errors"][0]["code"] == "E_KEY_UNKNOWN" and first["errors"][0]["similar"] == []
    ok = rec(fact("설명 제한은 1000자", [L("설명/길이제한", "1000자", new_key=True)]))
    assert ok["state"] == "proposed"
    near = rec(fact("설명 제한은 800자", [L("설명/길이제한값", "800자")]))
    assert near["errors"][0]["similar"] == ["설명/길이제한"]
    again = rec(fact("설명 제한은 800자", [L("설명/길이제한", "800자")]))
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select key,new_value,kind,source from knowledge.ledger_line where entry_id=any(%s::uuid[]) order by line_id",
                    ([ok["entry_id"], again["entry_id"]],))
        assert cur.fetchall() == [("설명/길이제한", "1000자", "change", "user"), ("설명/길이제한", "800자", "change", "user")]
    with pytest.raises(Exception):
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("update knowledge.ledger_line set new_value='x' where entry_id=%s", (ok["entry_id"],))
    for uid in (ok["work_unit_id"], again["work_unit_id"]):
        pg.abandon(dsn, uid, "test cleanup")


def test_db_rejects_malformed_line(dsn, host):
    with pytest.raises(Exception):
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("insert into knowledge.fact_key(host_id,key) values (%s,'no slash')", (host,))
