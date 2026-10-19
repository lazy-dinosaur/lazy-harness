"""Task158: synthetic issuer + actual entry/factory/quote/escrow/IPC code; no inference."""
import copy,json,sys,time,unittest
from dataclasses import asdict,replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
OUT=Path(__file__).resolve().parent;BASE=OUT.parent/'unit1-controller-source-phase1'
sys.path[:0]=[str(OUT.parent/'unit1-admission-frontier-source-01'),str(BASE)]
import test_frontier as f
import controller as c
import real_bindings as rb
import native_services as ns
import native_bridge as nb

class PerRequestTests(unittest.TestCase):
    bind=f.FrontierTests.bind
    request=f.FrontierTests.request
    quote=f.FrontierTests.quote
    authorize=f.FrontierTests.authorize
    build=f.FrontierTests.build
    admission=f.FrontierTests.admission
    grant=f.FrontierTests.grant
    native=f.FrontierTests.native
    history=f.FrontierTests.history
    prior=f.FrontierTests.prior
    values=f.FrontierTests.values
    db=f.FrontierTests.db
    bind_prior=f.FrontierTests.bind_prior
    execute=f.FrontierTests.execute
    native_entry=f.FrontierTests.native_entry
    sdk_request=f.FrontierTests.sdk_request
    def setUp(self):
        f.FrontierTests.setUp(self)
        self.events=[];self.issued=[];self.error=None;self.mutate={};self.max_cost='.001';self.skip_quote_trust=False
        self.issuer=rb.QuoteIssuer(self.issue)
        self.factory=ns.CurrentNativeServicesFactory(issuer=self.issuer)
        self.ledger.subscription_limits={'Luna':{'calls':2,'seconds':900,'per_call_seconds':450}}
    def issue(self,request,context):
        self.events.append('issue');self.issued.append((request,copy.deepcopy(context)))
        if self.error:raise self.error
        q=self.quote(request,**{'max_cost':self.max_cost,**self.mutate})
        if not self.skip_quote_trust:self.bind('per-request-quote',{'context':context,'quote':asdict(q)},q.receipt)
        return q
    def optin(self,permissions=(),naming=()):
        self.admission(c.digest(self.fact))
        self.a=replace(self.a,accounting_mode='per-request',accounting_policy='e'*64,quote_issuer_sha=self.issuer.fingerprint())
        for p,r in [('models','models'),('accounting','account'),('admission','authority'),('accounting-per-request','account')]:self.bind(p,asdict(self.a),r)
        cfg=self.native()
        cfg=replace(cfg,permission_inventory=permissions,naming_bindings=naming)
        self.control=replace(self.control,admission_sha=c.digest(asdict(self.a)),native=cfg,quotes=(),factory_sha=self.factory.fingerprint(),
            accounting_mode='per-request',accounting_policy=self.a.accounting_policy,quote_issuer_sha=self.a.quote_issuer_sha,issuer_receipt='issuer')
        self.rebind()
        self.wire=rb.WireBoundary(self.a,self.o,self.trust,ns.NativeLedger(self.ledger),c.Deadline(20),ledger_digest=f.previous.old.ledger_digest)
        return cfg
    def rebind(self):
        self.authorize(self.control)
        self.bind('quote-issuer',{'admission':asdict(self.a),'control':asdict(self.control),'issuer_sha':self.issuer.fingerprint()},self.control.issuer_receipt)
    def validate(self,selected):
        self.grant(selected,quotes=());self.rebind()
        ctx=rb.validate_stage_grant(self.a,self.trust,self.control,self.owned,selected)
        token=c.SELECTED_ADMISSION.set(ctx)
        try:self.factory.validate(self.control)
        finally:c.SELECTED_ADMISSION.reset(token)
    def http(self,bridge=None):return ns.NativeHTTP(self.wire,(),bridge or Mock(),self.control.native,control=self.control,issuer=self.issuer)
    def sdk_setup(self,role='subject-name'):
        import active_worker as worker
        packet={'source':'fixture source','unit':{'content':'fixture source','target_expression':'fixture','source_ranges':[[1,1]]},'domain':{'name':'fixture domain','description':'fixture domain description'}}
        self.optin();built=worker.build_request(role,packet,self.control.native.input_budget)
        permission={'kind':'sdk','provider':'openai','model':'gpt-6-luna','role':role,'inputBinding':built['inputBinding'],'sourceBinding':built['sourceBinding']}
        self.control=replace(self.control,native=replace(self.control.native,permission_inventory=(permission,),naming_bindings=(ns.naming_binding(permission),) if role=='subject-name' else ()))
        self.rebind()
        return worker,packet,built,permission
    def test_public_entry_real_factory_source_optin_no_quote_no_authority_issued(self):
        self.optin();self.grant(('source',),quotes=());self.rebind()
        with patch.object(rb,'run_owned_job',side_effect=lambda job,*a:job()),patch.object(ns.CurrentNativeServicesFactory,'build',side_effect=self.build):
            result=c.execute_live(self.a,self.o,self.trust,control=self.control,owned=self.owned,factory=self.factory,stages=('source',))
        self.assertEqual(result['values'],{'text':'fixture source'});self.assertEqual(self.issued,[]);self.assertEqual(result['physical_counts']['physical_post'],0)
        self.assertNotIsInstance(result,rb.StagePrior)
    def test_old_accounting_receipt_does_not_optin(self):
        self.optin();self.registry={r for r in self.registry if r[0]!='accounting-per-request'}
        with self.assertRaises(c.Stop):c.preflight(self.a,self.o,self.trust)
        self.assertFalse(self.issued)
    def test_unknown_mode_missing_policy_issuer_and_control_drift(self):
        self.optin()
        for kw in ({'accounting_mode':'bogus'},{'accounting_policy':''},{'quote_issuer_sha':''}):
            a=replace(self.a,**kw)
            for p,r in [('models','models'),('accounting','account'),('admission','authority'),('accounting-per-request','account')]:self.bind(p,asdict(a),r)
            with self.subTest(kw=kw),self.assertRaises(c.Stop):c.preflight(a,self.o,self.trust)
        for kw in ({'accounting_policy':'f'*64},{'quote_issuer_sha':'f'*64},{'issuer_receipt':'old-account'}):
            with self.subTest(kw=kw),self.assertRaises(c.Stop):rb.validate_accounting(self.a,replace(self.control,**kw),self.trust,self.issuer)
        with self.assertRaises(c.Stop):rb.validate_accounting(self.a,self.control,self.trust,None)
    def test_whole_default_static_quotes_does_not_invoke_issuer(self):
        f.FrontierTests.test_native_public_entry_zero_sdk_and_extract_only_quote_no_unused_write(self)
        self.assertFalse(self.issued)
        with self.assertRaises(c.Stop):rb.validate_accounting(self.a,self.control,self.trust,self.issuer)
    def test_factory_static_roles_inputs_and_naming_not_discarded(self):
        worker,packet,built,row=self.sdk_setup();self.validate(('place-subject',))
        good=self.control
        badrows=[{**row,'provider':'foreign'},{**row,'model':'foreign'},{**row,'role':'domain-name'},{**row,'inputBinding':''},{**row,'sourceBinding':''},{**row,'body_sha':'f'*64}]
        for row2 in badrows:
            self.control=replace(good,native=replace(good.native,permission_inventory=(row2,)))
            with self.subTest(row=row2),self.assertRaises(c.Stop):self.validate(('place-subject',))
        self.control=replace(good,native=replace(good.native,naming_bindings=()))
        with self.assertRaises(c.Stop):self.validate(('place-subject',))
        self.control=replace(good,native=replace(good.native,permission_inventory=()))
        with self.assertRaises(c.Stop):self.validate(('place-subject',))
        self.assertFalse(self.issued)
    def test_sdk_current_input_source_before_runtime(self):
        worker,packet,built,row=self.sdk_setup();bridge=Mock();http=self.http(bridge)
        changed=copy.deepcopy(packet);changed['source']='foreign source'
        with self.assertRaises(ns.NativeStop):http.sdk(worker,'subject-name',changed)
        bridge.exchange.assert_not_called();self.assertFalse(self.issued)
    def bridge_io(self,raw,text):
        """Only socket/process I/O is fake. Actual NodeBridge.exchange runs unmodified."""
        test=self
        class Stream:
            def __init__(self):self.i=0
            def readline(self,*a):
                self.i+=1
                if self.i==1:
                    test.events.append('preview')
                    return (json.dumps({'type':'wire','url':test.control.native.sdk_url,'body':raw})+'\n').encode()
                return (json.dumps({'type':'done','result':{'ok':True,'cost':.000001,'text':text}})+'\n').encode()
            def close(self):pass
        class Sock:
            def close(self):pass
            def fileno(self):return 99
            def settimeout(self,*a):pass
            def makefile(self,*a,**kw):return Stream()
            def shutdown(self,*a):pass
            def sendall(self,b):
                row=json.loads(b)
                if row.get('type')=='permit':
                    test.assertEqual(test.ledger.rows[-1]['state'],'reserved');test.events.append('permit')
        process=SimpleNamespace(pid=123,returncode=0,poll=lambda:0,wait=lambda **kw:0)
        bridge=nb.NodeBridge(self.control.native,c.Deadline(20),SimpleNamespace(spawning=False),str(self.home))
        return bridge,Sock,process
    def test_sdk_actual_python_preview_quote_escrow_permit_order(self):
        worker,packet,built,row=self.sdk_setup();self.validate(('place-subject',))
        output=json.dumps({'name':'fixture','description':'fixture description','source_concept':'fixture','original_expression':'fixture'})
        bridge,Sock,process=self.bridge_io('{"model":"gpt-6-luna","input":"opaque actual final"}',output)
        with patch.object(nb.socket,'socketpair',return_value=(Sock(),Sock())),patch.object(nb.subprocess,'Popen',return_value=process),patch.object(bridge,'argv',return_value=['fixture-only']):
            answer=self.http(bridge).sdk(worker,'subject-name',packet)
        self.assertEqual(answer['name'],'fixture');self.assertEqual(self.events,['preview','issue','permit'])
        self.assertEqual(self.wire.counts['sdk_subscription'],1);self.assertEqual(self.ledger.rows[-1]['state'],'done')
        self.assertEqual(self.issued[0][0].input_binding,built['inputBinding'])
    def test_sdk_wrong_final_input_or_role_no_quote_no_permit(self):
        worker,packet,built,row=self.sdk_setup()
        for kw in ({'role':'write'},{'provider':'foreign'},{'model':'foreign'},{'input_binding':'f'*64},{'source_binding':'f'*64}):
            req=c.Request('sdk','openai','gpt-6-luna','subject-name',b'actual',0,built['inputBinding'],built['sourceBinding'])
            with self.subTest(kw=kw),self.assertRaises(ns.NativeStop):self.http().final_quote(replace(req,**kw),(row,),input_binding=built['inputBinding'],source_binding=built['sourceBinding'])
            self.wire.stopped=False
        self.assertFalse(self.issued);self.assertFalse(self.ledger.rows)
    def test_final_quote_digest_expiry_ledger_inventory_and_trust_deny(self):
        row={'kind':'jev','provider':'jev','model':'fixture-jev','role':'selection'};self.optin((row,))
        req=c.Request('jev','jev','fixture-jev','selection',b'actual',1)
        for kw in ({'request_sha':'f'*64},{'expires':time.time()-1},{'ledger_binding':'f'*64},{'inventory_sha':'f'*64},{'max_cost':'NaN'},{'max_cost':'0'}):
            self.mutate=kw
            with self.subTest(kw=kw),self.assertRaises(ns.NativeStop):self.http().final_quote(req,(row,))
            self.wire.stopped=False
        self.mutate={};self.skip_quote_trust=True
        with self.assertRaises(ns.NativeStop):self.http().final_quote(req,(row,))
        self.assertFalse(self.ledger.rows)
    def test_issuer_exception_no_reservation_or_fallback(self):
        row={'kind':'jev','provider':'jev','model':'fixture-jev','role':'selection'};self.optin((row,));self.error=RuntimeError('fixture issuer failure')
        with self.assertRaises(ns.NativeStop):self.http().final_quote(c.Request('jev','jev','fixture-jev','selection',b'actual',1),(row,))
        self.assertEqual(len(self.issued),1);self.assertFalse(self.ledger.rows);self.assertTrue(self.wire.stopped)
    def test_jev_final_body_qcount_quote_then_actual_boundary(self):
        from urllib.request import Request
        row={'kind':'jev','provider':'jev','model':'fixture-jev','role':'selection'};self.optin((row,))
        body={'model':'fixture-jev','state':{'workerContract':{'role':'selection'}},'questions':{'q':{'type':'noul'}}}
        bridge=Mock()
        def exchange(payload,request,quote,wire,*,validate):
            self.assertEqual(json.loads(request.body),body);self.events.append('preview-final-body')
            return wire.attempt(request,quote,lambda r:validate({'body':{'model':'fixture-jev','answers':{'q':{'noul':.9}},'usage':{'cost':.000001}}}))
        bridge.exchange.side_effect=exchange
        result=self.http(bridge).http(Request(self.control.native.jev_url,data=json.dumps(body).encode(),method='POST'))
        self.assertEqual(json.load(result)['answers']['q']['noul'],.9);self.assertEqual(self.wire.counts['logical_q'],1);self.assertEqual(self.wire.counts['jev_http'],1)
    def test_q4_candidate_reserve_insufficient_no_send(self):
        row={'kind':'jev','provider':'jev','model':'fixture-jev','role':'worktime-actor'};self.optin((row,));self.max_cost='.044040192'
        req=c.Request('jev','jev','fixture-jev','worktime-actor',b'actual four questions',4);quote=self.http().final_quote(req,(row,));send=Mock()
        with self.assertRaises(BaseException):self.wire.attempt(req,quote,send)
        send.assert_not_called();self.assertFalse(self.ledger.rows);self.assertEqual(self.wire.counts['physical_post'],0)
    def test_unknown_after_permit_retains_hold_and_stops(self):
        row={'kind':'jev','provider':'jev','model':'fixture-jev','role':'selection'};self.optin((row,));req=c.Request('jev','jev','fixture-jev','selection',b'actual',1);quote=self.http().final_quote(req,(row,))
        with self.assertRaises(BaseException):self.wire.attempt(req,quote,Mock(side_effect=OSError('synthetic lost response')))
        self.assertEqual(self.ledger.rows[-1]['state'],'reserved');self.assertEqual(self.wire.counts['physical_post'],1)
        with self.assertRaises(ns.NativeStop):self.http().final_quote(req,(row,))
    def test_stage_context_binds_policy_and_issuer(self):
        self.optin();self.grant(('extract',),quotes=());self.rebind()
        p=self.prior('extract',values={'text':'fixture source'});self.control=replace(self.control,accounting_policy='f'*64)
        with self.assertRaises(c.Stop):rb.validate_prior(('extract',),p,self.a,self.control,self.owned,self.trust)
    def test_history_deadline_caps_and_pending_preserved(self):
        # Reuse actual guarded public entry protections after the changed constructors.
        self.factory=rb.PortedFactory(self.build)
        f.FrontierTests.test_ledger_pending_reset_foreign_binding_and_deadline_not_renewed(self)
    def test_history_counters_no_reset(self):
        self.factory=rb.PortedFactory(self.build)
        f.FrontierTests.test_history_scope_split_does_not_reset_sdk2_or_jev9_q15(self)
    def test_bridge_pair_bytes_unchanged(self):
        self.assertIn('result=wire.attempt(expected,quote,send)',(BASE/'native_bridge.py').read_text())
        self.assertIn("redirect:'error'",(BASE/'native_bridge.mjs').read_text())

if __name__=='__main__':unittest.main(verbosity=2)
