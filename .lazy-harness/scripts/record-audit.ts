#!/usr/bin/env bun
/**
 * Record Audit (SDD: spec/platform/record-audit.md)
 *
 * Read-only host record quality dashboard. Summarizes layer distribution,
 * host-owned/changed records, JSONL health, open markers, Project Profile
 * answer completeness, graph hygiene, and log volume.
 */
import { createHash } from 'node:crypto'
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { homedir } from 'node:os'
import { join, relative, resolve } from 'node:path'

interface Args {
  root: string
  source?: string
  format: 'json' | 'md'
  recent: number
}

interface LayerSummary {
  layer: string
  files: number
  bytes: number
}

interface HostComparisonLayer {
  layer: string
  unique: number
  changed: number
  same: number
  totalOwnedOrChanged: number
}

interface JsonlSummary {
  path: string
  lines: number
  invalid: number
}

interface MarkerSummary {
  marker: string
  files: number
  samplePaths: string[]
}

interface ProjectProfileSummary {
  artifactsPresent: number
  artifactsMissing: number
  artifactsComplete: boolean
  needsInterviewFields: number
  confirmedFields: number
  answersComplete: boolean
  projectFiles: Array<{ path: string; needsInterview: number; confirmed: number; bytes: number }>
}

interface GraphSummary {
  rows: number
  invalidRows: number
  missingPaths: number
  sourceOnlyPaths: number
  commaJoinedPaths: number
  sampleMissingPaths: string[]
  sampleSourceOnlyPaths: string[]
  sampleCommaJoinedPaths: string[]
}

interface RecentFile {
  path: string
  bytes: number
  mtime: string
}

type RecordQualityCode = 'missing-index-header' | 'missing-alias-or-search-key' | 'missing-source-test-hints' | 'missing-graph-link' | 'missing-rule-digest'

interface RecordQualityIssue {
  code: RecordQualityCode
  count: number
  samplePaths: string[]
}

interface RecordQualitySummary {
  advisoryOnly: true
  inspectedRecords: number
  completeRecords: number
  counts: Record<RecordQualityCode, number>
  issues: RecordQualityIssue[]
}

interface AuditResult {
  ok: true
  mode: 'record-audit.inspect'
  schemaVersion: '1.0'
  root: string
  source: string | null
  inspectedAt: string
  layers: LayerSummary[]
  totals: {
    files: number
    bytes: number
    hostUnique: number
    hostChanged: number
    hostSameAsSource: number
    hostOwnedOrChanged: number
  }
  hostComparison: HostComparisonLayer[]
  jsonl: JsonlSummary[]
  markers: MarkerSummary[]
  projectProfile: ProjectProfileSummary
  graph: GraphSummary
  recordQuality: RecordQualitySummary
  recentFiles: RecentFile[]
  warnings: string[]
  nextActions: string[]
}

const LAYERS = ['domain', 'spec', 'behavior', 'tests', 'decisions', 'ssot', 'planning', 'plans', 'knowledge', 'project', 'handoff', 'questions', 'logs']
const COMPARE_LAYERS = ['domain', 'spec', 'behavior', 'tests', 'decisions', 'ssot', 'planning', 'plans', 'knowledge', 'project', 'handoff', 'questions']
const MARKERS = ['needs-interview', 'TODO', 'FIXME', 'stale', 'conflict', 'ambiguous', 'needs-option-gate']
const SKIP_RECENT_PARTS = new Set(['scripts', 'bin', 'schemas', 'fixtures', 'node_modules', 'generated', 'hooks', 'manifests'])
const QUALITY_RECORD_LAYERS = ['domain', 'spec', 'behavior', 'tests', 'decisions', 'ssot', 'planning', 'plans', 'handoff', 'questions']
const RECORD_QUALITY_CODES: RecordQualityCode[] = ['missing-index-header', 'missing-alias-or-search-key', 'missing-source-test-hints', 'missing-graph-link', 'missing-rule-digest']
const PROJECT_ARTIFACTS = [
  '.lazy-harness/project/profile.xml',
  '.lazy-harness/project/stack.xml',
  '.lazy-harness/project/filesystem.xml',
  '.lazy-harness/project/feature-navigation.xml',
  '.lazy-harness/tests/test-strategy.xml',
]

function parseArgs(argv: string[]): Args {
  const args: Args = {
    root: process.env.LAZY_HOST_ROOT || process.cwd(),
    source: process.env.LAZY_FRAMEWORK_SOURCE,
    format: 'md',
    recent: 20,
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = argv[i + 1]
    if ((arg === '--root' || arg === '--host') && next) {
      args.root = next
      i += 1
    } else if (arg.startsWith('--root=')) {
      args.root = arg.slice('--root='.length)
    } else if (arg.startsWith('--host=')) {
      args.root = arg.slice('--host='.length)
    } else if (arg === '--source' && next) {
      args.source = next
      i += 1
    } else if (arg.startsWith('--source=')) {
      args.source = arg.slice('--source='.length)
    } else if (arg === '--format' && next) {
      if (next !== 'json' && next !== 'md' && next !== 'markdown') throw new Error(`Unsupported --format: ${next}`)
      args.format = next === 'markdown' ? 'md' : next
      i += 1
    } else if (arg.startsWith('--format=')) {
      const value = arg.slice('--format='.length)
      if (value !== 'json' && value !== 'md' && value !== 'markdown') throw new Error(`Unsupported --format: ${value}`)
      args.format = value === 'markdown' ? 'md' : value
    } else if (arg === '--recent' && next) {
      args.recent = Number(next)
      i += 1
    } else if (arg.startsWith('--recent=')) {
      args.recent = Number(arg.slice('--recent='.length))
    } else if (arg === '--help' || arg === '-h') {
      printHelp()
      process.exit(0)
    } else {
      throw new Error(`Unknown argument: ${arg}`)
    }
  }
  args.root = resolve(args.root)
  if (args.source) args.source = resolve(args.source)
  else args.source = defaultSource(args.root)
  if (!Number.isFinite(args.recent) || args.recent < 0) args.recent = 20
  return args
}

function printHelp(): void {
  console.log(`Record Audit\n\nUsage:\n  bun .lazy-harness/scripts/record-audit.ts [--format md|json] [--root <host>] [--source <framework>] [--recent 20]\n  .lazy-harness/bin/lazy record-audit [--format md|json]\n\nRead-only dashboard for accumulated lazy-harness records. The optional --source points at the canonical lazy-harness source checkout or its .lazy-harness directory, allowing host-owned/changed counts to exclude framework sync files.`)
}

function defaultSource(root: string): string | undefined {
  const candidates = [
    process.env.LAZY_SOURCE_ROOT,
    join(homedir(), 'dev', 'lazy-harness'),
    join(homedir(), 'dev', 'lazy-harness', '.lazy-harness'),
  ].filter(Boolean) as string[]
  for (const candidate of candidates) {
    const lazy = candidate.endsWith('.lazy-harness') ? candidate : join(candidate, '.lazy-harness')
    if (existsSync(lazy) && resolve(lazy) !== resolve(join(root, '.lazy-harness'))) return lazy
  }
  return undefined
}

function lazyDir(path: string): string {
  return path.endsWith('.lazy-harness') ? path : join(path, '.lazy-harness')
}

function sourceIsHost(root: string, source: string | undefined): boolean {
  if (!source) return false
  return resolve(lazyDir(source)) === resolve(join(root, '.lazy-harness'))
}

function walkFiles(dir: string): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  const stack = [dir]
  while (stack.length > 0) {
    const current = stack.pop()!
    for (const entry of readdirSync(current, { withFileTypes: true })) {
      const p = join(current, entry.name)
      if (entry.isDirectory()) stack.push(p)
      else if (entry.isFile()) out.push(p)
    }
  }
  return out
}

function sha(path: string): string {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function relFromLazy(root: string, file: string): string {
  return relative(join(root, '.lazy-harness'), file).replaceAll('\\', '/')
}

function text(path: string): string {
  return readFileSync(path, 'utf8')
}

function safeText(path: string): string {
  try {
    return text(path)
  } catch {
    return ''
  }
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values.map((value) => value.trim()).filter(Boolean))).sort((a, b) => a.localeCompare(b))
}

function cleanMarkdownValue(value: string): string {
  return value
    .trim()
    .replace(/^[-*]\s+/, '')
    .replace(/`/g, '')
    .replace(/^['"]|['"]$/g, '')
    .trim()
}

function splitValues(value: string): string[] {
  const ticked = Array.from(value.matchAll(/`([^`]+)`/g)).map((match) => cleanMarkdownValue(match[1]))
  if (ticked.length) return unique(ticked)
  return unique(value.split(',').map(cleanMarkdownValue))
}

function findHeadingBlock(body: string, heading: RegExp): string[] | null {
  const lines = body.split(/\r?\n/)
  let inFence = false
  let start = -1
  for (let i = 0; i < lines.length; i += 1) {
    if (/^\s*```/.test(lines[i])) inFence = !inFence
    if (!inFence && heading.test(lines[i].trim())) { start = i; break }
  }
  if (start < 0) return null
  let end = lines.length
  inFence = false
  for (let i = start + 1; i < lines.length; i += 1) {
    if (/^\s*```/.test(lines[i])) inFence = !inFence
    if (!inFence && /^##\s+/.test(lines[i])) { end = i; break }
  }
  return lines.slice(start + 1, end)
}

function collectMarkdownListValues(lines: string[], labels: string[]): string[] {
  const values: string[] = []
  let current: string | null = null
  for (const raw of lines) {
    const line = raw.trimEnd()
    const label = line.match(/^\s*-\s+([^:]+):\s*(.*)$/)
    if (label && labels.some((item) => item.toLowerCase() === label[1].trim().toLowerCase())) {
      current = label[1].trim().toLowerCase()
      if (label[2].trim()) values.push(...splitValues(label[2]))
      continue
    }
    const nextTopLevel = line.match(/^\s*-\s+([^:]+):\s*$/)
    if (nextTopLevel && !labels.some((item) => item.toLowerCase() === nextTopLevel[1].trim().toLowerCase())) current = null
    const bullet = line.match(/^\s{2,}-\s+(.+)$/)
    if (current && bullet) values.push(...splitValues(bullet[1]))
  }
  return unique(values)
}

function collectImplementationHintValues(lines: string[], labels: string[]): string[] {
  const values: string[] = []
  let inImplementationHints = false
  for (const raw of lines) {
    const line = raw.trimEnd()
    if (/^\s*-\s+Implementation hints:\s*$/i.test(line)) {
      inImplementationHints = true
      continue
    }
    const topLevel = line.match(/^\s*-\s+([^:]+):\s*$/)
    if (topLevel && !/^Implementation hints$/i.test(topLevel[1].trim())) inImplementationHints = false
    if (!inImplementationHints) continue
    const hint = line.match(/^\s{2,}-\s+([^:]+):\s*(.+)$/)
    if (hint && labels.some((item) => item.toLowerCase() === hint[1].trim().toLowerCase())) values.push(...splitValues(hint[2]))
  }
  return unique(values)
}

function implementationMapHints(body: string): { sourceHints: string[]; testHints: string[] } {
  const block = findHeadingBlock(body, /^##\s+Implementation map\s*$/i)
  if (!block) return { sourceHints: [], testHints: [] }
  const sourceHints: string[] = []
  const testHints: string[] = []
  const content = block.join('\n')
  const candidates = [
    ...Array.from(content.matchAll(/`([^`]+)`/g)).map((match) => match[1]),
    ...Array.from(content.matchAll(/(?:^|\s)((?:src|app|packages|components|tests|test|__tests__|\.lazy-harness)\/[A-Za-z0-9_./*-]+)/g)).map((match) => match[1]),
  ].map(cleanMarkdownValue)
  for (const candidate of candidates) {
    if (!candidate || candidate.includes(' ')) continue
    if (/test|spec|__tests__/.test(candidate)) testHints.push(candidate)
    else if (/^(\.lazy-harness|src|app|packages|components)\//.test(candidate) || /\.[A-Za-z0-9]+$/.test(candidate)) sourceHints.push(candidate)
  }
  return { sourceHints: unique(sourceHints), testHints: unique(testHints) }
}

function qualityRecordFiles(root: string): string[] {
  const files: string[] = []
  for (const layer of QUALITY_RECORD_LAYERS) {
    for (const file of walkFiles(join(root, '.lazy-harness', layer))) {
      if (file.endsWith('.md') && !file.endsWith('/README.md')) files.push(file)
    }
  }
  return files.sort((a, b) => a.localeCompare(b))
}

function rowStrings(value: unknown): string[] {
  if (typeof value === 'string') return [value]
  if (Array.isArray(value)) return value.flatMap(rowStrings)
  if (value && typeof value === 'object') return Object.values(value as Record<string, unknown>).flatMap(rowStrings)
  return []
}

function graphRows(root: string): Array<Record<string, unknown>> {
  const graphPath = join(root, '.lazy-harness', 'knowledge', 'graph.jsonl')
  if (!existsSync(graphPath)) return []
  const rows: Array<Record<string, unknown>> = []
  for (const line of safeText(graphPath).split(/\r?\n/)) {
    if (!line.trim()) continue
    try { rows.push(JSON.parse(line) as Record<string, unknown>) } catch { /* graph hygiene reports invalid rows elsewhere */ }
  }
  return rows
}

function graphRelatesTo(row: Record<string, unknown>, recordPath: string): boolean {
  return rowStrings(row).some((value) => cleanMarkdownValue(value) === recordPath)
}

function recordQualitySummary(root: string): RecordQualitySummary {
  const counts: Record<RecordQualityCode, number> = {
    'missing-index-header': 0,
    'missing-alias-or-search-key': 0,
    'missing-source-test-hints': 0,
    'missing-graph-link': 0,
    'missing-rule-digest': 0,
  }
  const samples: Record<RecordQualityCode, string[]> = {
    'missing-index-header': [],
    'missing-alias-or-search-key': [],
    'missing-source-test-hints': [],
    'missing-graph-link': [],
    'missing-rule-digest': [],
  }
  const rows = graphRows(root)
  let completeRecords = 0
  const add = (code: RecordQualityCode, recordPath: string): void => {
    counts[code] += 1
    if (samples[code].length < 12) samples[code].push(recordPath)
  }
  const files = qualityRecordFiles(root)
  for (const file of files) {
    const recordPath = `.lazy-harness/${relFromLazy(root, file)}`
    const body = safeText(file)
    const indexHeader = findHeadingBlock(body, /^##\s+Index header\s*$/i)
    const ruleDigest = findHeadingBlock(body, /^##\s+Rule digest\s*$/i)
    const mapHints = implementationMapHints(body)

    const aliasesOrSearchKeys = unique([
      ...(indexHeader ? collectMarkdownListValues(indexHeader, ['Primary aliases', 'Search keys', 'Surface terms']) : []),
      ...(ruleDigest ? collectMarkdownListValues(ruleDigest, ['Aliases', 'Surface terms']) : []),
    ])
    const sourceHints = unique([
      ...(indexHeader ? collectMarkdownListValues(indexHeader, ['Source files']) : []),
      ...(ruleDigest ? collectImplementationHintValues(ruleDigest, ['Files', 'Source files']) : []),
      ...mapHints.sourceHints,
    ])
    const testHints = unique([
      ...(indexHeader ? collectMarkdownListValues(indexHeader, ['Test files']) : []),
      ...(ruleDigest ? collectImplementationHintValues(ruleDigest, ['Tests', 'Test files']) : []),
      ...mapHints.testHints,
    ])
    const graphIds = indexHeader ? collectMarkdownListValues(indexHeader, ['Graph ids']) : []
    const hasGraphLink = graphIds.length > 0 || rows.some((row) => graphRelatesTo(row, recordPath))

    const missing: RecordQualityCode[] = []
    if (!indexHeader) missing.push('missing-index-header')
    if (aliasesOrSearchKeys.length === 0) missing.push('missing-alias-or-search-key')
    if (sourceHints.length === 0 || testHints.length === 0) missing.push('missing-source-test-hints')
    if (!hasGraphLink) missing.push('missing-graph-link')
    const isCanonicalReusable = /^\.lazy-harness\/(domain|spec|behavior|tests|decisions|ssot)\//.test(recordPath) && !recordPath.toLowerCase().endsWith('/readme.md')
    if (isCanonicalReusable && !ruleDigest) missing.push('missing-rule-digest')
    if (missing.length === 0) completeRecords += 1
    else for (const code of missing) add(code, recordPath)
  }
  return {
    advisoryOnly: true,
    inspectedRecords: files.length,
    completeRecords,
    counts,
    issues: RECORD_QUALITY_CODES.map((code) => ({ code, count: counts[code], samplePaths: samples[code] })).filter((issue) => issue.count > 0),
  }
}

function layerSummaries(root: string): LayerSummary[] {
  return LAYERS.map((layer) => {
    const files = walkFiles(join(root, '.lazy-harness', layer))
    return { layer, files: files.length, bytes: files.reduce((sum, f) => sum + statSync(f).size, 0) }
  }).filter((layer) => layer.files > 0)
}

function compareHost(root: string, source: string | undefined): { layers: HostComparisonLayer[]; totals: { unique: number; changed: number; same: number } } {
  if (!source) return { layers: [], totals: { unique: 0, changed: 0, same: 0 } }
  const sourceLazy = lazyDir(source)
  const layers: HostComparisonLayer[] = []
  let unique = 0
  let changed = 0
  let same = 0
  for (const layer of COMPARE_LAYERS) {
    let layerUnique = 0
    let layerChanged = 0
    let layerSame = 0
    for (const file of walkFiles(join(root, '.lazy-harness', layer))) {
      const rel = relFromLazy(root, file)
      const sourceFile = join(sourceLazy, rel)
      if (!existsSync(sourceFile)) {
        layerUnique += 1
      } else if (sha(file) !== sha(sourceFile)) {
        layerChanged += 1
      } else {
        layerSame += 1
      }
    }
    unique += layerUnique
    changed += layerChanged
    same += layerSame
    if (layerUnique || layerChanged || layerSame) {
      layers.push({ layer, unique: layerUnique, changed: layerChanged, same: layerSame, totalOwnedOrChanged: layerUnique + layerChanged })
    }
  }
  return { layers, totals: { unique, changed, same } }
}

function jsonlSummaries(root: string): JsonlSummary[] {
  const files = [...walkFiles(join(root, '.lazy-harness', 'knowledge')), ...walkFiles(join(root, '.lazy-harness', 'logs'))]
    .filter((file) => file.endsWith('.jsonl'))
    .sort()
  return files.map((file) => {
    const rel = `.lazy-harness/${relFromLazy(root, file)}`
    let lines = 0
    let invalid = 0
    for (const line of safeText(file).split(/\r?\n/)) {
      if (!line.trim()) continue
      lines += 1
      try { JSON.parse(line) } catch { invalid += 1 }
    }
    return { path: rel, lines, invalid }
  })
}

function markerSummaries(root: string): MarkerSummary[] {
  const files = walkFiles(join(root, '.lazy-harness')).filter((file) => ['.md', '.xml', '.jsonl', '.json'].some((ext) => file.endsWith(ext)))
  return MARKERS.map((marker) => {
    const hits: string[] = []
    for (const file of files) {
      if (safeText(file).includes(marker)) hits.push(`.lazy-harness/${relFromLazy(root, file)}`)
    }
    return { marker, files: hits.length, samplePaths: hits.slice(0, 12) }
  })
}

function projectProfileSummary(root: string): ProjectProfileSummary {
  const present = PROJECT_ARTIFACTS.filter((path) => existsSync(join(root, path))).length
  const projectDir = join(root, '.lazy-harness', 'project')
  const files = [...walkFiles(projectDir).filter((file) => file.endsWith('.xml'))]
  const testStrategy = join(root, '.lazy-harness', 'tests', 'test-strategy.xml')
  if (existsSync(testStrategy)) files.push(testStrategy)
  const projectFiles = files.sort().map((file) => {
    const content = safeText(file)
    return {
      path: `.lazy-harness/${relFromLazy(root, file)}`,
      needsInterview: (content.match(/status="needs-interview"/g) || []).length,
      confirmed: (content.match(/status="confirmed"/g) || []).length,
      bytes: statSync(file).size,
    }
  })
  const needsInterviewFields = projectFiles.reduce((sum, file) => sum + file.needsInterview, 0)
  const confirmedFields = projectFiles.reduce((sum, file) => sum + file.confirmed, 0)
  return {
    artifactsPresent: present,
    artifactsMissing: PROJECT_ARTIFACTS.length - present,
    artifactsComplete: present === PROJECT_ARTIFACTS.length,
    needsInterviewFields,
    confirmedFields,
    answersComplete: present === PROJECT_ARTIFACTS.length && needsInterviewFields === 0,
    projectFiles,
  }
}

function pathCandidatesFromGraphRow(row: Record<string, unknown>): string[] {
  const raw = row.path ?? row.file ?? row.sourcePath ?? row.targetPath
  if (typeof raw === 'string') return [raw]
  if (Array.isArray(raw)) return raw.filter((item): item is string => typeof item === 'string')
  return []
}

function existsInSource(source: string | undefined, path: string): boolean {
  return Boolean(source && path.startsWith('.lazy-harness/') && existsSync(join(lazyDir(source), path.slice('.lazy-harness/'.length))))
}

function graphSummary(root: string, source: string | undefined): GraphSummary {
  const graphPath = join(root, '.lazy-harness', 'knowledge', 'graph.jsonl')
  if (!existsSync(graphPath)) return { rows: 0, invalidRows: 0, missingPaths: 0, sourceOnlyPaths: 0, commaJoinedPaths: 0, sampleMissingPaths: [], sampleSourceOnlyPaths: [], sampleCommaJoinedPaths: [] }
  let rows = 0
  let invalidRows = 0
  const missing: string[] = []
  const sourceOnly: string[] = []
  const comma: string[] = []
  for (const line of safeText(graphPath).split(/\r?\n/)) {
    if (!line.trim()) continue
    rows += 1
    let row: Record<string, unknown>
    try {
      row = JSON.parse(line) as Record<string, unknown>
    } catch {
      invalidRows += 1
      continue
    }
    for (const p of pathCandidatesFromGraphRow(row)) {
      if (p.includes(',')) comma.push(p)
      if (p.startsWith('.') && !existsSync(join(root, p))) {
        if (existsInSource(source, p)) sourceOnly.push(p)
        else missing.push(p)
      }
    }
  }
  return {
    rows,
    invalidRows,
    missingPaths: missing.length,
    sourceOnlyPaths: sourceOnly.length,
    commaJoinedPaths: comma.length,
    sampleMissingPaths: [...new Set(missing)].slice(0, 12),
    sampleSourceOnlyPaths: [...new Set(sourceOnly)].slice(0, 12),
    sampleCommaJoinedPaths: [...new Set(comma)].slice(0, 12),
  }
}

function recentFiles(root: string, limit: number): RecentFile[] {
  const files = walkFiles(join(root, '.lazy-harness')).filter((file) => {
    const parts = relFromLazy(root, file).split('/')
    return !parts.some((part) => SKIP_RECENT_PARTS.has(part))
  })
  return files
    .map((file) => ({ path: `.lazy-harness/${relFromLazy(root, file)}`, bytes: statSync(file).size, mtimeMs: statSync(file).mtimeMs, mtime: statSync(file).mtime.toISOString() }))
    .sort((a, b) => b.mtimeMs - a.mtimeMs)
    .slice(0, limit)
    .map(({ path, bytes, mtime }) => ({ path, bytes, mtime }))
}

function buildAudit(args: Args): AuditResult {
  const layers = layerSummaries(args.root)
  const comparison = compareHost(args.root, args.source)
  const jsonl = jsonlSummaries(args.root)
  const markers = markerSummaries(args.root)
  const projectProfile = projectProfileSummary(args.root)
  const graph = graphSummary(args.root, args.source)
  const recordQuality = recordQualitySummary(args.root)
  const warnings: string[] = []
  if (!args.source) warnings.push('No framework source was found; host-owned/changed counts are unavailable.')
  if (sourceIsHost(args.root, args.source)) warnings.push('The --source argument points at this host .lazy-harness tree. Use the canonical framework source checkout for installed-host readiness checks, e.g. --source /home/lazydino/dev/lazy-harness.')
  if (!projectProfile.answersComplete) warnings.push(`Project Profile incomplete: ${projectProfile.artifactsMissing} missing artifact(s), ${projectProfile.needsInterviewFields} field(s) still need interview answers.`)
  if (graph.invalidRows > 0 || graph.missingPaths > 0 || graph.commaJoinedPaths > 0) warnings.push('Implementation graph hygiene issues detected.')
  const invalidJsonl = jsonl.reduce((sum, item) => sum + item.invalid, 0)
  if (invalidJsonl > 0) warnings.push(`${invalidJsonl} invalid JSONL line(s) detected.`)
  const skipped = jsonl.find((item) => item.path.endsWith('/skipped.jsonl'))
  if (skipped && skipped.lines > 0) warnings.push(`Skipped workflow entries exist: ${skipped.lines}.`)
  for (const issue of recordQuality.issues) warnings.push(`Record quality advisory ${issue.code}: ${issue.count} historical record(s).`)
  return {
    ok: true,
    mode: 'record-audit.inspect',
    schemaVersion: '1.0',
    root: args.root,
    source: args.source ?? null,
    inspectedAt: new Date().toISOString(),
    layers,
    totals: {
      files: layers.reduce((sum, layer) => sum + layer.files, 0),
      bytes: layers.reduce((sum, layer) => sum + layer.bytes, 0),
      hostUnique: comparison.totals.unique,
      hostChanged: comparison.totals.changed,
      hostSameAsSource: comparison.totals.same,
      hostOwnedOrChanged: comparison.totals.unique + comparison.totals.changed,
    },
    hostComparison: comparison.layers,
    jsonl,
    markers,
    projectProfile,
    graph,
    recordQuality,
    recentFiles: recentFiles(args.root, args.recent),
    warnings,
    nextActions: [
      'Use hostOwnedOrChanged and layer counts to judge whether dogfooding is creating reusable host memory.',
      'Resolve Project Profile needs-interview fields through project-profile interview/fill.',
      'Fix graph hygiene before relying on graph paths for navigation.',
      'Use log line counts to decide whether summary/compaction is needed.',
    ],
  }
}

function renderMd(result: AuditResult): string {
  const lines: string[] = []
  lines.push('# Record audit')
  lines.push('')
  lines.push(`- Root: \`${result.root}\``)
  lines.push(`- Source: ${result.source ? `\`${result.source}\`` : 'not found'}`)
  lines.push(`- Total files: ${result.totals.files}`)
  lines.push(`- Host-owned/changed: ${result.totals.hostOwnedOrChanged} (unique ${result.totals.hostUnique}, changed ${result.totals.hostChanged}, same-as-source ${result.totals.hostSameAsSource})`)
  lines.push('')
  lines.push('## Layers')
  for (const layer of result.layers) lines.push(`- ${layer.layer}: files=${layer.files}, bytes=${layer.bytes}`)
  if (result.hostComparison.length) {
    lines.push('')
    lines.push('## Host comparison')
    for (const layer of result.hostComparison) lines.push(`- ${layer.layer}: unique=${layer.unique}, changed=${layer.changed}, same=${layer.same}, ownedOrChanged=${layer.totalOwnedOrChanged}`)
  }
  lines.push('')
  lines.push('## Project Profile')
  lines.push(`- artifactsComplete: ${result.projectProfile.artifactsComplete}`)
  lines.push(`- answersComplete: ${result.projectProfile.answersComplete}`)
  lines.push(`- needsInterviewFields: ${result.projectProfile.needsInterviewFields}`)
  lines.push(`- confirmedFields: ${result.projectProfile.confirmedFields}`)
  for (const file of result.projectProfile.projectFiles) lines.push(`  - ${file.path}: needsInterview=${file.needsInterview}, confirmed=${file.confirmed}`)
  lines.push('')
  lines.push('## Graph')
  lines.push(`- rows: ${result.graph.rows}`)
  lines.push(`- invalidRows: ${result.graph.invalidRows}`)
  lines.push(`- missingPaths: ${result.graph.missingPaths}`)
  lines.push(`- sourceOnlyPaths: ${result.graph.sourceOnlyPaths}`)
  lines.push(`- commaJoinedPaths: ${result.graph.commaJoinedPaths}`)
  lines.push('')
  lines.push('## Record quality')
  lines.push(`- advisoryOnly: ${result.recordQuality.advisoryOnly}`)
  lines.push(`- inspectedRecords: ${result.recordQuality.inspectedRecords}`)
  lines.push(`- completeRecords: ${result.recordQuality.completeRecords}`)
  for (const issue of result.recordQuality.issues) lines.push(`- ${issue.code}: count=${issue.count}, samples=${issue.samplePaths.join(', ')}`)
  lines.push('')
  lines.push('## JSONL')
  for (const item of result.jsonl) lines.push(`- ${item.path}: lines=${item.lines}, invalid=${item.invalid}`)
  lines.push('')
  lines.push('## Markers')
  for (const marker of result.markers) lines.push(`- ${marker.marker}: files=${marker.files}`)
  lines.push('')
  lines.push('## Recent files')
  for (const file of result.recentFiles) lines.push(`- ${file.bytes} bytes ${file.path}`)
  if (result.warnings.length) {
    lines.push('')
    lines.push('## Warnings')
    for (const warning of result.warnings) lines.push(`- ${warning}`)
  }
  lines.push('')
  lines.push('## Next actions')
  for (const action of result.nextActions) lines.push(`- ${action}`)
  return lines.join('\n')
}

try {
  const args = parseArgs(process.argv.slice(2))
  const result = buildAudit(args)
  if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
  else console.log(renderMd(result))
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error))
  process.exit(1)
}
