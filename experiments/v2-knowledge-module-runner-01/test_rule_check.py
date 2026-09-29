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


def fake_two(answers):
    def ask2(state, n):
        rules = state["rules"]
        out = []
        for r in rules:
            c, d = answers[r["must"]]
            out.append({"type": "choice", "choice": c, "probabilities": {k: (.9 if k == c else .05) for k in rc.COND}})
            out.append({"type": "choice", "choice": d, "probabilities": {k: (.9 if k == d else .05) for k in rc.DONE}})
        return out, {"input_tokens": 50, "output_tokens": 5, "cost": 0.0}
    return ask2


def test_two_step_labels_and_alert():
    rules = [{"id": "p-1", "when": "w1", "must": "m1"}, {"id": "p-2", "when": "w2", "must": "m2", "unless": "u2"},
             {"id": "p-3", "when": "w3", "must": "m3"}, {"id": "p-4", "when": "w4", "must": "m4"}]
    ans = {"m1": ("met", "done"), "m2": ("not_met", "not_done"), "m3": ("met", "not_done"), "m4": ("unsure", "done")}
    verdicts, usage = rc.check_two_step("ev", rules, fake_two(ans))
    assert [v["label"] for v in verdicts] == ["followed", "not_applicable", "violated", "unsure"]
    assert usage["requests"] == 1 and verdicts[2]["confident"]
    text = rc.alert(verdicts, rules, "ev-summary")
    assert "p-3" in text and "m3" in text and "p-1" not in text and "ev-summary" in text
