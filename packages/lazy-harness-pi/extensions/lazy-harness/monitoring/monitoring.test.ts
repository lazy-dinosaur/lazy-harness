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
