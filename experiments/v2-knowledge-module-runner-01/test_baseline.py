"""Work-unit baseline integration and local Git checks (no network)."""
import subprocess
from pathlib import Path
from uuid import uuid4

import digest_driver
import store_pg as pg
from test_store_pg import fixture, host, judgement


def stage(dsn, body):
    entry = pg.register(dsn, body)
    response = fixture(text=body["facts"][0]["fact"])
    assert pg.batch(dsn, 1, {entry["entry_id"]: [response]})[0]["state"] == "provisional"
    pg.complete(dsn, body["work_unit_id"])
    return response


def test_baseline_and_changes(dsn, host):
    first = judgement(host, text="first baseline")
    first["baseline_code_ref"] = "commit-1"
    base = pg.start_work_unit(dsn, first["work_unit_id"], host, "domain", "commit-1")
    assert base["baseline_history_id"] == 0 and base["baseline_at"]
    assert pg.start_work_unit(dsn, first["work_unit_id"], host, "domain", "other") == base
    first["baseline_code_ref"] = "other"
    response = stage(dsn, first)
    assert pg.start_work_unit(dsn, first["work_unit_id"], host, "domain") == base
    assert pg.changed_since_baseline(dsn, first["work_unit_id"]) == []
    assert digest_driver.run_digestion(dsn, first["work_unit_id"], lambda _: {"answers": response["answers"]})["status"] == "absorbed"
    assert len(pg.changed_since_baseline(dsn, first["work_unit_id"])) == 1

    waiting = judgement(host, text="waiting fact")
    waiting["baseline_code_ref"] = "commit-2"
    waiting_response = stage(dsn, waiting)
    unit = next(u for u in pg.rows(dsn, "work_unit") if str(u["work_unit_id"]) == waiting["work_unit_id"])
    assert unit["baseline_code_ref"] == "commit-2" and unit["baseline_history_id"] > 0
    assert pg.changed_since_baseline(dsn, waiting["work_unit_id"]) == []
    newer = judgement(host, text="new current canon")
    newer_response = stage(dsn, newer)
    assert digest_driver.run_digestion(dsn, newer["work_unit_id"],
        lambda _: {"answers": newer_response["answers"]})["status"] == "absorbed"
    changes = pg.changed_since_baseline(dsn, waiting["work_unit_id"])
    assert len(changes) == 1 and changes[0]["text"] == "new current canon"
    seen = []
    def judge(packet):
        seen.append(packet["state"]["existing_records_excerpt"])
        return {"answers": waiting_response["answers"]}
    assert digest_driver.run_digestion(dsn, waiting["work_unit_id"], judge)["status"] == "absorbed"
    assert len(seen) == 1 and "new current canon" in seen[0]


def test_code_changed_since(tmp_path):
    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    git("init", "-q")
    git("config", "user.email", "local@example.test")
    git("config", "user.name", "Local")
    path = tmp_path / "proof.py"
    path.write_text("original\n")
    git("add", "proof.py")
    git("commit", "-qm", "baseline")
    ref = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], check=True,
                         capture_output=True, text=True).stdout.strip()
    assert pg.code_changed_since(tmp_path, ref, "proof.py") is False
    path.write_text("changed\n")
    assert pg.code_changed_since(tmp_path, ref, "proof.py") is True
    assert pg.code_changed_since(tmp_path, None, "proof.py") is None
    assert pg.code_changed_since(tmp_path, "invalid-ref", "proof.py") is None
    assert pg.code_changed_since(tmp_path, ref, "../outside") is None
