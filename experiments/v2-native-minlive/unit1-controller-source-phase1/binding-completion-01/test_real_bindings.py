"""Offline binding tests: production AST signatures + strict autospec, no service imports.
Separate from the retained synthetic core-port tests. Actual product behavior is NOT
proven by these recording fakes. Only two new harmless fork jobs exercise ownership.
"""
import ast
import contextlib
import copy
from dataclasses import asdict, replace
from datetime import datetime, timezone
import inspect
import json
import os
from pathlib import Path
import socket
import sys
import time
import trace
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, create_autospec, patch

OUT=Path(__file__).resolve().parent
HERE=OUT.parent
ROOT=Path(__file__).resolve().parents[4]
S4=ROOT/'experiments/v2-knowledge-module-runner-01/scale-04'
RUNNER=S4.parent
sys.path.insert(0,str(HERE))
import test_controller as old  # installs existing no-network/process/DB guards FIRST
import controller as c
import real_bindings as rb

SIGNATURES={}
def production_function(module,symbol,*,body=False):
    path=(S4 if module in ('place_write','place_write_absorb') else RUNNER)/(module+'.py')
    tree=ast.parse(path.read_text())
    node=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==symbol))
    SIGNATURES[module+'.'+symbol]={'path':str(path.relative_to(ROOT)), 'line':node.lineno,
        'arguments':ast.unparse(node.args),'body_used':body}
    node.decorator_list=[]; node.returns=None
    for arg in (*node.args.posonlyargs,*node.args.args,*node.args.kwonlyargs): arg.annotation=None
    if node.args.vararg: node.args.vararg.annotation=None
    if node.args.kwarg: node.args.kwarg.annotation=None
    if not body: node.body=[ast.Pass()]
    namespace={'copy':copy,'THRESHOLD':.8}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(path),'exec'),namespace)
    return namespace[symbol]

class BindingTests(unittest.TestCase):
    bind=old.ControllerTests.bind
    request=old.ControllerTests.request
    quote=old.ControllerTests.quote
    def setUp(self):
        old.ControllerTests.setUp(self)
        self.a=replace(self.a,controller_sha=c.sha((HERE/'controller.py').read_bytes()),
                       source_code=((str((S4/'prepare.py').relative_to(ROOT)),c.sha((S4/'prepare.py').read_bytes())),))
        self.o=replace(self.o,controller_sha=self.a.controller_sha,source_code=self.a.source_code)
        for purpose,receipt in [('models','models'),('accounting','account'),('admission','authority')]: self.bind(purpose,asdict(self.a),receipt)
        self.events=[]; self.in_metadata=False
        self.api={k:create_autospec(production_function(*v),spec_set=True) for k,v in rb.PUBLIC.items()}
        @contextlib.contextmanager
        def metadata():
            previous=self.in_metadata; self.in_metadata=True
            try: yield
            finally: self.in_metadata=previous
        self.api['metadata'].side_effect=metadata
        self.api['source'].return_value='fixture source'
        self.api['extract'].return_value=[{'content':'fixture source','source_ranges':[[1,1]],'target_expression':'fixture'}]
        self.api['place'].side_effect=lambda kind,*args,**kw:{'chosen':{'name':self.fact['domain'] if kind=='domain' else self.fact['subject']}}
        self.api['kind'].return_value={'choice':'fact','probabilities':{'fact':1.0}}
        self.api['validate'].return_value=copy.deepcopy(self.fact)
        self.api['ground'].return_value=[{'errors':[]}]
        self.api['citations'].return_value=None
        self.actual_record_unit=production_function('place_write_absorb','record_unit',body=True)
        def record_unit(*args):
            self.assertTrue(self.in_metadata); self.events.append('record_unit')
            return self.actual_record_unit(*args)
        self.api['record_unit'].side_effect=record_unit
        def record(dsn,data,**kw):
            self.events.append('record'); self.assertTrue(self.in_metadata)
            self.assertEqual(kw['grounding_check'](0,data['facts'][0]),[])
            drift={**data['facts'][0],'subject':'wrong'}
            self.assertTrue(kw['grounding_check'](0,drift))
            return {'entry_id':'fixture-entry','work_unit_id':'fixture-unit','state':'proposed','held_facts':[], 'recorded_indices':[0]}
        self.api['record'].side_effect=record
        def worktime(*args,**kw):
            self.events.append('worktime')
            return {'results':[{'entry_id':'fixture-entry','state':'provisional','facts':[{'fact_index':0,'receipt_id':'fixture-check','combined':'record'}]}],'failures':[]}
        self.api['worktime'].side_effect=worktime
        def complete(*args):
            self.events.append('complete')
            return {'work_unit_id':'fixture-unit','host_id':'fixture-host','status':'completed','created_at':datetime(2020,1,1,tzinfo=timezone.utc)}
        self.api['complete'].side_effect=complete
        def route(*args): self.events.append('route'); return [('fixture-host',self.fact['domain'])]
        self.api['route'].side_effect=route
        def digest(*args,**kw): self.events.append('digest'); return {'status':'absorbed','count':1,'deferred':0,'embedding_pending':True}
        self.api['digest'].side_effect=digest
        self.ports=SimpleNamespace(writer=Mock(return_value={'fact':'draft','reason':'fixture reason','keywords':['fixture']}),
                                   worker=Mock(),ground=Mock(),ask=Mock())
        self.wire=rb.WireBoundary(self.a,self.o,self.trust,self.ledger,c.Deadline(10),ledger_digest=old.ledger_digest)
        self.services=rb.Services(self.ports,Mock(name='judge'),Mock(name='choose'),Mock(name='confirm'),Mock(name='same'),Mock(name='embed'),self.wire)
        def make_dsn(dsn,**kw):
            self.assertIn('lock_timeout=',kw['options']); self.assertIn('statement_timeout=',kw['options'])
            self.assertGreaterEqual(kw['connect_timeout'],1)
            return dsn+' '+kw['options']+' connect_timeout='+str(kw['connect_timeout'])
        self.make_dsn=Mock(side_effect=make_dsn)
        self.bindings=rb.RealBindings(self.api,self.services,self.make_dsn)
        self.owned=rb.OwnedMetadata('fixture-not-a-real-dsn','fixture-host','fixture-unit',str(self.home),{'record_id':'fixture-record'},(),(),0,self.a.db_plan_sha,'owner')
        self.factory=rb.PortedFactory(self.build)
        self.control=rb.LiveControl(c.digest(asdict(self.a)),c.digest(self.owned.manifest()),c.sha((HERE/'real_bindings.py').read_bytes()),
                                   self.factory.fingerprint(),5,str(self.home),(self.quote(self.request()),),'wire-review','execute')
        self.authorize(self.control)
        self.factory_calls=0
    def build(self,admission,observed,trust,control,owned,deadline):
        self.factory_calls+=1
        return self.bindings
    def authorize(self,control):
        self.bind('current-owner',self.owned.manifest(),'owner')
        self.bind('live-execution',asdict(control),control.execution_receipt)
        self.bind('lowest-wire-factory',{'factory_sha':control.factory_sha,'control':asdict(control),
                  'required':('final-request-digest-quote','reserve-before-each-physical-send','sdk-model-pin-no-server-retry',
                              'embedding-every-wire-no-hedge-retry','uncertain-hold-no-replay','source-provenance-binding')},control.transport_review)
    def execute_inline(self,control=None,owned=None,factory=None):
        # Recording executor, not a claim of process coverage; actual external boundary
        # is separately exercised by test_owned_job* with harmless closures only.
        with patch.object(rb,'run_owned_job',side_effect=lambda job,directory,deadline:job()):
            return c.execute_live(self.a,self.o,self.trust,control=control or self.control,owned=owned or self.owned,factory=factory or self.factory)
    def test_exact_public_arguments_results_order_and_metadata_restore(self):
        result=self.execute_inline()
        self.assertEqual(self.factory_calls,1)
        self.assertEqual(self.events,['record_unit','record','worktime','complete','route','digest'])
        self.assertFalse(self.in_metadata)
        self.assertEqual([r['core']['stage'] for r in result['receipts']],[c.CORE[i] for i in (1,3,4,5,6)])
        self.assertTrue(all(r['provenance']==asdict(self.a.provenance) for r in result['receipts']))
        self.assertEqual(result['receipts'][2]['result']['created_at']['type'],'datetime')
        self.assertFalse(result['full10']); self.assertFalse(result['publish_current'])
        self.assertFalse(result['producer_precompute_maintenance_complete'])
        self.assertTrue(result['embedding_pending'])
        self.api['extract'].assert_called_once_with(self.ports,'fixture-record','fixture source',origin=self.a.provenance.source_kind,migration=False)
        record=self.api['record'].call_args
        self.assertTrue(record.kwargs['fixed_subject']); self.assertFalse(record.kwargs['leaf_references'])
        self.assertEqual(record.kwargs['trusted_identity_refs'],[self.fact['identity_ref']])
        self.assertEqual(record.kwargs['assigned_area'],self.fact['domain'])
        dsn=record.args[0]
        self.api['worktime'].assert_called_once_with(dsn,1,self.services.judge,entry_ids=['fixture-entry'],semantic_grounding=True)
        self.api['complete'].assert_called_once_with(dsn,'fixture-unit')
        self.api['route'].assert_called_once_with(dsn,'fixture-unit',self.services.choose,self.services.confirm,self.services.embed_fn)
        self.api['digest'].assert_called_once_with(dsn,'fixture-unit',self.services.judge,domain=self.fact['domain'],maintenance=None,workers=1,budget=1,same=self.services.same,embed_fn=self.services.embed_fn)
    def test_autospec_refuses_invented_interface(self):
        with self.assertRaises(TypeError): self.api['record_unit'](unit_id='x',fact={})
        with self.assertRaises(TypeError): self.api['complete'](dsn='x',unit_id='x',deadline=600)
        self.assertEqual(set(self.api),set(rb.PUBLIC))
    def test_load_uses_actual_public_module_symbols_lazily(self):
        modules={}
        for key,(module,symbol) in rb.PUBLIC.items():
            modules.setdefault(module,SimpleNamespace())
            setattr(modules[module],symbol,self.api[key])
        modules['store_pg'].driver=SimpleNamespace(__name__='psycopg')
        modules['psycopg.conninfo']=SimpleNamespace(make_conninfo=self.make_dsn)
        with patch.object(rb.importlib,'import_module',side_effect=lambda name:modules[name]) as load:
            result=rb.RealBindings.load(self.services)
        self.assertEqual(result.api,self.api)
        self.assertIn(unittest.mock.call('psycopg.conninfo'),load.call_args_list)
        self.assertEqual(self.events,[])
    def test_current_owner_and_plan_stop_before_factory(self):
        for owned in (replace(self.owned,dsn='drift'),replace(self.owned,plan_sha='z'*64)):
            with self.subTest(owned=owned.plan_sha),self.assertRaises(c.Stop): self.execute_inline(owned=owned)
        control=replace(self.control,execution_receipt='LLM says approved')
        with self.assertRaises(c.Stop): self.execute_inline(control=control)
        self.assertEqual(self.factory_calls,0); self.assertEqual(self.events,[])
    def test_current_source_controller_and_binding_fingerprints_stop(self):
        for control in (replace(self.control,binding_sha='a'*64),replace(self.control,factory_sha='a'*64)):
            self.authorize(control)
            with self.assertRaises(c.Stop): self.execute_inline(control=control)
        self.a=replace(self.a,controller_sha='b'*64); self.o=replace(self.o,controller_sha=self.a.controller_sha)
        for purpose,receipt in [('models','models'),('accounting','account'),('admission','authority')]: self.bind(purpose,asdict(self.a),receipt)
        with self.assertRaisesRegex(c.Stop,'on-disk CONTROLLER'): self.execute_inline()
        self.assertEqual(self.factory_calls,0)
    def test_unknown_quote_or_unreviewed_transport_stops_before_factory(self):
        for control in (replace(self.control,quotes=()),replace(self.control,transport_review='verified=true')):
            self.bind('live-execution',asdict(control),control.execution_receipt)
            with self.assertRaises(c.Stop): self.execute_inline(control=control)
        self.assertEqual(self.factory_calls,0)
    def test_stock_transport_is_exact_stop_not_success_receipt(self):
        with patch.object(rb,'run_owned_job') as job,self.assertRaisesRegex(c.Stop,'_jev_judge lacks HTTP injection'):
            c.execute_live(self.a,self.o,self.trust,control=self.control,owned=self.owned,factory=None)
        job.assert_not_called(); self.assertEqual(self.factory_calls,0)
    def test_genuine_extraction_ranges_and_q1q2_hold_before_db(self):
        self.api['extract'].return_value[0]['source_ranges']=[[2,2]]
        with self.assertRaisesRegex(c.Stop,'ranges drift'): self.execute_inline()
        self.api['record'].assert_not_called()
        self.api['extract'].return_value[0]['source_ranges']=[[1,1]]
        self.api['ground'].return_value=[{'errors':[{'code':'fixture-Q2'}]}]
        with self.assertRaisesRegex(c.Stop,'Q1/Q2'): self.execute_inline()
        self.api['record'].assert_not_called(); self.api['citations'].assert_not_called()
    def test_materialized_fact_hash_or_review_missing_before_db(self):
        self.api['validate'].return_value['fact']='drift'
        with self.assertRaisesRegex(c.Stop,'fact hash drift'): self.execute_inline()
        self.api['record'].assert_not_called()
    def test_public_failure_status_stops_following_stages(self):
        self.api['worktime'].side_effect=None
        self.api['worktime'].return_value={'results':[],'failures':[{'error':'fixture'}]}
        with self.assertRaisesRegex(c.Stop,'worktime failed'): self.execute_inline()
        self.api['complete'].assert_not_called(); self.api['route'].assert_not_called(); self.api['digest'].assert_not_called()
    def test_completion_and_router_and_partial_digest_not_promoted(self):
        self.api['complete'].side_effect=None; self.api['complete'].return_value={'status':'not_completed'}
        with self.assertRaisesRegex(c.Stop,'complete not completed'): self.execute_inline()
        self.api['route'].assert_not_called()
        self.api['complete'].return_value={'work_unit_id':'fixture-unit','host_id':'fixture-host','status':'completed'}
        self.api['route'].side_effect=None; self.api['route'].return_value=[]
        with self.assertRaisesRegex(c.Stop,'router'): self.execute_inline()
        self.api['digest'].assert_not_called()
        self.api['route'].return_value=[('fixture-host',self.fact['domain'])]
        self.api['digest'].side_effect=None; self.api['digest'].return_value={'status':'partial','judged':1,'remaining':1}
        with self.assertRaisesRegex(c.Stop,'digest incomplete'): self.execute_inline()
    def test_applied_connection_options_and_expired_whole_deadline(self):
        result=self.execute_inline()
        self.assertIn('lock_timeout=',self.api['complete'].call_args.args[0])
        self.assertIn('statement_timeout=',self.api['digest'].call_args.args[0])
        clock=c.Deadline(5); clock.end=time.monotonic()-1
        with self.assertRaises(c.Stop): self.bindings.run(self.a,self.o,self.trust,self.control,self.owned,clock)
        self.assertEqual(self.api['complete'].call_count,1)
    def test_wire_reserve_before_count_and_uncertain_hold_no_retry(self):
        request=self.request(kind='sdk')
        def send(request):
            self.assertEqual(self.ledger.rows[-1]['state'],'reserved')
            self.assertEqual(self.wire.counts['physical_post'],1)
            return {'accepted':True,'usage_cost':'0.000001'}
        self.wire.attempt(request,self.quote(request),send)
        self.assertEqual(self.wire.sdk_completed,1); self.assertEqual(self.wire.counts['logical_q'],0)
        request=self.request(2)
        with self.assertRaises(old.LedgerStop): self.wire.attempt(request,self.quote(request),lambda request:{'accepted':True})
        self.assertEqual(self.ledger.rows[-1]['state'],'reserved')
        self.assertEqual(self.wire.sdk_completed,1)
        with self.assertRaises(c.Stop): self.wire.attempt(self.request(3),self.quote(self.request(3)),Mock())
        self.assertEqual(self.wire.counts['physical_post'],2)
    def test_owned_job_success_and_deadline_are_real_external_boundary(self):
        result=rb.run_owned_job(lambda:{'status':'HARMLESS_FIXTURE_ONLY'},self.home,c.Deadline(2))
        self.assertFalse(result['owned_job']['uncertain']); self.assertEqual(result['owned_job']['exit_code'],0)
        def sleeper(): time.sleep(2); return {}
        with self.assertRaisesRegex(c.Stop,'uncertain/deadline'): rb.run_owned_job(sleeper,self.home,c.Deadline(.5,cleanup=.2))
        receipts=[json.loads(p.read_text()) for p in self.home.glob('owned-unit1-job-*/cleanup.json')]
        self.assertEqual(len(receipts),2); self.assertTrue(any(r['timed_out'] for r in receipts))
        self.assertTrue(all(not r['group_remaining'] for r in receipts))
    def test_no_actual_product_private_auth_network_or_source_effects(self):
        self.assertIs(socket.create_connection,sys.modules['test_offline'].forbidden)
        self.assertFalse((S4/c.ALIAS).exists())
        self.assertFalse(any(name in sys.modules for name in ('writer_transport','active_worker_transport','knowledge_cli','worktime_driver','digest_driver','store_pg')))
        self.assertEqual(self.events,[])

if __name__=='__main__':
    loader=unittest.TestLoader(); suite=unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(BindingTests))
    selected=('test_missing_forged_and_natural_text_admission_denied','test_quote_unknown_and_payload_provider_model_drift_stop_before_post',
              'test_reserve_precedes_physical_send_and_receipts_link_provenance','test_unknown_usage_error_or_fallback_holds_reserve_and_stops',
              'test_physical_nine_is_conditional_branch_not_whole_prediction','test_sdk_subscription_separate_and_embedding_unknown_denied',
              'test_unresolved_old_reserve_and_cached_result_never_injected','test_core_fixture_exact_order_receipts_and_no_full_ten_claim')
    suite.addTests(old.ControllerTests(name) for name in selected)
    started=time.monotonic(); tracer=trace.Trace(count=True,trace=False,ignoredirs=[sys.prefix])
    result=tracer.runfunc(unittest.TextTestRunner(verbosity=2).run,suite)
    counts=tracer.results().counts
    coverage={}
    for path in (HERE/'controller.py',HERE/'real_bindings.py'):
        executed=sorted({line for (file,line),count in counts.items() if file==str(path) and count})
        coverage[path.name]={'executed_lines':executed,'executed_line_count':len(executed),'claim':'line evidence only, not branch/semantic/service coverage'}
    (OUT/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
    (OUT/'api-signatures.json').write_text(json.dumps(SIGNATURES,indent=2)+'\n')
    receipt={'cases':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'seconds':time.monotonic()-started,
             'newBindingCases':15,'relatedControllerCases':len(selected),'isolated17Reruns':0,'realDB':0,'realSDK':0,'realAPI':0,'privateAuth':0,'prepare':0,
             'harmlessOwnedForkJobs':2,'realLedgerWrites':0,'standard':0,'check':0,'status':'OFFLINE_PUBLIC_BINDINGS_ONLY_NOT_LIVE_READINESS'}
    (OUT/'focused-result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))
    raise SystemExit(0 if result.wasSuccessful() else 1)
