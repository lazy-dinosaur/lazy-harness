"""G3: backup rotation and restore safety (the live round trip is checked by backup.py verify)."""
import json

import pytest

import backup
import store_pg as pg
from test_store_pg import host  # fixture


def test_rotate_keeps_newest(tmp_path):
    for i in range(17):
        (tmp_path / f"knowledge-2026092{i:02d}T000000Z.dump").write_bytes(b"x")
        (tmp_path / f"knowledge-2026092{i:02d}T000000Z.json").write_text("{}")
    gone = backup.rotate(tmp_path, keep=14)
    assert len(gone) == 3 and sorted(p.name for p in tmp_path.glob("*.dump"))[0] == "knowledge-202609203T000000Z.dump"
    assert len(list(tmp_path.glob("*.json"))) == 14


def test_backup_then_restore_refuses_existing_schema(dsn, host, tmp_path):
    meta = backup.backup(dsn, tmp_path)
    f = tmp_path / meta["file"]
    assert f.exists() and (f.stat().st_mode & 0o777) == 0o600 and meta["row_counts"]["host"] >= 1
    assert "history_ratio" in meta and "warning" not in meta
    with pytest.raises(RuntimeError, match="refuses to overwrite"):
        backup.restore(f, dsn)  # the test DB already has knowledge -> never overwritten
    side = json.loads(f.with_suffix(".json").read_text())
    side["sha256"] = "0" * 64
    f.with_suffix(".json").write_text(json.dumps(side))
    with pytest.raises(RuntimeError, match="sha256"):
        backup.restore(f, dsn)
