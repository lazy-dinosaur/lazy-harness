"""G3 backup/restore for the knowledge schema (planning/v2-knowledge-module-open-gaps.md 'G3').

  backup            pg_dump --schema=knowledge (custom format) to ~/.local/share/lazy-harness-v2/backups, keep newest 14,
                    sidecar JSON with per-table row counts and sha256.
  restore FILE URL  restore into URL; refuses when URL already has a knowledge schema (never overwrites).
  verify [FILE]     restore FILE (default newest) into a disposable local Supabase PG container, compare row counts and
                    one text search with the source DB, then remove the container.
The live DB is only read. DB URL comes from knowledge.json (config.require('db_url')); it is never printed.
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import config
import store_pg

DIR = Path(os.environ.get("LH_BACKUP_DIR") or Path.home() / ".local/share/lazy-harness-v2/backups")
KEEP = 14
HISTORY_RATIO_WARN = 10  # G9 (user 2026-09-28): history is kept in full; re-decide when history rows exceed 10x fragments
IMAGE = "public.ecr.aws/supabase/postgres:17.6.1.134"


def _counts(dsn):
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select n.nspname, c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace
                       where n.nspname in ('knowledge','rules') and c.relkind='r' order by 1, 2""")
        tables = cur.fetchall()
        out = {}
        for schema, t in tables:
            cur.execute(f'select count(*) from {schema}."{t}"')
            out[t if schema == "knowledge" else f"{schema}.{t}"] = cur.fetchone()[0]
        return out


def rotate(folder, keep=KEEP):
    """Delete all but the newest `keep` dumps (and their sidecars). Returns deleted dump names."""
    dumps = sorted(folder.glob("knowledge-*.dump"))
    gone = dumps[:-keep] if len(dumps) > keep else []
    for d in gone:
        d.unlink()
        d.with_suffix(".json").unlink(missing_ok=True)
    return [d.name for d in gone]


def backup(dsn=None, folder=DIR):
    dsn = dsn or config.require("db_url")["db_url"]
    folder.mkdir(parents=True, exist_ok=True)
    os.chmod(folder, 0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = folder / f"knowledge-{stamp}.dump"
    counts = _counts(dsn)
    tmp = path.with_suffix(".part")
    old = os.umask(0o077)
    try:
        r = subprocess.run(["pg_dump", "--schema=knowledge", "--schema=rules", "-Fc", "--no-owner", "--no-privileges", "-f", str(tmp), "-d", dsn],
                           capture_output=True, text=True)
    finally:
        os.umask(old)
    if r.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("pg_dump failed: " + r.stderr.replace(dsn, "<db_url>")[-400:])
    tmp.rename(path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    meta = {"file": path.name, "created_utc": stamp, "bytes": path.stat().st_size, "sha256": sha, "row_counts": counts}
    ratio = counts.get("fragment_history", 0) / max(1, counts.get("fragment", 0))
    meta["history_ratio"] = round(ratio, 2)
    if ratio > HISTORY_RATIO_WARN:
        meta["warning"] = f"fragment_history is {ratio:.1f}x fragments (> {HISTORY_RATIO_WARN}x): revisit the retention policy"
    side = path.with_suffix(".json")
    side.write_text(json.dumps(meta, indent=1))
    os.chmod(side, 0o600)
    meta["rotated_out"] = rotate(folder)
    return meta


def restore(file, target_dsn):
    file = Path(file)
    meta = json.loads(file.with_suffix(".json").read_text())
    if hashlib.sha256(file.read_bytes()).hexdigest() != meta["sha256"]:
        raise RuntimeError("backup file sha256 mismatch")
    with store_pg.connect(target_dsn) as conn, conn.cursor() as cur:
        cur.execute("select to_regnamespace('knowledge') is not null")
        if cur.fetchone()[0]:
            raise RuntimeError("target already has a knowledge schema; restore refuses to overwrite (drop it yourself first)")
        cur.execute("create schema if not exists extensions")
        cur.execute("create extension if not exists vector with schema extensions")
        cur.execute("create extension if not exists pg_trgm with schema extensions")
    r = subprocess.run(["pg_restore", "--no-owner", "--no-privileges", "--exit-on-error", "-d", target_dsn, str(file)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("pg_restore failed: " + r.stderr.replace(target_dsn, "<target>")[-600:])
    got = _counts(target_dsn)
    return {"file": file.name, "row_counts_match": got == meta["row_counts"], "expected": meta["row_counts"], "restored": got}


def _docker(*a, **k):
    return subprocess.run(["docker", *a], text=True, capture_output=True, **k)


def verify(file=None, name="lh-kdb-restore-check"):
    file = Path(file) if file else sorted(DIR.glob("knowledge-*.dump"))[-1]
    if _docker("ps", "-a", "--filter", f"name=^/{name}$", "--format", "{{.Names}}").stdout.strip():
        raise RuntimeError(f"{name} exists")
    assert _docker("run", "-d", "--rm", "--name", name, "-p", "127.0.0.1::5432", "-e", "POSTGRES_PASSWORD=localtest", IMAGE).returncode == 0
    try:
        port = _docker("port", name, "5432/tcp").stdout.strip().rsplit(":", 1)[-1]
        dsn = f"postgresql://postgres:localtest@127.0.0.1:{port}/postgres"
        for _ in range(120):
            if _docker("inspect", name, "--format", "{{.State.Health.Status}}").stdout.strip() == "healthy":
                try:
                    with store_pg.connect(dsn) as c, c.cursor() as cur:
                        cur.execute("select 1")
                    break
                except store_pg.driver.Error:
                    pass
            time.sleep(1)
        out = restore(file, dsn)
        src = config.require("db_url")["db_url"]
        meta = json.loads(file.with_suffix(".json").read_text())
        with store_pg.connect(src) as conn, conn.cursor() as cur:
            cur.execute("select host_id, text from knowledge.fragment where active order by id limit 1")
            row = cur.fetchone()
        if row:
            probe = row[1][:30]
            a = [r["id"] for r in store_pg.search(src, row[0], probe, 5)]
            b = [r["id"] for r in store_pg.search(dsn, row[0], probe, 5)]
            out["search_match"] = a == b
        out["live_counts_now"] = _counts(src)
        out["backup_counts"] = meta["row_counts"]
        return out
    finally:
        _docker("rm", "-f", name)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "backup"
    if cmd == "backup":
        print(json.dumps(backup()))
    elif cmd == "restore" and len(sys.argv) == 4:
        print(json.dumps(restore(sys.argv[2], sys.argv[3])))
    elif cmd == "verify":
        print(json.dumps(verify(sys.argv[2] if len(sys.argv) > 2 else None)))
    else:
        raise SystemExit("usage: backup.py backup | restore FILE TARGET_DB_URL | verify [FILE]")


if __name__ == "__main__":
    main()
