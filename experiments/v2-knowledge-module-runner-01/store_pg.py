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
    import subject_merge
    with connect(dsn) as conn, conn.cursor() as cur:
        subject_merge.lock_host(cur, host, exclusive=False)  # astra merge r2 P1-4: host lock before any question row
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
        cur.execute("""select q.entry_id::text, q.fact_index, q.reason, e.work_unit_id::text, q.confirmation_id
                    from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
                    where e.host_id=%s and q.rule_id='canon_contradiction' and q.status='pending' order by q.created_at""", (host,))
        for eid, idx, reason, wu, qid in cur.fetchall():
            r = json.loads(reason)
            cur.execute("select alias, text from knowledge.fragment where host_id=%s and active and alias = any(%s)",
                        (host, [r["alias"], r["with"]]))
            now = dict(cur.fetchall())
            if now.get(r["alias"]) != r["text"] or now.get(r["with"]) != r["with_text"]:
                # 0012: a changed side does not prove the contradiction is gone; withdraw the question, judge again
                cur.execute("""update knowledge.confirmation_queue set status='answered',answered_at=now(),
                            answer=%s, resolution='recheck' where confirmation_id=%s and status='pending'
                            and resolution='open' and reason=%s""",
                            (_json({"decision": "withdrawn", "by": "a side changed after it was asked"}), qid, reason))
                continue
            # flow3 r4 (2026-10-01): one question per fragment, listing every fragment it contradicts (P2 raised 9 items)
            reason_line = f"canon_contradiction: [{r['with']}] {fact_text.view(r['with_text'])}"
            same = next((it for it in items if it.get("kind") == "contradiction" and it["entry_id"] == eid and it["fact_index"] == idx), None)
            if same:
                if reason_line not in same["review_reasons"]:
                    same["review_reasons"].append(reason_line)
                same["question_ids"].append(qid)
                continue
            # astra direction review P1 (2026-10-01): the answer is bound to the questions shown (question_ids)
            items.append({"entry_id": eid, "fact_index": idx, "work_unit_id": wu, "entry_state": "canon", "kind": "contradiction",
                          "subject": None, "evidence_source": None, "fact": f"[{r['alias']}] {fact_text.view(r['text'])}",
                          "review_reasons": [reason_line], "question_ids": [qid]})
        # declared aliases whose evidence fragment changed or was retired: re-check them (never split automatically)
        cur.execute("""select a.alias, s.name, f.alias, f.active, f.revision, a.source_revision from knowledge.subject_alias a
                       join knowledge.subject s on s.subject_id=a.subject_id
                       join knowledge.fragment f on f.id=a.source_fragment_id
                       where a.host_id=%s and a.kind='declared' and (not f.active or f.revision <> a.source_revision)""", (host,))
        for alias_, sname, falias, factive, frev, srev in cur.fetchall():
            items.append({"entry_id": None, "fact_index": None, "work_unit_id": None, "entry_state": "canon",
                          "kind": "alias_recheck", "for": "parent", "subject": sname, "evidence_source": None,
                          "fact": f"별칭 '{alias_}' → '{sname}'",
                          "review_reasons": [f"alias_recheck: 근거 [{falias}] 가 " + ("폐기됐다" if not factive else f"r{srev} → r{frev} 로 바뀌었다")
                                             + ". 아직 같은 대상이면 aliases 를 다시 선언하고, 아니면 사용자에게 분리를 물는다"],
                          "question_ids": []})
        cur.execute("""select q.entry_id::text, q.fact_index, q.reason, e.work_unit_id::text, q.confirmation_id
                    from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
                    where e.host_id=%s and q.rule_id='alias_conflict' and q.status='pending' order by q.created_at""", (host,))
        import subject_dict
        import subject_merge
        conflicts = cur.fetchall()
        for eid, idx, reason, wu, qid in conflicts:
            r = json.loads(reason)
            ra, rname_a = subject_merge.root(cur, r.get("subject_id"))
            rb, rname_b = subject_merge.root(cur, r.get("other_id"))
            if ((ra, rb) != (r.get("subject_id"), r.get("other_id"))
                    or subject_merge.members(cur, ra) != r.get("members_a", [ra])
                    or subject_merge.members(cur, rb) != r.get("members_b", [rb])):
                # stage 2 (astra merge review P0-2): a question is about the two subject sets shown; once either changed
                # the old answer must not reach further -- withdraw it, and ask again about the current subjects if apart
                cur.execute("""update knowledge.confirmation_queue set status='answered', answered_at=now(), answer=%s
                               where confirmation_id=%s and status='pending' returning 1""",
                            (_json({"decision": "withdrawn", "by": "a subject was merged after it was asked"}), qid))
                if not cur.fetchone() or not ra or not rb or ra == rb:
                    continue  # another listing withdrew it first, or the two are one subject now
                r = {**r, "subject_id": ra, "subject": rname_a, "other_id": rb, "other": rname_b, "previous": qid,
                     "members_a": subject_merge.members(cur, ra), "members_b": subject_merge.members(cur, rb)}
                cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason)
                               values (%s,%s,'alias_conflict',%s) on conflict do nothing returning confirmation_id""",
                            (eid, idx, _json(r)))
                got = cur.fetchone()
                if not got:
                    continue
                qid = got[0]
            cur.execute("select name from knowledge.subject where subject_id=%s", (r.get("subject_id"),))
            sname = (cur.fetchone() or [r.get("subject")])[0]
            cur.execute("select name from knowledge.subject where subject_id=%s", (r.get("other_id"),))
            oname = (cur.fetchone() or [r.get("other")])[0]
            said = lambda sid: "; ".join(fact_text.view(t) for t in subject_dict.sentences(cur, sid)) or "(문장 없음)"
            # stage 2: the user decides (same merges the two subjects, different closes it, defer keeps it)
            items.append({"entry_id": eid, "fact_index": idx, "work_unit_id": wu, "entry_state": "canon",
                          "kind": "alias_conflict", "subject": sname, "evidence_source": None,
                          "fact": f"'{sname}' 와 '{oname}' 는 같은 대상인가? (별칭 '{r.get('alias')}' 선언)",
                          "review_reasons": [f"alias_conflict: '{sname}': {said(r.get('subject_id'))} / '{oname}': "
                                             f"{said(r.get('other_id'))}. 같다 → 두 주어를 합친다(되돌릴 수 있음), "
                                             "다르다 → 그대로, 보류 → 다음에 다시"],
                          "question_ids": [qid]})
        cur.execute("""select q.entry_id::text, q.fact_index, q.reason, e.work_unit_id::text, q.confirmation_id
                    from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
                    where e.host_id=%s and q.rule_id='canon_exception' and q.status='pending' order by q.created_at""", (host,))
        for eid, idx, reason, wu, qid in cur.fetchall():
            r = json.loads(reason)
            cur.execute("select alias, text from knowledge.fragment where host_id=%s and active and alias = any(%s)",
                        (host, [r["alias"], r["with"]]))
            now = dict(cur.fetchall())
            if now.get(r["alias"]) != r["text"] or now.get(r["with"]) != r["with_text"]:
                cur.execute("""update knowledge.confirmation_queue set status='answered', answered_at=now(), answer=%s
                            where confirmation_id=%s and status='pending'""",
                            (_json({"decision": "withdrawn", "by": "a side changed"}), qid))
                continue
            items.append({"entry_id": eid, "fact_index": idx, "work_unit_id": wu, "entry_state": "canon",
                          "kind": "exception_link", "for": "parent", "subject": None, "evidence_source": None,
                          "fact": f"[{r['alias']}] {fact_text.view(r['text'])}",
                          "review_reasons": [f"exception_link: [{r['with']}] {fact_text.view(r['with_text'])} — 기본값과 예외. "
                                             "기본값 조각을 'X EXCEPT WHEN 조건' 으로 고치면 하나로 읽힌다 (사용자에게 묻지 않는다)"],
                          "question_ids": [qid]})
        cur.execute("""select q.entry_id::text, q.fact_index, q.reason, e.work_unit_id::text, q.confirmation_id, q.answer
                    from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
                    where e.host_id=%s and q.rule_id='canon_contradiction' and q.status='answered' and q.resolution='open'
                    order by q.answered_at""", (host,))
        for eid, idx, reason, wu, qid, answer in cur.fetchall():
            r = json.loads(reason)
            items.append({"entry_id": eid, "fact_index": idx, "work_unit_id": wu, "entry_state": "canon",
                          "kind": "contradiction_fix_due", "subject": None, "evidence_source": None,
                          "fact": f"[{r['alias']}] {fact_text.view(r['text'])}",
                          "review_reasons": [f"fix_due: [{r['with']}] {fact_text.view(r['with_text'])} — 사용자 답: "
                                             + str((json.loads(answer or '{}')).get('quote'))],
                          "question_ids": [qid]})
        return items


def review_resolve(dsn, host, entry_id, fact_index, decision, quote, locator=None, question_ids=None):
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
        # astra P13 cross-review (2026-10-01): question_ids always mean a contradiction answer, never another review; the
        # shown rows are locked and closed atomically only while still pending, else the whole answer is refused.
        if question_ids is not None:
            shown = {int(q) for q in question_ids}
            if not shown:
                raise ValueError("contradiction: question_ids is empty")
            cur.execute("""select confirmation_id from knowledge.confirmation_queue where confirmation_id = any(%s)
                        and entry_id=%s and fact_index=%s and rule_id='canon_contradiction' and status='answered'
                        and resolution='open' for update""", (sorted(shown), entry_id, fact_index))
            due = {r[0] for r in cur.fetchall()}
            if due and due == shown:  # astra 0012 review P2: the fix is due; the user may still say it is not one
                if decision != "reject":
                    raise ValueError("already answered; write the fix record (the contradiction resolves when it is judged again)")
                cur.execute("""update knowledge.confirmation_queue set resolution='resolved', resolved_at=now(),
                            resolution_evidence=%s where confirmation_id = any(%s) and resolution='open'""",
                            (_json({"by": "user", "correction": True, "quote": quote, "locator": locator}), sorted(shown)))
                return {"entry_id": entry_id, "fact_index": fact_index, "decision": decision, "entry_state": entry["state"],
                        "pending_in_entry": None, "kind": "contradiction", "next": "Not a contradiction: resolved."}
            cur.execute("""select confirmation_id from knowledge.confirmation_queue where confirmation_id = any(%s)
                        and entry_id=%s and fact_index=%s and rule_id='canon_contradiction' and status='pending'
                        for update""", (sorted(shown), entry_id, fact_index))
            cur.execute("""update knowledge.confirmation_queue set status='answered',answer=%s,answered_at=now()
                        where confirmation_id = any(%s) and entry_id=%s and fact_index=%s
                        and rule_id='canon_contradiction' and status='pending' returning confirmation_id""",
                        (_json({"decision": decision, "quote": quote, "locator": locator}), sorted(shown), entry_id, fact_index))
            if {r[0] for r in cur.fetchall()} != shown:
                raise ValueError("contradiction question changed since it was listed; list again and ask the user")
            if decision == "reject":  # the user says the two facts do not contradict: that is a resolution with evidence
                cur.execute("""update knowledge.confirmation_queue set resolution='resolved', resolved_at=now(),
                            resolution_evidence=%s where confirmation_id = any(%s)""",
                            (_json({"by": "user", "quote": quote, "locator": locator}), sorted(shown)))
            cur.execute("select count(*) from knowledge.confirmation_queue where entry_id=%s and status='pending'", (entry_id,))
            left = cur.fetchone()[0]  # every pending question of the entry, any fact or rule
            return {"entry_id": entry_id, "fact_index": fact_index, "decision": decision, "entry_state": entry["state"],
                    "pending_in_entry": left, "kind": "contradiction",
                    "next": ("Not a contradiction: resolved." if decision == "reject" else
                             "Now write the fix the user chose: knowledge_record update/deprecate of the wrong fragment "
                             "([alias@revision]). The contradiction stays open until that change is digested and judged again.")}
        cur.execute("""select 1 from knowledge.confirmation_queue where entry_id=%s and fact_index=%s
                    and rule_id='canon_contradiction' and status='pending' limit 1""", (entry_id, fact_index))
        if cur.fetchone():
            raise ValueError("contradiction: pass question_ids exactly as listed by review list")
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
    if stage == "digestion" and fixture.get("subject_generation_seen") is not None:
        # astra merge r3 P1-1: a judgement made under another subject generation is a different receipt
        import hashlib
        key = hashlib.sha256(f"{key}/gen{fixture['subject_generation_seen']}".encode()).hexdigest()
    cur.execute("select receipt_id::text from knowledge.check_receipt where dedup_key=%s", (key,))
    cached = cur.fetchone()
    if cached:
        return cached[0]
    decision = _command(runner.decide(packet, answers, operation=fact.get("operation", "add")), fact.get("operation", "add"), packet)
    receipt_id = str(uuid4())
    cur.execute("""insert into knowledge.question_template(template_id,template_version,questions)
                   values (%s,%s,%s::jsonb) on conflict do nothing""",
                (packet["template_id"], packet["template_version"], _json(packet["questions"])))
    cur.execute("""insert into knowledge.check_receipt(receipt_id,entry_id,fact_index,stage,template_id,template_version,
                jev_model_requested,jev_model_actual,dedup_key,packet,answers,combined,review_reasons,
                target_fragment_id,target_revision_seen,input_tokens,output_tokens,cost_usd,usage_source,subject_generation)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s)""",
                (receipt_id, entry["entry_id"], index, stage, packet["template_id"], packet["template_version"],
                 fixture.get("jev_model_requested", model), model, key, _json(packet), _json(answers),
                 decision["combined"], _json(decision["review_reasons"]), current["id"] if current else None,
                 current["revision"] if current else None, fixture.get("input_tokens"), fixture.get("output_tokens"),
                 fixture.get("cost_usd"), fixture.get("usage_source", "unreported-by-tool"),
                 fixture.get("subject_generation_seen")))
    return receipt_id


def embed_unit(dsn, unit_id):
    """Embed the active fragments this unit absorbed that have no embedding for their current revision, after the commit
    and outside it (astra big review: embedding calls held the digestion transaction). -> count embedded; on an
    embedding outage nothing is written and the poller's embedding pass retries."""
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select distinct f.id::text, f.revision, f.text from knowledge.absorption a
                       join knowledge.fragment f on f.id=a.fragment_ref
                       left join knowledge.fragment_embedding e on e.fragment_id=f.id and e.revision=f.revision
                         and e.model_id=%s and e.embed_variant='plain'
                       where a.work_unit_id=%s and f.active and e.fragment_id is null""", (embed.MODEL_ID, unit_id))
        rows = cur.fetchall()
    done = 0
    if rows:
        try:
            vectors = embed.encode_passages([_embedding_input(None, None, [], t, "plain") for _, _, t in rows])
        except embed.EmbeddingUnavailable:
            vectors = None
        if vectors is not None:
            with connect(dsn) as conn, conn.cursor() as cur:
                for (fid, rev, _), vector in zip(rows, vectors):
                    cur.execute("select 1 from knowledge.fragment where id=%s and revision=%s", (fid, rev))
                    if cur.fetchone():  # still that revision
                        _upsert_embedding(cur, fid, rev, vector)
            done = len(rows)
    _embed_subjects(dsn, unit_id)  # independent of the passages (astra big review r3)
    return done


def backfill_subject_embeddings(dsn, host, limit=50):
    """Poller retry: subjects of the host registered without an embedding (digestion registers them without one; an
    embedding outage after the commit leaves them missing, and subject_dict.nearest skips them). -> count."""
    import subject_dict
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select s.subject_id::text, s.name from knowledge.subject s
                       left join knowledge.subject_embedding se on se.subject_id=s.subject_id and se.model_id=%s
                       where s.host_id=%s and se.subject_id is null order by s.created_at limit %s""",
                    (embed.MODEL_ID, host, limit))
        rows = cur.fetchall()
    if not rows:
        return 0
    vectors = embed.encode_queries([subject_dict.core(n) for _, n in rows])  # EmbeddingUnavailable -> caller
    with connect(dsn) as conn, conn.cursor() as cur:
        for (sid, _), v in zip(rows, vectors):
            cur.execute("""insert into knowledge.subject_embedding(subject_id,model_id,embedding) values (%s,%s,%s::extensions.vector)
                           on conflict (subject_id,model_id) do nothing""", (sid, embed.MODEL_ID, subject_dict._vec(v)))
    return len(rows)


def _embed_subjects(dsn, unit_id):
    """Subjects of the unit's fragments and leaves registered without an embedding (inside the digestion transaction)."""
    import subject_dict
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select distinct s.subject_id::text, s.name from knowledge.absorption a
                       join knowledge.fragment f on f.id=a.fragment_ref
                       join knowledge.fragment_leaf l on l.fragment_id=f.id
                       join knowledge.subject s on s.subject_id in (f.subject_id, l.subject_id)
                       left join knowledge.subject_embedding se on se.subject_id=s.subject_id and se.model_id=%s
                       where a.work_unit_id=%s and se.subject_id is null""", (embed.MODEL_ID, unit_id))
        rows = cur.fetchall()
    if not rows:
        return 0
    try:
        vectors = embed.encode_queries([subject_dict.core(n) for _, n in rows])
    except embed.EmbeddingUnavailable:
        return 0
    with connect(dsn) as conn, conn.cursor() as cur:
        for (sid, _), v in zip(rows, vectors):
            cur.execute("""insert into knowledge.subject_embedding(subject_id,model_id,embedding) values (%s,%s,%s::extensions.vector)
                           on conflict (subject_id,model_id) do nothing""", (sid, embed.MODEL_ID, subject_dict._vec(v)))
    return len(rows)


def cached_digestion_answers(dsn, items):
    """contra07 (2026-10-02): a large unit is judged over several passes. -> {worktime receipt id: saved judgement} for the
    items [(worktime receipt id, packet)] whose exact packet (same facts, same canon excerpt) was already judged at
    digestion. A packet that changed (the canon moved) is judged again."""
    out = {}
    with connect(dsn) as conn, conn.cursor() as cur:
        for rid, packet in items:
            cur.execute("""select r2.answers, r2.jev_model_requested, r2.jev_model_actual, r2.subject_generation
                           from knowledge.check_receipt r1
                           join knowledge.check_receipt r2 on r2.entry_id=r1.entry_id and r2.fact_index=r1.fact_index
                             and r2.stage='digestion' and r2.packet=%s::jsonb
                           where r1.receipt_id=%s order by r2.created_at desc limit 1""", (_json(packet), rid))
            row = cur.fetchone()
            if row:
                out[rid] = {"answers": row[0], "jev_model_requested": row[1], "jev_model_actual": row[2],
                            "subject_generation": row[3]}
    return out


def save_digestion_answers(dsn, saved):
    """Store judgements of a partial pass as digestion receipts (no canon write); the final pass reuses them.
    saved = {worktime receipt id: fixture with packet/answers/models}."""
    with connect(dsn) as conn, conn.cursor() as cur:
        for rid, fixture in saved.items():
            cur.execute("""select e.entry_id::text, e.host_id, e.partition_key, e.work_unit_id::text, e.judgement_id,
                           e.judgement_version, e.judgement_body, r.fact_index from knowledge.check_receipt r
                           join knowledge.ledger_entry e on e.entry_id=r.entry_id where r.receipt_id=%s""", (rid,))
            row = _row(cur)
            if not row:
                continue
            idx = row.pop("fact_index")
            fact = row["judgement_body"]["facts"][idx]
            current = _target(cur, fact) if fact.get("operation", "add") in ("update", "deprecate") else None
            _receipt(cur, row, idx, fact, fixture, "digestion", current)
    return len(saved)


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
                    decision = _command(runner.decide(fixture["packet"], fixture["answers"], operation=operation), operation,
                                        fixture["packet"])
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


def _command(decision, operation, packet=None):
    """schema-delta '사용자에게 묻는 것은 모순뿐': a ledger record is the user's command. update/deprecate apply
    unless Jev is sure it changes nothing (duplicate); no 'is it right?' review.
    contra06 (2026-10-02, user 'a'): a judge's duplicate alone never drops an add -- it closed v1/v2 and different-condition
    facts silently. The add is recorded and marked possible_duplicate; only the code's exact match (_canon_duplicate /
    same-pass dedup at digestion) keeps it as evidence instead of a new fragment; cleanup merges the rest later.
    Worktime and digestion share this one rule."""
    if decision["combined"] == "duplicate_skip":
        if operation == "add":
            return {**decision, "combined": "record", "review_reasons": [], "possible_duplicate": True}
        return decision
    combined = {"update": "update_record", "deprecate": "deprecate_record"}.get(operation, "record")
    return {**decision, "combined": combined, "review_reasons": []}


CANON_Q = ("items[{i}] 는 정본의 다른 사실이다. state.fact 와 items[{i}] 가 동시에 참일 수 없는가? "
           "둘 중 하나가 참이면 다른 하나가 반드시 거짓인 경우에만 true 다(같은 대상의 같은 속성에 서로 다른 값·규칙). 같은 값을 말함, 같은 대상의 다른 측면(예: 하나는 길이 제한, 하나는 라우팅 용도), 하나가 다른 하나를 보완·구체화, 서로 다른 대상이면 false.")
CONTRA_KEEP = 0.7  # modifications of the contradiction check (2026-09-30 retest): 0.5 flagged 11↔13, 11↔18 (not contradictions)


def _judged(items, answers):
    """astra direction review P1 (2026-10-01): zip() silently dropped the items a short judge answer did not cover and the
    fragment was still marked scanned. A count mismatch fails the scan; the poller retries it."""
    if not isinstance(answers, list) or len(answers) != len(items):
        raise ValueError(f"judge returned {len(answers) if isinstance(answers, list) else 'no list'} answers for {len(items)} items")
    return zip(items, answers)


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
    rel = {str(h["id"]): (fact_form.relation(own, forms[str(h["id"])]) if own and forms.get(str(h["id"])) else "compare")
           for h in hits}
    found = []
    for kind, q in (("compare", CANON_Q), ("exception", EXC_Q)):
        group = [h for h in hits if rel[str(h["id"])] == kind]
        if group:
            answers = judge({"fact": fact_text.view(text)}, [fact_text.view(h["text"]) for h in group], q)
            found += [{"alias": h["alias"], "text": h["text"], "kind": kind}
                      for h, a in _judged(group, answers) if capture_audit._noul(a) >= CONTRA_KEEP]
    return found  # kind 'exception' rows are parent hints, not contradictions (astra exc review: vector-only exceptions)


def _leaf_pairs(cur, host, fid, limit=60):
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
    # astra warn review: a leaf kept with a Korean connective may hold a second fact about another subject; such a
    # fragment is compared with the result leaves of every subject (bounded), not only its own subject's
    wide = any(fact_form.warnings(t) for t, _, _ in own)
    cur.execute("""select f.alias, f.form, l.text, l.subject_id::text, f.text from knowledge.fragment_leaf l
                   join knowledge.fragment f on f.id=l.fragment_id and l.revision=f.revision
                   where f.host_id=%s and f.active and f.id<>%s and l.role='then'
                   and (%s or l.subject_id = any(%s::uuid[]))
                   order by f.updated_at desc limit %s""", (host, fid, wide, subjects, limit))
    rows = cur.fetchall()
    if not wide:
        # astra warn review r2: an existing canon leaf kept with a warning may hold a fact about this subject under
        # another subject; recent warned leaves of other subjects are compared too (both directions)
        cur.execute("""select f.alias, f.form, l.text, l.subject_id::text, f.text from knowledge.fragment_leaf l
                       join knowledge.fragment f on f.id=l.fragment_id and l.revision=f.revision
                       where f.host_id=%s and f.active and f.id<>%s and l.role='then'
                       and not (l.subject_id = any(%s::uuid[])) order by f.updated_at desc limit 200""", (host, fid, subjects))
        warned = [r_ for r_ in cur.fetchall() if fact_form.warnings(r_[2])][:30]
        rows += warned
        warned_ids = {id(r_) for r_ in warned}
    else:
        warned_ids = set()
    pairs = []
    for row_ in rows:
        alias, oform, otext, osid, ofull = row_
        rel = fact_form.relation(form, oform) if oform else None
        if rel is None:
            continue
        for text, sid, _ in own:
            if sid == osid or wide or id(row_) in warned_ids:
                pairs.append((fact_form.display(form, text), fact_form.display(oform, otext), alias, ofull, rel))
    return pairs


EXC_Q = ("items[{i}] 와 state.fact 는 같은 대상의 같은 속성에 대해, 하나는 조건 없는 기본값이고 다른 하나는 특정 조건에서"
         " 다른 값·규칙을 말하는가(기본값의 예외)? 같은 값을 말함, 다른 속성, 다른 대상이면 false.")


def _scan_fragment(dsn, host, eid, idx, fid, judge, group_limit=30, leaf_limit=60, mark_scanned=True):
    """One canonical fragment against nearby canon (shared by unit scans and stage-2 rescans). -> (contradictions,
    subject generation judged under)."""
    import capture_audit
    import subject_merge
    with connect(dsn) as conn, conn.cursor() as cur:
        # astra 0012 round 3: a 'no contradiction' result is also a judgement of texts that may change meanwhile;
        # the canon history cursor before judging must be unchanged when the result is written
        # astra 0012 round 5: history ids are not commit-ordered; compare the (id, revision) of every active canon
        # fragment of the host before judging and under the final lock instead
        subject_merge.ensure_generation(cur, host)  # stage 2: a merge/undo during the judge calls fails this scan
        gen0 = subject_merge.generation(cur, host)
        cur.execute("select id::text, revision from knowledge.fragment where host_id=%s and active", (host,))
        seen_canon = dict(cur.fetchall())
        cur.execute("select alias, text, active, subject_id::text from knowledge.fragment where id=%s", (fid,))
        row = cur.fetchone()
        group = []
        if row and row[2] and row[3]:  # same subject (schema-delta: contradiction = same subject id; contra02 false alarms 8 -> 3)
            cur.execute("""select id::text, alias, text, form is null from knowledge.fragment where host_id=%s and subject_id=%s
                           and active and id<>%s order by updated_at desc limit %s""", (host, row[3], fid, group_limit))
            group = [{"id": r[0], "alias": r[1], "text": r[2], "no_form": r[3]} for r in cur.fetchall()]
        leaf_pairs = _leaf_pairs(cur, host, fid, limit=leaf_limit) if row and row[2] else None
    bad, exceptions = [], []
    if row and row[2] and leaf_pairs is not None:  # fragments with a stored form: leaf level, same condition
        by_own, by_own_exc = {}, {}
        for own, other, alias, full, rel in leaf_pairs:
            # the log keeps the other fragment's whole stored text: review_list closes an item when that text changes
            # (flow3 2026-10-01: logging the leaf display closed real contradictions at once)
            (by_own if rel == "compare" else by_own_exc).setdefault(own, []).append(
                {"alias": alias, "text": full, "shown": other})
        for own, others in by_own.items():
            answers = judge({"fact": own}, [o["shown"] for o in others], CANON_Q)
            bad += [o for o, a in _judged(others, answers) if capture_audit._noul(a) >= CONTRA_KEEP]
        # user 2026-10-02: a plain default and a conditional rule both stand; when the rule is an exception of the
        # default, the parent is told to write the default as 'X EXCEPT WHEN c' so a search never reads only one
        for own, others in by_own_exc.items():
            answers = judge({"fact": own}, [o["shown"] for o in others], EXC_Q)
            exceptions += [o for o, a in _judged(others, answers) if capture_audit._noul(a) >= CONTRA_KEEP]
        # flow3 r3 (2026-10-01): the same concept written under another subject never shows up in the leaf pairs
        # ('도메인 설명 길이' 1000 vs 'domain describe' 300 stayed silent) -> also the vector neighbours, same condition rule
        vec = _vector_contradictions(dsn, host, fid, row[1], {p_[2] for p_ in leaf_pairs}, judge)
        bad += [v for v in vec if v["kind"] == "compare"]
        exceptions += [v for v in vec if v["kind"] == "exception"]
        # astra merge r2 P1-5: a same-subject fragment without a stored form (pre-structure) has no leaves to pair; it is
        # compared by its whole text, so a merge rescan never skips it
        plain = [g for g in group if g["no_form"] and g["alias"] not in {p_[2] for p_ in leaf_pairs}]
        if plain:
            answers = judge({"fact": row[1]}, [g["text"] for g in plain], CANON_Q)
            bad += [g for g, a in _judged(plain, answers) if capture_audit._noul(a) >= CONTRA_KEEP]
    elif row and row[2]:
        hits = group if row[3] else [h for h in search(dsn, host, row[1], limit=6, mode="hybrid", expand=False)
                                     if str(h["id"]) != fid]  # fragments from before the subject dictionary
        if hits:
            answers = judge({"fact": row[1]}, [h["text"] for h in hits], CANON_Q)
            bad = [h for h, a in _judged(hits, answers) if capture_audit._noul(a) >= CONTRA_KEEP]
    bad = list({h["alias"]: h for h in bad}.values())
    with connect(dsn) as conn, conn.cursor() as cur:
        subject_merge.lock_host(cur, host, exclusive=False)  # lock order: host dictionary lock before rows
        # astra 0012 round 4: lock the host's active canon rows (FOR SHARE blocks any writer's UPDATE until this
        # commit), then check the cursor: a change before the lock is seen, a change after it waits for this write.
        # New fragments are not blocked; they are scanned with their own unit.
        cur.execute("select id::text, revision from knowledge.fragment where host_id=%s and active for share", (host,))
        if dict(cur.fetchall()) != seen_canon:  # FOR SHARE waits for an uncommitted writer, then sees its revision
            raise ValueError("the canon changed during the contradiction judge calls; scan again")
        if subject_merge.generation(cur, host, share=True) != gen0:  # astra merge review P1-5: revisions do not move on a merge
            raise ValueError("the subject dictionary changed (merge or undo) during the judge calls; scan again")
        for h in bad:
            cur.execute("select id::text, revision, text, active from knowledge.fragment where host_id=%s and alias=%s for share",
                        (host, h["alias"]))
            other_ = cur.fetchone()
            cur.execute("select revision, text, active from knowledge.fragment where id=%s for share", (fid,))
            own_rev, own_text, own_active = cur.fetchone()
            # astra 0012 round 2: record the revision of the text that was judged; a side changed during the judge
            # call fails this scan (rolled back, retried by the poller) instead of storing old text + new revision
            if not other_ or other_[2] != h["text"] or not other_[3] or own_text != row[1] or not own_active:
                raise ValueError("a side changed during the contradiction judge call; scan again")
            # 0012: the pair is identified by fragment ids and the revisions judged; one live question per pair
            cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason,resolution)
                        values (%s,%s,'canon_contradiction',%s,'open') on conflict do nothing""",
                        (eid, idx, _json({"alias": row[0], "text": row[1], "with": h["alias"], "with_text": h["text"],
                                          "id": fid, "rev": own_rev, "with_id": other_[0] if other_ else None,
                                          "with_rev": other_[1] if other_ else None})))
        for h in list({h["alias"]: h for h in exceptions}.values()):
            _add_exception(cur, host, eid, idx, row[0], row[1], h["alias"], h["text"])
        if not bad and mark_scanned:
            cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason,status,answered_at)
                        values (%s,%s,'canon_scanned','{}','answered',now())""", (eid, idx))
    return len(bad), gen0


def scan_contradictions(dsn, unit_id, judge):
    """After digestion (schema-delta '사용자에게 묻는 것은 모순뿐'): every fragment this unit made canonical is compared
    with nearby canonical fragments; contradictions stay in the canon and are logged in confirmation_queue
    (rule canon_contradiction) so the next session asks the user. judge(state, texts, question) -> [{noul}]."""
    import capture_audit  # noqa: F401 (used by _scan_fragment)
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
        found += _scan_fragment(dsn, host, eid, idx, fid, judge)[0]
    return {"scanned": len(todo), "contradictions": found}


def rescan_fragments(dsn, judge, limit=3):
    """Stage 2: fragments queued by a subject merge or undo are compared again with the (now joined) subject, with
    wider candidate limits (astra merge review P1-6). A judgement made under an older generation fails and retries."""
    done, failed = 0, 0
    if limit < 1:
        return {"rescanned": 0, "failed": 0}
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select fragment_id::text, host_id from knowledge.fragment_rescan where done_at is null
                       group by 1, 2 order by min(requested_at) limit %s""", (limit,))
        todo = cur.fetchall()
    for fid, host in todo:
        with connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""select a.entry_id::text, a.fact_index from knowledge.absorption a
                           where a.fragment_ref=%s and a.decision::text='absorbed' order by a.created_at desc limit 1""", (fid,))
            hit = cur.fetchone()
        try:
            if hit:  # a fragment with no absorption (pre-ledger) is still compared when its neighbours are rescanned
                # no candidate cap (astra merge r1 P1-6): every fragment of the joined subject is compared
                _, gen = _scan_fragment(dsn, host, hit[0], hit[1], fid, judge, group_limit=None, leaf_limit=None,
                                        mark_scanned=False)
                outcome = "scanned"
            else:
                # a pre-ledger fragment has no entry to hang a question on; it is still compared as the neighbour of every
                # rescanned fragment of the subject (two pre-ledger fragments stay unpaired -- known gap, open-gaps)
                outcome = "no_entry"
                with connect(dsn) as conn, conn.cursor() as cur:
                    cur.execute("select coalesce((select generation from knowledge.subject_generation where host_id=%s), 0)", (host,))
                    gen = cur.fetchone()[0]
            with connect(dsn) as conn, conn.cursor() as cur:
                cur.execute("""update knowledge.fragment_rescan set done_at=now(), outcome=%s where fragment_id=%s
                               and done_at is null and generation <= %s""", (outcome, fid, gen))
            done += 1
        except Exception:
            failed += 1
    return {"rescanned": done, "failed": failed}


def _add_exception(cur, host, eid, idx, alias, text, with_alias, with_text):
    """One pending exception hint per pair, in either direction (astra exc review: concurrent / two-sided duplicates)."""
    pair = sorted([alias, with_alias])
    cur.execute("select pg_advisory_xact_lock(hashtextextended(%s, 0))", (f"lh-exc/{host}/{pair[0]}/{pair[1]}",))
    cur.execute("""select q.confirmation_id, q.reason from knowledge.confirmation_queue q
                   join knowledge.ledger_entry e on e.entry_id=q.entry_id
                   where e.host_id=%s and q.rule_id='canon_exception' and q.status='pending'
                   and ((q.reason::jsonb->>'alias')=%s and (q.reason::jsonb->>'with')=%s
                        or (q.reason::jsonb->>'alias')=%s and (q.reason::jsonb->>'with')=%s)""",
                (host, alias, with_alias, with_alias, alias))
    texts = {alias: text, with_alias: with_text}
    for qid, reason in cur.fetchall():
        r = json.loads(reason)
        if texts.get(r["alias"]) == r["text"] and texts.get(r["with"]) == r["with_text"]:
            return False  # the same hint for the same texts is already pending
        # an older hint for older texts: withdrawn and replaced (astra exc review r2)
        cur.execute("""update knowledge.confirmation_queue set status='answered', answered_at=now(), answer=%s
                    where confirmation_id=%s and status='pending'""",
                    (_json({"decision": "withdrawn", "by": "replaced by a hint for the current texts"}), qid))
    cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason)
                values (%s,%s,'canon_exception',%s)""",
                (eid, idx, _json({"alias": alias, "text": text, "with": with_alias, "with_text": with_text})))
    return True


def _strict_noul(answer):
    """A judge score must be a finite number in [0, 1]; a missing or NaN score is a failure, never 'not contradicting'
    (astra 0012 review P1-3)."""
    import math
    v = answer.get("noul") if isinstance(answer, dict) else None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1:
        raise ValueError(f"judge score must be a number in [0,1], got {v!r}")
    return float(v)


_RECHECK_DUE = """from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
    where q.rule_id='canon_contradiction'
    and (q.rechecked_at is null or q.rechecked_at < now() - interval '5 minutes')  -- a failing row waits (astra 0012 r3)
    and (q.resolution='recheck' or (q.resolution='open' and exists (
      select 1 from knowledge.fragment f where f.host_id=e.host_id and (
        (f.id::text = (q.reason::jsonb)->>'id' and (f.revision::text <> (q.reason::jsonb)->>'rev' or not f.active)) or
        (f.id::text = (q.reason::jsonb)->>'with_id' and (f.revision::text <> (q.reason::jsonb)->>'with_rev' or not f.active)) or
        ((q.reason::jsonb)->>'id' is null and f.alias = (q.reason::jsonb)->>'alias' and (f.text <> (q.reason::jsonb)->>'text' or not f.active)) or
        ((q.reason::jsonb)->>'with_id' is null and f.alias = (q.reason::jsonb)->>'with' and (f.text <> (q.reason::jsonb)->>'with_text' or not f.active))))))"""


def _side(cur, host, fid, alias):
    """(id, text, revision, active, alias) of one side by fragment id (fragments are never deleted), else by alias (rows
    from before 0012). None when the alias is gone: that is unknown, never 'retired' (astra 0012 review P1-4)."""
    if fid:
        cur.execute("select id::text, text, revision, active, alias from knowledge.fragment where id=%s and host_id=%s for share",
                    (fid, host))
    else:
        cur.execute("select id::text, text, revision, active, alias from knowledge.fragment where alias=%s and host_id=%s for share",
                    (alias, host))
    return cur.fetchone()


def _merged_into(cur, host, side):
    """astra 0012 round 2: cleanup merges a fragment by rewriting the survivor and retiring the other in one transaction
    (same actor 'cleanup:*', same changed_at). -> the active survivor side, 'untracked' for a merge whose survivor is not
    found, or None when the retirement was a plain deprecation."""
    cur.execute("""select actor, changed_at from knowledge.fragment_history where fragment_id=%s and op='deprecate'
                   order by revision desc limit 1""", (side[0],))
    dep = cur.fetchone()
    if not dep or not (dep[0] or "").startswith("cleanup:"):
        return None
    cur.execute("""select h.fragment_id::text from knowledge.fragment_history h join knowledge.fragment f on f.id=h.fragment_id
                   where h.actor=%s and h.changed_at=%s and h.op='update' and h.fragment_id<>%s and f.host_id=%s and f.active""",
                (dep[0], dep[1], side[0], host))
    rows = cur.fetchall()
    return _side(cur, host, rows[0][0], None) if len(rows) == 1 else "untracked"


def recheck_contradictions(dsn, judge, limit=5):
    """0012: judge again the contradictions whose side changed (or retired) since they were judged, oldest-checked first.
    Retired side -> resolved; judged not contradicting -> resolved with the revisions judged; still contradicting ->
    this row is superseded (keeps its answer) and a new question is asked with the current texts. Applied with a
    revision CAS: a side that changed during the judge call is retried later. A failing row never blocks the others.
    An answer alone never resolves. -> counts."""
    import fact_text
    import subject_merge
    out = {"rechecked": 0, "resolved": 0, "reopened": 0, "failed": 0, "retried": 0}
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select q.confirmation_id " + _RECHECK_DUE +
                    " order by q.rechecked_at nulls first, q.confirmation_id limit %s", (limit,))
        due = [r[0] for r in cur.fetchall()]
    for qid in due:
        out["rechecked"] += 1
        try:
            with connect(dsn) as conn, conn.cursor() as cur:
                cur.execute("""select q.reason, q.resolution, e.host_id from knowledge.confirmation_queue q
                               join knowledge.ledger_entry e on e.entry_id=q.entry_id where q.confirmation_id=%s""", (qid,))
                reason, resolution, host = cur.fetchone()
                gen0 = subject_merge.generation(cur, host)  # astra merge r1 P1-5: a merge/undo meanwhile retries
                cur.execute("update knowledge.confirmation_queue set rechecked_at=now() where confirmation_id=%s", (qid,))
                r = json.loads(reason)
                a, b = _side(cur, host, r.get("id"), r["alias"]), _side(cur, host, r.get("with_id"), r["with"])
                merged = {}
                for name in ("a", "b"):
                    side = a if name == "a" else b
                    if side is not None and not side[3]:
                        succ = _merged_into(cur, host, side)
                        if succ == "untracked":
                            side = None  # merged but the survivor is unknown: stays unresolved
                        elif succ is not None:
                            merged[name] = side[4]
                            side = succ
                    if name == "a":
                        a = side
                    else:
                        b = side
            if a is None or b is None or a[0] == b[0]:
                out["failed"] += 1  # a side cannot be found or both merged into one: stays as is, never 'retired'
                continue
            seen = (a[2], b[2])
            if not a[3] or not b[3]:  # plainly deprecated (not a merge)
                verdict, evidence = "resolved", {"by": "a side retired", "ids": [a[0], b[0]], "revisions": list(seen)}
            else:
                import fact_form
                with connect(dsn) as conn, conn.cursor() as cur:
                    cur.execute("select id::text, form from knowledge.fragment where id = any(%s::uuid[])", ([a[0], b[0]],))
                    fm = dict(cur.fetchall())
                rel = fact_form.relation(fm[a[0]], fm[b[0]]) if fm.get(a[0]) and fm.get(b[0]) else "compare"
                if rel != "compare":
                    # astra exc review: e.g. an 'always' fact rewritten as a plain default -> default and exception now;
                    # a hint only when the judge confirms it is an exception (a different value), as a scan would (r2)
                    verdict = "resolved"
                    evidence = {"by": "no longer comparable", "relation": rel, "ids": [a[0], b[0]], "revisions": list(seen)}
                    if rel == "exception":
                        answers = judge({"fact": fact_text.view(a[1])}, [fact_text.view(b[1])], EXC_Q)
                        [(_, ans)] = list(_judged([b], answers))
                        evidence["is_exception"] = _strict_noul(ans) >= CONTRA_KEEP
                else:
                    answers = judge({"fact": fact_text.view(a[1])}, [fact_text.view(b[1])], CANON_Q)
                    [(_, ans)] = list(_judged([b], answers))
                    score = _strict_noul(ans)
                    verdict = "open" if score >= CONTRA_KEEP else "resolved"
                    evidence = {"by": "rejudged", "ids": [a[0], b[0]], "revisions": list(seen), "noul": score}
            with connect(dsn) as conn, conn.cursor() as cur:
                subject_merge.lock_host(cur, host, exclusive=False)
                cur.execute("select resolution, reason from knowledge.confirmation_queue where confirmation_id=%s for update", (qid,))
                now_res, now_reason = cur.fetchone()
                a2, b2 = _side(cur, host, a[0], r["alias"]), _side(cur, host, b[0], r["with"])
                if (now_res not in ("open", "recheck") or now_reason != reason or (a2[2], b2[2]) != seen
                        or subject_merge.generation(cur, host, share=True) != gen0):
                    out["retried"] += 1  # changed during the judge call: judged again on a later tick
                    continue
                if verdict == "resolved" and evidence.get("is_exception"):
                    cur.execute("select entry_id, fact_index from knowledge.confirmation_queue where confirmation_id=%s", (qid,))
                    e_, i_ = cur.fetchone()
                    _add_exception(cur, host, e_, i_, a[4], a[1], b[4], b[1])  # now a parent hint, not a question
                if verdict == "resolved":
                    cur.execute("""update knowledge.confirmation_queue set resolution='resolved', resolved_at=now(),
                                resolution_evidence=%s, status=case when status='pending'
                                then 'answered'::knowledge.confirmation_status else status end,
                                answered_at=coalesce(answered_at, now()) where confirmation_id=%s""", (_json(evidence), qid))
                    out["resolved"] += 1
                    continue
                if merged:
                    evidence["merged"] = merged
                same_text = not merged and r["text"] == a[1] and r["with_text"] == b[1]
                if same_text and resolution == "recheck":  # still the same pair, nothing new to ask: back to open
                    cur.execute("update knowledge.confirmation_queue set resolution='open' where confirmation_id=%s", (qid,))
                    continue
                # still contradicting with new text: keep this row (and its answer); ask a new question
                cur.execute("""select entry_id, fact_index from knowledge.confirmation_queue where confirmation_id=%s""", (qid,))
                entry_id_, fact_index_ = cur.fetchone()
                cur.execute("""update knowledge.confirmation_queue set resolution='superseded', resolved_at=now(),
                            resolution_evidence=%s, status=case when status='pending'
                            then 'answered'::knowledge.confirmation_status else status end,
                            answered_at=coalesce(answered_at, now()) where confirmation_id=%s""",
                            (_json({**evidence, "by": "asked again with the current texts"}), qid))
                cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason,resolution)
                            values (%s,%s,'canon_contradiction',%s,'open') on conflict do nothing returning confirmation_id""",
                            (entry_id_, fact_index_, _json({**r, "alias": a[4], "with": b[4], "text": a[1], "with_text": b[1],
                                                            "id": a[0], "rev": seen[0], "with_id": b[0], "with_rev": seen[1],
                                                            "previous": qid})))
                out["reopened"] += 1
        except Exception:
            out["failed"] += 1  # this row only; rechecked_at moved it to the back of the queue
    return out


def _assign_subject(cur, host, fact, fixture):
    """Digestion is the dictionary's only writer: reuse the routed subject (and its name) or register the name."""
    import subject_dict
    name = fact.get("subject")
    if not isinstance(name, str) or not name.strip():
        return None, fact
    routed = (fixture or {}).get("subject_routed") or {}
    # astra alias r2: the dictionary as it is now (under the spelling lock) wins over a routing decided before this
    # transaction -- another digestion may have declared this name an alias of another subject meanwhile
    subject_dict._lock_name(cur, host, name)
    hit = subject_dict.lookup(cur, host, name)  # a spelling (or its core without 화면/기능/…) is already known
    if hit and hit.get("kind") in ("declared", "merged"):
        return hit["subject_id"], fact  # a declared or merged other name: same subject id, the text keeps the written name
    if hit:
        routed = {"subject_id": hit["subject_id"], "name": hit["name"]}
    if routed.get("subject_id"):  # stage 2: a routing decided before a merge goes to the surviving subject
        import subject_merge
        rid, rname = subject_merge.root(cur, routed["subject_id"])
        if rid and rid != routed["subject_id"]:
            return rid, fact  # the routed name was merged away: keep the written text, use the survivor's id
    if routed.get("subject_id"):
        subject_dict.add_alias(cur, host, name, routed["subject_id"])
        text = subject_dict.rewrite(fact["fact"], name, routed["name"])
        if routed["name"] != name and routed["name"] in text:
            fact, _ = runner.normalize_fact({**fact, "fact": text, "subject": routed["name"], "subject_as_written": name})
        return routed["subject_id"], fact
    return subject_dict.register(cur, host, name, routed.get("vector"), allow_embed=False), fact


def _register_aliases(cur, host, entry_id, fact_index, fact, subject_id, fragment_id, revision):
    """Stage 1: the fact's declared aliases become declared aliases of its subject; a name already mapped to another
    subject is logged as 'alias_conflict' (a parent hint; merging two subjects is stage 2, with approval)."""
    import subject_dict
    import subject_merge
    if not subject_id:
        return
    for alias in fact.get("aliases") or []:
        outcome, hit = subject_dict.add_declared_alias(cur, host, alias, subject_id, fragment_id, revision)
        if outcome == "conflict":
            cur.execute("""insert into knowledge.confirmation_queue(entry_id,fact_index,rule_id,reason)
                        values (%s,%s,'alias_conflict',%s)""",
                        (entry_id, fact_index, _json({"alias": alias, "subject": fact.get("subject"),
                                                      "subject_id": subject_id, "other": hit and hit["name"],
                                                      "other_id": hit and hit["subject_id"], "fragment": fragment_id,
                                                      # stage 2: the answer binds to these two subject sets
                                                      "members_a": subject_merge.members(cur, subject_id),
                                                      "members_b": subject_merge.members(cur, hit and hit["subject_id"])})))


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
                sid = subject_dict.register(cur, host, head.group(1).strip(), allow_embed=False)
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


_UNSCANNED = """from knowledge.absorption a where a.decision::text='absorbed' and a.fragment_ref is not null
               and not exists (select 1 from knowledge.confirmation_queue q where q.entry_id=a.entry_id
                               and q.fact_index=a.fact_index and q.rule_id in ('canon_scanned','canon_contradiction'))"""


def units_to_scan(dsn, limit=5, after=None, with_key=False):
    """Units with absorbed fragments the canon scan has not marked, oldest absorption first (FIFO: a new unit never
    overtakes an older one, astra P13 round 3). Page with after=(key) of the last row; with_key returns (unit, key)."""
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select u, to_char(t, 'YYYYMMDDHH24MISSUS') || '/' || u as k from (
                         select a.work_unit_id::text as u, min(a.created_at) as t """ + _UNSCANNED + """
                         group by a.work_unit_id) x
                       where (%s::text is null or to_char(t, 'YYYYMMDDHH24MISSUS') || '/' || u > %s)
                       order by k limit %s""", (after, after, limit))
        rows = cur.fetchall()
        return [(r[0], r[1]) for r in rows] if with_key else [r[0] for r in rows]


def unscanned(dsn, unit_ids):
    """The subset of unit_ids that still has an unscanned absorbed fragment (exact check for hint pruning)."""
    if not unit_ids:
        return set()
    with connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select distinct a.work_unit_id::text " + _UNSCANNED + " and a.work_unit_id = any(%s::uuid[])",
                    (list(unit_ids),))  # uuid compare (uses the column index)
        return {r[0] for r in cur.fetchall()}


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
            import subject_merge
            cur.execute("select host_id from knowledge.work_unit where work_unit_id=%s", (unit_id,))
            host_row = cur.fetchone()
            if host_row:  # astra merge r1 P1-4: the host dictionary lock first, exclusive -- digestion writes the dictionary
                subject_merge.lock_host(cur, host_row[0], exclusive=True)
            cur.execute("""select status::text,host_id,baseline_history_id,baseline_code_ref
                        from knowledge.work_unit where work_unit_id=%s for update""", (unit_id,))
            unit = _row(cur)
            if not unit or unit["status"] != "completed":
                return {"status": "not_completed"}
            subject_gen = subject_merge.generation(cur, unit["host_id"])
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
            # astra direction review P1 (2026-10-01): one final change plan. The adds of this unit are judged against
            # the canon this commit leaves: merged updates, deprecations, nothing superseded or overlapping.
            rewrites = {str(f["target_ref"]): (f["fact"] if f.get("operation") == "update" else None)
                        for _, r, f in candidates if f.get("target_ref") and f.get("operation") in ("update", "deprecate")
                        and r["receipt_id"] not in overlap}
            if stale and not fixtures:
                return {"status": "needs_recheck", "receipt_ids": [r["receipt_id"] for _, r, _ in candidates],
                        "consistency_flags": flags, "rewrites": rewrites}
            if flags:
                return {"status": "needs_review", "consistency_flags": flags}
            if not candidates:
                return {"status": "noop"}
            if not fixtures:
                return {"status": "needs_recheck", "receipt_ids": [r["receipt_id"] for _, r, _ in candidates],
                        "consistency_flags": flags, "rewrites": rewrites}
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
                if fixture.get("subject_generation_seen") != subject_gen:  # missing, or a merge/undo since (astra merge r3 P1-2)
                    raise Recheck(old["receipt_id"], "subject dictionary changed (merge or undo)")
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
                                    fact.get("operation", "add"), fixture["packet"])
                if decision["combined"] == "duplicate_skip" and fact.get("operation") in ("update", "deprecate"):
                    import dedup
                    # review P1 (2026-10-01): a change is a command; it is skipped only when the code sees no change
                    if fact["operation"] == "deprecate" or not (current and dedup.same_fact(fact["fact"], current["text"])):
                        decision = {**decision, "combined": {"update": "update_record", "deprecate": "deprecate_record"}[fact["operation"]],
                                    "review_reasons": []}
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
                        if ((old.get("packet") and old.get("answers") is not None and  # the worktime judge said duplicate
                             runner.decide(old["packet"], old["answers"], operation="add")["combined"] == "duplicate_skip") or
                                runner.decide(fixture["packet"], fixture["answers"], operation="add")["combined"] == "duplicate_skip"):
                            fragment["source"]["possible_duplicate"] = True  # the judge said duplicate; cleanup merges
                        ref = fragment["id"]
                        cur.execute("""insert into knowledge.fragment(id,host_id,alias,domain,seq,text,keywords,kind,group_id,
                                    revision,active,confidence,source,valid_from,superseded_at,subject_id,form)
                                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s::jsonb)""",
                                    (ref, fragment["host_id"], fragment["alias"], fragment["domain"], fragment["seq"],
                                     fragment["text"], fragment["keywords"], fragment["kind"], fragment["group_id"],
                                     1, True, fragment["confidence"], _json(fragment["source"]), fragment["valid_from"], None,
                                     subject_id, _json(_form_of(fact))))
                        latest = 1
                        # declared aliases first, so a leaf written under an alias gets the same subject (astra alias r1)
                        _register_aliases(cur, entry["host_id"], entry["entry_id"], old["fact_index"], fact, subject_id, ref, 1)
                        _write_form(cur, entry["host_id"], ref, 1, fact, subject_id)
                        embedding_pending = True  # embedded after the commit (embed_unit), never inside this transaction
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
                            _register_aliases(cur, entry["host_id"], entry["entry_id"], old["fact_index"], fact,
                                              subject_id, ref, latest)
                            _write_form(cur, entry["host_id"], ref, latest, fact, subject_id)
                        if operation == "update":
                            embedding_pending = True  # embedded after the commit (embed_unit)
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
