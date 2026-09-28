"""Single-session worker entry point. Review and absorption remain the poller's responsibility."""
import json
import re
import subprocess
import sys
from uuid import UUID, uuid4

import config
import runner
import store_pg
import worktime_driver


def required(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value


def unit_id(value):
    try:
        return str(UUID(required(value, "work_unit_id")))
    except ValueError:
        raise ValueError("invalid work_unit_id") from None


def baseline_ref(cwd):
    if not isinstance(cwd, str) or not cwd:
        return None
    try:
        result = subprocess.run(["git", "-C", cwd, "rev-parse", "--verify", "HEAD"],
                                capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40,64}", result.stdout.strip()) else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def snapshot(dsn, uid):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select status::text,host_id,partition_key,baseline_history_id,baseline_code_ref,baseline_at,
                   completion_sources from knowledge.work_unit where work_unit_id=%s""", (uid,))
        unit = store_pg._row(cur)
        if unit is None:
            raise ValueError("unknown work_unit_id")
        cur.execute("select state::text,count(*) from knowledge.ledger_entry where work_unit_id=%s group by state", (uid,))
        states = dict(cur.fetchall())
        cur.execute("""select distinct f.alias from knowledge.fragment f join knowledge.absorption a on a.fragment_ref=f.id
                   join knowledge.ledger_entry e on e.entry_id=a.entry_id where e.work_unit_id=%s order by f.alias""", (uid,))
        aliases = [row[0] for row in cur.fetchall()]
    baseline = {k: unit[k] for k in ("baseline_history_id", "baseline_code_ref", "baseline_at")}
    return {"work_unit_id": uid, "status": unit["status"], "host_id": unit["host_id"],
            "partition_key": unit["partition_key"], "baseline": baseline,
            "entry_states": {k: states.get(k, 0) for k in ("proposed", "provisional", "review_queue", "rejected_input")},
            "all_entry_states": states, "absorbed_aliases": aliases,
            "changed_since_baseline": len(store_pg.changed_since_baseline(dsn, uid))}


def lint_update_fact(dsn, host, raw):
    """The record path's per-fact checks for one update fact, without registering. Returns error list."""
    fact = dict(raw)
    fact["evidence_quote"] = " / ".join(r["quote"] for r in fact.get("evidence_refs", []) if isinstance(r, dict) and isinstance(r.get("quote"), str))
    fact, _ = runner.normalize_fact(fact)
    errors = list(runner.lint_fact(fact)["errors"])
    try:
        packet = worktime_driver.build_packet(fact, worktime_driver._target_excerpt(dsn, host, fact))
        errors += runner.lint(packet)["errors"]
    except (KeyError, TypeError, ValueError) as exc:
        errors.append({"code": "E_PACKET", "detail": type(exc).__name__})
    return errors


def record(dsn, data):
    host = data.get("host_id") or config.load()["default_host"]
    required(host, "host_id (set default_host in knowledge.json)")
    partition = required(data.get("partition_key"), "partition_key")
    facts = data.get("facts")
    if not isinstance(facts, list) or not facts:
        return {"ok": False, "errors": [{"code": "E_FACTS", "where": "facts", "detail": "nonempty facts array required"}]}
    errors, warnings, repairs = [], [], []
    normalized = []
    for index, raw in enumerate(facts):
        if not isinstance(raw, dict):
            errors.append({"code": "E_SCHEMA", "where": f"facts.{index}", "detail": "fact must be an object"})
            continue
        fact = dict(raw)
        refs = fact.get("evidence_refs")
        if not isinstance(refs, list):
            refs = []
            errors.append({"code": "E_SCHEMA", "where": f"facts.{index}.evidence_refs", "detail": "evidence_refs must be an array"})
        fact["evidence_refs"] = refs
        if not fact.get("evidence_quote"):
            fact["evidence_quote"] = " / ".join(r["quote"] for r in refs if isinstance(r, dict) and isinstance(r.get("quote"), str))
        if not isinstance(fact.get("fact"), str) or not isinstance(fact.get("reason"), str) or not fact["reason"].strip():
            errors.append({"code": "E_SCHEMA", "where": f"facts.{index}", "detail": "fact and nonempty reason are required"})
            continue
        fact, fixes = runner.normalize_fact(fact)  # form-only repairs (subject, keywords); meaning untouched
        if fixes:
            repairs.append({"fact_index": index, "repairs": fixes})
        checked = runner.lint_fact(fact)
        for error in checked["errors"]:
            errors.append({**error, "where": f"facts.{index}.{error['where']}"})
        for warning in checked.get("warnings", []):
            warnings.append({**warning, "where": f"facts.{index}.{warning['where']}"})
        operation = fact.get("operation", "add")
        if operation not in ("add", "update", "deprecate"):
            errors.append({"code": "E_OPERATION", "where": f"facts.{index}.operation", "detail": "operation must be add|update|deprecate"})
            continue
        if operation in ("update", "deprecate") and not fact.get("target_ref"):
            errors.append({"code": "E_TARGET", "where": f"facts.{index}.target_ref", "detail": f"{operation} needs target_ref"})
            continue
        if operation == "deprecate" and fact.get("evidence_source") != "user_confirmed":
            # G2: removing knowledge needs the user's verbatim confirmation (lint_fact then checks it is a non-question).
            errors.append({"code": "E_DEPRECATE_CONFIRM", "where": f"facts.{index}.evidence_source",
                           "detail": "deprecate needs evidence_source user_confirmed with the user's verbatim confirmation"})
            continue
        try:
            excerpt = (worktime_driver._target_excerpt(dsn, host, fact) if operation in ("update", "deprecate")
                       else "이 host 의 정본에 관련 조각이 없다.")
            packet = worktime_driver.build_packet(fact, excerpt)
            for error in runner.lint(packet)["errors"]:
                errors.append({**error, "where": f"facts.{index}.{error['where']}"})
        except (KeyError, TypeError, ValueError) as exc:
            errors.append({"code": "E_PACKET", "where": f"facts.{index}", "detail": type(exc).__name__})
        normalized.append(fact)
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings, "repairs": repairs}
    uid = unit_id(data["work_unit_id"]) if data.get("work_unit_id") else str(uuid4())
    body = {"work_unit_id": uid, "host_id": host, "partition_key": partition,
            "judgement_id": str(uuid4()), "version": 1, "baseline_code_ref": baseline_ref(data.get("cwd")),
            "facts": normalized}
    entry = store_pg.register(dsn, body)
    return {"work_unit_id": uid, "entry_id": entry["entry_id"], "state": "proposed",
            "baseline": snapshot(dsn, uid)["baseline"], "warnings": warnings, "repairs": repairs}


def complete(dsn, data):
    uid = unit_id(data.get("work_unit_id"))
    quote = required(data.get("user_quote"), "user_quote")
    if runner.QUESTION_TAIL.search(quote.strip()):
        return {"ok": False, "errors": [{"code": "E_CONFIRM", "where": "user_quote",
                  "detail": "Ask for explicit user confirmation first; a question is not confirmation"}]}
    locator = data.get("locator")
    if locator is not None and not isinstance(locator, str):
        raise ValueError("locator must be a string")
    state = snapshot(dsn, uid)
    if state["status"] == "active":
        with store_pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("select completion_sources from knowledge.work_unit where work_unit_id=%s", (uid,))
            sources = cur.fetchone()[0]
        if not sources:
            store_pg.register_completion_sources(dsn, uid, ["user_confirm"])
    result = store_pg.signal_completion(dsn, uid, "user_confirm", evidence={"quote": quote, "locator": locator})
    state = snapshot(dsn, uid)
    result["entry_states"] = state["entry_states"]
    if state["entry_states"]["provisional"] == 0 and state["entry_states"]["proposed"]:
        result["notice"] = "작업 중 검수 대기 중 — 소화자가 곧 처리"
    return result


def tools(dsn, command, data):
    """Worker tools (worker_tools.py): search | fix_plan | fix_submit. Jev config is required for all three."""
    import worker_tools
    cfg = config.require("jev_api_key", "jev_base_url", "jev_model")
    ask = worker_tools.make_ask(cfg)
    host = data.get("host_id") or config.load()["default_host"]
    required(host, "host_id (set default_host in knowledge.json)")
    if command == "search":
        return worker_tools.search(dsn, host, data.get("question"), data.get("queries"), ask, layer=data.get("layer"),
                                   change=data.get("change"))
    if command == "fix_plan":
        return worker_tools.fix_plan(dsn, host, data.get("change"), data.get("queries"), ask)
    return worker_tools.fix_submit(dsn, data.get("plan_id"), data.get("answers"), ask, lambda d: record(dsn, d),
                                   partition_key=required(data.get("partition_key"), "partition_key"),
                                   work_unit_id=data.get("work_unit_id"), cwd=data.get("cwd"),
                                   precheck=lambda fact: lint_update_fact(dsn, host, fact))


def audit(dsn, data):
    """Capture audit (capture_audit.py): transcript vs facts already recorded in this work unit -> missing list."""
    import capture_audit
    cfg = config.require("jev_api_key", "jev_base_url", "jev_model")
    recorded = list(data.get("recorded_facts") or [])
    if data.get("work_unit_id"):
        uid = unit_id(data["work_unit_id"])
        with store_pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("select judgement_body from knowledge.ledger_entry where work_unit_id=%s", (uid,))
            for (body,) in cur.fetchall():
                recorded += [f.get("fact") for f in (body or {}).get("facts", []) if isinstance(f, dict)]
    return capture_audit.audit(data.get("transcript"), recorded, capture_audit.make_judge(cfg))


def domain_cmd(dsn, data):
    """knowledge_cli domain: list | show {domain} | merge {src,dst} | retire {domain} | describe {domain,description}."""
    import domain_router
    host = data.get("host_id") or config.load()["default_host"]
    required(host, "host_id (set default_host in knowledge.json)")
    action = data.get("action", "list")
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        if action == "describe":
            domain_router.describe(cur, host, data.get("domain"), data.get("description"))
        elif action == "merge":
            domain_router.merge(cur, host, required(data.get("src"), "src"), required(data.get("dst"), "dst"))
        elif action == "retire":
            domain_router.retire(cur, host, required(data.get("domain"), "domain"))
        elif action == "show":
            return {"domain": required(data.get("domain"), "domain"),
                    "fragments": domain_router.fragments(cur, host, data["domain"])}
        elif action != "list":
            raise ValueError("action must be list|show|merge|retire|describe")
        return {"domains": domain_router.list_domains(cur, host)}


COMMANDS = ("record", "complete", "status", "search", "more", "brief", "fix_plan", "fix_submit", "audit", "domain")


def main():
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
            raise ValueError("expected " + "|".join(COMMANDS))
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("input must be an object")
        dsn = config.require("db_url")["db_url"]
        command = sys.argv[1]
        if command in ("search", "fix_plan", "fix_submit"):
            result = tools(dsn, command, data)
        elif command == "brief":
            import brief, worker_tools
            cfg = config.require("jev_api_key", "jev_base_url", "jev_model")
            host = data.get("host_id") or config.load()["default_host"]
            result = brief.brief(dsn, required(host, "host_id"), data.get("question"), data.get("queries"),
                                 worker_tools.make_ask(cfg), change=data.get("change"))
        elif command == "more":
            import worker_tools
            result = worker_tools.more(dsn, required(data.get("search_id"), "search_id"), domain=data.get("domain"), group=data.get("group"))
        elif command == "audit":
            result = audit(dsn, data)
        elif command == "domain":
            result = domain_cmd(dsn, data)
        else:
            result = record(dsn, data) if command == "record" else (complete(dsn, data) if command == "complete" else snapshot(dsn, unit_id(data.get("work_unit_id"))))
    except ValueError as exc:
        result = {"ok": False, "error": "ValueError", "detail": str(exc)[:200]}
    except Exception as exc:
        result = {"ok": False, "error": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
