#!/usr/bin/env python3
"""Read-only relocated runtime probe; prints counts/identity, never DSNs or corpus text."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def probe(host, vector=False, *, query=None):
    if not os.environ.get('LH_KNOWLEDGE_CONFIG'):
        raise ValueError('explicit config file required')
    if vector and (not isinstance(query, str) or not query.strip()):
        raise ValueError('vector probe requires an explicitly approved caller query')
    import config
    import store_pg
    import embed
    from runtime_db import bind_runtime_db
    cfg = config.require('db_url', 'default_host')
    if host != cfg['default_host'] or host.startswith('<'):
        raise ValueError('exact configured host required')
    db = bind_runtime_db(cfg['db_url'], provenance='explicit-diagnostic')
    if db.endpoint[0] in ('localhost', '127.0.0.1', '::1', 'unix'):
        raise ValueError('existing remote target required')
    db.assert_environment()
    with store_pg.connect(db.dsn) as conn, conn.cursor() as cur:
        cur.execute('set transaction read only')
        cur.execute('set local statement_timeout=15000')
        cur.execute('select exists(select 1 from knowledge.host where host_id=%s)', (host,))
        if not cur.fetchone()[0]:
            raise ValueError('host not registered')
        cur.execute('''select count(*), md5(coalesce(string_agg(id::text || ':' || revision::text,
                       ',' order by id), '')) from knowledge.fragment where host_id=%s and active''', (host,))
        count, fingerprint = cur.fetchone()
        cur.execute('''select confidence::text,count(*) from knowledge.fragment
                       where host_id=%s and active group by confidence''', (host,))
        confidence = dict(cur.fetchall())
        cur.execute('''select e.model_id,extensions.vector_dims(e.embedding),count(*)
                       from knowledge.fragment_embedding e join knowledge.fragment f on f.id=e.fragment_id
                       where f.host_id=%s and f.active and e.revision=f.revision
                       group by e.model_id,extensions.vector_dims(e.embedding)''', (host,))
        embeddings = [{'model': a, 'dimensions': b, 'currentRows': c} for a, b, c in cur.fetchall()]
    env = dict(os.environ, PGOPTIONS='-c default_transaction_read_only=on -c statement_timeout=15000')
    child = subprocess.run([sys.executable, str(Path(__file__).with_name('knowledge_cli.py')), 'domain'],
        input=json.dumps({'host_id': host, 'action': 'list'}), text=True, capture_output=True, env=env, timeout=40)
    result = json.loads(child.stdout)
    if child.returncode or 'domains' not in result or result.get('ok') is False:
        raise RuntimeError('public CLI readback failed')
    out = {'ok': True, 'host': host, 'activeFragments': count, 'revisionFingerprint': fingerprint,
           'confidenceCounts': confidence, 'embeddingModel': embed.MODEL_ID,
           'currentEmbeddings': embeddings, 'publicCliDomainReadback': True,
           'domains': len(result['domains']), 'claimVerificationCalls': 0,
           'sourceSnapshotsRequired': False, 'physicalSecondPC': False}
    if vector:
        # One ordinary configured query embedding, no passage generation/backfill or digestion.
        rows = store_pg.search(db.dsn, host, query, limit=3, mode='hybrid', expand=False)
        out['vectorQuery'] = {'hits': len(rows), 'modes': sorted({r.get('mode_used') for r in rows}),
                              'warnings': any(r.get('warning') for r in rows),
                              'vectorContribution': any(r.get('vector_rank') is not None for r in rows)}
        out['oracleAnswerVerified'] = False
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    parser.add_argument('--vector', action='store_true')
    parser.add_argument('--query', help='explicit query for a separately approved vector probe')
    args = parser.parse_args()
    try:
        result = probe(args.host, args.vector, query=args.query)
    except Exception as exc:
        result = {'ok': False, 'error': type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
