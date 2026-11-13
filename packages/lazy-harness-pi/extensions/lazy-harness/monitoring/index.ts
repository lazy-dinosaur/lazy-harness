import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import type { ExtensionAPI } from '@earendil-works/pi-coding-agent'
import { startMonitoringComposition, references, prepareMonitoringBindings, createHandlerWorkerPort, bindReadRecordPort, exposeReadRecordPort, bindReportPort, exposeReportPort, canonicalJsonHash, type PortMajors } from '../../../../../vendor/lazy-harness-monitoring/composition.ts'
import { createPiObservationExtension, PiMonitoringObserver, attachPiFrames, piHostCapabilities, createParentReportDelivery, createReadResultAttestor, observationEvents } from '../../../../../vendor/lazy-harness-monitoring/hosts/pi/src/index.ts'
import { createRealtimeSelectionPipeline } from '../../../../../vendor/lazy-harness-monitoring/packages/core/src/engine/monitoring-core-realtime-selection.ts'
import { MonitoringModuleRuntime, ApprovedBudgetGate, monitoringReportId } from '../../../../../vendor/lazy-harness-monitoring/packages/core/src/engine/monitoring-engine-runtime.ts'
import { ContextCarryMailbox } from '../../../../../vendor/lazy-harness-monitoring/packages/core/src/engine/monitoring-core-context-mailbox.ts'
import type { InputPortContext } from '../../../../../vendor/lazy-harness-monitoring/packages/core/src/host/index.ts'
import { readMonitoringAttachConfig, parseMonitoringAttachConfig, type MonitoringAttachConfig } from './config.ts'
import { createHostReadRecords } from './read-records.ts'
import { classifierFromContext, createPiModelBinding, type ClassifierModel, type ClassifierRuntime } from './model.ts'
import { admitCatalog, captureRecord } from './catalog.ts'
import { createObservation } from './observation.ts'
import { observationHash } from './observe-log.ts'

export const MONITORING_ROOT = fileURLToPath(new URL('../../../../../vendor/lazy-harness-monitoring/', import.meta.url))
// Major support is independent of availability/activation. Full inventory required by module loader.
/** Long real sessions exceed the observer's default maxMessages (128) and would mark every snapshot unavailable.
 * Tail mode keeps the newest messages within the byte bound so the snapshot stays available; U1 reads only
 * its since-last region, so 32 messages is enough. */
export const OBSERVER_LIMITS = Object.freeze({ tailMessages: 32 })
/** The realtime selection job deadline defaults to 1 s, shorter than a real Jev judgement on a full U1 view (~1.1 s
 * observed live), which aborted the call and stopped the classifier. The job deadline must cover the model timeout. */
export const JOB_TIMEOUT_MARGIN_MS = 2000
/** Renew the selection pipeline at the next user input once its window has observed this many frames (module limit 2048). */
export const WINDOW_RENEW_EVENTS = 1024
export const HOST_PORT_MAJORS: PortMajors = Object.freeze({ 'worker.execution': 1, 'judgement.model': 1, 'session.read-records': 1, 'report.enqueue': 1, 'state.persistence': 1, 'memory.review-sink': 1, 'memory.source': 1, 'policy.registry': 1, 'rule.verifier': 1 })
export const UNAVAILABLE_PORTS = Object.freeze(['memory.review-sink', 'memory.source', 'policy.registry', 'rule.verifier'])
type PiHooks = Parameters<typeof attachPiFrames>[0]
export type AttachOptions = { root: string; config?: MonitoringAttachConfig; moduleRoot?: string; majors?: PortMajors; classifier?: { runtime: ClassifierRuntime; model: ClassifierModel } }
/** Guarded composition. The off path loads/validates the manifest but installs ZERO monitoring handlers. */
export function attachMonitoringPhase1(pi: PiHooks, options: AttachOptions) {
  return startMonitoringComposition(options.moduleRoot ?? MONITORING_ROOT, options.majors ?? HOST_PORT_MAJORS, () => {
    const config = options.config ? parseMonitoringAttachConfig(options.config) : readMonitoringAttachConfig(options.root)
    if (config.references.stage === 'off') return { stage: 'off' as const, async close() {}, async idle() {} }
    if (config.references.stage !== 'observe' || !options.classifier) throw Error('observe requires an admitted Pi classifier')
    return composeObserve(pi, options.root, config, options.classifier)
  })
}
function composeObserve(pi: PiHooks, root: string, config: MonitoringAttachConfig, classifier: NonNullable<AttachOptions['classifier']>) {
  const catalog = admitCatalog(root, config), observation = createObservation(root, config)
  let context: InputPortContext | undefined, closed = false, started = false, paused = false, reason: string | null = 'awaiting_session_start'
  let generation = 0, branch = 1, compaction = 1, sessionId = ''
  const draining = new Set<Promise<void>>()
  const reads = createHostReadRecords(() => !closed && catalog.isCurrent() ? context : undefined), port = bindReadRecordPort(exposeReadRecordPort(reads.port))
  const registration = references.createReferencesRegistration({ stage: 'observe', maxStage: 'observe', readRecords: { port, request(t, signal) {
    if (!context) throw Error('input scope unavailable')
    return { protocolVersion: 1, scope: context.scope, sourceRevision: context.sourceRevision, grantRevision: context.grantRevision, cursor: context.completeThroughCursor, sourceEventId: t.eventId, documents: t.evidence.filter(e => e.kind === 'knowledge').map(e => ({ documentId: e.id, documentVersion: e.version })), signal }
  } } })
  const binding = { ...references.referencesBinding, declaration: registration.declaration, declarationHash: registration.declarationHash }
  prepareMonitoringBindings({ contractVersion: 1, source: { kind: 'host-events', scope: 'host-supplied-events' }, goal: 'Supply admitted project records for the current request', receiver: 'parent', judge: 'jev', modules: [{ id: registration.moduleId, version: binding.version, settings: {}, stage: 'observe' }] }, {
    modules: { [registration.moduleId]: binding }, judges: { jev: async () => ({}) }, allowedSourceScopes: ['host-supplied-events'], maxModules: 1, capabilities: piHostCapabilities,
    inputPorts: { [registration.moduleId]: { 'already-read': { adapter: 'session.read-records', protocolVersion: 1, port } } },
  })
  const model = createPiModelBinding(classifier.runtime, classifier.model, config.budget, observation.exchange, () => generation)
  observation.configure(catalog.documents, model.remaining)
  const mailbox = new ContextCarryMailbox({ maxAgeMs: 30000, maxCarryTurns: 0, maxItems: 16, maxTextBytes: 16384, sourceVersion: catalog.sourceVersion })
  const delivery = createParentReportDelivery({ mailbox, sourceVersion: catalog.sourceVersion })
  const report = bindReportPort(exposeReportPort(r => ({ reportId: monitoringReportId(r), status: 'failed', reason: closed ? 'closed' : 'phase1-observe' })))
  const worker = createHandlerWorkerPort(registration.handlers, { maxActive: 1, maxQueued: 0, maxWork: 64 })
  const runtime = new MonitoringModuleRuntime({ modules: [registration], handlers: registration.handlers, workerPort: worker, budget: new ApprovedBudgetGate(), report })
  function makePipeline() {
    const epoch = generation
    const instance = createRealtimeSelectionPipeline({ enabled: true, realtimeLimits: { jobTimeoutMs: config.budget.timeoutMs + JOB_TIMEOUT_MARGIN_MS }, material: { allowedKinds: binding.grants.referenceKinds, references: catalog.documents, historyMode: 'since-last' }, selection: {
    ...model, trace: row => { if (epoch === generation && !closed && !paused) observation.trace(row, instance.selection.traces, instance.window.traces); else if (row.type === 'judgement') observation.discard(String(row.frameId)) },
    goal: 'Supply admitted project records for the current request', isPermitted: () => epoch === generation && !closed && !paused && !!context?.available && catalog.isCurrent(),
    modules: [{ id: registration.moduleId, watchEvents: ['input'], referenceKinds: binding.grants.referenceKinds, grants: binding.grants, question: references.referencesQuestion, destination: 'parent.context', compactRegion: true }],
  } })
    return instance
  }
  let pipeline = makePipeline()
  const observer = new PiMonitoringObserver(() => undefined, OBSERVER_LIMITS)
  const makeAttestor = () => createReadResultAttestor({ context: () => !closed && catalog.isCurrent() ? context : undefined, captureIdentity: () => closed ? undefined : { id: canonicalJsonHash([root, context?.scope]), epoch: 1 }, format: () => config.readFormat,
    capture(read) { const d = catalog.documents.find(d => resolve(root, d.path) === resolve(read.cwd, read.call.input.path)); return d && catalog.isCurrent() ? captureRecord(root, d.path) : undefined },
    resolveDocument(read, hash) { const d = catalog.documents.find(d => resolve(root, d.path) === resolve(read.cwd, read.call.input.path) && d.version === hash); return d ? { documentId: d.id, documentVersion: d.version, namespace: 'lazy-harness', sourceRecordId: d.path } : undefined }, record: reads.record,
  })
  let attestor = makeAttestor(), needsPipeline = false, windowRenewals = 0
  function retire() {
    generation++; context = undefined; attestor.close()
    if (!needsPipeline) {
      const old = pipeline; old.dispose()
      const drain = old.idle().catch(() => { /* cleanup remains advisory */ }).finally(() => draining.delete(drain)); draining.add(drain)
    }
    needsPipeline = true
  }
  function stop(why = 'closed') { if (closed) return; closed = true; reason = why; retire(); reads.close(); runtime.dispose(); observer.close() }
  const fences = new Set(['session_before_switch', 'session_before_fork', 'session_before_tree', 'session_tree', 'session_before_compact', 'session_compact', 'session_compact_failed', 'session_shutdown'])
  // Synchronous invalidation, asynchronous physical drain; never wait inside lifecycle hooks.
  for (const name of fences) pi.on(name, () => {
    if (closed) return undefined
    if (name === 'session_shutdown') { stop('session_shutdown'); return undefined }
    retire(); reason = name
    if (name.includes('compact')) compaction++; else branch++
    paused = name.startsWith('session_before_')
    return undefined
  })
  createPiObservationExtension({ enabled: true, observer })(pi)
  const detach = attachPiFrames(pi, observer, { halt: () => { if (!closed) stop('missing_source_frame') }, accept(frame, progress) {
    if (closed) return
    observation.frame(frame)
    if (frame.sourceEvent === 'session_start' && started) { stop('session_replaced_reload_required'); return }
    if (frame.sourceEvent === 'session_start') { started = true; sessionId = frame.sessionId; reason = null }
    if (fences.has(frame.sourceEvent)) return
    if (paused) return
    if (!started || sessionId !== frame.sessionId || !catalog.isCurrent()) { stop('scope_or_catalog_unavailable'); return }
    // Distinct reason: an unavailable snapshot/payload is not a scope or catalog change.
    if (!frame.available || !frame.snapshot.available) { stop('frame_unavailable'); return }
    // The module window and coordinator each stop permanently after maxEvents (2048) frames, and every Pi event counts
    // (streaming deltas included), so a long session silently stops judging. Renew at a user-input boundary: the
    // old pipeline is retired like a fence (late results discarded), the session model budget is NOT reset.
    if (frame.sourceEvent === 'input' && !needsPipeline) {
      const ws = pipeline.window.getStatus() as any
      if (ws.state === 'stopped' || ws.observed >= WINDOW_RENEW_EVENTS) { retire(); windowRenewals++ }
    }
    const scope = { sessionId: frame.sessionId, bindingGeneration: frame.binding, branchId: frame.snapshot.leafId ?? 'root', branchGeneration: branch, compactionGeneration: compaction }
    if (needsPipeline) {
      pipeline = makePipeline(); attestor = makeAttestor(); needsPipeline = false
      // Public start ports admit the real next frame without fabricating a session_start.
      const start = { sessionId: frame.sessionId, binding: frame.binding, afterCursor: frame.cursor - 1 }
      pipeline.window.start(start); pipeline.coordinator.start(start); reason = null
    }
    context = { scope, sourceRevision: canonicalJsonHash(catalog.documents.map(d => [d.id, d.version])), grantRevision: 'phase1-u1-observe-v1', completeThroughCursor: frame.cursor, available: true }
    // Hook provenance is main-session only. This feed never accepts Reader/worker summaries.
    const p = frame.payload as any
    if (frame.sourceEvent === 'tool_call' && p.toolName === 'read') attestor.start({ toolCallId: p.toolCallId, toolName: p.toolName, input: p.input }, root, 'main-agent')
    if (frame.sourceEvent === 'tool_result' && p.toolName === 'read') attestor.complete({ toolCallId: p.toolCallId, toolName: p.toolName, input: p.input, content: p.content, isError: p.isError }, root, 'main-agent', frame.cursor)
    pipeline.accept(frame, progress)
  } })
  // Observe cannot enqueue or inject. Keep the module-owned route uninstalled until a later active approval.
  return { stage: 'observe' as const, reads, port, report, worker, runtime, get pipeline() { return pipeline }, delivery,
    status() { return { attached: !closed && !paused, stage: 'observe', reason, window: (() => { const w = pipeline.window.getStatus() as any, t = pipeline.window.traces; return { state: w.state, sources: w.sources, bytes: w.bytes, lastReason: t.at(-1)?.reason ?? null, renewals: windowRenewals } })(), scope: context ? { sessionIdHash: observationHash(context.scope.sessionId), bindingGeneration: context.scope.bindingGeneration, branchGeneration: branch, compactionGeneration: compaction } : null, generation, catalog: { documents: catalog.documents.map(d => ({ id: d.id, version: d.version })), totalBytes: catalog.documents.reduce((n, d) => n + Buffer.byteLength(d.content), 0) }, watchEvents: ['input'], budget: { used: { ...model.usage }, remaining: model.remaining() }, counters: { ...observation.counters, errors: observation.counters.errors + observation.log.stats.errors }, lastOutcomes: [...observation.recent], log: { path: observation.log.path(), ...observation.log.stats }, classifierStopped: model.stopped } },
    async idle() { await pipeline.idle(); await Promise.all([...draining]); await runtime.idle(); await observer.idle(); await observation.log.idle() },
    async close() { detach(); stop(); await pipeline.idle(); await Promise.all([...draining]); await runtime.idle(); await observer.idle(); await observation.log.idle() },
  }
}
/** Extension startup is synchronous/off by default; the running Pi's registry is used only in explicit observe. */
export function installMonitoringPhase1(pi: ExtensionAPI, root: string) {
  const config = startMonitoringComposition(MONITORING_ROOT, HOST_PORT_MAJORS, () => readMonitoringAttachConfig(root))
  if (config.references.stage === 'off') return
  let owner: ReturnType<typeof attachMonitoringPhase1> | undefined
  const handlers = new Map<string, Array<(event: any, ctx: any) => unknown>>()
  const scopedPi = { on(name: string, handler: (event: any, ctx: any) => unknown) { const list = handlers.get(name) ?? []; list.push(handler); handlers.set(name, list); return () => { const i = list.indexOf(handler); if (i >= 0) list.splice(i, 1) } } }
  pi.registerCommand?.('monitoring', { description: 'Read-only monitoring status (no model calls)', handler: async (args, ctx) => {
    if (args.trim() && args.trim() !== 'status') { ctx.ui.notify('Usage: /monitoring status', 'info'); return }
    ctx.ui.notify(JSON.stringify(owner?.stage === 'observe' ? owner.status() : { attached: false, stage: 'observe', reason: 'awaiting_session_start' }, null, 2), 'info')
  } })
  // Register synchronously; forward the actual session_start only AFTER context registry admission.
  // No fabricated frame/session or handler added too late to see its initiating event.
  for (const name of observationEvents) (pi.on as any)(name, async (event: any, ctx: any) => {
    if (name === 'session_start' && !owner) {
      owner = attachMonitoringPhase1(scopedPi, { root, config, classifier: classifierFromContext(ctx) })
    }
    for (const handler of [...(handlers.get(name) ?? [])]) await handler(event, ctx)
    if (name === 'session_shutdown') void owner?.close().catch(() => { /* never delay Pi shutdown on physical model drain */ })
    return undefined
  })
}
