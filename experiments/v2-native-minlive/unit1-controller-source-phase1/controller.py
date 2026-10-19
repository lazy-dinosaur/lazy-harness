"""Local source-only controller. Importing this file creates no service or authority.
Live execution needs separately verified current owner/execution/transport admissions.
Synthetic tests remain distinct from the explicitly ported real public-call bindings.
"""
from dataclasses import dataclass, asdict
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
import uuid
from contextvars import ContextVar

# Installed only by the current externally verified selected-admission entry;
# never by checkpoint data or a caller's boolean. Forked owned jobs inherit it.
SELECTED_ADMISSION = ContextVar('selected_admission', default=None)

ALIAS = 'pilot-area-10-unit1-current'
CORE = ('subject_contract.unit_first_metadata', 'place_write_absorb.record_unit',
        'knowledge_cli.record', 'worktime_driver.run_worktime', 'store_pg.complete',
        'domain_router.route_pending', 'digest_driver.run_digestion')
# Synthetic carry profile only, not a historical balance or live budget allocation.
CARRY = ('0.50','0.40','0.04','0.001','0.039','0.006',1,900)

class Stop(RuntimeError): pass

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def sha(raw): return hashlib.sha256(raw).hexdigest()

def require(test, reason):
    if not test: raise Stop(reason)

@dataclass(frozen=True)
class Provenance:
    source_kind: str
    status: str
    asof: str
    asof_scope: str
    source_ref: str
    source_sha: str
    ranges: tuple
    review_receipt: str
    fact_sha: str
    audit_receipt: str
    lineage_receipt: str

@dataclass(frozen=True)
class Admission:
    alias: str
    source_code: tuple  # sorted (root-relative path, SHA) pairs, distinct from frozen DB plan
    controller_sha: str
    db_plan_sha: str
    provenance: Provenance
    core: tuple
    carry: tuple
    model_approval: str
    accounting_approval: str
    authority_receipt: str
    inventory_sha: str
    publish_current: bool = False
    accounting_mode: str = 'whole'
    accounting_policy: str = ''
    quote_issuer_sha: str = ''

@dataclass(frozen=True)
class Observed:
    source_code: tuple
    controller_sha: str
    db_plan_sha: str
    source_sha: str
    fact_sha: str
    inventory_sha: str

@dataclass(frozen=True)
class Trust:
    verify: object  # verify(purpose, digest, receipt) -> bool; external trusted control, not model

    def check(self, purpose, value, receipt):
        require(bool(receipt) and callable(self.verify) and self.verify(purpose,digest(value),receipt) is True,
                'unverified '+purpose)


def preflight(admission, observed, trust):
    require(type(admission) is Admission and type(observed) is Observed and type(trust) is Trust, 'typed admission required')
    a,p = admission,admission.provenance
    require(type(p) is Provenance, 'typed source metadata required')
    require(a.alias==ALIAS and a.core==CORE, 'fixed alias/supported core required')
    require(a.source_code==observed.source_code and bool(a.source_code) and len(dict(a.source_code))==len(a.source_code), 'current CODE SHA drift')
    require(a.controller_sha==observed.controller_sha and len(a.controller_sha)==64, 'CONTROLLER SHA drift')
    require(a.db_plan_sha==observed.db_plan_sha and len(a.db_plan_sha)==64, 'owned DB plan binding drift')
    require(a.carry==CARRY, 'existing cash/subscription carry drift')
    require(a.inventory_sha==observed.inventory_sha and len(a.inventory_sha)==64, 'embedding/wire inventory UNKNOWN')
    frontier=SELECTED_ADMISSION.get()
    defer_fact=frontier is not None and frontier['admission_sha']==digest(asdict(a)) and frontier['future_fact']
    require(p.source_sha==observed.source_sha and len(p.source_sha)==64, 'source SHA drift')
    if not defer_fact:
        require(p.fact_sha==observed.fact_sha and len(p.fact_sha)==64, 'source/fact SHA drift')
    else:
        require(p.fact_sha==observed.fact_sha and (not p.fact_sha or len(p.fact_sha)==64), 'future fact binding drift')
    require(all(type(v) is str and v.strip() for v in (p.source_kind,p.status,p.asof,p.source_ref)), 'missing source status/asof/kind/ref')
    require(p.asof_scope=='snapshot' and a.publish_current is False, 'upstream current-truth publication STOP')
    require(type(p.ranges) is tuple and bool(p.ranges) and all(type(r) is tuple and len(r)==2 and all(type(i) is int for i in r) and 1<=r[0]<=r[1] for r in p.ranges), 'exact source line ranges required')
    # Opaque caller-owned status is verified against audit, not classified from raw text.
    trust.check('source-review',asdict(p),p.review_receipt)
    trust.check('source-audit',asdict(p),p.audit_receipt)
    trust.check('artifact-lineage',asdict(p),p.lineage_receipt)
    trust.check('models',asdict(a),a.model_approval)
    trust.check('accounting',asdict(a),a.accounting_approval)
    trust.check('admission',asdict(a),a.authority_receipt)
    require(a.accounting_mode in ('whole','per-request'), 'unknown accounting mode')
    if a.accounting_mode=='whole':
        require(not a.accounting_policy and not a.quote_issuer_sha, 'whole mode must not carry opt-in authority')
    else:
        require(all(type(v) is str and len(v)==64 and all(ch in '0123456789abcdef' for ch in v)
                    for v in (a.accounting_policy,a.quote_issuer_sha)), 'explicit policy/issuer SHA required')
        trust.check('accounting-per-request',asdict(a),a.accounting_approval)
    return {'status':'PREFLIGHT_ONLY','admission_sha':digest(asdict(a)), 'provenance':asdict(p),
            'live_allowed':False,'semantic_quality_guaranteed':False,'core':CORE}


def execute_live(admission, observed=None, trust=None, *, control=None, owned=None, factory=None, stages=None, prior=None):
    # Lazy local import only. The real branch gates before imports/factories/DB/models.
    from real_bindings import execute
    return execute(admission, observed, trust, control=control, owned=owned, factory=factory, stages=stages, prior=prior)

@dataclass(frozen=True)
class Request:
    kind: str  # jev / sdk / embedding are separate accounting lanes, not business ontology
    provider: str
    model: str
    role: str
    body: bytes
    logical_questions: int = 0
    input_binding: str = ''  # optional non-secret naming metadata; legacy identity bytes unchanged
    source_binding: str = ''

@dataclass(frozen=True)
class Quote:
    request_sha: str
    inventory_sha: str
    ledger_binding: str
    max_cost: str
    expires: float
    receipt: str

@dataclass(frozen=True)
class SDKQuotaPolicy:
    profile_sha: str
    limits_sha: str
    call_seconds: float
    receipt: str

@dataclass(frozen=True)
class SubscriptionQuota:
    request_sha: str
    inventory_sha: str
    ledger_binding: str
    profile_sha: str
    limits_sha: str
    call_seconds: float
    expires: float
    receipt: str

@dataclass(frozen=True)
class EmbeddingPolicy:
    model: str
    source_sha: str
    max_posts: int
    max_inputs: int
    max_cash: str
    receipt: str



def request_identity(request):
    identity={'kind':request.kind,'provider':request.provider,'model':request.model,'role':request.role,
              'body_sha':sha(request.body),'logical_questions':request.logical_questions}
    if request.input_binding or request.source_binding:
        identity.update(inputBinding=request.input_binding,sourceBinding=request.source_binding)
    if request.kind=='embedding':
        try:body=json.loads(request.body)
        except (ValueError,UnicodeError):raise Stop('invalid embedding body encoding') from None
        require(type(body) is dict and set(body)=={'model','input'} and type(body['input']) is list and bool(body['input'])
                and all(type(t) is str and bool(t.strip()) for t in body['input']), 'embedding body shape')
        identity['input_count']=len(body['input'])
    return identity

class QuotedBoundary:
    """Reserve-before-one-physical-send primitive, NOT automatic transport wiring.
    A ported factory must install it at the actual lowest supported boundary. Its
    externally reviewed wiring is separate authority; a high-level callback is not
    proof of physical coverage. No retry/cache replay/fallback is permitted.
    """
    def __init__(self, admission, observed, trust, ledger, deadline, *, ledger_digest):
        self.packet=preflight(admission,observed,trust)
        self.admission,self.trust,self.ledger,self.deadline=admission,trust,ledger,deadline
        require(ledger.binding==admission.db_plan_sha and str(ledger.cash_limit)==CARRY[4], 'existing Ledger/cash seam mismatch')
        self.counts={'physical_post':0,'jev_http':0,'logical_q':0,'sdk_subscription':0,'embedding_post':0}
        require(callable(ledger_digest),'normal Ledger digest seam required')
        self.ledger_digest=ledger_digest
        self.stopped=False
        self.seen=set()
        self.lock=threading.Lock()
        self.sdk_quota=None
        self.embedding_policy=None
        self.embedding_spent=Decimal('0')
        self.control_sha=''

    def configure_resources(self,control):
        """Explicit externally verified opt-ins; never enabled by a model or cache miss."""
        sdk,emb=control.sdk_quota,control.embedding_policy
        require((sdk is None and emb is None) or self.admission.accounting_mode=='per-request', 'resource grants require per-request mode')
        context={'admission':asdict(self.admission),'control':asdict(control)}
        if sdk is not None:
            require(type(sdk) is SDKQuotaPolicy and len(sdk.profile_sha)==64
                    and sdk.limits_sha==digest(self.ledger.subscription_limits)
                    and math.isfinite(sdk.call_seconds) and 0<sdk.call_seconds<900, 'invalid SDK quota policy/limits')
            pool=self.ledger.subscription_limits.get('Luna',{})
            require(sdk.call_seconds==pool.get('per_call_seconds') and 0<pool.get('calls',0)<=6000
                    and 0<pool.get('seconds',0)<=28800, 'subscription quota pool mismatch')
            self.trust.check('sdk-subscription-cash0-policy',context,sdk.receipt)
        if emb is not None:
            require(type(emb) is EmbeddingPolicy and emb.model=='perplexity/pplx-embed-v1-0.6b'
                    and emb.source_sha==self.admission.provenance.source_sha
                    and type(emb.max_posts) is int and 0<emb.max_posts<=8
                    and type(emb.max_inputs) is int and 0<emb.max_inputs<=16
                    and Decimal(emb.max_cash).is_finite() and 0<Decimal(emb.max_cash)<=Decimal('.002048')
                    and 0<Decimal(str(self.ledger.caps.get('embedding',0)))<=Decimal(emb.max_cash), 'invalid embedding grant/cash subset')
            self.trust.check('native-embedding-policy',context,emb.receipt)
            self.counts.setdefault('embedding_inputs',0)
        self.sdk_quota,self.embedding_policy=sdk,emb
        self.control_sha=digest(asdict(control))

    def attempt(self, request, quote, send):
        with self.lock:
            require(not self.stopped,'first error/uncertain STOP')
            try:
                self.deadline.remaining()
                require(type(request) is Request and type(quote) in (Quote,SubscriptionQuota), 'typed quote/request required')
                identity=request_identity(request)
                key=digest(identity)
                require(key not in self.seen,'no retry or cached result injection')
                require(request.kind in ('jev','sdk','embedding') and all((request.provider,request.model,request.role,request.body)), 'transport identity required')
                require(type(request.logical_questions) is int and request.logical_questions>=0,'logical count invalid')
                require((request.kind=='jev') or request.logical_questions==0,'logical Q lane drift')
                require(quote.request_sha==key and quote.inventory_sha==self.admission.inventory_sha and quote.ledger_binding==self.ledger.binding,'quote/payload/provider/model/inventory/ledger drift')
                quota=type(quote) is SubscriptionQuota
                if quota:
                    policy=self.sdk_quota
                    require(request.kind=='sdk' and request.provider=='openai' and request.model=='gpt-6-luna' and request.role in ('extract','write','subject-name') and type(policy) is SDKQuotaPolicy
                            and quote.profile_sha==policy.profile_sha and quote.limits_sha==policy.limits_sha
                            and quote.call_seconds==policy.call_seconds, 'SDK quota grant/profile/limits mismatch')
                    require(math.isfinite(quote.expires) and quote.expires>time.time(),'SDK quota expired')
                    self.trust.check('sdk-subscription-quota',{'authorization':asdict(quote),'request':identity,
                                     'control_sha':self.control_sha},quote.receipt)
                    amount=Decimal('0')  # Stock subscription API: quota reservation, NOT a cash Quote.
                else:
                    require(not (request.kind=='sdk' and self.sdk_quota is not None),'cash quote cannot substitute for SDK quota')
                    amount=Decimal(quote.max_cost)
                    require(amount.is_finite() and amount>0 and math.isfinite(quote.expires) and quote.expires>time.time(),'quote UNKNOWN/expired')
                    self.trust.check('quote',asdict(quote),quote.receipt)
                emb=self.embedding_policy if request.kind=='embedding' else None
                if request.kind=='embedding':
                    require(type(emb) is EmbeddingPolicy and not quota and request.provider=='openrouter'
                            and request.model==emb.model and request.role in ('query','passage')
                            and request.source_binding==emb.source_sha
                            and self.counts['embedding_inputs']+identity['input_count']<=emb.max_inputs
                            and self.embedding_spent+amount<=Decimal(emb.max_cash),'embedding scope/input/cash cap STOP')
                limits={'jev':('jev_http',9),'sdk':('sdk_subscription',2),'embedding':('embedding_post',emb.max_posts if emb else 0)}
                counter,maximum=limits[request.kind]
                require(self.counts[counter]<maximum,'conditional small branch/inventory STOP')
                require(self.counts['logical_q']+request.logical_questions<=15,'logical Q branch STOP')
                step='generation' if request.kind=='sdk' else ('embedding' if request.kind=='embedding' else 'judging')
                require(not any(r.get('id')==self.ledger_digest([step,key]) for r in self.ledger.rows),'prior result/reservation: no injection/replay')
                self.seen.add(key)
                def effect():
                    self.deadline.remaining()
                    self.counts['physical_post']+=1
                    self.counts[counter]+=1
                    self.counts['logical_q']+=request.logical_questions
                    if emb is not None:
                        self.counts['embedding_inputs']+=identity['input_count']
                        self.embedding_spent+=amount
                    result=send(request)  # one lowest-boundary invocation; no retries here
                    self.deadline.remaining()
                    require(type(result) is dict and result.get('usage_cost') is not None and result.get('accepted') is True,'usage absent/error/fallback: reservation held')
                    actual=Decimal(str(result['usage_cost']))
                    require(actual.is_finite() and actual>=0 and (quota or actual<=amount),'uncertain/excess usage: reservation held')
                    if emb is not None:self.embedding_spent+=actual-amount
                    return {**result,
                            'accounting_basis':('subscription-quota' if quota else 'subscription-equivalent-bound' if request.kind=='sdk' else 'cash-quote'),
                            'equivalent_cost':str(actual) if request.kind=='sdk' else None,
                            'cash_charge':'0' if request.kind=='sdk' else str(actual),
                            'provenance':self.packet['provenance'],'admission_sha':self.packet['admission_sha'],'request_sha':key}
                # No new cash ledger. Subscription is separate from cash, original limit machinery retained.
                kwargs={'account':'subscription' if request.kind=='sdk' else 'cash','model':request.model,'request':identity}
                return self.ledger.call(step,key,float(amount),effect,
                                        cost=lambda r:float(Decimal(str(r['usage_cost']))),**kwargs)
            except BaseException:
                self.stopped=True
                raise

class SyntheticBoundary(QuotedBoundary):
    """Fixture-only use of the same reservation primitive; not live-wire evidence."""
    def __init__(self, *args, fixture=False, **kwargs):
        require(fixture is True, 'synthetic fixture capability required')
        super().__init__(*args, **kwargs)


@dataclass(frozen=True)
class CoreReceipt:
    stage: str
    unit_id: str
    entry_id: str
    domain: str
    fact_sha: str
    admission_sha: str
    receipt: str
    accepted: bool


def run_fixture_core(admission, observed, trust, fact, unit_id, ports, deadline, *, fixture=False):
    """Exact supported core ordering contract, synthetic ports only in Phase1.
    No fake install/completion receipt, direct SQL or producer/precompute/maintenance.
    A future live bridge must bind actual typed functions and normal trusted adapters;
    a dict of symbols or these synthetic green tests cannot admit such a bridge.
    """
    require(fixture is True,'no live core adapter admitted')
    packet=preflight(admission,observed,trust)
    require(type(fact) is dict and digest(fact)==observed.fact_sha,'typed fact binding drift')
    require(all(k in fact for k in ('fact','subject','domain','identity_ref','evidence_refs','source_unit')),'genuine fact/identity/source fields required')
    require(type(fact['identity_ref']) is dict and bool(fact['identity_ref']) and bool(fact['evidence_refs']),'trusted identity/evidence required')
    require(tuple(ports)==CORE and all(callable(v) for v in ports.values()),'supported core ports only')
    trust.check('fact-materialization',fact,admission.provenance.lineage_receipt)
    receipts=[]
    entry=None
    # unit_first_metadata owns the caller context; record_unit owns trusted fixed identity.
    with ports[CORE[0]]():
        for stage in CORE[1:]:
            deadline.remaining()
            args={'unit_id':unit_id,'fact':fact,'entry_id':entry,'domain':fact['domain'],
                  'provenance':packet['provenance'],'admission_sha':packet['admission_sha']}
            if stage==CORE[1]:
                args.update(record=ports[CORE[2]],fixed_subject=True,leaf_references=False,
                            trusted_identity_refs=[fact['identity_ref']])
            if stage==CORE[2]: continue  # invoked by record_unit, never a duplicate registration
            if stage==CORE[3]: args.update(window=1,entry_ids=[entry],semantic_grounding=True)
            if stage==CORE[6]: args.update(workers=1,budget=1,maintenance=None)
            row=ports[stage](**args)
            require(type(row) is CoreReceipt and row.stage==stage and row.unit_id==unit_id
                    and row.domain==fact['domain'] and row.fact_sha==observed.fact_sha
                    and row.admission_sha==packet['admission_sha'] and row.accepted is True
                    and bool(row.entry_id) and (entry is None or row.entry_id==entry),'core receipt/error/fallback STOP')
            trust.check('core-receipt',asdict(row),row.receipt)
            entry=row.entry_id
            receipts.append({'core':asdict(row),'provenance':packet['provenance']})
    return {'status':'SYNTHETIC_COMPONENT_ONLY','receipts':receipts,'full10':False,
            'publish_current':False,'producer_precompute_maintenance_complete':False}


class Deadline:
    def __init__(self, seconds, *, cleanup=.25):
        require(math.isfinite(seconds) and 0<cleanup<seconds<900,'finite whole deadline shorter than SDK900 required')
        self.started=time.monotonic()
        self.end=self.started+seconds
        self.cleanup=cleanup

    def remaining(self):
        left=self.end-time.monotonic()-self.cleanup
        require(left>0,'whole deadline STOP')
        return left

    def db_options(self):
        left=self.remaining()
        require(left>=1,'DB connect deadline cannot fit')
        ms=max(1,int(min(left,1)*1000))
        return {'connect_timeout':max(1,int(left)), 'options':f'-c lock_timeout={ms} -c statement_timeout={ms}'}


def run_owned_fixture(argv, directory, deadline, *, fixture=False):
    """Harmless fixture children ONLY. Finite group boundary; no arbitrary live runner.
    Linux /proc identity + private tag prevent signaling any foreign group. Captures
    real PID, wall clock and file streams; does not claim the SDK's Python timeout changed.
    """
    require(fixture is True and type(argv) is list and argv,'owned fixture only')
    directory=Path(directory)
    require(directory.is_dir() and directory.name.startswith('owned-'),'owned temp root required')
    token=uuid.uuid4().hex
    env={**os.environ,'UNIT1_FIXTURE_OWNER':token,'PYTHONDONTWRITEBYTECODE':'1'}
    deadline.remaining()
    with (directory/'stdout').open('wb') as out, (directory/'stderr').open('wb') as err:
        process=subprocess.Popen(argv,cwd=directory,env=env,stdout=out,stderr=err,start_new_session=True)
        pid=process.pid
        timed_out=False
        try:
            process.wait(timeout=deadline.remaining())
        except subprocess.TimeoutExpired:
            timed_out=True
        finally:
            members=[]
            for entry in Path('/proc').iterdir():
                if not entry.name.isdigit(): continue
                try:
                    stat=(entry/'stat').read_text().rsplit(')',1)[1].split()
                    if int(stat[2])!=pid or int(stat[3])!=pid or stat[0]=='Z': continue
                    tag=b'UNIT1_FIXTURE_OWNER='+token.encode()
                    require(tag in (entry/'environ').read_bytes().split(b'\0'),'foreign group member: cleanup STOP')
                    members.append(int(entry.name))
                except (FileNotFoundError,ProcessLookupError): pass
            if members:
                os.killpg(pid,signal.SIGKILL)
            process.wait(timeout=max(.001,deadline.end-time.monotonic()))
    result={'pid':pid,'pgid':pid,'owner':token,'exit_code':process.returncode,'timed_out':timed_out,
            'seconds':time.monotonic()-deadline.started,'cleanup_members':members}
    (directory/'receipt.json').write_text(json.dumps(result)+'\n')
    require(time.monotonic()<=deadline.end,'cleanup exceeded whole deadline')
    require(not timed_out and process.returncode==0,'owned child deadline/error STOP')
    return result
