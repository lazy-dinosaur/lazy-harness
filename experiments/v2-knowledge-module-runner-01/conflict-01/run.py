"""conflict-01: who resolves overlapping ledger records? P parent (worker model, sees conversation), C code actor,
J actor+Jev (no conversation), D one-change-per-line protocol (parent writes key|old->new|kind, code applies
later-wins per key, observations that disagree -> conflict). Gold: cases.tsv (user-reviewed table)."""
import csv, difflib, json, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent))
import config, capture_audit as ca, dedup
PI = "/home/lazydino/.npm-global/bin/pi"
F = {"F9": "describe 는 설명이 300자를 넘으면 오류로 거부하고, 앞뒤 공백을 제거한다", "F16": "도메인 설명 길이는 생성·수정 모두 300자",
     "F30": "검색 결과는 한 페이지에 30개까지 보여 준다", "F40": "예약 목록은 날짜 오름차순으로 정렬한다"}
LABELS = ["merge", "separate", "replace", "combine", "conflict"]
DESC = {"merge": "같은 변경·같은 내용이라 하나로 합침", "separate": "다른 사실이라 따로 둠", "replace": "새 기록이 앞 기록을 대체",
        "combine": "같은 조각의 서로 다른 부분 수정이라 둘 다 반영", "conflict": "어느 쪽이 맞는지 모르니 사람 검수"}


def load():
    rows = list(csv.DictReader(open(H / "cases.tsv"), delimiter="\t"))
    for r in rows:
        for k in ("earlier", "new"):
            m = re.match(r"(add|update)(?:\((\w+)\))?(?: (F\d+))?:\s*(.*)", r[k])
            r[k] = {"op": m.group(1), "source": m.group(2) or "", "frag": m.group(3), "text": m.group(4)}
    return rows


def rec_line(x):
    return f"{x['op']}{'(' + x['source'] + ')' if x['source'] else ''}{' ' + x['frag'] + ' 수정' if x['frag'] else ''}: {x['text']}"


def nums(t):
    return set(re.findall(r"\d[\d,]*", t.replace(",", ""))) | set(re.findall(r"[A-Za-z_]{3,}", t))


def code_actor(c):
    e, n = c["earlier"], c["new"]
    if dedup.find_duplicate(e["text"], [n["text"]]) is not None:
        return "merge"
    if e["frag"] and e["frag"] == n["frag"]:
        o, a, b = F[e["frag"]].split(), e["text"].split(), n["text"].split()
        ca_ = {i for tag, i1, i2, _, _ in difflib.SequenceMatcher(None, o, a).get_opcodes() if tag != "equal" for i in range(i1, max(i2, i1 + 1))}
        cb = {i for tag, i1, i2, _, _ in difflib.SequenceMatcher(None, o, b).get_opcodes() if tag != "equal" for i in range(i1, max(i2, i1 + 1))}
        return "conflict" if ca_ & cb else "combine"
    return "merge" if nums(e["text"]) & nums(n["text"]) - {"300"} else "separate"


def pi_call(prompt):
    t = time.time()
    r = subprocess.run([PI, "-ne", "-nc", "-ns", "--no-session", "--mode", "json", "-p", prompt], capture_output=True, text=True, timeout=300, cwd="/tmp")
    text, cost = "", 0.0
    for line in r.stdout.splitlines():
        try: ev = json.loads(line)
        except ValueError: continue
        m = ev.get("message") or {}
        if ev.get("type") == "message_end" and m.get("role") == "assistant":
            cost += ((m.get("usage") or {}).get("cost") or {}).get("total") or 0
            text = "".join(x.get("text", "") for x in m.get("content") or [] if x.get("type") == "text") or text
    return text.strip(), cost, time.time() - t


def ctx(c):
    return c["context"].replace(" / ", "\n").replace(" → ", "\n")


def parent(c):
    frag = c["new"]["frag"] or c["earlier"]["frag"]
    p = ("너는 이 작업을 하는 작업 AI 다. 도구를 쓰지 말고 답만 해라.\n\n작업 대화(요약, U=사용자, A=너):\n" + ctx(c) +
         (f"\n\n정본 조각 {frag} 원문: {F[frag]}" if frag else "") +
         f"\n\n너는 이 작업에서 먼저 이렇게 기록했다:\n- {rec_line(c['earlier'])}\n방금 이렇게 기록했다:\n- {rec_line(c['new'])}\n\n"
         "[원장 알림] 두 기록이 겹칠 수 있다. 너의 의도에 맞는 처리 하나를 골라 첫 줄에 그 단어만 써라:\n" +
         "\n".join(f"- {k}: {v}" for k, v in DESC.items()))
    text, cost, secs = pi_call(p)
    low = text.lower()
    label = next((k for k in LABELS if low.startswith(k)), next((k for k in LABELS if k in low), "?"))
    return label, cost, secs


def protocol(c):
    keys = "\n".join(f"- {k}: {v}" for k, v in F.items())
    p = ("너는 이 작업을 하는 작업 AI 다. 도구를 쓰지 말고 JSON 만 답해라.\n\n작업 대화(요약):\n" + ctx(c) +
         f"\n\n원장 규약: 기록 한 줄 = 변경·관찰 하나. key 는 그 사실의 대상(무엇의 어떤 속성)이고, 이미 있는 대상이면 같은 key 를 재사용한다. "
         "kind 는 change(사용자가 바꾸기로 한 것·작업이 바꾼 것) 또는 observation(코드·문서에서 본 현재 상태). "
         "한 문장에 대상이 둘이면 줄을 나눈다.\n정본 조각(기존 대상):\n" + keys +
         f"\n\n아래 두 기록을 규약대로 다시 써라. 형식: {{\"earlier\":[{{\"key\":..,\"old\":..,\"new\":..,\"kind\":..}}], \"new\":[...]}}\n"
         f"earlier: {rec_line(c['earlier'])}\nnew: {rec_line(c['new'])}")
    text, cost, secs = pi_call(p)
    m = re.search(r"\{.*\}", text, re.S)
    try:
        d = json.loads(m.group(0))
    except Exception:
        return "?", cost, secs, None
    return d_apply(d), cost, secs, d


def d_apply(d):
    norm = lambda s: dedup.normalize(str(s or ""))
    E = {norm(x.get("key")): x for x in d.get("earlier", [])}
    N = {norm(x.get("key")): x for x in d.get("new", [])}
    common = set(E) & set(N)
    if not common:
        return "separate"
    out = []
    for k in common:
        e, n = E[k], N[k]
        if norm(e.get("new")) == norm(n.get("new")):
            out.append("merge")
        elif e.get("kind") == "observation" and n.get("kind") == "observation" or (e.get("kind") != n.get("kind")):
            out.append("conflict")
        else:
            out.append("replace")
    if set(E) - common and set(N) - common or (set(E) - common and "replace" in out):
        return "separate"  # leftover facts must stay
    if "conflict" in out:
        return "conflict"
    return "replace" if "replace" in out else "merge"


def jev_arm(judge, c):
    frag = c["new"]["frag"] or c["earlier"]["frag"]
    st = {"original_fragment": F.get(frag, ""), "earlier_record": rec_line(c["earlier"])}
    a = judge(st, [rec_line(c["new"])], "items[{i}] 는 원장에 새로 들어온 기록이다. earlier_record 와의 관계를 골라라.", DESC)[0]
    return a.get("choice", "?")


def main():
    only = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--only" else None
    cases = load()
    res = {c["id"]: {"gold": c["gold"], "kind": c["kind"]} for c in cases}
    for c in cases:
        res[c["id"]]["C"] = code_actor(c)
    if only == "code":
        ok = sum(r["C"] == r["gold"] for r in res.values()); print("code", ok, "/", len(cases)); return
    judge = ca.make_judge(config.require("jev_api_key", "jev_base_url", "jev_model"))
    cost = {"P": 0.0, "D": 0.0}; secs = {"P": [], "D": []}
    jobs = [(c, rep) for rep in (1, 2) for c in cases]
    with ThreadPoolExecutor(6) as pool:
        for (c, rep), (p, d) in zip(jobs, pool.map(lambda j: (parent(j[0]), protocol(j[0])), jobs)):
            r = res[c["id"]]
            r[f"P{rep}"] = p[0]; cost["P"] += p[1]; secs["P"].append(p[2])
            r[f"D{rep}"] = d[0]; cost["D"] += d[1]; secs["D"].append(d[2]); r[f"Dlines{rep}"] = d[3]
        for (c, rep), j in zip(jobs, pool.map(lambda j: jev_arm(judge, j[0]), jobs)):
            res[c["id"]][f"J{rep}"] = j
    LOSE = {("separate", "merge"), ("separate", "replace"), ("combine", "merge"), ("combine", "replace"), ("conflict", "replace"), ("conflict", "merge")}
    KEEP = {("merge", "separate"), ("replace", "separate"), ("merge", "combine"), ("replace", "combine")}
    summ = {}
    for arm, cols in (("C", ["C"]), ("P", ["P1", "P2"]), ("J", ["J1", "J2"]), ("D", ["D1", "D2"])):
        n = ok = lose = both = 0
        for r in res.values():
            for col in cols:
                n += 1; ok += r[col] == r["gold"]; lose += (r["gold"], r[col]) in LOSE; both += (r["gold"], r[col]) in KEEP
        flip = sum(r[cols[0]] != r[cols[-1]] for r in res.values()) if len(cols) > 1 else 0
        summ[arm] = {"acc": round(ok / n, 3), "loses_knowledge": lose, "leaves_contradiction_or_dup": both, "flips": flip}
    summ["cost"] = {k: round(v, 3) for k, v in cost.items()}
    summ["secs_median"] = {k: round(sorted(v)[len(v) // 2], 1) for k, v in secs.items() if v}
    (H / "result.json").write_text(json.dumps({"summary": summ, "cases": res}, ensure_ascii=False, indent=1))
    print("SUMMARY " + json.dumps(summ, ensure_ascii=False))
    for k, r in res.items():
        print(k, r["gold"], "C", r["C"], "P", r["P1"], r["P2"], "J", r["J1"], r["J2"], "D", r["D1"], r["D2"])


if __name__ == "__main__":
    main()
