"""Single bounded focused entry: existing isolated + current + controller fixtures.
Network/process/DB guards installed before product imports; no pytest/conftest.
Only two explicitly tagged harmless fixture processes may use the saved Popen.
"""
import contextlib
from dataclasses import asdict, replace
from decimal import Decimal
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
RAW_POPEN = subprocess.Popen
HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
S4 = ROOT/'experiments/v2-knowledge-module-runner-01/scale-04'
sys.path.insert(0,str(S4))
import test_isolated_scope_offline as scopes  # imports test_offline guards first
from safety import Ledger, Stop as LedgerStop, digest as ledger_digest
import controller as c

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='owned-unit1-')
        self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name)
        self.fact={'fact':'Synthetic subject is synthetic.','subject':'Synthetic subject','domain':'Synthetic',
                   'identity_ref':{'origin':'fixture','subject_id':'fixture-id'},
                   'evidence_refs':[{'source':'fixture','lines':[1,1]}],'source_unit':'fixture-unit'}
        p=c.Provenance('caller-owned-fixture','snapshot historical fixture','fixture epoch','snapshot',
                       'fixture://owned/source',c.sha(b'fixture source'),((1,1),),'review',c.digest(self.fact),'audit','lineage')
        self.a=c.Admission(c.ALIAS,(('fixture.py','a'*64),),'b'*64,'c'*64,p,c.CORE,c.CARRY,'models','account','authority','d'*64)
        self.o=c.Observed(self.a.source_code,self.a.controller_sha,self.a.db_plan_sha,p.source_sha,p.fact_sha,self.a.inventory_sha)
        # Exact fixture registry owned by code, not a packet boolean or free-text authority.
        self.registry=set()
        self.trust=c.Trust(lambda purpose,hash_,receipt:(purpose,hash_,receipt) in self.registry)
        for purpose,receipt in [('source-review','review'),('source-audit','audit'),('artifact-lineage','lineage')]:
            self.bind(purpose,asdict(p),receipt)
        for purpose,receipt in [('models','models'),('accounting','account'),('admission','authority')]:
            self.bind(purpose,asdict(self.a),receipt)
        self.bind('fact-materialization',self.fact,'lineage')
        self.ledger=Ledger(self.home/'fixture-ledger.jsonl',self.a.db_plan_sha,
                           {'judging':.039,'generation':1},
                           subscription_limits={'fixture-sdk':{'calls':3,'seconds':2700,'per_call_seconds':900}},
                           cash_limit=.039)
        self.send=Mock(return_value={'accepted':True,'usage_cost':'0.000001'})

    def bind(self,purpose,value,receipt): self.registry.add((purpose,c.digest(value),receipt))
    def boundary(self):
        return c.SyntheticBoundary(self.a,self.o,self.trust,self.ledger,c.Deadline(10),ledger_digest=ledger_digest,fixture=True)
    def request(self,index=0,kind='jev',q=1):
        return c.Request(kind,'fixture-provider','fixture-sdk' if kind=='sdk' else 'fixture-model','fixture-role',('fixture body '+str(index)).encode(),q if kind=='jev' else 0)
    def quote(self,request,**kw):
        value=c.Quote(c.digest(c.request_identity(request)),self.a.inventory_sha,self.ledger.binding,'0.001',time.time()+30,'fixture-quote')
        value=replace(value,**kw)
        self.bind('quote',asdict(value),value.receipt)
        return value

    def test_valid_preflight_is_nonexecuting_and_preserves_snapshot_metadata(self):
        result=c.preflight(self.a,self.o,self.trust)
        self.assertEqual(result['status'],'PREFLIGHT_ONLY')
        self.assertFalse(result['live_allowed'])
        self.assertFalse(result['semantic_quality_guaranteed'])
        self.assertEqual(result['provenance'],asdict(self.a.provenance))
        self.assertFalse(self.ledger.path.exists())
        self.send.assert_not_called()

    def test_missing_forged_and_natural_text_admission_denied(self):
        for a,trust in ((None,self.trust),('진행',self.trust),({},self.trust),
                        (replace(self.a,authority_receipt='file-exists'),self.trust),(self.a,c.Trust(None))):
            with self.subTest(a=type(a).__name__),self.assertRaises(c.Stop): c.preflight(a,self.o,trust)
        with self.assertRaises(c.Stop): c.execute_live(self.a)
        self.send.assert_not_called()

    def test_source_controller_plan_fact_and_inventory_drift_denied(self):
        for kw in ({'source_code':(('fixture.py','e'*64),)},{'controller_sha':'e'*64},
                   {'db_plan_sha':'e'*64},{'source_sha':'e'*64},{'fact_sha':'e'*64},{'inventory_sha':'UNKNOWN'}):
            with self.subTest(kw=kw),self.assertRaises(c.Stop): c.preflight(self.a,replace(self.o,**kw),self.trust)
        self.assertFalse(self.ledger.path.exists())

    def test_status_asof_current_promotion_and_unreviewed_changes_denied(self):
        for field,value in (('asof',''),('status',''),('source_kind',''),('source_ref',''),
                            ('asof_scope','upstream-current'),('status','current rewritten'),
                            ('review_receipt',''),('audit_receipt',''),('lineage_receipt',''),('ranges',((0,1),))):
            a=replace(self.a,provenance=replace(self.a.provenance,**{field:value}))
            with self.subTest(field=field,value=value),self.assertRaises(c.Stop): c.preflight(a,self.o,self.trust)
        with self.assertRaises(c.Stop): c.preflight(replace(self.a,publish_current=True),self.o,self.trust)
        self.send.assert_not_called()

    def test_budget_carry_or_missing_model_accounting_authority_denied(self):
        for kw in ({'carry':('new namespace fresh cash',)}, {'model_approval':''},{'accounting_approval':''}):
            with self.subTest(kw=kw),self.assertRaises(c.Stop): c.preflight(replace(self.a,**kw),self.o,self.trust)
        self.assertEqual(c.CARRY,('0.50','0.40','0.04','0.001','0.039','0.006',1,900))

    def test_quote_unknown_and_payload_provider_model_drift_stop_before_post(self):
        r=self.request()
        quotes=[None,self.quote(r,max_cost='NaN'),self.quote(r,max_cost='0'),
                self.quote(r,expires=time.time()-1),self.quote(r,inventory_sha='UNKNOWN'),
                self.quote(r,request_sha='e'*64),self.quote(r,ledger_binding='e'*64)]
        for quote in quotes:
            b=self.boundary()
            with self.subTest(quote=quote),self.assertRaises((c.Stop,ArithmeticError)): b.attempt(r,quote,self.send)
            self.assertEqual(b.counts['physical_post'],0)
        for changed in (replace(r,provider='other'),replace(r,model='other'),replace(r,body=b'drift')):
            with self.assertRaises(c.Stop): self.boundary().attempt(changed,self.quote(r),self.send)
        self.send.assert_not_called()
        self.assertFalse(self.ledger.path.exists())

    def test_reserve_precedes_physical_send_and_receipts_link_provenance(self):
        b=self.boundary(); r=self.request(q=2)
        def send(request):
            self.assertEqual(self.ledger.rows[-1]['state'],'reserved')
            self.assertEqual(b.counts['physical_post'],1)
            return {'accepted':True,'usage_cost':'0.000001'}
        result=b.attempt(r,self.quote(r),send)
        self.assertEqual(result['provenance'],asdict(self.a.provenance))
        self.assertEqual(b.counts,{'physical_post':1,'jev_http':1,'logical_q':2,'sdk_subscription':0,'embedding_post':0})
        self.assertEqual(self.ledger.rows[-1]['state'],'done')

    def test_unknown_usage_error_or_fallback_holds_reserve_and_stops(self):
        for index,result in enumerate(({'accepted':True}, {'accepted':False,'usage_cost':'0'}, {'accepted':True,'usage_cost':'NaN'})):
            ledger=Ledger(self.home/f'uncertain-{index}.jsonl',self.a.db_plan_sha,{'judging':.039},cash_limit=.039)
            b=c.SyntheticBoundary(self.a,self.o,self.trust,ledger,c.Deadline(5),ledger_digest=ledger_digest,fixture=True)
            r=self.request(index)
            with self.assertRaises(LedgerStop): b.attempt(r,self.quote(r),lambda request:result)
            self.assertEqual(ledger.rows[-1]['state'],'reserved')
            with self.assertRaises(c.Stop): b.attempt(self.request(99),self.quote(self.request(99)),self.send)
            self.assertEqual(b.counts['physical_post'],1)
        self.send.assert_not_called()

    def test_physical_nine_is_conditional_branch_not_whole_prediction(self):
        b=self.boundary()
        for index in range(9):
            r=self.request(index); b.attempt(r,self.quote(r),self.send)
        r=self.request(10)
        with self.assertRaises(c.Stop): b.attempt(r,self.quote(r),self.send)
        self.assertEqual(self.send.call_count,9)
        self.assertEqual(b.counts['physical_post'],9)
        self.assertEqual(b.counts['logical_q'],9)

    def test_sdk_subscription_separate_and_embedding_unknown_denied(self):
        b=self.boundary()
        for i in range(2):
            r=self.request(i,kind='sdk'); b.attempt(r,self.quote(r),self.send)
        r=self.request(3,kind='sdk')
        with self.assertRaises(c.Stop): b.attempt(r,self.quote(r),self.send)
        self.assertEqual(b.counts['sdk_subscription'],2)
        self.assertEqual(b.counts['logical_q'],0)
        r=self.request(kind='embedding')
        with self.assertRaises(c.Stop): self.boundary().attempt(r,self.quote(r),self.send)
        self.assertEqual(self.send.call_count,2)

    def test_unresolved_old_reserve_and_cached_result_never_injected(self):
        r=self.request(); b=self.boundary()
        b.attempt(r,self.quote(r),self.send)
        with self.assertRaises(c.Stop): self.boundary().attempt(r,self.quote(r),self.send)
        self.assertEqual(self.send.call_count,1)
        self.ledger.append(dict(id='old-unknown',step='judging',state='reserved',charge=.006,account='cash'))
        r=self.request(2)
        with self.assertRaises(LedgerStop): self.boundary().attempt(r,self.quote(r),self.send)
        self.assertEqual(self.send.call_count,1)

    def test_core_fixture_exact_order_receipts_and_no_full_ten_claim(self):
        visited=[]; packet=c.preflight(self.a,self.o,self.trust)
        def record(**args): visited.append(c.CORE[2])
        def port(stage):
            def call(**args):
                visited.append(stage)
                if stage==c.CORE[1]: args['record'](**args)
                if stage==c.CORE[3]: self.assertEqual(args['entry_ids'],['fixture-entry'])
                row=c.CoreReceipt(stage,'fixture-unit','fixture-entry',self.fact['domain'],self.o.fact_sha,packet['admission_sha'],'core',True)
                self.bind('core-receipt',asdict(row),'core')
                return row
            return call
        ports={stage:port(stage) for stage in c.CORE}
        ports[c.CORE[0]]=contextlib.nullcontext
        ports[c.CORE[2]]=record
        result=c.run_fixture_core(self.a,self.o,self.trust,self.fact,'fixture-unit',ports,c.Deadline(5),fixture=True)
        self.assertEqual(visited,list(c.CORE[1:]))
        self.assertFalse(result['full10'])
        self.assertEqual(len(result['receipts']),5)
        self.assertTrue(all(r['provenance']==asdict(self.a.provenance) for r in result['receipts']))
        with self.assertRaises(c.Stop): c.run_fixture_core(self.a,self.o,self.trust,self.fact,'fixture-unit',ports,c.Deadline(5))
        ports[c.CORE[4]]=lambda **kw: None
        with self.assertRaises(c.Stop): c.run_fixture_core(self.a,self.o,self.trust,self.fact,'fixture-unit',ports,c.Deadline(5),fixture=True)

    def test_whole_deadline_and_db_lock_options_are_distinct(self):
        with self.assertRaises(c.Stop): c.Deadline(900)
        clock=c.Deadline(3)
        self.assertIn('lock_timeout=',clock.db_options()['options'])
        clock.end=time.monotonic()-1
        with self.assertRaises(c.Stop): clock.remaining()
        b=self.boundary(); b.deadline=clock; r=self.request()
        with self.assertRaises(c.Stop): b.attempt(r,self.quote(r),self.send)
        self.send.assert_not_called()

    def test_owned_child_positive_and_deadline_group_cleanup(self):
        # Only saved raw Popen for these two harmless tagged fixtures; never a service.
        with patch.object(c.subprocess,'Popen',RAW_POPEN):
            result=c.run_owned_fixture([sys.executable,'-I','-B',str(HERE/'fixture_child.py'),'ok'],self.home,c.Deadline(2),fixture=True)
            self.assertEqual(result['exit_code'],0)
            clock=c.Deadline(1,cleanup=.3)
            with self.assertRaisesRegex(c.Stop,'deadline/error'):
                c.run_owned_fixture([sys.executable,'-I','-B',str(HERE/'fixture_child.py'),'tree'],self.home,clock,fixture=True)
        receipt=json.loads((self.home/'receipt.json').read_text())
        self.assertTrue(receipt['timed_out'])
        self.assertLess(receipt['seconds'],1)
        self.assertGreaterEqual(len(receipt['cleanup_members']),2)
        for name in ('child.pid','grandchild.pid'):
            pid=int((self.home/name).read_text())
            stat=Path(f'/proc/{pid}/stat')
            if stat.exists(): self.assertEqual(stat.read_text().rsplit(')',1)[1].split()[0],'Z')

    def test_zero_live_effects_guards_present(self):
        self.assertIs(socket.create_connection,sys.modules['test_offline'].forbidden)
        self.assertIs(subprocess.Popen,sys.modules['test_offline'].forbidden)
        self.assertFalse((S4/c.ALIAS).exists())
        self.assertFalse(any(name in sys.modules for name in ('writer_host','writer_transport','active_worker_transport')))
        self.send.assert_not_called()

if __name__=='__main__':
    suite=unittest.TestSuite()
    loader=unittest.TestLoader()
    if len(sys.argv)>1:
        suite.addTests(loader.loadTestsFromNames(sys.argv[1:],sys.modules[__name__]))
    else:
        for cls in (scopes.SyntheticPreparation,scopes.CurrentAlias,ControllerTests): suite.addTests(loader.loadTestsFromTestCase(cls))
    started=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    receipt={'cases':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
             'seconds':time.monotonic()-started,'realDB':0,'model':0,'SDK':0,'auth':0,'network':0,
             'productProcess':0,'harmlessOwnedFixtureChildren':2 if len(sys.argv)==1 else 'selected-only',
             'standard':'PENDING_NOT_STARTED','realAliasExists':(S4/c.ALIAS).exists()}
    (HERE/('focused-result.json' if len(sys.argv)==1 else 'repair-result.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
    raise SystemExit(0 if result.wasSuccessful() else 1)
