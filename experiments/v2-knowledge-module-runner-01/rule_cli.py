"""rule_cli: rule tool commands for the harness extension (stdin JSON -> stdout JSON).
Commands: create {rule, quote, confirm_quote?} | update {id, changes, quote} | delete {id, quote} | list | history {id}.
Rules never go through knowledge digestion (schema-delta '규칙은 소화를 거치지 않고 규칙 도구로')."""
import json
import sys

import config
import rules_store as rs

COMMANDS = ("create", "update", "delete", "list", "history")


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
