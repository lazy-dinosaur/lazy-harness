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
RUNTIME += """subject_inspection identity_ref model_output subject_contract validation_receipts writer_worker embedding_models embedding_cache embedding_thresholds embedding_guard embedding_inputs embedding_transport embedding_admission candidate_policy source_grounding write_contract derived_view migration_evidence migrate_domain_subject""".split()
SCALE04 = """prepare ddd_criterion safety writer_transport area_catalog confirmed_area_catalog local_db jev_failure active_worker active_worker_transport active_judgements pipeline place_write place_write_absorb objects precompute area_absorb subject_ground subject_shorten reembed fresh report area_report publication_provenance calibrate calibration_evidence""".split()
SCALE04_ASSETS = ('writer_host.mjs', 'active_worker_host.mjs', 'test_offline.py',
                  'test_isolated_scope_offline.py', 'fixtures/inventory.json', 'v1/synthetic.md')
NATIVE_ALLOWLIST = (
    'unit1-controller-source-phase1/controller.py', 'unit1-controller-source-phase1/real_bindings.py',
    'unit1-controller-source-phase1/native_services.py', 'unit1-controller-source-phase1/native_bridge.py',
    'unit1-controller-source-phase1/native_bridge.mjs', 'unit1-controller-source-phase1/test_controller.py',
    'unit1-controller-source-phase1/binding-completion-01/test_real_bindings.py',
    'unit1-controller-source-phase1/fixture_child.py',
    'unit1-controller-source-phase1/native-completion-02/test_native.py',
    'unit1-controller-source-phase1/native-completion-02/fixture-bridge.mjs',
    'unit1-controller-source-phase1/native-completion-02/dummy-runtime.mjs',
    'unit1-controller-source-phase1/native-completion-02/dummy-auth.mjs',
    'unit1-trial-caller-01/trial.py', 'unit1-trial-caller-01/test_trial.py',
    'unit1-trial-caller-01/fixtures/plan.json', 'unit1-trial-caller-01/fixtures/synthetic-source.md',
    'unit1-per-request-quote-source-01/test_per_request.py', 'unit1-stage-control-01/test_stages.py',
    'unit1-admission-frontier-source-01/test_frontier.py', 'unit1-quota-embedding-source-01/test_broker.mjs',
)
MODULE_PREFIX = 'experiments/v2-knowledge-module-runner-01/'
NATIVE_PREFIX = 'experiments/v2-native-minlive/'
MIGRATIONS = (
    '0001_knowledge_init', '0002_search_and_cost', '0003_embedding_hybrid',
    '0004_work_unit_baseline', '0005_domain_type', '0006_rules', '0007_harness_rules_out',
    '0008_embedding_any_dim', '0009_subject_dictionary', '0010_fact_form',
    '0011_structure_fill_once', '0012_contradiction_resolution', '0013_declared_alias',
    '0014_subject_merge', '0015_source_review_receipt', '0016_source_correction',
    '0017_source_hint_resolution', '0018_source_metadata_repair',
    '0019_domain_subject', '0020_partition_actor', '0021_subject_type',
    '0022_subject_parent', '0023_validation_receipt',
)
PUBLIC_TESTS = (
    'test_public_relocation.py', 'test_brief_mapreduce_offline.py',
    'test_execution_scope_offline.py', 'test_lineage_row_provider_offline.py',
    'test_lineage_scope_offline.py', 'test_runtime_db_isolation_offline.py',
    'test_source_correction_receipt_offline.py', 'test_source_hint_rebind_offline.py',
    'test_source_review_gate_offline.py', 'test_publication_bundle.py',
    'test_subject_inspection_offline.py',
    'test_public_loader.ts',
)
ALLOWLIST = tuple(sorted([n + '.py' for n in RUNTIME] + [
    'migrations/' + n + '.sql' for n in MIGRATIONS] + [
    'portable_source.py', 'portable_probe.py', 'knowledge.example.json',
    'README.md', 'INSTALL.md', 'PORTABLE.md', 'pi-extension/knowledge.ts', 'fragmenter/check_fragments.py',
    'scale-03/measure/run_mapreduce.py', 'scale-03/measure/judge_measure.py',
    'test_g16_publication.py', 'test_g16_closure.py', 'test_g16_hosts.mjs'] + list(PUBLIC_TESTS) +
    ['scale-04/' + n + '.py' for n in SCALE04] + ['scale-04/' + n for n in SCALE04_ASSETS]))
REPOSITORY_ALLOWLIST = tuple(sorted([MODULE_PREFIX + n for n in ALLOWLIST] +
                                   [NATIVE_PREFIX + n for n in NATIVE_ALLOWLIST]))


def selected_paths(repository=False):
    return REPOSITORY_ALLOWLIST if repository else ALLOWLIST
MANIFEST = 'SOURCE-MANIFEST.json'
MAX_BYTES = 8 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def inventory(root, *, repository=False):
    root = root.resolve(strict=True)
    files = {}
    for name in selected_paths(repository):
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
                for local in (Path(name).parent / (imported + '.py'), Path(MODULE_PREFIX if repository else '') / (imported + '.py')):
                    if (root / local).is_file() and local.as_posix() not in files:
                        raise ValueError('runtime dependency absent from allowlist: ' + local.as_posix())
    return files


def build(root, output, *, repository=False):
    files = inventory(root, repository=repository)
    repo = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], text=True).strip()
    revision = subprocess.check_output(['git', '-C', repo, 'rev-parse', 'HEAD'], text=True).strip()
    rows = []
    for name, data in files.items():
        rel = (root.resolve() / name).relative_to(Path(repo)).as_posix()
        base = subprocess.run(['git', '-C', repo, 'show', revision + ':' + rel], capture_output=True)
        original = digest(base.stdout) if base.returncode == 0 else None
        rows.append({'path': name, 'sha256': digest(data), 'bytes': len(data), 'baseSha256': original,
                     'delta': 'added' if original is None else 'unchanged' if original == digest(data) else 'modified'})
    manifest = {'schema': 'lh-g16-public-source/v1' if repository else 'lh-v2-portable-source/v1', 'baseRevision': revision,
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


def verify(bundle, expected_sha256, *, repository=False):
    if bundle.stat().st_size > MAX_BYTES or digest(bundle.read_bytes()) != expected_sha256:
        raise ValueError('bundle checksum/size mismatch')
    names = selected_paths(repository)
    files = {}
    with tarfile.open(bundle, 'r:gz') as tar:
        total = 0
        for member in tar:
            if member.name not in (*names, MANIFEST) or not member.isfile() or member.name in files:
                raise ValueError('non-allowlisted/duplicate/nonregular archive member')
            total += member.size
            if member.size < 0 or total > MAX_BYTES:
                raise ValueError('archive size bound')
            files[member.name] = tar.extractfile(member).read()
    if set(files) != set(names) | {MANIFEST}:
        raise ValueError('incomplete bundle')
    manifest = json.loads(files[MANIFEST])
    rows = manifest['files']
    schema = 'lh-g16-public-source/v1' if repository else 'lh-v2-portable-source/v1'
    if manifest.get('schema') != schema or len(rows) != len(names):
        raise ValueError('invalid manifest')
    if {r['path'] for r in rows} != set(names) or digest(json_bytes(rows)) != manifest['sourceDigest']:
        raise ValueError('invalid source delta')
    for row in rows:
        data = files[row['path']]
        if len(data) != row['bytes'] or digest(data) != row['sha256']:
            raise ValueError('source checksum mismatch')
    return files, manifest


def extract(bundle, expected_sha256, destination, *, repository=False):
    files, manifest = verify(bundle, expected_sha256, repository=repository)
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
    build_parser.add_argument('--repository', action='store_true', help='repository-shaped G16 Native + module closure')
    for command in ('verify', 'extract'):
        p = sub.add_parser(command)
        p.add_argument('--bundle', required=True, type=Path)
        p.add_argument('--sha256', required=True)
        p.add_argument('--repository', action='store_true')
        if command == 'extract':
            p.add_argument('--destination', required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'build':
            result = build(MODULE.parents[1] if args.repository else MODULE, args.output, repository=args.repository)
        elif args.command == 'extract':
            result = extract(args.bundle, args.sha256, args.destination, repository=args.repository)
        else:
            _, manifest = verify(args.bundle, args.sha256, repository=args.repository)
            result = {'ok': True, 'sourceDigest': manifest['sourceDigest'], 'files': len(manifest['files'])}
        print(json.dumps(result))
        return 0
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': type(exc).__name__}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
