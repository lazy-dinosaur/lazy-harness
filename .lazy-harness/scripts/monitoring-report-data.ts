// Offline, explicit metadata projection. Never copy unknown objects into a report.
type Obj = Record<string, any>
const obj = (v: unknown): Obj => v && typeof v === 'object' && !Array.isArray(v) ? v : {}
const text = (v: unknown) => typeof v === 'string' && v.length <= 512 ? v : null
const num = (v: unknown) => typeof v === 'number' && Number.isFinite(v) && v >= 0 ? v : null
const pick = (v: unknown, strings: string[], numbers: string[] = []) => {
  const o = obj(v), result: Obj = {}
  for (const k of strings) if (text(o[k]) !== null) result[k] = o[k]
  for (const k of numbers) if (num(o[k]) !== null) result[k] = o[k]
  return result
}
const documents = (v: unknown, second = 'version') => Array.isArray(v) ? v.slice(0, 16).map(d => pick(d, ['id', second])) : []
const budgetKeys = ['maxCalls', 'maxConcurrent', 'maxQueued', 'timeoutMs', 'maxInputBytes', 'maxOutputBytes', 'maxOutputTokens', 'maxReservedTokens', 'maxReservedUsd']
export function projectConfig(value: unknown) {
  const v = obj(value)
  return { stage: ['off', 'observe'].includes(obj(v.references).stage) ? v.references.stage : 'unknown', catalog: documents(v.catalog, 'path'), readFormat: ['unknown', 'pi-read-text-v1', 'pi-hashline-edit-pro-v1'].includes(v.readFormat) ? v.readFormat : 'unknown', budget: pick(v.budget, [], budgetKeys) }
}
export function projectObserve(value: unknown): Obj | null {
  const v = obj(value)
  if (v.schema !== 'lazy-harness-observe/v1') return null
  const result: Obj = { ...pick(v, ['schema', 'time', 'sessionIdHash', 'frameId', 'eventId', 'trigger', 'errorClass'], ['bindingGeneration', 'confidence', 'candidateCount', 'modelCalls', 'reportedUsd', 'reportedTokens', 'latencyMs']), outcome: ['judged', 'skipped', 'refused', 'failed', 'compaction'].includes(v.outcome) ? v.outcome : null, decisionMode: ['run', 'skip', 'defer'].includes(v.decisionMode) ? v.decisionMode : null, selectedDocuments: documents(v.selectedDocuments), budgetRemaining: pick(v.budgetRemaining, [], ['calls', 'usd', 'tokens']) }
  for (const k of ['confidence', 'reportedUsd', 'reportedTokens', 'errorClass']) result[k] ??= null
  result.compaction = v.compaction ? { ...pick(v.compaction, [], ['kept', 'dropped']), withinBudget: typeof v.compaction.withinBudget === 'boolean' ? v.compaction.withinBudget : null } : null
  return result
}
export function projectStatus(value: unknown): Obj {
  const v = obj(value), result: Obj = pick(v, ['stage', 'reason', 'installHint'], ['generation'])
  for (const k of ['attached', 'classifierStopped']) if (typeof v[k] === 'boolean') result[k] = v[k]
  result.window = pick(v.window, ['state', 'lastReason'], ['sources', 'bytes', 'renewals'])
  result.scope = v.scope ? pick(v.scope, ['sessionIdHash'], ['bindingGeneration', 'branchGeneration', 'compactionGeneration']) : null
  result.catalog = { documents: documents(obj(v.catalog).documents), ...pick(v.catalog, [], ['totalBytes']) }
  result.watchEvents = Array.isArray(v.watchEvents) ? v.watchEvents.filter((s: unknown) => s === 'input') : []
  result.budget = { used: pick(obj(v.budget).used, ['lastFailure'], ['calls', 'tokens', 'usd', 'active', 'errors', 'reportedTokens', 'reportedUsd']), remaining: pick(obj(v.budget).remaining, [], ['calls', 'usd', 'tokens']) }
  result.counters = pick(v.counters, [], ['framesSeen', 'judgements', 'runs', 'skips', 'defers', 'compactions', 'errors'])
  result.lastOutcomes = Array.isArray(v.lastOutcomes) ? v.lastOutcomes.slice(-5).map((r: unknown) => { const o = obj(r); return { ...pick(o, ['frameId', 'eventId', 'outcome', 'decisionMode', 'errorClass']), selectedDocuments: documents(o.selectedDocuments) } }) : []
  result.log = pick(v.log, ['path'], ['written', 'dropped', 'errors'])
  return result
}
/** Refuse the entire outbound artifact, not just the matching substring. Never echo the match. */
export function privacy(text: string, home: string): string {
  if (/sk-|ghp_|github_pat_|\bBearer\b|api[_-]?key\s*=|-----BEGIN[^\r\n]*PRIVATE KEY-----/i.test(text)) throw Error('credential pattern detected; report refused')
  const safe = home && home !== '/' ? text.split(home).join('~') : text
  return safe.replace(/[\u001b\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, '')
}
export function summarize(rows: Obj[]) {
  const counts = (key: string) => {
    const m = new Map<string, number>()
    for (const r of rows) { const k = String(r[key] ?? '(none)'); m.set(k, (m.get(k) ?? 0) + 1) }
    return [...m].sort(([a], [b]) => a.localeCompare(b))
  }
  const latencies = rows.map(r => r.latencyMs).filter(n => num(n) !== null).sort((a, b) => a - b)
  const percentile = (p: number) => latencies.length ? latencies[Math.max(0, Math.ceil(latencies.length * p) - 1)] : null
  const usd = rows.filter(r => num(r.reportedUsd) !== null)
  return { outcome: counts('outcome'), mode: counts('decisionMode'), errorClass: counts('errorClass'), calls: rows.reduce((n, r) => n + (num(r.modelCalls) ?? 0), 0), usd: usd.length ? usd.reduce((n, r) => n + r.reportedUsd, 0) : null, usdMissing: rows.length - usd.length, p50: percentile(.5), p95: percentile(.95) }
}
