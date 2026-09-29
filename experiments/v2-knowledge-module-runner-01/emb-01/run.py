"""emb-01: embedding model quality on the medivance scale set (lh-kdb-test-13, 35,081 fragments, disposable).
Arms (vector-only retrieval, same inputs = ctx-v1 embedding text, same b3 queries, top-30 per question):
  small = stored intfloat/multilingual-e5-small (local)
  large = intfloat/multilingual-e5-large via OpenRouter (written to a side table emb01_large, 1024 dims)
Metric: nugget coverage of the top-30 fragment document (Jev COV per nugget, read-01 judging), recall-style.
Never touches the main DB."""
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
R = HERE.parent
sys.path.insert(0, str(R))
import config  # noqa: E402
import embed  # noqa: E402
import store_pg as pg  # noqa: E402

port = subprocess.run(["docker", "port", "lh-kdb-test-13", "5432/tcp"], capture_output=True, text=True).stdout.split("\n")[0].rsplit(":", 1)[-1]
DSN = f"postgresql://postgres:localtest@127.0.0.1:{port}/postgres"
HOST = "medivance-read"
LARGE = "intfloat/multilingual-e5-large"
cfg = config.require("jev_api_key", "jev_base_url", "jev_model")
TOPK = 30


def or_embed(texts, prefix):
    body = {"model": LARGE, "input": [f"{prefix}: {t}"[:1800] for t in texts]}
    for attempt in range(5):
        try:
            req = Request(cfg["jev_base_url"].rstrip("/") + "/v1/embeddings", data=json.dumps(body, ensure_ascii=False).encode(),
                          headers={"Authorization": "Bearer " + cfg["jev_api_key"], "Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=120) as r:
                d = json.load(r)
            data = sorted(d["data"], key=lambda x: x["index"])
            return [x["embedding"] for x in data], float((d.get("usage") or {}).get("cost") or 0)
        except Exception as e:  # noqa: BLE001
            time.sleep(2 * (attempt + 1)); last = e
    raise RuntimeError(f"embed failed: {last}")


def vec(v):
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def build_large():
    with pg.connect(DSN) as c, c.cursor() as cur:
        cur.execute("create table if not exists knowledge.emb01_large(fragment_id uuid primary key, embedding extensions.vector(1024) not null)")
        cur.execute("select count(*) from knowledge.emb01_large"); have = cur.fetchone()[0]
        cur.execute("""select f.id::text,f.text,f.kind::text,f.domain,f.group_id from knowledge.fragment f
                       where f.host_id=%s and not exists (select 1 from knowledge.emb01_large e where e.fragment_id=f.id) order by f.id""", (HOST,))
        todo = cur.fetchall()
        sib = {}
        cur.execute("select group_id, array_agg(left(text,80) order by id) from knowledge.fragment where host_id=%s group by 1", (HOST,))
        for g, arr in cur.fetchall():
            sib[g] = arr
    inputs = []
    for fid, text, kind, domain, gid in todo:
        s = [x for x in (sib.get(gid) or []) if not text.startswith(x)][:3]
        inputs.append((fid, pg._embedding_input(kind, domain, s, text, "ctx-v1")))
    print(json.dumps({"have": have, "todo": len(inputs)}), flush=True)
    batches = [inputs[k:k + 64] for k in range(0, len(inputs), 64)]
    cost, t0 = 0.0, time.time()
    def work(b):
        vs, c = or_embed([t for _, t in b], "passage")
        return b, vs, c
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, (b, vs, c) in enumerate(pool.map(work, batches)):
            cost += c
            with pg.connect(DSN) as conn, conn.cursor() as cur:
                for (fid, _), v in zip(b, vs):
                    cur.execute("insert into knowledge.emb01_large values (%s,%s::extensions.vector) on conflict do nothing", (fid, vec(v)))
            if i % 50 == 0:
                print(json.dumps({"batch": i, "of": len(batches), "secs": round(time.time() - t0, 1), "cost": round(cost, 5)}), flush=True)
    return {"embedded": len(inputs), "secs": round(time.time() - t0, 1), "cost": round(cost, 5)}


def retrieve(arm, queries):
    best = {}
    if arm == "small":
        qv = [embed.encode_query(q) for q in queries]
        sql = """select e.fragment_id::text, 1-(e.embedding <=> %s::extensions.vector) from knowledge.fragment_embedding e
                 where e.embed_variant='ctx-v1' order by e.embedding <=> %s::extensions.vector limit %s"""
    else:
        qv, _ = or_embed(queries, "query")
        sql = """select e.fragment_id::text, 1-(e.embedding <=> %s::extensions.vector) from knowledge.emb01_large e
                 order by e.embedding <=> %s::extensions.vector limit %s"""
    with pg.connect(DSN) as c, c.cursor() as cur:
        for v in qv:
            cur.execute(sql, (vec(v), vec(v), TOPK))
            for fid, s in cur.fetchall():
                best[fid] = max(best.get(fid, -1), s)
        top = sorted(best, key=best.get, reverse=True)[:TOPK]
        cur.execute("select id::text, text from knowledge.fragment where id = any(%s::uuid[])", (top,))
        text = dict(cur.fetchall())
    return [text[i] for i in top]


COV = "nuggets[{i}] 의 내용이 answer 에 담겨 있는가? 조건·예외·순서·값까지 같은 뜻이어야 한다. 표현이 달라도 뜻이 같으면 true, 빠졌거나 일부만이면 false."


def judge(q, claims, doc):
    ns = q["nuggets"]
    qs = {f"c{i}": {"type": "noul", "instructions": COV.format(i=i), "criteria": {"true": "담겨 있다", "false": "담겨 있지 않다"}} for i in range(len(ns))}
    body = {"model": cfg["jev_model"], "state": {"question": q["question"], "answer": doc,
            "nuggets": [{"i": i, "text": claims[n]} for i, n in enumerate(ns)]}, "questions": qs}
    for attempt in range(3):
        try:
            req = Request(cfg["jev_base_url"].rstrip("/") + "/v1/systemone", data=json.dumps(body, ensure_ascii=False).encode(),
                          headers={"Authorization": "Bearer " + cfg["jev_api_key"], "Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=120) as r:
                d = json.load(r)
            return [d["answers"][f"c{i}"]["noul"] for i in range(len(ns))], float((d.get("usage") or {}).get("cost") or 0)
        except Exception:  # noqa: BLE001
            time.sleep(2)
    return None, 0.0


def main():
    built = build_large()
    print(json.dumps({"build": built}), flush=True)
    qs = json.load(open(R / "read-01" / "questions.json"))
    claims_raw = json.load(open(R / "capture-01" / "s1-answer-key.json"))
    # s1-answer-key.json: {"claims": {qid: [{"id": "c1", "claim": ...}, ...]}}; nugget ids look like "R01:c9"
    claims = {f"{qid}:{c['id']}": c["claim"] for qid, cs in claims_raw["claims"].items() for c in cs}
    missing = [n for q in qs for n in q["nuggets"] if n not in claims]
    print(json.dumps({"claims": len(claims), "missing_nuggets": len(missing)}), flush=True)
    qs = [dict(q, nuggets=[n for n in q["nuggets"] if n in claims]) for q in qs]
    qs = [q for q in qs if q["nuggets"]]
    out, jcost, tsum = [], 0.0, {"small": 0.0, "large": 0.0}
    for q in qs:
        raw = (R / "read-01" / "b3-queries" / f"{q['qid']}.raw.txt")
        queries = [q["question"]]
        if raw.exists():
            import re
            m = re.search(r"\{.*\}", raw.read_text(errors="replace"), re.S)
            try:
                queries = json.loads(m.group(0))["queries"] if m else queries
            except (ValueError, KeyError):
                pass
        queries = queries + [q["question"]]
        row = {"qid": q["qid"], "n": len(q["nuggets"])}
        for arm in ("small", "large"):
            t = time.time(); docs = retrieve(arm, queries); tsum[arm] += time.time() - t
            cov, c = judge(q, claims, "\n".join(f"- {d}" for d in docs))
            jcost += c
            row[arm] = None if cov is None else round(sum(x >= 0.5 for x in cov) / len(cov), 3)
        out.append(row)
        print(json.dumps(row), flush=True)
    ok = [r for r in out if r["small"] is not None and r["large"] is not None]
    summ = {"questions": len(ok), "small_cov": round(sum(r["small"] for r in ok) / len(ok), 4),
            "large_cov": round(sum(r["large"] for r in ok) / len(ok), 4),
            "large_better": sum(r["large"] > r["small"] for r in ok), "small_better": sum(r["small"] > r["large"] for r in ok),
            "retrieve_secs_per_q": {k: round(v / len(qs), 2) for k, v in tsum.items()}, "jev_cost": round(jcost, 4), "build": built}
    (HERE / "result.json").write_text(json.dumps({"summary": summ, "rows": out}, ensure_ascii=False, indent=1))
    print("SUMMARY " + json.dumps(summ, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
