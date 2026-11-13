import { constants } from 'node:fs'
import { mkdir, lstat, open, readdir, unlink, realpath } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { homedir } from 'node:os'
import { dirname, isAbsolute, join, relative, resolve } from 'node:path'

export const observationHash = (value: string) => createHash('sha256').update(value).digest('hex')
export type ObserveOutcome = {
  schema: 'lazy-harness-observe/v1'; time: string; sessionIdHash: string; bindingGeneration: number
  frameId: string; eventId: string; trigger: string; outcome: 'judged' | 'skipped' | 'refused' | 'failed' | 'compaction'
  decisionMode: 'run' | 'skip' | 'defer' | null; confidence: number | null
  selectedDocuments: Array<{ id: string; version: string }>; candidateCount: number
  compaction: { kept: number | null; dropped: number | null; withinBudget: boolean } | null
  modelCalls: number; reportedUsd: number | null; reportedTokens: number | null; latencyMs: number
  budgetRemaining: { calls: number; usd: number; tokens: number }; errorClass: string | null
}
/** Metadata-only sink. Never pass raw trace/exchange objects to this boundary. Bounded asynchronous queue. */
export function createObserveLog(root: string, setting?: false | string, options: { now?: () => number; maxBytes?: number } = {}) {
  const now = options.now ?? Date.now, maxBytes = options.maxBytes ?? 2 * 1024 * 1024
  const base = resolve(setting || join(process.env.XDG_STATE_HOME || join(homedir(), '.local/state'), 'lazy-harness/monitoring/observe'))
  const dir = join(base, observationHash(resolve(root)))
  const stats = { written: 0, dropped: 0, errors: 0 }
  let pending = Promise.resolve(), queued = 0
  const path = () => setting === false ? null : join(dir, new Date(now()).toISOString().slice(0, 10) + '.jsonl')
  async function prepare() {
    // Reject project/Git locations and symlink components, including custom paths.
    const project = await realpath(root)
    const rel = relative(project, dir)
    if (!rel || (!rel.startsWith('..' + '/') && rel !== '..' && !isAbsolute(rel))) throw Error('project log path')
    const chain: string[] = []
    for (let p = dir; ; p = dirname(p)) { chain.unshift(p); if (dirname(p) === p) break }
    for (const p of chain) {
      const st = await lstat(p).catch((e: NodeJS.ErrnoException) => { if (e.code !== 'ENOENT') throw e; return undefined })
      if (st && (!st.isDirectory() || st.isSymbolicLink())) throw Error('unsafe log directory')
      if (await lstat(join(p, '.git')).then(() => true, (e: NodeJS.ErrnoException) => { if (e.code !== 'ENOENT') throw e; return false })) throw Error('Git log path')
      if (!st) await mkdir(p, { mode: 0o700 }).catch((e: NodeJS.ErrnoException) => { if (e.code !== 'EEXIST') throw e })
      if (p === base) { const d = await open(p, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_DIRECTORY); try { await d.chmod(0o700) } finally { await d.close() } }
    }
    const d = await open(dir, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_DIRECTORY)
    try { await d.chmod(0o700) } finally { await d.close() }
    for (const f of await readdir(dir)) if (/^\d{4}-\d{2}-\d{2}\.jsonl$/.test(f) && Date.parse(f.slice(0, 10) + 'T00:00:00Z') < now() - 14 * 86400000) await unlink(join(dir, f))
  }
  return { stats, path,
    write(row: ObserveOutcome) {
      if (setting === false) return
      if (queued >= 64) { stats.dropped++; return }
      // Explicit top-level whitelist; unknown fields (including future trace bodies) cannot escape.
      const { schema, time, sessionIdHash, bindingGeneration, frameId, eventId, trigger, outcome, decisionMode, confidence, selectedDocuments, candidateCount, compaction, modelCalls, reportedUsd, reportedTokens, latencyMs, budgetRemaining, errorClass } = row
      const line = JSON.stringify({ schema, time, sessionIdHash, bindingGeneration, frameId, eventId, trigger, outcome, decisionMode, confidence, selectedDocuments: selectedDocuments.map(({ id, version }) => ({ id, version })), candidateCount, compaction: compaction && { kept: compaction.kept, dropped: compaction.dropped, withinBudget: compaction.withinBudget }, modelCalls, reportedUsd, reportedTokens, latencyMs, budgetRemaining: { calls: budgetRemaining.calls, usd: budgetRemaining.usd, tokens: budgetRemaining.tokens }, errorClass }) + '\n'
      queued++
      pending = pending.then(async () => {
        await prepare()
        const file = await open(path()!, constants.O_APPEND | constants.O_CREAT | constants.O_WRONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK, 0o600)
        try {
          const st = await file.stat(); if (!st.isFile()) throw Error('unsafe log file')
          await file.chmod(0o600)
          if (st.size + Buffer.byteLength(line) > maxBytes) { stats.dropped++; return }
          await file.writeFile(line); stats.written++
        } finally { await file.close() }
      }).catch(() => { stats.errors++ }).finally(() => { queued-- })
    },
    async idle() { await pending },
  }
}
