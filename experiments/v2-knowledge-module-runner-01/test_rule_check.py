"""rule_check engine: batching, parallel requests, verdict margin, continue policy (Jev faked)."""
import threading

import pytest

import rule_check as rc


def fake_ask(labels):
    calls = []
    lock = threading.Lock()
    def ask(state, n):
        with lock:
            calls.append([r["text"] for r in state["rules"]])
        out = []
        for r in state["rules"]:
            lab, p = labels[r["text"]]
            probs = {k: (p if k == lab else (1 - p) / 3) for k in rc.LABELS}
            out.append({"type": "choice", "choice": lab, "probabilities": probs})
        return out, {"input_tokens": 100, "output_tokens": 10, "cost": 0.0001}
    ask.calls = calls
    return ask


RULES = ["a", "b", "c", "d", "e"]
LABELS = {"a": ("followed", .9), "b": ("violated", .9), "c": ("violated", .3), "d": ("unsure", .8), "e": ("not_applicable", .95)}


@pytest.mark.parametrize("batch,requests", [(1, 5), (2, 3), (5, 1), (9, 1)])
def test_batch_sizes_give_same_verdicts(batch, requests):
    ask = fake_ask(LABELS)
    verdicts, usage = rc.check("ev", RULES, ask, batch=batch)
    assert usage["requests"] == requests == len(ask.calls)
    assert [v["label"] for v in verdicts] == ["followed", "violated", "violated", "unsure", "not_applicable"]
    assert usage["input_tokens"] == 100 * requests


def test_only_confident_violation_continues():
    verdicts, _ = rc.check("ev", RULES, fake_ask(LABELS), batch=1)
    cont, notice = rc.to_continue(verdicts, RULES)
    assert cont == ["b"] and notice == ["d"]  # 'c' violated but low margin -> no continuation
    with pytest.raises(ValueError):
        rc.check("ev", RULES, fake_ask(LABELS), batch=0)
