"""rule_cli: rule tool commands for the harness extension (stdin JSON -> stdout JSON).
Commands: create {rule, quote, confirm_quote?} | update {id, changes, quote} | delete {id, quote} | list | history {id}.
Rules never go through knowledge digestion (schema-delta '규칙은 소화를 거치지 않고 규칙 도구로')."""
import json
import sys

import config
import rules_store as rs

COMMANDS = ("create", "update", "delete", "list", "history", "block", "inject", "judge", "dispute")
LEVEL_KO = {"must": "반드시", "should": "권장"}
BLOCK_HEAD = ("[harness-rules] 이 프로젝트에서 지켜야 할 규칙 (하네스가 요청마다 붙임, 지식과 별개). "
              "h-* 는 하네스 기본 규칙, p-* 는 이 프로젝트 규칙. 답변 끝에 지켰는지 판정된다.")


SELECT_MIN = 0.83  # e5 cosine; inj-01 'select' mode only


def select_rules(rules, question):
    """Keep the project rules whose when/must are close to the request (local embedding, no Jev)."""
    import embed
    if not rules or not isinstance(question, str) or not question.strip():
        return rules
    q = embed.encode_query(question[:1000])
    vecs = embed.encode_passages([f"{r['when']} {r['must']}" for r in rules])
    return [r for r, v in zip(rules, vecs) if sum(a * b for a, b in zip(q, v)) >= SELECT_MIN]


def harness_guide():
    """v2 base guidance: harness rules are told here (not in the project rule block)."""
    import harness_rules
    lines = ["[harness-guide] lazy-harness 기본 규칙 (하네스 특성, 고정). 지침은 lazy-harness 만 따른다."]
    for r in harness_rules.SEMANTIC + harness_rules.CODE_ENFORCED:
        extra = f" (예외: {r['unless']})" if r.get("unless") else ""
        lines.append(f"- [{r['id']}] {r['when']} → {r['must']}{extra}")
    return "\n".join(lines)


def render_block(rules):
    """Rule block text (all active rules, short). Separate path from the knowledge window."""
    if not rules:
        return {"text": "", "ids": [], "tokens": 0}
    lines = [BLOCK_HEAD]
    for r in rules:
        line = f"- [{r['id']}] ({LEVEL_KO.get(r.get('level'), r.get('level'))}) {r['when']} → {r['must']}"
        extra = [f"예외: {r['unless']}" for _ in [0] if r.get("unless")] + [f"기준: 지식 '{r['ref']}'" for _ in [0] if r.get("ref")]
        lines.append(line + (f" ({' / '.join(extra)})" if extra else ""))
    text = "\n".join(lines)
    return {"text": text, "ids": [r["id"] for r in rules], "tokens": max(1, len(text) // 2)}


def _review(dsn, host):
    import rule_check
    import rule_review
    cfg = config.require("jev_api_key", "jev_base_url", "jev_model")
    return rule_review.make_review(rule_review.make_ask(cfg), rule_check.make_ask_two(cfg),
                                   lambda: rule_review.recent_evidence(dsn, host))


def _judges():
    import rule_check
    cfg = config.require("jev_api_key", "jev_base_url", "jev_model")
    return rule_check.make_ask_two(cfg), rule_check.make_ask_items(cfg)


def ref_fetch(dsn, host):
    """fetch(ref, diff, k): active fragments of knowledge domain `ref`, ranked by local embedding similarity to the diff."""
    import embed
    import store_pg
    def fetch(ref, diff, k):
        with store_pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("select count(*) from knowledge.fragment where host_id=%s and active and domain=%s", (host, ref))
            if cur.fetchone()[0] <= k:
                cur.execute("select alias, text from knowledge.fragment where host_id=%s and active and domain=%s order by seq", (host, ref))
                return [{"alias": a, "text": t} for a, t in cur.fetchall()]
            q = store_pg._vector(embed.encode_query(diff[:1500]))
            cur.execute("""select f.alias, f.text from knowledge.fragment f
                           join knowledge.fragment_embedding e on e.fragment_id=f.id and e.revision=f.revision
                             and e.model_id=%s and e.embed_variant='ctx-v1'
                           where f.host_id=%s and f.active and f.domain=%s
                           order by e.embedding <=> %s::extensions.vector limit %s""", (embed.MODEL_ID, host, ref, q, k))
            return [{"alias": a, "text": t} for a, t in cur.fetchall()]
    return fetch


def evidence_text(ev):
    parts = [f"사용자: {ev.get('user', '')[:1500]}"]
    if ev.get("files"):
        parts.append("바뀐 파일: " + ", ".join(ev["files"][:30]))
    if ev.get("commands"):
        parts.append("실행한 명령: " + " / ".join(c[:200] for c in ev["commands"][:15]))
    if ev.get("answer"):
        parts.append(f"어시스턴트 최종: {ev['answer'][:1500]}")
    return "\n".join(parts)


def judge(dsn, host, data, ask2, ask_items, fetch=None):
    """Post-turn rule judgment (step 4): two-step over all active rules, ref items against the diff,
    delivery marks from the injection record, receipts saved; returns the grouped alert for confident violations."""
    import rule_check
    import harness_rules
    rules = harness_rules.rules() + [dict(r, origin="project") for r in rs.list_rules(dsn, host)]
    ev = data.get("evidence") or {}
    text = evidence_text(ev)
    verdicts, usage = rule_check.check_with_refs(text, ev.get("diff") or "", rules, ask2, ask_items, fetch or ref_fetch(dsn, host))
    turn = data.get("turn_ref") or "unknown"
    rule_check.mark_delivery(verdicts, rules, rs.injected(dsn, host, turn))
    ids = rs.save_receipts(dsn, host, turn, rules, verdicts, {**ev, "diff": (ev.get("diff") or "")[:4000]})
    cont, notice = rule_check.to_continue(verdicts, rules)
    alert = rule_check.alert(verdicts, rules, text.splitlines()[0][:120])
    receipts = {r["id"]: rid for r, rid in zip(rules, ids)}
    return {"ok": True, "rules": len(rules), "alert": alert, "continue": [r["id"] for r in cont],
            "unsure": [r["id"] for r in notice], "receipts": {k: receipts[k] for k in [r["id"] for r in cont]},
            "usage": usage}


def run(dsn, host, command, data, review_factory=_review, judges=None):
    if command == "list":
        return {"rules": rs.list_rules(dsn, host)}
    if command == "history":
        return {"history": rs.history(dsn, data.get("id"))}
    if command == "judge":
        return judge(dsn, host, data, *(judges or _judges()))
    if command == "dispute":
        return rs.dispute(dsn, data.get("receipt_id"), data.get("reason"))
    if command == "block":
        rules = rs.list_rules(dsn, host)
        if data.get("select"):
            rules = select_rules(rules, data.get("question"))
        out = render_block(rules)
        out["guide"] = harness_guide()
        return out
    if command == "inject":
        turn = data.get("turn_ref")
        if not isinstance(turn, str) or not turn.strip():
            raise ValueError("turn_ref required")
        return {"ok": True, "injection_id": rs.record_injection(dsn, host, turn, data.get("rule_ids") or [],
                                                                 data.get("aliases") or [], int(data.get("tokens") or 0))}
    if command == "create":
        review = review_factory(dsn, host) if review_factory else None
        return rs.create(dsn, host, data.get("rule"), data.get("quote"), review=review, confirm_quote=data.get("confirm_quote"))
    if command == "update":
        return rs.update(dsn, host, data.get("id"), data.get("changes") or {}, data.get("quote"))
    if command == "delete":
        return rs.delete(dsn, host, data.get("id"), data.get("quote"))
    raise ValueError("expected " + "|".join(COMMANDS))


def main():
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
            raise ValueError("expected " + "|".join(COMMANDS))
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("input must be an object")
        dsn = config.require("db_url")["db_url"]
        host = data.get("host_id") or config.load()["default_host"]
        result = run(dsn, host, sys.argv[1], data)
    except ValueError as exc:
        result = {"ok": False, "error": "ValueError", "detail": str(exc)[:300]}
    except Exception as exc:
        result = {"ok": False, "error": type(exc).__name__, "detail": (str(exc).strip().splitlines() or [""])[0][:300]}
    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
