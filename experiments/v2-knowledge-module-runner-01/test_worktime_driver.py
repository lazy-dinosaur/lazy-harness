"""Worktime driver integration using only the conftest-owned local container."""
import ast
from pathlib import Path

import pytest

import digest_driver
import store_pg as pg
import worktime_driver as work
from test_store_pg import fixture, host, judgement


def test_packet_matches_prep_literal():
    tree = ast.parse((Path(__file__).parent / "first-load-01/prep.py").read_text())
    original = next(ast.literal_eval(node.value) for node in tree.body
                    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TEMPLATE"
                                                           for t in node.targets))
    fact = {"reason": "synthetic", "fact": "new", "evidence_quote": "new"}
    packet = work.build_packet(fact, "old")
    assert packet == {"template_id": "record-need", "template_version": "v0.2.2",
                      "questions": original, "state": {"narrative": "synthetic", "candidate_fact": "new",
                                                    "evidence_quote": "new", "existing_records_excerpt": "old"}}
    dep = work.build_packet({**fact, "operation": "deprecate"}, "old")  # G2: deprecate has its own wire template
    assert dep["template_id"] == "intent-deprecate" and dep["state"]["deprecate_reason"] == "new" and "candidate_fact" not in dep["state"]
    with pytest.raises(NotImplementedError):
        work.build_packet({**fact, "operation": "merge"}, "old")


def test_excerpt_host_isolation_and_fallback(dsn, host, monkeypatch):
    other = f"other-{host}"
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("insert into knowledge.host(host_id,name,repo_locator) values (%s,%s,'local-test')", (other, other))
        for owner, text in ((host, "shared phrase same-host"), (other, "shared phrase other-host")):
            cur.execute("""insert into knowledge.fragment(host_id,alias,domain,seq,text,kind,source)
                        values (%s,'domain-1','domain',1,%s,'fact','{"evidence_refs":[]}'::jsonb)""", (owner, text))
    import embed
    def unavailable(query):
        raise embed.EmbeddingUnavailable("offline")
    monkeypatch.setattr(embed, "encode_query", unavailable)
    excerpt = work.existing_excerpt(dsn, host, {"fact": "shared phrase"})
    assert "same-host" in excerpt and "other-host" not in excerpt
    assert "text fallback" in excerpt
    empty = f"empty-{host}"
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("insert into knowledge.host(host_id,name,repo_locator) values (%s,%s,'local-test')", (empty, empty))
    assert "관련 조각이 없다" in work.existing_excerpt(dsn, empty, {"fact": "shared phrase"})


def test_judge_failure_keeps_proposed(dsn, host):
    body = judgement(host)
    entry = pg.register(dsn, body)
    result = work.run_worktime(dsn, 1, lambda packet: (_ for _ in ()).throw(RuntimeError("judge failed")))
    assert result["failures"][0]["fact_index"] == 0
    assert result["results"][0]["state"] == "proposed"
    assert next(r for r in pg.rows(dsn, "ledger_entry") if str(r["entry_id"]) == entry["entry_id"])["state"] == "proposed"
    pg.abandon(dsn, body["work_unit_id"], "test cleanup")


def test_worktime_to_completion_and_digestion(dsn, host):
    body = judgement(host)
    pg.register(dsn, body)
    response = fixture()
    judge = lambda packet: {"answers": response["answers"]}
    result = work.run_worktime(dsn, 1, judge, utterance_judge=lambda fact: {"probabilities": {"confirmed_decision": .98, "tentative_opinion": .02}})
    assert result["failures"] == []
    assert result["results"][0]["state"] == "provisional"
    assert result["results"][0]["utterance_status"]
    assert len([r for r in pg.rows(dsn, "fragment") if r["host_id"] == host]) == 0
    pg.register_completion_sources(dsn, body["work_unit_id"], ["merge"])
    assert pg.signal_completion(dsn, body["work_unit_id"], "merge")["status"] == "completed"
    digested = digest_driver.run_digestion(dsn, body["work_unit_id"], judge)
    assert digested["status"] == "absorbed"
    assert len([r for r in pg.rows(dsn, "fragment") if r["host_id"] == host]) == 1


def test_packet_lint_before_any_judge_call_and_cost_kept(dsn, host):
    # cycle-02 finding: a packet lint error in one fact rejected the whole entry after the other facts were already paid for.
    body = judgement(host)
    good = body["facts"][0]
    # Claim names a code identifier (hospitalId) that none of its quotes contain -> packet lint E_CLAIM_QUOTE.
    bad = {**good, "fact": "new hospitalId", "subject": "new hospitalId", "keywords": [], "evidence_quote": "new",
           "evidence_refs": [{"type": "user_utterance", "locator": "test/local", "quote": "new"}]}
    body["facts"] = [good, bad]
    pg.register(dsn, body)
    calls = []
    def judge(packet):
        calls.append(packet)
        return {"answers": fixture()["answers"], "cost_usd": 0.001, "input_tokens": 10, "output_tokens": 2}
    result = work.run_worktime(dsn, 1, judge)
    assert result["failures"] and "E_CLAIM_QUOTE" in result["failures"][0]["error"]
    assert len(calls) == 1  # the good fact was judged before the bad one was built; no call for the bad fact
    pg.abandon(dsn, body["work_unit_id"], "test cleanup")

    ok = judgement(host)
    entry = pg.register(dsn, ok)
    result = work.run_worktime(dsn, 1, judge)
    assert result["results"][0]["state"] == "provisional"
    receipt = next(r for r in pg.rows(dsn, "check_receipt") if str(r["entry_id"]) == entry["entry_id"])
    assert float(receipt["cost_usd"]) == 0.001 and receipt["input_tokens"] == 10
    pg.abandon(dsn, ok["work_unit_id"], "test cleanup")


def test_existing_excerpt_sees_the_canon_as_the_work_leaves_it(dsn, host, monkeypatch):
    """2026-10-01 split: an add split out of a fragment must not be a duplicate of that fragment's old text."""
    hits = [{"id": "f1", "text": "A는 X이고 B는 Y다"}, {"id": "f2", "text": "C는 Z다"}, {"id": "f3", "text": "D는 W다"}]
    monkeypatch.setattr(work.store_pg, "search", lambda *a, **k: [dict(h) for h in hits])
    facts = [{"operation": "update", "target_ref": "f1", "fact": "A는 X다"},
             {"operation": "deprecate", "target_ref": "f3", "fact": "D는 W다"},
             {"operation": "add", "fact": "B는 Y다"}]
    excerpt = work.existing_excerpt(dsn, host, facts[2], work.pending_rewrites(facts))
    assert "B는 Y" not in excerpt and "A는 X다" in excerpt and "C는 Z다" in excerpt and "D는 W" not in excerpt
    assert "B는 Y" in work.existing_excerpt(dsn, host, facts[2])  # without the work's rewrites: old text
