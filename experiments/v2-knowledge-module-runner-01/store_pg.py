"""PostgreSQL storage for the offline knowledge runner (DSN supplied explicitly)."""
import json
import subprocess
from pathlib import Path

from contextlib import contextmanager, closing
from uuid import uuid4

import embed
import policy
import runner
import store

try:
    import psycopg as driver
except ImportError:
    import psycopg2 as driver


@contextmanager
def connect(dsn):
    with closing(driver.connect(dsn)) as conn:
        with conn:
            yield conn


def next_seq(cur, host, domain):
    """Next alias number for (host, domain). G8: a transaction-scoped advisory lock serialises concurrent digestions
    of the same domain until commit, so unique(host_id, domain, seq) is never raced. No schema change."""
    cur.execute("select pg_advisory_xact_lock(hashtextextended(%s, 0))", (f"lh-seq/{host}/{domain}",))
    cur.execute("select coalesce(max(seq),0)+1 from knowledge.fragment where host_id=%s and domain=%s", (host, domain))
    return cur.fetchone()[0]


def _json(value):
    return json.dumps(value, ensure_ascii=False)


def _row(cursor):
    value = cursor.fetchone()
    return dict(zip([col[0] for col in cursor.description], value)) if value else None


def _rows(cursor):
    return [dict(zip([col[0] for col in cursor.description], value)) for value in cursor.fetchall()]


def search(dsn, host, query, limit=8, cross_hosts=None, mode="text", min_similarity=None,
           exclude_ids=None, variant="plain", expand=True):
    _variant(variant)
    if limit < 0:
        raise ValueError("limit must be nonnegative")
    if mode not in ("text", "hybrid"):
        raise ValueError("unknown search mode")
    warning = None
    if mode == "hybrid":
        try:
            vector = embed.encode_query(query)
        except embed.EmbeddingUnavailable:
            mode, warning = "text", "embedding service unavailable; text fallback"
    else:
        vector = None
    with connect(dsn) as conn, conn.cursor() as cur:
        if mode == "hybrid":
            cur.execute("select * from knowledge.search_hybrid(%s,%s,%s::extensions.vector,%s,%s,%s::text[],%s,%s,%s::uuid[],%s)",
                        (host, query, _vector(vector), embed.MODEL_ID, limit, cross_hosts, 60,
                         min_similarity, list(exclude_ids or []), variant))
        else:
            cur.execute("select * from knowledge.search_fragments(%s,%s,%s,%s::text[])",
                        (host, query, 2147483647 if exclude_ids else limit, cross_hosts))
            if exclude_ids:
                excluded = set(exclude_ids)
        results = _rows(cur)
        if mode == "text" and exclude_ids:
            results = [r for r in results if str(r["id"]) not in excluded][:limit]
        for result in results:
            result["id"] = str(result["id"])
            result["mode_used"] = mode
            if warning:
                result["warning"] = warning
            result["group"] = []
            if expand and result["group_id"] is not None:
                cur.execute("select * from knowledge.expand_group(%s,%s)",
                            (result["host_id"], result["group_id"]))
                result["group"] = [{**sibling, "id": str(sibling["id"])} for sibling in _rows(cur)
                                   if str(sibling["id"]) != result["id"]]
        return results


def _vector(values):
    return "[" + ",".join(str(value) for value in values) + "]"


def _variant(variant):
    if variant not in ("plain", "ctx-v1"):
        raise ValueError("unknown embedding variant")


def _upsert_embedding(cur, fragment_id, revision, vector, variant="plain"):
    _variant(variant)
    cur.execute("""insert into knowledge.fragment_embedding(fragment_id,revision,model_id,embed_variant,embedding)
                values (%s,%s,%s,%s,%s::extensions.vector)
                on conflict (fragment_id,model_id,embed_variant) do update
                set revision=excluded.revision, embedding=excluded.embedding, created_at=now()""",
                (fragment_id, revision, embed.MODEL_ID, variant, _vector(vector)))


def _embedding_input(kind, domain, siblings, text, variant):
    if variant == "plain":
        return text
    # Stable, bounded DB-derived context; never changes the stored fragment body.
    context = f"kind={kind}; domain={domain}; siblings={'; '.join(siblings)[:160]}"
    return f"[{context}] {text}"


def backfill_embeddings(dsn, host, variant="plain", limit=None):
    _variant(variant)
    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select f.id::text,f.revision,f.text,f.kind::text,f.domain,f.group_id
                    from knowledge.fragment f
                    left join knowledge.fragment_embedding e on e.fragment_id=f.id and e.model_id=%s
                      and e.embed_variant=%s
                    where f.host_id=%s and f.active and (e.fragment_id is null or e.revision<>f.revision)
                    order by f.id limit %s for update of f""", (embed.MODEL_ID, variant, host, limit or 2147483647))
        missing = cur.fetchall()
        inputs = []
        for fragment_id, revision, text, kind, domain, group_id in missing:
            siblings = []
            if variant == "ctx-v1" and group_id is not None:
                cur.execute("""select left(text,80) from knowledge.fragment
                            where host_id=%s and group_id=%s and id<>%s and active
                            order by id limit 3""", (host, group_id, fragment_id))
                siblings = [row[0] for row in cur.fetchall()]
            inputs.append(_embedding_input(kind, domain, siblings, text, variant))
        vectors = embed.encode_passages(inputs)
        for (fragment_id, revision, *_), vector in zip(missing, vectors):
            _upsert_embedding(cur, fragment_id, revision, vector, variant)
        return len(missing)


def rows(dsn, table):
    if table not in {"host", "fragment", "fragment_history", "work_unit", "work_unit_event", "ledger_entry",
                     "ledger_entry_event", "check_receipt", "absorption", "confirmation_queue", "question_template"}:
        raise ValueError("unknown table")
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(f"select * from knowledge.{table}")
        return _rows(cur)


def policies(cur, host_id):
    cur.execute("select count(*) from knowledge.acceptance_policy where host_id=%s", (host_id,))
    scope = host_id if cur.fetchone()[0] else None
    cur.execute("""select rule_id, when_json, then_action from knowledge.acceptance_policy
                   where host_id is not distinct from %s and version=(select max(version) from knowledge.acceptance_policy
                   where host_id is not distinct from %s) order by ordinal""", (scope, scope))
    return [{"id": r["rule_id"], "when": {k: tuple(v) if isinstance(v, list) and k != "review_reasons" else v
            for k, v in r["when_json"].items()}, "then": r["then_action"]} for r in _rows(cur)]


def _transition(cur, entry, state, actor, receipt_ref=None):
    old = entry["state"]
    cur.execute("update knowledge.ledger_entry set state=%s where entry_id=%s", (state, entry["entry_id"]))
    cur.execute('insert into knowledge.ledger_entry_event(entry_id,"from","to",actor,receipt_ref) values (%s,%s,%s,%s,%s)',
                (entry["entry_id"], old, state, actor, receipt_ref))
    entry["state"] = state


def _history_max(cur, host):
    cur.execute("""select coalesce(max(h.history_id),0) from knowledge.fragment_history h
                   join knowledge.fragment f on f.id=h.fragment_id where f.host_id=%s""", (host,))
    return cur.fetchone()[0]


def _start(cur, unit_id, host, partition_key, code_ref):
    # Serialize creation against another registration of this UUID; never reset an existing baseline.
    cur.execute("select host_id,partition_key from knowledge.work_unit where work_unit_id=%s", (unit_id,))
    existing = _row(cur)
    if existing:
        if (existing["host_id"], existing["partition_key"]) != (host, partition_key):
            raise ValueError("work unit host/partition mismatch")
        return False
    cur.execute("""insert into knowledge.work_unit
                (work_unit_id,host_id,partition_key,baseline_history_id,baseline_at,baseline_code_ref)
                values (%s,%s,%s,%s,now(),%s) on conflict (work_unit_id) do nothing""",
                (unit_id, host, partition_key, _history_max(cur, host), code_ref))
    if cur.rowcount:
        cur.execute('insert into knowledge.work_unit_event(work_unit_id,"to",source) values (%s,%s,%s)',
                    (unit_id, "active", "register"))
        return True
    cur.execute("select host_id,partition_key from knowledge.work_unit where work_unit_id=%s", (unit_id,))
    existing = _row(cur)
    if (existing["host_id"], existing["partition_key"]) != (host, partition_key):
        raise ValueError("work unit host/partition mismatch")
    return False


def start_work_unit(dsn, unit_id, host, partition_key, code_ref=None):
    with connect(dsn) as conn, conn.cursor() as cur:
        _start(cur, unit_id, host, partition_key, code_ref)
        cur.execute("""select work_unit_id::text,host_id,partition_key,baseline_history_id,
                    baseline_code_ref,baseline_at from knowledge.work_unit where work_unit_id=%s""", (unit_id,))
        return _row(cur)


def changed_since_baseline(dsn, unit_id):
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select host_id,baseline_history_id from knowledge.work_unit where work_unit_id=%s", (unit_id,))
        unit = _row(cur)
        if not unit or unit["baseline_history_id"] is None:
            raise ValueError("work unit has no baseline")
        cur.execute("select * from knowledge.changed_since(%s,%s)",
                    (unit["host_id"], unit["baseline_history_id"]))
        return _rows(cur)


def code_changed_since(repo_root, code_ref, path):
    """True/False for a tracked path compared with ref (including working tree); None if unknowable."""
    if not repo_root or not code_ref or not path:
        return None
    try:
        root = Path(repo_root).resolve(strict=True)
        target = (root / path).resolve(strict=True)
        relative = target.relative_to(root).as_posix()
        def git(*args):
            return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=5)
        top = git("rev-parse", "--show-toplevel")
        if top.returncode or Path(top.stdout.strip()).resolve() != root:
            return None
        if git("cat-file", "-e", f"{code_ref}^{{commit}}").returncode:
            return None
        tracked = git("ls-files", "--error-unmatch", "--", relative)
        if tracked.returncode:
            return None
        diff = git("diff", "--name-only", code_ref, "--", relative)
        return None if diff.returncode else bool(diff.stdout.strip())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def register(dsn, judgement):
    with connect(dsn) as conn, conn.cursor() as cur:
        host, unit = judgement["host_id"], judgement["work_unit_id"]
        _start(cur, unit, host, judgement["partition_key"], judgement.get("baseline_code_ref"))
        entry_id = str(uuid4())
        cur.execute("""insert into knowledge.ledger_entry(entry_id,host_id,partition_key,work_unit_id,judgement_id,
                   judgement_version,judgement_body) values (%s,%s,%s,%s,%s,%s,%s::jsonb)
                   returning entry_id::text,host_id,partition_key,work_unit_id::text,judgement_id,
                   judgement_version,state::text,supplement_count,created_at""",
                    (entry_id, host, judgement["partition_key"], unit, judgement["judgement_id"],
                     judgement["version"], _json(judgement)))
        entry = _row(cur)
        entry["judgement_body"] = judgement
        cur.execute('insert into knowledge.ledger_entry_event(entry_id,"to",actor) values (%s,%s,%s)',
                    (entry_id, "proposed", "worker"))
        return entry


def _target(cur, fact):
    ref = fact.get("target_ref")
    if not ref:
        return None
    try:
        from uuid import UUID
        UUID(ref)
    except (ValueError, TypeError, AttributeError):
        return None
    cur.execute("select id::text,revision,text,active from knowledge.fragment where id=%s", (ref,))
    return _row(cur)


def _receipts(cur, entry_id, stage):
    cur.execute("""select receipt_id::text,entry_id::text,fact_index,stage::text,template_id,template_version,
               jev_model_requested,jev_model_actual,dedup_key,packet,answers,combined::text,review_reasons,
               target_fragment_id::text,target_revision_seen from knowledge.check_receipt where entry_id=%s and stage=%s
               order by fact_index""", (entry_id, stage))
    return _rows(cur)


def _receipt(cur, entry, index, fact, fixture, stage, current=None):
    packet, answers = fixture["packet"], fixture["answers"]
    model = fixture.get("jev_model_actual", "offline-fixture")
    key = store.dedup_key(entry, fact, packet, model, index, stage)
    cur.execute("select receipt_id::text from knowledge.check_receipt where dedup_key=%s", (key,))
    cached = cur.fetchone()
    if cached:
        return cached[0]
    decision = runner.decide(packet, answers, operation=fact.get("operation", "add"))
    receipt_id = str(uuid4())
    cur.execute("""insert into knowledge.question_template(template_id,template_version,questions)
                   values (%s,%s,%s::jsonb) on conflict do nothing""",
                (packet["template_id"], packet["template_version"], _json(packet["questions"])))
    cur.execute("""insert into knowledge.check_receipt(receipt_id,entry_id,fact_index,stage,template_id,template_version,
                jev_model_requested,jev_model_actual,dedup_key,packet,answers,combined,review_reasons,
                target_fragment_id,target_revision_seen,input_tokens,output_tokens,cost_usd,usage_source)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s::jsonb,%s,%s,%s,%s,%s,%s)""",
                (receipt_id, entry["entry_id"], index, stage, packet["template_id"], packet["template_version"],
                 fixture.get("jev_model_requested", model), model, key, _json(packet), _json(answers),
                 decision["combined"], _json(decision["review_reasons"]), current["id"] if current else None,
                 current["revision"] if current else None, fixture.get("input_tokens"), fixture.get("output_tokens"),
                 fixture.get("cost_usd"), fixture.get("usage_source", "unreported-by-tool")))
    return receipt_id


def batch(dsn, window, fixtures, *, entry_ids=None):
    if window < 1:
        raise ValueError("window must be positive")
    results = []
    with connect(dsn) as conn, conn.cursor() as cur:
        # Lock units before entries, matching completion's lock order.
        cur.execute("""select work_unit_id from knowledge.work_unit where work_unit_id in
                    (select work_unit_id from knowledge.ledger_entry
                     where state='proposed' and (%s::uuid[] is null or entry_id=any(%s::uuid[]))
                     order by created_at,entry_id limit %s) order by work_unit_id for update""",
                    (entry_ids, entry_ids, window))
        cur.execute("""select entry_id::text,host_id,partition_key,work_unit_id::text,judgement_id,
                    judgement_version,judgement_body,state::text from knowledge.ledger_entry
                    where state='proposed' and (%s::uuid[] is null or entry_id=any(%s::uuid[]))
                    order by created_at,entry_id limit %s for update""", (entry_ids, entry_ids, window))
        for entry in _rows(cur):
            outcomes = []
            for index, fact in enumerate(entry["judgement_body"].get("facts", [])):
                operation = fact.get("operation", "add")
                current = _target(cur, fact) if operation in ("update", "deprecate") else None
                errors = runner.lint_fact(fact)["errors"]
                if operation not in ("add", "update", "deprecate"):
                    errors.append({"code": "E_SCHEMA", "where": f"facts.{index}.operation", "detail": "unknown operation"})
                if operation in ("update", "deprecate") and current is None:
                    errors.append({"code": "E_TARGET", "where": f"facts.{index}.target_ref", "detail": "target missing"})
                available = fixtures.get(entry["entry_id"], [])
                fixture = available[index] if index < len(available) else None
                if fixture is not None:
                    errors += runner.lint(fixture["packet"])["errors"]
                    excerpt = fixture["packet"].get("state", {}).get("target_excerpt")
                    if current and excerpt != current["text"]:
                        errors.append({"code": "E_TARGET", "where": f"facts.{index}.target_excerpt",
                                       "detail": "target_excerpt differs from target fragment text"})
                if errors:
                    outcomes.append({"fact_index": index, "errors": errors})
                elif fixture is None:
                    outcomes.append({"fact_index": index, "pending_fixture": True})
                else:
                    receipt_id = _receipt(cur, entry, index, fact, fixture, "worktime", current)
                    decision = runner.decide(fixture["packet"], fixture["answers"], operation=operation)
                    outcomes.append({"fact_index": index, "receipt_id": receipt_id, "combined": decision["combined"]})
            if not outcomes or any("errors" in o for o in outcomes):
                state = "rejected_input"
            elif any("pending_fixture" in o for o in outcomes):
                state = "proposed"
            elif any(o["combined"] == "needs_review" for o in outcomes):
                state = "review_queue"
            elif any(o["combined"] in ("record", "update_record", "deprecate_record") for o in outcomes):
                state = "provisional"
            else:
                state = "closed"
            if state == "provisional":
                # Completion can precede worktime review; never strand a late entry.
                cur.execute("select status::text from knowledge.work_unit where work_unit_id=%s",
                            (entry["work_unit_id"],))
                unit_status = cur.fetchone()[0]
                if unit_status == "completed":
                    state = "eligible"
                elif unit_status == "abandoned":
                    state = "expired"
            if state != "proposed":
                _transition(cur, entry, state, "runner")
            results.append({"entry_id": entry["entry_id"], "state": state, "facts": outcomes})
    return results


def register_completion_sources(dsn, unit_id, sources: list[str]):
    if not isinstance(sources, list) or any(not isinstance(s, str) or not s.strip() for s in sources):
        raise ValueError("sources must be nonempty strings")
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select status::text,completion_sources from knowledge.work_unit where work_unit_id=%s for update", (unit_id,))
        unit = _row(cur)
        if not unit or unit["status"] != "active":
            raise ValueError("work unit must be active")
        existing = {item["source"]: item for item in unit["completion_sources"]}
        for source in sources:
            existing.setdefault(source, {"source": source, "received": False})
        merged = list(existing.values())
        cur.execute("update knowledge.work_unit set completion_sources=%s::jsonb where work_unit_id=%s",
                    (_json(merged), unit_id))
        return merged


def signal_completion(dsn, unit_id, source, evidence=None):
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select status::text,completion_sources from knowledge.work_unit where work_unit_id=%s for update", (unit_id,))
        unit = _row(cur)
        if not unit:
            return {"status": "not_active", "pending": []}
        pending = [item["source"] for item in unit["completion_sources"] if not item["received"]]
        if unit["status"] == "completed":
            return {"status": "already_completed", "pending": []}
        if unit["status"] != "active":
            return {"status": "not_active", "pending": pending}
        match = next((item for item in unit["completion_sources"] if item["source"] == source), None)
        if match is None:
            return {"status": "unknown_source", "pending": pending}
        if not match["received"]:
            match.update(received=True, received_at=store.now(), evidence=evidence)
            cur.execute("update knowledge.work_unit set completion_sources=%s::jsonb where work_unit_id=%s",
                        (_json(unit["completion_sources"]), unit_id))
            cur.execute('insert into knowledge.work_unit_event(work_unit_id,"from","to",source) values (%s,%s,%s,%s)',
                        (unit_id, "active", "active", source))
        pending = [item["source"] for item in unit["completion_sources"] if not item["received"]]
        if pending:
            return {"status": "waiting", "pending": pending}
        # Reuse complete's transition under the same row lock and transaction.
        _complete(cur, unit_id, unit)
        return {"status": "completed", "pending": []}


def abandon(dsn, unit_id, reason):
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("reason is required")
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select status::text from knowledge.work_unit where work_unit_id=%s for update", (unit_id,))
        unit = _row(cur)
        if not unit or unit["status"] != "active":
            raise ValueError("work unit must be active")
        cur.execute("update knowledge.work_unit set status='abandoned' where work_unit_id=%s", (unit_id,))
        cur.execute('insert into knowledge.work_unit_event(work_unit_id,"from","to",source) values (%s,%s,%s,%s)',
                    (unit_id, "active", "abandoned", reason))
        cur.execute("""select entry_id::text,state::text from knowledge.ledger_entry where work_unit_id=%s
                    and state in ('proposed','review_queue','provisional') for update""", (unit_id,))
        entries = _rows(cur)
        for entry in entries:
            _transition(cur, entry, "expired", "runner")
        cur.execute("update knowledge.confirmation_queue set status='expired' where entry_id in "
                    "(select entry_id from knowledge.ledger_entry where work_unit_id=%s) and status='pending'", (unit_id,))
        return {"status": "abandoned", "expired": len(entries)}


def _complete(cur, unit_id, unit):
    if not unit or unit["status"] != "active" or any(not s.get("received") for s in unit["completion_sources"]):
        raise ValueError("work unit not active or completion sources unsatisfied")
    cur.execute("""update knowledge.work_unit set status='completed',completed_at=now() where work_unit_id=%s
                returning work_unit_id::text,host_id,partition_key,status::text,completion_sources,created_at,completed_at""", (unit_id,))
    result = _row(cur)
    cur.execute('insert into knowledge.work_unit_event(work_unit_id,"from","to",source) values (%s,%s,%s,%s)',
                (unit_id, "active", "completed", "explicit"))
    cur.execute("""select entry_id::text,state::text from knowledge.ledger_entry where work_unit_id=%s
                and state='provisional' for update""", (unit_id,))
    for entry in _rows(cur):
        _transition(cur, entry, "eligible", "runner")
    return result


def complete(dsn, unit_id):
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select status::text,completion_sources from knowledge.work_unit where work_unit_id=%s for update", (unit_id,))
        return _complete(cur, unit_id, _row(cur))


def resubmit(dsn, entry_id, actor="luna", limit=2):
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select entry_id::text,state::text,supplement_count from knowledge.ledger_entry where entry_id=%s for update", (entry_id,))
        entry = _row(cur)
        if not entry or entry["state"] != "review_queue":
            raise ValueError("only review_queue entries can be resubmitted")
        if entry["supplement_count"] >= limit:
            _transition(cur, entry, "review_queue", "runner")
            return {"status": "escalated", "supplement_count": entry["supplement_count"]}
        cur.execute("update knowledge.ledger_entry set supplement_count=supplement_count+1 where entry_id=%s", (entry_id,))
        _transition(cur, entry, "proposed", actor)
        return {"status": "proposed", "supplement_count": entry["supplement_count"] + 1}


def digest(dsn, unit_id, apply=False, fixtures=None):
    # One transaction covers both the fresh recheck and every resulting write.
    class Recheck(Exception):
        def __init__(self, receipt):
            self.receipt = receipt
    try:
        with connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""select status::text,host_id,baseline_history_id,baseline_code_ref
                        from knowledge.work_unit where work_unit_id=%s for update""", (unit_id,))
            unit = _row(cur)
            if not unit or unit["status"] != "completed":
                return {"status": "not_completed"}
            cur.execute("""select entry_id::text,host_id,partition_key,work_unit_id::text,judgement_id,
                        judgement_version,judgement_body,state::text from knowledge.ledger_entry
                        where work_unit_id=%s and state in ('eligible','provisional') order by created_at for update""", (unit_id,))
            candidates = [(entry, receipt, entry["judgement_body"]["facts"][receipt["fact_index"]])
                          for entry in _rows(cur) for receipt in _receipts(cur, entry["entry_id"], "worktime")]
            targets = {}
            for entry, receipt, fact in candidates:
                if fact.get("target_ref"):
                    targets.setdefault(fact["target_ref"], []).append(fact["operation"])
            flags = [{"target_ref": ref, "operations": sorted(ops)} for ref, ops in targets.items() if len(ops) > 1]
            history_max = _history_max(cur, unit["host_id"])
            cur.execute("select repo_locator from knowledge.host where host_id=%s", (unit["host_id"],))
            repo_root = cur.fetchone()[0]
            changed = unit["baseline_history_id"] is not None and history_max > unit["baseline_history_id"]
            stale = [r["receipt_id"] for _, r, f in candidates if
                     (r["target_fragment_id"] and
                      (not _target(cur, f) or _target(cur, f)["revision"] != r["target_revision_seen"])) or
                     (f.get("operation", "add") == "add" and changed) or
                     any(ref.get("type") == "code_test" and
                         code_changed_since(repo_root, unit["baseline_code_ref"], ref.get("locator")) is True
                         for ref in f.get("evidence_refs", []) if isinstance(ref, dict))]
            if stale and not fixtures:
                return {"status": "needs_recheck", "receipt_ids": [r["receipt_id"] for _, r, _ in candidates], "consistency_flags": flags}
            if flags:
                return {"status": "needs_review", "consistency_flags": flags}
            if not candidates:
                return {"status": "noop"}
            if not fixtures:
                return {"status": "needs_recheck", "receipt_ids": [r["receipt_id"] for _, r, _ in candidates], "consistency_flags": flags}
            prepared = []
            for entry, old, fact in candidates:
                fixture = fixtures.get(old["receipt_id"])
                if not fixture or not runner.lint(fixture["packet"])["ok"]:
                    raise Recheck(old["receipt_id"])
                current = _target(cur, fact) if fact.get("operation", "add") in ("update", "deprecate") else None
                if (fact.get("operation") in ("update", "deprecate") and
                    (not current or fixture.get("target_revision_seen") != current["revision"] or
                     fixture["packet"].get("state", {}).get("target_excerpt") != current["text"])):
                    raise Recheck(old["receipt_id"])
                if any(ref.get("type") == "code_test" and
                       code_changed_since(repo_root, unit["baseline_code_ref"], ref.get("locator")) is True
                       for ref in fact.get("evidence_refs", []) if isinstance(ref, dict)):
                    raise Recheck(old["receipt_id"])
                if old["receipt_id"] in stale and fixture.get("baseline_history_seen") != history_max:
                    raise Recheck(old["receipt_id"])
                if old["receipt_id"] in stale and fact.get("operation", "add") == "add" and not fixture.get("fresh_excerpt"):
                    raise Recheck(old["receipt_id"])
                decision = runner.decide(fixture["packet"], fixture["answers"], operation=fact.get("operation", "add"))
                if decision["combined"] != old["combined"]:
                    return {"status": "needs_review", "receipt_ids": [old["receipt_id"]], "consistency_flags": flags}
                source = fact.get("evidence_source")
                if source == "user_confirmed" and fixture.get("utterance_status"):
                    source = policy.apply_utterance_status(source, fixture["utterance_status"])
                verdict = policy.evaluate({"combined": decision["combined"], "review_reasons": decision["review_reasons"],
                    "operation": fact.get("operation", "add"), "kind": fact.get("kind"), "evidence_source": source,
                    "conflict": False, "can_ask_now": fact.get("can_ask_now", False), "completion": True}, policies(cur, entry["host_id"]))
                prepared.append((entry, old, fact, fixture, current, verdict))
            if not apply:
                return {"status": "proposal", "consistency_flags": flags, "count": len(prepared)}
            actions = []
            embedding_pending = False
            for entry, old, fact, fixture, current, verdict in prepared:
                receipt_id = _receipt(cur, entry, old["fact_index"], fact, fixture, "digestion", current)
                action, operation = verdict["action"], fact.get("operation", "add")
                absorption_id, latest, ref = str(uuid4()), None, fact.get("target_ref")
                if action == "absorb":
                    cur.execute("select set_config('knowledge.actor',%s,true),set_config('knowledge.absorption_id',%s,true)",
                                ("acceptance", absorption_id))
                    if operation == "add":
                        # domain routed by digest_driver (domain_router); falls back to the worker's partition_key
                        domain = (fixture.get("domain_routed") or {}).get("domain") or entry["partition_key"]
                        cur.execute("""insert into knowledge.domain_type(host_id, domain, description) values (%s,%s,%s)
                                    on conflict (host_id, domain) do nothing""", (entry["host_id"], domain, fact.get("fact", "")[:200]))
                        fragment = store.build_fragment({**entry, "partition_key": domain}, old["fact_index"], fact.get("keywords", []),
                                                        [old["receipt_id"], receipt_id], store.now(), next_seq(cur, entry["host_id"], domain))
                        ref = fragment["id"]
                        cur.execute("""insert into knowledge.fragment(id,host_id,alias,domain,seq,text,keywords,kind,group_id,
                                    revision,active,confidence,source,valid_from,superseded_at)
                                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)""",
                                    (ref, fragment["host_id"], fragment["alias"], fragment["domain"], fragment["seq"],
                                     fragment["text"], fragment["keywords"], fragment["kind"], fragment["group_id"],
                                     1, True, fragment["confidence"], _json(fragment["source"]), fragment["valid_from"], None))
                        latest = 1
                        try:
                            vector = embed.encode_passages([fragment["text"]])[0]
                        except embed.EmbeddingUnavailable:
                            embedding_pending = True
                        else:
                            _upsert_embedding(cur, ref, latest, vector)
                    else:
                        cur.execute("""update knowledge.fragment set revision=revision+1,
                                    text=case when %s='update' then %s else text end,
                                    active=case when %s='deprecate' then false else active end
                                    where id=%s and revision=%s returning revision""",
                                    (operation, fact["fact"], operation, ref, current["revision"]))
                        updated = cur.fetchone()
                        if not updated:
                            raise Recheck(old["receipt_id"])
                        latest = updated[0]
                        if operation == "update":
                            try:
                                vector = embed.encode_passages([fact["fact"]])[0]
                            except embed.EmbeddingUnavailable:
                                embedding_pending = True
                            else:
                                _upsert_embedding(cur, ref, latest, vector)
                decision = {"absorb": "absorbed", "retain_as_evidence": "retained_as_evidence", "reject": "rejected"}.get(action, "retained_as_evidence")
                cur.execute("""insert into knowledge.absorption(absorption_id,work_unit_id,entry_id,fact_index,
                            digestion_receipt_id,proposal,decision,decided_by,rule_id,action,fragment_ref,fragment_revision_after)
                            values (%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s)""",
                            (absorption_id, unit_id, entry["entry_id"], old["fact_index"], receipt_id,
                             _json({"action": operation, "target": ref, "text": fact["fact"], "scope_caveat": None, "review_flags": []}),
                             decision, "acceptance_policy", verdict["rule_id"], action, ref if latest else None, latest))
                if action == "queue_for_human":
                    cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason)
                                values (%s,%s,%s,%s)""", (entry["entry_id"], old["fact_index"], verdict["rule_id"], "policy requires confirmation"))
                _transition(cur, entry, {"absorb": "absorbed", "retain_as_evidence": "retained_as_evidence",
                                          "reject": "closed"}.get(action, "review_queue"), "acceptance", receipt_id)
                actions.append(action)
            return {"status": "absorbed" if actions and all(a == "absorb" for a in actions) else "processed", "count": len(prepared), "embedding_pending": embedding_pending}
    except Recheck as error:
        return {"status": "needs_recheck", "receipt_ids": [error.receipt], "consistency_flags": []}


def stats(dsn):
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select template_version,answers from knowledge.check_receipt")
        groups = {}
        for version, answers in cur.fetchall():
            for name, answer in answers.items():
                group = groups.setdefault((version, name), {"total": 0, "referred": 0, "flat": 0})
                group["total"] += 1
                if answer["type"] == "choice":
                    probabilities = sorted(answer["probabilities"].values(), reverse=True)
                    flat = len(probabilities) < 2 or probabilities[0] - probabilities[1] < .15
                    escaped = "none_or_uncertain" in str(answer.get("choice", ""))
                else:
                    value = float(answer.get("noul", answer.get("value")))
                    flat, escaped = .35 <= value <= .65, False
                group["flat"] += int(flat)
                group["referred"] += int(flat or escaped)
        return [{"template_version": version, "question": name, **value}
                for (version, name), value in sorted(groups.items())]
