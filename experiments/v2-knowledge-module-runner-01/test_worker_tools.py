"""worker_tools against the conftest-owned disposable DB; Jev replaced by a deterministic fake."""
import json

import pytest

import store_pg as pg
import worker_tools as wt
from test_store_pg import host  # fixture


def seed(dsn, host, texts, group="g1"):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        for i, t in enumerate(texts, 1):
            cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                        values (%s,%s,%s,%s,%s,'fact',%s,%s::jsonb)""", (host, f"D-{i:03d}", "D", i, t, f"D:{group}",
                        json.dumps({"record_id": "D", "origin": "test", "evidence_refs": []})))
    for v in ("plain", "ctx-v1"):
        pg.backfill_embeddings(dsn, host, v)


def test_code_refs_pick_changed_lines_with_new_value(tmp_path):
    import subprocess
    g = lambda *a: subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    (tmp_path / "router.py").write_text("LIMIT = 300\nother = 1\n")
    (tmp_path / "test_router.py").write_text("assert LIMIT == 300\n")
    g("add", "."); g("commit", "-qm", "base")
    (tmp_path / "router.py").write_text("LIMIT = 1000\nother = 1\n")
    (tmp_path / "test_router.py").write_text("assert LIMIT == 1000\n")
    added = wt._added_lines(tmp_path)
    assert ("router.py", 1, "LIMIT = 1000") in added
    ch = {"new": "1000"}
    refs = wt._code_refs(ch, "router.py 의 LIMIT 는 1000", added)
    assert refs[0] == {"type": "code_test", "locator": "router.py:1", "quote": "LIMIT = 1000"}
    assert {r["locator"] for r in refs} == {"router.py:1", "test_router.py:1"}
    assert wt._code_refs({"new": "2000"}, "x", added) == []  # code does not show the change -> no code evidence
    # prose value: '1000자' matches the code token 1000 that the old value '300자' did not have
    assert wt._code_refs({"old": "300자", "new": "1000자"}, "router.py", added)[0]["locator"] == "router.py:1"
    assert wt._added_lines(None) == [] and wt._added_lines(tmp_path / "nope") == []
    fact = wt._update_fact({"user_quote": "1000으로", "subject": "s", "old": "300", "new": "1000"},
                           {"alias": "a-1", "text": "LIMIT 는 300", "id": "x"}, "LIMIT 는 1000", refs)
    assert [r["type"] for r in fact["evidence_refs"]] == ["user_utterance", "official_doc", "code_test", "code_test"]


def fake_ask(old_marker="HOSPITAL_SCHEDULE", still_marker="HOSPITAL_SCHEDULE"):
    calls = []
    def ask(state, texts, question):
        calls.append(question)
        if question is wt.STALE_Q:
            return [1.0 if old_marker in t else 0.0 for t in texts]
        if question is wt.STILL_Q:
            return [1.0 if still_marker in t else 0.0 for t in texts]
        return [1.0] * len(texts)  # page relevance
    ask.calls = calls
    return ask


CHANGE = {"type": "rename", "subject": "병원 일정 종류 이름", "old": "HOSPITAL_SCHEDULE", "new": "CLINIC_WIDE_SCHEDULE",
          "instruction": "병원 전체 일정 종류 이름을 CLINIC_WIDE_SCHEDULE 로 바꾼다",
          "user_quote": "HOSPITAL_SCHEDULE 을 CLINIC_WIDE_SCHEDULE 로 바꾸기로 확정해"}


@pytest.fixture
def plans(tmp_path, monkeypatch):
    monkeypatch.setenv("LH_KNOWLEDGE_PLAN_DIR", str(tmp_path))
    return tmp_path


def seed_kinds(dsn, host, rows, groups=None):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        for i, (kind, t) in enumerate(rows, 1):
            g = (groups or {}).get(i, "D:g1")
            cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                        values (%s,%s,'D',%s,%s,%s,%s,%s::jsonb)""", (host, f"D-{i:03d}", i, t, kind, g,
                        json.dumps({"record_id": "D", "origin": "test", "evidence_refs": []})))
    for v in ("plain", "ctx-v1"):
        pg.backfill_embeddings(dsn, host, v)


def need_ask(state, texts, question):
    if question is wt.NEED_Q:
        return [1.0 if "종류" in t else 0.0 for t in texts]
    if question is wt.CONFLICT_Q:
        return [1.0 if "바꾸지 않는다" in t else 0.0 for t in texts]
    return [1.0] * len(texts)


ROWS = [("fact", "병원 일정 종류는 HOSPITAL_SCHEDULE 이다."), ("decision", "일정 종류 구분은 부서 요청으로 도입했다."),
        ("constraint", "일정 종류 이름은 바꾸지 않는다."), ("fact", "일정 색상은 부서별이다.")]


@pytest.fixture
def searches(tmp_path, monkeypatch):
    monkeypatch.setenv("LH_KNOWLEDGE_SEARCH_DIR", str(tmp_path))
    return tmp_path


def test_search_returns_needed_only_in_four_views_with_more_index(dsn, host, searches):
    seed_kinds(dsn, host, ROWS, groups={4: "D:g2"})  # D-004 is in another group -> not needed, not returned
    out = wt.search(dsn, host, "일정 종류를 바꾸려면?", ["일정 종류"], need_ask)
    doc = out["document"]
    assert out["relevant"] == 3 and "[D-004]" not in doc  # not needed -> not returned
    assert doc.index("## 이전 결정·이유 (1)") < doc.index("## 현재 구현 (1)") < doc.index("## 유지해야 할 것 (1)")
    assert out["more"]["domains"] == {"D": 1} and "- 영역 D: 1개 더" in doc and "충돌 후보" not in doc
    got = wt.more(dsn, out["search_id"], domain="D")
    assert got["count"] == 1 and "[D-004]" in got["document"]
    assert wt.more(dsn, out["search_id"], domain="D")["count"] == 0  # already returned
    with pytest.raises(ValueError):
        wt.more(dsn, out["search_id"])


def test_search_brings_group_siblings(dsn, host, searches):
    seed_kinds(dsn, host, ROWS)  # all four in group D:g1
    out = wt.search(dsn, host, "일정 종류를 바꾸려면?", ["일정 종류"], need_ask)
    assert out["relevant"] == 3 and out["returned"] == 4 and "[D-004]" in out["document"]


def test_search_flags_conflicts_with_planned_change(dsn, host, searches):
    seed_kinds(dsn, host, ROWS)
    out = wt.search(dsn, host, "일정 종류 이름 변경", ["일정 종류"], need_ask, change="일정 종류 이름을 CLINIC_WIDE_SCHEDULE 로 바꾼다")
    assert out["conflicts"] == 1 and "- ⚠ 충돌 후보 [D-003]" in out["document"]


def test_search_layer_guide_and_validation(dsn, host, searches):
    seed_kinds(dsn, host, ROWS)
    doc = wt.search(dsn, host, "일정 종류", ["일정 종류"], need_ask, layer="spec")["document"]
    assert "# 레이어 노트 작성 안내 (spec)" in doc and "knowledge_more(domain)" in doc and "구성 요소와 코드 경로" in doc
    assert "레이어 노트 작성 안내" not in wt.search(dsn, host, "일정 종류", ["일정 종류"], need_ask)["document"]
    with pytest.raises(ValueError):
        wt.search(dsn, host, "q", ["x"], need_ask, layer="bdd")
    with pytest.raises(ValueError):
        wt.search(dsn, host, "q", [], need_ask)


def test_fix_plan_lists_stale_with_rename_proposal(dsn, host, plans):
    seed(dsn, host, ["병원 일정 종류는 HOSPITAL_SCHEDULE 이다.", "부서 일정은 DEPARTMENT_SCHEDULE 이다."])
    out = wt.fix_plan(dsn, host, CHANGE, ["병원 일정 종류"], fake_ask())
    assert [i["alias"] for i in out["items"]] == ["D-001"]
    assert out["items"][0]["proposed_text"] == "병원 일정 종류는 CLINIC_WIDE_SCHEDULE 이다."
    assert (plans / f"{out['plan_id']}.json").exists()
    with pytest.raises(ValueError):
        wt.fix_plan(dsn, host, {**CHANGE, "user_quote": ""}, ["x"], fake_ask())


def test_fix_submit_requires_every_item(dsn, host, plans):
    seed(dsn, host, ["A HOSPITAL_SCHEDULE 이다.", "B HOSPITAL_SCHEDULE 이다."])
    plan = wt.fix_plan(dsn, host, CHANGE, ["일정"], fake_ask())
    assert len(plan["items"]) == 2
    out = wt.fix_submit(dsn, plan["plan_id"], [{"alias": "D-001", "action": "keep", "why": "x"}], fake_ask(),
                        lambda d: pytest.fail("must not record"), partition_key="D")
    assert not out["ok"] and out["errors"][0]["code"] == "E_MISSING" and out["errors"][0]["aliases"] == ["D-002"]


def test_fix_submit_guards_and_records(dsn, host, plans):
    seed(dsn, host, ["A HOSPITAL_SCHEDULE 이다.", "B HOSPITAL_SCHEDULE 이다.", "C HOSPITAL_SCHEDULE 이다.", "E HOSPITAL_SCHEDULE 이다."])
    plan = wt.fix_plan(dsn, host, CHANGE, ["일정"], fake_ask())
    recorded = []
    answers = [
        {"alias": "D-001", "action": "update", "text": "A CLINIC_WIDE_SCHEDULE 이다."},                 # accepted
        {"alias": "D-002", "action": "update", "text": "B HOSPITAL_SCHEDULE 이다 그리고 여전히."},       # still old
        {"alias": "D-003", "action": "update", "text": "C CLINIC_WIDE_SCHEDULE 이다. " + "덧붙임 " * 10},  # grew
        {"alias": "D-004", "action": "deprecate", "why": "병원 일정 종류 구분이 없어졌다"},                   # deprecated
    ]
    out = wt.fix_submit(dsn, plan["plan_id"], answers, fake_ask(), lambda d: recorded.append(d) or {"entry_id": "e"},
                        partition_key="D")
    assert out["ok"] and out["accepted"] == ["D-001"] and out["deprecated"] == ["D-004"]
    assert {r["alias"]: r["reason"] for r in out["retry"]} == {"D-002": "old content still present",
                                                                 "D-003": "text grew too much; change only the old part"}
    fact = recorded[0]["facts"][0]
    assert fact["operation"] == "update" and fact["fact"] == "A CLINIC_WIDE_SCHEDULE 이다."
    dep = recorded[0]["facts"][1]
    assert dep["operation"] == "deprecate" and dep["evidence_source"] == "user_confirmed" and "[D-004]" in dep["fact"]
    bad = wt.fix_submit(dsn, plan["plan_id"], [{**a, "why": ""} if a["action"] == "deprecate" else a for a in answers],
                        fake_ask(), lambda d: {"entry_id": "e"}, partition_key="D")
    assert not bad["ok"] and bad["errors"][0]["code"] == "E_WHY"
    assert fact["evidence_refs"][0]["quote"] == CHANGE["user_quote"] and fact["evidence_refs"][1]["quote"] == "A HOSPITAL_SCHEDULE 이다."


def test_fix_submit_through_real_record_path(dsn, host, plans, tmp_path, monkeypatch):
    """Accepted update passes the existing knowledge_cli.record lint (E_CLAIM_QUOTE covered by the two evidence refs)."""
    import knowledge_cli
    seed(dsn, host, ["병원 일정 종류는 HOSPITAL_SCHEDULE 이다."])
    plan = wt.fix_plan(dsn, host, CHANGE, ["일정"], fake_ask())
    out = wt.fix_submit(dsn, plan["plan_id"], [{"alias": "D-001", "action": "update", "text": plan["items"][0]["proposed_text"]}],
                        fake_ask(), lambda d: knowledge_cli.record(dsn, d), partition_key="D")
    assert out["ok"] and out["accepted"] == ["D-001"], out
    assert out["recorded"].get("state") == "proposed", out["recorded"]
    # Same cleanup as test_knowledge_cli: a leftover proposed entry would be picked up by other tests' worktime window.
    pg.abandon(dsn, out["recorded"]["work_unit_id"], "test: worker_tools fix_submit registration cleanup")


def test_fix_submit_precheck_returns_ledger_lint_as_retry(dsn, host, plans):
    """A rewrite with a derived identifier absent from the confirmed change is returned for retry, not accepted."""
    import knowledge_cli
    seed(dsn, host, ["병원 일정 종류는 HOSPITAL_SCHEDULE 이다.", "B HOSPITAL_SCHEDULE 이다."])
    plan = wt.fix_plan(dsn, host, CHANGE, ["일정"], fake_ask())
    answers = [{"alias": "D-001", "action": "update", "text": plan["items"][0]["proposed_text"]},
               {"alias": "D-002", "action": "update", "text": "B `ClinicWideScheduleType` 이다."}]
    recorded = []
    out = wt.fix_submit(dsn, plan["plan_id"], answers, fake_ask(), lambda d: recorded.append(d) or {"state": "proposed"},
                        partition_key="D", precheck=lambda f: knowledge_cli.lint_update_fact(dsn, host, f))
    assert out["accepted"] == ["D-001"], out
    r = {x["alias"]: x for x in out["retry"]}
    assert "ClinicWideScheduleType" in r["D-002"]["reason"] and r["D-002"]["lint"] == ["E_CLAIM_QUOTE"]
    assert [f["fact"] for f in recorded[0]["facts"]] == [plan["items"][0]["proposed_text"]]


def test_fix_plan_flags_unconfirmed_new_form_and_forms_quote_passes_lint(dsn, host, plans):
    """C07 case: confirmation paraphrases the new identifier -> needs_confirmation; forms_quote makes the rewrite pass the ledger lint."""
    import knowledge_cli
    seed(dsn, host, ["회차는 `date asc, createdAt asc` 순서로 재생한다."])
    change = {"type": "semantic", "subject": "회차 재생 순서", "old": "date asc, createdAt asc", "new": "date asc, id asc",
              "instruction": "정렬을 ID 오름차순으로", "user_quote": "날짜 오름차순 후 ID 오름차순으로 정렬하도록 바꿔 주세요"}
    ask = fake_ask(old_marker="createdAt", still_marker="createdAt")
    plan = wt.fix_plan(dsn, host, change, ["회차 순서"], ask)
    assert plan["needs_confirmation"] and "date asc, id asc" in plan["needs_confirmation"]["ask_user"]
    ans = [{"alias": "D-001", "action": "update", "text": "회차는 `date asc, id asc` 순서로 재생한다."}]
    pre = lambda f: knowledge_cli.lint_update_fact(dsn, host, f)
    out = wt.fix_submit(dsn, plan["plan_id"], ans, ask, lambda d: {"state": "x"}, partition_key="D", precheck=pre)
    assert out["accepted"] == [] and out["retry"][0]["lint"] == ["E_CLAIM_QUOTE"]
    plan2 = wt.fix_plan(dsn, host, {**change, "forms_quote": "정렬 표기는 `date asc, id asc` 로 쓴다"}, ["회차 순서"], ask)
    assert plan2["needs_confirmation"] is None
    out2 = wt.fix_submit(dsn, plan2["plan_id"], ans, ask, lambda d: {"state": "x"}, partition_key="D", precheck=pre)
    assert out2["accepted"] == ["D-001"], out2
    # a question is not a confirmation
    # (the ledger lint only needs SOME non-question user_utterance, so the tool itself must refuse a question here)
    with pytest.raises(ValueError, match="forms_quote is a question"):
        wt.fix_plan(dsn, host, {**change, "forms_quote": "`date asc, id asc` 로 쓰면 되지?"}, ["회차 순서"], ask)
