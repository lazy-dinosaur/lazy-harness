"""Guard-first offline tests for the normal source-required poller gate."""
import json
import socket
import subprocess
import unittest
from unittest.mock import patch

BLOCKED = {name: 0 for name in ("connect", "connect_ex", "create_connection", "getaddrinfo", "popen", "driver", "model")}

def _deny(name):
    def deny(*_args, **_kwargs):
        BLOCKED[name] += 1
        raise AssertionError("offline guard blocked " + name)
    return deny

socket.socket.connect = _deny("connect")
socket.socket.connect_ex = _deny("connect_ex")
socket.create_connection = _deny("create_connection")
socket.getaddrinfo = _deny("getaddrinfo")
subprocess.Popen = _deny("popen")

import poller
import runtime_db
import store_pg
import capture_audit

store_pg.driver.connect = _deny("driver")
capture_audit.make_judge = _deny("model")


class SourceReviewGateOffline(unittest.TestCase):
    def setUp(self):
        self.before = BLOCKED.copy()

    def test_guarded_tick_routes_pending_questions_through_source_review_gate(self):
        dsn = "postgresql://u:p@127.0.0.1:33490/postgres"
        context = runtime_db.bind_runtime_db(dsn, provenance="explicit-test")
        events = []
        reviewer = lambda *_a, **_k: {}
        reviewer.runtime_db = context

        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *_a): return False
            def execute(self, *_a, **_k): pass
            def fetchone(self): return (True,)
            def fetchall(self): return []
        class Connection:
            autocommit = False
            def cursor(self): return Cursor()
            def __enter__(self): return self
            def __exit__(self, *_a): return False
            def close(self): pass
        patches = [
            (poller.store_pg.driver, "connect", lambda *_a: Connection()),
            (poller, "_candidates", lambda *_a: ([], [])),
            (poller, "_prune", lambda *_a: None),
            (poller.store_pg, "unscanned", lambda *_a: []),
            (poller.store_pg, "recheck_contradictions", lambda *_a, **kw:
                events.append(("recheck", kw)) or {"rechecked": 0, "failed": 0}),
            (poller.store_pg, "source_review_pending", lambda *_a, **kw:
                events.append(("source_review", kw)) or {"attempted": []}),
            (poller.store_pg, "rescan_fragments", lambda *_a, **_k: {"rescanned": 0, "failed": 0}),
            (poller.store_pg, "source_hint_pending", lambda *_a, **_k: {"attempted": []}),
            (poller, "_runnable_scans", lambda *_a: []),
            (poller, "_pending_hosts", lambda *_a: []),
        ]
        originals = [(obj, name, getattr(obj, name)) for obj, name, _ in patches]
        try:
            for obj, name, replacement in patches:
                setattr(obj, name, replacement)
            result = poller.tick(dsn, lambda *_a: [], contra_judge=lambda *_a: [],
                source_reviewer=reviewer, require_source_review=True, runtime_db=context,
                max_units=1, window=1, state="offline-unused-state")
        finally:
            for obj, name, original in originals:
                setattr(obj, name, original)
        self.assertEqual([event[0] for event in events[:2]], ["recheck", "source_review"])
        self.assertTrue(events[0][1].get("source_review_required"), events)
        self.assertIn("source_review", result)
        self.assertEqual(BLOCKED, self.before)

    def test_existing_source_queue_closes_only_with_current_source_receipt(self):
        import json
        import subject_merge
        dsn, host = "offline", "pilot-host"
        left = {"id": "left", "revision": 3, "text": "claim A", "source": {"evidence_refs": []}, "active": True}
        right = {"id": "right", "revision": 5, "text": "claim B", "source": {"evidence_refs": []}, "active": True}
        reason = {"id": "left", "rev": 3, "text": "claim A", "alias": "a",
                  "with_id": "right", "with_rev": 5, "with_text": "claim B", "with": "b"}
        reason_text = json.dumps(reason)
        class Cursor:
            rowcount = 0
            def __enter__(self): return self
            def __exit__(self, *_a): return False
            def execute(self, query, _params):
                self.query = query
                if query.startswith("update knowledge.confirmation_queue set status='answered'"):
                    updates.append(query)
                    self.rowcount = 1
            def fetchall(self):
                if "q.confirmation_id,e.host_id,q.reason" in self.query:
                    return [(73, host, reason_text)]
                if "select id::text,revision,text,source,active from knowledge.fragment" in self.query:
                    return [(left["id"], left["revision"], left["text"], left["source"], True),
                            (right["id"], right["revision"], right["text"], right["source"], True)]
                return []
            def fetchone(self):
                if "select q.reason,q.status::text,q.resolution" in self.query:
                    return (reason_text, "pending", "open")
                return None
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *_a): return False
            def cursor(self): return Cursor()
        receipt_writes, updates, verdict, revision_delta = [], [], ["compatible"], [0]
        def reviewer(_host, current_left, current_right, question_id=None):
            return {"status": "reviewed", "left_id": current_left["id"],
                "left_revision": current_left["revision"], "right_id": current_right["id"],
                "right_revision": current_right["revision"] + revision_delta[0], "verdict": verdict[0],
                "origin": "live-root", "question_id": question_id}
        with (patch.object(store_pg, "connect", lambda _dsn: Connection()),
              patch.object(store_pg, "record_source_review_receipt", lambda *_a: receipt_writes.append(True) or
                           {"status": "recorded", "receipt_id": "fresh-receipt"}),
              patch.object(subject_merge, "lock_host", lambda *_a, **_k: None)):
            result = store_pg.source_review_pending(dsn, reviewer, host=host, question_ids=[73])
        self.assertEqual((result["reviewed"], result["resolved"]), (1, 1))
        self.assertEqual(result["attempted"][0]["receipt_id"], "fresh-receipt")
        self.assertEqual(receipt_writes, [True])
        verdict[0] = "genuine_conflict"
        with (patch.object(store_pg, "connect", lambda _dsn: Connection()),
              patch.object(store_pg, "record_source_review_receipt", lambda *_a: {"status": "recorded", "receipt_id": "conflict-receipt"}),
              patch.object(subject_merge, "lock_host", lambda *_a, **_k: None)):
            conflict = store_pg.source_review_pending(dsn, reviewer, host=host, question_ids=[73])
        self.assertEqual(conflict["verified_conflicts"], {"73": "conflict-receipt"})
        self.assertEqual(len(updates), 1)  # only the positive compatible receipt closed the question
        verdict[0] = "compatible"
        revision_delta[0] = 1
        writes_before_stale = len(receipt_writes)
        with (patch.object(store_pg, "connect", lambda _dsn: Connection()),
              patch.object(store_pg, "record_source_review_receipt", lambda *_a: receipt_writes.append(True)),
              patch.object(subject_merge, "lock_host", lambda *_a, **_k: None)):
            stale = store_pg.source_review_pending(dsn, reviewer, host=host, question_ids=[73])
        self.assertEqual(stale["evidence_needed"], 1)
        self.assertEqual(len(receipt_writes), writes_before_stale)
        self.assertEqual(BLOCKED, self.before)

    def test_source_required_tick_without_contradiction_judge_fails_before_connect(self):
        dsn = "postgresql://u:p@127.0.0.1:33490/postgres"
        context = runtime_db.bind_runtime_db(dsn, provenance="explicit-test")
        reviewer = lambda *_a, **_k: {}
        reviewer.runtime_db = context
        with self.assertRaisesRegex(ValueError, "contradiction judge"):
            poller.tick(dsn, lambda *_a: [], source_reviewer=reviewer,
                        require_source_review=True, runtime_db=context, state="offline-unused-state")
        self.assertEqual(BLOCKED, self.before)

    def test_recheck_sql_excludes_pending_open_only_in_guarded_mode(self):
        class Cursor:
            def __init__(self, queries): self.queries = queries
            def __enter__(self): return self
            def __exit__(self, *_a): return False
            def execute(self, query, _params): self.queries.append(query)
            def fetchall(self): return []
        class Connection:
            def __init__(self, queries): self.queries = queries
            def __enter__(self): return self
            def __exit__(self, *_a): return False
            def cursor(self): return Cursor(self.queries)
        queries = []
        with patch.object(store_pg, "connect", lambda _dsn: Connection(queries)):
            store_pg.recheck_contradictions("offline", lambda *_a: [], source_review_required=True)
            store_pg.recheck_contradictions("offline", lambda *_a: [])
        self.assertIn("not (q.status='pending' and q.resolution='open')", queries[0])
        self.assertIn("knowledge.source_review_receipt", queries[0])
        self.assertIn("sr.left_revision=sl.revision", queries[0])
        self.assertIn("q.confirmation_id=any(%s::bigint[])", queries[0])
        self.assertNotIn("knowledge.source_review_receipt", queries[1])
        self.assertNotIn("not (q.status='pending' and q.resolution='open')", queries[1])
        self.assertEqual(BLOCKED, self.before)

    def test_historical_answer_without_current_source_receipt_is_review_eligible_and_preserved(self):
        reason = json.dumps({"id":"left","rev":1,"alias":"a","text":"old A",
                             "with_id":"right","with_rev":1,"with":"b","with_text":"old B"})
        left={"id":"left","revision":2,"text":"current A","source":{"evidence_refs":[]},"active":True,"alias":"a"}
        right={"id":"right","revision":1,"text":"current B","source":{"evidence_refs":[]},"active":True,"alias":"b"}
        class Cursor:
            def __init__(self): self.query=""
            def __enter__(self): return self
            def __exit__(self,*_a): return False
            def execute(self,query,_params): self.query=query
            def fetchall(self):
                if "select q.confirmation_id,q.entry_id::text" in self.query:
                    return [(403,"entry",0,"pilot",reason)]
                if "select id::text,revision,text,source,active,alias" in self.query:
                    return [("left",2,"current A",left["source"],True,"a"),
                            ("right",1,"current B",right["source"],True,"b")]
                return []
        class Connection:
            def __enter__(self): return self
            def __exit__(self,*_a): return False
            def cursor(self): return Cursor()
        calls=[]
        def reviewer(_host,a,b,question_id=None):
            calls.append((a["revision"],b["revision"],question_id))
            return {"status":"reviewed","left_id":"left","left_revision":2,"right_id":"right",
                    "right_revision":1,"verdict":"compatible"}
        reviewer.accepts_question_id=True
        with (patch.object(store_pg,"connect",lambda _dsn:Connection()),
              patch.object(store_pg,"record_source_review_receipt",lambda *_a:{"status":"recorded","receipt_id":"fresh"})):
            result=store_pg.source_review_historical_pending("offline",reviewer,host="pilot",limit=1)
        self.assertEqual(calls,[(2,1,403)])
        self.assertEqual(result["reviewed"],1)
        self.assertEqual(result["attempted"][0]["receipt_id"],"fresh")
        self.assertEqual(BLOCKED,self.before)

    def test_historical_genuine_conflict_creates_followup_without_rewriting_answer(self):
        reason=json.dumps({"id":"left","rev":1,"alias":"a","text":"old A",
                           "with_id":"right","with_rev":1,"with":"b","with_text":"old B"})
        left={"id":"left","revision":2,"text":"current A","source":{"evidence_refs":[]},"active":True,"alias":"a"}
        right={"id":"right","revision":1,"text":"current B","source":{"evidence_refs":[]},"active":True,"alias":"b"}
        statements=[]
        class Cursor:
            def __init__(self): self.query=""
            def __enter__(self): return self
            def __exit__(self,*_a): return False
            def execute(self,query,_params): self.query=query; statements.append(query)
            def fetchall(self):
                if "select q.confirmation_id,q.entry_id::text" in self.query:
                    return [(403,"entry",0,"pilot",reason)]
                if "select id::text,revision,text,source,active,alias" in self.query:
                    return [("left",2,"current A",left["source"],True,"a"),
                            ("right",1,"current B",right["source"],True,"b")]
                if "select id::text,revision,text,active from knowledge.fragment" in self.query:
                    return [("left",2,"current A",True),("right",1,"current B",True)]
                return []
            def fetchone(self):
                if "select q.status::text,q.resolution,q.reason" in self.query:
                    return ("answered","resolved",reason)
                if "returning confirmation_id" in self.query: return (901,)
                return None
        class Connection:
            def __enter__(self): return self
            def __exit__(self,*_a): return False
            def cursor(self): return Cursor()
        reviewer=lambda *_a,**_k:{"status":"reviewed","left_id":"left","left_revision":2,
            "right_id":"right","right_revision":1,"verdict":"genuine_conflict"}
        with (patch.object(store_pg,"connect",lambda _dsn:Connection()),
              patch.object(store_pg,"record_source_review_receipt",lambda *_a:{"status":"recorded","receipt_id":"fresh-conflict"}),
              patch("subject_merge.lock_host",lambda *_a,**_k:None)):
            result=store_pg.source_review_historical_pending("offline",reviewer,host="pilot",limit=1)
        self.assertEqual(result["reopened"],1)
        self.assertEqual(result["attempted"][0]["followup_question_id"],901)
        self.assertTrue(any("insert into knowledge.confirmation_queue" in q for q in statements))
        self.assertFalse(any("update knowledge.confirmation_queue" in q for q in statements))
        self.assertEqual(BLOCKED,self.before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
