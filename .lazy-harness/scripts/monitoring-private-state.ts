import { constants } from 'node:fs'
import { lstat, mkdir, open, rename, unlink } from 'node:fs/promises'
import { createHash, randomBytes } from 'node:crypto'
import { homedir } from 'node:os'
import { dirname, join, resolve } from 'node:path'

export function observeDirectory(root: string, setting?: false | string) {
  const base = resolve(typeof setting === 'string' ? setting : join(process.env.XDG_STATE_HOME || join(homedir(), '.local/state'), 'lazy-harness/monitoring/observe'))
  return join(base, createHash('sha256').update(resolve(root)).digest('hex'))
}
/** Walk all components: covers linked worktrees (.git file), symlinks and not-yet-created paths. */
export async function assertOutsideGit(path: string) {
  for (let p = resolve(path); ; p = dirname(p)) {
    const st = await lstat(p).catch((e: NodeJS.ErrnoException) => { if (e.code !== 'ENOENT') throw e; return undefined })
    if (st?.isSymbolicLink()) throw Error('symlink path refused')
    const git = await lstat(join(p, '.git')).catch((e: NodeJS.ErrnoException) => { if (e.code !== 'ENOENT' && e.code !== 'ENOTDIR') throw e; return undefined })
    if (git || p.endsWith('/.git')) throw Error('output inside Git refused')
    if (dirname(p) === p) break
  }
}
export async function writePrivate(path: string, text: string, privateDirectory = false) {
  path = resolve(path)
  await assertOutsideGit(path)
  await mkdir(dirname(path), { recursive: true, mode: 0o700 })
  await assertOutsideGit(path)
  if (privateDirectory) {
    const dir = await open(dirname(path), constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_DIRECTORY)
    try { await dir.chmod(0o700) } finally { await dir.close() }
  }
  const previous = await lstat(path).catch((e: NodeJS.ErrnoException) => { if (e.code !== 'ENOENT') throw e; return undefined })
  if (previous && (!previous.isFile() || previous.nlink !== 1)) throw Error('unsafe output file')
  const tmp = join(dirname(path), '.monitoring-' + randomBytes(12).toString('hex'))
  try {
    const file = await open(tmp, constants.O_CREAT | constants.O_EXCL | constants.O_WRONLY | constants.O_NOFOLLOW, 0o600)
    try { await file.writeFile(text); await file.chmod(0o600) } finally { await file.close() }
    await rename(tmp, path)
  } finally { await unlink(tmp).catch(() => {}) }
}
export async function readMetadata(path: string, maxBytes = 2 * 1024 * 1024): Promise<{ text: string; mtimeMs: number } | null> {
  for (let p = resolve(path); ; p = dirname(p)) {
    const st = await lstat(p).catch((e: NodeJS.ErrnoException) => { if (e.code !== 'ENOENT') throw e; return undefined })
    if (!st) return null
    if (st.isSymbolicLink()) throw Error('symlink input refused')
    if (dirname(p) === p) break
  }
  const file = await open(path, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK)
  try {
    const st = await file.stat()
    if (!st.isFile() || st.size > maxBytes) throw Error('unsafe or oversized metadata')
    const bytes = Buffer.alloc(maxBytes + 1)
    const { bytesRead } = await file.read(bytes, 0, bytes.length, 0)
    if (bytesRead > maxBytes) throw Error('oversized metadata')
    return { text: bytes.subarray(0, bytesRead).toString('utf8'), mtimeMs: st.mtimeMs }
  } finally { await file.close() }
}
