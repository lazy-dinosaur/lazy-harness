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
  format: 'json' | 'markdown' | 'jcode-prompt'
  includeReadme: boolean
}

interface RecordAudit {
  path: string
  layer: string
  hasImplementationMap: boolean
  hasImplementationHints: boolean
  status: 'ok' | 'needs-map' | 'no-implementation-hints' | 'needs-review'
  hints: string[]
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
      if (!['json', 'markdown', 'jcode-prompt'].includes(value)) throw new Error(`Invalid --format: ${value}`)
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
  --format json|markdown|jcode-prompt
                               Output format (default: markdown)
  --include-readme             Include README.md files
  --help                       Show help

This script is read-only. It never edits host records.`)
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
  return { path: relPath, layer, hasImplementationMap, hasImplementationHints, status, hints }
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
    return
  }
  console.log('| Status | Layer | Path | Hints |')
  console.log('|---|---|---|---|')
  for (const record of needs) {
    console.log(`| ${record.status} | ${record.layer} | \`${record.path}\` | ${record.hints.join(', ') || '-'} |`)
  }
}

function printJcodePrompt(records: RecordAudit[]): void {
  const needs = records.filter((record) => record.status === 'needs-map' || record.status === 'needs-review')
  console.log('Migrate these lazy-harness records to ADR 0030 implementation maps. Follow `.lazy-harness/spec/platform/implementation-map-migration.md`. Do not invent symbols. Inspect source with file reads/LSP/outline before marking verified. Update Markdown Implementation map sections and add graph facts only when confirmed or clearly code-evidenced.\n')
  if (needs.length === 0) {
    console.log('No candidate records found by audit.')
    return
  }
  for (const record of needs) {
    console.log(`- ${record.status} ${record.layer} ${record.path} (hints: ${record.hints.join(', ') || 'none'})`)
  }
}

function main(): void {
  try {
    const args = parseArgs(process.argv.slice(2))
    const root = resolve(args.root)
    const records = audit(root, args.includeReadme)
    if (args.format === 'json') {
      console.log(JSON.stringify({ root, summary: summarize(records), records }, null, 2))
    } else if (args.format === 'jcode-prompt') {
      printJcodePrompt(records)
    } else {
      printMarkdown(records)
    }
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    process.exit(1)
  }
}

main()
