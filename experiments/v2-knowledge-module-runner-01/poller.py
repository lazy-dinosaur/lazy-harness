"""One DB-backed digestion tick. The JSON state is only a retry hint, never a queue."""
import argparse
import json
import os
import tempfile
import time
from pathlib import Path
from contextlib import closing

import digest_driver
import embed
import store_pg
import templates
import worktime_driver

LOCK_KEY = 0x4C484B4449473031  # LHKDIG01; reserved for this poller
SCAN_PER_TICK = 5
MAX_UNIT_FACTOR = 4  # a unit runs alone up to 4 x window entries (Jev calls, one transaction)
IDLE_DELAY = 60  # seconds before a unit that made no progress is tried again
RECHECK_PER_TICK = 2  # of SCAN_PER_TICK: at least 3 scans of newly absorbed units run every tick
DEFAULT_STATE = Path("~/.local/state/lazy-harness-v2/poller-state.json").expanduser()


def _load(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".poller-", delete=False) as file:
            name = file.name
            json.dump(state, file, sort_keys=True)
            file.flush()
            os.fsync(file.fileno())
        os.replace(name, path)
        name = None
        fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if name is not None:
            os.unlink(name)


def _blocked(state, key, now, skipped):
    hint = state.get(key, {})
    if hint.get("stuck"):
        skipped["stuck"] += 1
        return True
    if hint.get("next", 0) > now:
        skipped["backoff"] += 1
        return True
    return False


def _failure(state, key, now, max_attempts, base_delay):
    count = state.get(key, {}).get("attempts", 0) + 1
    state[key] = {"attempts": count, "next": now + base_delay * 2 ** (count - 1),
                  "stuck": count >= max_attempts}


def _prune(hints, entries, units, scans):
    """Drop hints whose object is no longer pending (2026-10-01: four 'stuck' scan hints and stale entry hints stayed
    after their units were scanned/absorbed, so the poller reported stuck items that no longer existed).
    scans = the set of hinted scan units that are still unscanned (exact DB check, store_pg.unscanned)."""
    live = ({"entry:" + e for e in entries} | {"unit:" + u["work_unit_id"] for u in units} | {"scan:" + s for s in scans})
    for key in [k for k in hints if k.split(":", 1)[0] in ("entry", "unit", "scan") and k not in live]:
        hints.pop(key, None)


def _runnable_scans(dsn, hints, now, skipped, budget):
    """Page through unscanned units in a stable order until `budget` runnable ones are found (stuck/backoff skipped)."""
    out, after = [], None
    while len(out) < budget:
        page = store_pg.units_to_scan(dsn, limit=200, after=after, with_key=True)
        if not page:
            break
        for uid_, _ in page:
            if len(out) < budget and not _blocked(hints, "scan:" + uid_, now, skipped):
                out.append(uid_)
        after = page[-1][1]
    return out


def _candidates(dsn):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select w.work_unit_id::text, count(*)::int as entries from knowledge.work_unit w
                    join knowledge.ledger_entry e on e.work_unit_id=w.work_unit_id
                    where w.status='completed' and e.state='eligible'
                    -- contra06 (2026-10-02): a unit with unchecked entries cannot digest yet ('waiting'); counting it used
                    -- the whole window every tick, so its own worktime never ran (150-entry unit stalled at 50 eligible)
                    and not exists (select 1 from knowledge.ledger_entry p where p.work_unit_id=w.work_unit_id
                                    and p.state='proposed')
                    group by w.work_unit_id,w.completed_at
                    order by w.completed_at,w.work_unit_id""")
        units = store_pg._rows(cur)
        cur.execute("""select entry_id::text from knowledge.ledger_entry where state='proposed'
                    order by created_at,entry_id""")
        entries = [r[0] for r in cur.fetchall()]
    return units, entries


def _pending_hosts(dsn, variant):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select distinct f.host_id from knowledge.fragment f
                    left join knowledge.fragment_embedding e on e.fragment_id=f.id and e.model_id=%s
                      and e.embed_variant=%s
                    where f.active and (e.fragment_id is null or e.revision<>f.revision)
                    order by f.host_id""", (embed.MODEL_ID, variant))
        return [r[0] for r in cur.fetchall()]


def tick(dsn, judge, *, utterance_judge=None, max_units=20, window=50, state=DEFAULT_STATE,
         max_attempts=5, base_delay=30, now=None, choose=None, confirm=None, contra_judge=None, subject_same=None):
    if min(max_units, window, max_attempts, base_delay) < 1:
        raise ValueError("limits and delay must be positive")
    now = time.time() if now is None else now
    result = {"units": 0, "entries": 0, "embeddings": 0, "stuck": 0,
              "skipped": {"lock_busy": 0, "backoff": 0, "stuck": 0, "limit": 0, "embedding_unavailable": 0, "failed": 0}}
    skipped = result["skipped"]
    # Session advisory lock is held by a dedicated connection across all short DB
    # transactions and HTTP calls. Connection loss releases it automatically.
    with closing(store_pg.driver.connect(dsn)) as lock_conn:
        lock_conn.autocommit = True
        with lock_conn.cursor() as cur:
            cur.execute("select pg_try_advisory_lock(%s)", (LOCK_KEY,))
            acquired = cur.fetchone()[0]
        if not acquired:
            skipped["lock_busy"] = 1
            return result
        try:
            hints = _load(state)
            units, entries = _candidates(dsn)
            hinted_scans = [k.split(":", 1)[1] for k in hints if k.startswith("scan:")]
            # astra P13 cross-review: scan hints are pruned by an exact DB check, never by a limited candidate list
            _prune(hints, entries, units, store_pg.unscanned(dsn, hinted_scans) if contra_judge is not None else hinted_scans)
            # worktime keeps a reserved share of the window so a digestion backlog never starves checking (astra stall review)
            reserve = max(1, window // 5)
            remaining = window - reserve
            for unit in units:
                # a unit is one commit: one larger than the window still runs when it is the first of the tick
                # (contra06: a 150-entry unit with window 50 was skipped forever), up to MAX_UNIT_FACTOR x window;
                # a bigger unit is reported (skipped.oversize), never run unbounded
                if unit["entries"] > MAX_UNIT_FACTOR * window:
                    skipped["oversize"] = skipped.get("oversize", 0) + 1
                    continue
                if result["units"] >= max_units or (remaining < unit["entries"] and result["units"] > 0):
                    skipped["limit"] += 1
                    continue
                key = "unit:" + unit["work_unit_id"]
                if _blocked(hints, key, now, skipped):
                    continue
                result["units"] += 1
                spent = min(remaining, unit["entries"])
                remaining -= spent
                try:
                    outcome = digest_driver.run_digestion(dsn, unit["work_unit_id"], judge, choose=choose, confirm=confirm,
                                                          same=subject_same)
                    # canon scans run below in one budgeted scheduler (astra P13 cross-review: they bypassed the budget)
                    if outcome["status"] in ("needs_review", "needs_recheck"):
                        _failure(hints, key, now, max_attempts, base_delay)
                    elif outcome["status"] in ("noop", "waiting"):
                        # no progress (e.g. a change waits for a human): give the budget back and wait before the next
                        # try without counting toward stuck (astra stall review P1-1)
                        result["units"] -= 1
                        remaining += spent
                        hints[key] = {"attempts": 0, "next": now + IDLE_DELAY, "stuck": False, "idle": True}
                    else:
                        hints.pop(key, None)
                except Exception:
                    skipped["failed"] += 1
                    _failure(hints, key, now, max_attempts, base_delay)
                _save(state, hints)
            if contra_judge is not None:  # review P1: retry canon scans that did not finish after their commit
                # one budget for all canon checks (astra 0012 review P2): rechecks first, scans take the rest
                try:  # 0012: contradictions whose side changed are judged again (an answer alone never resolves)
                    # rechecks get at most RECHECK_PER_TICK, so new units are always scanned (astra 0012 round 3)
                    rc = store_pg.recheck_contradictions(dsn, contra_judge, limit=RECHECK_PER_TICK)
                    result["rechecked"] = rc["rechecked"]
                    skipped["failed"] += rc["failed"]
                except Exception:
                    rc = {"rechecked": 0}
                    skipped["failed"] += 1
                for uid_ in _runnable_scans(dsn, hints, now, skipped, max(0, SCAN_PER_TICK - rc["rechecked"])):
                    key = "scan:" + uid_
                    try:
                        store_pg.scan_contradictions(dsn, uid_, contra_judge)
                        hints.pop(key, None)
                    except Exception:
                        _failure(hints, key, now, max_attempts, base_delay)
                _save(state, hints)
            remaining += reserve  # the reserved share is worktime's
            selected = []
            for entry_id in entries:
                if len(selected) >= remaining:
                    skipped["limit"] += 1
                    continue
                if not _blocked(hints, "entry:" + entry_id, now, skipped):
                    selected.append(entry_id)
            if selected:
                try:
                    outcome = worktime_driver.run_worktime(dsn, len(selected), judge,
                                    utterance_judge=utterance_judge, entry_ids=selected)
                    failures = {r["entry_id"] for r in outcome["failures"]}
                    statuses = {r["entry_id"]: r["state"] for r in outcome["results"]}
                    for entry_id in selected:
                        key = "entry:" + entry_id
                        if entry_id in failures or statuses.get(entry_id) in (None, "proposed", "review_queue"):
                            _failure(hints, key, now, max_attempts, base_delay)
                            skipped["failed"] += int(entry_id in failures)
                        else:
                            hints.pop(key, None)
                    result["entries"] = len(selected)
                except Exception:
                    skipped["failed"] += len(selected)
                    for entry_id in selected:
                        _failure(hints, "entry:" + entry_id, now, max_attempts, base_delay)
                _save(state, hints)
            # The remaining item budget also bounds optional embedding work.
            remaining -= len(selected)
            for variant in ("plain", "ctx-v1"):
                if remaining <= 0:
                    break
                try:
                    hosts = _pending_hosts(dsn, variant)
                    for host in hosts:
                        if remaining <= 0:
                            break
                        count = store_pg.backfill_embeddings(dsn, host, variant, limit=remaining)
                        result["embeddings"] += count
                        remaining -= count
                except embed.EmbeddingUnavailable:
                    skipped["embedding_unavailable"] += 1
                    break
            result["stuck"] = sum(bool(v.get("stuck")) for v in hints.values() if isinstance(v, dict))
            return result
        finally:
            with lock_conn.cursor() as cur:
                cur.execute("select pg_advisory_unlock(%s)", (LOCK_KEY,))


def _utterance_judge(fact):
    refs = fact.get("evidence_refs", [])
    utterance = next((r.get("quote") for r in refs if r.get("type") == "user_utterance" and r.get("quote")),
                     fact.get("evidence_quote", ""))
    packet = templates.utterance_packet(fact.get("reason", ""), utterance)
    return digest_driver._jev_judge(packet)["answers"]["utterance_status"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", required=True)
    parser.add_argument("--judge", choices=("jev",), default="jev")
    parser.add_argument("--max-units", type=int, default=20)
    parser.add_argument("--window", type=int, default=50)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args()
    import config
    try:
        cfg = config.require("db_url", "jev_api_key", "jev_base_url", "jev_model")
    except config.ConfigError as exc:
        parser.error(str(exc))  # names missing keys only, never values
    config.apply_embed_env(cfg)
    try:
        print(json.dumps(tick(cfg["db_url"], digest_driver._jev_judge,
                              utterance_judge=_utterance_judge, max_units=args.max_units,
                              window=args.window, state=args.state,
                              choose=__import__("domain_router").make_choose(cfg),
                              confirm=__import__("domain_router").make_confirm(cfg),
                              contra_judge=__import__("capture_audit").make_judge(cfg),
                              subject_same=__import__("worker_tools").make_ask(cfg))))
    except Exception as exc:
        # No exception message: driver errors may contain connection credentials.
        print(json.dumps({"error": type(exc).__name__}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
