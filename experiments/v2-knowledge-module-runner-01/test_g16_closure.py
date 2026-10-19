"""Synthetic G16 closure probes; run only inside the isolated publication worker.
No provider, database, financial receipt authority or PostgreSQL correctness claim.
"""
import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

MODULE = Path(__file__).resolve().parent
REPO = MODULE.parents[1]
SCALE = MODULE/'scale-04'
NATIVE = REPO/'experiments/v2-native-minlive/unit1-controller-source-phase1'
sys.path[:0] = [str(SCALE), str(NATIVE), str(MODULE)]
import portable_source
import safety
from safety import Stop, digest, load, save


class PublicClosure(unittest.TestCase):
    def test_passive_conditional_imports_and_relocated_native_paths(self):
        for name in portable_source.SCALE04:
            module = importlib.import_module(name)
            self.assertEqual(Path(module.__file__).resolve().parent, SCALE)
        import native_services, native_bridge, writer_transport
        self.assertEqual(native_services.public_source_roots(), (REPO, MODULE, SCALE))
        bridge = native_bridge.NodeBridge(None, None, None, 'fixture')
        with patch.object(writer_transport, 'runtime_path', return_value=Path('/fixture/runtime.mjs')):
            args = bridge.argv(123)
        self.assertEqual(args, ['node', str(NATIVE/'native_bridge.mjs'), '123', '/fixture/runtime.mjs'])

    def test_exact_23_sql_sources_and_template_seed_without_db(self):
        import local_db, templates
        paths = local_db.migration_paths()
        self.assertEqual(local_db.MIGRATIONS, list(portable_source.MIGRATIONS))
        self.assertEqual([p.name[:4] for p in paths], [f'{i:04}' for i in range(1,24)])
        calls = []
        # Fake asset consumer, NOT a SQL engine or schema-application test.
        for path in paths:
            body = path.read_text()
            self.assertTrue(body.strip()); calls.append((path.name, body))
        self.assertEqual(len(calls), 23)
        self.assertIn('validation_receipt', calls[-1][1])
        self.assertIn('is_new', templates.record_need())
        self.assertIn('correction_evidence', templates.intent())
        self.assertFalse(any('apply_form' in p.name for p in paths))

    def test_missing_0023_is_typed_and_never_inserts_diagnostics(self):
        import validation_receipts as vr
        class Cursor:
            def __init__(self): self.calls = []
            def execute(self, sql, *args): self.calls.append(sql)
            def fetchone(self): return (None,)
        cur = Cursor()
        with self.assertRaises(vr.ValidationReceiptMigrationRequired): vr.insert(cur, {})
        self.assertEqual(len(cur.calls), 1)
        self.assertNotIn('insert', cur.calls[0].lower())

    def test_financial_unavailability_precedes_effect_or_release(self):
        import jev_failure, local_db, place_write
        with tempfile.TemporaryDirectory() as tmp:
            ledger = safety.Ledger(Path(tmp)/'paid.jsonl', 'fixture', {'judging':1.,'embedding':1.})
            def uncertain(): raise RuntimeError('synthetic ambiguous send')
            with self.assertRaises(Stop): ledger.call('judging','fixture',.1,uncertain)
            before = ledger.path.read_bytes()
            ident = ledger.rows[-1]['id']
            for effect in (lambda: jev_failure.resolve(ledger,ident,'fixture explicit reason'),
                           lambda: ledger.release(ident,'fixture explicit reason'),
                           lambda: safety.Paid(ledger,'judging',{}).http(None,'https://example.invalid'),
                           lambda: safety.Paid(ledger,'judging',{}).model('fixture',Path(tmp)),
                           lambda: local_db.docker('ps'),
                           lambda: place_write.production(None,{})):
                with self.assertRaises(Stop): effect()
                self.assertEqual(ledger.path.read_bytes(), before)
            self.assertEqual(ledger.spent('judging'),.1)

    def test_actual_received_error_never_implies_free_or_replay(self):
        import jev_failure
        url = 'https://openrouter.ai/api/v1/systemone'
        for status in (400, 429, 500):
            error = HTTPError(url,status,'synthetic failure',{},io.BytesIO(b'{"id":"gen-fixture","error":{"usage":{"cost":0}}}'))
            evidence = jev_failure.capture(error)
            with tempfile.TemporaryDirectory() as tmp:
                self.assertFalse(jev_failure.uncharged(evidence,Path(tmp)))
            self.assertEqual(evidence['status'],status)
        self.assertFalse(jev_failure.uncharged(None,Path('.')))

    def test_synthetic_catalog_plan_hash_home_and_conflicts(self):
        import prepare, confirmed_area_catalog as catalog, area_catalog
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); scope = 'pilot-area-10-isolated'; home = root/scope
            plan = {'scope':scope,'area_catalog':True,'synthetic_only':True,'paid_approved':False}
            save(home/'plan.json',plan); save(home/'state/plan.json',plan)
            with patch.object(prepare,'HERE',root):
                with self.assertRaises(Stop): catalog.write_confirmed(plan,home,'stale')
                with self.assertRaises(Stop): catalog.write_confirmed(plan,root/'foreign',digest(plan))
                result = catalog.write_confirmed(plan,home,digest(plan))
                self.assertEqual(len(area_catalog.confirmed(plan,home)),10)
                self.assertTrue(result['synthetic_only'])
                self.assertIn('fixture-only',result['confirmation'])
                result['areas'][0]['description']='conflicting fixture'
                save(home/'state/area-catalog.json',result)
                with self.assertRaises(Stop): catalog.write_confirmed(plan,home,digest(plan))
                save(home/'state/plan.json', {**plan,'changed':True})
                with self.assertRaises(Stop): area_catalog.confirmed(plan,home)
            for name in ('one two', 'x/y'):
                with self.assertRaises(Stop): area_catalog.areas({'areas':[{'name':name,'description':'fixture'}]})
            with self.assertRaises(Stop): area_catalog.areas({'areas':[{'name':'Fixture','description':'a\nb'}]})

    def test_explicit_synthetic_input_not_private_baseline_or_calibration(self):
        import prepare, embedding_thresholds, embed
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError): prepare.inputs()
        manifest = SCALE/'fixtures/inventory.json'
        with patch.dict(os.environ, {'LH_G16_FIXTURE_MANIFEST':str(manifest)}):
            records, questions = prepare.inputs()
        self.assertTrue(records); self.assertEqual(questions,[])
        self.assertEqual(prepare.baseline(questions)['status'],'unavailable')
        with patch.object(embed,'MODEL_ID','perplexity/pplx-embed-v1-0.6b@openrouter'), patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(embedding_thresholds.get('retrieval'))
            with self.assertRaises(embedding_thresholds.CalibrationRequired): embedding_thresholds.get('capture_dedupe')

    def test_synthetic_caller_dry_plan_and_no_provisioning(self):
        sys.path.insert(0,str(NATIVE.parent/'unit1-trial-caller-01'))
        import trial
        self.assertEqual(trial.run()['effects'],0)
        self.assertTrue(json.loads((trial.HOME/'plan.json').read_text())['synthetic_only'])
        with self.assertRaises(ValueError): trial.LocalResources()(None,None,None).__enter__()


if __name__ == '__main__': unittest.main(verbosity=2)
