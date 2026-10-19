"""One changed-native bundle. No actual SDK/model/auth/DB or Source services.
Public Python signatures: AST strict fakes. Actual Node public hosts: dummy runtime.
"""
import ast
import copy
from dataclasses import asdict,replace,dataclass
import importlib
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from typing import Callable
import unittest
from unittest.mock import Mock,create_autospec,patch
OUT=Path(__file__).resolve().parent; HERE=OUT.parent; ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(HERE/'binding-completion-01')]
import test_real_bindings as previous
import controller as c
import real_bindings as rb
import native_services as ns
import native_bridge as nb
old=previous.old
S4=previous.S4; RUNNER=S4.parent
sys.path.append(str(RUNNER))
# Pure packet contracts only. No services/model constructors or SDK imports.
import writer_worker as writer
import active_worker as worker
import active_judgements as aj
import capture_audit as ca
import runner
SIGNATURES={}
def function(module,symbol,body=True):
    path=(S4 if module in ('place_write','active_judgements') else RUNNER)/(module+'.py')
    tree=ast.parse(path.read_text()); node=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==symbol))
    SIGNATURES[module+'.'+symbol]=ast.unparse(node.args)
    if not body: node.body=[ast.Pass()]
    namespace={'json':json,'urlopen':Mock(side_effect=AssertionError('no network')),'time':time,'CHUNK':20}
    from urllib.request import Request
    namespace['Request']=Request
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(path),'exec'),namespace)
    return namespace[symbol]
def sdk_body(request):
    ctx=request['context']
    return {'model':'gpt-6-luna','input':[{'role':'system','content':ctx['systemPrompt']},{'role':'user','content':ctx['messages'][0]['content']}],
            'store':False,'stream':True,'reasoning':{'effort':'medium'}}
def raw(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
class FixtureBridge(nb.NodeBridge):
    mode='ok'
    def argv(self,fd):return ['node',str(OUT/'fixture-bridge.mjs'),str(fd),str(OUT/'dummy-runtime.mjs'),self.mode]
class NativeTests(unittest.TestCase):
    bind=previous.BindingTests.bind
    request=previous.BindingTests.request
    quote=previous.BindingTests.quote
    build=previous.BindingTests.build
    authorize=previous.BindingTests.authorize
    def setUp(self):
        previous.BindingTests.setUp(self)
        self.factory=ns.CurrentNativeServicesFactory()
        self.persist=OUT/('owned-'+self._testMethodName);self.persist.mkdir(exist_ok=True)
        self.deadline=c.Deadline(12)
        cache=self.home/'cache';cache.mkdir();(cache/'fixture.json').write_text('{"synthetic":true}')
        conf=self.home/'public-embedding.json';conf.write_text('{"embed":{"provider":"openrouter","model_dir":"/synthetic/no-model"}}')
        self.ledger.path.touch()
        # Direct WireBoundary fixtures pin the physical model; native factory separately
        # maps it to the original Luna carry account through NativeLedger.
        self.ledger.subscription_limits={'gpt-6-luna':{'calls':3,'seconds':2700,'per_call_seconds':900}}
        self.cfg=ns.NativeConfig('synthetic-jev','https://synthetic.invalid/v1/systemone','https://synthetic.invalid/responses',
          str(OUT/'dummy-auth.mjs'),c.sha((OUT/'dummy-auth.mjs').read_bytes()),str(conf),c.sha(conf.read_bytes()),str(cache),
          (('fixture.json',c.sha((cache/'fixture.json').read_bytes())),),'synthetic-embed',str(self.ledger.path),
          (('judging',.039),('generation',1)),(('Luna',{'calls':3,'seconds':2700,'per_call_seconds':900}),),290000,())
        self.extract={'source':'fixture source','source_start':1,'chunk_range':[1,1],'origin':'fixture','migration':False}
        self.write={'source':'fixture source','unit':{'content':'fixture source','source_ranges':[[1,1]],'target_expression':'fixture','host_id':'fixture-host','unit_id':'fixture-unit'},
                    'chosen_domain':{'name':self.fact['domain'],'description':'fixture domain'},'chosen_subject':{'name':self.fact['subject'],'description':'fixture subject'}}
        self.requests=[]
        for module,role,packet in ((worker,'extract',self.extract),(writer,'write',self.write)):
            body=sdk_body(module.build_request(role,packet,self.cfg.input_budget))
            self.requests.append(c.Request('sdk','openai','gpt-6-luna',role,raw(body),0))
        self.quotes=tuple(self.quote(r) for r in self.requests)
        self.cfg=replace(self.cfg,request_inventory=tuple(c.request_identity(r) for r in self.requests))
        self.control=replace(self.control,native=self.cfg,factory_sha=self.factory.fingerprint(),evidence_directory=str(self.persist),quotes=self.quotes)
        self.authorize(self.control)
        self.wire=rb.WireBoundary(self.a,self.o,self.trust,self.ledger,self.deadline,ledger_digest=old.ledger_digest)
        self.bridge=FixtureBridge(self.cfg,self.deadline,ns.ProcessGuard(),self.persist)
        self.http=ns.NativeHTTP(self.wire,self.quotes,self.bridge,self.cfg)
    def add_jev(self,body):
        role=body.get('state',{}).get('workerContract',{}).get('role','routing')
        req=self.http.request('jev',role,body);q=self.quote(req);self.http.quotes[q.request_sha]=q
        return req,q
    def test_native_sdk_public_writer_and_worker_sse_count_reserve(self):
        before=set(self.persist.glob('native-child-*.json'))  # preserve earlier failed PID receipts
        with patch.object(nb.subprocess,'Popen',old.RAW_POPEN):
            extract=self.http.sdk(worker,'extract',self.extract)
            answer=self.http.sdk(writer,'write',self.write)
        self.assertEqual(len(extract['items']),1);self.assertEqual(answer['source_ranges'],[[1,1]])
        self.assertEqual(self.wire.counts,{'physical_post':2,'jev_http':0,'logical_q':0,'sdk_subscription':2,'embedding_post':0})
        self.assertEqual(self.wire.sdk_completed,2);self.assertTrue(all(r['state']=='done' for r in self.ledger.rows[1::2]))
        receipts=[p for p in self.persist.glob('native-child-*.json') if p not in before];self.assertEqual(len(receipts),2)
        self.assertTrue(all(json.loads(p.read_text())['exit_code']==0 for p in receipts))
    def test_native_actor_public_projection_and_template_questions(self):
        packet={'template_id':'synthetic-only','template_version':1,'state':{'narrative':'fixture source','candidate_fact':'fixture sentence','private':'drop'},
                'questions':{'Q1':{'type':'noul','instructions':'synthetic Q1','criteria':{'true':'yes','false':'no'}},
                             'Q2':{'type':'noul','instructions':'synthetic Q2','criteria':{'true':'yes','false':'no'}}}}
        body=aj.bind_body('worktime-actor',runner.build_request({**packet,'model':self.cfg.jev_model},'state'),
                          template={'template_id':packet['template_id'],'template_version':1},original=packet)
        self.add_jev(body)
        with patch.object(nb.subprocess,'Popen',old.RAW_POPEN):
            answer=aj.make_actor_judge({},judge=self.http.actor)(packet)
        self.assertEqual(set(answer['answers']),{'Q1','Q2'});self.assertNotIn('workerContract',packet['state'])
        self.assertEqual(answer['worker_contract']['role'],'worktime-actor')
        self.assertEqual(self.wire.counts['logical_q'],2);self.assertEqual(self.wire.counts['jev_http'],1)
    def test_all_public_judgement_roles_share_boundary(self):
        cfg={'jev_model':self.cfg.jev_model,'jev_base_url':'https://synthetic.invalid','jev_api_key':'SYNTHETIC_PLACEHOLDER'}
        calls=[]
        def collect(req,**kw):
            body=json.loads(req.data);self.add_jev(body);calls.append(body)
            import io
            return io.BytesIO(json.dumps({'answers':{k:({'choice':'fact','probabilities':{'fact':1}} if q['type']=='choice' else {'noul':.99}) for k,q in body['questions'].items()}}).encode())
        ask=function('worker_tools','make_ask')
        # Real public makers with recording http; replay those actual projected final requests through one native boundary.
        with patch.dict(sys.modules,{'worker_tools':SimpleNamespace(make_ask=ask)}):
            makers=[ca.make_judge(cfg,http=aj.wire('selection',collect),max_attempts=1,text_limit=None),
                    aj.make_ask(cfg,'placement',http=collect),aj.make_ask(cfg,'grounding',http=collect)]
            makers[0]({'sentence':'fixture'},['unit'],ns.CHOICE_QUESTIONS['kind']+'items[{i}]',{'fact':'fact'})
            makers[1]({'unit':{'content':'fixture'}},['identity'],'items[{i}]')
            makers[2]({'sentence':'fixture'},['Q1','Q2'],'items[{i}]')
        with patch.object(nb.subprocess,'Popen',old.RAW_POPEN):
            from urllib.request import Request
            for body in calls:self.http.http(Request(self.cfg.jev_url,data=json.dumps(body,ensure_ascii=False).encode(),method='POST'),timeout=999)
        self.assertEqual(self.wire.counts['physical_post'],3);self.assertEqual(self.wire.counts['logical_q'],4)
        self.assertEqual(self.wire.counts['embedding_post'],0)
    def test_unknown_quote_and_unselected_role_stop_before_process(self):
        self.http.quotes.clear()
        with patch.object(nb.subprocess,'Popen') as spawn,self.assertRaises(ns.NativeStop):self.http.sdk(writer,'write',self.write)
        spawn.assert_not_called()  # missing candidate quote stops before runtime creation.
        self.assertEqual(self.wire.counts['physical_post'],0)
        self.wire.stopped=False
        with patch.object(nb.subprocess,'Popen') as spawn,self.assertRaises(ns.NativeStop):self.http.sdk(worker,'describe',{})
        spawn.assert_not_called()
    def test_native_bad_sse_wrong_model_and_bypass_hold_no_retry(self):
        for mode in ('truncated','wrongmodel','bypass'):
            with self.subTest(mode=mode):
                ledger=old.Ledger(self.home/(mode+'.jsonl'),self.a.db_plan_sha,{'generation':1},
                  subscription_limits={'gpt-6-luna':{'calls':3,'seconds':2700,'per_call_seconds':900}},cash_limit=.039)
                wire=rb.WireBoundary(self.a,self.o,self.trust,ledger,self.deadline,ledger_digest=old.ledger_digest)
                bridge=FixtureBridge(self.cfg,self.deadline,ns.ProcessGuard(),self.persist);bridge.mode=mode
                http=ns.NativeHTTP(wire,self.quotes,bridge,self.cfg)
                with patch.object(nb.subprocess,'Popen',old.RAW_POPEN),self.assertRaises(ns.NativeStop):http.sdk(writer,'write',self.write)
                self.assertEqual(wire.counts['physical_post'],1);self.assertEqual(wire.sdk_completed,0)
                self.assertEqual(ledger.rows[-1]['state'],'reserved')
                with self.assertRaises(ns.NativeStop):http.sdk(writer,'write',self.write)
                self.assertEqual(wire.counts['physical_post'],1)
    def test_malformed_ipc_stops_before_effect(self):
        self.bridge.mode='badipc'
        with patch.object(nb.subprocess,'Popen',old.RAW_POPEN),self.assertRaises(ns.NativeStop):self.http.sdk(writer,'write',self.write)
        self.assertEqual(self.wire.counts['physical_post'],0);self.assertEqual(self.ledger.rows,[])
        for path in self.persist.glob('native-child-*.json'):
            self.assertFalse(Path('/proc',str(json.loads(path.read_text())['pid'])).exists())
    def test_real_deadline_propagates_and_child_cleanup_persists(self):
        self.deadline=c.Deadline(.7,cleanup=.2)
        self.wire.deadline=self.deadline;self.bridge.deadline=self.deadline;self.bridge.mode='timeout'
        with patch.object(nb.subprocess,'Popen',old.RAW_POPEN),self.assertRaises(ns.NativeStop):self.http.sdk(writer,'write',self.write)
        self.assertEqual(self.ledger.rows[-1]['state'],'reserved')
        self.assertLess(time.monotonic()-self.deadline.started,1)
        for p in self.persist.glob('native-child-*.json'):
            pid=json.loads(p.read_text())['pid'];self.assertFalse(Path('/proc',str(pid)).exists())
    def test_factory_costproof_provision_and_default_entry_gate(self):
        self.factory.validate(self.control)
        for native in (None,replace(self.cfg,request_inventory=()),replace(self.cfg,auth_sha='0'*64)):
            with self.subTest(native=type(native).__name__),self.assertRaises(c.Stop):self.factory.validate(replace(self.control,native=native))
        empty=replace(self.control,quotes=());self.authorize(empty)
        with patch.object(ns.CurrentNativeServicesFactory,'build') as build,patch.object(rb,'run_owned_job') as job,self.assertRaises(c.Stop):
            c.execute_live(self.a,self.o,self.trust,control=empty,owned=self.owned)
        build.assert_not_called();job.assert_not_called()
    def test_default_native_factory_builds_actual_binding_and_public_ports(self):
        modules={}
        for key,(module,symbol) in rb.PUBLIC.items():
            modules.setdefault(module,SimpleNamespace());setattr(modules[module],symbol,self.api[key])
        ports_node=next(n for n in ast.parse((S4/'place_write.py').read_text()).body if isinstance(n,ast.ClassDef) and n.name=='Ports')
        namespace={'dataclass':dataclass,'Callable':Callable};exec(compile(ast.Module(body=[ports_node],type_ignores=[]),'Ports','exec'),namespace)
        pw=modules['place_write'];pw.Ports=namespace['Ports'];pw.DOMAIN_CRITERION=worker.DOMAIN_CRITERION;pw.model_view=function('place_write','model_view')
        ask=function('worker_tools','make_ask');wt=SimpleNamespace(make_ask=create_autospec(ask,spec_set=True,side_effect=ask))
        choose=function('domain_router','make_choose')
        modules['domain_router'].make_choose=create_autospec(choose,spec_set=True,side_effect=choose)
        modules['domain_router'].SAME_Q='items[{i}]'
        encode=create_autospec(lambda texts:None,spec_set=True,side_effect=lambda texts:[[1.0] for t in texts])
        embedding=SimpleNamespace(MODEL_ID=self.cfg.embed_model+'@openrouter',configure_cache=Mock(),encode_queries=encode)
        modules.update(active_judgements=aj,worker_tools=wt,capture_audit=ca,embed=embedding,writer_worker=writer,active_worker=worker,safety=sys.modules['safety'],runner=runner)
        modules['store_pg'].driver=SimpleNamespace(__name__='psycopg');modules['psycopg.conninfo']=SimpleNamespace(make_conninfo=self.make_dsn)
        packets=[{'template_id':'synthetic','template_version':1,'state':{'narrative':name},
                  'questions':{'Q':{'type':'noul','instructions':'synthetic question','criteria':{'true':'yes','false':'no'}}}} for name in ('worktime','digest')]
        requests=list(self.requests);quotes=list(self.quotes)
        for packet in packets:
            body=aj.bind_body('worktime-actor',runner.build_request({**packet,'model':self.cfg.jev_model},'state'),
                              template={'template_id':'synthetic','template_version':1},original=packet)
            req,q=self.add_jev(body);requests.append(req);quotes.append(q)
        cfg=replace(self.cfg,request_inventory=tuple(c.request_identity(r) for r in requests))
        control=replace(self.control,native=cfg,quotes=tuple(quotes));self.authorize(control)
        self.api['extract'].side_effect=lambda ports,*args,**kw:ports.worker('extract',self.extract)['items']
        self.api['place'].side_effect=lambda kind,*args,**kw:self.write['chosen_'+kind] and {'chosen':self.write['chosen_'+kind]}
        original_worktime=self.api['worktime'].side_effect;original_digest=self.api['digest'].side_effect
        def worktime(dsn,window,judge,**kw):judge(packets[0]);return original_worktime(dsn,window,judge,**kw)
        def digestion(dsn,unit,judge,**kw):judge(packets[1]);return original_digest(dsn,unit,judge,**kw)
        self.api['worktime'].side_effect=worktime;self.api['digest'].side_effect=digestion
        with patch.object(ns.ProcessGuard,'install'),patch.object(nb,'NodeBridge',FixtureBridge),patch.object(ns.importlib,'import_module',side_effect=lambda name:modules[name]),patch.dict(sys.modules,{'worker_tools':wt}),patch.dict(os.environ,{},clear=False),patch.object(rb,'run_owned_job',side_effect=lambda job,directory,deadline:job()),patch.object(nb.subprocess,'Popen',old.RAW_POPEN):
            result=c.execute_live(self.a,self.o,self.trust,control=control,owned=self.owned)
        self.assertEqual(result['status'],'PUBLIC_CORE_RETURNED')
        self.assertEqual(self.events,['record_unit','record','worktime','complete','route','digest'])
        self.assertEqual(result['physical_counts'],{'physical_post':4,'jev_http':2,'logical_q':2,'sdk_subscription':2,'embedding_post':0})
        self.assertEqual(result['sdk_completed'],2);self.assertFalse(result['full10'])
        embedding.configure_cache.assert_called_once_with(self.cfg.cache_directory)
        self.assertEqual(self.api['worktime'].call_args.args[1],1)
        self.assertIsNone(self.api['digest'].call_args.kwargs['maintenance'])
        self.assertEqual(self.api['digest'].call_args.kwargs['budget'],1)
    def test_embedding_all_warm_query_and_direct_http_effect_guard(self):
        def job():
            import urllib.request
            import embedding_cache
            tree=ast.parse((RUNNER/'embed.py').read_text())
            names=('_cached_encode','_encode','encode_queries','encode_passages','encode_query')
            nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
            namespace={'models':SimpleNamespace(check_provider=lambda provider:None),'PROVIDER':'openrouter',
                       'MODEL_ID':'SYNTHETIC','CACHE':embedding_cache.VectorCache(),'urllib':__import__('urllib'),'os':os,'json':json}
            exec(compile(ast.Module(body=nodes,type_ignores=[]),str(RUNNER/'embed.py'),'exec'),namespace)
            embed=SimpleNamespace(**{name:namespace[name] for name in names})
            warm=function('embedding_inputs','warm')
            warm.__globals__['collect']=create_autospec(function('embedding_inputs','collect',body=False),spec_set=True,
                                                       return_value={'query':['fixture query'],'passage':['fixture passage']})
            guard=ns.ProcessGuard();guard.install();blocked=[]
            with patch.dict(sys.modules,{'embed':embed}):
                for name,fn in (('warm-query',lambda:warm([{'fact':'SyntheticMetadata'}])),
                                ('query',lambda:embed.encode_query('missing')),('passage',lambda:embed.encode_passages(['missing']))):
                    guard.arm_profile()
                    try:fn()
                    except ns.NativeStop:blocked.append(name)
                namespace['CACHE'].put_many('SYNTHETIC','query',['fixture query'],[[1.0]])
                guard.arm_profile()
                try:warm([{'fact':'SyntheticMetadata'}])
                except ns.NativeStop:blocked.append('warm-passage')
                namespace['CACHE'].put_many('SYNTHETIC','passage',['fixture passage'],[[1.0]])
                guard.arm_profile()
                cached=warm([{'fact':'SyntheticMetadata'}])
            return {'blocked':blocked,'physical':0,'cachedWarm':cached=={'query':['fixture query'],'passage':['fixture passage']}}
        result=rb.run_owned_job(job,self.persist,c.Deadline(2))
        self.assertEqual(len(result['blocked']),4);self.assertEqual(result['physical'],0);self.assertTrue(result['cachedWarm'])
        self.assertFalse(result['owned_job']['group_remaining'])
        self.assertTrue(Path(result['evidence_path'],'cleanup.json').exists())
    def test_native_factory_fingerprint_and_stdio_secret_absent(self):
        self.assertEqual(len(self.factory.fingerprint()),64)
        for path in self.persist.glob('*.json'):self.assertNotIn('SYNTHETIC_NEVER_LOG_KEY',path.read_text())
        self.assertFalse((S4/c.ALIAS).exists())
        self.assertNotIn('embed',sys.modules);self.assertNotIn('onnxruntime',sys.modules)

if __name__=='__main__':
    loader=unittest.TestLoader()
    if len(sys.argv)>1:suite=loader.loadTestsFromNames(sys.argv[1:],module=sys.modules[__name__])
    else:
        suite=loader.loadTestsFromTestCase(NativeTests)
        suite.addTests(previous.BindingTests(name) for name in ('test_exact_public_arguments_results_order_and_metadata_restore','test_unknown_quote_or_unreviewed_transport_stops_before_factory','test_applied_connection_options_and_expired_whole_deadline'))
        suite.addTests(old.ControllerTests(name) for name in ('test_reserve_precedes_physical_send_and_receipts_link_provenance','test_unresolved_old_reserve_and_cached_result_never_injected'))
    start=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(suite)
    receipt={'cases':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
             'seconds':time.monotonic()-start,'realSDK':0,'realAuth':0,'realModel':0,'realAPI':0,'realDB':0,'standard':0,
             'failedCases':[test.id() for test,_ in result.failures+result.errors],'claim':'synthetic public-port source-only, not semantic or live proof'}
    label='focused-result' if len(sys.argv)==1 else 'repair-result-'+str(time.time_ns())
    (OUT/(label+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    (OUT/'api-signatures.json').write_text(json.dumps({**previous.SIGNATURES,**SIGNATURES},indent=2)+'\n')
    print(json.dumps(receipt));raise SystemExit(not result.wasSuccessful())
