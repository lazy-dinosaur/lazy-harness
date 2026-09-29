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


def to_continue(verdicts, rules):
    """Only confident 'violated' continues the turn; 'unsure' is a notice."""
    return ([rules[i] for i, v in enumerate(verdicts) if v["label"] == "violated" and v["confident"]],
            [rules[i] for i, v in enumerate(verdicts) if v["label"] == "unsure"])
