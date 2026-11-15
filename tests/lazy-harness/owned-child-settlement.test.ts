import { expect, test } from 'bun:test';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { observeOwnedChild } from '../../packages/lazy-harness-pi/tests/fixtures/owned-child.ts';

function fixture(code: string, termMs = 80, killMs = 1500) {
  const child = spawn('node', ['-e', code], { stdio: ['ignore', 'pipe', 'pipe'] });
  const signals: (NodeJS.Signals | number | undefined)[] = [];
  const kill = child.kill.bind(child);
  child.kill = signal => {
    expect(child.exitCode).toBeNull(); expect(child.signalCode).toBeNull();
    signals.push(signal); return kill(signal);
  };
  return { child, signals, owner: observeOwnedChild(child, { termMs, killMs }) };
}

test('normally closed child receives no termination signal', async () => {
  const f = fixture('process.exit(0)');
  expect(await f.owner.waitForClose(3000)).toBe(0);
  expect(await f.owner.settle()).toEqual([]);
  expect(f.signals).toEqual([]);
});
test('deadline preserves failure, TERM stops a live owned child, then physically closes', async () => {
  const f = fixture("process.on('SIGTERM',()=>process.exit(0));console.log('ready');setInterval(()=>{},1000)");
  await once(f.child.stdout, 'data');
  await expect(f.owner.waitForClose(15)).rejects.toThrow('deadline');
  expect(await f.owner.settle()).toEqual(['SIGTERM']);
  expect(f.owner.closed).toBe(true);
  expect(f.signals).toEqual(['SIGTERM']);
});
test('ignored TERM escalates only the same still-live child to KILL and awaits close', async () => {
  const f = fixture("process.on('SIGTERM',()=>{});console.log('ready');setInterval(()=>{},1000)", 50);
  await once(f.child.stdout, 'data');
  expect(await f.owner.settle()).toEqual(['SIGTERM', 'SIGKILL']);
  expect(f.owner.closed).toBe(true);
  expect(f.child.signalCode).toBe('SIGKILL');
});
test('already exited parent with a briefly inherited pipe is awaited but never signalled', async () => {
  const f = fixture("require('node:child_process').spawn(process.execPath,['-e','setTimeout(()=>{},200)'],{stdio:['ignore',1,2]});process.exit(0)", 1500);
  await once(f.child, 'exit');
  expect(await f.owner.settle()).toEqual([]);
  expect(f.owner.closed).toBe(true);
  expect(f.signals).toEqual([]);
});
test('unsettled inherited pipe fails closed without signalling an exited PID', async () => {
  const f = fixture("require('node:child_process').spawn(process.execPath,['-e','setTimeout(()=>{},350)'],{stdio:['ignore',1,2]});process.exit(0)", 20, 20);
  await once(f.child, 'exit');
  await expect(f.owner.settle()).rejects.toThrow('physically close');
  expect(f.signals).toEqual([]);
  await f.owner.waitForClose(2500);
});
test('spawn error is observed without a signal or unhandled rejection', async () => {
  const child = spawn('/missing-owned-fixture-executable', [], { stdio: 'ignore' });
  const owner = observeOwnedChild(child, { termMs: 20, killMs: 20 });
  await expect(owner.waitForClose(1000)).rejects.toThrow();
  expect(await owner.settle()).toEqual([]);
  expect(owner.closed).toBe(true);
});
