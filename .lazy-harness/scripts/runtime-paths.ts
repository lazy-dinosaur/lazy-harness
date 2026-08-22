#!/usr/bin/env bun
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, writeFileSync, renameSync, rmSync } from 'node:fs'
import { dirname, join, resolve, isAbsolute } from 'node:path'
import { execFileSync } from 'node:child_process'

export function stableHash(value: unknown, length = 16): string {
  return createHash('sha256').update(String(value ?? ''), 'utf8').digest('hex').slice(0, length)
}

function gitOutput(root: string, args: string[]): string {
  try {
    return execFileSync('git', ['-C', root, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim()
  } catch {
    return ''
  }
}

export function hostRoot(explicit?: string): string {
  const candidate = explicit || process.env.LAZY_HOST_ROOT || process.cwd()
  return resolve(candidate)
}

export function sessionKey(sessionId?: string): string {
  const raw = sessionId || process.env.LAZY_SESSION_ID || ''
  const trimmed = String(raw || '').trim()
  if (!trimmed) return 'default'
  return `session-${stableHash(trimmed, 20)}`
}

export function worktreeGitDir(root = hostRoot()): string {
  const gitDir = gitOutput(root, ['rev-parse', '--absolute-git-dir'])
  if (gitDir) return gitDir
  return join(root, '.lazy-harness', '.gitless')
}

export function gitCommonDir(root = hostRoot()): string {
  const common = gitOutput(root, ['rev-parse', '--git-common-dir'])
  if (!common) return worktreeGitDir(root)
  return isAbsolute(common) ? common : resolve(root, common)
}

export function runtimeRoot(root = hostRoot(), sessionId?: string): string {
  const explicit = process.env.LAZY_RUNTIME_ROOT
  if (explicit) return resolve(explicit)
  return join(worktreeGitDir(root), 'lazy-harness', 'runtime', sessionKey(sessionId))
}

export function sharedRoot(root = hostRoot()): string {
  const explicit = process.env.LAZY_SHARED_ROOT
  if (explicit) return resolve(explicit)
  return join(gitCommonDir(root), 'lazy-harness', 'shared')
}

export function runtimeStatePath(name: string, root = hostRoot(), sessionId?: string): string {
  return join(runtimeRoot(root, sessionId), 'state', name)
}

export function runtimeLogPath(name: string, root = hostRoot(), sessionId?: string): string {
  return join(runtimeRoot(root, sessionId), 'logs', name)
}

export function sharedPath(rel: string, root = hostRoot()): string {
  return join(sharedRoot(root), rel)
}

export function ensureParent(filePath: string): void {
  mkdirSync(dirname(filePath), { recursive: true })
}

function sleep(ms: number): void {
  const end = Date.now() + ms
  while (Date.now() < end) {
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, Math.min(50, end - Date.now()))
  }
}

export function withLock<T>(lockName: string, fn: () => T, root = hostRoot(), timeoutMs = 5000): T {
  const lockDir = join(sharedRoot(root), 'locks', `${lockName.replace(/[^A-Za-z0-9_.-]/g, '_')}.lockdir`)
  mkdirSync(dirname(lockDir), { recursive: true })
  const started = Date.now()
  while (true) {
    try {
      mkdirSync(lockDir)
      writeFileSync(join(lockDir, 'owner.json'), JSON.stringify({ pid: process.pid, startedAt: new Date().toISOString() }) + '\n')
      break
    } catch {
      if (Date.now() - started > timeoutMs) {
        throw new Error(`Timed out waiting for lazy-harness lock: ${lockDir}`)
      }
      sleep(50)
    }
  }
  try {
    return fn()
  } finally {
    try { rmSync(lockDir, { recursive: true, force: true }) } catch { /* ignore */ }
  }
}

export type JsonlAppendStatus = 'appended' | 'deduped-identical' | 'conflict-recorded'

function stableJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`
  if (value && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
      .filter(([, v]) => v !== undefined)
      .sort(([a], [b]) => a.localeCompare(b))
    return `{${entries.map(([k, v]) => `${JSON.stringify(k)}:${stableJson(v)}`).join(',')}}`
  }
  return JSON.stringify(value)
}

function atomicWrite(filePath: string, text: string): void {
  ensureParent(filePath)
  const tmp = `${filePath}.tmp-${process.pid}-${Date.now()}`
  writeFileSync(tmp, text, 'utf8')
  renameSync(tmp, filePath)
}

export function appendJsonlStable(filePath: string, row: Record<string, unknown>, idKey = 'id', root = hostRoot()): JsonlAppendStatus {
  const id = typeof row[idKey] === 'string' ? String(row[idKey]) : ''
  const incoming = stableJson(row)
  const lockName = `jsonl-${stableHash(filePath, 24)}`
  return withLock(lockName, () => {
    const lines = existsSync(filePath) ? readFileSync(filePath, 'utf8').split(/\r?\n/).filter((line) => line.trim()) : []
    for (const line of lines) {
      try {
        const existing = JSON.parse(line)
        if (stableJson(existing) === incoming) return 'deduped-identical'
        if (id) {
          if (existing && typeof existing === 'object' && existing[idKey] === id) {
            const conflict = {
              id: `conflict_${id}_${stableHash(stableJson(row), 12)}`,
              event: 'lazy-harness.jsonl-conflict',
              status: 'conflict-recorded',
              detectedAt: new Date().toISOString(),
              targetPath: filePath,
              idKey,
              conflictingId: id,
              existingHash: stableHash(stableJson(existing)),
              incomingHash: stableHash(stableJson(row)),
              incoming: row,
            }
            const conflictPath = `${filePath}.conflicts.jsonl`
            ensureParent(conflictPath)
            const current = existsSync(conflictPath) ? readFileSync(conflictPath, 'utf8') : ''
            writeFileSync(conflictPath, `${current}${JSON.stringify(conflict)}\n`, 'utf8')
            return 'conflict-recorded'
          }
        }
      } catch {
        // malformed historical lines do not block appending a new stable row
      }
    }
    lines.push(JSON.stringify(row))
    atomicWrite(filePath, `${lines.join('\n')}\n`)
    return 'appended'
  }, root)
}

if (import.meta.main) {
  const root = hostRoot()
  const sessionArg = process.argv.find((arg) => arg.startsWith('--session-id='))?.slice('--session-id='.length)
  const mode = process.argv[2] || 'print'
  if (mode === 'runtime-root') console.log(runtimeRoot(root, sessionArg))
  else if (mode === 'shared-root') console.log(sharedRoot(root))
  else if (mode === 'state-path') console.log(runtimeStatePath(process.argv[3] || 'state.json', root, sessionArg))
  else if (mode === 'log-path') console.log(runtimeLogPath(process.argv[3] || 'log.jsonl', root, sessionArg))
  else console.log(JSON.stringify({ hostRoot: root, runtimeRoot: runtimeRoot(root, sessionArg), sharedRoot: sharedRoot(root) }, null, 2))
}
