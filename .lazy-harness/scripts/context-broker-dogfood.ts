#!/usr/bin/env bun
/**
 * context-broker-dogfood.ts — explicit dogfood collector for Native Context Broker.
 *
 * Runs Context Delivery + Record Decision generator against one or more host roots
 * and writes sanitized JSONL observations. This is not a hook and does not mutate
 * canonical records. Context Delivery --journal may append host runtime state by design.
 */
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import * as path from 'node:path'
import { spawnSync } from 'node:child_process'

type Format = 'json' | 'md'

interface CaseSpec {
  label: string
  message: string
}

interface Args {
  root: string
  hosts: string[]
  cases: CaseSpec[]
  outPath: string
  format: Format
  dryRun: boolean
  append: boolean
}

interface CommandResult {
  status: number | null
  stdout: string
  stderr: string
}

interface DogfoodRow {
  schemaVersion: '1.0'
  event: 'context-broker.dogfood'
  timestamp: string
  host: string
  hostMarker: string | null
  caseLabel: string
  messageHash: string
  contextDelivery: {
    ok: boolean
    instructionLevel?: string
    confidence?: number
    requiredReadCount?: number
    optionalReadCount?: number
    candidateMeaningCount?: number
    fallbackSearchCount?: number
    topRequiredRead?: Array<{ path: string; kind: string; confidence: number }>
  }
  packetJournal: {
    checked: boolean
    hasMessageHash?: boolean
    rawMessagePresent?: boolean
  }
  recordDecision: {
    ok: boolean
    disposition?: string
    trigger?: string
    confidence?: number
    recommendedActions?: string[]
  }
  errors: string[]
}

function usage(): never {
  console.error(`Usage: context-broker-dogfood [options]

Options:
  --root DIR              Collector root (default: LAZY_HOST_ROOT or cwd)
  --host DIR              Host root to inspect (repeatable; default: --root)
  --case LABEL::MESSAGE   Dogfood case (repeatable)
  --out PATH              Output JSONL path (default: .lazy-harness/state/context-broker-dogfood.jsonl)
  --format json|md        Output summary format (default json)
  --dry-run               Do not write collector JSONL
  --no-append             Replace output file instead of appending
  --help                  Show help

Examples:
  .lazy-harness/bin/lazy context-dogfood --host /home/lazydino/dev/medivance --case reservation::예약시트\ 고쳐줘
  .lazy-harness/bin/lazy context-dogfood --host /home/lazydino/dev/medivance --host /home/lazydino/dev/medivance-pwa --format=md
`)
  process.exit(2)
}

function valueFor(argv: string[], index: number, flag: string): { value: string | null; consumed: number } {
  const current = argv[index]
  if (current === flag) {
    const value = argv[index + 1]
    if (!value) usage()
    return { value, consumed: 1 }
  }
  const prefix = `${flag}=`
  if (current.startsWith(prefix)) {
    const value = current.slice(prefix.length)
    if (!value) usage()
    return { value, consumed: 0 }
  }
  return { value: null, consumed: 0 }
}

function parseCase(value: string): CaseSpec {
  const idx = value.indexOf('::')
  if (idx <= 0 || idx === value.length - 2) usage()
  return { label: compact(value.slice(0, idx), 64), message: value.slice(idx + 2).trim() }
}

function parseArgs(argv: string[]): Args {
  const root = path.resolve(process.env.LAZY_HOST_ROOT || process.cwd())
  const args: Args = {
    root,
    hosts: [],
    cases: [],
    outPath: path.join(root, '.lazy-harness', 'state', 'context-broker-dogfood.jsonl'),
    format: 'json',
    dryRun: false,
    append: true,
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    let parsed = valueFor(argv, i, '--root')
    if (parsed.value !== null) {
      args.root = path.resolve(parsed.value)
      if (args.outPath.endsWith('/.lazy-harness/state/context-broker-dogfood.jsonl')) {
        args.outPath = path.join(args.root, '.lazy-harness', 'state', 'context-broker-dogfood.jsonl')
      }
      i += parsed.consumed
      continue
    }
    parsed = valueFor(argv, i, '--host')
    if (parsed.value !== null) { args.hosts.push(path.resolve(parsed.value)); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--case')
    if (parsed.value !== null) { args.cases.push(parseCase(parsed.value)); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--out')
    if (parsed.value !== null) { args.outPath = path.resolve(parsed.value); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--format')
    if (parsed.value !== null) {
      if (parsed.value !== 'json' && parsed.value !== 'md' && parsed.value !== 'markdown') usage()
      args.format = parsed.value === 'markdown' ? 'md' : parsed.value
      i += parsed.consumed
      continue
    }
    if (arg === '--dry-run') { args.dryRun = true; continue }
    if (arg === '--no-append') { args.append = false; continue }
    if (arg === '--help' || arg === '-h') usage()
    usage()
  }
  if (!args.hosts.length) args.hosts.push(args.root)
  if (!args.cases.length) {
    args.cases.push({ label: 'reservation-surface', message: '예약시트 고쳐줘' })
    args.cases.push({ label: 'status-readonly', message: '상태 요약' })
  }
  return args
}

function compact(value: string, max = 160): string {
  const text = String(value || '').replace(/\s+/g, ' ').trim()
  return text.length > max ? `${text.slice(0, max - 1)}…` : text
}

function hash(value: string): string {
  return createHash('sha256').update(value, 'utf8').digest('hex').slice(0, 16)
}

function run(host: string, args: string[]): CommandResult {
  const lazy = path.join(host, '.lazy-harness', 'bin', 'lazy')
  const result = spawnSync(lazy, args, { cwd: host, encoding: 'utf8', maxBuffer: 10 * 1024 * 1024 })
  return {
    status: result.status,
    stdout: result.stdout || '',
    stderr: result.stderr || '',
  }
}

function readMarker(host: string): string | null {
  const marker = path.join(host, '.lazy-harness', 'state', 'synced-from-commit')
  if (!existsSync(marker)) return null
  try {
    const parsed = JSON.parse(readFileSync(marker, 'utf8'))
    return typeof parsed.syncedFromCommit === 'string' ? parsed.syncedFromCommit : null
  } catch {
    return null
  }
}

function latestPacketJournal(host: string): Record<string, unknown> | null {
  const journal = path.join(host, '.lazy-harness', 'state', 'context-delivery-packets.jsonl')
  if (!existsSync(journal)) return null
  try {
    const lines = readFileSync(journal, 'utf8').split(/\r?\n/).filter((line) => line.trim())
    if (!lines.length) return null
    return JSON.parse(lines[lines.length - 1])
  } catch {
    return null
  }
}

function sanitizeContextPacket(packet: any): DogfoodRow['contextDelivery'] {
  const required = Array.isArray(packet?.requiredRead) ? packet.requiredRead : []
  return {
    ok: true,
    instructionLevel: String(packet?.instructionLevel || ''),
    confidence: typeof packet?.confidence === 'number' ? packet.confidence : undefined,
    requiredReadCount: required.length,
    optionalReadCount: Array.isArray(packet?.optionalRead) ? packet.optionalRead.length : 0,
    candidateMeaningCount: Array.isArray(packet?.candidateMeanings) ? packet.candidateMeanings.length : 0,
    fallbackSearchCount: Array.isArray(packet?.fallbackSearches) ? packet.fallbackSearches.length : 0,
    topRequiredRead: required.slice(0, 5).map((item: any) => ({
      path: String(item?.path || ''),
      kind: String(item?.kind || ''),
      confidence: typeof item?.confidence === 'number' ? item.confidence : 0,
    })).filter((item: any) => item.path),
  }
}

function sanitizeRecordDecision(packet: any): DogfoodRow['recordDecision'] {
  const decision = packet?.recordDecision || {}
  const recs = Array.isArray(decision.recommendedRecords) ? decision.recommendedRecords : []
  return {
    ok: true,
    disposition: String(decision.disposition || ''),
    trigger: String(decision.trigger || ''),
    confidence: typeof decision.confidence === 'number' ? decision.confidence : undefined,
    recommendedActions: Array.from(new Set(recs.map((item: any) => String(item?.action || '')).filter(Boolean))).slice(0, 8),
  }
}

function collectCase(host: string, spec: CaseSpec): DogfoodRow {
  const now = new Date().toISOString()
  const messageHash = hash(spec.message)
  const messageId = `dogfood-${spec.label}-${messageHash}`
  const sessionId = `dogfood-${hash(host)}`
  const row: DogfoodRow = {
    schemaVersion: '1.0',
    event: 'context-broker.dogfood',
    timestamp: now,
    host,
    hostMarker: readMarker(host),
    caseLabel: spec.label,
    messageHash,
    contextDelivery: { ok: false },
    packetJournal: { checked: false },
    recordDecision: { ok: false },
    errors: [],
  }

  const context = run(host, ['context-delivery', '--message', spec.message, '--journal', '--message-id', messageId, '--session-id', sessionId, '--format=json'])
  if (context.status !== 0) {
    row.errors.push(`context-delivery failed status=${context.status}: ${compact(context.stderr || context.stdout)}`)
  } else {
    try {
      const packet = JSON.parse(context.stdout)
      row.contextDelivery = sanitizeContextPacket(packet)
    } catch (error) {
      row.errors.push(`context-delivery JSON parse failed: ${String(error)}`)
    }
  }

  const journalRow = latestPacketJournal(host)
  row.packetJournal.checked = true
  if (journalRow) {
    row.packetJournal.hasMessageHash = Boolean((journalRow as any).messageIdHash)
    row.packetJournal.rawMessagePresent = JSON.stringify(journalRow).includes(spec.message)
  }

  const decision = run(host, ['record-decision', '--message', spec.label, '--validation-only', '--validation', `context dogfood collection ${spec.label}`, '--format=json'])
  if (decision.status !== 0) {
    row.errors.push(`record-decision failed status=${decision.status}: ${compact(decision.stderr || decision.stdout)}`)
  } else {
    try {
      const packet = JSON.parse(decision.stdout)
      row.recordDecision = sanitizeRecordDecision(packet)
    } catch (error) {
      row.errors.push(`record-decision JSON parse failed: ${String(error)}`)
    }
  }

  return row
}

function writeRows(outPath: string, rows: DogfoodRow[], append: boolean): void {
  mkdirSync(path.dirname(outPath), { recursive: true })
  const payload = rows.map((row) => JSON.stringify(row, null, 0)).join('\n') + '\n'
  if (append && existsSync(outPath)) {
    const existing = readFileSync(outPath, 'utf8')
    writeFileSync(outPath, existing + payload, 'utf8')
  } else {
    writeFileSync(outPath, payload, 'utf8')
  }
}

function renderMarkdown(rows: DogfoodRow[], outPath: string, dryRun: boolean): string {
  const lines = ['# Context Broker Dogfood', '', `- Rows: ${rows.length}`, `- Output: ${dryRun ? '(dry-run)' : outPath}`, '', '| Host | Case | Context | Required | Decision | Journal raw? | Errors |', '|---|---|---:|---:|---|---|---:|']
  for (const row of rows) {
    const hostName = path.basename(row.host)
    lines.push(`| ${hostName} | ${row.caseLabel} | ${row.contextDelivery.ok ? 'ok' : 'fail'} | ${row.contextDelivery.requiredReadCount ?? 0} | ${row.recordDecision.disposition || 'fail'} | ${row.packetJournal.rawMessagePresent ? 'yes' : 'no'} | ${row.errors.length} |`)
  }
  lines.push('')
  return lines.join('\n')
}

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  const rows: DogfoodRow[] = []
  for (const host of args.hosts) {
    const lazy = path.join(host, '.lazy-harness', 'bin', 'lazy')
    if (!existsSync(lazy)) {
      rows.push({
        schemaVersion: '1.0',
        event: 'context-broker.dogfood',
        timestamp: new Date().toISOString(),
        host,
        hostMarker: readMarker(host),
        caseLabel: 'host-missing-lazy-cli',
        messageHash: hash(host),
        contextDelivery: { ok: false },
        packetJournal: { checked: false },
        recordDecision: { ok: false },
        errors: [`missing lazy CLI: ${lazy}`],
      })
      continue
    }
    for (const spec of args.cases) rows.push(collectCase(host, spec))
  }
  if (!args.dryRun) writeRows(args.outPath, rows, args.append)
  if (args.format === 'md') process.stdout.write(renderMarkdown(rows, args.outPath, args.dryRun))
  else process.stdout.write(`${JSON.stringify({ schemaVersion: '1.0', rows, outPath: args.dryRun ? null : args.outPath, dryRun: args.dryRun }, null, 2)}\n`)
}

main()
