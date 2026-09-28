"""Fragment storage standard v1 gate (revised 2026-09-25 after write-01):
form-only issues are repaired (subject, keywords) or warned (evidence count); meaning/trust codes still block."""
import runner

BASE = {"operation": "add", "fact": "지식 모듈의 소화자는 완료 신호 뒤에만 흡수한다.", "kind": "fact",
        "subject": "지식 모듈의 소화자", "evidence_source": "official_doc", "evidence_quote": "q", "keywords": [],
        "evidence_refs": [{"type": "official_doc", "locator": "spec#5", "quote": "q"}]}


def codes(**change):
    return {e["code"] for e in runner.lint_fact({**BASE, **change})["errors"]}


def warns(**change):
    return {e["code"] for e in runner.lint_fact({**BASE, **change})["warnings"]}


def test_ok():
    assert codes() == set()


def test_subject_still_required_by_lint_but_repaired_by_normalize():
    assert "E_SUBJECT" in codes(subject="")
    fixed, repairs = runner.normalize_fact({**BASE, "subject": "소화자 동작 방식"})
    assert fixed["subject"] in fixed["fact"] and repairs and repairs[0]["field"] == "subject"
    assert runner.lint_fact(fixed)["ok"]
    assert fixed["fact"] == BASE["fact"]  # meaning untouched


def test_keywords_repaired_not_rejected():
    fixed, _ = runner.normalize_fact({**BASE, "fact": "`hospitalId` 는 호출자 입력으로 믿지 않는다.", "subject": "hospitalId",
                                      "keywords": ["권한 근거"], "evidence_quote": "`hospitalId` 는 권한 근거가 아니다"})
    assert fixed["keywords"] == ["권한 근거"]  # valid keywords are kept as written, no additions
    fixed_empty, _ = runner.normalize_fact({**BASE, "fact": "`hospitalId` 는 호출자 입력으로 믿지 않는다.", "subject": "hospitalId", "keywords": []})
    assert "hospitalId" in fixed_empty["keywords"]  # empty keywords are filled from identifiers
    fixed2, _ = runner.normalize_fact({**BASE, "keywords": ["없는 말"]})
    assert "없는 말" not in fixed2["keywords"] and runner.lint_fact(fixed2)["ok"]


def test_evidence_count_is_warning_why_still_blocks():
    assert codes(kind="decision", why="이유") == set() and "E_EVIDENCE_COUNT" in warns(kind="decision", why="이유")
    assert "E_WHY" in codes(kind="decision")
    assert "E_EVIDENCE_COUNT" in warns(kind="constraint")


def test_user_confirmed_needs_non_question_quote():
    q = lambda quote: codes(evidence_source="user_confirmed", evidence_refs=[{"type": "user_utterance", "locator": "c", "quote": quote}])
    for question in ("그래야 다른 세션들이 오해하지 않지 그지?", "이거 pi 꺼잔아", "맞지?", "그렇게 할까"):
        assert "E_USER_REF" in q(question), question
    for confirmed in ("좋아 그렇게 하도록 하자", "좋아 추천대로 하자", "a로 하자 그러면"):
        assert "E_USER_REF" not in q(confirmed), confirmed
    assert "E_USER_REF" in codes(evidence_source="user_confirmed")


def test_user_confirmed_every_cited_utterance_must_be_non_question():
    """Revision 3 (2026-09-27): a question cited next to a confirmation no longer passes (one non-question is not enough)."""
    ok = {"type": "user_utterance", "locator": "a", "quote": "좋아 그렇게 하도록 하자"}
    ask = {"type": "user_utterance", "locator": "b", "quote": "`date asc, id asc` 로 쓰면 되지?"}
    assert "E_USER_REF" not in codes(evidence_source="user_confirmed", evidence_refs=[ok, {**ok, "locator": "c", "quote": "a로 가자"}])
    assert "E_USER_REF" in codes(evidence_source="user_confirmed", evidence_refs=[ok, ask])
    assert "E_USER_REF" in codes(evidence_source="user_confirmed", evidence_refs=[ok, {**ok, "locator": "d", "quote": "  "}])
    # the same question cited as context under another evidence type is fine
    assert "E_USER_REF" not in codes(evidence_source="user_confirmed", evidence_refs=[ok, {**ask, "type": "observed_output"}])

def test_claim_quote_ignores_plain_acronyms_but_checks_code_identifiers():
    import worktime_driver as w
    base = {"reason": "r", "evidence_quote": "규칙을 갱신한다", "fact": ""}
    ok = runner.lint(w.build_packet({**base, "fact": "API 와 SSOT 의 Hard-stop 규칙을 갱신한다"}, "x"))
    assert not [e for e in ok["errors"] if e["code"] == "E_CLAIM_QUOTE"]
    for ident in ("`isEdit: true`", "AddScheduleModal", "hospitalId", "SUPPLY_UNIT_PRESET_NAMES", "src/main/unit.ts", "v1.6.14"):
        bad = runner.lint(w.build_packet({**base, "fact": f"{ident} 규칙을 갱신한다"}, "x"))
        assert [e for e in bad["errors"] if e["code"] == "E_CLAIM_QUOTE"], ident


def test_evidence_ref_type_must_match_db_check():
    strict = lambda **change: {e["code"] for e in runner.lint_fact({**BASE, **change}, strict_refs=True)["errors"]}
    assert "E_REF" in strict(evidence_refs=[{"type": "code", "locator": "a.py:1", "quote": "x"}])
    detail = next(e["detail"] for e in runner.lint_fact({**BASE, "evidence_refs": [{"type": "assistant_utterance", "locator": "s", "quote": "q"}]},
                                                        strict_refs=True)["errors"] if e["code"] == "E_REF")
    assert "code_test" in detail and "user_utterance" in detail
    assert "E_REF" in strict(evidence_refs=[{"type": "code_test", "locator": "", "quote": "x"}])
    assert "E_REF" not in strict(evidence_refs=[{"type": "code_test", "locator": "a.py:1", "quote": "x"}])
    assert "E_REF" not in codes(evidence_refs=["legacy string ref"])  # file store keeps string refs
    assert "allowed:" in next(e["detail"] for e in runner.lint_fact({**BASE, "kind": "rule"})["errors"] if e["code"] == "E_KIND")
