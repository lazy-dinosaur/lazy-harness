#!/usr/bin/env bun
/**
 * relevant-record-query.ts — explicit compact relevant-record helper.
 *
 * Prototype scope (ADR 0041 Phase 3): build a compact digest from canonical
 * .lazy-harness records without attaching policy to concrete tools.
 */

import { existsSync, readFileSync, readdirSync, statSync } from 'fs'
import * as path from 'path'

const LAYER_DIRS = {
  DDD: '.lazy-harness/domain',
  SDD: '.lazy-harness/spec',
  BDD: '.lazy-harness/behavior',
  TDD: '.lazy-harness/tests',
  ADR: '.lazy-harness/decisions',
  SSOT: '.lazy-harness/ssot',
  Planning: '.lazy-harness/planning'
} as const

type Layer = keyof typeof LAYER_DIRS

type DigestStatus = 'active' | 'advisory' | 'deprecated' | 'reverted' | 'needs-review'
type Scope = 'framework-global' | 'host-project' | 'team-policy' | 'layer-fact' | 'transient-plan' | 'jcode-local' | 'ambiguous'
type DigestSource = 'rule-digest' | 'fallback'

interface CliOptions {
  root: string
  message: string
  recentContext: string[]
  touchedFiles: string[]
  preferredLayers: Layer[]
  includeStatuses: DigestStatus[]
  limit: number
  tokenBudget: number
  format: 'md' | 'json'
  requireDigest: boolean
}

interface IndexedDigest {
  recordPath: string
  title: string
  layer: Layer
  status: DigestStatus
  scope: Scope
  digestSource: DigestSource
  appliesWhen: string[]
  must: string[]
  mustNot: string[]
  bullets: string[]
  recordCompletion?: string
  relatedRecords: string[]
  bodyPreview: string
  updatedAt?: string
  startLine?: number
  endLine?: number
}

interface QueryEntry extends IndexedDigest {
  score: number
  matchedCues: string[]
}

function usage(): never {
  console.error(`Usage: relevant-record-query --message "..." [options]

Options:
  --root DIR                 Host root (default: LAZY_HOST_ROOT or cwd)
  --message TEXT             User/coordinator message to query for
  --recent-context TEXT      Additional short context; may repeat
  --touched-file PATH        Touched file path; may repeat
  --layer LAYER              Preferred layer; may repeat (DDD|SDD|BDD|TDD|ADR|SSOT|Planning)
  --status STATUS            Included digest status; may repeat
  --limit N                  Max entries (default 5)
  --token-budget N           Approx token budget (default 600, max suggested 1000)
  --format md|json           Output format (default md)
  --require-digest           Exclude fallback entries without a Rule digest
`)
  process.exit(2)
}

function parseArgs(argv: string[]): CliOptions {
  const opts: CliOptions = {
    root: process.env.LAZY_HOST_ROOT || process.cwd(),
    message: '',
    recentContext: [],
    touchedFiles: [],
    preferredLayers: [],
    includeStatuses: ['active', 'advisory', 'needs-review'],
    limit: 5,
    tokenBudget: 600,
    format: 'md',
    requireDigest: false
  }
  let customStatuses = false
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    const next = () => {
      const v = argv[++i]
      if (!v) usage()
      return v
    }
    const valueFor = (flag: string): string | null => {
      if (a === flag) return next()
      const prefix = `${flag}=`
      if (a.startsWith(prefix)) {
        const v = a.slice(prefix.length)
        if (!v) usage()
        return v
      }
      return null
    }
    let value: string | null = null
    if (a === '--help' || a === '-h') usage()
    else if ((value = valueFor('--root')) !== null) opts.root = value
    else if ((value = valueFor('--message')) !== null) opts.message = value
    else if ((value = valueFor('--recent-context')) !== null) opts.recentContext.push(value)
    else if ((value = valueFor('--touched-file')) !== null) opts.touchedFiles.push(value)
    else if (a === '--layer') {
      const layer = next() as Layer
      if (!(layer in LAYER_DIRS)) usage()
      opts.preferredLayers.push(layer)
    } else if ((value = valueFor('--layer')) !== null) {
      const layer = value as Layer
      if (!(layer in LAYER_DIRS)) usage()
      opts.preferredLayers.push(layer)
    } else if ((value = valueFor('--status')) !== null) {
      const status = value as DigestStatus
      if (!['active', 'advisory', 'deprecated', 'reverted', 'needs-review'].includes(status)) usage()
      if (!customStatuses) {
        opts.includeStatuses = []
        customStatuses = true
      }
      opts.includeStatuses.push(status)
    } else if ((value = valueFor('--limit')) !== null) opts.limit = Math.max(1, Number(value) || 5)
    else if ((value = valueFor('--token-budget')) !== null) opts.tokenBudget = Math.max(80, Number(value) || 600)
    else if ((value = valueFor('--format')) !== null) {
      const fmt = value
      if (fmt !== 'md' && fmt !== 'json') usage()
      opts.format = fmt
    } else if (a === '--require-digest') opts.requireDigest = true
    else usage()
  }
  if (!opts.message.trim()) usage()
  opts.root = path.resolve(opts.root)
  return opts
}

function walkRecordFiles(dir: string): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) out.push(...walkRecordFiles(full))
    else if (entry.isFile() && entry.name !== 'README.md' && /\.(md|xml)$/i.test(entry.name)) out.push(full)
  }
  return out
}

function rel(root: string, filePath: string): string {
  return path.relative(root, filePath).split(path.sep).join('/')
}

function titleFromBody(body: string, recordPath: string): string {
  const heading = body.split(/\r?\n/).find((line) => /^#\s+/.test(line))
  if (heading) return heading.replace(/^#\s+/, '').trim()
  return path.basename(recordPath).replace(/\.[^.]+$/, '')
}

function layerForPath(recordPath: string): Layer | undefined {
  const normalized = recordPath.split(path.sep).join('/')
  for (const [layer, dir] of Object.entries(LAYER_DIRS) as Array<[Layer, string]>) {
    if (normalized.includes(`/${dir}/`) || normalized.endsWith(`/${dir}`) || normalized.startsWith(`${dir}/`)) return layer
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

function findDigestBlock(body: string): { lines: string[]; startLine: number; endLine: number } | null {
  const lines = body.split(/\r?\n/)
  let inFence = false
  let start = -1
  for (let i = 0; i < lines.length; i++) {
    if (/^\s*```/.test(lines[i])) inFence = !inFence
    if (!inFence && /^##\s+Rule digest\s*$/i.test(lines[i].trim())) {
      start = i
      break
    }
  }
  if (start < 0) return null
  let end = lines.length
  inFence = false
  for (let i = start + 1; i < lines.length; i++) {
    if (/^\s*```/.test(lines[i])) inFence = !inFence
    if (!inFence && /^##\s+/.test(lines[i])) {
      end = i
      break
    }
  }
  return { lines: lines.slice(start + 1, end), startLine: start + 1, endLine: end }
}

function parseDigest(body: string, recordPath: string, layer: Layer): Omit<IndexedDigest, 'recordPath' | 'title' | 'layer' | 'bodyPreview' | 'updatedAt'> | null {
  const block = findDigestBlock(body)
  if (!block) return null
  let status: DigestStatus = 'active'
  let digestLayer: Layer = layer
  let scope: Scope = layer === 'Planning' ? 'transient-plan' : 'layer-fact'
  const appliesWhen: string[] = []
  const must: string[] = []
  const mustNot: string[] = []
  const relatedRecords: string[] = []
  let recordCompletion = ''
  let current: 'appliesWhen' | 'must' | 'mustNot' | 'relatedRecords' | 'recordCompletion' | null = null

  for (const raw of block.lines) {
    const line = raw.trimEnd()
    const field = line.match(/^-\s+(Status|Layer|Scope|Record completion):\s*(.*)$/i)
    if (field) {
      const key = field[1].toLowerCase()
      const value = field[2].trim()
      current = null
      if (key === 'status') status = normalizeStatus(value)
      else if (key === 'layer') digestLayer = normalizeLayer(value, layer)
      else if (key === 'scope') scope = normalizeScope(value, scope)
      else if (key === 'record completion') {
        current = 'recordCompletion'
        if (value) recordCompletion = value
      }
      continue
    }
    const collection = line.match(/^-\s+(Applies when|Must|Must not|Related records):\s*$/i)
    if (collection) {
      const key = collection[1].toLowerCase()
      if (key === 'applies when') current = 'appliesWhen'
      else if (key === 'must') current = 'must'
      else if (key === 'must not') current = 'mustNot'
      else if (key === 'related records') current = 'relatedRecords'
      continue
    }
    const item = line.match(/^\s*-\s+(.+)$/)
    if (item && current) {
      const value = item[1].trim()
      if (current === 'appliesWhen') appliesWhen.push(value)
      else if (current === 'must') must.push(value)
      else if (current === 'mustNot') mustNot.push(value)
      else if (current === 'relatedRecords') relatedRecords.push(value.replace(/`/g, ''))
      else if (current === 'recordCompletion') recordCompletion = recordCompletion ? `${recordCompletion}; ${value}` : value
    }
  }
  const bullets = [...must, ...mustNot.map((b) => `Do not: ${b}`)].slice(0, 5)
  return {
    status,
    scope,
    digestSource: 'rule-digest',
    appliesWhen,
    must,
    mustNot,
    bullets: bullets.length ? bullets : appliesWhen.slice(0, 3),
    recordCompletion: recordCompletion || undefined,
    relatedRecords,
    startLine: block.startLine,
    endLine: block.endLine,
    layer: digestLayer
  } as Omit<IndexedDigest, 'recordPath' | 'title' | 'bodyPreview' | 'updatedAt'> & { layer: Layer }
}

function fallbackDigest(body: string, layer: Layer): Omit<IndexedDigest, 'recordPath' | 'title' | 'layer' | 'updatedAt'> {
  const lines = body.split(/\r?\n/)
  const meaningful = lines
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#') && !line.startsWith('```'))
    .slice(0, 4)
  const scope: Scope = layer === 'Planning' ? 'transient-plan' : 'layer-fact'
  return {
    status: 'active',
    scope,
    digestSource: 'fallback',
    appliesWhen: [],
    must: [],
    mustNot: [],
    bullets: meaningful.slice(0, 2),
    relatedRecords: [],
    bodyPreview: meaningful.join(' ').slice(0, 600)
  }
}

function buildIndex(root: string): IndexedDigest[] {
  const out: IndexedDigest[] = []
  for (const [layer, dir] of Object.entries(LAYER_DIRS) as Array<[Layer, string]>) {
    for (const file of walkRecordFiles(path.join(root, dir))) {
      let body = ''
      try {
        body = readFileSync(file, 'utf8')
      } catch {
        continue
      }
      const recordPath = rel(root, file)
      const actualLayer = layerForPath(recordPath) || layer
      const parsed = parseDigest(body, recordPath, actualLayer)
      const fallback = fallbackDigest(body, actualLayer)
      const stat = (() => { try { return statSync(file) } catch { return undefined } })()
      const base = parsed || fallback
      out.push({
        ...base,
        recordPath,
        title: titleFromBody(body, recordPath),
        layer: (parsed as any)?.layer || actualLayer,
        bodyPreview: fallback.bodyPreview,
        updatedAt: stat?.mtime.toISOString()
      } as IndexedDigest)
    }
  }
  return out
}

function tokenize(text: string): string[] {
  return Array.from(new Set(
    text
      .toLowerCase()
      .replace(/[`*_#()[\]{}.,:;!?/\\|]+/g, ' ')
      .split(/\s+/)
      .map((t) => t.trim())
      .filter((t) => t.length >= 2)
  ))
}

function estimateTokens(text: string): number {
  const asciiWords = (text.match(/[A-Za-z0-9_./:-]+/g) || []).length
  const hangulChars = (text.match(/[가-힣]/g) || []).length
  return Math.max(1, Math.ceil(asciiWords * 1.3 + hangulChars / 2.5))
}

function scoreRecord(record: IndexedDigest, opts: CliOptions, tokens: string[]): QueryEntry | null {
  if (!opts.includeStatuses.includes(record.status)) return null
  if (opts.requireDigest && record.digestSource !== 'rule-digest') return null
  if (opts.preferredLayers.length && !opts.preferredLayers.includes(record.layer)) return null

  const sections = {
    applies: record.appliesWhen.join(' ').toLowerCase(),
    title: `${record.title} ${record.recordPath}`.toLowerCase(),
    bullets: `${record.bullets.join(' ')} ${record.bodyPreview}`.toLowerCase(),
    related: record.relatedRecords.join(' ').toLowerCase()
  }
  const message = [opts.message, ...opts.recentContext, ...opts.touchedFiles].join(' ').toLowerCase()
  const matched = new Set<string>()
  let raw = 0

  for (const cue of record.appliesWhen) {
    const c = cue.toLowerCase()
    if (c && (message.includes(c) || c.split(/\s+/).some((part) => part.length >= 2 && message.includes(part)))) {
      raw += 5
      matched.add(cue)
    }
  }

  for (const token of tokens) {
    if (sections.applies.includes(token)) { raw += 3; matched.add(token) }
    if (sections.title.includes(token)) { raw += 2; matched.add(token) }
    if (sections.bullets.includes(token)) { raw += 1; matched.add(token) }
    if (sections.related.includes(token)) { raw += 1; matched.add(token) }
  }

  for (const file of opts.touchedFiles) {
    const stem = path.basename(file).toLowerCase().replace(/\.[^.]+$/, '')
    if (stem && sections.related.includes(stem)) { raw += 2; matched.add(stem) }
  }

  if (raw <= 0) return null
  const statusWeight: Record<DigestStatus, number> = {
    active: 1,
    advisory: 0.8,
    'needs-review': 0.7,
    deprecated: 0.2,
    reverted: 0.1
  }
  const sourceWeight = record.digestSource === 'rule-digest' ? 1 : 0.55
  const score = Math.min(1, (raw / Math.max(6, tokens.length * 4)) * statusWeight[record.status] * sourceWeight)
  return { ...record, score, matchedCues: Array.from(matched).slice(0, 8) }
}

function query(opts: CliOptions): { entries: QueryEntry[]; estimatedTokens: number; truncated: boolean } {
  const tokens = tokenize([opts.message, ...opts.recentContext, ...opts.touchedFiles].join(' '))
  const entries = buildIndex(opts.root)
    .map((record) => scoreRecord(record, opts, tokens))
    .filter((r): r is QueryEntry => Boolean(r))
    .sort((a, b) => b.score - a.score || a.recordPath.localeCompare(b.recordPath))

  const selected: QueryEntry[] = []
  let estimated = estimateTokens('Explicit relevant-record helper output')
  let truncated = false
  for (const entry of entries) {
    if (selected.length >= opts.limit) { truncated = entries.length > selected.length; break }
    const bullets = compactBullets(entry)
    const cost = estimateTokens(`${entry.recordPath} ${entry.title} ${bullets.join(' ')}`)
    if (selected.length > 0 && estimated + cost > opts.tokenBudget) {
      truncated = true
      break
    }
    selected.push({ ...entry, bullets })
    estimated += cost
  }
  return { entries: selected, estimatedTokens: estimated, truncated }
}

function compactBullets(entry: IndexedDigest): string[] {
  const bullets = entry.bullets.length ? entry.bullets : entry.appliesWhen
  return bullets.map((b) => b.replace(/\s+/g, ' ').trim()).filter(Boolean).slice(0, 3)
}

function renderMarkdown(result: ReturnType<typeof query>): string {
  if (result.entries.length === 0) return 'Explicit relevant-record helper output\n- Helper only: this is not automatic semantic authority. No matching rule digest found; perform direct root-bound record/source/test search if the task is host-specific.\n'
  const lines = ['Explicit relevant-record helper output', '- Helper only: do not treat this digest as semantic authority; perform direct root-bound search/read when host detail or ambiguity remains.']
  for (const entry of result.entries) {
    const statusSuffix = entry.status === 'active' ? '' : ` [${entry.status}]`
    lines.push(`- \`${entry.recordPath}\` — ${entry.title}${statusSuffix}`)
    for (const bullet of compactBullets(entry)) lines.push(`  - ${bullet}`)
    if (entry.recordCompletion) lines.push(`  - Record completion: ${entry.recordCompletion}`)
  }
  if (result.truncated) lines.push('- ... truncated by token budget')
  return lines.join('\n') + '\n'
}

function main() {
  const opts = parseArgs(process.argv.slice(2))
  if (!existsSync(path.join(opts.root, '.lazy-harness'))) {
    console.error(`relevant-record-query: not a lazy-harness host: ${opts.root}`)
    process.exit(2)
  }
  const result = query(opts)
  if (opts.format === 'json') {
    console.log(JSON.stringify({
      schemaVersion: '1.0',
      generatedAt: new Date().toISOString(),
      query: {
        message: opts.message,
        recentContext: opts.recentContext,
        touchedFiles: opts.touchedFiles,
        preferredLayers: opts.preferredLayers,
        limit: opts.limit,
        tokenBudget: opts.tokenBudget,
        includeStatuses: opts.includeStatuses,
        requireDigest: opts.requireDigest
      },
      digest: result
    }, null, 2))
  } else {
    process.stdout.write(renderMarkdown(result))
  }
}

main()
