"""Fill the 0009/0010 structure of canonical fragments made before them (review 2026-10-01, main DB plan).

For each active fragment without a form: form = fact_form.parse(text) (a legacy sentence becomes one plain leaf),
subject = source.subject, else the sentence's head noun (runner.SUBJECT_HEAD), matched to the dictionary by core
(subject_dict.lookup) or registered; one fragment_leaf per leaf at the current revision. No Jev, no embedding change
(the Korean view of a plain sentence is the sentence). With the 0010 trigger this changes no revision and no history.

Usage: python3 backfill_structure.py --host H [--dsn DSN] (--dry-run | --apply)
"""
import argparse
import json
import sys

import config
import fact_form
import runner
import store_pg
import subject_dict


def subject_of(text, source):
    s = (source or {}).get("subject")
    if isinstance(s, str) and s.strip() and s.strip() in text:
        return s.strip(), "source"
    head = runner.SUBJECT_HEAD.match((fact_form.parse(text).get("then") or [text])[0] + " ")
    return (head.group(1).strip(), "head") if head else (None, "none")


def plan(cur, host):
    cur.execute("""select id::text, alias, revision, text, source from knowledge.fragment
                   where host_id=%s and active order by domain, seq""", (host,))
    rows = []
    for fid, alias, rev, text, source in cur.fetchall():
        form = fact_form.parse(text)
        name, how = subject_of(text, source)
        rows.append({"id": fid, "alias": alias, "revision": rev, "text": text, "form_kind": form["kind"],
                     "leaves": len(fact_form.leaves(form)), "subject": name, "subject_from": how,
                     "form_check": fact_form.check(text)})
    return rows


def apply(cur, host, rows):
    import store_pg as pg
    import subject_merge
    subject_merge.lock_host(cur, host, exclusive=True)  # astra merge r1 P1-4: dictionary writers take the host lock first
    done = 0
    for r in rows:
        cur.execute("select form is not null from knowledge.fragment where id=%s", (r["id"],))
        if cur.fetchone()[0]:
            continue  # already structured
        sid = subject_dict.register(cur, host, r["subject"]) if r["subject"] else None
        fact = {"fact": r["text"], "subject": r["subject"]}
        # revision CAS (astra direction review P1): fill only the revision that was planned, and only once
        cur.execute("""update knowledge.fragment set form=%s::jsonb, subject_id=coalesce(subject_id, %s)
                       where id=%s and revision=%s and form is null returning 1""",
                    (json.dumps(fact_form.parse(r["text"]), ensure_ascii=False), sid, r["id"], r["revision"]))
        if not cur.fetchone():
            continue  # changed since the plan: run the plan again
        pg._write_form(cur, host, r["id"], r["revision"], fact, sid)
        done += 1
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--dsn")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    dsn = a.dsn or config.load()["db_url"]
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        rows = plan(cur, a.host)
        if a.dry_run:
            conn.rollback()
            print(json.dumps(rows, ensure_ascii=False, indent=1))
            return
        print(json.dumps({"structured": apply(cur, a.host, rows), "fragments": len(rows)}))


if __name__ == "__main__":
    main()
