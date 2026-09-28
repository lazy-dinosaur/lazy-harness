"""capture_audit with a deterministic fake Jev (no network)."""
import capture_audit as ca
from test_store_pg import host  # fixture


def fake_judge(knowledge_marker="규칙", covered=()):
    calls = []
    def judge(state, texts, question, criteria=None):
        calls.append((question[:12], criteria is not None))
        if question is ca.CQ:
            return [{"noul": 1.0 if any(c in t for c in covered) else 0.0} for t in texts]
        if criteria:  # kind choice
            return [{"choice": "rule" if knowledge_marker in t else "not_knowledge",
                     "probabilities": {"rule": .9, "not_knowledge": .1} if knowledge_marker in t else {"rule": .1, "not_knowledge": .9}}
                    for t in texts]
        return [{"noul": 0.9 if knowledge_marker in t else 0.1} for t in texts]
    judge.calls = calls
    return judge


TRANSCRIPT = [
    {"role": "user", "text": "빈 병원에만 시딩한다는 규칙을 지켜. 좋아."},
    {"role": "assistant", "text": "알겠습니다. 테스트를 돌려 보겠습니다."},
    {"role": "code", "text": "- `src/unit.ts` — 빈 병원 규칙 구현\n- `README.md` — 오탈자"},
]


def test_split_units_keeps_roles_and_code_lines():
    u = ca.split_units(TRANSCRIPT)
    assert ("user", "빈 병원에만 시딩한다는 규칙을 지켜.") in u
    assert ("code", "`src/unit.ts` — 빈 병원 규칙 구현") in u
    assert all(r in ("user", "assistant", "code") for r, _ in u)
    assert ca.split_units(None) == [] and ca.split_units([{"role": "system", "text": "x y z w"}]) == []


def test_audit_lists_uncovered_knowledge_only():
    j = fake_judge()
    out = ca.audit(TRANSCRIPT, [], j)
    texts = [m["text"] for m in out["missing"]]
    assert texts == ["빈 병원에만 시딩한다는 규칙을 지켜.", "`src/unit.ts` — 빈 병원 규칙 구현"]
    assert out["missing"][0]["kind"] == "rule" and out["missing"][0]["votes"] == 3
    # no recorded facts -> coverage question is skipped
    assert not any(q == ca.CQ[:12] for q, _ in j.calls)


def test_audit_skips_what_recorded_facts_already_cover():
    out = ca.audit(TRANSCRIPT, ["빈 병원에만 시딩"], fake_judge(covered=("시딩",)))
    assert [m["text"] for m in out["missing"]] == ["`src/unit.ts` — 빈 병원 규칙 구현"]


def test_union_any_single_vote_is_enough():
    """Only the kind question flags it (noul questions say no) -> still listed (union rule from q_compare)."""
    def judge(state, texts, question, criteria=None):
        if question is ca.CQ:
            return [{"noul": 0.0} for _ in texts]
        if criteria:
            return [{"choice": "behavior", "probabilities": {"behavior": .7, "not_knowledge": .3}} for _ in texts]
        return [{"noul": 0.1} for _ in texts]
    out = ca.audit([{"role": "user", "text": "버튼을 누르면 모달이 열린다."}], [], judge)
    assert len(out["missing"]) == 1 and out["missing"][0]["votes"] == 1 and out["missing"][0]["kind"] == "behavior"


def test_empty_transcript():
    assert ca.audit([], ["x"], fake_judge()) == {"ok": True, "units": 0, "missing": [], "truncated": False}


def test_cli_audit_reads_recorded_facts_of_the_work_unit(dsn, host, monkeypatch):
    """knowledge_cli.audit pulls facts recorded in the work unit and passes them as coverage context."""
    import knowledge_cli, capture_audit
    seen = {}
    def fake_audit(transcript, recorded, judge):
        seen["recorded"] = recorded; seen["n"] = len(transcript)
        return {"ok": True, "units": 1, "missing": [], "truncated": False}
    monkeypatch.setattr(capture_audit, "audit", fake_audit)
    monkeypatch.setattr(capture_audit, "make_judge", lambda cfg: None)
    monkeypatch.setattr(knowledge_cli.config, "require", lambda *k: {"jev_api_key": "x", "jev_base_url": "x", "jev_model": "x"})
    rec = knowledge_cli.record(dsn, {"partition_key": "D", "host_id": host, "facts": [{"operation": "add", "kind": "fact",
          "subject": "빈 병원", "fact": "빈 병원에만 시딩한다", "reason": "r", "evidence_source": "user_confirmed",
          "evidence_refs": [{"type": "user_utterance", "locator": "t", "quote": "빈 병원에만 시딩한다"}]}]})
    out = knowledge_cli.audit(dsn, {"transcript": [{"role": "user", "text": "빈 병원에만 시딩한다"}], "work_unit_id": rec["work_unit_id"]})
    assert out["ok"] and seen["recorded"] == ["빈 병원에만 시딩한다"] and seen["n"] == 1
    import store_pg as pg
    pg.abandon(dsn, rec["work_unit_id"], "test: capture audit cleanup")


def test_dedupe_keeps_assistant_statement_and_distinct_items():
    items = [{"id": "u0", "from": "user", "text": "설명 제한을 300자로 늘려줘", "kind": "rule", "votes": 3},
             {"id": "u1", "from": "assistant", "text": "설명 제한을 300자로 늘렸습니다.", "kind": "behavior", "votes": 3},
             {"id": "u2", "from": "assistant", "text": "생성 제한은 그대로 둡니다.", "kind": "decision", "votes": 2}]
    vec = {"설명 제한을 300자로 늘려줘": [1.0, 0.0], "설명 제한을 300자로 늘렸습니다.": [0.99, 0.141], "생성 제한은 그대로 둡니다.": [0.0, 1.0]}
    kept = ca.dedupe(items, lambda texts: [vec[t] for t in texts])
    assert [i["id"] for i in kept] == ["u1", "u2"]
    assert ca.dedupe(items, lambda texts: (_ for _ in ()).throw(RuntimeError("down"))) == items
