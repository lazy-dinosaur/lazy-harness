"""audit-01/flow2: continue flow.py after the turns: ledger, poller digestion, canonical result (disposable lhv2-flow DB)."""
import json, os, subprocess, sys, time
from pathlib import Path
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R))
import config, store_pg
dsn = config.load()["db_url"]
assert "127.0.0.1" in dsn, "must be the disposable DB"
U = "3d342e7d-c1d7-44c8-aafa-27734497ebd4"


def q(sql, a=()):
    with store_pg.connect(dsn) as c, c.cursor() as cur:
        cur.execute(sql, a); return cur.fetchall()


print("FRAGS_BEFORE " + json.dumps(q("select alias, revision, active, left(text,160) from knowledge.fragment where alias in ('knowledge-module-9','knowledge-module-11','knowledge-module-16','knowledge-module-17','knowledge-module-18') order by alias"), ensure_ascii=False), flush=True)
print("LEDGER " + json.dumps(q("select state::text, left(judgement_body::text, 600) from knowledge.ledger_entry where work_unit_id=%s order by created_at", (U,)), ensure_ascii=False, default=str), flush=True)
for i in range(5):
    p = subprocess.run(["/usr/bin/python3", str(R / "poller.py"), "--once", "--judge", "jev", "--state", "/tmp/lhv2-flow/poller-state.json"],
                       env=os.environ, capture_output=True, text=True, timeout=900)
    print(f"POLL{i} rc={p.returncode} " + (p.stdout[-700:] + p.stderr[-300:]).replace("\n", " | "), flush=True)
    st = q("select state::text, count(*) from knowledge.ledger_entry where work_unit_id=%s group by 1", (U,))
    print("  states " + json.dumps(st), flush=True)
    if all(s in ("absorbed", "closed", "rejected_input", "expired") for s, _ in st):
        break
    time.sleep(3)
print("ABSORB " + json.dumps(q("select fact_index, decision::text, decided_by, action, fragment_ref, left(proposal::text, 260) from knowledge.absorption where work_unit_id=%s order by created_at", (U,)), ensure_ascii=False, default=str), flush=True)
print("FRAGS_AFTER " + json.dumps(q("select alias, revision, active, left(text,200) from knowledge.fragment where text ~ '(300|1000)자' or alias in ('knowledge-module-9','knowledge-module-11','knowledge-module-16','knowledge-module-17','knowledge-module-18') order by alias"), ensure_ascii=False), flush=True)
print("REVIEW " + json.dumps(q("select count(*) from knowledge.confirmation_queue where status='open'"), default=str), flush=True)
print("UNIT " + json.dumps(q("select status::text from knowledge.work_unit where work_unit_id=%s", (U,))), flush=True)
