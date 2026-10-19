"""Native public-port composition. No services/config/auth/SDK imports at module load.
D10/S0: cache hits only for embeddings; every cache-miss egress is a fatal STOP.
"""
from dataclasses import dataclass, asdict
import importlib
import io
import json
import os
from pathlib import Path
import sys
import threading
import controller as c

class NativeStop(BaseException):
    """Must escape product Exception retry/fallback handlers."""

@dataclass(frozen=True)
class NativeConfig:
    jev_model: str
    jev_url: str
    sdk_url: str
    auth_module: str
    auth_sha: str
    public_config: str
    public_config_sha: str
    cache_directory: str
    cache_manifest: tuple
    embed_model: str
    ledger_path: str
    caps: tuple
    subscription_limits: tuple
    input_budget: int
    request_inventory: tuple  # final request_identity values; externally approved, no credentials
    naming_bindings: tuple = ()  # approved {provider,model,role,inputBinding,sourceBinding} rows
    permission_inventory: tuple = ()  # opt-in static provider/role/current-input rights; never final quotes
    sdk_profile: object = None  # nonsecret exact public physical-model descriptor
    sdk_runtime_sha: str = ''

class ProcessGuard:
    """Public CPython audit in the owned disposable child, NOT a kernel sandbox.
    libpq is the separately admitted SQL driver/DSN. Python inference HTTP/socket,
    native inference imports and unexpected subprocesses are refused before effect.
    No private symbol is replaced. The Node child has its own network broker.
    """
    def __init__(self):
        self.spawning=False
        self.active=True
        self.embed_file=str(Path(__file__).resolve().parents[3]/'experiments/v2-knowledge-module-runner-01/embed.py')
    def audit(self,event,args):
        if not self.active: return
        if event in ('urllib.Request','socket.connect','socket.getaddrinfo'):
            raise NativeStop('unbrokered inference/network STOP (SQL uses admitted libpq DSN)')
        if event=='import' and args[0].split('.')[0] in ('onnxruntime','tokenizers'):
            raise NativeStop('unported local inference STOP')
        if event in ('subprocess.Popen','os.system','os.exec','os.posix_spawn') and not self.spawning:
            raise NativeStop('unbrokered process STOP')
    def profile(self,frame,event,arg):
        # Public process-scope profiling, not replacement of any private function.
        # _cached_encode calls _encode only on a MISS; stop before _remote config/auth,
        # transport retry/hedge, or local inference can start. Hits remain usable.
        if self.active and event=='call' and frame.f_code.co_filename==self.embed_file and frame.f_code.co_name in ('_encode','_remote','_infer','encode_model'):
            raise NativeStop('unported embedding cache MISS/evaluation STOP before config/inference')
    def arm_profile(self):
        sys.setprofile(self.profile)
        threading.setprofile(self.profile)
    def install(self):
        sys.addaudithook(self.audit)
        self.arm_profile()

class NativeLedger:
    """Retain stock Luna subscription carry while quoting physical gpt-6-luna."""
    def __init__(self,ledger): self.ledger=ledger
    def __getattr__(self,name): return getattr(self.ledger,name)
    def call(self,*args,**kw):
        if kw.get('account')=='subscription':
            c.require(kw.get('model')=='gpt-6-luna','native subscription model drift')
            kw['model']='Luna'
        return self.ledger.call(*args,**kw)

NAMING_KEYS={'provider','model','role','inputBinding','sourceBinding'}
def naming_binding(identity):
    """Thin metadata projection only; active_worker owns all input construction."""
    value={key:identity[key] for key in NAMING_KEYS}
    c.require(value['provider']=='openai' and value['model']=='gpt-6-luna'
              and value['role']=='subject-name','unsupported naming provider/model/role')
    c.require(all(type(value[key]) is str and len(value[key])==64
                  and all(ch in '0123456789abcdef' for ch in value[key])
                  for key in ('inputBinding','sourceBinding')),'malformed naming binding')
    return value
def naming_request_binding(identity):
    c.require(set(identity)==NAMING_KEYS|{'kind','body_sha','logical_questions'}
              and identity['kind']=='sdk' and type(identity['logical_questions']) is int
              and identity['logical_questions']==0 and type(identity['body_sha']) is str
              and len(identity['body_sha'])==64
              and all(ch in '0123456789abcdef' for ch in identity['body_sha']),
              'malformed naming request identity')
    return naming_binding(identity)

PERMISSION_KEYS={'kind','provider','model','role'}

def public_source_roots():
    """Bind source imports to this repository-shaped public extraction, never cwd/HOME."""
    current = Path(__file__).absolute()
    root = current.parents[3]
    runner = root/'experiments/v2-knowledge-module-runner-01'
    scale = runner/'scale-04'
    expected = root/'experiments/v2-native-minlive/unit1-controller-source-phase1/native_services.py'
    for path in (root, runner, scale, expected, current.with_name('native_bridge.py'), current.with_name('native_bridge.mjs')):
        c.require(path.exists() and path.resolve() == path and not path.is_symlink(), 'public source containment drift')
    c.require(current == expected, 'repository-shaped Native source required')
    return root, runner, scale

def permission(row,jev_model):
    c.require(type(row) is dict and row.get('kind') in ('sdk','jev','embedding'), 'typed static permission required')
    if row['kind']=='embedding':
        c.require(set(row)==PERMISSION_KEYS|{'sourceBinding','inputScope','dimensions','format'}
                  and row['provider']=='openrouter' and row['model']=='perplexity/pplx-embed-v1-0.6b'
                  and row['role'] in ('query','passage') and row['inputScope']=='unit-derived'
                  and row['dimensions']==1024 and row['format']=='raw'
                  and type(row['sourceBinding']) is str and len(row['sourceBinding'])==64,
                  'embedding static permission drift')
        return dict(row)
    sdk=row['kind']=='sdk'
    c.require(set(row)==PERMISSION_KEYS|({'inputBinding','sourceBinding'} if sdk else set()),
              'closed static permission schema required')
    c.require(row['provider']==('openai' if sdk else 'jev') and row['model']==('gpt-6-luna' if sdk else jev_model)
              and type(row['role']) is str and bool(row['role']), 'static provider/model/role drift')
    if sdk:
        c.require(row['role'] in ('extract','write','subject-name'), 'static SDK role not admitted')
        c.require(all(type(row[k]) is str and len(row[k])==64 and all(ch in '0123456789abcdef' for ch in row[k])
                      for k in ('inputBinding','sourceBinding')), 'current SDK input/source binding required')
    return dict(row)


class NativeHTTP:
    def __init__(self,wire,quotes,bridge,config,*,control=None,issuer=None):
        self.wire,self.bridge,self.config=wire,bridge,config
        self.control,self.issuer=control,issuer
        self.dynamic=control is not None and control.accounting_mode=='per-request'
        self.quotes={q.request_sha:q for q in quotes}
        c.require(len(self.quotes)==len(quotes),'duplicate native quote identity')
        if self.dynamic:
            from real_bindings import validate_accounting
            validate_accounting(wire.admission,control,wire.trust,issuer)
            if control.sdk_quota is not None or control.embedding_policy is not None:
                self.wire.configure_resources(control)

    def final_quote(self,request,approved,*,input_binding='',source_binding=''):
        """Existing SDK preview callback and Jev final body; never permission from issuer."""
        from real_bindings import validate_accounting
        try:
            c.require(not self.wire.stopped,'quote after terminal STOP')
            validate_accounting(self.wire.admission,self.control,self.wire.trust,self.issuer)
            row={'kind':request.kind,'provider':request.provider,'model':request.model,'role':request.role}
            if request.kind=='sdk':
                c.require(request.input_binding==input_binding and request.source_binding==source_binding,
                          'actual SDK current-input metadata drift')
                row.update(inputBinding=input_binding,sourceBinding=source_binding)
            if request.kind=='embedding':
                row.update(sourceBinding=request.source_binding,inputScope='unit-derived',dimensions=1024,format='raw')
                c.require(self.control.embedding_policy is not None and request.source_binding==self.wire.admission.provenance.source_sha,
                          'embedding source scope not granted')
            c.require(permission(row,self.config.jev_model) in approved,'actual wire lacks static permission')
            context={'policy_sha':self.control.accounting_policy,'issuer_sha':self.control.quote_issuer_sha,
                     'control_sha':c.digest(asdict(self.control)),'request':c.request_identity(request)}
            context_sha=c.digest(context)
            quote=self.issuer.issue(request,context)
            c.require(c.digest(context)==context_sha,'issuer mutated policy/request context')
            if request.kind=='sdk' and self.control.sdk_quota is not None:
                policy=self.control.sdk_quota
                c.require(type(quote) is c.SubscriptionQuota and quote.profile_sha==policy.profile_sha
                          and quote.limits_sha==policy.limits_sha and quote.call_seconds==policy.call_seconds
                          and quote.request_sha==c.digest(c.request_identity(request))
                          and quote.inventory_sha==self.wire.admission.inventory_sha
                          and quote.ledger_binding==self.wire.admission.db_plan_sha
                          and c.math.isfinite(quote.expires) and quote.expires>c.time.time(), 'invalid subscription authorization')
                self.wire.trust.check('per-request-sdk-quota',{'context':context,'authorization':asdict(quote)},quote.receipt)
                return quote
            c.require(type(quote) is c.Quote and quote.request_sha==c.digest(c.request_identity(request))
                      and quote.inventory_sha==self.wire.admission.inventory_sha
                      and quote.ledger_binding==self.wire.admission.db_plan_sha
                      and c.Decimal(quote.max_cost).is_finite() and c.Decimal(quote.max_cost)>0
                      and c.math.isfinite(quote.expires) and quote.expires>c.time.time(),
                      'issuer final quote malformed/stale/drift')
            self.wire.trust.check('per-request-quote',{'context':context,'quote':asdict(quote)},quote.receipt)
            return quote
        except BaseException:
            self.wire.stopped=True
            raise NativeStop('per-request quote STOP before reserve/permit') from None
    def encode(self,texts,role='query'):
        """Exact cache hits, or one quoted broker send; never Python inference/retry."""
        try:
            from embedding_cache import VectorCache
            c.require(role in ('query','passage') and type(texts) in (list,tuple)
                      and all(type(t) is str and bool(t.strip()) for t in texts),'invalid encoder input')
            cache=VectorCache(self.config.cache_directory)
            model=self.config.embed_model;model_id=model+'@openrouter'
            unique=list(dict.fromkeys(texts));found={t:cache.get(model_id,role,t) for t in unique}
            missing=[t for t in unique if found[t] is None]
            if missing:
                c.require(self.dynamic and type(self.control.embedding_policy) is c.EmbeddingPolicy,
                          'embedding miss requires explicit grant')
                body={'model':model,'input':missing}
                raw=json.dumps(body,ensure_ascii=False,allow_nan=False).encode()
                req=c.Request('embedding','openrouter',model,role,raw,0,c.digest(missing),self.wire.admission.provenance.source_sha)
                quote=self.final_quote(req,self.config.permission_inventory)
                url=self.config.jev_url.removesuffix('/v1/systemone')+'/v1/embeddings'
                result=self.bridge.exchange({'kind':'embedding','url':url,'body':body,'role':role},req,quote,self.wire,
                                            validate=lambda r:self.validate_embedding(r,body))
                vectors=result['vectors']
                # exchange returns only AFTER normal Ledger settlement. No partial/lucky cache.
                cache.put_many(model_id,role,missing,vectors)
                found.update(zip(missing,vectors))
            c.require(all(type(v) is list and len(v)==1024 and all(type(x) in (int,float) and c.math.isfinite(x) for x in v)
                          for v in found.values()),'cached vector model/dimension/value drift')
            return [list(found[t]) for t in texts]
        except BaseException:
            self.wire.stopped=True
            raise NativeStop('quoted encoder STOP; no retry/no partial cache') from None

    def validate_embedding(self,result,request):
        body=result['body'];model=request['model']
        c.require(body.get('model') in (model,model.split('/',1)[-1]) and not body.get('error'), 'embedding response model/error')
        data=sorted(body['data'],key=lambda row:row['index'])
        c.require([r['index'] for r in data]==list(range(len(request['input'])))
                  and all(type(r['embedding']) is list and len(r['embedding'])==1024
                          and all(type(x) in (int,float) and c.math.isfinite(x) for x in r['embedding']) for r in data),
                  'embedding response count/dimensions/values')
        usage=body.get('usage',{});cost=c.Decimal(str(usage.get('cost')))
        c.require(cost.is_finite() and cost>=0,'embedding actual usage unknown')
        return {'accepted':True,'usage_cost':str(cost),'vectors':[r['embedding'] for r in data],'body':body}

    def request(self,kind,role,body):
        raw=json.dumps(body,ensure_ascii=False,allow_nan=False).encode()
        return c.Request(kind,'openai' if kind=='sdk' else 'jev',
                         'gpt-6-luna' if kind=='sdk' else self.config.jev_model,
                         role,raw,len(body['questions']) if kind=='jev' else 0)
    def quote(self,request):
        q=self.quotes.get(c.digest(c.request_identity(request)))
        c.require(q is not None,'final body/model hard quote absent; before POST STOP')
        return q
    def http(self,request,*,timeout=None):
        try:
            body=json.loads(request.data)
            c.require(request.get_method()=='POST' and request.full_url==self.config.jev_url
                      and body['model']==self.config.jev_model,'native Jev endpoint/model drift')
            role=body.get('state',{}).get('workerContract',{}).get('role','routing')
            final=self.request('jev',role,body)
            result=self.bridge.exchange({'kind':'jev','url':request.full_url,'body':body,'role':role},
                                        final,(self.final_quote(final,self.config.permission_inventory) if self.dynamic else self.quote(final)),self.wire,validate=lambda r:self.validate_jev(r,body))
            return io.BytesIO(json.dumps(result['body'],ensure_ascii=False,allow_nan=False).encode())
        except NativeStop: raise
        except BaseException: raise NativeStop('native Jev failed; no retry/fallback') from None
    def validate_jev(self,result,request):
        body=result['body']; answers=body['answers']
        c.require(body.get('model')==self.config.jev_model and set(answers)==set(request['questions']),
                  'native Jev answer/model drift')
        for key,q in request['questions'].items():
            a=answers[key]
            if q['type']=='choice':
                p=a['probabilities']
                c.require(set(p)==set(q['criteria']) and a['choice'] in p,'native Choice shape drift')
                values=p.values()
            else: values=[a[q['type']]]
            c.require(all(type(v) in (int,float) and c.math.isfinite(v) and 0<=v<=1 for v in values),
                      'native typed decision shape drift')
        cost=body.get('usage',{}).get('cost')
        c.require(cost is not None,'native usage UNKNOWN')
        return {'accepted':True,'usage_cost':cost,'body':body}
    def actor(self,packet,*,cfg=None,request_projector=None):
        # Same public runner projection and documented _jev_judge result shape.
        try:
            runner=importlib.import_module('runner')
            body=runner.build_request({**packet,'model':self.config.jev_model},'state')
            if request_projector is not None: body=request_projector(body)
            from urllib.request import Request
            with self.http(Request(self.config.jev_url,data=json.dumps(body,ensure_ascii=False).encode(),method='POST')) as response:
                answer=json.load(response)
            usage=answer['usage']
            return {'answers':answer['answers'],'jev_model_requested':self.config.jev_model,
                    'jev_model_actual':answer['model'],'input_tokens':usage.get('input_tokens'),
                    'output_tokens':usage.get('output_tokens'),'cost_usd':usage['cost'],'usage_source':'provider-response'}
        except NativeStop: raise
        except BaseException: raise NativeStop('native actor STOP') from None
    def sdk(self,module,role,packet):
        try:
            c.require(role in ('extract','write','subject-name'),'unselected SDK role; before runtime STOP')
            request=module.build_request(role,packet,self.config.input_budget)
            candidates=[i for i in (self.config.permission_inventory if self.dynamic else self.config.request_inventory) if i['kind']=='sdk' and i['role']==role]
            binding=None
            if role=='subject-name':
                binding=naming_binding({'provider':'openai','model':'gpt-6-luna','role':role,
                    'inputBinding':request['inputBinding'],'sourceBinding':request['sourceBinding']})
                c.require(binding in self.config.naming_bindings,'unprovisioned naming input; before runtime STOP')
                candidates=[i for i in candidates if (naming_binding(i) if self.dynamic else naming_request_binding(i))==binding]
            if self.dynamic:
                candidates=[permission(i,self.config.jev_model) for i in candidates
                            if i.get('inputBinding')==request['inputBinding'] and i.get('sourceBinding')==request['sourceBinding']]
                c.require(bool(candidates),'unselected current SDK input/source; before runtime STOP')
                binding={'provider':'openai','model':'gpt-6-luna','role':role,
                         'inputBinding':request['inputBinding'],'sourceBinding':request['sourceBinding']}
                selected={}
            else:
                c.require(bool(candidates) and all(c.digest(i) in self.quotes
                          and self.quotes[c.digest(i)].expires>c.time.time() for i in candidates),
                          'unselected/unquoted SDK input; before runtime STOP')
                if binding is not None:
                    c.require(all(c.Decimal(self.quotes[c.digest(i)].max_cost).is_finite()
                                  and c.Decimal(self.quotes[c.digest(i)].max_cost)>0 for i in candidates),
                              'invalid naming hard quote; before runtime STOP')
                selected={c.digest(i):self.quotes[c.digest(i)] for i in candidates}
            def quote_for(final):
                if self.dynamic:
                    return self.final_quote(final,candidates,input_binding=request['inputBinding'],source_binding=request['sourceBinding'])
                quote=selected.get(c.digest(c.request_identity(final)))
                c.require(quote is not None,'actual wire absent from selected input quotes; before reserve STOP')
                return quote
            quota_payload={}
            if self.control is not None and self.control.sdk_quota is not None:
                quota_payload={'sdkProfile':self.config.sdk_profile,'runtimeSHA':self.config.sdk_runtime_sha,
                               'profileSHA':self.control.sdk_quota.profile_sha}
            result=self.bridge.exchange({'kind':'sdk','url':self.config.sdk_url,'request':request,'role':role,
                                         **quota_payload,**({'identityBinding':binding} if binding is not None else {})},
                                        None,None,self.wire,quote_for=quote_for,
                                        validate=lambda r:{'accepted':r.get('ok') is True,'usage_cost':r.get('cost'),**r})
            if module.__name__=='writer_worker':
                return module.parse_output(result['text'],role,packet['unit']['source_ranges'])
            return module.parse_output(result['text'],role)
        except NativeStop: raise
        except BaseException: raise NativeStop('native SDK failed; no retry/fallback') from None

class CurrentNativeServicesFactory:
    def __init__(self,*,issuer=None):
        self.issuer=issuer
    def fingerprint(self):
        home=Path(__file__).parent
        files={name:c.sha((home/name).read_bytes()) for name in
               ('native_services.py','native_bridge.py','native_bridge.mjs')}
        if self.issuer is not None:
            from real_bindings import QuoteIssuer
            c.require(type(self.issuer) is QuoteIssuer,'typed trusted quote issuer required')
            files['issuer']=self.issuer.fingerprint()
        return c.digest(files)
    def validate(self,control):
        cfg=control.native
        c.require(type(cfg) is NativeConfig,'typed native provisioning absent; before services STOP')
        c.require(cfg.jev_model and cfg.jev_url.startswith('https://') and cfg.sdk_url.startswith('https://')
                  and type(cfg.input_budget) is int and cfg.input_budget>1024,'native model/URL/budget admission absent')
        for path,sha in ((cfg.auth_module,cfg.auth_sha),(cfg.public_config,cfg.public_config_sha)):
            c.require(Path(path).is_absolute() and c.sha(Path(path).read_bytes())==sha,'native provision SHA drift')
        # Public config is a dedicated non-secret file, NEVER the user's knowledge.json.
        public=json.loads(Path(cfg.public_config).read_text())
        c.require(set(public)<= {'embed'} and set(public.get('embed',{}))<= {'provider','model_dir'},'private config is not a native control port')
        c.require(public.get('embed',{}).get('provider')=='openrouter','D10 cache-only remote model required')
        root=Path(cfg.cache_directory).resolve()
        c.require(root.is_dir() and bool(cfg.cache_manifest),'admitted warm-cache inventory absent')
        c.require({str(p.relative_to(root)) for p in root.glob('*.json')}=={r for r,_ in cfg.cache_manifest},
                  'unmanifested embedding cache STOP')
        for relative,sha in cfg.cache_manifest:
            path=(root/relative).resolve()
            c.require(path.is_relative_to(root) and path.is_file() and c.sha(path.read_bytes())==sha,'native cache inventory drift')
        c.require(Path(cfg.ledger_path).is_file(),'current carry ledger absent; no implicit new ledger')
        c.require('Luna' in dict(cfg.subscription_limits),'existing Luna carry account required')
        identities=cfg.request_inventory
        frontier=c.SELECTED_ADMISSION.get()
        if control.stage_grant is not None:
            from real_bindings import select_stages,selected_sdk_roles
            c.require(frontier is not None and frontier['control_sha']==c.digest(asdict(control)) and frontier['stages']==select_stages(control.stage_grant.stages),
                      'selected native inventory requires current verified entry')
            c.require(str(Path(cfg.ledger_path).resolve())==str(Path(control.stage_grant.ledger_path).resolve()),
                      'selected native ledger ownership drift')
            required=selected_sdk_roles(frontier['stages'])
            zero_inventory=frontier['stages']==('source',)
        else:
            required={'extract','write'}; zero_inventory=False
        dynamic=control.accounting_mode=='per-request'
        c.require(control.accounting_mode in ('whole','per-request'),'unknown native accounting mode')
        if dynamic:
            from real_bindings import QuoteIssuer
            c.require(type(self.issuer) is QuoteIssuer and self.issuer.fingerprint()==control.quote_issuer_sha
                      and bool(control.accounting_policy) and bool(control.issuer_receipt), 'native issuer provisioning absent')
            c.require(not identities and not control.quotes,'opt-in permissions must be separate from static final quotes')
            if control.sdk_quota is not None:
                p=control.sdk_quota;model=cfg.sdk_profile
                c.require(type(p) is c.SDKQuotaPolicy and type(model) is dict
                          and set(model)=={'provider','id','api','baseUrl','reasoning','contextWindow','maxTokens','cost'}
                          and model['provider']=='openai' and model['id']=='gpt-6-luna'
                          and model['api']=='openai-responses' and model['reasoning'] is True
                          and model['baseUrl']=='https://api.openai.com/v1'
                          and len(cfg.sdk_runtime_sha)==64
                          and p.profile_sha==c.digest({'runtime_sha':cfg.sdk_runtime_sha,'model':model})
                          and p.limits_sha==c.digest(dict(cfg.subscription_limits)), 'public SDK quota profile/limits drift')
            if control.embedding_policy is not None:
                c.require(type(control.embedding_policy) is c.EmbeddingPolicy
                          and cfg.embed_model==control.embedding_policy.model, 'embedding model/grant drift')
            c.require(type(cfg.permission_inventory) is tuple,'typed permission inventory required')
            identities=tuple(permission(i,cfg.jev_model) for i in cfg.permission_inventory)
            c.require((bool(identities) or zero_inventory) and len({c.digest(i) for i in identities})==len(identities),
                      'missing/duplicate static permission inventory')
        else:
            c.require(self.issuer is None and not cfg.permission_inventory and control.sdk_quota is None and control.embedding_policy is None,'whole mode cannot use dynamic permissions/issuer')
            c.require((bool(identities) or zero_inventory) and {c.digest(i) for i in identities}=={q.request_sha for q in control.quotes},
                      'native validated costproof inventory incomplete; before SDK/HTTP factory STOP')
        sdk_roles={i['role'] for i in identities if i['kind']=='sdk'}
        c.require(required<=sdk_roles<= {'extract','write','subject-name'},
                  'selected SDK roles required; only extract/write/subject-name admitted')
        c.require(type(cfg.naming_bindings) is tuple,'typed naming provisioning required')
        bindings=[naming_binding(row) for row in cfg.naming_bindings]
        c.require(all(set(row)==NAMING_KEYS for row in cfg.naming_bindings)
                  and len({c.digest(row) for row in bindings})==len(bindings),'malformed/duplicate naming provisioning')
        named=[i for i in identities if i['kind']=='sdk' and i['role']=='subject-name']
        c.require({c.digest((naming_binding(i) if dynamic else naming_request_binding(i))) for i in named}=={c.digest(row) for row in bindings},
                  'naming inventory/provision binding mismatch')
        for identity in (() if dynamic else named):
            quote=next(q for q in control.quotes if q.request_sha==c.digest(identity))
            c.require(quote.expires>c.time.time() and c.Decimal(quote.max_cost).is_finite()
                      and c.Decimal(quote.max_cost)>0,'naming hard quote expired/invalid')
        c.require(all(i['kind']=='embedding' or (i['kind'] in ('jev','sdk') and i['model']==('gpt-6-luna' if i['kind']=='sdk' else cfg.jev_model)
                      and i['provider']==('openai' if i['kind']=='sdk' else 'jev')) for i in identities),
                  'native model pin/inventory drift')
        c.require(not any(i['kind']=='embedding' for i in identities) or control.embedding_policy is not None,
                  'embedding permissions require separate grant')
    def build(self,admission,observed,trust,control,owned,deadline):
        # Called only after execute authority/cost/fingerprint gates, INSIDE owned job.
        from real_bindings import RealBindings,Services,WireBoundary
        from native_bridge import NodeBridge
        cfg=control.native
        self.validate(control)
        # No inherited API secret is consumed. Only this admitted non-secret config/cache.
        for key in tuple(os.environ):
            if key.startswith(('LH_','TYPESAFE_')): os.environ.pop(key,None)
        os.environ.update(LH_KNOWLEDGE_CONFIG=cfg.public_config,LH_EMBED_PROVIDER='openrouter',
                          LH_EMBED_CACHE_DIR=cfg.cache_directory,LH_EMBED_MODEL=cfg.embed_model)
        c.require(not any(k in sys.modules for k in ('embed','onnxruntime','tokenizers')),'preloaded unguarded embedding STOP')
        root, runner, scale = public_source_roots()
        sys.path[:0]=[str(scale),str(runner)]
        guard=ProcessGuard(); guard.install()
        safety=importlib.import_module('safety')
        ledger=safety.Ledger(cfg.ledger_path,admission.db_plan_sha,dict(cfg.caps),
                             subscription_limits=dict(cfg.subscription_limits),cash_limit=float(c.CARRY[4]))
        wire=WireBoundary(admission,observed,trust,NativeLedger(ledger),deadline,ledger_digest=safety.digest)
        bridge=NodeBridge(cfg,deadline,guard,control.evidence_directory)
        http=NativeHTTP(wire,control.quotes,bridge,cfg,control=control,issuer=self.issuer)
        aj=importlib.import_module('active_judgements')
        wt=importlib.import_module('worker_tools')
        ca=importlib.import_module('capture_audit')
        pw=importlib.import_module('place_write')
        dr=importlib.import_module('domain_router')
        embed=importlib.import_module('embed')
        c.require(embed.MODEL_ID==cfg.embed_model+'@openrouter','admitted embedding model drift')
        embed.configure_cache(cfg.cache_directory)
        # make_choice uses the public final-wire projection; force max_attempts=1.
        judge=ca.make_judge({'jev_model':cfg.jev_model,'jev_base_url':cfg.jev_url.removesuffix('/v1/systemone'),'jev_api_key':'IPC_HOST_AUTH_ONLY'},
                            http=aj.wire('selection',http.http),max_attempts=1,text_limit=None)
        conf={'jev_model':cfg.jev_model,'jev_base_url':cfg.jev_url.removesuffix('/v1/systemone'),'jev_api_key':'IPC_HOST_AUTH_ONLY'}
        def choice(kind,packet,options):
            question=CHOICE_QUESTIONS[kind] if kind in CHOICE_QUESTIONS else CHOICE_QUESTIONS['subject']
            if kind=='domain': question=pw.DOMAIN_CRITERION+question
            return judge(pw.model_view(packet),['unit'],question+'items[{i}]',options)[0]['probabilities']
        writer=importlib.import_module('writer_worker'); worker=importlib.import_module('active_worker')
        def unsupported(*args,**kw): raise NativeStop('unselected legacy/model path STOP')
        encoder=http.encode if control.embedding_policy is not None else embed.encode_queries
        ports=pw.Ports(unsupported,encoder,choice,
                       aj.make_ask(conf,'placement',http=http.http),None,
                       lambda stage,packet:http.sdk(writer,stage,packet),
                       lambda role,packet:http.sdk(worker,role,packet),
                       aj.make_ask(conf,'grounding',http=http.http))
        same=wt.make_ask(conf,http=http.http)
        services=Services(ports,aj.make_actor_judge(conf,judge=http.actor),dr.make_choose(conf,http=http.http),
                          lambda text,candidates:same({'facts':text},candidates,dr.SAME_Q),same,encoder,wire)
        return RealBindings.load(services)

# Verbatim existing place_write.production choice templates, not a new semantic policy.
CHOICE_QUESTIONS={
 'kind':('작성된 sentence의 종류를 options 고정 목록에서 정확히 하나 선택한다. Luna가 종류를 정하지 않는다. '
         '뜻: fact=대상의 동작·상태·구성 설명, decision=무엇을 하기로 정한 결정, rationale=결정의 이유, '
         'rejected=검토했지만 버린 대안, constraint=반드시 지키거나 하지 말아야 하는 제약(Must·Must not·금지·필수), '
         'procedure=순서가 있는 절차·단계, term=용어의 정의, question=아직 정해지지 않은 미해결 질문. '),
 'domain':('도메인은 여러 주어를 담는 업무 영역이다. '
           'unit의 대상 표현(주어가 될 대상)이 속한 업무 영역을 선택한다. 다른 영역은 문장 안 언급일 뿐이다. '
           '후보 설명과 unit 내용 전체를 비교한다. 맞는 후보가 없으면 none. '),
 'subject':('선택 domain 안에서 unit의 소유 엔티티(대상 표현)와 같은 대상인 subject를 고른다. '
            '이름이 달라도 별칭·번역·표기 차이로 같은 대상이면 같음. 관련 대상·부분·다른 기능은 같음 아님. 없으면 none. ')}
