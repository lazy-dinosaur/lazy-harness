import { judgementEntriesFromExchange } from '../../../../../vendor/lazy-harness-monitoring/packages/core/src/engine/monitoring-engine-judgement-log.ts'
import { createObserveLog, observationHash, type ObserveOutcome } from './observe-log.ts'
import type { MonitoringAttachConfig } from './config.ts'

type Frame = { id: string; sessionId: string; binding: number; sourceEvent: string }
type Summary = { frame: Frame; at: number; calls: number; usd: number | null; tokens: number | null; mode: ObserveOutcome['decisionMode']; confidence: number | null; selected: string[]; failed: boolean; compactCalls: number; compactUsd: number | null; compactTokens: number | null }
/** Host projection of public module trace/notes and judgement-log codec. No bodies/reasons retained. */
export function createObservation(root: string, config: MonitoringAttachConfig) {
  const log = createObserveLog(root, config.observeLog), frames = new Map<string, Summary>()
  const counters = { framesSeen: 0, judgements: 0, runs: 0, skips: 0, defers: 0, compactions: 0, errors: 0 }
  const recent: Array<Pick<ObserveOutcome, 'frameId' | 'eventId' | 'outcome' | 'decisionMode' | 'selectedDocuments'>> = []
  let remaining = () => ({ calls: 0, usd: 0, tokens: 0 })
  const finite = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v) && v >= 0
  function emit(s: Summary, outcome: ObserveOutcome['outcome'], errorClass: string | null, compaction: ObserveOutcome['compaction'] = null) {
    const row: ObserveOutcome = { schema: 'lazy-harness-observe/v1', time: new Date().toISOString(), sessionIdHash: observationHash(s.frame.sessionId), bindingGeneration: s.frame.binding, frameId: s.frame.id, eventId: s.frame.id, trigger: s.frame.sourceEvent, outcome, decisionMode: s.mode, confidence: s.confidence, selectedDocuments: config.catalog.filter(d => s.selected.includes(d.id)).map(d => ({ id: d.id, version: versions.get(d.id)! })), candidateCount: config.catalog.length, compaction, modelCalls: s.calls, reportedUsd: s.usd, reportedTokens: s.tokens, latencyMs: Math.max(0, performance.now() - s.at), budgetRemaining: remaining(), errorClass }
    if (outcome === 'judged') { counters.judgements++; if (s.mode === 'run') counters.runs++; if (s.mode === 'skip') counters.skips++; if (s.mode === 'defer') counters.defers++ }
    if (outcome === 'failed') counters.errors++
    if (outcome === 'compaction') counters.compactions++
    recent.push({ frameId: row.frameId, eventId: row.eventId, outcome, decisionMode: row.decisionMode, selectedDocuments: row.selectedDocuments }); if (recent.length > 5) recent.shift()
    log.write(row)
  }
  const versions = new Map<string, string>()
  return { log, counters, recent,
    configure(documents: readonly { id: string; version: string }[], budget: typeof remaining) { documents.forEach(d => versions.set(d.id, d.version)); remaining = budget },
    frame(frame: Frame) { counters.framesSeen++; frames.set(frame.id, { frame: { id: frame.id, sessionId: frame.sessionId, binding: frame.binding, sourceEvent: frame.sourceEvent }, at: performance.now(), calls: 0, usd: null, tokens: null, mode: null, confidence: null, selected: [], failed: false, compactCalls: 0, compactUsd: null, compactTokens: null }); if (frames.size > 256) frames.delete(frames.keys().next().value!) },
    exchange(request: any, value: any, _latencyMs: number, error: boolean) {
      // Public helper parses the native choice/bool exchange; discard text, reasons and input digest immediately.
      for (const entry of judgementEntriesFromExchange(request, value?.answers ?? {}, { at: Date.now(), sessionId: '', eventId: '' })) {
        const task = request.body.state.tasks.find((t: any) => t.processorId === entry.moduleId)
        const id = task?.view?.event?.id
        const compact = typeof id === 'string' && id.endsWith(':compact')
        const s = frames.get(compact ? id.slice(0, -8) : id); if (!s) continue
        if (compact) {
          s.compactCalls++
          if (finite(value?.usage?.totalTokens)) s.compactTokens = (s.compactTokens ?? 0) + value.usage.totalTokens
          if (finite(value?.usage?.cost?.total)) s.compactUsd = (s.compactUsd ?? 0) + value.usage.cost.total
          continue
        }
        s.calls++; s.failed ||= error
        const u = value?.usage
        if (finite(u?.totalTokens)) s.tokens = (s.tokens ?? 0) + u.totalTokens
        if (finite(u?.cost?.total)) s.usd = (s.usd ?? 0) + u.cost.total
        if (['run', 'skip', 'defer'].includes(entry.decision)) s.mode = entry.decision as Summary['mode']
        s.confidence = finite(entry.confidence) && entry.confidence <= 1 ? entry.confidence : null
        s.selected = entry.offered.filter(r => r.selected && versions.has(r.id)).map(r => r.id)
      }
    },
    trace(row: Readonly<Record<string, unknown> & { type: string }>, notes: readonly { frameId: string; status: string }[]) {
      const s = frames.get(String(row.frameId)); if (!s) return
      if (row.type === 'judgement') {
        const note = notes.findLast(n => n.frameId === s.frame.id && n.status.startsWith('region_'))
        const input = row.input as any
        if (note) { const withinBudget = note.status === 'region_within_budget', kept = withinBudget ? input?.compactionCandidates : input?.compactionKept, candidates = input?.compactionCandidates; emit({ ...s, calls: s.compactCalls, mode: null, confidence: null, selected: [], usd: s.compactUsd, tokens: s.compactTokens }, 'compaction', note.status === 'region_compaction_failed' ? 'compaction_failed' : null, { kept: finite(kept) ? kept : null, dropped: finite(candidates) && finite(kept) ? Math.max(0, candidates - kept) : null, withinBudget }) }
        const outcome = (row.outcomes as any[])?.[0]
        // Core-decoded decisions, not raw provider answers, determine the final mode.
        s.mode = ['run', 'skip', 'defer'].includes(outcome?.mode) ? outcome.mode : null
        emit(s, s.failed ? 'failed' : s.mode ? 'judged' : 'refused', s.failed ? 'classifier_uncertain' : s.mode ? null : 'no_admitted_decision')
      } else if (row.type === 'selection') emit(s, String(row.status).includes('failed') || String(row.status).includes('rejected') ? 'failed' : 'skipped', 'selection_' + String(row.status))
    },
    discard(frameId: string) { const s = frames.get(frameId); if (s) emit({ ...s, mode: null, selected: [] }, 'skipped', 'stale_scope') },
  }
}
