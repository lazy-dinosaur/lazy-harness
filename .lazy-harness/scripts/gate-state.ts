#!/usr/bin/env bun
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'

type Format = 'json' | 'md'

type GateEntry = {
  first_seen_message_id?: string
  first_seen_ts?: string
  [key: string]: unknown
}

type GateState = {
  last_message_id?: string
  open_fingerprints?: Record<string, GateEntry>
  [key: string]: unknown
}

function usage(exitCode = 0): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Usage: lazy gate-state <command> [options]

Commands:
  list [--format=json|md]
  clear-stale --older-than-hours <hours> [--prefix <prefix>] [--dry-run] [--format=json|md]

Runtime state only: edits .lazy-harness/state/open-gates.json, never canonical records.
`)
  process.exit(exitCode)
}

function parseOptions(argv: string[]): Record<string, string | boolean> {
  const opts: Record<string, string | boolean> = {}
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    const next = argv[i + 1]
    if (arg === '-h' || arg === '--help') usage(0)
    if (arg.startsWith('--') && arg.includes('=')) {
      const [key, ...rest] = arg.slice(2).split('=')
      opts[key] = rest.join('=')
    } else if (arg.startsWith('--')) {
      const key = arg.slice(2)
      if (['format', 'target', 'older-than-hours', 'prefix'].includes(key)) {
        if (!next || next.startsWith('--')) {
          console.error(`Missing value for ${arg}`)
          process.exit(2)
        }
        opts[key] = next
        i += 1
      } else {
        opts[key] = true
      }
    } else {
      console.error(`Unknown argument: ${arg}`)
      usage(2)
    }
  }
  return opts
}

function hostRoot(opts: Record<string, string | boolean>): string {
  const explicit = typeof opts.target === 'string' ? opts.target : process.env.LAZY_HOST_ROOT
  return resolve(explicit || process.cwd())
}

function statePath(root: string): string {
  return join(root, '.lazy-harness', 'state', 'open-gates.json')
}

function format(opts: Record<string, string | boolean>): Format {
  const value = String(opts.format || 'md')
  if (value !== 'md' && value !== 'json') {
    console.error(`Unsupported --format: ${value}`)
    process.exit(2)
  }
  return value
}

function readState(root: string): GateState {
  const path = statePath(root)
  if (!existsSync(path)) return { open_fingerprints: {} }
  try {
    const parsed = JSON.parse(readFileSync(path, 'utf8'))
    if (parsed && typeof parsed === 'object') return parsed as GateState
  } catch (error) {
    throw new Error(`Failed to parse ${path}: ${error instanceof Error ? error.message : String(error)}`)
  }
  return { open_fingerprints: {} }
}

function writeState(root: string, state: GateState, dryRun: boolean): void {
  if (dryRun) return
  const path = statePath(root)
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, JSON.stringify(state, null, 2) + '\n')
}

function entries(state: GateState): Array<{ fingerprint: string; firstSeenMessageId: string | null; firstSeenTs: string | null; ageHours: number | null }> {
  const now = Date.now()
  const fps = state.open_fingerprints && typeof state.open_fingerprints === 'object' ? state.open_fingerprints : {}
  return Object.entries(fps).map(([fingerprint, value]) => {
    const ts = typeof value.first_seen_ts === 'string' ? value.first_seen_ts : null
    const millis = ts ? Date.parse(ts) : Number.NaN
    return {
      fingerprint,
      firstSeenMessageId: typeof value.first_seen_message_id === 'string' ? value.first_seen_message_id : null,
      firstSeenTs: ts,
      ageHours: Number.isFinite(millis) ? (now - millis) / 3_600_000 : null,
    }
  }).sort((a, b) => a.fingerprint.localeCompare(b.fingerprint))
}

function printJson(value: unknown): void {
  console.log(JSON.stringify(value, null, 2))
}

function list(root: string, fmt: Format): void {
  const state = readState(root)
  const rows = entries(state)
  if (fmt === 'json') {
    printJson({ ok: true, root, path: statePath(root), lastMessageId: state.last_message_id ?? null, count: rows.length, entries: rows })
    return
  }
  console.log('# Gate state')
  console.log(`- root: ${root}`)
  console.log(`- path: ${statePath(root)}`)
  console.log(`- last_message_id: ${state.last_message_id ?? 'n/a'}`)
  console.log(`- open_fingerprints: ${rows.length}`)
  for (const row of rows) {
    const age = row.ageHours === null ? 'unknown' : `${row.ageHours.toFixed(2)}h`
    console.log(`  - ${row.fingerprint} first_seen=${row.firstSeenTs ?? 'n/a'} age=${age}`)
  }
}

function clearStale(root: string, opts: Record<string, string | boolean>, fmt: Format): void {
  const hoursRaw = opts['older-than-hours']
  if (typeof hoursRaw !== 'string') {
    console.error('gate-state clear-stale requires --older-than-hours <hours>')
    process.exit(2)
  }
  const olderThanHours = Number(hoursRaw)
  if (!Number.isFinite(olderThanHours) || olderThanHours < 0) {
    console.error(`Invalid --older-than-hours: ${hoursRaw}`)
    process.exit(2)
  }
  const prefix = typeof opts.prefix === 'string' ? opts.prefix : undefined
  const dryRun = opts['dry-run'] === true
  const state = readState(root)
  const fps = state.open_fingerprints && typeof state.open_fingerprints === 'object' ? state.open_fingerprints : {}
  const now = Date.now()
  const removed: string[] = []
  const kept: Record<string, GateEntry> = {}
  for (const [fingerprint, value] of Object.entries(fps)) {
    const ts = typeof value.first_seen_ts === 'string' ? Date.parse(value.first_seen_ts) : Number.NaN
    const ageHours = Number.isFinite(ts) ? (now - ts) / 3_600_000 : Number.POSITIVE_INFINITY
    const matchesPrefix = !prefix || fingerprint.startsWith(prefix)
    if (matchesPrefix && ageHours >= olderThanHours) removed.push(fingerprint)
    else kept[fingerprint] = value
  }
  const nextState = { ...state, open_fingerprints: kept }
  writeState(root, nextState, dryRun)
  const result = { ok: true, dryRun, root, path: statePath(root), olderThanHours, prefix: prefix ?? null, removed, remaining: Object.keys(kept).sort() }
  if (fmt === 'json') printJson(result)
  else {
    console.log(`# Gate state clear-stale${dryRun ? ' dry-run' : ''}`)
    console.log(`- removed: ${removed.length}`)
    for (const item of removed.sort()) console.log(`  - ${item}`)
    console.log(`- remaining: ${Object.keys(kept).length}`)
  }
}

function main(): void {
  const [cmd, ...rest] = process.argv.slice(2)
  if (!cmd || cmd === '-h' || cmd === '--help') usage(cmd ? 0 : 2)
  const opts = parseOptions(rest)
  const root = hostRoot(opts)
  const fmt = format(opts)
  try {
    if (cmd === 'list') return list(root, fmt)
    if (cmd === 'clear-stale') return clearStale(root, opts, fmt)
    console.error(`Unknown gate-state command: ${cmd}`)
    usage(2)
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    if (fmt === 'json') printJson({ ok: false, error: message })
    else console.error(message)
    process.exit(1)
  }
}

main()
