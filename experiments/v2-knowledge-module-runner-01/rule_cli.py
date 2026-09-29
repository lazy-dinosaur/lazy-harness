"""rule_cli: rule tool commands for the harness extension (stdin JSON -> stdout JSON).
Commands: create {rule, quote, confirm_quote?} | update {id, changes, quote} | delete {id, quote} | list | history {id}.
Rules never go through knowledge digestion (schema-delta '규칙은 소화를 거치지 않고 규칙 도구로')."""
import json
import sys

import config
import rules_store as rs

COMMANDS = ("create", "update", "delete", "list", "history", "block", "inject")
LEVEL_KO = {"must": "반드시", "should": "권장"}
BLOCK_HEAD = ("[harness-rules] 이 프로젝트에서 지켜야 할 규칙 (하네스가 요청마다 붙임, 지식과 별개). "
              "h-* 는 하네스 기본 규칙, p-* 는 이 프로젝트 규칙. 답변 끝에 지켰는지 판정된다.")


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


def run(dsn, host, command, data, review_factory=_review):
    if command == "list":
        return {"rules": rs.list_rules(dsn, host)}
    if command == "history":
        return {"history": rs.history(dsn, data.get("id"))}
    if command == "block":
        return render_block(rs.list_rules(dsn, host))
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
