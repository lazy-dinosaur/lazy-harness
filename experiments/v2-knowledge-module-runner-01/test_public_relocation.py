"""Synthetic source-relocation checks. No database, provider, native runtime or shell.

Run directly with Python, not pytest's legacy service-starting conftest.
This tests source packaging and pure boundaries, not PostgreSQL correctness.
"""
import ast
from contextlib import ExitStack
import importlib
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def denied(*args, **kwargs):
    raise AssertionError('offline relocation attempted a network/process/DB effect')


class PublicRelocation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack = ExitStack()
        cls.scratch = cls.stack.enter_context(tempfile.TemporaryDirectory(prefix='relocation-'))
        old_cwd = Path.cwd()
        cls.stack.callback(os.chdir, old_cwd)
        os.chdir(cls.scratch)  # unrelated to the source directory
        cls.stack.enter_context(patch.object(tempfile, 'tempdir', cls.scratch))
        home = Path(cls.scratch) / 'home'
        home.mkdir()
        cls.stack.enter_context(patch.dict(os.environ, {
            'HOME': str(home), 'LH_KNOWLEDGE_CONFIG': str(home / 'absent-config.json'),
            'LH_EMBED_PROVIDER': 'local', 'LH_EMBED_MODEL_DIR': str(home / 'absent-model'),
        }, clear=True))
        cls.stack.enter_context(patch.object(socket, 'create_connection', denied))
        cls.stack.enter_context(patch.object(socket, 'getaddrinfo', denied))
        cls.stack.enter_context(patch.object(socket.socket, 'connect', denied))
        cls.stack.enter_context(patch.object(socket.socket, 'connect_ex', denied))
        cls.stack.enter_context(patch.object(subprocess, 'Popen', denied))
        import portable_source
        cls.portable = portable_source
        cls.modules = {}
        try:
            for name in portable_source.RUNTIME:
                cls.modules[name] = importlib.import_module(name)
            cls.stack.enter_context(patch.object(cls.modules['store_pg'].driver, 'connect', denied))
        except BaseException:
            cls.stack.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.stack.close()

    def test_imports_resolve_only_from_public_module(self):
        for name, module in self.modules.items():
            self.assertEqual(Path(module.__file__).resolve().parent, ROOT, name)

    def test_source_inventory_contains_runtime_sql_and_loader(self):
        files = self.portable.inventory(ROOT)
        self.assertEqual(len(files), len(set(self.portable.ALLOWLIST)))
        self.assertEqual(sum(n.startswith('migrations/') for n in files), 23)
        self.assertIn('pi-extension/knowledge.ts', files)
        self.assertIn('lineage_row_provider.py', files)
        self.assertIn('current_v1_semantic.py', files)
        for name, body in files.items():
            if name.endswith('.py'):
                ast.parse(body, filename=name)
            self.assertNotIn(b'/home/' + b'lazydino/', body, name)

    def test_runtime_seed_assets_are_readable_without_database(self):
        templates = self.modules['templates']
        self.assertIn('is_new', templates.record_need())
        self.assertIn('correction_evidence', templates.intent())

    def test_unconfigured_probe_denies_before_config_import(self):
        import portable_probe
        with patch.dict(os.environ, {}, clear=True), patch.object(importlib, 'import_module', denied):
            with self.assertRaisesRegex(ValueError, 'explicit config'):
                portable_probe.probe('fixture-host')
        with self.assertRaisesRegex(ValueError, 'caller query'):
            portable_probe.probe('fixture-host', True)

    def test_runtime_target_and_ambient_routing_fail_closed(self):
        runtime = self.modules['runtime_db']
        db = runtime.bind_runtime_db('postgresql://fixture@db.invalid:5432/fixture', provenance='explicit-test')
        self.assertNotIn('db.invalid', repr(db))
        with self.assertRaises(runtime.RuntimeDBBindingError):
            db.require_same_target('postgresql://fixture@other.invalid:5432/fixture')
        with patch.dict(os.environ, {'PGHOST': 'unapproved.invalid'}):
            with self.assertRaises(runtime.RuntimeDBBindingError):
                db.assert_environment()

    def test_exact_source_quote_and_escape_denial(self):
        evidence = self.modules['source_evidence']
        with tempfile.TemporaryDirectory(dir=self.scratch) as directory:
            root = Path(directory)
            (root / 'fixture.txt').write_text('Synthetic source statement.\n')
            ref = {'type': 'official_doc', 'locator': 'fixture.txt:1', 'quote': 'Synthetic source statement.'}
            proof = evidence.read_reference(root, ref)
            self.assertEqual(proof['origin'], 'live-root')
            with self.assertRaises(evidence.SourceEvidenceError):
                evidence.read_reference(root, {**ref, 'quote': 'Unbound claim'})
            with self.assertRaises(evidence.SourceEvidenceError):
                evidence.read_reference(root, {**ref, 'locator': '../outside.txt:1'})
            (root / 'escape.txt').symlink_to(Path(self.scratch) / 'outside.txt')
            with self.assertRaises(evidence.SourceEvidenceError):
                evidence.read_reference(root, {**ref, 'locator': 'escape.txt:1'})

    def test_source_authority_override_is_atomic(self):
        config = self.modules['config']
        with self.assertRaises(config.ConfigError):
            config.source_authority({}, 'fixture-host', root_override=str(ROOT))
        with self.assertRaises(config.ConfigError):
            config.source_authority({}, 'fixture-host', root_override=str(ROOT), host_override='other-host')

    def test_unfinished_work_never_absorbs(self):
        policy = self.modules['policy']
        self.assertEqual(policy.evaluate({'completion': False})['action'], 'hold')
        self.assertEqual(policy.evaluate({'completion': True, 'conflict': True})['action'], 'queue_for_human')
        self.assertEqual(policy.evaluate({})['action'], 'hold')

    def test_quote_presence_does_not_mint_writer_capability(self):
        correction = self.modules['source_correction']
        self.assertFalse(correction.is_verified_correction({'status': 'supported'}))
        with self.assertRaises(ValueError):
            correction.seal_verified_correction({'status': 'supported'})

    def test_reservations_are_consumed_and_not_replayed(self):
        recovery = self.modules['current_v1_recovery']
        counts = {'proposer': 0, 'judge': 0}
        with tempfile.TemporaryDirectory(dir=self.scratch) as directory:
            recovery.reserve(Path(directory), 'fixture-group', 'proposer', counts)
            with self.assertRaises(ValueError):
                recovery.reserve(Path(directory), 'fixture-group', 'proposer', counts)
            self.assertEqual(counts['proposer'], 1)

    def test_default_brief_is_whole_document_and_usage_unknown(self):
        brief = self.modules['brief']
        document = '# Synthetic knowledge\n\n영역 목록: Fixture\n\n## View\n\n### 영역 Fixture\n- [fixture-1] Synthetic fact.\n'
        seen = []
        def writer(prompt, cwd):
            path = Path(cwd) / 'knowledge.md'
            seen.append(path)
            self.assertEqual(path.read_text(), document)
            return 'Synthetic brief', None
        with patch.object(brief.worker_tools, 'collect_wide', return_value=(document, {'collected': 1})), patch.dict(os.environ, {'LH_BRIEF_MAPREDUCE': '0'}):
            result = brief.brief('unused', 'fixture-host', 'fixture task', ['fixture'], denied, runner=writer)
        self.assertEqual(len(seen), 1)
        self.assertIsNone(result['writer_cost_usd'])
        self.assertFalse(seen[0].exists())
        self.assertNotIn('map_parts', result)

    def test_semantic_paths_refuse_outside_and_symlink(self):
        planning = self.modules['semantic_plan']
        with tempfile.TemporaryDirectory(dir=self.scratch) as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                planning.local(root, root / '..' / 'outside')
            (root / 'link').symlink_to(root)
            with self.assertRaises(ValueError):
                planning.local(root, root / 'link' / 'file')

    def test_maintenance_guards_and_preview_never_apply(self):
        cleanup = self.modules['cleanup']
        pair = {'a': {'id': 'a', 'alias': 'A', 'seq': 1, 'text': 'Fixture slotMinutes는 30분이다.'},
                'b': {'id': 'b', 'alias': 'B', 'seq': 2, 'text': 'Fixture slotMinutes는 30분이다.'},
                'domain': 'fixture', 'sim': .99}
        for relation, merged, clauses, expected in (
            ('partial_overlap', 'unused', 1, 'skipped'),
            ('same', 'Fixture는 30분이다.', 1, 'kept_code'),
            ('same', pair['a']['text'], 0, 'kept_clause'),
            ('same', pair['a']['text'], 1, 'merge'),
        ):
            with self.subTest(expected=expected), tempfile.TemporaryDirectory(dir=self.scratch) as directory:
                calls = []
                def merger(items):
                    calls.append(items)
                    return {i['id']: {'action': 'merge', 'text': merged} for i in items}
                with patch.object(cleanup, 'pairs', return_value=[pair]), patch.object(cleanup.store_pg, 'connect', denied):
                    result = cleanup.run('unused', 'fixture',
                        lambda packet: {'answers': {'relation': {'choice': relation}}},
                        lambda state, texts, q: [clauses] * len(texts), merger, state_dir=Path(directory))
                self.assertEqual(result['counts'], {expected: 1})
                self.assertFalse(any(r['applied'] for r in result['rows']))
                self.assertEqual(len(calls), 0 if expected == 'skipped' else 2 if expected == 'kept_code' else 1)
        guards = self.modules['merge_guard']
        self.assertTrue(guards.code_missing('Fixture는 a/b.py를 변경하지 않는다.', '', 'Fixture 변경'))
        reopen = self.modules['reopen_duplicates']
        rows = [('entry', 0, {'fact': 'Synthetic fact'}, 'judge-only')]
        self.assertEqual(reopen.classify(rows, [('fixture-1', 'Synthetic fact')])[0]['in_canon_as'], 'fixture-1')
        self.assertIsNone(reopen.classify(rows, [])[0]['in_canon_as'])

    def test_backfill_lock_idempotence_and_revision_cas(self):
        bf = self.modules['backfill_structure']
        pg = self.modules['store_pg']
        events = []
        class Cursor:
            def execute(self, sql, params):
                events.append((sql, params))
                self.select = sql.startswith('select form')
            def fetchone(self):
                return (False, 'fixture') if self.select else None  # stale revision, never write leaves
        with patch.object(self.modules['subject_merge'], 'lock_host', side_effect=lambda *a, **k: events.append(('lock', k))), \
             patch.object(pg, '_write_form', denied):
            result = bf.apply(Cursor(), 'fixture', [{'id': 'synthetic', 'subject': None, 'text': 'Fixture는 하나다.', 'revision': 7}])
        self.assertEqual(result, 0)
        self.assertEqual(events[0], ('lock', {'exclusive': True}))
        self.assertIn('revision=%s and form is null', events[-1][0])
        self.assertEqual(events[-1][1][-1], 7)
        self.assertEqual(bf.subject_of('Fixture는 하나다.', {'subject': 'Fixture'}), ('Fixture', 'source'))

    def test_conditional_fragment_parser_and_merger_failure_cleanup(self):
        cleanup = self.modules['cleanup']
        with patch.object(self.modules['brief'], 'pi_runner', side_effect=RuntimeError('fixture writer failure')):
            with self.assertRaisesRegex(RuntimeError, 'fixture writer failure'):
                cleanup.luna_merger([{'id': 'fixture', 'a': 'A', 'b': 'B'}])
        parser = importlib.import_module('check_fragments')
        self.assertEqual(Path(parser.__file__).resolve(), ROOT / 'fragmenter/check_fragments.py')
        self.assertEqual(parser.parse('{"items": []}'), {'items': []})
        with patch.object(self.modules['brief'], 'pi_runner', return_value='{"items": []}'):
            self.assertEqual(cleanup.luna_merger([]), {})

    def test_transport_guards_are_active(self):
        with self.assertRaises(AssertionError):
            socket.create_connection(('fixture.invalid', 443))
        with self.assertRaises(AssertionError):
            subprocess.Popen(['not-approved'])
        with self.assertRaises(AssertionError):
            self.modules['store_pg'].driver.connect('not-approved')


if __name__ == '__main__':
    unittest.main(verbosity=2)
