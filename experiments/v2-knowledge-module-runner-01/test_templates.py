"""templates.py is the single template source and must match the migration seed and the first-load packets."""
import ast
import json
from pathlib import Path

import templates
import worktime_driver

HERE = Path(__file__).parent


def _prep_literal():
    tree = ast.parse((HERE / "first-load-01/prep.py").read_text(encoding="utf-8"))
    return next(ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "TEMPLATE" for t in n.targets))


def test_record_need_matches_seed_and_first_load():
    seeded = templates.record_need()
    assert seeded == _prep_literal()
    first = json.loads((HERE / "first-load-01/packets.json").read_text(encoding="utf-8"))[0]["questions"]
    assert seeded == first
    assert set(seeded) == {"is_new", "is_supported", "durability", "impact"}


def test_worktime_uses_single_source():
    assert worktime_driver._questions() == templates.record_need()
    assert worktime_driver._intent_questions() == templates.intent()


def test_utterance_packet_shape():
    p = templates.utterance_packet("조수가 선택지를 제시했다.", "그렇게 하자")
    assert set(p["questions"]) == {"utterance_status"}
    q = p["questions"]["utterance_status"]
    assert q["type"] == "choice" and set(q["criteria"]) == {"confirmed_decision", "tentative_opinion", "none_or_uncertain"}
