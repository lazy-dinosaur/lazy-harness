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
    for _ in range(20):  # judge calls are spread over ticks within the window budget
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


def test_large_unit_is_judged_over_passes_and_committed_once(dsn, tmp_path):
    """contra07 (2026-10-02): a 220-fact unit exceeded the old 4 x window cap and was never digested. Judge calls are
    spread over ticks (saved as digestion receipts); the commit happens once, in the pass that has every judgement."""
    owner = "large-" + __import__("uuid").uuid4().hex[:8]
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("insert into knowledge.host(host_id,name,repo_locator) values (%s,%s,'t')", (owner, owner))
    unit = None
    for n in range(9):
        body = judgement(owner, text=f"대형 작업 사실 {n} 번이다")
        if unit:
            body["work_unit_id"] = unit
        unit = body["work_unit_id"]
        pg.register(dsn, body)
    pg.complete(dsn, unit)
    calls = []

    def judge(packet):
        calls.append(packet["state"].get("candidate_fact"))
        return {"answers": fixture(text=packet["state"]["candidate_fact"])["answers"]}
    state = tmp_path / "s.json"
    absorbed_after = []
    for _ in range(12):
        poller.tick(dsn, judge, window=4, state=state)
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("select count(*) from knowledge.fragment where host_id=%s", (owner,))
            absorbed_after.append(cur.fetchone()[0])
    assert absorbed_after[-1] == 9
    assert all(n in (0, 9) for n in absorbed_after), absorbed_after  # never a part of the unit (one commit)
    mine = [c for c in calls if c and c.startswith("대형 작업")]
    assert len(mine) == 18, mine  # 9 worktime checks + 9 digestion judgements: each judged once, reused at the commit


def test_partial_without_progress_waits_and_gives_the_budget_back(dsn, tmp_path, monkeypatch):
    """astra big review: a large unit whose saved judgements stop matching (the canon moved) must not hold every tick."""
    monkeypatch.setattr(poller, "_candidates", lambda dsn: ([{"work_unit_id": "big", "entries": 300},
                                                            {"work_unit_id": "small", "entries": 2}], []))
    ran = []

    def fake(dsn, unit, judge, **k):
        ran.append((unit, k.get("budget")))
        return {"status": "partial", "judged": 5, "remaining": 100} if unit == "big" else {"status": "absorbed"}
    monkeypatch.setattr(poller.digest_driver, "run_digestion", fake)
    state = tmp_path / "s.json"
    poller.tick(dsn, judge=None, window=50, state=state, now=1000)
    assert ran[0][0] == "big" and ran[0][1] < 40 and ("small", 2) in ran  # half the budget, the small unit still ran
    ran.clear()
    poller.tick(dsn, judge=None, window=50, state=state, now=1001)
    assert ran[0][0] == "big"
    hints = json.loads(state.read_text())
    assert hints["unit:big"]["idle"]  # remaining did not drop: wait IDLE_DELAY
    ran.clear()
    poller.tick(dsn, judge=None, window=50, state=state, now=1002)
    assert [u for u, _ in ran] == ["small"]


def test_workers_judge_units_at_once_and_commit_each_once(dsn, host, tmp_path):
    """Migration parallel load (2026-10-03): with workers=4 several units are judged at the same time (the judge sees
    overlapping calls) and every unit is still digested exactly once, like workers=1."""
    import time
    # unrelated topics: an add whose existing-knowledge excerpt changes (a similar fact landed first) is judged again --
    # that is the point of the excerpt check, so this test uses facts that do not show up in each other's excerpt
    topics = ["사과 재고는 매일 집계한다", "버스 노선은 주말에 줄인다", "환불 요청은 영업일 기준 처리한다",
              "서버 로그는 30일 보관한다", "회의실 예약은 하루 전 마감한다", "택배 라벨은 흑백으로 인쇄한다"]
    bodies = [staged(dsn, host, t) for t in topics]
    pending = [pg.register(dsn, judgement(host, text=f"pending-par-{i}")) for i in range(4)]
    live, peak, lock = [0], [0], threading.Lock()

    def judge(packet):
        with lock:
            live[0] += 1
            peak[0] = max(peak[0], live[0])
        time.sleep(0.2)
        with lock:
            live[0] -= 1
        return answer(packet)
    state = tmp_path / "state.json"
    out = poller.tick(dsn, judge, window=20, state=state, workers=4)
    assert out["units"] == 6 and out["entries"] == 4 and out["skipped"]["failed"] == 0, out
    assert peak[0] >= 2  # judged at once
    # an add whose excerpt changed because another landed first is judged again on a later tick (the offline
    # embedding has no relevance floor, so in this tiny canon every new fact enters the others' excerpts)
    for _ in range(8):
        if len(fragments(dsn, host)) >= len(topics):
            break
        poller.tick(dsn, judge, window=20, state=state, workers=4, now=time.time() + 10 ** 6)
    texts = sorted(r["text"] for r in fragments(dsn, host))
    assert texts == sorted(topics)  # each digested exactly once
    assert {r["state"] for r in pg.rows(dsn, "ledger_entry") if str(r["entry_id"]) in
            {e["entry_id"] for e in pending}} == {"provisional"}
    assert poller.tick(dsn, judge, window=20, state=state, workers=4)["units"] == 0


def test_workers_must_be_positive(dsn, tmp_path):
    with pytest.raises(ValueError):
        poller.tick(dsn, answer, state=tmp_path / "s.json", workers=0)


def test_an_add_whose_excerpt_changed_meanwhile_is_judged_again(dsn, host, tmp_path):
    """astra parallel review P2: both units judged on the same (empty) excerpt at once (barrier); the second commit
    sees a changed excerpt -> 'canon changed' recheck without counting toward stuck; next tick judges it against the
    new excerpt and both end digested."""
    import time
    staged(dsn, host, "주차 요금은 시간당 1000원이다")
    staged(dsn, host, "주차 제한은 3시간이다")
    barrier = threading.Barrier(2, timeout=10)
    packets = []

    def judge(packet):
        packets.append(packet["state"].get("existing_records_excerpt"))
        if len(packets) <= 2:
            barrier.wait()
        return answer(packet)
    state = tmp_path / "state.json"
    out = poller.tick(dsn, judge, window=20, state=state, workers=2)
    assert out["skipped"]["failed"] == 0
    hints = json.loads(state.read_text())
    unit_hints = [v for k, v in hints.items() if k.startswith("unit:")]
    assert len(fragments(dsn, host)) == 1 and len(unit_hints) == 1
    assert unit_hints[0]["attempts"] == 0 and unit_hints[0]["conflicts"] == 1 and not unit_hints[0]["stuck"]
    poller.tick(dsn, judge, window=20, state=state, workers=2, now=time.time() + 10 ** 6)
    assert len(fragments(dsn, host)) == 2
    assert packets[-1] != packets[0]  # judged again against the excerpt that now holds the first fact


def test_history_moved_but_same_excerpt_commits_in_the_same_tick(dsn, host, tmp_path, monkeypatch):
    """astra parallel review P2: the excerpt check itself -- the host history moves between judging and commit, the
    excerpt rebuilt under the lock is unchanged, so the add commits without a recheck."""
    import worktime_driver
    monkeypatch.setattr(worktime_driver, "existing_excerpt", lambda *a, **k: "이 host 의 정본에 관련 조각이 없다.")
    staged(dsn, host, "사과 재고는 매일 집계한다")
    staged(dsn, host, "버스 노선은 주말에 줄인다")
    barrier = threading.Barrier(2, timeout=10)

    def judge(packet):
        barrier.wait()
        return answer(packet)
    out = poller.tick(dsn, judge, window=20, state=tmp_path / "s.json", workers=2)
    assert out["skipped"]["failed"] == 0 and len(fragments(dsn, host)) == 2


def test_entries_of_one_unit_split_across_workers_are_all_checked(dsn, host, tmp_path):
    """astra parallel review P2: worktime chunks split one unit's entries across threads; each is checked once."""
    body = judgement(host, text="첫 번째 사실은 켜진다")
    entries = [pg.register(dsn, body)]
    for i in range(5):
        b2 = judgement(host, text=f"다음 사실 {i} 은 켜진다")
        b2["work_unit_id"] = body["work_unit_id"]
        entries.append(pg.register(dsn, b2))
    out = poller.tick(dsn, answer, window=20, state=tmp_path / "s.json", workers=3)
    assert out["entries"] == 6 and out["skipped"]["failed"] == 0
    states = {r["state"] for r in pg.rows(dsn, "ledger_entry") if str(r["entry_id"]) in {e["entry_id"] for e in entries}}
    assert states == {"provisional"}


def test_conflict_cap_is_kept_across_backoff():
    """astra parallel review r2: after MAX_CONFLICTS immediate retries a unit stays on the normal backoff; the conflict
    count is not reset by a failure."""
    hints = {"unit:u": {"attempts": 0, "next": 0, "stuck": False, "conflicts": poller.MAX_CONFLICTS}}
    poller._failure(hints, "unit:u", 1000.0, 5, 30)
    assert hints["unit:u"]["conflicts"] == poller.MAX_CONFLICTS and hints["unit:u"]["next"] > 1000.0


def test_parallel_scans_record_contradictions_once(dsn, host, tmp_path, monkeypatch):
    """astra parallel review r3/r4: both units absorbed first, then exactly their two scans are run in one batch and must
    meet at a barrier (judged at the same time); each side is logged exactly once, both directions."""
    import time
    staged(dsn, host, "주차 요금은 시간당 1000원이다")
    staged(dsn, host, "주차 요금은 시간당 2000원이다")
    state = tmp_path / "s.json"
    for _ in range(6):  # digest both, no canon judge yet
        poller.tick(dsn, answer, window=20, state=state, workers=2, now=time.time() + 10 ** 6)
    assert len(fragments(dsn, host)) == 2
    units = [str(r["work_unit_id"]) for r in pg.rows(dsn, "work_unit") if r["host_id"] == host]  # str, as _runnable_scans
    # isolate the batch: only this host's two units (the shared test DB holds other hosts' unscanned units)
    monkeypatch.setattr(poller, "_runnable_scans", lambda *a, **k: list(units))
    barrier = threading.Barrier(2, timeout=10)
    met, first = [], set()

    def contra(state_, texts, q, criteria=None):
        key = str(state_.get("fact", ""))
        if key not in first:
            first.add(key)
            barrier.wait()  # raises BrokenBarrierError if the two scans did not run at the same time
            met.append(key)
        if criteria:
            return [{"probabilities": {"contradiction": 0.0, "exception": 0.0, "neither": 1.0}} for _ in texts]
        return [{"noul": 0.9 if ("1000" in t) != ("1000" in key) else 0.0} for t in texts]
    poller.tick(dsn, answer, window=20, state=state, workers=2, contra_judge=contra, now=time.time() + 10 ** 6)
    assert len(met) == 2  # both scans reached the barrier together
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select q.reason from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
                       where e.host_id=%s and q.rule_id='canon_contradiction'""", (host,))
        sides = sorted((json.loads(r[0])["alias"], json.loads(r[0])["with"]) for r in cur.fetchall())
    assert len(sides) == 2 and sides[0] == tuple(reversed(sides[1])), sides  # each side once, both directions

def test_conflict_count_survives_a_partial_pass(dsn, tmp_path, monkeypatch):
    """astra parallel review r3/r4: needs_recheck(canon changed) -> partial -> needs_recheck on consecutive ticks keeps
    counting toward MAX_CONFLICTS, and at the cap the normal backoff applies."""
    import time
    import digest_driver
    unit = {"work_unit_id": "00000000-0000-0000-0000-0000000000aa", "entries": 3}
    monkeypatch.setattr(poller, "_candidates", lambda d: ([unit], []))
    monkeypatch.setattr(poller, "_prune", lambda *a, **k: None)
    seq = iter([{"status": "needs_recheck", "why": "canon changed (history)"},
                {"status": "partial", "judged": 1, "remaining": 2},
                {"status": "needs_recheck", "why": "canon changed (history)"}])
    monkeypatch.setattr(digest_driver, "run_digestion", lambda *a, **k: next(seq))
    state = tmp_path / "s.json"
    key = "unit:" + unit["work_unit_id"]
    counts = []
    for _ in range(3):
        poller.tick(dsn, answer, window=20, state=state, now=time.time() + 10 ** 6)
        counts.append(json.loads(state.read_text())[key].get("conflicts"))
    assert counts == [1, 1, 2]
    monkeypatch.setattr(digest_driver, "run_digestion", lambda *a, **k: {"status": "needs_recheck", "why": "canon changed (history)"})
    hints = json.loads(state.read_text())
    hints[key]["conflicts"] = poller.MAX_CONFLICTS
    state.write_text(json.dumps(hints))
    now = time.time() + 10 ** 6
    poller.tick(dsn, answer, window=20, state=state, now=now)
    h = json.loads(state.read_text())[key]
    assert h["attempts"] == 1 and h["next"] > now and h["conflicts"] == poller.MAX_CONFLICTS  # backoff, cap kept
