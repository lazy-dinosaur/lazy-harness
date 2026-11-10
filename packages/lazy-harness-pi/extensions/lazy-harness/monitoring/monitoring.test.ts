/// <reference types="bun" />
import { expect, test } from 'bun:test';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  evaluateReadRecordSnapshot, runReadRecordPortConformance, syntheticInputPortContext,
  syntheticReadRecord, syntheticReadRequest, validateRequiredInputPorts,
  type InputPortContext, type ReadRecord, type ReadRecordConformanceFactory,
} from '@lazy-harness/monitoring-core/host';
import { CaptureEvidence } from '../capture-evidence.ts';
import { createHash } from 'node:crypto';
import { createReadResultAttestor, type MainReadCall, type MainReadResult, type ReadTextFormat } from './read-attestation.ts';
import { createHarnessReadRecordPort, type ExposureEvidenceKind } from './read-record-port.ts';
import { createHarnessReferences, type HarnessReferencesBindings } from './references.ts';

function evidence(r: ReadRecord, kind: ExposureEvidenceKind = r.exposure.kind === 'full' ? 'context-full-record' : 'context-partial-record') {
  const { exposure, ...record } = r;
  return { record, evidenceKind: kind, attestationId: exposure.attestationId };
}
const factory: ReadRecordConformanceFactory = (context, options) => {
  const adapter = createHarnessReadRecordPort({ context, ...options });
  return { port: adapter.port, record: r => adapter.recordEvidence(evidence(r)), close: adapter.close };
};
test('harness adapter passes official five-group version-aware read port conformance', async () => {
  expect(await runReadRecordPortConformance(factory)).toEqual([
    'exact-version/replay/mutation', 'scope-fencing/no-carry/immutable',
    'freshness/cancellation/unavailable', 'partial/count-and-byte-bounds', 'delayed-race/single-flight/close',
  ]);
});
for (const kind of ['tool-success-only', 'reader-joined-fingerprint', 'tool-result-text-runtime-file'] as const) {
  test(`${kind} cannot become a full read or suppress a document`, async () => {
    const context = syntheticInputPortContext(), a = createHarnessReadRecordPort({ context: () => context });
    try {
      expect(a.recordEvidence(evidence(syntheticReadRecord(context), kind))).toBe(true);
      const request = syntheticReadRequest(context), snapshot = await a.port.snapshot(request);
      expect(snapshot.records[0].exposure.kind).toBe('unknown');
      expect(evaluateReadRecordSnapshot(request, snapshot)[0].status).toBe('not-read');
    } finally { a.close(); }
  });
}

test('existing CaptureEvidence read receipts adapt honestly; root, epoch, scope and writes fail closed', async () => {
  const root = mkdtempSync(join(tmpdir(), 'monitoring-invented-'));
  const path = '.lazy-harness/spec/lantern.md', input = { path };
  mkdirSync(join(root, '.lazy-harness/spec'), { recursive: true });
  writeFileSync(join(root, path), '# Invented lantern\nUse blue glass.\n');
  let context: InputPortContext = syntheticInputPortContext();
  const identity = { root, epoch: 3 }, capturedScope = context.scope;
  const a = createHarnessReadRecordPort({ context: () => context, captureIdentity: () => identity });
  try {
    const source = new CaptureEvidence();
    source.start(root, root, 3, 'invented-read', 'read', input);
    // Real source accepts nonempty text, even a truncated/error-looking body.
    // Therefore its runtime-file hash does NOT attest full exposure.
    source.complete(root, root, 3, 'invented-read', 'read', input, false, [{ type: 'text', text: 'Use blue...' }]);
    const judgement = '\n<record-judgement>\n' + JSON.stringify({ disposition: 'reuse', reason: 'invented fixture', facts: [{ path, fact: 'Invented lantern.' }] }) + '\n</record-judgement>';
    const capture = source.evaluate(root, 3, judgement);
    expect(capture.status).toBe('evidence-linked');
    const catalog = { resolve(p: string, hash: string) { return p === path && hash === capture.facts[0].receipt!.sha256 ? { documentId: 'synthetic-doc', documentVersion: 'v1' } : undefined; } };
    expect(a.ingestCapture(capture, 2, catalog, capturedScope)).toBe(1);
    expect(a.exposureEvidenceKind).toBe('tool-result-text-runtime-file');
    const snapshot = await a.port.snapshot(syntheticReadRequest(context));
    expect(snapshot.records[0].exposure).toEqual({ kind: 'unknown', attestationId: 'invented-read' });
    expect(evaluateReadRecordSnapshot(syntheticReadRequest(context), snapshot)[0].status).toBe('not-read');
    expect(a.ingestCapture({ ...capture, root: root + '-other' }, 2, catalog, capturedScope)).toBe(0);
    expect(a.ingestCapture({ ...capture, epoch: 4 }, 2, catalog, capturedScope)).toBe(0);
    expect(a.ingestCapture(capture, 2, { resolve: () => undefined }, capturedScope)).toBe(0);
    expect(a.ingestCapture({ ...capture, judgement: { ...capture.judgement!, disposition: 'required' } }, 2, catalog, capturedScope)).toBe(0);
    context = { ...context, scope: { ...context.scope, compactionGeneration: 1 } };
    expect(a.ingestCapture(capture, 2, catalog, capturedScope)).toBe(0);
    expect((await a.port.snapshot(syntheticReadRequest(context))).records).toHaveLength(0);
    writeFileSync(join(root, path), '# Changed invented lantern\n');
    expect(source.evaluate(root, 3, judgement).status).toBe('unverified');
  } finally { a.close(); rmSync(root, { recursive: true, force: true }); }
});

const bindings = (): HarnessReferencesBindings => ({
  catalog: { resolve: () => ({ documentId: 'synthetic-doc', documentVersion: 'v1' }) },
  context: () => { const { scope, ...context } = syntheticInputPortContext(); return context; },
  captureIdentity: () => ({ root: 'invented-root', epoch: 1 }),
});
function attach(c: ReturnType<typeof createHarnessReferences>) {
  const hooks = new Map<string, (event: unknown, ctx: unknown) => void>();
  c.extension({ on(name, handler) { hooks.set(name, handler); } });
  const ctx = { sessionManager: { getSessionId: () => 'synthetic-session', getLeafId: () => 'synthetic-branch' } };
  hooks.get('session_start')!({}, ctx);
  return { hooks, ctx };
}
test('composition preflight requires bindings and official port validation fails closed', () => {
  expect(() => createHarnessReferences({ bindings: undefined! })).toThrow('bindings');
  expect(() => createHarnessReferences({ bindings: { ...bindings(), catalog: undefined! } })).toThrow('bindings');
  const c = createHarnessReferences({ bindings: bindings() });
  try {
    expect(() => validateRequiredInputPorts(c.registration.moduleId, c.registration.declaration.needs, c.inputPorts)).not.toThrow();
    expect(() => validateRequiredInputPorts(c.registration.moduleId, c.registration.declaration.needs)).toThrow();
    expect(() => validateRequiredInputPorts(c.registration.moduleId, c.registration.declaration.needs, {
      'context.references': { 'already-read': { adapter: 'session.read-records', protocolVersion: 1, port: {} } },
    })).toThrow();
    expect(c.generations.current()).toBeUndefined(); // Construction attached nothing.
  } finally { c.close(); }
});
test('default observe never runs delivery or emits reports, even with explicit trigger and report sink', async () => {
  const reports: unknown[] = [];
  const c = createHarnessReferences({ bindings: bindings(), report(r) { reports.push(r); throw Error('must not report'); } });
  try {
    const { hooks, ctx } = attach(c);
    expect(hooks.has('input')).toBe(false);
    expect(hooks.has('context_with_system')).toBe(false);
    expect(c.registration.stage).toBe('observe');
    c.runtime.start();
    const outcomes = await c.runtime.onTrigger({ moduleId: 'context.references', sessionId: 'synthetic-session', eventId: 'invented-trigger',
      evidence: [{ id: 'synthetic-doc', kind: 'knowledge', version: 'v1', text: 'Invented lantern.' }] });
    expect(outcomes).toHaveLength(1);
    expect(outcomes[0].reason).toBe('stage:observe');
    expect(outcomes[0].reported).toBe(false);
    expect(reports).toEqual([]);
    const before = c.generations.current()!;
    hooks.get('session_before_compact')!({}, ctx);
    expect(c.generations.current()).toBeUndefined();
    hooks.get('session_compact')!({}, ctx);
    expect(c.generations.current()!.compactionGeneration).toBeGreaterThan(before.compactionGeneration);
  } finally { await c.runtime.idle(); c.close(); }
});
test('live extension entry does not activate the new composition', () => {
  const entry = readFileSync(new URL('../index.ts', import.meta.url), 'utf8');
  expect(entry).not.toContain('./monitoring/');
  expect(entry).not.toContain('createHarnessReferences');
});

// All contents, identifiers and event bodies below are invented; no live transcript.
function attestationFixture(format: ReadTextFormat = 'pi-read-text-v1', text = 'Invented lantern\nBlue glass.') {
  const root = mkdtempSync(join(tmpdir(), 'monitoring-attestation-'));
  const path = '.lazy-harness/spec/lantern.md';
  mkdirSync(join(root, '.lazy-harness/spec'), { recursive: true });
  writeFileSync(join(root, path), text);
  let context: InputPortContext = syntheticInputPortContext(), epoch = 1;
  const adapter = createHarnessReadRecordPort({ context: () => context, captureIdentity: () => ({ root, epoch }) });
  const catalog = { resolve(p: string, hash: string) {
    return p === path ? { documentId: 'synthetic-doc', documentVersion: hash } : undefined;
  } };
  const producer = createReadResultAttestor({ context: () => context, captureIdentity: () => ({ root, epoch }),
    format: () => format, catalog, record: adapter.recordEvidence });
  let serial = 0;
  const call = (input: Partial<MainReadCall['input']> = {}): MainReadCall => ({
    toolCallId: `invented-read-${++serial}`, toolName: 'read', input: { path, ...input },
  });
  const result = (c: MainReadCall, body = text, extra: Partial<MainReadResult> = {}): MainReadResult => ({
    ...c, isError: false, content: [{ type: 'text', text: body }], ...extra,
  });
  return { root, path, adapter, producer, catalog, call, result,
    context: () => context,
    changeContext(next: InputPortContext) { context = next; },
    bumpEpoch() { epoch++; },
    write(value: string | Uint8Array) { writeFileSync(join(root, path), value); },
    async feed(body = text, input: Partial<MainReadCall['input']> = {}, extra: Partial<MainReadResult> = {}) {
      const c = call(input);
      expect(producer.start(c, root, 'main-agent')).toBe(true);
      expect(producer.complete(result(c, body, extra), root, 'main-agent', 2)).toBe(true);
      return (await adapter.port.snapshot(syntheticReadRequest(context))).records.at(-1)!;
    },
    close() { producer.close(); adapter.close(); rmSync(root, { recursive: true, force: true }); },
  };
}

test('stage-1 exact plain result hashes bytes and binds document identity and current scope', async () => {
  const f = attestationFixture('pi-read-text-v1', 'Invented\r\nlantern.\n');
  try {
    const r = await f.feed();
    const hash = createHash('sha256').update('Invented\r\nlantern.\n').digest('hex');
    expect(r.documentVersion).toBe(hash);
    expect(r.sourceRecordRevision).toBe(hash);
    expect(r.sourceRecordId).toBe(f.path);
    expect(r.scope).toEqual(f.context().scope);
    expect(r.exposure.kind).toBe('full');
    expect(r.exposure.attestationId).toMatch(/^tool-result-full-text:[0-9a-f]{64}$/);
    expect((await f.feed(undefined, { offset: 1, limit: 100 })).exposure.kind).toBe('full');
  } finally { f.close(); }
});

test('numeric range proves partial only; whole-result text cannot override a subset request', async () => {
  const f = attestationFixture();
  try {
    expect((await f.feed('Blue glass.', { offset: 2, limit: 1 })).exposure.kind).toBe('partial');
    expect((await f.feed('Invented lantern', { limit: 1 })).exposure.kind).toBe('partial');
    expect((await f.feed(undefined, { offset: 2, limit: 1 })).exposure.kind).toBe('unknown');
    expect((await f.feed(undefined, { offset: 'abcde' })).exposure.kind).toBe('unknown');
    expect((await f.feed(undefined, { offset: 0 })).exposure.kind).toBe('unknown');
  } finally { f.close(); }
});

test('hashline strips only five lowercase letters plus U+2502, preserves payload bytes', async () => {
  const f = attestationFixture('pi-hashline-edit-pro-v1', '  Invented│lantern\n\nBlue glass.  ');
  try {
    expect((await f.feed('abcde│  Invented│lantern\nfghij│\nklmno│Blue glass.  ')).exposure.kind).toBe('full');
    expect((await f.feed('abcde│  Invented│lantern\nfghij│\nklmno│Blue glass.  ', { offset: 1, limit: 3 })).exposure.kind).toBe('full');
    for (const body of ['1:abcde│  Invented│lantern', 'ABCDe│  Invented│lantern', 'abcdef│  Invented│lantern', 'abcde|  Invented│lantern', 'abcde│  Invented│lantern\nBlue glass.  ']) {
      expect((await f.feed(body)).exposure.kind).toBe('unknown');
    }
    // The real renderer drops terminal LF. Stage 1 must not invent it back.
    f.write('Invented lantern\n');
    expect((await f.feed('abcde│Invented lantern')).exposure.kind).toBe('unknown');
  } finally { f.close(); }
});

for (const extra of [
  { details: { truncation: { truncated: true } } },
  { details: { nextOffset: 2 } },
  { details: { metrics: { truncated: true } } },
  { structuredContent: { truncated: true } },
  { structuredContent: { blockedByLongLine: true } },
  { structuredContent: { hadUtf8DecodeErrors: true } },
  { structuredContent: { notices: ['Invented warning'] } },
] as Partial<MainReadResult>[]) {
  test(`truncation/continuation metadata never attests full: ${JSON.stringify(extra)}`, async () => {
    const f = attestationFixture();
    try { expect((await f.feed(undefined, {}, extra)).exposure.kind).toBe('unknown'); }
    finally { f.close(); }
  });
}

test('continuation notices, stale capture, unknown format, binary and lossy text fail closed', async () => {
  const f = attestationFixture();
  try {
    expect((await f.feed('Invented lantern\n\n[Showing lines 1-1 of 2. Use offset=2 to continue.]')).exposure.kind).toBe('unknown');
    // Even file content that resembles a tool notice is conservatively not full.
    f.write('[Read truncated; call outline]');
    expect((await f.feed('[Read truncated; call outline]')).exposure.kind).toBe('unknown');
    const c = f.call();
    expect(f.producer.start(c, f.root, 'main-agent')).toBe(true);
    f.write('Changed invented lantern');
    expect(f.producer.complete(f.result(c), f.root, 'main-agent', 2)).toBe(true);
    const stale = (await f.adapter.port.snapshot(syntheticReadRequest(f.context()))).records.at(-1)!;
    expect(stale.exposure.kind).toBe('unknown');
    f.write(Buffer.from([0xff, 0x61]));
    expect((await f.feed('\ufffda')).exposure.kind).toBe('unknown');
    f.write('Invented\0lantern');
    expect((await f.feed('Invented\0lantern')).exposure.kind).toBe('unknown');
  } finally { f.close(); }
  const unknown = attestationFixture('unknown');
  try { expect((await unknown.feed()).exposure.kind).toBe('unknown'); } finally { unknown.close(); }
});

test('paired event identity, main-agent provenance, errors and nontext results cannot be promoted', async () => {
  const f = attestationFixture();
  try {
    const c = f.call();
    expect(f.producer.complete(f.result(c), f.root, 'main-agent', 2)).toBe(false);
    expect(f.producer.start(c, f.root, 'other')).toBe(false);
    expect(f.producer.start({ ...c, type: 'tool_call' } as MainReadCall, f.root, 'main-agent')).toBe(true);
    expect(f.producer.complete(f.result(c), f.root, 'main-agent', 2)).toBe(true);
    expect(f.producer.complete(f.result(c), f.root, 'main-agent', 2)).toBe(false);
    for (const extra of [{ isError: true }, { isError: undefined }, { toolName: 'read_file' }, { input: { path: f.path, limit: 1 } }]) {
      const next = f.call();
      expect(f.producer.start(next, f.root, 'main-agent')).toBe(true);
      expect(f.producer.complete(f.result(next, undefined, extra), f.root, 'main-agent', 2)).toBe(false);
    }
    expect((await f.feed(undefined, {}, { content: [{ type: 'image', data: 'invented' }] })).exposure.kind).toBe('unknown');
    expect((await f.feed(undefined, {}, { content: [{ type: 'text', text: 'Invented lantern\nBlue glass.' }, { type: 'text', text: 'extra' }] })).exposure.kind).toBe('unknown');
    const escape = f.call({ path: '../outside.md' });
    expect(f.producer.start(escape, f.root, 'main-agent')).toBe(false);
  } finally { f.close(); }
});

for (const bump of ['session', 'branch', 'compaction', 'epoch', 'grant', 'source'] as const) {
  test(`${bump} change clears admitted versions and rejects in-flight old-scope reads`, async () => {
    const f = attestationFixture();
    try {
      await f.feed();
      const pending = f.call();
      expect(f.producer.start(pending, f.root, 'main-agent')).toBe(true);
      const c = f.context();
      if (bump === 'epoch') f.bumpEpoch();
      else f.changeContext({ ...c,
        ...(bump === 'grant' ? { grantRevision: 'invented-grant-2' } : {}),
        ...(bump === 'source' ? { sourceRevision: 'invented-source-2' } : {}),
        scope: { ...c.scope,
          ...(bump === 'session' ? { sessionId: 'invented-session-2' } : {}),
          ...(bump === 'branch' ? { branchGeneration: c.scope.branchGeneration + 1 } : {}),
          ...(bump === 'compaction' ? { compactionGeneration: c.scope.compactionGeneration + 1 } : {}),
        },
      });
      expect(f.producer.complete(f.result(pending), f.root, 'main-agent', 2)).toBe(false);
      expect((await f.adapter.port.snapshot(syntheticReadRequest(f.context()))).records).toHaveLength(0);
    } finally { f.close(); }
  });
}

test('references composition consumes stage-1 full attestation for exactly one version, then fences lifecycle bumps', async () => {
  const f = attestationFixture();
  const c = createHarnessReferences({ bindings: { ...bindings(), catalog: f.catalog,
    captureIdentity: () => ({ root: f.root, epoch: 1 }), readTextFormat: () => 'pi-read-text-v1' } });
  try {
    const { hooks, ctx } = attach(c);
    expect(c.registration.stage).toBe('observe');
    const call = f.call();
    expect(c.attestations.start(call, f.root, 'main-agent')).toBe(true);
    expect(c.attestations.complete(f.result(call), f.root, 'main-agent', 2)).toBe(true);
    const version = createHash('sha256').update('Invented lantern\nBlue glass.').digest('hex');
    const trigger = { moduleId: 'context.references', sessionId: 'synthetic-session', eventId: 'invented-trigger',
      evidence: [{ id: 'synthetic-doc', kind: 'knowledge' as const, version, text: 'Invented lantern.' }] };
    const run = (v = version) => c.registration.handlers['context.references.deliver'].run({
      trigger: { ...trigger, evidence: [{ ...trigger.evidence[0], version: v }] },
      job: c.registration.jobs[0], signal: new AbortController().signal,
    });
    expect((await run()).status).toBe('rejected'); // already-read, not tool success
    expect((await run(version + '-different')).status).toBe('prepared');
    for (const hook of ['session_compact', 'session_tree', 'session_start']) {
      const late = f.call();
      expect(c.attestations.start(late, f.root, 'main-agent')).toBe(true);
      hooks.get(hook)!({}, ctx);
      expect(c.attestations.complete(f.result(late), f.root, 'main-agent', 2)).toBe(false);
      expect((await run()).status).toBe('prepared');
      const fresh = f.call();
      expect(c.attestations.start(fresh, f.root, 'main-agent')).toBe(true);
      expect(c.attestations.complete(f.result(fresh), f.root, 'main-agent', 2)).toBe(true);
      expect((await run()).status).toBe('rejected');
    }
  } finally { c.close(); f.close(); }
});
