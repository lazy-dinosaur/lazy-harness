#!/usr/bin/env bun
/**
 * Document Resource Ingestion (SDD: spec/platform/document-resource-ingestion.md)
 *
 * Current slices are safe-by-default: inspect and plan are read-only; apply is
 * implemented as dry-run only until explicit record-promotion UX exists.
 */
import { createHash } from 'node:crypto'
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { basename, join, relative } from 'node:path'

const STATUS_VALUES = ['authoritative', 'candidate', 'historical', 'duplicate', 'conflicting', 'rejected'] as const
type Status = typeof STATUS_VALUES[number]
type Format = 'json' | 'md'
type Mode = 'inspect' | 'plan' | 'apply'

interface Args {
  mode: Mode
  format: Format
  root: string
  includes: string[]
  maxFiles: number
  dryRun: boolean
}

interface PathReference {
  value: string
  exists: boolean
}

interface DocumentReport {
  id: string
  path: string
  bytes: number
  mtime: string
  title: string | null
  headings: string[]
  keywords: string[]
  pathReferences: PathReference[]
  fingerprint: string
  duplicateGroupId: string | null
  status: Status
  reasons: string[]
  scores: {
    freshness: number
    authority: number
    duplicate: number
    contamination: number
  }
}

interface DuplicateGroup {
  id: string
  paths: string[]
  reason: string
}

interface InspectResult {
  ok: true
  mode: 'document-resource-ingestion.inspect'
  schemaVersion: '1.0'
  root: string
  scannedAt: string
  documents: DocumentReport[]
  duplicateGroups: DuplicateGroup[]
  warnings: string[]
  nextActions: string[]
}

interface ProposedWrite {
  path: string
  kind: 'document-intake-ledger' | 'candidate-jsonl'
  action: 'create-or-update' | 'append'
  content: string
  summary: string
}

interface CandidateEntry {
  timestamp: string
  type: 'document-resource-ingestion-candidate'
  sourcePath: string
  status: Status
  title: string | null
  keywords: string[]
  reasons: string[]
  scores: DocumentReport['scores']
  provenance: {
    documentId: string
    fingerprint: string
    duplicateGroupId: string | null
  }
  promotion: 'requires-user-confirmation'
}

interface PlanResult {
  ok: true
  mode: 'document-resource-ingestion.plan' | 'document-resource-ingestion.apply-dry-run'
  schemaVersion: '1.0'
  root: string
  generatedAt: string
  dryRun: boolean
  inspect: InspectResult
  proposedWrites: ProposedWrite[]
  candidateEntries: CandidateEntry[]
  optionGate: {
    prompt: string
    options: string[]
    recommended: string
  }
  warnings: string[]
}

const DEFAULT_INCLUDES = [
  'README.md',
  'README.*',
  'docs/**/*.{md,mdx,txt}',
  'architecture/**/*.{md,mdx,txt}',
  'notes/**/*.{md,mdx,txt}',
  'CHANGELOG.md',
  'CONTRIBUTING.md',
  'MIGRATION*.md',
  'RELEASE*.md',
]

const EXCLUDED_DIRS = new Set([
  '.git',
  '.lazy-harness',
  '.jcode',
  'node_modules',
  'dist',
  'build',
  'out',
  'coverage',
  '.next',
  '.turbo',
  '.cache',
])

function parseArgs(argv: string[]): Args {
  const args: Args = {
    mode: 'inspect',
    format: 'md',
    root: process.env.LAZY_HOST_ROOT || process.cwd(),
    includes: [...DEFAULT_INCLUDES],
    maxFiles: 200,
    dryRun: false,
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = argv[i + 1]
    if (arg === '--mode' && next && ['inspect', 'plan', 'apply'].includes(next)) {
      args.mode = next as Mode
      i += 1
    } else if (arg.startsWith('--mode=')) {
      const value = arg.slice('--mode='.length)
      if (!['inspect', 'plan', 'apply'].includes(value)) throw new Error(`Unsupported --mode: ${value}`)
      args.mode = value as Mode
    } else if (arg === '--format' && (next === 'json' || next === 'md' || next === 'markdown')) {
      args.format = next === 'markdown' ? 'md' : next
      i += 1
    } else if (arg.startsWith('--format=')) {
      const value = arg.slice('--format='.length)
      if (value !== 'json' && value !== 'md' && value !== 'markdown') throw new Error(`Unsupported --format: ${value}`)
      args.format = value === 'markdown' ? 'md' : value
    } else if (arg === '--root' && next) {
      args.root = next
      i += 1
    } else if (arg.startsWith('--root=')) {
      args.root = arg.slice('--root='.length)
    } else if (arg === '--include' && next) {
      args.includes.push(next)
      i += 1
    } else if (arg.startsWith('--include=')) {
      args.includes.push(arg.slice('--include='.length))
    } else if (arg === '--max-files' && next) {
      args.maxFiles = Number.parseInt(next, 10)
      i += 1
    } else if (arg.startsWith('--max-files=')) {
      args.maxFiles = Number.parseInt(arg.slice('--max-files='.length), 10)
    } else if (arg === '--dry-run') {
      args.dryRun = true
    } else if (arg === '--help' || arg === '-h') {
      printHelp()
      process.exit(0)
    } else {
      throw new Error(`Unknown or incomplete flag: ${arg}`)
    }
  }
  if (!Number.isFinite(args.maxFiles) || args.maxFiles < 1) throw new Error('--max-files must be a positive integer')
  return args
}

function printHelp(): void {
  console.log(`Document Resource Ingestion\n\nUsage:\n  bun .lazy-harness/scripts/document-resource-ingestion.ts --mode inspect [--format md|json] [--root <path>] [--include <glob>] [--max-files N]\n  bun .lazy-harness/scripts/document-resource-ingestion.ts --mode plan [--format md|json] [--root <path>] [--max-files N]\n  bun .lazy-harness/scripts/document-resource-ingestion.ts --mode apply --dry-run [--format md|json] [--root <path>] [--max-files N]\n\nInspect mode is read-only. Plan mode proposes document-intake/candidate writes without applying. Apply currently requires --dry-run and prints the same proposed writes.`)
}

function normalizeRel(path: string): string {
  return path.replace(/\\/g, '/').replace(/^\.\//, '')
}

function escapeRegExp(value: string): string {
  return value.replace(/[|\\{}()[\]^$+?.]/g, '\\$&')
}

function globToRegex(glob: string): RegExp {
  let pattern = normalizeRel(glob)
  pattern = pattern.replace(/\{([^}]+)\}/g, (_match, body: string) => `__ALT_${body.split(',').map((x) => escapeRegExp(x)).join('|')}__`)
  pattern = pattern.split('**/*').join('(?:.*/)?')
  pattern = pattern.split('**').join('.*')
  pattern = pattern.split('*').join('[^/]*')
  pattern = pattern.replace(/__ALT_([^_]+)__/, '($1)')
  return new RegExp(`^${pattern}$`, 'i')
}

function shouldInspect(path: string, includeRegexes: RegExp[]): boolean {
  const rel = normalizeRel(path)
  if (!/\.(md|mdx|txt)$/i.test(rel)) return false
  if (matchesBuiltInDocPath(rel)) return true
  return includeRegexes.some((regex) => regex.test(rel))
}

function matchesBuiltInDocPath(rel: string): boolean {
  const lower = rel.toLowerCase()
  if (/^readme\.(md|mdx|txt)$/.test(lower)) return true
  if (/^(docs|architecture|notes)\/.+\.(md|mdx|txt)$/.test(lower)) return true
  if (/^(changelog|contributing)\.(md|mdx|txt)$/.test(lower)) return true
  if (/^(migration|release)[^/]*\.(md|mdx|txt)$/.test(lower)) return true
  return false
}

function walk(root: string, includeRegexes: RegExp[], maxFiles: number): string[] {
  const out: string[] = []
  function visit(abs: string): void {
    if (out.length >= maxFiles) return
    const st = statSync(abs)
    const name = basename(abs)
    if (st.isDirectory()) {
      if (EXCLUDED_DIRS.has(name)) return
      for (const entry of readdirSync(abs).sort()) visit(join(abs, entry))
      return
    }
    if (!st.isFile()) return
    const rel = normalizeRel(relative(root, abs))
    if (shouldInspect(rel, includeRegexes)) out.push(abs)
  }
  visit(root)
  return out.slice(0, maxFiles)
}

function hash(value: string, length = 16): string {
  return createHash('sha256').update(value).digest('hex').slice(0, length)
}

function titleAndHeadings(text: string): { title: string | null; headings: string[] } {
  const headings = text.split(/\r?\n/)
    .map((line) => line.match(/^#{1,4}\s+(.+?)\s*#*\s*$/)?.[1]?.trim())
    .filter((value): value is string => Boolean(value))
    .slice(0, 12)
  return { title: headings[0] || null, headings }
}

function words(text: string): string[] {
  return [...new Set(text.toLowerCase().match(/[a-z][a-z0-9_-]{2,}|[가-힣]{2,}/g) || [])]
}

function detectKeywords(text: string): string[] {
  const lower = text.toLowerCase()
  const mapping: Array<[string, RegExp]> = [
    ['architecture', /architecture|system design|아키텍|시스템\s*디자인|bounded context|layered|clean architecture/],
    ['domain', /domain|entity|aggregate|business rule|도메인|엔티티|비즈니스\s*규칙/],
    ['test', /test|vitest|playwright|pytest|coverage|테스트|검증|회귀/],
    ['config', /config|env|schema|migration|설정|환경변수|스키마|마이그레이션/],
    ['frontend', /frontend|react|next\.js|component|design system|ui|컴포넌트|디자인\s*시스템/],
    ['backend', /backend|api|database|postgres|server|백엔드|데이터베이스/],
    ['release', /release|changelog|migration|deploy|릴리즈|배포/],
    ['deprecated', /deprecated|outdated|legacy|do not use|더 이상|폐기|레거시/],
  ]
  return mapping.filter(([, regex]) => regex.test(lower)).map(([name]) => name)
}

function detectPathReferences(root: string, text: string): PathReference[] {
  const pathReferencePattern = /(?:^|[\s`'"(])((?:src|app|pages|components|lib|server|docs|\.lazy-harness|tests|test|prisma|scripts|packages)\/[A-Za-z0-9_.\-/]+)(?=[\s`'"),.:;]|$)/gm
  const candidates = [...text.matchAll(pathReferencePattern)]
    .map((match) => match[1].replace(/[),.;:]+$/, ''))
    .slice(0, 30)
  return [...new Set(candidates)].map((value) => ({ value, exists: existsSync(join(root, value)) }))
}

function contentFingerprint(title: string | null, headings: string[], text: string): string {
  const source = [title || '', ...headings.slice(0, 5), ...words(text).slice(0, 80)].join('\n')
  return hash(source, 12)
}

function scoreDocument(root: string, abs: string, text: string, duplicateCount: number): Omit<DocumentReport, 'id' | 'path' | 'bytes' | 'mtime' | 'duplicateGroupId'> {
  const rel = normalizeRel(relative(root, abs))
  const st = statSync(abs)
  const { title, headings } = titleAndHeadings(text)
  const keywords = detectKeywords(text)
  const pathReferences = detectPathReferences(root, text)
  const fingerprint = contentFingerprint(title, headings, text)
  const ageDays = Math.max(0, (Date.now() - st.mtimeMs) / 86_400_000)
  const existingRefs = pathReferences.filter((entry) => entry.exists).length
  const missingRefs = pathReferences.filter((entry) => !entry.exists).length
  const lower = text.toLowerCase()
  const relLower = rel.toLowerCase()
  const reasons: string[] = []

  let freshness = 50
  if (ageDays <= 90) { freshness += 20; reasons.push('recently modified') }
  if (existingRefs > 0) { freshness += Math.min(20, existingRefs * 5); reasons.push('references current paths') }
  if (missingRefs > 0) { freshness -= Math.min(30, missingRefs * 7); reasons.push('references missing paths') }
  if (/legacy|archive|old|deprecated|outdated|historical|폐기|레거시/.test(relLower + '\n' + lower)) { freshness -= 25; reasons.push('legacy/outdated signal') }

  let authority = 30
  if (/^readme\./i.test(rel)) { authority += 20; reasons.push('root README') }
  if (/contributing|release|migration|changelog/i.test(rel)) { authority += 10; reasons.push('project lifecycle doc') }
  if (keywords.includes('architecture') || keywords.includes('config') || keywords.includes('test')) { authority += 10; reasons.push('contains operational keywords') }

  let contamination = 0
  if (/\uFFFD|�/.test(text)) { contamination += 35; reasons.push('replacement-character contamination') }
  if (/do not use|outdated|deprecated|obsolete|wrong|invalid|폐기|오염|사용하지/.test(lower)) { contamination += 25; reasons.push('explicit stale/pollution wording') }
  if (missingRefs >= 3) { contamination += 20; reasons.push('many missing path references') }
  if (text.length > 500_000) { contamination += 15; reasons.push('oversized document') }

  const duplicate = duplicateCount > 1 ? Math.min(100, 50 + duplicateCount * 10) : 0
  if (duplicate > 0) reasons.push('duplicate/overlap cluster')

  freshness = clamp(freshness)
  authority = clamp(authority)
  contamination = clamp(contamination)

  let status: Status = 'candidate'
  if (contamination >= 50) status = 'rejected'
  else if (duplicate > 0) status = 'duplicate'
  else if (freshness < 35 || /legacy|archive|historical|old/i.test(relLower)) status = 'historical'
  else if (authority >= 55 && freshness >= 45 && contamination < 30) status = 'authoritative'
  else if (missingRefs > existingRefs && missingRefs > 0) status = 'conflicting'

  return { title, headings, keywords, pathReferences, fingerprint, status, reasons: [...new Set(reasons)], scores: { freshness, authority, duplicate, contamination } }
}

function clamp(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)))
}

function inspect(args: Args): InspectResult {
  const root = args.root
  if (!existsSync(root)) throw new Error(`Root does not exist: ${root}`)
  const includeRegexes = args.includes.map(globToRegex)
  const files = walk(root, includeRegexes, args.maxFiles)
  const rawDocs = files.map((abs) => {
    const text = readFileSync(abs, 'utf8')
    const { title, headings } = titleAndHeadings(text)
    return { abs, text, fingerprint: contentFingerprint(title, headings, text) }
  })
  const counts = new Map<string, number>()
  rawDocs.forEach((doc) => counts.set(doc.fingerprint, (counts.get(doc.fingerprint) || 0) + 1))
  const groups: DuplicateGroup[] = [...counts.entries()]
    .filter(([, count]) => count > 1)
    .map(([fingerprint]) => ({ id: `DIG-${fingerprint}`, paths: rawDocs.filter((doc) => doc.fingerprint === fingerprint).map((doc) => normalizeRel(relative(root, doc.abs))), reason: 'same title/heading/content fingerprint' }))
  const documents = rawDocs.map((doc) => {
    const st = statSync(doc.abs)
    const partial = scoreDocument(root, doc.abs, doc.text, counts.get(doc.fingerprint) || 0)
    return {
      id: `DOC-${hash(normalizeRel(relative(root, doc.abs)), 12)}`,
      path: normalizeRel(relative(root, doc.abs)),
      bytes: st.size,
      mtime: st.mtime.toISOString(),
      ...partial,
      duplicateGroupId: (counts.get(doc.fingerprint) || 0) > 1 ? `DIG-${doc.fingerprint}` : null,
    }
  }).sort((a, b) => a.path.localeCompare(b.path))
  const warnings: string[] = []
  if (documents.length === args.maxFiles) warnings.push(`max-files limit reached (${args.maxFiles}); report may be incomplete`)
  if (documents.length === 0) warnings.push('no non-harness documents matched include patterns')
  return {
    ok: true,
    mode: 'document-resource-ingestion.inspect',
    schemaVersion: '1.0',
    root,
    scannedAt: new Date().toISOString(),
    documents,
    duplicateGroups: groups,
    warnings,
    nextActions: [
      'Review authoritative/candidate/conflicting/rejected suggestions before writing records.',
      'Run a future plan/apply mode only after user confirmation.',
      'Use Project Profile after document-resource evidence is reviewed.',
    ],
  }
}

function renderMd(result: InspectResult): string {
  const statusCounts = new Map<Status, number>()
  for (const doc of result.documents) statusCounts.set(doc.status, (statusCounts.get(doc.status) || 0) + 1)
  const lines: string[] = []
  lines.push('# Document Resource Ingestion inspect report')
  lines.push('')
  lines.push(`- Root: \`${result.root}\``)
  lines.push(`- Documents: ${result.documents.length}`)
  lines.push(`- Duplicate groups: ${result.duplicateGroups.length}`)
  lines.push(`- Status counts: ${STATUS_VALUES.map((status) => `${status}=${statusCounts.get(status) || 0}`).join(', ')}`)
  if (result.warnings.length) {
    lines.push('')
    lines.push('## Warnings')
    result.warnings.forEach((warning) => lines.push(`- ${warning}`))
  }
  lines.push('')
  lines.push('## Documents')
  for (const doc of result.documents) {
    lines.push('')
    lines.push(`### ${doc.path}`)
    lines.push(`- Status: **${doc.status}**`)
    lines.push(`- Scores: freshness=${doc.scores.freshness}, authority=${doc.scores.authority}, duplicate=${doc.scores.duplicate}, contamination=${doc.scores.contamination}`)
    if (doc.title) lines.push(`- Title: ${doc.title}`)
    if (doc.keywords.length) lines.push(`- Keywords: ${doc.keywords.join(', ')}`)
    if (doc.duplicateGroupId) lines.push(`- Duplicate group: ${doc.duplicateGroupId}`)
    if (doc.pathReferences.length) lines.push(`- Path refs: ${doc.pathReferences.slice(0, 8).map((ref) => `${ref.exists ? '✓' : '✗'} ${ref.value}`).join('; ')}`)
    if (doc.reasons.length) lines.push(`- Reasons: ${doc.reasons.join('; ')}`)
  }
  if (result.duplicateGroups.length) {
    lines.push('')
    lines.push('## Duplicate groups')
    for (const group of result.duplicateGroups) lines.push(`- ${group.id}: ${group.paths.join(', ')}`)
  }
  lines.push('')
  lines.push('## Next actions')
  result.nextActions.forEach((action) => lines.push(`- ${action}`))
  return lines.join('\n')
}

function xmlEscape(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function buildCandidateEntries(inspectResult: InspectResult, generatedAt: string): CandidateEntry[] {
  return inspectResult.documents
    .filter((doc) => doc.status !== 'authoritative')
    .map((doc) => ({
      timestamp: generatedAt,
      type: 'document-resource-ingestion-candidate',
      sourcePath: doc.path,
      status: doc.status,
      title: doc.title,
      keywords: doc.keywords,
      reasons: doc.reasons,
      scores: doc.scores,
      provenance: {
        documentId: doc.id,
        fingerprint: doc.fingerprint,
        duplicateGroupId: doc.duplicateGroupId,
      },
      promotion: 'requires-user-confirmation',
    }))
}

function buildIntakeLedgerXml(inspectResult: InspectResult, generatedAt: string): string {
  const statusCounts = new Map<Status, number>()
  for (const doc of inspectResult.documents) statusCounts.set(doc.status, (statusCounts.get(doc.status) || 0) + 1)
  const lines: string[] = []
  lines.push('<?xml version="1.0" encoding="UTF-8"?>')
  lines.push(`<documentIntake version="1" generatedAt="${xmlEscape(generatedAt)}" root="${xmlEscape(inspectResult.root)}">`)
  lines.push('  <summary>')
  lines.push(`    <documents total="${inspectResult.documents.length}" duplicateGroups="${inspectResult.duplicateGroups.length}" />`)
  lines.push(`    <statuses ${STATUS_VALUES.map((status) => `${status}="${statusCounts.get(status) || 0}"`).join(' ')} />`)
  lines.push('  </summary>')
  if (inspectResult.duplicateGroups.length) {
    lines.push('  <duplicateGroups>')
    for (const group of inspectResult.duplicateGroups) {
      lines.push(`    <group id="${xmlEscape(group.id)}" reason="${xmlEscape(group.reason)}">`)
      for (const path of group.paths) lines.push(`      <path>${xmlEscape(path)}</path>`)
      lines.push('    </group>')
    }
    lines.push('  </duplicateGroups>')
  }
  lines.push('  <documents>')
  for (const doc of inspectResult.documents) {
    lines.push(`    <document id="${xmlEscape(doc.id)}" path="${xmlEscape(doc.path)}" status="${doc.status}" fingerprint="${xmlEscape(doc.fingerprint)}">`)
    if (doc.title) lines.push(`      <title>${xmlEscape(doc.title)}</title>`)
    lines.push(`      <scores freshness="${doc.scores.freshness}" authority="${doc.scores.authority}" duplicate="${doc.scores.duplicate}" contamination="${doc.scores.contamination}" />`)
    if (doc.keywords.length) lines.push(`      <keywords>${doc.keywords.map(xmlEscape).join(',')}</keywords>`)
    if (doc.duplicateGroupId) lines.push(`      <duplicateGroup>${xmlEscape(doc.duplicateGroupId)}</duplicateGroup>`)
    if (doc.reasons.length) {
      lines.push('      <reasons>')
      for (const reason of doc.reasons) lines.push(`        <reason>${xmlEscape(reason)}</reason>`)
      lines.push('      </reasons>')
    }
    lines.push('    </document>')
  }
  lines.push('  </documents>')
  lines.push('</documentIntake>')
  return lines.join('\n') + '\n'
}

function buildPlanResult(args: Args): PlanResult {
  if (args.mode === 'apply' && !args.dryRun) {
    throw new Error('apply mode is not implemented yet; use --dry-run to preview proposed writes')
  }
  const inspectResult = inspect(args)
  const generatedAt = new Date().toISOString()
  const candidateEntries = buildCandidateEntries(inspectResult, generatedAt)
  const ledgerXml = buildIntakeLedgerXml(inspectResult, generatedAt)
  const candidateJsonl = candidateEntries.map((entry) => JSON.stringify(entry, null, 0)).join('\n') + (candidateEntries.length ? '\n' : '')
  const proposedWrites: ProposedWrite[] = [
    {
      path: '.lazy-harness/project/document-intake.xml',
      kind: 'document-intake-ledger',
      action: 'create-or-update',
      content: ledgerXml,
      summary: `Document intake ledger for ${inspectResult.documents.length} scanned docs`,
    },
  ]
  if (candidateEntries.length) {
    proposedWrites.push({
      path: '.lazy-harness/knowledge/candidates.jsonl',
      kind: 'candidate-jsonl',
      action: 'append',
      content: candidateJsonl,
      summary: `${candidateEntries.length} candidate/quarantine entries requiring review`,
    })
  }
  return {
    ok: true,
    mode: args.mode === 'apply' ? 'document-resource-ingestion.apply-dry-run' : 'document-resource-ingestion.plan',
    schemaVersion: '1.0',
    root: args.root,
    generatedAt,
    dryRun: args.mode === 'apply' ? true : args.dryRun,
    inspect: inspectResult,
    proposedWrites,
    candidateEntries,
    optionGate: {
      prompt: 'How should document-resource ingestion proceed?',
      options: [
        'A. Create/update document-intake ledger only (Recommended)',
        'B. Append candidate/quarantine entries only',
        'C. Defer writes and continue Project Profile interview',
        'D. Custom instruction',
      ],
      recommended: 'A',
    },
    warnings: [
      ...inspectResult.warnings,
      'No DDD/SDD/BDD/TDD/ADR/SSOT promotion is included in this plan.',
      'User confirmation is required before any write is applied.',
    ],
  }
}

function renderPlanMd(result: PlanResult): string {
  const lines: string[] = []
  lines.push(`# ${result.mode === 'document-resource-ingestion.apply-dry-run' ? 'Document Resource Ingestion apply dry-run' : 'Document Resource Ingestion plan'}`)
  lines.push('')
  lines.push(`- Root: \`${result.root}\``)
  lines.push(`- Dry run: ${result.dryRun ? 'yes' : 'plan-only'}`)
  lines.push(`- Documents: ${result.inspect.documents.length}`)
  lines.push(`- Candidate entries: ${result.candidateEntries.length}`)
  lines.push('')
  lines.push('## Proposed writes')
  for (const write of result.proposedWrites) {
    lines.push(`- \`${write.path}\` (${write.action}, ${write.kind}): ${write.summary}`)
  }
  if (result.warnings.length) {
    lines.push('')
    lines.push('## Warnings')
    result.warnings.forEach((warning) => lines.push(`- ${warning}`))
  }
  lines.push('')
  lines.push('## Option gate')
  lines.push(result.optionGate.prompt)
  result.optionGate.options.forEach((option) => lines.push(`- ${option}`))
  lines.push('')
  lines.push('## Candidate preview')
  for (const entry of result.candidateEntries.slice(0, 20)) {
    lines.push(`- ${entry.status}: \`${entry.sourcePath}\`${entry.title ? ` — ${entry.title}` : ''}`)
  }
  if (result.candidateEntries.length > 20) lines.push(`- ... ${result.candidateEntries.length - 20} more`)
  return lines.join('\n')
}

function main(): void {
  try {
    const args = parseArgs(process.argv.slice(2))
    if (args.mode === 'inspect') {
      const result = inspect(args)
      if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
      else console.log(renderMd(result))
    } else {
      const result = buildPlanResult(args)
      if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
      else console.log(renderPlanMd(result))
    }
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    process.exit(1)
  }
}

main()
