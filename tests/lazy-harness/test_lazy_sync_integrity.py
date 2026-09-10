#!/usr/bin/env python3
"""Isolated CLI regression: real synthetic Git sources/hosts, no live host sync.

Run with Python; SYNC_TEST_OUTPUT retains JSON results and per-case CLI logs.
TMPDIR controls fixture placement. Only copies exact runtime dependencies.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_FILES = [
    'bin/lazy', 'scripts/lazy-sync.ts', 'scripts/runtime-paths.ts',
    'scripts/manifest-path-matcher.ts', 'scripts/agent-activate.ts',
]


def put(root, rel, content):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def git(root, *args):
    return subprocess.check_output(
        ['git', '-c', 'core.hooksPath=/dev/null', '-C', str(root), *args],
        env={k: v for k, v in os.environ.items() if not k.startswith('GIT_')},
        stderr=subprocess.PIPE, text=True,
    ).strip()


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*')
            if p.is_file() and '.git' not in p.relative_to(root).parts}


def run_case(name, output):
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='lazy-sync-integrity-') as tmp:
        base = Path(tmp)
        source, host = base / 'source', base / 'host'
        source.mkdir()
        host.mkdir()
        for root in (source, host):
            git(root, 'init', '-q')
            git(root, 'config', 'user.email', 'fixture@example.invalid')
            git(root, 'config', 'user.name', 'Sync fixture')
        for rel in RUNTIME_FILES:
            dest = source / '.lazy-harness' / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / '.lazy-harness' / rel, dest)
        put(source, '.lazy-harness/AGENTS.md', 'synthetic framework\n')
        put(source, '.lazy-harness/required.txt', 'required\n')
        items = [{'path': rel, 'kind': 'file'} for rel in RUNTIME_FILES + [
            'AGENTS.md', 'required.txt', 'ssot/capabilities.json', 'ssot/policies.json']]
        for key in ('capabilities', 'policies'):
            put(source, f'.lazy-harness/ssot/{key}.json', json.dumps({
                key: [{'id': 'shared', 'owner': 'framework-global', 'value': 'source'},
                      {'id': 'new-seed', 'owner': 'framework-global'}]}))
        put(source, '.lazy-harness/manifests/init-categories.json',
            json.dumps({'categories': {'A': {'items': items}}}))
        git(source, 'add', '.')
        git(source, 'commit', '-qm', 'initial')
        old_sha = git(source, 'rev-parse', 'HEAD')
        shutil.copytree(source / '.lazy-harness', host / '.lazy-harness')
        put(source, '.lazy-harness/required.txt', 'updated required\n')
        for key in ('capabilities', 'policies'):
            put(host, f'.lazy-harness/ssot/{key}.json', json.dumps({
                key: [{'id': 'shared', 'owner': 'host-project', 'value': 'host'},
                      {'id': 'host-only', 'owner': 'host-project'}], 'hostMetadata': True}))
        put(host, '.lazy-harness/domain/host.md', 'host-owned memory\n')
        if name.startswith('missing-required'):
            (source / '.lazy-harness/required.txt').unlink()
        if name.startswith('malformed-'):
            _, side, key, form = name.split('-')
            root = source if side == 'source' else host
            put(root, f'.lazy-harness/ssot/{key}.json', '{bad' if form == 'syntax' else json.dumps({key: {}}))
        git(source, 'add', '-A')
        git(source, 'commit', '-qm', 'new framework revision')
        head = git(source, 'rev-parse', 'HEAD')
        marker = '.lazy-harness/state/synced-from-commit'
        marker_sha = head if name == 'dirty-equal' else old_sha
        if name != 'unknown-marker':
            put(host, marker, json.dumps({'syncedFromCommit': marker_sha, 'sourceRoot': str(source)}))
        if name.startswith('dirty-'):
            put(source, '.lazy-harness/required.txt', 'uncommitted source\n')
        if name == 'activation-failure':
            put(host, '.pi/settings.json', '{bad')
        before = snapshot(host)
        flags = ['--force'] if name.endswith('-force') else []
        if name == 'clean-dry-run':
            flags.append('--dry-run')
        env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'LAZY_'))}
        env.update(LAZY_HOST_ROOT=str(host), LAZY_RUNTIME_ROOT=str(base / 'runtime'),
                   LAZY_SHARED_ROOT=str(base / 'shared'), HOME=str(base / 'home'),
                   GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null')
        command = ['bun', str(source / '.lazy-harness/scripts/lazy-sync.ts'),
                   '--from', str(source), '--target', str(host), *flags]
        result = subprocess.run(command, cwd=host, env=env, capture_output=True, text=True, timeout=30)
        after = snapshot(host)
        text = result.stdout + result.stderr
        assertions = {}
        if name == 'unknown-marker':
            # The governing record conflicts (warn versus exit 2); observe, do not invent policy.
            assertions['host memory preserved'] = after['.lazy-harness/domain/host.md'] == before['.lazy-harness/domain/host.md']
        elif name.startswith(('missing-required', 'malformed-')) or name in ('dirty-behind', 'dirty-equal', 'activation-failure'):
            assertions['nonzero exit'] = result.returncode != 0
            assertions['marker byte-identical'] = after.get(marker) == before.get(marker)
            assertions['no success publication'] = '✓ Synced.' not in text and '✓ marker updated' not in text
            if name != 'activation-failure':
                assertions['host byte-identical'] = after == before
            if name.startswith('dirty-'):
                assertions['dirty denial exit 2'] = result.returncode == 2 and '[Drift] ahead:' in text
        elif name == 'clean-dry-run':
            assertions['dry-run succeeds'] = result.returncode == 0
            assertions['host byte-identical'] = after == before
        else:
            assertions['sync succeeds'] = result.returncode == 0 and '✓ Synced.' in text
            assertions['marker advances'] = json.loads(after[marker])['syncedFromCommit'] == head
            assertions['managed file updated'] = after['.lazy-harness/required.txt'] == (source / '.lazy-harness/required.txt').read_bytes()
            assertions['activation created'] = (host / '.pi/APPEND_SYSTEM.md').is_file()
            for key in ('capabilities', 'policies'):
                data = json.loads(after[f'.lazy-harness/ssot/{key}.json'])
                rows = {r['id']: r for r in data[key]}
                assertions[f'{key} ownership retained'] = data['hostMetadata'] and rows['shared']['value'] == 'host' and 'host-only' in rows and 'new-seed' in rows
        assertions['host memory preserved'] = after['.lazy-harness/domain/host.md'] == before['.lazy-harness/domain/host.md']
        if output:
            (output / f'{name}.log').write_text(json.dumps(command) + '\n' + text, encoding='utf-8')
        return {'case': name, 'exitCode': result.returncode, 'assertions': assertions,
                'passed': all(assertions.values()), 'elapsedSeconds': round(time.monotonic() - started, 4),
                'observationOnly': name == 'unknown-marker'}


def main():
    output = Path(os.environ['SYNC_TEST_OUTPUT']) if os.environ.get('SYNC_TEST_OUTPUT') else None
    if output:
        output.mkdir(parents=True, exist_ok=True)
    cases = ['dirty-behind', 'dirty-equal', 'missing-required', 'missing-required-force']
    cases += [f'malformed-{side}-{key}-{form}' for side in ('source', 'host')
              for key in ('capabilities', 'policies') for form in ('syntax', 'shape')]
    cases += ['clean-sync', 'dirty-behind-force', 'clean-dry-run', 'activation-failure', 'unknown-marker']
    started = time.monotonic()
    results = [run_case(case, output) for case in cases]
    report = {'results': results, 'passed': sum(r['passed'] for r in results),
              'failed': sum(not r['passed'] for r in results),
              'assertions': sum(len(r['assertions']) for r in results),
              'failedAssertions': sum(sum(not a for a in r['assertions'].values()) for r in results),
              'elapsedSeconds': round(time.monotonic() - started, 4)}
    text = json.dumps(report, indent=2)
    print(text)
    if output:
        (output / 'results.json').write_text(text + '\n', encoding='utf-8')
    return int(report['failed'] > 0)


if __name__ == '__main__':
    raise SystemExit(main())
