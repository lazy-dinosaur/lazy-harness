"""Standalone offline regression: run directly, never through pytest/conftest fixtures."""
import socket
import subprocess
import os
import tempfile
import unittest
import io
import json
import sys
from unittest.mock import patch

BLOCKED = {"socket_connect": 0, "socket_connect_ex": 0, "create_connection": 0, "getaddrinfo": 0,
           "popen": 0, "driver_connect": 0, "model": 0}


def _blocked(name):
    def deny(*_args, **_kwargs):
        BLOCKED[name] += 1
        raise AssertionError("offline guard blocked " + name)
    return deny


# Install all transport/process guards before importing any project module.
socket.socket.connect = _blocked("socket_connect")
socket.socket.connect_ex = _blocked("socket_connect_ex")
socket.create_connection = _blocked("create_connection")
socket.getaddrinfo = _blocked("getaddrinfo")
subprocess.Popen = _blocked("popen")

import config
import poller
import runtime_db
import knowledge_cli
import store_pg
import source_generation
import source_review
import source_evidence
import source_metadata_repair

# psycopg's C/libpq connect path does not necessarily use Python socket methods.
store_pg.driver.connect = _blocked("driver_connect")
import capture_audit
capture_audit.make_judge = _blocked("model")
source_generation._default_generate = _blocked("model")


class RuntimeDBIsolationOffline(unittest.TestCase):
    def setUp(self):
        self.saved = BLOCKED.copy()

    def assert_no_transports(self):
        self.assertEqual(BLOCKED, self.saved)

    def test_endpoint_binding_rejects_mismatch_and_routing_before_connect(self):
        chosen = runtime_db.bind_runtime_db(
            "postgresql://pilot-user:secret@127.0.0.1:33490/postgres", provenance="explicit-test")
        for incomplete in (
            "postgresql:///knowledge",
            "postgresql://u:p@db.example.invalid/knowledge",
            "postgresql://u:p@db.example.invalid:5432",
            "host=db.example.invalid port=5432 dbname=knowledge",
            "host=db.example.invalid dbname=knowledge user=u",
        ):
            with self.subTest(incomplete=incomplete), self.assertRaises(runtime_db.RuntimeDBBindingError):
                runtime_db.bind_runtime_db(incomplete)
        with self.assertRaises(runtime_db.RuntimeDBBindingError):
            chosen.require_same_target("postgresql://other:secret@example.invalid:5432/postgres")
        for bad in (
            "postgresql://u:p@127.0.0.1:33490/postgres?hostaddr=192.0.2.4",
            "host=127.0.0.1,example.invalid port=33490 dbname=postgres user=u",
            "service=not-allowed dbname=postgres",
        ):
            with self.assertRaises(runtime_db.RuntimeDBBindingError):
                runtime_db.bind_runtime_db(bad)
        with patch.dict(os.environ, {"PGHOST": "elsewhere.invalid"}):
            with self.assertRaises(runtime_db.RuntimeDBBindingError):
                runtime_db.bind_runtime_db("postgresql://u:p@127.0.0.1:33490/postgres")
        for key, value in (("PGHOSTADDR", "192.0.2.4"), ("PGPORT", "6543"),
                            ("PGDATABASE", "redirected"), ("PGUSER", "redirected"),
                            ("PGSERVICE", "redirected"), ("PGSERVICEFILE", "/tmp/redirected")):
            with patch.dict(os.environ, {key: value}), self.assertRaises(runtime_db.RuntimeDBBindingError):
                runtime_db.bind_runtime_db("postgresql://u:p@127.0.0.1:33490/postgres")
        self.assert_no_transports()

    def test_context_constructor_cannot_lie_about_dsn_endpoint(self):
        selected = "postgresql://u:p@db.example.invalid:6432/knowledge"
        forged = runtime_db.bind_runtime_db("postgresql://u:p@other.example.invalid:6432/knowledge").endpoint
        with self.assertRaisesRegex(runtime_db.RuntimeDBBindingError, "does not match"):
            runtime_db.RuntimeDBContext(selected, forged, "explicit-test")
        self.assert_no_transports()

    def test_late_environment_reroute_fails_before_tick_connector_or_model(self):
        dsn = "postgresql://prod-user:synthetic-secret@prod.example.invalid:6432/knowledge"
        context = runtime_db.bind_runtime_db(dsn, provenance="explicit-test")
        with patch.dict(os.environ, {"PGPORT": "6543"}):
            with self.assertRaises(runtime_db.RuntimeDBBindingError):
                poller.tick(dsn, lambda *_a: self.fail("model must not run"), runtime_db=context,
                            state="unused")
        self.assert_no_transports()

    def test_selected_production_endpoint_is_actual_fake_connector_argument(self):
        dsn = "postgresql://prod-user:synthetic-secret@prod.example.invalid:6432/knowledge"
        received = []
        class FakeConnection:
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def close(self): pass
        def fake_connect(target):
            received.append(target)
            return FakeConnection()
        context = runtime_db.bind_runtime_db(dsn, provenance="explicit-test")
        with patch.object(store_pg.driver, "connect", fake_connect):
            with store_pg.connect(context.dsn):
                pass
        self.assertEqual(received, [dsn])
        self.assertEqual(runtime_db._endpoint(received[0]), context.endpoint)
        self.assert_no_transports()

    def test_late_environment_reroute_fails_at_reviewer_before_model_or_writer(self):
        dsn = "postgresql://prod-user:synthetic-secret@prod.example.invalid:6432/knowledge"
        context = runtime_db.bind_runtime_db(dsn, provenance="explicit-test")
        model_calls, writer_calls = [], []
        reviewer = poller.configured_source_reviewer(
            {"default_host": "host-pilot", "db_url": dsn}, context,
            root_override=tempfile.mkdtemp(prefix="runtime-db-reviewer-offline-"),
            host_override="host-pilot", verifier=lambda *_a, **_k: model_calls.append(True),
            correction_writer=lambda *_a, **_k: writer_calls.append(True))
        with patch.dict(os.environ, {"PGDATABASE": "redirected"}):
            with self.assertRaises(runtime_db.RuntimeDBBindingError):
                reviewer("host-pilot", {"id": "left"}, {"id": "right"})
        self.assertEqual(model_calls, [])
        self.assertEqual(writer_calls, [])
        self.assert_no_transports()

    def test_runtime_context_freezes_configured_reviewer_callbacks(self):
        pilot = "postgresql://pilot-user:secret@127.0.0.1:33490/postgres"
        runtime = runtime_db.bind_runtime_db(pilot, provenance="explicit-diagnostic")
        calls = []
        verifier_calls = []
        generation_calls = []
        source_root = tempfile.mkdtemp(prefix="runtime-db-offline-")
        original_review = source_review.review_pair
        original_generate = source_generation.generate_and_verify
        source_review.review_pair = lambda *_a, **_k: {"status": "evidence_needed", "reason": "synthetic"}
        source_generation.generate_and_verify = lambda *_a, **_k: generation_calls.append(True) or {"status": "supported", "evidence": {}}
        try:
            def writer(dsn, host, proposal, **kwargs):
                calls.append((dsn, host, proposal, kwargs))
                return {"status": "applied"}
            # Swap only the protected fake writer; no database writer is invoked.
            mutable_cfg = {"db_url": "postgresql://remote-user:secret@example.invalid:5432/postgres",
                           "default_host": "host-pilot"}
            legacy_selected = mutable_cfg["db_url"]
            self.assertNotEqual(legacy_selected, runtime.dsn)  # offline reproduction of the former split target
            reviewer2 = poller.configured_source_reviewer(
                mutable_cfg, runtime, root_override=source_root, host_override="host-pilot",
                verifier=lambda *_a, **_k: verifier_calls.append(True) or [], correction_writer=writer)
            mutable_cfg["db_url"] = "postgresql://later:secret@elsewhere.invalid:5432/postgres"
            # Prevent source-file reads and model calls; source proofs are synthetic and local.
            provider = source_review.SourceProvider
            old_provider_read = provider.read_fragment
            provider.read_fragment = lambda *_a, **_k: {"fingerprint": "offline-proof"}
            try:
                left = {"id": "left", "revision": 1, "text": "claim", "source": {"evidence_refs": []}}
                right = {"id": "right", "revision": 1, "text": "other", "source": {"evidence_refs": []}}
                reviewer2("host-pilot", left, right, question_id=384)
            finally:
                provider.read_fragment = old_provider_read
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0], pilot)
            self.assertEqual(calls[0][1], "host-pilot")
            self.assertEqual(verifier_calls, [])
            self.assertEqual(generation_calls, [True])
            self.assertEqual(reviewer2.runtime_db.dsn, pilot)
            self.assert_no_transports()
        finally:
            source_review.review_pair = original_review
            source_generation.generate_and_verify = original_generate

    def test_missing_reviewer_context_fails_before_driver_or_model(self):
        dsn = "postgresql://pilot-user:secret@127.0.0.1:33490/postgres"
        with self.assertRaisesRegex(ValueError, "binding is required"):
            poller.tick(dsn, lambda *_a: [], require_source_review=True, state="unused")
        with self.assertRaisesRegex(ValueError, "binding mismatch"):
            poller.tick(dsn, lambda *_a: [], source_reviewer=lambda *_a: {},
                        require_source_review=True, state="unused")
        self.assert_no_transports()

    def test_legitimate_bound_target_uses_only_injected_fake_connector(self):
        dsn = "postgresql://pilot-user:secret@127.0.0.1:33490/postgres"
        received = []
        class FakeConnection:
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def close(self): pass
        def fake_connect(target):
            received.append(target)
            return FakeConnection()
        with patch.object(store_pg.driver, "connect", fake_connect):
            with store_pg.connect(runtime_db.bind_runtime_db(dsn).dsn):
                pass
        self.assertEqual(received, [dsn])
        self.assert_no_transports()

    def test_polling_target_mismatch_fails_before_driver_or_model(self):
        pilot = "postgresql://pilot-user:secret@127.0.0.1:33490/postgres"
        context = runtime_db.bind_runtime_db(pilot)
        with self.assertRaises(runtime_db.RuntimeDBBindingError):
            poller.tick("postgresql://remote:secret@example.invalid/postgres", lambda *_a: [],
                        runtime_db=context, state="unused")
        self.assert_no_transports()

    def test_public_cli_explicit_dsn_is_the_same_callback_context(self):
        pilot = "postgresql://pilot-user:secret@127.0.0.1:33490/postgres"
        captured = []
        old_review = knowledge_cli.review_cmd
        old_argv, old_stdin, old_stdout = sys.argv, sys.stdin, sys.stdout
        output = io.StringIO()
        try:
            knowledge_cli.review_cmd = lambda dsn, _data, *, runtime_db=None: captured.append(
                (dsn, runtime_db.dsn, runtime_db.provenance)) or {"items": []}
            sys.argv = ["knowledge_cli.py", "review", "--dsn", pilot]
            sys.stdin = io.StringIO('{"action":"list"}')
            sys.stdout = output
            knowledge_cli.main()
        finally:
            knowledge_cli.review_cmd = old_review
            sys.argv, sys.stdin, sys.stdout = old_argv, old_stdin, old_stdout
        self.assertEqual(captured, [(pilot, pilot, "explicit-cli")])
        self.assert_no_transports()

    def _metadata_recovery_case(self, mutate_environment):
        dsn = "postgresql://prod-user:synthetic-secret@prod.example.invalid:6432/knowledge"
        context = runtime_db.bind_runtime_db(dsn, provenance="explicit-test")
        root = tempfile.mkdtemp(prefix="runtime-db-metadata-offline-")
        model_calls, writer_calls = [], []
        fragment = {"id": "claim-1", "host_id": "host-pilot", "revision": 3, "text": "supported claim",
                    "source": {"evidence_refs": [{"type": "official_doc", "locator": "stale", "quote": "old citation"}]}}
        reviewer = poller.configured_source_reviewer(
            {"default_host": "host-pilot", "db_url": dsn}, context, root_override=root, host_override="host-pilot",
            generator=lambda *_a: model_calls.append("generate") or json.dumps(
                {"quotes": ["supported claim quote"], "why": "synthetic verified source"}),
            verifier=lambda *_a, **_k: model_calls.append("verify") or self._metadata_verdict(mutate_environment),
            correction_writer=lambda *_a, **_k: self.fail("claim correction writer must not run"))
        original_review_pair = source_review.review_pair
        original_read = source_review.SourceProvider.read_fragment
        original_recover = source_review.SourceProvider.recover_original_context
        original_prepare = source_metadata_repair.prepare
        original_literal_quotes = source_evidence.literal_quote_references
        original_connect, original_row = store_pg.connect, store_pg._row
        original_metadata_writer = store_pg.apply_source_metadata_repair
        try:
            source_review.review_pair = lambda *_a, **_k: {"status": "evidence_needed", "reason": "synthetic"}
            def fake_read(_provider, current):
                refs = (current.get("source") or {}).get("evidence_refs", [])
                if refs and refs[0].get("locator") == "stale":
                    raise source_evidence.SourceEvidenceError("synthetic stale citation")
                return {"fingerprint": "synthetic-proof", "evidence": [{"context": "supported claim quote",
                    "origin": "official_doc"}]}
            source_review.SourceProvider.read_fragment = fake_read
            source_review.SourceProvider.recover_original_context = lambda *_a, **_k: {
                "evidence": [{"context": "supported claim quote"}], "fingerprint": "synthetic-proof",
                "verification": "synthetic-verified"}
            source_evidence.literal_quote_references = lambda _contexts, quotes: [
                {"type": "official_doc", "locator": "guide.md:L2", "quote": quote} for quote in quotes
                if quote == "supported claim quote"]
            source_metadata_repair.prepare = lambda *_a, **_k: {"operation": "metadata_repair"}
            class Cursor:
                def execute(self, *_a, **_k): pass
                def __enter__(self): return self
                def __exit__(self, *_a): pass
            class Connection:
                def cursor(self): return Cursor()
                def __enter__(self): return self
                def __exit__(self, *_a): pass
            store_pg.connect = lambda *_a, **_k: Connection()
            store_pg._row = lambda _cur: fragment
            def metadata_writer(*_a, **_k):
                writer_calls.append(_a[0])
                return {"status": "applied"}
            store_pg.apply_source_metadata_repair = metadata_writer
            caught = None
            with patch.dict(os.environ):
                try:
                    result = reviewer("host-pilot", fragment, {"id": "other", "revision": 3}, question_id=18)
                except runtime_db.RuntimeDBBindingError as exc:
                    caught, result = exc, None
            return result, model_calls, writer_calls, dsn, reviewer.runtime_db, caught
        finally:
            source_review.review_pair = original_review_pair
            source_review.SourceProvider.read_fragment = original_read
            source_review.SourceProvider.recover_original_context = original_recover
            source_metadata_repair.prepare = original_prepare
            source_evidence.literal_quote_references = original_literal_quotes
            store_pg.connect, store_pg._row = original_connect, original_row
            store_pg.apply_source_metadata_repair = original_metadata_writer

    def _metadata_verdict(self, mutate_environment):
        if mutate_environment:
            os.environ["PGHOSTADDR"] = "203.0.113.7"
        return [{"choice": "supported", "probabilities": {"supported": 0.99}}]

    def test_metadata_claim_recovery_rechecks_environment_after_model_before_writer(self):
        result, model_calls, writer_calls, _dsn, _context, caught = self._metadata_recovery_case(True)
        self.assertIsInstance(caught, runtime_db.RuntimeDBBindingError)
        self.assertEqual(model_calls, ["generate", "verify"])
        self.assertEqual(writer_calls, [])
        self.assertIsNone(result)
        self.assert_no_transports()

    def test_metadata_claim_recovery_keeps_selected_context_for_fake_writer(self):
        result, model_calls, writer_calls, dsn, context, caught = self._metadata_recovery_case(False)
        self.assertIsNone(caught)
        self.assertEqual(model_calls, ["generate", "verify"])
        self.assertEqual(writer_calls, [dsn])
        self.assertEqual(context.dsn, dsn)
        self.assertEqual(result["reason"], "source_metadata_repair_applied")
        self.assert_no_transports()

    def test_guard_counts_are_zero_for_all_cases(self):
        self.assertEqual(BLOCKED, self.saved)


if __name__ == "__main__":
    unittest.main(verbosity=2)
