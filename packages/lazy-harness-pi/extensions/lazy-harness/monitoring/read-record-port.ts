import {
  InputPortContextSchema, sameInputPortScope, validatePortData, validateReadRecord,
  validateReadRecordRequest, validateReadRecordSnapshot,
  type InputPortContext, type InputPortScope, type ReadRecord, type ReadRecordPort, type ReadRecordRequest, type ReadRecordSnapshot,
} from '@lazy-harness/monitoring-core/host';
import type { CaptureValidation } from '../capture-evidence.ts';

/** TODO: replace this injected identity-only seam with the future catalog contract.
 * No discovery, source bodies, generated indexes or catalog implementation here. */
export interface ReadRecordCatalog {
  resolve(path: string, sha256: string): Readonly<{ documentId: string; documentVersion: string }> | undefined;
}
export type ExposureEvidenceKind =
  | 'context-full-record' | 'context-partial-record'
  | 'tool-result-text-runtime-file' | 'reader-joined-fingerprint' | 'tool-success-only';
export type HarnessReadEvidence = Readonly<{
  record: Omit<ReadRecord, 'exposure'>;
  evidenceKind: ExposureEvidenceKind;
  attestationId: string;
}>;
export type ReadRecordPortOptions = Readonly<{
  context(): InputPortContext | undefined;
  maxItems?: number;
  maxBytes?: number;
  beforeSnapshot?(): Promise<void>;
  captureIdentity?(): Readonly<{ root: string; epoch: number }> | undefined;
}>;

/** Volatile version-aware adapter. Only explicit full-context attestation suppresses
 * a version; successful tools, readback hashes and Reader joins cannot attest that.
 * No listener is installed, no receipt is restored, and no filesystem I/O is done. */
export function createHarnessReadRecordPort(options: ReadRecordPortOptions) {
  const maxItems = options.maxItems ?? 4096, maxBytes = options.maxBytes ?? 1048576;
  if (!Number.isSafeInteger(maxItems) || maxItems < 1 || maxItems > 4096 ||
      !Number.isSafeInteger(maxBytes) || maxBytes < 1 || maxBytes > 1048576) throw Error('Invalid read-record bounds');
  const entries = new Map<string, ReadRecord>();
  let generation = '', revision = 0, usedBytes = 0, overflow = false, busy = false, closed = false;
  function current() {
    const raw = options.context();
    const c = raw ? validatePortData<InputPortContext>(InputPortContextSchema, raw) : undefined;
    const key = JSON.stringify(c ? [c.scope, c.sourceRevision, c.grantRevision, c.available] : null);
    if (generation !== key) {
      entries.clear(); usedBytes = 0; overflow = false; revision++; generation = key;
    }
    return c;
  }
  const matches = (c: InputPortContext | undefined, r: Pick<ReadRecord, 'scope' | 'sourceRevision' | 'grantRevision'>) =>
    !!c?.available && sameInputPortScope(c.scope, r.scope) && c.sourceRevision === r.sourceRevision && c.grantRevision === r.grantRevision;
  const port: ReadRecordPort = Object.freeze({
    protocolVersion: 1,
    async snapshot(input: ReadRecordRequest) {
      const request = validateReadRecordRequest(input), context = current(), capturedRevision = revision;
      const snapshot = (status: ReadRecordSnapshot['status']) => validateReadRecordSnapshot({
        protocolVersion: 1, scope: request.scope, sourceRevision: request.sourceRevision, grantRevision: request.grantRevision,
        snapshotRevision: String(capturedRevision), completeThroughCursor: context?.completeThroughCursor ?? 0,
        status, records: status === 'available' ? [...entries.values()] : [],
      });
      if (closed || busy || overflow || request.signal?.aborted || !matches(context, request)) return snapshot('unavailable');
      busy = true;
      try {
        await options.beforeSnapshot?.();
        const now = current();
        if (closed || request.signal?.aborted || capturedRevision !== revision || !matches(now, request)) return snapshot('stale');
        return snapshot(!overflow && now!.completeThroughCursor >= request.cursor ? 'available' : 'unavailable');
      } finally { busy = false; }
    },
    isCurrent(input: ReadRecordRequest, value: ReadRecordSnapshot) {
      try {
        const request = validateReadRecordRequest(input), snapshot = validateReadRecordSnapshot(value), c = current();
        return !closed && !overflow && !request.signal?.aborted && matches(c, request) && matches(c, snapshot) &&
          snapshot.status === 'available' && snapshot.snapshotRevision === String(revision) &&
          snapshot.completeThroughCursor >= request.cursor && c!.completeThroughCursor >= request.cursor;
      } catch { return false; }
    },
  });
  function recordEvidence(evidence: HarnessReadEvidence): boolean {
    // Never trust an exposure field smuggled in through the source record.
    const kind = evidence.evidenceKind === 'context-full-record' ? 'full' :
      evidence.evidenceKind === 'context-partial-record' ? 'partial' : 'unknown';
    const record = validateReadRecord({ ...evidence.record, exposure: { kind, attestationId: evidence.attestationId } });
    const c = current();
    if (closed || overflow || !matches(c, record) || record.cursor > c!.completeThroughCursor) return false;
    const key = JSON.stringify([record.scope, record.documentId, record.documentVersion, record.sourceEventId]);
    const previous = entries.get(key);
    if (previous) return JSON.stringify(previous) === JSON.stringify(record);
    const size = new TextEncoder().encode(JSON.stringify(record)).length;
    if (entries.size === maxItems || usedBytes + size > maxBytes) { overflow = true; revision++; return false; }
    entries.set(key, record); usedBytes += size; revision++;
    return true;
  }
  /** Existing CaptureEvidence.evaluate output, NOT a new tool-success heuristic.
   * That source checks start/result/root/epoch/path/input, nonempty text and a
   * current file hash, but does not prove exact/full source text reached context. */
  function ingestCapture(capture: CaptureValidation, cursor: number, catalog: ReadRecordCatalog, scope: InputPortScope): number {
    const c = current(), identity = options.captureIdentity?.();
    if (!c || !sameInputPortScope(c.scope, scope) || !identity || identity.root !== capture.root ||
        identity.epoch !== capture.epoch || capture.status !== 'evidence-linked' || capture.judgement?.disposition !== 'reuse') return 0;
    let admitted = 0;
    for (const fact of capture.facts) {
      const receipt = fact.receipt;
      if (fact.status !== 'evidence-linked' || !receipt || receipt.epoch !== capture.epoch ||
          receipt.path !== fact.path || !['read', 'read_file', 'read_text_file'].includes(receipt.name) ||
          receipt.readback !== 'runtime-file' || receipt.is_error !== false) continue;
      const document = catalog.resolve(receipt.path, receipt.sha256);
      if (!document) continue;
      if (recordEvidence({ evidenceKind: 'tool-result-text-runtime-file', attestationId: receipt.toolCallId,
        record: { protocolVersion: 1, scope: c.scope, ...document, namespace: 'lazy-harness',
          sourceRecordId: receipt.path, sourceRecordRevision: receipt.sha256, sourceEventId: receipt.toolCallId,
          cursor, sourceRevision: c.sourceRevision, grantRevision: c.grantRevision } })) admitted++;
    }
    return admitted;
  }
  return Object.freeze({ port, recordEvidence, ingestCapture,
    exposureEvidenceKind: 'tool-result-text-runtime-file' as const,
    close() { closed = true; entries.clear(); usedBytes = 0; revision++; },
  });
}
