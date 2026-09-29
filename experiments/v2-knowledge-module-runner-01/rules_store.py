"""Rule module storage and rule tool operations (rules schema, migrations/0006).
Rules do not go through knowledge digestion: the agent turns a user's instruction into a rule and calls these.
Creation checks: schema (code) first, then an optional injected review (Jev: conflict / duplicate / weakens
base / unjudgeable / too broad). Flags stop the write until the user confirms (confirm_quote)."""
import json
from uuid import uuid4

import runner
import store_pg

FIELDS = ("when", "must", "level", "unless", "why", "ref", "code_check")
COLUMN = {"when": "when_text", "must": "must_text", "level": "level", "unless": "unless_text", "why": "why_text",
          "ref": "ref", "code_check": "code_check"}
CODE_CHECKS = {"command_succeeded_after_edit", "path_outside_project"}


def schema_errors(rule, partial=False):
    errs = []
    if not isinstance(rule, dict):
        return ["rule must be an object"]
    unknown = set(rule) - set(FIELDS)
    if unknown:
        errs.append("unknown fields: " + ", ".join(sorted(unknown)) + " (id, status and history are managed by the DB)")
    for k in ("when", "must", "level"):
        if (not partial or k in rule) and (not isinstance(rule.get(k), str) or not rule[k].strip()):
            errs.append(f"missing {k}")
    if "level" in rule and rule.get("level") not in ("must", "should"):
        errs.append("level must be must|should (enforcement is derived from level and code_check)")
    for k in ("unless", "why", "ref"):
        if k in rule and rule[k] is not None and (not isinstance(rule[k], str) or not rule[k].strip()):
            errs.append(f"{k} must be a nonempty string when given")
    cc = rule.get("code_check")
    if cc is not None and (not isinstance(cc, dict) or cc.get("type") not in CODE_CHECKS):
        errs.append("unknown code_check type; allowed: " + ", ".join(sorted(CODE_CHECKS)))
    return errs


def _source(quote):
    if not isinstance(quote, str) or not quote.strip():
        raise ValueError("source quote (the user's words) required")
    if runner.QUESTION_TAIL.search(quote.strip()):
        raise ValueError("a question is not an instruction; ask the user first")
    return {"quote": quote.strip()}


def _row_rule(row):
    rule = {"id": row["rule_id"], "version": row["version"]}
    for k, c in COLUMN.items():
        if row.get(c) is not None:
            rule[k] = row[c]
    return rule


def list_rules(dsn, host, include_base=True):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select * from rules.rule where status='active' and (host_id=%s or (%s and host_id is null))
                       order by (host_id is not null), created_at, rule_id""", (host, include_base))
        return [_row_rule(r) for r in store_pg._rows(cur)]


def _history(cur, rule_id, version, op, snapshot, source):
    cur.execute("""insert into rules.rule_history(rule_id,version,op,snapshot,source) values (%s,%s,%s,%s::jsonb,%s::jsonb)""",
                (rule_id, version, op, json.dumps(snapshot, ensure_ascii=False), json.dumps(source, ensure_ascii=False)))


def create(dsn, host, rule, quote, review=None, confirm_quote=None):
    """review(rule, existing) -> list of flag strings (Jev). Flags block the write unless confirm_quote is given."""
    errs = schema_errors(rule)
    if errs:
        return {"ok": False, "errors": errs}
    source = _source(quote)
    existing = list_rules(dsn, host)
    flags = review(rule, existing) if review else []
    if flags and not confirm_quote:
        return {"ok": False, "needs_user": True, "flags": flags,
                "instruction": "Show the flags to the user in plain words, propose a fix, and call again with confirm_quote "
                               "(the user's non-question answer) only if the user still wants this rule."}
    if flags:
        source["confirm"] = _source(confirm_quote)["quote"]
        source["flags"] = flags
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select nextval('rules.rule_seq')")
        rule_id = f"p-{cur.fetchone()[0]}"
        cols = ["rule_id", "host_id", "source"] + [COLUMN[k] for k in FIELDS if rule.get(k) is not None]
        vals = [rule_id, host, json.dumps(source, ensure_ascii=False)] + [
            json.dumps(rule[k]) if k == "code_check" else rule[k] for k in FIELDS if rule.get(k) is not None]
        cur.execute(f"insert into rules.rule({','.join(cols)}) values ({','.join(['%s'] * len(vals))})", vals)
        _history(cur, rule_id, 1, "create", {k: rule[k] for k in FIELDS if rule.get(k) is not None}, source)
    return {"ok": True, "id": rule_id, "version": 1, "flags": flags}


def _locked(cur, host, rule_id):
    if not isinstance(rule_id, str) or not rule_id.startswith("p-"):
        raise ValueError("only project rules (p-) can be changed; harness base rules (h-) are fixed")
    cur.execute("select * from rules.rule where rule_id=%s and host_id=%s and status='active' for update", (rule_id, host))
    row = store_pg._row(cur)
    if not row:
        raise ValueError("active rule not found for host")
    return row


def update(dsn, host, rule_id, changes, quote):
    errs = schema_errors(changes, partial=True)
    if errs or not changes:
        return {"ok": False, "errors": errs or ["no changes"]}
    source = _source(quote)
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        row = _locked(cur, host, rule_id)
        sets = [f"{COLUMN[k]}=%s" for k in changes] + ["version=version+1", "updated_at=now()", "source=%s::jsonb"]
        vals = [json.dumps(v) if k == "code_check" and v is not None else v for k, v in changes.items()]
        cur.execute(f"update rules.rule set {', '.join(sets)} where rule_id=%s returning *",
                    vals + [json.dumps(source, ensure_ascii=False), rule_id])
        new = _row_rule(store_pg._row(cur))
        _history(cur, rule_id, new["version"], "update", {k: v for k, v in new.items() if k in FIELDS}, source)
    return {"ok": True, "id": rule_id, "version": new["version"], "before_version": row["version"]}


def delete(dsn, host, rule_id, quote):
    source = _source(quote)
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        row = _locked(cur, host, rule_id)
        cur.execute("update rules.rule set status='deleted', version=version+1, updated_at=now() where rule_id=%s", (rule_id,))
        _history(cur, rule_id, row["version"] + 1, "delete", _row_rule(row), source)
    return {"ok": True, "id": rule_id, "status": "deleted"}


def history(dsn, rule_id):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select version, op, snapshot, source, at from rules.rule_history where rule_id=%s order by history_id", (rule_id,))
        return store_pg._rows(cur)


BASE_FILE = __import__("pathlib").Path(__file__).with_name("base_rules.json")


def sync_base(dsn, path=BASE_FILE):
    """Upsert the shipped harness base rules (host_id null, h-*). Changes are versioned in rule_history."""
    data = json.loads(path.read_text(encoding="utf-8"))
    created, updated, unchanged = [], [], []
    source = {"quote": "harness base rules (" + path.name + ")"}
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        for rule in data["rules"]:
            rid = rule["id"]
            if not rid.startswith("h-"):
                raise ValueError("base rule ids must start with h-")
            body = {k: rule.get(k) for k in FIELDS}
            errs = schema_errors({k: v for k, v in body.items() if v is not None})
            if errs:
                raise ValueError(f"{rid}: {errs}")
            cur.execute("select * from rules.rule where rule_id=%s for update", (rid,))
            row = store_pg._row(cur)
            vals = [json.dumps(body[k]) if k == "code_check" and body[k] is not None else body[k] for k in FIELDS]
            if row is None:
                cur.execute(f"insert into rules.rule(rule_id,host_id,source,{','.join(COLUMN[k] for k in FIELDS)}) values (%s,null,%s::jsonb,{','.join(['%s'] * len(FIELDS))})",
                            [rid, json.dumps(source)] + vals)
                _history(cur, rid, 1, "create", {k: v for k, v in body.items() if v is not None}, source)
                created.append(rid)
                continue
            current = {k: row.get(COLUMN[k]) for k in FIELDS}
            if current == body and row["status"] == "active":
                unchanged.append(rid)
                continue
            cur.execute(f"update rules.rule set {', '.join(COLUMN[k] + '=%s' for k in FIELDS)}, status='active', version=version+1, "
                        "updated_at=now(), source=%s::jsonb where rule_id=%s returning version", vals + [json.dumps(source), rid])
            _history(cur, rid, cur.fetchone()[0], "update", {k: v for k, v in body.items() if v is not None}, source)
            updated.append(rid)
    return {"created": sorted(created), "updated": sorted(updated), "unchanged": sorted(unchanged)}


def record_injection(dsn, host, turn_ref, rule_ids, aliases, tokens):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into rules.injection(host_id,turn_ref,rule_ids,knowledge_aliases,tokens) values (%s,%s,%s,%s,%s)
                       returning injection_id""", (host, turn_ref, list(rule_ids), list(aliases), int(tokens)))
        return cur.fetchone()[0]


def injected(dsn, host, turn_ref):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select coalesce(array_agg(distinct r), '{}') , coalesce(array_agg(distinct k), '{}')
                       from rules.injection i left join lateral unnest(i.rule_ids) r on true
                       left join lateral unnest(i.knowledge_aliases) k on true where host_id=%s and turn_ref=%s""", (host, turn_ref))
        rules, aliases = cur.fetchone()
    return {"rules": [x for x in rules if x], "knowledge": [x for x in aliases if x]}


def save_receipts(dsn, host, turn_ref, rules, verdicts, evidence):
    ids = []
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        for r, v in zip(rules, verdicts):
            rid = str(uuid4())
            cur.execute("""insert into rules.judgement_receipt(receipt_id,host_id,turn_ref,rule_id,rule_version,label,confident,
                           cond,done,items,evidence,rule_delivered) values (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s)""",
                        (rid, host, turn_ref, r["id"], r.get("version", 1), v["label"], bool(v["confident"]),
                         json.dumps(v["cond"]), json.dumps(v["done"]), json.dumps(v.get("items", []), ensure_ascii=False),
                         json.dumps(evidence, ensure_ascii=False), v.get("rule_delivered")))
            ids.append(rid)
    return ids


def dispute(dsn, receipt_id, reason):
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("reason required")
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update rules.judgement_receipt set dispute=%s where receipt_id=%s and dispute is null returning receipt_id",
                    (reason.strip(), receipt_id))
        if not cur.fetchone():
            raise ValueError("receipt not found or already disputed")
    return {"ok": True}
