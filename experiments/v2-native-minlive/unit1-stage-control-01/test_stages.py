"""Approved Task144 offline stage/control protections; no product services."""
import copy,json,sys,time,unittest
from dataclasses import asdict,replace
from pathlib import Path
from unittest.mock import Mock,patch
OUT=Path(__file__).resolve().parent
BASE=OUT.parent/'unit1-controller-source-phase1'
sys.path[:0]=[str(BASE),str(BASE/'binding-completion-01')]
import test_real_bindings as previous
import controller as c
import real_bindings as rb

TRACES=[]
class StageTests(unittest.TestCase):
    setUp=previous.BindingTests.setUp
    bind=previous.BindingTests.bind
    request=previous.BindingTests.request
    quote=previous.BindingTests.quote
    authorize=previous.BindingTests.authorize
    build=previous.BindingTests.build
    def values(self):
        return {'text':'fixture source','unit':{'content':'fixture source','source_ranges':[[1,1]],'target_expression':'fixture',
                'host_id':self.owned.host,'unit_id':self.owned.unit_id,'source_text':'fixture source'},
                'placement':{'domain':{'chosen':{'name':self.fact['domain']}},'subject':{'chosen':{'name':self.fact['subject']}}},
                'answer':{'fact':'draft','kind':'fact'},'fact':copy.deepcopy(self.fact),'checked':{'errors':[]},
                'entry':'fixture-entry','worktime_receipt':'fixture-check'}
    def db(self,stage):
        status,state={'worktime':('active','proposed'),'complete':('active','provisional'),
                      'route':('completed','eligible'),'digest':('completed','eligible')}[stage]
        return {'unit':[self.owned.host,status],'entry':[self.owned.host,self.owned.unit_id,state,{'facts':[copy.deepcopy(self.fact)]}],
                'receipts':[['fixture-check',0,'record']],'parts':[[self.owned.host,self.fact['domain'],0]],
                'generation':[3],'entries':[['fixture-entry']]}
    def prior(self,start,values=None,db=None):
        if start=='source': return None
        db=self.db(start) if start in rb.STAGES[11:] and db is None else db
        p=rb.StagePrior(rb.prior_context(self.a,self.control,self.owned),values or self.values(),db,'prior')
        self.bind_prior(p)
        return p
    def bind_prior(self,p):
        self.bind('stage-prerequisite',{'context':p.context,'values':p.values,'db':p.db},p.receipt)
    def execute(self,stages=None,prior=None,admission=True):
        with patch.object(rb,'run_owned_job',side_effect=lambda job,directory,deadline:job()):
            return c.execute_live(self.a if admission else None,self.o,self.trust,control=self.control,
                                  owned=self.owned,factory=self.factory,stages=stages,prior=prior)
    def clear_calls(self):
        self.events.clear()
        for api in self.api.values():api.reset_mock()
        self.ports.writer.reset_mock()
        self.make_dsn.reset_mock()
        self.factory_calls=0
    def test_every_single_and_contiguous_forward_range_uses_only_selected_stage_code(self):
        for start in range(len(rb.STAGES)):
            for end in range(start+1,len(rb.STAGES)+1):
                stages=rb.STAGES[start:end]
                with self.subTest(stages=stages):
                    self.clear_calls()
                    p=self.prior(stages[0])
                    with patch.object(rb,'read_stage_state',return_value=p.db if p else None) as read,patch.object(self.bindings,'stage',wraps=self.bindings.stage) as stage:
                        result=self.execute(stages,p)
                    calls=[call.args[0] for call in stage.call_args_list]
                    self.assertEqual(calls,list(stages))
                    expected={'source':stages.count('source'),'extract':stages.count('extract'),
                              'place':sum(stages.count(s) for s in ('place-domain','place-subject')),
                              'kind':stages.count('kind'),'validate':stages.count('validate'),'ground':stages.count('ground'),
                              'citations':stages.count('citations'),'record_unit':stages.count('record'),'record':stages.count('record'),
                              'worktime':stages.count('worktime'),'complete':stages.count('complete'),'route':stages.count('route'),'digest':stages.count('digest')}
                    self.assertEqual({k:self.api[k].call_count for k in expected},expected)
                    self.assertEqual(self.ports.writer.call_count,stages.count('write'))
                    self.assertEqual(read.call_count,int(start>=11))
                    self.assertEqual(result['status'],'PUBLIC_CORE_RETURNED' if stages==rb.STAGES else 'SELECTED_STAGES_RETURNED')
                    TRACES.append({'selected':list(stages),'actual':calls,'apiCounts':expected,'dbReads':read.call_count})
    def test_default_full_order_and_result_compatibility(self):
        result=self.execute()
        self.assertEqual(self.events,['record_unit','record','worktime','complete','route','digest'])
        self.assertEqual(result['status'],'PUBLIC_CORE_RETURNED')
        self.assertNotIn('values',result)
        self.assertEqual([r['core']['stage'] for r in result['receipts']],[c.CORE[i] for i in (1,3,4,5,6)])
        self.assertTrue(result['embedding_pending'])
        self.assertFalse(self.in_metadata)
    def test_bad_selector_and_missing_admission_never_build_factory_or_read_db(self):
        with patch.object(rb,'read_stage_state') as read:
            for bad in ('digest',[],(),('bogus',),('digest','route'),('write','write'),('source','write'),(1,),{'stage':'digest'}):
                with self.subTest(bad=bad),self.assertRaises(c.Stop):self.execute(bad)
            with self.assertRaises(c.Stop):self.execute(('source',),admission=False)
            with self.assertRaises(c.Stop):self.execute(('digest',),self.prior('digest'),admission=False)
        read.assert_not_called()
        self.assertEqual(self.factory_calls,0)
        self.assertEqual(self.events,[])
        self.ports.writer.assert_not_called()
    def test_missing_malformed_forged_and_foreign_prior_rejected_before_factory(self):
        good=self.prior('digest')
        bads=[None,{},replace(good,receipt='accepted=true'),replace(good,values={}),replace(good,db={'completed':True})]
        for field in ('host','unit_id','execution_receipt','owned_sha','admission_sha','control_sha','source'):
            bads.append(replace(good,context={**good.context,field:'foreign'}))
        for key,value in (('entry',False),('worktime_receipt',{}),('fact',{**self.fact,'domain':'foreign'}),('text','stale')):
            p=replace(good,values={**good.values,key:value});self.bind_prior(p);bads.append(p)
        with patch.object(rb,'read_stage_state') as read:
            for p in bads:
                with self.subTest(prior=p),self.assertRaises(c.Stop):self.execute(('digest',),p)
        read.assert_not_called()
        self.assertEqual(self.factory_calls,0)
    def test_finer_role_prior_shapes_and_holds_fail_before_factory(self):
        cases=[('extract','text',False),('place-domain','unit',{}),('place-subject','placement',{}),
               ('write','placement',{'domain':{'chosen':{'name':'D'}}}),('kind','answer',[]),('validate','answer',{}),
               ('ground','fact',{}),('citations','checked',{'errors':['held']})]
        for stage,key,value in cases:
            p=self.prior(stage);p=replace(p,values={**p.values,key:value});self.bind_prior(p)
            with self.subTest(stage=stage),self.assertRaises(c.Stop):self.execute((stage,),p)
        self.assertEqual(self.factory_calls,0)
    def test_stale_current_db_and_forged_state_stop_before_model_or_write(self):
        for stage in rb.STAGES[11:]:
            good=self.prior(stage)
            for key in good.db:
                actual={**good.db,key:[]}
                with self.subTest(stage=stage,key=key),patch.object(rb,'read_stage_state',return_value=actual),self.assertRaises(c.Stop):
                    self.execute((stage,),good)
            forged=replace(good,db={**good.db,'entry':['foreign',self.owned.unit_id,'eligible',{'facts':[self.fact]}]})
            self.bind_prior(forged)
            with patch.object(rb,'read_stage_state',return_value=forged.db),self.assertRaises(c.Stop):self.execute((stage,),forged)
        self.assertEqual(self.events,[])
        self.ports.writer.assert_not_called()
        self.services.judge.assert_not_called()
    def test_digest_explicit_domain_never_routes_or_reextracts(self):
        p=self.prior('digest')
        with patch.object(rb,'read_stage_state',return_value=p.db): result=self.execute(('digest',),p)
        self.assertEqual(self.events,['digest'])
        self.assertEqual(self.api['digest'].call_args.kwargs['domain'],self.fact['domain'])
        self.api['route'].assert_not_called();self.api['source'].assert_not_called();self.api['extract'].assert_not_called()
        self.api['record'].assert_not_called();self.ports.writer.assert_not_called()
        self.assertEqual(result['receipts'][0]['receipt_kind'],'observed-public-return')
    def test_actual_fact_source_unit_projection_supported(self):
        fact={**self.fact,'source_unit':{'content':'fixture source','target_expression':'fixture','source_ranges':[[1,1]]}}
        self.a=replace(self.a,provenance=replace(self.a.provenance,fact_sha=c.digest(fact)))
        self.o=replace(self.o,fact_sha=c.digest(fact))
        for purpose,receipt in [('source-review','review'),('source-audit','audit'),('artifact-lineage','lineage')]:self.bind(purpose,asdict(self.a.provenance),receipt)
        for purpose,receipt in [('models','models'),('accounting','account'),('admission','authority')]:self.bind(purpose,asdict(self.a),receipt)
        self.bind('fact-materialization',fact,'lineage')
        self.control=replace(self.control,admission_sha=c.digest(asdict(self.a)))
        self.authorize(self.control)
        p=self.prior('review',values={'fact':fact})
        self.assertEqual(self.execute(('review',),p)['status'],'SELECTED_STAGES_RETURNED')
    def test_current_db_adapter_is_read_only_and_uses_bounded_dsn(self):
        values=self.values();db=self.db('digest')
        cur=Mock();cur.__enter__=Mock(return_value=cur);cur.__exit__=Mock(return_value=False)
        cur.fetchone.side_effect=[tuple(db['unit']),tuple(db['entry']),tuple(db['generation'])]
        cur.fetchall.side_effect=[db['receipts'],db['parts'],db['entries']]
        conn=Mock();conn.__enter__=Mock(return_value=conn);conn.__exit__=Mock(return_value=False);conn.cursor.return_value=cur
        pg=Mock();pg.connect.return_value=conn
        with patch.object(rb.importlib,'import_module',return_value=pg):actual=rb.read_stage_state('fixture bounded dsn',self.owned,values)
        self.assertEqual(actual,db)
        queries=[call.args[0] for call in cur.execute.call_args_list]
        self.assertEqual(queries[0],'set transaction read only')
        self.assertTrue(all(q.startswith('select ') for q in queries[1:]))
        pg.connect.assert_called_once_with('fixture bounded dsn')

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(StageTests)
    for name in ('test_exact_public_arguments_results_order_and_metadata_restore','test_current_owner_and_plan_stop_before_factory',
                 'test_current_source_controller_and_binding_fingerprints_stop','test_unknown_quote_or_unreviewed_transport_stops_before_factory',
                 'test_genuine_extraction_ranges_and_q1q2_hold_before_db','test_materialized_fact_hash_or_review_missing_before_db',
                 'test_public_failure_status_stops_following_stages','test_completion_and_router_and_partial_digest_not_promoted',
                 'test_applied_connection_options_and_expired_whole_deadline','test_wire_reserve_before_count_and_uncertain_hold_no_retry'):
        suite.addTest(previous.BindingTests(name))
    for name in ('test_quote_unknown_and_payload_provider_model_drift_stop_before_post','test_budget_carry_or_missing_model_accounting_authority_denied',
                 'test_unknown_usage_error_or_fallback_holds_reserve_and_stops'):
        suite.addTest(previous.old.ControllerTests(name))
    sys.path.insert(0,str(BASE/'native-completion-02'))
    import test_native
    suite.addTest(test_native.NativeTests('test_embedding_all_warm_query_and_direct_http_effect_guard'))
    started=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(suite)
    (OUT/'call-traces.json').write_text(json.dumps(TRACES,indent=2)+'\n')
    (OUT/'focused-result.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skipped':len(result.skipped),'seconds':time.monotonic()-started,'rangeProbes':len(TRACES),'externalEffects':0},indent=2)+'\n')
    sys.exit(not result.wasSuccessful())
