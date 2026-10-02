"""Re-record adds that were dropped only because a judge called them duplicates (before 2026-10-02 'add never dropped by a
judge alone'; astra dupA review P1-2). Skips a fact the code finds in the active canon (dedup.same_fact) and any fact a
human rejected. One new work unit per run, evidence and reason kept, completion source 'merge'.

Usage: python3 reopen_duplicates.py --host H (--dry-run | --apply)"""
import argparse
import json
import uuid

import config
import dedup
import knowledge_cli
import store_pg as pg


def candidates(dsn, host):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select e.entry_id::text, a.fact_index, e.judgement_body->'facts'->a.fact_index, 'digestion P03'
                       from knowledge.absorption a join knowledge.ledger_entry e on e.entry_id=a.entry_id
                       where e.host_id=%s and a.rule_id='P03' and a.decision::text='rejected' and a.decided_by<>'human'
                         and coalesce(e.judgement_body->'facts'->a.fact_index->>'operation','add')='add'
                       union all
                       select e.entry_id::text, r.fact_index, e.judgement_body->'facts'->r.fact_index, 'worktime duplicate'
                       from knowledge.ledger_entry e join knowledge.check_receipt r on r.entry_id=e.entry_id
                       where e.host_id=%s and e.state='closed' and r.stage='worktime' and r.combined='duplicate_skip'
                         and coalesce(e.judgement_body->'facts'->r.fact_index->>'operation','add')='add'
                         and not exists (select 1 from knowledge.absorption a where a.entry_id=e.entry_id)""", (host, host))
        rows = cur.fetchall()
        cur.execute("select alias, text from knowledge.fragment where host_id=%s and active", (host,))
        canon = cur.fetchall()
    return classify(rows, canon)


def classify(rows, canon):
    """rows (entry_id, fact_index, fact body, why), canon (alias, text) -> candidates with in_canon_as (code exact match)."""
    out = []
    for eid, idx, fact, why in rows:
        same = next((a for a, t in canon if dedup.same_fact(fact.get("fact"), t)), None)
        out.append({"entry_id": eid, "fact_index": idx, "why": why, "fact": fact.get("fact"), "in_canon_as": same,
                    "body": fact})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    dsn = config.require("db_url")["db_url"]
    cands = candidates(dsn, a.host)
    todo = [c for c in cands if not c["in_canon_as"]]
    if a.dry_run:
        print(json.dumps([{k: c[k] for k in ("why", "fact", "in_canon_as")} for c in cands], ensure_ascii=False, indent=1))
        return
    unit = str(uuid.uuid4())
    for c in todo:
        fact = {**c["body"], "reason": (c["body"].get("reason") or "") + " — 재처리: 판정 중복으로만 버려짐"}
        res = knowledge_cli.record(dsn, {"host_id": a.host, "partition_key": "reopen", "work_unit_id": unit, "facts": [fact]})
        print(json.dumps({"fact": c["fact"], "ok": res.get("ok", True), "errors": res.get("errors")}, ensure_ascii=False))
    if todo:
        pg.register_completion_sources(dsn, unit, ["merge"])
        pg.signal_completion(dsn, unit, "merge", evidence={"reopen": len(todo)})
    print(json.dumps({"reopened": len(todo), "skipped_in_canon": len(cands) - len(todo), "unit": unit}))


if __name__ == "__main__":
    main()
