"""G16 atomic local-only schema/data migration. Default is rollback (dry run).

No config/env DSN fallback, models, remote services or worker execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID, uuid5

import store_pg as pg

SQL = Path(__file__).with_name('migrations') / '0019_domain_subject.sql'
NAMESPACE = UUID('bfda0e69-340b-4c8f-a72b-214fbc0db919')


def rows(cur, sql, args=()):
    cur.execute(sql, args)
    names = [d[0] for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def hashes(cur):
    return {r['id']: hashlib.sha256(json.dumps([r['text'], r['form']], ensure_ascii=False,
            sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            for r in rows(cur, 'select id::text,text,form from knowledge.fragment order by id')}


def counts(cur, scoped):
    by_domain = rows(cur, """select f.host_id,f.domain,count(*) fragments,
        (select count(*) from knowledge.fragment_leaf l join knowledge.fragment p on p.id=l.fragment_id
         where p.host_id=f.host_id and p.domain=f.domain) leaves
        from knowledge.fragment f group by f.host_id,f.domain order by 1,2""")
    subjects = rows(cur, 'select host_id,' + ('domain' if scoped else "'<unscoped>'::text domain") +
                    ',count(*) subjects from knowledge.subject group by 1,2 order by 1,2')
    aliases = rows(cur, 'select host_id,' + ('domain' if scoped else "'<unscoped>'::text domain") +
                   ',count(*) aliases from knowledge.subject_alias group by 1,2 order by 1,2')
    return {'fragments_leaves': by_domain, 'subjects': subjects, 'aliases': aliases}


def plan(subjects, fragments, leaves):
    """Pure deterministic a–d assignment; names never imply an existing unrelated domain."""
    source = {s['subject_id']: s for s in subjects}
    reps, leaf_domains = {}, {}
    for f in fragments:
        if f['subject_id']:
            reps.setdefault(f['subject_id'], set()).add(f['domain'])
    for leaf in leaves:
        if leaf['subject_id']:
            leaf_domains.setdefault(leaf['subject_id'], set()).add(leaf['domain'])
    result = {}

    def assign(sid, trail=()):
        if sid in result:
            return result[sid]
        if sid in trail:
            raise ValueError('corrupt subject merge cycle: ' + str(trail))
        s = source[sid]
        if sid in reps:
            domains, rule = reps[sid], 'a'
        elif sid in leaf_domains:
            domains, rule = leaf_domains[sid], 'b'
        elif s['merged_into']:
            domains, _ = assign(s['merged_into'], trail + (sid,))
            rule = 'c'
        else:
            domains, rule = {'subject:' + s['name'].strip()}, 'd'
        result[sid] = (sorted(domains), rule)
        return result[sid]

    for sid in sorted(source):
        assign(sid)
    return result


def migrate(dsn, apply=False):
    parsed = urlparse(dsn)
    if parsed.scheme not in ('postgresql', 'postgres') or parsed.hostname not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError('only explicit loopback disposable PostgreSQL DSNs are allowed')
    conn = pg.driver.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute("select pg_advisory_xact_lock(hashtextextended('g16-migration',0))")
            cur.execute("select to_regclass('knowledge.g16_migration')")
            if cur.fetchone()[0]:
                cur.execute("select report from knowledge.g16_migration where version='0019'")
                prior = cur.fetchone()
                if prior:
                    return {'already_applied': True, 'report': prior[0]}
            cur.execute('lock table knowledge.subject,knowledge.subject_alias,knowledge.fragment,knowledge.fragment_leaf in access exclusive mode')
            before = counts(cur, False)
            before_hashes = hashes(cur)
            subjects = rows(cur, 'select subject_id::text,host_id,name,created_at,merged_into::text from knowledge.subject')
            aliases = rows(cur, 'select * from knowledge.subject_alias')
            fragments = rows(cur, 'select id::text,host_id,domain,subject_id::text from knowledge.fragment')
            leaves = rows(cur, '''select l.fragment_id::text,l.revision,l.ord,l.subject_id::text,f.host_id,f.domain
                from knowledge.fragment_leaf l join knowledge.fragment f on f.id=l.fragment_id''')
            assignments = plan(subjects, fragments, leaves)
            cur.execute(SQL.read_text())
            mapping, created = {}, []
            split_counts = {rule: {'subjects': 0, 'extra_rows': 0, 'assigned': 0} for rule in 'abcd'}
            for s in sorted(subjects, key=lambda s: s['subject_id']):
                sid = s['subject_id']
                domains, rule = assignments[sid]
                split_counts[rule]['assigned'] += 1
                split_counts[rule]['subjects'] += int(len(domains) > 1)
                split_counts[rule]['extra_rows'] += len(domains) - 1
                for i, domain in enumerate(domains):
                    cur.execute('''insert into knowledge.domain_type(host_id,domain,maintenance_pending)
                        values(%s,%s,true) on conflict do nothing returning domain''', (s['host_id'], domain))
                    if cur.fetchone():
                        created.append({'host_id': s['host_id'], 'domain': domain, 'rule': rule})
                    new = sid if i == 0 else str(uuid5(NAMESPACE, sid + '/' + domain))
                    mapping[sid, domain] = new
                    if i == 0:
                        cur.execute('update knowledge.subject set domain=%s where subject_id=%s', (domain, sid))
                    else:
                        cur.execute('''insert into knowledge.subject(subject_id,host_id,domain,name,created_at)
                            values(%s,%s,%s,%s,%s)''', (new, s['host_id'], domain, s['name'], s['created_at']))
                        cur.execute('''insert into knowledge.subject_embedding(subject_id,model_id,embedding,created_at)
                            select %s,model_id,embedding,created_at from knowledge.subject_embedding where subject_id=%s''', (new, sid))
                    cur.execute('insert into knowledge.g16_subject_map values(%s,%s,%s,%s)', (sid, domain, new, rule))
            for s in subjects:
                if s['merged_into']:
                    for domain in assignments[s['subject_id']][0]:
                        target = mapping[s['merged_into'], domain]
                        cur.execute('update knowledge.subject set merged_into=%s where subject_id=%s',
                                    (target, mapping[s['subject_id'], domain]))
            for a in aliases:
                sid = str(a['subject_id'])
                for i, domain in enumerate(assignments[sid][0]):
                    new = mapping[sid, domain]
                    if i == 0:
                        cur.execute('update knowledge.subject_alias set domain=%s where host_id=%s and alias=%s',
                                    (domain, a['host_id'], a['alias']))
                    else:
                        cur.execute('''insert into knowledge.subject_alias(host_id,domain,alias,subject_id,created_at,
                            kind,source_fragment_id,source_revision,merged_by) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                            (a['host_id'], domain, a['alias'], new, a['created_at'], a['kind'],
                             a['source_fragment_id'], a['source_revision'], a['merged_by']))
            for table, entries in [('fragment', fragments), ('fragment_leaf', leaves)]:
                for row in entries:
                    old = row['subject_id']
                    if not old:
                        continue
                    domains = assignments[old][0]
                    domain = row['domain'] if row['domain'] in domains else domains[0]
                    new = mapping[old, domain]
                    if old == new:
                        continue
                    key = {'id': row['id']} if table == 'fragment' else {k: row[k] for k in ('fragment_id','revision','ord')}
                    cur.execute('insert into knowledge.g16_move(tbl,row_key,host_id,old_subject,new_subject) values(%s,%s,%s,%s,%s)',
                                (table, json.dumps(key), row['host_id'], old, new))
                    where = ' and '.join(k + '=%s' for k in key)
                    cur.execute('update knowledge.' + table + ' set subject_id=%s where ' + where, (new, *key.values()))
            # Preserve legacy receipts; materialize their split-aware undo projection once.
            fragment_domains = {r['id']: r['domain'] for r in fragments}
            for item in rows(cur, '''select i.* from knowledge.subject_merge_item i
                    join knowledge.subject_merge m using(merge_id) where m.state='done' order by i.merge_id,i.seq'''):
                key, tbl = item['row_key'], item['tbl']
                old, new = str(item['old_subject']) if item['old_subject'] else None, str(item['new_subject'])
                if tbl in ('fragment', 'fragment_leaf'):
                    d = fragment_domains[key['id'] if tbl == 'fragment' else key['fragment_id']]
                    domains = [d if (new, d) in mapping else assignments[new][0][0]]
                else:
                    domains = assignments[new][0]
                for domain in domains:
                    mapped_key = dict(key)
                    if tbl == 'subject_alias':
                        mapped_key['domain'] = domain
                    elif tbl == 'subject':
                        mapped_key['subject_id'] = mapping[key['subject_id'], domain]
                    cur.execute('''insert into knowledge.g16_merge_item
                        (merge_id,seq,domain,tbl,row_key,old_subject,new_subject,guard)
                        values(%s,%s,%s,%s,%s,%s,%s,%s)''',
                        (item['merge_id'], item['seq'], domain, tbl, json.dumps(mapped_key),
                         mapping[old, domain] if old else None, mapping[new, domain], json.dumps(item['guard'])))
            cur.execute('set constraints all immediate')
            for table, constraints in {
                'subject': ['g16_subject_domain_fk', 'g16_subject_domain_required', 'g16_merge_domain_fk'],
                'subject_alias': ['g16_alias_domain_required', 'g16_alias_domain_fk'],
                'fragment': ['g16_fragment_subject_fk'],
            }.items():
                for constraint in constraints:
                    cur.execute('alter table knowledge.' + table + ' validate constraint ' + constraint)
            cur.execute('alter table knowledge.subject alter column domain set not null')
            cur.execute('alter table knowledge.subject_alias alter column domain set not null')
            cur.execute('''select count(*) from knowledge.fragment_leaf l join knowledge.fragment f on f.id=l.fragment_id
                join knowledge.subject s on s.subject_id=l.subject_id where s.host_id<>f.host_id''')
            assert cur.fetchone()[0] == 0, 'cross-host leaf'
            cur.execute('set constraints all immediate')
            after_hashes = hashes(cur)
            assert before_hashes == after_hashes, 'fragment text/form changed'
            report = {'before': before, 'after': counts(cur, True), 'splits': split_counts,
                      'created_domains': created, 'fragments_hashed': len(before_hashes), 'all_fragment_hashes_unchanged': True,
                      'hash_manifest_sha256': hashlib.sha256(json.dumps(before_hashes, sort_keys=True).encode()).hexdigest()}
            cur.execute("insert into knowledge.g16_migration(version,report) values('0019',%s)", (json.dumps(report),))
        if apply:
            conn.commit()
        else:
            conn.rollback()
        return {'applied': apply, 'report': report}
    finally:
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dsn', required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = migrate(args.dsn, args.apply)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    if args.report:
        args.report.write_text(rendered + '\n')
    print(rendered)
