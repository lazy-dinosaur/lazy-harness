import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'
import type { ExtensionAPI } from '@earendil-works/pi-coding-agent'
import { startMonitoringComposition, references, prepareMonitoringBindings, createHandlerWorkerPort, bindReadRecordPort, exposeReadRecordPort, bindReportPort, exposeReportPort, canonicalJsonHash, type PortMajors } from '../../../../../vendor/lazy-harness-monitoring/composition.ts'
import { createPiInputPortGenerations, createPiObservationExtension, PiMonitoringObserver, attachPiFrames, piHostCapabilities, createParentReportDelivery, createReadResultAttestor, observationEvents } from '../../../../../vendor/lazy-harness-monitoring/hosts/pi/src/index.ts'
import { createRealtimeSelectionPipeline } from '../../../../../vendor/lazy-harness-monitoring/packages/core/src/engine/monitoring-core-realtime-selection.ts'
import { MonitoringModuleRuntime, ApprovedBudgetGate, monitoringReportId } from '../../../../../vendor/lazy-harness-monitoring/packages/core/src/engine/monitoring-engine-runtime.ts'
import { ContextCarryMailbox } from '../../../../../vendor/lazy-harness-monitoring/packages/core/src/engine/monitoring-core-context-mailbox.ts'
import type { InputPortContext } from '../../../../../vendor/lazy-harness-monitoring/packages/core/src/host/index.ts'
import { readMonitoringAttachConfig, parseMonitoringAttachConfig, type MonitoringAttachConfig } from './config.ts'
import { createHostReadRecords } from './read-records.ts'
import { classifierFromContext, createPiModelBinding, type ClassifierModel, type ClassifierRuntime } from './model.ts'
import { admitCatalog, captureRecord } from './catalog.ts'

export const MONITORING_ROOT = fileURLToPath(new URL('../../../../../vendor/lazy-harness-monitoring/', import.meta.url))
// Major support is independent of availability/activation. Full inventory required by module loader.
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
  const catalog = admitCatalog(root, config), generations = createPiInputPortGenerations()
  let context: InputPortContext | undefined, closed = false, started = false
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
  const model = createPiModelBinding(classifier.runtime, classifier.model, config.budget)
  const mailbox = new ContextCarryMailbox({ maxAgeMs: 30000, maxCarryTurns: 0, maxItems: 16, maxTextBytes: 16384, sourceVersion: catalog.sourceVersion })
  const delivery = createParentReportDelivery({ mailbox, sourceVersion: catalog.sourceVersion })
  const report = bindReportPort(exposeReportPort(r => ({ reportId: monitoringReportId(r), status: 'failed', reason: closed ? 'closed' : 'phase1-observe' })))
  const worker = createHandlerWorkerPort(registration.handlers, { maxActive: 1, maxQueued: 0, maxWork: 64 })
  const runtime = new MonitoringModuleRuntime({ modules: [registration], handlers: registration.handlers, workerPort: worker, budget: new ApprovedBudgetGate(), report })
  const pipeline = createRealtimeSelectionPipeline({ enabled: true, material: { allowedKinds: binding.grants.referenceKinds, references: catalog.documents, historyTurns: 4, historyMode: 'since-last' }, selection: {
    ...model, goal: 'Supply admitted project records for the current request', isPermitted: () => !closed && !!context?.available && catalog.isCurrent(),
    modules: [{ id: registration.moduleId, watchEvents: ['input'], referenceKinds: binding.grants.referenceKinds, grants: binding.grants, question: references.referencesQuestion, destination: 'parent.context', compactRegion: true }],
  } })
  const observer = new PiMonitoringObserver(() => undefined)
  const attestor = createReadResultAttestor({ context: () => !closed && catalog.isCurrent() ? context : undefined, captureIdentity: () => closed ? undefined : { id: canonicalJsonHash([root, context?.scope]), epoch: 1 }, format: () => config.readFormat,
    capture(read) { const d = catalog.documents.find(d => resolve(root, d.path) === resolve(read.cwd, read.call.input.path)); return d && catalog.isCurrent() ? captureRecord(root, d.path) : undefined },
    resolveDocument(read, hash) { const d = catalog.documents.find(d => resolve(root, d.path) === resolve(read.cwd, read.call.input.path) && d.version === hash); return d ? { documentId: d.id, documentVersion: d.version, namespace: 'lazy-harness', sourceRecordId: d.path } : undefined }, record: reads.record,
  })
  function stop() { if (closed) return; closed = true; context = undefined; generations.close(); attestor.close(); reads.close(); runtime.dispose(); pipeline.dispose(); observer.close() }
  const fences = new Set(['session_before_switch', 'session_before_fork', 'session_before_tree', 'session_tree', 'session_before_compact', 'session_compact', 'session_compact_failed', 'session_shutdown'])
  // Fences are notification-only and precede sources/delivery; failed boundaries stay closed until reload.
  for (const name of fences) pi.on(name, () => { stop(); return undefined })
  generations.extension(pi)
  createPiObservationExtension({ enabled: true, observer })(pi)
  const detach = attachPiFrames(pi, observer, { halt: stop, accept(frame, progress) {
    if (closed) return
    if (frame.sourceEvent === 'session_start' && started) { stop(); return }
    if (frame.sourceEvent === 'session_start') started = true
    const scope = generations.current()
    if (!scope || !frame.available || !frame.snapshot.available || scope.sessionId !== frame.sessionId || scope.bindingGeneration !== frame.binding || !catalog.isCurrent()) { stop(); return }
    context = { scope, sourceRevision: canonicalJsonHash(catalog.documents.map(d => [d.id, d.version])), grantRevision: 'phase1-u1-observe-v1', completeThroughCursor: frame.cursor, available: true }
    // Hook provenance is main-session only. This feed never accepts Reader/worker summaries.
    const p = frame.payload as any
    if (frame.sourceEvent === 'tool_call' && p.toolName === 'read') attestor.start({ toolCallId: p.toolCallId, toolName: p.toolName, input: p.input }, root, 'main-agent')
    if (frame.sourceEvent === 'tool_result' && p.toolName === 'read') attestor.complete({ toolCallId: p.toolCallId, toolName: p.toolName, input: p.input, content: p.content, isError: p.isError }, root, 'main-agent', frame.cursor)
    pipeline.accept(frame, progress)
  } })
  // Observe cannot enqueue or inject. Keep the module-owned route uninstalled until a later active approval.
  return { stage: 'observe' as const, reads, port, report, worker, runtime, pipeline, delivery,
    async idle() { await pipeline.idle(); await runtime.idle(); await observer.idle() },
    async close() { detach(); stop(); await pipeline.idle(); await runtime.idle(); await observer.idle() },
  }
}
/** Extension startup is synchronous/off by default; the running Pi's registry is used only in explicit observe. */
export function installMonitoringPhase1(pi: ExtensionAPI, root: string) {
  const config = startMonitoringComposition(MONITORING_ROOT, HOST_PORT_MAJORS, () => readMonitoringAttachConfig(root))
  if (config.references.stage === 'off') return
  let owner: ReturnType<typeof attachMonitoringPhase1> | undefined
  const handlers = new Map<string, Array<(event: any, ctx: any) => unknown>>()
  const scopedPi = { on(name: string, handler: (event: any, ctx: any) => unknown) { const list = handlers.get(name) ?? []; list.push(handler); handlers.set(name, list); return () => { const i = list.indexOf(handler); if (i >= 0) list.splice(i, 1) } } }
  // Register synchronously; forward the actual session_start only AFTER context registry admission.
  // No fabricated frame/session or handler added too late to see its initiating event.
  for (const name of observationEvents) (pi.on as any)(name, async (event: any, ctx: any) => {
    if (name === 'session_start' && !owner) {
      owner = attachMonitoringPhase1(scopedPi, { root, config, classifier: classifierFromContext(ctx) })
    }
    for (const handler of [...(handlers.get(name) ?? [])]) await handler(event, ctx)
    if (name === 'session_shutdown') await owner?.close()
    return undefined
  })
}
