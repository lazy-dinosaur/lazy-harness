"""Completion and one-shot digestion on the conftest-owned local PostgreSQL container."""
from concurrent.futures import ThreadPoolExecutor

import pytest

import digest_driver
import store_pg as pg
from test_store_pg import fixture, host, judgement


def staged(dsn, host_id, *, unit=None, text="new"):
    body = judgement(host_id, text=text)
    if unit:
        body["work_unit_id"] = unit
    entry = pg.register(dsn, body)
    response = fixture(text=text)
    assert pg.batch(dsn, 1, {entry["entry_id"]: [response]})[0]["state"] == "provisional"
    return body, entry, response


def count(dsn, host_id):
    return len([r for r in pg.rows(dsn, "fragment") if r["host_id"] == host_id])


def test_completion_and_idempotent_digest(dsn, host):
    body, entry, response = staged(dsn, host)
    unit = body["work_unit_id"]
    judged = []
    def judge(packet):
        judged.append(packet)
        return {"answers": response["answers"], "jev_model_requested": "fixture-model"}

    assert digest_driver.run_digestion(dsn, unit, judge) == {"status": "not_completed"}
    assert count(dsn, host) == 0 and not judged
    assert pg.register_completion_sources(dsn, unit, ["merge", "confirm"]) == [
        {"source": "merge", "received": False}, {"source": "confirm", "received": False}]
    assert pg.signal_completion(dsn, unit, "unknown")["status"] == "unknown_source"
    assert pg.signal_completion(dsn, unit, "merge", {"ref": "local"}) == {"status": "waiting", "pending": ["confirm"]}
    assert pg.signal_completion(dsn, unit, "merge") == {"status": "waiting", "pending": ["confirm"]}
    assert digest_driver.run_digestion(dsn, unit, judge)["status"] == "not_completed"
    assert pg.signal_completion(dsn, unit, "confirm") == {"status": "completed", "pending": []}
    assert pg.signal_completion(dsn, unit, "confirm")["status"] == "already_completed"
    assert digest_driver.run_digestion(dsn, unit, judge)["status"] == "absorbed"
    assert count(dsn, host) == 1 and len(judged) == 1
    assert digest_driver.run_digestion(dsn, unit, judge) == {"status": "noop"}
    assert count(dsn, host) == 1
    events = [e for e in pg.rows(dsn, "work_unit_event") if str(e["work_unit_id"]) == unit]
    assert [e["source"] for e in events].count("merge") == 1
    assert len([e for e in events if e["to"] == "completed"]) == 1
    sources = next(u for u in pg.rows(dsn, "work_unit") if str(u["work_unit_id"]) == unit)["completion_sources"]
    assert sources[0]["evidence"] == {"ref": "local"} and sources[0]["received_at"]


@pytest.mark.parametrize("length", [200, 201, 300, 301])
def test_generated_domain_description_limit(dsn, host, monkeypatch, length):
    import domain_router

    text = "가" * length
    body, _, response = staged(dsn, host, text=text)
    seen = []
    route = domain_router.route_unit

    def spy(domains, proposed, facts, choose, confirm=None):
        seen.append(domains)  # Retain the routing cache to inspect its generated description.
        return route(domains, proposed, facts, choose, confirm=confirm)

    monkeypatch.setattr(domain_router, "route_unit", spy)
    pg.complete(dsn, body["work_unit_id"])
    assert digest_driver.run_digestion(
        dsn, body["work_unit_id"], lambda packet: {"answers": response["answers"]}
    )["status"] == "absorbed"
    expected = {"domain": text[:300]}
    assert len(seen) == 1
    assert seen[0]["domain"]["description"] == text[:300]
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        domains = domain_router.load(cur, host)
    assert {name: row["description"] for name, row in domains.items()} == expected


def test_concurrent_digest_only_one_fragment(dsn, host):
    body, _, response = staged(dsn, host)
    pg.complete(dsn, body["work_unit_id"])
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: digest_driver.run_digestion(
            dsn, body["work_unit_id"], lambda packet: {"answers": response["answers"]}), range(2)))
    assert sorted(result["status"] for result in outcomes) == ["absorbed", "noop"]
    assert count(dsn, host) == 1
    assert len([a for a in pg.rows(dsn, "absorption") if str(a["work_unit_id"]) == body["work_unit_id"]]) == 1


def test_same_pass_add_identical_to_update_is_retained(dsn, host, monkeypatch):
    """An add recorded mid-work that equals an update applied in the same digestion becomes evidence, not a fragment."""
    import store_pg as pg2
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,group_id,source)
                    values (%s,'dup-1','dup',1,'설명은 300자로 자른다','fact','dup:g','{"evidence_refs": []}'::jsonb) returning id::text""", (host,))
        target = cur.fetchone()[0]
    add = {"operation": "add", "fact": "설명은 1000자로 자른다."}  # qualifiers count since P0-4: same sentence, ending only
    upd = {"operation": "update", "fact": "설명은 1000자로 자른다", "target_ref": target}
    other = {"operation": "add", "fact": "설명은 수정 때 1000자를 넘으면 거부한다"}
    prepared = [({}, {"human_approved": False}, add, None, None, {"rule_id": "P", "action": "absorb"}),
                ({}, {"human_approved": False}, upd, None, None, {"rule_id": "P", "action": "absorb"}),
                ({}, {"human_approved": False}, other, None, None, {"rule_id": "P", "action": "absorb"})]
    import dedup
    batch = [f["fact"] for _, _, f, _, _, v in prepared if v["action"] == "absorb" and f.get("operation") == "update"]
    assert dedup.find_duplicate(add["fact"], batch) == 0
    assert dedup.find_duplicate(other["fact"], batch) is None
    assert pg2.BATCH_DUP_RULE == "digest_batch_duplicate"


def test_abandon_expires_without_absorption(dsn, host):
    body, provisional, _ = staged(dsn, host)
    proposed_body = judgement(host)
    proposed_body["work_unit_id"] = body["work_unit_id"]
    pg.register(dsn, proposed_body)
    reviewed_body = judgement(host)
    reviewed_body["work_unit_id"] = body["work_unit_id"]
    reviewed = pg.register(dsn, reviewed_body)
    # Remaining entries may be proposed; transition one explicitly to review_queue.
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.ledger_entry set state='review_queue' where entry_id=%s", (reviewed["entry_id"],))
    assert pg.abandon(dsn, body["work_unit_id"], "cancelled")["expired"] == 3
    assert {r["state"] for r in pg.rows(dsn, "ledger_entry") if str(r["work_unit_id"]) == body["work_unit_id"]} == {"expired"}
    assert digest_driver.run_digestion(dsn, body["work_unit_id"], lambda _: pytest.fail("judge called"))["status"] == "not_completed"
    assert pg.signal_completion(dsn, body["work_unit_id"], "merge")["status"] == "not_active"
    assert count(dsn, host) == 0


def test_isolation_and_fresh_target(dsn, host):
    first, _, response = staged(dsn, host, text="first")
    other, other_entry, _ = staged(dsn, host, text="other")
    pg.complete(dsn, first["work_unit_id"])
    assert digest_driver.run_digestion(dsn, first["work_unit_id"], lambda p: {"answers": response["answers"]})["status"] == "absorbed"
    assert count(dsn, host) == 1
    assert digest_driver.run_digestion(dsn, other["work_unit_id"], lambda _: pytest.fail("judge called"))["status"] == "not_completed"
    ref = next(r for r in pg.rows(dsn, "fragment") if r["host_id"] == host)
    body = judgement(host, "update", str(ref["id"]), "changed")
    entry = pg.register(dsn, body)
    response = fixture("update", "changed", "first", 1)
    assert pg.batch(dsn, 1, {entry["entry_id"]: [response]})[0]["state"] == "provisional"
    pg.complete(dsn, body["work_unit_id"])
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.fragment set revision=revision+1, text='new target' where id=%s", (ref["id"],))
    seen = []
    def judge(packet):
        seen.append(packet["state"]["target_excerpt"])
        return {"answers": response["answers"]}
    result = digest_driver.run_digestion(dsn, body["work_unit_id"], judge)
    assert seen == ["new target"] and result["status"] == "absorbed"
    assert next(r for r in pg.rows(dsn, "fragment") if r["id"] == ref["id"])["revision"] == 3
    assert count(dsn, host) == 1
    assert next(r for r in pg.rows(dsn, "ledger_entry") if str(r["entry_id"]) == other_entry["entry_id"])["state"] == "provisional"


def test_digestion_receipt_keeps_provider_cost(dsn, host):
    body, _, response = staged(dsn, host, text="cost kept")
    unit = body["work_unit_id"]
    pg.register_completion_sources(dsn, unit, ["merge"])
    pg.signal_completion(dsn, unit, "merge")
    judge = lambda packet: {"answers": response["answers"], "cost_usd": 0.002, "input_tokens": 7, "output_tokens": 3}
    assert digest_driver.run_digestion(dsn, unit, judge)["status"] == "absorbed"
    rows = [r for r in pg.rows(dsn, "check_receipt") if r["stage"] == "digestion" and r["input_tokens"] == 7]
    assert rows and float(rows[0]["cost_usd"]) == 0.002
