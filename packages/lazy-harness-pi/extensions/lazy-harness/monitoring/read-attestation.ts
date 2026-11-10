import { createHash } from 'node:crypto';
import { closeSync, constants, fstatSync, openSync, readSync, realpathSync } from 'node:fs';
import { isAbsolute, relative, resolve } from 'node:path';
import {
  InputPortContextSchema, validatePortData, type InputPortContext,
} from '@lazy-harness/monitoring-core/host';
import type { HarnessReadEvidence, ReadRecordCatalog } from './read-record-port.ts';

/** Owner-selected serialization of the actual main-agent read tool, NOT sniffed from text. */
export type ReadTextFormat = 'pi-read-text-v1' | 'pi-hashline-edit-pro-v1' | 'unknown';
export type MainReadCall = Readonly<{
  toolCallId: string;
  toolName: string;
  input: Readonly<{ path: string; offset?: number | string; limit?: number; anchors?: boolean }>;
}>;
export type MainReadResult = MainReadCall & Readonly<{
  isError?: boolean;
  is_error?: boolean;
  content: unknown;
  details?: unknown;
  structuredContent?: unknown;
}>;
type Identity = Readonly<{ root: string; epoch: number }>;
type Pending = Readonly<{
  callHash: string; cwd: string; path: string; identity: Identity;
  context: InputPortContext; format: ReadTextFormat;
}>;
const MAX_BYTES = 1024 * 1024, MAX_CALLS = 256;
const digest = (value: string | Uint8Array) => createHash('sha256').update(value).digest('hex');
const callDigest = (call: MainReadCall) => digest(JSON.stringify([call.toolCallId, call.toolName, call.input]));
const object = (v: unknown): v is Record<string, unknown> => !!v && typeof v === 'object' && !Array.isArray(v);
const notice = /\[(?:Showing lines |\d+ more lines in file\.|Line \d+ is |Read truncated;)|Use offset=|content not shown|Non-UTF-8 bytes/;

/** Bounded, root-bound runtime bytes, never a read-success receipt or a restored hash.
 * Mirrors CaptureEvidence's safe snapshot checks without changing its private tracker. */
function capture(root: string, path: string): Buffer | undefined {
  let fd: number | undefined;
  try {
    const actual = realpathSync(resolve(root, path)), inside = relative(realpathSync(root), actual);
    if (isAbsolute(inside) || inside.split(/[\\/]/).includes('..')) return;
    fd = openSync(actual, constants.O_RDONLY | constants.O_NOFOLLOW);
    const before = fstatSync(fd);
    if (!before.isFile() || before.size > MAX_BYTES) return;
    const bytes = Buffer.alloc(MAX_BYTES + 1);
    let size = 0;
    while (size < bytes.length) {
      const n = readSync(fd, bytes, size, bytes.length - size, null);
      if (!n) break;
      size += n;
    }
    const after = fstatSync(fd);
    if (size > MAX_BYTES || size !== before.size || before.size !== after.size ||
        before.mtimeMs !== after.mtimeMs || before.ctimeMs !== after.ctimeMs ||
        realpathSync(resolve(root, path)) !== actual) return;
    return bytes.subarray(0, size);
  } catch { return; }
  finally { if (fd !== undefined) closeSync(fd); }
}

function bodyOf(text: string, format: ReadTextFormat): string | undefined {
  if (format === 'pi-read-text-v1') return text;
  if (format !== 'pi-hashline-edit-pro-v1') return;
  // alphabet.ts HASH_CLASS = [a-z]{5}; resolve.ts fmtRow = anchor + U+2502 + text.
  // Keep every other byte, including whitespace, CR, nested pipes and LF. No EOL repair.
  const rows = text.split('\n');
  if (!rows.every(row => /^[a-z]{5}│/.test(row))) return;
  return rows.map(row => row.slice(6)).join('\n');
}
function classification(call: MainReadCall, result: MainReadResult, bytes: Buffer, format: ReadTextFormat) {
  const content = result.content;
  if (!Array.isArray(content) || content.length !== 1 || !object(content[0]) ||
      content[0].type !== 'text' || typeof content[0].text !== 'string') return { kind: 'unknown' as const };
  const text = content[0].text;
  if (Buffer.byteLength(text, 'utf8') > MAX_BYTES * 2) return { kind: 'unknown' as const };
  const details = object(result.details) ? result.details : {};
  const metrics = object(details.metrics) ? details.metrics : {};
  const truncation = object(details.truncation) ? details.truncation : {};
  const structured = object(result.structuredContent) ? result.structuredContent : {};
  if (notice.test(text) || truncation.truncated === true || truncation.firstLineExceedsLimit === true ||
      metrics.truncated === true || details.nextOffset != null || metrics.next_offset != null ||
      structured.truncated === true || structured.nextOffset != null || structured.blockedByLongLine === true ||
      structured.hadUtf8DecodeErrors === true || (Array.isArray(structured.notices) && structured.notices.length)) {
    return { kind: 'unknown' as const };
  }
  const body = bodyOf(text, format);
  if (body === undefined) return { kind: 'unknown' as const };
  const bodyBytes = Buffer.from(body, 'utf8'), bodyHash = digest(bodyBytes), fileHash = digest(bytes);
  // Refuse invalid UTF-8 roundtrips and binary text; do not normalize BOM/CRLF/EOF.
  const file = bytes.toString('utf8');
  if (!Buffer.from(file, 'utf8').equals(bytes) || file.includes('\0')) return { kind: 'unknown' as const, bodyHash };
  const keysKnown = Object.keys(call.input).every(k => ['path', 'offset', 'limit', 'anchors'].includes(k));
  const offset = call.input.offset ?? 1, limit = call.input.limit;
  const valid = keysKnown && Number.isSafeInteger(offset) && Number(offset) >= 1 &&
    (limit === undefined || (Number.isSafeInteger(limit) && limit >= 1));
  if (!valid || format === 'unknown') return { kind: 'unknown' as const, bodyHash };
  // The hashline renderer omits the terminal empty row; plain Pi counts it.
  const lines = file.split('\n');
  if (format === 'pi-hashline-edit-pro-v1' && file.endsWith('\n')) lines.pop();
  const whole = offset === 1 && (limit === undefined || limit >= lines.length);
  if (whole && bodyHash === fileHash && bodyBytes.equals(bytes)) return { kind: 'full' as const, bodyHash };
  const start = Number(offset) - 1, selected = lines.slice(start, limit === undefined ? undefined : start + limit).join('\n');
  if (!whole && bodyBytes.length > 0 && body === selected) return { kind: 'partial' as const, bodyHash };
  return { kind: 'unknown' as const, bodyHash };
}

/** Explicit inactive feed seam. The caller owns main-agent provenance and format;
 * never forward Reader summaries, nested agent results or provider enqueue receipts.
 * start captures the generation, complete captures bytes and admits only that scope. */
export function createReadResultAttestor(options: Readonly<{
  context(): InputPortContext | undefined;
  captureIdentity(): Identity | undefined;
  format(): ReadTextFormat;
  catalog: ReadRecordCatalog;
  record(evidence: HarnessReadEvidence): boolean;
}>) {
  const pending = new Map<string, Pending>(), seen = new Set<string>();
  let generation = '', closed = false, exhausted = false;
  function current() {
    const raw = options.context(), identity = options.captureIdentity();
    const context = raw ? validatePortData<InputPortContext>(InputPortContextSchema, raw) : undefined;
    const key = JSON.stringify([context?.scope, context?.sourceRevision, context?.grantRevision, context?.available, identity, options.format()]);
    if (key !== generation) { pending.clear(); seen.clear(); exhausted = false; generation = key; }
    return { context, identity };
  }
  function start(call: MainReadCall, cwd: string, origin: 'main-agent' | 'other'): boolean {
    const { context, identity } = current();
    if (closed || exhausted || origin !== 'main-agent' || !context?.available || !identity ||
        call.toolName !== 'read' || !call.toolCallId || call.toolCallId.length > 512 ||
        !identity.root || !Number.isSafeInteger(identity.epoch) || identity.epoch < 0 ||
        typeof call.input?.path !== 'string') return false;
    if (seen.has(call.toolCallId)) { pending.delete(call.toolCallId); return false; }
    // Overflow fences this generation rather than forgetting replay protection.
    if (seen.size === MAX_CALLS) { pending.clear(); exhausted = true; return false; }
    seen.add(call.toolCallId);
    const path = relative(identity.root, resolve(cwd, call.input.path));
    if (!path || isAbsolute(path) || path.split(/[\\/]/).includes('..')) return false;
    pending.set(call.toolCallId, Object.freeze({ callHash: callDigest(call), cwd: resolve(cwd), path,
      identity: Object.freeze({ ...identity }), context, format: options.format() }));
    return true;
  }
  function complete(result: MainReadResult, cwd: string, origin: 'main-agent' | 'other', cursor: number): boolean {
    const { context, identity } = current(), p = pending.get(result.toolCallId);
    pending.delete(result.toolCallId);
    const call: MainReadCall = { toolCallId: result.toolCallId, toolName: result.toolName, input: result.input };
    if (closed || exhausted || !p || !context?.available || !identity || origin !== 'main-agent' ||
        (result.isError !== false && result.is_error !== false) || result.isError === true || result.is_error === true ||
        p.cwd !== resolve(cwd) || p.callHash !== callDigest(call) ||
        !Number.isSafeInteger(cursor) || cursor < 0 || cursor > context.completeThroughCursor) return false;
    const bytes = capture(p.identity.root, p.path);
    if (!bytes) return false;
    const fileHash = digest(bytes), document = options.catalog.resolve(p.path, fileHash);
    if (!document) return false;
    const exposure = classification(call, result, bytes, p.format);
    const attestationId = 'tool-result-full-text:' + digest(JSON.stringify([
      p.callHash, p.identity, p.context, p.format, cursor, document, fileHash, exposure,
    ]));
    return options.record({
      evidenceKind: exposure.kind === 'full' ? 'context-full-record' : exposure.kind === 'partial' ? 'context-partial-record' : 'tool-result-text-runtime-file',
      attestationId,
      record: { protocolVersion: 1, scope: p.context.scope, ...document, namespace: 'lazy-harness',
        sourceRecordId: p.path, sourceRecordRevision: fileHash, sourceEventId: result.toolCallId,
        cursor, sourceRevision: p.context.sourceRevision, grantRevision: p.context.grantRevision },
    });
  }
  return Object.freeze({ start, complete, close() { closed = true; pending.clear(); seen.clear(); } });
}
