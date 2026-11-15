import { expect } from 'bun:test';
import { execFileSync, spawn } from 'node:child_process';
import { cpSync, existsSync, mkdtempSync, mkdirSync, readFileSync, realpathSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { fabricReaderLedgerPath } from '../../extensions/lazy-harness/fabric-reader.ts';
import { observeOwnedChild } from './owned-child.ts';

export interface FabricScenario { order: 'wait-first' | 'source-first'; mode: 'json' | 'text'; advisory: 'capture' | 'placement'; trusted: boolean }
interface TraceRow { event: string; at: number; pid: number; sessionId?: string; sessionFile?: string; result?: { toolName: string; input?: Record<string, unknown>; isError?: boolean; details?: Record<string, unknown> }; messages?: { role: string; content: unknown }[] }
const host = resolve(import.meta.dir, '../../../..');
const rowsFrom = (path: string): TraceRow[] => readFileSync(path, 'utf8').split('\n').filter(Boolean).map(line => JSON.parse(line));
const record = (value: unknown): Record<string, unknown> => value !== null && typeof value === 'object' ? value as Record<string, unknown> : {};

export async function runFabricScenario(scenario: FabricScenario): Promise<void> {
  const runtime = join(host, 'tests/runtime/fabric/node_modules');
  const piRoot = process.env.LAZY_TEST_PI_ROOT ?? join(runtime, '@earendil-works/pi-coding-agent');
  const fabricRoot = process.env.LAZY_TEST_FABRIC_ROOT ?? join(runtime, 'pi-fabric');
  for (const [root, version] of [[piRoot, '1.5.2'], [fabricRoot, '0.136.0']]) {
    if (!existsSync(join(root, 'package.json'))) throw new Error('Missing pinned current runtime. Run bun run test:fabric:setup; legacy native paths are not substitutes.');
    expect(JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')).version).toBe(version);
  }
  const canonicalTmp = realpathSync(tmpdir());
  const sandbox = realpathSync(mkdtempSync(join(canonicalTmp, 'fabric-reader-cli-')));
  const root = join(sandbox, 'host'), agent = join(sandbox, 'agent'), trace = join(sandbox, 'trace.jsonl');
  let child: ReturnType<typeof spawn> | undefined;
  let stdout = '', stderr = '';
  let supervision: ReturnType<typeof observeOwnedChild> | undefined;
  let hadFailure = false;
  let passed = false;
  try {
    execFileSync('git', ['clone', '--quiet', '--shared', '--no-checkout', host, root]);
    for (const dir of ['.lazy-harness/bin', '.lazy-harness/spec', '.pi']) mkdirSync(join(root, dir), { recursive: true });
    mkdirSync(agent); mkdirSync(join(sandbox, 'home'));
    cpSync(join(host, '.lazy-harness/hooks/lifecycle'), join(root, '.lazy-harness/hooks/lifecycle'), { recursive: true });
    for (const helper of ['on-response-completed.sh', 'helpers/check-analysis-discovery-capture.sh', 'helpers/check-project-rule-placement.sh']) expect(readFileSync(join(root, '.lazy-harness/hooks/lifecycle', helper))).toEqual(readFileSync(join(host, '.lazy-harness/hooks/lifecycle', helper)));
    writeFileSync(join(root, '.lazy-harness/bin/lazy'), '#!/bin/sh\nprintf "fixture-fact: .lazy-harness/spec/fact.md\\n"\n', { mode: 0o755 });
    writeFileSync(join(root, '.lazy-harness/spec/fact.md'), 'canonical fact: delivery matters\n');
    writeFileSync(join(root, '.lazy-harness/spec/second.md'), 'canonical second fact: keep successful reads\n');
    writeFileSync(join(root, 'source.txt'), 'Parent independent source\n');
    const revision = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
    const provider = join(agent, 'offline-provider.ts');
    cpSync(join(import.meta.dir, 'fabric-reader-provider.ts'), provider);
    symlinkSync(dirname(dirname(piRoot)), join(agent, 'node_modules'));
    writeFileSync(join(agent, 'settings.json'), JSON.stringify({ extensions: [provider], defaultProjectTrust: scenario.trusted ? 'always' : 'never', compaction: { enabled: false }, retry: { enabled: false } }));
    writeFileSync(join(agent, 'auth.json'), '{}');
    writeFileSync(join(root, '.pi/settings.json'), JSON.stringify({ packages: [fabricRoot, join(host, 'packages/lazy-harness-pi')] }));
    writeFileSync(trace, '');
    const env = { PATH: process.env.PATH, TMPDIR: canonicalTmp, HOME: join(sandbox, 'home'), PI_CODING_AGENT_DIR: agent, PI_OFFLINE: '1', FABRIC_READER_TEST_ROOT: root, FABRIC_READER_TEST_TRACE: trace, FABRIC_READER_TEST_REVISION: revision, FABRIC_READER_TEST_ORDER: scenario.order, FABRIC_READER_TEST_ADVISORY: scenario.advisory, FABRIC_READER_TEST_TRUST: String(scenario.trusted), NATIVE_READER_TRACE: trace, NODE_OPTIONS: `--import=${join(import.meta.dir, 'native-reader-network-guard.mjs')}`, TERM: 'dumb', NO_COLOR: '1' };
    child = spawn(process.env.LAZY_TEST_NODE ?? 'node', [join(piRoot, 'dist/cli.js'), '--offline', '--approve', '--print', '--mode', scenario.mode, '--model', 'offline-fabric-reader/scripted', '--thinking', 'low', '--no-skills', '--no-context-files', '--no-prompt-templates', '--no-themes', '--system-prompt', 'OFFLINE FABRIC PARENT: read source independently and join Reader before answering.', 'Inspect delivery rule.'], { cwd: root, env, detached: true, stdio: ['ignore', 'pipe', 'pipe'] });
    supervision = observeOwnedChild(child);
    child.stdout?.on('data', data => { stdout += data; }); child.stderr?.on('data', data => { stderr += data; });
    const exit = await supervision.waitForClose(100000);
    expect(exit, stderr + '\n' + stdout.slice(-1500)).toBe(0);
    const rows = rowsFrom(trace);
    expect(rows.filter(row => ['network-denied', 'script-error', 'unwanted-continuation'].includes(row.event))).toEqual([]);
    const start = rows.find(row => row.event === 'reader-start');
    const end = rows.find(row => row.event === 'reader-end');
    expect(start).toBeDefined(); expect(end).toBeDefined();
    const sourceRead = rows.find(row => row.event === 'parent-tool' && row.result?.toolName === 'read');
    expect(sourceRead).toBeDefined();
    if (scenario.order === 'source-first') expect(sourceRead?.at).toBeLessThan(end?.at ?? 0);
    else expect(sourceRead?.at).toBeGreaterThanOrEqual(end?.at ?? Infinity);
    const joined = rows.find(row => row.event === 'parent-tool' && row.result?.toolName === 'lazy_reader_join')?.result;
    expect(joined?.isError).toBe(!scenario.trusted);
    if (scenario.trusted) {
      expect(joined?.details?.joined).toBe(true);
      expect(joined?.details?.recordCount).toBe(2);
      expect(joined?.input?.recordPaths).toEqual(['.lazy-harness/spec/fact.md']);
      const launch = rows.find(row => row.event === 'parent-tool' && row.result?.toolName === 'agents.spawn');
      const id = record(launch?.result?.details?.result).id;
      expect(typeof id).toBe('string');
      if (typeof id !== 'string') throw new Error('Missing actual Fabric run id');
      const ledgerRows = readFileSync(fabricReaderLedgerPath(root, id), 'utf8').split('\n').filter(Boolean).map(line => JSON.parse(line));
      const ledger = ledgerRows.at(-1)?.data;
      expect(ledger).toMatchObject({ fabricRunId: id, root, revision, evidenceEpoch: 1, sessionId: start?.sessionId, terminal: true, readCalls: 2, requestedLines: 400, maxObservedReadLimit: 200, failedToolCalls: 0 });
      expect(Object.keys(ledger.recordHashes)).toEqual(['.lazy-harness/spec/fact.md', '.lazy-harness/spec/second.md']);
      expect(ledger.readerPolicy).toMatchObject({ systemPromptMode: 'replace', inheritProjectContext: false, inheritSkills: false, context: 'fresh', output: false, maxTurns: 12, graceTurns: 2, turnBudgetExceeded: false });
      for (const claim of ['CLAIM-1', 'CLAIM-2', 'CLAIM-3', 'CLAIM-4']) expect(stdout).toContain(claim);
      const final = rows.filter(row => row.event === 'parent-end').at(-1);
      expect(final?.at).toBeGreaterThanOrEqual(end?.at ?? Infinity);
      const sessionFile = final?.sessionFile;
      if (!sessionFile) throw new Error('Missing real Parent session file');
      const sessionRows = readFileSync(sessionFile, 'utf8').split('\n').filter(Boolean).map(line => JSON.parse(line));
      const capture = sessionRows.filter(row => row.type === 'custom' && row.customType === 'lazy-harness-capture').at(-1);
      expect(capture?.data).toMatchObject({ root, epoch: 1, status: 'unverified', semanticStatus: 'llm-judgement-not-verified', approvalStatus: 'not-evaluated' });
      expect(sessionRows.filter(row => row.type === 'custom_message' && row.customType === 'lazy-harness-capture')).toEqual([]);
      if (scenario.advisory === 'placement') { expect(stderr).toContain('Project rule placement gate'); expect(stderr).toContain('primary stdout preserved'); }
      rmSync(fabricReaderLedgerPath(root, id), { force: true });
    } else {
      expect(joined?.details?.joined).not.toBe(true);
      expect(stdout).toContain('Rejected unsafe Reader join');
      expect(stdout).not.toContain('Substantive answer:');
    }
    expect(stdout).not.toContain('Partial replacement');
    expect(stderr).not.toContain('Analysis discovery capture gate');
    expect(rows.filter(row => ['write', 'edit', 'multiedit'].includes(row.result?.toolName ?? ''))).toEqual([]);
    expect(readFileSync(join(root, '.lazy-harness/spec/fact.md'), 'utf8')).toBe('canonical fact: delivery matters\n');
    expect(readFileSync(join(root, '.lazy-harness/spec/second.md'), 'utf8')).toBe('canonical second fact: keep successful reads\n');
    expect(existsSync(join(root, '.lazy-harness/knowledge/candidates.jsonl'))).toBe(false);
    passed = true;
  } catch (error) { hadFailure = true; console.error(`Fabric fixture preserved: ${sandbox}\n${stderr}\n${stdout.slice(-2000)}`); throw error; }
  finally {
    try { await supervision?.settle(); }
    catch (error) {
      passed = false;
      console.error(`Owned Parent did not settle; fixture preserved: ${sandbox}`, error);
      if (!hadFailure) throw error;
    }
    if (passed) rmSync(sandbox, { recursive: true, force: true });
  }
}
