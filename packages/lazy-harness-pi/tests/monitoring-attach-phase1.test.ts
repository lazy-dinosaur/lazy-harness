import { describe, test, expect } from 'bun:test'
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync, symlinkSync, statSync, readdirSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { attachMonitoringPhase1, installMonitoringPhase1, HOST_PORT_MAJORS, MONITORING_ROOT, UNAVAILABLE_PORTS, OBSERVER_LIMITS } from '../extensions/lazy-harness/monitoring/index.ts'
import { parseMonitoringAttachConfig } from '../extensions/lazy-harness/monitoring/config.ts'
import { createHostReadRecords } from '../extensions/lazy-harness/monitoring/read-records.ts'
import { createPiModelBinding, assertOpenRouterJevOnly } from '../extensions/lazy-harness/monitoring/model.ts'
import { createObservation } from '../extensions/lazy-harness/monitoring/observation.ts'
import { createObserveLog } from '../extensions/lazy-harness/monitoring/observe-log.ts'
import { captureRecord, admitCatalog } from '../extensions/lazy-harness/monitoring/catalog.ts'
import { createMonitoringModelRouter, createInMemoryWorkerPort, runWorkerPortConformance, references, host, canonicalJsonHash } from '../../../vendor/lazy-harness-monitoring/composition.ts'
import { runReadRecordPortConformance } from '../../../vendor/lazy-harness-monitoring/packages/core/src/host/input-port-conformance.ts'

const fakeModel: any = { provider: 'openrouter', id: 'typesafe/jev-1.14', api: 'typesafe-system-one', type: 'classifier', baseUrl: 'https://openrouter.ai/api/v1', contextWindow: 131072, cost: { input: 0.1, output: 0, cacheRead: 0, cacheWrite: 0 } }
const admitted = () => parseMonitoringAttachConfig({ observeLog: false, references: { stage: 'observe' }, budget: { maxCalls: 4, maxReservedTokens: 200000, maxReservedUsd: 1 } })
function hooks(context: object = {}) {
  const map = new Map<string, Function[]>()
  const ctx = { sessionManager: { getSessionId: () => 'synthetic-session', getLeafId: () => 'leaf-1', getBranch: () => [], buildSessionProjection: () => ({ messages: [] }) }, getSystemPrompt: () => '', ...context }
  const commands = new Map<string, any>()
  return { commands, registerCommand(name: string, spec: any) { commands.set(name, spec) }, on(name: string, f: any) { const list = map.get(name) ?? []; list.push(f); map.set(name, list); return () => { const i = list.indexOf(f); if (i >= 0) list.splice(i, 1) } }, map, emit(name: string, extra: object = {}) { return [...(map.get(name) ?? [])].map(f => f({ type: name, ...extra }, ctx)) } }
}
function fakeClassifier(calls: any[]) {
  return { model: fakeModel, runtime: { async classify(model: any, body: any, options: any) {
    calls.push({ model, body, options })
    return { ...fakeModel, model: model.id, stopReason: 'stop', answers: Object.fromEntries(Object.entries(body.questions).map(([key, q]: any) => [key, q.type === 'choice' ? { type: 'choice', choice: 'run', confidence: 0.9 } : { type: 'bool', probability: 1 }])) }
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
      writeFileSync(join(dir, '.lazy-harness/monitoring-attach.json'), JSON.stringify({ references: { stage: 'observe' }, observeLog: false }))
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
      writeFileSync(join(dir, '.lazy-harness/monitoring-attach.json'), JSON.stringify({ references: { stage: 'observe' }, observeLog: false }))
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
  test('private metadata log, status, permissions, retention, size cap and no body leakage', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-telemetry-')), state = mkdtempSync(join(tmpdir(), 'lh-state-'))
    const calls: any[] = [], pi = hooks()
    let owner: ReturnType<typeof attachMonitoringPhase1> | undefined
    try {
      mkdirSync(join(dir, '.lazy-harness/spec'), { recursive: true }); writeFileSync(join(dir, '.lazy-harness/spec/fake.md'), 'BODY_SECRET_SENTINEL')
      const config = parseMonitoringAttachConfig({ ...admitted(), observeLog: state, catalog: [{ id: 'doc:fake', path: '.lazy-harness/spec/fake.md' }] })
      const fake = fakeClassifier(calls), classify = fake.runtime.classify
      fake.runtime.classify = async (...args: any[]) => ({ ...await classify(...args), usage: { totalTokens: 23, cost: { total: 0.0002 } } })
      owner = attachMonitoringPhase1(pi, { root: dir, config, classifier: fake })
      if (owner.stage !== 'observe') throw Error('observe missing')
      pi.emit('session_start'); pi.emit('input', { text: 'CONVERSATION_SECRET_SENTINEL', source: 'interactive' }); await owner.idle()
      const status = owner.status(), path = status.log.path!
      const lines = readFileSync(path, 'utf8').trim().split('\n').map(l => JSON.parse(l))
      expect(lines.some(l => l.outcome === 'judged' && l.decisionMode === 'run')).toBe(true)
      expect(lines.some(l => l.outcome === 'compaction' && l.compaction.withinBudget)).toBe(true)
      expect(lines.find(l => l.outcome === 'judged').selectedDocuments).toEqual([{ id: 'doc:fake', version: admitCatalog(dir, config).documents[0].version }])
      expect(lines.find(l => l.outcome === 'judged').reportedTokens).toBe(23)
      expect(lines.find(l => l.outcome === 'judged').confidence).toBe(0.9)
      const allowed = ['schema', 'time', 'sessionIdHash', 'bindingGeneration', 'frameId', 'eventId', 'trigger', 'outcome', 'decisionMode', 'confidence', 'selectedDocuments', 'candidateCount', 'compaction', 'modelCalls', 'reportedUsd', 'reportedTokens', 'latencyMs', 'budgetRemaining', 'errorClass'].sort()
      for (const line of lines) expect(Object.keys(line).sort()).toEqual(allowed)
      for (const forbidden of ['BODY_SECRET_SENTINEL', 'CONVERSATION_SECRET_SENTINEL', 'synthetic-session', 'OPENROUTER_API_KEY', 'questions', 'prompt']) expect(readFileSync(path, 'utf8')).not.toContain(forbidden)
      expect(statSync(path).mode & 0o777).toBe(0o600); expect(statSync(join(path, '..')).mode & 0o777).toBe(0o700)
      expect(status.attached).toBe(true); expect(status.watchEvents).toEqual(['input']); expect(status.catalog.totalBytes).toBe(20)
      expect(status.budget.used.calls).toBe(1); expect(status.budget.used.reportedTokens).toBe(23); expect(status.counters.judgements).toBe(1); expect(status.lastOutcomes.length).toBeLessThanOrEqual(5)
      const sink = createObserveLog(dir, state, { maxBytes: 1 })
      sink.write(lines[0]); await sink.idle(); expect(sink.stats.dropped).toBe(1)
      const expired = join(path, '..', '2000-01-01.jsonl'); writeFileSync(expired, '{}\n')
      const fresh = createObserveLog(dir, state); fresh.write(lines[0]); await fresh.idle(); expect(readdirSync(join(path, '..'))).not.toContain('2000-01-01.jsonl')
    } finally { await owner?.close(); rmSync(dir, { recursive: true, force: true }); rmSync(state, { recursive: true, force: true }) }
  })
  test('log failure is nonfatal and counted; project paths refused', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-log-fail-')), pi = hooks(), calls: any[] = []
    const owner = attachMonitoringPhase1(pi, { root: dir, config: parseMonitoringAttachConfig({ ...admitted(), observeLog: dir }), classifier: fakeClassifier(calls) })
    try {
      if (owner.stage !== 'observe') throw Error('observe missing')
      pi.emit('session_start'); pi.emit('input', { text: 'Synthetic', source: 'interactive' }); await owner.idle()
      expect(calls).toHaveLength(1); expect(owner.status().log.errors).toBeGreaterThan(0); expect(owner.status().attached).toBe(true)
      expect(owner.status().counters.errors).toBeGreaterThan(0)
    } finally { await owner.close(); rmSync(dir, { recursive: true, force: true }) }
  })
  test('compaction discards late old result; resumes with lifetime budget; shutdown closes', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-resume-')), pi = hooks(), calls: any[] = []
    let release!: () => void, began!: () => void
    const ready = new Promise<void>(r => began = r), gate = new Promise<void>(r => release = r)
    const fake = fakeClassifier(calls), classify = fake.runtime.classify
    fake.runtime.classify = async (...args: any[]) => { if (!calls.length) { began(); await gate } return classify(...args) }
    const owner = attachMonitoringPhase1(pi, { root: dir, config: parseMonitoringAttachConfig({ ...admitted(), budget: { ...admitted().budget, maxCalls: 2 } }), classifier: fake })
    try {
      if (owner.stage !== 'observe') throw Error('observe missing')
      pi.emit('session_start'); pi.emit('input', { text: 'old input', source: 'interactive' }); await ready
      const reserved = owner.status().budget.used.tokens
      pi.emit('session_before_compact'); expect(owner.status().attached).toBe(false)
      release(); await owner.idle()
      expect(owner.status().counters.runs).toBe(0)
      expect(owner.status().lastOutcomes.some(o => o.outcome === 'skipped')).toBe(true)
      pi.emit('session_compact'); pi.emit('input', { text: 'new input', source: 'interactive' }); await owner.idle()
      expect(calls).toHaveLength(2); expect(owner.status().attached).toBe(true); expect(owner.status().budget.used.tokens).toBeGreaterThan(reserved); expect(owner.status().budget.remaining.calls).toBe(0)
      pi.emit('session_before_compact'); pi.emit('session_compact_failed'); pi.emit('input', { text: 'budget exhausted', source: 'interactive' }); await owner.idle()
      expect(calls).toHaveLength(2)
      pi.emit('session_shutdown'); pi.emit('input', { text: 'closed', source: 'interactive' }); await owner.idle()
      expect(owner.status().attached).toBe(false); expect(owner.status().reason).toBe('session_shutdown'); expect(calls).toHaveLength(2)
    } finally { release?.(); await owner.close(); rmSync(dir, { recursive: true, force: true }) }
  })
  test('trace projection records skip/defer/refusal/failure and compaction calls without bodies', async () => {
    const config = admitted(), observation = createObservation(tmpdir(), config)
    observation.configure([], () => ({ calls: 4, tokens: 100, usd: 1 }))
    for (const mode of ['skip', 'defer']) {
      const id = 'frame-' + mode
      observation.frame({ id, sessionId: 'private', binding: 1, sourceEvent: 'input' })
      observation.exchange({ body: { state: { tasks: [{ processorId: 'context.references', view: { event: { id }, context: { references: [] } } }] } } }, { answers: { decision_0: { type: 'choice', choice: mode, confidence: 0.8 } } }, 1, false)
      observation.trace({ type: 'judgement', frameId: id, outcomes: [{ mode }] }, [])
    }
    expect(observation.counters.skips).toBe(1); expect(observation.counters.defers).toBe(1)
    observation.frame({ id: 'bad', sessionId: 'private', binding: 1, sourceEvent: 'input' })
    observation.trace({ type: 'judgement', frameId: 'bad', outcomes: [] }, [])
    expect(observation.recent.at(-1)?.outcome).toBe('refused')
    // One final outcome per frame (sweep/dedupe): a separate frame carries the selection failure.
    observation.frame({ id: 'bad2', sessionId: 'private', binding: 1, sourceEvent: 'input' })
    observation.trace({ type: 'selection', frameId: 'bad2', status: 'core_or_material_rejected', bodies: [{ text: 'NEVER_STORE' }] }, [])
    observation.trace({ type: 'selection', frameId: 'bad', status: 'core_or_material_rejected' }, [])
    expect(observation.recent.filter(o => o.frameId === 'bad').length).toBe(1)
    expect(observation.recent.at(-1)?.outcome).toBe('failed'); expect(observation.counters.errors).toBe(1)
    await observation.log.idle(); expect(observation.log.stats.written).toBe(0)
  })
  test('XDG default log path, file symlink refusal, and disabled sink writes nothing', async () => {
    const root = mkdtempSync(join(tmpdir(), 'lh-xdg-root-')), state = mkdtempSync(join(tmpdir(), 'lh-xdg-state-')), old = process.env.XDG_STATE_HOME
    try {
      process.env.XDG_STATE_HOME = state
      const sink = createObserveLog(root), path = sink.path()!
      expect(path.startsWith(join(state, 'lazy-harness/monitoring/observe'))).toBe(true)
      mkdirSync(join(path, '..'), { recursive: true })
      const target = join(state, 'target'); writeFileSync(target, 'untouched'); symlinkSync(target, path)
      const row: any = { schema: 'lazy-harness-observe/v1', selectedDocuments: [], budgetRemaining: { calls: 0, usd: 0, tokens: 0 } }
      sink.write(row); await sink.idle(); expect(sink.stats.errors).toBe(1); expect(readFileSync(target, 'utf8')).toBe('untouched')
      const off = createObserveLog(root, false); off.write(row); await off.idle(); expect(off.stats.written).toBe(0); expect(off.path()).toBeNull()
    } finally { if (old === undefined) delete process.env.XDG_STATE_HOME; else process.env.XDG_STATE_HOME = old; rmSync(root, { recursive: true, force: true }); rmSync(state, { recursive: true, force: true }) }
  })
  test('tree completion resumes, replacement is closed, off registers nothing; status command is read-only', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-status-')), pi = hooks(), calls: any[] = [], fake = fakeClassifier(calls)
    const owner = attachMonitoringPhase1(pi, { root: dir, config: admitted(), classifier: fake })
    try {
      if (owner.stage !== 'observe') throw Error('observe missing')
      pi.emit('session_start'); pi.emit('session_before_tree'); pi.emit('session_tree'); pi.emit('input', { text: 'after tree', source: 'interactive' }); await owner.idle()
      expect(calls).toHaveLength(1); expect(owner.status().generation).toBe(2)
      pi.emit('session_before_fork'); pi.emit('session_start'); expect(owner.status().reason).toBe('session_replaced_reload_required')
      const off = hooks(); installMonitoringPhase1(off as any, dir); expect(off.commands.size).toBe(0); expect(off.map.size).toBe(0)
      mkdirSync(join(dir, '.lazy-harness'), { recursive: true }); writeFileSync(join(dir, '.lazy-harness/monitoring-attach.json'), JSON.stringify({ ...admitted(), observeLog: false }))
      const installed = hooks({ modelRegistry: { ...fake.runtime, getModelOfType: () => fake.model } }); installMonitoringPhase1(installed as any, dir)
      await Promise.all(installed.emit('session_start'))
      const before = calls.length, messages: string[] = []
      await installed.commands.get('monitoring').handler('status', { ui: { notify: (s: string) => messages.push(s) } })
      const status = JSON.parse(messages[0]); expect(status.stage).toBe('observe'); expect(status.watchEvents).toEqual(['input']); expect(status.log.path).toBeNull(); expect(calls).toHaveLength(before)
      for (const field of ['attached', 'reason', 'scope', 'generation', 'catalog', 'budget', 'counters', 'lastOutcomes', 'log']) expect(status).toHaveProperty(field)
      await Promise.all(installed.emit('session_shutdown'))
    } finally { await owner.close(); rmSync(dir, { recursive: true, force: true }) }
  })
  test('long real sessions stay observable through tail snapshots (regression: 7k-message session stopped at session_start)', async () => {
    expect(OBSERVER_LIMITS.tailMessages).toBeGreaterThan(0)
    const messages = Array.from({ length: 600 }, (_, i) => ({ role: i % 2 ? 'assistant' : 'user', content: [{ type: 'text', text: `message ${i}` }], timestamp: i }))
    const branch = messages.map((_, i) => ({ id: `e${i}`, parentId: i ? `e${i - 1}` : null, type: 'message' }))
    const pi = hooks({ sessionManager: { getSessionId: () => 'long-session', getLeafId: () => 'e599', getBranch: () => branch, buildSessionProjection: () => ({ messages }) } })
    const calls: any[] = [], owner = attachMonitoringPhase1(pi, { root: tmpdir(), config: admitted(), classifier: fakeClassifier(calls) })
    try {
      if (owner.stage !== 'observe') throw Error('observe missing')
      pi.emit('session_start'); pi.emit('input', { text: 'Which project facts matter?', source: 'interactive' }); await owner.idle()
      expect(owner.status().reason).not.toBe('scope_or_catalog_unavailable')
      expect(owner.status().attached).toBe(true)
      expect(calls.length).toBeGreaterThan(0)
    } finally { await owner.close() }
  })
  test('realistic catalog + long messages still judge (regression: material_limit blocked every live input)', async () => {
    const dir = mkdtempSync(join(tmpdir(), 'lh-matfix-'))
    try {
      mkdirSync(join(dir, '.lazy-harness/ssot'), { recursive: true }); mkdirSync(join(dir, '.lazy-harness/decisions'), { recursive: true })
      writeFileSync(join(dir, '.lazy-harness/ssot/a.md'), '# A\n' + 'ownership fact. '.repeat(370)); writeFileSync(join(dir, '.lazy-harness/decisions/b.md'), '# B\n' + 'repository decision. '.repeat(180))
      const config = parseMonitoringAttachConfig({ observeLog: false, references: { stage: 'observe' }, catalog: [{ id: 'ssot:a', path: '.lazy-harness/ssot/a.md' }, { id: 'adr:b', path: '.lazy-harness/decisions/b.md' }], budget: { maxCalls: 4, maxReservedTokens: 1000000, maxReservedUsd: 1 } })
      const messages = Array.from({ length: 300 }, (_, i) => ({ role: i % 2 ? 'assistant' : 'user', content: [{ type: 'text', text: `m${i} ` + 'x'.repeat(1500) }], timestamp: i }))
      const branch = messages.map((_, i) => ({ id: `e${i}`, parentId: i ? `e${i - 1}` : null, type: 'message' }))
      const pi = hooks({ sessionManager: { getSessionId: () => 'long', getLeafId: () => 'e299', getBranch: () => branch, buildSessionProjection: () => ({ messages }) } })
      const calls: any[] = [], owner = attachMonitoringPhase1(pi, { root: dir, config, classifier: fakeClassifier(calls) })
      try {
        if (owner.stage !== 'observe') throw Error('observe missing')
        pi.emit('session_start'); pi.emit('input', { text: 'first question', source: 'interactive' }); await owner.idle()
        expect(owner.pipeline.window.traces.map((t: any) => t.reason)).not.toContain('material_limit')
        expect(calls.length).toBeGreaterThan(0)
        expect(owner.status().window.lastReason).toBeNull()
      } finally { await owner.close() }
    } finally { rmSync(dir, { recursive: true, force: true }) }
  })
  test('classifier failure records a bounded failure class (no provider text) in status and outcome', async () => {
    const pi = hooks(), calls: any[] = []
    const failing: any = { model: fakeModel, runtime: { async classify(model: any) { calls.push(1); return { ...fakeModel, model: model.id, stopReason: 'error', errorMessage: '401 Unauthorized: secret-bearing provider text', answers: {} } } } }
    const owner = attachMonitoringPhase1(pi, { root: tmpdir(), config: admitted(), classifier: failing })
    try {
      if (owner.stage !== 'observe') throw Error('observe missing')
      pi.emit('session_start'); pi.emit('input', { text: 'Which project facts matter?', source: 'interactive' }); await owner.idle()
      expect(calls.length).toBe(1)
      const status = owner.status()
      expect(status.budget.used.lastFailure).toBe('stop_error_auth_401')
      expect(JSON.stringify(status)).not.toContain('secret-bearing')
      expect(status.classifierStopped).toBe(true)
    } finally { await owner.close() }
  })
  test('a judgement slower than one second is not aborted by the selection job deadline (regression: live classifier_uncertain:aborted)', async () => {
    const pi = hooks(), calls: any[] = []
    const slow: any = { model: fakeModel, runtime: { async classify(model: any, body: any, options: any) { calls.push(1); await new Promise(r => setTimeout(r, 1500)); if (options.signal?.aborted) return { ...fakeModel, model: model.id, stopReason: 'aborted', answers: {} }; return { ...fakeModel, model: model.id, stopReason: 'stop', answers: Object.fromEntries(Object.entries(body.questions).map(([key, q]: any) => [key, q.type === 'choice' ? { type: 'choice', choice: 'run', confidence: 0.9 } : { type: 'bool', probability: 1 }])) } } } }
    const owner = attachMonitoringPhase1(pi, { root: tmpdir(), config: admitted(), classifier: slow })
    try {
      if (owner.stage !== 'observe') throw Error('observe missing')
      pi.emit('session_start'); pi.emit('input', { text: 'Which project facts matter?', source: 'interactive' }); await owner.idle()
      expect(calls.length).toBe(1)
      expect(owner.status().budget.used.lastFailure).toBeNull()
      expect(owner.status().classifierStopped).toBe(false)
      expect(owner.status().counters.judgements).toBe(1)
    } finally { await owner.close() }
  })
  test('event budget: a long-running session keeps judging after more than 2048 frames (regression: window stopped with event_budget)', async () => {
    const pi = hooks(), calls: any[] = [], owner = attachMonitoringPhase1(pi, { root: tmpdir(), config: admitted(), classifier: fakeClassifier(calls) })
    try {
      if (owner.stage !== 'observe') throw Error('observe missing')
      pi.emit('session_start')
      for (let i = 0; i < 2100; i++) pi.emit('message_update', { message: { role: 'assistant', content: [{ type: 'text', text: 'x' }] }, assistantMessageEvent: { type: 'text_delta', delta: 'x' } })
      pi.emit('input', { text: 'Which project facts matter?', source: 'interactive' }); await owner.idle()
      expect(calls.length).toBeGreaterThan(0)
      expect(owner.status().window.renewals).toBe(1)
      expect(owner.status().budget.used.calls).toBeGreaterThan(0)
    } finally { await owner.close() }
  })
  test('queued follow-up/steer inputs are logged as skipped with a reason (regression: no line for a mid-run message)', async () => {
    const pi = hooks(), calls: any[] = []
    const slow: any = { model: fakeModel, runtime: { async classify(model: any, body: any) { calls.push(1); await new Promise(r => setTimeout(r, 300)); return { ...fakeModel, model: model.id, stopReason: 'stop', answers: Object.fromEntries(Object.entries(body.questions).map(([key, q]: any) => [key, q.type === 'choice' ? { type: 'choice', choice: 'skip', confidence: 0.6 } : { type: 'bool', probability: 0.1 }])) } } } }
    const config = parseMonitoringAttachConfig({ observeLog: false, references: { stage: 'observe' }, budget: { maxCalls: 6, timeoutMs: 1000, maxReservedTokens: 200000, maxReservedUsd: 1 } })
    const owner = attachMonitoringPhase1(pi, { root: tmpdir(), config, classifier: slow })
    try {
      if (owner.stage !== 'observe') throw Error('observe missing')
      const a = { role: 'assistant', content: [{ type: 'text', text: 'working' }], timestamp: 1 }
      pi.emit('session_start'); pi.emit('input', { text: 'normal prompt', source: 'interactive' })
      pi.emit('before_agent_start', { prompt: 'normal prompt' }); pi.emit('agent_start'); pi.emit('turn_start', { turnIndex: 0 }); pi.emit('message_start', { message: a })
      pi.emit('input', { text: 'queued follow-up', source: 'interactive', streamingBehavior: 'followUp' })
      pi.emit('input', { text: 'mid-run steer', source: 'interactive', streamingBehavior: 'steer' })
      pi.emit('message_end', { message: a }); pi.emit('turn_end', { turnIndex: 0, message: a, toolResults: [] }); pi.emit('agent_end', { messages: [] })
      await owner.idle(); await new Promise(r => setTimeout(r, 4300))
      const outcomes = owner.status().lastOutcomes as any[]
      const finals = outcomes.filter(o => o.outcome !== 'compaction')
      expect(new Set(finals.map(o => o.frameId)).size).toBe(finals.length)
      expect(finals.some(o => o.outcome === 'skipped' && String(o.errorClass).startsWith('queued_input_followUp:'))).toBe(true)
      expect(finals.filter(o => o.outcome !== 'judged').every(o => typeof o.errorClass === 'string' && o.errorClass.length > 0)).toBe(true)
    } finally { await owner.close() }
  }, 15000)
})
