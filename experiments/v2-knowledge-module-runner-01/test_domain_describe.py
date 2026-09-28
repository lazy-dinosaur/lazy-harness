"""domain describe: bounded metadata edit, isolated local PostgreSQL only."""
import io
import json
from unittest.mock import Mock

import pytest

import domain_router as dr
import knowledge_cli as cli
import store_pg as pg
from test_store_pg import host
from test_domain_digest import absorb


@pytest.mark.parametrize("domain", [None, "", " \t", 1, [], {}])
def test_invalid_domain(domain):
    cur = Mock()
    with pytest.raises(ValueError, match="domain must"):
        dr.describe(cur, "host", domain, "설명")
    cur.execute.assert_not_called()


@pytest.mark.parametrize("description", [None, "", " \n", 1, [], {}, "가" * 301])
def test_invalid_description(description):
    cur = Mock()
    with pytest.raises(ValueError, match="description must"):
        dr.describe(cur, "host", "예약", description)
    cur.execute.assert_not_called()


@pytest.mark.parametrize("length", [200, 201, 300])
def test_valid_description(length):
    cur = Mock(rowcount=1)
    dr.describe(cur, "host", " 예약 ", " " + "가" * length + " ")
    assert cur.execute.call_args.args[1] == ("가" * length, "host", "예약")


def test_describe_cli_and_isolation(dsn, host, monkeypatch, capsys):
    absorb(dsn, host, "예약 기본 길이는 30분이다", "예약", lambda text, options: {})
    other = host + "-other"
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("insert into knowledge.host(host_id,name,repo_locator) values (%s,%s,%s)",
                    (other, other, "local-test"))
        for h in (host, other):
            dr.ensure(cur, h, "예약", "old")
        dr.ensure(cur, host, "병합", "merged-old")
        dr.merge(cur, host, "병합", "예약")
        dr.ensure(cur, host, "폐기", "retired-old")
        dr.retire(cur, host, "폐기")
        cur.execute("update knowledge.domain_type set updated_at='2000-01-01' where host_id=%s", (host,))
        cur.execute("select * from knowledge.fragment where host_id=%s", (host,))
        before_fragments = cur.fetchall()
        assert len(before_fragments) == 1
    monkeypatch.setattr(cli.config, "load", lambda: {"default_host": host})
    monkeypatch.setattr(cli.config, "require", lambda *args: {"db_url": dsn})
    monkeypatch.setattr(cli.sys, "argv", ["knowledge_cli.py", "domain"])
    monkeypatch.setattr(cli.sys, "stdin", io.StringIO(json.dumps({
        "action": "describe", "domain": " 예약 ", "description": " " + "가" * 300 + " "})))
    cli.main()
    result = json.loads(capsys.readouterr().out)
    rows = {r["domain"]: r for r in result["domains"]}
    assert rows["예약"]["description"] == "가" * 300
    assert rows["예약"]["status"] == "active" and rows["예약"]["merged_into"] is None
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        assert dr.load(cur, other)["예약"]["description"] == "old"
        cur.execute("select updated_at > '2000-01-01'::timestamptz from knowledge.domain_type where host_id=%s and domain=%s", (host, "예약"))
        assert cur.fetchone()[0]
        cur.execute("select * from knowledge.fragment where host_id=%s", (host,))
        assert cur.fetchall() == before_fragments
    for name in ("없는", "폐기", "병합"):
        with pytest.raises(ValueError, match="unknown or inactive"):
            cli.domain_cmd(dsn, {"host_id": host, "action": "describe", "domain": name, "description": "no"})
    with pytest.raises(ValueError):
        cli.domain_cmd(dsn, {"host_id": "missing-host", "action": "describe", "domain": "예약", "description": "no"})
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        rows = dr.load(cur, host)
        assert rows["병합"]["description"] == "merged-old"
        assert rows["폐기"]["description"] == "retired-old"
        assert rows["예약"]["description"] == "가" * 300
    assert cli.domain_cmd(dsn, {"host_id": other, "action": "describe", "domain": "예약", "description": "x"})["domains"][0]["description"] == "x"
    monkeypatch.setattr(cli.sys, "stdin", io.StringIO('{"action":"describe","domain":"예약","description":false}'))
    cli.main()
    assert json.loads(capsys.readouterr().out)["error"] == "ValueError"
