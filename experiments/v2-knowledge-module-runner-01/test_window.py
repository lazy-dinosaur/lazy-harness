"""Knowledge window: Jev-selected fragments only, constraints/decisions first, capped, overflow listed."""
import pytest

import window
import worker_tools as wt
from test_store_pg import host  # fixture
from test_worker_tools import seed_kinds

ROWS = [("fact", "일정 종류 목록은 설정 화면에서 고른다."), ("decision", "일정 종류 구분은 부서 요청으로 도입했다."),
        ("constraint", "일정 종류 이름은 바꾸지 않는다."), ("fact", "일정 색상은 부서별이다.")]


@pytest.fixture
def searches(tmp_path, monkeypatch):
    monkeypatch.setenv("LH_KNOWLEDGE_SEARCH_DIR", str(tmp_path))
    return tmp_path


def ask(state, texts, question):
    return [1.0 if "종류" in t else 0.0 for t in texts]


def test_window_orders_constraints_first_and_skips_irrelevant(dsn, host, searches):
    seed_kinds(dsn, host, ROWS)
    out = window.build(dsn, host, "일정 종류 화면을 고친다", ["일정 종류"], ask)
    assert out["relevant"] == 3 and out["dropped"] == 0
    assert "색상" not in out["text"] and out["text"].startswith("[knowledge-window]")
    assert out["aliases"][:2] == ["D-003", "D-002"]  # constraint, then decision
    assert out["tokens"] < 1000


def test_window_cap_lists_overflow(dsn, host, searches):
    rows = [("fact", f"일정 종류 규칙 {i} " + "가" * 300) for i in range(12)] + [("constraint", "일정 종류 이름은 바꾸지 않는다.")]
    seed_kinds(dsn, host, rows)
    out = window.build(dsn, host, "일정 종류", ["일정 종류"], ask, cap=800)
    assert out["dropped"] > 0 and "D-013" in out["aliases"]  # the constraint survives the cap
    assert f"못 담은 조각 {out['dropped']}개" in out["text"] and "search_id:" in out["text"]
    assert out["tokens"] <= 900


def test_window_empty_when_nothing_relevant(dsn, host, searches):
    seed_kinds(dsn, host, [("fact", "색상은 부서별이다.")])
    assert window.build(dsn, host, "일정 종류", [], ask)["text"] == ""
    with pytest.raises(ValueError):
        window.build(dsn, host, " ", [], ask)
