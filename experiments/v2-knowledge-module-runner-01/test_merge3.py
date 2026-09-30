"""merge3: word-level three-way merge (git semantics)."""
import merge3

BASE = "describe 는 앞뒤 공백 제거 후 설명은 300자 이하로 제한한다."


def test_non_overlapping_edits_are_both_kept():
    theirs = "describe 는 앞뒤 공백과 줄바꿈 제거 후 설명은 300자 이하로 제한한다."
    mine = "describe 는 앞뒤 공백 제거 후 설명은 1000자 이하로 제한한다."
    text, err = merge3.merge(BASE, theirs, mine)
    assert err is None and text == "describe 는 앞뒤 공백과 줄바꿈 제거 후 설명은 1000자 이하로 제한한다."


def test_same_place_different_value_is_a_conflict():
    theirs = BASE.replace("300", "800")
    mine = BASE.replace("300", "1000")
    assert merge3.merge(BASE, theirs, mine) == (None, "conflict")


def test_trivial_cases():
    mine = BASE.replace("300", "1000")
    assert merge3.merge(BASE, BASE, mine) == (mine, None)
    assert merge3.merge(BASE, mine, mine) == (mine, None)
    assert merge3.merge(BASE, mine, BASE) == (mine, None)
