"""Rule creation review (schema-delta '규칙 JSON 스키마와 생성 확인', verified in rules-02):
Jev flags conflict / duplicate / weakens a harness base rule against the current rules, then a dry run over
recent judged turns flags a rule that is unjudgeable (mostly 'unsure' where applicable) or too broad (applies
to every turn). Flags stop the write until the user confirms."""
import json
from urllib.request import Request, urlopen

import harness_rules
import rule_check
import store_pg

CREATE_Q = {
    "conflict": "candidate 규칙을 따르면 existing 규칙 중 하나를 어기게 되는가(같은 상황에서 서로 반대되는 행동을 요구하는가)?",
    "duplicate": "candidate 규칙은 existing 규칙 중 하나와 사실상 같은 조건에서 같은 행동을 요구하는가?",
    "weakens_base": "candidate 규칙을 따르면 base(하네스 기본 규칙) 중 하나를 어기거나 약하게 만드는가?",
}
LABELS = {"conflict": "기존 규칙과 충돌", "duplicate": "기존 규칙과 중복", "weakens_base": "하네스 기본 규칙을 약하게 만듦",
          "unjudgeable": "조건·행동이 흐려서 판정하기 어려움", "too_broad": "너무 넓어서 모든 턴에 해당됨"}


def make_ask(cfg, http=urlopen):
    def ask(state):
        qs = {k: {"type": "noul", "instructions": q, "criteria": {"true": "예", "false": "아니오"}} for k, q in CREATE_Q.items()}
        body = {"model": cfg["jev_model"], "state": state, "questions": qs}
        req = Request(cfg["jev_base_url"].rstrip("/") + "/v1/systemone", data=json.dumps(body, ensure_ascii=False).encode(),
                      headers={"Authorization": "Bearer " + cfg["jev_api_key"], "Content-Type": "application/json"}, method="POST")
        with http(req, timeout=90) as resp:
            data = json.load(resp)
        return {k: float(data["answers"][k].get("noul", 0)) for k in qs}
    return ask


def recent_evidence(dsn, host, limit=7):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select distinct on (turn_ref) turn_ref, evidence, at from rules.judgement_receipt
                       where host_id=%s order by turn_ref, at desc""", (host,))
        rows = sorted(cur.fetchall(), key=lambda r: r[2], reverse=True)[:limit]
    return [r[1] if isinstance(r[1], str) else json.dumps(r[1], ensure_ascii=False) for r in rows]


def make_review(ask, ask2, evidence_source, min_turns=3):
    """ask(state) -> {conflict, duplicate, weakens_base: noul}; ask2 = rule_check two-step asker;
    evidence_source() -> recent turn evidences. Dry run needs at least min_turns judged turns."""
    def review(rule, existing):
        base = harness_rules.for_review()
        proj = [r for r in existing if r["id"].startswith("p-")]
        view = lambda r: {k: r[k] for k in ("id", "when", "must", "unless") if r.get(k)}
        scores = ask({"candidate": {k: rule[k] for k in ("when", "must", "unless") if rule.get(k)},
                      "existing": [view(r) for r in proj], "base": [view(r) for r in base]})
        flags = [LABELS[k] + f" ({v:.2f})" for k, v in scores.items() if v >= 0.5 and (k != "weakens_base" or base)]
        turns = evidence_source()
        if len(turns) >= min_turns:
            probe = {"id": "candidate", **{k: rule[k] for k in ("when", "must", "unless", "why") if rule.get(k)}}
            labels = [rule_check.check_two_step(ev, [probe], ask2)[0][0]["label"] for ev in turns]
            applies = sum(l != "not_applicable" for l in labels)
            if applies and labels.count("unsure") / applies >= 0.5:
                flags.append(LABELS["unjudgeable"] + f" (해당 {applies}턴 중 모름 {labels.count('unsure')})")
            if applies == len(labels):
                flags.append(LABELS["too_broad"] + f" ({applies}/{len(labels)}턴)")
        return flags
    return review
