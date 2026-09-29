"""audit-01/persist: second check only for USER sentences the union flagged: 'does this remain knowledge after this request?'.
Measures request-set false alarms and write-01 misses at thresholds (keep if score >= t)."""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval as ev
import config
import capture_audit as ca

PQ = ("items[{i}] 는 사용자가 한 말이다. conversation 흐름상 이 말이 이번 요청이 끝난 뒤에도 남아야 할 제품·작업 지식인가? "
      "true: 값·대상·범위·금지·방침을 정하는 말(예: '1000자로 늘려줘', '앞으로 환자 이름은 로그에 남기지 마'), "
      "그대로 수행된 작업이 무엇을 만드는지·어느 대상인지 정하는 요청, 제시된 선택지 중 하나를 고르는 확정(예: 'a로 가자'). "
      "false: 인사, 정보를 묻는 질문, 되묻기로 끝난 값 없는 요청, 이번 답변·작업 방식만 정하는 지시(예: '한국어로 답해줘', "
      "'다른 파일은 건드리지 마', '코드는 바꾸지 말고 알려줘'), 작업 절차만 시키는 요청(예: '테스트 돌려봐', 'PR 올려줘').")
TS = (0.5, 0.3, 0.2)
judge = ca.make_judge(config.require("jev_api_key", "jev_base_url", "jev_model"))


def roles_units(turn):
    if turn["kind"] == "code":
        return [("code", u) for u in ev.units_of(turn)]
    txt = re.sub(r"\*\*(사용자 요청|사용자|조수):\*\*", lambda m: "\n@@" + ("A" if m.group(1) == "조수" else "U") + "@@", turn["text"])
    out, role = [], "user"
    for s in re.split(r"(?<=[.!?。])\s+|\n+", txt):
        m = re.match(r"@@([UA])@@", s)
        if m:
            role = "user" if m.group(1) == "U" else "assistant"; s = s[m.end():]
        if len(s.strip()) > 3:
            out.append((role, s.strip()))
    assert [t for _, t in out] == ev.units_of(turn), "unit order drift"
    return out


def scored(conv, rows, fl):
    idx = [i for i, ((role, _), f) in enumerate(zip(rows, fl)) if f and role == "user"]
    sc = {}
    if idx:
        ans = judge({"conversation": conv}, [rows[i][1] for i in idx], PQ)
        sc = {i: ca._noul(a) for i, a in zip(idx, ans)}
    return sc


def final(fl, sc, t):
    return [f and (i not in sc or sc[i] >= t) for i, f in enumerate(fl)]


# request set
def case(c):
    conv = "\n".join(f"{r}: {t}" for r, t, _ in c)
    rows = [(r, t) for r, t, _ in c]
    fl = ev.flags(judge, conv, [t for _, t in rows], ev.CUR)
    return c, fl, scored(conv, rows, fl)
with ThreadPoolExecutor(8) as pool:
    cases = list(pool.map(case, ev.CASES))
out = {}
for t in TS:
    s = {"fp_user": 0, "n_user_no": 0, "miss_record": 0, "n_record": 0, "wrong": []}
    for c, fl, sc in cases:
        for (role, text, lab), f in zip(c, final(fl, sc, t)):
            if lab == "no" and role == "user":
                s["n_user_no"] += 1; s["fp_user"] += f
                if f: s["wrong"].append("FP " + text)
            elif lab == "record":
                s["n_record"] += 1; s["miss_record"] += (not f)
                if not f: s["wrong"].append("MISS " + text)
    out[f"req@{t}"] = s
base = sum(f for c, fl, sc in cases for (role, _, lab), f in zip(c, fl) if lab == "no" and role == "user")
print("REQ base_fp", base, json.dumps(out, ensure_ascii=False), flush=True)

# write-01
def run(rid):
    _, turns = ev.turns_of(rid)
    rows = [x for t in turns for x in roles_units(t)]
    d = ev.parse(ev.repair_json((ev.R / "write-01" / "qcmp-raw" / f"{rid}-gold.txt").read_text())[0]) or {}
    lab = {x.get("id"): x.get("label") for x in d.get("labels", []) if isinstance(x, dict)}
    gold = [lab.get(f"u{i}") for i in range(len(rows))]
    conv = (ev.ISO / f"{rid}.md").read_text()[-8000:]
    fl = ev.flags(judge, conv, [t for _, t in rows], ev.CUR)
    return rows, gold, fl, scored(conv, rows, fl)
with ThreadPoolExecutor(12) as pool:
    res = list(pool.map(run, sorted(p.stem for p in ev.ISO.glob("R*.md"))))
w = {}
for t in [None, *TS]:
    fn = fp = 0; lost = []
    for rows, gold, fl, sc in res:
        fin = fl if t is None else final(fl, sc, t)
        for (role, text), g, f, f0 in zip(rows, gold, fin, fl):
            if g == "record": fn += (not f)
            elif g == "no": fp += f
            if t == 0.5 and g == "record" and f0 and not f: lost.append(text[:120])
    w["base" if t is None else f"@{t}"] = {"fn": fn, "fp": fp}
    if t == 0.5: w["lost@0.5"] = lost
users = sum(1 for rows, *_ in res for r, _ in rows if r == "user")
print("WRITE01 user_units", users, json.dumps(w, ensure_ascii=False), flush=True)
(Path(__file__).resolve().parent / "persist.json").write_text(json.dumps({"req": out, "write01": w}, ensure_ascii=False, indent=1))
