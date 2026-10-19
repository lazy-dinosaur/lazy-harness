"""Explicitly ported public-call adapter, not a built-in admitted SDK/HTTP factory.
No product imports/config/auth/DSN discovery on import. Missing lowest-wire coverage
is a concrete STOP, never a fabricated successful transport receipt.
"""
from dataclasses import dataclass, asdict, field
import copy
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
import importlib
import inspect
import json
import os
from pathlib import Path
import signal
import tempfile
import threading
import time

import controller as c

# Verified exact public symbols. Loader injection is for AST-autospec tests only;
# production uses ordinary imports, never exec/eval/private product entry points.
PUBLIC = {
    'metadata': ('subject_contract', 'unit_first_metadata'),
    'extract': ('place_write', 'judge_input'),
    'place': ('place_write', 'place_identity'),
    'kind': ('place_write', 'fact_kind'),
    'validate': ('place_write', 'validate_fact'),
    'source': ('place_write', 'source'),
    'ground': ('source_grounding', 'check_many'),
    'citations': ('source_grounding', 'repair_citations'),
    'record_unit': ('place_write_absorb', 'record_unit'),
    'record': ('knowledge_cli', 'record'),
    'worktime': ('worktime_driver', 'run_worktime'),
    'complete': ('store_pg', 'complete'),
    'route': ('domain_router', 'route_pending'),
    'digest': ('digest_driver', 'run_digestion'),
}

@dataclass(frozen=True)
class OwnedMetadata:
    # Caller supplies already verified EXISTING resources. Never provisions anything.
    dsn: str = field(repr=False)
    host: str
    unit_id: str
    home: str
    record: dict
    domains: tuple
    subjects: tuple
    extraction_index: int
    plan_sha: str
    owner_receipt: str

    def manifest(self):
        return {**{k:v for k,v in asdict(self).items() if k!='dsn'}, 'dsn_sha':c.sha(self.dsn.encode())}

@dataclass(frozen=True)
class LiveControl:
    admission_sha: str
    owned_sha: str
    binding_sha: str
    factory_sha: str
    whole_seconds: float  # proposed 600 must come from FUTURE authority, not this source approval
    evidence_directory: str
    quotes: tuple
    transport_review: str
    execution_receipt: str
    native: object = None  # typed non-secret provisioning; absent means STOP
    stage_grant: object = None  # opt-in current Trust-verified range; legacy positional/default unchanged
    accounting_mode: str = 'whole'
    accounting_policy: str = ''
    quote_issuer_sha: str = ''
    issuer_receipt: str = ''
    sdk_quota: object = None  # controller.SDKQuotaPolicy; separate noncash authorization
    embedding_policy: object = None  # controller.EmbeddingPolicy; default native embed0
    identity_install_receipt: str = ''  # opt-in genuine one-unit metadata materialization before record

@dataclass(frozen=True)
class StageGrant:
    stages: tuple
    ledger_path: str
    ledger_sha: str
    trial_started: float
    trial_ends: float
    receipt: str

@dataclass(frozen=True)
class Services:
    ports: object
    judge: object
    choose: object
    confirm: object
    same: object
    embed_fn: object
    wire: object

@dataclass(frozen=True)
class PortedFactory:
    # Trusted code capability, never loaded from user/model JSON or a module-name string.
    # Signature build(admission, observed, trust, control, owned, deadline) -> RealBindings.
    build: object

    def fingerprint(self):
        c.require(callable(self.build), 'ported factory code required')
        path=inspect.getsourcefile(self.build)
        c.require(path is not None, 'uninspectable ported factory')
        return c.digest({'file_sha':c.sha(Path(path).read_bytes()), 'symbol':self.build.__qualname__})

@dataclass(frozen=True)
class QuoteIssuer:
    """External code capability only; constructing it grants no rights or receipt."""
    issue: object

    def fingerprint(self):
        c.require(callable(self.issue), 'callable quote issuer required')
        path=inspect.getsourcefile(self.issue)
        c.require(path is not None, 'inspectable issuer code required')
        return c.digest({'file_sha':c.sha(Path(path).read_bytes()),'symbol':self.issue.__qualname__})


def validate_accounting(admission,control,trust,issuer):
    c.require((control.accounting_mode,control.accounting_policy,control.quote_issuer_sha)==
              (admission.accounting_mode,admission.accounting_policy,admission.quote_issuer_sha),
              'admission/control accounting drift')
    if admission.accounting_mode=='whole':
        c.require(issuer is None and not control.issuer_receipt, 'whole mode cannot invoke an issuer')
        return
    c.require(admission.accounting_mode=='per-request' and type(issuer) is QuoteIssuer
              and issuer.fingerprint()==admission.quote_issuer_sha, 'current quote issuer mismatch')
    trust.check('quote-issuer',{'admission':asdict(admission),'control':asdict(control),
                              'issuer_sha':issuer.fingerprint()},control.issuer_receipt)


def public_value(value):
    """Lossless typed public-return projection, not arbitrary default=str receipts."""
    if value is None or type(value) in (str,int,bool,float): return value
    if isinstance(value,(datetime,date)): return {'type':type(value).__name__,'iso':value.isoformat()}
    if isinstance(value,(UUID,Decimal)): return {'type':type(value).__name__,'value':str(value)}
    if type(value) in (list,tuple): return [public_value(v) for v in value]
    if type(value) is dict and all(type(k) is str for k in value): return {k:public_value(v) for k,v in value.items()}
    raise c.Stop('unsupported public return type: '+type(value).__name__)


class RealBindings:
    def __init__(self, api, services, make_dsn):
        c.require(set(api)==set(PUBLIC) and all(callable(v) for v in api.values()), 'exact public bindings required')
        c.require(type(services) is Services and callable(make_dsn), 'typed services/public DSN builder required')
        self.api,self.services,self.make_dsn=api,services,make_dsn

    @classmethod
    def load(cls, services):
        # Caller invokes only INSIDE the owned job after all authority gates.
        api={key:getattr(importlib.import_module(module),symbol) for key,(module,symbol) in PUBLIC.items()}
        pg=importlib.import_module('store_pg')
        if pg.driver.__name__=='psycopg':
            make_dsn=importlib.import_module('psycopg.conninfo').make_conninfo
        else:
            c.require(pg.driver.__name__=='psycopg2', 'unsupported public DSN driver')
            make_dsn=importlib.import_module('psycopg2.extensions').make_dsn
        return cls(api,services,make_dsn)

    def materialize(self, admission, owned, deadline):
        state={}
        with self.api['metadata']():
            for stage in STAGES[:9]:
                self.stage(stage,state,admission,owned,deadline,None)
        c.require(c.digest(state['fact'])==admission.provenance.fact_sha, 'genuine reviewed fact hash drift')
        return state['fact']

    def stage(self, stage, state, admission, owned, deadline, dsn):
        api,s=self.api,self.services
        deadline.remaining()
        if stage=='source':
            text=api['source'](owned.record,Path(owned.home))
            c.require(type(text) is str and c.sha(text.encode())==admission.provenance.source_sha, 'current genuine source SHA drift')
            state['text']=text
        elif stage=='extract':
            c.require(callable(s.ports.worker), 'explicit worker role required; no legacy model fallback')
            items=api['extract'](s.ports,owned.record['record_id'],state['text'],origin=admission.provenance.source_kind,migration=False)
            c.require(type(items) is list and type(owned.extraction_index) is int and 0<=owned.extraction_index<len(items), 'explicit extraction index required')
            item=items[owned.extraction_index]
            c.require(type(item) is dict and not any(item.get(k) for k in ('judge_partial','range_invalid','target_ungrounded')), 'genuine extraction held')
            c.require(tuple(tuple(r) for r in item['source_ranges'])==admission.provenance.ranges, 'extraction/review ranges drift')
            state['unit']={**copy.deepcopy(item),'host_id':owned.host,'unit_id':owned.unit_id,
                           'source_text':'\n'.join('\n'.join(state['text'].splitlines()[a-1:b]) for a,b in item['source_ranges'])}
            state['placement']={}
        elif stage in ('place-domain','place-subject'):
            kind=stage.split('-')[1]
            placement=state.setdefault('placement',{})
            domain=placement.get('domain',{}).get('chosen')
            catalog=list(owned.domains) if kind=='domain' else [r for r in owned.subjects if r['domain']==domain['name']]
            placement[kind]=api['place'](kind,state['unit'],domain,catalog,s.ports,5,document=state['text'])
            c.require(placement[kind].get('chosen') and not placement[kind].get('held_reasons'), 'real placement held')
        elif stage=='write':
            c.require(callable(s.ports.writer), 'explicit writer role required; no legacy model fallback')
            packet={'source':state['text'],'unit':state['unit'],'chosen_domain':state['placement']['domain']['chosen'],'chosen_subject':state['placement']['subject']['chosen']}
            state['answer']=copy.deepcopy(s.ports.writer('write',packet))
            state['answer'].pop('kind',None)
        elif stage=='kind':
            state['answer']['kind']=api['kind'](s.ports,state['unit'],state['answer'])['choice']
        elif stage=='validate':
            state['fact']=api['validate'](owned.record,Path(owned.home),state['unit'],state['placement'],state['answer'])
        elif stage=='ground':
            checked=api['ground']([state['fact']],state['text'],s.ports.ground or s.ports.ask,check_identity=False)
            c.require(len(checked)==1 and not checked[0]['errors'], 'real Q1/Q2 held; no unapproved retry')
            state['checked']=checked[0]
        elif stage=='citations':
            api['citations'](state['fact'],state['checked'],state['text'])
        elif stage=='review':
            c.require(c.digest(state['fact'])==admission.provenance.fact_sha, 'genuine reviewed fact hash drift')
        elif stage=='record':
            fact=state['fact']
            identity={key:copy.deepcopy(fact.get(key)) for key in ('fact','subject','domain','aliases','evidence_refs','identity_ref','subject_id','source_unit')}
            def same_fact(index,candidate):
                return [] if index==0 and all(candidate.get(k)==v for k,v in identity.items()) else [{'code':'E_GROUNDING_DRIFT','where':'fact','detail':'reviewed materialization drift'}]
            def record(data,**kw):
                deadline.remaining()
                return api['record'](dsn,data,same=None,embed_fn=s.embed_fn,source_text='',**kw)
            result=api['record_unit'](owned.unit_id,fact,record,owned.host,same_fact)
            c.require(type(result) is dict and not result.get('errors') and not result.get('held_facts')
                      and result.get('work_unit_id')==owned.unit_id and result.get('state')=='proposed'
                      and result.get('recorded_indices')==[0] and bool(result.get('entry_id')), 'real record rejected/held')
            state['entry']=result['entry_id']
            return result
        elif stage=='worktime':
            result=api['worktime'](dsn,1,s.judge,entry_ids=[state['entry']],semantic_grounding=True)
            c.require(type(result) is dict and not result.get('failures') and len(result.get('results',[]))==1, 'real worktime failed')
            work=result['results'][0]
            c.require(work.get('entry_id')==state['entry'] and work.get('state')=='provisional'
                      and len(work.get('facts',[]))==1 and bool(work['facts'][0].get('receipt_id'))
                      and not work['facts'][0].get('errors'), 'worktime did not yield one provisional receipt')
            state['worktime_receipt']=work['facts'][0]['receipt_id']
            return result
        elif stage=='complete':
            result=api['complete'](dsn,owned.unit_id)
            c.require(type(result) is dict and result.get('work_unit_id')==owned.unit_id and result.get('host_id')==owned.host
                      and result.get('status')=='completed', 'real complete not completed')
            return result
        elif stage=='route':
            result=api['route'](dsn,owned.unit_id,s.choose,s.confirm,s.embed_fn)
            c.require(result==[(owned.host,state['fact']['domain'])], 'real router missing/drifted partition')
            return result
        elif stage=='digest':
            result=api['digest'](dsn,owned.unit_id,s.judge,domain=state['fact']['domain'],maintenance=None,workers=1,
                                 budget=1,same=s.same,embed_fn=s.embed_fn)
            c.require(type(result) is dict and result.get('status') in ('absorbed','processed')
                      and result.get('count')==1 and result.get('deferred',0)==0, 'real digest incomplete/held')
            return result
        return None

    def run(self, admission, observed, trust, control, owned, deadline, *, stages=None, prior=None):
        selected=select_stages(stages)
        packet=c.preflight(admission,observed,trust)
        validate_prior(selected,prior,admission,control,owned,trust)
        state=copy.deepcopy(prior.values) if prior else {}
        s,api=self.services,self.api
        dsn=None
        if any(stage in STAGES[10:] for stage in selected):
            dsn=self.make_dsn(owned.dsn,**deadline.db_options())
            c.require(type(dsn) is str and dsn and dsn!=owned.dsn, 'bounded connection DSN required')
        if STAGES.index(selected[0])>=11:
            actual=read_stage_state(dsn,owned,state)
            c.require(actual==prior.db, 'stale current DB prerequisite')
            validate_db(selected[0],actual,owned,state)
        rows=[]; result={}
        with api['metadata']():
            if control.identity_install_receipt:
                c.require(selected==('record',) and 'placement' in state and 'unit' in state,
                          'identity install requires genuine single record prerequisite')
                trust.check('one-unit-identity-install',{'control':asdict(control),'owned':owned.manifest(),
                            'fact':state['fact'],'placement':state['placement']},control.identity_install_receipt)
                safety=importlib.import_module('safety')
                plan=safety.load(Path(owned.home)/'state/plan.json')
                c.require(safety.digest(plan)==owned.plan_sha,'identity install state plan drift')
                install=importlib.import_module('place_write_absorb').install
                held=install(plan,Path(owned.home),dsn,owned.host,{'units':[{'unit_id':owned.unit_id,
                             'fact':state['fact'],'domain':state['placement']['domain'],
                             'subject':state['placement']['subject']}]},s.embed_fn)
                c.require(not held,'one-unit identity materialization held')
            for stage in selected:
                deadline.remaining()
                value=self.stage(stage,state,admission,owned,deadline,dsn)
                if stage=='review':
                    trust.check('fact-materialization',state['fact'],admission.provenance.lineage_receipt)
                if stage in STAGES[10:]:
                    result=value
                    core=c.CORE[{'record':1,'worktime':3,'complete':4,'route':5,'digest':6}[stage]]
                    projected=public_value(value)
                    row=c.CoreReceipt(core,owned.unit_id,state.get('entry'),state['fact']['domain'],observed.fact_sha,packet['admission_sha'],c.digest(projected),True)
                    rows.append({'core':asdict(row),'result':projected,'receipt_kind':'observed-public-return',
                                 'provenance':packet['provenance'],'control_sha':c.digest(asdict(control))})
        response={'status':'PUBLIC_CORE_RETURNED' if selected==STAGES else 'SELECTED_STAGES_RETURNED',
                  'receipts':rows,'full10':False,'publish_current':False,
                  'producer_precompute_maintenance_complete':False,'embedding_pending':result.get('embedding_pending') if type(result) is dict else None,
                  'physical_counts':dict(s.wire.counts),'sdk_completed':s.wire.sdk_completed,'semantic_quality_guaranteed':False}
        if selected!=STAGES: response.update(selected_stages=selected,values=public_value(state))
        return response

# Stage selection is control flow only; never execution/spend or accepted-state authority.
STAGES=('source','extract','place-domain','place-subject','write','kind','validate','ground','citations','review',
        'record','worktime','complete','route','digest')

@dataclass(frozen=True)
class StagePrior:
    context: dict
    values: dict
    db: dict | None
    receipt: str

def select_stages(stages=None):
    if stages is None: return STAGES
    c.require(type(stages) is tuple and bool(stages) and all(type(s) is str and s in STAGES for s in stages), 'stage whitelist/tuple required')
    start=STAGES.index(stages[0])
    c.require(stages==STAGES[start:start+len(stages)], 'stages must be unique contiguous forward range')
    return stages

def prior_context(admission,control,owned):
    return {'admission_sha':c.digest(asdict(admission)),'control_sha':c.digest(asdict(control)),
            'owned_sha':c.digest(owned.manifest()),'host':owned.host,'unit_id':owned.unit_id,
            'execution_receipt':control.execution_receipt,'source':asdict(admission.provenance)}

def validate_prior(selected,prior,admission,control,owned,trust):
    start=STAGES.index(selected[0])
    if start==0:
        c.require(prior is None, 'source start must not inject prior results')
        return
    c.require(type(prior) is StagePrior and type(prior.context) is dict and type(prior.values) is dict
              and (prior.db is None or type(prior.db) is dict), 'typed stage prerequisite required')
    c.require(prior.context==prior_context(admission,control,owned), 'foreign source/unit/host/execution prerequisite')
    # JSON-compatible, finite, code-reviewed binding. An artifact flag is not this receipt.
    c.digest(asdict(prior))
    trust.check('stage-prerequisite',{'context':prior.context,'values':prior.values,'db':prior.db},prior.receipt)
    v=prior.values
    required=(('text',),('text','unit'),('text','unit','placement'),('text','unit','placement'),
              ('text','unit','placement','answer'),('text','unit','placement','answer'),('text','fact'),
              ('text','fact','checked'),('fact',),('fact',),('fact','entry'),
              ('fact','entry','worktime_receipt'),('fact','entry','worktime_receipt'),('fact','entry','worktime_receipt'))[start-1]
    c.require(all(k in v for k in required), 'missing stage prerequisite')
    c.require(set(v)<=set(('text','unit','placement','answer','fact','checked','entry','worktime_receipt')), 'unknown prerequisite fields')
    if 'text' in v: c.require(type(v['text']) is str and c.sha(v['text'].encode())==admission.provenance.source_sha, 'prior source SHA drift')
    if 'unit' in v:
        u=v['unit']
        c.require(type(u) is dict and u.get('host_id')==owned.host and u.get('unit_id')==owned.unit_id
                  and u.get('source_ranges')==[list(r) for r in admission.provenance.ranges], 'prior extraction binding drift')
    if 'placement' in required:
        p=v['placement']
        c.require(type(p) is dict, 'prior placement shape')
        for kind in (('domain',) if start==3 else ('domain','subject')):
            c.require(type(p.get(kind)) is dict and type(p[kind].get('chosen')) is dict
                      and type(p[kind]['chosen'].get('name')) is str and not p[kind].get('held_reasons'), 'prior placement held/shape')
    if 'answer' in required: c.require(type(v['answer']) is dict and bool(v['answer']), 'prior writer shape')
    if 'checked' in required: c.require(type(v['checked']) is dict and v['checked'].get('errors')==[], 'prior Q1/Q2 held/shape')
    if 'fact' in v:
        f=v['fact']
        c.require(type(f) is dict and all(type(f.get(k)) is str and f[k] for k in ('fact','subject','domain'))
                  and (f.get('source_unit')==owned.unit_id or (type(f.get('source_unit')) is dict
                       and f['source_unit'].get('source_ranges')==[list(r) for r in admission.provenance.ranges]
                       and type(f['source_unit'].get('content')) is str
                       and type(f['source_unit'].get('target_expression')) is str)), 'prior fact shape/unit')
        if start>=9: c.require(c.digest(f)==admission.provenance.fact_sha, 'prior reviewed fact SHA drift')
    for key in ('entry','worktime_receipt'):
        if key in required: c.require(type(v[key]) is str and bool(v[key]), 'prior entry/receipt shape')
    if start>=10: trust.check('fact-materialization',v['fact'],admission.provenance.lineage_receipt)
    if start>=11:
        c.require(type(prior.db) is dict and set(prior.db)=={'unit','entry','receipts','parts','generation','entries'}
                  and all(type(prior.db[k]) is list for k in ('unit','entry','receipts','parts','entries'))
                  and (prior.db['generation'] is None or type(prior.db['generation']) is list), 'current DB prerequisite required')

def read_stage_state(dsn,owned,values):
    """Read-only snapshot under execute admission. Core still owns locks/CAS/writes.
    Never calls digest preview (which is not a general no-effects boundary).
    """
    pg=importlib.import_module('store_pg')
    with pg.connect(dsn) as conn,conn.cursor() as cur:
        cur.execute('set transaction read only')
        cur.execute('select host_id,status::text from knowledge.work_unit where work_unit_id=%s',(owned.unit_id,))
        unit=cur.fetchone()
        cur.execute('select host_id,work_unit_id::text,state::text,judgement_body from knowledge.ledger_entry where entry_id=%s',(values['entry'],))
        entry=cur.fetchone()
        cur.execute("select receipt_id::text,fact_index,combined::text from knowledge.check_receipt where entry_id=%s and stage='worktime' order by fact_index,receipt_id",(values['entry'],))
        receipts=cur.fetchall()
        cur.execute('select host_id,domain,fact_index from knowledge.digest_part where entry_id=%s order by fact_index',(values['entry'],))
        parts=cur.fetchall()
        cur.execute('select generation from knowledge.domain_type where host_id=%s and domain=%s',(owned.host,values['fact']['domain']))
        generation=cur.fetchone()
        # Whole unit must remain the admitted single-entry/single-fact unit; router is unit-scoped.
        cur.execute('select entry_id::text from knowledge.ledger_entry where work_unit_id=%s order by entry_id',(owned.unit_id,))
        entries=cur.fetchall()
    return public_value({'unit':unit,'entry':entry,'receipts':receipts,'parts':parts,'generation':generation,'entries':entries})

def validate_db(stage,db,owned,values):
    unit,entry=db.get('unit'),db.get('entry')
    expected={'worktime':('active','proposed'),'complete':('active','provisional'),
              'route':('completed','eligible'),'digest':('completed','eligible')}[stage]
    c.require(unit==[owned.host,expected[0]] and type(entry) is list and len(entry)==4
              and entry[:3]==[owned.host,owned.unit_id,expected[1]], 'current DB unit/host/entry/state drift')
    c.require(type(entry[3]) is dict and entry[3].get('facts')==[values['fact']]
              and db.get('entries')==[[values['entry']]], 'current DB reviewed fact/unit scope drift')
    if stage!='worktime':
        receipts=db.get('receipts')
        c.require(type(receipts) is list and len(receipts)==1 and type(receipts[0]) is list and len(receipts[0])==3 and receipts[0][0]==values['worktime_receipt']
                  and receipts[0][1]==0 and receipts[0][2] in ('record','update_record','deprecate_record'), 'current DB worktime receipt missing/held')
    if stage=='digest':
        c.require(db.get('parts')==[[owned.host,values['fact']['domain'],0]], 'current DB explicit domain/routing prerequisite')
        c.require(type(db.get('generation')) is list and len(db['generation'])==1 and type(db['generation'][0]) is int,
                  'current DB domain generation missing')

class WireBoundary(c.QuotedBoundary):
    """Only an explicit ported factory may install this at the final one-send seam.
    Contains real Ledger.call and count logic; does NOT claim stock factories use it.
    """
    def __init__(self,*args,**kw):
        super().__init__(*args,**kw)
        self.sdk_completed=0
    def attempt(self,request,quote,send):
        result=super().attempt(request,quote,send)
        if request.kind=='sdk': self.sdk_completed+=1
        return result

@dataclass(frozen=True)
class CleanupReceipt:
    pid: int
    pgid: int
    seconds: float
    timed_out: bool
    exit_code: int
    signal_sent: int | None
    uncertain: bool
    group_remaining: tuple


def run_owned_job(job,directory,deadline):
    """Fork a trusted code closure, NOT shell/model text. Entire job + descendants
    have an external wall bound. Leader remains unreaped until group cleanup, so
    its PID cannot be reused while signaling. No global kill, no reserve release.
    This does not shorten the product's internal Python900 timeout.
    """
    c.require(threading.active_count()==1 and hasattr(os,'fork') and hasattr(os,'WNOWAIT'), 'single-thread Linux owned executor required')
    directory=Path(directory)
    c.require(directory.is_dir(), 'caller-owned evidence directory required')
    home=Path(tempfile.mkdtemp(prefix='owned-unit1-job-',dir=directory))
    deadline.remaining()
    pid=os.fork()
    if pid==0:
        try:
            os.setsid()
            (home/'ready').write_text(str(os.getpid()))
            with (home/'stdout').open('wb') as out,(home/'stderr').open('wb') as err:
                os.dup2(out.fileno(),1); os.dup2(err.fileno(),2)
                try:
                    result=job()
                    (home/'result.json').write_text(json.dumps(result,allow_nan=False))
                except BaseException as exc:
                    (home/'error.json').write_text(json.dumps({'error_class':type(exc).__name__,'uncertain':True}))
                    os._exit(1)
            os._exit(0)
        except BaseException:
            os._exit(2)
    timed_out=False; sent=None; status=None
    try:
        while os.waitid(os.P_PID,pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is None:
            left=deadline.end-time.monotonic()-deadline.cleanup
            if left<=0:
                timed_out=True; break
            time.sleep(min(.01,left))
    finally:
        # Only this exact unreaped leader's newly created session/group can be killed.
        pgid=os.getpgid(pid)
        if pgid==pid:
            os.killpg(pid,signal.SIGKILL); sent=int(signal.SIGKILL)
        else:
            # Before setsid, kill only our direct child, never the inherited parent group.
            os.kill(pid,signal.SIGKILL); sent=int(signal.SIGKILL)
        _,status=os.waitpid(pid,0)
    remaining=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdigit(): continue
        try:
            row=(path/'stat').read_text().rsplit(')',1)[1].split()
            if int(row[2])==pid and int(row[3])==pid and row[0]!='Z': remaining.append(int(path.name))
        except (FileNotFoundError,ProcessLookupError): pass
    exit_code=os.waitstatus_to_exitcode(status)
    receipt=CleanupReceipt(pid,pid,time.monotonic()-deadline.started,timed_out,exit_code,sent,
                           timed_out or exit_code!=0 or bool(remaining),tuple(remaining))
    (home/'cleanup.json').write_text(json.dumps(asdict(receipt)))
    c.require(not receipt.uncertain and receipt.seconds<=deadline.end-deadline.started, 'owned real job uncertain/deadline STOP; retain reserve: '+str(home))
    result=json.loads((home/'result.json').read_text())
    return {**result,'owned_job':asdict(receipt),'evidence_path':str(home)}


def selected_sdk_roles(selected):
    roles=set()
    if 'extract' in selected: roles.add('extract')
    if 'write' in selected: roles.add('write')
    # Existing placement may name a subject; unsupported domain-name/reextract
    # remain denied by the unchanged native role boundary.
    if 'place-subject' in selected: roles.add('subject-name')
    return roles

def validate_stage_grant(admission,trust,control,owned,selected):
    g=control.stage_grant
    c.require(type(g) is StageGrant and type(trust) is c.Trust, 'typed selected-stage admission required')
    c.require(select_stages(g.stages)==selected, 'requested stages differ from current grant')
    c.require(type(owned) is OwnedMetadata and type(admission) is c.Admission, 'current grant context required')
    trust.check('selected-stage-admission',{'admission':asdict(admission),'control':asdict(control),
                'owned':owned.manifest()},g.receipt)
    now=time.time()
    c.require(all(type(v) in (int,float) and c.math.isfinite(v) for v in (g.trial_started,g.trial_ends))
              and g.trial_started<=now<g.trial_ends and 0<g.trial_ends-g.trial_started<900,
              'original whole-trial deadline expired/invalid')
    path=Path(g.ledger_path)
    c.require(path.is_absolute() and not path.is_symlink() and path.is_file(), 'same owned existing trial ledger required')
    raw=path.read_bytes()
    c.require(c.sha(raw)==g.ledger_sha, 'current trial ledger history drift/reset')
    rows=[json.loads(line) for line in raw.splitlines()]
    c.require(all(type(r) is dict and r.get('binding')==admission.db_plan_sha for r in rows), 'trial ledger binding drift')
    latest={}
    for row in rows:
        c.require(row.get('state') in ('reserved','done'), 'released/unknown trial history STOP')
        latest[row['id']]=row
    c.require(all(r['state']=='done' for r in latest.values()), 'pending trial history STOP; no release/reset')
    counts={'physical_post':0,'jev_http':0,'logical_q':0,'sdk_subscription':0,'embedding_post':0}
    embedding_cash=c.Decimal('0')
    if control.embedding_policy is not None:counts['embedding_inputs']=0
    for row in latest.values():
        req=row.get('request')
        c.require(type(req) is dict and req.get('kind') in (('sdk','jev','embedding') if control.embedding_policy is not None else ('sdk','jev')), 'unclassified trial history STOP')
        lane={'sdk':'sdk_subscription','jev':'jev_http','embedding':'embedding_post'}[req['kind']]
        q=req.get('logical_questions')
        c.require(type(q) is int and q>=0 and (req['kind']=='jev' or q==0), 'trial logical history drift')
        counts['physical_post']+=1; counts[lane]+=1; counts['logical_q']+=q
        if req['kind']=='embedding':
            n=req.get('input_count')
            c.require(type(n) is int and n>0 and req.get('sourceBinding')==control.embedding_policy.source_sha
                      and req.get('model')==control.embedding_policy.model and req.get('provider')=='openrouter'
                      and req.get('role') in ('query','passage'), 'embedding history scope drift')
            charge=c.Decimal(str(row.get('charge')))
            c.require(charge.is_finite() and charge>=0,'unknown embedding history charge')
            counts['embedding_inputs']+=n;embedding_cash+=charge
    c.require(counts['sdk_subscription']<=2 and counts['jev_http']<=9 and counts['logical_q']<=15, 'trial rights exhausted/drift')
    if control.embedding_policy is not None:
        e=control.embedding_policy
        c.require(type(e) is c.EmbeddingPolicy and counts['embedding_post']<=e.max_posts
                  and counts['embedding_inputs']<=e.max_inputs and embedding_cash<=c.Decimal(e.max_cash), 'embedding history limits exhausted')
    return {'admission_sha':c.digest(asdict(admission)), 'control_sha':c.digest(asdict(control)), 'future_fact':STAGES.index(selected[-1])<9,
            'stages':selected,'counts':counts,'embedding_cash':str(embedding_cash),'trial_ends':g.trial_ends}

def execute(admission,observed,trust,*,control,owned,factory,stages=None,prior=None):
    selected=select_stages(stages)
    frontier=None
    if type(control) is LiveControl and control.stage_grant is not None:
        frontier=validate_stage_grant(admission,trust,control,owned,selected)
    token=c.SELECTED_ADMISSION.set(frontier)
    try:
        return _execute_current(admission,observed,trust,control=control,owned=owned,factory=factory,stages=stages,prior=prior)
    finally:
        c.SELECTED_ADMISSION.reset(token)

def _execute_current(admission,observed,trust,*,control,owned,factory,stages=None,prior=None):
    selected=select_stages(stages)
    packet=c.preflight(admission,observed,trust)
    c.require(admission.controller_sha==c.sha(Path(c.__file__).read_bytes()), 'current on-disk CONTROLLER SHA drift')
    root=Path(__file__).resolve().parents[3]
    for relative,expected in admission.source_code:
        path=(root/relative).resolve()
        c.require(not Path(relative).is_absolute() and path.is_relative_to(root) and path.is_file()
                  and c.sha(path.read_bytes())==expected, 'current on-disk CODE SHA drift')
    c.require(type(control) is LiveControl and type(owned) is OwnedMetadata, 'current typed owner/plan/execution admission absent')
    c.require(control.admission_sha==packet['admission_sha'] and control.owned_sha==c.digest(owned.manifest())
              and owned.plan_sha==admission.db_plan_sha, 'owner/DSN/plan/control drift')
    c.require(control.binding_sha==c.sha(Path(__file__).read_bytes()), 'real binding code SHA drift')
    trust.check('current-owner',owned.manifest(),owned.owner_receipt)
    trust.check('live-execution',asdict(control),control.execution_receipt)
    frontier=c.SELECTED_ADMISSION.get()
    no_model=frontier is not None and selected==('source',)
    c.require((control.quotes or no_model or admission.accounting_mode=='per-request') and all(type(q) is c.Quote for q in control.quotes), 'current hard quote inventory UNKNOWN; POST STOP')
    for quote in control.quotes:
        amount=c.Decimal(quote.max_cost)
        c.require(amount.is_finite() and amount>0 and len(quote.request_sha)==64
                  and quote.inventory_sha==admission.inventory_sha and quote.ledger_binding==admission.db_plan_sha
                  and c.math.isfinite(quote.expires) and quote.expires>time.time(), 'current quote inventory/expiry drift')
        trust.check('quote',asdict(quote),quote.receipt)
    validate_prior(selected,prior,admission,control,owned,trust)
    from native_services import CurrentNativeServicesFactory
    if factory is None: factory=CurrentNativeServicesFactory()
    c.require(type(factory) in (PortedFactory,CurrentNativeServicesFactory), 'typed trusted factory required')
    c.require(factory.fingerprint()==control.factory_sha, 'ported factory code drift')
    validate_accounting(admission,control,trust,factory.issuer if type(factory) is CurrentNativeServicesFactory else None)
    trust.check('lowest-wire-factory',{'factory_sha':control.factory_sha,'control':asdict(control),
                'required':('final-request-digest-quote','reserve-before-each-physical-send','sdk-model-pin-no-server-retry',
                            'embedding-every-wire-no-hedge-retry','uncertain-hold-no-replay','source-provenance-binding')},control.transport_review)
    # No DB/models/factories before all gates above. No self-verified boolean grants authority.
    if type(factory) is CurrentNativeServicesFactory: factory.validate(control)
    seconds=control.whole_seconds
    if frontier is not None: seconds=min(seconds,frontier['trial_ends']-time.time())
    deadline=c.Deadline(seconds)
    def job():
        bindings=factory.build(admission,observed,trust,control,owned,deadline)
        c.require(type(bindings) is RealBindings, 'ported factory must bind actual public APIs')
        if frontier is not None:
            # Existing boundary caps and normal Ledger stay authoritative. Carry the
            # verified physical history into each newly constructed local boundary.
            wire=bindings.services.wire
            c.require(isinstance(wire,WireBoundary) and wire.admission==admission,
                      'selected admission requires actual guarded wire')
            c.require(str(Path(wire.ledger.path).resolve())==str(Path(control.stage_grant.ledger_path).resolve())
                      and wire.ledger.binding==admission.db_plan_sha
                      and c.sha(Path(wire.ledger.path).read_bytes())==control.stage_grant.ledger_sha,
                      'same owned ledger changed before selected job')
            wire.counts=dict(frontier['counts'])
            wire.sdk_completed=frontier['counts']['sdk_subscription']
            wire.embedding_spent=c.Decimal(frontier['embedding_cash'])
            wire.deadline=deadline
        return bindings.run(admission,observed,trust,control,owned,deadline,stages=selected,prior=prior)
    return run_owned_job(job,control.evidence_directory,deadline)
