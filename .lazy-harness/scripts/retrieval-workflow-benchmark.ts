#!/usr/bin/env bun
/**
 * retrieval-workflow-benchmark.ts
 *
 * Read-only benchmark for post-overview retrieval helper workflows. This script
 * measures bytes/tokens/time/candidate coverage and a deterministic follow-up
 * record-read simulation. It is not semantic authority and must not change
 * lifecycle, prompt, overview, read-debt, or option-gate policy.
 */
import path from 'node:path'
import { existsSync, readFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'

const DEFAULT_QUERIES = [
  'map-first-retrieval',
  'record-source-indexing',
  'capability-registry',
  'sync-install-update',
]

const FORBIDDEN_FIELDS = new Set(['requiredRead', 'optionalRead', 'confidence', 'intent', 'risk', 'gate', 'nextAction', 'candidateMeanings'])
const LAYERS = ['DDD', 'BDD', 'SDD', 'TDD', 'SSOT'] as const

type Format = 'json' | 'md'
type SurfaceName = 'map' | 'map_plus_retrieval_audit' | 'no_map'
type LayerName = typeof LAYERS[number]

interface Args {
  root: string
  format: Format
  limit: number
  queries: string[]
}

interface Candidates {
  recordPaths: string[]
  sourceFiles: string[]
  testFiles: string[]
  graphIds: string[]
}

interface FollowupRead {
  recordPaths: string[]
  readCount: number
  bytes: number
  estimatedTokens: number
  coveredLayers: Record<LayerName, boolean>
  missingLayers: LayerName[]
}

interface SurfaceMetric {
  name: SurfaceName
  helperCalls: number
  helperBytes: number
  helperEstimatedTokens: number
  elapsedMs: number
  resultState: string
  candidateCounts: {
    records: number
    sources: number
    tests: number
    graphs: number
  }
  layerCoverage: Record<LayerName, boolean>
  followupRead: FollowupRead
  totalEstimatedTokens: number
}

interface QueryBenchmark {
  query: string
  surfaces: Record<SurfaceName, SurfaceMetric>
}

interface OverviewCost {
  command: string
  helperBytes: number
  helperEstimatedTokens: number
  elapsedMs: number
}

interface RetrievalWorkflowBenchmark {
  schemaVersion: '1.0'
  mode: 'retrieval-workflow-benchmark'
  root: string
  querySet: string[]
  limit: number
  notes: string[]
  policyBoundary: string
  surfaces: QueryBenchmark[]
  overview: OverviewCost
  summary: {
    queryCount: number
    aggregate: Record<SurfaceName, {
      helperCalls: number
      helperBytes: number
      helperEstimatedTokens: number
      followupReadCount: number
      followupBytes: number
      followupEstimatedTokens: number
      totalEstimatedTokens: number
      fullLayerCoverageCount: number
    }>
    mapInclusive: {
      helperEstimatedTokens: number
      followupEstimatedTokens: number
      totalEstimatedTokens: number
    }
    deltas: {
      mapPlusRetrievalAuditVsMap: {
        helperCallDelta: number
        helperTokenDelta: number
        totalTokenDelta: number
      }
      noMapVsMap: {
        helperTokenDelta: number
        totalTokenDelta: number
      }
      noMapVsMapInclusive: {
        helperTokenDelta: number
        totalTokenDelta: number
      }
    }
  }
}

function usage(exitCode = 2): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Retrieval Workflow Benchmark\n\nUsage:\n  .lazy-harness/bin/lazy retrieval-workflow-benchmark [--format=json|md] [--limit=N] [--queries=q1,q2]\n\nRead-only measurement helper. Compares post-overview lazy map and retrieval-audit workflows. Measurement only; not semantic authority.`)
  process.exit(exitCode)
}

function parseArgs(argv: string[]): Args {
  const args: Args = { root: process.env.LAZY_HOST_ROOT || process.cwd(), format: 'md', limit: 8, queries: DEFAULT_QUERIES }
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
    else if ((arg === '--queries' || arg === '-q') && next) { args.queries = parseQueries(next); i += 1 }
    else if (arg.startsWith('--queries=')) args.queries = parseQueries(arg.slice('--queries='.length))
    else if (arg.startsWith('-')) throw new Error(`Unknown argument: ${arg}`)
    else args.queries = parseQueries(arg)
  }
  args.root = path.resolve(args.root)
  if (!existsSync(path.join(args.root, '.lazy-harness'))) throw new Error(`Host root missing .lazy-harness: ${args.root}`)
  if (args.queries.length === 0) throw new Error('At least one query is required')
  return args
}

function normalizeFormat(value: string): Format {
  if (value === 'markdown') return 'md'
  if (value === 'json' || value === 'md') return value
  throw new Error(`Unsupported --format: ${value}`)
}

function normalizeLimit(value: string): number {
  const n = Number(value)
  if (!Number.isInteger(n) || n < 1 || n > 50) throw new Error(`Unsupported --limit: ${value}`)
  return n
}

function parseQueries(value: string): string[] {
  return value.split(',').map((item) => item.trim()).filter(Boolean)
}

function estimateTokensFromBytes(bytes: number): number {
  return Math.ceil(bytes / 4)
}

const NO_MAP_DIRS = ['domain', 'spec', 'behavior', 'tests', 'decisions', 'ssot', 'planning']

function runGrepNoMap(root: string, query: string): { recordPaths: string[]; bytes: number; elapsedMs: number } {
  const terms = unique(query.split(/[-\s]+/).filter((term) => term.length > 1))
  const pattern = terms.length ? terms.join('|') : query
  const dirs = NO_MAP_DIRS
    .map((dir) => `.lazy-harness/${dir}`)
    .filter((dir) => existsSync(path.join(root, dir)))
  const start = performance.now()
  const completed = spawnSync('grep', ['-rliE', pattern, ...dirs], {
    cwd: root,
    env: { ...process.env },
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
  })
  const elapsedMs = Math.round((performance.now() - start) * 100) / 100
  if (completed.status !== 0 && completed.status !== 1) {
    throw new Error(`grep no-map failed with exit ${completed.status}:\n${completed.stdout || ''}${completed.stderr || ''}`)
  }
  const stdout = completed.stdout || ''
  const recordPaths = unique(stdout.split('\n').map((line) => line.trim()).filter(Boolean)).sort()
  return { recordPaths, bytes: Buffer.byteLength(stdout, 'utf8'), elapsedMs }
}

function measureOverview(root: string, limit: number): OverviewCost {
  const overview = runLazyJson(root, ['map', '--overview', '--format=json', `--limit=${limit}`, '--fresh'])
  return {
    command: `lazy map --overview --format=json --limit=${limit} --fresh`,
    helperBytes: overview.bytes,
    helperEstimatedTokens: estimateTokensFromBytes(overview.bytes),
    elapsedMs: overview.elapsedMs,
  }
}

function unique(values: Array<string | undefined | null>): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  for (const raw of values) {
    const value = (raw || '').trim()
    if (!value || seen.has(value)) continue
    seen.add(value)
    out.push(value)
  }
  return out
}

function mergeCandidates(...sets: Candidates[]): Candidates {
  return {
    recordPaths: unique(sets.flatMap((set) => set.recordPaths)),
    sourceFiles: unique(sets.flatMap((set) => set.sourceFiles)),
    testFiles: unique(sets.flatMap((set) => set.testFiles)),
    graphIds: unique(sets.flatMap((set) => set.graphIds)),
  }
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
  const coverage = Object.fromEntries(LAYERS.map((layer) => [layer, false])) as Record<LayerName, boolean>
  for (const recordPath of recordPaths) {
    const layer = layerForRecordPath(recordPath)
    if (layer) coverage[layer] = true
  }
  return coverage
}

function missingLayers(coverage: Record<LayerName, boolean>): LayerName[] {
  return LAYERS.filter((layer) => !coverage[layer])
}

function simulateFollowupRead(root: string, recordPaths: string[]): FollowupRead {
  const covered = Object.fromEntries(LAYERS.map((layer) => [layer, false])) as Record<LayerName, boolean>
  const selected: string[] = []
  let bytes = 0
  for (const recordPath of recordPaths) {
    const absolute = path.resolve(root, recordPath)
    if (!absolute.startsWith(root) || !existsSync(absolute)) continue
    selected.push(recordPath)
    bytes += readFileSync(absolute).byteLength
    const layer = layerForRecordPath(recordPath)
    if (layer) covered[layer] = true
    if (LAYERS.every((layer) => covered[layer])) break
  }
  return {
    recordPaths: selected,
    readCount: selected.length,
    bytes,
    estimatedTokens: estimateTokensFromBytes(bytes),
    coveredLayers: covered,
    missingLayers: missingLayers(covered),
  }
}

function runLazyJson(root: string, args: string[]): { payload: any; bytes: number; elapsedMs: number } {
  const lazy = path.join(root, '.lazy-harness/bin/lazy')
  const start = performance.now()
  const completed = spawnSync(lazy, args, {
    cwd: root,
    env: { ...process.env, LAZY_HOST_ROOT: root },
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
  })
  const elapsedMs = Math.round((performance.now() - start) * 100) / 100
  if (completed.status !== 0) {
    throw new Error(`lazy ${args.join(' ')} failed with exit ${completed.status}:\n${completed.stdout || ''}${completed.stderr || ''}`)
  }
  const stdout = completed.stdout || ''
  return { payload: JSON.parse(stdout), bytes: Buffer.byteLength(stdout, 'utf8'), elapsedMs }
}

function candidatesFromMap(payload: any): Candidates {
  const drill = payload?.drilldown || {}
  return {
    recordPaths: Array.isArray(drill.recordPaths) ? drill.recordPaths : [],
    sourceFiles: Array.isArray(drill.sourceFiles) ? drill.sourceFiles : [],
    testFiles: Array.isArray(drill.testFiles) ? drill.testFiles : [],
    graphIds: Array.isArray(drill.graphIds) ? drill.graphIds : [],
  }
}

function candidatesFromStandard(payload: any): Candidates {
  const candidates = payload?.candidates || {}
  return {
    recordPaths: Array.isArray(candidates.recordPaths) ? candidates.recordPaths : [],
    sourceFiles: Array.isArray(candidates.sourceFiles) ? candidates.sourceFiles : [],
    testFiles: Array.isArray(candidates.testFiles) ? candidates.testFiles : [],
    graphIds: Array.isArray(candidates.graphIds) ? candidates.graphIds : [],
  }
}

function resultState(payload: any): string {
  return String(payload?.resultState || payload?.coverage?.state || payload?.mode || 'unknown')
}

function metric(name: SurfaceName, helperCalls: number, helperBytes: number, elapsedMs: number, state: string, candidates: Candidates, root: string): SurfaceMetric {
  const coverage = layerCoverage(candidates.recordPaths)
  const followupRead = simulateFollowupRead(root, candidates.recordPaths)
  const helperEstimatedTokens = estimateTokensFromBytes(helperBytes)
  return {
    name,
    helperCalls,
    helperBytes,
    helperEstimatedTokens,
    elapsedMs: Math.round(elapsedMs * 100) / 100,
    resultState: state,
    candidateCounts: {
      records: candidates.recordPaths.length,
      sources: candidates.sourceFiles.length,
      tests: candidates.testFiles.length,
      graphs: candidates.graphIds.length,
    },
    layerCoverage: coverage,
    followupRead,
    totalEstimatedTokens: helperEstimatedTokens + followupRead.estimatedTokens,
  }
}

function measureQuery(root: string, query: string, limit: number): QueryBenchmark {
  const map = runLazyJson(root, ['map', query, '--format=json', `--limit=${limit}`, '--fresh'])
  const retrieval = runLazyJson(root, ['retrieval-audit', query, '--format=json', `--limit=${limit}`])

  const mapCandidates = candidatesFromMap(map.payload)
  const retrievalCandidates = candidatesFromStandard(retrieval.payload)
  const merged = mergeCandidates(mapCandidates, retrievalCandidates)
  const noMap = runGrepNoMap(root, query)
  const noMapCandidates: Candidates = { recordPaths: noMap.recordPaths, sourceFiles: [], testFiles: [], graphIds: [] }

  return {
    query,
    surfaces: {
      map: metric('map', 1, map.bytes, map.elapsedMs, resultState(map.payload), mapCandidates, root),
      map_plus_retrieval_audit: metric('map_plus_retrieval_audit', 2, map.bytes + retrieval.bytes, map.elapsedMs + retrieval.elapsedMs, resultState(retrieval.payload), merged, root),
      no_map: metric('no_map', 1, noMap.bytes, noMap.elapsedMs, 'grep-fallback', noMapCandidates, root),
    },
  }
}

function aggregate(surfaces: QueryBenchmark[], name: SurfaceName): RetrievalWorkflowBenchmark['summary']['aggregate'][SurfaceName] {
  const metrics = surfaces.map((query) => query.surfaces[name])
  return {
    helperCalls: metrics.reduce((sum, item) => sum + item.helperCalls, 0),
    helperBytes: metrics.reduce((sum, item) => sum + item.helperBytes, 0),
    helperEstimatedTokens: metrics.reduce((sum, item) => sum + item.helperEstimatedTokens, 0),
    followupReadCount: metrics.reduce((sum, item) => sum + item.followupRead.readCount, 0),
    followupBytes: metrics.reduce((sum, item) => sum + item.followupRead.bytes, 0),
    followupEstimatedTokens: metrics.reduce((sum, item) => sum + item.followupRead.estimatedTokens, 0),
    totalEstimatedTokens: metrics.reduce((sum, item) => sum + item.totalEstimatedTokens, 0),
    fullLayerCoverageCount: metrics.filter((item) => missingLayers(item.layerCoverage).length === 0).length,
  }
}

function buildBenchmark(root: string, queries: string[], limit: number): RetrievalWorkflowBenchmark {
  const surfaces = queries.map((query) => measureQuery(root, query, limit))
  const overview = measureOverview(root, limit)
  const aggregateMap = aggregate(surfaces, 'map')
  const aggregateMapRetrieval = aggregate(surfaces, 'map_plus_retrieval_audit')
  const aggregateNoMap = aggregate(surfaces, 'no_map')
  const overviewTokensPerTask = overview.helperEstimatedTokens * surfaces.length
  const mapInclusive = {
    helperEstimatedTokens: aggregateMap.helperEstimatedTokens + overviewTokensPerTask,
    followupEstimatedTokens: aggregateMap.followupEstimatedTokens,
    totalEstimatedTokens: aggregateMap.totalEstimatedTokens + overviewTokensPerTask,
  }
  return {
    schemaVersion: '1.0',
    mode: 'retrieval-workflow-benchmark',
    root,
    querySet: queries,
    limit,
    notes: [
      'measurement-only; cues are not semantic authority',
      'map and map_plus_retrieval_audit are post-overview helper paths; no_map is the AGENTS.md root-bound grep fallback that skips lazy map entirely',
      'overview reports the otherwise-excluded mandatory lazy map --overview cost; mapInclusive adds it back per task so map is compared against no_map honestly',
      'no_map uses a deterministic term-alternation grep proxy over record dirs; conservative cost proxy, not optimal agent behavior or proof that skipping map is permitted',
      'follow-up reads are deterministic cost proxies, not proof of sufficient evidence',
      'graph query/path/explain CLI has been removed from the default retrieval workflow',
      'does not change lifecycle/prompt/overview policy; message.received still mandates map-first',
    ],
    policyBoundary: 'measurement-only; does not change lifecycle/prompt/overview policy or replace real record/source/test reads',
    surfaces,
    overview,
    summary: {
      queryCount: surfaces.length,
      aggregate: {
        map: aggregateMap,
        map_plus_retrieval_audit: aggregateMapRetrieval,
        no_map: aggregateNoMap,
      },
      mapInclusive,
      deltas: {
        mapPlusRetrievalAuditVsMap: {
          helperCallDelta: aggregateMapRetrieval.helperCalls - aggregateMap.helperCalls,
          helperTokenDelta: aggregateMapRetrieval.helperEstimatedTokens - aggregateMap.helperEstimatedTokens,
          totalTokenDelta: aggregateMapRetrieval.totalEstimatedTokens - aggregateMap.totalEstimatedTokens,
        },
        noMapVsMap: {
          helperTokenDelta: aggregateNoMap.helperEstimatedTokens - aggregateMap.helperEstimatedTokens,
          totalTokenDelta: aggregateNoMap.totalEstimatedTokens - aggregateMap.totalEstimatedTokens,
        },
        noMapVsMapInclusive: {
          helperTokenDelta: aggregateNoMap.helperEstimatedTokens - mapInclusive.helperEstimatedTokens,
          totalTokenDelta: aggregateNoMap.totalEstimatedTokens - mapInclusive.totalEstimatedTokens,
        },
      },
    },
  }
}

function renderMarkdown(benchmark: RetrievalWorkflowBenchmark): string {
  const lines: string[] = []
  lines.push('# Retrieval Workflow Benchmark')
  lines.push('')
  lines.push(`- mode: \`${benchmark.mode}\``)
  lines.push(`- queries: ${benchmark.querySet.length}`)
  lines.push(`- limit: ${benchmark.limit}`)
  lines.push(`- policy: ${benchmark.policyBoundary}`)
  lines.push(`- overview (mandatory per task): ${benchmark.overview.helperEstimatedTokens} tokens (${benchmark.overview.helperBytes} bytes, ${benchmark.overview.elapsedMs}ms)`)
  lines.push('')
  lines.push('## Aggregate')
  lines.push('')
  lines.push('| Surface | Helper calls | Helper tokens | Follow-up reads | Follow-up tokens | Total tokens | Full layer coverage |')
  lines.push('|---|---:|---:|---:|---:|---:|---:|')
  for (const name of ['map', 'map_plus_retrieval_audit', 'no_map'] as SurfaceName[]) {
    const item = benchmark.summary.aggregate[name]
    lines.push(`| ${name} | ${item.helperCalls} | ${item.helperEstimatedTokens} | ${item.followupReadCount} | ${item.followupEstimatedTokens} | ${item.totalEstimatedTokens} | ${item.fullLayerCoverageCount}/${benchmark.summary.queryCount} |`)
  }
  const inclusive = benchmark.summary.mapInclusive
  lines.push(`| map+overview (per task) | - | ${inclusive.helperEstimatedTokens} | - | ${inclusive.followupEstimatedTokens} | ${inclusive.totalEstimatedTokens} | - |`)
  lines.push('')
  lines.push('## Deltas')
  lines.push('')
  lines.push(`- map_plus_retrieval_audit vs map helper call delta: ${benchmark.summary.deltas.mapPlusRetrievalAuditVsMap.helperCallDelta}`)
  lines.push(`- map_plus_retrieval_audit vs map total token delta: ${benchmark.summary.deltas.mapPlusRetrievalAuditVsMap.totalTokenDelta}`)
  lines.push(`- no_map vs map helper token delta: ${benchmark.summary.deltas.noMapVsMap.helperTokenDelta}`)
  lines.push(`- no_map vs map total token delta: ${benchmark.summary.deltas.noMapVsMap.totalTokenDelta}`)
  lines.push(`- no_map vs map+overview helper token delta: ${benchmark.summary.deltas.noMapVsMapInclusive.helperTokenDelta}`)
  lines.push(`- no_map vs map+overview total token delta: ${benchmark.summary.deltas.noMapVsMapInclusive.totalTokenDelta}`)
  lines.push('')
  lines.push('## Per query')
  for (const query of benchmark.surfaces) {
    lines.push('')
    lines.push(`### ${query.query}`)
    lines.push('| Surface | State | Helper tokens | Follow-up reads | Total tokens | Missing layers |')
    lines.push('|---|---|---:|---:|---:|---|')
    for (const name of ['map', 'map_plus_retrieval_audit', 'no_map'] as SurfaceName[]) {
      const item = query.surfaces[name]
      lines.push(`| ${name} | ${item.resultState} | ${item.helperEstimatedTokens} | ${item.followupRead.readCount} | ${item.totalEstimatedTokens} | ${item.followupRead.missingLayers.join(', ') || '-'} |`)
    }
  }
  lines.push('')
  lines.push('## Notes')
  for (const note of benchmark.notes) lines.push(`- ${note}`)
  return `${lines.join('\n')}\n`
}

function assertNoForbiddenFields(value: unknown, pathName = '$'): void {
  if (Array.isArray(value)) {
    value.forEach((child, index) => assertNoForbiddenFields(child, `${pathName}[${index}]`))
    return
  }
  if (!value || typeof value !== 'object') return
  for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
    if (FORBIDDEN_FIELDS.has(key)) throw new Error(`Forbidden semantic-authority field in benchmark output: ${pathName}.${key}`)
    assertNoForbiddenFields(child, `${pathName}.${key}`)
  }
}

function main(): void {
  try {
    const args = parseArgs(process.argv.slice(2))
    const benchmark = buildBenchmark(args.root, args.queries, args.limit)
    assertNoForbiddenFields(benchmark)
    if (args.format === 'json') console.log(JSON.stringify(benchmark, null, 2))
    else process.stdout.write(renderMarkdown(benchmark))
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    process.exit(1)
  }
}

main()
