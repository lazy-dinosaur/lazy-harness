"""Medivance pilot 02 (frozen plan medivance-pilot-02/plan.json). Local-only; no production DB."""
import collections
import argparse
import json
import math
import os
import random
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import collect
import embed
import store_pg as pg

HERE = Path(__file__).resolve().parent
BASE = HERE / "medivance-pilot-02"
OUT = BASE
IMAGE = "public.ecr.aws/supabase/postgres:17.6.1.134"
NAME = "lh-kdb-test-10"
MODEL = "typesafe/jev-1.13"
HOST = "medivance-pilot"
QUESTION = {
    "narrow": "candidates 의 {i}번 조각은 topic 이 가리키는 바로 그 기능·규칙·동작·구현에 대한 설명인가? 다른 기능의 비슷한 개념(예: 다른 곳의 중단 조건·저장소)이면 false.",
    "relaxed": "candidates 의 {i}번 조각은 topic 을 이해하거나 topic 의 기능을 작업할 때 알아야 할 내용인가?",
}
CRITERIA = {
    "narrow": {"true": "topic 이 가리키는 그 기능·규칙에 대한 설명이다", "false": "다른 기능이거나 주제와 무관하다"},
    "relaxed": {"true": "topic 을 다루는 데 필요한 내용이다", "false": "topic 과 무관하다"},
}


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def docker(*args, input=None):
    return subprocess.run(["docker", *args], input=input, text=True, capture_output=True, check=True).stdout.strip()


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_health(url, process=None):
    for _ in range(120):
        if process is not None and process.poll() is not None:
            raise RuntimeError("embedding process exited")
        try:
            with urllib.request.urlopen(url, timeout=1):
                return
        except (OSError, urllib.error.URLError):
            time.sleep(1)
    raise RuntimeError("local service failed health check")


def safe_error(error, key):
    # HTTP exception text can include the URL, but never retain a credential or response headers.
    return type(error).__name__ + (" (credential redacted)" if key and key in str(error) else "")


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", choices=sorted(QUESTION), default="narrow")
    parser.add_argument("--out", default="run-01")
    args = parser.parse_args()
    args.jev_only = False
    OUT = BASE / args.out
    if OUT.exists():
        raise RuntimeError(f"{args.out} exists; refusing overwrite")
    OUT.mkdir()
    first = None
    prior = {(t["record_id"], t["variant"]): t for t in first["topics"]} if first else {}
    log = []
    def event(text):
        log.append(text)
        (OUT / "run.log").write_text("\n".join(log) + "\n", encoding="utf-8")

    key = os.environ.get("TYPESAFE_API_KEY")
    base = os.environ.get("TYPESAFE_BASE_URL")
    if not key or not base:
        raise RuntimeError("TYPESAFE_API_KEY and TYPESAFE_BASE_URL must be present; no run started")
    if not base.startswith("https://"):
        raise RuntimeError("TYPESAFE_BASE_URL must be HTTPS")
    if not shutil.which("docker"):
        raise RuntimeError("Docker unavailable")
    if docker("ps", "-a", "--filter", f"name=^/{NAME}$", "--format", "{{.Names}}"):
        raise RuntimeError(f"STOP: {NAME} already exists; untouched")
    docker("image", "inspect", IMAGE, "--format", "{{.Id}}")
    fragments = json.loads((BASE / "fragments-all.json").read_text(encoding="utf-8"))
    records = {r["record_id"]: r for r in json.loads((BASE / "records.json").read_text(encoding="utf-8"))}
    topics = json.loads((HERE / "medivance-pilot-01/topics.json").read_text(encoding="utf-8"))["topics"]
    term = {q["record_id"]: q["query"] for q in json.loads((BASE / "term-queries.json").read_text(encoding="utf-8"))["term_queries"]}
    topics = [dict(t, queries=t["queries"] + [term[t["record_id"]]]) for t in topics if t["record_id"] != "R10"]
    assert len(topics) == 19 and all(len(t["queries"]) == 4 for t in topics)
    assert len({f["record_id"] for f in fragments}) == 60
    counts = collections.Counter(f["record_id"] for f in fragments)
    # The experiment is local-only even when unrelated LH_KNOWLEDGE_DB_URL is present.
    db_port, embed_port = free_port(), free_port()
    while embed_port == db_port:
        embed_port = free_port()
    dsn = f"postgresql://postgres:localtest@127.0.0.1:{db_port}/postgres"
    embed_url = f"http://127.0.0.1:{embed_port}"
    started = False
    process = None
    previous_embed = os.environ.get("LH_EMBED_URL")
    result = {"experiment": "medivance-pilot-02", "question_variant": args.question, "host": HOST, "excluded": {"record_id": "R10", "reason": "원본에 # 제목이 없어 주제 생성기가 ## Rule digest를 제목으로 착각; 질문이 기록 내용과 무관"}, "gold_definition": "같은 record_id의 조각만 정답; 다른 기록의 실제 관련 조각도 정답 외로 집계", "total_fragments": len(fragments), "topics": [], "raw_responses": [], "judge_calls": 0, "judge_failures": 0}
    if args.jev_only:
        result["baseline_provenance"] = "A/B-oracle metrics copied from run-01-failed; their returned_ids omitted because DB regenerated; only B-jev rerun"
    judgments = []
    try:
        event("starting isolated loopback container and embedding process")
        docker("run", "-d", "--rm", "--name", NAME, "-p", f"127.0.0.1:{db_port}:5432", "-e", "POSTGRES_PASSWORD=localtest", IMAGE)
        started = True
        for _ in range(120):
            if docker("inspect", NAME, "--format", "{{.State.Health.Status}}") == "healthy":
                try:
                    with pg.connect(dsn) as conn, conn.cursor() as cur:
                        cur.execute("select 1")
                    break
                except pg.driver.Error:
                    pass
            time.sleep(1)
        else:
            raise RuntimeError("local postgres not healthy")
        for name in ("0001_knowledge_init.sql", "0002_search_and_cost.sql", "0003_embedding_hybrid.sql"):
            docker("exec", "-i", NAME, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres", "-f", "-", input=(HERE / "migrations" / name).read_text())
        python = embed._MODEL_DIR / "venv/bin/python"
        os.environ["LH_EMBED_URL"] = embed_url
        with (OUT / "embedding.log").open("w") as stream:
            process = subprocess.Popen([str(python), str(HERE / "embed_server.py"), "--port", str(embed_port)], stdout=stream, stderr=stream)
        wait_health(embed_url + "/health", process)
        event(f"local services healthy; inserting {len(fragments)} fragments")
        ids = {}
        seq = collections.Counter()
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("insert into knowledge.host(host_id,name,repo_locator) values (%s,%s,%s)", (HOST, HOST, "local-copy"))
            for index, fragment in enumerate(fragments):
                record_id = fragment["record_id"]
                domain = records[record_id]["layer"]
                seq[domain] += 1
                cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                    values (%s,%s,%s,%s,%s,%s,%s,%s::jsonb) returning id::text""",
                    (HOST, f"{record_id}-{index:04d}", domain, seq[domain], fragment["text"], fragment["kind"], f"{record_id}:{fragment.get('group') or index}",
                     json.dumps({"record_id": record_id, "source_lines": fragment["source_lines"], "evidence_refs": [], "copy": records[record_id]["copy"]}, ensure_ascii=False)))
                ids[cur.fetchone()[0]] = fragment
        for variant in ("plain", "ctx-v1"):
            n = pg.backfill_embeddings(dsn, HOST, variant)
            if n != len(fragments):
                raise RuntimeError(f"incomplete {variant} embedding backfill: {n}")
            event(f"{variant}: embedded {n}")
        for variant in ("plain", "ctx-v1"):
            for topic in topics:
                rid = topic["record_id"]
                entry = {"record_id": rid, "title": topic["title"], "gold_count": counts[rid], "variant": variant, "methods": {}}
                gold = lambda c: ids[c["id"]]["record_id"] == rid
                if not args.jev_only:
                    a = pg.search(dsn, HOST, topic["queries"][0], 30, mode="hybrid", variant=variant, expand=False)
                    if any(c["mode_used"] != "hybrid" for c in a):
                        raise RuntimeError("hybrid search fell back to text")
                def metrics(returned, read, trace, picked=None):
                    correct = sum(gold(c) for c in returned)
                    extra = {} if picked is None else {"recall_no_group": sum(gold(c) for c in picked) / counts[rid], "picked": len(picked), "picked_non_gold": sum(not gold(c) for c in picked)}
                    return {**extra, "gold_found": correct, "recall": correct / counts[rid], "non_gold": len(returned) - correct,
                            "precision": correct / len(returned) if returned else None, "read": read, "returned": len(returned),
                            "returned_ids": [c["id"] for c in returned], "trace": trace,
                            "stop_reasons": dict(collections.Counter(t["stop"] for t in trace))}
                if args.jev_only:
                    entry["methods"] = {method: {k: v for k, v in prior[(rid, variant)]["methods"][method].items() if k != "returned_ids"} for method in ("A", "B-oracle")}
                else:
                    entry["methods"]["A"] = metrics(a, len(a), [{"query": topic["queries"][0], "pages": 1, "read": len(a), "stop": "top_30"}])
                    def oracle(query, candidates):
                        return [{"relevant": gold(c), "novel": gold(c)} for c in candidates]
                    b = collect.collect_topic(dsn, HOST, topic["queries"], judge=oracle, variant=variant)
                    entry["methods"]["B-oracle"] = metrics(b["note"], sum(t["read"] for t in b["trace"]), b["trace"], b["relevant"])
                page_counter = 0
                def jev(query, candidates):
                    nonlocal page_counter
                    page_counter += 1
                    page = page_counter
                    packet = {"state": {"topic": topic["title"], "queries": topic["queries"],
                                        "candidates": [{"i": i, "text": c["text"]} for i, c in enumerate(candidates)]},
                              "questions": {str(i): {"type": "noul", "instructions": QUESTION[args.question].format(i=i), "criteria": CRITERIA[args.question]} for i in range(len(candidates))}, "model": MODEL}
                    for attempt in (1, 2):
                        result["judge_calls"] += 1
                        path = OUT / "jev-raw" / f"{variant}-{rid}-page{page:03d}-attempt{attempt}.json"
                        try:
                            request = urllib.request.Request(base.rstrip("/") + "/v1/systemone", data=json.dumps(packet, ensure_ascii=False).encode(), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
                            with urllib.request.urlopen(request, timeout=60) as response:
                                raw = response.read()
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(raw)
                            parsed = json.loads(raw)
                            answers = parsed["answers"]
                            if set(answers) != set(packet["questions"]):
                                raise ValueError("answer keys mismatch")
                            scores = [answers[str(i)]["noul"] for i in range(len(candidates))]
                            if any(answers[str(i)].get("type") != "noul" or not isinstance(s, (float, int)) or isinstance(s, bool) or not math.isfinite(s) or not 0 <= s <= 1 for i, s in enumerate(scores)):
                                raise ValueError("invalid noul scores")
                            result["raw_responses"].append(str(path.relative_to(OUT)))
                            for c, score in zip(candidates, scores):
                                judgments.append({"record_id": rid, "topic": topic["title"], "variant": variant, "query": query, "candidate_id": c["id"], "text": c["text"], "score": score, "relevant": score >= .5, "gold": gold(c), "response_path": str(path.relative_to(OUT))})
                            return [{"relevant": s >= .5, "novel": s >= .5} for s in scores]
                        except (OSError, TimeoutError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                            if isinstance(error, urllib.error.HTTPError):
                                path.parent.mkdir(parents=True, exist_ok=True)
                                path.write_bytes(error.read().replace(key.encode(), b"[REDACTED]"))
                            result["judge_failures"] += 1
                            result.setdefault("failed_pages", []).append({"variant": variant, "record_id": rid, "query": query, "page": page, "attempt": attempt, "error": safe_error(error, key), "http_status": error.code if isinstance(error, urllib.error.HTTPError) else None, "raw_path": str(path.relative_to(OUT)) if path.exists() else None})
                    raise collect.JudgePageFailure()
                b = collect.collect_topic(dsn, HOST, topic["queries"], judge=jev, variant=variant)
                entry["methods"]["B-jev"] = metrics(b["note"], sum(t["read"] for t in b["trace"]), b["trace"], b["relevant"])
                result["topics"].append(entry)
                event(f"{variant} {rid}: A={entry['methods']['A']['recall']:.3f} oracle={entry['methods']['B-oracle']['recall_no_group']:.3f} Jev={entry['methods']['B-jev']['recall_no_group']:.3f} calls={result['judge_calls']} failures={result['judge_failures']}")
                save(OUT / "result.json", result)
        result["means"] = {method: {variant: {metric: sum(t["methods"][method][metric] for t in result["topics"] if t["variant"] == variant) / 19 for metric in ("recall", "read", "non_gold", "returned") + (("recall_no_group", "picked_non_gold") if method != "A" else ())} for variant in ("plain", "ctx-v1")} for method in ("A", "B-oracle", "B-jev")}
        result["judgments"] = judgments
        result["judge_accuracy"] = {label: {"total": len(rows), "relevant": sum(r["relevant"] for r in rows), "rate": sum(r["relevant"] for r in rows) / len(rows) if rows else None} for label, rows in (("gold", [j for j in judgments if j["gold"]]), ("non_gold", [j for j in judgments if not j["gold"]]))}
        rng = random.Random(20260924)
        groups = [[j for j in judgments if j["gold"] == g and j["relevant"] == r] for g in (True, False) for r in (True, False)]
        for group in groups:
            rng.shuffle(group)
        selection = []
        while len(selection) < 60 and any(groups):
            for group in groups:
                if group and len(selection) < 60:
                    selection.append(group.pop())
        result["human_review_count"] = len(selection)
        review = ["# Jev 판정 사람 검토 (seed 20260924)", "", "정답은 동일 record_id 기준; 정답 외도 실제로 관련될 수 있음.", ""]
        for n, j in enumerate(selection, 1):
            review += [f"## {n}. {j['variant']} / {j['record_id']} — {j['topic']}", "", f"- Jev: {'관련' if j['relevant'] else '비관련'} ({j['score']:.4f}); 정답 조각: {'예' if j['gold'] else '아니오'}", "- 사람 판정: ______", "", j["text"], ""]
        (OUT / "human-review.md").write_text("\n".join(review), encoding="utf-8")
        lines = ["# Medivance 검색 파일럿", "", "R10 제외: 원본에 # 제목이 없어 ## Rule digest를 제목으로 오인한 무관한 질문. 19개 주제 × 두 벡터 방식.", "", "| 방식 | 벡터 | 평균 재현율 | 평균 읽은 조각 | 평균 정답 외 반환 |", "|---|---|---:|---:|---:|"]
        for method in ("A", "B-oracle", "B-jev"):
            for variant in ("plain", "ctx-v1"):
                m = result["means"][method][variant]
                lines.append(f"| {method} | {variant} | {m['recall']:.3f} | {m['read']:.1f} | {m['non_gold']:.1f} |")
        lines += ["", f"Jev 호출 {result['judge_calls']}, 실패 시도 {result['judge_failures']} (최종 실패 페이지 {len([p for p in result.get('failed_pages', []) if p['attempt'] == 2])}).", f"정답 판정 relevant 비율 {result['judge_accuracy']['gold']['rate']}; 정답 외 판정 relevant 비율 {result['judge_accuracy']['non_gold']['rate']}.", "정답 외에도 실제로 관련 있을 수 있으므로 정답 외 relevant는 의미론적 오판율이 아니다.", "collect_topic note는 relevant 조각의 같은 group_id 전체를 확장해 포함한다. 읽은 수는 검색 페이지 수, 반환 수는 확장 후 중복 제거한 수다.", "", "## 주제별", "", "| 주제 | 벡터 | A 재현율 | oracle 재현율 | Jev 재현율 | Jev 읽음 | 멈춤 사유 |", "|---|---|---:|---:|---:|---:|---|"]
        for t in result["topics"]:
            m = t["methods"]
            lines.append(f"| {t['record_id']} {t['title']} | {t['variant']} | {m['A']['recall']:.3f} | {m['B-oracle']['recall']:.3f} | {m['B-jev']['recall']:.3f} | {m['B-jev']['read']} | {m['B-jev']['stop_reasons']} |")
        (OUT / "result.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        save(OUT / "result.json", result)
        event("results and human-review written")
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if previous_embed is None:
            os.environ.pop("LH_EMBED_URL", None)
        else:
            os.environ["LH_EMBED_URL"] = previous_embed
        if started:
            docker("rm", "-f", "-v", NAME)
        event(f"cleanup: container absent={not bool(docker('ps', '-a', '--filter', f'name=^/{NAME}$', '--format', '{{.Names}}'))}, embed process stopped={process is None or process.poll() is not None}")


if __name__ == "__main__":
    main()
