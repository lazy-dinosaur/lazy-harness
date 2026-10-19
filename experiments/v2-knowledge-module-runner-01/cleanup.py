"""G4 near-duplicate clean-up by MERGE-UPDATE, separate from digestion (schema-delta '소화 규칙 확정': merging is a later,
separate job; user 2026-09-28 '폐기보다 … 업데이트 식'; cleanup-01 showed plain deprecation lost knowledge in 10/19).

  1. pairs: active fragments in the same (host, domain) whose text embeddings (variant 'plain') are >= MIN_SIM
  2. Jev relation; 'different' / uncertain pairs are skipped
  3. Luna (headless pi -p, read tool only) writes one merged sentence per pair, or 'conflict'
  4. guards (merge_guard): code check (identifiers/paths/numbers/negation) -> one re-merge with the missing list;
     then clause-level Jev check. Both must pass, otherwise both fragments stay as they are.
  5. apply: the lower-numbered fragment gets the merged text (revision+1, re-embedded), the other goes active=false;
     history actor 'cleanup:<run>'; receipt JSON with pair, merged text and guard results
Preview by default; --apply changes the DB. A fragment touched earlier in the run is skipped.
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import merge_guard
import store_pg

MIN_SIM = 0.95
DEPRECATE_MIN = 0.8
MAX_PAIRS = 50
VARIANT = "plain"
STATE = Path(os.environ.get("LH_CLEANUP_DIR") or Path.home() / ".local/state/lazy-harness-v2/cleanup")
RELATION = {"type": "choice",
            "instructions": "지식 조각 a 와 b 의 관계는? '포함' 은 한쪽의 모든 조건·값·대상·식별자·이유가 다른 쪽에 다 있을 때만이다.",
            "criteria": {"a_contains_b": "b 의 내용이 모두 a 에 있고 a 에 더 있다",
                         "b_contains_a": "a 의 내용이 모두 b 에 있고 b 에 더 있다",
                         "same": "둘은 같은 내용이다(표현만 다름)",
                         "partial_overlap": "일부만 겹치고 각자에만 있는 내용이 있다",
                         "different": "다른 내용이다",
                         "none_or_uncertain": "판단할 수 없거나 불확실하다"}}


def pairs(dsn, host, min_sim=MIN_SIM, limit=MAX_PAIRS, variant=VARIANT):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select a.id::text, a.alias, a.seq, a.text, b.id::text, b.alias, b.seq, b.text, a.domain,
                              1 - (ea.embedding operator(extensions.<=>) eb.embedding) as sim
                       from knowledge.fragment a join knowledge.fragment b
                         on a.host_id=b.host_id and a.id < b.id
                       join knowledge.fragment_embedding ea on ea.fragment_id=a.id and ea.embed_variant=%s and ea.revision=a.revision
                       join knowledge.fragment_embedding eb on eb.fragment_id=b.id and eb.embed_variant=%s and eb.revision=b.revision
                       where a.host_id=%s and a.active and b.active
                         -- contra06 (2026-10-02): a fragment the judge called a duplicate (source.possible_duplicate) is
                         -- paired at a lower similarity and across domains; the merge guards decide as for any pair
                         and ((a.domain=b.domain and 1 - (ea.embedding operator(extensions.<=>) eb.embedding) >= %s)
                              or (coalesce((a.source->>'possible_duplicate')::boolean, false)
                                  or coalesce((b.source->>'possible_duplicate')::boolean, false))
                                 and 1 - (ea.embedding operator(extensions.<=>) eb.embedding) >= %s)
                       order by sim desc limit %s""", (variant, variant, host, min_sim, DEPRECATE_MIN, limit))
        return [{"a": {"id": r[0], "alias": r[1], "seq": r[2], "text": r[3]},
                 "b": {"id": r[4], "alias": r[5], "seq": r[6], "text": r[7]}, "domain": r[8], "sim": round(r[9], 4)}
                for r in cur.fetchall()]


def _probs(answer):
    p = answer.get("probabilities") or {}
    return {k: float(p.get(k, 1.0 if answer.get("choice") == k else 0.0)) for k in RELATION["criteria"]}


# partial_overlap is never merged (cleanup-02: 5 of the 7 meaning losses came from partial overlaps; user 2026-09-28 'a로 가자').
SKIP_RELATIONS = ("different", "none_or_uncertain", "partial_overlap")
MERGE_PROMPT = """너는 지식 조각을 합치는 작업자다. 파일을 쓰거나 고치지 않는다. 최종 응답은 JSON 하나만.

파일: {FILE}
(pairs = [{id, a, b, missing?, previous_attempt?}] — a 와 b 는 같은 영역에 저장된 비슷한 지식 조각)

## 할 일
pairs 의 **모든 id 에 하나씩** 답한다.
- merge: 두 문장을 합친 **한국어 한두 문장**을 쓴다. 두 문장의 조건·값·대상·식별자·코드 경로·순서·범위·이유·보호 요구를 **빠짐없이** 담는다.
  식별자·경로는 원문 표기 그대로, '…하지 않는다' 같은 부정은 뜻 그대로. 두 문장에 없는 내용은 쓰지 않는다.
  missing 이 있으면 previous_attempt 를 고쳐 missing 항목이 모두 들어가게 한다.
- conflict: 같은 항목에 서로 다른 값·규칙을 말해서 하나로 합칠 수 없으면 conflict, why 에 짧게.

## 출력
{"items":[{"id":"...","action":"merge","text":"합친 문장"},{"id":"...","action":"conflict","why":"..."}]}
"""


def luna_merger(items):
    """items: [{id, a, b, missing?, previous_attempt?}] -> {id: {'action', 'text'|'why'}} via headless pi -p (read only)."""
    import shutil
    import tempfile
    import brief
    sys.path.insert(0, str(Path(__file__).resolve().parent / "fragmenter"))
    from check_fragments import parse, repair_json
    d = Path(tempfile.mkdtemp(prefix="lh-merge-"))
    try:
        os.chmod(d, 0o700)
        f = d / "pairs.json"
        f.write_text(json.dumps({"pairs": items}, ensure_ascii=False))
        out = brief.pi_runner(MERGE_PROMPT.replace("{FILE}", str(f)), str(d))
    finally:
        shutil.rmtree(d, ignore_errors=True)
    parsed = parse(repair_json(out)[0]) or {}
    return {x["id"]: x for x in parsed.get("items", []) if isinstance(x, dict) and x.get("id")}


def _merge_all(cands, merger, chunk=20, workers=4):
    from concurrent.futures import ThreadPoolExecutor
    out = {}
    with ThreadPoolExecutor(workers) as ex:
        for part in ex.map(merger, [cands[k:k + chunk] for k in range(0, len(cands), chunk)]):
            out.update(part)
    return out


def run(dsn, host, judge, ask, merger, *, apply=False, min_sim=MIN_SIM, limit=MAX_PAIRS, variant=VARIANT, state_dir=STATE):
    """judge(packet)->{'answers': {'relation': ...}} (Jev), ask = worker_tools.make_ask (Jev noul), merger(items)->{id: result}."""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    rows, cands, used = [], [], set()
    for p in pairs(dsn, host, min_sim, limit, variant):
        if p["a"]["id"] in used or p["b"]["id"] in used:
            continue
        probs = _probs(judge({"state": {"a": p["a"]["text"], "b": p["b"]["text"]}, "questions": {"relation": RELATION}})["answers"]["relation"])
        rel = max(probs, key=probs.get) if probs else "none_or_uncertain"
        row = {"id": f"p{len(rows)}", "domain": p["domain"], "sim": p["sim"], "relation": rel, "a": p["a"], "b": p["b"],
               "status": "skipped" if rel in SKIP_RELATIONS else "candidate", "applied": False}
        rows.append(row)
        if row["status"] == "candidate":
            cands.append(row)
            used.update({p["a"]["id"], p["b"]["id"]})
    first = _merge_all([{"id": r["id"], "a": r["a"]["text"], "b": r["b"]["text"]} for r in cands], merger)
    retry = []
    for r in cands:
        m = first.get(r["id"]) or {}
        if m.get("action") != "merge" or not str(m.get("text", "")).strip():
            r.update(status="conflict" if m.get("action") == "conflict" else "no_merge", why=m.get("why"))
            continue
        r["merged"] = m["text"].strip()
        r["code_missing"] = merge_guard.code_missing(r["a"]["text"], r["b"]["text"], r["merged"])
        if r["code_missing"]:
            retry.append({"id": r["id"], "a": r["a"]["text"], "b": r["b"]["text"], "previous_attempt": r["merged"], "missing": r["code_missing"]})
    if retry:
        second = _merge_all(retry, merger)
        for r in cands:
            m = second.get(r["id"])
            if m and m.get("action") == "merge" and str(m.get("text", "")).strip():
                r["merged"] = m["text"].strip()
                r["code_missing"] = merge_guard.code_missing(r["a"]["text"], r["b"]["text"], r["merged"])
    for r in cands:
        if "merged" not in r or r["status"] != "candidate":
            continue
        if r["code_missing"]:
            r["status"] = "kept_code"
            continue
        r["clause_missing"] = merge_guard.clause_missing(ask, r["a"]["text"], r["b"]["text"], r["merged"])
        r["status"] = "kept_clause" if r["clause_missing"] else "merge"
    for r in cands:
        if r["status"] != "merge":
            continue
        keep, drop = (r["a"], r["b"]) if (r["a"]["seq"] or 0) <= (r["b"]["seq"] or 0) else (r["b"], r["a"])
        r["keep"], r["drop"] = keep["alias"], drop["alias"]
        if apply:
            with store_pg.connect(dsn) as conn, conn.cursor() as cur:
                cur.execute("select set_config('knowledge.actor', %s, true)", (f"cleanup:{run_id}",))
                cur.execute("update knowledge.fragment set revision=revision+1, text=%s where id=%s and active returning revision",
                            (r["merged"], keep["id"]))
                ok = cur.fetchone() is not None
                cur.execute("update knowledge.fragment set revision=revision+1, active=false where id=%s and active returning revision",
                            (drop["id"],))
                ok = ok and cur.fetchone() is not None
                if not ok:
                    conn.rollback()
                    r["status"] = "stale"
                    continue
            r["applied"] = True
    if apply and any(r["applied"] for r in rows):
        for v in ("plain", "ctx-v1"):
            try:
                store_pg.backfill_embeddings(dsn, host, v)
            except Exception:  # the resident poller backfills later if the embedding service is down
                pass
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    out = {"run_id": run_id, "host": host, "apply": apply, "min_sim": min_sim, "pairs": len(rows), "counts": counts,
           "merged": sum(1 for r in rows if r["status"] == "merge"), "rows": rows}
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / f"{run_id}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def revert(dsn, host, run_id, state_dir=STATE):
    """Undo an applied run from its receipt: the kept fragment gets its original text back, the retired one is active
    again (each revision+1, actor 'revert:<run>'; history keeps both steps)."""
    rec = json.loads((state_dir / f"{run_id}.json").read_text())
    done = []
    for r in rec["rows"]:
        if not r.get("applied"):
            continue
        keep = r["a"] if r["a"]["alias"] == r["keep"] else r["b"]
        drop = r["b"] if keep is r["a"] else r["a"]
        with store_pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("select set_config('knowledge.actor', %s, true)", (f"revert:{run_id}",))
            cur.execute("update knowledge.fragment set revision=revision+1, text=%s where id=%s and text=%s returning 1",
                        (keep["text"], keep["id"], r["merged"]))
            ok = cur.fetchone() is not None
            cur.execute("update knowledge.fragment set revision=revision+1, active=true where id=%s and not active returning 1", (drop["id"],))
            ok = ok and cur.fetchone() is not None
            if not ok:
                conn.rollback()  # changed since the run: leave it for a person
                continue
        done.append(r["keep"])
    if done:
        for v in ("plain", "ctx-v1"):
            try:
                store_pg.backfill_embeddings(dsn, host, v)
            except Exception:
                pass
    return {"run_id": run_id, "reverted": done}


def main():
    import config
    import digest_driver
    ap = argparse.ArgumentParser()
    ap.add_argument("--host")
    ap.add_argument("--revert", metavar="RUN_ID")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=MAX_PAIRS)
    ap.add_argument("--min-sim", type=float, default=MIN_SIM)
    a = ap.parse_args()
    cfg = config.require("db_url")
    host = a.host or config.load().get("default_host")
    if a.revert:
        print(json.dumps(revert(cfg["db_url"], host, a.revert)))
        return
    import worker_tools
    ask = worker_tools.make_ask(config.require("jev_api_key", "jev_base_url", "jev_model"))
    out = run(cfg["db_url"], host, digest_driver._jev_judge, ask, luna_merger, apply=a.apply, min_sim=a.min_sim, limit=a.limit)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}))


if __name__ == "__main__":
    main()
