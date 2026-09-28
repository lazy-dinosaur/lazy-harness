"""Offline injected transports for fragment assembly and Jev validation."""
import hashlib
import json
import pytest

import collect
import fragment
from judge_jev import make_jev_judge

SOURCE = "\n".join(f"규칙 줄 {i}" for i in range(1, 41))


def output(count=6, text="규칙을 지킨다."):
    return json.dumps({"records": [{"record_id": "R1", "fragments": [
        {"text": text, "kind": "fact", "source_lines": [1, 2], "group": f"g{i}"}
        for i in range(count)]}]}, ensure_ascii=False)


def test_fragment_prompt_and_retry_from_japanese():
    calls = iter([output(text="規則です"), output()])
    def llm(prompt):
        assert "R1" in prompt and "source.md" in prompt
        return next(calls)
    result = fragment.fragment_record("R1", SOURCE, "source.md", llm)
    assert result["ok"] and len(result["attempts"]) == 2
    assert "kana" in result["attempts"][0]["reasons"]
    assert result["attempts"][1]["ok"]


def test_fragment_repair_and_failure_preservation():
    raw = output()[:-1]
    result = fragment.fragment_record("R1", SOURCE, "source.md", lambda _: raw)
    assert result["ok"] and result["attempts"][0]["repaired"]
    assert result["attempts"][0]["raw_sha256"] == hashlib.sha256(raw.encode()).hexdigest()
    for bad, reason in (("거부합니다", "parse"), (output(40), "count")):
        failed = fragment.fragment_record("R1", SOURCE, "source.md", lambda _: bad)
        assert not failed["ok"] and len(failed["attempts"]) == 2
        assert any(reason in r for r in failed["attempts"][-1]["reasons"])
        assert failed["attempts"][-1]["raw_sha256"] == hashlib.sha256(bad.encode()).hexdigest()


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


def test_jev_model_question_threshold_and_judgments():
    calls = []
    def http(request, timeout):
        packet = json.loads(request.data)
        calls.append(packet)
        return FakeResponse({"answers": {"0": {"type": "noul", "noul": 0.4}}})
    candidate = [{"id": "id1", "text": "내용"}]
    judge = make_jev_judge("topic", ["query"], base_url="https://local.invalid", api_key="secret", http=http)
    assert judge("query", candidate) == [{"relevant": False, "novel": False}]
    assert calls[0]["model"] == "~typesafe/jev-latest"
    assert calls[0]["questions"]["0"]["criteria"]["true"] == "topic 을 다루는 데 필요한 내용이다"
    assert judge.judgments == [{"query": "query", "candidate_id": "id1", "score": .4, "relevant": False}]
    judge = make_jev_judge("topic", ["query"], base_url="https://local.invalid", api_key="secret",
                           threshold=.3, question="narrow", http=http)
    assert judge("query", candidate)[0]["relevant"]
    assert "바로 그 기능" in calls[-1]["questions"]["0"]["instructions"]
    with pytest.raises(ValueError, match="model"):
        make_jev_judge("topic", ["query"], base_url="https://local.invalid", api_key="secret", model="")


@pytest.mark.parametrize("answer", [
    {"other": {"type": "noul", "noul": .9}},
    {"0": {"type": "noul", "noul": 1.2}},
    {"0": {"type": "noul", "noul": True}},
    {"0": {"type": "choice", "noul": .8}},
])
def test_jev_invalid_answers_retry_then_fail(answer):
    requests = []
    def http(request, timeout):
        requests.append(request)
        return FakeResponse({"answers": answer})
    judge = make_jev_judge("topic", ["query"], base_url="https://local.invalid", api_key="secret", http=http)
    with pytest.raises(collect.JudgePageFailure):
        judge("query", [{"id": "id1", "text": "내용"}])
    assert len(requests) == 2 and judge.judgments == []


def test_jev_raw_redacts_key(tmp_path):
    def http(request, timeout):
        return FakeResponse({"answers": {"0": {"type": "noul", "noul": .5, "echo": "secret"}}})
    judge = make_jev_judge("topic", ["query"], base_url="https://local.invalid", api_key="secret",
                           raw_dir=tmp_path, http=http)
    assert judge("query", [{"id": "id1", "text": "내용"}])[0]["relevant"]
    assert b"secret" not in next(tmp_path.iterdir()).read_bytes()
