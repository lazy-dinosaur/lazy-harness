"""rule_cli + rule_review with fake Jev on the disposable DB."""
import rule_cli
import rule_review
import rules_store as rs
from test_store_pg import host  # fixture

RULE = {"when": "코드 파일을 수정했을 때", "must": "관련 테스트를 실행해 통과시킨다", "level": "must"}


def two(label_cond, label_done):
    def ask2(state, n):
        c = {"type": "choice", "choice": label_cond, "probabilities": {k: (.9 if k == label_cond else .05) for k in ("met", "not_met", "unsure")}}
        d = {"type": "choice", "choice": label_done, "probabilities": {k: (.9 if k == label_done else .05) for k in ("done", "not_done", "unsure")}}
        return [c, d] * n, {}
    return ask2


def test_cli_crud_without_review(dsn, host):
    out = rule_cli.run(dsn, host, "create", {"rule": RULE, "quote": "앞으로 테스트 돌려"}, review_factory=None)
    rid = out["id"]
    assert [r["id"] for r in rule_cli.run(dsn, host, "list", {})["rules"]] == [rid]
    assert rule_cli.run(dsn, host, "update", {"id": rid, "changes": {"level": "should"}, "quote": "권장으로"})["version"] == 2
    assert rule_cli.run(dsn, host, "delete", {"id": rid, "quote": "지워"})["status"] == "deleted"
    assert [h["op"] for h in rule_cli.run(dsn, host, "history", {"id": rid})["history"]] == ["create", "update", "delete"]


def test_review_flags_conflict_and_broad(dsn, host):
    ask = lambda state: {"conflict": .9 if state["existing"] else .1, "duplicate": .1, "weakens_base": .9}
    review = rule_review.make_review(ask, two("met", "not_done"), lambda: ["t1", "t2", "t3"])
    first = rs.create(dsn, host, RULE, "테스트 돌려", review=review)
    assert first["needs_user"] and any("너무 넓어서" in f for f in first["flags"])
    assert not any("기본 규칙" in f for f in first["flags"])  # no base rules registered -> no weakens flag
    quiet = rule_review.make_review(ask, two("not_met", "done"), lambda: ["t1", "t2", "t3"])
    ok = rs.create(dsn, host, RULE, "테스트 돌려", review=quiet)
    assert ok["ok"] and ok["flags"] == []
    again = rs.create(dsn, host, {**RULE, "must": "테스트 없이 커밋한다"}, "빨리", review=quiet)
    assert again["needs_user"] and any("충돌" in f for f in again["flags"])


def test_review_unjudgeable_and_skip_dry_run(dsn, host):
    ask = lambda state: {"conflict": .1, "duplicate": .1, "weakens_base": .1}
    vague = rule_review.make_review(ask, two("met", "unsure"), lambda: ["t1", "t2", "t3"])
    held = rs.create(dsn, host, {**RULE, "must": "깔끔하게 짠다"}, "깔끔하게", review=vague)
    assert any("판정하기 어려움" in f for f in held["flags"])
    few = rule_review.make_review(ask, two("met", "unsure"), lambda: ["t1"])
    assert rs.create(dsn, host, RULE, "테스트", review=few)["ok"]  # too few judged turns -> no dry run


def test_rule_block_and_injection(dsn, host):
    assert rule_cli.run(dsn, host, "block", {}) == {"text": "", "ids": [], "tokens": 0}
    rid = rule_cli.run(dsn, host, "create", {"rule": {**RULE, "unless": "문서만 바꾼 경우", "ref": "디자인 시스템"},
                                            "quote": "테스트 돌려"}, review_factory=None)["id"]
    block = rule_cli.run(dsn, host, "block", {})
    assert block["ids"] == [rid] and block["text"].startswith("[harness-rules]")
    assert f"[{rid}] (반드시) 코드 파일을 수정했을 때 → 관련 테스트를 실행해 통과시킨다 (예외: 문서만 바꾼 경우 / 기준: 지식 '디자인 시스템')" in block["text"]
    out = rule_cli.run(dsn, host, "inject", {"turn_ref": "s1#1", "rule_ids": block["ids"], "aliases": ["design-1"], "tokens": block["tokens"]})
    assert out["ok"] and rs.injected(dsn, host, "s1#1") == {"rules": [rid], "knowledge": ["design-1"]}
