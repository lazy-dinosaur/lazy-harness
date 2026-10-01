"""audit-01/flow_par: two work units in parallel on the same knowledge (disposable copy of the main DB + 0009).
P1 compatible: A '설명 1000자' / B '줄바꿈도 제거' (both touch fragment 9, different parts).
P2 conflicting: A '설명 1000자' / B '설명 800자'. After both complete: poller; then every review approved; poller again."""
import json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R))
import backup, config, store_pg, knowledge_cli
PI = "/home/lazydino/.npm-global/bin/pi"
NAME = "lhv2-flow"; IMAGE = "public.ecr.aws/supabase/postgres:17.6.1.134"
ROOT = Path("/tmp/lhv2-par"); ROOT.mkdir(exist_ok=True)
WT = {"A": Path("/tmp/lhv2-live"), "B": Path("/tmp/lhv2-live-b")}
SCEN = {
 "P1": {"A": ["도메인 설명 길이 제한을 1000자로 늘려줘", "좋아 이걸로 완료하자"],
        "B": ["domain describe 에서 설명의 앞뒤 공백뿐 아니라 줄바꿈도 제거하도록 바꿔줘", "좋아 이걸로 완료하자"]},
 "P2": {"A": ["도메인 설명 길이 제한을 1000자로 늘려줘", "좋아 이걸로 완료하자"],
        "B": ["도메인 설명 길이 제한을 800자로 바꿔줘", "좋아 이걸로 완료하자"]},
}


def sh(*a, **k):
    return subprocess.run(list(a), capture_output=True, text=True, **k)


def setup():
    sh("docker", "rm", "-f", NAME)
    assert sh("docker", "run", "-d", "--rm", "--name", NAME, "-p", "127.0.0.1::5432", "-e", "POSTGRES_PASSWORD=localtest", IMAGE).returncode == 0
    port = sh("docker", "port", NAME, "5432/tcp").stdout.split("\n")[0].rsplit(":", 1)[-1]
    dsn = f"postgresql://postgres:localtest@127.0.0.1:{port}/postgres"
    for _ in range(60):
        try:
            with store_pg.connect(dsn) as c, c.cursor() as cur:
                cur.execute("select 1"); break
        except Exception:
            time.sleep(2)
    time.sleep(5)
    backup.restore(sorted(backup.DIR.glob("knowledge-*.dump"))[-1], dsn)
    for mig in sorted((R / "migrations").glob("0009_*.sql")):
        assert sh("docker", "exec", "-i", NAME, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres", "-f", "-", input=mig.read_text()).returncode == 0
    main = json.loads((Path.home() / ".config/lazy-harness-v2/knowledge.json").read_text())
    main["db_url"] = dsn
    cp = ROOT / "knowledge.json"; cp.write_text(json.dumps(main, ensure_ascii=False)); os.chmod(cp, 0o600)
    for w in WT.values():
        if not w.exists():
            sh("git", "-C", "/home/lazydino/dev/lazy-harness.v2", "worktree", "add", "-q", "--detach", str(w), "HEAD")
        sh("git", "-C", str(w), "checkout", "-q", "--", "."); sh("git", "-C", str(w), "clean", "-qfd")
    return dsn, {**os.environ, "LH_KNOWLEDGE_CONFIG": str(cp)}


def session(env, tag, who, turns):
    sess = ROOT / f"{tag}-{who}.session.jsonl"
    if sess.exists(): sess.unlink()
    out = []
    for k, prompt in enumerate(turns, 1):
        t0 = time.time(); f = ROOT / f"{tag}-{who}-T{k}.jsonl"
        with open(f, "w") as fh:
            r = subprocess.run([PI, "-ne", "-nc", "-ns", "--session", str(sess), "-e", str(R / "pi-extension/knowledge.ts"),
                                "-e", str(R / "pi-extension/harness-rules.ts"), "--mode", "json", "-p", prompt],
                               cwd=WT[who], env=env, stdout=fh, stderr=subprocess.PIPE, text=True, timeout=900)
        calls, cost = [], 0.0
        for line in open(f, errors="replace"):
            try: e = json.loads(line)
            except ValueError: continue
            m = e.get("message") or {}
            if e.get("type") == "message_end" and m.get("role") == "assistant":
                cost += ((m.get("usage") or {}).get("cost") or {}).get("total") or 0
                calls += [c.get("name") for c in m.get("content") or [] if c.get("type") == "toolCall" and str(c.get("name")).startswith("knowledge_")]
        out.append({"turn": k, "exit": r.returncode, "secs": round(time.time() - t0, 1), "cost": round(cost, 3), "knowledge_calls": calls, "stderr": r.stderr[-200:]})
    return out


def q(dsn, sql, a=()):
    with store_pg.connect(dsn) as c, c.cursor() as cur:
        cur.execute(sql, a); return cur.fetchall()


def snapshot(dsn, host, label):
    frags = q(dsn, "select alias, text from knowledge.fragment where active and (text ~ '(300|800|1000)자' or alias in ('knowledge-module-9')) order by alias")
    print(label, "FRAGS", json.dumps(frags, ensure_ascii=False), flush=True)
    items = knowledge_cli.review_cmd(dsn, {"action": "list", "host_id": host})["items"]
    print(label, "REVIEW", json.dumps([{"fact": i["fact"][:90], "why": i["why_waiting"]} for i in items], ensure_ascii=False), flush=True)
    print(label, "ABSORB", q(dsn, "select rule_id, decision::text, count(*) from knowledge.absorption where created_at > now()-interval '2 hour' group by 1,2 order by 1"), flush=True)
    return items


def poll(env, n=4):
    for _ in range(n):
        subprocess.run(["/usr/bin/python3", str(R / "poller.py"), "--once", "--judge", "jev", "--state", str(ROOT / "poller.json")], env=env, capture_output=True, timeout=900)
        time.sleep(2)


def main(tag):
    dsn, env = setup()
    host = json.loads((ROOT / "knowledge.json").read_text())["default_host"]
    with ThreadPoolExecutor(2) as pool:
        runs = dict(zip("AB", pool.map(lambda w: session(env, tag, w, SCEN[tag][w]), "AB")))
    print(tag, "SESSIONS", json.dumps(runs, ensure_ascii=False), flush=True)
    print(tag, "UNITS", q(dsn, "select work_unit_id::text, status::text, completed_at from knowledge.work_unit where created_at > now()-interval '2 hour' order by completed_at"), flush=True)
    poll(env)
    items = snapshot(dsn, host, tag + " after-poll")
    # simulated user: in P2 the user picks 1000자 (rejects 800자); everything else approved. Unblocking can surface
    # new review items, so answer and digest up to three rounds.
    for rnd in range(1, 4):
        if not items:
            break
        for it in items:
            decision = "reject" if tag == "P2" and "800" in (it.get("fact") or "") else "approve"
            store_pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], decision, "응 그렇게 해" if decision == "approve" else "아니 그건 아니야", "test/user", it.get("question_ids"))
        poll(env)
        items = snapshot(dsn, host, f"{tag} after-answer{rnd}")
    print(tag, "CONTRADICTIONS", json.dumps(q(dsn, "select rule_id, status::text, left(reason, 300) from knowledge.confirmation_queue where rule_id='canon_contradiction' order by created_at"), ensure_ascii=False), flush=True)
    for w in WT.values():
        sh("git", "-C", str(w), "checkout", "-q", "--", "."); sh("git", "-C", str(w), "clean", "-qfd")


if __name__ == "__main__":
    for tag in sys.argv[1:] or ["P1", "P2"]:
        main(tag)
