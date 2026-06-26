#!/usr/bin/env bun
/**
 * implementation-map-audit — non-destructive audit for ADR 0030 migration.
 *
 * Scans host .lazy-harness layer Markdown records and reports which records likely
 * need an Implementation map section. This script does not edit files.
 */

import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'

interface Args {
  root: string
  format: 'json' | 'markdown' | 'agent-prompt'
  includeReadme: boolean
}

interface RecordAudit {
  path: string
  layer: string
  hasImplementationMap: boolean
  hasImplementationHints: boolean
  status: 'ok' | 'needs-map' | 'no-implementation-hints' | 'needs-review'
  hints: string[]
  mapStatus: string | null
  drift: string[]
  driftDetail: string[]
  driftFiles: string[]
}

const LAYER_DIRS: Array<[string, string]> = [
  ['ddd', 'domain'],
  ['sdd', 'spec'],
  ['bdd', 'behavior'],
  ['tdd', 'tests'],
  ['adr', 'decisions'],
  ['ssot', 'ssot']
]

const HINT_PATTERNS: Array<[string, RegExp]> = [
  ['source path', /\b(src|app|pages|components|lib|server|api|routes|prisma|scripts|hooks)\//i],
  ['test path', /\b(test|tests|spec|__tests__)\//i],
  ['function mention', /\b(function|class|component|hook|handler|route|schema|model|service|controller|resolver)\b/i],
  ['code fence', /```(?:ts|tsx|js|jsx|py|rs|go|java|kt|swift|sql|json|yaml|yml)/i],
  ['file extension', /\b[\w./-]+\.(ts|tsx|js|jsx|py|sql|prisma|json|yaml|yml|mdx?)\b/i]
]

function parseArgs(argv: string[]): Args {
  const args: Args = { root: process.cwd(), format: 'markdown', includeReadme: false }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--root') args.root = argv[++i]
    else if (a.startsWith('--root=')) args.root = a.slice('--root='.length)
    else if (a === '--format' || a.startsWith('--format=')) {
      const value = a.startsWith('--format=') ? a.slice('--format='.length) : argv[++i]
      if (!['json', 'markdown', 'agent-prompt'].includes(value)) throw new Error(`Invalid --format: ${value}`)
      args.format = value as Args['format']
    } else if (a === '--include-readme') args.includeReadme = true
    else if (a === '--help' || a === '-h') {
      printHelp()
      process.exit(0)
    } else {
      throw new Error(`Unknown flag: ${a}`)
    }
  }
  return args
}

function printHelp(): void {
  console.log(`implementation-map-audit — audit ADR 0030 record migration

Usage:
  bun .lazy-harness/scripts/implementation-map-audit.ts [options]

Options:
  --root <dir>                 Host root (default: cwd)
  --format json|markdown|agent-prompt
                               Output format (default: markdown)
  --include-readme             Include README.md files
  --help                       Show help

This script is read-only. It never edits host records.
It also reports advisory Implementation-map status drift (planned-but-files-present, verified-but-files-missing).`)
}

function walkMarkdown(dir: string): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  const entries = readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const path = join(dir, entry.name)
    if (entry.isDirectory()) out.push(...walkMarkdown(path))
    else if (entry.isFile() && entry.name.endsWith('.md')) out.push(path)
  }
  return out
}

const CODE_EXT = /\.(ts|tsx|js|jsx|mjs|cjs|py|sh|bash|sql|prisma|rs|go|rb|java|kt|swift)$/i

/** Body of a `## <heading>` section (until the next h2 or EOF), fenced code blocks stripped. */
function extractSection(text: string, headingRe: RegExp): string | null {
  const lines = text.split('\n')
  let start = -1
  for (let i = 0; i < lines.length; i++) {
    if (headingRe.test(lines[i])) {
      start = i + 1
      break
    }
  }
  if (start === -1) return null
  let end = lines.length
  for (let i = start; i < lines.length; i++) {
    if (/^##\s+/.test(lines[i])) {
      end = i
      break
    }
  }
  return lines.slice(start, end).join('\n').replace(/```[\s\S]*?```/g, '')
}

/** First `- Status:` value inside a section block, lowercased with backticks stripped; null for template placeholders. */
function parseStatus(block: string): string | null {
  const match = block.match(/^\s*-\s*Status:\s*(.+?)\s*$/im)
  if (!match) return null
  const value = match[1].replace(/`/g, '').trim().toLowerCase()
  if (!value || value.includes('|')) return null
  return value.split(/\s+/)[0]
}

/** A backtick token is a checkable path: slash + file extension, no spaces, env vars, globs, anchors, or placeholders. */
function isCleanPath(token: string): boolean {
  if (!token.includes('/')) return false
  if (/[\s$*<>"\[\]#]/.test(token)) return false
  if (token.startsWith('path/to/')) return false
  return /\.[a-z0-9]{1,5}$/i.test(token)
}

/** Resolve a ref against the host root, with a `.lazy-harness/`-relative fallback for shorthand like `knowledge/graph.jsonl`. */
function refExists(root: string, ref: string): boolean {
  if (existsSync(resolve(root, ref))) return true
  if (!ref.startsWith('.lazy-harness/') && existsSync(resolve(root, '.lazy-harness', ref))) return true
  return false
}

/** Clean path refs listed under `Primary files:` / `Future files:` only (excludes Tests/validation/cross-layer noise). */
function extractPrimaryFutureRefs(block: string): string[] {
  const refs = new Set<string>()
  let inside = false
  for (const line of block.split('\n')) {
    const keyMatch = line.match(/^\s*-\s*([A-Za-z][\w /]*?):\s*$/)
    if (keyMatch) {
      const key = keyMatch[1].trim().toLowerCase()
      inside = key === 'primary files' || key === 'future files'
      continue
    }
    if (!inside) continue
    for (const match of line.matchAll(/`([^`]+)`/g)) {
      const token = match[1].trim()
      if (isCleanPath(token)) refs.add(token)
    }
  }
  return [...refs]
}

function auditRecord(root: string, layer: string, absPath: string, includeReadme: boolean): RecordAudit | null {
  const relPath = relative(root, absPath)
  if (!includeReadme && relPath.endsWith('/README.md')) return null
  const text = readFileSync(absPath, 'utf8')
  const hasImplementationMap = /^##\s+Implementation map\b/im.test(text)
  const hints = HINT_PATTERNS.filter(([, pattern]) => pattern.test(text)).map(([label]) => label)
  const hasImplementationHints = hints.length > 0
  let status: RecordAudit['status']
  if (hasImplementationMap && hasImplementationHints) status = 'ok'
  else if (hasImplementationMap && !hasImplementationHints) status = 'needs-review'
  else if (!hasImplementationMap && hasImplementationHints) status = 'needs-map'
  else status = 'no-implementation-hints'

  let mapStatus: string | null = null
  const drift: string[] = []
  const driftDetail: string[] = []
  const driftFiles: string[] = []
  const mapBlock = extractSection(text, /^##\s+Implementation map\b/i)
  if (mapBlock !== null) {
    mapStatus = parseStatus(mapBlock)
    const digestBlock = extractSection(text, /^##\s+Rule digest\b/i)
    const digestStatus = digestBlock ? parseStatus(digestBlock) : null
    const dead = digestStatus === 'deprecated' || digestStatus === 'reverted'
    if (!dead) {
      const refs = extractPrimaryFutureRefs(mapBlock)
      const presentCode = refs.filter((ref) => CODE_EXT.test(ref) && refExists(root, ref))
      const missing = refs.filter((ref) => !refExists(root, ref))
      if ((mapStatus === 'planned' || mapStatus === 'none') && presentCode.length > 0) {
        drift.push('planned-status-files-present')
        driftDetail.push(`Status='${mapStatus}' but implementing files exist: ${presentCode.join(', ')}`)
        driftFiles.push(...presentCode)
      }
      if (mapStatus === 'verified' && missing.length > 0) {
        drift.push('verified-status-files-missing')
        driftDetail.push(`Status='verified' but Primary/Future files missing: ${missing.join(', ')}`)
        driftFiles.push(...missing)
      }
    }
  }
  return { path: relPath, layer, hasImplementationMap, hasImplementationHints, status, hints, mapStatus, drift, driftDetail, driftFiles }
}

function audit(root: string, includeReadme: boolean): RecordAudit[] {
  const lazyRoot = join(root, '.lazy-harness')
  if (!existsSync(lazyRoot) || !statSync(lazyRoot).isDirectory()) {
    throw new Error(`No .lazy-harness directory under root: ${root}`)
  }
  const records: RecordAudit[] = []
  for (const [layer, dirName] of LAYER_DIRS) {
    const dir = join(lazyRoot, dirName)
    for (const file of walkMarkdown(dir)) {
      const record = auditRecord(root, layer, file, includeReadme)
      if (record) records.push(record)
    }
  }
  return records.sort((a, b) => a.path.localeCompare(b.path))
}

function summarize(records: RecordAudit[]): Record<string, number> {
  return records.reduce<Record<string, number>>((acc, record) => {
    acc[record.status] = (acc[record.status] ?? 0) + 1
    return acc
  }, {})
}

function printMarkdown(records: RecordAudit[]): void {
  const summary = summarize(records)
  console.log('# Implementation map audit\n')
  console.log('| Status | Count |')
  console.log('|---|---:|')
  for (const key of ['needs-map', 'needs-review', 'ok', 'no-implementation-hints']) {
    console.log(`| ${key} | ${summary[key] ?? 0} |`)
  }
  console.log('\n## Records needing migration\n')
  const needs = records.filter((record) => record.status === 'needs-map' || record.status === 'needs-review')
  if (needs.length === 0) {
    console.log('No records need implementation-map migration based on current heuristics.')
  } else {
    console.log('| Status | Layer | Path | Hints |')
    console.log('|---|---|---|---|')
    for (const record of needs) {
      console.log(`| ${record.status} | ${record.layer} | \`${record.path}\` | ${record.hints.join(', ') || '-'} |`)
    }
  }
  console.log('\n## Implementation status drift\n')
  console.log('Advisory only: file existence is a heuristic, not proof of completion.\n')
  const drifted = records.filter((record) => record.drift.length > 0)
  if (drifted.length === 0) {
    console.log('No implementation-map status drift candidates.')
  } else {
    console.log('| Drift | Layer | Path | Detail |')
    console.log('|---|---|---|---|')
    for (const record of drifted) {
      console.log(`| ${record.drift.join(', ')} | ${record.layer} | \`${record.path}\` | ${record.driftDetail.join('; ')} |`)
    }
  }
}

function printAgentPrompt(records: RecordAudit[]): void {
  const needs = records.filter((record) => record.status === 'needs-map' || record.status === 'needs-review')
  console.log('Migrate these lazy-harness records to ADR 0030 implementation maps. Follow `.lazy-harness/spec/platform/implementation-map-migration.md`. Do not invent symbols. Inspect source with file reads/LSP/outline before marking verified. Update Markdown Implementation map sections and add graph facts only when confirmed or clearly code-evidenced.\n')
  if (needs.length === 0) {
    console.log('No candidate records found by audit.')
  } else {
    for (const record of needs) {
      console.log(`- ${record.status} ${record.layer} ${record.path} (hints: ${record.hints.join(', ') || 'none'})`)
    }
  }
  const drifted = records.filter((record) => record.drift.length > 0)
  if (drifted.length > 0) {
    console.log('\nReview these implementation-map status drift candidates (advisory; file existence is a heuristic, not proof of completion):')
    for (const record of drifted) {
      console.log(`- ${record.drift.join(', ')} ${record.layer} ${record.path} — ${record.driftDetail.join('; ')}`)
    }
  }
}

function main(): void {
  try {
    const args = parseArgs(process.argv.slice(2))
    const root = resolve(args.root)
    const records = audit(root, args.includeReadme)
    if (args.format === 'json') {
      const driftCandidates = records.filter((record) => record.drift.length > 0).map((record) => ({ path: record.path, layer: record.layer, mapStatus: record.mapStatus, drift: record.drift, driftDetail: record.driftDetail, driftFiles: record.driftFiles }))
      console.log(JSON.stringify({ root, summary: summarize(records), driftCandidates, records }, null, 2))
    } else if (args.format === 'agent-prompt') {
      printAgentPrompt(records)
    } else {
      printMarkdown(records)
    }
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    process.exit(1)
  }
}

main()
