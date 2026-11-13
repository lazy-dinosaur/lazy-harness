import { describe, test, expect } from 'bun:test'
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync, symlinkSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { attachMonitoringPhase1, installMonitoringPhase1, HOST_PORT_MAJORS, MONITORING_ROOT, UNAVAILABLE_PORTS } from '../extensions/lazy-harness/monitoring/index.ts'
import { parseMonitoringAttachConfig } from '../extensions/lazy-harness/monitoring/config.ts'
import { createHostReadRecords } from '../extensions/lazy-harness/monitoring/read-records.ts'
import { createPiModelBinding, assertOpenRouterJevOnly } from '../extensions/lazy-harness/monitoring/model.ts'
import { captureRecord, admitCatalog } from '../extensions/lazy-harness/monitoring/catalog.ts'
import { createMonitoringModelRouter, createInMemoryWorkerPort, runWorkerPortConformance, references, host, canonicalJsonHash } from '../../../vendor/lazy-harness-monitoring/composition.ts'
import { runReadRecordPortConformance } from '../../../vendor/lazy-harness-monitoring/packages/core/src/host/input-port-conformance.ts'

const fakeModel: any = { provider: 'openrouter', id: 'typesafe/jev-1.14', api: 'typesafe-system-one', type: 'classifier', baseUrl: 'https://openrouter.ai/api/v1', contextWindow: 131072, cost: { input: 0.1, output: 0, cacheRead: 0, cacheWrite: 0 } }
const admitted = () => parseMonitoringAttachConfig({ references: { stage: 'observe' }, budget: { maxCalls: 4, maxReservedTokens: 200000, maxReservedUsd: 1 } })
function hooks(context: object = {}) {
  const map = new Map<string, Function[]>()
  const ctx = { sessionManager: { getSessionId: () => 'synthetic-session', getLeafId: () => 'leaf-1', getBranch: () => [], buildSessionProjection: () => ({ messages: [] }) }, getSystemPrompt: () => '', ...context }
  return { on(name: string, f: any) { const list = map.get(name) ?? []; list.push(f); map.set(name, list); return () => { const i = list.indexOf(f); if (i >= 0) list.splice(i, 1) } }, map, emit(name: string, extra: object = {}) { return [...(map.get(name) ?? [])].map(f => f({ type: name, ...extra }, ctx)) } }
}
function fakeClassifier(calls: any[]) {
  return { model: fakeModel, runtime: { async classify(model: any, body: any, options: any) {
    calls.push({ model, body, options })
    return { ...fakeModel, model: model.id, stopReason: 'stop', answers: Object.fromEntries(Object.entries(body.questions).map(([key, q]: any) => [key, q.type === 'choice' ? { type: 'choice', choice: 'run' } : { type: 'bool', probability: 1 }])) }
  } } as any }
}
const task: any = { processorId: 'context.references', question: references.referencesQuestion, view: { eventRef: 'event:e1', event: { id: 'e1', kind: 'user.input', sequence: 1, scopeId: 'scope', contextVersion: '1' }, context: { scopeId: 'scope', version: '1', goal: 'Read project facts', references: [{ id: 'doc:one', kind: 'knowledge', version: '1', content: 'Synthetic fact' }] } } }

describe('phase 1 offline attachment', () => {
  test('pinned manifest validates and off installs nothing; no classifier or fetch', async () => {
    const pi = hooks(), calls: any[] = [], prior = globalThis.fetch
    globalThis.fetch = (() => { throw Error('network prohibited') }) as any
    try {
      const owner = attachMonitoringPhase1(pi, { root: tmpdir(), config: parseMonitoringAttachConfig({}), classifier: fakeClassifier(calls) })
      installMonitoringPhase1(pi as any, tmpdir()); expect(owner.stage).toBe('off'); expect(pi.map.size).toBe(0); await owner.close(); expect(calls).toHaveLength(0)
      expect(Object.values(HOST_PORT_MAJORS).every(v => v === 1)).toBe(true)
    } finally { globalThis.fetch = prior }
  })
  test('installed observe uses the running context registry without network; zero budget never classifies', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-context-registry-')), calls: any[] = [], lookups: unknown[][] = []
    const fake = fakeClassifier(calls)
    const registry = { ...fake.runtime, getModelOfType(...args: unknown[]) { expect(this).toBe(registry); lookups.push(args); return fake.model } }
    const pi = hooks({ modelRegistry: registry }), prior = globalThis.fetch
    globalThis.fetch = (() => { throw Error('network prohibited') }) as any
    try {
      mkdirSync(join(dir, '.lazy-harness'), { recursive: true })
      writeFileSync(join(dir, '.lazy-harness/monitoring-attach.json'), JSON.stringify({ references: { stage: 'observe' } }))
      installMonitoringPhase1(pi as any, dir)
      await Promise.all(pi.emit('session_start'))
      await Promise.all(pi.emit('input', { text: 'Synthetic input', source: 'interactive' }))
      await Promise.all(pi.emit('session_shutdown'))
      expect(lookups).toEqual([['classifier', 'openrouter', 'typesafe/jev-1.14']]); expect(calls).toHaveLength(0)
    } finally { globalThis.fetch = prior; rmSync(dir, { recursive: true, force: true }) }
  })
  test('installed observe fails closed on old/missing registries and unavailable/wrong models', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-context-reject-'))
    try {
      mkdirSync(join(dir, '.lazy-harness'), { recursive: true })
      writeFileSync(join(dir, '.lazy-harness/monitoring-attach.json'), JSON.stringify({ references: { stage: 'observe' } }))
      for (const registry of [undefined, {}, { getModelOfType: () => fakeModel }, { classify: () => { throw Error('must not classify') }, getModelOfType: () => undefined }, { classify: () => { throw Error('must not classify') }, getModelOfType: () => ({ ...fakeModel, id: 'typesafe/jev-latest' }) }]) {
        const pi = hooks({ modelRegistry: registry }); installMonitoringPhase1(pi as any, dir)
        await expect(Promise.all(pi.emit('session_start'))).rejects.toThrow()
      }
    } finally { rmSync(dir, { recursive: true, force: true }) }
  })
  test('monitoring does not load a host SDK or eval transport; package has no local SDK pin', () => {
    for (const name of ['model', 'index']) {
      const source = readFileSync(new URL(`../extensions/lazy-harness/monitoring/${name}.ts`, import.meta.url), 'utf8')
      expect(source).not.toContain("import('@earendil-works/pi-coding-agent')"); expect(source).not.toContain('compaction-transport.ts'); expect(source).not.toContain('ModelRuntime')
    }
    const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'))
    expect(pkg.devDependencies['@earendil-works/pi-coding-agent']).toBeUndefined()
  })
  test('unsupported host major refuses before hooks/classifier', () => {
    const pi = hooks(), calls: any[] = []
    expect(() => attachMonitoringPhase1(pi, { root: tmpdir(), config: parseMonitoringAttachConfig({}), majors: { ...HOST_PORT_MAJORS, 'judgement.model': 2 }, classifier: fakeClassifier(calls) })).toThrow()
    expect(pi.map.size).toBe(0); expect(calls).toHaveLength(0)
  })
  test('invalid/missing manifest and unsupported module major refuse before composition', () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-manifest-'))
    try {
      const pi = hooks()
      expect(() => attachMonitoringPhase1(pi, { root: dir, moduleRoot: dir })).toThrow()
      const manifest = JSON.parse(readFileSync(join(MONITORING_ROOT, 'lazy-harness.module.json'), 'utf8'))
      for (const path of [manifest.entry, ...manifest.conformance]) { const target = join(dir, path); mkdirSync(join(target, '..'), { recursive: true }); writeFileSync(target, '') }
      for (const patch of [{ schema: 'lazy-harness-module/v2' }, { requires: [{ port: 'worker.execution', v: 2 }] }, { runtime: null }]) {
        writeFileSync(join(dir, 'lazy-harness.module.json'), JSON.stringify({ ...manifest, ...patch }))
        expect(() => attachMonitoringPhase1(pi, { root: dir, moduleRoot: dir })).toThrow()
      }
      expect(pi.map.size).toBe(0)
    } finally { rmSync(dir, { recursive: true, force: true }) }
  })
  test.each(['active', 'shadow', 'invalid'])('cannot activate stage %s', stage => expect(() => parseMonitoringAttachConfig({ references: { stage } })).toThrow())
  test('unavailable rules/memory cannot be configured or started', () => {
    for (const name of ['memory', 'rules']) expect(() => parseMonitoringAttachConfig({ [name]: { stage: 'observe' } })).toThrow()
    expect(UNAVAILABLE_PORTS).toEqual(['memory.review-sink', 'memory.source', 'policy.registry', 'rule.verifier'])
  })
  test('own host read ledger passes manifest input conformance', async () => {
    const checks = await runReadRecordPortConformance((context, options) => createHostReadRecords(context, options))
    expect(checks).toHaveLength(5)
  })
  test('chosen module default passes manifest worker conformance', async () => {
    const result = await runWorkerPortConformance(createInMemoryWorkerPort)
    expect(result.checks).toHaveLength(24)
  })
  test('Jev-only guard and exact route reject aliases, other models/endpoints', () => {
    for (const id of ['openai/gpt-4', 'typesafe/jev-latest', 'typesafe/jev-1.14:latest']) expect(() => assertOpenRouterJevOnly({ provider: 'openrouter', id })).toThrow()
    for (const patch of [{ id: 'typesafe/jev-1.13' }, { provider: 'typesafe' }, { baseUrl: 'https://example.invalid' }]) expect(() => createPiModelBinding(fakeClassifier([]).runtime, { ...fakeModel, ...patch }, admitted().budget)).toThrow()
  })
  test('fake native classifier mapping, stored credentials and zero retries, lifetime budget', async () => {
    const calls: any[] = [], fake = fakeClassifier(calls), config = admitted()
    const binding = createPiModelBinding(fake.runtime, fake.model, { ...config.budget, maxCalls: 1 })
    const router = createMonitoringModelRouter(binding.modelConfig, binding.modelHost)
    try {
      const result = await router.judgeBatch([task], new AbortController().signal)
      expect(result['context.references'].mode).toBe('run'); expect(result['context.references'].evidenceRefs).toEqual(['event:e1', 'doc:one'])
      expect(calls).toHaveLength(1); expect(calls[0].body.questions.decision_0.type).toBe('choice'); expect(calls[0].body.questions.ref_0_0.type).toBe('bool')
      expect(calls[0].options.maxRetries).toBe(0); expect(calls[0].options.env).toEqual({ OPENROUTER_API_KEY: '' })
      expect(await router.judgeBatch([task], new AbortController().signal)).toEqual({}); expect(calls).toHaveLength(1)
    } finally { router.dispose(); await router.idle() }
  })
  test('default zero paid budget and pre-cancel dispatch zero classifier calls', async () => {
    for (const cancel of [false, true]) {
      const calls: any[] = [], fake = fakeClassifier(calls), binding = createPiModelBinding(fake.runtime, fake.model, parseMonitoringAttachConfig({}).budget)
      const router = createMonitoringModelRouter(binding.modelConfig, binding.modelHost), ctrl = new AbortController()
      if (cancel) ctrl.abort()
      expect(await router.judgeBatch([task], ctrl.signal)).toEqual({}); expect(calls).toHaveLength(0); router.dispose(); await router.idle()
    }
  })
  test('uncertain classifier is not retried', async () => {
    let calls = 0
    const binding = createPiModelBinding({ classify: async () => { calls++; throw Error('synthetic transport failure') } } as any, fakeModel, admitted().budget)
    const router = createMonitoringModelRouter(binding.modelConfig, binding.modelHost)
    expect(await router.judgeBatch([task], new AbortController().signal)).toEqual({})
    expect(await router.judgeBatch([task], new AbortController().signal)).toEqual({}); expect(calls).toBe(1); router.dispose(); await router.idle()
  })
  test('observe attaches frames, judges fake input, executes no jobs/enqueues/injection, boundary closes', async () => {
    const pi = hooks(), calls: any[] = [], owner = attachMonitoringPhase1(pi, { root: tmpdir(), config: admitted(), classifier: fakeClassifier(calls) })
    try {
      expect(owner.stage).toBe('observe')
      if (owner.stage !== 'observe') throw Error('observe missing')
      pi.emit('session_start'); pi.emit('input', { text: 'Which project facts matter?', source: 'interactive' }); await owner.idle()
      expect(calls.length).toBeGreaterThan(0)
      expect(owner.worker.getStatus().started).toBe(0)
      expect(pi.emit('context_with_system', { messages: [] }).every(r => r === undefined)).toBe(true)
      pi.emit('session_before_compact'); pi.emit('input', { text: 'another input', source: 'interactive' }); await owner.idle()
      const count = calls.length; pi.emit('session_compact_failed'); await owner.idle(); expect(calls.length).toBe(count)
      expect(owner.reads.record).toBeFunction()
    } finally { await owner.close() }
  })
  test('actual paired main read is attested; report enqueue refuses; byte changes revoke snapshots', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-read-feed-'))
    let owner: ReturnType<typeof attachMonitoringPhase1> | undefined
    try {
      const path = '.lazy-harness/spec/example.md'; mkdirSync(join(dir, '.lazy-harness/spec'), { recursive: true }); writeFileSync(join(dir, path), 'Synthetic bytes')
      const config = parseMonitoringAttachConfig({ references: { stage: 'observe' }, catalog: [{ id: 'doc:one', path }], readFormat: 'pi-read-text-v1' }), pi = hooks(), catalog = admitCatalog(dir, config)
      owner = attachMonitoringPhase1(pi, { root: dir, config, classifier: fakeClassifier([]) })
      if (owner.stage !== 'observe') throw Error('observe missing')
      pi.emit('session_start')
      pi.emit('tool_call', { toolCallId: 'read-1', toolName: 'read', input: { path } })
      pi.emit('tool_result', { toolCallId: 'read-1', toolName: 'read', input: { path }, content: [{ type: 'text', text: 'Synthetic bytes' }], isError: false })
      const request: any = { protocolVersion: 1, scope: { sessionId: 'synthetic-session', bindingGeneration: 1, branchId: 'leaf-1', branchGeneration: 1, compactionGeneration: 1 }, sourceRevision: canonicalJsonHash(catalog.documents.map(d => [d.id, d.version])), grantRevision: 'phase1-u1-observe-v1', cursor: 3, sourceEventId: 'input-1', documents: [{ documentId: 'doc:one', documentVersion: catalog.documents[0].version }] }
      const snapshot = await owner.port.snapshot(request)
      expect(host.evaluateReadRecordSnapshot(request, snapshot)[0].status).toBe('already-read')
      expect(owner.report({ moduleId: 'context.references', jobId: 'deliver', eventId: 'input-1', sessionId: 'synthetic-session', mode: 'always', text: 'Synthetic report', riskTier: 'read-only' }).status).toBe('failed')
      expect(owner.delivery.deliveryReceipts).toHaveLength(0)
      writeFileSync(join(dir, path), 'Changed bytes')
      expect(owner.port.isCurrent(request, snapshot)).toBe(false)
      expect(host.evaluateReadRecordSnapshot(request, await owner.port.snapshot(request))[0].status).toBe('unknown')
    } finally { await owner?.close(); rmSync(dir, { recursive: true, force: true }) }
  })
  test('catalog rejects traversal/symlinks, binds stable versions and revokes changed bytes', () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-catalog-'))
    try {
      const path = '.lazy-harness/spec/example.md'; mkdirSync(join(dir, '.lazy-harness/spec'), { recursive: true }); writeFileSync(join(dir, path), 'Synthetic bytes')
      const config = parseMonitoringAttachConfig({ catalog: [{ id: 'doc:one', path }] }), catalog = admitCatalog(dir, config)
      expect(catalog.isCurrent()).toBe(true); writeFileSync(join(dir, path), 'Changed'); expect(catalog.isCurrent()).toBe(false)
      expect(captureRecord(dir, '../escape')).toBeUndefined()
      symlinkSync(join(dir, path), join(dir, '.lazy-harness/spec/link.md')); expect(captureRecord(dir, '.lazy-harness/spec/link.md')).toBeUndefined()
      expect(() => parseMonitoringAttachConfig({ catalog: [{ id: 'doc:one', path: '.lazy-harness/spec/../secret.md' }] })).toThrow()
    } finally { rmSync(dir, { recursive: true, force: true }) }
  })
})
