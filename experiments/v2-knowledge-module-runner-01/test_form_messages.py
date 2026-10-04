"""real01 (2026-10-03, user 'a'): the two shapes parents wrote most are refused with a message that says how to
rewrite them (automatic splitting was dropped after the astra split review: it changed meanings)."""
import fact_form


def test_plain_and_rule_says_record_two_facts():
    errs = fact_form.check("보고서는 기본을 보존한다 AND IF 보고서는 single-line을 쓴다 THEN 보고서는 한 줄로 표시한다")
    assert "사실 두 개로 따로 기록" in errs[0] and "AND 뒤에 문장이 없다" not in errs
    for op in ("BEFORE", "AFTER"):
        e2 = fact_form.check(f"보고서는 기본을 보존한다 AND {op} 저장 THEN 보고서는 잠긴다")
        assert "사실 두 개" in e2[0], (op, e2)


def test_a_rule_then_another_rule_asks_to_keep_the_condition_scope():
    errs = fact_form.check("IF A는 켜진다 THEN B는 꺼진다 AND IF C는 켜진다 THEN D는 꺼진다")
    assert "조건 범위" in errs[0] and "조건 없는 사실" not in errs[0]


def test_operator_words_in_code_are_not_advised_and_other_errors_stay():
    # no rewrite advice for operator words inside code (check() itself still splits on them -- a known gap of split())
    assert not any("사실 두 개" in e or "규칙 둘" in e for e in fact_form.check("설명은 `A AND IF c THEN r` 이다"))
    e = fact_form.check("A는 켜진다 AND IF B는 꺼진다")  # no THEN: that error stays next to the advice
    assert "IF 뒤에 THEN 결과가 없다" in e, e
    e = fact_form.check("EVEN IF A는 켜진다 THEN B는 꺼진다 AND")
    assert "맨 앞 EVEN IF" in e[0] and "AND 뒤에 문장이 없다" in e


def test_leading_even_if_says_how_to_keep_the_guarantee():
    errs = fact_form.check("EVEN IF 장치는 비로그인 상태다 THEN 장치는 출력 경로를 유지한다")
    assert "반드시 '항상'" in errs[0] and "IF 조건 THEN 결과" in errs[0]
    # the suggested rewrite is a plain fact that says 'always', so a conditional opposite is compared, not an exception
    rewrite = fact_form.parse("장치는 비로그인 상태여도 항상 출력 경로를 유지한다")
    assert fact_form.check("장치는 비로그인 상태여도 항상 출력 경로를 유지한다") == []
    assert fact_form.relation(rewrite, fact_form.parse("IF 장치는 비로그인 상태다 THEN 장치는 출력 경로를 막는다")) == "compare"


def test_other_errors_keep_their_messages():
    assert fact_form.check("A는 켜진다 AND") == ["AND 뒤에 문장이 없다"]
    assert fact_form.check("IF A는 켜진다 THEN B는 꺼진다") == []


def test_a_time_rule_keeps_its_time_relation_in_the_advice():
    e = fact_form.check("IF A는 켜진다 THEN B는 꺼진다 AND BEFORE 저장 THEN C는 잠긴다")
    assert "BEFORE x THEN y" in e[0] and "IF 앞조건 AND 뒤조건" not in e[0]
    e = fact_form.check("BEFORE 저장 THEN C는 잠긴다 AND IF A는 켜진다 THEN B는 꺼진다")
    assert "BEFORE x THEN y" in e[0]


def test_every_joined_rule_needs_its_own_then():
    e = fact_form.check("A는 켜진다 AND IF B는 켜진다 THEN C는 꺼진다 AND IF D는 켜진다")
    assert "IF 뒤에 THEN 결과가 없다" in e, e
