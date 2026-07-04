#!/usr/bin/env bun
/**
 * retro.ts — retro learning loop MVP (W4, memory-device-implementation-plan).
 *
 * Subcommands:
 *   feedback  — append a classified feedback entry to `.lazy-harness/retrospective/feedback.jsonl`
 *               (L1 implementation / L2 design / L3 spec; optional kind signature + vocab harvest).
 *   report    — read-only aggregation: KPT summary + deterministic pattern detection
 *               (identical `kind` signature appearing >= 3 times → promotion candidate).
 *               Writes `.lazy-harness/retrospective/retro-<date>.md` unless --dry-run.
 *   resolve   — mark a feedback entry resolved after its promotion/fix is user-confirmed.
 *
 * Boundaries (SSOT cli-tool-boundary, ADR 0041/0053):
 *   - deterministic matching only (no semantic scoring, no custom search);
 *   - the CLI never promotes anything: pattern candidates are PRESENTED; promotion to
 *     record/policy/capability happens through a user option gate driven by the agent;
 *   - vocab harvest feeds ADR 0053 surface-term seeding; the CLI only stores terms.
 *
 * Contract: `.lazy-harness/spec/platform/retro-loop.md`.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync } from 'node:fs'
import path from 'node:path'

type Level = 1 | 2 | 3

interface FeedbackEntry {
  id: string
  ts: string
  level: Level
  kind: string
  message: string
  vocab: string[]
  refs: string[]
  source: 'agent' | 'user'
  status: 'open' | 'resolved'
  resolution: string | null
}

function findHarnessRoot(start: string): string | null {
  let cur = path.resolve(start)
  while (true) {
    if (existsSync(path.join(cur, '.lazy-harness'))) return cur
    const parent = path.dirname(cur)
    if (parent === cur) return null
    cur = parent
  }
}

function usage(code = 2): never {
  const out = code === 0 ? console.log : console.error
  out(`Retro Loop (W4 MVP)

Usage:
  lazy retro feedback --level 1|2|3 --kind <signature> --message <text> [--vocab a,b] [--refs p1,p2] [--source agent|user]
  lazy retro report [--format=json|md] [--dry-run]
  lazy retro resolve --id <fb-id> --resolution <text>

feedback levels: 1=implementation 2=design 3=spec/requirement.
kind is the deterministic pattern signature (e.g. premature-execution, recall-miss-synthesis).
Patterns = same kind >= 3 entries; the CLI only reports candidates — promotion goes through a user option gate.`)
  process.exit(code)
}

function arg(argv: string[], name: string): string | null {
  const idx = argv.findIndex((a) => a === `--${name}`)
  if (idx >= 0 && argv[idx + 1]) return argv[idx + 1]
  const pref = argv.find((a) => a.startsWith(`--${name}=`))
  return pref ? pref.slice(name.length + 3) : null
}

function loadEntries(file: string): FeedbackEntry[] {
  if (!existsSync(file)) return []
  const out: FeedbackEntry[] = []
  for (const line of readFileSync(file, 'utf8').split('\n')) {
    if (!line.trim()) continue
    try {
      out.push(JSON.parse(line) as FeedbackEntry)
    } catch {
      /* report counts parse errors below */
    }
  }
  return out
}

function cmdFeedback(root: string, argv: string[]): number {
  const levelRaw = arg(argv, 'level')
  const kind = arg(argv, 'kind')
  const message = arg(argv, 'message')
  if (!levelRaw || !kind || !message) usage()
  const level = Number(levelRaw)
  if (level !== 1 && level !== 2 && level !== 3) usage()
  if (!/^[a-z0-9][a-z0-9-]*$/.test(kind)) {
    console.error(`retro feedback: kind must be a lowercase-hyphen signature, got '${kind}'`)
    return 2
  }
  const sourceRaw = arg(argv, 'source') || 'agent'
  const source = sourceRaw === 'user' ? 'user' : 'agent'
  const vocab = (arg(argv, 'vocab') || '').split(',').map((s) => s.trim()).filter(Boolean)
  const refs = (arg(argv, 'refs') || '').split(',').map((s) => s.trim()).filter(Boolean)
  const dir = path.join(root, '.lazy-harness', 'retrospective')
  mkdirSync(dir, { recursive: true })
  const file = path.join(dir, 'feedback.jsonl')
  const entry: FeedbackEntry = {
    id: `fb-${Date.now().toString(36)}-${Math.floor(Math.random() * 1296).toString(36).padStart(2, '0')}`,
    ts: new Date().toISOString(),
    level: level as Level,
    kind,
    message,
    vocab,
    refs,
    source,
    status: 'open',
    resolution: null,
  }
  appendFileSync(file, `${JSON.stringify(entry)}\n`)
  console.log(`retro feedback: recorded ${entry.id} (L${level}, kind=${kind}${vocab.length ? `, vocab=${vocab.length}` : ''})`)
  return 0
}

function cmdResolve(root: string, argv: string[]): number {
  const id = arg(argv, 'id')
  const resolution = arg(argv, 'resolution')
  if (!id || !resolution) usage()
  const file = path.join(root, '.lazy-harness', 'retrospective', 'feedback.jsonl')
  const entries = loadEntries(file)
  const target = entries.find((e) => e.id === id)
  if (!target) {
    console.error(`retro resolve: no entry with id '${id}'`)
    return 1
  }
  target.status = 'resolved'
  target.resolution = resolution
  writeFileSync(file, `${entries.map((e) => JSON.stringify(e)).join('\n')}\n`)
  console.log(`retro resolve: ${id} marked resolved`)
  return 0
}

function cmdReport(root: string, argv: string[]): number {
  const format = (arg(argv, 'format') || 'md') as 'md' | 'json'
  const dryRun = argv.includes('--dry-run')
  const file = path.join(root, '.lazy-harness', 'retrospective', 'feedback.jsonl')
  const entries = loadEntries(file)
  const open = entries.filter((e) => e.status === 'open')
  const resolved = entries.filter((e) => e.status === 'resolved')

  const byKind = new Map<string, FeedbackEntry[]>()
  for (const e of entries) {
    if (!byKind.has(e.kind)) byKind.set(e.kind, [])
    byKind.get(e.kind)!.push(e)
  }
  const patterns = [...byKind.entries()]
    .filter(([, list]) => list.length >= 3)
    .map(([kind, list]) => ({
      kind,
      total: list.length,
      open: list.filter((e) => e.status === 'open').length,
      levels: [...new Set(list.map((e) => e.level))].sort(),
      vocab: [...new Set(list.flatMap((e) => e.vocab))],
      refs: [...new Set(list.flatMap((e) => e.refs))].slice(0, 10),
    }))
    .sort((a, b) => b.total - a.total)

  const vocabHarvest = [...new Set(entries.flatMap((e) => e.vocab))]

  // skipped.jsonl summary (optional data source)
  const skippedFile = path.join(root, '.lazy-harness', 'logs', 'skipped.jsonl')
  const skippedCount = existsSync(skippedFile)
    ? readFileSync(skippedFile, 'utf8').split('\n').filter((l) => l.trim()).length
    : 0

  const result = {
    schemaVersion: '1.0',
    mode: 'retro-report',
    generatedAt: new Date().toISOString(),
    totals: { entries: entries.length, open: open.length, resolved: resolved.length, skippedLog: skippedCount },
    byLevel: {
      L1: entries.filter((e) => e.level === 1).length,
      L2: entries.filter((e) => e.level === 2).length,
      L3: entries.filter((e) => e.level === 3).length,
    },
    patterns,
    vocabHarvest,
    note: 'Deterministic aggregation only. Pattern candidates (kind >= 3) require a USER OPTION GATE before promotion to record/policy/capability; vocab terms feed ADR 0053 surface-term seeding via the same gate.',
  }

  const lines: string[] = []
  lines.push(`# Retro report — ${new Date().toISOString().slice(0, 10)}`)
  lines.push('')
  lines.push(`- entries: ${result.totals.entries} (open ${result.totals.open} / resolved ${result.totals.resolved}) · levels L1=${result.byLevel.L1} L2=${result.byLevel.L2} L3=${result.byLevel.L3} · skipped-log rows: ${skippedCount}`)
  lines.push('')
  lines.push('## Keep (resolved)')
  if (!resolved.length) lines.push('- none yet')
  for (const e of resolved.slice(-10)) lines.push(`- [${e.kind}] ${e.message} → ${e.resolution}`)
  lines.push('')
  lines.push('## Problem (open feedback)')
  if (!open.length) lines.push('- none')
  for (const e of open.slice(-20)) lines.push(`- \`${e.id}\` [L${e.level}/${e.kind}] ${e.message}`)
  lines.push('')
  lines.push('## Try (pattern candidates — REQUIRE user option gate before promotion)')
  if (!patterns.length) lines.push('- no kind has reached the 3-repeat threshold')
  for (const p of patterns) {
    lines.push(`- **${p.kind}** ×${p.total} (open ${p.open}, levels ${p.levels.map((l) => `L${l}`).join('/')})`)
    if (p.vocab.length) lines.push(`  - harvested vocab: ${p.vocab.join(', ')}`)
    if (p.refs.length) lines.push(`  - refs: ${p.refs.map((r) => `\`${r}\``).join(', ')}`)
  }
  lines.push('')
  lines.push('## Vocab harvest (surface-term seeding queue, ADR 0053)')
  if (!vocabHarvest.length) lines.push('- empty')
  else lines.push(`- ${vocabHarvest.join(', ')}`)
  lines.push('')
  lines.push(`> ${result.note}`)
  const md = `${lines.join('\n')}\n`

  if (!dryRun) {
    const outPath = path.join(root, '.lazy-harness', 'retrospective', `retro-${new Date().toISOString().slice(0, 10)}.md`)
    writeFileSync(outPath, md)
    console.error(`retro report: wrote ${path.relative(root, outPath)}`)
  }
  if (format === 'json') console.log(JSON.stringify(result, null, 2))
  else process.stdout.write(md)
  return 0
}

function main(): number {
  const argv = process.argv.slice(2)
  if (!argv.length || argv[0] === '--help' || argv[0] === '-h') usage(argv.length ? 0 : 2)
  const rootArg = arg(argv, 'root')
  const root = findHarnessRoot(rootArg ? path.resolve(rootArg) : process.cwd())
  if (!root) {
    console.error('retro: no .lazy-harness root found')
    return 1
  }
  const sub = argv[0]
  if (sub === 'feedback') return cmdFeedback(root, argv.slice(1))
  if (sub === 'report') return cmdReport(root, argv.slice(1))
  if (sub === 'resolve') return cmdResolve(root, argv.slice(1))
  usage()
}

process.exit(main())
