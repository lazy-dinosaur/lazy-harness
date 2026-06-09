#!/usr/bin/env bun
/**
 * graph-explain-accuracy-benchmark.ts
 *
 * Read-only gold-labeled retrieval/ranking benchmark for `lazy graph explain`.
 * Measures retrieval quality, not semantic task success. The fixture is
 * human-selected and cue-only; it must not become required-read policy.
 */
import path from 'node:path'
import { existsSync, readFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { createHash } from 'node:crypto'

type Format = 'json' | 'md'

type Scenario = {
  id: string
  query: string
  gold: string[]
  expectedLayers?: string[]
  negativeContains?: string[]
  expectedGap?: boolean
}

type Fixture = {
  schemaVersion: string
  mode: string
  notes?: string[]
  scenarios: Scenario[]
}

type Args = {
  root: string
  fixture: string
  format: Format
  limit: number
  maxStatements: number
  precisionK: number
  failOnThresholds: boolean
}

type ScenarioMetric = {
  id: string
  query: string
  state: string
  rankedCount: number
  goldCount: number
  hits: number
  misses: string[]
  ranks: Record<string, number | null>
  recall: number | null
  precisionAtKStrict: number | null
  mrr: number | null
  ndcg: number | null
  expectedLayers: string[]
  layersFound: string[]
  layerRecall: number | null
  negativeHits: string[]
  topK: string[]
  forbiddenFields: string[]
  okAllGoldFoundOrGap: boolean
}

type BenchmarkResult = {
  schemaVersion: '1.0'
  mode: 'graph-explain-accuracy-benchmark'
  root: string
  fixture: string
  limit: number
  maxStatements: number
  precisionK: number
  notes: string[]
  policyBoundary: string
  rows: ScenarioMetric[]
  summary: {
    scenarioCount: number
    nonGapScenarios: number
    gapScenarios: number
    goldItemsTotal: number
    goldHitsTotal: number
    microRecall: number | null
    macroRecall: number | null
    macroPrecisionAtKStrict: number | null
    macroMrr: number | null
    macroNdcg: number | null
    macroLayerRecall: number | null
    negativeHitScenarios: number
    gapAccuracy: number | null
    allGoldFoundOrGapCount: number
    forbiddenFieldScenarios: number
    watchedFilesMutated: string[]
  }
}

const DEFAULT_FIXTURE = '.lazy-harness/fixtures/graph-explain-gold-accuracy.json'
const FORBIDDEN_FIELDS = new Set(['requiredRead', 'optionalRead', 'confidence', 'intent', 'risk', 'gate', 'nextAction', 'candidateMeanings', 'importance', 'score'])
const WATCHED_FILES = [
  '.lazy-harness/knowledge/graph.jsonl',
  '.lazy-harness/generated/record-index.json',
  '.lazy-harness/generated/implementation-index.json',
]

function usage(exitCode = 2): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Graph Explain Accuracy Benchmark\n\nUsage:\n  .lazy-harness/bin/lazy graph-explain-accuracy-benchmark [--format=json|md] [--fixture=PATH] [--limit=N] [--max-statements=N] [--precision-k=N] [--fail-on-thresholds]\n\nRead-only gold-labeled retrieval/ranking benchmark. Measurement only; not semantic authority.`)
  process.exit(exitCode)
}

function parseArgs(argv: string[]): Args {
  const args: Args = {
    root: process.env.LAZY_HOST_ROOT || process.cwd(),
    fixture: DEFAULT_FIXTURE,
    format: 'md',
    limit: 20,
    maxStatements: 20,
    precisionK: 8,
    failOnThresholds: false,
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = argv[i + 1]
    if (arg === '--help' || arg === '-h') usage(0)
    else if ((arg === '--root' || arg === '--host') && next) { args.root = next; i += 1 }
    else if (arg.startsWith('--root=')) args.root = arg.slice('--root='.length)
    else if (arg.startsWith('--host=')) args.root = arg.slice('--host='.length)
    else if ((arg === '--fixture') && next) { args.fixture = next; i += 1 }
    else if (arg.startsWith('--fixture=')) args.fixture = arg.slice('--fixture='.length)
    else if ((arg === '--format' || arg === '-f') && next) { args.format = normalizeFormat(next); i += 1 }
    else if (arg.startsWith('--format=')) args.format = normalizeFormat(arg.slice('--format='.length))
    else if ((arg === '--limit' || arg === '-n') && next) { args.limit = normalizeInt(next, 'limit', 1, 100); i += 1 }
    else if (arg.startsWith('--limit=')) args.limit = normalizeInt(arg.slice('--limit='.length), 'limit', 1, 100)
    else if ((arg === '--max-statements') && next) { args.maxStatements = normalizeInt(next, 'max-statements', 1, 20); i += 1 }
    else if (arg.startsWith('--max-statements=')) args.maxStatements = normalizeInt(arg.slice('--max-statements='.length), 'max-statements', 1, 20)
    else if ((arg === '--precision-k') && next) { args.precisionK = normalizeInt(next, 'precision-k', 1, 50); i += 1 }
    else if (arg.startsWith('--precision-k=')) args.precisionK = normalizeInt(arg.slice('--precision-k='.length), 'precision-k', 1, 50)
    else if (arg === '--fail-on-thresholds') args.failOnThresholds = true
    else if (arg.startsWith('-')) throw new Error(`Unknown argument: ${arg}`)
    else args.fixture = arg
  }
  args.root = path.resolve(args.root)
  if (!existsSync(path.join(args.root, '.lazy-harness'))) throw new Error(`Host root missing .lazy-harness: ${args.root}`)
  args.fixture = path.isAbsolute(args.fixture) ? args.fixture : path.join(args.root, args.fixture)
  if (!existsSync(args.fixture)) throw new Error(`Fixture missing: ${args.fixture}`)
  return args
}

function normalizeFormat(value: string): Format {
  if (value === 'markdown') return 'md'
  if (value === 'json' || value === 'md') return value
  throw new Error(`Unsupported --format: ${value}`)
}

function normalizeInt(raw: string, name: string, min: number, max: number): number {
  const parsed = Number.parseInt(raw, 10)
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) throw new Error(`Unsupported --${name}: ${raw}`)
  return parsed
}

function loadFixture(file: string): Fixture {
  const parsed = JSON.parse(readFileSync(file, 'utf8'))
  if (parsed?.mode !== 'graph-explain-gold-accuracy-fixture' || !Array.isArray(parsed.scenarios)) throw new Error(`Invalid fixture: ${file}`)
  return parsed
}

function sha256IfExists(root: string, rel: string): string | null {
  const file = path.join(root, rel)
  if (!existsSync(file)) return null
  return createHash('sha256').update(readFileSync(file)).digest('hex')
}

function runGraphExplain(root: string, query: string, limit: number, maxStatements: number): unknown {
  const proc = spawnSync(path.join(root, '.lazy-harness/bin/lazy'), [
    'graph',
    'explain',
    query,
    '--format=json',
    `--limit=${limit}`,
    `--max-statements=${maxStatements}`,
  ], { cwd: root, encoding: 'utf8', env: { ...process.env, LAZY_HOST_ROOT: root } })
  if (proc.status !== 0) throw new Error(`graph explain failed for ${query}\nSTDOUT=${proc.stdout}\nSTDERR=${proc.stderr}`)
  return JSON.parse(proc.stdout)
}

function layerForPath(value: string): string {
  if (value.startsWith('.lazy-harness/domain/')) return 'DDD'
  if (value.startsWith('.lazy-harness/behavior/')) return 'BDD'
  if (value.startsWith('.lazy-harness/spec/')) return 'SDD'
  if (value.startsWith('.lazy-harness/tests/')) return 'TDD'
  if (value.startsWith('.lazy-harness/decisions/')) return 'ADR'
  if (value.startsWith('.lazy-harness/ssot/')) return 'SSOT'
  if (value.startsWith('.lazy-harness/planning/') || value.startsWith('.lazy-harness/plans/')) return 'Planning'
  if (value.startsWith('.lazy-harness/evidence/')) return 'evidence'
  if (value.startsWith('.lazy-harness/scripts/') || value.startsWith('src/') || value.startsWith('tests/')) return 'source'
  return 'other'
}

function addPath(root: string, paths: string[], value: unknown): void {
  if (typeof value !== 'string' || !value) return
  if (!existsSync(path.join(root, value))) return
  if (!paths.includes(value)) paths.push(value)
}

function rankedPaths(root: string, payload: any): string[] {
  const paths: string[] = []
  for (const statement of payload?.statements || []) {
    for (const support of statement?.support || []) addPath(root, paths, support?.path)
    for (const citation of statement?.citations || []) addPath(root, paths, citation)
  }
  const queryPacket = payload?.queryPacket || {}
  for (const seed of queryPacket.seeds || []) {
    addPath(root, paths, seed?.path)
    for (const recordPath of seed?.records || []) addPath(root, paths, recordPath)
    for (const sourceFile of seed?.sourceFiles || []) addPath(root, paths, sourceFile)
  }
  const candidates = queryPacket.candidates || {}
  for (const key of ['recordPaths', 'sourceFiles', 'testFiles']) {
    for (const item of candidates[key] || []) addPath(root, paths, item)
  }
  for (const citation of queryPacket.citations || []) addPath(root, paths, citation?.path || citation)
  return paths
}

function forbiddenPaths(value: unknown, prefix = '$'): string[] {
  const found: string[] = []
  if (Array.isArray(value)) {
    value.forEach((child, index) => found.push(...forbiddenPaths(child, `${prefix}[${index}]`)))
  } else if (value && typeof value === 'object') {
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      if (FORBIDDEN_FIELDS.has(key)) found.push(`${prefix}.${key}`)
      found.push(...forbiddenPaths(child, `${prefix}.${key}`))
    }
  }
  return found
}

function dcg(relevances: number[]): number {
  return relevances.reduce((sum, rel, index) => sum + rel / Math.log2(index + 2), 0)
}

function avg(values: Array<number | null>): number | null {
  const nums = values.filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
  if (!nums.length) return null
  return nums.reduce((sum, value) => sum + value, 0) / nums.length
}

function round(value: number | null): number | null {
  if (value == null) return null
  return Math.round(value * 1000) / 1000
}

function scenarioMetric(root: string, scenario: Scenario, limit: number, maxStatements: number, precisionK: number): ScenarioMetric {
  const payload: any = runGraphExplain(root, scenario.query, limit, maxStatements)
  const ranked = rankedPaths(root, payload)
  const gold = scenario.gold || []
  const goldSet = new Set(gold)
  const expectedGap = Boolean(scenario.expectedGap)
  const hits = gold.filter((item) => ranked.includes(item))
  const ranks: Record<string, number | null> = {}
  for (const item of gold) ranks[item] = ranked.includes(item) ? ranked.indexOf(item) + 1 : null
  const rels = ranked.map((item) => goldSet.has(item) ? 1 : 0)
  const ideal = Array.from({ length: ranked.length }, (_, index) => index < gold.length ? 1 : 0)
  const expectedLayers = new Set(scenario.expectedLayers || [])
  const layersFound = new Set(ranked.map(layerForPath))
  const negativeHits = Array.from(new Set(ranked.flatMap((candidate) => (scenario.negativeContains || []).filter((neg) => candidate.toLowerCase().includes(neg.toLowerCase())).map(() => candidate))))
  const recall = gold.length ? hits.length / gold.length : (expectedGap && payload.resultState === 'gap' && ranked.length === 0 ? 1 : null)
  const top = ranked.slice(0, precisionK)
  const precisionAtKStrict = top.length ? top.filter((item) => goldSet.has(item)).length / top.length : (expectedGap && payload.resultState === 'gap' ? 1 : null)
  const reciprocalRanks = Object.values(ranks).filter((rank): rank is number => typeof rank === 'number').map((rank) => 1 / rank)
  const mrr = gold.length ? (reciprocalRanks.length ? Math.max(...reciprocalRanks) : 0) : (expectedGap && payload.resultState === 'gap' ? 1 : null)
  const ndcg = gold.length && dcg(ideal) > 0 ? dcg(rels) / dcg(ideal) : (expectedGap && payload.resultState === 'gap' ? 1 : null)
  const layerRecall = expectedLayers.size ? Array.from(expectedLayers).filter((layer) => layersFound.has(layer)).length / expectedLayers.size : (expectedGap && payload.resultState === 'gap' ? 1 : null)
  return {
    id: scenario.id,
    query: scenario.query,
    state: String(payload.resultState || ''),
    rankedCount: ranked.length,
    goldCount: gold.length,
    hits: hits.length,
    misses: gold.filter((item) => !ranked.includes(item)),
    ranks,
    recall: round(recall),
    precisionAtKStrict: round(precisionAtKStrict),
    mrr: round(mrr),
    ndcg: round(ndcg),
    expectedLayers: Array.from(expectedLayers).sort(),
    layersFound: Array.from(layersFound).sort(),
    layerRecall: round(layerRecall),
    negativeHits,
    topK: top,
    forbiddenFields: forbiddenPaths(payload),
    okAllGoldFoundOrGap: expectedGap ? payload.resultState === 'gap' && ranked.length === 0 : hits.length === gold.length,
  }
}

function buildBenchmark(args: Args): BenchmarkResult {
  const fixture = loadFixture(args.fixture)
  const before = new Map(WATCHED_FILES.map((file) => [file, sha256IfExists(args.root, file)]))
  const rows = fixture.scenarios.map((scenario) => scenarioMetric(args.root, scenario, args.limit, args.maxStatements, args.precisionK))
  const after = new Map(WATCHED_FILES.map((file) => [file, sha256IfExists(args.root, file)]))
  const watchedFilesMutated = WATCHED_FILES.filter((file) => before.get(file) !== after.get(file))
  const nonGap = rows.filter((row) => row.goldCount > 0)
  const gap = rows.filter((row) => row.goldCount === 0)
  const goldItemsTotal = nonGap.reduce((sum, row) => sum + row.goldCount, 0)
  const goldHitsTotal = nonGap.reduce((sum, row) => sum + row.hits, 0)
  const summary = {
    scenarioCount: rows.length,
    nonGapScenarios: nonGap.length,
    gapScenarios: gap.length,
    goldItemsTotal,
    goldHitsTotal,
    microRecall: round(goldItemsTotal ? goldHitsTotal / goldItemsTotal : null),
    macroRecall: round(avg(nonGap.map((row) => row.recall))),
    macroPrecisionAtKStrict: round(avg(nonGap.map((row) => row.precisionAtKStrict))),
    macroMrr: round(avg(nonGap.map((row) => row.mrr))),
    macroNdcg: round(avg(nonGap.map((row) => row.ndcg))),
    macroLayerRecall: round(avg(nonGap.map((row) => row.layerRecall))),
    negativeHitScenarios: rows.filter((row) => row.negativeHits.length).length,
    gapAccuracy: round(avg(gap.map((row) => row.recall))),
    allGoldFoundOrGapCount: rows.filter((row) => row.okAllGoldFoundOrGap).length,
    forbiddenFieldScenarios: rows.filter((row) => row.forbiddenFields.length).length,
    watchedFilesMutated,
  }
  return {
    schemaVersion: '1.0',
    mode: 'graph-explain-accuracy-benchmark',
    root: args.root,
    fixture: path.relative(args.root, args.fixture) || args.fixture,
    limit: args.limit,
    maxStatements: args.maxStatements,
    precisionK: args.precisionK,
    notes: fixture.notes || [],
    policyBoundary: 'measurement-only: cue-only retrieval/ranking benchmark; not semantic authority and not required-read policy',
    rows,
    summary,
  }
}

function renderMarkdown(result: BenchmarkResult): string {
  const lines: string[] = []
  lines.push('# Graph explain accuracy benchmark')
  lines.push('')
  lines.push(`- mode: \`${result.mode}\``)
  lines.push(`- fixture: \`${result.fixture}\``)
  lines.push(`- scenarios: ${result.summary.scenarioCount}`)
  lines.push(`- precisionK: ${result.precisionK}`)
  lines.push(`- policy: ${result.policyBoundary}`)
  lines.push('')
  lines.push('## Summary')
  for (const [key, value] of Object.entries(result.summary)) lines.push(`- ${key}: ${Array.isArray(value) ? value.join(', ') || '-' : value}`)
  lines.push('')
  lines.push('| id | state | gold | hits | recall | P@K strict | MRR | nDCG | layer recall | negatives |')
  lines.push('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|')
  for (const row of result.rows) {
    lines.push(`| ${row.id} | ${row.state} | ${row.goldCount} | ${row.hits} | ${row.recall ?? ''} | ${row.precisionAtKStrict ?? ''} | ${row.mrr ?? ''} | ${row.ndcg ?? ''} | ${row.layerRecall ?? ''} | ${row.negativeHits.length} |`)
  }
  lines.push('')
  lines.push('## Misses')
  for (const row of result.rows.filter((item) => item.misses.length)) lines.push(`- ${row.id}: ${row.misses.map((item) => `\`${item}\``).join(', ')}`)
  if (!result.rows.some((item) => item.misses.length)) lines.push('- -')
  lines.push('')
  lines.push('## Notes')
  for (const note of result.notes) lines.push(`- ${note}`)
  return `${lines.join('\n')}\n`
}

function assertThresholds(result: BenchmarkResult): void {
  const failures: string[] = []
  const s = result.summary
  if ((s.microRecall ?? 0) < 0.939) failures.push(`microRecall < 0.939: ${s.microRecall}`)
  if ((s.macroRecall ?? 0) < 0.94) failures.push(`macroRecall < 0.94: ${s.macroRecall}`)
  if ((s.macroPrecisionAtKStrict ?? 0) < 0.5) failures.push(`macroPrecisionAtKStrict < 0.5: ${s.macroPrecisionAtKStrict}`)
  if ((s.macroMrr ?? 0) < 0.7) failures.push(`macroMrr < 0.7: ${s.macroMrr}`)
  if ((s.macroNdcg ?? 0) < 0.75) failures.push(`macroNdcg < 0.75: ${s.macroNdcg}`)
  if ((s.macroLayerRecall ?? 0) < 1) failures.push(`macroLayerRecall < 1: ${s.macroLayerRecall}`)
  if (s.negativeHitScenarios !== 0) failures.push(`negativeHitScenarios != 0: ${s.negativeHitScenarios}`)
  if ((s.gapAccuracy ?? 0) < 1) failures.push(`gapAccuracy < 1: ${s.gapAccuracy}`)
  if (s.forbiddenFieldScenarios !== 0) failures.push(`forbiddenFieldScenarios != 0: ${s.forbiddenFieldScenarios}`)
  if (s.watchedFilesMutated.length) failures.push(`watched files mutated: ${s.watchedFilesMutated.join(', ')}`)
  if (failures.length) throw new Error(`graph-explain accuracy thresholds failed:\n- ${failures.join('\n- ')}`)
}

function main(): void {
  try {
    const args = parseArgs(process.argv.slice(2))
    const result = buildBenchmark(args)
    if (args.failOnThresholds) assertThresholds(result)
    if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
    else process.stdout.write(renderMarkdown(result))
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    process.exit(1)
  }
}

main()
