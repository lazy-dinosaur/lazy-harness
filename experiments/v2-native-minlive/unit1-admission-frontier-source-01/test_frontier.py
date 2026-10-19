"""Task152 guarded public entry + real Factory validators, synthetic services only."""
import copy,json,sys,time,unittest
from dataclasses import asdict,replace
from pathlib import Path
from unittest.mock import Mock,patch
OUT=Path(__file__).resolve().parent; BASE=OUT.parent/'unit1-controller-source-phase1'
sys.path[:0]=[str(BASE),str(OUT.parent/'unit1-stage-control-01'),str(BASE/'binding-completion-01')]
import test_stages as legacy
import test_real_bindings as previous
import controller as c
import real_bindings as rb
import native_services as ns
TRACES=[]
class FrontierTests(unittest.TestCase):
    bind=previous.BindingTests.bind
    request=previous.BindingTests.request
    quote=previous.BindingTests.quote
    authorize=previous.BindingTests.authorize
    values=legacy.StageTests.values
    db=legacy.StageTests.db
    prior=legacy.StageTests.prior
    bind_prior=legacy.StageTests.bind_prior
    execute=legacy.StageTests.execute
    def setUp(self):
        previous.BindingTests.setUp(self)
        self.ledger.path.touch()
        self.factory=rb.PortedFactory(self.build)
        self.control=replace(self.control,factory_sha=self.factory.fingerprint())
        self.authorize(self.control)
        self.start=time.time()-1;self.end=self.start+60
    def build(self,admission,observed,trust,control,owned,deadline):
        self.factory_calls+=1
        self.wire=rb.WireBoundary(admission,observed,trust,self.ledger,deadline,ledger_digest=previous.old.ledger_digest)
        self.services=replace(self.services,wire=self.wire)
        self.bindings=rb.RealBindings(self.api,self.services,self.make_dsn)
        return self.bindings
    def admission(self,fact_sha=''):
        self.a=replace(self.a,provenance=replace(self.a.provenance,fact_sha=fact_sha))
        self.o=replace(self.o,fact_sha=fact_sha)
        for purpose,receipt in [('source-review','review'),('source-audit','audit'),('artifact-lineage','lineage')]:self.bind(purpose,asdict(self.a.provenance),receipt)
        for purpose,receipt in [('models','models'),('accounting','account'),('admission','authority')]:self.bind(purpose,asdict(self.a),receipt)
        self.control=replace(self.control,admission_sha=c.digest(asdict(self.a)))
    def grant(self,selected,quotes=None):
        g=rb.StageGrant(selected,str(self.ledger.path.resolve()),c.sha(self.ledger.path.read_bytes()),self.start,self.end,'grant')
        self.control=replace(self.control,stage_grant=g,quotes=self.control.quotes if quotes is None else quotes)
        self.authorize(self.control)
        self.bind('selected-stage-admission',{'admission':asdict(self.a),'control':asdict(self.control),'owned':self.owned.manifest()},'grant')
        return g
    def native(self,identities=(),quotes=()):
        cache=self.home/'cache';cache.mkdir(exist_ok=True);(cache/'declared.json').write_text('{}')
        auth=self.home/'synthetic-auth.mjs';auth.write_text('export const synthetic=true;')
        conf=self.home/'public.json';conf.write_text('{"embed":{"provider":"openrouter"}}')
        cfg=ns.NativeConfig('fixture-jev','https://synthetic.invalid/v1/systemone','https://synthetic.invalid/responses',
            str(auth),c.sha(auth.read_bytes()),str(conf),c.sha(conf.read_bytes()),str(cache),
            (('declared.json',c.sha((cache/'declared.json').read_bytes())),),'fixture-embed',str(self.ledger.path),
            (('generation',1),('judging',.039)),(('Luna',{'calls':2,'seconds':900,'per_call_seconds':450}),),290000,identities)
        self.control=replace(self.control,native=cfg,quotes=quotes)
        return cfg
    def factory_validate(self):
        # Exactly the admission verification used by the public entry. No validator
        # is mocked away. The context token is always scoped/reset.
        context=rb.validate_stage_grant(self.a,self.trust,self.control,self.owned,self.control.stage_grant.stages)
        token=c.SELECTED_ADMISSION.set(context)
        try:ns.CurrentNativeServicesFactory().validate(self.control)
        finally:c.SELECTED_ADMISSION.reset(token)
    def sdk_request(self,role='extract',body=b'fixture'):
        return c.Request('sdk','openai','gpt-6-luna',role,body)
    def history(self,sdk=0,jev=0,logical=0,pending=False):
        rows=[]
        for i in range(sdk+jev):
            req=c.request_identity(self.sdk_request(body=str(i).encode())) if i<sdk else c.request_identity(c.Request('jev','jev','fixture-jev','selection',str(i).encode(),logical if i==sdk else 0))
            ident='history-'+str(i)
            reserved={'id':ident,'binding':self.a.db_plan_sha,'step':'generation' if i<sdk else 'judging','state':'reserved','charge':.0001,'account':'subscription' if i<sdk else 'cash','model':'gpt-6-luna' if i<sdk else 'fixture-jev'}
            rows.append(reserved)
            if not pending:rows.append({**reserved,'state':'done','request':req,'seconds':1})
        self.ledger.path.write_text(''.join(json.dumps(r)+'\n' for r in rows));self.ledger.rows=rows
    def native_entry(self,selected):
        self.control=replace(self.control,factory_sha=ns.CurrentNativeServicesFactory().fingerprint())
        self.grant(selected,quotes=self.control.quotes)
        with patch.object(rb,'run_owned_job',side_effect=lambda job,directory,deadline:job()),patch.object(ns.CurrentNativeServicesFactory,'build',side_effect=self.build):
            return c.execute_live(self.a,self.o,self.trust,control=self.control,owned=self.owned,
                                  factory=ns.CurrentNativeServicesFactory(),stages=selected,
                                  prior=None if selected[0]=='source' else self.prior(selected[0],values={'text':'fixture source'}))
    def test_native_public_entry_zero_sdk_and_extract_only_quote_no_unused_write(self):
        self.admission();self.native()
        result=self.native_entry(('source',))
        self.assertEqual(result['values'],{'text':'fixture source'});self.assertEqual(self.wire.counts['physical_post'],0)
        r=self.sdk_request();q=self.quote(r);self.native((c.request_identity(r),),(q,))
        self.native_entry(('extract',))
        self.ports.writer.assert_not_called();self.make_dsn.assert_not_called();self.api['record'].assert_not_called()
    def test_source_prefix_without_future_fact_or_quotes_is_data_only(self):
        self.admission();self.grant(('source',),quotes=())
        with patch.object(rb,'read_stage_state',side_effect=AssertionError('DB forbidden')):
            result=self.execute(('source',))
        self.assertEqual(result['values'],{'text':'fixture source'})
        self.assertEqual(result['physical_counts'],dict.fromkeys(('physical_post','jev_http','logical_q','sdk_subscription','embedding_post'),0))
        self.assertNotIsInstance(result,rb.StagePrior);self.make_dsn.assert_not_called()
        self.api['extract'].assert_not_called();self.api['record'].assert_not_called()
        self.assertIsNone(c.SELECTED_ADMISSION.get())
        with self.assertRaises(c.Stop):c.preflight(self.a,self.o,self.trust)
        with self.assertRaises(c.Stop):self.execute(('extract',),result)
    def test_source_provenance_review_lineage_and_owner_still_required(self):
        self.admission();self.grant(('source',),quotes=())
        original=self.trust
        for purpose in ('source-review','source-audit','artifact-lineage','current-owner','live-execution','models','accounting','admission','lowest-wire-factory'):
            self.trust=c.Trust(lambda p,d,r,blocked=purpose:p!=blocked and original.verify(p,d,r))
            with self.subTest(purpose=purpose),self.assertRaises(c.Stop):self.execute(('source',))
        self.trust=original
        self.assertEqual(self.factory_calls,0)
    def test_prefix_through_citations_no_final_hash_then_current_external_readmission(self):
        self.admission();self.grant(rb.STAGES[:9])
        with patch.object(self.bindings,'stage',wraps=self.bindings.stage):
            result=self.execute(rb.STAGES[:9])
        self.assertEqual(result['selected_stages'],rb.STAGES[:9]);self.assertNotIn('review',result['selected_stages'])
        self.api['record'].assert_not_called()
        # Synthetic external verifier genuinely verifies this new current binding;
        # checkpoint output by itself is never used as permission or a typed prior.
        self.admission(c.digest(self.fact));self.grant(('review',))
        p=self.prior('review',values={'fact':copy.deepcopy(self.fact)})
        self.assertEqual(self.execute(('review',),p)['status'],'SELECTED_STAGES_RETURNED')
        self.assertEqual(self.api['source'].call_count,1);self.assertEqual(self.api['extract'].call_count,1)
    def test_extract_prefix_with_current_verified_source_prior_no_writer(self):
        self.admission();self.grant(('extract',))
        p=self.prior('extract',values={'text':'fixture source'})
        result=self.execute(('extract',),p)
        self.api['source'].assert_not_called();self.api['extract'].assert_called_once();self.ports.writer.assert_not_called()
        self.assertIn('unit',result['values']);self.make_dsn.assert_not_called()
    def test_review_record_need_actual_hash_and_materialization_before_db(self):
        for selected in (('review',),('record',),('review','record')):
            self.admission();self.grant(selected)
            p=self.prior(selected[0],values={'fact':copy.deepcopy(self.fact)})
            with self.subTest(selected=selected),self.assertRaises(c.Stop):self.execute(selected,p)
        self.admission(c.digest(self.fact));self.grant(('record',))
        p=self.prior('record',values={'fact':copy.deepcopy(self.fact)})
        old=self.trust;self.trust=c.Trust(lambda purpose,d,r:purpose!='fact-materialization' and old.verify(purpose,d,r))
        with self.assertRaises(c.Stop):self.execute(('record',),p)
        self.api['record'].assert_not_called();self.make_dsn.assert_not_called();self.assertEqual(self.factory_calls,0)
    def test_forged_malformed_mismatch_scope_and_expired_grants_stop(self):
        self.admission();good=self.grant(('source',),quotes=());control=self.control
        for stages in (('bogus',),('source','write'),('extract','source'),('source','source')):
            self.control=replace(control,stage_grant=replace(good,stages=stages))
            with self.subTest(stages=stages),self.assertRaises(c.Stop):self.execute(stages)
        self.control=control
        with self.assertRaises(c.Stop):self.execute(('source','extract'))
        self.control=replace(control,stage_grant=replace(good,receipt='forged'))
        with self.assertRaises(c.Stop):self.execute(('source',))
        self.end=time.time()-1;self.start=self.end-50;self.grant(('source',),quotes=())
        with self.assertRaises(c.Stop):self.execute(('source',))
        self.assertEqual(self.factory_calls,0)
    def test_wrong_source_sha_and_current_binding_stop_before_factory(self):
        self.admission();self.grant(('source',),quotes=())
        original=self.o;self.o=replace(original,source_sha='f'*64)
        with self.assertRaises(c.Stop):self.execute(('source',))
        self.o=original;self.control=replace(self.control,binding_sha='f'*64)
        with self.assertRaises(c.Stop):self.execute(('source',))
        self.assertEqual(self.factory_calls,0)
    def test_native_factory_source_zero_inventory_extract_only_and_legacy_requirements(self):
        self.admission();self.native();self.grant(('source',),quotes=());self.factory_validate()
        r=self.sdk_request();q=self.quote(r)
        self.native((c.request_identity(r),),(q,));self.grant(('extract',));self.factory_validate()
        self.control=replace(self.control,stage_grant=None)
        with self.assertRaises(c.Stop):ns.CurrentNativeServicesFactory().validate(self.control)
        w=self.sdk_request('write',b'writer');qw=self.quote(w)
        self.native((c.request_identity(r),c.request_identity(w)),(q,qw))
        ns.CurrentNativeServicesFactory().validate(self.control)
    def test_native_selected_missing_quote_foreign_wire_and_new_roles_stop(self):
        self.admission();r=self.sdk_request();q=self.quote(r)
        self.native((c.request_identity(r),),());self.grant(('extract',))
        with self.assertRaises(c.Stop):self.factory_validate()
        self.native((c.request_identity(r),),(replace(q,request_sha='f'*64),));self.grant(('extract',))
        with self.assertRaises(c.Stop):self.factory_validate()
        for role in ('domain-name','reextract','arbitrary'):
            bad=self.sdk_request(role);qb=self.quote(bad)
            self.native((c.request_identity(r),c.request_identity(bad)),(q,qb));self.grant(('extract',))
            with self.subTest(role=role),self.assertRaises(c.Stop):self.factory_validate()
    def test_selected_factory_keeps147_current_input_final_wire_lookup(self):
        import active_worker as worker
        self.admission();cfg=self.native()
        packet={'source':'fixture source','unit':{'content':'fixture source','target_expression':'fixture','source_ranges':[[1,1]]},
                'domain':{'name':'fixture domain','description':'fixture domain description'}}
        other=copy.deepcopy(packet);other['unit']['target_expression']='foreign fixture'
        built=[worker.build_request('subject-name',p,cfg.input_budget) for p in (packet,other)]
        # Synthetic opaque wire bytes, NOT a production serializer clone.
        requests=[c.Request('sdk','openai','gpt-6-luna','subject-name',b'wire-'+str(i).encode(),0,b['inputBinding'],b['sourceBinding']) for i,b in enumerate(built)]
        identities=tuple(c.request_identity(r) for r in requests);quotes=tuple(self.quote(r) for r in requests)
        self.control=replace(self.control,native=replace(cfg,request_inventory=identities,
            naming_bindings=tuple(ns.naming_request_binding(i) for i in identities)),quotes=quotes)
        self.grant(('place-subject',));self.factory_validate()
        bridge=Mock()
        def foreign(payload,expected,quote,wire,*,quote_for,validate):
            # Same body as foreign B, but actual observed request carries A's
            # current input metadata. Global B quote must NOT satisfy A.
            return quote_for(replace(requests[1],input_binding=requests[0].input_binding,source_binding=requests[0].source_binding))
        bridge.exchange.side_effect=foreign
        http=ns.NativeHTTP(self.wire,quotes,bridge,self.control.native)
        with self.assertRaises(ns.NativeStop):http.sdk(worker,'subject-name',packet)
        bridge.exchange.assert_called_once();self.assertEqual(self.wire.counts['physical_post'],0)
        changed=copy.deepcopy(packet);changed['source']='wrong source'
        bridge.reset_mock()
        with self.assertRaises(ns.NativeStop):http.sdk(worker,'subject-name',changed)
        bridge.exchange.assert_not_called()
        self.assertNotIn('inputBinding',c.request_identity(self.sdk_request()))
    def test_factory_grant_flag_alone_not_authority_and_cache_manifest_checks(self):
        self.admission();self.native();self.grant(('source',),quotes=())
        with self.assertRaises(c.Stop):ns.CurrentNativeServicesFactory().validate(self.control)
        (Path(self.control.native.cache_directory)/'declared.json').write_text('drift')
        with self.assertRaises(c.Stop):self.factory_validate()
    def test_history_scope_split_does_not_reset_sdk2_or_jev9_q15(self):
        self.admission();self.history(sdk=2,jev=9,logical=15);self.grant(('source',),quotes=())
        first=self.execute(('source',));self.assertEqual(first['physical_counts']['sdk_subscription'],2)
        self.grant(('extract',),quotes=(self.quote(self.request()),));p=self.prior('extract',values={'text':'fixture source'})
        self.execute(('extract',),p)
        for req in (self.sdk_request(body=b'new-sdk'),c.Request('jev','jev','fixture-jev','selection',b'new-q',1),c.Request('embedding','x','x','x',b'cold')):
            with self.subTest(kind=req.kind),self.assertRaises(c.Stop):self.wire.attempt(req,self.quote(req),Mock(side_effect=AssertionError('no new effect')))
            self.wire.stopped=False
        self.assertEqual(self.wire.counts['sdk_subscription'],2);self.assertEqual(self.wire.counts['logical_q'],15)
        self.assertEqual(len(self.ledger.rows),22)
    def test_ledger_pending_reset_foreign_binding_and_deadline_not_renewed(self):
        self.admission();self.history(sdk=1);self.grant(('source',),quotes=())
        original=self.ledger.path.read_bytes();self.ledger.path.write_bytes(b'')
        with self.assertRaises(c.Stop):self.execute(('source',))
        self.ledger.path.write_bytes(original)
        self.history(sdk=1,pending=True);self.grant(('source',),quotes=())
        with self.assertRaises(c.Stop):self.execute(('source',))
        self.history(sdk=1);rows=copy.deepcopy(self.ledger.rows);rows[0]['binding']='foreign'
        self.ledger.path.write_text(''.join(json.dumps(r)+'\n' for r in rows));self.grant(('source',),quotes=())
        with self.assertRaises(c.Stop):self.execute(('source',))
        self.history();self.start=time.time()-50;self.end=self.start+51;self.grant(('source',),quotes=())
        self.execute(('source',));self.assertLess(self.wire.deadline.end-time.monotonic(),1.1)
    def test_partial_result_and_foreign_prior_never_promote_or_rerun(self):
        self.admission();self.grant(('source',),quotes=());result=self.execute(('source',))
        self.grant(('extract',));p=self.prior('extract',values={'text':'fixture source'})
        with self.assertRaises(c.Stop):self.execute(('extract',),result)
        bad=replace(p,context={**p.context,'execution_receipt':'foreign'});self.bind_prior(bad)
        with self.assertRaises(c.Stop):self.execute(('extract',),bad)
        self.api['extract'].assert_not_called();self.assertEqual(self.api['source'].call_count,1)
    def test_full_legacy_order_and_all_selected_handlers_no_hidden_rerun(self):
        self.authorize(self.control)
        with patch.object(rb.RealBindings,'stage',autospec=True,side_effect=rb.RealBindings.stage) as stage:
            result=self.execute()
        self.assertEqual([call.args[1] for call in stage.call_args_list],list(rb.STAGES))
        self.assertEqual(result['status'],'PUBLIC_CORE_RETURNED')
        TRACES.append({'selected':list(rb.STAGES),'actual':[call.args[1] for call in stage.call_args_list]})

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:],module=sys.modules[__name__]) if len(sys.argv)>1 else unittest.defaultTestLoader.loadTestsFromTestCase(FrontierTests)
    # Only directly affected legacy preflight/prior/boundary protections. No old
    # 147/144 standalone suite, no SDK/runtime/DB/network/service execution.
    for name in (() if len(sys.argv)>1 else ('test_current_source_controller_and_binding_fingerprints_stop','test_unknown_quote_or_unreviewed_transport_stops_before_factory',
                 'test_wire_reserve_before_count_and_uncertain_hold_no_retry')):
        suite.addTest(previous.BindingTests(name))
    started=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(suite)
    (OUT/('focused-result.json' if len(sys.argv)==1 else 'repair-'+str(time.time_ns())+'-result.json')).write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skipped':len(result.skipped),'seconds':time.monotonic()-started,'failedCases':[t.id() for t,_ in result.failures+result.errors],'traces':TRACES,'externalEffects':0},indent=2)+'\n')
    sys.exit(not result.wasSuccessful())
