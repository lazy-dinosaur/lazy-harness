"""dedup: same-sentence test used by digestion (no DB, no network)."""
import dedup


def test_same_sentence_ignoring_filler_and_ending():
    assert dedup.find_duplicate("도메인 설명 길이는 생성·수정 모두 최대 1000자이다.", ["x", "도메인 설명 길이는 생성·수정 모두 1000자"]) == 1
    assert dedup.find_duplicate("`ensure` 는 1000자로 자른다.", ["ensure는 1000자로 자른다"]) == 0


def test_near_but_different_facts_are_kept():
    base = "도메인 설명은 생성 때 1000자로 자른다"
    for other in ("도메인 설명은 수정 때 1000자로 자른다", "도메인 설명은 생성 때 1000자로 자르지 않는다",
                  "도메인 설명은 생성 때 300자로 자른다", "도메인 이름은 생성 때 1000자로 자른다"):
        assert dedup.find_duplicate(base, [other]) is None
    assert dedup.find_duplicate("", [""]) is None and dedup.find_duplicate("a", None) is None
