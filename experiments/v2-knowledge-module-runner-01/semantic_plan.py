"""Immutable, local-only source accounting for a fresh semantic digestion job.

No model/DB imports. An absent original is a blocker, never a snippet substitute.
"""
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
import re

import current_v1_import as intake
import current_v1_review as review
import current_v1_register as registration

SCHEMA = 'current-v1-semantic/v1'
CAP = 4244
LIMITS = {'sourceChars': 18000, 'packetChars': 100000, 'outputChars': 48000,
          'claimsPerPage': 16, 'relationsPerPage': 2, 'pagesPerBatch': 4}
ARTIFACTS = ('result.json', 'intake-ledger.jsonl', 'candidates.jsonl', 'references.jsonl', 'events.jsonl')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def fingerprint(value):
    return sha(review.canonical_json(value).encode())


def local(root, path):
    root = Path(root).resolve(strict=True)
    path = Path(path)
    if not path.is_absolute():
        path = root / path
    # Reject symlinks even when their current target is contained.
    if not path.is_relative_to(root) or any(p.is_symlink() for p in (path, *path.parents) if p != root.parent):
        raise ValueError('path_not_root_bound')
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError('path_not_root_bound')
    return resolved


def immutable(path, value):
    """Same bytes are idempotent; different bytes or symlinks never overwrite."""
    path = Path(path)
    data = (review.canonical_json(value) + '\n').encode()
    if path.is_symlink():
        raise ValueError('symlink_artifact')
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('immutable_artifact_conflict')
        return sha(data)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return sha(data)


def role(kind):
    if kind == 'lazy-harness-host-knowledge-record':
        return 'host-operational'
    if kind and ('framework' in kind or 'context' in kind or kind == 'source-policy-context'):
        return 'framework-context'
    return 'med-business-reference'


def request_context(path, expected):
    root = Path.cwd().resolve()
    request = registration.bound_json(local(root, path), expected)
    if (request.get('schemaVersion') != SCHEMA or request.get('root') != str(root)
            or request.get('roleCaps') != {'proposer': CAP, 'judge': CAP}
            or request.get('limits') != LIMITS
            or request.get('truthPromotion') != 'none'
            or request.get('approvedReferenceUse') != 'user-approved-reference'
            or request.get('authorOwnership') != 'unverified'
            or request.get('confidence') != 'candidate'
            or not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,79}', request.get('host', ''))):
        raise ValueError('semantic_request_scope_mismatch')
    parent = registration.bound_json(local(root, request['parentReceipt']), request['parentReceiptSha256'])
    if any(parent.get(k) != request.get(k) for k in ('sourceRoot', 'host')):
        raise ValueError('semantic_parent_scope_mismatch')
    job = local(root, request['jobDirectory'])
    if not job.is_relative_to(root / '.local') or job == root / '.local':
        raise ValueError('job_not_private_local')
    for old in request['paidResults']:
        p = local(root, old['path'])
        if registration.digest(p) != old['sha256'] or job == p.parent or job in p.parents:
            raise ValueError('old_paid_result_binding_mismatch')
    return request


def paid_evidence(request):
    """Reuse real claim payloads only. Old hash-only rows are NOT generated knowledge."""
    claims, uncertain, rows = {}, defaultdict(set), []
    for entry in request['paidResults']:
        for row in review.read_jsonl(local(request['root'], entry['path'])):
            rows.append(row)
            proof = row.get('sourceProof', {})
            fp = proof.get('sourceDocFP')
            payloads = row.get('verifiedCandidates', [])
            supported = []
            for item in payloads:
                if (isinstance(item, dict) and item.get('status') == 'supported'
                        and review.payload_status(item, item.get('source_quote', '')) == 'eligible_payload'):
                    key = item.get('claimFP')
                    if key:
                        claims[key] = {'claimFP': key, 'claim': item['claim'], 'source_quote': item['source_quote'],
                                       'sourceDocFP': fp, 'proof': proof, 'result': entry}
                        supported.append(key)
            if row.get('status') != 'reviewed' or any(c.get('status') != 'supported' for c in payloads):
                for cid in row.get('candidateIds', []):
                    uncertain[cid].add(entry['sha256'])
    return list(claims.values()), uncertain


def source_ranges(text, suffix):
    """Preserve structured parents. Oversized parents explicitly remain incomplete.

    JSONL rows stay whole. Markdown/plain text splits at line boundaries with the
    full heading context retained by the batch; no prompt slice is silently lost.
    """
    limit = LIMITS['sourceChars']
    if suffix in {'.json', '.xml'}:
        try:
            if suffix == '.json':
                json.loads(text)
            else:
                from xml.etree import ElementTree
                if re.search(r'<!\s*(DOCTYPE|ENTITY)\b', text, re.I):
                    return [], 'unsafe_xml_entity'
                ElementTree.fromstring(text)
        except Exception:
            return [], 'invalid_structured_parent'
        return ([(0, len(text))], None) if len(text) <= limit else ([], 'structured_parent_input_limit')
    if suffix not in {'.md', '.markdown', '.txt', '.jsonl', '.yaml', '.yml', '.csv'}:
        return [], 'unsupported_parent_format'
    spans, start, end = [], 0, 0
    for line in text.splitlines(keepends=True):
        if suffix == '.jsonl' and line.strip():
            try:
                json.loads(line)
            except ValueError:
                return [], 'invalid_jsonl_parent'
        if len(line) > limit:
            return [], 'parent_line_input_limit'
        if end + len(line) - start > limit:
            spans.append((start, end))
            start = end
        end += len(line)
    if end > start:
        spans.append((start, end))
    return spans, None if spans else 'empty_source'


def build_plan(request, request_hash):
    root = Path(request['root'])
    old, uncertain = paid_evidence(request)
    reused = defaultdict(list)
    for c in old:
        reused[c['sourceDocFP']].append(c)
    dispositions, batches, documents, blockers = [], [], [], []
    versions = {}
    for dataset in request['datasets']:
        directory = local(root, dataset['ingestion'])
        for name in ARTIFACTS:
            if registration.digest(directory / name) != dataset['intakeHashes'][name]:
                raise ValueError('intake_changed')
        result, candidates, ledger = review.load_ingestion(directory)
        manifest = result['manifest']
        if (manifest['sha256'] != dataset['manifestSha256'] or manifest['version'] != dataset['version']
                or manifest['sourceIdentity']['sourceRoot'] != request['sourceRoot']):
            raise ValueError('dataset_identity_mismatch')
        versions[dataset['version']] = len(candidates)
        grouped = defaultdict(list)
        for candidate in candidates:
            grouped[candidate['sourceDocFP']].append(candidate)
        bundle = local(root, dataset['bundle'])
        objects = None
        if (bundle / 'manifest.json').is_file():
            kwargs = dict(expected_manifest_sha256=dataset['manifestSha256'], expected_source_root=request['sourceRoot'],
                          expected_namespace='current-v1', expected_version=dataset['version'])
            if dataset.get('parentManifestSha256'):
                kwargs['expected_parent_manifest_sha256'] = dataset['parentManifestSha256']
            _, _, objects = intake.load_and_validate_bundle(bundle, **kwargs)
        else:
            blockers.append({'version': dataset['version'], 'reason': 'original_bundle_missing_inside_root', 'bundle': str(bundle)})
        by_fp = defaultdict(list)
        for obj in objects or []:
            by_fp[obj.sha256].append(obj)
        # Account captured documents even where old structural intake made no candidate.
        all_fps = sorted(set(grouped) | set(by_fp) | set(ledger))
        for fp in all_fps:
            cs, obs = grouped[fp], by_fp[fp]
            paths = sorted({o.original_relative_path for o in obs} or set(ledger.get(fp, {}).get('sourcePaths', [])))
            kinds = sorted({o.source_kind or 'unknown' for o in obs} or set(ledger.get(fp, {}).get('sourceKinds', [])))
            roles = sorted({role(k) for k in kinds})
            source_role = roles[0] if len(roles) == 1 else 'mixed-source-context'
            reason, text, spans = None, '', []
            if not obs:
                reason = 'original_bundle_missing_inside_root'
            elif any(o.disposition not in intake.CAPTURED_DISPOSITIONS | {'framework-context', 'supported-safe-textcaptured+structure-ready'} for o in obs):
                reason = 'capture_safety_or_nonknowledge_hold'
            elif any(k.startswith('excluded-') or 'private' in k for k in kinds):
                reason = 'privacy_unsafe_source_kind'
            else:
                try:
                    text = obs[0].body.decode('utf-8')
                except UnicodeDecodeError:
                    reason = 'non_utf8_parent'
                if not reason and not review.safe_payload_text(text, max(len(text), 1)):
                    reason = 'privacy_or_unsafe_body'
                if not reason:
                    spans, reason = source_ranges(text, Path(paths[0]).suffix.lower())
            doc_id = fingerprint([dataset['version'], fp])
            doc = {'documentId': doc_id, 'version': dataset['version'], 'sourceDocFP': fp,
                   'sourcePaths': paths, 'sourceKinds': kinds, 'sourceRole': source_role,
                   'ownership': sorted({o.ownership or 'unverified' for o in obs}),
                   'captureTime': sorted({o.capture_time for o in obs if o.capture_time}),
                   'originalDisposition': sorted({o.disposition for o in obs}),
                   'batchIds': [], 'deferredReason': reason}
            # Old unknown/error calls are not replaced by fresh source-level replay.
            unknown = [c for c in cs if c['candidateId'] in uncertain]
            doc_batches = []
            for start, end in spans:
                line_start = text.count('\n', 0, start) + 1
                line_end = text.count('\n', 0, end) + (0 if text[:end].endswith('\n') else 1)
                linked = [c['candidateId'] for c in cs if c.get('lineStart') is None or
                          (c.get('lineStart', 1) <= line_end and c.get('lineEnd', c.get('lineStart', 1)) >= line_start)]
                held = any(c['candidateId'] in linked for c in unknown)
                bid = fingerprint([doc_id, start, end, sha(text[start:end].encode())])
                heading_context = '\n'.join(l for l in text.splitlines() if re.match(r'^#{1,6} ', l)) if Path(paths[0]).suffix.lower() in {'.md', '.markdown'} else ''
                batch = {'batchId': bid, 'documentId': doc_id, 'sourceRole': source_role,
                         'sourceDocFP': fp, 'sourcePaths': paths, 'version': dataset['version'],
                         'manifestSha256': dataset['manifestSha256'], 'ownership': doc['ownership'],
                         'captureTime': doc['captureTime'], 'originalDisposition': doc['originalDisposition'],
                         'start': start, 'end': end, 'lineStart': line_start, 'lineEnd': line_end,
                         'text': text[start:end], 'textSha256': sha(text[start:end].encode()),
                         'parentContext': heading_context, 'candidateIds': linked,
                         'existingClaims': [c for c in reused[fp] if c['source_quote'] in text[start:end]],
                         'deferredReason': 'old_uncertain_paid_outcome_no_replay' if held else None}
                if len(review.canonical_json(batch)) > LIMITS['packetChars']:
                    batch['deferredReason'] = 'packet_context_input_limit'
                batches.append(batch)
                doc_batches.append(batch)
                doc['batchIds'].append(bid)
            documents.append(doc)
            for c in cs:
                linked_batches = [b for b in doc_batches if c['candidateId'] in b['candidateIds']]
                deferred = reason or ('no_exact_parent_range' if not linked_batches else None)
                if linked_batches and all(b['deferredReason'] for b in linked_batches):
                    deferred = 'old_uncertain_paid_outcome_no_replay' if c['candidateId'] in uncertain else 'parent_batch_deferred'
                dispositions.append({'candidateId': c['candidateId'], 'version': dataset['version'],
                                     'sourceDocFP': fp, 'sourceRole': source_role,
                                     'batchIds': [b['batchId'] for b in linked_batches],
                                     'disposition': 'justified_deferred' if deferred else 'pending_semantic_result',
                                     'reason': deferred})
    runnable = sum(not b['deferredReason'] for b in batches)
    summary = {'candidateCountsByVersion': versions, 'originalPlusDeltaCandidates': sum(versions.values()),
               'candidateDispositions': dict(Counter(c['disposition'] for c in dispositions)),
               'candidateRoles': dict(Counter(c['sourceRole'] for c in dispositions)),
               'documents': len(documents), 'sourceBatchGroupCount': len(batches), 'runnableBatchCount': runnable,
               'minimumRoleCalls': {'proposer': runnable, 'judge': runnable},
               'maximumPlannedRoleCalls': {r: min(CAP, runnable * LIMITS['pagesPerBatch']) for r in ('proposer', 'judge')},
               'roleCeiling': CAP, 'continuationDemandUpperBound': runnable * LIMITS['pagesPerBatch'],
               'privacyHeldDocuments': None if blockers else sum((d['deferredReason'] or '').startswith(('privacy', 'unsafe', 'capture_safety')) for d in documents),
               'reusedGeneratedClaims': len(old), 'referenceFragmentsAreGenerated': False,
               'safeCapturedExhaustive': False, 'wholeComplete': False,
               'planningBlocked': bool(blockers), 'baseCallsExceedCap': runnable > CAP}
    return {'schemaVersion': SCHEMA, 'requestSha256': request_hash, 'root': request['root'],
            'host': request['host'], 'sourceRoot': request['sourceRoot'], 'limits': LIMITS,
            'roleCaps': request['roleCaps'], 'documents': documents, 'batches': batches,
            'candidates': dispositions, 'reusedClaims': old, 'blockers': blockers, 'summary': summary}


def implementation_hashes():
    directory = Path(__file__).resolve().parent
    names = ('semantic_plan.py', 'current_v1_semantic.py', 'current_v1_host_knowledge.py',
             'current_v1_review.py', 'current_v1_import.py', 'current_v1_register.py', 'current_v1_recovery.py',
             'source_generation.py', 'brief.py', 'capture_audit.py', 'config.py', 'store_pg.py',
             'runtime_db.py', 'embed.py', 'worker_tools.py')
    return {n: registration.digest(directory / n) for n in names}


def prepare(request_path, request_hash):
    request = request_context(request_path, request_hash)
    plan = build_plan(request, request_hash)
    job = local(request['root'], request['jobDirectory'])
    filename = 'blocked-plan.json' if plan['blockers'] else 'plan.json'
    plan_hash = immutable(job / filename, plan)
    if not plan['blockers']:
        receipt = {**request, 'planPath': str(job / filename), 'planSha256': plan_hash,
                   'requestPath': str(local(request['root'], request_path)), 'requestSha256': request_hash,
                   'implementationHashes': implementation_hashes()}
        receipt_hash = immutable(job / 'receipt.json', receipt)
    else:
        receipt_hash = None
    report = {**plan['summary'], 'planPath': str(job / filename), 'planSha256': plan_hash,
              'receiptSha256': receipt_hash, 'blockers': plan['blockers']}
    immutable(job / ('blocked-report.json' if plan['blockers'] else 'prepare-report.json'), report)
    return report


def context(receipt_path, receipt_hash):
    root = Path.cwd().resolve()
    receipt = registration.bound_json(local(root, receipt_path), receipt_hash)
    request = request_context(receipt['requestPath'], receipt['requestSha256'])
    if receipt.get('implementationHashes') != implementation_hashes():
        raise ValueError('execution_implementation_changed')
    if any(receipt.get(k) != value for k, value in request.items()):
        raise ValueError('receipt_request_mismatch')
    plan = registration.bound_json(local(root, receipt['planPath']), receipt['planSha256'])
    if (plan['requestSha256'] != receipt['requestSha256'] or plan['root'] != str(root)
            or plan['blockers'] or plan != build_plan(request, receipt['requestSha256'])):
        raise ValueError('normalized_plan_binding_mismatch')
    return receipt, plan
