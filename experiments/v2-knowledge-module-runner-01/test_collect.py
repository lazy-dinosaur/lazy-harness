"""Local-only collector integration and 500-fragment oracle evaluation."""
import json
from pathlib import Path

import collect
import embed
import store_pg as pg
from test_hybrid_pg import _host
from test_search_pg import insert_fragment

DATASET = Path(__file__).parent.parent / "v2-embedding-500-01/dataset.json"


def oracle(gold):
    return lambda query, candidates: [{"relevant": c["alias"] in gold,
                                        "novel": c["alias"] in gold} for c in candidates]


def test_exclusion_variants_and_group(dsn):
    host = _host(dsn)
    a = insert_fragment(dsn, host, "one", "distinct alpha keyword", [], "local")
    b = insert_fragment(dsn, host, "two", "distinct beta keyword", [], "local")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.fragment set group_id='pair',revision=revision+1 where id=any(%s::uuid[])", ([a, b],))
    assert pg.backfill_embeddings(dsn, host, "plain") == 2
    assert pg.backfill_embeddings(dsn, host, "ctx-v1") == 2
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select embed_variant,count(*) from knowledge.fragment_embedding where fragment_id=any(%s::uuid[]) group by embed_variant", ([a,b],))
        assert dict(cur.fetchall()) == {"plain": 2, "ctx-v1": 2}
        cur.execute("select embed_variant,embedding::text from knowledge.fragment_embedding where fragment_id=%s", (a,))
        assert len({vector for _, vector in cur.fetchall()}) == 2
    assert a not in [r["id"] for r in pg.search(dsn, host, "distinct alpha keyword", mode="hybrid", exclude_ids=[a])]
    result = collect.collect_topic(dsn, host, ["distinct alpha keyword", "distinct beta keyword"],
                                   page_size=1, judge=oracle({"one"}))
    assert {r["id"] for r in result["note"]} == {a, b}  # group expansion
    assert [r["id"] for r in result["relevant"]] == [a]  # judge selection before group expansion
    assert sum(t["read"] for t in result["trace"]) <= 2  # global exclusion
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.fragment set revision=revision+1 where id=%s", (a,))
    for variant in ("plain", "ctx-v1"):
        assert all(r["id"] != a or r["vector_rank"] is None for r in pg.search(
            dsn, host, "unrelated no text hit", mode="hybrid", variant=variant))
    assert pg.backfill_embeddings(dsn, host, "ctx-v1") == 1
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select revision from knowledge.fragment_embedding where fragment_id=%s and embed_variant='plain'", (a,))
        assert cur.fetchone()[0] == 2
    assert pg.backfill_embeddings(dsn, host, "plain") == 1


def test_pages_and_limits(dsn):
    host = _host(dsn)
    for i in range(7):
        insert_fragment(dsn, host, f"item-{i}", f"identical searchable item {i}", [], "local")
    pg.backfill_embeddings(dsn, host)
    q = "identical searchable item"
    result = collect.collect_topic(dsn, host, [q], page_size=2, max_pages_per_query=2,
                                   judge=oracle({f"item-{i}" for i in range(7)}))
    assert result["trace"][0]["pages"] == 2 and result["trace"][0]["stop"] == "max_pages_per_query"
    assert result["trace"][0]["read"] == 4
    result = collect.collect_topic(dsn, host, [q], page_size=2, max_total=3,
                                   judge=oracle({f"item-{i}" for i in range(7)}))
    assert result["trace"][0]["read"] == 3 and result["trace"][0]["stop"] == "max_total"
    result = collect.collect_topic(dsn, host, [q], page_size=2, judge=oracle(set()))
    assert result["trace"][0]["pages"] == 1 and result["trace"][0]["stop"] == "no_new_content"


def test_500_topic_oracle(dsn):
    data = json.loads(DATASET.read_text())
    host = _host(dsn)
    docs = data["documents"]
    vectors = embed.encode_passages([d["text"] for d in docs])
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        for i, (doc, vector) in enumerate(zip(docs, vectors), 1):
            cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,source)
                        values (%s,%s,%s,%s,%s,'fact','{"evidence_refs":[]}') returning id::text""",
                        (host, doc["id"], doc["domain"], i, doc["text"]))
            pg._upsert_embedding(cur, cur.fetchone()[0], 1, vector)
    assert pg.backfill_embeddings(dsn, host, "ctx-v1") == 500
    cases = {}
    for q in data["queries"]:
        cases.setdefault(q["case_id"], []).append(q)
    print("500 TOPIC | variant | method | all-evidence | read fragments")
    for variant in ("plain", "ctx-v1"):
        for method in ("a", "b"):
            recovered = read = total = 0
            for q in data["queries"]:
                if not q["gold"]:
                    continue
                gold = set(q["gold"])
                if method == "a":
                    rows = pg.search(dsn, host, q["text"], 30, mode="hybrid", variant=variant, expand=False)
                    aliases = {row["alias"] for row in rows}
                    count = len(rows)
                else:
                    alternate = next((other["text"] for other in cases[q["case_id"]]
                                      if other["id"] != q["id"] and other["gold"]), None)
                    queries = [q["text"]] + ([alternate] if alternate else [])
                    outcome = collect.collect_topic(dsn, host, queries, judge=oracle(gold), variant=variant)
                    aliases = {row["alias"] for row in outcome["note"]}
                    count = sum(t["read"] for t in outcome["trace"])
                recovered += gold <= aliases
                read += count
                total += 1
            print(f"{variant} | {method} | {recovered}/{total} | {read}")
