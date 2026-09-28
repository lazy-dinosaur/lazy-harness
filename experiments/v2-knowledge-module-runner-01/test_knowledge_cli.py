"""CLI integration against the conftest-owned disposable database only."""
import json
import os
import subprocess
import sys
from pathlib import Path

import store_pg as pg
import digest_driver
from test_store_pg import fixture, host  # fixture

CLI = Path(__file__).with_name("knowledge_cli.py")


def call(dsn, config_path, command, data):
    env = {**os.environ, "LH_KNOWLEDGE_CONFIG": str(config_path), "LH_KNOWLEDGE_DB_URL": dsn}
    proc = subprocess.run([sys.executable, str(CLI), command], input=json.dumps(data), text=True,
                          capture_output=True, env=env, check=True)
    assert len(proc.stdout.splitlines()) == 1
    return json.loads(proc.stdout)


def sample(text="alpha"):
    return {"operation": "add", "kind": "fact", "subject": text, "fact": text,
            "reason": "synthetic evidence", "evidence_source": "user_confirmed",
            "evidence_refs": [{"type": "user_utterance", "locator": "test/utterance", "quote": text}]}


def test_record_complete_status(dsn, host, tmp_path):
    cfg = tmp_path / "knowledge.json"
    cfg.write_text(json.dumps({"default_host": host}))
    cfg.chmod(0o600)
    payload = {"partition_key": "domain", "facts": [sample()]}
    # subject mismatch is a form-only issue: repaired and reported, not rejected (write-01 revision)
    repaired = call(dsn, cfg, "record", {**payload, "facts": [{**sample(), "subject": "absent"}]})
    assert repaired["state"] == "proposed" and repaired["repairs"][0]["repairs"][0]["field"] == "subject"
    store_pg_cleanup = repaired["work_unit_id"]
    packet_bad = call(dsn, cfg, "record", {**payload, "facts": [{**sample("hospitalId claim"),
        "evidence_refs": [{"type": "user_utterance", "locator": "test/utterance", "quote": "claim"}]}]})
    assert any(e["code"] == "E_CLAIM_QUOTE" for e in packet_bad["errors"])
    assert [str(e["work_unit_id"]) for e in pg.rows(dsn, "ledger_entry") if e["host_id"] == host] == [store_pg_cleanup]
    pg.abandon(dsn, store_pg_cleanup, "test: repaired-subject registration cleanup")
    no_git = tmp_path / "not-git"
    no_git.mkdir()
    first = call(dsn, cfg, "record", {**payload, "cwd": str(no_git)})
    uid = first["work_unit_id"]
    assert first["state"] == "proposed" and first["baseline"]["baseline_code_ref"] is None
    repo = tmp_path / "repo"
    repo.mkdir()
    def git(*args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()
    git("init", "-q")
    git("-c", "user.name=Test", "-c", "user.email=test@local", "commit", "--allow-empty", "-qm", "initial")
    ref = git("rev-parse", "HEAD")
    second = call(dsn, cfg, "record", {**payload, "facts": [sample("beta")], "work_unit_id": uid, "cwd": str(repo)})
    assert second["work_unit_id"] == uid and second["entry_id"] != first["entry_id"]
    assert second["baseline"]["baseline_code_ref"] is None  # immutable first baseline
    body = next(e for e in pg.rows(dsn, "ledger_entry") if str(e["entry_id"]) == second["entry_id"])["judgement_body"]
    assert body["version"] == 1 and body["facts"][0]["evidence_quote"] == "beta"
    assert body["judgement_id"] != next(e for e in pg.rows(dsn, "ledger_entry") if str(e["entry_id"]) == first["entry_id"])["judgement_body"]["judgement_id"]
    third = call(dsn, cfg, "record", {**payload, "facts": [sample("gamma")], "cwd": str(repo)})
    assert third["baseline"]["baseline_code_ref"] == ref
    rejected = call(dsn, cfg, "complete", {"work_unit_id": uid, "user_quote": "맞지?"})
    assert rejected["errors"][0]["code"] == "E_CONFIRM"
    done = call(dsn, cfg, "complete", {"work_unit_id": uid, "user_quote": "확정한다", "locator": "test/user"})
    assert done["status"] == "completed" and done["entry_states"]["proposed"] == 2
    assert "검수 대기" in done["notice"]
    status = call(dsn, cfg, "status", {"work_unit_id": uid})
    assert status["status"] == "completed" and status["changed_since_baseline"] == 0
    assert status["absorbed_aliases"] == [] and status["entry_states"]["proposed"] == 2
    assert status["baseline"]["baseline_code_ref"] is None
    # Do not leave proposed/completed work for the shared-container poller tests.
    pg.abandon(dsn, third["work_unit_id"], "test cleanup")
    for entry_id, text in ((first["entry_id"], "alpha"), (second["entry_id"], "beta")):
        assert pg.batch(dsn, 1, {entry_id: [fixture(text=text)]}, entry_ids=[entry_id])[0]["state"] == "eligible"
    assert digest_driver.run_digestion(dsn, uid, lambda _: {"answers": fixture()["answers"]})["status"] == "absorbed"
