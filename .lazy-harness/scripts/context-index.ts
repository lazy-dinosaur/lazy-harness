#!/usr/bin/env bun
/**
 * context-index.ts — deterministic generated Context Delivery index.
 *
 * Canonical truth remains Markdown/XML records, knowledge graph JSONL, and
 * project profile files. This script builds a non-canonical cache at
 * .lazy-harness/generated/context-index.json for later Context Broker phases.
 */
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import * as path from 'node:path'

const LAYER_DIRS = {
  DDD: '.lazy-harness/domain',
  SDD: '.lazy-harness/spec',
  BDD: '.lazy-harness/behavior',
  TDD: '.lazy-harness/tests',
  ADR: '.lazy-harness/decisions',
  SSOT: '.lazy-harness/ssot',
  Planning: '.lazy-harness/planning',
} as const

type Layer = keyof typeof LAYER_DIRS
type DigestStatus = 'active' | 'advisory' | 'deprecated' | 'reverted' | 'needs-review'
type Scope = 'framework-global' | 'host-project' | 'team-policy' | 'layer-fact' | 'transient-plan' | 'jcode-local' | 'ambiguous'
type DigestSource = 'rule-digest' | 'fallback'
type Format = 'json' | 'md'

interface Args {
  root: string
  output: string
  write: boolean
  format: Format
}

interface ImplementationHints {
  routeHints: string[]
  componentHints: string[]
  fileHints: string[]
  symbolHints: string[]
  testHints: string[]
}

interface DigestInfo {
  status: DigestStatus
  layer: Layer
  scope: Scope
  digestSource: DigestSource
  appliesWhen: string[]
  must: string[]
  mustNot: string[]
  bullets: string[]
  recordCompletion?: string
  relatedRecords: string[]
  aliases: string[]
  surfaceTerms: string[]
  implementationHints: ImplementationHints
  sourceRange?: { startLine: number; endLine: number }
}

interface GraphHint {
  id: string
  relation?: string
  source?: string
  target?: string
  path?: string
}

interface RecordEntry {
  recordPath: string
  title: string
  layer: Layer
  status: DigestStatus
  scope: Scope
  digestSource: DigestSource
  digest: {
    appliesWhen: string[]
    must: string[]
    mustNot: string[]
    bullets: string[]
    recordCompletion?: string
    relatedRecords: string[]
    sourceRange?: { startLine: number; endLine: number }
  }
  aliases: string[]
  surfaceTerms: string[]
  implementationHints: ImplementationHints
  graphIds: string[]
  graphHints: GraphHint[]
  projectProfileFeatureIds: string[]
  updatedAt?: string
}

interface AliasEntry {
  value: string
  lang?: string
}

interface FeatureRecordRef {
  path: string
  layer?: Layer
}

interface FeatureEntry {
  id: string
  status: string
  label: string
  aliases: AliasEntry[]
  routes: string[]
  components: string[]
  records: FeatureRecordRef[]
  sourceFiles: string[]
  tests: string[]
}

interface GraphRow {
  id?: string
  relation?: string
  type?: string
  source?: string
  target?: string
  path?: string
  [key: string]: unknown
}

interface ContextIndex {
  schemaVersion: '1.0'
  generatedAt: string
  fingerprint: string
  source: {
    root: string
    method: 'context-index-v1'
    tool: string
    canonicalInputs: string[]
  }
  records: RecordEntry[]
  projectProfile: {
    featureNavigationPath: string | null
    features: FeatureEntry[]
  }
  graph: {
    graphPath: string | null
    rows: number
    invalidRows: number
  }
}

function usage(): never {
  console.error(`Usage: context-index [options]

Options:
  --root DIR              Host root (default: LAZY_HOST_ROOT or cwd)
  --output PATH           Output path (default: .lazy-harness/generated/context-index.json)
  --write                 Write output file instead of printing to stdout
  --format json|md        Output format when not writing (default json)
  --help                  Show this help

Examples:
  bun .lazy-harness/scripts/context-index.ts --root . --format json
  .lazy-harness/bin/lazy context-index --write
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
    output: '',
    write: false,
    format: 'json',
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    let parsed = valueFor(argv, i, '--root')
    if (parsed.value !== null) { args.root = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--output')
    if (parsed.value !== null) { args.output = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--format')
    if (parsed.value !== null) {
      if (parsed.value !== 'json' && parsed.value !== 'md' && parsed.value !== 'markdown') usage()
      args.format = parsed.value === 'markdown' ? 'md' : parsed.value
      i += parsed.consumed
      continue
    }
    if (arg === '--write') args.write = true
    else if (arg === '--help' || arg === '-h') usage()
    else usage()
  }
  args.root = path.resolve(args.root)
  if (!args.output) args.output = path.join(args.root, '.lazy-harness', 'generated', 'context-index.json')
  else args.output = path.resolve(args.output)
  return args
}

function rel(root: string, filePath: string): string {
  return path.relative(root, filePath).split(path.sep).join('/')
}

function normalizePath(value: string): string {
  return value.trim().replace(/^[`'"\s]+|[`'"\s]+$/g, '').split(path.sep).join('/')
}

function uniqueSorted(values: Array<string | undefined | null>): string[] {
  return Array.from(new Set(values.map((v) => (v || '').trim()).filter(Boolean))).sort((a, b) => a.localeCompare(b))
}

function emptyHints(): ImplementationHints {
  return { routeHints: [], componentHints: [], fileHints: [], symbolHints: [], testHints: [] }
}

function mergeHints(target: ImplementationHints, source: Partial<ImplementationHints>): void {
  target.routeHints = uniqueSorted([...target.routeHints, ...(source.routeHints || [])])
  target.componentHints = uniqueSorted([...target.componentHints, ...(source.componentHints || [])])
  target.fileHints = uniqueSorted([...target.fileHints, ...(source.fileHints || [])])
  target.symbolHints = uniqueSorted([...target.symbolHints, ...(source.symbolHints || [])])
  target.testHints = uniqueSorted([...target.testHints, ...(source.testHints || [])])
}

function walkRecordFiles(dir: string): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  for (const entry of readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) out.push(...walkRecordFiles(full))
    else if (entry.isFile() && entry.name !== 'README.md' && /\.(md|xml)$/i.test(entry.name)) out.push(full)
  }
  return out.sort((a, b) => a.localeCompare(b))
}

function layerForPath(recordPath: string): Layer | undefined {
  for (const [layer, dir] of Object.entries(LAYER_DIRS) as Array<[Layer, string]>) {
    if (recordPath === dir || recordPath.startsWith(`${dir}/`)) return layer
  }
  return undefined
}

function normalizeStatus(value: string | undefined): DigestStatus {
  const v = (value || 'active').trim().toLowerCase()
  if (['active', 'advisory', 'deprecated', 'reverted', 'needs-review'].includes(v)) return v as DigestStatus
  return 'active'
}

function normalizeLayer(value: string | undefined, fallback: Layer): Layer {
  const v = (value || '').trim()
  if (v in LAYER_DIRS) return v as Layer
  return fallback
}

function normalizeScope(value: string | undefined, fallback: Scope): Scope {
  const v = (value || '').trim()
  const allowed: Scope[] = ['framework-global', 'host-project', 'team-policy', 'layer-fact', 'transient-plan', 'jcode-local', 'ambiguous']
  return allowed.includes(v as Scope) ? v as Scope : fallback
}

function titleFromBody(body: string, recordPath: string): string {
  const heading = body.split(/\r?\n/).find((line) => /^#\s+/.test(line))
  if (heading) return heading.replace(/^#\s+/, '').trim()
  return path.basename(recordPath).replace(/\.[^.]+$/, '')
}

function findHeadingBlock(body: string, heading: RegExp): { lines: string[]; startLine: number; endLine: number } | null {
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
  return { lines: lines.slice(start + 1, end), startLine: start + 1, endLine: end }
}

function cleanMarkdownValue(value: string): string {
  return value
    .trim()
    .replace(/^[-*]\s+/, '')
    .replace(/`/g, '')
    .replace(/^['"]|['"]$/g, '')
    .trim()
}

function splitHintValues(value: string): string[] {
  const ticked = Array.from(value.matchAll(/`([^`]+)`/g)).map((m) => cleanMarkdownValue(m[1]))
  if (ticked.length) return uniqueSorted(ticked)
  return uniqueSorted(value.split(',').map(cleanMarkdownValue))
}

function addHint(hints: ImplementationHints, kind: string, values: string[]): void {
  const k = kind.toLowerCase()
  if (/^routes?$/.test(k)) hints.routeHints = uniqueSorted([...hints.routeHints, ...values])
  else if (/^components?$/.test(k)) hints.componentHints = uniqueSorted([...hints.componentHints, ...values])
  else if (/^files?$/.test(k)) hints.fileHints = uniqueSorted([...hints.fileHints, ...values])
  else if (/^symbols?$/.test(k)) hints.symbolHints = uniqueSorted([...hints.symbolHints, ...values])
  else if (/^tests?$/.test(k)) hints.testHints = uniqueSorted([...hints.testHints, ...values])
}

function parseDigest(body: string, layer: Layer): DigestInfo {
  const block = findHeadingBlock(body, /^##\s+Rule digest\s*$/i)
  const fallbackScope: Scope = layer === 'Planning' ? 'transient-plan' : 'layer-fact'
  if (!block) {
    const preview = body.split(/\r?\n/).map((line) => line.trim()).filter((line) => line && !line.startsWith('#')).slice(0, 2)
    return {
      status: 'active',
      layer,
      scope: fallbackScope,
      digestSource: 'fallback',
      appliesWhen: [],
      must: [],
      mustNot: [],
      bullets: preview,
      relatedRecords: [],
      aliases: [],
      surfaceTerms: [],
      implementationHints: emptyHints(),
    }
  }

  let status: DigestStatus = 'active'
  let digestLayer: Layer = layer
  let scope: Scope = fallbackScope
  let recordCompletion = ''
  const appliesWhen: string[] = []
  const must: string[] = []
  const mustNot: string[] = []
  const relatedRecords: string[] = []
  const aliases: string[] = []
  const surfaceTerms: string[] = []
  const implementationHints = emptyHints()
  let current: 'appliesWhen' | 'must' | 'mustNot' | 'relatedRecords' | 'recordCompletion' | 'aliases' | 'surfaceTerms' | 'implementationHints' | null = null

  for (const raw of block.lines) {
    const line = raw.trimEnd()
    const field = line.match(/^\s*-\s+(Status|Layer|Scope|Record completion):\s*(.*)$/i)
    if (field) {
      const key = field[1].toLowerCase()
      const value = field[2].trim()
      current = null
      if (key === 'status') status = normalizeStatus(value)
      else if (key === 'layer') digestLayer = normalizeLayer(value, layer)
      else if (key === 'scope') scope = normalizeScope(value, scope)
      else if (key === 'record completion') {
        current = 'recordCompletion'
        if (value) recordCompletion = cleanMarkdownValue(value)
      }
      continue
    }
    const collection = line.match(/^\s*-\s+(Applies when|Must|Must not|Related records|Aliases|Surface terms|Implementation hints):\s*$/i)
    if (collection) {
      const key = collection[1].toLowerCase()
      if (key === 'applies when') current = 'appliesWhen'
      else if (key === 'must') current = 'must'
      else if (key === 'must not') current = 'mustNot'
      else if (key === 'related records') current = 'relatedRecords'
      else if (key === 'aliases') current = 'aliases'
      else if (key === 'surface terms') current = 'surfaceTerms'
      else if (key === 'implementation hints') current = 'implementationHints'
      continue
    }
    const item = line.match(/^\s*-\s+(.+)$/)
    if (!item || !current) continue
    const value = cleanMarkdownValue(item[1])
    if (!value) continue
    if (current === 'appliesWhen') appliesWhen.push(value)
    else if (current === 'must') must.push(value)
    else if (current === 'mustNot') mustNot.push(value)
    else if (current === 'relatedRecords') relatedRecords.push(value)
    else if (current === 'recordCompletion') recordCompletion = recordCompletion ? `${recordCompletion}; ${value}` : value
    else if (current === 'aliases') aliases.push(value)
    else if (current === 'surfaceTerms') surfaceTerms.push(value)
    else if (current === 'implementationHints') {
      const hint = value.match(/^(Routes?|Components?|Files?|Symbols?|Tests?):\s*(.+)$/i)
      if (hint) addHint(implementationHints, hint[1], splitHintValues(hint[2]))
    }
  }

  const bullets = [...must, ...mustNot.map((b) => `Do not: ${b}`)].slice(0, 5)
  return {
    status,
    layer: digestLayer,
    scope,
    digestSource: 'rule-digest',
    appliesWhen: uniqueSorted(appliesWhen),
    must: uniqueSorted(must),
    mustNot: uniqueSorted(mustNot),
    bullets: bullets.length ? uniqueSorted(bullets) : uniqueSorted(appliesWhen).slice(0, 3),
    recordCompletion: recordCompletion || undefined,
    relatedRecords: uniqueSorted(relatedRecords),
    aliases: uniqueSorted(aliases),
    surfaceTerms: uniqueSorted(surfaceTerms),
    implementationHints,
    sourceRange: { startLine: block.startLine, endLine: block.endLine },
  }
}

function isPathLike(value: string): boolean {
  return /^(\.lazy-harness|src|app|packages|components|tests|test|__tests__)\//.test(value) || /\.[A-Za-z0-9]+$/.test(value)
}

function classifyHint(value: string, hints: ImplementationHints): void {
  const normalized = normalizePath(value)
  if (!normalized) return
  if (normalized.startsWith('/') && !normalized.startsWith('//')) hints.routeHints = uniqueSorted([...hints.routeHints, normalized])
  else if (/test|spec|__tests__/.test(normalized)) hints.testHints = uniqueSorted([...hints.testHints, normalized])
  else if (isPathLike(normalized)) hints.fileHints = uniqueSorted([...hints.fileHints, normalized])
  else if (/^[A-Z][A-Za-z0-9_.$-]+$/.test(normalized)) hints.componentHints = uniqueSorted([...hints.componentHints, normalized])
}

function extractImplementationMapHints(body: string): ImplementationHints {
  const hints = emptyHints()
  const block = findHeadingBlock(body, /^##\s+Implementation map\s*$/i)
  if (!block) return hints
  const text = block.lines.join('\n')
  for (const match of text.matchAll(/`([^`]+)`/g)) classifyHint(match[1], hints)
  for (const match of text.matchAll(/(?:^|\s)((?:src|app|packages|components|tests|test|__tests__)\/[A-Za-z0-9_./*-]+)/g)) classifyHint(match[1], hints)
  return hints
}

function buildRecordEntries(root: string): RecordEntry[] {
  const records: RecordEntry[] = []
  for (const [layer, dir] of Object.entries(LAYER_DIRS) as Array<[Layer, string]>) {
    for (const file of walkRecordFiles(path.join(root, dir))) {
      let body = ''
      try { body = readFileSync(file, 'utf8') } catch { continue }
      const recordPath = rel(root, file)
      const actualLayer = layerForPath(recordPath) || layer
      const digest = parseDigest(body, actualLayer)
      const implementationMapHints = extractImplementationMapHints(body)
      mergeHints(digest.implementationHints, implementationMapHints)
      records.push({
        recordPath,
        title: titleFromBody(body, recordPath),
        layer: digest.layer,
        status: digest.status,
        scope: digest.scope,
        digestSource: digest.digestSource,
        digest: {
          appliesWhen: digest.appliesWhen,
          must: digest.must,
          mustNot: digest.mustNot,
          bullets: digest.bullets,
          ...(digest.recordCompletion ? { recordCompletion: digest.recordCompletion } : {}),
          relatedRecords: digest.relatedRecords,
          ...(digest.sourceRange ? { sourceRange: digest.sourceRange } : {}),
        },
        aliases: digest.aliases,
        surfaceTerms: digest.surfaceTerms,
        implementationHints: digest.implementationHints,
        graphIds: [],
        graphHints: [],
        projectProfileFeatureIds: [],
      })
    }
  }
  return records.sort((a, b) => a.recordPath.localeCompare(b.recordPath))
}

function attr(attrs: string, name: string): string | undefined {
  const match = attrs.match(new RegExp(`${name}=["']([^"']+)["']`))
  return match?.[1]
}

function textValues(body: string, tag: string): string[] {
  const out: string[] = []
  const re = new RegExp(`<${tag}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${tag}>`, 'g')
  for (const match of body.matchAll(re)) out.push(cleanXml(match[1]))
  return uniqueSorted(out)
}

function sectionTextValues(body: string, sectionTag: string, itemTag: string): string[] {
  const values: string[] = []
  const sectionRe = new RegExp(`<${sectionTag}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${sectionTag}>`, 'g')
  for (const section of body.matchAll(sectionRe)) values.push(...textValues(section[1], itemTag))
  return uniqueSorted(values)
}

function cleanXml(value: string): string {
  return value.replace(/<[^>]+>/g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').trim()
}

function parseFeatureNavigation(root: string): { path: string | null; features: FeatureEntry[] } {
  const featurePath = path.join(root, '.lazy-harness', 'project', 'feature-navigation.xml')
  if (!existsSync(featurePath)) return { path: null, features: [] }
  let xml = ''
  try { xml = readFileSync(featurePath, 'utf8') } catch { return { path: rel(root, featurePath), features: [] } }
  const features: FeatureEntry[] = []
  const featureRe = /<feature\b([^>]*)>([\s\S]*?)<\/feature>/g
  for (const match of xml.matchAll(featureRe)) {
    const attrs = match[1]
    const body = match[2]
    const aliases: AliasEntry[] = []
    for (const aliasMatch of body.matchAll(/<alias\b([^>]*)>([\s\S]*?)<\/alias>/g)) {
      const value = cleanXml(aliasMatch[2])
      if (value) aliases.push({ value, ...(attr(aliasMatch[1], 'lang') ? { lang: attr(aliasMatch[1], 'lang') } : {}) })
    }
    const records: FeatureRecordRef[] = []
    for (const recordMatch of body.matchAll(/<record\b([^>]*)>([\s\S]*?)<\/record>/g)) {
      const value = cleanXml(recordMatch[2])
      if (!value) continue
      const layer = attr(recordMatch[1], 'layer')
      records.push({ path: value, ...(layer && layer in LAYER_DIRS ? { layer: layer as Layer } : {}) })
    }
    features.push({
      id: attr(attrs, 'id') || `feature-${features.length + 1}`,
      status: attr(attrs, 'status') || 'unknown',
      label: textValues(body, 'label')[0] || '',
      aliases: aliases.sort((a, b) => a.value.localeCompare(b.value)),
      routes: textValues(body, 'route'),
      components: textValues(body, 'component'),
      records: records.sort((a, b) => a.path.localeCompare(b.path)),
      sourceFiles: sectionTextValues(body, 'sourceFiles', 'path'),
      tests: sectionTextValues(body, 'tests', 'path'),
    })
  }
  for (const feature of features) {
    feature.sourceFiles = uniqueSorted(feature.sourceFiles)
    feature.tests = uniqueSorted(feature.tests)
  }
  return { path: rel(root, featurePath), features: features.sort((a, b) => a.id.localeCompare(b.id)) }
}

function mergeProjectProfile(records: RecordEntry[], profile: { features: FeatureEntry[] }): void {
  const byPath = new Map(records.map((record) => [record.recordPath, record]))
  for (const feature of profile.features) {
    const aliasValues = feature.aliases.map((alias) => alias.value)
    for (const recordRef of feature.records) {
      const record = byPath.get(recordRef.path)
      if (!record) continue
      record.projectProfileFeatureIds = uniqueSorted([...record.projectProfileFeatureIds, feature.id])
      record.aliases = uniqueSorted([...record.aliases, ...aliasValues, feature.label])
      record.surfaceTerms = uniqueSorted([...record.surfaceTerms, ...aliasValues])
      mergeHints(record.implementationHints, {
        routeHints: feature.routes,
        componentHints: feature.components,
        fileHints: feature.sourceFiles,
        testHints: feature.tests,
      })
    }
  }
}

function parseGraph(root: string): { path: string | null; rows: GraphRow[]; invalidRows: number } {
  const graphPath = path.join(root, '.lazy-harness', 'knowledge', 'graph.jsonl')
  if (!existsSync(graphPath)) return { path: null, rows: [], invalidRows: 0 }
  const rows: GraphRow[] = []
  let invalidRows = 0
  for (const line of readFileSync(graphPath, 'utf8').split(/\r?\n/)) {
    if (!line.trim()) continue
    try { rows.push(JSON.parse(line) as GraphRow) } catch { invalidRows += 1 }
  }
  rows.sort((a, b) => String(a.id || '').localeCompare(String(b.id || '')))
  return { path: rel(root, graphPath), rows, invalidRows }
}

function graphRelatesTo(row: GraphRow, recordPath: string): boolean {
  return [row.path, row.source, row.target, row.sourcePath, row.targetPath]
    .filter((v): v is string => typeof v === 'string')
    .some((value) => normalizePath(value) === recordPath)
}

function mergeGraph(records: RecordEntry[], graphRows: GraphRow[]): void {
  for (const record of records) {
    for (const row of graphRows) {
      if (!row.id || !graphRelatesTo(row, record.recordPath)) continue
      record.graphIds = uniqueSorted([...record.graphIds, row.id])
      const hint: GraphHint = {
        id: row.id,
        ...(typeof row.relation === 'string' ? { relation: row.relation } : {}),
        ...(typeof row.type === 'string' ? { relation: row.type } : {}),
        ...(typeof row.source === 'string' ? { source: row.source } : {}),
        ...(typeof row.target === 'string' ? { target: row.target } : {}),
        ...(typeof row.path === 'string' ? { path: row.path } : {}),
      }
      record.graphHints.push(hint)
      for (const value of [row.path, row.source, row.target, row.sourcePath, row.targetPath]) {
        if (typeof value === 'string' && normalizePath(value) !== record.recordPath) classifyHint(value, record.implementationHints)
      }
    }
    record.graphHints.sort((a, b) => a.id.localeCompare(b.id))
  }
}

function canonicalInputs(root: string): string[] {
  return uniqueSorted([
    ...Object.values(LAYER_DIRS),
    '.lazy-harness/project/feature-navigation.xml',
    '.lazy-harness/knowledge/graph.jsonl',
  ].filter((p) => existsSync(path.join(root, p))))
}

function buildContextIndex(root: string): ContextIndex {
  const records = buildRecordEntries(root)
  const profile = parseFeatureNavigation(root)
  mergeProjectProfile(records, profile)
  const graph = parseGraph(root)
  mergeGraph(records, graph.rows)

  for (const record of records) {
    record.aliases = uniqueSorted(record.aliases)
    record.surfaceTerms = uniqueSorted(record.surfaceTerms)
    record.projectProfileFeatureIds = uniqueSorted(record.projectProfileFeatureIds)
    mergeHints(record.implementationHints, {})
  }

  const source = {
    root,
    method: 'context-index-v1' as const,
    tool: '.lazy-harness/scripts/context-index.ts',
    canonicalInputs: canonicalInputs(root),
  }
  const contentForHash = { source, records, projectProfile: { featureNavigationPath: profile.path, features: profile.features }, graph: { graphPath: graph.path, rows: graph.rows.length, invalidRows: graph.invalidRows } }
  const fingerprint = createHash('sha256').update(JSON.stringify(contentForHash)).digest('hex').slice(0, 16)
  return {
    schemaVersion: '1.0',
    generatedAt: '1970-01-01T00:00:00.000Z',
    fingerprint,
    source,
    records,
    projectProfile: { featureNavigationPath: profile.path, features: profile.features },
    graph: { graphPath: graph.path, rows: graph.rows.length, invalidRows: graph.invalidRows },
  }
}

function renderMarkdown(index: ContextIndex): string {
  const aliasRecords = index.records.filter((record) => record.aliases.length || record.surfaceTerms.length || record.projectProfileFeatureIds.length)
  const lines = [
    'Context index',
    `- fingerprint: ${index.fingerprint}`,
    `- records: ${index.records.length}`,
    `- project profile features: ${index.projectProfile.features.length}`,
    `- graph rows: ${index.graph.rows} (invalid: ${index.graph.invalidRows})`,
  ]
  if (aliasRecords.length) {
    lines.push('', 'Records with retrieval metadata')
    for (const record of aliasRecords.slice(0, 10)) {
      lines.push(`- ${record.recordPath} — ${record.title}`)
      if (record.aliases.length) lines.push(`  - aliases: ${record.aliases.join(', ')}`)
      if (record.implementationHints.componentHints.length) lines.push(`  - components: ${record.implementationHints.componentHints.join(', ')}`)
    }
  }
  return `${lines.join('\n')}\n`
}

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  const index = buildContextIndex(args.root)
  const json = `${JSON.stringify(index, null, 2)}\n`
  if (args.write) {
    mkdirSync(path.dirname(args.output), { recursive: true })
    writeFileSync(args.output, json, 'utf8')
    if (args.format === 'json') process.stdout.write(json)
    else process.stdout.write(renderMarkdown(index))
    return
  }
  if (args.format === 'md') process.stdout.write(renderMarkdown(index))
  else process.stdout.write(json)
}

main()
