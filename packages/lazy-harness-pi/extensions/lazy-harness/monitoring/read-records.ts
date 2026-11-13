import { canonicalJsonHash, host } from '../../../../../vendor/lazy-harness-monitoring/composition.ts'
import type { InputPortContext, ReadRecord, ReadRecordPort, ReadRecordRequest, ReadRecordSnapshot } from '../../../../../vendor/lazy-harness-monitoring/packages/core/src/host/index.ts'

/** Host-owned volatile ledger. Only attested main read results enter; report receipts never do. */
export function createHostReadRecords(context: () => InputPortContext | undefined, options: { maxItems?: number; maxBytes?: number; beforeSnapshot?: () => Promise<void> } = {}) {
  const maxItems = options.maxItems ?? 4096, maxBytes = options.maxBytes ?? 1048576
  if (!Number.isSafeInteger(maxItems) || maxItems < 1 || maxItems > 4096 || !Number.isSafeInteger(maxBytes) || maxBytes < 1 || maxBytes > 1048576) throw Error('invalid ledger bounds')
  const records = new Map<string, ReadRecord>()
  let epoch = '', revision = 0, bytes = 0, incomplete = false, pending = false, closed = false
  function current() {
    const raw = context(), c = raw ? host.validatePortData<InputPortContext>(host.InputPortContextSchema, raw) : undefined
    const key = canonicalJsonHash(c ? [c.scope, c.sourceRevision, c.grantRevision, c.available] : null)
    if (key !== epoch) { epoch = key; records.clear(); bytes = 0; incomplete = false; revision++ }
    return c
  }
  const matches = (c: InputPortContext | undefined, r: Pick<ReadRecord, 'scope' | 'sourceRevision' | 'grantRevision'>) => !!c?.available && host.sameInputPortScope(c.scope, r.scope) && c.sourceRevision === r.sourceRevision && c.grantRevision === r.grantRevision
  const port: ReadRecordPort = Object.freeze({ protocolVersion: 1,
    async snapshot(input: ReadRecordRequest) {
      const r = host.validateReadRecordRequest(input), c = current(), captured = revision
      const result = (status: ReadRecordSnapshot['status']) => host.validateReadRecordSnapshot({ protocolVersion: 1, scope: r.scope, sourceRevision: r.sourceRevision, grantRevision: r.grantRevision, snapshotRevision: String(captured), completeThroughCursor: c?.completeThroughCursor ?? 0, status, records: status === 'available' ? [...records.values()] : [] })
      if (closed || pending || incomplete || r.signal?.aborted || !matches(c, r)) return result('unavailable')
      pending = true
      try {
        await options.beforeSnapshot?.()
        const now = current()
        if (closed || r.signal?.aborted || !matches(now, r) || captured !== revision) return result('stale')
        return result(!incomplete && now!.completeThroughCursor >= r.cursor ? 'available' : 'unavailable')
      } finally { pending = false }
    },
    isCurrent(r: ReadRecordRequest, s: ReadRecordSnapshot) { const c = current(); return !closed && !incomplete && !r.signal?.aborted && matches(c, r) && s.status === 'available' && s.snapshotRevision === String(revision) && c!.completeThroughCursor >= r.cursor },
  })
  return Object.freeze({ port,
    record(input: ReadRecord) {
      const r = host.validateReadRecord(input), c = current()
      if (closed || incomplete || !matches(c, r) || r.cursor > c!.completeThroughCursor) return false
      const key = canonicalJsonHash([r.scope, r.documentId, r.documentVersion, r.sourceEventId]), old = records.get(key)
      if (old) return canonicalJsonHash(old) === canonicalJsonHash(r)
      const size = Buffer.byteLength(JSON.stringify(r), 'utf8')
      if (records.size >= maxItems || bytes + size > maxBytes) { incomplete = true; revision++; return false }
      records.set(key, r); bytes += size; revision++; return true
    },
    close() { closed = true; records.clear(); bytes = 0; revision++ },
  })
}
