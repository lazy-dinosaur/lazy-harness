import { expect, test } from 'bun:test';
import { readFileSync, mkdtempSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { resolve, join } from 'node:path';
import { tmpdir } from 'node:os';

const root = resolve(import.meta.dir, '../..');
test('historical native matrix is retained byte-for-byte below its classification header', () => {
  const text = readFileSync(resolve(root, 'packages/lazy-harness-pi/tests/reader-primary-answer-cli.legacy.fixture.ts'));
  const body = text.subarray(text.indexOf(10) + 1);
  expect(createHash('sha1').update(`blob ${body.length}\0`).update(body).digest('hex')).toBe('16c4aae32ed18ab76e9f01c2bae8f94e466014a5');
});
test('affected test:run forwards a concrete target without discovering historical or Node-only suites', () => {
  const result = spawnSync('node', ['scripts/test-runner.mjs', 'tests/lazy-harness/affected/covered.test.ts'], { cwd: root, encoding: 'utf8', timeout: 30000 });
  expect(result.status, result.stderr).toBe(0);
  expect(result.stdout).toContain('1 passed');
  expect(result.stderr).not.toContain('native package paths');
});


function observeRouting(args: string[]) {
  const temporary = mkdtempSync(join(tmpdir(), 'test-route-observer-'));
  try {
    const trace = join(temporary, 'calls.jsonl');
    const preload = join(temporary, 'observe.cjs');
    writeFileSync(preload, `const cp=require('node:child_process');const fs=require('node:fs');cp.spawnSync=(command,args)=>{fs.appendFileSync(${JSON.stringify(trace)},JSON.stringify({command,args})+'\\n');return {status:0}};require('node:module').syncBuiltinESMExports();`);
    const result = spawnSync('node', ['--require', preload, 'scripts/test-runner.mjs', ...args], { cwd: root, encoding: 'utf8', timeout: 10000 });
    const calls: { command: string; args: string[] }[] = existsSync(trace) ? readFileSync(trace, 'utf8').trim().split('\n').filter(Boolean).map(line => JSON.parse(line)) : [];
    return { result, calls };
  } finally { rmSync(temporary, { recursive: true, force: true }); }
}
const sdk = 'tests/lazy-harness/pi-capture-evidence.test.ts';
const bun = 'tests/lazy-harness/affected/covered.test.ts';
for (const sdkPath of [sdk, './' + sdk, resolve(root, sdk), sdk.replaceAll('/', '\\')]) {
  test(`mixed targets partition the Node-only file: ${sdkPath}`, () => {
    const { result, calls } = observeRouting([sdkPath, bun]);
    expect(result.status, result.stderr).toBe(0);
    expect(calls).toHaveLength(2);
    expect(calls.find(call => call.command === 'bun')?.args).toEqual(['test', bun]);
    expect(calls.find(call => call.command !== 'bun')?.args).toContain('scripts/test-pi-capture.mjs');
  });
}
test('Node target plus pattern options stays on Node with translated flags', () => {
  const { result, calls } = observeRouting([sdk, '-t', 'typed evidence boundary']);
  expect(result.status, result.stderr).toBe(0);
  expect(calls).toHaveLength(1);
  expect(calls[0]?.args).toEqual(['scripts/test-pi-capture.mjs', '--capture-only', '--test-name-pattern', 'typed evidence boundary']);
});
test('mixed lanes receive their own shared pattern flags', () => {
  const { result, calls } = observeRouting(['--', sdk, bun, '--test-name-pattern=boundary']);
  expect(result.status, result.stderr).toBe(0);
  expect(calls.find(call => call.command === 'bun')?.args).toEqual(['test', '-t', 'boundary', bun]);
  expect(calls.find(call => call.command !== 'bun')?.args).toContain('boundary');
});
test('directory selection cannot send the Node SDK fixture through Bun', () => {
  const { result, calls } = observeRouting(['tests/lazy-harness', '-t', 'boundary']);
  expect(result.status, result.stderr).toBe(0);
  expect(calls).toHaveLength(2);
  expect(calls.find(call => call.command === 'bun')?.args).not.toContain(sdk);
});
test('Bun-only timeout is forwarded, but a Node lane rejects it before any engine runs', () => {
  const onlyBun = observeRouting([bun, '--timeout', '1234']);
  expect(onlyBun.result.status).toBe(0);
  expect(onlyBun.calls[0]?.args).toEqual(['test', '--timeout', '1234', bun]);
  const mixed = observeRouting([sdk, bun, '--timeout', '1234']);
  expect(mixed.result.status).not.toBe(0);
  expect(mixed.result.stderr).toContain('unsupported for the Node lane');
  expect(mixed.calls).toHaveLength(0);
});


test('real mixed Node/Bun targets honor a shared name filter in their actual engines', () => {
  const result = spawnSync('node', ['scripts/test-runner.mjs', sdk, bun, '-t', 'typed evidence boundary|increments by one'], { cwd: root, encoding: 'utf8', timeout: 30000 });
  expect(result.status, result.stderr + result.stdout).toBe(0);
  expect(result.stdout).toContain('typed evidence boundary');
  expect(result.stderr).toContain('increments by one');
  expect(result.stdout).toContain('1 passed');
}, 35000);
