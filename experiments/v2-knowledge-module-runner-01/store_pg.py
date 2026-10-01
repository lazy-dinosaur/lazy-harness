"""PostgreSQL storage for the offline knowledge runner (DSN supplied explicitly)."""
import json
import re
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
    import fact_text  # schema-delta '임베딩은 한국어 보기로': questions are Korean, operator text is the stored form
    text = fact_text.view(text)
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
                     "ledger_entry_event", "check_receipt", "absorption", "confirmation_queue", "question_template", "subject",
                     "fragment_leaf"}:
        raise ValueError("unknown table")
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(f"select * from knowledge.{table}")
        return _rows(cur)


def policies(cur, host_id):
    """Acceptance rules are fixed harness behavior (user-confirmed 2026-09-28): no per-host override.
    knowledge.acceptance_policy rows (seeded copy, any host rows) are ignored; the code defaults win."""
    return policy.DEFAULT_POLICY


def _transition(cur, entry, state, actor, receipt_ref=None):
    old = entry["state"]
    cur.execute("update knowledge.ledger_entry set state=%s where entry_id=%s", (state, entry["entry_id"]))
    cur.execute('insert into knowledge.ledger_entry_event(entry_id,"from","to",actor,receipt_ref) values (%s,%s,%s,%s,%s)',
                (entry["entry_id"], old, state, actor, receipt_ref))
    entry["state"] = state


RECORDISH = ("record", "update_record", "deprecate_record")
REVIEW_RULE = "worktime_review"
BATCH_DUP_RULE = "digest_batch_duplicate"
CANON_DUP_RULE = "digest_canon_duplicate"  # same subject, same condition, same result sentences
DIGEST_RULE = "digestion_review"
REVIEWABLE = ("review_queue", "provisional", "eligible", "absorbed", "retained_as_evidence")


def _review_answers(cur, entry_id):
    cur.execute("""select fact_index,answer from knowledge.confirmation_queue
                   where entry_id=%s and rule_id=any(%s) and status='answered'""", (entry_id, [REVIEW_RULE, DIGEST_RULE]))
    return {index: json.loads(answer).get("decision") for index, answer in cur.fetchall()}


def _pending_digest(cur, entry_id):
    cur.execute("""select fact_index from knowledge.confirmation_queue
                   where entry_id=%s and rule_id=%s and status='pending'""", (entry_id, DIGEST_RULE))
    return {row[0] for row in cur.fetchall()}


def _absorbed_facts(cur, entry_id):
    cur.execute("select fact_index from knowledge.absorption where entry_id=%s", (entry_id,))
    return {row[0] for row in cur.fetchall()}


def review_list(dsn, host):
    """Worktime needs_review facts still waiting for a human decision (fact level)."""
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select e.entry_id::text,e.work_unit_id::text,e.state::text,e.judgement_body,r.fact_index,r.review_reasons
                    from knowledge.check_receipt r join knowledge.ledger_entry e on e.entry_id=r.entry_id
                    join knowledge.work_unit w on w.work_unit_id=e.work_unit_id
                    where e.host_id=%s and r.stage='worktime' and r.combined='needs_review'
                    and e.state::text = any(%s) and w.status<>'abandoned'
                    and not exists (select 1 from knowledge.confirmation_queue q where q.entry_id=r.entry_id
                      and q.fact_index=r.fact_index and q.rule_id=%s and q.status='answered')
                    order by e.created_at,r.fact_index""", (host, list(REVIEWABLE), REVIEW_RULE))
        rows = _rows(cur)
        # Digestion recheck disagreed with the worktime check: parked per fact, never per unit.
        seen_stale = set()
        cur.execute("""select e.entry_id::text,e.work_unit_id::text,e.state::text,e.judgement_body,q.fact_index,q.reason
                    from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
                    join knowledge.work_unit w on w.work_unit_id=e.work_unit_id
                    where e.host_id=%s and q.rule_id=%s and q.status='pending' and w.status<>'abandoned'
                    order by q.created_at,q.fact_index""", (host, DIGEST_RULE))
        for row in _rows(cur):
            reason = json.loads(row.pop("reason"))
            reasons_ = list(reason.get("reasons") or [])
            if any(str(x).startswith("stale_base") for x in reasons_):
                if row["work_unit_id"] in seen_stale:
                    continue  # one question per change (the whole work unit), not one per fragment or record
                seen_stale.add(row["work_unit_id"])
            rows.append({**row, "review_reasons": reasons_})
        items = [{"entry_id": row["entry_id"], "fact_index": row["fact_index"], "work_unit_id": row["work_unit_id"],
                 "entry_state": row["state"], "review_reasons": row["review_reasons"],
                 **{k: row["judgement_body"]["facts"][row["fact_index"]].get(k) for k in ("kind", "subject", "fact", "evidence_source")}}
                for row in rows]
        import fact_text  # the question the user sees is Korean; the stored text stays in operator form
        cur.execute("""select q.entry_id::text, q.fact_index, q.reason, e.work_unit_id::text from knowledge.confirmation_queue q
                    join knowledge.ledger_entry e on e.entry_id=q.entry_id
                    where e.host_id=%s and q.rule_id='canon_contradiction' and q.status='pending' order by q.created_at""", (host,))
        for eid, idx, reason, wu in cur.fetchall():
            r = json.loads(reason)
            cur.execute("select alias, text from knowledge.fragment where host_id=%s and active and alias = any(%s)",
                        (host, [r["alias"], r["with"]]))
            now = dict(cur.fetchall())
            if now.get(r["alias"]) != r["text"] or now.get(r["with"]) != r["with_text"]:
                cur.execute("""update knowledge.confirmation_queue set status='answered',answered_at=now(),
                            answer=%s where entry_id=%s and fact_index=%s and rule_id='canon_contradiction' and status='pending'
                            and reason=%s""", (_json({"decision": "resolved", "by": "later change of one side"}), eid, idx, reason))
                continue
            # flow3 r4 (2026-10-01): one question per fragment, listing every fragment it contradicts (P2 raised 9 items)
            reason_line = f"canon_contradiction: [{r['with']}] {fact_text.view(r['with_text'])}"
            same = next((it for it in items if it.get("kind") == "contradiction" and it["entry_id"] == eid and it["fact_index"] == idx), None)
            if same:
                if reason_line not in same["review_reasons"]:
                    same["review_reasons"].append(reason_line)
                continue
            items.append({"entry_id": eid, "fact_index": idx, "work_unit_id": wu, "entry_state": "canon", "kind": "contradiction",
                          "subject": None, "evidence_source": None, "fact": f"[{r['alias']}] {fact_text.view(r['text'])}",
                          "review_reasons": [reason_line]})
        return items


def review_resolve(dsn, host, entry_id, fact_index, decision, quote, locator=None):
    """Record a human approve/reject for one needs_review fact and move the entry so digestion can proceed."""
    if decision not in ("approve", "reject"):
        raise ValueError("decision must be approve|reject")
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select e.entry_id::text,e.state::text,e.host_id,w.status::text as unit_status,w.completion_sources
                    from knowledge.ledger_entry e join knowledge.work_unit w on w.work_unit_id=e.work_unit_id
                    where e.entry_id=%s for update of e""", (entry_id,))
        entry = _row(cur)
        if not entry or entry["host_id"] != host:
            raise ValueError("entry not found for host")
        # Harness base rule (schema-delta '검수 승인은 그 사실을 보여 준 뒤의 답'): a completion confirmation
        # cannot approve a waiting fact; the answer must follow showing that fact to the user.
        norm = lambda t: " ".join(str(t or "").split())
        used = {norm((s.get("evidence") or {}).get("quote")) for s in (entry.pop("completion_sources") or []) if isinstance(s, dict)}
        if decision == "approve" and norm(quote) and norm(quote) in used:
            raise ValueError("the completion confirmation cannot approve a waiting fact; show the fact to the user and quote their answer")
        cur.execute("""select confirmation_id from knowledge.confirmation_queue where entry_id=%s and fact_index=%s
                    and rule_id='canon_contradiction' and status='pending' order by confirmation_id""", (entry_id, fact_index))
        canon = [r[0] for r in cur.fetchall()]
        if canon:  # one answer for the grouped question closes every listed contradiction (the fix is a new record)
            cur.execute("update knowledge.confirmation_queue set status='answered',answer=%s,answered_at=now() where confirmation_id = any(%s)",
                        (_json({"decision": decision, "quote": quote, "locator": locator}), canon))
            return {"entry_id": entry_id, "fact_index": fact_index, "decision": decision, "entry_state": entry["state"],
                    "pending_in_entry": 0, "kind": "contradiction",
                    "next": "Now write the fix the user chose: knowledge_record update/deprecate of the wrong fragment ([alias@revision])."}
        if entry["state"] not in REVIEWABLE or entry["unit_status"] == "abandoned":
            raise ValueError(f"entry is not reviewable in state {entry['state']}")
        receipts = {r["fact_index"]: r for r in _receipts(cur, entry_id, "worktime")}
        answers, parked, done = _review_answers(cur, entry_id), _pending_digest(cur, entry_id), _absorbed_facts(cur, entry_id)
        waiting = lambda i: receipts[i]["combined"] == "needs_review" or i in parked
        if fact_index not in receipts or not waiting(fact_index) or fact_index in done:
            raise ValueError("fact is not waiting for review")
        if fact_index in answers and fact_index not in parked:
            raise ValueError("fact already resolved")
        # a fact asked again (another unit changed the fragment after the approval, P0-3) takes the new answer
        answer = _json({"decision": decision, "quote": quote, "locator": locator})
        bulk = {}  # other entries of the unit answered by this one stale-base answer
        if fact_index in parked:
            cur.execute("""update knowledge.confirmation_queue set status='answered',answer=%s,answered_at=now()
                        where entry_id=%s and fact_index=%s and rule_id=%s and status='pending'""",
                        (answer, entry_id, fact_index, DIGEST_RULE))
            # a stale-base answer is about the whole change: it answers every stale-base question of the work unit
            cur.execute("""select q.entry_id::text, q.fact_index from knowledge.confirmation_queue q
                        join knowledge.ledger_entry e on e.entry_id=q.entry_id
                        where e.work_unit_id=(select work_unit_id from knowledge.ledger_entry where entry_id=%s)
                        and q.rule_id=%s and q.status='pending' and q.reason like '%%stale_base%%'""", (entry_id, DIGEST_RULE))
            for other_entry, other in cur.fetchall():
                cur.execute("""update knowledge.confirmation_queue set status='answered',answer=%s,answered_at=now()
                            where entry_id=%s and fact_index=%s and rule_id=%s and status='pending'""",
                            (answer, other_entry, other, DIGEST_RULE))
                if other_entry == entry_id:
                    answers[other] = decision
                else:
                    bulk.setdefault(other_entry, {})[other] = decision
        else:
            cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason,status,answer,answered_at)
                        values (%s,%s,%s,%s,'answered',%s,now())""",
                        (entry_id, fact_index, REVIEW_RULE, _json(receipts[fact_index]["review_reasons"]), answer))
        answers[fact_index] = decision
        ready = "eligible" if entry["unit_status"] == "completed" else "provisional"
        pending = [i for i in receipts if waiting(i) and i not in answers]
        digestible = [i for i in receipts if i not in done and answers.get(i) != "reject"
                      and (answers.get(i) == "approve" or not waiting(i))]
        target = None
        if digestible and entry["state"] in ("review_queue", "absorbed", "retained_as_evidence"):
            target = ready
        elif entry["state"] == "review_queue" and not pending:
            target = "closed"
        if target:
            _transition(cur, entry, target, "human")
        for other_entry, decided in bulk.items():  # flow3 P2: reopen them too, or their changes never reach the canon
            _reopen(cur, other_entry, decided, ready)
        return {"entry_id": entry_id, "fact_index": fact_index, "decision": decision,
                "entry_state": entry["state"], "pending_in_entry": len(pending)}


def _reopen(cur, entry_id, decided, ready):
    """Move an entry whose waiting facts were answered (decided: {fact_index: decision}) so digestion picks it up."""
    cur.execute("select entry_id::text,state::text from knowledge.ledger_entry where entry_id=%s for update", (entry_id,))
    entry = _row(cur)
    receipts = {r["fact_index"]: r for r in _receipts(cur, entry_id, "worktime")}
    answers, parked, done = _review_answers(cur, entry_id), _pending_digest(cur, entry_id), _absorbed_facts(cur, entry_id)
    answers.update(decided)
    waiting = lambda i: receipts[i]["combined"] == "needs_review" or i in parked or i in decided
    pending = [i for i in receipts if waiting(i) and i not in answers]
    digestible = [i for i in receipts if i not in done and answers.get(i) != "reject"
                  and (answers.get(i) == "approve" or not waiting(i))]
    if digestible and entry["state"] in ("review_queue", "absorbed", "retained_as_evidence"):
        _transition(cur, entry, ready, "human")
    elif entry["state"] == "review_queue" and not pending:
        _transition(cur, entry, "closed", "human")


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
    decision = _command(runner.decide(packet, answers, operation=fact.get("operation", "add")), fact.get("operation", "add"))
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
                errors = runner.lint_fact(fact, strict_refs=True)["errors"]
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
                    decision = _command(runner.decide(fixture["packet"], fixture["answers"], operation=operation), operation)
                    outcomes.append({"fact_index": index, "receipt_id": receipt_id, "combined": decision["combined"]})
            if not outcomes or any("errors" in o for o in outcomes):
                state = "rejected_input"
            elif any("pending_fixture" in o for o in outcomes):
                state = "proposed"
            elif any(o["combined"] in RECORDISH for o in outcomes):
                # Fact-level review: needs_review facts wait for knowledge_review; the rest proceed.
                state = "provisional"
            elif any(o["combined"] == "needs_review" for o in outcomes):
                state = "review_queue"
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


def _command(decision, operation):
    """schema-delta '사용자에게 묻는 것은 모순뿐': a ledger record is the user's command. update/deprecate apply
    unless Jev is sure it changes nothing (duplicate); add is added unless it duplicates. No 'is it right?' review."""
    if decision["combined"] == "duplicate_skip":
        return decision
    combined = {"update": "update_record", "deprecate": "deprecate_record"}.get(operation, "record")
    return {**decision, "combined": combined, "review_reasons": []}


CANON_Q = ("items[{i}] 는 정본의 다른 사실이다. state.fact 와 items[{i}] 가 동시에 참일 수 없는가? "
           "둘 중 하나가 참이면 다른 하나가 반드시 거짓인 경우에만 true 다(같은 대상의 같은 속성에 서로 다른 값·규칙). 같은 값을 말함, 같은 대상의 다른 측면(예: 하나는 길이 제한, 하나는 라우팅 용도), 하나가 다른 하나를 보완·구체화, 서로 다른 대상이면 false.")
CONTRA_KEEP = 0.7  # modifications of the contradiction check (2026-09-30 retest): 0.5 flagged 11↔13, 11↔18 (not contradictions)


def _vector_contradictions(dsn, host, fid, text, asked, judge):
    """Top-6 hybrid neighbours not already compared by subject; skipped when both carry a form under different conditions.
    Judged on the Korean view of both facts."""
    import capture_audit
    import fact_form
    import fact_text
    hits = [h for h in search(dsn, host, fact_text.view(text), limit=6, mode="hybrid", expand=False)
            if str(h["id"]) != fid and h["alias"] not in asked]
    if not hits:
        return []
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select form from knowledge.fragment where id=%s", (fid,))
        own = cur.fetchone()[0]
        cur.execute("select id::text, form from knowledge.fragment where id = any(%s::uuid[])", ([str(h["id"]) for h in hits],))
        forms = dict(cur.fetchall())
    hits = [h for h in hits if not own or not forms.get(str(h["id"])) or fact_form.comparable(own, forms[str(h["id"])])]
    if not hits:
        return []
    answers = judge({"fact": fact_text.view(text)}, [fact_text.view(h["text"]) for h in hits], CANON_Q)
    return [{"alias": h["alias"], "text": h["text"]} for h, a in zip(hits, answers) if capture_audit._noul(a) >= CONTRA_KEEP]


def _leaf_pairs(cur, host, fid):
    """0010 + contra05: this fragment's result leaves vs other active fragments' result leaves of the same subject,
    compared only under the same condition or when either side is unconditional (rules under different conditions
    are not asked). -> [(own display, other display, other alias)], or None when the fragment has no leaves."""
    import fact_form
    cur.execute("""select l.text, l.subject_id::text, f.form from knowledge.fragment_leaf l join knowledge.fragment f
                   on f.id=l.fragment_id and l.revision=f.revision where f.id=%s and l.role='then' order by l.ord""", (fid,))
    own = cur.fetchall()
    if not own or own[0][2] is None:
        return None
    form = own[0][2]
    subjects = sorted({s for _, s, _ in own if s})
    if not subjects:
        return None
    cur.execute("""select f.alias, f.form, l.text, l.subject_id::text, f.text from knowledge.fragment_leaf l
                   join knowledge.fragment f on f.id=l.fragment_id and l.revision=f.revision
                   where f.host_id=%s and f.active and f.id<>%s and l.role='then' and l.subject_id = any(%s::uuid[])
                   order by f.updated_at desc limit 60""", (host, fid, subjects))
    mine, free = fact_form.condition_key(form), fact_form.unconditional(form)
    pairs = []
    for alias, oform, otext, osid, ofull in cur.fetchall():
        if not oform or not (free or fact_form.unconditional(oform) or fact_form.condition_key(oform) == mine):
            continue
        for text, sid, _ in own:
            if sid == osid:
                pairs.append((fact_form.display(form, text), fact_form.display(oform, otext), alias, ofull))
    return pairs


def scan_contradictions(dsn, unit_id, judge):
    """After digestion (schema-delta '사용자에게 묻는 것은 모순뿐'): every fragment this unit made canonical is compared
    with nearby canonical fragments; contradictions stay in the canon and are logged in confirmation_queue
    (rule canon_contradiction) so the next session asks the user. judge(state, texts, question) -> [{noul}]."""
    import capture_audit
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select a.entry_id::text, a.fact_index, a.fragment_ref::text, e.host_id from knowledge.absorption a
                    join knowledge.ledger_entry e on e.entry_id=a.entry_id
                    where a.work_unit_id=%s and a.decision::text='absorbed' and a.fragment_ref is not null
                    and not exists (select 1 from knowledge.confirmation_queue q where q.entry_id=a.entry_id
                                    and q.fact_index=a.fact_index and q.rule_id in ('canon_scanned','canon_contradiction'))""",
                    (unit_id,))
        todo = cur.fetchall()
    found = 0
    for eid, idx, fid, host in todo:
        with connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("select alias, text, active, subject_id::text from knowledge.fragment where id=%s", (fid,))
            row = cur.fetchone()
            group = []
            if row and row[2] and row[3]:  # same subject (schema-delta: contradiction = same subject id; contra02 false alarms 8 -> 3)
                cur.execute("""select id::text, alias, text from knowledge.fragment where host_id=%s and subject_id=%s
                               and active and id<>%s order by updated_at desc limit 30""", (host, row[3], fid))
                group = [{"id": r[0], "alias": r[1], "text": r[2]} for r in cur.fetchall()]
            leaf_pairs = _leaf_pairs(cur, host, fid) if row and row[2] else None
        bad = []
        if row and row[2] and leaf_pairs is not None:  # fragments with a stored form: leaf level, same condition
            by_own = {}
            for own, other, alias, full in leaf_pairs:
                # the log keeps the other fragment's whole stored text: review_list closes an item when that text changes
                # (flow3 2026-10-01: logging the leaf display closed real contradictions at once)
                by_own.setdefault(own, []).append({"alias": alias, "text": full, "shown": other})
            for own, others in by_own.items():
                answers = judge({"fact": own}, [o["shown"] for o in others], CANON_Q)
                bad += [o for o, a in zip(others, answers) if capture_audit._noul(a) >= CONTRA_KEEP]
            # flow3 r3 (2026-10-01): the same concept written under another subject never shows up in the leaf pairs
            # ('도메인 설명 길이' 1000 vs 'domain describe' 300 stayed silent) -> also the vector neighbours, same condition rule
            bad += _vector_contradictions(dsn, host, fid, row[1], {a for _, _, a, _ in leaf_pairs}, judge)
        elif row and row[2]:
            hits = group if row[3] else [h for h in search(dsn, host, row[1], limit=6, mode="hybrid", expand=False)
                                         if str(h["id"]) != fid]  # fragments from before the subject dictionary
            if hits:
                answers = judge({"fact": row[1]}, [h["text"] for h in hits], CANON_Q)
                bad = [h for h, a in zip(hits, answers) if capture_audit._noul(a) >= CONTRA_KEEP]
        with connect(dsn) as conn, conn.cursor() as cur:
            for h in bad:
                cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason)
                            values (%s,%s,'canon_contradiction',%s)""",
                            (eid, idx, _json({"alias": row[0], "text": row[1], "with": h["alias"], "with_text": h["text"]})))
            if not bad:
                cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason,status,answered_at)
                            values (%s,%s,'canon_scanned','{}','answered',now())""", (eid, idx))
        found += len(bad)
    return {"scanned": len(todo), "contradictions": found}


def _assign_subject(cur, host, fact, fixture):
    """Digestion is the dictionary's only writer: reuse the routed subject (and its name) or register the name."""
    import subject_dict
    name = fact.get("subject")
    if not isinstance(name, str) or not name.strip():
        return None, fact
    routed = (fixture or {}).get("subject_routed") or {}
    if not routed.get("subject_id"):
        hit = subject_dict.lookup(cur, host, name)  # a spelling (or its core without 화면/기능/…) is already known
        if hit:
            routed = {"subject_id": hit["subject_id"], "name": hit["name"]}
    if routed.get("subject_id"):
        subject_dict.add_alias(cur, host, name, routed["subject_id"])
        text = subject_dict.rewrite(fact["fact"], name, routed["name"])
        if routed["name"] != name and routed["name"] in text:
            fact, _ = runner.normalize_fact({**fact, "fact": text, "subject": routed["name"], "subject_as_written": name})
        return routed["subject_id"], fact
    return subject_dict.register(cur, host, name, routed.get("vector")), fact


def _form_of(fact):
    """0010: the stored form follows the text (a 3-way merge may have changed the text after the record parsed it)."""
    import fact_form
    return fact_form.parse(fact["fact"])


def _write_form(cur, host, fragment_id, revision, fact, subject_id):
    """0010: one fragment_leaf row per sentence; a leaf's subject is the fact subject when the leaf states it, otherwise
    the leaf's own head noun matched or registered in the dictionary (digestion is its only writer)."""
    import fact_form
    import subject_dict
    form = _form_of(fact)
    subject = fact.get("subject") if isinstance(fact.get("subject"), str) else ""
    for ord_, leaf in enumerate(fact_form.leaves(form)):
        sid = None
        if subject and subject in leaf["text"]:
            sid = subject_id
        else:
            head = runner.SUBJECT_HEAD.match(leaf["text"] + " ")
            if head and head.group(1).strip():
                sid = subject_dict.register(cur, host, head.group(1).strip())
        cur.execute("""insert into knowledge.fragment_leaf(fragment_id,revision,ord,role,text,subject_id,polarity)
                       values (%s,%s,%s,%s,%s,%s,%s)""", (fragment_id, revision, ord_, leaf["role"], leaf["text"], sid, leaf["polarity"]))


def _canon_duplicate(cur, host, fact, changing=frozenset()):
    """Alias of an active canonical fact of the same subject that is the same fact (dedup.same_fact), else None.
    Read only; the subject is looked up, never registered here."""
    import dedup
    import subject_dict
    name = fact.get("subject")
    hit = subject_dict.lookup(cur, host, name) if isinstance(name, str) and name.strip() else None
    if not hit:
        return None
    cur.execute("""select id::text, alias, text, revision from knowledge.fragment where host_id=%s and subject_id=%s and active
                   order by updated_at desc limit 200""", (host, hit["subject_id"]))
    for fid, alias, text, revision in cur.fetchall():
        if fid in changing:
            continue  # updated or deprecated in this same pass (review P1): not part of the canon after the commit
        if dedup.same_fact(fact.get("fact"), text):
            return {"id": fid, "alias": alias, "revision": revision}
    return None


def units_to_scan(dsn, limit=5):
    """Units with absorbed fragments the canon scan has not marked (a scan that failed after the commit, review P1)."""
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select distinct a.work_unit_id::text from knowledge.absorption a
                       where a.decision::text='absorbed' and a.fragment_ref is not null
                       and not exists (select 1 from knowledge.confirmation_queue q where q.entry_id=a.entry_id
                                       and q.fact_index=a.fact_index and q.rule_id in ('canon_scanned','canon_contradiction'))
                       limit %s""", (limit,))
        return [r[0] for r in cur.fetchall()]


def _atomic(entry):
    body = entry["judgement_body"]
    return bool(body.get("atomic")) or any(f.get("operation") in ("update", "deprecate") for f in body.get("facts", []))


def digest(dsn, unit_id, apply=False, fixtures=None):
    # One transaction covers both the fresh recheck and every resulting write.
    class Recheck(Exception):
        def __init__(self, receipt, why="recheck"):
            self.receipt, self.why = receipt, why
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
            candidates = []
            rows_ = []
            change_waits = False
            for entry in _rows(cur):
                answers, done = _review_answers(cur, entry["entry_id"]), _absorbed_facts(cur, entry["entry_id"])
                parked = _pending_digest(cur, entry["entry_id"])
                cur.execute("""select fact_index, reason from knowledge.confirmation_queue where entry_id=%s and rule_id=%s
                            and status='answered' and reason like '%%stale_base%%' and answer like '%%"approve"%%'
                            order by answered_at""", (entry["entry_id"], DIGEST_RULE))
                stale_ok = {}  # fact_index -> the revision the user approved against (astra review P0-3)
                for i, why in cur.fetchall():
                    m = re.search(r"지금 r(\d+)", why or "")
                    if m:
                        stale_ok[i] = int(m.group(1))
                recs = _receipts(cur, entry["entry_id"], "worktime")
                facts_ = entry["judgement_body"]["facts"]
                for r in recs:
                    i = r["fact_index"]
                    waits = i in parked or (r["combined"] == "needs_review" and answers.get(i) != "approve")
                    if waits and i not in done and answers.get(i) != "reject" and facts_[i].get("operation") in ("update", "deprecate"):
                        change_waits = True
                rows_.append((entry, answers, done, parked, stale_ok, recs))
            # astra review P0-1: a waiting change parked in review_queue, or an entry not checked yet, still belongs to
            # this commit; reading only eligible/provisional let a later pass commit the rest of the unit.
            cur.execute("""select entry_id::text, state::text, judgement_body from knowledge.ledger_entry
                        where work_unit_id=%s and state in ('proposed','review_queue')""", (unit_id,))
            for eid_, st_, body_ in cur.fetchall():
                if st_ == "proposed":
                    return {"status": "waiting", "why": "an entry of the unit is not checked yet"}
                answers_, done_, parked_ = _review_answers(cur, eid_), _absorbed_facts(cur, eid_), _pending_digest(cur, eid_)
                for r_ in _receipts(cur, eid_, "worktime"):
                    i_ = r_["fact_index"]
                    waits_ = i_ in parked_ or (r_["combined"] == "needs_review" and answers_.get(i_) != "approve")
                    if (waits_ and i_ not in done_ and answers_.get(i_) != "reject"
                            and body_["facts"][i_].get("operation") in ("update", "deprecate")):
                        change_waits = True
            for entry, answers, done, parked, stale_ok, recs in rows_:
                for receipt in recs:
                    index = receipt["fact_index"]
                    fact = entry["judgement_body"]["facts"][index]
                    if index in done or answers.get(index) == "reject" or index in parked:
                        continue  # digested, rejected, or an open question on this fact
                    if receipt["combined"] == "needs_review" and answers.get(index) != "approve":
                        continue  # still waiting for the user
                    if change_waits:
                        continue  # the unit is one commit: nothing of it goes in while a change of it waits
                    receipt["human_approved"] = answers.get(index) == "approve"
                    receipt["stale_ok"] = stale_ok.get(index)
                    candidates.append((entry, receipt, fact))
            last = {}
            for k, (entry, receipt, fact) in enumerate(candidates):
                if fact.get("target_ref"):
                    last[fact["target_ref"]] = k
            # astra review P0-2: updates of one fragment in one unit all read the same revision; merging them in record
            # order keeps every change (an earlier change of another part is not lost to 'last wins'). Overlapping
            # edits go to the user once; an approved answer takes the last record as written.
            import merge_form
            groups = {}
            for k, (entry, receipt, fact) in enumerate(candidates):
                if fact.get("target_ref"):
                    groups.setdefault(fact["target_ref"], []).append(k)
            overlap = set()
            for tgt, ks in groups.items():
                if len(ks) < 2 or any(candidates[k][2].get("operation") != "update" for k in ks) or candidates[ks[-1]][1]["human_approved"]:
                    continue
                exp = candidates[ks[-1]][2].get("expected_revision")
                cur.execute("""select coalesce((select snapshot->>'text' from knowledge.fragment_history where fragment_id=%s and revision=%s),
                               (select text from knowledge.fragment where id=%s))""", (tgt, exp, tgt))
                base_text = cur.fetchone()[0]
                acc = candidates[ks[0]][2]["fact"]
                for k in ks[1:]:
                    acc, err = merge_form.merge(base_text, acc, candidates[k][2]["fact"])
                    if err:
                        break
                if err:
                    overlap.add(candidates[ks[-1]][1]["receipt_id"])
                else:
                    e_, r_, f_ = candidates[ks[-1]]
                    candidates[ks[-1]] = (e_, r_, {**f_, "fact": acc})
            superseded = [c for k, c in enumerate(candidates) if c[2].get("target_ref") and last[c[2]["target_ref"]] != k]
            candidates = [c for k, c in enumerate(candidates) if not (c[2].get("target_ref") and last[c[2]["target_ref"]] != k)]
            def write_superseded():
                for entry, receipt, fact in superseded:
                    cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason,status,answer,answered_at)
                                values (%s,%s,%s,%s,'answered',%s,now())""", (entry["entry_id"], receipt["fact_index"], DIGEST_RULE,
                                _json({"reasons": ["superseded_in_unit: 같은 작업의 나중 기록이 같은 조각을 다시 바꿈"]}),
                                _json({"decision": "reject", "superseded": True, "quote": None, "locator": None})))
                for e_id in {e["entry_id"] for e, _, _ in superseded}:
                    cur.execute("select entry_id::text,state::text,judgement_body from knowledge.ledger_entry where entry_id=%s", (e_id,))
                    ent = _row(cur)
                    ans_, done_ = _review_answers(cur, e_id), _absorbed_facts(cur, e_id)
                    if ent["state"] in ("eligible", "provisional") and all(
                            i in ans_ or i in done_ for i in range(len(ent["judgement_body"].get("facts", [])))):
                        _transition(cur, ent, "closed", "digester")
            flags = []
            history_max = _history_max(cur, unit["host_id"])
            cur.execute("select repo_locator from knowledge.host where host_id=%s", (unit["host_id"],))
            repo_root = cur.fetchone()[0]
            changed = unit["baseline_history_id"] is not None and history_max > unit["baseline_history_id"]
            stale = [r["receipt_id"] for _, r, f in candidates if
                     (r["target_fragment_id"] and
                      (not _target(cur, f) or _target(cur, f)["revision"] != r["target_revision_seen"])) or
                     (f.get("operation", "add") == "add" and changed)]
            if stale and not fixtures:
                return {"status": "needs_recheck", "receipt_ids": [r["receipt_id"] for _, r, _ in candidates], "consistency_flags": flags}
            if flags:
                return {"status": "needs_review", "consistency_flags": flags}
            if not candidates:
                return {"status": "noop"}
            if not fixtures:
                return {"status": "needs_recheck", "receipt_ids": [r["receipt_id"] for _, r, _ in candidates], "consistency_flags": flags}
            prepared, deferred = [], []
            for entry, old, fact in candidates:
                fixture = fixtures.get(old["receipt_id"])
                if not fixture or not runner.lint(fixture["packet"])["ok"]:
                    raise Recheck(old["receipt_id"], "no fixture or packet lint")
                current = _target(cur, fact) if fact.get("operation", "add") in ("update", "deprecate") else None
                if (fact.get("operation") in ("update", "deprecate") and
                    (not current or fixture.get("target_revision_seen") != current["revision"] or
                     fixture["packet"].get("state", {}).get("target_excerpt") != current["text"])):
                    raise Recheck(old["receipt_id"], "target revision/text changed since the check")
                if old["receipt_id"] in stale and fixture.get("baseline_history_seen") != history_max:
                    raise Recheck(old["receipt_id"], "canon changed (history)")
                if old["receipt_id"] in stale and fact.get("operation", "add") == "add" and not fixture.get("fresh_excerpt"):
                    raise Recheck(old["receipt_id"], "add excerpt stale")
                if old["receipt_id"] in overlap:
                    deferred.append((entry, old, {"combined": "needs_review",
                                                  "review_reasons": ["in_unit_overlap: 이 작업에서 같은 조각의 같은 부분을 두 번 다르게 바꿈 — 마지막 기록이 맞나"]}))
                    continue
                # expected version (EventStoreDB expectedVersion): the fragment changed after the worker read it
                exp = fact.get("expected_revision")
                if exp and current and current["revision"] != int(exp) and old.get("stale_ok") != current["revision"]:
                    import merge3
                    cur.execute("select snapshot->>'text' from knowledge.fragment_history where fragment_id=%s and revision=%s",
                                (current["id"], int(exp)))
                    base = cur.fetchone()
                    import merge_form  # leaf level first (schema-delta '잎 단위 3자 병합'), word level for text without a form
                    merged, err = merge_form.merge(base[0], current["text"], fact["fact"]) if base and base[0] is not None else (None, "no base")
                    if err is None and fact.get("operation") == "update":
                        fact = {**fact, "fact": merged}  # both changes kept (git 3-way merge)
                    else:
                        deferred.append((entry, old, {"combined": "needs_review",
                                                      "review_reasons": [f"stale_base: r{exp} 을 읽었는데 지금 r{current['revision']}"]}))
                        continue
                decision = _command(runner.decide(fixture["packet"], fixture["answers"], operation=fact.get("operation", "add")),
                                    fact.get("operation", "add"))
                if decision["combined"] == "duplicate_skip" and fact.get("operation") in ("update", "deprecate"):
                    import dedup
                    # review P1 (2026-10-01): a change is a command; it is skipped only when the code sees no change
                    if fact["operation"] == "deprecate" or not (current and dedup.same_fact(fact["fact"], current["text"])):
                        decision = {**decision, "combined": {"update": "update_record", "deprecate": "deprecate_record"}[fact["operation"]],
                                    "review_reasons": []}
                if (decision["combined"] == "duplicate_skip" and fact.get("operation", "add") == "add"
                        and fact.get("evidence_source") == "user_confirmed"):
                    # 2026-10-01 main canon split: 11 user-confirmed adds were dropped as Jev duplicates with no trace.
                    # A duplicate is not a contradiction, so the user is not asked: a confirmed fact is added unless the
                    # code finds the same fact (_canon_duplicate below keeps it as evidence of that fragment).
                    decision = {**decision, "combined": "record", "review_reasons": []}
                if False:  # no second-opinion review: the digestion judgement only filters duplicates
                    # Park only this fact for a human; the rest of the unit keeps digesting.
                    deferred.append((entry, old, decision))
                    continue
                source = fact.get("evidence_source")
                if source == "user_confirmed" and fixture.get("utterance_status"):
                    source = policy.apply_utterance_status(source, fixture["utterance_status"])
                verdict = policy.evaluate({"combined": decision["combined"], "review_reasons": decision["review_reasons"],
                    "operation": fact.get("operation", "add"), "kind": fact.get("kind"), "evidence_source": source,
                    "conflict": False, "can_ask_now": fact.get("can_ask_now", False), "completion": True}, policies(cur, entry["host_id"]))
                if old["human_approved"]:
                    verdict = {"rule_id": REVIEW_RULE, "action": "absorb"}
                prepared.append((entry, old, fact, fixture, current, verdict))
            if any(o_fact.get("operation") in ("update", "deprecate")
                   for e, o, _ in deferred for o_fact in [e["judgement_body"]["facts"][o["fact_index"]]]):
                prepared = []  # the unit is one commit: all or nothing
            if not apply:  # the preview writes nothing (astra review P0-2)
                return {"status": "proposal", "consistency_flags": flags, "count": len(prepared), "deferred": len(deferred)}
            if prepared:
                write_superseded()  # only in a pass that commits the surviving record
            for entry, old, decision in deferred:
                cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason)
                            values (%s,%s,%s,%s)""", (entry["entry_id"], old["fact_index"], DIGEST_RULE,
                            _json({"worktime": old["combined"], "recheck": decision["combined"],
                                   "reasons": decision["review_reasons"]})))
            moving = {entry["entry_id"] for entry, *_ in prepared}
            for entry in {e["entry_id"]: e for e, _, _ in deferred}.values():
                if entry["entry_id"] not in moving and entry["state"] != "review_queue":
                    _transition(cur, entry, "review_queue", "digester")
            actions = []
            embedding_pending = False
            # Same-pass duplicates (audit-01 flow: an add recorded mid-work was judged new against the old fragment, and
            # the update of that fragment in this same pass made it identical -> two fragments). The texts this pass is
            # about to make canonical are the reference; an identical add is kept as evidence instead of a new fragment.
            import dedup
            batch = [fact["fact"] for _, _, fact, _, _, verdict in prepared
                     if verdict["action"] == "absorb" and fact.get("operation") == "update"]
            changing = {str(fact.get("target_ref")) for _, _, fact, _, _, verdict in prepared
                        if verdict["action"] == "absorb" and fact.get("operation") in ("update", "deprecate")}
            for k, (entry, old, fact, fixture, current, verdict) in enumerate(prepared):
                if verdict["action"] == "absorb" and fact.get("operation", "add") == "add" and not old["human_approved"]:
                    same = _canon_duplicate(cur, entry["host_id"], fact, changing)
                    if same:
                        prepared[k] = (entry, old, fact, fixture, current,
                                       {"rule_id": CANON_DUP_RULE, "action": "retain_as_evidence", "already": same})
                    elif dedup.find_duplicate(fact["fact"], batch) is not None:
                        prepared[k] = (entry, old, fact, fixture, current, {"rule_id": BATCH_DUP_RULE, "action": "retain_as_evidence"})
                    else:
                        batch.append(fact["fact"])
            for entry, old, fact, fixture, current, verdict in prepared:
                receipt_id = _receipt(cur, entry, old["fact_index"], fact, fixture, "digestion", current)
                action, operation = verdict["action"], fact.get("operation", "add")
                absorption_id, latest, ref = str(uuid4()), None, fact.get("target_ref")
                if verdict.get("already"):  # 'already in canon as [alias@revision]': the absorption points at it
                    ref, latest = verdict["already"]["id"], verdict["already"]["revision"]
                if action == "absorb":
                    cur.execute("select set_config('knowledge.actor',%s,true),set_config('knowledge.absorption_id',%s,true)",
                                ("acceptance", absorption_id))
                    if operation == "add":
                        # domain routed by digest_driver (domain_router); falls back to the worker's partition_key
                        domain = (fixture.get("domain_routed") or {}).get("domain") or entry["partition_key"]
                        cur.execute("""insert into knowledge.domain_type(host_id, domain, description) values (%s,%s,%s)
                                    on conflict (host_id, domain) do nothing""", (entry["host_id"], domain, fact.get("fact", "")[:300]))
                        subject_id, fact = _assign_subject(cur, entry["host_id"], fact, fixture)
                        facts_now = list(entry["judgement_body"]["facts"])
                        facts_now[old["fact_index"]] = fact
                        fragment = store.build_fragment({**entry, "partition_key": domain,
                                                         "judgement_body": {**entry["judgement_body"], "facts": facts_now}},
                                                        old["fact_index"], fact.get("keywords", []),
                                                        [old["receipt_id"], receipt_id], store.now(), next_seq(cur, entry["host_id"], domain))
                        ref = fragment["id"]
                        cur.execute("""insert into knowledge.fragment(id,host_id,alias,domain,seq,text,keywords,kind,group_id,
                                    revision,active,confidence,source,valid_from,superseded_at,subject_id,form)
                                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s::jsonb)""",
                                    (ref, fragment["host_id"], fragment["alias"], fragment["domain"], fragment["seq"],
                                     fragment["text"], fragment["keywords"], fragment["kind"], fragment["group_id"],
                                     1, True, fragment["confidence"], _json(fragment["source"]), fragment["valid_from"], None,
                                     subject_id, _json(_form_of(fact))))
                        latest = 1
                        _write_form(cur, entry["host_id"], ref, 1, fact, subject_id)
                        try:
                            vector = embed.encode_passages([_embedding_input(None, None, [], fragment["text"], "plain")])[0]
                        except embed.EmbeddingUnavailable:
                            embedding_pending = True
                        else:
                            _upsert_embedding(cur, ref, latest, vector)
                    else:
                        subject_id = None
                        if operation == "update":
                            subject_id, fact = _assign_subject(cur, entry["host_id"], fact, fixture)
                        cur.execute("""update knowledge.fragment set revision=revision+1,
                                    text=case when %s='update' then %s else text end,
                                    active=case when %s='deprecate' then false else active end,
                                    subject_id=coalesce(%s::uuid, subject_id),
                                    form=case when %s='update' then %s::jsonb else form end
                                    where id=%s and revision=%s returning revision""",
                                    (operation, fact["fact"], operation, subject_id, operation,
                                     _json(_form_of(fact)) if operation == "update" else None, ref, current["revision"]))
                        updated = cur.fetchone()
                        if not updated:
                            raise Recheck(old["receipt_id"])
                        latest = updated[0]
                        if operation == "update":
                            _write_form(cur, entry["host_id"], ref, latest, fact, subject_id)
                        if operation == "update":
                            try:
                                vector = embed.encode_passages([_embedding_input(None, None, [], fact["fact"], "plain")])[0]
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
                             decision, "human" if old["human_approved"] else "acceptance_policy", verdict["rule_id"], action,
                             ref if latest else None, latest))
                if action == "queue_for_human":
                    cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason)
                                values (%s,%s,%s,%s)""", (entry["entry_id"], old["fact_index"], verdict["rule_id"], "policy requires confirmation"))
                _transition(cur, entry, {"absorb": "absorbed", "retain_as_evidence": "retained_as_evidence",
                                          "reject": "closed"}.get(action, "review_queue"), "acceptance", receipt_id)
                actions.append(action)
            status = ("deferred_to_review" if not actions else
                      "absorbed" if all(a == "absorb" for a in actions) and not deferred else "processed")
            return {"status": status, "count": len(prepared), "deferred": len(deferred), "embedding_pending": embedding_pending}
    except Recheck as error:
        return {"status": "needs_recheck", "receipt_ids": [error.receipt], "consistency_flags": [], "why": error.why}


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
