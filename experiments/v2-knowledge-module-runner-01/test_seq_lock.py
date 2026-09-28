"""G8: concurrent digestions of the same domain get distinct alias numbers (advisory lock in store_pg.next_seq)."""
import json
import threading
import time

import store_pg as pg
from test_store_pg import host  # fixture


def _insert(cur, host, seq):
    cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                values (%s,%s,'D',%s,%s,'fact','D:g',%s::jsonb)""",
                (host, f"D-{seq}", seq, f"t{seq}", json.dumps({"record_id": "D", "origin": "test", "evidence_refs": []})))


def test_second_digestion_waits_and_gets_next_number(dsn, host):
    got = {}
    first_locked = threading.Event()
    release = threading.Event()

    def first():
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            s = pg.next_seq(cur, host, "D")
            first_locked.set()
            release.wait(5)
            _insert(cur, host, s)
            got["first"] = s

    def second():
        first_locked.wait(5)
        t0 = time.time()
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            s = pg.next_seq(cur, host, "D")
            got["waited"] = time.time() - t0
            _insert(cur, host, s)
            got["second"] = s

    a, b = threading.Thread(target=first), threading.Thread(target=second)
    a.start(); b.start()
    first_locked.wait(5)
    time.sleep(0.5)
    assert "second" not in got  # blocked on the lock while the first transaction is open
    release.set()
    a.join(10); b.join(10)
    assert (got["first"], got["second"]) == (1, 2) and got["waited"] >= 0.4
