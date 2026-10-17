import { beforeAll, describe, expect, test } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url));
const cases = [
  'sandbox-copy-error', 'sandbox-copy-cancel', 'sandbox-init-error',
  'sandbox-parse-error', 'sandbox-normal', 'parity-first-copy-error',
  'parity-second-copy-error', 'parity-second-copy-cancel',
  'parity-prepare-error', 'parity-normal',
];

// Compile exact production function bodies only: no module startup, real hooks,
// Git writes, application copies, dependency copies, or retained test sandbox.
const pythonProbe = String.raw`
import __future__
import argparse
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

source = Path(sys.argv[1]) / '.lazy-harness' / 'scripts'
original_mkdtemp = tempfile.mkdtemp
original_rmtree = shutil.rmtree
hashes = {}


def functions(filename, names, host):
    path = source / filename
    data = path.read_bytes()
    hashes[str(path)] = hashlib.sha256(data).hexdigest()
    tree = ast.parse(data, filename=str(path))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == set(names), 'Missing production function'
    namespace = dict(Path=Path, argparse=argparse, json=json, shutil=shutil,
                     subprocess=subprocess, sys=sys, tempfile=tempfile, ROOT=host)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec',
                 flags=__future__.annotations.compiler_flag, dont_inherit=True), namespace)
    return namespace


reports = []
with tempfile.TemporaryDirectory(prefix='lazy-cleanup-regression-') as directory:
    owned = Path(directory).resolve()
    host = owned / 'minimal-input'
    (host / '.lazy-harness').mkdir(parents=True)

    def run_case(name, kind, copy_failure=0, cancel=False, init_failure=False,
                 parse_failure=False, prepare_failure=False):
        allocated = []
        case_root = owned / name
        case_root.mkdir()
        failure = KeyboardInterrupt(name) if cancel else OSError(name)
        if parse_failure or prepare_failure:
            failure = ValueError(name)
        copy_count = 0
        guard_checked = False
        namespace = functions(
            'lifecycle-check.py' if kind == 'sandbox' else 'lifecycle-parity-runner.py',
            {'sandbox_root', 'main'} if kind == 'sandbox' else {'copy_host', 'run_fixture', 'hook_body'}, host)
        namespace.update(parse_payload=lambda raw: ({}, True, None),
                         git_output=lambda *args: '',
                         mirror_first_existing_state=lambda *args, **kwargs: (False, 0),
                         inspect=lambda raw, root, **kwargs: {'root': str(root)},
                         prepare_env=lambda *args: {}, read_validation_rows=lambda *args: [])
        if parse_failure:
            def fail_parse(raw):
                raise failure
            namespace['parse_payload'] = fail_parse
        if prepare_failure:
            def fail_prepare(*args):
                raise failure
            namespace['prepare_env'] = fail_prepare

        def allocate(suffix=None, prefix=None, dir=None):
            path = Path(original_mkdtemp(suffix=suffix, prefix=prefix, dir=str(case_root)))
            allocated.append(path)
            return str(path)

        def copy_minimal(src, destination, **kwargs):
            nonlocal copy_count, guard_checked
            copy_count += 1
            if kind == 'parity':
                ignore = kwargs['ignore']
                assert 'tmp' in ignore(str(src), ['tmp', 'keep'])
                assert 'tmp' not in ignore(str(Path(src) / 'fixtures'), ['tmp', 'keep'])
                guard_checked = True
            if copy_count == copy_failure:
                raise failure
            Path(destination).mkdir(parents=True)
            return str(destination)

        def process(args, **kwargs):
            if args == ['git', 'init', '-q']:
                if init_failure:
                    raise failure
                return subprocess.CompletedProcess(args, 0, stdout='', stderr='')
            if kind == 'parity' and str(args[0]).endswith('on-response-completed.sh'):
                return subprocess.CompletedProcess(args, 0, stdout='', stderr='')
            if kind == 'parity' and args[1:] == ['lifecycle-check', '--format=json']:
                return subprocess.CompletedProcess(args, 0, stdout=json.dumps({
                    'ok': True, 'firstOutput': '', 'helperResults': [],
                }), stderr='')
            raise AssertionError('Unexpected external process: ' + repr(args))

        def remove(path, *args, **kwargs):
            resolved = Path(path).resolve()
            assert owned in resolved.parents, 'Removal escaped newly owned test fixtures'
            return original_rmtree(path, *args, **kwargs)

        caught = None
        result = None
        output = io.StringIO()
        with patch.object(tempfile, 'mkdtemp', side_effect=allocate), \
             patch.object(shutil, 'copytree', side_effect=copy_minimal), \
             patch.object(shutil, 'rmtree', side_effect=remove), \
             patch.object(subprocess, 'run', side_effect=process), \
             patch.object(sys, 'argv', ['lifecycle-check.py', '--root', str(host), '--sandbox', '--payload', '{}']), \
             contextlib.redirect_stdout(output):
            try:
                if kind == 'sandbox':
                    result = namespace['main']()
                else:
                    result = namespace['run_fixture'](host, {'name': name, 'payload': {}, 'expectOutput': False})
            except BaseException as error:
                caught = error
        expects_error = bool(copy_failure or init_failure or parse_failure or prepare_failure)
        assert (caught is failure) if expects_error else (caught is None), (name, repr(caught))
        assert allocated and not any(path.exists() for path in allocated), (name, 'retained allocation')
        if not expects_error:
            if kind == 'sandbox':
                assert result == 0 and json.loads(output.getvalue())['sandbox'] is True
            else:
                assert result['ok'] is True and result['issues'] == []
        reports.append(dict(name=name, allocations=len(allocated), retained=0,
                            error_preserved=not expects_error or caught is failure,
                            runtime_tmp_guard=kind != 'parity' or guard_checked))

    run_case('sandbox-copy-error', 'sandbox', copy_failure=1)
    run_case('sandbox-copy-cancel', 'sandbox', copy_failure=1, cancel=True)
    run_case('sandbox-init-error', 'sandbox', init_failure=True)
    run_case('sandbox-parse-error', 'sandbox', parse_failure=True)
    run_case('sandbox-normal', 'sandbox')
    run_case('parity-first-copy-error', 'parity', copy_failure=1)
    run_case('parity-second-copy-error', 'parity', copy_failure=2)
    run_case('parity-second-copy-cancel', 'parity', copy_failure=2, cancel=True)
    run_case('parity-prepare-error', 'parity', prepare_failure=True)
    run_case('parity-normal', 'parity')
    fixture_files = [path for path in owned.rglob('*') if path.is_file()]
    assert not fixture_files, 'Probe unexpectedly wrote fixture/application files'
    fixture_root = str(owned)

assert not Path(fixture_root).exists(), 'Outer probe fixture was retained'
assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == value for path, value in hashes.items())
print(json.dumps(dict(cases=reports, fixture_files=0, fixture_file_bytes=0,
                      application_or_dependency_copies=0, source_unchanged=True,
                      fixture_root_removed=True)))
`;

type Report = {
  cases: Array<{ name: string; allocations: number; retained: number; error_preserved: boolean; runtime_tmp_guard: boolean }>;
  fixture_files: number;
  fixture_file_bytes: number;
  application_or_dependency_copies: number;
  source_unchanged: boolean;
  fixture_root_removed: boolean;
};

let report: Report;
beforeAll(() => {
  const run = spawnSync('python3', ['-c', pythonProbe, root], {
    cwd: root,
    encoding: 'utf8',
    timeout: 20_000,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
  });
  if (run.error || run.status !== 0) {
    throw new Error(`cleanup regression probe failed: ${run.error ?? run.status}\n${run.stderr}\n${run.stdout}`);
  }
  report = JSON.parse(run.stdout) as Report;
}, 25_000);

describe('lifecycle temporary allocation ownership', () => {
  for (const name of cases) {
    test(name, () => {
      const observed = report.cases.find(row => row.name === name);
      expect(observed).toBeDefined();
      expect(observed!.allocations).toBeGreaterThan(0);
      expect(observed!.retained).toBe(0);
      expect(observed!.error_preserved).toBe(true);
      expect(observed!.runtime_tmp_guard).toBe(true);
    });
  }

  test('uses no application copy and removes its own fixture', () => {
    expect(report.cases).toHaveLength(cases.length);
    expect(report.fixture_files).toBe(0);
    expect(report.fixture_file_bytes).toBe(0);
    expect(report.application_or_dependency_copies).toBe(0);
    expect(report.fixture_root_removed).toBe(true);
  });

  test('does not mutate production source', () => {
    expect(report.source_unchanged).toBe(true);
  });
});
