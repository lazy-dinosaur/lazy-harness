"""Task163 offline suite including the 17 changed-surface compatibility cases.
Synthetic ports/FD/profile/receipts only. No product inference, auth or database.
"""
import contextlib,copy,io,json,sys,time,unittest
from dataclasses import asdict,replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
OUT=Path(__file__).resolve().parent;PACKET=OUT.parent/'unit1-quota-embedding-source-01'
sys.path[:0]=[str(OUT),str(OUT.parent/'unit1-per-request-quote-source-01')]
import test_per_request as p
import controller as c,real_bindings as rb,native_services as ns,native_bridge as nb
import trial

class ResourceTests(p.PerRequestTests):
    # All 17 compatibility cases inherited. Historical byte-freeze assertion is
    # adapted for the now-approved bridge changes; default broker behavior tested.
    def test_bridge_pair_bytes_unchanged(self):
        self.assertIn("redirect:'error'",(p.BASE/'native_bridge.mjs').read_text())
        self.assertIn('result=wire.attempt(expected,quote,send)',(p.BASE/'native_bridge.py').read_text())
        text=(trial.ROOT/'experiments/v2-knowledge-module-runner-01/scale-04/writer_host.mjs').read_text()
        self.assertIn('maxRetries: 0',text)
        self.assertIn("fail('E_WRITER_COST_UNKNOWN')",text)
    def rebind(self):
        super().rebind()
        for field,purpose in [('sdk_quota','sdk-subscription-cash0-policy'),('embedding_policy','native-embedding-policy')]:
            policy=getattr(self.control,field,None)
            if policy:self.bind(purpose,{'admission':asdict(self.a),'control':asdict(self.control)},policy.receipt)
    def issue(self,request,context):
        if request.kind=='sdk' and self.control.sdk_quota is not None:
            self.events.append('issue');self.issued.append((request,copy.deepcopy(context)))
            if self.error:raise self.error
            policy=self.control.sdk_quota
            q=c.SubscriptionQuota(c.digest(c.request_identity(request)),self.a.inventory_sha,self.a.db_plan_sha,policy.profile_sha,policy.limits_sha,policy.call_seconds,time.time()+30,'fixture-quota')
            q=replace(q,**self.mutate)
            self.bind('per-request-sdk-quota',{'context':context,'authorization':asdict(q)},q.receipt)
            self.bind('sdk-subscription-quota',{'authorization':asdict(q),'request':c.request_identity(request),'control_sha':c.digest(asdict(self.control))},q.receipt)
            return q
        return super().issue(request,context)
    def quota_setup(self):
        worker,packet,built,row=self.sdk_setup()
        self.ledger.subscription_limits={'Luna':{'calls':2,'seconds':1200,'per_call_seconds':600}}
        runtime=self.home/'fixture-runtime.mjs';runtime.write_text('export const fixture=true;')
        model={'provider':'openai','id':'gpt-6-luna','api':'openai-responses','baseUrl':'https://api.openai.com/v1','reasoning':True,'contextWindow':272000,'maxTokens':128000,'cost':{'input':.1,'output':.5,'cacheRead':.01,'cacheWrite':.125}}
        cfg=replace(self.control.native,sdk_profile=model,sdk_runtime_sha=c.sha(runtime.read_bytes()),subscription_limits=tuple(self.ledger.subscription_limits.items()))
        policy=c.SDKQuotaPolicy(c.digest({'runtime_sha':cfg.sdk_runtime_sha,'model':model}),c.digest(self.ledger.subscription_limits),600,'fixture-cash0-profile-policy')
        self.control=replace(self.control,native=cfg,sdk_quota=policy);self.rebind();self.wire.configure_resources(self.control)
        return worker,packet,built,row
    def embedding_setup(self):
        model='perplexity/pplx-embed-v1-0.6b'
        self.optin();self.ledger.caps['embedding']=.002048
        rows=tuple({'kind':'embedding','provider':'openrouter','model':model,'role':role,'sourceBinding':self.a.provenance.source_sha,'inputScope':'unit-derived','dimensions':1024,'format':'raw'} for role in ('query','passage'))
        policy=c.EmbeddingPolicy(model,self.a.provenance.source_sha,8,16,'.002048','fixture-embedding-policy')
        cfg=replace(self.control.native,embed_model=model,permission_inventory=rows)
        self.control=replace(self.control,native=cfg,embedding_policy=policy);self.rebind();self.wire.configure_resources(self.control)
        return rows
    def io_bridge(self,result,*,wrong_profile=False):
        test=self;events=self.events
        class Stream:
            def __init__(self):self.i=0
            def readline(self,*a):
                self.i+=1
                if self.i==1:
                    events.append('preview');packet=test.sent_packet
                    raw=packet.get('bodyRaw') or '{"model":"gpt-6-luna","input":"synthetic final wire"}'
                    value={'type':'wire','url':packet['url'],'body':raw}
                    if packet.get('sdkProfile'):value['profileSHA']='f'*64 if wrong_profile else packet['profileSHA']
                    return (json.dumps(value)+'\n').encode()
                return (json.dumps({'type':'done','result':result})+'\n').encode()
            def close(self):pass
        class Sock:
            def close(self):pass
            def fileno(self):return 123
            def settimeout(self,*a):pass
            def makefile(self,*a,**kw):return Stream()
            def shutdown(self,*a):pass
            def sendall(self,raw):
                row=json.loads(raw)
                if row.get('type')=='permit':
                    test.assertEqual(test.ledger.rows[-1]['state'],'reserved');test.permit=row;events.append('permit')
                else:test.sent_packet=row
        process=SimpleNamespace(pid=321,returncode=0,poll=lambda:0,wait=lambda **kw:0)
        bridge=nb.NodeBridge(self.control.native,c.Deadline(20),SimpleNamespace(spawning=False),str(self.home))
        stack=contextlib.ExitStack();stack.enter_context(patch.object(nb.socket,'socketpair',return_value=(Sock(),Sock())));stack.enter_context(patch.object(nb.subprocess,'Popen',return_value=process));stack.enter_context(patch.object(bridge,'argv',return_value=['fixture-only']))
        return bridge,stack
    def test_legacy_sdk_equivalent_bound_does_not_label_cash_charge(self):
        worker,packet,built,row=self.sdk_setup();self.validate(('place-subject',))
        output=json.dumps({'name':'fixture','description':'fixture description','source_concept':'fixture','original_expression':'fixture'})
        usage=0.000001
        bridge,stack=self.io_bridge({'ok':True,'cost':usage,'text':output})
        with stack:self.http(bridge).sdk(worker,'subject-name',packet)
        self.assertEqual(self.events,['preview','issue','permit'])
        self.assertEqual(self.ledger.rows[-1]['account'],'subscription')
        self.assertEqual(self.ledger.rows[-1]['charge'],usage)
        self.assertEqual(self.ledger.spent('generation','cash'),0)
        result=json.loads((self.home/self.ledger.rows[-1]['result']).read_text())
        self.assertEqual(result['accounting_basis'],'subscription-equivalent-bound')
        self.assertEqual(result['equivalent_cost'],str(c.Decimal(str(usage))))
        self.assertEqual(result['cash_charge'],'0')
        self.assertEqual(result['usage_cost'],usage)

    def test_quota_actual_fd_reservation_permit_metric_not_cash(self):
        worker,packet,built,row=self.quota_setup();self.validate(('place-subject',))
        output=json.dumps({'name':'fixture','description':'fixture description','source_concept':'fixture','original_expression':'fixture'})
        bridge,stack=self.io_bridge({'ok':True,'cost':12345.0,'text':output})
        with stack:self.http(bridge).sdk(worker,'subject-name',packet)
        self.assertEqual(self.events,['preview','issue','permit']);self.assertEqual(self.ledger.rows[0]['charge'],0)
        self.assertEqual(self.ledger.rows[-1]['account'],'subscription');self.assertEqual(self.ledger.rows[-1]['charge'],12345.0)
        self.assertEqual(self.ledger.spent('generation','cash'),0);self.assertLessEqual(self.permit['timeoutMs'],20000)
        result=json.loads((self.home/self.ledger.rows[-1]['result']).read_text())
        self.assertEqual(result['accounting_basis'],'subscription-quota');self.assertEqual(result['equivalent_cost'],'12345.0');self.assertEqual(result['usage_cost'],12345.0)
    def test_quota_profile_receipt_and_actual_profile_observation_deny(self):
        worker,packet,built,row=self.quota_setup();good=self.control
        for field in ('profile_sha','limits_sha'):
            self.control=replace(good,sdk_quota=replace(good.sdk_quota,**{field:'f'*64}))
            with self.subTest(field=field),self.assertRaises(c.Stop):self.wire.configure_resources(self.control)
        self.control=replace(good,sdk_quota=replace(good.sdk_quota,receipt='untrusted'))
        with self.assertRaises(c.Stop):self.wire.configure_resources(self.control)
        self.control=good;self.wire.configure_resources(good)
        bridge,stack=self.io_bridge({'ok':True,'cost':1,'text':'{}'},wrong_profile=True)
        with stack,self.assertRaises(ns.NativeStop):self.http(bridge).sdk(worker,'subject-name',packet)
        self.assertNotIn('permit',self.events);self.assertFalse(self.ledger.rows)
    def test_quota_wrong_expiry_limits_and_cash_quote_zero_still_invalid(self):
        worker,packet,built,row=self.quota_setup()
        req=c.Request('sdk','openai','gpt-6-luna','subject-name',b'actual',0,built['inputBinding'],built['sourceBinding'])
        for kw in ({'expires':time.time()-1},{'limits_sha':'f'*64},{'profile_sha':'f'*64},{'call_seconds':1}):
            self.mutate=kw
            with self.subTest(kw=kw),self.assertRaises(ns.NativeStop):self.http().final_quote(req,(row,),input_binding=built['inputBinding'],source_binding=built['sourceBinding'])
            self.wire.stopped=False
        with self.assertRaises(c.Stop):self.wire.attempt(req,self.quote(req,max_cost='0'),Mock())
        self.assertFalse(self.ledger.rows)
    def test_quota_unknown_metric_hold_no_replay(self):
        worker,packet,built,row=self.quota_setup();req=c.Request('sdk','openai','gpt-6-luna','subject-name',b'actual',0,built['inputBinding'],built['sourceBinding'])
        q=self.http().final_quote(req,(row,),input_binding=built['inputBinding'],source_binding=built['sourceBinding'])
        with self.assertRaises(BaseException):self.wire.attempt(req,q,lambda r:{'accepted':True,'usage_cost':None})
        self.assertEqual(self.ledger.rows[-1]['state'],'reserved');self.assertEqual(self.ledger.rows[-1]['charge'],0);self.assertTrue(self.wire.stopped)
    def test_embedding_actual_fd_miss_settle_cache_hit_zero(self):
        self.embedding_setup();self.max_cost='.000128';body={'model':self.control.native.embed_model,'data':[{'index':0,'embedding':[0.0]*1024}],'usage':{'cost':.000001}}
        bridge,stack=self.io_bridge({'body':body})
        with stack:
            http=self.http(bridge);self.assertEqual(len(http.encode(['synthetic fresh','synthetic fresh'])),2)
            calls=len(self.issued);http.encode(['synthetic fresh']);self.assertEqual(len(self.issued),calls)
        self.assertEqual(self.wire.counts['embedding_post'],1);self.assertEqual(self.wire.counts['embedding_inputs'],1)
        self.assertEqual(self.ledger.rows[-1]['account'],'cash');self.assertEqual(self.ledger.rows[-1]['step'],'embedding')
    def test_embedding_malformed_unknown_or_overquote_no_cache(self):
        self.embedding_setup();self.max_cost='.000128';root=Path(self.control.native.cache_directory)
        baseline=set(root.iterdir())
        for body in ({'model':self.control.native.embed_model,'data':[{'index':0,'embedding':[0.0]*4}],'usage':{'cost':.000001}}, {'model':self.control.native.embed_model,'data':[{'index':0,'embedding':[0.0]*1024}],'usage':{}}, {'model':self.control.native.embed_model,'data':[{'index':0,'embedding':[0.0]*1024}],'usage':{'cost':.01}}):
            # Each variant is an independent synthetic trial, never a retry after an unknown.
            bridge,stack=self.io_bridge({'body':body})
            with stack,self.assertRaises(ns.NativeStop):self.http(bridge).encode(['synthetic fresh'])
            self.assertEqual(set(root.iterdir()),baseline);self.assertEqual(self.ledger.rows[-1]['state'],'reserved')
            break  # No replay in this fixture; the other invalid forms are pure validators below.
        http=self.http()
        for usage in ({},{'cost':'NaN'},{'cost':-1}):
            with self.subTest(usage=usage),self.assertRaises(BaseException):http.validate_embedding({'body':{'model':self.control.native.embed_model,'data':[{'index':0,'embedding':[0.0]*1024}],'usage':usage}},{'model':self.control.native.embed_model,'input':['x']})
    def test_embedding_batch_inputs_cash_subcap_shared_total_and_no_grant(self):
        rows=self.embedding_setup();self.max_cost='.002049'
        req=c.Request('embedding','openrouter',self.control.native.embed_model,'query',json.dumps({'model':self.control.native.embed_model,'input':['a','b']}).encode(),0,c.digest(['a','b']),self.a.provenance.source_sha)
        q=self.http().final_quote(req,rows);send=Mock()
        with self.assertRaises(c.Stop):self.wire.attempt(req,q,send)
        send.assert_not_called();self.assertFalse(self.ledger.rows)
        self.wire.stopped=False;self.max_cost='.000128';q=self.http().final_quote(req,rows)
        self.wire.counts['embedding_inputs']=15
        with self.assertRaises(c.Stop):self.wire.attempt(req,q,send)
        self.wire.stopped=False;self.wire.counts['embedding_inputs']=0
        self.ledger.call('judging','fixture prior cash',.03895,lambda:{'cost':.03895},lambda r:r['cost'])
        with self.assertRaises(BaseException):self.wire.attempt(req,q,send)
        send.assert_not_called()
    def test_embedding_history_and_unknown_denial(self):
        rows=self.embedding_setup();self.max_cost='.000128';req=c.Request('embedding','openrouter',self.control.native.embed_model,'query',json.dumps({'model':self.control.native.embed_model,'input':['a','b']}).encode(),0,c.digest(['a','b']),self.a.provenance.source_sha)
        q=self.http().final_quote(req,rows);self.wire.attempt(req,q,lambda r:{'accepted':True,'usage_cost':'.000001'})
        self.grant(('source',),quotes=());self.rebind();ctx=rb.validate_stage_grant(self.a,self.trust,self.control,self.owned,('source',))
        self.assertEqual(ctx['counts']['embedding_post'],1);self.assertEqual(ctx['counts']['embedding_inputs'],2);self.assertEqual(ctx['embedding_cash'],'0.000001')
        self.ledger.path.write_text(self.ledger.path.read_text()+json.dumps({**self.ledger.rows[-1],'id':'unknown-fixture','state':'reserved'})+'\n')
        self.grant(('source',),quotes=());self.rebind()
        with self.assertRaises(c.Stop):rb.validate_stage_grant(self.a,self.trust,self.control,self.owned,('source',))
    def test_embedding_unknown_cost_after_send_holds_and_writes_no_cache(self):
        self.embedding_setup();self.max_cost='.000128';root=Path(self.control.native.cache_directory);before=set(root.iterdir())
        body={'model':self.control.native.embed_model,'data':[{'index':0,'embedding':[0.0]*1024}],'usage':{}}
        bridge,stack=self.io_bridge({'body':body})
        with stack,self.assertRaises(ns.NativeStop):self.http(bridge).encode(['synthetic unknown cost'])
        self.assertEqual(set(root.iterdir()),before);self.assertEqual(self.ledger.rows[-1]['state'],'reserved');self.assertTrue(self.wire.stopped)
    def test_embedding_overquote_after_send_holds_and_writes_no_cache(self):
        self.embedding_setup();self.max_cost='.000128';root=Path(self.control.native.cache_directory);before=set(root.iterdir())
        body={'model':self.control.native.embed_model,'data':[{'index':0,'embedding':[0.0]*1024}],'usage':{'cost':.01}}
        bridge,stack=self.io_bridge({'body':body})
        with stack,self.assertRaises(ns.NativeStop):self.http(bridge).encode(['synthetic overquote'])
        self.assertEqual(set(root.iterdir()),before);self.assertEqual(self.ledger.rows[-1]['state'],'reserved');self.assertTrue(self.wire.stopped)
    def test_encoder_default_miss_stop_no_issuer_or_send(self):
        self.optin();bridge=Mock()
        with self.assertRaises(ns.NativeStop):self.http(bridge).encode(['synthetic ungranted miss'])
        bridge.exchange.assert_not_called();self.assertFalse(self.issued);self.assertFalse(self.ledger.rows)
    def test_sdk_quota_two_calls_plus_third_denied_in_same_history(self):
        worker,packet,built,row=self.quota_setup()
        send=Mock(return_value={'accepted':True,'usage_cost':1000.0})
        for i in range(3):
            req=c.Request('sdk','openai','gpt-6-luna','subject-name',('synthetic wire '+str(i)).encode(),0,built['inputBinding'],built['sourceBinding'])
            q=self.http().final_quote(req,(row,),input_binding=built['inputBinding'],source_binding=built['sourceBinding'])
            if i<2:self.wire.attempt(req,q,send)
            else:
                with self.assertRaises(c.Stop):self.wire.attempt(req,q,send)
        self.assertEqual(send.call_count,2);self.assertEqual(self.wire.counts['sdk_subscription'],2);self.assertEqual(self.ledger.spent('generation','cash'),0)
    def test_node_syntax_and_actual_broker_embedding_offline(self):
        raw=p.f.previous.old.RAW_POPEN
        for args in (['node','--check',str(p.BASE/'native_bridge.mjs')],['node',str(PACKET/'test_broker.mjs')]):
            child=raw(args,stdout=-1,stderr=-1);out,err=child.communicate(timeout=15)
            self.assertEqual(child.returncode,0,err.decode());self.assertNotIn(b'SYNTHETIC_FIXTURE_ONLY',out)

class CallerTests(unittest.TestCase):
    def test_default_dry_and_invalid_execute_have_no_product_effects(self):
        self.assertEqual(trial.run()['effects'],0)
        with self.assertRaises(c.Stop):trial.run(execute=True)
    def test_fake_lease_cleanup_on_rejected_resolver(self):
        # Registry verifies exact tuples, not an always-True verifier.
        events=[]
        class Lease:
            @contextlib.contextmanager
            def __call__(self,plan,grant,clock):
                events.append('enter')
                try:yield SimpleNamespace(dsn='fixture',host='fixture',fixture_only=True)
                finally:events.append('cleanup')
        def resolver(*args):return {'not':'a typed bundle'}
        lease=Lease();code=tuple((str(path.relative_to(trial.ROOT)),trial.file_sha(path)) for path in [*[p.BASE/n for n in ('controller.py','real_bindings.py','native_services.py','native_bridge.py','native_bridge.mjs')],Path(trial.__file__)])
        grant=trial.TrialGrant(trial.PLAN_SHA,trial.SOURCE_SHA,code,trial.capability_sha(lease.__call__),trial.capability_sha(resolver),30,'fixture-image',0,time.time()+60,'fixture-trial')
        public={k:'a'*64 for k in ('sdk_profile_sha','pricing_policy_sha','history_sha','initial_cache_sha')}
        grant=replace(grant,preflight_sha=c.digest(public),preflight_receipt='fixture-preflight')
        registry={('temporary-one-unit-trial',c.digest(asdict(grant)),grant.receipt)}
        registry.add(('one-unit-preparation-proof',c.digest({'grant':asdict(grant),'public':public}),grant.preflight_receipt))
        trust=c.Trust(lambda purpose,digest,receipt:(purpose,digest,receipt) in registry)
        with self.assertRaises(c.Stop):trial.run(public,execute=True,grant=grant,trust=trust,provisioner=lease,resolver=resolver)
        self.assertEqual(events,['enter','cleanup'])
    def test_fake_execute_actual_public_entries_temporary_record_and_cleanup(self):
        h=ResourceTests(methodName='runTest');h.setUp();self.addCleanup(h.doCleanups)
        h.quota_setup()
        source=trial.SOURCE.read_text();line=source.splitlines()[10]
        prov=replace(h.a.provenance,source_sha=trial.SOURCE_SHA,ranges=((11,11),),fact_sha=c.digest(h.fact))
        h.a=replace(h.a,db_plan_sha=trial.PLAN_SHA,provenance=prov)
        h.o=replace(h.o,db_plan_sha=trial.PLAN_SHA,source_sha=trial.SOURCE_SHA,fact_sha=c.digest(h.fact))
        h.ledger.binding=trial.PLAN_SHA;h.ledger.caps['embedding']=.002048
        h.owned=replace(h.owned,plan_sha=trial.PLAN_SHA,record={'record_id':'R05'},subjects=({'subject_id':'fixture-id','domain':h.fact['domain']},))
        cfg=h.control.native
        rights=({'kind':'sdk','provider':'openai','model':'gpt-6-luna','role':role,'inputBinding':'a'*64,'sourceBinding':'b'*64} for role in ('subject-name','write'))
        rights=tuple(rights);naming=tuple(ns.naming_binding(row) for row in rights if row['role']=='subject-name')
        cfg=replace(cfg,embed_model='perplexity/pplx-embed-v1-0.6b',permission_inventory=rights,naming_bindings=naming)
        embedding=c.EmbeddingPolicy(cfg.embed_model,trial.SOURCE_SHA,8,16,'.002048','fixture-embedding-policy')
        h.control=replace(h.control,native=cfg,embedding_policy=embedding,owned_sha=c.digest(h.owned.manifest()),admission_sha=c.digest(asdict(h.a)),whole_seconds=20)
        for purpose,receipt in [('source-review','review'),('source-audit','audit'),('artifact-lineage','lineage')]:h.bind(purpose,asdict(prov),receipt)
        for purpose,receipt in [('models','models'),('accounting','account'),('admission','authority'),('accounting-per-request','account')]:h.bind(purpose,asdict(h.a),receipt)
        h.bind('fact-materialization',h.fact,'lineage');h.rebind()
        events=[]
        class Lease:
            @contextlib.contextmanager
            def __call__(self,plan,grant,clock):
                events.append('enter')
                resource=SimpleNamespace(fixture_only=True,dsn=h.owned.dsn,host=h.owned.host,readback=lambda unit,entry:{'unit':unit,'state':'proposed','entry':entry})
                try:yield resource
                finally:events.append('cleanup')
        def resolver(selected,resource,previous,clock):
            h.start=clock['started'];h.end=clock['ends'];h.grant(selected,quotes=());h.rebind()
            values=previous['values'] if previous else {'text':source,'unit':{'content':line,'source_ranges':[[11,11]],'target_expression':'host/project context','source_text':line,'host_id':h.owned.host,'unit_id':h.owned.unit_id},'placement':{}}
            prior=h.prior(selected[0],values=values)
            return trial.StageBundle(h.a,h.o,h.control,h.owned,h.factory,prior)
        lease=Lease();code=tuple((str(path.relative_to(trial.ROOT)),trial.file_sha(path)) for path in [*[p.BASE/n for n in ('controller.py','real_bindings.py','native_services.py','native_bridge.py','native_bridge.mjs')],Path(trial.__file__)])
        grant=trial.TrialGrant(trial.PLAN_SHA,trial.SOURCE_SHA,code,trial.capability_sha(lease.__call__),trial.capability_sha(resolver),30,'fixture-image',0,time.time()+60,'fixture-trial')
        public={'sdk_profile_sha':h.control.sdk_quota.profile_sha,'pricing_policy_sha':h.a.accounting_policy,
                'history_sha':c.sha(h.ledger.path.read_bytes()),'initial_cache_sha':c.digest(h.control.native.cache_manifest)}
        grant=replace(grant,preflight_sha=c.digest(public),preflight_receipt='fixture-preflight')
        h.bind('one-unit-preparation-proof',{'grant':asdict(grant),'public':public},grant.preflight_receipt)
        h.bind('temporary-one-unit-trial',asdict(grant),grant.receipt)
        with patch.object(rb,'run_owned_job',side_effect=lambda job,*args:job()),patch.object(ns.CurrentNativeServicesFactory,'build',side_effect=h.build):
            result=trial.run(public,execute=True,grant=grant,trust=h.trust,provisioner=lease,resolver=resolver)
        self.assertEqual(result['status'],'TEMPORARY_RECORD_READBACK');self.assertFalse(result['full135_complete']);self.assertEqual(events,['enter','cleanup'])
        self.assertEqual(h.api['record'].call_count,1);h.api['worktime'].assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
