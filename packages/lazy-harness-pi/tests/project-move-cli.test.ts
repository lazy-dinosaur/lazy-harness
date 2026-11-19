import { expect, test } from 'bun:test';
import { spawn } from 'node:child_process';
import { copyFileSync, mkdtempSync, mkdirSync, readFileSync, realpathSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { createInterface } from 'node:readline';
import { observeOwnedChild } from './fixtures/owned-child.ts';

type Row = { type: string; id?: string; success?: boolean; method?: string; message?: string; error?: string; data?: Record<string, unknown> };
const originalId = 'project-move-original';
const model = 'offline-project-move/scripted';
const proof = 'MOVE_PROOF history=true targetRules=true';
const piRoot = process.env.LAZY_TEST_PI_ROOT ?? resolve(import.meta.dir, '../../../tests/runtime/fabric/node_modules/@earendil-works/pi-coding-agent');
const extension = resolve(import.meta.dir, '../extensions/lazy-harness/index.ts');

for (const entry of ['official CLI', 'slash command', 'model tool', 'cancelled switch'] as const) {
  const title = entry === 'cancelled switch'
    ? 'cancelled switch leaves the original Pi session active and never reports success'
    : `${entry} copies conversation, rebinds target cwd and rules, and retains the source`;
  test(title, async () => {
    const sandbox = realpathSync(mkdtempSync(join(tmpdir(), 'lazy-pi-project-move-')));
    const source = join(sandbox, 'source'), target = join(sandbox, 'target project'), agent = join(sandbox, 'agent');
    const original = join(sandbox, 'original.jsonl');
    const now = new Date().toISOString();
    const seed = [
      { type: 'session', version: 3, id: originalId, timestamp: now, cwd: source },
      { type: 'message', id: 'abc00001', parentId: null, timestamp: now, message: { role: 'user', content: 'original conversation marker', timestamp: Date.now() } },
    ].map(row => JSON.stringify(row)).join('\n') + '\n';
    for (const [root, marker] of [[source, 'SOURCE'], [target, 'TARGET']]) {
      mkdirSync(join(root, '.lazy-harness/bin'), { recursive: true });
      writeFileSync(join(root, '.lazy-harness/bin/lazy'), '#!/bin/sh\n', { mode: 0o755 });
      writeFileSync(join(root, 'AGENTS.md'), `${marker}_RULE_MARKER\n`);
      writeFileSync(join(root, 'marker.txt'), `${marker}_TOOL_MARKER\n`);
    }
    mkdirSync(agent);
    mkdirSync(join(sandbox, 'home'));
    const provider = join(agent, 'provider.ts');
    copyFileSync(join(import.meta.dir, 'fixtures/project-move-provider.ts'), provider);
    symlinkSync(dirname(dirname(piRoot)), join(agent, 'node_modules'));
    writeFileSync(join(agent, 'settings.json'), JSON.stringify({ extensions: [provider, ...(entry === 'official CLI' ? [] : [extension])], defaultProjectTrust: 'always', compaction: { enabled: false }, retry: { enabled: false } }));
    writeFileSync(original, seed);
    const child = spawn(process.env.LAZY_TEST_NODE ?? 'node', [join(piRoot, 'dist/cli.js'), '--offline', '--approve', '--mode', 'rpc', '--model', model, '--thinking', 'off', entry === 'official CLI' ? '--fork' : '--session', original], {
      cwd: entry === 'official CLI' ? target : source, detached: true,
      env: { PATH: process.env.PATH, HOME: join(sandbox, 'home'), PI_CODING_AGENT_DIR: agent, PI_OFFLINE: '1', MOVE_FIXTURE_TARGET: target, MOVE_FIXTURE_CANCEL: entry === 'cancelled switch' ? '1' : '0', NO_COLOR: '1' },
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    const supervision = observeOwnedChild(child);
    const rows: Row[] = [];
    let stderr = '';
    child.stderr.on('data', data => { stderr += data.toString(); });
    child.stdin.on('error', () => {});
    const lines = createInterface({ input: child.stdout });
    let listener: (() => void) | undefined;
    lines.on('line', line => {
      try { rows.push(JSON.parse(line)); } catch { stderr += `\nNon-JSON output: ${line}`; }
      listener?.();
    });
    const wait = (predicate: (row: Row) => boolean) => new Promise<Row>((finish, reject) => {
      const timer = setTimeout(() => {
        listener = undefined;
        const recent = rows.slice(-12).map(row => JSON.stringify(row).slice(0, 500));
        reject(new Error(`Pi response missing (${entry})\n${stderr.slice(-2000)}\n${recent.join('\n')}`));
      }, 10000);
      listener = () => {
        const match = rows.find(predicate);
        if (match) { clearTimeout(timer); listener = undefined; finish(match); }
      };
      listener();
    });
    let id = 0;
    const rpc = async (type: string, args: Record<string, unknown> = {}) => {
      const request = String(++id);
      child.stdin.write(JSON.stringify({ id: request, type, ...args }) + '\n');
      const row = await wait(event => event.type === 'response' && event.id === request);
      expect(row.success, JSON.stringify(row)).toBe(true);
      return row.data;
    };
    try {
      let originalBeforeHandoff = seed;
      if (entry !== 'official CLI') {
        expect((await rpc('get_state'))?.sessionId).toBe(originalId);
        originalBeforeHandoff = readFileSync(original, 'utf8');
        await rpc('prompt', { message: entry === 'model tool' ? 'move through the tool' : `/lazy-move "${target}"` });
      }
      if (entry === 'cancelled switch') {
        expect((await rpc('get_state'))?.sessionId).toBe(originalId);
        expect(readFileSync(original, 'utf8')).toBe(originalBeforeHandoff);
        expect(rows.some(row => row.method === 'notify' && row.message?.includes('Move cancelled'))).toBe(true);
        expect(rows.some(row => row.method === 'notify' && row.message?.includes('Continued the conversation'))).toBe(false);
        return;
      }
      if (entry !== 'model tool') await rpc('prompt', { message: 'inspect workspace' });
      const response = await wait(row => row.type === 'message_end' && JSON.stringify(row.message).includes(proof));
      await wait(row => row.type === 'agent_settled' && rows.indexOf(row) > rows.indexOf(response));
      const state = await rpc('get_state');
      expect(state?.sessionId).not.toBe(originalId);
      const forkFile = state?.sessionFile;
      if (typeof forkFile !== 'string') throw new Error('Pi did not persist the target session');
      const header = JSON.parse(readFileSync(forkFile, 'utf8').split('\n')[0]);
      expect(header.cwd).toBe(target);
      expect(header.parentSession).toBe(original);
      expect((await rpc('bash', { command: 'cat marker.txt', excludeFromContext: true }))?.output).toContain('TARGET_TOOL_MARKER');
      const retained = readFileSync(original, 'utf8');
      if (entry === 'model tool') {
        expect(retained.startsWith(originalBeforeHandoff)).toBe(true);
        expect(retained).toContain('Queued conversation copy');
        expect(retained).not.toContain(proof);
      } else expect(retained).toBe(originalBeforeHandoff);
      expect(rows.filter(row => row.type === 'extension_error')).toEqual([]);
    } finally {
      lines.close();
      await supervision.settle();
      rmSync(sandbox, { recursive: true, force: true });
    }
  }, 40000);
}
