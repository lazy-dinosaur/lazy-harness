#!/usr/bin/env bun
/**
 * Record Map
 *
 * Read-only overview/drill-down helper for searchable record memory.
 * It uses record-authored metadata, feature navigation, and graph links as
 * navigation cues only. It must not decide intent, confidence, required reads,
 * risk, gates, or next actions.
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'
import { buildRecordIndex, type FeatureEntry, type RecordEntry, type RecordIndex } from './record-index.ts'

type OutputFormat = 'json' | 'md'

interface Args {
  root: string
  query: string
  format: OutputFormat
  limit: number
  overview: boolean
  fresh: boolean
}

interface CacheInfo {
  path: string
  used: boolean
  reason: string
}

interface MatchDetail {
  field: string
  value: string
}

interface FeatureMatch {
  id: string
  label: string
  status: string
  matchCount: number
  matched: MatchDetail[]
  aliases: string[]
  routes: string[]
  components: string[]
  records: string[]
  sourceFiles: string[]
  testFiles: string[]
}

interface RecordMatch {
  recordPath: string
  title: string
  layer: string
  status: string
  matchCount: number
  matched: MatchDetail[]
  aliases: string[]
  surfaceTerms: string[]
  featureIds: string[]
  sourceFiles: string[]
  testFiles: string[]
  symbols: string[]
  routes: string[]
  components: string[]
  graphIds: string[]
  relatedRecords: string[]
}

interface GraphMatch {
  id: string
  relation?: string
  kind?: string
  path?: string
  source?: string
  target?: string
  matchCount: number
  matched: MatchDetail[]
}

interface Drilldown {
  recordPaths: string[]
  sourceFiles: string[]
  testFiles: string[]
  graphIds: string[]
}

interface RecordMapResult {
  schemaVersion: '1.0'
  mode: 'record-map.inspect'
  query: string
  root: string
  source: {
    method: 'record-map-v1'
    tool: '.lazy-harness/scripts/record-map.ts'
    recordIndexMethod: 'record-index-v1'
    recordIndexCache: CacheInfo
  }
  counts: {
    features: number
    records: number
    graphRows: number
  }
  notes: string[]
  features: FeatureMatch[]
  records: RecordMatch[]
  graphRows: GraphMatch[]
  drilldown: Drilldown
}

interface OverviewLayer {
  layer: string
  count: number
  records: Array<{ recordPath: string; title: string; status: string }>
}

interface RecordMapOverview {
  schemaVersion: '1.0'
  mode: 'record-map.overview'
  root: string
  source: {
    method: 'record-map-v1'
    tool: '.lazy-harness/scripts/record-map.ts'
    recordIndexMethod: 'record-index-v1'
    recordIndexCache: CacheInfo
  }
  notes: string[]
  inventory: {
    totalRecords: number
    totalFeatures: number
    totalGraphRows: number
    layers: OverviewLayer[]
    generatedIndexes: Record<string, boolean>
  }
  features: Array<{
    id: string
    label: string
    status: string
    aliases: string[]
    routes: string[]
    components: string[]
    records: string[]
  }>
  graph: {
    relations: Array<{ relation: string; count: number }>
    sampleRows: GraphMatch[]
  }
  drilldown: Drilldown
}

interface GraphRow {
  id?: string
  relation?: string
  kind?: string
  type?: string
  path?: string
  source?: string
  target?: string
  [key: string]: unknown
}

const LAYER_DIRS = [
  '.lazy-harness/domain/',
  '.lazy-harness/spec/',
  '.lazy-harness/behavior/',
  '.lazy-harness/tests/',
  '.lazy-harness/decisions/',
  '.lazy-harness/ssot/',
  '.lazy-harness/planning/',
  '.lazy-harness/plans/',
  '.lazy-harness/project/',
]

const RECORD_INDEX_INPUTS = [
  '.lazy-harness/domain',
  '.lazy-harness/spec',
  '.lazy-harness/behavior',
  '.lazy-harness/tests',
  '.lazy-harness/decisions',
  '.lazy-harness/ssot',
  '.lazy-harness/planning',
  '.lazy-harness/project/feature-navigation.xml',
  '.lazy-harness/knowledge/graph.jsonl',
]

function usage(exitCode = 2): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Record Map\n\nUsage:\n  .lazy-harness/bin/lazy map --overview [--format=json|md] [--limit=N] [--fresh]\n  .lazy-harness/bin/lazy map <feature-id|record-path|graph-id|source-path> [--format=json|md] [--limit=N] [--fresh]\n  bun .lazy-harness/scripts/record-map.ts --root . --overview --format=md\n\nRead-only project map traversal helper. Start with --overview, let the LLM choose a concrete node/key from the map, then drill into that node. This is not a free-form search box and it does not decide intent, confidence, required reads, risk, gates, or next actions.`)
  process.exit(exitCode)
}

function parseArgs(argv: string[]): Args {
  const args: Args = {
    root: process.env.LAZY_HOST_ROOT || process.cwd(),
    query: '',
    format: 'md',
    limit: 8,
    overview: false,
    fresh: false,
  }
  const queryParts: string[] = []
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = argv[i + 1]
    if (arg === '--help' || arg === '-h') usage(0)
    else if (arg === '--overview') args.overview = true
    else if (arg === '--fresh' || arg === '--no-cache') args.fresh = true
    else if ((arg === '--root' || arg === '--host') && next) { args.root = next; i += 1 }
    else if (arg.startsWith('--root=')) args.root = arg.slice('--root='.length)
    else if (arg.startsWith('--host=')) args.root = arg.slice('--host='.length)
    else if ((arg === '--format' || arg === '-f') && next) {
      args.format = normalizeFormat(next)
      i += 1
    } else if (arg.startsWith('--format=')) args.format = normalizeFormat(arg.slice('--format='.length))
    else if ((arg === '--limit' || arg === '-n') && next) {
      args.limit = normalizeLimit(next)
      i += 1
    } else if (arg.startsWith('--limit=')) args.limit = normalizeLimit(arg.slice('--limit='.length))
    else if (arg.startsWith('-')) throw new Error(`Unknown argument: ${arg}`)
    else queryParts.push(arg)
  }
  args.query = queryParts.join(' ').trim()
  if (!args.query && !args.overview) usage()
  if (args.query) validateTraversalKey(args.query)
  args.root = path.resolve(args.root)
  return args
}

function normalizeFormat(value: string): OutputFormat {
  if (value === 'markdown') return 'md'
  if (value === 'json' || value === 'md') return value
  throw new Error(`Unsupported --format: ${value}`)
}

function normalizeLimit(value: string): number {
  const n = Number(value)
  if (!Number.isInteger(n) || n < 1 || n > 100) throw new Error(`Unsupported --limit: ${value}`)
  return n
}

function validateTraversalKey(value: string): void {
  const text = value.trim()
  if (/\s/.test(text)) {
    throw new Error('lazy map expects a concrete map node/key, not free-form search text. Start with `lazy map --overview`, then pass a feature id, record path, graph id, source path, or test path copied from the map.')
  }
}

function newestMtimeMs(targetPath: string): number {
  if (!existsSync(targetPath)) return 0
  let stat
  try { stat = statSync(targetPath) } catch { return 0 }
  if (!stat.isDirectory()) return stat.mtimeMs
  let newest = stat.mtimeMs
  let entries
  try { entries = readdirSync(targetPath, { withFileTypes: true }) } catch { return newest }
  for (const entry of entries) {
    const full = path.join(targetPath, entry.name)
    if (entry.isDirectory()) newest = Math.max(newest, newestMtimeMs(full))
    else if (entry.isFile()) {
      try { newest = Math.max(newest, statSync(full).mtimeMs) } catch { /* ignore unreadable files */ }
    }
  }
  return newest
}

function newestCanonicalInputMtimeMs(root: string): number {
  return Math.max(0, ...RECORD_INDEX_INPUTS.map((input) => newestMtimeMs(path.join(root, input))))
}

function validateRecordIndex(value: unknown): value is RecordIndex {
  if (!value || typeof value !== 'object') return false
  const index = value as Partial<RecordIndex>
  return index.schemaVersion === '1.0'
    && index.source?.method === 'record-index-v1'
    && Array.isArray(index.records)
    && Array.isArray(index.projectProfile?.features)
}

function loadRecordIndex(root: string, fresh = false): { index: RecordIndex; cache: CacheInfo } {
  const cachePath = path.join(root, '.lazy-harness', 'generated', 'record-index.json')
  const relCachePath = '.lazy-harness/generated/record-index.json'
  if (fresh) {
    return { index: buildRecordIndex(root), cache: { path: relCachePath, used: false, reason: '--fresh requested source rebuild' } }
  }
  if (!existsSync(cachePath)) {
    return { index: buildRecordIndex(root), cache: { path: relCachePath, used: false, reason: 'cache missing; source rebuilt' } }
  }
  const cacheMtime = newestMtimeMs(cachePath)
  const newestInputMtime = newestCanonicalInputMtimeMs(root)
  if (cacheMtime < newestInputMtime) {
    return { index: buildRecordIndex(root), cache: { path: relCachePath, used: false, reason: 'cache older than canonical inputs; source rebuilt' } }
  }
  try {
    const parsed = JSON.parse(readFileSync(cachePath, 'utf8'))
    if (!validateRecordIndex(parsed)) {
      return { index: buildRecordIndex(root), cache: { path: relCachePath, used: false, reason: 'cache schema invalid; source rebuilt' } }
    }
    return { index: parsed, cache: { path: relCachePath, used: true, reason: 'fresh generated cache' } }
  } catch {
    return { index: buildRecordIndex(root), cache: { path: relCachePath, used: false, reason: 'cache unreadable; source rebuilt' } }
  }
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

function queryNeedles(query: string): string[] {
  const base = normalized(query)
  const parts = base.split(/\s+/).filter((part) => part.length >= 2)
  return uniq([base, compact(query), ...parts.map(compact), ...parts])
}

function queryParts(query: string): string[] {
  return uniq(normalized(query).split(/\s+/).filter((part) => part.length >= 2).map(compact))
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
  if (parts.length > 1) {
    return parts.every((part) => compactHay.includes(compact(part)))
  }
  const needles = queryNeedles(query)
  return needles.some((needle) => needle && (hay.includes(needle) || compactHay.includes(compact(needle))))
}

function sameTraversalKey(query: string, value: string): boolean {
  const q = query.replace(/^\.\//, '').trim()
  const v = value.replace(/^\.\//, '').trim()
  return Boolean(q && v && q === v)
}

function addExactMatches(out: MatchDetail[], query: string, field: string, values: string[] | string | undefined): void {
  const list = Array.isArray(values) ? values : values ? [values] : []
  for (const value of list) {
    if (sameTraversalKey(query, value)) out.push({ field, value })
  }
}


function addMatches(out: MatchDetail[], query: string, field: string, values: string[] | string | undefined): void {
  const list = Array.isArray(values) ? values : values ? [values] : []
  for (const value of list) {
    if (matches(query, value)) out.push({ field, value })
  }
}

function addAggregateFallbackMatches(out: MatchDetail[], query: string, field: string, values: Array<string | undefined | null>): void {
  if (out.length) return
  const parts = queryParts(query)
  if (parts.length < 3) return
  const hay = compact(values.filter((value): value is string => Boolean(value && value.trim())).join(' '))
  if (!hay) return
  const matchedParts = parts.filter((part) => hay.includes(part))
  const minimum = Math.max(2, Math.ceil(parts.length * 0.5))
  if (matchedParts.length < minimum) return
  for (const part of matchedParts) out.push({ field, value: `token:${part}` })
}

function rowStrings(value: unknown): string[] {
  if (typeof value === 'string') return [value]
  if (Array.isArray(value)) return value.flatMap(rowStrings)
  if (value && typeof value === 'object') return Object.values(value as Record<string, unknown>).flatMap(rowStrings)
  return []
}

function isPathLike(value: string): boolean {
  if (/\s/.test(value)) return false
  return value.startsWith('.lazy-harness/') || value.startsWith('src/') || value.startsWith('app/') || value.startsWith('tests/') || value.includes('/') || /\.[A-Za-z0-9]+(#.+)?$/.test(value)
}

function looksLikeRecordPath(value: string): boolean {
  return LAYER_DIRS.some((dir) => value.startsWith(dir)) && /\.(md|xml)$/.test(value)
}

function looksLikeTestPath(value: string): boolean {
  return /(^|\/)(tests?|__tests__)(\/|$)/.test(value) || /\.(test|spec)\.[A-Za-z0-9]+$/.test(value)
}

function readablePathExists(root: string | undefined, value: string): boolean {
  if (!root) return true
  const withoutAnchor = value.split('#', 1)[0]
  if (!withoutAnchor || withoutAnchor.includes('*') || withoutAnchor.startsWith('~')) return false
  const full = path.isAbsolute(withoutAnchor) ? withoutAnchor : path.join(root, withoutAnchor)
  return existsSync(full)
}

function addPath(value: string, target: Drilldown, root?: string): void {
  const cleaned = value.replace(/`/g, '').trim()
  if (!cleaned || !isPathLike(cleaned)) return
  if (looksLikeRecordPath(cleaned)) target.recordPaths.push(cleaned)
  else if (looksLikeTestPath(cleaned)) {
    if (readablePathExists(root, cleaned)) target.testFiles.push(cleaned)
  } else if (readablePathExists(root, cleaned)) target.sourceFiles.push(cleaned)
}

function featureMatch(query: string, feature: FeatureEntry): FeatureMatch | null {
  const matched: MatchDetail[] = []
  const aliases = feature.aliases.map((alias) => alias.value)
  addExactMatches(matched, query, 'feature.idExact', feature.id)
  addExactMatches(matched, query, 'feature.recordsExact', feature.records.map((record) => record.path))
  addExactMatches(matched, query, 'feature.sourceFilesExact', feature.sourceFiles)
  addExactMatches(matched, query, 'feature.testsExact', feature.tests)
  addMatches(matched, query, 'feature.id', feature.id)
  addMatches(matched, query, 'feature.label', feature.label)
  addMatches(matched, query, 'feature.aliases', aliases)
  addMatches(matched, query, 'feature.routes', feature.routes)
  addMatches(matched, query, 'feature.components', feature.components)
  addMatches(matched, query, 'feature.records', feature.records.map((record) => record.path))
  addMatches(matched, query, 'feature.sourceFiles', feature.sourceFiles)
  addMatches(matched, query, 'feature.tests', feature.tests)
  addAggregateFallbackMatches(matched, query, 'feature.aggregateTokenFallback', [
    feature.id,
    feature.label,
    feature.status,
    ...aliases,
    ...feature.routes,
    ...feature.components,
    ...feature.records.map((record) => record.path),
    ...feature.sourceFiles,
    ...feature.tests,
  ])
  if (!matched.length) return null
  return {
    id: feature.id,
    label: feature.label,
    status: feature.status,
    matchCount: matched.length,
    matched,
    aliases,
    routes: feature.routes,
    components: feature.components,
    records: feature.records.map((record) => record.path),
    sourceFiles: feature.sourceFiles,
    testFiles: feature.tests,
  }
}

function recordMatch(query: string, record: RecordEntry): RecordMatch | null {
  const matched: MatchDetail[] = []
  const hints = record.implementationHints
  addExactMatches(matched, query, 'record.pathExact', record.recordPath)
  addExactMatches(matched, query, 'record.sourceFilesExact', hints.fileHints)
  addExactMatches(matched, query, 'record.testFilesExact', hints.testHints)
  addExactMatches(matched, query, 'record.graphIdsExact', record.graphIds)
  addMatches(matched, query, 'record.path', record.recordPath)
  addMatches(matched, query, 'record.title', record.title)
  addMatches(matched, query, 'record.layer', record.layer)
  addMatches(matched, query, 'record.aliases', record.aliases)
  addMatches(matched, query, 'record.surfaceTerms', record.surfaceTerms)
  addMatches(matched, query, 'record.featureIds', record.projectProfileFeatureIds)
  addMatches(matched, query, 'record.digest.appliesWhen', record.digest.appliesWhen)
  addMatches(matched, query, 'record.digest.must', record.digest.must)
  addMatches(matched, query, 'record.digest.mustNot', record.digest.mustNot)
  addMatches(matched, query, 'record.digest.bullets', record.digest.bullets)
  addMatches(matched, query, 'record.digest.relatedRecords', record.digest.relatedRecords)
  addMatches(matched, query, 'record.routes', hints.routeHints)
  addMatches(matched, query, 'record.components', hints.componentHints)
  addMatches(matched, query, 'record.sourceFiles', hints.fileHints)
  addMatches(matched, query, 'record.symbols', hints.symbolHints)
  addMatches(matched, query, 'record.testFiles', hints.testHints)
  addMatches(matched, query, 'record.graphIds', record.graphIds)
  addMatches(matched, query, 'record.graphHints', record.graphHints.flatMap((hint) => [hint.id, hint.relation, hint.path, hint.source, hint.target].filter((value): value is string => Boolean(value))))
  addAggregateFallbackMatches(matched, query, 'record.aggregateTokenFallback', [
    record.recordPath,
    record.title,
    record.layer,
    record.status,
    ...record.aliases,
    ...record.surfaceTerms,
    ...record.projectProfileFeatureIds,
    ...record.digest.appliesWhen,
    ...record.digest.must,
    ...record.digest.mustNot,
    ...record.digest.bullets,
    ...record.digest.relatedRecords,
    ...hints.routeHints,
    ...hints.componentHints,
    ...hints.fileHints,
    ...hints.symbolHints,
    ...hints.testHints,
    ...record.graphIds,
    ...record.graphHints.flatMap((hint) => [hint.id, hint.relation, hint.path, hint.source, hint.target]),
  ])
  if (!matched.length) return null
  return {
    recordPath: record.recordPath,
    title: record.title,
    layer: record.layer,
    status: record.status,
    matchCount: matched.length,
    matched,
    aliases: record.aliases,
    surfaceTerms: record.surfaceTerms,
    featureIds: record.projectProfileFeatureIds,
    sourceFiles: hints.fileHints,
    testFiles: hints.testHints,
    symbols: hints.symbolHints,
    routes: hints.routeHints,
    components: hints.componentHints,
    graphIds: record.graphIds,
    relatedRecords: record.digest.relatedRecords,
  }
}

function graphRows(root: string): GraphRow[] {
  const graphPath = path.join(root, '.lazy-harness', 'knowledge', 'graph.jsonl')
  if (!existsSync(graphPath)) return []
  const rows: GraphRow[] = []
  for (const line of readFileSync(graphPath, 'utf8').split(/\r?\n/)) {
    if (!line.trim()) continue
    try { rows.push(JSON.parse(line) as GraphRow) } catch { /* graph-hygiene reports invalid rows */ }
  }
  return rows
}

function graphMatch(query: string, row: GraphRow): GraphMatch | null {
  const matched: MatchDetail[] = []
  if (typeof row.id === 'string') addExactMatches(matched, query, 'graph.idExact', row.id)
  if (typeof row.path === 'string') addExactMatches(matched, query, 'graph.pathExact', row.path)
  if (typeof row.source === 'string') addExactMatches(matched, query, 'graph.sourceExact', row.source)
  if (typeof row.target === 'string') addExactMatches(matched, query, 'graph.targetExact', row.target)
  for (const [key, value] of Object.entries(row)) {
    for (const text of rowStrings(value)) addMatches(matched, query, `graph.${key}`, text)
  }
  addAggregateFallbackMatches(matched, query, 'graph.aggregateTokenFallback', rowStrings(row))
  if (!matched.length) return null
  return {
    id: String(row.id || ''),
    relation: typeof row.relation === 'string' ? row.relation : typeof row.type === 'string' ? row.type : undefined,
    kind: typeof row.kind === 'string' ? row.kind : undefined,
    path: typeof row.path === 'string' ? row.path : undefined,
    source: typeof row.source === 'string' ? row.source : undefined,
    target: typeof row.target === 'string' ? row.target : undefined,
    matchCount: matched.length,
    matched,
  }
}

function exactMatchWeight(item: { matched: MatchDetail[] }): number {
  return item.matched.some((match) => match.field.endsWith('Exact')) ? 1 : 0
}

function sortMatches<T extends { matchCount: number; matched: MatchDetail[] }>(items: T[], label: (item: T) => string): T[] {
  return [...items].sort((a, b) => exactMatchWeight(b) - exactMatchWeight(a) || b.matchCount - a.matchCount || label(a).localeCompare(label(b)))
}

function buildDrilldown(root: string, features: FeatureMatch[], records: RecordMatch[], graphRows: GraphMatch[]): Drilldown {
  const out: Drilldown = { recordPaths: [], sourceFiles: [], testFiles: [], graphIds: [] }
  for (const feature of features) {
    for (const record of feature.records) addPath(record, out, root)
    for (const file of feature.sourceFiles) addPath(file, out, root)
    for (const file of feature.testFiles) addPath(file, out, root)
  }
  for (const record of records) {
    addPath(record.recordPath, out, root)
    for (const related of record.relatedRecords) addPath(related, out, root)
    for (const file of record.sourceFiles) addPath(file, out, root)
    for (const file of record.testFiles) addPath(file, out, root)
    for (const id of record.graphIds) out.graphIds.push(id)
  }
  for (const row of graphRows) {
    if (row.id) out.graphIds.push(row.id)
    for (const value of [row.path, row.source, row.target]) if (value) addPath(value, out, root)
  }
  return {
    recordPaths: uniq(out.recordPaths),
    sourceFiles: uniq(out.sourceFiles),
    testFiles: uniq(out.testFiles),
    graphIds: uniq(out.graphIds),
  }
}

export function buildRecordMap(root: string, query: string, limit = 8, fresh = false): RecordMapResult {
  const { index, cache } = loadRecordIndex(root, fresh)
  const features = sortMatches(index.projectProfile.features.map((feature) => featureMatch(query, feature)).filter((value): value is FeatureMatch => Boolean(value)), (item) => item.id).slice(0, limit)
  const records = sortMatches(index.records.map((record) => recordMatch(query, record)).filter((value): value is RecordMatch => Boolean(value)), (item) => item.recordPath).slice(0, limit)
  const graph = sortMatches(graphRows(root).map((row) => graphMatch(query, row)).filter((value): value is GraphMatch => Boolean(value)), (item) => item.id || item.path || '').slice(0, limit)
  return {
    schemaVersion: '1.0',
    mode: 'record-map.inspect',
    query,
    root,
    source: {
      method: 'record-map-v1',
      tool: '.lazy-harness/scripts/record-map.ts',
      recordIndexMethod: index.source.method,
      recordIndexCache: cache,
    },
    counts: { features: features.length, records: records.length, graphRows: graph.length },
    notes: [
      'Cues only: read real record bodies, Implementation maps, source, and tests before relying on a match.',
      'If matches conflict or remain incomplete after evidence reads, ask an option gate instead of auto-selecting.',
    ],
    features,
    records,
    graphRows: graph,
    drilldown: buildDrilldown(root, features, records, graph),
  }
}

export function buildRecordMapOverview(root: string, limit = 20, fresh = false): RecordMapOverview {
  const { index, cache } = loadRecordIndex(root, fresh)
  const graphSourceRows = graphRows(root)
  const graphMatches = graphSourceRows.map((row) => ({
    id: String(row.id || ''),
    relation: typeof row.relation === 'string' ? row.relation : typeof row.type === 'string' ? row.type : undefined,
    kind: typeof row.kind === 'string' ? row.kind : undefined,
    path: typeof row.path === 'string' ? row.path : undefined,
    source: typeof row.source === 'string' ? row.source : undefined,
    target: typeof row.target === 'string' ? row.target : undefined,
    matchCount: 0,
    matched: [],
  }))
  const layerGroups = new Map<string, RecordEntry[]>()
  for (const record of index.records) {
    const existing = layerGroups.get(record.layer) || []
    existing.push(record)
    layerGroups.set(record.layer, existing)
  }
  const layers = Array.from(layerGroups.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([layer, records]) => ({
      layer,
      count: records.length,
      records: records.slice(0, limit).map((record) => ({ recordPath: record.recordPath, title: record.title, status: record.status })),
    }))
  const relationCounts = new Map<string, number>()
  for (const row of graphMatches) {
    const relation = row.relation || row.kind || 'row'
    relationCounts.set(relation, (relationCounts.get(relation) || 0) + 1)
  }
  const features = index.projectProfile.features.slice(0, limit).map((feature) => ({
    id: feature.id,
    label: feature.label,
    status: feature.status,
    aliases: feature.aliases.map((alias) => alias.value),
    routes: feature.routes,
    components: feature.components,
    records: feature.records.map((record) => record.path),
  }))
  const drilldown: Drilldown = { recordPaths: [], sourceFiles: [], testFiles: [], graphIds: [] }
  for (const record of index.records) {
    addPath(record.recordPath, drilldown, root)
    for (const file of record.implementationHints.fileHints) addPath(file, drilldown, root)
    for (const file of record.implementationHints.testHints) addPath(file, drilldown, root)
    for (const id of record.graphIds) drilldown.graphIds.push(id)
  }
  for (const feature of index.projectProfile.features) {
    for (const record of feature.records) addPath(record.path, drilldown, root)
    for (const file of feature.sourceFiles) addPath(file, drilldown, root)
    for (const file of feature.tests) addPath(file, drilldown, root)
  }
  for (const row of graphMatches) {
    if (row.id) drilldown.graphIds.push(row.id)
    for (const value of [row.path, row.source, row.target]) if (value) addPath(value, drilldown, root)
  }
  return {
    schemaVersion: '1.0',
    mode: 'record-map.overview',
    root,
    source: {
      method: 'record-map-v1',
      tool: '.lazy-harness/scripts/record-map.ts',
      recordIndexMethod: index.source.method,
      recordIndexCache: cache,
    },
    notes: [
      'Overview first: inspect this project map before choosing concrete map nodes.',
      'Then use `.lazy-harness/bin/lazy map <feature-id|record-path|graph-id|source-path> --format=md --limit=8` with feature ids, record paths, graph ids, source paths, and test paths copied from the map; read real evidence, and only then answer or mutate.',
      'Cues only: overview and drill-down candidates do not satisfy read debt by themselves.',
    ],
    inventory: {
      totalRecords: index.records.length,
      totalFeatures: index.projectProfile.features.length,
      totalGraphRows: graphSourceRows.length,
      layers,
      generatedIndexes: {
        recordIndex: existsSync(path.join(root, '.lazy-harness', 'generated', 'record-index.json')),
        implementationIndex: existsSync(path.join(root, '.lazy-harness', 'generated', 'implementation-index.json')),
        referenceIndex: existsSync(path.join(root, '.lazy-harness', 'generated', 'reference-index.json')),
      },
    },
    features,
    graph: {
      relations: Array.from(relationCounts.entries()).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).map(([relation, count]) => ({ relation, count })),
      sampleRows: graphMatches.slice(0, limit),
    },
    drilldown: {
      recordPaths: uniq(drilldown.recordPaths).slice(0, limit * 3),
      sourceFiles: uniq(drilldown.sourceFiles).slice(0, limit * 3),
      testFiles: uniq(drilldown.testFiles).slice(0, limit * 3),
      graphIds: uniq(drilldown.graphIds).slice(0, limit * 3),
    },
  }
}

function renderList(values: string[], indent = '  '): string[] {
  if (!values.length) return [`${indent}- -`]
  return values.map((value) => `${indent}- \`${value}\``)
}

function renderMarkdown(result: RecordMapResult): string {
  const lines: string[] = []
  lines.push('# Record map')
  lines.push('')
  lines.push(`- query: \`${result.query}\``)
  lines.push(`- features: ${result.counts.features}`)
  lines.push(`- records: ${result.counts.records}`)
  lines.push(`- graph rows: ${result.counts.graphRows}`)
  lines.push(`- record-index cache: ${result.source.recordIndexCache.used ? 'used' : 'rebuilt'} (${result.source.recordIndexCache.reason})`)
  lines.push('- caveat: cues only; read real records/source/tests before relying on a match.')
  lines.push('')
  lines.push('## Features')
  if (!result.features.length) lines.push('- -')
  for (const feature of result.features) {
    lines.push(`- \`${feature.id}\` — ${feature.label || '(no label)'} (${feature.status}, matches=${feature.matchCount})`)
    if (feature.routes.length) lines.push(`  - routes: ${feature.routes.map((item) => `\`${item}\``).join(', ')}`)
    if (feature.components.length) lines.push(`  - components: ${feature.components.map((item) => `\`${item}\``).join(', ')}`)
    if (feature.records.length) lines.push(`  - records: ${feature.records.map((item) => `\`${item}\``).join(', ')}`)
  }
  lines.push('', '## Records')
  if (!result.records.length) lines.push('- -')
  for (const record of result.records) {
    lines.push(`- \`${record.recordPath}\` — ${record.title} (${record.layer}/${record.status}, matches=${record.matchCount})`)
    if (record.aliases.length) lines.push(`  - aliases: ${record.aliases.slice(0, 8).map((item) => `\`${item}\``).join(', ')}`)
    if (record.components.length) lines.push(`  - components: ${record.components.slice(0, 8).map((item) => `\`${item}\``).join(', ')}`)
    if (record.sourceFiles.length) lines.push(`  - source: ${record.sourceFiles.slice(0, 8).map((item) => `\`${item}\``).join(', ')}`)
    if (record.testFiles.length) lines.push(`  - tests: ${record.testFiles.slice(0, 8).map((item) => `\`${item}\``).join(', ')}`)
    if (record.graphIds.length) lines.push(`  - graph: ${record.graphIds.slice(0, 8).map((item) => `\`${item}\``).join(', ')}`)
  }
  lines.push('', '## Graph rows')
  if (!result.graphRows.length) lines.push('- -')
  for (const row of result.graphRows) {
    lines.push(`- \`${row.id || '(no id)'}\` (${row.relation || row.kind || 'row'}, matches=${row.matchCount})`)
    if (row.path) lines.push(`  - path: \`${row.path}\``)
    if (row.source) lines.push(`  - source: \`${row.source}\``)
    if (row.target) lines.push(`  - target: \`${row.target}\``)
  }
  lines.push('', '## Drill-down candidates')
  lines.push('- Records:')
  lines.push(...renderList(result.drilldown.recordPaths, '  '))
  lines.push('- Source files:')
  lines.push(...renderList(result.drilldown.sourceFiles, '  '))
  lines.push('- Test files:')
  lines.push(...renderList(result.drilldown.testFiles, '  '))
  lines.push('- Graph ids:')
  lines.push(...renderList(result.drilldown.graphIds, '  '))
  lines.push('')
  lines.push('## Fallback')
  lines.push('- If this map is empty or ambiguous, do root-bound source search inside this host, then create/update records only after evidence and user confirmation.')
  return `${lines.join('\n')}\n`
}

function renderOverviewMarkdown(result: RecordMapOverview): string {
  const lines: string[] = []
  lines.push('# Record map overview')
  lines.push('')
  lines.push('- mode: `record-map.overview`')
  lines.push(`- records: ${result.inventory.totalRecords}`)
  lines.push(`- features: ${result.inventory.totalFeatures}`)
  lines.push(`- graph rows: ${result.inventory.totalGraphRows}`)
  lines.push(`- record-index cache: ${result.source.recordIndexCache.used ? 'used' : 'rebuilt'} (${result.source.recordIndexCache.reason})`)
  lines.push(`- generated indexes: record-index=${result.inventory.generatedIndexes.recordIndex ? 'present' : 'missing'}, implementation-index=${result.inventory.generatedIndexes.implementationIndex ? 'present' : 'missing'}, reference-index=${result.inventory.generatedIndexes.referenceIndex ? 'present' : 'missing'}`)
  lines.push('- first step: use this overview as the project map; the LLM chooses concrete feature ids, record paths, graph ids, source paths, or test paths from this output.')
  lines.push('- drill-down CLI: `.lazy-harness/bin/lazy map <feature-id|record-path|graph-id|source-path> --format=md --limit=8`')
  lines.push('- caveat: cues only; read real records/source/tests before relying on a match.')
  lines.push('', '## Layers')
  for (const layer of result.inventory.layers) {
    lines.push(`- ${layer.layer}: ${layer.count}`)
    for (const record of layer.records.slice(0, 5)) lines.push(`  - \`${record.recordPath}\` — ${record.title} (${record.status})`)
  }
  lines.push('', '## Features')
  if (!result.features.length) lines.push('- -')
  for (const feature of result.features) {
    lines.push(`- \`${feature.id}\` — ${feature.label || '(no label)'} (${feature.status})`)
    if (feature.aliases.length) lines.push(`  - aliases: ${feature.aliases.slice(0, 8).map((item) => `\`${item}\``).join(', ')}`)
    if (feature.routes.length) lines.push(`  - routes: ${feature.routes.slice(0, 8).map((item) => `\`${item}\``).join(', ')}`)
    if (feature.components.length) lines.push(`  - components: ${feature.components.slice(0, 8).map((item) => `\`${item}\``).join(', ')}`)
  }
  lines.push('', '## Graph relations')
  if (!result.graph.relations.length) lines.push('- -')
  for (const relation of result.graph.relations.slice(0, 20)) lines.push(`- ${relation.relation}: ${relation.count}`)
  lines.push('', '## Drill-down candidates')
  lines.push('- Records:')
  lines.push(...renderList(result.drilldown.recordPaths, '  '))
  lines.push('- Source files:')
  lines.push(...renderList(result.drilldown.sourceFiles, '  '))
  lines.push('- Test files:')
  lines.push(...renderList(result.drilldown.testFiles, '  '))
  lines.push('- Graph ids:')
  lines.push(...renderList(result.drilldown.graphIds, '  '))
  return `${lines.join('\n')}\n`
}

function main(): void {
  try {
    const args = parseArgs(process.argv.slice(2))
    if (args.overview) {
      const result = buildRecordMapOverview(args.root, args.limit, args.fresh)
      if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
      else process.stdout.write(renderOverviewMarkdown(result))
    } else {
      const result = buildRecordMap(args.root, args.query, args.limit, args.fresh)
      if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
      else process.stdout.write(renderMarkdown(result))
    }
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    process.exit(1)
  }
}

if (import.meta.main) main()
