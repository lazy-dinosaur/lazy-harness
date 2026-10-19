"""Guard-first regression for normal source-hint review after callback mutations."""
import json
import socket
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

BLOCKED = {name: 0 for name in ("connect", "connect_ex", "create_connection", "getaddrinfo", "popen", "driver", "model")}
def _deny(name):
    def deny(*_args, **_kwargs):
        BLOCKED[name] += 1
        raise AssertionError("offline hint guard blocked " + name)
    return deny
socket.socket.connect = _deny("connect")
socket.socket.connect_ex = _deny("connect_ex")
socket.create_connection = _deny("create_connection")
socket.getaddrinfo = _deny("getaddrinfo")
subprocess.Popen = _deny("popen")

import store_pg
import source_review

store_pg.driver.connect = _deny("driver")


class _DB:
    def __init__(self, rows):
        self.rows = rows
    def cursor(self): return _Cursor(self.rows)
    def __enter__(self): return self
    def __exit__(self, *_args): return False

class _Cursor:
    def __init__(self, rows): self.rows = rows; self.result = []
    def __enter__(self): return self
    def __exit__(self, *_args): return False
    def execute(self, sql, _params):
        if "from knowledge.confirmation_queue q" in sql:
            self.result = [(701, "pilot-host", "canon_exception", json.dumps({"alias":"A", "text":"Claim A", "with":"B", "with_text":"Claim B"}))]
        elif "select id::text,revision,text,source,active" in sql:
            self.result = [(r["id"], r["revision"], r["text"], r["source"], r["active"])
                           for r in self.rows]
        else:
            self.result = [(r["id"], r["alias"], r["revision"], r["text"], r["source"], r["active"])
                           for r in self.rows]
    def fetchall(self): return list(self.result)


import unittest

class HintRebindOffline(unittest.TestCase):
    def setUp(self):
        self.before = BLOCKED.copy()
        refs = [{"type":"official_doc", "locator":"source.md:L1", "quote":"The source documents both scoped claims."}]
        self.rows = [
            {"id":"frag-a", "alias":"A", "revision":1, "text":"Claim A", "source":{"evidence_refs":refs}, "active":True},
            {"id":"frag-b", "alias":"B", "revision":1, "text":"Claim B", "source":{"evidence_refs":refs}, "active":True},
        ]
    def execute(self, callback, *, scope=None):
        writer_calls = []
        def connect(_dsn): return _DB(self.rows)
        with tempfile.TemporaryDirectory() as root, patch.object(store_pg, "connect", connect), \
             patch.object(store_pg, "resolve_source_hint", lambda *_a: writer_calls.append(True) or {"status":"resolved", "hint_receipt_id":"h1"}):
            Path(root, "source.md").write_text("The source documents both scoped claims.\n", encoding="utf-8")
            def reviewer(_host, kind, left, right, question_id=None):
                return callback(root, kind, left, right, question_id)
            result = store_pg.source_hint_pending("offline", reviewer, limit=1, host="pilot-host", execution_scope=scope)
        return result, writer_calls
    def test_fresh_receipt_for_citation_only_revised_current_pair_is_admitted(self):
        def callback(root, kind, left, right, qid):
            for row in self.rows:
                row["revision"] += 1
                row["source"]["evidence_refs"] = list(row["source"]["evidence_refs"])
            current = [dict(r) for r in self.rows]
            return source_review.review_hint_pair(kind, current[0], current[1], source_review.SourceProvider(root),
                lambda *_a, **_k: [{"choice":"complementary", "probabilities":{"complementary":0.99}}], question_id=qid)
        result, writes = self.execute(callback)
        assert result["resolved"] == 1 and result["attempted"][0]["status"] == "resolved", result
        assert writes == [True]
        assert BLOCKED == self.before
    def test_restricted_hint_resolves_corrected_current_pair_by_lineage_ids(self):
        self.rows[0].update(revision=2, alias="A-corrected", text="Corrected claim A")
        self.rows[1].update(revision=3, alias="B-corrected", text="Corrected claim B")
        class Scope:
            def pair_for_question(self, qid): return ("frag-a", "frag-b") if str(qid) == "701" else None
            def revalidate_current_question(self, *_args): return True
        def callback(root, kind, left, right, qid):
            return source_review.review_hint_pair(kind, left, right, source_review.SourceProvider(root),
                lambda *_a, **_k: [{"choice":"complementary", "probabilities":{"complementary":0.99}}], question_id=qid)
        result, writes = self.execute(callback, scope=Scope())
        assert result["resolved"] == 1 and writes == [True], result
        assert BLOCKED == self.before
    def test_semantic_mutation_with_old_receipt_is_rejected(self):
        old = {}
        def callback(root, kind, left, right, qid):
            old.update(source_review.review_hint_pair(kind, left, right, source_review.SourceProvider(root),
                lambda *_a, **_k: [{"choice":"complementary", "probabilities":{"complementary":0.99}}], question_id=qid))
            self.rows[0]["revision"] += 1
            self.rows[0]["text"] = "Changed semantic claim"
            return old
        result, writes = self.execute(callback)
        assert result["evidence_needed"] == 1 and result["resolved"] == 0, result
        assert writes == [] and self.rows[0]["text"] == "Changed semantic claim"
        assert BLOCKED == self.before
    def test_callback_pair_swap_is_rejected_by_scope_before_writer(self):
        class Scope:
            def revalidate_current_question(self, _dsn, _qid, _host, _fragments):
                raise ValueError("callback fragment pair is outside scope")
        def callback(root, kind, left, right, qid):
            return source_review.review_hint_pair(kind, left, right, source_review.SourceProvider(root),
                lambda *_a, **_k: [{"choice":"complementary", "probabilities":{"complementary":0.99}}], question_id=qid)
        result, writes = self.execute(callback, scope=Scope())
        assert result["failed"] == 1 and writes == [], result
        assert BLOCKED == self.before

if __name__ == "__main__":
    import unittest
    unittest.main()
