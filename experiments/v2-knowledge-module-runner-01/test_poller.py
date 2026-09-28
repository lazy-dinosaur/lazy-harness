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
    assert (result["units"], result["entries"]) == (1, 0)
    assert result["skipped"]["limit"] >= 1
    assert poller.tick(dsn, answer, max_units=2, window=3, state=tmp_path / "state.json")["entries"] == 1
    assert len(fragments(dsn, host)) == 2
