"""audit-01/flow: multi-turn real flow on a disposable copy of the main DB.
request -> clarify -> decide+edit -> user confirms completion -> poller digests -> canonical. Main DB untouched."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R))
import backup, config, store_pg

PI = "/home/lazydino/.npm-global/bin/pi"
NAME = "lhv2-flow"; IMAGE = "public.ecr.aws/supabase/postgres:17.6.1.134"
ROOT = Path("/tmp/lhv2-flow"); ROOT.mkdir(exist_ok=True)
WT = Path("/tmp/lhv2-live")
TURNS = ["도메인 설명 길이 제한을 늘려줘", "1000자로 늘려줘", "좋아 이걸로 완료하자"]


def sh(*a, **k):
    return subprocess.run(list(a), capture_output=True, text=True, **k)


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
dump = sorted(backup.DIR.glob("knowledge-*.dump"))[-1]
print(json.dumps({"restore": {k: v for k, v in backup.restore(dump, dsn).items() if k != "expected"}}, default=str)[:400], flush=True)
for mig in sorted((R / "migrations").glob("0009_*.sql")):  # not yet on the main DB: apply to the disposable copy
    out = subprocess.run(["docker", "exec", "-i", NAME, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres", "-f", "-"],
                         input=mig.read_text(), capture_output=True, text=True)
    print(json.dumps({"migration": mig.name, "rc": out.returncode, "err": out.stderr[-300:]}), flush=True)

main = json.loads(config.config_path().read_text()) if hasattr(config, "config_path") else json.loads((Path.home() / ".config/lazy-harness-v2/knowledge.json").read_text())
main["db_url"] = dsn
cp = ROOT / "knowledge.json"; cp.write_text(json.dumps(main, ensure_ascii=False)); os.chmod(cp, 0o600)
env = {**os.environ, "LH_KNOWLEDGE_CONFIG": str(cp)}
env.pop("LH_KNOWLEDGE_DB_URL", None)

sh("git", "-C", str(WT), "checkout", "-q", "--", "."); sh("git", "-C", str(WT), "clean", "-qfd")
sess = ROOT / "session.jsonl"
if sess.exists(): sess.unlink()


def q(sql, a=()):
    with store_pg.connect(dsn) as c, c.cursor() as cur:
        cur.execute(sql, a); return cur.fetchall()


for k, prompt in enumerate(TURNS, 1):
    t0 = time.time(); f = ROOT / f"T{k}.jsonl"
    with open(f, "w") as fh:
        r = subprocess.run([PI, "-ne", "-nc", "-ns", "--session", str(sess), "-e", str(R / "pi-extension/knowledge.ts"),
                            "-e", str(R / "pi-extension/harness-rules.ts"), "--mode", "json", "-p", prompt],
                           cwd=WT, env=env, stdout=fh, stderr=open(ROOT / f"T{k}.err", "w"), timeout=600)
    steps, harness, cost = [], [], 0.0
    for line in open(f, errors="replace"):
        try: e = json.loads(line)
        except ValueError: continue
        if e.get("type") == "message_end":
            m = e.get("message") or {}
            if m.get("role") == "assistant":
                cost += ((m.get("usage") or {}).get("cost") or {}).get("total") or 0
                for c in m.get("content") or []:
                    if c.get("type") == "toolCall": steps.append("call " + str(c.get("name")) + " " + json.dumps(c.get("arguments"), ensure_ascii=False)[:300])
                    elif c.get("type") == "text" and c["text"].strip(): steps.append("text " + c["text"][:400])
            elif m.get("role") == "toolResult":
                steps.append("result " + "".join(x.get("text", "") for x in m.get("content") or [] if isinstance(x, dict))[:250])
        elif e.get("type") == "entry_appended" and (e.get("entry") or {}).get("type") == "custom_message":
            en = e["entry"]; harness.append(f"{en.get('customType')}: {str(en.get('content'))[:500]}")
    print(json.dumps({"turn": k, "prompt": prompt, "exit": r.returncode, "secs": round(time.time() - t0, 1), "cost": round(cost, 4),
                      "harness": harness, "steps": steps, "diff": sh("git", "-C", str(WT), "diff", "--stat").stdout,
                      "stderr": (ROOT / f"T{k}.err").read_text()[-400:]}, ensure_ascii=False), flush=True)

print("DIFF " + sh("git", "-C", str(WT), "diff").stdout[:2500], flush=True)
print("UNITS " + json.dumps(q("select work_unit_id::text, status::text from knowledge.work_unit where created_at > now() - interval '1 hour'"), default=str), flush=True)
print("LEDGER " + json.dumps(q("select work_unit_id::text, state::text, left(judgement_body::text, 900) from knowledge.ledger_entry where created_at > now() - interval '1 hour'"), ensure_ascii=False, default=str), flush=True)
for i in range(5):
    p = subprocess.run(["/usr/bin/python3", str(R / "poller.py"), "--once", "--judge", "jev", "--state", str(ROOT / "poller-state.json")],
                       env=env, capture_output=True, text=True, timeout=900)
    print(f"POLL{i} rc={p.returncode} " + (p.stdout[-800:] + p.stderr[-400:]).replace("\n", " | "), flush=True)
    time.sleep(3)
print("ABSORB " + json.dumps(q("select fact_index, decision::text, decided_by, rule_id, action, fragment_ref from knowledge.absorption where created_at > now() - interval '1 hour'"), ensure_ascii=False, default=str), flush=True)
print("LINES " + json.dumps(q("select l.key, l.old_value, l.new_value, l.kind, l.source, e.state::text from knowledge.ledger_line l join knowledge.ledger_entry e on e.entry_id=l.entry_id order by l.line_id"), ensure_ascii=False, default=str), flush=True)
print("KEYS " + json.dumps(q("select key from knowledge.fact_key order by created_at"), ensure_ascii=False, default=str), flush=True)
sys.path.insert(0, str(R)); os.environ["LH_KNOWLEDGE_CONFIG"] = str(cp)
import knowledge_cli
print("REVIEW " + json.dumps([{k: i.get(k) for k in ("fact", "why_waiting")} for i in knowledge_cli.review_cmd(dsn, {"action": "list"})["items"]], ensure_ascii=False), flush=True)
print("LEDGER2 " + json.dumps(q("select state::text, count(*) from knowledge.ledger_entry where created_at > now() - interval '1 hour' group by 1"), default=str), flush=True)
print("FRAGS " + json.dumps(q("select alias, revision, active, text from knowledge.fragment where text ~ '(300|1000)자' order by alias"), ensure_ascii=False, default=str), flush=True)
print("UNITS2 " + json.dumps(q("select work_unit_id::text, status::text from knowledge.work_unit where created_at > now() - interval '1 hour'"), default=str), flush=True)
