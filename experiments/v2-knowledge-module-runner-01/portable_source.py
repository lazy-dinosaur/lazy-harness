#!/usr/bin/env python3
"""Deterministic allowlisted source transfer; no credentials, data, service or DB effects."""
import argparse
import ast
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

MODULE = Path(__file__).resolve().parent
RUNTIME = """backfill_structure cleanup merge_guard reopen_duplicates backup brief capture_audit collect config current_v1_import current_v1_review current_v1_register current_v1_recovery current_v1_host_knowledge current_v1_semantic semantic_plan lineage_scope lineage_row_provider dedup digest_driver domain_router embed embed_server execution_scope fact_form fact_text harness_rules judge_jev knowledge_cli merge3 merge_form policy poller rule_check rule_cli rule_review rules_store runner runtime_db source_correction source_evidence source_generation source_metadata_repair source_review store store_pg subject_dict subject_merge templates window worker_tools worktime_driver""".split()
MIGRATIONS = (
    '0001_knowledge_init', '0002_search_and_cost', '0003_embedding_hybrid',
    '0004_work_unit_baseline', '0005_domain_type', '0006_rules', '0007_harness_rules_out',
    '0008_embedding_any_dim', '0009_subject_dictionary', '0010_fact_form',
    '0011_structure_fill_once', '0012_contradiction_resolution', '0013_declared_alias',
    '0014_subject_merge', '0015_source_review_receipt', '0016_source_correction',
    '0017_source_hint_resolution', '0018_source_metadata_repair',
)
PUBLIC_TESTS = (
    'test_public_relocation.py', 'test_brief_mapreduce_offline.py',
    'test_execution_scope_offline.py', 'test_lineage_row_provider_offline.py',
    'test_lineage_scope_offline.py', 'test_runtime_db_isolation_offline.py',
    'test_source_correction_receipt_offline.py', 'test_source_hint_rebind_offline.py',
    'test_source_review_gate_offline.py', 'test_publication_bundle.py',
    'test_public_loader.ts',
)
ALLOWLIST = tuple(sorted([n + '.py' for n in RUNTIME] + [
    'migrations/' + n + '.sql' for n in MIGRATIONS] + [
    'portable_source.py', 'portable_probe.py', 'knowledge.example.json',
    'README.md', 'INSTALL.md', 'PORTABLE.md', 'pi-extension/knowledge.ts', 'fragmenter/check_fragments.py',
    'scale-03/measure/run_mapreduce.py', 'scale-03/measure/judge_measure.py'] + list(PUBLIC_TESTS)))
MANIFEST = 'SOURCE-MANIFEST.json'
MAX_BYTES = 8 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def inventory(root):
    root = root.resolve(strict=True)
    files = {}
    for name in ALLOWLIST:
        p = root / name
        if any(x.is_symlink() for x in [p, *p.parents] if x != root.parent):
            raise ValueError('symlink source denied')
        p.resolve(strict=True).relative_to(root)
        data = p.read_bytes()
        if len(data) > MAX_BYTES:
            raise ValueError('oversize source')
        files[name] = data
    # Fail closed if a local Python import is omitted from the explicit allowlist.
    for name, data in files.items():
        if not name.endswith('.py'):
            continue
        for node in ast.walk(ast.parse(data)):
            names = ([a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import)
                     else [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
            for imported in names:
                local = imported + '.py'
                if (root / local).is_file() and local not in files:
                    raise ValueError('runtime dependency absent from allowlist: ' + local)
    return files


def build(root, output):
    files = inventory(root)
    repo = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], text=True).strip()
    revision = subprocess.check_output(['git', '-C', repo, 'rev-parse', 'HEAD'], text=True).strip()
    rows = []
    for name, data in files.items():
        rel = (root.resolve() / name).relative_to(Path(repo)).as_posix()
        base = subprocess.run(['git', '-C', repo, 'show', revision + ':' + rel], capture_output=True)
        original = digest(base.stdout) if base.returncode == 0 else None
        rows.append({'path': name, 'sha256': digest(data), 'bytes': len(data), 'baseSha256': original,
                     'delta': 'added' if original is None else 'unchanged' if original == digest(data) else 'modified'})
    manifest = {'schema': 'lh-v2-portable-source/v1', 'baseRevision': revision,
                'sourceDigest': digest(json_bytes(rows)), 'files': rows,
                'scope': 'source-only; reviewed code and inert SQL assets only; no corpus, credentials, SQL application, installed services or release',
                'externalDependencies': {'python': '>=3.12', 'databaseDriver': 'psycopg or psycopg2',
                    'optionalPi': 'existing authenticated pi CLI; load extension with -e',
                    'embedding': 'existing configured provider; same model/dimension as stored corpus'}}
    files[MANIFEST] = json_bytes(manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w', format=tarfile.USTAR_FORMAT) as tar:
            for name, data in sorted(files.items()):
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(data), 0o644, 0
                tar.addfile(info, io.BytesIO(data))
    return {'ok': True, 'bundle': str(output), 'sha256': digest(output.read_bytes()),
            'sourceDigest': manifest['sourceDigest'], 'baseRevision': revision, 'files': len(rows)}


def verify(bundle, expected_sha256):
    if bundle.stat().st_size > MAX_BYTES or digest(bundle.read_bytes()) != expected_sha256:
        raise ValueError('bundle checksum/size mismatch')
    files = {}
    with tarfile.open(bundle, 'r:gz') as tar:
        total = 0
        for member in tar:
            if member.name not in (*ALLOWLIST, MANIFEST) or not member.isfile() or member.name in files:
                raise ValueError('non-allowlisted/duplicate/nonregular archive member')
            total += member.size
            if member.size < 0 or total > MAX_BYTES:
                raise ValueError('archive size bound')
            files[member.name] = tar.extractfile(member).read()
    if set(files) != set(ALLOWLIST) | {MANIFEST}:
        raise ValueError('incomplete bundle')
    manifest = json.loads(files[MANIFEST])
    rows = manifest['files']
    if manifest.get('schema') != 'lh-v2-portable-source/v1' or len(rows) != len(ALLOWLIST):
        raise ValueError('invalid manifest')
    if {r['path'] for r in rows} != set(ALLOWLIST) or digest(json_bytes(rows)) != manifest['sourceDigest']:
        raise ValueError('invalid source delta')
    for row in rows:
        data = files[row['path']]
        if len(data) != row['bytes'] or digest(data) != row['sha256']:
            raise ValueError('source checksum mismatch')
    return files, manifest


def extract(bundle, expected_sha256, destination):
    files, manifest = verify(bundle, expected_sha256)
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o644)
    return {'ok': True, 'files': len(manifest['files']), 'sourceDigest': manifest['sourceDigest']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build_parser = sub.add_parser('build')
    build_parser.add_argument('--output', required=True, type=Path)
    for command in ('verify', 'extract'):
        p = sub.add_parser(command)
        p.add_argument('--bundle', required=True, type=Path)
        p.add_argument('--sha256', required=True)
        if command == 'extract':
            p.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'build':
            result = build(MODULE, args.output)
        elif args.command == 'extract':
            result = extract(args.bundle, args.sha256, args.destination)
        else:
            _, manifest = verify(args.bundle, args.sha256)
            result = {'ok': True, 'sourceDigest': manifest['sourceDigest'], 'files': len(manifest['files'])}
        print(json.dumps(result))
        return 0
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': type(exc).__name__}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
