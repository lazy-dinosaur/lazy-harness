"""Bounded one-unit caller. Import/dry run has no product imports, authority or effects.
External code capabilities and exact Trust receipts are required for execution.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import contextlib,hashlib,inspect,json,time

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'experiments/v2-native-minlive/unit1-controller-source-phase1'
ALIAS='pilot-area-10-unit1-current'  # protocol label; never permission
HOME=Path(__file__).resolve().parent/'fixtures'
SOURCE=HOME/'synthetic-source.md'
SOURCE_SHA=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
PLAN_SHA=hashlib.sha256(json.dumps({'scope':ALIAS,'paid_approved':False,'synthetic_only':True},sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
IMAGE='public.ecr.aws/supabase/postgres:17.6.1.134'
CARRY=('0.50','0.40','0.04','0.001','0.039','0.006',1,900)  # synthetic, not paid history

def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def capability_sha(fn):
    fn=inspect.unwrap(fn)
    path=inspect.getsourcefile(fn)
    if path is None:raise ValueError('inspectable external capability required')
    return hashlib.sha256((file_sha(path)+':'+fn.__qualname__).encode()).hexdigest()

@dataclass(frozen=True)
class TrialGrant:
    plan_sha: str
    source_sha: str
    code: tuple
    provisioner_sha: str
    resolver_sha: str
    seconds: float
    image_id: str
    max_anonymous_volumes: int
    expires: float
    receipt: str
    target: str = 'temporary-record'
    record_id: str = 'R05'
    extraction_index: int = 0
    sdk_roles: tuple = ('subject-name','write')
    sdk_calls: int = 2
    carry: tuple = CARRY
    preflight_sha: str = ''
    preflight_receipt: str = ''

@dataclass(frozen=True)
class StageBundle:
    admission: object
    observed: object
    control: object
    owned: object
    factory: object
    prior: object

class LocalResources:
    """Existing owned database context, no KEEP/probe/new image or key configuration."""
    @contextlib.contextmanager
    def __call__(self,plan,grant,clock):
        raise ValueError('SYNTHETIC profile: real provisioning is unavailable in this public fixture')


def run(public=None,*,execute=False,grant=None,trust=None,provisioner=None,resolver=None):
    """No CLI execute switch: trusted host code must supply actual typed capabilities."""
    if not execute:
        return {'status':'DRY_PLAN','effects':0,'target':'temporary-record','record_id':'R05','extraction_index':0,
                'requires':['external TrialGrant/Trust','current StageBundles','SDK cash0 quota evidence','hard embedding/Jev quotes','owned continuous lease'],
                'public':public if type(public) is dict else {}}
    import sys
    if str(BASE) not in sys.path:sys.path.insert(0,str(BASE))
    import controller as c,real_bindings as rb
    c.require(type(grant) is TrialGrant and type(trust) is c.Trust and callable(provisioner) and callable(resolver),'typed trial/capabilities required')
    c.require(grant.plan_sha==PLAN_SHA and grant.source_sha==SOURCE_SHA and grant.target=='temporary-record'
              and grant.record_id=='R05' and grant.extraction_index==0 and grant.sdk_roles==('subject-name','write')
              and grant.sdk_calls==2 and grant.carry==CARRY and 0<grant.seconds<900 and grant.expires>time.time()
              and type(grant.max_anonymous_volumes) is int and 0<=grant.max_anonymous_volumes<=8 and bool(grant.image_id), 'finite exact trial scope required')
    required={str((BASE/n).relative_to(ROOT)) for n in ('controller.py','real_bindings.py','native_services.py','native_bridge.py','native_bridge.mjs')}
    required.add(str(Path(__file__).resolve().relative_to(ROOT)))
    c.require(set(dict(grant.code))==required and len(grant.code)==len(required),'exact caller/native code inventory required')
    for relative,sha in grant.code:
        path=ROOT/relative
        c.require(path.resolve()==path and file_sha(path)==sha,'trial code/symlink drift')
    c.require(capability_sha(provisioner.__call__)==grant.provisioner_sha and capability_sha(resolver)==grant.resolver_sha,'trial capability fingerprint drift')
    trust.check('temporary-one-unit-trial',asdict(grant),grant.receipt)
    c.require(type(public) is dict and set(public)=={'sdk_profile_sha','pricing_policy_sha','history_sha','initial_cache_sha'}
              and all(type(v) is str and len(v)==64 for v in public.values())
              and c.digest(public)==grant.preflight_sha,'actual public preflight evidence inventory required')
    trust.check('one-unit-preparation-proof',{'grant':asdict(grant),'public':public},grant.preflight_receipt)
    c.require(HOME.resolve()==HOME and not HOME.is_symlink() and file_sha(SOURCE)==SOURCE_SHA,'source/home boundary drift')
    plan=json.loads((HOME/'plan.json').read_text())
    # Product plan digest has its existing spaced JSON convention, not controller.digest.
    digest=hashlib.sha256(json.dumps(plan,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
    c.require(digest==PLAN_SHA and plan['paid_approved'] is False and plan['scope']==ALIAS and plan.get('synthetic_only') is True,'protected prepared plan drift')
    clock={'started':time.time()};clock['ends']=clock['started']+grant.seconds
    previous=None;unit=None;entry=None
    # lease context guarantees cleanup after every resolver, quote, selected-stage or readback failure.
    for path in (HOME.parent,HOME.parent.parent):
        if str(path) not in sys.path:sys.path.insert(0,str(path))
    with provisioner(plan,grant,clock) as resource:
        c.require(getattr(resource,'fixture_only',False) is True,'synthetic fixture resource required; no live authority')
        for selected in (rb.STAGES[2:9],('review',),('record',)):
            c.require(time.time()<clock['ends'],'original caller deadline expired')
            bundle=resolver(selected,resource,previous,clock)
            c.require(type(bundle) is StageBundle,'current externally attested StageBundle required')
            a,o,control,owned=bundle.admission,bundle.observed,bundle.control,bundle.owned
            c.require(a.accounting_mode=='per-request' and a.db_plan_sha==PLAN_SHA
                      and a.provenance.source_sha==SOURCE_SHA and owned.extraction_index==0
                      and owned.record.get('record_id')=='R05' and owned.dsn==resource.dsn
                      and owned.host==resource.host and control.whole_seconds<=grant.seconds,'trial bundle scope drift')
            sg=control.stage_grant
            c.require(type(sg) is rb.StageGrant and sg.trial_started==clock['started'] and sg.trial_ends==clock['ends'], 'trial clock continuity required')
            c.require(control.sdk_quota is not None and control.embedding_policy is not None,'explicit SDK/embedding rights required')
            c.require(control.sdk_quota.profile_sha==public['sdk_profile_sha'] and a.accounting_policy==public['pricing_policy_sha'],
                      'preparation profile/accounting evidence changed')
            if previous is None:
                c.require(sg.ledger_sha==public['history_sha'] and c.digest(control.native.cache_manifest)==public['initial_cache_sha'],
                          'initial trial history/cache evidence changed')
            if selected==('record',) and not owned.subjects:
                c.require(bool(control.identity_install_receipt),'new subject requires genuine metadata materialization authority')
            if unit is not None:c.require(owned.unit_id==unit,'unit changed across stages')
            unit=owned.unit_id
            previous=c.execute_live(a,o,trust,control=control,owned=owned,factory=bundle.factory,stages=selected,prior=bundle.prior)
            # Returned data is NEVER converted into StagePrior or signed by this caller.
            if selected==('record',):entry=previous['values']['entry']
        readback=resource.readback(unit,entry)
        c.require(readback.get('state')=='proposed' and readback.get('unit')==unit,'actual temporary readback missing')
    return {'status':'TEMPORARY_RECORD_READBACK','synthetic_only':True,'unit':unit,'entry':entry,'readback':readback,
            'full135_complete':False,'publish_current':False,'trial_clock':clock,'cleanup':'lease context exited'}

if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False))
