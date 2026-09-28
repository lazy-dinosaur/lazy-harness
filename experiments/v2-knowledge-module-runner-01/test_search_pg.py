"""Local-only search and cost integration; never consult production credentials."""
import json
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

import store_pg as pg
from test_store_pg import fixture, judgement, process

ROOT = Path(__file__).parent


@pytest.fixture(scope="module")
def local_dsn(dsn):
    return dsn


def insert_fragment(dsn, host, alias, text, keywords, quote, group_id=None, active=True):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,keywords,kind,group_id,active,source)
                    values (%s,%s,'search', (select coalesce(max(seq),0)+1 from knowledge.fragment
                    where host_id=%s and domain='search'),%s,%s,'decision',%s,%s,%s::jsonb) returning id::text""",
                    (host, alias, host, text, keywords, group_id, active,
                     json.dumps({"evidence_refs": [{"type": "user_utterance", "locator": "local/test", "quote": quote}]})))
        return cur.fetchone()[0]


def test_search_scope_groups_ranking_and_permissions(local_dsn):
    dsn = local_dsn
    host, other = f"search-{uuid4()}", f"other-{uuid4()}"
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        for name in (host, other):
            cur.execute("insert into knowledge.host(host_id,name,repo_locator) values (%s,%s,'local-test')", (name, name))
    facts = json.loads((ROOT / "first-load-01/judgement.json").read_text())["facts"]
    for index, fact in enumerate(facts, 1):
        insert_fragment(dsn, host, f"knowledge-module-{index}", fact["fact"], fact["keywords"],
                        fact["evidence_refs"][0]["quote"], "decision-bundle" if index == 1 else None)
    queries = [("메인 DB 어디에 둬?", "knowledge-module-1"),
               ("Jev 익명화 하나?", "knowledge-module-3"),
               ("계획 백로그 어디서 관리?", "knowledge-module-2")]
    for query, expected in queries:
        results = pg.search(dsn, host, query)
        print(f"QUERY {query}: " + ", ".join(f"{row['alias']}={row['score']:.6f}" for row in results))
        assert results and results[0]["alias"] == expected
        assert results[0]["evidence_quote"] == facts[int(expected[-1]) - 1]["evidence_refs"][0]["quote"]
    insert_fragment(dsn, host, "sibling", "같은 결정의 이유", ["이유"], "동일 묶음 근거", "decision-bundle")
    group_result = pg.search(dsn, host, "메인 DB 어디에 둬?")[0]
    assert any(row["alias"] == "sibling" and row["score"] is None for row in group_result["group"])
    insert_fragment(dsn, host, "inactive", "메인 DB 어디에 둬?", ["메인 DB"], "폐기", active=False)
    insert_fragment(dsn, other, "cross", "메인 DB 어디에 둬?", ["메인 DB"], "교차")
    assert all(row["host_id"] == host for row in pg.search(dsn, host, "메인 DB 어디에 둬?"))
    assert all(row["host_id"] == host for row in pg.search(dsn, host, "메인 DB 어디에 둬?", cross_hosts=[other]))
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.host set cross_search_allowed=true where host_id=%s", (other,))
    cross = pg.search(dsn, host, "메인 DB 어디에 둬?", cross_hosts=[other])
    assert any(row["alias"] == "cross" and row["host_id"] == other for row in cross)
    assert all(row["alias"] != "inactive" for row in cross)
    print("scope=pass inactive=pass group=pass")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("set role anon")
        for sql, params in (("select * from knowledge.search_fragments(%s,%s)", (host, "메인")),
                            ("select * from knowledge.expand_group(%s,%s)", (host, "decision-bundle"))):
            cur.execute("savepoint anon_call")
            with pytest.raises(pg.driver.Error, match="permission denied"):
                cur.execute(sql, params)
            cur.execute("rollback to savepoint anon_call")
        cur.execute("reset role")
    cli = subprocess.run(["python3", str(ROOT / "runner.py"), "search", "--host", host,
                          "--query", "메인 DB 어디에 둬?", "--backend", "pg", "--dsn", dsn],
                         text=True, capture_output=True)
    assert cli.returncode == 0, cli.stderr
    assert json.loads(cli.stdout)[0]["alias"] == "knowledge-module-1"
    unsupported = subprocess.run(["python3", str(ROOT / "runner.py"), "search", "--host", host,
                                  "--query", "메인"], text=True, capture_output=True)
    assert unsupported.returncode != 0 and "does not support search" in unsupported.stderr
    print("anon=denied both")


def test_receipt_usage(local_dsn):
    host = f"usage-{uuid4()}"
    with pg.connect(local_dsn) as conn, conn.cursor() as cur:
        cur.execute("insert into knowledge.host(host_id,name,repo_locator) values (%s,%s,'local-test')", (host, host))
    reported = fixture()
    reported.update(input_tokens=12, output_tokens=7, cost_usd="0.001234", usage_source="openrouter-usage")
    for response in (reported, fixture()):
        process(local_dsn, judgement(host), response)
    with pg.connect(local_dsn) as conn, conn.cursor() as cur:
        cur.execute("""select r.input_tokens,r.output_tokens,r.cost_usd,r.usage_source
                    from knowledge.check_receipt r join knowledge.ledger_entry e on e.entry_id=r.entry_id
                    where e.host_id=%s order by r.created_at,r.receipt_id""", (host,))
        rows = cur.fetchall()
        assert len(rows) == 2
        assert any(row[0] == 12 and row[1] == 7 and str(row[2]) == "0.001234" and
                   row[3] == "openrouter-usage" for row in rows)
        assert any(row[:3] == (None, None, None) and row[3] == "unreported-by-tool" for row in rows)
    print("receipt reported/unreported=pass")
