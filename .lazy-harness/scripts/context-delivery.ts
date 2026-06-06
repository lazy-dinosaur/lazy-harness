#!/usr/bin/env bun
/**
 * context-delivery.ts — explicit candidate retrieval helper.
 *
 * CLI boundary: this tool lists deterministic candidate hits from record-authored
 * fields and generated indexes. It does not decide intent, importance, risk,
 * required reads, gates, record-write need, or next actions. The LLM/searcher
 * owns those judgments after reading root-bound evidence.
 */
import { existsSync, readFileSync } from 'node:fs'
import * as path from 'node:path'
import { buildContextIndex, type ContextIndex, type RecordEntry, type FeatureEntry } from './context-index.ts'

type Format = 'json' | 'md'
type QuerySource = 'user-phrase' | 'llm-supplied' | 'record-link' | 'fallback'
type CandidateKind = 'record' | 'project-profile' | 'graph-edge' | 'source-file' | 'test' | 'schema' | 'generated-index'

interface Args {
  root: string
  query: string
  format: Format
  limit: number
  indexPath: string
  handoffPrompt: boolean
}

interface QueryItem {
  query: string
  source: QuerySource
}

interface CandidateHit {
  path: string
  kind: CandidateKind
  matchedQueries: string[]
  matchedFields: string[]
  layer?: string
  title?: string
  symbols?: string[]
}

interface ContextCandidatePacket {
  schemaVersion: '2.0'
  generatedAt: string
  mode: 'candidate-retrieval'
  queries: QueryItem[]
  candidateHits: CandidateHit[]
  fallbackSearches: string[]
  notes: string[]
}

function usage(): never {
  console.error(`Usage: context-delivery --message "..." [options]

Options:
  --root DIR              Host root (default: LAZY_HOST_ROOT or cwd)
  --message TEXT          Literal user/LLM query to match against record-authored fields
  --query TEXT            Alias for --message
  --format json|md        Output format (default json)
  --limit N               Max candidate hits to return in source order (default 20)
  --index PATH            Optional generated context-index path
  --handoff-prompt        Render a searcher handoff prompt that returns candidate hits only
  --help                  Show this help

Examples:
  bun .lazy-harness/scripts/context-delivery.ts --message "feature surface" --format md
  .lazy-harness/bin/lazy context-delivery --query="기능패널" --format=json
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

function parseArgs(argv: string[]): Args {
  const root = process.env.LAZY_HOST_ROOT || process.cwd()
  const args: Args = {
    root,
    query: '',
    format: 'json',
    limit: 20,
    indexPath: '',
    handoffPrompt: false,
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    let parsed = valueFor(argv, i, '--root')
    if (parsed.value !== null) { args.root = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--message')
    if (parsed.value !== null) { args.query = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--query')
    if (parsed.value !== null) { args.query = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--format')
    if (parsed.value !== null) {
      if (parsed.value !== 'json' && parsed.value !== 'md' && parsed.value !== 'markdown') usage()
      args.format = parsed.value === 'markdown' ? 'md' : parsed.value
      i += parsed.consumed
      continue
    }
    parsed = valueFor(argv, i, '--limit')
    if (parsed.value !== null) {
      const n = Number(parsed.value)
      if (!Number.isFinite(n) || n < 1) usage()
      args.limit = Math.floor(n)
      i += parsed.consumed
      continue
    }
    parsed = valueFor(argv, i, '--index')
    if (parsed.value !== null) { args.indexPath = parsed.value; i += parsed.consumed; continue }
    if (arg === '--handoff-prompt') args.handoffPrompt = true
    else if (arg === '--journal') {
      console.error('journal mode was removed: CLI tools may return candidate evidence, but must not create required-read debt.')
      process.exit(2)
    } else if (arg === '--help' || arg === '-h') usage()
    else usage()
  }
  if (!args.query.trim()) usage()
  args.root = path.resolve(args.root)
  if (!args.indexPath) args.indexPath = path.join(args.root, '.lazy-harness', 'generated', 'context-index.json')
  else args.indexPath = path.resolve(args.indexPath)
  return args
}

function normalize(value: string): string {
  return value.toLowerCase().replace(/\s+/g, ' ').trim()
}

function queryTerms(query: string): string[] {
  const full = query.trim()
  const parts = full.split(/[\s,|/]+/).map((v) => v.trim()).filter((v) => v.length >= 2)
  return Array.from(new Set([full, ...parts].filter(Boolean)))
}

function quoteForRg(query: string): string {
  return query.replace(/\\/g, '\\\\').replace(/"/g, '\\"')
}

function fieldsForRecord(record: RecordEntry): Array<[string, string]> {
  const hints = record.implementationHints
  const rows: Array<[string, string]> = [
    ['recordPath', record.recordPath],
    ['title', record.title],
    ['layer', record.layer],
    ['status', record.status],
    ...record.aliases.map((v) => ['alias', v] as [string, string]),
    ...record.surfaceTerms.map((v) => ['surfaceTerm', v] as [string, string]),
    ...record.digest.relatedRecords.map((v) => ['relatedRecord', v] as [string, string]),
    ...hints.routeHints.map((v) => ['routeHint', v] as [string, string]),
    ...hints.componentHints.map((v) => ['componentHint', v] as [string, string]),
    ...hints.fileHints.map((v) => ['fileHint', v] as [string, string]),
    ...hints.symbolHints.map((v) => ['symbolHint', v] as [string, string]),
    ...hints.testHints.map((v) => ['testHint', v] as [string, string]),
  ]
  return rows
}

function matched(fields: Array<[string, string]>, terms: string[]): { matchedQueries: string[]; matchedFields: string[] } {
  const matchedQueries = new Set<string>()
  const matchedFields = new Set<string>()
  for (const [field, value] of fields) {
    const hay = normalize(value)
    if (!hay) continue
    for (const term of terms) {
      const needle = normalize(term)
      if (!needle) continue
      if (hay.includes(needle) || needle.includes(hay)) {
        matchedQueries.add(term)
        matchedFields.add(field)
      }
    }
  }
  return { matchedQueries: Array.from(matchedQueries), matchedFields: Array.from(matchedFields).sort() }
}

function addHit(target: Map<string, CandidateHit>, hit: CandidateHit): void {
  const key = `${hit.kind}:${hit.path}`
  const existing = target.get(key)
  if (!existing) {
    target.set(key, {
      ...hit,
      matchedQueries: Array.from(new Set(hit.matchedQueries)),
      matchedFields: Array.from(new Set(hit.matchedFields)).sort(),
      symbols: hit.symbols ? Array.from(new Set(hit.symbols)).sort() : undefined,
    })
    return
  }
  existing.matchedQueries = Array.from(new Set([...existing.matchedQueries, ...hit.matchedQueries]))
  existing.matchedFields = Array.from(new Set([...existing.matchedFields, ...hit.matchedFields])).sort()
  if (hit.symbols) existing.symbols = Array.from(new Set([...(existing.symbols || []), ...hit.symbols])).sort()
}

function kindForHintPath(value: string): CandidateKind {
  if (/\btests?\//.test(value) || /\.test\./.test(value) || /\.spec\./.test(value)) return 'test'
  if (/\.lazy-harness\/.+schema/.test(value) || /\.schema\.json$/.test(value)) return 'schema'
  if (/^\.lazy-harness\//.test(value)) return 'record'
  return 'source-file'
}

function collectRecordHits(index: ContextIndex, terms: string[]): CandidateHit[] {
  const hits = new Map<string, CandidateHit>()
  for (const record of index.records) {
    const m = matched(fieldsForRecord(record), terms)
    if (!m.matchedQueries.length) continue
    addHit(hits, {
      path: record.recordPath,
      kind: 'record',
      title: record.title,
      layer: record.layer,
      matchedQueries: m.matchedQueries,
      matchedFields: m.matchedFields,
      symbols: record.implementationHints.symbolHints,
    })
    for (const file of record.implementationHints.fileHints) {
      addHit(hits, { path: file, kind: kindForHintPath(file), matchedQueries: m.matchedQueries, matchedFields: ['record.fileHint'] })
    }
    for (const test of record.implementationHints.testHints) {
      addHit(hits, { path: test, kind: 'test', matchedQueries: m.matchedQueries, matchedFields: ['record.testHint'] })
    }
    for (const hint of record.graphHints) {
      const target = hint.path || hint.target || hint.source
      if (target) addHit(hits, { path: target, kind: target.startsWith('.lazy-harness/') ? 'record' : 'graph-edge', matchedQueries: m.matchedQueries, matchedFields: ['record.graphHint'] })
    }
  }
  return Array.from(hits.values())
}

function fieldsForFeature(feature: FeatureEntry): Array<[string, string]> {
  return [
    ['feature.id', feature.id],
    ['feature.label', feature.label],
    ...feature.aliases.map((a) => ['feature.alias', a.value] as [string, string]),
    ...feature.routes.map((v) => ['feature.route', v] as [string, string]),
    ...feature.components.map((v) => ['feature.component', v] as [string, string]),
  ]
}

function collectFeatureHits(index: ContextIndex, terms: string[]): CandidateHit[] {
  const hits = new Map<string, CandidateHit>()
  for (const feature of index.projectProfile.features) {
    const m = matched(fieldsForFeature(feature), terms)
    if (!m.matchedQueries.length) continue
    const nav = index.projectProfile.featureNavigationPath
    if (nav) addHit(hits, { path: nav, kind: 'project-profile', matchedQueries: m.matchedQueries, matchedFields: m.matchedFields, title: feature.label })
    for (const ref of feature.records) addHit(hits, { path: ref.path, kind: 'record', layer: ref.layer, matchedQueries: m.matchedQueries, matchedFields: ['feature.record'] })
    for (const file of feature.sourceFiles) addHit(hits, { path: file, kind: 'source-file', matchedQueries: m.matchedQueries, matchedFields: ['feature.sourceFile'] })
    for (const test of feature.tests) addHit(hits, { path: test, kind: 'test', matchedQueries: m.matchedQueries, matchedFields: ['feature.test'] })
  }
  return Array.from(hits.values())
}

function loadIndex(args: Args): { index: ContextIndex; source: string } {
  if (existsSync(args.indexPath)) {
    return { index: JSON.parse(readFileSync(args.indexPath, 'utf8')) as ContextIndex, source: 'generated-index' }
  }
  return { index: buildContextIndex(args.root), source: 'source-scan' }
}

function buildPacket(args: Args): ContextCandidatePacket {
  const terms = queryTerms(args.query)
  const { index, source } = loadIndex(args)
  const hits = new Map<string, CandidateHit>()
  for (const hit of collectRecordHits(index, terms)) addHit(hits, hit)
  for (const hit of collectFeatureHits(index, terms)) addHit(hits, hit)
  const allHits = Array.from(hits.values())
  const limited = allHits.slice(0, args.limit)
  const notes = [
    `contextIndexSource=${source}`,
    'candidate-only: CLI does not decide intent, importance, required reads, gates, record-write need, or next action',
  ]
  if (allHits.length > limited.length) notes.push(`truncated=${allHits.length - limited.length}`)
  return {
    schemaVersion: '2.0',
    generatedAt: new Date().toISOString(),
    mode: 'candidate-retrieval',
    queries: terms.map((query) => ({ query, source: 'user-phrase' as QuerySource })),
    candidateHits: limited,
    fallbackSearches: [`rg -n "${quoteForRg(args.query)}" .lazy-harness src tests`],
    notes,
  }
}

function renderMarkdown(packet: ContextCandidatePacket): string {
  const lines: string[] = []
  lines.push('# Context candidate retrieval')
  lines.push('')
  lines.push('This is candidate evidence only. The LLM/searcher decides importance, required reads, gates, record-write need, and next action after reading evidence.')
  lines.push('')
  lines.push('## Queries')
  for (const q of packet.queries) lines.push(`- ${q.query} (${q.source})`)
  lines.push('')
  lines.push('## Candidate hits')
  if (!packet.candidateHits.length) lines.push('- none')
  for (const hit of packet.candidateHits) {
    const fields = hit.matchedFields.join(', ')
    const queries = hit.matchedQueries.join(', ')
    lines.push(`- ${hit.kind}: \`${hit.path}\` [fields: ${fields}; queries: ${queries}]`)
  }
  lines.push('')
  lines.push('## Fallback searches')
  for (const search of packet.fallbackSearches) lines.push(`- \`${search}\``)
  lines.push('')
  lines.push('## Notes')
  for (const note of packet.notes) lines.push(`- ${note}`)
  return lines.join('\n') + '\n'
}

function renderHandoff(args: Args, seed: ContextCandidatePacket): string {
  const safeRoot = args.root
  return `# Context candidate search handoff

You are a read-only searcher. Use root-bound search/read tools in this host only.

Host root: ${safeRoot}
Current query: ${args.query}

Return one JSON object matching \`.lazy-harness/schemas/context-delivery-packet.schema.json\`.

Important boundary:
- Do not mutate files.
- Do not decide final intent, importance, required reads, gates, record-write need, risk, or next action.
- Return candidateHits with paths, matchedFields, and matchedQueries only.
- The main LLM will read evidence and decide what matters.

Seed packet:

\`\`\`json
${JSON.stringify(seed, null, 2)}
\`\`\`
`
}

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  const packet = buildPacket(args)
  if (args.handoffPrompt) {
    process.stdout.write(renderHandoff(args, packet))
    return
  }
  if (args.format === 'json') process.stdout.write(JSON.stringify(packet, null, 2) + '\n')
  else process.stdout.write(renderMarkdown(packet))
}

main()
