import { constants, closeSync, fstatSync, lstatSync, openSync, readFileSync, realpathSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path'
import type { MonitoringAttachConfig } from './config.ts'
export const sha256 = (bytes: Uint8Array) => createHash('sha256').update(bytes).digest('hex')
/** Explicit admission only; reject symlinks in every component and fail closed on byte/identity races. */
export function captureRecord(root: string, path: string): Buffer | undefined {
  let fd: number | undefined
  try {
    const base = realpathSync(root), target = resolve(base, path), rel = relative(base, target)
    if (!rel || isAbsolute(rel) || rel === '..' || rel.startsWith('..' + sep)) return
    let cursor = target
    while (cursor !== base) { if (lstatSync(cursor).isSymbolicLink()) return; cursor = dirname(cursor) }
    if (realpathSync(target) !== target) return
    fd = openSync(target, constants.O_RDONLY | constants.O_NOFOLLOW)
    const before = fstatSync(fd, { bigint: true })
    if (!before.isFile() || before.size > 8192n) return
    const bytes = readFileSync(fd), after = fstatSync(fd, { bigint: true }), current = lstatSync(target, { bigint: true })
    if ((['dev', 'ino', 'size', 'mtimeNs', 'ctimeNs'] as const).some(k => before[k] !== after[k] || after[k] !== current[k]) || realpathSync(target) !== target) return
    if (!Buffer.from(bytes.toString('utf8'), 'utf8').equals(bytes) || bytes.includes(0)) return
    return bytes
  } catch { return undefined } finally { if (fd !== undefined) closeSync(fd) }
}
export function admitCatalog(root: string, config: MonitoringAttachConfig) {
  const documents = config.catalog.map(d => {
    const bytes = captureRecord(root, d.path)
    if (!bytes?.length) throw Error('catalog bytes unavailable or over 8192 bytes')
    return Object.freeze({ ...d, version: sha256(bytes), content: bytes.toString('utf8'), kind: 'knowledge' as const })
  })
  if (documents.reduce((n, d) => n + Buffer.byteLength(d.content), 0) > 12288) throw Error('catalog exceeds U1 material budget')
  return Object.freeze({ documents: Object.freeze(documents),
    isCurrent() { return documents.every(d => { const b = captureRecord(root, d.path); return b && sha256(b) === d.version }) },
    sourceVersion(id: string) { const d = documents.find(d => d.id === id); if (!d) return; const b = captureRecord(root, d.path); return b && sha256(b) === d.version ? d.version : undefined },
  })
}
