"""Offline pgvector integration on the shared loopback-only test container."""
import json
from pathlib import Path
from uuid import uuid4

import pytest

import embed
import store_pg as pg
from test_search_pg import insert_fragment
from test_store_pg import fixture, judgement, process

HERE = Path(__file__).parent
DATASET = HERE.parent / "v2-embedding-500-01/dataset.json"


def _host(dsn, cross=False):
    host = f"hybrid-{uuid4()}"
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("insert into knowledge.host(host_id,name,repo_locator,cross_search_allowed) values (%s,%s,'local',%s)",
                    (host, host, cross))
    return host


def test_embedding_lifecycle_scope_and_permissions(dsn):
    host, other = _host(dsn), _host(dsn)
    add = judgement(host, text="조각 벡터 확인")
    entry, _, receipt = process(dsn, add, fixture(text="조각 벡터 확인"))
    assert pg.digest(dsn, add["work_unit_id"], True,
                     {receipt: fixture(text="조각 벡터 확인")})["status"] == "absorbed"
    # embeddings are written after the commit, outside digest()'s transaction (astra big review)
    assert pg.embed_unit(dsn, add["work_unit_id"]) == 1
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select f.id::text,f.revision,e.revision,f.group_id from knowledge.fragment f
                    join knowledge.fragment_embedding e on f.id=e.fragment_id
                    where f.source->>'entry_id'=%s and e.model_id=%s""", (entry["entry_id"], embed.MODEL_ID))
        ident, revision, embedded_revision, group_id = cur.fetchone()
        assert revision == embedded_revision == 1
        assert group_id == entry["judgement_id"] + ":0"
    assert pg.search(dsn, host, "조각 벡터 확인", mode="hybrid")[0]["id"] == ident
    assert pg.search(dsn, host, "조각 벡터 확인", mode="hybrid", min_similarity=1.1)[0]["vector_rank"] is None
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.fragment set revision=revision+1 where id=%s", (ident,))
    vector_only = pg.search(dsn, host, "의미상 관련 없는 질문", mode="hybrid")
    assert all(row["id"] != ident or row["vector_rank"] is None for row in vector_only)
    assert pg.backfill_embeddings(dsn, host) == 1
    assert pg.backfill_embeddings(dsn, host) == 0
    assert pg.search(dsn, host, "조각 벡터 확인", mode="hybrid")[0]["vector_rank"] == 1
    # The ordinary update path advances the embedding revision right after the commit (embed_unit, astra big review).
    update = judgement(host, "update", ident, "수정된 조각 벡터", source="code_test")
    response = fixture("update", "수정된 조각 벡터", "조각 벡터 확인", 2)
    _, _, receipt = process(dsn, update, response)
    assert pg.digest(dsn, update["work_unit_id"], True, {receipt: response})["status"] == "absorbed"
    assert pg.embed_unit(dsn, update["work_unit_id"]) == 1
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select f.revision,e.revision from knowledge.fragment f join knowledge.fragment_embedding e on f.id=e.fragment_id where f.id=%s", (ident,))
        assert cur.fetchone() == (3, 3)
    foreign = insert_fragment(dsn, other, "foreign", "수정된 조각 벡터", [], "local")
    assert pg.backfill_embeddings(dsn, other) == 1
    assert all(row["id"] != foreign for row in pg.search(dsn, host, "수정된 조각 벡터", mode="hybrid", cross_hosts=[other]))
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.host set cross_search_allowed=true where host_id=%s", (other,))
    assert any(row["id"] == foreign for row in pg.search(dsn, host, "수정된 조각 벡터", mode="hybrid", cross_hosts=[other]))
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("set role anon")
        with pytest.raises(pg.driver.Error, match="permission denied"):
            cur.execute("select * from knowledge.search_hybrid(%s,%s,%s::extensions.vector,%s)",
                        (host, "test", pg._vector(embed.encode_query("test")), embed.MODEL_ID))
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.fragment set active=false,revision=revision+1 where id=%s", (ident,))
    assert all(row["id"] != ident for row in pg.search(dsn, host, "수정된 조각 벡터", mode="hybrid"))
    print("lifecycle add/update/stale/backfill/deprecate/cross/anon/group=pass")


def test_three_real_fragments_seven_queries(dsn):
    host = _host(dsn)
    facts = json.loads((HERE / "first-load-01/judgement.json").read_text())["facts"]
    for index, fact in enumerate(facts, 1):
        insert_fragment(dsn, host, f"knowledge-module-{index}", fact["fact"], fact["keywords"],
                        fact["evidence_refs"][0]["quote"])
    assert pg.backfill_embeddings(dsn, host) == 3
    queries = [line[3:] for line in (HERE / "first-load-01/search-ranking-probe.log").read_text().splitlines()
               if line.startswith("Q: ")]
    print("3 FRAGMENTS | query | text ranking | hybrid ranking")
    for query in queries:
        text = pg.search(dsn, host, query)
        hybrid = pg.search(dsn, host, query, mode="hybrid")
        print(json.dumps([query, [row["alias"] for row in text],
                          [[row["alias"], round(row["vector_similarity"], 4) if row["vector_similarity"] is not None else None]
                           for row in hybrid]], ensure_ascii=False))
    assert len(queries) == 7


def test_500_corpus_retrieval(dsn):
    data = json.loads(DATASET.read_text())
    host = _host(dsn)
    docs = data["documents"]
    vectors = embed.encode_passages([doc["text"] for doc in docs])
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        for index, (doc, vector) in enumerate(zip(docs, vectors), 1):
            cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,source)
                        values (%s,%s,'benchmark',%s,%s,'fact','{"evidence_refs":[]}') returning id::text""",
                        (host, doc["id"], index, doc["text"]))
            pg._upsert_embedding(cur, cur.fetchone()[0], 1, vector)
    counts = {mode: {3: 0, 5: 0, 15: 0} for mode in ("text", "vector", "hybrid")}
    eligible = [query for query in data["queries"] if query["gold"]]
    thresholds = (-1, .7, .75, .8, .82, .84, .85, .86, .87, .88, .89, .9, .91, .92, .93, .94, .95)
    threshold_hits = {value: 0 for value in thresholds}
    no_evidence_counts = {value: [] for value in thresholds}
    no_evidence_vector_counts = {value: [] for value in thresholds}
    gold_similarities, non_gold_top = [], []
    for query in data["queries"]:
        vector = embed.encode_query(query["text"])
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""select f.alias, 1 - (e.embedding OPERATOR(extensions.<=>) %s::extensions.vector)
                        from knowledge.fragment f join knowledge.fragment_embedding e
                        on e.fragment_id=f.id and e.revision=f.revision and e.model_id=%s
                        where f.host_id=%s and f.active order by e.embedding OPERATOR(extensions.<=>) %s::extensions.vector, f.id limit 500""",
                        (pg._vector(vector), embed.MODEL_ID, host, pg._vector(vector)))
            candidates = cur.fetchall()
            vector_ranking = [row[0] for row in candidates[:15]]
        if query["gold"]:
            gold_similarities.extend(score for alias, score in candidates if alias in query["gold"])
            non_gold_top.append(next((score for alias, score in candidates if alias not in query["gold"]), None))
        for threshold in thresholds:
            rows = pg.search(dsn, host, query["text"], 5 if query["gold"] else 15, mode="hybrid", min_similarity=threshold)
            if query["gold"]:
                threshold_hits[threshold] += set(query["gold"]).issubset(row["alias"] for row in rows)
            else:
                no_evidence_counts[threshold].append(len(rows))
                no_evidence_vector_counts[threshold].append(sum(row["vector_rank"] is not None for row in rows))
        if not query["gold"]:
            continue
        rankings = {"vector": vector_ranking,
                    "text": [r["alias"] for r in pg.search(dsn, host, query["text"], 15)],
                    "hybrid": [r["alias"] for r in pg.search(dsn, host, query["text"], 15, mode="hybrid")]}
        for mode, ranking in rankings.items():
            for cutoff in (3, 5, 15):
                counts[mode][cutoff] += set(query["gold"]).issubset(ranking[:cutoff])
    print("500 CORPUS | mode | all@3 | all@5 | all@15 | denominator")
    for mode, row in counts.items():
        print(f"{mode} | {row[3]}/{len(eligible)} | {row[5]}/{len(eligible)} | {row[15]}/{len(eligible)} | {len(eligible)}")
    print("500 CUTOFF | min_similarity | all@5/56 | unsupported returned/8 (limit 15) | vector-backed/8")
    for value in thresholds:
        print(f"{value} | {threshold_hits[value]}/56 | {no_evidence_counts[value]} | {no_evidence_vector_counts[value]}")
    for label, samples in (("gold", gold_similarities), ("non_gold_top", [s for s in non_gold_top if s is not None])):
        samples.sort()
        print(f"COSINE {label} | min={samples[0]:.4f} median={samples[len(samples)//2]:.4f} max={samples[-1]:.4f}")
    if abs(counts["vector"][5] - 54) > 5:
        print("VECTOR DIFF from prior 54/56: inspect corpus/scoring/pooling")
