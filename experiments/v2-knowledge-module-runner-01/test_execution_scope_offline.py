"""Guard-first offline proof for immutable normal-poller scope propagation."""
import hashlib
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

BLOCKED = {name: 0 for name in ("connect", "connect_ex", "create_connection", "getaddrinfo", "popen", "driver", "model")}

def _deny(name):
    def deny(*_args, **_kwargs):
        BLOCKED[name] += 1
        raise AssertionError("offline scope guard blocked " + name)
    return deny

socket.socket.connect = _deny("connect")
socket.socket.connect_ex = _deny("connect_ex")
socket.create_connection = _deny("create_connection")
socket.getaddrinfo = _deny("getaddrinfo")
subprocess.Popen = _deny("popen")

import config
import poller
import runtime_db
import store_pg
import source_evidence
from execution_scope import ExecutionScope, ExecutionScopeError, VerifiedScopeDependency

store_pg.driver.connect = _deny("driver")


class ExecutionScopeOffline(unittest.TestCase):
    def setUp(self):
        self.before = BLOCKED.copy()

    def scope(self):
        dsn = "postgresql://u:p@127.0.0.1:33490/postgres"
        endpoint = runtime_db.bind_runtime_db(dsn, provenance="explicit-test").endpoint
        dataset_fp = hashlib.sha256(__import__("json").dumps(endpoint, separators=(",", ":")).encode()).hexdigest()
        return ExecutionScope("pilot-host", dataset_fp, frozenset({"101"}), frozenset({"frag-a", "frag-b"}),
            frozenset(), frozenset(), frozenset({"subject-a"}), "a" * 64, "b" * 64,
            (VerifiedScopeDependency._from_protected_receipt("101", "102", {
                "status": "applied", "parent_id": "101", "child_id": "102", "receipt_id": "r1",
                "source_fingerprint": "d" * 64, "cas_verified": True}),
             VerifiedScopeDependency._from_protected_receipt("frag-a", "frag-c", {
                "status": "applied", "parent_id": "frag-a", "child_id": "frag-c", "receipt_id": "r2",
                "source_fingerprint": "e" * 64, "cas_verified": True})),
            (("101", frozenset({"frag-a", "frag-b"})),), (("101", "c" * 64),))

    def test_root_and_verified_child_membership_is_immutable_and_exact(self):
        scope = self.scope()
        self.assertTrue(scope.admits_question(101))
        self.assertTrue(scope.admits_question("102"))
        self.assertFalse(scope.admits_question("120"))
        self.assertTrue(scope.admits_fragment("frag-c"))
        self.assertFalse(scope.admits_fragment("arbitrary-fragment"))
        with self.assertRaises((AttributeError, TypeError)):
            scope.namespace = "other-host"
        with self.assertRaises(ExecutionScopeError):
            ExecutionScope("pilot-host", "c" * 64, frozenset(), frozenset({"f"}),
                frozenset(), frozenset(), frozenset(), "a" * 64, "b" * 64)
        with self.assertRaises(ExecutionScopeError):
            VerifiedScopeDependency("101", "999", "unverified", "d" * 64)
        with self.assertRaises(ExecutionScopeError):
            VerifiedScopeDependency._from_protected_receipt("101", "999", {"status": "applied"})
        self.assertEqual(BLOCKED, self.before)

    def test_actual_tick_passes_scope_to_each_queue_phase_and_never_selects_siblings(self):
        dsn = "postgresql://u:p@127.0.0.1:33490/postgres"
        context = runtime_db.bind_runtime_db(dsn, provenance="explicit-test")
        scope = self.scope()
        reviewer = lambda *_a, **_k: {}
        reviewer.runtime_db = context
        reviewer.host_id = scope.namespace
        reviewer.review_hint = lambda *_a, **_k: {}
        reviewer.execution_scope = scope
        events = []

        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *_a): return False
            def execute(self, *_a, **_k): pass
            def fetchone(self): return (True,)
        class Connection:
            autocommit = False
            def cursor(self): return Cursor()
            def __enter__(self): return self
            def __exit__(self, *_a): return False
            def close(self): pass

        patches = [
            (poller.store_pg.driver, "connect", lambda *_a: Connection()),
            (poller, "_candidates", lambda _dsn, got: events.append(("candidates", got)) or ([], [])),
            (poller, "_prune", lambda *_a: None),
            (poller, "_save", lambda *_a: None),
            (poller.store_pg, "recheck_contradictions", lambda *_a, **kw:
                events.append(("recheck", kw)) or {"rechecked": 0, "failed": 0}),
            (poller.store_pg, "source_review_historical_pending", lambda *_a, **kw:
                events.append(("historical", kw)) or {"attempted": []}),
            (poller.store_pg, "source_review_pending", lambda *_a, **kw:
                events.append(("review", kw)) or {"attempted": []}),
            (poller.store_pg, "source_hint_pending", lambda *_a, **kw:
                events.append(("hint", kw)) or {"attempted": []}),
            (poller, "_runnable_scans", lambda *_a: self.fail("scoped queue must not enumerate global scans")),
            (poller.store_pg, "backfill_embeddings", lambda *_a, **kw:
                events.append(("fragment_embedding", kw)) or 0),
            (poller.store_pg, "backfill_subject_embeddings", lambda *_a, **kw:
                events.append(("subject_embedding", kw)) or 0),
        ]
        originals = [(obj, name, getattr(obj, name)) for obj, name, _ in patches]
        try:
            for obj, name, replacement in patches:
                setattr(obj, name, replacement)
            result = poller.tick(dsn, lambda *_a: self.fail("model called"), contra_judge=lambda *_a: [],
                source_reviewer=reviewer, require_source_review=True, runtime_db=context,
                execution_scope=scope, max_units=1, window=1, state="offline-scope-state.json")
        finally:
            for obj, name, original in originals:
                setattr(obj, name, original)
        by_name = {name: kw for name, kw in events if isinstance(kw, dict)}
        self.assertIs(events[0][1], scope)
        for name in ("recheck", "historical", "review", "hint"):
            self.assertEqual(by_name[name]["host"], scope.namespace)
            self.assertEqual(set(by_name[name]["question_ids"]), {"101"})
        self.assertNotIn("rescan", by_name)  # no cohort-authorized neighbor dependency exists
        self.assertEqual(by_name["fragment_embedding"]["fragment_ids"], ["frag-a", "frag-b"])
        self.assertEqual(by_name["subject_embedding"]["subject_ids"], ["subject-a"])
        self.assertEqual(result["units"], 0)
        self.assertEqual(result["entries"], 0)
        self.assertEqual(BLOCKED, self.before)

    def test_source_reviewer_rejects_outside_question_before_model_or_source_io(self):
        dsn = "postgresql://u:p@127.0.0.1:33490/postgres"
        context = runtime_db.bind_runtime_db(dsn, provenance="explicit-test")
        original_scope = self.scope()
        scope = ExecutionScope(original_scope.namespace, original_scope.dataset_fingerprint,
            original_scope.root_question_ids, original_scope.root_fragment_ids,
            original_scope.root_work_unit_ids, original_scope.root_entry_ids,
            original_scope.root_subject_ids, original_scope.root_baseline_fingerprint,
            hashlib.sha256(b"manifest").hexdigest(), original_scope.dependencies,
            original_scope.question_fragment_pairs, original_scope.question_fingerprints)
        model_calls = []
        with tempfile.TemporaryDirectory() as root, patch.object(config, "source_authority", lambda *_a, **_k:
                {"root": root, "import_manifest": "manifest.json", "host_id": "pilot-host"}), \
             patch.object(source_evidence, "load_import_bindings", lambda *_a: {}):
            from pathlib import Path
            (Path(root) / "manifest.json").write_bytes(b"manifest")
            reviewer = poller.configured_source_reviewer({"default_host": "pilot-host", "db_url": dsn}, context,
                root_override=root, host_override="pilot-host", execution_scope=scope,
                verifier=lambda *_a, **_k: model_calls.append(True))
            left = {"id": "frag-a", "revision": 1}
            right = {"id": "frag-b", "revision": 1}
            with self.assertRaisesRegex(ValueError, "outside the immutable execution scope"):
                reviewer("pilot-host", left, right, question_id=120)
            with self.assertRaisesRegex(ValueError, "outside the immutable execution scope"):
                reviewer("pilot-host", left, right, question_id=102)
            with self.assertRaisesRegex(ValueError, "outside the immutable execution scope"):
                reviewer("pilot-host", {"id": "frag-a", "revision": 1},
                    {"id": "frag-c", "revision": 1}, question_id=101)
        self.assertEqual(model_calls, [])
        self.assertEqual(BLOCKED, self.before)

    def test_source_hint_pair_is_reloaded_after_a_reviewer_revision(self):
        queries = []
        class Cursor:
            def __enter__(self): return self
            def __exit__(self, *_a): return False
            def execute(self, query, params):
                queries.append((query, params))
            def fetchall(self):
                return [("frag-a", 2, "claim A", {"evidence_refs": []}, True),
                        ("frag-b", 3, "claim B", {"evidence_refs": []}, True)]
        class Connection:
            def __enter__(self): return self
            def __exit__(self, *_a): return False
            def cursor(self): return Cursor()
        with patch.object(store_pg, "connect", lambda _dsn: Connection()):
            current = store_pg._current_source_hint_pair("offline", "pilot-host", "frag-a", "frag-b")
        self.assertEqual((current[0]["revision"], current[1]["revision"]), (2, 3))
        self.assertIn("id=any(%s::uuid[])", queries[0][0])
        self.assertIn("_current_source_hint_pair", __import__("inspect").getsource(store_pg.source_hint_pending))
        self.assertEqual(BLOCKED, self.before)

    def test_missing_or_mutated_scope_stops_before_connection(self):
        dsn = "postgresql://u:p@127.0.0.1:33490/postgres"
        context = runtime_db.bind_runtime_db(dsn, provenance="explicit-test")
        reviewer = lambda *_a, **_k: {}
        reviewer.runtime_db = context
        reviewer.host_id = "pilot-host"
        reviewer.execution_scope = None
        with self.assertRaisesRegex(ValueError, "immutable validated ExecutionScope"):
            poller.tick(dsn, lambda *_a: self.fail("model called"), source_reviewer=reviewer,
                require_source_review=True, runtime_db=context, execution_scope=object(), state="unused")
        self.assertEqual(BLOCKED, self.before)


if __name__ == "__main__":
    unittest.main()
