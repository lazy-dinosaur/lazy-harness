"""Offline poller integration: only conftest's disposable loopback PG is used."""
import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

import poller
import store_pg as pg
from test_store_pg import fixture, host, judgement


def staged(dsn, owner, text):
    body = judgement(owner, text=text)
    entry = pg.register(dsn, body)
    assert pg.batch(dsn, 1, {entry["entry_id"]: [fixture(text=text)]})[0]["state"] == "provisional"
    pg.complete(dsn, body["work_unit_id"])
    return body


def fragments(dsn, owner):
    return [r for r in pg.rows(dsn, "fragment") if r["host_id"] == owner]


def answer(packet):
    return {"answers": fixture()["answers"]}


def test_backlog_and_oldest_first(dsn, host, tmp_path):
    older = staged(dsn, host, "older")
    newer = staged(dsn, host, "newer")
    entries = [pg.register(dsn, judgement(host, text=f"pending-{i}")) for i in range(3)]
    seen = []
    def judge(packet):
        seen.append(packet["state"]["candidate_fact"])
        return answer(packet)
    state = tmp_path / "state.json"
    outcome = poller.tick(dsn, judge, window=5, state=state)
    assert outcome["units"] == 2 and outcome["entries"] == 3
    assert seen[:2] == ["older", "newer"]
    assert len(fragments(dsn, host)) == 2
    assert {r["state"] for r in pg.rows(dsn, "ledger_entry") if str(r["entry_id"]) in
            {e["entry_id"] for e in entries}} == {"provisional"}
    # Deleting the hint cannot delete the DB queue: newly completed entries still recover.
    state.unlink()
    for entry in entries:
        pg.complete(dsn, str(entry["work_unit_id"]))
    assert poller.tick(dsn, judge, window=5, state=state)["units"] == 3
    assert len(fragments(dsn, host)) == 5
    assert poller.tick(dsn, judge, window=5, state=state)["units"] == 0
    assert len([r for r in pg.rows(dsn, "check_receipt") if r["stage"] == "digestion" and
                r["entry_id"] in {e["entry_id"] for e in entries}]) == 3


def test_completed_before_proposed_review_is_not_stranded(dsn, host, tmp_path):
    body = judgement(host, text="late review")
    entry = pg.register(dsn, body)
    pg.complete(dsn, body["work_unit_id"])
    state = tmp_path / "state.json"
    assert poller.tick(dsn, answer, state=state)["entries"] == 1
    assert next(r for r in pg.rows(dsn, "ledger_entry") if str(r["entry_id"]) == entry["entry_id"])["state"] == "eligible"
    assert poller.tick(dsn, answer, state=state)["units"] == 1
    assert len(fragments(dsn, host)) == 1


def test_interruption_and_corrupt_hint_recovery(dsn, host, tmp_path):
    body = staged(dsn, host, "interrupted")
    state = tmp_path / "state.json"
    calls = 0
    def fail_once(packet):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("offline interruption")
        return answer(packet)
    first = poller.tick(dsn, fail_once, state=state, now=100)
    assert first["skipped"]["failed"] == 1
    assert fragments(dsn, host) == []
    assert not [r for r in pg.rows(dsn, "absorption") if str(r["work_unit_id"]) == body["work_unit_id"]]
    assert poller.tick(dsn, fail_once, state=state, now=101)["skipped"]["backoff"] == 1
    state.write_text("{broken")
    assert poller.tick(dsn, fail_once, state=state, now=102)["units"] == 1
    assert calls == 2 and len(fragments(dsn, host)) == 1


def test_concurrent_ticks_one_lock(dsn, host, tmp_path):
    staged(dsn, host, "concurrent")
    entered, release = threading.Event(), threading.Event()
    def slow(packet):
        entered.set()
        assert release.wait(15)
        return answer(packet)
    state = tmp_path / "state.json"
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(poller.tick, dsn, slow, state=state)
        assert entered.wait(15)
        second = pool.submit(poller.tick, dsn, answer, state=state).result(timeout=15)
        release.set()
        first_result = first.result(timeout=15)
    assert second["skipped"]["lock_busy"] == 1 and second["units"] == 0
    assert first_result["units"] == 1 and len(fragments(dsn, host)) == 1
    assert len([r for r in pg.rows(dsn, "absorption") if r["entry_id"] and r["decision"] == "absorbed"
                and str(r["work_unit_id"]) == str(next(u["work_unit_id"] for u in pg.rows(dsn, "work_unit") if u["host_id"] == host))]) == 1


def test_backoff_stuck_and_skip_following_entry(dsn, host, tmp_path):
    bad = pg.register(dsn, judgement(host, text="bad"))
    good = pg.register(dsn, judgement(host, text="good"))
    calls = 0
    def judge(packet):
        nonlocal calls
        if packet["state"]["candidate_fact"] == "bad":
            calls += 1
            raise RuntimeError("offline failure")
        return answer(packet)
    state = tmp_path / "state.json"
    for instant in (0, 1, 10, 30, 70):
        poller.tick(dsn, judge, state=state, now=instant, max_attempts=3, base_delay=10)
    assert calls == 3
    hints = json.loads(state.read_text())
    assert hints["entry:" + bad["entry_id"]]["stuck"]
    assert poller.tick(dsn, judge, state=state, now=1000, max_attempts=3)["skipped"]["stuck"] >= 1
    assert calls == 3
    states = {str(r["entry_id"]): r["state"] for r in pg.rows(dsn, "ledger_entry")}
    assert states[bad["entry_id"]] == "proposed" and states[good["entry_id"]] == "provisional"
    state.unlink()
    assert poller.tick(dsn, answer, state=state, now=2000)["entries"] == 1
    assert {str(r["entry_id"]): r["state"] for r in pg.rows(dsn, "ledger_entry")}[bad["entry_id"]] == "provisional"


def test_item_and_unit_limits(dsn, host, tmp_path):
    staged(dsn, host, "first")
    staged(dsn, host, "second")
    pg.register(dsn, judgement(host, text="waiting"))
    result = poller.tick(dsn, answer, max_units=1, window=1, state=tmp_path / "state.json")
    # worktime has a reserved share of the window (astra stall review): one entry is checked even when digestion runs
    assert (result["units"], result["entries"]) == (1, 1)
    assert result["skipped"]["limit"] >= 1
    poller.tick(dsn, answer, max_units=2, window=3, state=tmp_path / "state.json")
    assert len(fragments(dsn, host)) >= 2


def test_prune_drops_hints_of_objects_no_longer_pending():
    hints = {"entry:a": {"attempts": 1}, "entry:b": {"attempts": 1}, "unit:u": {"stuck": True},
             "scan:s1": {"stuck": True}, "scan:s2": {"stuck": True}, "other": {"x": 1}}
    poller._prune(hints, entries=["a"], units=[], scans=["s2"])
    assert hints == {"entry:a": {"attempts": 1}, "scan:s2": {"stuck": True}, "other": {"x": 1}}


def test_stuck_scans_do_not_starve_healthy_ones(dsn, tmp_path, monkeypatch):
    """astra P13 cross-review: 250 blocked units (stuck + backoff) ahead of the healthy ones span two pages; the tick
    runs exactly SCAN_PER_TICK healthy scans in FIFO order and prunes the hint of a unit no longer unscanned."""
    blocked = [f"a{i:04d}" for i in range(250)]
    healthy = [f"b{i:04d}" for i in range(8)]
    done = "z-done"
    state = tmp_path / "hints.json"
    hints = {"scan:" + u: {"attempts": 5, "next": 0, "stuck": True} for u in blocked[:200]}
    hints.update({"scan:" + u: {"attempts": 1, "next": 10 ** 12, "stuck": False} for u in blocked[200:]})
    hints["scan:" + done] = {"attempts": 1, "next": 0, "stuck": False}
    state.write_text(json.dumps(hints))
    allu = blocked + healthy  # FIFO key order
    monkeypatch.setattr(poller, "_candidates", lambda dsn: ([], []))
    monkeypatch.setattr(poller.store_pg, "units_to_scan",
                        lambda dsn, limit=5, after=None, with_key=False:
                        [(u, u) for u in allu if after is None or u > after][:limit])
    monkeypatch.setattr(poller.store_pg, "unscanned", lambda dsn, ids: set(ids) & set(allu))
    ran = []
    monkeypatch.setattr(poller.store_pg, "scan_contradictions", lambda dsn, u, j: ran.append(u))
    poller.tick(dsn, judge=None, state=state, contra_judge=lambda *a: [])
    assert ran == healthy[:poller.SCAN_PER_TICK]
    left = json.loads(state.read_text())
    assert "scan:" + done not in left and all("scan:" + u in left for u in blocked)


def test_unit_larger_than_the_window_is_checked_then_digested(dsn, tmp_path, monkeypatch):
    """contra06 (2026-10-02): a completed unit with more entries than the window stalled forever: its eligible part was
    counted for digestion ('waiting'), which used the whole window, so the rest was never checked."""
    owner = "big-" + __import__("uuid").uuid4().hex[:8]
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("insert into knowledge.host(host_id,name,repo_locator) values (%s,%s,'t')", (owner, owner))
    unit = None
    for n in range(5):
        body = judgement(owner, text=f"큰 작업 사실 {n} 번이다")
        if unit:
            body["work_unit_id"] = unit
        unit = body["work_unit_id"]
        pg.register(dsn, body)
    pg.complete(dsn, unit)
    state = tmp_path / "s.json"
    judge = lambda packet: {"answers": fixture(text=packet["state"]["candidate_fact"])["answers"]}
    for _ in range(6):
        poller.tick(dsn, judge, window=2, state=state)
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select state::text from knowledge.ledger_entry where work_unit_id=%s", (unit,))
        assert {r[0] for r in cur.fetchall()} == {"absorbed"}


def test_a_unit_without_progress_gives_the_budget_back(dsn, tmp_path, monkeypatch):
    """astra stall review P1-1: a large unit that cannot commit (a change waits for a human) must not take every tick."""
    monkeypatch.setattr(poller, "_candidates", lambda dsn: ([{"work_unit_id": "big", "entries": 60},
                                                            {"work_unit_id": "small", "entries": 2}], []))
    ran = []

    def fake(dsn, unit, judge, **k):
        ran.append(unit)
        return {"status": "noop"} if unit == "big" else {"status": "absorbed"}
    monkeypatch.setattr(poller.digest_driver, "run_digestion", fake)
    state = tmp_path / "s.json"
    poller.tick(dsn, judge=None, window=50, state=state, now=1000)
    assert ran == ["big", "small"]  # the budget came back, the next unit ran
    ran.clear()
    poller.tick(dsn, judge=None, window=50, state=state, now=1001)
    assert ran == ["small"]  # the idle unit waits IDLE_DELAY
    hints = json.loads(state.read_text())
    assert hints["unit:big"]["idle"] and not hints["unit:big"]["stuck"]


def test_oversize_unit_is_reported_not_run(dsn, tmp_path, monkeypatch):
    monkeypatch.setattr(poller, "_candidates", lambda dsn: ([{"work_unit_id": "huge", "entries": 50 * poller.MAX_UNIT_FACTOR + 1}], []))
    monkeypatch.setattr(poller.digest_driver, "run_digestion", lambda *a, **k: (_ for _ in ()).throw(AssertionError("ran")))
    out = poller.tick(dsn, judge=None, window=50, state=tmp_path / "s.json")
    assert out["skipped"]["oversize"] == 1
