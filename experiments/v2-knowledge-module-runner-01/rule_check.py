"""Rule check engine (harness rule layer): Jev judges, per rule, whether this turn's evidence
shows the rule was not applicable / followed / violated / unsure. `batch` controls how many rules go into
one Jev request (1 = one HTTP request per rule, sent in parallel). Strength principle: Jev verdicts only
inform or continue, never block (schema-delta '하네스 규칙 강도 원칙')."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen

LABELS = ("not_applicable", "followed", "violated", "unsure")
CRITERIA = {"not_applicable": "이번 턴의 행동이 이 규칙의 조건에 해당하지 않는다",
            "followed": "조건에 해당하고 evidence 에 규칙을 지킨 흔적이 있다",
            "violated": "조건에 해당하는데 evidence 에 규칙을 어긴 흔적이 있다(해야 할 것을 안 했거나 금지된 것을 했다)",
            "unsure": "evidence 만으로는 판단할 수 없다"}
QUESTION = ("rules[{i}] 는 이 프로젝트의 규칙이다. evidence(이번 턴에 실제로 있었던 대화·바뀐 파일·실행한 명령)를 보고 "
            "이번 턴이 이 규칙과 어떤 관계인지 고른다. 다른 규칙은 고려하지 않는다.")
MARGIN = 0.15


def make_ask(cfg, http=urlopen, timeout=90):
    """ask(state, n) -> (answers list, usage dict) for n choice questions over state['rules']."""
    def ask(state, n):
        qs = {f"m{j}": {"type": "choice", "instructions": QUESTION.format(i=j), "criteria": CRITERIA} for j in range(n)}
        body = {"model": cfg["jev_model"], "state": state, "questions": qs}
        last = None
        for attempt in (1, 2, 3):
            try:
                req = Request(cfg["jev_base_url"].rstrip("/") + "/v1/systemone", data=json.dumps(body, ensure_ascii=False).encode(),
                              headers={"Authorization": "Bearer " + cfg["jev_api_key"], "Content-Type": "application/json"}, method="POST")
                with http(req, timeout=timeout) as resp:
                    data = json.load(resp)
                if set(data.get("answers", {})) != set(qs):
                    raise ValueError("answer keys mismatch")
                usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
                return [data["answers"][f"m{j}"] for j in range(n)], usage
            except (OSError, ValueError, KeyError, TypeError) as exc:
                last = exc
                time.sleep(attempt)
        raise RuntimeError(f"Jev rule check failed: {last}")
    return ask


def verdict(answer):
    p = answer.get("probabilities") or {}
    ranked = sorted(p, key=p.get, reverse=True)
    choice = answer.get("choice") or (ranked[0] if ranked else "unsure")
    margin = p.get(ranked[0], 0) - p.get(ranked[1], 0) if len(ranked) > 1 else 1.0
    confident = choice in LABELS and margin >= MARGIN
    return {"label": choice if choice in LABELS else "unsure", "confident": confident,
            "p_violated": float(p.get("violated", 1.0 if choice == "violated" else 0.0))}


def check(evidence, rules, ask, batch=1, concurrency=8):
    """rules: list of rule sentences. Returns (per-rule verdicts, stats)."""
    if batch < 1:
        raise ValueError("batch must be >= 1")
    groups = [list(range(k, min(k + batch, len(rules)))) for k in range(0, len(rules), batch)]
    def run(idx):
        state = {"evidence": evidence, "rules": [{"i": j, "text": rules[r]} for j, r in enumerate(idx)]}
        return idx, ask(state, len(idx))
    start = time.time()
    with ThreadPoolExecutor(max_workers=max(1, min(concurrency, len(groups)))) as pool:
        results = list(pool.map(run, groups))
    out, usage = [None] * len(rules), {"requests": len(groups), "input_tokens": 0, "output_tokens": 0, "cost": 0.0}
    for idx, (answers, u) in results:
        for r, a in zip(idx, answers):
            out[r] = verdict(a)
        usage["input_tokens"] += u.get("input_tokens") or 0
        usage["output_tokens"] += u.get("output_tokens") or 0
        usage["cost"] += u.get("cost") or 0.0
    usage["seconds"] = round(time.time() - start, 2)
    return out, usage


COND = ("met", "not_met", "unsure")
DONE = ("done", "not_done", "unsure")
COND_C = {"met": "이번 턴이 when 조건에 해당하고 unless(예외)에는 해당하지 않는다",
          "not_met": "when 조건에 해당하지 않거나 unless(예외)에 해당한다",
          "unsure": "evidence 만으로는 판단할 수 없다"}
DONE_C = {"done": "evidence 에 must 를 이행한(금지라면 하지 않은) 흔적이 있다",
          "not_done": "evidence 에 must 를 이행하지 않은(금지라면 한) 흔적이 있다",
          "unsure": "evidence 만으로는 판단할 수 없다"}
COND_Q = "rules[{i}] 의 when(조건)과 unless(예외)만 본다. evidence 의 이번 턴은 이 규칙의 조건에 해당하는가? 다른 규칙은 고려하지 않는다."
DONE_Q = "rules[{i}] 의 must(해야 할 것)만 본다. evidence 에서 이번 턴은 must 를 이행했는가? 다른 규칙은 고려하지 않는다."


def make_ask_two(cfg, http=urlopen, timeout=90):
    """Two questions per rule (condition, action) in one request over state['rules'] (schema: when/must/unless/why)."""
    def ask(state, n):
        qs = {}
        for j in range(n):
            qs[f"c{j}"] = {"type": "choice", "instructions": COND_Q.format(i=j), "criteria": COND_C}
            qs[f"d{j}"] = {"type": "choice", "instructions": DONE_Q.format(i=j), "criteria": DONE_C}
        body = {"model": cfg["jev_model"], "state": state, "questions": qs}
        last = None
        for attempt in (1, 2, 3):
            try:
                req = Request(cfg["jev_base_url"].rstrip("/") + "/v1/systemone", data=json.dumps(body, ensure_ascii=False).encode(),
                              headers={"Authorization": "Bearer " + cfg["jev_api_key"], "Content-Type": "application/json"}, method="POST")
                with http(req, timeout=timeout) as resp:
                    data = json.load(resp)
                if set(data.get("answers", {})) != set(qs):
                    raise ValueError("answer keys mismatch")
                usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
                out = []
                for j in range(n):
                    out += [data["answers"][f"c{j}"], data["answers"][f"d{j}"]]
                return out, usage
            except (OSError, ValueError, KeyError, TypeError) as exc:
                last = exc
                time.sleep(attempt)
        raise RuntimeError(f"Jev rule check failed: {last}")
    return ask


def _pick(answer, labels):
    p = answer.get("probabilities") or {}
    ranked = sorted(p, key=p.get, reverse=True)
    choice = answer.get("choice") or (ranked[0] if ranked else "unsure")
    margin = p.get(ranked[0], 0) - p.get(ranked[1], 0) if len(ranked) > 1 else 1.0
    return (choice if choice in labels else "unsure"), round(float(p.get(choice, 0)), 2), margin


def check_two_step(evidence, rules, ask2, batch=20, concurrency=8):
    """rules: [{id, when, must, unless?, why?}]. Label = condition first, then action."""
    groups = [list(range(k, min(k + batch, len(rules)))) for k in range(0, len(rules), batch)]
    def run(idx):
        state = {"evidence": evidence, "rules": [{"i": j, **{k: rules[r][k] for k in ("when", "must", "unless", "why") if rules[r].get(k)}}
                                                  for j, r in enumerate(idx)]}
        return idx, ask2(state, len(idx))
    start = time.time()
    with ThreadPoolExecutor(max_workers=max(1, min(concurrency, len(groups)))) as pool:
        results = list(pool.map(run, groups))
    out, usage = [None] * len(rules), {"requests": len(groups), "input_tokens": 0, "output_tokens": 0, "cost": 0.0}
    for idx, (answers, u) in results:
        for k, r in enumerate(idx):
            c, cp, cm = _pick(answers[2 * k], COND)
            d, dp, dm = _pick(answers[2 * k + 1], DONE)
            if c == "not_met":
                label = "not_applicable"
            elif c == "met" and d == "done":
                label = "followed"
            elif c == "met" and d == "not_done":
                label = "violated"
            else:
                label = "unsure"
            out[r] = {"label": label, "cond": (c, cp), "done": (d, dp), "confident": min(cm, dm) >= MARGIN}
        usage["input_tokens"] += u.get("input_tokens") or 0
        usage["output_tokens"] += u.get("output_tokens") or 0
        usage["cost"] += u.get("cost") or 0.0
    usage["seconds"] = round(time.time() - start, 2)
    return out, usage


COND_KO = {"met": "예", "not_met": "아니오", "unsure": "모름"}
DONE_KO = {"done": "예", "not_done": "아니오", "unsure": "모름"}


def alert(verdicts, rules, evidence_summary):
    """Continuation text for confident violations: which rule, which step, what Jev looked at."""
    lines = []
    for v, r in zip(verdicts, rules):
        if v["label"] != "violated" or not v["confident"]:
            continue
        head = f"- {r['id']}: {r['when']} → {r['must']}"
        extra = " / ".join(x for x in (f"예외: {r['unless']}" if r.get("unless") else "", f"이유: {r['why']}" if r.get("why") else "") if x)
        lines += [head + (f" ({extra})" if extra else ""),
                  f"  · 조건 충족: {COND_KO[v['cond'][0]]} ({v['cond'][1]})  · 해야 할 것 수행: {DONE_KO[v['done'][0]]} ({v['done'][1]})"]
    if not lines:
        return ""
    return ("[harness-rule-check] 규칙 위반 가능성\n" + "\n".join(lines) + f"\n  · Jev 가 본 근거: {evidence_summary}\n"
            "→ 사실이면 고치고, 사실이 아니면 이유를 한 줄 적고 넘어가.")


ITEM_C = {"violated": "diff 의 변경이 이 항목을 어긴다", "followed": "diff 의 변경이 이 항목과 관련 있고 지켰다",
          "not_related": "diff 의 변경은 이 항목과 관련이 없다"}
ITEM_Q = ("items[{i}] 는 이 프로젝트 컨벤션의 한 항목이다. diff(이번 턴에 바뀐 코드, + 는 추가 - 는 삭제)만 보고, "
          "추가·변경된 코드가 이 항목을 어겼는지 고른다. 다른 항목은 고려하지 않는다.")
DIFF_CAP = 6000


def cap_diff(diff, cap=DIFF_CAP):
    """Keep changed lines first (+/-), then context, up to cap characters."""
    if not diff:
        return ""
    lines = diff.splitlines()
    changed = [l for l in lines if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    head = [l for l in lines if l.startswith(("+++", "---", "diff ", "@@"))]
    out, size = [], 0
    for l in head + changed:
        if size + len(l) + 1 > cap:
            out.append(f"… (diff {len(diff) - size}자 생략)")
            break
        out.append(l); size += len(l) + 1
    return "\n".join(out)


def make_ask_items(cfg, http=urlopen, timeout=90):
    def ask(state, n):
        qs = {f"m{j}": {"type": "choice", "instructions": ITEM_Q.format(i=j), "criteria": ITEM_C} for j in range(n)}
        body = {"model": cfg["jev_model"], "state": state, "questions": qs}
        last = None
        for attempt in (1, 2, 3):
            try:
                req = Request(cfg["jev_base_url"].rstrip("/") + "/v1/systemone", data=json.dumps(body, ensure_ascii=False).encode(),
                              headers={"Authorization": "Bearer " + cfg["jev_api_key"], "Content-Type": "application/json"}, method="POST")
                with http(req, timeout=timeout) as resp:
                    data = json.load(resp)
                if set(data.get("answers", {})) != set(qs):
                    raise ValueError("answer keys mismatch")
                u = data.get("usage") if isinstance(data.get("usage"), dict) else {}
                return [data["answers"][f"m{j}"] for j in range(n)], u
            except (OSError, ValueError, KeyError, TypeError) as exc:
                last = exc
                time.sleep(attempt)
        raise RuntimeError(f"Jev item check failed: {last}")
    return ask


def check_with_refs(evidence, diff, rules, ask2, ask_items, fetch, max_items=10, diff_cap=DIFF_CAP):
    """Stage 1: two-step over all rules. Stage 2: for rules whose condition is met and that carry a ref, fetch
    up to max_items knowledge items related to the diff (fetch(ref, diff, k) -> [{alias,text}]) and judge them
    in one Jev request. Any confident 'violated' item makes the rule violated. Skipped when there is no diff."""
    verdicts, usage = check_two_step(evidence, rules, ask2)
    usage["item_requests"] = 0
    diff = cap_diff(diff, diff_cap)
    if not diff:
        return verdicts, usage
    for v, r in zip(verdicts, rules):
        if not r.get("ref") or v["cond"][0] != "met":
            continue
        items = fetch(r["ref"], diff, max_items)[:max_items]
        if not items:
            continue
        answers, u = ask_items({"diff": diff, "rule": {k: r[k] for k in ("when", "must") if r.get(k)},
                                "items": [{"i": j, "text": it["text"]} for j, it in enumerate(items)]}, len(items))
        usage["item_requests"] += 1
        usage["input_tokens"] += u.get("input_tokens") or 0
        usage["cost"] += u.get("cost") or 0.0
        bad = []
        for it, a in zip(items, answers):
            lab, prob, margin = _pick(a, tuple(ITEM_C))
            if lab == "violated" and margin >= MARGIN:
                bad.append({**it, "p": prob})
        v["items_checked"] = [it["alias"] for it in items]
        v["items"] = bad
        v["diff"] = diff
        if bad:
            v.update(label="violated", done=("not_done", max(b["p"] for b in bad)), confident=True)
        elif v["label"] == "violated":
            pass  # stage 1 found a violation outside the referenced items; keep it
        else:
            v.update(label="followed", done=("done", v["done"][1]))
    return verdicts, usage


def mark_delivery(verdicts, rules, injected):
    """injected = {'rules': [rule ids in this turn's rule block], 'knowledge': [aliases in the knowledge window]}.
    Code-known, no Jev: tells whether a violation happened despite delivery (agent) or without it (harness)."""
    rs, ks = set(injected.get("rules") or []), set(injected.get("knowledge") or [])
    for v, r in zip(verdicts, rules):
        v["rule_delivered"] = None if r.get("origin") == "harness" else r["id"] in rs
        v["knowledge_delivered"] = [i["alias"] for i in v.get("items", []) if i["alias"] in ks]
    return verdicts


def alert(verdicts, rules, evidence_summary):
    """Continuation text for confident violations, grouped per rule: rule, both steps, delivery, violated items,
    added lines; then what Jev looked at."""
    lines = []
    for v, r in zip(verdicts, rules):
        if v["label"] != "violated" or not v["confident"]:
            continue
        head = f"- {'[하네스 기본 규칙] ' if r.get('origin') == 'harness' else ''}{r['id']}: {r['when']} → {r['must']}"
        extra = " / ".join(x for x in (f"예외: {r['unless']}" if r.get("unless") else "", f"이유: {r['why']}" if r.get("why") else "") if x)
        lines += [head + (f" ({extra})" if extra else ""),
                  f"  · 조건 충족: {COND_KO[v['cond'][0]]} ({v['cond'][1]})  · 해야 할 것 수행: {DONE_KO[v['done'][0]]} ({v['done'][1]})"]
        if v.get("rule_delivered") is not None:
            lines.append("  · " + ("이번 턴 규칙 블록에 있었음" if v["rule_delivered"] else "이번 턴에 전달되지 않음(하네스 확인 필요)"))
        for it in v.get("items", []):
            sent = " (지식 창으로 전달됨)" if it["alias"] in v.get("knowledge_delivered", []) else ""
            lines.append(f"  · 어긴 항목: [{it['alias']}] {it['text']} ({it['p']}){sent}")
        if v.get("items") and v.get("diff"):
            shown = [l for l in v["diff"].splitlines() if l.startswith("+") and not l.startswith("+++")][:4]
            lines += [f"    {l}" for l in shown]
    if not lines:
        return ""
    return ("[harness-rule-check] 규칙 위반 가능성\n" + "\n".join(lines) + f"\n· Jev 가 본 근거: {evidence_summary}\n"
            "→ 사실이면 고치고, 사실이 아니면 rule_dispute 로 이유를 한 줄 남기고 넘어가.")


def to_continue(verdicts, rules):
    """Only confident 'violated' continues the turn; 'unsure' is a notice."""
    return ([rules[i] for i, v in enumerate(verdicts) if v["label"] == "violated" and v["confident"]],
            [rules[i] for i, v in enumerate(verdicts) if v["label"] == "unsure"])
