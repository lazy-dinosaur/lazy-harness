"""conflict-01 D2: robust ledger protocol at record time. The parent writes each record as protocol lines itself
(target key from a key registry, old->new, kind, source; one line = one key); a lint rejects malformed lines once
(retry with the reason); application is purely mechanical per key. Same 30 cases, 2 reps."""
import json, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H)); sys.path.insert(0, str(H.parent))
import run as base, dedup
KEYS = {"도메인설명/길이제한": "F16 도메인 설명 길이는 생성·수정 모두 300자",
        "도메인설명/초과처리": "F9 describe 는 설명이 300자를 넘으면 오류로 거부", "도메인설명/공백처리": "F9 …앞뒤 공백을 제거한다",
        "검색결과/페이지크기": "F30 한 페이지에 30개", "예약목록/정렬": "F40 날짜 오름차순"}
FRAG_OF = {"도메인설명/초과처리": "F9", "도메인설명/공백처리": "F9", "도메인설명/길이제한": "F16", "검색결과/페이지크기": "F30", "예약목록/정렬": "F40"}
RULES = ("원장 규약(탄탄한 버전):\n"
         "1. 기록 한 줄 = 대상 하나의 변경·관찰 하나. 한 문장에 대상이 둘이면 줄을 나눈다(예: '설명 1000자, 이름 50자' → 두 줄).\n"
         "2. key = '대상/속성'. 아래 키 목록에 같은 대상·속성이 있으면 그 키를 그대로 쓴다. 없으면 같은 형식으로 새 키를 만든다"
         "(대상이 다르면 새 키: 도메인이름/길이제한, 모바일검색결과/페이지크기, 관리자설명/길이제한 처럼; 같은 대상의 다른 속성도 새 키).\n"
         "3. new = 그 속성의 값(숫자는 아라비아 숫자·단위 포함, 예: '1000자', '1000바이트', '내림차순'). 값을 모르면 쓰지 않는다. old = 바뀌기 전 값(모르면 빈 문자열).\n"
         "4. kind: change(사용자가 바꾸기로 한 것·작업이 바꾼 것·사용자가 정정·취소한 것) | observation(코드·문서에서 본 현재 상태). "
         "임시·테스트 값이면 temporary: true.\n5. source: user | code | doc | worker.\n")


def lint(lines):
    errs = []
    if not isinstance(lines, list) or not lines:
        return ["lines must be a nonempty list"]
    for i, x in enumerate(lines):
        if not isinstance(x, dict) or not re.fullmatch(r"[^/\s]+/[^/\s]+", str(x.get("key", ""))):
            errs.append(f"{i}: key must be '대상/속성'")
        elif not str(x.get("new", "")).strip():
            errs.append(f"{i}: new value required")
        elif x.get("kind") not in ("change", "observation"):
            errs.append(f"{i}: kind must be change|observation")
        elif re.search(r"[,，]|그리고| 및 ", str(x["new"])):
            errs.append(f"{i}: one value per line (split into lines)")
    return errs


def write(c, which):
    keys = "\n".join(f"- {k}: {v}" for k, v in KEYS.items())
    p = ("너는 이 작업을 하는 작업 AI 다. 도구를 쓰지 말고 JSON 만 답해라.\n\n작업 대화(요약):\n" + base.ctx(c) + "\n\n" + RULES +
         "\n키 목록(정본):\n" + keys + f"\n\n지금 원장에 이 기록을 남긴다: {base.rec_line(c[which])}\n"
         '형식: {"lines":[{"key":..,"old":..,"new":..,"kind":..,"source":..,"temporary":false}]}')
    cost = secs = 0.0
    for attempt in (1, 2):
        text, c1, s1 = base.pi_call(p); cost += c1; secs += s1
        m = re.search(r"\{.*\}", text, re.S)
        try:
            lines = json.loads(m.group(0))["lines"]
        except Exception:
            lines = None
        errs = lint(lines) if lines is not None else ["not JSON"]
        if not errs:
            return lines, cost, secs, attempt
        p += "\n\n[원장 검사 거절] " + "; ".join(errs) + " — 고쳐서 다시 써라."
    return None, cost, secs, 3


def apply(E, N):
    if E is None or N is None:
        return "?"
    norm = lambda s: dedup.normalize(str(s or "")).replace(",", "")
    E = [x for x in E if not x.get("temporary")] or E
    ek, nk = {x["key"]: x for x in E}, {x["key"]: x for x in N}
    common = set(ek) & set(nk)
    if not common:
        same = {FRAG_OF.get(k) for k in ek} & {FRAG_OF.get(k) for k in nk} - {None}
        return "combine" if same else "separate"
    out = []
    for k in common:
        e, n = ek[k], nk[k]
        if norm(e["new"]) == norm(n["new"]):
            out.append("merge")
        elif n["kind"] == "change" or (e["kind"] == "change" and n["kind"] == "change"):
            out.append("replace" if not (e["kind"] == "change" and n["kind"] == "observation") else "conflict")
        else:
            out.append("conflict")
    if set(ek) - common:
        return "separate"  # the earlier record carries something the new one does not
    if "conflict" in out:
        return "conflict"
    return "replace" if "replace" in out else "merge"


def main():
    cases = base.load()
    temp = {c["id"] for c in cases if "테스트" in c["context"] or "임시" in c["context"]}
    jobs = [(c, rep) for rep in (1, 2) for c in cases]
    res, cost, secs, retries = {c["id"]: {"gold": c["gold"]} for c in cases}, 0.0, [], 0
    with ThreadPoolExecutor(6) as pool:
        outs = list(pool.map(lambda j: (write(j[0], "earlier"), write(j[0], "new")), jobs))
    for (c, rep), (e, n) in zip(jobs, outs):
        cost += e[1] + n[1]; secs.append(e[2] + n[2]); retries += (e[3] > 1) + (n[3] > 1)
        res[c["id"]][f"E{rep}"] = apply(e[0], n[0]); res[c["id"]][f"lines{rep}"] = {"earlier": e[0], "new": n[0]}
    LOSE, KEEP = base_sets()
    n = ok = lose = keep = 0
    for r in res.values():
        for col in ("E1", "E2"):
            n += 1; ok += r[col] == r["gold"]; lose += (r["gold"], r[col]) in LOSE; keep += (r["gold"], r[col]) in KEEP
    flips = sum(r["E1"] != r["E2"] for r in res.values())
    summ = {"acc": round(ok / n, 3), "loses_knowledge": lose, "leaves_contradiction_or_dup": keep, "flips": flips,
            "lint_retries": retries, "cost": round(cost, 3), "secs_median_pair": round(sorted(secs)[len(secs) // 2], 1)}
    (H / "result_d2.json").write_text(json.dumps({"summary": summ, "cases": res}, ensure_ascii=False, indent=1))
    print("SUMMARY " + json.dumps(summ, ensure_ascii=False))
    for k, r in res.items():
        print(k, r["gold"], "E", r["E1"], r["E2"])


def base_sets():
    LOSE = {("separate", "merge"), ("separate", "replace"), ("combine", "merge"), ("combine", "replace"), ("conflict", "replace"), ("conflict", "merge")}
    KEEP = {("merge", "separate"), ("replace", "separate"), ("merge", "combine"), ("replace", "combine")}
    return LOSE, KEEP


if __name__ == "__main__":
    main()
