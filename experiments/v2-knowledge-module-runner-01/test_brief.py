"""knowledge_brief: wide collection -> temp file read by the writer -> only the brief comes back; temp file removed."""
from pathlib import Path

import pytest

import brief
from test_store_pg import host  # fixture
from test_worker_tools import ROWS, need_ask, seed_kinds


def test_brief_returns_writer_text_and_removes_temp(dsn, host):
    seed_kinds(dsn, host, ROWS, groups={4: "D:g2"})
    seen = {}
    def runner(prompt, cwd):
        f = Path(prompt.split("파일: ")[1].split("\n")[0])
        seen["doc"], seen["path"], seen["mode"] = f.read_text(), f, oct(f.stat().st_mode & 0o777)
        seen["prompt"] = prompt
        return "## 이전 결정·이유\n- x [D-002@1]"
    out = brief.brief(dsn, host, "일정 종류 이름을 바꾼다", ["일정 종류"], need_ask, change="이름을 CLINIC 으로", runner=runner)
    assert out["brief"].startswith("## 이전 결정") and out["relevant"] == 3
    assert out["collected"] == 4  # working domain D expanded: the unjudged D-004 is collected for the writer
    assert "⚠ 충돌 후보 [D-003@1]" in seen["doc"] and "[D-004@1]" in seen["doc"] and seen["mode"] == "0o600"
    assert "하려는 변경: 이름을 CLINIC 으로" in seen["prompt"]
    assert not seen["path"].exists() and not seen["path"].parent.exists()  # temp removed


def test_brief_cleans_up_on_writer_failure(dsn, host):
    seed_kinds(dsn, host, ROWS)
    seen = {}
    def runner(prompt, cwd):
        seen["cwd"] = Path(cwd)
        raise RuntimeError("writer down")
    with pytest.raises(RuntimeError):
        brief.brief(dsn, host, "일정 종류", ["일정 종류"], need_ask, runner=runner)
    assert not seen["cwd"].exists()
