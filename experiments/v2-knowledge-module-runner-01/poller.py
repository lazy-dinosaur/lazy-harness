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


def _kept(prev):
    """The conflict count a unit carries until it is digested (astra parallel review r3: partial/idle hints reset it)."""
    return {"conflicts": prev["conflicts"]} if prev and "conflicts" in prev else {}


def _failure(state, key, now, max_attempts, base_delay):
    prev = state.get(key, {})
    count = prev.get("attempts", 0) + 1
    state[key] = {"attempts": count, "next": now + base_delay * 2 ** (count - 1),
                  "stuck": count >= max_attempts,
                  **({"conflicts": prev["conflicts"]} if "conflicts" in prev else {})}  # the cap survives a backoff


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


def _candidates(dsn, execution_scope=None):
    if execution_scope is not None:
        # The admitted source-review cohort does not authorize sibling ledger work.
        # Future explicit work-unit/entry scopes may opt into those phases.
        if not execution_scope.root_work_unit_ids and not execution_scope.root_entry_ids:
            return [], []
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select w.work_unit_id::text, count(*)::int as entries from knowledge.work_unit w
                    join knowledge.ledger_entry e on e.work_unit_id=w.work_unit_id
                    where w.status='completed' and e.state='eligible'
                    -- contra06 (2026-10-02): a unit with unchecked entries cannot digest yet ('waiting'); counting it used
                    -- the whole window every tick, so its own worktime never ran (150-entry unit stalled at 50 eligible)
                    and not exists (select 1 from knowledge.ledger_entry p where p.work_unit_id=w.work_unit_id
                                    and p.state='proposed')
                    and (%s::uuid[] is null or w.work_unit_id=any(%s::uuid[]))
                    group by w.work_unit_id,w.completed_at
                    order by w.completed_at,w.work_unit_id""",
                    (sorted(execution_scope.root_work_unit_ids) if execution_scope else None,
                     sorted(execution_scope.root_work_unit_ids) if execution_scope else None))
        units = store_pg._rows(cur)
        cur.execute("""select entry_id::text from knowledge.ledger_entry where state='proposed'
                    and (%s::uuid[] is null or entry_id=any(%s::uuid[])) order by created_at,entry_id""",
                    (sorted(execution_scope.root_entry_ids) if execution_scope else None,
                     sorted(execution_scope.root_entry_ids) if execution_scope else None))
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


MAX_CONFLICTS = 20  # 'canon changed' rechecks of one unit retried at once before the normal backoff


def _pool(workers, fn, items):
    """Run fn(item) for each item, `workers` at a time (1 = in order, as before). -> [(item, result or exception)].
    Migration parallel load (user 'a', 2026-10-03): Jev judging happens outside transactions, so several units or entry
    chunks are judged at once; every commit still takes the host dictionary lock and the subject-generation checks.
    Contract (astra parallel review P1): with workers > 1 the DB commit order of units is NOT the candidate order -- an
    update/deprecate is protected by its target-revision CAS (the later one is rechecked), adds by the excerpt check.
    The injected judge / contra_judge / same functions must be thread-safe (the Jev and embedding clients are per call)."""
    if workers <= 1 or len(items) <= 1:
        out = []
        for it in items:
            try:
                out.append((it, fn(it)))
            except Exception as exc:  # noqa: BLE001 -- recorded per item as before
                out.append((it, exc))
        return out
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [(it, ex.submit(fn, it)) for it in items]
        out = []
        for it, f in futs:
            try:
                out.append((it, f.result()))
            except Exception as exc:  # noqa: BLE001
                out.append((it, exc))
        return out


def tick(dsn, judge, *, utterance_judge=None, max_units=20, window=50, state=DEFAULT_STATE,
         max_attempts=5, base_delay=30, now=None, choose=None, confirm=None, contra_judge=None, subject_same=None,
         workers=1, source_reviewer=None, require_source_review=False, runtime_db=None, execution_scope=None):
    from runtime_db import bind_runtime_db
    runtime_db = bind_runtime_db(runtime_db or dsn)
    dsn = runtime_db.require_same_target(dsn)
    if execution_scope is not None:
        from execution_scope import ExecutionScope
        if not isinstance(execution_scope, ExecutionScope):
            raise ValueError("execution scope must be an immutable validated ExecutionScope")
        if not require_source_review or source_reviewer is None:
            raise ValueError("scoped polling requires the bound source-review pipeline")
        import hashlib
        import json as _json
        target_fingerprint = hashlib.sha256(_json.dumps(runtime_db.endpoint, separators=(",", ":")).encode()).hexdigest()
        if execution_scope.dataset_fingerprint != target_fingerprint:
            raise ValueError("execution scope dataset does not match runtime database binding")
        if execution_scope.namespace != getattr(source_reviewer, "host_id", None):
            raise ValueError("execution scope namespace does not match source authority")
        if getattr(source_reviewer, "execution_scope", None) is not execution_scope:
            raise ValueError("source reviewer was not constructed with this immutable execution scope")
        state_path = Path(state)
        state_key = hashlib.sha256((execution_scope.dataset_fingerprint +
            execution_scope.root_baseline_fingerprint).encode()).hexdigest()[:16]
        state = state_path.with_name(f".{state_path.name}.scope-{state_key}")
    if require_source_review and source_reviewer is None:
        raise ValueError("source reviewer runtime database binding is required")
    if source_reviewer is not None:
        reviewer_context = getattr(source_reviewer, "runtime_db", None)
        if reviewer_context is not runtime_db:
            raise ValueError("source reviewer runtime database binding mismatch")
    if require_source_review and contra_judge is None:
        raise ValueError("source-required polling needs a contradiction judge")
    if min(max_units, window, max_attempts, base_delay, workers) < 1:
        raise ValueError("limits and delay must be positive")
    now = time.time() if now is None else now
    result = {"units": 0, "entries": 0, "embeddings": 0, "stuck": 0,
              "skipped": {"lock_busy": 0, "backoff": 0, "stuck": 0, "limit": 0, "embedding_unavailable": 0, "failed": 0}}
    if execution_scope is not None:
        result["execution_scope"] = {"root_questions": len(execution_scope.root_question_ids),
            "admitted_questions": len(execution_scope.question_ids),
            "blocked_unproven_dependencies": len(execution_scope.blocked_root_question_ids),
            "dataset_fingerprint": execution_scope.dataset_fingerprint,
            "root_fragments": len(execution_scope.root_fragment_ids),
            "root_subjects": len(execution_scope.root_subject_ids),
            "root_baseline_fingerprint": execution_scope.root_baseline_fingerprint,
            "source_manifest_fingerprint": execution_scope.source_manifest_fingerprint}
    source_telemetry = getattr(source_reviewer, "telemetry", None)
    source_telemetry_start = len(source_telemetry) if isinstance(source_telemetry, list) else 0
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
            units, entries = _candidates(dsn, execution_scope)
            hinted_scans = [k.split(":", 1)[1] for k in hints if k.startswith("scan:")]
            # astra P13 cross-review: scan hints are pruned by an exact DB check, never by a limited candidate list
            _prune(hints, entries, units, store_pg.unscanned(dsn, hinted_scans) if contra_judge is not None else hinted_scans)
            # worktime keeps a reserved share of the window so a digestion backlog never starves checking (astra stall review)
            reserve = max(1, window // 5)
            remaining = window - reserve
            planned = []  # (unit, key, spent) in order; judged in the pool, outcomes applied below in this order
            for unit in units:
                # a unit is one commit: one larger than the window runs when it is the first of the tick; its judge
                # calls are spread over ticks (budget = remaining), the commit happens in the pass that has them all
                # (contra06: 150 entries skipped forever; contra07: 220 entries > the old 4 x window cap, never digested)
                if result["units"] >= max_units or (remaining < unit["entries"] and result["units"] > 0):
                    skipped["limit"] += 1
                    continue
                key = "unit:" + unit["work_unit_id"]
                if _blocked(hints, key, now, skipped):
                    continue
                result["units"] += 1
                # a unit larger than what is left takes at most half of it, so units behind it still run (astra big review)
                spent = unit["entries"] if unit["entries"] <= remaining else max(1, remaining // 2)
                remaining = max(0, remaining - spent)  # never into worktime's reserved share
                planned.append((unit, key, spent))
            digested = _pool(workers, lambda pl: digest_driver.run_digestion(
                dsn, pl[0]["work_unit_id"], judge, choose=choose, confirm=confirm, same=subject_same,
                budget=max(1, pl[2])), planned)
            for (unit, key, spent), outcome in digested:
                if isinstance(outcome, Exception):
                    skipped["failed"] += 1
                    _failure(hints, key, now, max_attempts, base_delay)
                    continue
                # canon scans run below in one budgeted scheduler (astra P13 cross-review: they bypassed the budget)
                if (outcome["status"] == "needs_recheck" and outcome.get("why") == "canon changed (history)"
                        and hints.get(key, {}).get("conflicts", 0) < MAX_CONFLICTS):
                    # another unit landed first and changed what this add was judged on: not a failure -- judged
                    # again on the next tick without counting toward stuck; bounded (astra parallel review: outside
                    # writes could otherwise keep it retrying forever), then the normal backoff applies
                    prev = hints.get(key, {})
                    hints[key] = {"attempts": prev.get("attempts", 0), "next": 0, "stuck": False,
                                  "conflicts": prev.get("conflicts", 0) + 1}
                elif outcome["status"] in ("needs_review", "needs_recheck"):
                    _failure(hints, key, now, max_attempts, base_delay)
                elif outcome["status"] == "partial":
                    before = hints.get(key, {}).get("remaining")
                    if before is not None and outcome["remaining"] >= before:
                        # no progress (the canon moved and saved judgements no longer match): wait, budget back
                        result["units"] -= 1
                        remaining += spent
                        hints[key] = {"attempts": 0, "next": now + IDLE_DELAY, "stuck": False, "idle": True,
                                      "remaining": outcome["remaining"], **_kept(hints.get(key))}
                    else:
                        hints[key] = {"attempts": 0, "next": 0, "stuck": False, "remaining": outcome["remaining"],
                                      **_kept(hints.get(key))}
                elif outcome["status"] in ("noop", "waiting"):
                    # no progress (e.g. a change waits for a human): give the budget back and wait before the next
                    # try without counting toward stuck (astra stall review P1-1)
                    result["units"] -= 1
                    remaining += spent
                    hints[key] = {"attempts": 0, "next": now + IDLE_DELAY, "stuck": False, "idle": True,
                                  **_kept(hints.get(key))}
                else:
                    hints.pop(key, None)
            _save(state, hints)
            if contra_judge is not None:  # review P1: retry canon scans that did not finish after their commit
                history_review_used = 0
                if require_source_review and source_reviewer:
                    try:
                        history = store_pg.source_review_historical_pending(dsn, source_reviewer,
                            limit=1, host=execution_scope.namespace if execution_scope else None,
                            question_ids=sorted(execution_scope.question_ids) if execution_scope else None,
                            execution_scope=execution_scope,
                            after_id=hints.get("_historical_source_review_cursor"))
                        result["historical_source_review"] = history
                        if history.get("attempted"):
                            hints["_historical_source_review_cursor"] = history.get("last_id")
                            history_review_used = len(history["attempted"])
                        elif history.get("cursor_wrapped"):
                            hints["_historical_source_review_cursor"] = 0
                    except Exception as exc:
                        result["historical_source_review"] = {"failed": 1, "reason": type(exc).__name__}
                        skipped["failed"] += 1
                # one budget for all canon checks (astra 0012 review P2): source proof/rechecks first, scans take the rest
                try:  # 0012: contradictions whose side changed are judged again (an answer alone never resolves)
                    # rechecks get at most RECHECK_PER_TICK, so new units are always scanned (astra 0012 round 3)
                    rc = store_pg.recheck_contradictions(dsn, contra_judge, limit=RECHECK_PER_TICK,
                        source_review_required=require_source_review,
                        host=execution_scope.namespace if execution_scope else None,
                        question_ids=sorted(execution_scope.question_ids) if execution_scope else None,
                        execution_scope=execution_scope)
                    result["rechecked"] = rc["rechecked"]
                    skipped["failed"] += rc["failed"]
                except Exception:
                    rc = {"rechecked": 0}
                    skipped["failed"] += 1
                if require_source_review:
                    try:
                        cursor = hints.get("_source_review_cursor")
                        review_budget = max(0, SCAN_PER_TICK - rc["rechecked"] - history_review_used)
                        review_limit = max(0, (review_budget - 1) // 2)  # reserve fair capacity for hints
                        review_batch = store_pg.source_review_pending(dsn, source_reviewer,
                            limit=review_limit, host=execution_scope.namespace if execution_scope else None,
                            question_ids=sorted(execution_scope.question_ids) if execution_scope else None,
                            execution_scope=execution_scope,
                            after_id=cursor)
                        result["source_review"] = review_batch
                        if review_batch.get("attempted"):
                            hints["_source_review_cursor"] = review_batch.get("last_id")
                        elif review_batch.get("cursor_wrapped"):
                            hints["_source_review_cursor"] = 0
                        attempts = hints.setdefault("_source_review_attempts", {})
                        for item in review_batch.get("attempted", []):
                            key = str(item.get("question_id"))
                            previous = attempts.get(key, {})
                            attempts[key] = {"count": previous.get("count", 0) + 1,
                                "status": item.get("status"), "reason": item.get("reason"),
                                "receipt_id": item.get("receipt_id")}
                    except Exception as exc:
                        result["source_review"] = {"failed": 1, "reason": type(exc).__name__}
                        skipped["failed"] += 1
                if execution_scope:
                    # A root question authorizes its exact source pair, not a global canon-neighbour scan.
                    # Keep rescan markers queued until their complete comparison dependencies are admitted.
                    rs = {"rescanned": 0, "failed": 0}
                else:
                    try:  # stage 2: fragments queued by a subject merge/undo; at most half of what is left, new units keep the rest
                        rs = store_pg.rescan_fragments(dsn, contra_judge,
                            limit=max(0, SCAN_PER_TICK - rc["rechecked"]) // 2)
                        result["rescanned"] = rs["rescanned"]
                        skipped["failed"] += rs["failed"]
                    except Exception:
                        rs = {"rescanned": 0}
                        skipped["failed"] += 1
                if require_source_review and source_reviewer and hasattr(source_reviewer, "review_hint"):
                    try:
                        prior_review = result.get("source_review", {})
                        hint_budget = max(0, SCAN_PER_TICK - rc["rechecked"]
                                          - len(prior_review.get("attempted", [])) - rs["rescanned"])
                        hint_batch = store_pg.source_hint_pending(dsn, source_reviewer.review_hint,
                            limit=hint_budget, host=execution_scope.namespace if execution_scope else None,
                            question_ids=sorted(execution_scope.question_ids) if execution_scope else None,
                            execution_scope=execution_scope,
                            after_id=hints.get("_source_hint_cursor"))
                        result["source_hint"] = hint_batch
                        if hint_batch.get("attempted"):
                            hints["_source_hint_cursor"] = hint_batch.get("last_id")
                        elif hint_batch.get("cursor_wrapped"):
                            hints["_source_hint_cursor"] = 0
                        attempts = hints.setdefault("_source_hint_attempts", {})
                        for item in hint_batch.get("attempted", []):
                            key = str(item.get("question_id"))
                            previous = attempts.get(key, {})
                            attempts[key] = {"count": previous.get("count", 0) + 1,
                                "kind": item.get("kind"), "status": item.get("status"),
                                "reason": item.get("reason"), "receipt_id": item.get("receipt_id")}
                    except Exception as exc:
                        result["source_hint"] = {"failed": 1, "reason": type(exc).__name__}
                        skipped["failed"] += 1
                source_review_used = (history_review_used
                    + len(result.get("source_review", {}).get("attempted", [])))
                source_hint_used = len(result.get("source_hint", {}).get("attempted", []))
                scans = ([] if execution_scope and not execution_scope.root_work_unit_ids else
                    list(_runnable_scans(dsn, hints, now, skipped,
                    max(0, SCAN_PER_TICK * workers - rc["rechecked"] - rs["rescanned"]
                        - source_review_used - source_hint_used))))
                if require_source_review or source_reviewer:
                    scan_call = lambda u: store_pg.scan_contradictions(dsn, u, contra_judge,
                        source_reviewer=source_reviewer, require_source_review=require_source_review)
                else:
                    scan_call = lambda u: store_pg.scan_contradictions(dsn, u, contra_judge)
                for uid_, outcome in _pool(workers, scan_call, scans):
                    key = "scan:" + uid_
                    if isinstance(outcome, Exception) or (isinstance(outcome, dict) and outcome.get("evidence_needed")):
                        _failure(hints, key, now, max_attempts, base_delay)
                    else:
                        hints.pop(key, None)
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
                    # entries are checked independently: split into `workers` chunks judged at once
                    chunks = [selected[k::workers] for k in range(min(workers, len(selected)))]
                    runs = _pool(workers, lambda ch: worktime_driver.run_worktime(
                        dsn, len(ch), judge, utterance_judge=utterance_judge, entry_ids=ch), chunks)
                    failures, statuses = set(), {}
                    for ch, outcome in runs:
                        if isinstance(outcome, Exception):
                            failures |= set(ch)  # counted below per entry
                            continue
                        failures |= {r["entry_id"] for r in outcome["failures"]}
                        statuses.update({r["entry_id"]: r["state"] for r in outcome["results"]})
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
                    hosts = ([execution_scope.namespace] if execution_scope else _pending_hosts(dsn, variant))
                    for host in hosts:
                        if remaining <= 0:
                            break
                        count = store_pg.backfill_embeddings(dsn, host, variant, limit=remaining,
                            fragment_ids=sorted(execution_scope.root_fragment_ids) if execution_scope else None)
                        result["embeddings"] += count
                        remaining -= count
                except embed.EmbeddingUnavailable:
                    skipped["embedding_unavailable"] += 1
                    break
            try:  # subjects registered without an embedding (astra big review r3)
                if execution_scope:
                    subject_hosts = [execution_scope.namespace]
                else:
                    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
                        cur.execute("select distinct host_id from knowledge.subject")
                        subject_hosts = [r[0] for r in cur.fetchall()]
                for host in subject_hosts:
                    result["embeddings"] += store_pg.backfill_subject_embeddings(dsn, host, limit=50,
                        subject_ids=sorted(execution_scope.root_subject_ids) if execution_scope else None)
            except embed.EmbeddingUnavailable:
                skipped["embedding_unavailable"] += 1
            result["stuck"] = sum(bool(v.get("stuck")) for v in hints.values() if isinstance(v, dict))
            if isinstance(source_telemetry, list):
                result["source_model_io"] = {"events": source_telemetry[source_telemetry_start:],
                    "usage": "token counts are not returned by the existing adapters"}
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


def configured_source_reviewer(cfg, runtime_db, *, root_override=None, host_override=None, manifest_override=None,
                               generator=None, verifier=None, correction_writer=None, execution_scope=None):
    """Build the normal-path source recovery/review/correction pipeline from one host binding."""
    import config
    import source_evidence
    import source_review
    from runtime_db import bind_runtime_db

    runtime_db = bind_runtime_db(runtime_db)
    # Freeze the selected runtime target into this private callback config snapshot.
    from types import MappingProxyType
    cfg = MappingProxyType({**cfg, "db_url": runtime_db.dsn})
    host_id = host_override or cfg.get("default_host")
    if not host_id:
        if root_override or manifest_override:
            raise config.ConfigError("source authority override requires --source-host")
        return None
    authority = config.source_authority(cfg, host_id, root_override=root_override,
        host_override=host_override, manifest_override=manifest_override)
    if authority is None:
        return None
    bindings = (source_evidence.load_import_bindings(authority["root"], authority["import_manifest"])
                if authority["import_manifest"] else {})
    if execution_scope is not None:
        import hashlib
        import json as _json
        target_fingerprint = hashlib.sha256(_json.dumps(runtime_db.endpoint, separators=(",", ":")).encode()).hexdigest()
        if execution_scope.dataset_fingerprint != target_fingerprint:
            raise ValueError("execution scope dataset does not match source authority runtime")
        if not authority["import_manifest"]:
            raise ValueError("scoped polling requires an explicit frozen source manifest")
        manifest_path = Path(authority["root"]) / authority["import_manifest"]
        manifest_fingerprint = __import__("hashlib").sha256(manifest_path.read_bytes()).hexdigest()
        if manifest_fingerprint != execution_scope.source_manifest_fingerprint:
            raise ValueError("execution scope source-manifest fingerprint mismatch")
        if execution_scope.namespace != authority["host_id"]:
            raise ValueError("execution scope namespace does not match source binding")
    provider = source_review.SourceProvider(authority["root"], bindings=bindings)
    judge = verifier or __import__("capture_audit").make_judge(cfg)
    telemetry = []

    def guard_scope(question_id, fragments):
        if execution_scope is None:
            return
        ids = [str(item.get("id")) for item in fragments if isinstance(item, dict) and item.get("id")]
        expected = next((set(pair) for qid, pair in execution_scope.question_fragment_pairs
                         if qid == str(question_id)), None)
        if (question_id is None or expected is None or not ids or not set(ids).issubset(expected)):
            raise ValueError("question or fragment dependency is outside the immutable execution scope")

    def revalidate_scope(question_id, fragments):
        guard_scope(question_id, fragments)
        if execution_scope is not None:
            expected = next(pair for qid, pair in execution_scope.question_fragment_pairs
                            if qid == str(question_id))
            # Single-fragment correction/metadata callbacks revalidate their complete captured pair.
            execution_scope.revalidate_current_question(cfg["db_url"], question_id, authority["host_id"],
                sorted(expected))

    def typed_judge(state, questions, question, **kwargs):
        runtime_db.assert_environment()
        sides = [state.get(name, {}) for name in ("left", "right", "fragment")]
        ids = [item.get("id") for item in sides if isinstance(item, dict) and item.get("id")]
        if execution_scope is not None and any(not execution_scope.admits_fragment(fid) for fid in ids):
            raise ValueError("model callback fragment is outside the immutable execution scope")
        entry = {"kind": "typed-verification", "fragment_ids": ids,
                 "question_kind": state.get("hint_kind") or ("pair" if "left" in state and "right" in state else "correction")}
        try:
            result = judge(state, questions, question, **kwargs)
            choices = [item.get("choice") for item in result if isinstance(item, dict)] if isinstance(result, list) else []
            telemetry.append({**entry, "status": "returned", "choices": choices})
            return result
        except Exception as exc:
            telemetry.append({**entry, "status": "failed", "failure": type(exc).__name__})
            raise

    def generate(fragment, prompt, cwd):
        runtime_db.assert_environment()
        if execution_scope is not None and not execution_scope.admits_fragment(fragment.get("id")):
            raise ValueError("generation fragment is outside the immutable execution scope")
        import source_generation
        event = {"kind": "proposal-generation", "adapter": "existing-pi-luna",
                 "fragment_id": fragment.get("id"), "revision": fragment.get("revision"),
                 "usage": "not-reported-by-generator-adapter"}
        try:
            text = generator(prompt, cwd) if generator is not None else source_generation._default_generate(prompt, cwd)
            telemetry.append({**event, "status": "returned"})
            return text
        except Exception as exc:
            telemetry.append({**event, "status": "failed", "failure": type(exc).__name__})
            raise

    def recover_metadata_claim(fragment, question_id, stage):
        guard_scope(question_id, [fragment])
        import source_generation, source_metadata_repair
        telemetry.append({"kind": "metadata-rebind-start", "stage": stage, "question_id": question_id,
            "fragment_id": fragment.get("id"), "revision": fragment.get("revision")})
        proposal = source_generation.generate_metadata_references(fragment, provider, typed_judge,
            generator=lambda prompt, cwd: generate(fragment, prompt, cwd))
        telemetry.append({"kind": "metadata-rebind-proposal", "stage": stage, "question_id": question_id,
            "fragment_id": fragment.get("id"), "revision": fragment.get("revision"),
            "status": proposal.get("status"), "reason": proposal.get("reason")})
        if proposal.get("status") != "supported":
            return proposal.get("status"), proposal.get("reason")
        revalidate_scope(question_id, [fragment])
        runtime_db.require_same_target(cfg["db_url"])
        with store_pg.connect(cfg["db_url"]) as conn, conn.cursor() as cur:
            cur.execute("""select id::text,host_id,alias,domain,seq,text,keywords,kind::text,group_id,revision,active,
                        confidence::text,source,valid_from,superseded_at,subject_id::text
                        from knowledge.fragment where host_id=%s and id=%s""",
                        (authority["host_id"], fragment["id"]))
            full_fragment = store_pg._row(cur)
        if not full_fragment or full_fragment["revision"] != fragment["revision"]:
            return "stale", "fragment_revision_changed"
        repair = source_metadata_repair.prepare(full_fragment, proposal["new_refs"], authority["root"],
            bindings=bindings, expected_host=authority["host_id"],
            source_verification=proposal["semantic_verification"])
        stored = store_pg.apply_source_metadata_repair(cfg["db_url"], authority["host_id"], repair,
            source_root=authority["root"], bindings=bindings)
        telemetry.append({"kind": "metadata-rebind-apply", "stage": stage, "question_id": question_id,
            "fragment_id": fragment["id"], "status": stored.get("status")})
        return stored.get("status"), None

    def review(source_host, left, right, question_id=None):
        guard_scope(question_id, [left, right])
        runtime_db.assert_environment()
        if source_host != authority["host_id"]:
            return {"status": "evidence_needed", "reason": "source_root_host_mismatch"}
        pair_ids = [item.get("id") for item in (left, right)]
        telemetry.append({"kind": "pair-review", "question_id": question_id, "fragment_ids": pair_ids})
        receipt = source_review.review_pair(left, right, provider, typed_judge)
        revalidate_scope(question_id, [left, right])
        if receipt.get("status") == "reviewed" and receipt.get("verdict") != "genuine_conflict":
            return receipt
        import source_evidence, source_generation, source_metadata_repair
        writer = correction_writer or store_pg.apply_source_correction
        for fragment in (left, right):
            # Citation-only rebinding is attempted only after exact declared-document reads prove
            # each old verbatim quote at one unique coordinate. It is never semantic approval.
            try:
                proof = provider.read_fragment(fragment)
                telemetry.append({"kind": "source-proof-read", "stage": "source_review",
                    "question_id": question_id, "fragment_id": fragment.get("id"),
                    "revision": fragment.get("revision"), "fingerprint": proof["fingerprint"]})
            except source_evidence.SourceEvidenceError as guard_error:
                telemetry.append({"kind": "source-guard", "stage": "source_review",
                    "question_id": question_id, "fragment_id": fragment.get("id"),
                    "revision": fragment.get("revision"), "reason": guard_error.code})
                try:
                    recovered = provider.recover_original_context(fragment)
                    originals = recovered["evidence"]
                    telemetry.append({"kind": "original-context-read", "stage": "source_review",
                        "question_id": question_id, "fragment_id": fragment.get("id"),
                        "revision": fragment.get("revision"), "fingerprint": recovered["fingerprint"],
                        "verification": recovered["verification"]})
                    with store_pg.connect(cfg["db_url"]) as conn, conn.cursor() as cur:
                        cur.execute("""select id::text,host_id,alias,domain,seq,text,keywords,kind::text,group_id,revision,active,
                                    confidence::text,source,valid_from,superseded_at,subject_id::text
                                    from knowledge.fragment where host_id=%s and id=%s""",
                                    (authority["host_id"], fragment["id"]))
                        full_fragment = store_pg._row(cur)
                    if not full_fragment or full_fragment["revision"] != fragment["revision"]:
                        telemetry.append({"kind": "metadata-rebind-skip", "stage": "source_review",
                            "question_id": question_id, "fragment_id": fragment["id"],
                            "expected_revision": fragment.get("revision"),
                            "current_revision": full_fragment.get("revision") if full_fragment else None})
                        continue
                    old_refs = (fragment.get("source") or {}).get("evidence_refs", [])
                    exact_refs = source_evidence.literal_quote_references(originals,
                        [ref.get("quote") for ref in old_refs if isinstance(ref, dict)])
                    replacements = []
                    for ref in old_refs:
                        matches = [candidate for candidate in exact_refs if candidate["quote"] == ref.get("quote")]
                        if len(matches) != 1:
                            replacements = []
                            break
                        replacements.append({k: v for k, v in matches[0].items() if not k.startswith("_")})
                    if replacements and len(replacements) == len(old_refs):
                        revalidate_scope(question_id, [fragment])
                        repair = source_metadata_repair.prepare(full_fragment, replacements, authority["root"],
                            bindings=bindings, expected_host=authority["host_id"])
                        repaired = store_pg.apply_source_metadata_repair(cfg["db_url"], authority["host_id"], repair,
                            source_root=authority["root"], bindings=bindings)
                        if repaired.get("status") in ("applied", "existing"):
                            return {"status": "evidence_needed", "reason": "source_metadata_repair_applied",
                                    "repair_status": repaired["status"]}
                except (source_evidence.SourceEvidenceError, ValueError, OSError):
                    pass
                rebound, reason = recover_metadata_claim(fragment, question_id, "source_review")
                if rebound in ("applied", "existing"):
                    return {"status": "evidence_needed", "reason": "source_metadata_repair_applied",
                            "repair_status": rebound}
        # A pair receipt cannot identify which assertion is wrong. Generate and separately verify
        # each side against its own authorized original document; a successful CAS changes revision,
        # causing the enclosing contradiction scan to retry before any user question is exposed.
        for fragment in (left, right):
            proposal = source_generation.generate_and_verify(fragment, provider, typed_judge,
                generator=lambda prompt, cwd, item=fragment: generate(item, prompt, cwd))
            reason = proposal.get("reason")
            telemetry.append({"kind": "proposal-result", "question_id": question_id,
                "fragment_id": fragment.get("id"), "status": proposal.get("status"),
                "reason": reason if isinstance(reason, str) and reason.replace("_", "").isalnum() else None})
            if proposal.get("status") != "supported":
                continue
            revalidate_scope(question_id, [fragment])
            runtime_db.assert_environment()
            applied = writer(cfg["db_url"], authority["host_id"], proposal,
                source_root=authority["root"], bindings=bindings)
            if applied.get("status") in ("applied", "existing"):
                return {"status": "evidence_needed", "reason": "source_correction_applied",
                        "correction_status": applied["status"]}
        return receipt
    def review_hint(source_host, hint_kind, left, right, question_id=None):
        guard_scope(question_id, [left, right])
        runtime_db.assert_environment()
        if source_host != authority["host_id"]:
            return {"status": "evidence_needed", "reason": "source_root_host_mismatch"}
        telemetry.append({"kind": "hint-review", "hint_kind": hint_kind,
                          "question_id": question_id, "fragment_ids": [left.get("id"), right.get("id")]})
        result = source_review.review_hint_pair(hint_kind, left, right, provider, typed_judge,
                                                question_id=question_id)
        revalidate_scope(question_id, [left, right])
        if result.get("status") == "reviewed" or result.get("reason") not in {
                "quote_not_in_declared_range", "quote_absent_or_ambiguous",
                "source_line_range_invalid", "section_breadcrumb_unmatched_or_ambiguous",
                "section_breadcrumb_not_verbatim"}:
            return result
        # A bad citation is not a reason to skip the already-declared original document. First
        # attempt exact, unique quote rebinding through the protected metadata-only writer.
        import source_metadata_repair, source_generation
        current = [left, right]
        for index, fragment in enumerate(current):
            try:
                originals = provider.recover_original_context(fragment)
                old_refs = (fragment.get("source") or {}).get("evidence_refs", [])
                file_refs = [ref for ref in old_refs if isinstance(ref, dict)
                             and ref.get("type") in ("official_doc", "code_test")]
                if not file_refs or len(file_refs) != len(old_refs):
                    continue
                exact_refs = source_evidence.literal_quote_references(originals["evidence"],
                    [ref.get("quote") for ref in file_refs])
                replacements = []
                for ref in file_refs:
                    matches = [candidate for candidate in exact_refs if candidate["quote"] == ref.get("quote")]
                    if len(matches) != 1:
                        replacements = []
                        break
                    replacements.append({k: v for k, v in matches[0].items() if not k.startswith("_")})
                if replacements and len(replacements) == len(old_refs):
                    revalidate_scope(question_id, [fragment])
                    with store_pg.connect(cfg["db_url"]) as conn, conn.cursor() as cur:
                        cur.execute("""select id::text,host_id,alias,domain,seq,text,keywords,kind::text,group_id,revision,active,
                                    confidence::text,source,valid_from,superseded_at,subject_id::text
                                    from knowledge.fragment where host_id=%s and id=%s""",
                                    (authority["host_id"], fragment["id"]))
                        full_fragment = store_pg._row(cur)
                    if full_fragment and full_fragment["revision"] == fragment["revision"]:
                        repair = source_metadata_repair.prepare(full_fragment, replacements, authority["root"],
                            bindings=bindings, expected_host=authority["host_id"])
                        stored = store_pg.apply_source_metadata_repair(cfg["db_url"], authority["host_id"], repair,
                            source_root=authority["root"], bindings=bindings)
                        if stored.get("status") in ("applied", "existing"):
                            telemetry.append({"kind": "hint-source-rebind", "question_id": question_id,
                                "fragment_id": fragment["id"], "status": stored["status"]})
            except (source_evidence.SourceEvidenceError, ValueError, OSError):
                pass
            rebound, reason = recover_metadata_claim(fragment, question_id, "source_hint")
            if rebound in ("applied", "existing"):
                telemetry.append({"kind": "hint-source-rebind", "question_id": question_id,
                    "fragment_id": fragment["id"], "status": rebound})
        # Reload both active fragments after any metadata revision change; never reuse old receipts.
        with store_pg.connect(cfg["db_url"]) as conn, conn.cursor() as cur:
            cur.execute("""select id::text,revision,text,source,active from knowledge.fragment
                           where host_id=%s and id=any(%s::uuid[])""",
                        (authority["host_id"], [left["id"], right["id"]]))
            latest = {row[0]: {"id": row[0], "revision": row[1], "text": row[2], "source": row[3], "active": row[4]}
                      for row in cur.fetchall()}
        current = [latest.get(left["id"]), latest.get(right["id"])]
        if all(current):
            result = source_review.review_hint_pair(hint_kind, current[0], current[1], provider, typed_judge,
                                                    question_id=question_id)
            if result.get("status") == "reviewed" or result.get("reason") not in {
                    "quote_not_in_declared_range", "quote_absent_or_ambiguous",
                    "source_line_range_invalid", "section_breadcrumb_unmatched_or_ambiguous",
                    "section_breadcrumb_not_verbatim"}:
                return result
            # If citations cannot be rebound without changing claim meaning, run the existing
            # bounded proposal + independent typed verifier for each declared source context.
            writer = correction_writer or store_pg.apply_source_correction
            for fragment in current:
                proposal = source_generation.generate_and_verify(fragment, provider, typed_judge,
                    generator=lambda prompt, cwd, item=fragment: generate(item, prompt, cwd))
                if proposal.get("status") != "supported":
                    continue
                revalidate_scope(question_id, [fragment])
                runtime_db.assert_environment()
                applied = writer(cfg["db_url"], authority["host_id"], proposal,
                    source_root=authority["root"], bindings=bindings)
                if applied.get("status") in ("applied", "existing"):
                    telemetry.append({"kind": "hint-source-correction", "question_id": question_id,
                        "fragment_id": fragment["id"], "status": applied["status"]})
                    return {"status": "evidence_needed", "reason": "source_correction_applied"}
        return result

    review.telemetry = telemetry
    review.runtime_db = runtime_db
    review.host_id = authority["host_id"]
    review.execution_scope = execution_scope
    review.accepts_question_id = True
    review.review_hint = review_hint
    return review


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", required=True)
    parser.add_argument("--judge", choices=("jev",), default="jev")
    parser.add_argument("--max-units", type=int, default=20)
    parser.add_argument("--window", type=int, default=50)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--workers", type=int, default=1)  # units / entry chunks judged at once (migration load)
    parser.add_argument("--dsn", help="explicit runtime PostgreSQL connection string; never logged")
    parser.add_argument("--source-root", type=Path, help="explicit authorized project root for source-backed contradiction review")
    parser.add_argument("--source-host", help="host_id authorized for --source-root; other hosts fail closed")
    parser.add_argument("--source-import-manifest", type=Path, help="optional explicit frozen-import manifest under --source-root")
    parser.add_argument("--execution-scope-ledger", type=Path,
                        help="explicit approved cohort ledger; constrains every poller phase for this invocation")
    args = parser.parse_args()
    import config
    try:
        cfg = config.require("jev_api_key", "jev_base_url", "jev_model")
        from runtime_db import bind_runtime_db
        runtime_db = bind_runtime_db(args.dsn or config.require("db_url")["db_url"],
                                     provenance="explicit-cli" if args.dsn else "configured-entry")
    except config.ConfigError as exc:
        parser.error(str(exc))  # names missing keys only, never values
    if bool(args.source_root) != bool(args.source_host):
        parser.error("--source-root and --source-host must be supplied together")
    if args.source_import_manifest and not args.source_root:
        parser.error("--source-import-manifest requires --source-root")
    execution_scope = None
    if args.execution_scope_ledger:
        if not (args.source_root and args.source_host and args.source_import_manifest):
            parser.error("--execution-scope-ledger requires explicit --source-root, --source-host, and --source-import-manifest")
        from execution_scope import ExecutionScope
        import hashlib
        manifest_path = args.source_import_manifest
        if not manifest_path.is_absolute():
            manifest_path = args.source_root / manifest_path
        try:
            manifest_fingerprint = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            execution_scope = ExecutionScope.from_pilot_ledger(runtime_db.dsn, args.execution_scope_ledger,
                namespace=args.source_host, source_manifest_fingerprint=manifest_fingerprint)
        except (ValueError, OSError) as exc:
            parser.error(type(exc).__name__)
    try:
        source_reviewer = configured_source_reviewer(cfg, runtime_db, root_override=args.source_root,
            host_override=args.source_host, manifest_override=args.source_import_manifest,
            execution_scope=execution_scope)
    except (config.ConfigError, ValueError, OSError) as exc:
        parser.error(type(exc).__name__)
    config.apply_embed_env(cfg)
    try:
        print(json.dumps(tick(runtime_db.dsn, digest_driver._jev_judge,
                              utterance_judge=_utterance_judge, max_units=args.max_units, workers=args.workers,
                              window=args.window, state=args.state,
                              choose=__import__("domain_router").make_choose(cfg),
                              confirm=__import__("domain_router").make_confirm(cfg),
                              contra_judge=__import__("capture_audit").make_judge(cfg),
                              subject_same=__import__("worker_tools").make_ask(cfg),
                              # ssot/v2-knowledge-module-source-authority.md: a missing binding means no source
                              # provider for that host (not a failed tick); a configured binding is required in full.
                              source_reviewer=source_reviewer, require_source_review=source_reviewer is not None,
                              runtime_db=runtime_db, execution_scope=execution_scope)))
    except Exception as exc:
        # No exception message: driver errors may contain connection credentials.
        print(json.dumps({"error": type(exc).__name__}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
