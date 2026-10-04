"""Stage 2 of resolving aliases in the subject dictionary (2026-10-03, user 'a'): an alias_conflict question is answered
by the user; 'same' merges the two subjects in place (no revision bump, option A) with a merge log, 'different' and
'defer' change nothing; an undo reverts exactly the logged rows (later merges first). astra design review fixes: the
trigger allows the move only for rows logged by the merge running in this transaction, a question binds to the two
subjects shown, the host subject generation fails a judgement made across a merge, moved fragments are rescanned."""
import pytest

import knowledge_cli
import store_pg as pg
import subject_dict
from test_declared_alias import _absorb, _frag
from test_store_pg import host  # noqa: F401 (fixture)

OPT = "회수접수는 우편번호를 선택 항목으로 둔다"
REQ = "반품API는 우편번호를 필수로 요구한다"
JUDGE = lambda state, texts, q, criteria=None: [{"noul": 0.9 if ("선택" in t) != ("선택" in state["fact"]) else 0.0} for t in texts]


def _conflicts(dsn, host):
    return [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "alias_conflict"]


def _setup(dsn, host):
    _absorb(dsn, host, OPT, "회수접수")
    _absorb(dsn, host, REQ, "반품API", aliases=["회수접수"])
    (item,) = _conflicts(dsn, host)
    return item["question_ids"][0]


def _answer(dsn, host, qid, decision, quote="응 그 둘은 같은 거야"):
    return knowledge_cli.review_cmd(dsn, {"host_id": host, "action": "resolve", "decision": decision,
                                         "question_ids": [qid], "user_quote": quote})


def _undo(dsn, host, mid, quote="아니 그건 다른 거였어"):
    return knowledge_cli.review_cmd(dsn, {"host_id": host, "action": "undo_merge", "merge_id": mid, "user_quote": quote})


def test_same_merges_in_place_and_the_rescan_finds_the_contradiction(dsn, host):
    qid = _setup(dsn, host)
    before = (_frag(dsn, host, OPT), _frag(dsn, host, REQ))
    assert before[0]["subject_id"] != before[1]["subject_id"]
    out = _answer(dsn, host, qid, "same")
    assert out["merge_id"] and out["rescan"] == 2
    a, b = _frag(dsn, host, OPT), _frag(dsn, host, REQ)
    assert a["subject_id"] == b["subject_id"]
    assert (a["text"], a["revision"], b["text"], b["revision"]) == (OPT, before[0]["revision"], REQ, before[1]["revision"])
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # leaves moved too, the history has no extra row
        cur.execute("""select count(distinct l.subject_id) from knowledge.fragment_leaf l where l.fragment_id = any(%s::uuid[])""",
                    ([a["id"], b["id"]],))
        assert cur.fetchone()[0] == 1
        cur.execute("select count(*) from knowledge.fragment_history where fragment_id = any(%s::uuid[])", ([a["id"], b["id"]],))
        assert cur.fetchone()[0] == 2
    assert not _conflicts(dsn, host)
    assert pg.rescan_fragments(dsn, JUDGE, limit=10)["rescanned"] == 2
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select count(*) from knowledge.confirmation_queue where rule_id='canon_contradiction'")
        assert cur.fetchone()[0] >= 1
        cur.execute("select count(*) from knowledge.fragment_rescan where done_at is null")
        assert cur.fetchone()[0] == 0
    assert not [i for i in knowledge_cli.review_cmd(dsn, {"host_id": host})["items"] if i.get("kind") == "alias_recheck"]


def test_a_name_merged_away_keeps_its_text_and_gets_the_survivor(dsn, host):
    qid = _setup(dsn, host)
    _answer(dsn, host, qid, "same")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        hits = {n: subject_dict.lookup(cur, host, n) for n in ("회수접수", "반품API")}
    assert hits["회수접수"]["subject_id"] == hits["반품API"]["subject_id"]
    assert "merged" in {hits["회수접수"]["kind"], hits["반품API"]["kind"]}
    later = "회수접수는 우편번호를 다섯 자리로 받는다"
    _absorb(dsn, host, later, "회수접수")
    _absorb(dsn, host, "반품API는 우편번호를 숫자로 받는다", "반품API")
    assert _frag(dsn, host, later)["subject_id"] == _frag(dsn, host, REQ)["subject_id"]
    assert _frag(dsn, host, "반품API는 우편번호를 숫자로 받는다")["subject_id"] == _frag(dsn, host, REQ)["subject_id"]


def test_different_and_defer_change_nothing(dsn, host):
    qid = _setup(dsn, host)
    assert _answer(dsn, host, qid, "defer", "나중에 볼게")["decision"] == "defer"
    assert [i["question_ids"] for i in _conflicts(dsn, host)] == [[qid]]
    assert _answer(dsn, host, qid, "different", "아니 다른 거야")["decision"] == "different"
    assert _frag(dsn, host, OPT)["subject_id"] != _frag(dsn, host, REQ)["subject_id"]
    assert not _conflicts(dsn, host)
    with pytest.raises(ValueError, match="already closed"):  # a retried answer is refused
        _answer(dsn, host, qid, "same")


def test_subject_id_moves_only_inside_a_logged_merge(dsn, host):
    _setup(dsn, host)
    a, b = _frag(dsn, host, OPT), _frag(dsn, host, REQ)
    with pytest.raises(Exception, match="revision must advance"):
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("update knowledge.fragment set subject_id=%s where id=%s", (b["subject_id"], a["id"]))
    with pytest.raises(Exception, match="written once"):
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("update knowledge.fragment_leaf set subject_id=%s where fragment_id=%s", (b["subject_id"], a["id"]))


def test_a_question_about_a_subject_merged_meanwhile_is_asked_again(dsn, host):
    qid = _setup(dsn, host)
    _absorb(dsn, host, "회수운임은 할인을 금지한다", "회수운임")
    _absorb(dsn, host, "반품요금은 할인을 허용한다", "반품요금", aliases=["회수운임"])
    other = [i["question_ids"][0] for i in _conflicts(dsn, host) if i["question_ids"][0] != qid][0]
    _answer(dsn, host, other, "same")
    # a third conflict names a subject that was just merged away: the old question is withdrawn and asked again
    _absorb(dsn, host, "정산요금은 할인을 허용한다", "정산요금", aliases=["반품요금"])
    items = _conflicts(dsn, host)
    assert len(items) == 2 and all("같은 대상인가" in i["fact"] for i in items)


def test_undo_reverts_exactly_the_logged_rows_later_merges_first(dsn, host):
    qid = _setup(dsn, host)
    before = {_frag(dsn, host, OPT)["id"]: _frag(dsn, host, OPT)["subject_id"], _frag(dsn, host, REQ)["id"]: _frag(dsn, host, REQ)["subject_id"]}
    m1 = _answer(dsn, host, qid, "same")["merge_id"]
    _absorb(dsn, host, "환불API는 우편번호를 요구하지 않는다", "환불API", aliases=["반품API"])
    (item,) = _conflicts(dsn, host)
    m2 = _answer(dsn, host, item["question_ids"][0], "same")["merge_id"]
    with pytest.raises(ValueError, match="later merges"):
        _undo(dsn, host, m1)
    assert _undo(dsn, host, m2)["undone"]
    out = _undo(dsn, host, m1)
    assert out["undone"] and out["fragments_back"] >= 1
    assert {i: _frag(dsn, host, t)["subject_id"] for i, t in ((_frag(dsn, host, OPT)["id"], OPT), (_frag(dsn, host, REQ)["id"], REQ))} == before
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        assert subject_dict.lookup(cur, host, "회수접수")["subject_id"] != subject_dict.lookup(cur, host, "반품API")["subject_id"]
        cur.execute("select count(*) from knowledge.subject where merged_into is not null and host_id=%s", (host,))
        assert cur.fetchone()[0] == 0
    with pytest.raises(ValueError, match="only a done merge"):
        _undo(dsn, host, m1)


def test_undo_refuses_when_a_moved_row_changed(dsn, host):
    qid = _setup(dsn, host)
    out = _answer(dsn, host, qid, "same")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""update knowledge.subject_alias set subject_id=(select subject_id from knowledge.subject where host_id=%s
                       and merged_into is not null) where host_id=%s and merged_by=%s and alias=%s""",
                    (host, host, out["merge_id"], subject_dict.norm(out["merged"]["from"])))
    with pytest.raises(ValueError, match="nothing was undone"):
        _undo(dsn, host, out["merge_id"])


def test_a_merge_during_the_judge_calls_fails_the_scan(dsn, host):
    qid = _setup(dsn, host)
    unit = _absorb(dsn, host, "반품API는 우편번호를 선택 항목으로 둔다", "반품API")
    fired = []

    def judge(state, texts, q, criteria=None):
        if not fired:
            fired.append(_answer(dsn, host, qid, "same"))
        return JUDGE(state, texts, q)
    with pytest.raises(ValueError, match="subject dictionary changed"):
        pg.scan_contradictions(dsn, unit, judge)
    assert fired


def test_a_merge_log_needs_the_pending_question_about_exactly_these_subjects(dsn, host):
    """astra merge r1 P0-1: a hand-made log cannot open the trigger exception."""
    qid = _setup(dsn, host)
    a, b = _frag(dsn, host, OPT), _frag(dsn, host, REQ)
    with pytest.raises(Exception, match="pending alias_conflict question"):
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""select confirmation_id from knowledge.confirmation_queue where rule_id <> 'alias_conflict'
                           limit 1""")
            other_q = cur.fetchone()[0]
            cur.execute("""insert into knowledge.subject_merge(host_id,from_subject,into_subject,confirmation_id,shown,approved_quote)
                           values (%s,%s,%s,%s,'{}','x')""", (host, a["subject_id"], b["subject_id"], other_q))
    out = _answer(dsn, host, qid, "same")
    with pytest.raises(Exception, match="not allowed here|only its state"):  # a done merge cannot be re-opened
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("update knowledge.subject_merge set state='running', txid=txid_current() where merge_id=%s",
                        (out["merge_id"],))
    with pytest.raises(Exception, match="only the merge running"):
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""insert into knowledge.subject_merge_item(merge_id,seq,tbl,row_key,old_subject,new_subject)
                           values (%s,999,'fragment','{}',%s,%s)""", (out["merge_id"], a["subject_id"], b["subject_id"]))


def test_a_survivor_that_grew_after_the_question_needs_a_new_question(dsn, host):
    """astra merge r1 P0-2: A/B shown, then C merged into B -> the A/B answer must not merge A with B+C."""
    qid = _setup(dsn, host)  # 회수접수 / 반품API
    _absorb(dsn, host, "환불API는 우편번호를 받지 않는다", "환불API")
    _absorb(dsn, host, "환불API는 우편번호를 숫자로 받는다", "환불API")
    _absorb(dsn, host, "반품API는 회수지 주소를 받는다", "반품API", aliases=["환불API"])
    other = [i["question_ids"][0] for i in _conflicts(dsn, host) if i["question_ids"][0] != qid][0]
    _answer(dsn, host, other, "same")
    with pytest.raises(ValueError, match="changed since this question was listed"):
        _answer(dsn, host, qid, "same")
    items = _conflicts(dsn, host)  # listed again about the current sets
    assert len(items) == 1 and items[0]["question_ids"][0] != qid
    assert _answer(dsn, host, items[0]["question_ids"][0], "same")["merge_id"]


def test_undo_refuses_after_a_moved_fragment_was_revised(dsn, host):
    """astra merge r1 P1-3: a fragment revised after the merge would split from its new leaves."""
    qid = _setup(dsn, host)
    out = _answer(dsn, host, qid, "same")
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        moved = REQ if out["merged"]["from"] == "반품API" else OPT  # a fragment of the merged-away subject
        cur.execute("update knowledge.fragment set revision=revision+1, text=text||'.' where host_id=%s and text=%s",
                    (host, moved))
    with pytest.raises(ValueError, match="nothing was undone"):
        _undo(dsn, host, out["merge_id"])


def test_a_digestion_judged_before_a_merge_is_rechecked(dsn, host):
    """astra merge r1 P1-5: the subject generation seen when judging must still hold at the commit."""
    from test_store_pg import fixture, judgement
    qid = _setup(dsn, host)
    body = judgement(host, text="반품API는 우편번호를 다섯 자리로 받는다")
    body["facts"][0]["subject"] = "반품API"
    e = pg.register(dsn, body)
    pg.batch(dsn, 1, {e["entry_id"]: [fixture(text=body["facts"][0]["fact"])]}, entry_ids=[e["entry_id"]])
    pg.complete(dsn, body["work_unit_id"])
    preview = pg.digest(dsn, body["work_unit_id"], False)
    fx = {rid: {**fixture(text=body["facts"][0]["fact"]), "subject_generation_seen": 0} for rid in preview["receipt_ids"]}
    _answer(dsn, host, qid, "same")
    out = pg.digest(dsn, body["work_unit_id"], True, fx)
    assert out["status"] == "needs_recheck" and "subject dictionary changed" in out["why"]


def test_an_item_outside_the_approved_pair_is_refused(dsn, host):
    """astra merge r2 P1-3: a running A/B merge cannot log (and so allow) a C -> D move."""
    import subject_merge
    qid = _setup(dsn, host)
    _absorb(dsn, host, "정산API는 금액을 정수로 받는다", "정산API")
    _absorb(dsn, host, "지급API는 금액을 정수로 받는다", "지급API")
    c, d = _frag(dsn, host, "정산API는 금액을 정수로 받는다"), _frag(dsn, host, "지급API는 금액을 정수로 받는다")
    a, b = _frag(dsn, host, OPT), _frag(dsn, host, REQ)
    with pytest.raises(Exception, match="its own from -> into"):
        with pg.connect(dsn) as conn, conn.cursor() as cur:
            subject_merge.lock_host(cur, host, exclusive=True)
            cur.execute("""insert into knowledge.subject_merge(host_id,from_subject,into_subject,confirmation_id,shown,approved_quote)
                           values (%s,%s,%s,%s,'{}','응 같아') returning merge_id::text""",
                        (host, a["subject_id"], b["subject_id"], qid))
            mid = cur.fetchone()[0]
            cur.execute("""insert into knowledge.subject_merge_item(merge_id,seq,tbl,row_key,old_subject,new_subject)
                           values (%s,0,'fragment',%s,%s,%s)""",
                        (mid, '{"id": "%s"}' % c["id"], c["subject_id"], d["subject_id"]))


def _plain(dsn, host, like_text, subject_text, seq, text):
    """An old fragment without a stored form (pre-structure) of the subject of subject_text."""
    with pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""insert into knowledge.fragment(id,host_id,domain,seq,alias,kind,text,subject_id,source)
                       select gen_random_uuid(), f.host_id, f.domain, %s, f.domain || '-' || %s, f.kind, %s, s.subject_id, f.source
                       from knowledge.fragment f, knowledge.fragment s where f.host_id=%s and f.text=%s
                       and s.host_id=%s and s.text=%s returning id::text""",
                    (seq, seq, text, host, like_text, host, subject_text))
        return cur.fetchone()[0]


def test_undo_refuses_after_structure_was_filled(dsn, host):
    """astra merge r2 P1-1: a fragment structured after the merge (same revision, new leaves) blocks the undo."""
    qid = _setup(dsn, host)
    _plain(dsn, host, OPT, OPT, 901, "회수접수는 회수지를 받는다")
    _plain(dsn, host, OPT, OPT, 902, "회수접수는 회수 일자를 받는다")
    old = _plain(dsn, host, OPT, REQ, 903, "반품API는 반품 사유를 받는다")  # merged away (fewer fragments)
    out = _answer(dsn, host, qid, "same")
    assert out["merged"]["from"] == "반품API"
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # backfill fills the structure in place (0011 exemption)
        import json
        import fact_form
        cur.execute("update knowledge.fragment set form=%s::jsonb where id=%s",
                    (json.dumps(fact_form.parse("반품API는 반품 사유를 받는다"), ensure_ascii=False), old))
    with pytest.raises(ValueError, match="nothing was undone"):
        _undo(dsn, host, out["merge_id"])


def test_a_partial_digestion_judged_before_a_merge_is_judged_again_and_finishes(dsn, host):
    """astra merge r2 P1-2 / r3 P1-1: partial save -> merge -> the same packet is judged again (a new receipt under the new
    generation, not the old one) -> the next pass finishes."""
    import digest_driver
    from test_store_pg import fixture, judgement
    qid = _setup(dsn, host)
    body = judgement(host, text="반품API는 우편번호를 숫자로 받는다")
    body["facts"].append({**body["facts"][0], "fact": "반품API는 주소를 문자로 받는다",
                          "evidence_refs": [{"type": "user_utterance", "locator": "test/local", "quote": "반품API는 주소를 문자로 받는다"}]})
    for f in body["facts"]:
        f["subject"] = "반품API"
    e = pg.register(dsn, body)
    pg.batch(dsn, 1, {e["entry_id"]: [fixture(text=f["fact"]) for f in body["facts"]]}, entry_ids=[e["entry_id"]])
    pg.complete(dsn, body["work_unit_id"])
    calls = []
    judge = lambda p: (calls.append(p["state"]["candidate_fact"]) or
                       {"answers": fixture(text=p["state"]["candidate_fact"])["answers"]})
    assert digest_driver.run_digestion(dsn, body["work_unit_id"], judge, budget=1)["status"] == "partial"
    _answer(dsn, host, qid, "same")  # generation 0 -> 1
    n = len(calls)
    out = digest_driver.run_digestion(dsn, body["work_unit_id"], judge, budget=1)
    assert out["status"] == "partial" and len(calls) == n + 1  # the saved generation-0 judgement is not reused
    out = digest_driver.run_digestion(dsn, body["work_unit_id"], judge, budget=1)
    assert out["status"] in ("absorbed", "processed"), out  # generation-1 judgements of both facts are reused
    assert len(calls) == n + 2


def test_a_fixture_without_a_generation_is_rechecked(dsn, host):
    """astra merge r3 P1-2: the final apply requires the generation the judgement was made under."""
    from test_store_pg import fixture, judgement
    _setup(dsn, host)
    body = judgement(host, text="반품API는 우편번호를 두 줄로 받는다")
    body["facts"][0]["subject"] = "반품API"
    e = pg.register(dsn, body)
    pg.batch(dsn, 1, {e["entry_id"]: [fixture(text=body["facts"][0]["fact"])]}, entry_ids=[e["entry_id"]])
    pg.complete(dsn, body["work_unit_id"])
    rid = pg.digest(dsn, body["work_unit_id"], False)["receipt_ids"][0]
    fx = fixture(text=body["facts"][0]["fact"])
    fx.pop("subject_generation_seen")
    assert pg.digest(dsn, body["work_unit_id"], True, {rid: fx})["status"] == "needs_recheck"


def test_a_rescan_compares_a_same_subject_fragment_without_form(dsn, host):
    """astra merge r2 P1-5: a pre-structure fragment of the joined subject is compared by its whole text."""
    qid = _setup(dsn, host)
    _answer(dsn, host, qid, "same")
    survivor = _frag(dsn, host, OPT)["subject_id"]
    with pg.connect(dsn) as conn, conn.cursor() as cur:  # an old fragment (no form, no leaves) of the same subject
        cur.execute("""insert into knowledge.fragment(id,host_id,domain,seq,alias,kind,text,subject_id,source)
                       select gen_random_uuid(), host_id, domain, 900, domain || '-900', kind, '반품API는 우편번호 없이도 접수한다',
                       %s, source from knowledge.fragment where host_id=%s and text=%s""", (survivor, host, REQ))
    seen = []

    def judge(state, texts, q, criteria=None):
        seen.extend(texts)
        return JUDGE(state, texts, q)
    pg.rescan_fragments(dsn, judge, limit=500)  # the shared test DB holds other tests' queued rescans too
    assert "반품API는 우편번호 없이도 접수한다" in seen
