"""Domain routing and management (domain_router) — pure routing plus DB-backed management/digestion."""
import pytest

import domain_router as dr
import store_pg as pg
from test_store_pg import host  # fixture


def D(**kw):
    return {k: {"description": v, "status": "active", "merged_into": None} for k, v in kw.items()}


def choose_fixed(probs):
    calls = []
    def choose(text, options):
        calls.append(options)
        return {k: probs.get(k, 0.0) for k in options}
    choose.calls = calls
    return choose


def test_exact_name_skips_jev():
    c = choose_fixed({})
    assert dr.route(D(예약="예약·시간"), " 예약 ", "x", c) == ("예약", "exact") and c.calls == []


def test_first_domain_is_created():
    assert dr.route({}, "예약", "x", choose_fixed({})) == ("예약", "new")


def test_routes_to_existing_domain_instead_of_new_name():
    # worker wrote 'reservation' but Jev says it is the existing '예약'
    # options are the active names sorted: d0 = 예약, d1 = 채팅
    out = dr.route(D(예약="예약", 채팅="채팅"), "reservation", "x", choose_fixed({"d0": .8, "d1": .1, "none": .1}))
    assert out == ("예약", "routed")


def test_new_only_when_none_is_confident():
    doms = D(예약="예약", 채팅="채팅")
    assert dr.route(doms, "재고", "x", choose_fixed({"none": .8, "d0": .1, "d1": .1})) == ("재고", "new")
    # ambiguous 'none' -> best existing domain, not a new scattered name
    assert dr.route(doms, "재고", "x", choose_fixed({"none": .5, "d0": .3, "d1": .2})) == ("예약", "routed")


def test_merged_name_resolves_to_survivor():
    doms = D(예약="예약")
    doms["reservation"] = {"description": "", "status": "retired", "merged_into": "예약"}
    assert dr.route(doms, "reservation", "x", choose_fixed({})) == ("예약", "exact")


@pytest.mark.parametrize("description", [None, "", "가" * 201, "가" * 300, "가" * 301])
def test_ensure_description_limit_and_no_overwrite(dsn, host, description):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        dr.ensure(cur, host, "예약", description)
        expected = (description or "")[:300]
        assert dr.load(cur, host)["예약"]["description"] == expected
        dr.ensure(cur, host, "예약", "새 설명")
        assert dr.load(cur, host)["예약"]["description"] == expected


def test_management_and_backfill(dsn, host):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        dr.ensure(cur, host, "예약", "예약 시간 규칙")
        dr.ensure(cur, host, "reservation", "")
        dr.merge(cur, host, "reservation", "예약")
        with pytest.raises(ValueError):
            dr.merge(cur, host, "예약", "reservation")  # cycle
        rows = {r["domain"]: r for r in dr.list_domains(cur, host)}
        assert rows["reservation"]["status"] == "retired" and rows["reservation"]["merged_into"] == "예약"
        assert dr.resolve(dr.load(cur, host), "reservation") == "예약"
        dr.ensure(cur, host, "채팅", "")
        dr.retire(cur, host, "채팅")
        assert dr.load(cur, host)["채팅"]["status"] == "retired"


def test_route_unit_ambiguous_creates_worker_name():
    doms = D(예약="예약", 채팅="채팅")
    # ambiguous (best existing .45) -> the worker's own name, not the nearest existing domain
    assert dr.route_unit(doms, "일정 관리", ["a", "b"], choose_fixed({"d0": .45, "d1": .1, "none": .45})) == ("일정 관리", "new")
    # confident existing -> join it
    assert dr.route_unit(doms, "reservation", ["a"], choose_fixed({"d0": .8, "d1": .1, "none": .1})) == ("예약", "routed")
    # exact name -> no Jev call
    c = choose_fixed({})
    assert dr.route_unit(doms, "채팅", ["a"], c) == ("채팅", "exact") and c.calls == []


def test_route_unit_asks_once_with_all_facts():
    c = choose_fixed({"none": .9})
    dr.route_unit(D(예약="예약"), "재고", ["첫 사실", "둘째 사실"], c)
    assert len(c.calls) == 1


def test_route_unit_confirms_before_creating():
    doms = D(예약="예약", 채팅="채팅")
    ambiguous = choose_fixed({"d0": .45, "d1": .1, "none": .45})
    asked = []
    def confirm(text, candidates):
        asked.append(candidates)
        return [0.9 if c.startswith("예약") else 0.1 for c in candidates]
    assert dr.route_unit(doms, "일정 관리", ["a"], ambiguous, confirm=confirm) == ("예약", "confirmed")
    assert len(asked) == 1 and len(asked[0]) == 2 and asked[0][0].startswith("예약")  # closest first, at most two
    no = lambda text, candidates: [0.2] * len(candidates)
    assert dr.route_unit(doms, "일정 관리", ["a"], ambiguous, confirm=no) == ("일정 관리", "new")
    # a confident route or an exact name never asks
    boom = lambda text, candidates: (_ for _ in ()).throw(AssertionError("must not ask"))
    assert dr.route_unit(doms, "reservation", ["a"], choose_fixed({"d0": .8, "none": .1}), confirm=boom) == ("예약", "routed")
    assert dr.route_unit(doms, "채팅", ["a"], choose_fixed({}), confirm=boom) == ("채팅", "exact")
