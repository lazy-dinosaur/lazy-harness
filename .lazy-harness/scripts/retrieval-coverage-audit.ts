#!/usr/bin/env bun
/**
 * retrieval-coverage-audit.ts
 *
 * Read-only coverage audit for LLM-owned record retrieval. This tool inspects
 * deterministic record-index/feature/graph surfaces and reports whether a query
 * produced enough structural entrypoints to continue reading. It is not a
 * semantic search engine and must not decide intent, confidence, risk, gates,
 * required reads, or next actions.
 */
import path from 'node:path'
import { existsSync, readFileSync } from 'node:fs'
import { buildRecordIndex, type RecordIndex } from './record-index.ts'

type Format = 'json' | 'md'
type CoverageState = 'mapped' | 'partial' | 'gap'

interface Args {
  root: string
  query: string
  format: Format
  limit: number
}

interface MatchItem {
  kind: 'feature' | 'record' | 'graph'
  id: string
  label: string
  matchedFields: string[]
}

interface RetrievalCoverageAudit {
  schemaVersion: '1.0'
  mode: 'retrieval-coverage-audit'
  query: string
  root: string
  source: {
    method: 'retrieval-coverage-audit-v1'
    tool: '.lazy-harness/scripts/retrieval-coverage-audit.ts'
    recordIndexMethod: 'record-index-v1'
  }
  notes: string[]
  counts: {
    features: number
    records: number
    graphRows: number
    recordCandidates: number
    sourceCandidates: number
    testCandidates: number
  }
  coverage: {
    state: CoverageState
    gaps: string[]
  }
  matches: MatchItem[]
  candidates: {
    recordPaths: string[]
    sourceFiles: string[]
    testFiles: string[]
    graphIds: string[]
    unresolvedTerms: string[]
  }
  commands: {
    overview: string
    concreteMapNodes: string[]
    missingPrerequisite: string
  }
}

function usage(exitCode = 2): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Retrieval Coverage Audit\n\nUsage:\n  .lazy-harness/bin/lazy retrieval-audit <term-or-file> [--format=json|md] [--limit=N]\n\nRead-only coverage audit for lazy map/record-index retrieval. Reports structural coverage gaps and fallback commands. It is not semantic authority.`)
  process.exit(exitCode)
}

function parseArgs(argv: string[]): Args {
  const args: Args = { root: process.env.LAZY_HOST_ROOT || process.cwd(), query: '', format: 'md', limit: 8 }
  const queryParts: string[] = []
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = argv[i + 1]
    if (arg === '--help' || arg === '-h') usage(0)
    else if ((arg === '--root' || arg === '--host') && next) { args.root = next; i += 1 }
    else if (arg.startsWith('--root=')) args.root = arg.slice('--root='.length)
    else if (arg.startsWith('--host=')) args.root = arg.slice('--host='.length)
    else if ((arg === '--format' || arg === '-f') && next) { args.format = normalizeFormat(next); i += 1 }
    else if (arg.startsWith('--format=')) args.format = normalizeFormat(arg.slice('--format='.length))
    else if ((arg === '--limit' || arg === '-n') && next) { args.limit = normalizeLimit(next); i += 1 }
    else if (arg.startsWith('--limit=')) args.limit = normalizeLimit(arg.slice('--limit='.length))
    else if (arg.startsWith('-')) throw new Error(`Unknown argument: ${arg}`)
    else queryParts.push(arg)
  }
  args.query = queryParts.join(' ').trim()
  if (!args.query) usage()
  args.root = path.resolve(args.root)
  return args
}

function normalizeFormat(value: string): Format {
  if (value === 'markdown') return 'md'
  if (value === 'json' || value === 'md') return value
  throw new Error(`Unsupported --format: ${value}`)
}

function normalizeLimit(value: string): number {
  const n = Number(value)
  if (!Number.isInteger(n) || n < 1 || n > 100) throw new Error(`Unsupported --limit: ${value}`)
  return n
}

function shellQuote(value: string): string {
  return `'${value.replace(/'/g, `'"'"'`)}'`
}

function uniq(values: Array<string | undefined | null>): string[] {
  return Array.from(new Set(values.map((value) => (value || '').trim()).filter(Boolean))).sort((a, b) => a.localeCompare(b))
}

function compact(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9가-힣]/g, '')
}

function normalized(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9가-힣]+/g, ' ').trim()
}

function queryTerms(query: string): string[] {
  const base = normalized(query)
  const parts = base.split(/\s+/).filter((part) => part.length >= 2)
  return uniq([base, compact(query), ...parts, ...parts.map(compact)]).slice(0, 12)
}

function matches(query: string, value: string): boolean {
  if (!value) return false
  const base = normalized(query)
  const compactBase = compact(query)
  const parts = base.split(/\s+/).filter((part) => part.length >= 2)
  const hay = normalized(value)
  const compactHay = compact(value)
  if (base && hay.includes(base)) return true
  if (compactBase && compactHay.includes(compactBase)) return true
  if (parts.length > 1) return parts.every((part) => compactHay.includes(compact(part)))
  return queryTerms(query).some((term) => term && (hay.includes(term) || compactHay.includes(compact(term))))
}

function addMatch(fields: string[], query: string, field: string, values: string[] | string | undefined): void {
  const list = Array.isArray(values) ? values : values ? [values] : []
  if (list.some((value) => matches(query, value))) fields.push(field)
}

function rowStrings(value: unknown): string[] {
  if (typeof value === 'string') return [value]
  if (Array.isArray(value)) return value.flatMap(rowStrings)
  if (value && typeof value === 'object') return Object.values(value as Record<string, unknown>).flatMap(rowStrings)
  return []
}

function buildAudit(args: Args): RetrievalCoverageAudit {
  const index = buildRecordIndex(args.root)
  const matchesOut: MatchItem[] = []
  const recordPaths: string[] = []
  const sourceFiles: string[] = []
  const testFiles: string[] = []
  const graphIds: string[] = []

  for (const feature of index.projectProfile.features) {
    const fields: string[] = []
    addMatch(fields, args.query, 'feature.id', feature.id)
    addMatch(fields, args.query, 'feature.label', feature.label)
    addMatch(fields, args.query, 'feature.aliases', feature.aliases.map((alias) => alias.value))
    addMatch(fields, args.query, 'feature.routes', feature.routes)
    addMatch(fields, args.query, 'feature.components', feature.components)
    addMatch(fields, args.query, 'feature.records', feature.records.map((record) => record.path))
    addMatch(fields, args.query, 'feature.sourceFiles', feature.sourceFiles)
    addMatch(fields, args.query, 'feature.tests', feature.tests)
    if (!fields.length) continue
    matchesOut.push({ kind: 'feature', id: feature.id, label: feature.label || feature.id, matchedFields: uniq(fields) })
    recordPaths.push(...feature.records.map((record) => record.path))
    sourceFiles.push(...feature.sourceFiles)
    testFiles.push(...feature.tests)
  }

  for (const record of index.records) {
    const fields: string[] = []
    addMatch(fields, args.query, 'record.path', record.recordPath)
    addMatch(fields, args.query, 'record.title', record.title)
    addMatch(fields, args.query, 'record.aliases', record.aliases)
    addMatch(fields, args.query, 'record.surfaceTerms', record.surfaceTerms)
    addMatch(fields, args.query, 'record.appliesWhen', record.digest.appliesWhen)
    addMatch(fields, args.query, 'record.must', record.digest.must)
    addMatch(fields, args.query, 'record.relatedRecords', record.digest.relatedRecords)
    addMatch(fields, args.query, 'record.sourceFiles', record.implementationHints.fileHints)
    addMatch(fields, args.query, 'record.testFiles', record.implementationHints.testHints)
    addMatch(fields, args.query, 'record.symbols', record.implementationHints.symbolHints)
    addMatch(fields, args.query, 'record.routes', record.implementationHints.routeHints)
    if (!fields.length) continue
    matchesOut.push({ kind: 'record', id: record.recordPath, label: record.title, matchedFields: uniq(fields) })
    recordPaths.push(record.recordPath, ...record.digest.relatedRecords)
    sourceFiles.push(...record.implementationHints.fileHints)
    testFiles.push(...record.implementationHints.testHints)
    graphIds.push(...record.graphIds)
  }

  const graphRows = loadGraphRows(index)
  for (const row of graphRows) {
    const strings = rowStrings(row)
    if (!strings.some((value) => matches(args.query, value))) continue
    const id = typeof row.id === 'string' ? row.id : `graph-row-${matchesOut.length + 1}`
    matchesOut.push({ kind: 'graph', id, label: [row.relation, row.path, row.target].filter(Boolean).join(' ') || id, matchedFields: ['graph.row'] })
    if (typeof row.id === 'string') graphIds.push(row.id)
    if (typeof row.path === 'string') sourceFiles.push(row.path)
    if (typeof row.source === 'string' && row.source.startsWith('.lazy-harness/')) recordPaths.push(row.source)
    if (typeof row.target === 'string') {
      if (row.target.startsWith('.lazy-harness/')) recordPaths.push(row.target)
      else sourceFiles.push(row.target)
    }
  }

  const limitedMatches = matchesOut.slice(0, args.limit)
  const candidates = {
    recordPaths: uniq(recordPaths).slice(0, args.limit),
    sourceFiles: uniq(sourceFiles).slice(0, args.limit),
    testFiles: uniq(testFiles).slice(0, args.limit),
    graphIds: uniq(graphIds).slice(0, args.limit),
    unresolvedTerms: queryTerms(args.query).filter((term) => term !== normalized(args.query)).slice(0, args.limit),
  }
  const gaps: string[] = []
  if (!matchesOut.length) gaps.push('no-map-matches')
  if (!candidates.recordPaths.length) gaps.push('no-record-candidates')
  if (!candidates.sourceFiles.length) gaps.push('no-source-candidates')
  if (!candidates.testFiles.length) gaps.push('no-test-candidates')
  if (!candidates.graphIds.length) gaps.push('no-graph-candidates')
  const state: CoverageState = !matchesOut.length ? 'gap' : gaps.length ? 'partial' : 'mapped'
  const concreteNodes = Array.from(new Set([...limitedMatches.map((item) => item.id), ...candidates.recordPaths, ...candidates.sourceFiles, ...candidates.testFiles, ...candidates.graphIds])).filter((node) => node && !/\s/.test(node))
  return {
    schemaVersion: '1.0',
    mode: 'retrieval-coverage-audit',
    query: args.query,
    root: args.root,
    source: {
      method: 'retrieval-coverage-audit-v1',
      tool: '.lazy-harness/scripts/retrieval-coverage-audit.ts',
      recordIndexMethod: 'record-index-v1',
    },
    notes: [
      'Coverage audit is map/index coverage only; it is not semantic authority.',
      'The LLM/searcher must read real records/source/tests and decide whether evidence is sufficient.',
      'If coverage is gap or partial, inspect concrete map nodes surfaced by the audit; if none exist, ask an option gate or state the missing prerequisite.',
    ],
    counts: {
      features: matchesOut.filter((item) => item.kind === 'feature').length,
      records: matchesOut.filter((item) => item.kind === 'record').length,
      graphRows: matchesOut.filter((item) => item.kind === 'graph').length,
      recordCandidates: candidates.recordPaths.length,
      sourceCandidates: candidates.sourceFiles.length,
      testCandidates: candidates.testFiles.length,
    },
    coverage: { state, gaps },
    matches: limitedMatches,
    candidates,
    commands: {
      overview: '.lazy-harness/bin/lazy map --overview --complete --format=md',
      concreteMapNodes: concreteNodes.map((node) => `.lazy-harness/bin/lazy map ${shellQuote(node)} --format=md --limit=${args.limit}`),
      missingPrerequisite: 'No concrete map node surfaced; ask a 3-5 option gate or state the missing prerequisite instead of running keyword fallback.',
    },
  }
}

function loadGraphRows(index: RecordIndex): Array<Record<string, unknown>> {
  const graphPath = index.graph.graphPath
  if (!graphPath) return []
  const absolute = path.isAbsolute(graphPath) ? graphPath : path.join(index.source.root, graphPath)
  if (!existsSync(absolute)) return []
  try {
    return readFileSync(absolute, 'utf8').split(/\r?\n/).filter((line) => line.trim()).flatMap((line) => {
      try {
        const parsed = JSON.parse(line)
        return parsed && typeof parsed === 'object' ? [parsed as Record<string, unknown>] : []
      } catch {
        return []
      }
    })
  } catch {
    return []
  }
}

function renderMd(result: RetrievalCoverageAudit): string {
  const lines: string[] = []
  lines.push('# Retrieval Coverage Audit', '')
  lines.push(`- query: \`${result.query}\``)
  lines.push(`- mode: \`${result.mode}\``)
  lines.push(`- coverage: \`${result.coverage.state}\``)
  lines.push(`- gaps: ${result.coverage.gaps.length ? result.coverage.gaps.map((gap) => `\`${gap}\``).join(', ') : '-'}`)
  lines.push(`- counts: features=${result.counts.features}, records=${result.counts.records}, graphRows=${result.counts.graphRows}, recordCandidates=${result.counts.recordCandidates}, sourceCandidates=${result.counts.sourceCandidates}, testCandidates=${result.counts.testCandidates}`)
  lines.push('', '## Notes')
  for (const note of result.notes) lines.push(`- ${note}`)
  lines.push('', '## Matches')
  if (!result.matches.length) lines.push('- -')
  for (const match of result.matches) lines.push(`- ${match.kind}: \`${match.id}\` — ${match.label} (${match.matchedFields.join(', ')})`)
  lines.push('', '## Candidates')
  lines.push(`- Records: ${result.candidates.recordPaths.length ? result.candidates.recordPaths.map((value) => `\`${value}\``).join(', ') : '-'}`)
  lines.push(`- Source files: ${result.candidates.sourceFiles.length ? result.candidates.sourceFiles.map((value) => `\`${value}\``).join(', ') : '-'}`)
  lines.push(`- Test files: ${result.candidates.testFiles.length ? result.candidates.testFiles.map((value) => `\`${value}\``).join(', ') : '-'}`)
  lines.push(`- Graph ids: ${result.candidates.graphIds.length ? result.candidates.graphIds.map((value) => `\`${value}\``).join(', ') : '-'}`)
  lines.push('', '## Commands')
  lines.push(`- Overview: \`${result.commands.overview}\``)
  if (result.commands.concreteMapNodes.length) {
    lines.push('- Concrete map nodes:')
    for (const command of result.commands.concreteMapNodes) lines.push(`  - \`${command}\``)
  } else {
    lines.push('- Concrete map nodes: -')
  }
  lines.push(`- Missing prerequisite: ${result.commands.missingPrerequisite}`)
  return `${lines.join('\n')}\n`
}

function main(): void {
  const args = parseArgs(Bun.argv.slice(2))
  const result = buildAudit(args)
  if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
  else process.stdout.write(renderMd(result))
}

if (import.meta.main) main()
