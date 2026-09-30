"""One isolated PostgreSQL container for the complete local test session."""
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlparse

import pytest

os.environ["LH_EMBED_PROVIDER"] = "local"  # before embed is imported: MODEL_ID follows the provider
import store_pg as pg  # noqa: E402
import embed  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def embed_service():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    python = embed._MODEL_DIR / "venv/bin/python"
    env = {**os.environ, "LH_EMBED_URL": f"http://127.0.0.1:{port}"}
    os.environ["LH_EMBED_URL"] = env["LH_EMBED_URL"]
    process = subprocess.Popen([str(python), str(Path(__file__).parent / "embed_server.py"), "--port", str(port)],
                               env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for _ in range(120):
            if process.poll() is not None:
                pytest.fail(f"embed server exited: {process.stderr.read().decode()}")
            try:
                with urlopen(env["LH_EMBED_URL"] + "/health", timeout=1):
                    break
            except OSError:
                time.sleep(.1)
        else:
            pytest.fail("embed server did not start")
        yield env["LH_EMBED_URL"]
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        os.environ.pop("LH_EMBED_URL", None)
        embed.encode_query.cache_clear()
from test_store_pg import IMAGE, NAME, SQL, docker


@pytest.fixture(scope="session")
def dsn():
    if pg.driver.__name__ not in ("psycopg", "psycopg2"):
        pytest.fail("PostgreSQL driver unavailable")
    # Never allow a credential override: this fixture owns its loopback-only container.
    if not shutil.which("docker") or docker("info").returncode:
        pytest.skip("local Docker unavailable")
    if docker("ps", "-a", "--filter", f"name=^/{NAME}$", "--format", "{{.Names}}").stdout.strip():
        pytest.fail(f"STOP: {NAME} already exists; no container touched")
    if docker("image", "inspect", IMAGE).returncode:
        pytest.skip("local image unavailable (pull forbidden)")
    started = False
    try:
        result = docker("run", "-d", "--rm", "--name", NAME, "-p", "127.0.0.1::5432",
                        "-e", "POSTGRES_PASSWORD=localtest", IMAGE)
        assert result.returncode == 0, result.stderr
        started = True
        port = docker("port", NAME, "5432/tcp")
        assert port.returncode == 0, port.stderr
        local_dsn = f"postgresql://postgres:localtest@127.0.0.1:{port.stdout.strip().rsplit(':', 1)[-1]}/postgres"
        assert urlparse(local_dsn).hostname == "127.0.0.1"
        for _ in range(120):
            if docker("inspect", NAME, "--format", "{{.State.Health.Status}}").stdout.strip() == "healthy":
                try:
                    with pg.connect(local_dsn) as conn, conn.cursor() as cur:
                        cur.execute("select 1")
                    break
                except pg.driver.Error:
                    pass
            time.sleep(1)
        else:
            pytest.fail("local postgres did not become healthy")
        for migration in (SQL, SQL.with_name("0002_search_and_cost.sql"),
                          SQL.with_name("0003_embedding_hybrid.sql"),
                          SQL.with_name("0004_work_unit_baseline.sql"),
                          SQL.with_name("0005_domain_type.sql"),
                          SQL.with_name("0006_rules.sql"),
                          SQL.with_name("0007_harness_rules_out.sql"),
                          SQL.with_name("0008_embedding_any_dim.sql"),
                          SQL.with_name("0009_subject_dictionary.sql")):
            migrated = docker("exec", "-i", NAME, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", "postgres",
                              "-d", "postgres", "-f", "-", input=migration.read_text())
            assert migrated.returncode == 0, migrated.stderr
        yield local_dsn
    finally:
        if started:
            removed = docker("rm", "-f", "-v", NAME)
            assert removed.returncode == 0, removed.stderr
            assert not docker("ps", "-a", "--filter", f"name=^/{NAME}$", "--format", "{{.Names}}").stdout.strip()
