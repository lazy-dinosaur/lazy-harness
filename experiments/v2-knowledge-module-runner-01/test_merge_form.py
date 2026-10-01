"""merge_form: leaf-level three-way merge of operator facts, word-level fallback."""
import fact_form
import merge3
import merge_form

BASE = "IF 보관 위치가 없다 THEN 첨부 파일은 7일 보관된다 AND 첨부 파일은 목록에서 숨겨진다"


def test_condition_changed_on_one_side_and_a_result_rewritten_on_the_other_are_both_kept():
    theirs = "IF 보관 위치가 비활성 상태다 THEN 첨부 파일은 7일 보관된다 AND 첨부 파일은 목록에서 숨겨진다"
    mine = "IF 보관 위치가 없다 THEN 첨부 파일은 7일 보관된다 AND 관리자 화면에만 첨부 파일 아이콘이 남는다"
    text, err = merge_form.merge(BASE, theirs, mine)
    assert err is None and text == ("IF 보관 위치가 비활성 상태다 THEN 첨부 파일은 7일 보관된다 "
                                    "AND 관리자 화면에만 첨부 파일 아이콘이 남는다"), text


def test_different_result_sentences_rewritten_on_each_side_merge_where_words_conflict():
    theirs = "IF 보관 위치가 없다 THEN 첨부 파일은 30일 보관된다 AND 첨부 파일은 목록에서 숨겨진다"
    mine = "IF 보관 위치가 없다 THEN 첨부 파일은 7일 보관된다 AND 숨김 처리는 관리자에게만 알린다"
    text, err = merge_form.merge(BASE, theirs, mine)
    assert err is None and text == "IF 보관 위치가 없다 THEN 첨부 파일은 30일 보관된다 AND 숨김 처리는 관리자에게만 알린다", text


def test_same_sentence_changed_differently_is_a_conflict():
    theirs = BASE.replace("7일", "30일")
    mine = BASE.replace("7일", "14일")
    assert merge_form.merge(BASE, theirs, mine) == (None, "conflict")
    assert merge_form.merge(BASE, BASE.replace("없다", "잇다"), BASE.replace("없다", "비었다")) == (None, "conflict")


def test_added_and_removed_results_combine():
    theirs = BASE + " AND 첨부 파일은 읽기 전용이 된다"
    mine = "IF 보관 위치가 없다 THEN 첨부 파일은 7일 보관된다"
    text, err = merge_form.merge(BASE, theirs, mine)
    assert err is None and text == "IF 보관 위치가 없다 THEN 첨부 파일은 7일 보관된다 AND 첨부 파일은 읽기 전용이 된다", text


def test_plain_text_falls_back_to_word_merge_and_round_trip_holds():
    base, theirs, mine = "설명은 300자 이하다", "설명은 1000자 이하다", "설명은 300자 이하다"
    assert merge_form.merge(base, theirs, mine) == merge3.merge(base, theirs, mine)
    for t in (BASE, "IF A가 있다 EVEN IF B가 없다 THEN C는 열린다 EXCEPT WHEN D가 막는다 BECAUSE 규칙이다",
              "AFTER 캐시를 올렸다 THEN 빌드가 줄었다", "A는 된다 OR B는 된다"):
        assert fact_form.parse(merge_form.to_text(fact_form.parse(t))) == fact_form.parse(t), t
