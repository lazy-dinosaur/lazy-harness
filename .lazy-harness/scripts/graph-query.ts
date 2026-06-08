#!/usr/bin/env bun
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { buildRecordIndex, type RecordEntry, type RecordIndex } from './record-index.ts'

type Format = 'json' | 'md'
type ResultState = 'mapped' | 'partial' | 'gap'
type NodeKind = 'record' | 'source' | 'test' | 'graph-row' | 'implementation' | 'feature'
type LayerName = 'DDD' | 'BDD' | 'SDD' | 'TDD' | 'SSOT'

type GraphRow = {
  id?: string
  relation?: string
  type?: string
  source?: string
  target?: string
  path?: string
  subject?: string
  predicate?: string
  object?: string
  kind?: string
  layer?: string
  [key: string]: unknown
}

type ImplRecord = {
  id?: string
  subject?: string
  predicate?: string
  object?: string
  path?: string
  kind?: string
  layer?: string
  links?: Array<{ rel?: string; target?: string }>
  evidence?: Array<{ type?: string; path?: string; quote?: string }>
  [key: string]: unknown
}

type Seed = {
  kind: 'record' | 'graph-row' | 'implementation' | 'feature'
  id: string
  label: string
  path?: string
  matchedFields: string[]
  provenance: string
}

type SubgraphNode = {
  id: string
  kind: NodeKind
  label: string
  path?: string
  provenance: string[]
}

type SubgraphEdge = {
  source: string
  target: string
  relation: string
  provenance: string[]
}

type Citation = {
  kind: 'record' | 'graph-row' | 'generated-index' | 'source' | 'test'
  id?: string
  path?: string
  provenance: string
}

type GraphQueryResult = {
  mode: 'graph-query.query'
  query: string
  resultState: ResultState
  coverage: { gaps: string[] }
  seeds: Seed[]
  subgraph: { nodes: SubgraphNode[]; edges: SubgraphEdge[] }
  candidates: {
    recordPaths: string[]
    sourceFiles: string[]
    testFiles: string[]
    graphIds: string[]
  }
  citations: Citation[]
  fallback: {
    overview: string
    map: string
    retrievalAudit: string
    grep: string
  }
  notes: string[]
}

type Args = {
  root: string
  command: string
  query: string
  format: Format
  limit: number
  depth: number
  fresh: boolean
}

const FORBIDDEN_COMMANDS = new Set(['path', 'explain'])
const MAX_PROVENANCE_PER_ITEM = 2
const RETRIEVAL_LAYER_BRIDGES: Array<{ layer: LayerName; recordPath: string; reason: string }> = [
  { layer: 'DDD', recordPath: '.lazy-harness/domain/searchable-record-memory.md', reason: 'retrieval-helper-domain-bridge' },
  { layer: 'BDD', recordPath: '.lazy-harness/behavior/llm-owned-record-retrieval.md', reason: 'retrieval-helper-behavior-bridge' },
]

function usage(exitCode = 1): never {
  const msg = `Usage: graph query <term-or-file> [--format=json|md] [--limit=N] [--depth=N] [--fresh] [--root DIR]\n\nPrototype slice 1 supports only: graph query\nUnsupported until separate approval: graph path, graph explain, MCP/daemon.`
  if (exitCode === 0) console.log(msg)
  else console.error(msg)
  process.exit(exitCode)
}

function parseArgs(argv: string[]): Args {
  let root = process.env.LAZY_HOST_ROOT || process.cwd()
  let format: Format = 'md'
  let limit = 8
  let depth = 1
  let fresh = false
  const positional: string[] = []
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    if (arg === '--help' || arg === '-h') usage(0)
    else if (arg === '--fresh') fresh = true
    else if (arg === '--root') {
      const next = argv[++i]
      if (!next) usage()
      root = next
    } else if (arg.startsWith('--root=')) root = arg.slice('--root='.length)
    else if (arg === '--format') {
      const next = argv[++i]
      if (next !== 'json' && next !== 'md') usage()
      format = next
    } else if (arg.startsWith('--format=')) {
      const value = arg.slice('--format='.length)
      if (value !== 'json' && value !== 'md') usage()
      format = value
    } else if (arg === '--limit') {
      const next = argv[++i]
      if (!next) usage()
      limit = parsePositiveInt(next, 'limit')
    } else if (arg.startsWith('--limit=')) limit = parsePositiveInt(arg.slice('--limit='.length), 'limit')
    else if (arg === '--depth') {
      const next = argv[++i]
      if (!next) usage()
      depth = parsePositiveInt(next, 'depth')
    } else if (arg.startsWith('--depth=')) depth = parsePositiveInt(arg.slice('--depth='.length), 'depth')
    else positional.push(arg)
  }
  if (!positional.length) usage()
  const command = positional.shift() || 'query'
  if (FORBIDDEN_COMMANDS.has(command)) {
    console.error(`lazy graph ${command} is unsupported in prototype slice 1. Implement and benchmark lazy graph query first, then open an option gate/ADR before path/explain.`)
    process.exit(2)
  }
  if (command !== 'query') usage()
  const query = positional.join(' ').trim()
  if (!query) usage()
  return { root: path.resolve(root), command, query, format, limit: Math.min(Math.max(limit, 1), 100), depth: Math.min(Math.max(depth, 1), 2), fresh }
}

function parsePositiveInt(raw: string, name: string): number {
  const parsed = Number.parseInt(raw, 10)
  if (!Number.isFinite(parsed) || parsed < 1) {
    console.error(`Invalid --${name}: ${raw}`)
    process.exit(1)
  }
  return parsed
}

function normalize(value: string): string {
  return value.toLowerCase().replace(/[`'"“”‘’]/g, '').replace(/\s+/g, ' ').trim()
}

function queryTokens(query: string): string[] {
  const normalized = normalize(query)
  const raw = normalized.split(/[^a-z0-9가-힣_.:/-]+/iu).filter(Boolean)
  const stop = new Set(['the', 'and', 'or', 'a', 'an', 'to', 'of', 'in', 'for', 'with', 'lazy', 'graph', 'query'])
  return unique(raw.filter((token) => token.length >= 2 && !stop.has(token)))
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => a.localeCompare(b))
}

function uniquePreserve(values: string[]): string[] {
  const seen = new Set<string>()
  const result: string[] = []
  for (const value of values) {
    if (!value || seen.has(value)) continue
    seen.add(value)
    result.push(value)
  }
  return result
}

function compactProvenance(values: string[]): string[] {
  return uniquePreserve(values).slice(0, MAX_PROVENANCE_PER_ITEM)
}

function capped(values: string[], limit: number): string[] {
  return uniquePreserve(values).slice(0, limit)
}

function layerForRecordPath(recordPath: string): LayerName | null {
  if (recordPath.includes('/domain/')) return 'DDD'
  if (recordPath.includes('/behavior/')) return 'BDD'
  if (recordPath.includes('/spec/')) return 'SDD'
  if (recordPath.includes('/tests/')) return 'TDD'
  if (recordPath.includes('/ssot/')) return 'SSOT'
  return null
}

function layerCoverage(recordPaths: string[]): Record<LayerName, boolean> {
  return {
    DDD: recordPaths.some((recordPath) => layerForRecordPath(recordPath) === 'DDD'),
    BDD: recordPaths.some((recordPath) => layerForRecordPath(recordPath) === 'BDD'),
    SDD: recordPaths.some((recordPath) => layerForRecordPath(recordPath) === 'SDD'),
    TDD: recordPaths.some((recordPath) => layerForRecordPath(recordPath) === 'TDD'),
    SSOT: recordPaths.some((recordPath) => layerForRecordPath(recordPath) === 'SSOT'),
  }
}

function capRecordPathsWithBridges(values: string[], bridgeValues: string[], limit: number): string[] {
  const all = uniquePreserve(values)
  if (all.length <= limit) return all
  const bridges = uniquePreserve(bridgeValues).filter((value) => all.includes(value))
  if (!bridges.length) return all.slice(0, limit)
  const direct = all.filter((value) => !bridges.includes(value))
  const reservedBridgeCount = Math.min(bridges.length, Math.max(0, limit - 1))
  const reservedBridges = bridges.slice(0, reservedBridgeCount)
  const directBudget = Math.max(0, limit - reservedBridges.length)
  return uniquePreserve([...direct.slice(0, directBudget), ...reservedBridges]).slice(0, limit)
}

function stringifyField(value: unknown): string {
  if (value == null) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value)) return value.map(stringifyField).join(' ')
  if (typeof value === 'object') return Object.entries(value as Record<string, unknown>).map(([k, v]) => `${k} ${stringifyField(v)}`).join(' ')
  return String(value)
}

function fieldMatches(value: unknown, tokens: string[]): boolean {
  const text = normalize(stringifyField(value))
  if (!text) return false
  return tokens.some((token) => text.includes(token))
}

function matchedFields(fields: Record<string, unknown>, tokens: string[]): string[] {
  return Object.entries(fields)
    .filter(([, value]) => fieldMatches(value, tokens))
    .map(([key]) => key)
    .sort()
}

function relevanceScore(fields: Record<string, unknown>, tokens: string[], phrase: string): number {
  if (!tokens.length) return 0
  const allText = normalize(Object.values(fields).map(stringifyField).join(' '))
  if (!allText) return 0
  const matched = tokens.filter((token) => allText.includes(token))
  const matchedCount = new Set(matched).size
  const phraseHit = phrase.length >= 3 && allText.includes(phrase)
  if (!phraseHit && tokens.length >= 2 && matchedCount < Math.min(2, tokens.length)) return 0
  let score = phraseHit ? 50 : 0
  if (matchedCount === tokens.length) score += 25
  score += matchedCount * 5
  for (const [key, value] of Object.entries(fields)) {
    const text = normalize(stringifyField(value))
    if (!text) continue
    if (phraseHit && text.includes(phrase)) score += key === 'title' || key === 'recordPath' || key === 'id' ? 20 : 10
    const fieldMatched = tokens.filter((token) => text.includes(token)).length
    score += fieldMatched
  }
  return score
}

function byScoreThenLabel<T extends { score: number; label: string }>(a: T, b: T): number {
  if (b.score !== a.score) return b.score - a.score
  return a.label.localeCompare(b.label)
}

function readJsonl(root: string): GraphRow[] {
  const graphPath = path.join(root, '.lazy-harness/knowledge/graph.jsonl')
  if (!existsSync(graphPath)) return []
  const rows: GraphRow[] = []
  const lines = readFileSync(graphPath, 'utf8').split(/\r?\n/)
  for (const line of lines) {
    if (!line.trim()) continue
    try {
      const parsed = JSON.parse(line)
      if (parsed && typeof parsed === 'object') rows.push(parsed)
    } catch {
      // graph hygiene owns invalid row reporting; query ignores invalid rows.
    }
  }
  return rows
}

function readImplementationIndex(root: string): ImplRecord[] {
  const file = path.join(root, '.lazy-harness/generated/implementation-index.json')
  if (!existsSync(file)) return []
  try {
    const parsed = JSON.parse(readFileSync(file, 'utf8'))
    if (Array.isArray(parsed?.records)) return parsed.records.filter((row: unknown) => row && typeof row === 'object')
  } catch {
    return []
  }
  return []
}

function addNode(map: Map<string, SubgraphNode>, node: SubgraphNode): void {
  const existing = map.get(node.id)
  if (!existing) {
    map.set(node.id, { ...node, provenance: compactProvenance(node.provenance) })
    return
  }
  existing.provenance = compactProvenance([...existing.provenance, ...node.provenance])
  if (!existing.path && node.path) existing.path = node.path
}

function addEdge(map: Map<string, SubgraphEdge>, edge: SubgraphEdge): void {
  const key = `${edge.source}\u0000${edge.relation}\u0000${edge.target}`
  const existing = map.get(key)
  if (!existing) {
    map.set(key, { ...edge, provenance: compactProvenance(edge.provenance) })
    return
  }
  existing.provenance = compactProvenance([...existing.provenance, ...edge.provenance])
}

function stableHash(value: string): string {
  let hash = 2166136261
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return (hash >>> 0).toString(36)
}

function shortLabel(value: string): string {
  const withoutFragment = value.split('#')[0]
  const base = path.basename(withoutFragment) || value
  const fragment = value.includes('#') ? `#${value.split('#').slice(1).join('#')}` : ''
  const label = `${base}${fragment}`
  return label.length > 64 ? `${label.slice(0, 61)}...` : label
}

function compactNodeId(prefix: string, value: string): string {
  const label = shortLabel(value).replace(/[^A-Za-z0-9_.#-]+/g, '_').slice(0, 32) || prefix
  return `${prefix}:${label}:${stableHash(value)}`
}

function recordNodeId(recordPath: string): string {
  return compactNodeId('r', recordPath)
}

function pathNodeId(kind: 'source' | 'test' | 'implementation', value: string): string {
  return compactNodeId(kind === 'source' ? 's' : kind === 'test' ? 't' : 'i', value)
}

function graphNodeId(id: string): string {
  return compactNodeId('g', id)
}

function isTestPath(value: string): boolean {
  return /(^|\/)(tests?|__tests__)(\/|$)/i.test(value) || /\.(test|spec)\.[cm]?[jt]sx?$/i.test(value)
}

function looksLikePath(value: string | undefined): value is string {
  if (!value) return false
  if (/\s/.test(value)) return false
  if (/^(\.lazy-harness|\.jcode|src|tests?|docs|fixtures|scripts|bin|package\.json|tsconfig\.json|bun\.lockb?)(\/|$)/.test(value)) return true
  return value.includes('/') && /^[A-Za-z0-9_./#-]+\.[A-Za-z0-9]{1,8}(#.*)?$/.test(value)
}

function buildFallback(query: string) {
  const escaped = query.replace(/'/g, `'"'"'`)
  return {
    overview: `.lazy-harness/bin/lazy map --overview --format=md --limit=20`,
    map: `.lazy-harness/bin/lazy map '${escaped}' --format=md --limit=8`,
    retrievalAudit: `.lazy-harness/bin/lazy retrieval-audit '${escaped}' --format=json --limit=8`,
    grep: `grep -Rli '${escaped}' .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,plans,project,knowledge}/ src tests 2>/dev/null`,
  }
}

function buildGraphQuery(root: string, query: string, limit: number, depth: number, fresh = false): GraphQueryResult {
  void fresh // buildRecordIndex is fresh/rebuild-only and does not write.
  const tokens = queryTokens(query)
  const phrase = normalize(query)
  const index = buildRecordIndex(root)
  const graphRows = readJsonl(root)
  const implementationRecords = readImplementationIndex(root)

  const recordSeeds: Array<{ record: RecordEntry; fields: string[]; score: number; label: string }> = []
  for (const record of index.records) {
    const matchSurface = {
      recordPath: record.recordPath,
      title: record.title,
      layer: record.layer,
      aliases: record.aliases,
      surfaceTerms: record.surfaceTerms,
      appliesWhen: record.digest.appliesWhen,
      must: record.digest.must,
      mustNot: record.digest.mustNot,
      bullets: record.digest.bullets,
      relatedRecords: record.digest.relatedRecords,
      routeHints: record.implementationHints.routeHints,
      componentHints: record.implementationHints.componentHints,
      fileHints: record.implementationHints.fileHints,
      symbolHints: record.implementationHints.symbolHints,
      testHints: record.implementationHints.testHints,
      graphIds: record.graphIds,
    }
    const fields = matchedFields(matchSurface, tokens)
    const score = relevanceScore(matchSurface, tokens, phrase)
    if (score > 0) recordSeeds.push({ record, fields, score, label: `${record.title}:${record.recordPath}` })
  }

  const featureSeeds = index.projectProfile.features
    .map((feature) => {
      const matchSurface = {
        id: feature.id,
        label: feature.label,
        aliases: feature.aliases.map((a) => a.value),
        routes: feature.routes,
        components: feature.components,
        records: feature.records.map((r) => r.path),
        sourceFiles: feature.sourceFiles,
        tests: feature.tests,
      }
      return {
        feature,
        fields: matchedFields(matchSurface, tokens),
        score: relevanceScore(matchSurface, tokens, phrase),
        label: `${feature.label}:${feature.id}`,
      }
    })
    .filter((seed) => seed.score > 0)
    .sort(byScoreThenLabel)

  const graphSeeds = graphRows
    .map((row) => {
      const matchSurface = row as Record<string, unknown>
      const id = row.id ? String(row.id) : JSON.stringify(row).slice(0, 80)
      return { row, fields: matchedFields(matchSurface, tokens), score: relevanceScore(matchSurface, tokens, phrase), label: id }
    })
    .filter((seed) => seed.score > 0)
    .sort(byScoreThenLabel)

  const implSeeds = implementationRecords
    .map((row) => {
      const matchSurface = {
        id: row.id,
        subject: row.subject,
        predicate: row.predicate,
        object: row.object,
        path: row.path,
        kind: row.kind,
        layer: row.layer,
        links: row.links?.map((link) => link.target),
        evidence: row.evidence?.map((item) => `${item.path || ''} ${item.quote || ''}`),
      }
      const id = row.id || row.subject || row.path || JSON.stringify(row).slice(0, 80)
      return { row, fields: matchedFields(matchSurface, tokens), score: relevanceScore(matchSurface, tokens, phrase), label: String(id) }
    })
    .filter((seed) => seed.score > 0)
    .sort(byScoreThenLabel)

  recordSeeds.sort(byScoreThenLabel)

  const recordByPath = new Map(index.records.map((record) => [record.recordPath, record]))
  const graphById = new Map(graphRows.filter((row) => row.id).map((row) => [String(row.id), row]))
  const nodes = new Map<string, SubgraphNode>()
  const edges = new Map<string, SubgraphEdge>()
  const citations: Citation[] = []
  const seeds: Seed[] = []
  const recordPaths: string[] = []
  const sourceFiles: string[] = []
  const testFiles: string[] = []
  const graphIds: string[] = []
  const bridgeRecordPaths: string[] = []

  function cite(citation: Citation): void {
    const key = `${citation.kind}\u0000${citation.id || ''}\u0000${citation.path || ''}\u0000${citation.provenance}`
    if (!citations.some((item) => `${item.kind}\u0000${item.id || ''}\u0000${item.path || ''}\u0000${item.provenance}` === key)) citations.push(citation)
  }

  function includeRecord(record: RecordEntry, provenance: string, remainingDepth: number): void {
    recordPaths.push(record.recordPath)
    addNode(nodes, { id: recordNodeId(record.recordPath), kind: 'record', label: record.title || record.recordPath, path: record.recordPath, provenance: [provenance] })
    cite({ kind: 'record', path: record.recordPath, provenance })
    for (const file of record.implementationHints.fileHints) {
      if (recordByPath.has(file)) {
        recordPaths.push(file)
        addNode(nodes, { id: recordNodeId(file), kind: 'record', label: recordByPath.get(file)?.title || file, path: file, provenance: [`${record.recordPath}:implementationHints.fileHints`] })
        addEdge(edges, { source: recordNodeId(record.recordPath), target: recordNodeId(file), relation: 'hints_record', provenance: [record.recordPath] })
        cite({ kind: 'record', path: file, provenance: record.recordPath })
        continue
      }
      if (!looksLikePath(file)) continue
      if (isTestPath(file)) {
        testFiles.push(file)
        addNode(nodes, { id: pathNodeId('test', file), kind: 'test', label: shortLabel(file), path: file, provenance: [`${record.recordPath}:implementationHints.fileHints`] })
        addEdge(edges, { source: recordNodeId(record.recordPath), target: pathNodeId('test', file), relation: 'hints_test', provenance: [record.recordPath] })
        cite({ kind: 'test', path: file, provenance: record.recordPath })
      } else {
        sourceFiles.push(file)
        addNode(nodes, { id: pathNodeId('source', file), kind: 'source', label: shortLabel(file), path: file, provenance: [`${record.recordPath}:implementationHints.fileHints`] })
        addEdge(edges, { source: recordNodeId(record.recordPath), target: pathNodeId('source', file), relation: 'hints_source', provenance: [record.recordPath] })
        cite({ kind: 'source', path: file, provenance: record.recordPath })
      }
    }
    for (const file of record.implementationHints.testHints) {
      if (recordByPath.has(file)) {
        recordPaths.push(file)
        addNode(nodes, { id: recordNodeId(file), kind: 'record', label: recordByPath.get(file)?.title || file, path: file, provenance: [`${record.recordPath}:implementationHints.testHints`] })
        addEdge(edges, { source: recordNodeId(record.recordPath), target: recordNodeId(file), relation: 'hints_record', provenance: [record.recordPath] })
        cite({ kind: 'record', path: file, provenance: record.recordPath })
        continue
      }
      if (!looksLikePath(file)) continue
      testFiles.push(file)
      addNode(nodes, { id: pathNodeId('test', file), kind: 'test', label: shortLabel(file), path: file, provenance: [`${record.recordPath}:implementationHints.testHints`] })
      addEdge(edges, { source: recordNodeId(record.recordPath), target: pathNodeId('test', file), relation: 'hints_test', provenance: [record.recordPath] })
      cite({ kind: 'test', path: file, provenance: record.recordPath })
    }
    for (const graphId of record.graphIds) {
      graphIds.push(graphId)
      addNode(nodes, { id: graphNodeId(graphId), kind: 'graph-row', label: graphId, provenance: [`${record.recordPath}:graphIds`] })
      addEdge(edges, { source: recordNodeId(record.recordPath), target: graphNodeId(graphId), relation: 'mentions_graph_row', provenance: [record.recordPath] })
      cite({ kind: 'graph-row', id: graphId, provenance: record.recordPath })
      const row = graphById.get(graphId)
      if (row) includeGraphRow(row, `graph-row:${graphId}`, Math.max(remainingDepth - 1, 0))
    }
    if (remainingDepth > 0) {
      for (const related of record.digest.relatedRecords) {
        recordPaths.push(related)
        addNode(nodes, { id: recordNodeId(related), kind: 'record', label: related, path: related, provenance: [`${record.recordPath}:relatedRecords`] })
        addEdge(edges, { source: recordNodeId(record.recordPath), target: recordNodeId(related), relation: 'related_record', provenance: [record.recordPath] })
        const relatedRecord = recordByPath.get(related)
        if (relatedRecord && remainingDepth > 1) includeRecord(relatedRecord, `${record.recordPath}:relatedRecords`, remainingDepth - 1)
      }
    }
  }

  function includeGraphRow(row: GraphRow, provenance: string, remainingDepth: number): void {
    const id = row.id ? String(row.id) : `anonymous:${JSON.stringify(row).slice(0, 80)}`
    graphIds.push(id)
    addNode(nodes, { id: graphNodeId(id), kind: 'graph-row', label: id, path: typeof row.path === 'string' ? row.path : undefined, provenance: [provenance] })
    cite({ kind: 'graph-row', id, path: typeof row.path === 'string' ? row.path : undefined, provenance })
    const relation = String(row.relation || row.predicate || row.type || 'related')
    const endpoints = [row.source, row.subject, row.path, row.target, row.object].filter((value): value is string => typeof value === 'string' && value.length > 0)
    for (const value of endpoints) {
      if (recordByPath.has(value)) {
        recordPaths.push(value)
        addNode(nodes, { id: recordNodeId(value), kind: 'record', label: recordByPath.get(value)?.title || value, path: value, provenance: [id] })
        addEdge(edges, { source: graphNodeId(id), target: recordNodeId(value), relation, provenance: [id] })
        if (remainingDepth > 0) includeRecord(recordByPath.get(value)!, id, remainingDepth - 1)
      } else if (looksLikePath(value)) {
        if (isTestPath(value)) testFiles.push(value)
        else sourceFiles.push(value)
        const kind = isTestPath(value) ? 'test' : 'source'
        addNode(nodes, { id: pathNodeId(kind, value), kind, label: value, path: value, provenance: [id] })
        addEdge(edges, { source: graphNodeId(id), target: pathNodeId(kind, value), relation, provenance: [id] })
        cite({ kind, path: value, provenance: id })
      }
    }
  }

  function includeImplementation(row: ImplRecord, provenance: string): void {
    const id = row.id || row.subject || row.path || JSON.stringify(row).slice(0, 80)
    addNode(nodes, { id: pathNodeId('implementation', id), kind: 'implementation', label: shortLabel(id), path: row.path || row.subject, provenance: [provenance] })
    cite({ kind: 'generated-index', id, path: row.path || row.subject, provenance: '.lazy-harness/generated/implementation-index.json' })
    for (const target of [row.subject, row.object, row.path, ...(row.links || []).map((link) => link.target)].filter((value): value is string => typeof value === 'string' && value.length > 0)) {
      if (recordByPath.has(target)) {
        recordPaths.push(target)
        addNode(nodes, { id: recordNodeId(target), kind: 'record', label: recordByPath.get(target)?.title || target, path: target, provenance: [id] })
        addEdge(edges, { source: pathNodeId('implementation', id), target: recordNodeId(target), relation: row.predicate || 'references', provenance: [id] })
      } else if (looksLikePath(target)) {
        if (isTestPath(target)) testFiles.push(target)
        else sourceFiles.push(target)
        const kind = isTestPath(target) ? 'test' : 'source'
        addNode(nodes, { id: pathNodeId(kind, target), kind, label: target, path: target, provenance: [id] })
        addEdge(edges, { source: pathNodeId('implementation', id), target: pathNodeId(kind, target), relation: row.predicate || 'references', provenance: [id] })
      }
    }
  }

  function includeBridgeRecord(recordPath: string, provenance: string): void {
    const record = recordByPath.get(recordPath)
    if (!record) return
    const anchor = uniquePreserve(recordPaths).find((candidate) => candidate !== recordPath)
    recordPaths.push(recordPath)
    bridgeRecordPaths.push(recordPath)
    addNode(nodes, { id: recordNodeId(recordPath), kind: 'record', label: record.title || recordPath, path: recordPath, provenance: [provenance] })
    if (anchor) addEdge(edges, { source: recordNodeId(anchor), target: recordNodeId(recordPath), relation: 'layer_bridge', provenance: [provenance] })
    cite({ kind: 'record', path: recordPath, provenance })
  }

  function includeLayerBridges(candidateLimit: number): void {
    const current = uniquePreserve(recordPaths)
    if (!current.length) return
    const preview = current.slice(0, candidateLimit)
    const coverage = layerCoverage(preview)
    for (const bridge of RETRIEVAL_LAYER_BRIDGES) {
      if (!coverage[bridge.layer] && recordByPath.has(bridge.recordPath)) includeBridgeRecord(bridge.recordPath, bridge.reason)
    }
    const afterRetrievalBridges = layerCoverage(uniquePreserve(recordPaths).slice(0, candidateLimit))
    if (!afterRetrievalBridges.TDD) {
      const existingTdd = uniquePreserve(recordPaths).find((recordPath) => layerForRecordPath(recordPath) === 'TDD')
      const tddSeed = recordSeeds.find((seed) => layerForRecordPath(seed.record.recordPath) === 'TDD')
      const tddBridge = existingTdd || tddSeed?.record.recordPath
      if (tddBridge) includeBridgeRecord(tddBridge, 'matched-tdd-protection-bridge')
    }
  }

  for (const seed of recordSeeds.slice(0, limit)) {
    seeds.push({ kind: 'record', id: seed.record.recordPath, label: seed.record.title, path: seed.record.recordPath, matchedFields: seed.fields, provenance: 'record-index' })
    includeRecord(seed.record, 'record-index-match', depth)
  }
  for (const seed of featureSeeds.slice(0, limit)) {
    seeds.push({ kind: 'feature', id: seed.feature.id, label: seed.feature.label, matchedFields: seed.fields, provenance: 'feature-navigation' })
    addNode(nodes, { id: `feature:${seed.feature.id}`, kind: 'feature', label: seed.feature.label, provenance: ['feature-navigation'] })
    for (const ref of seed.feature.records) {
      recordPaths.push(ref.path)
      addNode(nodes, { id: recordNodeId(ref.path), kind: 'record', label: ref.path, path: ref.path, provenance: [`feature:${seed.feature.id}`] })
      addEdge(edges, { source: `feature:${seed.feature.id}`, target: recordNodeId(ref.path), relation: 'feature_record', provenance: [seed.feature.id] })
      const record = recordByPath.get(ref.path)
      if (record) includeRecord(record, `feature:${seed.feature.id}`, Math.max(depth - 1, 0))
    }
    sourceFiles.push(...seed.feature.sourceFiles)
    testFiles.push(...seed.feature.tests)
  }
  for (const seed of graphSeeds.slice(0, limit)) {
    const id = seed.row.id ? String(seed.row.id) : `graph-seed:${JSON.stringify(seed.row).slice(0, 80)}`
    seeds.push({ kind: 'graph-row', id, label: id, path: typeof seed.row.path === 'string' ? seed.row.path : undefined, matchedFields: seed.fields, provenance: 'graph.jsonl' })
    includeGraphRow(seed.row, 'graph-match', depth)
  }
  for (const seed of implSeeds.slice(0, limit)) {
    const id = seed.row.id || seed.row.subject || seed.row.path || `implementation:${seeds.length}`
    seeds.push({ kind: 'implementation', id: String(id), label: String(id), path: seed.row.path || seed.row.subject, matchedFields: seed.fields, provenance: 'implementation-index' })
    includeImplementation(seed.row, 'implementation-index-match')
  }

  includeLayerBridges(limit)

  const candidateRecordPaths = capRecordPathsWithBridges(recordPaths, bridgeRecordPaths, limit)
  const candidateSourceFiles = capped(sourceFiles, limit)
  const candidateTestFiles = capped(testFiles, limit)
  const candidateGraphIds = capped(graphIds, limit)
  const gaps: string[] = []
  if (!seeds.length) gaps.push('no-seeds')
  if (!candidateRecordPaths.length) gaps.push('no-record-candidates')
  if (!candidateSourceFiles.length) gaps.push('no-source-candidates')
  if (!candidateTestFiles.length) gaps.push('no-test-candidates')
  if (!candidateGraphIds.length) gaps.push('no-graph-candidates')
  const resultState: ResultState = !seeds.length ? 'gap' : gaps.length ? 'partial' : 'mapped'

  return {
    mode: 'graph-query.query',
    query,
    resultState,
    coverage: { gaps },
    seeds: seeds.sort((a, b) => `${a.kind}:${a.id}`.localeCompare(`${b.kind}:${b.id}`)).slice(0, limit),
    subgraph: {
      nodes: Array.from(nodes.values()).sort((a, b) => a.id.localeCompare(b.id)).slice(0, limit),
      edges: Array.from(edges.values()).sort((a, b) => `${a.source}:${a.relation}:${a.target}`.localeCompare(`${b.source}:${b.relation}:${b.target}`)).slice(0, limit),
    },
    candidates: {
      recordPaths: candidateRecordPaths,
      sourceFiles: candidateSourceFiles,
      testFiles: candidateTestFiles,
      graphIds: candidateGraphIds,
    },
    citations: citations.sort((a, b) => `${a.kind}:${a.id || ''}:${a.path || ''}`.localeCompare(`${b.kind}:${b.id || ''}:${b.path || ''}`)).slice(0, limit),
    fallback: buildFallback(query),
    notes: [
      'cue-only: graph query output is navigation context, not proof that evidence was read',
      'generated/non-canonical: read real records/source/tests before relying on any candidate',
      'prototype slice 1: only lazy graph query is supported; path/explain/lifecycle policy changes are out of scope',
    ],
  }
}

function renderMarkdown(result: GraphQueryResult): string {
  const lines: string[] = []
  lines.push('# Graph query')
  lines.push('')
  lines.push(`- mode: \`${result.mode}\``)
  lines.push(`- query: \`${result.query}\``)
  lines.push(`- resultState: \`${result.resultState}\``)
  if (result.coverage.gaps.length) lines.push(`- gaps: ${result.coverage.gaps.map((gap) => `\`${gap}\``).join(', ')}`)
  lines.push('- caveat: cue-only; read real records/source/tests before relying on candidates.')
  lines.push('')
  lines.push('## Seeds')
  if (!result.seeds.length) lines.push('- -')
  for (const seed of result.seeds) {
    lines.push(`- ${seed.kind}: ${seed.path || seed.id} — ${seed.label}`)
    if (seed.matchedFields.length) lines.push(`  - matched: ${seed.matchedFields.join(', ')}`)
  }
  lines.push('', '## Candidates')
  lines.push('- Records:')
  if (!result.candidates.recordPaths.length) lines.push('  - -')
  for (const value of result.candidates.recordPaths) lines.push(`  - \`${value}\``)
  lines.push('- Source files:')
  if (!result.candidates.sourceFiles.length) lines.push('  - -')
  for (const value of result.candidates.sourceFiles) lines.push(`  - \`${value}\``)
  lines.push('- Test files:')
  if (!result.candidates.testFiles.length) lines.push('  - -')
  for (const value of result.candidates.testFiles) lines.push(`  - \`${value}\``)
  lines.push('- Graph ids:')
  if (!result.candidates.graphIds.length) lines.push('  - -')
  for (const value of result.candidates.graphIds) lines.push(`  - \`${value}\``)
  lines.push('', '## Subgraph')
  lines.push(`- nodes: ${result.subgraph.nodes.length}`)
  for (const node of result.subgraph.nodes.slice(0, 12)) lines.push(`  - ${node.kind}: ${node.path || node.id}`)
  lines.push(`- edges: ${result.subgraph.edges.length}`)
  for (const edge of result.subgraph.edges.slice(0, 12)) lines.push(`  - ${edge.source} --${edge.relation}--> ${edge.target}`)
  lines.push('', '## Fallback')
  lines.push(`- overview: \`${result.fallback.overview}\``)
  lines.push(`- map: \`${result.fallback.map}\``)
  lines.push(`- retrieval-audit: \`${result.fallback.retrievalAudit}\``)
  lines.push(`- grep: \`${result.fallback.grep}\``)
  lines.push('', '## Notes')
  for (const note of result.notes) lines.push(`- ${note}`)
  return `${lines.join('\n')}\n`
}

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  const result = buildGraphQuery(args.root, args.query, args.limit, args.depth, args.fresh)
  if (args.format === 'json') process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
  else process.stdout.write(renderMarkdown(result))
}

if (import.meta.main) main()

export { buildGraphQuery, type GraphQueryResult }
