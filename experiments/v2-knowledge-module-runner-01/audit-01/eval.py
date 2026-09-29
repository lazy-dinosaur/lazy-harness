"""audit-01: false alarms of the answer-end record check on request/question-only turns (live-01 finding), plus the
write-01 q_compare regression (359 units, Sol gold) so a fix does not raise misses.
Usage: eval.py cur|new   (cur = capture_audit questions as shipped, new = request-aware wording below)
Union vote like capture_audit.audit: Q0 KQ, Q4 KQ_EX, Q2 kind != not_knowledge. CQ is not applied (no facts), as in q_compare."""
import json, shutil, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
HERE = Path(__file__).resolve().parent
R = HERE.parent
sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "write-01")); sys.path.insert(0, str(R / "fragmenter"))
import config
import capture_audit as ca

ISO = Path("/tmp/lh-write-iso"); ISO.mkdir(parents=True, exist_ok=True)
for p in (R / "write-01" / "situations").glob("R*.md"):
    shutil.copy(p, ISO / p.name)
from turn_step import turns_of, units_of  # noqa: E402
from check_fragments import parse, repair_json  # noqa: E402

REQ = (" 사용자의 작업 요청·질문(해 달라·알려 달라·바꿔 달라·봐 달라)은 그 자체로는 지식이 아니다. 요청이 값·범위·금지·방침을 확정해 "
       "이번 일이 끝난 뒤에도 제품이나 작업에 계속 적용될 때만 true 다(예: '설명은 1000자까지로 늘려줘', '앞으로 로그에 환자 이름을 남기지 마' 는 true / "
       "'제한을 늘려줘', '코드는 바꾸지 말고 알려줘', 'README 를 요약해줘', '테스트 돌려봐' 는 false).")
NEW = {"KQ": ca.KQ + REQ, "KQ_EX": ca.KQ_EX + REQ,
       "KIND_C": {**ca.KIND_C, "not_knowledge": ca.NOTK + "·값이나 범위를 정하지 않은 작업 요청·이번 일에만 해당하는 지시(예: '코드는 바꾸지 말고 알려줘')·정보를 묻는 질문"}}
CUR = {"KQ": ca.KQ, "KQ_EX": ca.KQ_EX, "KIND_C": ca.KIND_C}
# new2 (after new raised write-01 misses 15 -> 25): Sol gold counts a request as knowledge when the work was carried out
# (it says what was built / which target). Only unanswered asks, info questions, turn-only answer/working-style
# instructions and pure procedure chores are excluded.
REQ2 = (" 사용자 요청도 그대로 작업이 진행됐거나 대상·값·범위·방침을 구체적으로 정하면 true 다(무엇을 만들었는지·어느 대상인지의 지식). "
        "false 인 요청: 수행되지 않고 되묻기로 끝난 요청(예: 값 없이 '제한을 늘려줘' 뒤 '몇 자로?'), 정보를 묻는 질문, "
        "이번 턴의 답변·작업 방식만 정하는 지시(예: '코드는 바꾸지 말고 알려줘', '한국어로 답해줘', '다른 파일은 건드리지 마'), "
        "제품이 아니라 작업 절차만 시키는 요청(예: '테스트 돌려봐', 'PR 올려줘', 'README 를 요약해줘').")
NEW2 = {"KQ": ca.KQ + REQ2, "KQ_EX": ca.KQ_EX + REQ2,
        "KIND_C": {**ca.KIND_C, "not_knowledge": ca.NOTK + "·되묻기로 끝난 요청·이번 턴의 답변·작업 방식만 정하는 지시·작업 절차만 시키는 요청·정보를 묻는 질문"}}

# request/question-only turns; label per unit: record | no | skip (not scored)
CASES = [
 [("user", "지식 모듈에서 도메인 설명은 최대 몇 자로 만들어?", "no"), ("user", "코드는 바꾸지 말고 알려줘.", "no"),
  ("assistant", "최대 300자입니다.", "record"), ("assistant", "생성할 때는 300자로 잘라 저장하고, 수정할 때는 300자를 넘으면 오류로 거부합니다.", "record")],
 [("user", "도메인 설명 길이 제한을 늘려줘", "no"), ("assistant", "현재 생성·수정 모두 최대 300자입니다.", "record"), ("assistant", "몇 자로 늘릴까요?", "no")],
 [("user", "/home/lazydino/dev/lazy-harness/README.md 를 읽고 세 줄로 요약해줘", "no"), ("assistant", "해당 경로는 현재 프로젝트 밖이라 직접 읽을 수 없습니다.", "skip"),
  ("assistant", "README 내용을 붙여 넣어 주세요.", "no")],
 [("user", "로그인 버튼 색 좀 바꿔줘", "no"), ("assistant", "어떤 색으로 바꿀까요?", "no")],
 [("user", "테스트 한번 돌려봐", "no"), ("assistant", "테스트를 돌렸고 모두 통과했습니다.", "no")],
 [("user", "이 함수 뭐하는 거야?", "no"), ("assistant", "`formatName` 은 이름 앞뒤 공백을 없애고 성과 이름을 합친다.", "record")],
 [("user", "주문 금액 계산 로직 어디 있어?", "no"), ("assistant", "`src/order.js` 의 `calcTotal` 이 주문 금액을 계산한다.", "record")],
 [("assistant", "현재 도메인 설명은 최대 300자입니다. 몇 자로 늘릴까요?", "skip"), ("user", "그럼 1000자로 늘려줘", "record"),
  ("assistant", "도메인 설명 제한을 300자에서 1000자로 늘렸습니다.", "record")],
 [("user", "앞으로 로그인 버튼은 디자인 토큰 색만 써", "record"), ("assistant", "알겠습니다.", "no")],
 [("assistant", "A 는 임베딩을 e5-large 로 전환하고, B 는 로컬 모델을 유지합니다. 어느 쪽으로 할까요?", "no"), ("user", "a로 가자", "record")],
 [("user", "그거 다시 설명해줘", "no"), ("assistant", "기록 누락 검사는 답변이 끝날 때 이번 턴 문장 중 기록 안 된 지식을 찾는다.", "record")],
 [("user", "잠깐, 왜 이렇게 느려?", "no"), ("assistant", "검색어를 하나씩 원격으로 보내서 느렸습니다.", "skip")],
 [("user", "PR 올려줘", "no"), ("assistant", "PR 을 올렸습니다.", "no")],
 [("user", "날짜 형식 확인해줘", "no"), ("assistant", "날짜는 `YYYY-MM-DD` 형식으로 저장된다.", "record")],
 [("user", "환자 이름은 절대 로그에 남기면 안 돼", "record"), ("assistant", "로그에서 환자 이름을 지웠습니다.", "skip")],
 [("user", "빌드가 왜 깨졌는지 봐줘", "no"), ("user", "고칠 때 다른 파일은 건드리지 마", "no"),
  ("assistant", "`tsconfig` 의 경로 설정이 빠져 빌드가 깨졌습니다.", "skip")],
 [("user", "검색 결과 몇 개까지 보여줘?", "no"), ("assistant", "검색 결과는 한 페이지에 30개까지 보여 준다.", "record")],
 [("user", "이거 좀 더 빠르게 해줄 수 있어?", "no"), ("assistant", "어느 부분이 느린지 알려 주시겠어요?", "no")],
 [("user", "우선 a 해볼까??", "skip"), ("user", "무슨 문제가 있는지 잘 설명해줘", "no"), ("assistant", "세션을 닫을 때 오류가 납니다.", "skip")],
 [("user", "이 파일 구조 알려줘", "no"), ("user", "한국어로 답해줘", "no"), ("assistant", "파일은 세 부분으로 나뉘어 있습니다.", "skip")],
]


def flags(judge, conv, texts, q):
    q0 = judge({"conversation": conv}, texts, q["KQ"])
    q4 = judge({"conversation": conv}, texts, q["KQ_EX"])
    q2 = judge({"conversation": conv}, texts, ca.KIND_Q, q["KIND_C"])
    return [any([ca._noul(a) >= .5, ca._noul(b) >= .5, ca._not_knowledge(c) < .5]) for a, b, c in zip(q0, q4, q2)]


def main(ver):
    q = {"new": NEW, "new2": NEW2}.get(ver, CUR)
    judge = ca.make_judge(config.require("jev_api_key", "jev_base_url", "jev_model"))
    # 1) request/question set
    def case(c):
        conv = "\n".join(f"{r}: {t}" for r, t, _ in c)
        return list(zip(c, flags(judge, conv, [t for _, t, _ in c], q)))
    with ThreadPoolExecutor(8) as pool:
        res = [x for c in pool.map(case, CASES) for x in c]
    s = {"fp_user_request": 0, "n_user_request": 0, "fp_other_no": 0, "n_other_no": 0, "miss_record": 0, "n_record": 0, "wrong": []}
    for (role, text, lab), f in res:
        if lab == "no":
            key = "user_request" if role == "user" else "other_no"
            s["n_" + key] += 1; s["fp_" + key] += f
            if f: s["wrong"].append("FP " + text)
        elif lab == "record":
            s["n_record"] += 1; s["miss_record"] += (not f)
            if not f: s["wrong"].append("MISS " + text)
    print("REQSET " + json.dumps(s, ensure_ascii=False), flush=True)
    # 2) write-01 regression (Sol gold)
    rids = sorted(p.stem for p in ISO.glob("R*.md"))
    def run(rid):
        _, turns = turns_of(rid)
        us = [u for t in turns for u in units_of(t)]
        d = parse(repair_json((R / "write-01" / "qcmp-raw" / f"{rid}-gold.txt").read_text())[0]) or {}
        lab = {x.get("id"): x.get("label") for x in d.get("labels", []) if isinstance(x, dict)}
        gold = [lab.get(f"u{i}") for i in range(len(us))]
        conv = (ISO / f"{rid}.md").read_text()[-8000:]
        return gold, flags(judge, conv, us, q)
    fn = fp = nr = nn = 0
    with ThreadPoolExecutor(12) as pool:
        for gold, fl in pool.map(run, rids):
            for g, f in zip(gold, fl):
                if g == "record": nr += 1; fn += (not f)
                elif g == "no": nn += 1; fp += f
    print("WRITE01 " + json.dumps({"record": nr, "no": nn, "fn": fn, "fp": fp}), flush=True)
    (HERE / f"{ver}.json").write_text(json.dumps({"reqset": s, "write01": {"record": nr, "no": nn, "fn": fn, "fp": fp}}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
