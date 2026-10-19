"""Same-ten isolated preparation using only synthetic raw/source/temp HOME.
No real restored records, old pilot state, profile credentials, models, or DB.
Run directly with python3 scale-04/test_isolated_scope_offline.py.
"""
import test_offline  # network/process guards, before production imports
import hashlib
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import prepare
import confirmed_area_catalog as confirmed
from area_catalog import PILOT_TEN
from safety import Ledger, Stop, digest, load, save

ISOLATED = 'pilot-area-10-isolated'
CURRENT = 'pilot-area-10-unit1-current'


class SyntheticPreparation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.runner = self.root/'runner'
        self.here = self.runner/'scale-04'
        self.here.mkdir(parents=True)
        self.addCleanup(patch.stopall)
        patch.object(prepare, 'HERE', self.here).start()
        patch.object(prepare, 'RUNNER', self.runner).start()
        patch.object(sys, 'path', list(sys.path)).start()
        patch.dict(os.environ, {'HOME': str(self.root/'fake-home'),
                               'LH_KNOWLEDGE_CONFIG': str(self.root/'absent.json'),
                               'LH_PILOT_CASH_PRIOR_USD': '0.125'}).start()
        patch.dict(sys.modules, {'check_fragments': SimpleNamespace(
            parse=lambda raw: {'queries': [{'query': raw, 'kind': 'synthetic'}]})}).start()
        import embedding_transport, candidate_policy, ddd_criterion
        self.embedding = {'version': 999, 'model': {'model_id': 'synthetic-embedding'}, 'synthetic': True}
        self.candidate = {'version': 999, 'top_k': 5, 'synthetic': True}
        patch.object(embedding_transport, 'policy', return_value=self.embedding).start()
        patch.object(candidate_policy, 'policy', return_value=self.candidate).start()
        patch.object(ddd_criterion, 'criterion_sha', return_value='e'*64).start()
        # All rows use one deliberately synthetic raw document; IDs still exercise PILOT_TEN filtering.
        raw = '# Synthetic fixture\nSynthetic reservation rule.\n'
        self.raw = raw.encode()
        rawpath = self.here/'v1/synthetic.md'
        rawpath.parent.mkdir()
        rawpath.write_bytes(self.raw)
        ids = list(PILOT_TEN) + [f'SYNTH-{i}' for i in range(588)]
        records = [{'record_id': rid, 'path': 'synthetic.md', 'pilot': i < 55,
                    'bytes': len(self.raw), 'sha256': hashlib.sha256(self.raw).hexdigest()}
                   for i, rid in enumerate(ids)]
        save(self.runner/'scale-01/records.json', records)
        save(self.here/'restore-report.json', {'excluded_questions': sorted(prepare.EXCLUDED), 'missing': []})
        nugget = PILOT_TEN[0]+':F1'
        questions = [{'qid': f'Q{i:03}', 'nuggets': [nugget]} for i in range(64)]
        manifest = self.here/'fixtures/inventory.json'
        save(manifest, {'synthetic_only':True, 'records':records, 'questions':questions})
        patch.dict(os.environ, {'LH_G16_FIXTURE_MANIFEST':str(manifest)}).start()
        save(self.runner/'read-01/questions.json', questions)
        queryhome = self.runner/'read-01/b3-queries'
        queryhome.mkdir()
        for q in questions: (queryhome/(q['qid']+'.raw.txt')).write_text('synthetic query')
        save(self.runner/'capture-01/s1b-claims-flat.json', [
            {'rid': PILOT_TEN[0], 'id': 'F1', 'claim': 'synthetic claim'}])
        for n in (1, 2, 3):
            save(self.runner/f'scale-03/measure/sol-result-{n}.json',
                 {'items': [{'id': nugget, 'verdict': 'supported'}]})
        rows = [{'run': n, 'qid': q['qid'], 'nugget': nugget, 'covered': 1., 'contradicted': 0.}
                for n in (1, 2, 3) for q in questions]
        for name in ('judged-measure.json', 'judged-measure-raw-mr.json'):
            save(self.runner/'scale-03/measure'/name, rows)
        # Only fake source bytes are inventoried; bounded globs must not traverse nested stores.
        for rel in ('scale-04/prepare.py', 'scale-04/role_worker.py', 'shared.py',
                    'scale-04/writer_host.mjs', 'scale-04/role_host.mjs',
                    'migrations/0023_validation_receipt.sql', 'pi-extension/knowledge.ts',
                    'fragmenter/check_fragments.py', 'scale-04/publication_provenance.py',
                    'scale-04/node_modules/not-source.mjs', 'scale-04/.local/not-source.mjs'):
            path = self.runner/rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic source: '+rel)

    def make_plan(self, scope=None):
        scope = scope or ISOLATED
        result = prepare.prepare(scope)
        plan=load(prepare.scope_home(scope)/'plan.json')
        plan['synthetic_only']=True
        save(prepare.scope_home(scope)/'plan.json',plan)
        return load(prepare.scope_home(scope)/'plan.json'), result

    def test_scope_exports_and_same_ten_raw_root_default_run(self):
        self.assertIsInstance(prepare.SCOPES, tuple)
        self.assertIsInstance(prepare.AREA_SCOPES, tuple)
        self.assertIsInstance(prepare.TEN_SCOPES, tuple)
        self.assertEqual(prepare.SCOPES, ('full', 'pilot', 'pilot-fresh', 'pilot-feature',
                                         'pilot-area-10', 'pilot-area', 'pilot-area-10-isolated', CURRENT))
        self.assertEqual(prepare.AREA_SCOPES, ('pilot-area-10', 'pilot-area', 'pilot-area-10-isolated', CURRENT))
        self.assertEqual(prepare.TEN_SCOPES, ('pilot-area-10', 'pilot-area-10-isolated', CURRENT))
        old, oq = prepare.inputs('pilot-area-10')
        new, nq = prepare.inputs(ISOLATED)
        self.assertEqual(old, new)
        self.assertEqual(oq, nq)
        self.assertEqual({r['record_id'] for r in new}, set(PILOT_TEN))
        self.assertEqual(len(new), 10)
        self.assertEqual(len(nq), 64)
        self.assertEqual({r['sha256'] for r in new}, {hashlib.sha256(self.raw).hexdigest()})
        home = prepare.scope_home(ISOLATED)
        self.assertEqual(prepare.source_home(home), self.here)
        self.assertEqual((prepare.source_home(home)/'v1/synthetic.md').read_bytes(), self.raw)
        self.assertEqual(prepare.default_runs(ISOLATED), 1)
        self.assertEqual(prepare.default_runs('full'), 3)
        self.assertEqual(len(prepare.inputs('pilot-area')[0]), 55)

    def test_new_plan_is_unit_first_not_fifty_five_or_fresh_cash_profile(self):
        old, _ = self.make_plan('pilot-area-10')
        new, result = self.make_plan()
        self.assertEqual(new['records'], old['records'])
        for key in ('subject_contract', 'grounding_version', 'candidate_policy', 'embedding_policy',
                    'required_phases', 'resume_mode', 'cash_caps', 'subscription_limits'):
            self.assertEqual(new[key], old[key], key)
        self.assertEqual(new['subject_contract']['version'], 11)
        self.assertEqual(new['subject_contract']['criterion'], 'DDD2')
        self.assertEqual(new['grounding_version'], 6)
        self.assertEqual(new['embedding_policy'], self.embedding)
        self.assertEqual(new['candidate_policy'], self.candidate)
        self.assertEqual(new['quality_sample_records'], 10)
        self.assertEqual(new['write_path'], 2)
        self.assertTrue(new['sequential_units'])
        self.assertTrue(new['area_catalog'])
        self.assertEqual(new['resume_mode'], 'unit-first')
        self.assertEqual(new['host'], 'fixture-g16-scale04-'+ISOLATED)
        self.assertEqual(new['container'], 'lh-g16-scale04-'+ISOLATED+'-local')
        self.assertNotEqual(digest(new), digest(old))
        self.assertEqual(result['records'], 10)
        self.assertFalse(new['paid_approved'])
        self.assertFalse((prepare.scope_home(ISOLATED)/'state').exists())
        fresh, _ = self.make_plan('pilot-fresh')
        self.assertEqual(fresh['cash_caps']['total_usd'], 24.5)
        self.assertEqual(len(fresh['records']), 55)

    def test_explicit_prior_required_finite_range_and_no_effect_on_rejection(self):
        for raw in (None, '', ' ', 'nan', 'inf', '-inf', '-0.01', '0.5', '1', 'not-a-number'):
            with self.subTest(raw=raw), patch.dict(os.environ), patch.object(prepare, 'inputs') as inputs:
                if raw is None: os.environ.pop('LH_PILOT_CASH_PRIOR_USD', None)
                else: os.environ['LH_PILOT_CASH_PRIOR_USD'] = raw
                with self.assertRaisesRegex(ValueError, 'prior pilot cash'):
                    prepare.prepare(ISOLATED)
                inputs.assert_not_called()
                self.assertFalse(prepare.scope_home(ISOLATED).exists())
        # Explicit zero remains a caller assertion, never an inferred reset/default.
        with patch.dict(os.environ, {'LH_PILOT_CASH_PRIOR_USD': '0'}):
            plan, _ = self.make_plan()
            self.assertEqual(plan['cash_caps']['prior_spent_usd'], 0)

    def test_namespace_does_not_reset_cumulative_total_admission(self):
        plan, _ = self.make_plan()
        self.assertEqual(plan['cash_caps']['total_usd'], .5)
        self.assertEqual(plan['cash_caps']['prior_spent_usd'], .125)
        remaining = plan['cash_caps']['total_usd']-plan['cash_caps']['prior_spent_usd']
        ledger = Ledger(self.root/'fake-ledger.jsonl', digest(plan), plan['caps'], cash_limit=remaining)
        ledger.admit_cash(.375)
        with self.assertRaisesRegex(Stop, 'total cash'): ledger.admit_cash(.376)
        self.assertFalse(ledger.path.exists())

    def test_started_new_and_frozen_old_state_remain_byte_identical(self):
        oldhome = self.here/'pilot-area-10'
        sentinels = ('plan.json', 'state/plan.json', 'state/completion.json', 'state/paid.jsonl',
                     'state/database.dump', 'state/readback.json')
        for rel in sentinels:
            path = oldhome/rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('old synthetic immutable '+rel).encode())
        oldbytes = {p: p.read_bytes() for p in oldhome.rglob('*') if p.is_file()}
        plan, _ = self.make_plan()
        home = prepare.scope_home(ISOLATED)
        save(home/'state/plan.json', plan)
        save(home/'state/paid.jsonl', {'synthetic': 'started'})
        before = {p: p.read_bytes() for p in home.rglob('*') if p.is_file()}
        with patch.object(prepare, 'inputs') as inputs, self.assertRaisesRegex(ValueError, 'immutable started'):
            prepare.prepare(ISOLATED)
        inputs.assert_not_called()
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        self.assertEqual({p: p.read_bytes() for p in oldbytes}, oldbytes)

    def test_unknown_scope_and_path_traversal_rejected_before_input_reads(self):
        for scope in ('unknown', '../pilot-area-10-isolated', '/tmp/pilot-area-10-isolated',
                      'pilot-area-10-isolated/child'):
            for operation in (prepare.scope_home, prepare.default_runs, prepare.inputs, prepare.prepare):
                with self.subTest(scope=scope, operation=operation.__name__), self.assertRaises(ValueError):
                    operation(scope)
        outside = self.root/'outside'
        outside.mkdir()
        (self.here/ISOLATED).symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'source root'): prepare.scope_home(ISOLATED)
        (self.here/ISOLATED).unlink()
        sibling = self.here/'pilot-area-10'
        sibling.mkdir()
        (self.here/ISOLATED).symlink_to(sibling, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'source root'): prepare.scope_home(ISOLATED)

    def test_confirmed_seed_areas_unchanged_and_exact_new_plan_digest_required(self):
        plan, _ = self.make_plan()
        home = prepare.scope_home(ISOLATED)
        save(home/'state/plan.json', plan)
        with self.assertRaisesRegex(Stop, 'exact plan SHA'):
            confirmed.write_confirmed(plan, home, 'stale-sha')
        value = confirmed.write_confirmed(plan, home, digest(plan))
        self.assertEqual(value['areas'], [{'name': name, 'description': description}
                                         for name, description in confirmed.CONFIRMED_AREAS])
        self.assertEqual(len(value['areas']), 10)
        self.assertEqual(value['plan_sha'], digest(plan))
        self.assertTrue(value['confirmed_by_user'])
        with self.assertRaisesRegex(Stop, 'exact isolated home'):
            confirmed.write_confirmed(plan, self.here/'foreign', digest(plan))
        save(home/'state/area-catalog.json', {'sentinel': 'do not overwrite'})
        with self.assertRaisesRegex(Stop, 'do not overwrite'):
            confirmed.write_confirmed(plan, home, digest(plan))

    def test_code_fingerprint_includes_new_role_python_and_bounded_mjs_only(self):
        plan, _ = self.make_plan()
        for rel in ('scale-04/role_worker.py', 'scale-04/writer_host.mjs', 'scale-04/role_host.mjs'):
            self.assertEqual(plan['code'][rel], hashlib.sha256((self.runner/rel).read_bytes()).hexdigest())
        self.assertFalse(any('node_modules' in rel or '/.local/' in rel for rel in plan['code']))
        (self.here/'role_host.mjs').write_text('changed synthetic role host')
        changed, _ = self.make_plan()
        self.assertNotEqual(plan['code']['scale-04/role_host.mjs'], changed['code']['scale-04/role_host.mjs'])
        self.assertNotEqual(digest(plan), digest(changed))


class CurrentAlias(SyntheticPreparation):
    """Run identical same-ten/prior/started/path protections for the fixed current alias."""
    def setUp(self):
        super().setUp()
        patch(__name__+'.ISOLATED', CURRENT).start()

    def test_confirmed_seed_areas_unchanged_and_exact_new_plan_digest_required(self):
        # The old seed-file CLI remains isolated-only; no invented all-ten receipt.
        plan, _ = self.make_plan()
        self.assertEqual(len(confirmed.CONFIRMED_AREAS), 10)
        self.assertEqual({r['record_id'] for r in plan['records']}, set(PILOT_TEN))
        self.assertEqual(plan['host'], 'fixture-g16-scale04-'+CURRENT)

    def test_owned_current_plan_dsn_digest_and_predocker_guards(self):
        import local_db
        patch.object(local_db, 'HERE', self.here).start()
        plan, _ = self.make_plan()
        home = prepare.scope_home(CURRENT)
        host, name = plan['host'], plan['container']
        save(home/'state/plan.json', plan)
        binding = digest(plan)
        dsn = 'postgresql://postgres:localtest@127.0.0.1:54321/postgres'
        self.assertEqual(local_db._owned_unit_first_plan(home,host,name,binding,dsn), plan)
        for url in ('postgresql://postgres:localtest@localhost:54321/postgres',
                    'postgresql://postgres:localtest@127.0.0.1:0/postgres',
                    'postgresql://postgres:localtest@127.0.0.1:65536/postgres',
                    dsn+'?hostaddr=8.8.8.8'):
            with self.subTest(url=url), patch('store_pg.connect') as connect:
                with self.assertRaises(Stop): local_db.apply_unit_first_schema(home,host,name,binding,url)
                connect.assert_not_called()
        for h, owner, container, sha in ((home,host,name,'bad'), (home,'foreign',name,binding),
                                        (home,host,'foreign',binding), (self.here/'foreign',host,name,binding)):
            with self.subTest(home=h,owner=owner), patch.object(local_db,'docker') as docker:
                with self.assertRaises(Stop):
                    with local_db.database(sha, home=h, host=owner, name=container): self.fail('yielded')
                docker.assert_not_called()
        # 0023 preflight precedes local schema relaxation and ready/dump effects.
        calls=[]
        class Cursor:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def execute(self,*args): calls.append(args[0])
        class Conn:
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def cursor(self): return Cursor()
        def fake_docker(*args):
            if args[0]=='port': return b'127.0.0.1:54321'
            return b''
        with patch.object(local_db,'docker',side_effect=fake_docker) as docker, \
             patch('store_pg.connect',return_value=Conn()), \
             patch.object(local_db,'preflight_validation_receipts',side_effect=Stop('0023 required')), \
             patch.object(local_db,'apply_unit_first_schema') as schema:
            with self.assertRaisesRegex(Stop,'0023'):
                with local_db.database(binding,home=home,host=host,name=name): self.fail('yielded')
            schema.assert_not_called()
            self.assertIn(('rm','-f','-v',name), [x.args for x in docker.call_args_list])
            self.assertFalse((home/'state/database.dump').exists())
            self.assertFalse((home/'state/unit-first-schema.json').exists())


if __name__ == '__main__': unittest.main()
