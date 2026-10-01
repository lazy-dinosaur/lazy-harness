"""audit-01/flow3: real pi sessions after the 2026-09-30 schema work (3766f10 .. 5788e7f): two work units in parallel on a
disposable copy of the main DB + 0009 subject dictionary + 0010 fact form. Same scenarios as flow_par (P1 compatible,
P2 conflicting). Everything is written under ~/.cache/lh-flow3 (not /tmp). Reports, besides flow_par's:
E_FORM rejections and operator use in the parent's records, subject matches (from -> to), stored forms and leaves,
dictionary size, how the Korean view reads, the review questions as the user would see them."""
import json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R))
import backup, store_pg, knowledge_cli, fact_text
PI = "/home/lazydino/.npm-global/bin/pi"
V2 = Path("/home/lazydino/dev/lazy-harness.v2")
NAME = "lhv2-flow3"; IMAGE = "public.ecr.aws/supabase/postgres:17.6.1.134"
ROOT = Path.home() / ".cache/lh-flow3"; ROOT.mkdir(parents=True, exist_ok=True)
TMP = ROOT / "tmp"; TMP.mkdir(exist_ok=True)
WT = {"A": ROOT / "wt-A", "B": ROOT / "wt-B"}
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
    for mig in ("0009_subject_dictionary.sql", "0010_fact_form.sql"):
        r = sh("docker", "exec", "-i", NAME, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres", "-f", "-",
               input=(R / "migrations" / mig).read_text())
        assert r.returncode == 0, (mig, r.stderr[-400:])
    main = json.loads((Path.home() / ".config/lazy-harness-v2/knowledge.json").read_text())
    main["db_url"] = dsn
    cp = ROOT / "knowledge.json"; cp.write_text(json.dumps(main, ensure_ascii=False)); os.chmod(cp, 0o600)
    for w in WT.values():
        if not w.exists():
            sh("git", "-C", str(V2), "worktree", "add", "-q", "--detach", str(w), "HEAD")
        sh("git", "-C", str(w), "checkout", "-q", "--detach", sh("git", "-C", str(V2), "rev-parse", "HEAD").stdout.strip())
        sh("git", "-C", str(w), "checkout", "-q", "--", "."); sh("git", "-C", str(w), "clean", "-qfd")
    return dsn, {**os.environ, "LH_KNOWLEDGE_CONFIG": str(cp), "TMPDIR": str(TMP)}


def session(env, tag, who, turns):
    sess = ROOT / f"{tag}-{who}.session.jsonl"
    if sess.exists(): sess.unlink()
    out = []
    for k, prompt in enumerate(turns, 1):
        t0 = time.time(); f = ROOT / f"{tag}-{who}-T{k}.jsonl"
        with open(f, "w") as fh:
            r = subprocess.run([PI, "-ne", "-nc", "-ns", "--session", str(sess), "-e", str(R / "pi-extension/knowledge.ts"),
                                "-e", str(R / "pi-extension/harness-rules.ts"), "--mode", "json", "-p", prompt],
                               cwd=WT[who], env=env, stdout=fh, stderr=subprocess.PIPE, text=True, timeout=1500)
        calls, cost, eform, subj, contra = [], 0.0, 0, [], 0
        for line in open(f, errors="replace"):
            try: e = json.loads(line)
            except ValueError: continue
            m = e.get("message") or {}
            if e.get("type") == "message_end" and m.get("role") == "assistant":
                cost += ((m.get("usage") or {}).get("cost") or {}).get("total") or 0
                calls += [c.get("name") for c in m.get("content") or [] if c.get("type") == "toolCall" and str(c.get("name")).startswith("knowledge_")]
            if e.get("type") == "message_end" and m.get("role") == "toolResult" and str(m.get("toolName", "")).startswith("knowledge_record"):
                body = json.dumps(m.get("content"), ensure_ascii=False)
                eform += body.count("E_FORM")
                contra += body.count("contradictions")
                subj += re.findall(r'\\"from\\": \\"([^\\]+)\\", \\"to\\": \\"([^\\]+)\\"', body)
        out.append({"turn": k, "exit": r.returncode, "secs": round(time.time() - t0, 1), "cost": round(cost, 3),
                    "knowledge_calls": calls, "E_FORM": eform, "subject_matches": subj, "in_unit_contradictions": contra,
                    "stderr": r.stderr[-200:]})
    return out


def q(dsn, sql, a=()):
    with store_pg.connect(dsn) as c, c.cursor() as cur:
        cur.execute(sql, a); return cur.fetchall()


def snapshot(dsn, host, label):
    frags = q(dsn, """select alias, revision, text, form is not null, subject_id is not null from knowledge.fragment
                     where active and (text ~ '(300|800|1000)자' or alias in ('knowledge-module-9')) order by alias""")
    print(label, "FRAGS", json.dumps([{"alias": a, "rev": v, "text": t, "form": f, "subject": s, "korean": fact_text.view(t)}
                                      for a, v, t, f, s in frags], ensure_ascii=False), flush=True)
    items = knowledge_cli.review_cmd(dsn, {"action": "list", "host_id": host})["items"]
    print(label, "REVIEW", json.dumps([{"kind": i.get("kind"), "fact": i["fact"][:160], "why": i["why_waiting"]} for i in items], ensure_ascii=False), flush=True)
    print(label, "ABSORB", q(dsn, "select rule_id, decision::text, count(*) from knowledge.absorption where created_at > now()-interval '2 hour' group by 1,2 order by 1"), flush=True)
    return items


def ledger(dsn):
    rows = q(dsn, "select judgement_body from knowledge.ledger_entry where created_at > now()-interval '2 hour' order by created_at")
    facts = [f for (b,) in rows for f in b.get("facts", [])]
    return [{"op": f.get("operation"), "fact": f.get("fact"), "subject": f.get("subject"), "as_written": f.get("subject_as_written"),
             "new_subject": f.get("subject_new"), "form_kind": (f.get("form") or {}).get("kind"),
             "operators": bool(re.search(r"\b(IF|THEN|AND|OR|EVEN IF|EXCEPT WHEN|BEFORE|AFTER|BECAUSE)\b", f.get("fact") or ""))}
            for f in facts]


def poll(env, n=4):
    for _ in range(n):
        subprocess.run(["/usr/bin/python3", str(R / "poller.py"), "--once", "--judge", "jev", "--state", str(ROOT / "poller.json")],
                       env=env, capture_output=True, timeout=900)
        time.sleep(2)


def main(tag):
    dsn, env = setup()
    host = json.loads((ROOT / "knowledge.json").read_text())["default_host"]
    with ThreadPoolExecutor(2) as pool:
        runs = dict(zip("AB", pool.map(lambda w: session(env, tag, w, SCEN[tag][w]), "AB")))
    print(tag, "SESSIONS", json.dumps(runs, ensure_ascii=False), flush=True)
    print(tag, "LEDGER", json.dumps(ledger(dsn), ensure_ascii=False), flush=True)
    print(tag, "UNITS", q(dsn, "select work_unit_id::text, status::text from knowledge.work_unit where created_at > now()-interval '2 hour' order by completed_at"), flush=True)
    poll(env)
    items = snapshot(dsn, host, tag + " after-poll")
    for rnd in range(1, 4):
        if not items:
            break
        for it in items:
            decision = "reject" if tag == "P2" and "800" in (it.get("fact") or "") else "approve"
            store_pg.review_resolve(dsn, host, it["entry_id"], it["fact_index"], decision,
                                    "응 그렇게 해" if decision == "approve" else "아니 그건 아니야", "test/user")
        poll(env)
        items = snapshot(dsn, host, f"{tag} after-answer{rnd}")
    print(tag, "STRUCTURE", json.dumps({
        "fragments_with_form": q(dsn, "select count(*) from knowledge.fragment where form is not null")[0][0],
        "leaves": q(dsn, "select role, polarity, count(*) from knowledge.fragment_leaf group by 1,2 order by 1,2"),
        "subjects": q(dsn, "select name from knowledge.subject order by created_at"),
        "routing": q(dsn, """select r.packet->>'template_id', count(*) from knowledge.check_receipt r where r.stage='digestion'
                             and r.created_at > now()-interval '2 hour' group by 1""")}, ensure_ascii=False, default=str), flush=True)
    print(tag, "CONTRADICTIONS", json.dumps(q(dsn, "select rule_id, status::text, left(reason, 400) from knowledge.confirmation_queue where rule_id='canon_contradiction' order by created_at"), ensure_ascii=False), flush=True)
    for w in WT.values():
        sh("git", "-C", str(w), "checkout", "-q", "--", "."); sh("git", "-C", str(w), "clean", "-qfd")
    sh("docker", "rm", "-f", NAME)


if __name__ == "__main__":
    for tag in sys.argv[1:] or ["P1", "P2"]:
        main(tag)
