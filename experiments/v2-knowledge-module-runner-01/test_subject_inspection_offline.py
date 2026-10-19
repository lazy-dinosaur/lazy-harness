"""Standalone P2a fakes; no pytest/conftest, DB, model, service or subprocess."""
import base64
import copy
import contextlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
import urllib.request
from unittest.mock import patch

OUT = Path(os.environ.get('TMPDIR', '/tmp')) / 'synthetic-subject-inspection'
BLOCKED = []
def forbidden(*args, **kwargs):
    BLOCKED.append('forbidden side effect')
    raise AssertionError('offline transport/process/model/config guard')

# Guards precede EVERY application import (including config/embed/store).
os.environ['LH_EMBED_PROVIDER'] = 'local'
os.environ['LH_KNOWLEDGE_CONFIG'] = str(OUT / 'synthetic-no-private-config.json')
for key in ('PGHOST','PGHOSTADDR','PGPORT','PGDATABASE','PGUSER','PGSERVICE','PGSERVICEFILE'):
    os.environ.pop(key, None)
socket.socket.connect = forbidden
socket.socket.connect_ex = forbidden
socket.create_connection = forbidden
socket.getaddrinfo = forbidden
subprocess.Popen = forbidden
subprocess.run = forbidden
urllib.request.urlopen = forbidden
try:
    import psycopg as driver
except ImportError:
    import psycopg2 as driver
driver.connect = forbidden
import config
DSN = 'postgresql://synthetic:synthetic@127.0.0.1:35432/synthetic'
CFG = dict(db_url=DSN, default_host='current', embed_provider='local')
config._file = forbidden
config.load = lambda: dict(CFG)
import embed
embed.encode_queries = embed.encode_documents = forbidden
import knowledge_cli as cli
import runtime_db
import subject_dict as sd
import subject_inspection as core
import write_contract as wc

CTX = runtime_db.bind_runtime_db(DSN, provenance='explicit-test')
def sid(i): return '00000000-0000-0000-0000-%012d' % i


def subject(i, host='current', domain='D', name=None, **kw):
    return dict(host_id=host, domain=domain, subject_id=sid(i), name=name or 'Object'+str(i),
                subject_type='기능', description='metadata', parent_subject_id=None,
                merged_into=None, **kw)


class FakeDB:
    """Explicit SQL interpreter: unknown SELECTs and ALL data writes are errors."""
    def __init__(self):
        self.subjects = [
            subject(1,name='Order'), subject(2), subject(3), subject(4),
            subject(5,domain='Other',name='Order'), subject(6,host='foreign',name='Secret'),
            subject(7,domain='Retired'), subject(8,name='Legacy')]
        self.subjects[1]['parent_subject_id'] = sid(1)
        self.subjects[2]['merged_into'] = sid(1)
        self.subjects[3]['subject_type'] = None
        self.subjects[3]['description'] = 'x'*400
        self.domains = {('current','D'):('active',None), ('current','Other'):('active',None),
                        ('foreign','D'):('active',None), ('current','Retired'):('retired','D')}
        self.aliases = [('current','D','order',sid(1),'spelling',False),
                        ('current','D','post /orders',sid(1),'declared',False),
                        ('current','D','old order',sid(3),'spelling',True),
                        ('current','Other','order',sid(5),'spelling',False),
                        ('foreign','D','secret',sid(6),'declared',False),
                        ('current','D','poison',sid(6),'declared',False)]
        self.calls = []; self.connections = 0
    def state(self): return copy.deepcopy((self.subjects,self.domains,self.aliases))
    def connect(self, dsn):
        assert dsn == DSN
        self.connections += 1
        return Connection(self)


class Connection:
    def __init__(self, db): self.db=db; self.readonly=False
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def cursor(self): return Cursor(self)


class Cursor:
    def __init__(self, conn): self.conn=conn; self.rows=[]
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def execute(self, sql, params=()):
        q=' '.join(sql.lower().split()); db=self.conn.db
        db.calls.append((q,params)); self.rows=[]
        if q == 'set transaction read only':
            assert not self.conn.readonly
            self.conn.readonly=True; return
        alias_sql = "select s.subject_id::text, s.name, case when a.merged_by is not null and a.kind = 'spelling' then 'merged' else a.kind end, s.subject_type, s.description from knowledge.subject_alias a join knowledge.subject s on s.subject_id=a.subject_id and s.host_id=a.host_id and s.domain=a.domain where a.host_id=%s and a.alias=%s and (%s or a.kind = 'spelling') and (%s::text is null or a.domain=%s)"
        if q == alias_sql:
            host,key,exact,domain,d2=params; assert domain == d2
            for ah,ad,alias,aid,kind,merged in db.aliases:
                for s in db.subjects:
                    if (s['subject_id']==aid and s['host_id']==ah and s['domain']==ad
                        and ah==host and alias==key and (exact or kind=='spelling') and (domain is None or ad==domain)):
                        self.rows.append((aid,s['name'],'merged' if merged and kind=='spelling' else kind,s['subject_type'],s['description']))
            return
        follow = 'select subject_id::text,name,domain,merged_into::text,subject_type,description,parent_subject_id::text from knowledge.subject where host_id=%s and subject_id=%s'
        if q == follow:
            self.rows=[tuple(s[k] for k in ('subject_id','name','domain','merged_into','subject_type','description','parent_subject_id')) for s in db.subjects if (s['host_id'],s['subject_id'])==params]
            return
        prefix=' '.join(core.SELECT.lower().split())
        suffixes = (' and s.name=%s order by s.subject_id limit 1',
                    ' and s.subject_id=%s::uuid limit 1',
                    ' and (%s::uuid is null or s.subject_id>%s::uuid) order by s.subject_id limit %s')
        if not q.startswith(prefix) or q[len(prefix):] not in suffixes:
            raise AssertionError('unknown/write SQL: '+q)
        assert self.conn.readonly, 'metadata must begin with READ ONLY'
        host,domain,d2,*rest=params; assert domain==d2
        rows=[s for s in db.subjects if s['host_id']==host and (domain is None or s['domain']==domain) and (host,s['domain']) in db.domains]
        suffix=q[len(prefix):]
        if suffix==suffixes[0]: rows=[s for s in rows if s['name']==rest[0]][:1]
        elif suffix==suffixes[1]: rows=[s for s in rows if s['subject_id']==rest[0]][:1]
        else:
            after,a2,limit=rest; assert after==a2 and 2<=limit<=101
            rows=sorted((s for s in rows if after is None or s['subject_id']>after),key=lambda s:s['subject_id'])[:limit]
        for s in rows:
            status,merged=db.domains[(host,s['domain'])]
            self.rows.append(tuple(s[k] for k in ('host_id','domain','subject_id','name','subject_type'))+
                             (s['description'][:300],s['parent_subject_id'],s['merged_into'],status,merged,len(s['description'])>300))
    def fetchall(self): return self.rows
    def fetchone(self): return self.rows[0] if self.rows else None


PARITY=[]
class SubjectInspectionTests(unittest.TestCase):
    def setUp(self):
        self.db=FakeDB(); self.before=self.db.state(); self.before_blocks=list(BLOCKED)
    def tearDown(self):
        self.assertEqual(self.db.state(),self.before, 'NO DB writes, including failures')
        self.assertEqual(BLOCKED,self.before_blocks, 'no attempted model/transport/config effects')
    def read(self, data): return core.inspect_subjects(self.db.connect,CTX,'current',data)
    def cli(self, data, *extra):
        out=io.StringIO()
        with patch.object(cli.store_pg,'connect',self.db.connect), patch.object(sys,'argv',['knowledge_cli.py','subject',*extra]), patch.object(sys,'stdin',io.StringIO(json.dumps(data))), contextlib.redirect_stdout(out):
            cli.main()
        return json.loads(out.getvalue())
    def test_list_metadata_and_bounds(self):
        out=self.read({'action':'list','domain':'D'})
        self.assertEqual(len(out['items']),5)
        self.assertEqual(out['items'][1]['parent_subject_id'],sid(1))
        self.assertIsNone(out['items'][3]['subject_type'])
        self.assertEqual(len(out['items'][3]['description']),300)
        self.assertTrue(out['items'][3]['description_truncated'])
        self.assertTrue(all(set(i)==set(core.FIELDS)|{'status'} for i in out['items']))
    def test_stable_paging(self):
        data={'action':'list','limit':2}; seen=[]
        while True:
            out=self.read(data); seen.extend(i['subject_id'] for i in out['items'])
            if out['next_cursor'] is None: break
            data={**data,'cursor':out['next_cursor']}
        self.assertEqual(seen,[sid(i) for i in (1,2,3,4,5,7,8)])
        self.assertEqual(self.read({'action':'list','limit':2}),self.read({'action':'list','limit':2}))
    def test_empty_and_end_page(self):
        self.assertEqual(self.read({'action':'list','domain':'absent'})['items'],[])
        self.assertEqual(self.read({'action':'list','cursor':core._cursor('current',None,sid(999))})['items'],[])
    def test_limit_validation(self):
        for limit in (0,-1,101,True,False,1.5,'2',None,10**50):
            with self.subTest(limit=limit),self.assertRaises(ValueError): self.read({'action':'list','limit':limit})
        self.assertEqual(self.db.connections,0)
        self.assertLessEqual(len(self.read({'action':'list','limit':100})['items']),100)
    def test_inspect_existing(self):
        out=self.read({'action':'inspect','subject_id':sid(1)})
        self.assertEqual(out['items'][0]['name'],'Order'); self.assertEqual(out['status'],'found')
    def test_foreign_id_is_identical_to_missing(self):
        self.assertEqual(self.read({'action':'inspect','subject_id':sid(6)}),self.read({'action':'inspect','subject_id':sid(999)}))
    def test_domain_id_fence(self):
        self.assertEqual(self.read({'action':'inspect','subject_id':sid(5),'domain':'D'})['status'],'not_found')
    def test_merged_not_followed(self):
        item=self.read({'action':'inspect','subject_id':sid(3)})['items'][0]
        self.assertEqual((item['subject_id'],item['merged_into'],item['status']),(sid(3),sid(1),'merged'))
    def test_retired_domain_is_visible_truthfully(self):
        item=self.read({'action':'inspect','subject_id':sid(7)})['items'][0]
        self.assertEqual((item['status'],item['domain_status'],item['domain_merged_into']),('retired','retired','D'))
    def test_lookup_name_and_normalized_spelling(self):
        for name in ('Order','  `ORDER`  '):
            self.assertEqual(self.read({'action':'lookup','domain':'D','name':name})['items'][0]['subject_id'],sid(1))
    def test_lookup_declared_alias(self):
        out=self.read({'action':'lookup','domain':'D','name':'POST /orders'})
        self.assertEqual((out['match_kind'],out['items'][0]['subject_id']),('declared',sid(1)))
    def test_lookup_does_not_strip_tail_or_search(self):
        for name in ('Order 화면','Order 기능','POST /orders 화면','Ord','unrelated'):
            self.assertEqual(self.read({'action':'lookup','domain':'D','name':name})['status'],'not_found')
    def test_lookup_domain_fence_and_poisoned_alias(self):
        self.assertEqual(self.read({'action':'lookup','domain':'Other','name':'Order'})['items'][0]['subject_id'],sid(5))
        for name in ('secret','poison'):
            self.assertEqual(self.read({'action':'lookup','domain':'D','name':name})['status'],'not_found')
    def test_lookup_merged_alias(self):
        out=self.read({'action':'lookup','domain':'D','name':'old order'})
        self.assertEqual((out['match_kind'],out['items'][0]['status']),('merged','merged'))
    def test_legacy_name_without_alias(self):
        out=self.read({'action':'lookup','domain':'D','name':'Legacy'})
        self.assertEqual((out['match_kind'],out['items'][0]['subject_id']),('name',sid(8)))
    def test_bad_ids_and_selectors(self):
        bad=[{'action':'inspect','subject_id':v} for v in (None,3,{},'bad',sid(1).upper()+'x')]
        bad += [{'action':'lookup','name':'Order'}, {'action':'lookup','domain':'D','name':'`"'}, {'action':'list','domain':None}, {'action':'list','domain':'x'*257}]
        for data in bad:
            with self.subTest(data=data),self.assertRaises(ValueError): self.read(data)
        self.assertEqual(self.db.connections,0)
    def test_unknown_mutation_and_authority_fail_closed(self):
        bad=[{'action':a} for a in ('create','rename','alias','merge','move','undo','undo_merge','delete','resolve',None,{},[])]
        bad += [{'action':'list',key:'forged'} for key in ('host_id','dsn','db_url','actor','state','authority','trusted_identity_refs','subject_id','name')]
        bad += [{'action':'inspect','subject_id':sid(1),'limit':1}, {'action':'lookup','name':'Order','domain':'D','cursor':'fake'}, [], None]
        for data in bad:
            with self.subTest(data=data),self.assertRaises(ValueError): self.read(data)
        self.assertEqual(self.db.calls,[])
    def test_cursor_scope_and_forgery(self):
        for token in ('bad', 'x'*4097, core._cursor('foreign',None,sid(1)),core._cursor('current','D',sid(1)),
                      base64.urlsafe_b64encode(b'{"host_id":"foreign"}').decode(), core._cursor('current',None,'bad')):
            with self.subTest(token=token[:25]),self.assertRaises(ValueError): self.read({'action':'list','cursor':token})
        self.assertEqual(self.db.connections,0)
    def test_caller_input_unchanged(self):
        for data in ({'action':'list','limit':2},{'action':'inspect','subject_id':sid(1)},{'action':'lookup','domain':'D','name':'Order'}):
            before=copy.deepcopy(data);self.read(data);self.cli(data);self.assertEqual(before,data)
    def test_cli_dispatch_parity_and_full_json(self):
        cases=[{'action':'list','domain':'D','limit':2}, {'action':'inspect','subject_id':sid(3)},
               {'action':'lookup','domain':'D','name':'POST /orders'}, {'action':'inspect','subject_id':sid(6)},
               {'action':'inspect','subject_id':sid(7)}]
        cases += [{'action':'list','cursor':self.read(cases[0])['next_cursor'],'domain':'D','limit':2}]
        for data in cases:
            expected=self.read(data); actual=self.cli(data); self.assertEqual(expected,actual)
            PARITY.append(dict(input=data,output=actual))
        for data in ({'action':'rename'},{'action':'list','host_id':'foreign'},{'action':'list','limit':101}):
            out=self.cli(data);self.assertFalse(out['ok']);PARITY.append(dict(input=data,output=out))
    def test_config_snapshot_and_cli_explicit_target(self):
        with patch.object(config,'require',wraps=config.require) as required:
            self.assertTrue(self.cli({'action':'list'},'--dsn',DSN)['ok'])
            self.assertEqual(required.call_args_list[0].args,('default_host',))
            self.assertEqual(required.call_count,1)
        with patch.object(config,'require',return_value={'db_url':DSN,'default_host':None}):
            self.assertFalse(self.cli({'action':'list'})['ok'])
    def test_runtime_ambient_reroute_fails_before_connector(self):
        with patch.dict(os.environ,{'PGHOST':'foreign.invalid'}),self.assertRaises(ValueError): self.read({'action':'list'})
        self.assertEqual(self.db.connections,0)
    def test_sql_failures_never_write_or_expose_driver_details(self):
        with patch.object(cli.store_pg,'connect',side_effect=RuntimeError('credential-secret')):
            out=io.StringIO()
            with patch.object(sys,'argv',['knowledge_cli.py','subject']),patch.object(sys,'stdin',io.StringIO('{"action":"list"}')),contextlib.redirect_stdout(out):cli.main()
            self.assertEqual(json.loads(out.getvalue()),{'ok':False,'error':'RuntimeError'})
    def test_existing_public_ids_and_provisional_contract(self):
        data={'host_id':'current','partition_key':'D','trusted_identity_refs':[{'forged':True}],
              'facts':[{'fact':'Order는 기록을 보존한다.','reason':'offline fixture','subject':'Order','subject_id':sid(1),'identity_ref':{'forged':True},'subject_provisional':{'status':'FINAL'}}]}
        before=copy.deepcopy(data);clean,errors=wc.public_input(data,'current')
        self.assertFalse(errors);self.assertFalse(wc.FACT_AUTHORITY & clean['facts'][0].keys());self.assertEqual(data,before)
        resolve=sd.resolver(self.db.connect,DSN,'current',domain='D')
        self.assertEqual(resolve('Order'),('Order','exact'));self.assertEqual(resolve.provisional['status'],'PROVISIONAL')
        self.assertEqual(resolve('POST /orders'),('POST /orders','declared_alias'))
        self.assertEqual(resolve('New object'),('New object','new_unchecked'))
        self.assertEqual(resolve.provisional['status'],'PROVISIONAL')
        # Legacy matching still strips generic tails; exact read API above explicitly does not.
        self.assertEqual(resolve('Order 화면'),('Order','alias'))


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SubjectInspectionTests))
    receipt=dict(ok=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                 skipped=len(result.skipped),elapsed_seconds=round(time.monotonic()-start,4),blocked_attempts=BLOCKED,
                 real_db=False,model_calls=0)
    (OUT/'focused-result.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (OUT/'adapter-parity-cases.json').write_text(json.dumps(PARITY,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(receipt));sys.exit(not result.wasSuccessful())
