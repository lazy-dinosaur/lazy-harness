import { describe, expect, test } from 'bun:test';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { collectRuntimePaths } from '../../.lazy-harness/scripts/framework-runtime-ownership.ts';
import path from 'node:path';

const root = fileURLToPath(new URL('../../', import.meta.url));
const cases = ['host-local', 'managed-leak', 'framework-local', 'explicit-local', 'missing-manifest', 'external-writer', 'graph-write', 'graph-delete', 'cache-write', 'cache-delete', 'environment', 'copy-failure'];
const probe = String.raw`
import __future__
import ast
import contextlib
import io
import json
import os
from pathlib import Path
import pathlib
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace

repo = Path(sys.argv[1]).resolve()
case = sys.argv[2]
source = repo / '.lazy-harness/scripts/self-test.py'
original = source.read_bytes()
tree = ast.parse(original, filename=str(source))
names = {'check_framework_runtime_no_host_product_hardcoding', 'copy_harness_fixture', 'check_retrieval_workflow_benchmark_cli', '_check_retrieval_workflow_benchmark_fixture'}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
class GuardFailure(Exception): pass
def fail(message): raise GuardFailure(message)
def clean_env(**overrides):
    result = {k:v for k,v in os.environ.items() if not k.startswith('LAZY_')}
    result.update(overrides)
    return result

with tempfile.TemporaryDirectory(prefix='validation-boundary-case-') as directory:
    owned = Path(directory).resolve()
    canonical = owned / 'live-host'
    lazy = canonical / '.lazy-harness'
    scripts = lazy / 'scripts'
    scripts.mkdir(parents=True)
    (lazy / 'manifests').mkdir()
    marker = 'medi' + 'vance'
    (scripts / 'local').mkdir()
    (scripts / 'local/operator.sh').write_text(marker)
    manifest = {'categories': {'A': {'items': [{'path':'scripts/','kind':'directory','glob':['*.ts','*.py']}]}}}
    if case == 'explicit-local': manifest['categories']['A']['items'].append({'path':'scripts/local/','kind':'directory','glob':['*.sh']})
    manifest_file = lazy / 'manifests/init-categories.json'
    manifest_file.write_text(json.dumps(manifest))
    for name in ['framework-runtime-ownership.ts', 'manifest-path-matcher.ts']:
        path = repo / '.lazy-harness/scripts' / name
        if path.exists(): shutil.copyfile(path, scripts / name)
    namespace = dict(pathlib=pathlib, ROOT=canonical, LAZY=lazy, ACTIVE_SCOPE='host', json=json, os=os, shutil=shutil, subprocess=subprocess, tempfile=tempfile, fail=fail, env_without_lazy_runtime=clean_env)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec', flags=__future__.annotations.compiler_flag, dont_inherit=True), namespace)
    output = io.StringIO()
    if case in {'host-local','managed-leak','framework-local','explicit-local','missing-manifest'}:
        if case == 'managed-leak': (scripts / 'managed.py').write_text(marker)
        if case == 'framework-local': namespace['ACTIVE_SCOPE'] = 'framework'
        if case == 'missing-manifest': manifest_file.unlink()
        rejected = None
        try:
            with contextlib.redirect_stdout(output): namespace['check_framework_runtime_no_host_product_hardcoding']()
        except GuardFailure as error: rejected = str(error)
        if case == 'host-local': assert rejected is None, rejected
        else:
            assert rejected is not None, 'ownership failure must remain a failure'
            if case == 'missing-manifest': assert 'ownership' in rejected.lower(), rejected
            if case in {'managed-leak','framework-local','explicit-local'}: assert marker in rejected, rejected
    else:
        # Minimal controlled I/O unit, not a replacement benchmark acceptance run.
        for subdir in ['knowledge','generated','spec/platform','tests','bin','fixtures/tmp','tmp']:
            (lazy / subdir).mkdir(parents=True, exist_ok=True)
        (lazy / 'tmp/broken').symlink_to(owned / 'missing-scratch')
        (lazy / 'fixtures/tmp/keep.txt').write_text('nested canonical input')
        (lazy / 'evidence').mkdir()
        (lazy / 'evidence/keep.md').write_text('canonical evidence input')
        (scripts / 'retrieval-workflow-benchmark.ts').write_text('// controlled unit caller')
        for relative in ['spec/platform/retrieval-workflow-benchmark.md','tests/retrieval-workflow-benchmark.md']:
            shutil.copyfile(repo / '.lazy-harness' / relative, lazy / relative)
        (lazy / 'bin/lazy').write_text('controlled unit command')
        graph = lazy / 'knowledge/graph.jsonl'
        cache = lazy / 'generated/record-index.json'
        graph.write_text('canonical before\n')
        cache.write_text('{"before":true}')
        allocations = []
        real_temporary = tempfile.TemporaryDirectory
        class OwnedTemporary(real_temporary):
            def __enter__(self):
                result = super().__enter__()
                allocations.append(Path(result).resolve())
                return result
        def metric(calls):
            return dict(helperCalls=calls, helperBytes=1, helperEstimatedTokens=1, elapsedMs=1, totalEstimatedTokens=2, candidateCounts=dict(records=1,sources=0,tests=0,graphs=1), followupRead=dict(readCount=1,bytes=1,estimatedTokens=1,coveredLayers={k:True for k in ['DDD','BDD','SDD','TDD','SSOT']}))
        payload = dict(schemaVersion='1.0', mode='retrieval-workflow-benchmark', querySet=['map-first-retrieval','record-source-indexing'], policyBoundary='measurement-only', surfaces=[dict(surfaces=dict(map=metric(1), map_plus_retrieval_audit=metric(2), no_map=metric(1)))], overview=dict(helperBytes=1,helperEstimatedTokens=1,elapsedMs=1), summary=dict(aggregate={k:{} for k in ['map','map_plus_retrieval_audit','no_map']},mapInclusive=dict(helperEstimatedTokens=1,followupEstimatedTokens=1,totalEstimatedTokens=2),deltas={k:dict(helperTokenDelta=0,totalTokenDelta=0) for k in ['mapPlusRetrievalAuditVsMap','noMapVsMap','noMapVsMapInclusive']}))
        def call(args, **kwargs):
            cwd = Path(kwargs.get('cwd', canonical)).resolve()
            observed = cwd / '.lazy-harness'
            if '--format=json' in args:
                if case == 'environment':
                    env = kwargs.get('env', {})
                    assert env.get('LAZY_HOST_ROOT') == str(cwd), 'ambient host root must not control the fixture command'
                    assert cwd != canonical, 'benchmark must run in its own fixture'
                if case == 'external-writer': graph.write_text('unrelated canonical writer\n')
                target = observed / ('generated/record-index.json' if case.startswith('cache-') else 'knowledge/graph.jsonl')
                if case.endswith('-write'):
                    target.write_text('benchmark mutation')
                elif case.endswith('-delete'):
                    target.unlink()
                if cwd != canonical:
                    assert not (observed / 'tmp').exists(), 'root scratch was copied'
                    assert (observed / 'fixtures/tmp/keep.txt').read_text() == 'nested canonical input'
                    assert (observed / 'evidence/keep.md').read_text() == 'canonical evidence input'
                return SimpleNamespace(returncode=0,stdout=json.dumps(payload),stderr='')
            return SimpleNamespace(returncode=0,stdout='measurement-only; does not change lifecycle/prompt/overview policy',stderr='')
        namespace['subprocess'] = SimpleNamespace(run=call, check_output=lambda *args, **kwargs: 'retrieval-workflow-benchmark')
        namespace['tempfile'] = SimpleNamespace(TemporaryDirectory=OwnedTemporary)
        failure = OSError('copy failed')
        if case == 'copy-failure':
            def failed_copy(*args): raise failure
            namespace['copy_harness_fixture'] = failed_copy
        rejected = None
        try:
            with contextlib.redirect_stdout(output): namespace['check_retrieval_workflow_benchmark_cli']()
        except (GuardFailure, OSError) as error: rejected = error
        if case == 'copy-failure':
            assert rejected is failure, 'fixture-copy failure identity must survive'
            assert allocations, 'owned allocation must precede fixture copy'
        elif case in {'graph-write','graph-delete','cache-write','cache-delete'}:
            assert isinstance(rejected, GuardFailure) and 'must not mutate' in str(rejected), str(rejected)
            assert graph.read_text() == 'canonical before\n', 'live graph was mutated instead of the isolated fixture'
            assert cache.read_text() == '{"before":true}', 'live index was mutated instead of the isolated fixture'
        else:
            assert rejected is None, str(rejected)
            assert allocations, 'benchmark must own an isolated allocation'
            if case == 'external-writer': assert graph.read_text() == 'unrelated canonical writer\n', 'must not restore a concurrent writer'
        assert all(not path.exists() for path in allocations), 'owned temporary fixture leaked'
    assert source.read_bytes() == original, 'probe cannot change framework source'
print(json.dumps({'case':case,'ok':True}))
`;

describe('host validation ownership and observation isolation', () => {
  for (const name of cases) {
    test(name, () => {
      const result = spawnSync('python3', ['-c', probe, root, name], { encoding: 'utf8', timeout: 30000 });
      expect(result.status, result.stderr || result.stdout).toBe(0);
      expect(JSON.parse(result.stdout).ok).toBe(true);
    }, 35000);
  }
});


test('real manifest and unmocked isolated benchmark retain actual runtime and CLI contracts', () => {
  const paths = collectRuntimePaths(path.join(root, '.lazy-harness'), 'host');
  expect(paths).toContain('scripts/framework-runtime-ownership.ts');
  expect(paths).toContain('scripts/self-test.py');
  const code = String.raw`
import runpy
import sys
from pathlib import Path
namespace = runpy.run_path(str(Path(sys.argv[1]) / '.lazy-harness/scripts/self-test.py'), run_name='focused_validation_isolation')
for name in ['check_framework_runtime_no_host_product_hardcoding', 'check_harness_fixture_runtime_isolation', 'check_retrieval_workflow_benchmark_cli']:
    check = namespace[name]
    check.__globals__['ACTIVE_SCOPE'] = 'framework'
    check()
`;
  const result = spawnSync('python3', ['-c', code, root], { encoding: 'utf8', timeout: 110000 });
  expect(result.status, result.stderr || result.stdout).toBe(0);
  expect(result.stdout).toContain('retrieval workflow benchmark CLI ok');
}, 120000);
