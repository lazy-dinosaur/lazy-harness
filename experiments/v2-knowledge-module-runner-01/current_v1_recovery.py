"""Resumable full reference recovery. One locked job, durable role reservations.

Only old model-result groups are targets; old errors/classification stay separate.
All returned safe structured payloads remain private, including deferred claims.
"""
import argparse
from collections import Counter
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import time

import current_v1_register as reg
import current_v1_review as review

CAP = 4244
SEED = {"proposer": 4, "judge": 3}


def atomic(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        os.chmod(tmp, 0o600)
        json.dump(data, f, ensure_ascii=False, sort_keys=True)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


@contextmanager
def writer(directory):
    directory = Path(directory)
    if directory.is_symlink(): raise ValueError('symlink job')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(directory / 'writer.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try: yield
        finally: fcntl.flock(lock, fcntl.LOCK_UN)


def load(path):
    return json.loads(Path(path).read_text())


def full_context(receipt, receipt_hash, ingestion, bundle, host):
    auth = reg.bound_json(receipt, receipt_hash)
    if (auth.get('recoveryScope') != 'full-old-model-groups'
            or auth.get('roleCaps') != {'proposer': CAP, 'judge': CAP}
            or auth.get('seedUsage') != SEED):
        raise ValueError('full recovery scope/budget mismatch')
    pa = reg.bound_json(auth['pilotReceipt'], auth['pilotReceiptSha256'])
    if any(pa.get(k) != auth.get(k) for k in ('host', 'sourceRoot', 'sourceVersion', 'manifestSha256')):
        raise ValueError('mixed pilot scope')
    pilot_auth, pilot_selected = reg.context(auth['pilotReceipt'], auth['pilotReceiptSha256'], ingestion, bundle, host)
    pilot_results = Path(pa['reviewDirectory']) / 'results.jsonl'
    pilot_plan = reg.preview(pilot_auth, pilot_selected, pilot_results, auth['pilotResultsSha256'], auth['pilotReceiptSha256'])
    calls = list(review.read_jsonl(Path(pa['reviewDirectory']) / 'calls.jsonl'))
    if dict(Counter(x['role'] for x in calls)) != SEED:
        raise ValueError('pilot charge mismatch')
    old = Path(auth['oldResults'])
    if reg.digest(old) != auth['oldResultsSha256']:
        raise ValueError('old review changed')
    rows = list(review.read_jsonl(old))
    target_ids = [r['groupId'] for r in rows]
    if len(target_ids) != len(set(target_ids)) or set(target_ids) != set(auth['groupIds']):
        raise ValueError('old target inventory mismatch')
    auth, selected = reg.context(receipt, receipt_hash, ingestion, bundle, host)
    for row in rows:
        gid = row['groupId']; g, span = selected[gid]
        p = row.get('sourceProof', {})
        # Legacy paid rows bound only path/range/span hash. Their separately trusted
        # immutable file hash plus current manifest/group identity supplies context;
        # never pretend that these rows already held full generated payload proof.
        expected = {k: span[k] for k in ('sourcePath', 'lineStart', 'lineEnd', 'sourceQuoteHash')}
        # Original review retained the structural end (including trailing blank
        # lines); current payload proof reports the actual hashed span end.
        expected['lineEnd'] = g['sample'].get('lineEnd', expected['lineEnd'])
        if (p != expected or row.get('sourceVersion') != auth['sourceVersion']
                or row.get('candidateIds') != g['candidateIds']
                or row.get('sourceInputIDs') != g['sourceInputIDs']):
            raise ValueError('old source proof mismatch')
    if not set(pilot_selected) <= set(selected):
        raise ValueError('pilot outside full target')
    return auth, selected, pilot_plan, set(pilot_selected)


def reserve(directory, gid, role, counts):
    if role not in SEED or counts[role] >= CAP:
        raise ValueError('role cap exhausted')
    path = directory / (role + '-reservation.json')
    if path.exists(): raise ValueError('paid reservation replay forbidden')
    atomic(path, {'groupId': gid, 'role': role, 'state': 'reserved', 'charged': True,
                  'started': time.time(), 'billing': 'unknown', 'rawOutputStored': False})
    counts[role] += 1


def safe_proposals(data):
    # Malformed/private inputs never persist unsafe provider strings. Safe incomplete
    # structured fields are retained separately from verifier-eligible payloads.
    out = []
    for index, candidate in enumerate(data):
        item = {'proposalIndex': index}
        if isinstance(candidate, dict):
            for key, bound in [('claim', 4000), ('source_quote', 8000), ('facet', 20), ('relation', 120)]:
                if review.safe_payload_text(candidate.get(key), bound): item[key] = candidate[key]
        item['storage'] = 'safe-structured-fields-only'
        out.append(item)
    return out


def recover_group(auth, gid, group, span, directory, counts, proposer, judge):
    directory.mkdir(exist_ok=True, mode=0o700)
    result_path = directory / 'results.jsonl'
    if result_path.exists(): return load(result_path)
    start = time.time()
    base = {'groupId': gid, 'candidateIds': group['candidateIds'], 'sourceInputIDs': group['sourceInputIDs'],
            'classification': group['classification'], 'sourceVersion': auth['sourceVersion'],
            'sourceProof': reg.proof(auth, gid, group, span, directory.name), 'truthPromotion': 'none'}
    proposed_path = directory / 'proposed.json'
    durations = {}
    try:
        if not proposed_path.exists():
            if (directory / 'proposer-reservation.json').exists():
                raise RuntimeError('ambiguous_proposer_reservation')
            reserve(directory, gid, 'proposer', counts)
            packet = {'sourceVersion': auth['sourceVersion'], 'groupId': gid, 'sourcePath': span['sourcePath'],
                      'lineStart': span['lineStart'], 'lineEnd': span['lineEnd'], 'span': span['text'],
                      'guard': {'manifestSha256': auth['manifestSha256'], 'sourceRoot': auth['sourceRoot'],
                                'sourceDocFP': group['sourceDocFP']}}
            t = time.time()
            reply, meta = review.normalize_reply(proposer(packet))
            durations['proposerSeconds'] = time.time() - t
            if not reply or len(reply) > review.MAX_PROPOSER_OUTPUT_CHARS: raise ValueError('invalid_proposer_output')
            data = json.loads(reply)
            if not isinstance(data, dict) or set(data) != {'candidates'} or not isinstance(data['candidates'], list) or len(data['candidates']) > 16:
                raise ValueError('invalid_proposer_schema')
            atomic(proposed_path, {'candidates': safe_proposals(data['candidates']), 'durations': durations,
                                   'profile': meta.get('profile', 'configured-brief-default'),
                                   'rawOutputStored': False})
        proposed = load(proposed_path)
        durations.update(proposed['durations'])
        def durable_judge(*args, **kwargs):
            answer_path = directory / 'judge-return.json'
            if answer_path.exists():
                returned = load(answer_path)
                durations.update(returned['durations'])
                return returned['answers']
            if (directory / 'judge-reservation.json').exists(): raise RuntimeError('ambiguous_judge_reservation')
            reserve(directory, gid, 'judge', counts)
            t = time.time()
            answers = judge(*args, **kwargs)
            durations['judgeSeconds'] = time.time() - t
            cleaned = [{'choice': a.get('choice') if a.get('choice') in review.VERIFY_C else 'uncertain',
                        'probabilities': {k: v for k,v in (a.get('probabilities') or {}).items()
                                          if k in review.VERIFY_C and isinstance(v, (float,int))}}
                       for a in answers]
            atomic(answer_path, {'answers': cleaned, 'durations': durations})
            return cleaned
        verified = review.verify_candidates(proposed['candidates'], span['text'], durable_judge)
        for c in verified:
            if c.get('claimHash') and c.get('quoteHash'):
                c['claimFP'] = review.stable_id('claim', auth['sourceRoot'], auth['sourceVersion'], gid, c['claimHash'], c['quoteHash'])
        row = {**base, 'status': 'reviewed', 'verifiedCandidates': verified,
               'model': {'proposer': proposed['profile'], 'judge': 'configured-typed-jev'}}
    except Exception as exc:
        # Reservation remains consumed even for timeout/unknown transport outcomes.
        row = {**base, 'status': 'deferred', 'reason': 'paid_outcome_unknown_or_invalid',
               'errorClass': type(exc).__name__, 'verifiedCandidates': [],
               'proposedPayloadRetained': proposed_path.exists()}
    row['timing'] = {**durations, 'groupSeconds': time.time() - start}
    atomic(result_path, row)
    return row


def group_plan(auth, selected, job, receipt_hash):
    fragments, excluded, seen = [], Counter(), set()
    for gid, pair in selected.items():
        path = job / gid / 'results.jsonl'
        if not path.exists(): continue
        plan = reg.preview(auth, {gid: pair}, path, reg.digest(path), receipt_hash)
        excluded.update(plan['summary']['excluded'])
        for f in plan['fragments']:
            if f['id'] not in seen: fragments.append(f); seen.add(f['id'])
    return {'host': auth['host'], 'sourceRoot': auth['sourceRoot'], 'fragments': fragments,
            'summary': {'eligibleClaims': len(fragments), 'excluded': dict(excluded)}}


def run(auth, selected, pilot_ids, receipt_hash, *, proposer=None, judge=None, checkpoint=None):
    job = Path(auth['reviewDirectory'])
    with writer(job):
        if auth.get('roleCaps') != {'proposer': CAP, 'judge': CAP}:
            raise ValueError('fixed cumulative caps required')
        scope = {'receiptSha256': receipt_hash, 'roleCaps': auth['roleCaps'], 'seedUsage': SEED,
                 'selected': sorted(selected), 'pilot': sorted(pilot_ids)}
        if (job / 'scope.json').exists():
            if load(job / 'scope.json') != scope: raise ValueError('job scope changed')
        else: atomic(job / 'scope.json', scope)
        counts = Counter(SEED)
        targets = {k:v for k,v in selected.items() if k not in pilot_ids}
        for gid in targets:
            for role in SEED:
                p = job / gid / (role + '-reservation.json')
                if p.exists():
                    reservation = load(p)
                    if reservation.get('groupId') != gid or reservation.get('role') != role or reservation.get('charged') is not True:
                        raise ValueError('reservation corrupt')
                    counts[role] += 1
        if any(counts[r] > CAP for r in SEED): raise ValueError('cumulative budget exceeded')
        start_path = job / 'started.json'
        if not start_path.exists(): atomic(start_path, {'started': time.time()})
        started = load(start_path)['started']
        proposer = proposer or review.default_proposer
        judge = judge or review.make_judge_from_config()
        completed = []
        def progress(terminal=False):
            rows = [load(job / g / 'results.jsonl') for g in targets if (job / g / 'results.jsonl').exists()]
            elapsed = time.time() - started
            result = {'state': 'terminal' if terminal else 'running', 'targetGroups': len(selected),
                      'alreadyRestored': len(pilot_ids), 'newTerminalGroups': len(rows),
                      'remainingGroups': len(targets)-len(rows), 'recoveryUsed': dict(counts),
                      'newCalls': {r: counts[r]-SEED[r] for r in SEED}, 'wallSeconds': elapsed,
                      'outcomes': dict(Counter(row['status'] for row in rows)), 'totalBilling': 'unknown',
                      'progressPath': str(job / 'progress.json')}
            atomic(job / 'progress.json', result)
            return result
        # Replay DB checkpoints first; no paid calls and stable per-group provenance.
        if checkpoint: checkpoint(group_plan(auth, targets, job, receipt_hash))
        for gid, (group, span) in targets.items():
            if (job / gid / 'results.jsonl').exists(): continue
            if counts['proposer'] >= CAP and not (job / gid / 'proposer-reservation.json').exists(): break
            recover_group(auth, gid, group, span, job / gid, counts, proposer, judge)
            completed.append(gid)
            status = progress()
            n = status['newTerminalGroups']
            if n == 20 and not (job / 'first20.json').exists():
                rows = [load(job / g / 'results.jsonl') for g in targets if (job / g / 'results.jsonl').exists()]
                times = [r['timing']['groupSeconds'] for r in rows]
                rate = 20 / sum(times) if sum(times) else 0
                atomic(job / 'first20.json', {**status, 'measuredGroups': 20, 'groupDurations': times,
                       'callDurations': [r['timing'] for r in rows], 'groupsPerSecond': rate,
                       'remainingSecondsRange': [min(times)*status['remainingGroups'], max(times)*status['remainingGroups']],
                       'estimatedRemainingSeconds': status['remainingGroups']/rate if rate else None,
                       'etaQualification': 'observed first20 incl errors; excludes variable DB/embed latency'})
                print(json.dumps({'event': 'first20', 'artifact': str(job/'first20.json'), 'groupsPerSecond': rate}), flush=True)
            if n == 20 or len(completed) >= 250:
                if checkpoint: checkpoint(group_plan(auth, targets, job, receipt_hash))
                completed.clear()
                print(json.dumps({'event': 'checkpoint', **progress()}), flush=True)
        if checkpoint: checkpoint(group_plan(auth, targets, job, receipt_hash))
        return progress(terminal=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['validate', 'run'])
    for key in ('receipt', 'receipt-sha256', 'ingestion', 'bundle', 'host'): p.add_argument('--'+key, required=True)
    args = p.parse_args(argv)
    try:
        auth, selected, pilot, pilot_ids = full_context(args.receipt, args.receipt_sha256, args.ingestion, args.bundle, args.host)
        if args.command == 'validate':
            result = {'targetGroups': len(selected), 'alreadyRestored': len(pilot_ids), 'newGroups': len(selected)-len(pilot_ids)}
        else:
            import config, embed, store_pg
            from runtime_db import bind_runtime_db
            runtime = bind_runtime_db(config.require('db_url')['db_url'], provenance='configured-entry')
            if runtime.endpoint[0] in {'unix','localhost','127.0.0.1','::1'}: raise ValueError('remote required')
            if embed.MODEL_ID != 'intfloat/multilingual-e5-large@openrouter' or embed.PROVIDER != 'openrouter':
                raise ValueError('configured embedding profile mismatch')
            existing = reg.register(runtime, pilot)
            if existing['new']: raise ValueError('pilot DB missing')
            def checkpoint(plan):
                db = reg.register(runtime, plan, apply=True)
                ids = [f['id'] for f in plan['fragments']]
                generated = 0
                # Small exact-ID transactions preserve partial embedding progress.
                for offset in range(0, len(ids), 32):
                    chunk = ids[offset:offset+32]
                    generated += store_pg.backfill_embeddings(runtime.dsn, args.host, variant='ctx-v1', fragment_ids=chunk, limit=len(chunk))
                atomic(Path(auth['reviewDirectory'])/'db-progress.json', {**db, 'generatedVectorsThisCheckpoint': generated})
            result = run(auth, selected, pilot_ids, args.receipt_sha256, checkpoint=checkpoint)
        print(json.dumps({'ok': True, **result}), flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': type(exc).__name__}), flush=True)
        return 2


if __name__ == '__main__': raise SystemExit(main())
