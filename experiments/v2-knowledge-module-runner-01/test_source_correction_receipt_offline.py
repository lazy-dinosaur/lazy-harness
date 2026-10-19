"""Guard-first standalone offline regression for store_pg.apply_source_correction receipts.

Run directly with Python. It stubs the PostgreSQL driver, connection, and cursor before
project imports and never uses pytest/conftest, Docker, network, subprocess, or a model.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import socket
import subprocess
import sys
import types
import unittest
from pathlib import Path

BLOCKED = {name: 0 for name in (
    "socket_connect", "socket_connect_ex", "create_connection", "getaddrinfo", "popen", "driver_connect",
)}


def _blocked(name):
    def deny(*_args, **_kwargs):
        BLOCKED[name] += 1
        raise AssertionError("offline guard blocked " + name)
    return deny


# Install transport/process/driver guards before importing project modules.
socket.socket.connect = _blocked("socket_connect")
socket.socket.connect_ex = _blocked("socket_connect_ex")
socket.create_connection = _blocked("create_connection")
socket.getaddrinfo = _blocked("getaddrinfo")
subprocess.Popen = _blocked("popen")

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# store_pg imports these at module import. Provide inert modules for unused paths so import
# cannot initialize model/provider code or a real PostgreSQL driver.
sys.modules.setdefault("psycopg", types.SimpleNamespace(connect=_blocked("driver_connect")))
sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=_blocked("driver_connect")))
sys.modules.setdefault("embed", types.SimpleNamespace(
    MODEL_ID="offline-embed", EmbeddingUnavailable=RuntimeError,
    encode_query=lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("model must not run")),
    encode_passages=lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("model must not run")),
))
sys.modules.setdefault("policy", types.SimpleNamespace(DEFAULT_POLICY={}))
sys.modules.setdefault("runner", types.SimpleNamespace())
sys.modules.setdefault("store", types.SimpleNamespace())
sys.modules.setdefault("subject_merge", types.SimpleNamespace(lock_host=lambda *_a, **_k: None))

source_correction = importlib.import_module("source_correction")
store_pg = importlib.import_module("store_pg")


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.description = []
        self._next = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        self.connection.statements.append((query, params))
        self._next = None
        compact = " ".join(query.split())
        if compact.startswith("select correction_id::text,new_revision"):
            self.description = [("correction_id",), ("new_revision",)]
            self._next = self.connection.existing_receipt
        elif compact.startswith("select id::text,revision,text,source,active"):
            self.description = [("id",), ("revision",), ("text",), ("source",), ("active",)]
            row = self.connection.row
            self._next = None if row is None else (row["id"], row["revision"], row["text"], row["source"], row["active"])
        elif compact.startswith("update knowledge.fragment set"):
            self.connection.updated = True
            self.description = [("revision",)]
            self._next = (self.connection.row["revision"] + 1,)
        elif compact.startswith("insert into knowledge.source_correction_receipt"):
            if self.connection.fail_on_insert:
                raise RuntimeError("synthetic receipt insert failure")
            self.connection.inserted = True
            self.description = [("correction_id",)]
            self._next = ("receipt-offline",)
        else:
            self.description = []

    def fetchone(self):
        value = self._next
        self._next = None
        return value

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self, row, *, existing_receipt=None, fail_on_insert=False):
        self.row = row
        self.existing_receipt = existing_receipt
        self.fail_on_insert = fail_on_insert
        self.statements = []
        self.updated = False
        self.inserted = False
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_args):
        if exc_type is None:
            self.committed = True
        else:
            self.rolled_back = True
        return False

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True


class FakeDriver:
    def __init__(self, connection):
        self.connection = connection
        self.calls = []

    def connect(self, dsn):
        self.calls.append(dsn)
        return self.connection


def digest_refs(refs):
    return hashlib.sha256(json.dumps(refs, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode()).hexdigest()


def make_proposal(fragment, corrected_text, *, refs_digest, replacement_refs=None, choice="supported", confidence=0.97):
    evidence = {"source_contexts": [{"origin": "live-root", "quote": "new evidence", "context": "ctx"}],
        "semantic_judgement": {"choice": choice, "probabilities": {choice: confidence}}}
    if replacement_refs is not None:
        evidence["source_recovery"] = {"replacement_refs": replacement_refs}
    proposal = {"status": "supported", "fragment_id": fragment["id"], "expected_revision": fragment["revision"],
        "expected_text": fragment["text"], "corrected_text": corrected_text,
        "source_fingerprint": "source-proof-fp", "source_refs_digest": refs_digest,
        "origin": "live-root", "evidence": evidence}
    proposal["correction_key"] = hashlib.sha256(json.dumps(proposal, sort_keys=True,
        ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return source_correction.VerifiedCorrection(proposal)


class SourceCorrectionReceiptOffline(unittest.TestCase):
    def setUp(self):
        self.before = BLOCKED.copy()
        self.original_driver = store_pg.driver

    def tearDown(self):
        store_pg.driver = self.original_driver
        self.assertEqual(BLOCKED, self.before)

    def run_apply(self, row, proposal, *, fail_on_insert=False):
        connection = FakeConnection(row, fail_on_insert=fail_on_insert)
        driver = FakeDriver(connection)
        store_pg.driver = driver
        return store_pg.apply_source_correction("offline-dsn", "host-a", proposal), connection, driver

    def receipt_params(self, connection):
        inserts = [(q, p) for q, p in connection.statements if "insert into knowledge.source_correction_receipt" in q]
        self.assertEqual(len(inserts), 1, connection.statements)
        return inserts[0][1]

    def test_replacement_refs_persist_post_update_digest_and_versioned_pre_after_evidence(self):
        old_refs = [{"path": "doc.md", "quote": "old"}]
        new_refs = [{"path": "doc.md", "quote": "new"}, {"path": "doc2.md", "quote": "newer"}]
        row = {"id": "11111111-1111-1111-1111-111111111111", "revision": 7,
               "text": "old claim", "source": {"evidence_refs": old_refs, "basis": "kept"}, "active": True}
        proposal = make_proposal(row, "new claim", refs_digest=digest_refs(old_refs), replacement_refs=new_refs)
        result, connection, driver = self.run_apply(row, proposal)
        params = self.receipt_params(connection)
        proof = json.loads(params[10])["source_refs_fingerprint"]
        self.assertEqual(result, {"status": "applied", "correction_id": "receipt-offline", "revision": 8})
        self.assertEqual(driver.calls, ["offline-dsn"])
        self.assertEqual(params[7], digest_refs(new_refs))  # receipt/source_correction_receipt.source_refs_digest is POST-write refs
        self.assertEqual(proof, {"version": "source-refs-before-after-v1",
            "before": digest_refs(old_refs), "after": digest_refs(new_refs)})
        self.assertEqual(proof["before"], proposal["source_refs_digest"])
        updates = [(q, p) for q, p in connection.statements if q.lstrip().startswith("update knowledge.fragment")]
        self.assertEqual(len(updates), 1)
        self.assertEqual(json.loads(updates[0][1][1])["evidence_refs"], new_refs)
        self.assertEqual(json.loads(updates[0][1][6])["evidence_refs"], old_refs)
        self.assertTrue(connection.committed)

    def test_unchanged_source_refs_keep_pre_and_post_digest_equal(self):
        refs = [{"path": "doc.md", "quote": "same"}]
        row = {"id": "22222222-2222-2222-2222-222222222222", "revision": 2,
               "text": "before", "source": {"evidence_refs": refs}, "active": True}
        proposal = make_proposal(row, "after", refs_digest=digest_refs(refs))
        result, connection, _driver = self.run_apply(row, proposal)
        params = self.receipt_params(connection)
        proof = json.loads(params[10])["source_refs_fingerprint"]
        self.assertEqual(result["status"], "applied")
        self.assertEqual(params[7], digest_refs(refs))
        self.assertEqual(proof["before"], proposal["source_refs_digest"])
        self.assertEqual(proof["after"], proposal["source_refs_digest"])
        updates = [(q, p) for q, p in connection.statements if q.lstrip().startswith("update knowledge.fragment")]
        self.assertEqual(len(updates), 1)
        self.assertNotIn("source=%s::jsonb", updates[0][0])

    def test_stale_precondition_rejects_without_update_or_receipt_write(self):
        old_refs = [{"path": "doc.md", "quote": "old"}]
        row = {"id": "33333333-3333-3333-3333-333333333333", "revision": 4,
               "text": "before", "source": {"evidence_refs": old_refs}, "active": True}
        proposal = make_proposal(row, "after", refs_digest=digest_refs([{"path": "other", "quote": "mismatch"}]))
        result, connection, _driver = self.run_apply(row, proposal)
        self.assertEqual(result, {"status": "stale"})
        written = [q for q, _p in connection.statements if q.lstrip().startswith(("update ", "insert "))]
        self.assertEqual(written, [])

    def test_receipt_insert_failure_rolls_back_fragment_update_atomically(self):
        refs = [{"path": "doc.md", "quote": "old"}]
        row = {"id": "44444444-4444-4444-4444-444444444444", "revision": 1,
               "text": "before", "source": {"evidence_refs": refs}, "active": True}
        proposal = make_proposal(row, "after", refs_digest=digest_refs(refs))
        connection = FakeConnection(row, fail_on_insert=True)
        store_pg.driver = FakeDriver(connection)
        with self.assertRaisesRegex(RuntimeError, "synthetic receipt insert failure"):
            store_pg.apply_source_correction("offline-dsn", "host-a", proposal)
        self.assertTrue(connection.updated)
        self.assertFalse(connection.inserted)
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)

    def test_invalid_fid_and_unsupported_scope_fail_before_driver_connect(self):
        refs = []
        row = {"id": "55555555-5555-5555-5555-555555555555", "revision": 1,
               "text": "before", "source": {"evidence_refs": refs}, "active": True}
        invalid_fid = make_proposal(row, "after", refs_digest=digest_refs(refs))
        invalid_fid["fragment_id"] = 42
        invalid_fid["correction_key"] = hashlib.sha256(json.dumps({k: v for k, v in invalid_fid.items() if k != "correction_key"},
            sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        invalid_fid = source_correction.seal_verified_correction(invalid_fid)
        unsupported = make_proposal(row, "after", refs_digest=digest_refs(refs), choice="unsupported", confidence=0.99)
        for proposal, message in ((invalid_fid, "identity or text"), (unsupported, "lacks semantic support")):
            store_pg.driver = types.SimpleNamespace(connect=_blocked("driver_connect"))
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                store_pg.apply_source_correction("offline-dsn", "host-a", proposal)


if __name__ == "__main__":
    unittest.main(verbosity=2)
