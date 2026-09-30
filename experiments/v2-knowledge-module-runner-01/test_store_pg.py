"""Local-only integration tests; never read production connection settings."""
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

import policy
import runner
import store
import store_pg as pg

IMAGE = "public.ecr.aws/supabase/postgres:17.6.1.134"
NAME = "lh-kdb-test-08"
SQL = Path(__file__).parent / "migrations/0001_knowledge_init.sql"


def docker(*args, **kwargs):
    return subprocess.run(["docker", *args], text=True, capture_output=True, **kwargs)


@pytest.fixture
def host(dsn):
    host_id = f"test-{uuid4()}"
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("insert into knowledge.host(host_id,name,repo_locator) values (%s,%s,%s)",
                    (host_id, host_id, "local-test"))
    return host_id


def judgement(host, operation="add", target=None, text="new", kind="fact", source="user_confirmed"):
    fact = {"operation": operation, "fact": text, "kind": kind, "evidence_source": source, "subject": text,
            "evidence_quote": text, "keywords": [text], "reason": "synthetic correction",
            "evidence_refs": [{"type": "user_utterance", "locator": "test/local", "quote": text}]}
    if kind in ("decision", "constraint"):  # standard v1: who decided + what was decided
        fact["evidence_refs"].append({"type": "official_doc", "locator": "test/spec", "quote": text})
    if kind == "decision":
        fact["why"] = "synthetic reason"
    if target:
        fact["target_ref"] = target
    return {"judgement_id": str(uuid4()), "version": 1, "host_id": host, "partition_key": "domain",
            "work_unit_id": str(uuid4()), "facts": [fact]}


def fixture(operation="add", text="new", excerpt=None, revision=None):
    if operation == "add":
        answers = {"is_new": {"type": "noul", "noul": .96},
                   "durability": {"type": "choice", "choice": "durable_fact",
                                  "probabilities": {"durable_fact": .96, "none_or_uncertain": .04}},
                   "should_record": {"type": "noul", "noul": .95}}
        state = {"narrative": "synthetic", "candidate_fact": text, "evidence_quote": text,
                 "existing_records_excerpt": ""}
        template = ("record-need", "v0.2.2")
    else:
        from test_runner import FIXTURES
        answers = runner.load(FIXTURES / "c1-offline-responses.json")["U1" if operation == "update" else "D1"]
        state = {"narrative": "synthetic", "candidate_fact": text, "evidence_quote": text,
                 "target_excerpt": excerpt}
        template = ("intent", "v0.3.1")
    questions = {key: {"type": answer["type"], "instructions": "Select literal value",
                          "criteria": ({"true": None, "false": None} if answer["type"] == "noul" else
                                       {name: None for name in answer["probabilities"]})}
                 for key, answer in answers.items()}
    return {"packet": {"template_id": template[0], "template_version": template[1],
                       "state": state, "questions": questions}, "answers": answers,
            "target_revision_seen": revision}


def process(dsn, judgement_body, response):
    entry = pg.register(dsn, judgement_body)
    result = pg.batch(dsn, 1, {entry["entry_id"]: [response]})[0]
    pg.complete(dsn, judgement_body["work_unit_id"])
    receipts = [r for r in pg.rows(dsn, "check_receipt") if str(r["entry_id"]) == entry["entry_id"] and r["stage"] == "worktime"]
    assert len(receipts) == 1
    return entry, result, str(receipts[0]["receipt_id"])


@pytest.mark.parametrize("length", [200, 201, 300, 301])
def test_digest_domain_description_limit_and_preservation(dsn, host, length):
    import domain_router

    text = "가" * length
    body = judgement(host, text=text)
    response = fixture(text=text)
    _, _, receipt = process(dsn, body, response)
    assert pg.digest(dsn, body["work_unit_id"], True, {receipt: response})["status"] == "absorbed"
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        assert domain_router.load(cur, host)["domain"]["description"] == text[:300]
        domain_router.describe(cur, host, "domain", "나" * 300)

    body = judgement(host, text="later fact")
    response = fixture(text="later fact")
    _, _, receipt = process(dsn, body, response)
    assert pg.digest(dsn, body["work_unit_id"], True, {receipt: response})["status"] == "absorbed"
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        assert domain_router.load(cur, host)["domain"]["description"] == "나" * 300


def test_policy_is_fixed_harness_default(dsn, host):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        assert pg.policies(cur, host) == policy.DEFAULT_POLICY
        cur.execute("""insert into knowledge.acceptance_policy(host_id,version,ordinal,rule_id,when_json,then_action)
                       values (%s,2,1,'LOCAL','{}'::jsonb,'hold'),(%s,1,1,'OLD','{}'::jsonb,'reject')""", (host, host))
        assert pg.policies(cur, host) == policy.DEFAULT_POLICY  # per-host rows never override


def test_register_batch_complete_add_update_cas_and_queue(dsn, host):
    add = judgement(host)
    add_fixture = fixture()
    entry, batch_result, receipt = process(dsn, add, add_fixture)
    assert batch_result["state"] == "provisional"
    assert batch_result["facts"][0]["combined"] == runner.decide(add_fixture["packet"], add_fixture["answers"])["combined"]
    assert any(str(r["entry_id"]) == entry["entry_id"] and r["to"] == "proposed" for r in pg.rows(dsn, "ledger_entry_event"))
    assert any(str(r["work_unit_id"]) == add["work_unit_id"] and r["status"] == "completed" for r in pg.rows(dsn, "work_unit"))
    assert pg.digest(dsn, add["work_unit_id"], True, {receipt: add_fixture})["status"] == "absorbed"
    fragment = next(r for r in pg.rows(dsn, "fragment") if r["host_id"] == host)
    ref = str(fragment["id"])
    assert (fragment["confidence"], fragment["revision"], fragment["text"]) == ("confirmed", 1, "new")
    assert len([h for h in pg.rows(dsn, "fragment_history") if str(h["fragment_id"]) == ref and h["op"] == "create"]) == 1
    absorption = next(a for a in pg.rows(dsn, "absorption") if str(a["entry_id"]) == entry["entry_id"])
    assert (absorption["rule_id"], absorption["action"]) == ("P10", "absorb")
    with tempfile.TemporaryDirectory() as directory:
        file_entry = store.register(directory, add)
        file_result = store.batch(directory, 1, {file_entry["entry_id"]: [add_fixture]})[0]
        store.complete(directory, add["work_unit_id"])
        file_receipt = store.rows(directory, "check_receipt")[0]["receipt_id"]
        assert store.digest(directory, add["work_unit_id"], True, {file_receipt: add_fixture})["status"] == "absorbed"
        file_absorption = store.rows(directory, "absorption")[0]
        # the file store (legacy, not used by the pi tools) keeps policy P10; the DB path applies ledger commands
        assert (batch_result["facts"][0]["combined"], absorption["action"]) == (
            file_result["facts"][0]["combined"], file_absorption["action"])

    update = judgement(host, "update", ref, "changed")
    response = fixture("update", "changed", "new", 1)
    _, outcome, receipt = process(dsn, update, response)
    assert outcome["facts"][0]["combined"] == runner.decide(response["packet"], response["answers"], "update")["combined"]
    assert pg.digest(dsn, update["work_unit_id"], True, {receipt: response})["status"] == "absorbed"
    history = [h for h in pg.rows(dsn, "fragment_history") if str(h["fragment_id"]) == ref]
    assert sorted((h["revision"], h["op"]) for h in history) == [(1, "create"), (2, "update")]
    assert next(f for f in pg.rows(dsn, "fragment") if str(f["id"]) == ref)["text"] == "changed"

    stale = judgement(host, "update", ref, "later")
    response = fixture("update", "later", "changed", 2)
    _, _, receipt = process(dsn, stale, response)
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("update knowledge.fragment set revision=revision+1 where id=%s and revision=2", (ref,))
    before = next(f for f in pg.rows(dsn, "fragment") if str(f["id"]) == ref)
    assert pg.digest(dsn, stale["work_unit_id"], True, {receipt: response})["status"] == "needs_recheck"
    assert next(f for f in pg.rows(dsn, "fragment") if str(f["id"]) == ref) == before
    assert not any(str(a["work_unit_id"]) == stale["work_unit_id"] for a in pg.rows(dsn, "absorption"))

    decision = judgement(host, "add", text="new decision", kind="decision", source="ai_inference")
    decision_fixture = fixture(text="new decision")
    _, _, receipt = process(dsn, decision, decision_fixture)
    assert pg.digest(dsn, decision["work_unit_id"], True, {receipt: decision_fixture})["status"] == "processed"
    assert len([f for f in pg.rows(dsn, "fragment") if f["host_id"] == host]) == 1
    assert len([q for q in pg.rows(dsn, "confirmation_queue") if str(q["entry_id"]) ==
                next(a["entry_id"] for a in pg.rows(dsn, "absorption") if str(a["work_unit_id"]) == decision["work_unit_id"])]) == 1
    assert next(a for a in pg.rows(dsn, "absorption") if str(a["work_unit_id"]) == decision["work_unit_id"])["rule_id"] == "P09"


def test_deprecate_never_deletes(dsn, host):
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,source)
                       values (%s,'domain-1','domain',1,'old','fact','{"evidence_refs":[]}'::jsonb) returning id::text""", (host,))
        ref = cur.fetchone()[0]
    body = judgement(host, "deprecate", ref, "obsolete")
    response = fixture("deprecate", "obsolete", "old", 1)
    entry, outcome, receipt = process(dsn, body, response)
    assert outcome["facts"][0]["combined"] == "deprecate_record"
    assert pg.digest(dsn, body["work_unit_id"], True, {receipt: response})["status"] == "absorbed"
    fragment = next(f for f in pg.rows(dsn, "fragment") if str(f["id"]) == ref)
    assert fragment["revision"] == 2 and fragment["active"] is False
    assert any(h["op"] == "deprecate" and str(h["fragment_id"]) == ref for h in pg.rows(dsn, "fragment_history"))
